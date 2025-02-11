#!/usr/bin/env python3
"""Defining  Control Flow in Run operational mode cases"""
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
from pl_parking.PLP.CV.PCE.constants import BaseCtrl, PlotlyTemplate

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "GRAPPA_SIGNALS"

example_obj = ft.PCESignals()


@teststep_definition(
    step_number=1,
    name="SWRT_CNC_PCE_RUNMODETIMESTAMP",
    description="This test step confirms that the component forwards timestamp information from control input to all "
    "of its data output when component is triggered in run operation mode.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ft.PCESignals)
class PCERunmodeTimeStampFWDTestStep(TestStep):
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
        # To check the signals availability.
        # list of cameras
        camera_list = ["fc", "rc", "rsc", "lsc"]
        dict_signal_check = []
        # evaluation description
        evaluation_desc = {}
        evaluation_desc_failed = {}
        for camera in camera_list:
            # evaluation description for each camera
            evaluation_desc[camera] = f"{camera.swapcase()} TimeStamp in run mode"
            evaluation_desc_failed[camera] = f"TimeStamps where the timestamps are not same in {camera.swapcase()}"
            # list the signals needed for test
            dict_signal_check.append(f"detection_results_timestamp_{camera}")
            dict_signal_check.append(f"semseg_timestamp_{camera}")
            dict_signal_check.append(f"Base_ctrl_opmode_{camera}")
            dict_signal_check.append(f"ChipsY_Timestamp_{camera}")
            dict_signal_check.append(f"ChipsUV_Timestamp_{camera}")
        signal_availability, list_of_missing_signals = ft.check_required_signals(dict_signal_check, df)
        # Evaluation of the test case
        eval_0 = "PCE is triggered in run opmode and Timestamp of data outputs == timestamp of relevant data inputs."
        # captures the result of all cameras
        dict_camera_result = {}
        # captures the evaluation of all cameras
        evaluation_result = {}
        # Verdict result of all cameras
        verdict_result = {}
        # check if all the required signals are available to test
        if signal_availability:
            od_invalid_timestamps = {}
            semseg_invalid_timestamps = {}
            # For all the 4 instances
            for camera in camera_list:
                # temp variable to hold the invalid timestamps
                od_temp = []
                semseg_temp = []
                # set all the invalid timestamps initially to None
                od_invalid_timestamps[camera] = None
                semseg_invalid_timestamps[camera] = None
                # filters df for each camera
                df_filtered = df[(df[f"Base_ctrl_opmode_{camera}"] == BaseCtrl.GS_BASE_OM_RUN)]
                df_filtered = df_filtered.drop_duplicates(
                    subset=[f"detection_results_timestamp_{camera}"], keep="last"
                )
                # checks whether the inputs of each camera have same timestamps
                if not df_filtered.empty:
                    # check if data inputs(CHIPSY/CHIPSUV) timestamps are same
                    df_chips_invalid = ft.check_data_input_timestamp(df_filtered, camera)
                    if df_chips_invalid.empty:
                        # perform the following when data inputs have the same timestamps
                        # check if data inputs(CHIPSY/CHIPSUV) and data output(detection_results) timestamps are same
                        df_invalid_od_timestamps = ft.check_detection_results_timestamp(df_filtered, camera)
                        # check if data inputs(CHIPSY/CHIPSUV) and data output(semseg) timestamps are same
                        df_invalid_sem_timestamps = ft.check_semseg_results_timestamp(df_filtered, camera)
                        # capture the mts_ts where data outputs and data inputs don't have the same timestamps to plot
                        # the test fail state in the graph
                        for _, row in df_invalid_od_timestamps.iterrows():
                            od_temp.append(row["mts_ts"])
                        for _, row in df_invalid_sem_timestamps.iterrows():
                            semseg_temp.append(row["mts_ts"])
                        od_invalid_timestamps[camera] = od_temp
                        semseg_invalid_timestamps[camera] = semseg_temp
                        if df_invalid_od_timestamps.empty and df_invalid_sem_timestamps.empty:
                            # Set camera result to True if timestamp at each camera data outputs and relevant data
                            # inputs is same
                            dict_camera_result[camera] = True
                            evaluation_result[camera] = (
                                f"Timestamp of {camera.swapcase()} PCE data outputs \
                                == Timestamp of relevant {camera.swapcase()} data inputs"
                            )
                            verdict_result[camera] = "passed"
                        else:
                            # Set camera result to False if timestamp at each camera data outputs and relevant data
                            # inputs is not same
                            dict_camera_result[camera] = False
                            evaluation_result[camera] = (
                                f"Timestamp of {camera.swapcase()} PCE data outputs \
                                != Timestamp of relevant {camera.swapcase()} data inputs"
                            )
                            verdict_result[camera] = "failed"
                    else:
                        # Set camera result to not assessed when timestamps at data inputs are not same
                        dict_camera_result[camera] = fc.NOT_ASSESSED
                        evaluation_result[camera] = "Timestamps of CHIPS Y != Timestamps of CHIPS UV"
                        verdict_result[camera] = "Not assessed"
                else:
                    # Set camera result to not assessed when component is not triggered in run mode
                    dict_camera_result[camera] = fc.NOT_ASSESSED
                    evaluation_result[camera] = "PCE is not triggered in run mode"
                    verdict_result[camera] = "Not assessed"
            if all(ele is True for ele in dict_camera_result.values()):
                # perform following when timestamp of data outputs and timestamp of relevant inputs is same for all
                # of the camera instances.
                test_result = fc.PASS
                self.result.measured_result = TRUE
            elif any(ele is False for ele in dict_camera_result.values()):
                # perform following when timestamp of data outputs and timestamp of relevant inputs is not same for any
                # of the camera instances.
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
            # plotting the required signals
            for cam in camera_list:
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=df["mts_ts"],
                        y=df[f"detection_results_timestamp_{cam}"],
                        mode="lines",
                        name=f"detection_results_timestamp_{cam}",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df["mts_ts"],
                        y=df[f"semseg_timestamp_{cam}"],
                        mode="lines",
                        name=f"semseg_timestamp_{cam}",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df["mts_ts"],
                        y=df[f"Base_ctrl_opmode_{cam}"],
                        mode="lines",
                        name=f"Base_ctrl_opmode_{cam}",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df["mts_ts"],
                        y=df[f"ChipsY_Timestamp_{cam}"],
                        mode="lines",
                        name=f"ChipsY_Timestamp_{cam}",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df["mts_ts"],
                        y=df[f"ChipsUV_Timestamp_{cam}"],
                        mode="lines",
                        name=f"ChipsUV_Timestamp_{cam}",
                    )
                )
                fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="MTS_TS")
                fig.update_layout(PlotlyTemplate.lgt_tmplt, showlegend=True)
                # add the vertical line to represent the timestamp where the test is failed due to detection results
                # output (timestamps at data_output(detection_results) is not matched with the data inputs(CHIPSY/UV))
                if od_invalid_timestamps[f"{cam}"] is not None:
                    for time_threshold in od_invalid_timestamps[f"{cam}"]:
                        fig.add_vline(
                            x=time_threshold, line_width=0.5, line_dash="dash", line_color="red", annotation_text="od"
                        )
                # add the vertical line to represent the timestamp where the test is failed due to semseg output
                # (timestamps at data_output(detection_results) is not matched with the data inputs(CHIPSY/UV))
                if semseg_invalid_timestamps[f"{cam}"] is not None:
                    for time_threshold in semseg_invalid_timestamps[f"{cam}"]:
                        if time_threshold in od_invalid_timestamps[f"{cam}"]:
                            # if test is failed due to OD and semseg then append the annotation_text with /sem
                            line_text = "     /sem"
                        else:
                            # if test is failed only due to semseg then append the annotation_text with sem
                            line_text = "sem"
                        fig.add_vline(
                            x=time_threshold,
                            line_width=0.5,
                            line_dash="dash",
                            line_color="yellow",
                            annotation_text=line_text,
                        )

                plots.append(fig)
                remarks.append("")

        else:
            # Signals are not available
            test_result = fc.NOT_ASSESSED
            self.result.measured_result = NAN
            self.result.details["Step_result"] = test_result
            evaluation_text = " ".join(
                f"Evaluation is {test_result}, Input signals {list_of_missing_signals} are not available in bsig file.".split()
            )
            signal_summary = pd.DataFrame(
                {
                    "Evaluation": {
                        "1": eval_0,
                    },
                    "Result": {"1": evaluation_text},
                    "Verdict": {
                        "1": test_result,
                    },
                }
            )
            # Add the table
            sig_sum = fh.build_html_table(signal_summary)
            # signal plot
            plot_titles.append("Signal Evaluation")
            plots.append(sig_sum)
            remarks.append("PCE Evaluation")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1407386"],
            fc.TESTCASE_ID: ["36476"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Ensures that the component forwards timestamp information from relevant inputs to all of its data"
                "outputs when component is triggered in run operation mode."
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


@verifies("L3_PCE_1407386")
@testcase_definition(
    name="SWRT_CNC_PCE_ControlFlowRunModeTimestampFwd",
    description="This test ensures that the component forwards timestamp information from relevant inputs to all of its"
    "data outputs when component is triggered in run operation mode.",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class PCERunTimeStampFWD(TestCase):
    """List of control flow of Run operation mode test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PCERunmodeTimeStampFWDTestStep,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.
    """
    """Need to update bsig"""
    test_bsigs = r"D:\csv's\Grappa_bsig_files\2024.12.12_at_12.29.23_camera-mi_9056.bsig"
    debug(
        PCERunTimeStampFWD,
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
