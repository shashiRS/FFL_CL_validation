#!/usr/bin/env python3
"""Defining  SemSeg Calculation test cases"""
import logging
import os
import tempfile
from pathlib import Path

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

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.CV.PCE.ft_helper as ft
from pl_parking.PLP.CV.PCE.constants import BaseCtrl, SigStatus

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "GRAPPA_SIGNALS"

example_obj = ft.PCESignals()


@teststep_definition(
    step_number=1,
    name="SWRT_CNC_PCE_RUNMODESEMSEGCALCULATIONSUCCESS",
    description="This test step confirms that the component component sets SemSeg data output to valid when SemSeg"
    " calculation is done successfully.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ft.PCESignals)
class PCERunModeSemSegCalculationSuccessTestStep(TestStep):
    """Test Step definition."""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        test_result = fc.NOT_ASSESSED  # Result
        plot_titles, plots, remarks = fh.rep([], 3)

        reader = self.readers[SIGNAL_DATA]
        df = reader.as_plain_df
        self.result.measured_result = NAN
        # list of cameras
        camera_list = ["fc", "rc", "rsc", "lsc"]
        # list the signals needed for the test.
        dict_signal_check = []
        # evaluation description
        evaluation_desc = {}
        for camera in camera_list:
            # evaluation description for each camera
            evaluation_desc[camera] = f"{camera.swapcase()} SemSeg signal status in run opmode"
            # list the signals needed for test
            dict_signal_check.append(f"semseg_sig_status_{camera}")
            dict_signal_check.append(f"Base_ctrl_opmode_{camera}")
        signal_availability, list_of_missing_signals = ft.check_required_signals(dict_signal_check, df)
        # captures success/Failure state of the test case
        # Evaluation of the test case
        eval_0 = "PCE is triggered in run opmode and Signal status of SemSeg is OK"
        # captures the result of all cameras
        dict_camera_result = {}
        # captures the evaluation of all cameras
        evaluation_result = {}
        # Verdict result of all cameras
        verdict_result = {}
        # check if all the required signals are available to test
        if signal_availability:
            # perform following when all of signals to test are available
            # For all the 4 instances
            for camera in camera_list:
                # Filters df for 'Base_ctrl_opmode == SigStatus.GS_BASE_OM_RUN'
                df_filtered = df[(df[f"Base_ctrl_opmode_{camera}"] == BaseCtrl.GS_BASE_OM_RUN)]
                # performs following when Base_ctrl_opmode == BaseCtrl.GS_BASE_OM_RUN
                if not df_filtered.empty:
                    # Check signal status of FC semseg
                    if (df_filtered[f"semseg_sig_status_{camera}"] == SigStatus.AL_SIG_STATE_OK).all():
                        # Set camera result to True when signal status on FC SemSeg Data output is ok
                        dict_camera_result[camera] = True
                        evaluation_result[camera] = f"{camera.swapcase()} SemSeg signal status is OK in run mode."
                        verdict_result[camera] = "passed"
                    else:
                        # Set camera result to False when signal status on FC SemSeg Data output is not ok
                        dict_camera_result[camera] = False
                        evaluation_result[camera] = f"{camera.swapcase()} SemSeg signal status is not OK in run mode."
                        verdict_result[camera] = "failed"
                else:
                    # Set fc_result to not assessed when component is not triggered in run mode
                    dict_camera_result[camera] = fc.NOT_ASSESSED
                    evaluation_result[camera] = "PCE is not triggered in run mode"
                    verdict_result[camera] = "Not assessed"
            # check calculation status of all camera instances
            if all(ele is True for ele in dict_camera_result.values()):
                # perform following when signal status of SemSeg is OK for all the camera instances
                # sets test to Pass when signal status of SemSeg is OK
                test_result = fc.PASS
                self.result.measured_result = TRUE
            elif any(ele is False for ele in dict_camera_result.values()):
                # perform following when signal status of SemSeg is not OK for any of the camera instances
                # sets test to Fail when signal status of SemSeg is not OK
                test_result = fc.FAIL
                self.result.measured_result = FALSE
            else:
                # perform following when precondition is not met for any camera instance
                test_result = fc.NOT_ASSESSED
                self.result.measured_result = NAN
                self.result.details["Step_result"] = test_result
            # Set table dataframe
            signal_summary = pd.DataFrame(
                {
                    "Evaluation": evaluation_desc.values(),
                    "Result": evaluation_result.values(),
                    "Verdict": verdict_result.values(),
                }
            )
            # Add the table
            sig_sum = fh.build_html_table(signal_summary)
            # signal plot
            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append("")
            # plot the signals needed
            fig = go.Figure()
            for cam in camera_list:
                pce_data = df[[f"semseg_sig_status_{cam}", f"Base_ctrl_opmode_{cam}"]]
                for camera, _ in pce_data.items():
                    fig.add_trace(
                        go.Scatter(
                            x=list(range(len(df[camera]))),
                            y=pce_data[camera].values.tolist(),
                            mode="lines",
                            name=f"{camera}",
                        )
                    )
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Frames")
            plots.append(fig)
            remarks.append("")
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
        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1407403", "1407389"],
            fc.TESTCASE_ID: ["55117"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Ensures that the component sets SemSeg output state to valid when SemSeg calculation is done "
                "successfully.",
            ],
            fc.TEST_RESULT: [test_result],
        }

        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = result_df


@verifies("L3_PCE_1407403, L3_PCE_1407389")
@testcase_definition(
    name="SWRT_CNC_PCE_SemSegCalculationSignalSuccess",
    description="Ensures that the component sets SemSeg output state to valid when SemSeg calculation is done "
    "successfully.",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class PCERunModeSemSegCalculationSuccess(TestCase):
    """ListofParkingMarkings test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PCERunModeSemSegCalculationSuccessTestStep,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.
    """
    """Need to update bsig"""
    test_bsigs = r"V:\Grappa_bsig's\2024.09.26_at_11.18.23_camera-mi_020.bsig"
    debug(
        PCERunModeSemSegCalculationSuccess,
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
