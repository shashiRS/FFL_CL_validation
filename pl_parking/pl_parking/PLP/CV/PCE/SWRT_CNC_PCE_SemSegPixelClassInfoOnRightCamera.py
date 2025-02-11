#!/usr/bin/env python3
"""Defining  Semseg Pixel Class Information"""
import logging
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from tsf.core.results import FALSE, NAN, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.core.utilities import debug
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.CV.PCE.ft_helper as ft
from pl_parking.PLP.CV.PCE.constants import BaseCtrl, PlotlyTemplate, SemSegLabel, SigStatus

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "SEMSEG_RIGHT_SIGNALS"

example_obj = ft.PCESignals()


class PCESEMSEGSignals(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        BASE_CTRL_OPMODE_RSC = "Base_ctrl_opmode_rsc"
        SEMSEG_TIMESTAMP_RSC = "semseg_timestamp_rsc"
        SEMSEG_SIGSTATUS_RSC = "semseg_sig_status_rsc"
        SEMSEG_IMAGEDATA_RSC = "SemSeg_imageData_rsc"
        SEMSEG_IMAGEDATAOFFSET_RSC = "SemSeg_imageDataOffset_rsc"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()
        self._root = ["MTA_ADC5", "AP"]
        self._properties = self.get_properties()

    def get_properties(self):
        """Generate a string of signals to be read."""
        signal_dict = {
            # signal name has to be updated after having R4 recordings
            self.Columns.MTS_TS: "MTS.Package.TimeStamp",
            self.Columns.BASE_CTRL_OPMODE_RSC: ".GRAPPA_RSC_DATA.syncRef.m_baseCtrlData.eOpMode",
            self.Columns.SEMSEG_TIMESTAMP_RSC: ".GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.signalHeader.uiTimeStamp",
            self.Columns.SEMSEG_SIGSTATUS_RSC: ".GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.signalHeader.eSigStatus",
            self.Columns.SEMSEG_IMAGEDATA_RSC: ".GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.imageData",
            self.Columns.SEMSEG_IMAGEDATAOFFSET_RSC: ".GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.imageDataOffset",
        }
        return signal_dict


@register_signals(SIGNAL_DATA, PCESEMSEGSignals)
@teststep_definition(
    step_number=1,
    name="SWRT_CNC_PCE_SEMSEG_PIXELCLASSINFO_ONRIGHTCAM",
    description="This test step confirms that the component provides the semseg class information",
    expected_result=BooleanResult(TRUE),
)
class PCESemsegClassInfoOnRightCameraTestStep(TestStep):
    """Test Step definition."""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()
        self.idx = 0

    def get_semseg_imagedata(self, row, camera):
        """Get semseg image data"""
        Semseg_Imagedata = int(row[f"SemSeg_imageData_{camera}", self.idx])
        self.idx = self.idx + 1
        return Semseg_Imagedata

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = fh.rep([], 3)
        self.result.measured_result = NAN

        reader = self.readers[SIGNAL_DATA]
        df = reader.as_plain_df
        signal_check = []
        signal_check.append("semseg_sig_status_rsc")
        signal_check.append("Base_ctrl_opmode_rsc")
        # checks availability of the signals
        signal_availability, list_of_missing_signals = ft.check_required_signals(signal_check, df)

        # holds the information about valid class of semseg
        list_passed = []
        eval_0 = "Ensures that the component provides the semseg class information for every pixel"

        if signal_availability:
            # when signals are available
            evaluation_desc = "RSC Semseg pixel classes"
            # Filters df for 'semseg_sig_status == AL_SIG_STATE_OK' and 'Base_ctrl_opmode is == GS_BASE_OM_RUN'
            df_filtered_check = df[
                (df["semseg_sig_status_rsc"] == SigStatus.AL_SIG_STATE_OK)
                & (df["Base_ctrl_opmode_rsc"] == BaseCtrl.GS_BASE_OM_RUN)
            ]
            df_filtered = df_filtered_check.drop_duplicates(subset=["semseg_timestamp_rsc"], keep="last")
            if not df_filtered.empty:
                # if 'semseg_sig_status == AL_SIG_STATE_OK' and 'Base_ctrl_opmode is == GS_BASE_OM_RUN'
                for _, row in df_filtered.iterrows():
                    pce = PCESemsegClassInfoOnRightCameraTestStep()
                    # get the semseg image data offset for every row
                    self.idx = int(row["SemSeg_imageDataOffset_rsc"])
                    # maximum index of semseg image data
                    maximum_index = self.idx + 532480
                    # get the class information of each and every pixel
                    Semseg_Imagedata = list(
                        map(lambda x: pce.get_semseg_imagedata(row=row, camera="rsc"), range(self.idx, maximum_index))
                    )
                    np_Semseg_Imagedata = np.array(Semseg_Imagedata)
                    # checks if each and every pixel is assigned with valid frame
                    valid_class = np.logical_and(
                        np_Semseg_Imagedata >= SemSegLabel.GRAPPA_SEMSEG_LABEL_BACKGROUND,
                        np_Semseg_Imagedata <= SemSegLabel.GRAPPA_SEMSEG_LABEL_ROAD_SIGN,
                    )
                    if valid_class.size > 0 and all(valid_class):
                        # if valid class is provided for each and every pixel
                        list_passed.append(True)
                    else:
                        # if valid class is not provided for any of the pixel in frame
                        list_passed.append(False)
                if all(list_passed):
                    # when valid class is provided for all pixels on semseg data output.
                    evaluation_result = "valid class is provided for all pixels on RSC semseg data output"
                    test_result = fc.PASS
                    self.result.measured_result = TRUE
                    verdict_result = "passed"
                else:
                    # when valid class is not provided for any of pixels on semseg data output
                    test_result = fc.FAIL
                    self.result.measured_result = FALSE
                    evaluation_result = (
                        "valid class information is not provided for any one pixel on RSC semseg data output"
                    )
                    verdict_result = "failed"
            else:
                # when preconditions not met (Filters df for 'semseg_sig_status != AL_SIG_STATE_OK' and
                # 'Base_ctrl_opmode is != GS_BASE_OM_RUN')
                test_result = fc.NOT_ASSESSED
                self.result.measured_result = NAN
                evaluation_result = "precondition not met."
                verdict_result = "Not assessed"
            signal_summary = pd.DataFrame(
                {
                    "Evaluation": {
                        "1": evaluation_desc,
                    },
                    "Result": {
                        "1": evaluation_result,
                    },
                    "Verdict": {
                        "1": verdict_result,
                    },
                }
            )
            # Add the table
            sig_sum = fh.build_html_table(signal_summary)
            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append("")
            # plot the signals needed
            df_filtered_check = df[["mts_ts", "semseg_timestamp_rsc", "semseg_sig_status_rsc", "Base_ctrl_opmode_rsc"]]
            df_plot = df_filtered_check[
                (df_filtered_check["semseg_sig_status_rsc"] == SigStatus.AL_SIG_STATE_OK)
                & (df_filtered_check["Base_ctrl_opmode_rsc"] == BaseCtrl.GS_BASE_OM_RUN)
            ]
            df_plot = df_plot.drop_duplicates(subset=["semseg_timestamp_rsc"], keep="last")
            fig = go.Figure()
            # Semseg status
            fig.add_trace(
                go.Scatter(
                    x=df_plot["semseg_timestamp_rsc"],
                    y=df_plot["semseg_sig_status_rsc"],
                    mode="lines",
                    name="semseg_sig_status_rsc",
                )
            )
            # Base control opmode
            fig.add_trace(
                go.Scatter(
                    x=df_plot["semseg_timestamp_rsc"],
                    y=df_plot["Base_ctrl_opmode_rsc"],
                    mode="lines",
                    name="Base_ctrl_opmode_rsc",
                )
            )
            # To plot the evaluation_status
            for i in range(len(list_passed)):
                list_passed[i] = int(list_passed[i])
            fig.add_trace(
                go.Scatter(
                    x=df_plot["semseg_timestamp_rsc"],
                    y=np.array(list_passed),
                    mode="lines",
                    name="evaluation_status",
                )
            )
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="SemSeg_TimeStamp(us)",
            )
            fig.update_layout(PlotlyTemplate.lgt_tmplt, showlegend=True)
            plots.append(fig)
        else:
            # Set table dataframe
            evaluation_text = (
                f"Evaluation is {test_result}, Input signals {list_of_missing_signals} are not available in bsig file."
            )
            signal_summary = pd.DataFrame(
                {
                    "Evaluation": {
                        "1": eval_0,
                    },
                    "Result": {
                        "1": evaluation_text,
                    },
                    "Verdict": {
                        "1": test_result,
                    },
                }
            )
            # Add the table
            sig_sum = fh.build_html_table(signal_summary)
            plots.append(sig_sum)

        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)
        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1407397"],
            fc.TESTCASE_ID: ["112212"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Ensures that the component provides most confident class is provided for all \
                            the semseg pixels."
            ],
            fc.TEST_RESULT: [test_result],
        }

        self.result.details["Additional_results"] = result_df


@verifies("L3_PCE_1407397")
@testcase_definition(
    name="SWRT_CNC_PCE_SEMSEG_PIXELCLASSINFO_ONRIGHTCAM",
    description="This test ensures that the component provides most confident class is provided for all the semseg \
    pixels.",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class PCESemsegPixelClassInfoOnRightCamera(TestCase):
    """SemsegPixelClassInfo test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PCESemsegClassInfoOnRightCameraTestStep,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.
    """
    # test_bsigs = r"D:\csv's\check_with_mts\2024.09.26_at_11.18.23_camera-mi_020_checkarray_rrec.bsig"
    # test_bsigs = r"D:\csv's\check_with_mts\checkarray.bsig"
    # test_bsigs = r"D:\csv's\2024.08.29_at_13.48.06_camera-mi_13.bsig"
    # test_bsigs = r"D:\csv's\check_with_mts\semseg_imagedata.bsig"
    # test_bsigs = r"D:\csv's\check_with_mts\2024.09.26_at_11.18.23_camera-mi_020_Senseg_for_all_cameras.bsig"
    test_bsigs = r"D:\csv's\2024.12.04_at_14.11.29_camera-mi_9056_R7_SemSeg.bsig"
    debug(
        PCESemsegPixelClassInfoOnRightCamera,
        test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
        kpi_report=False,
        dev_report=True,
    )
    _log.debug("All done.")


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"
    out_folder = working_directory / "out"

    main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)
