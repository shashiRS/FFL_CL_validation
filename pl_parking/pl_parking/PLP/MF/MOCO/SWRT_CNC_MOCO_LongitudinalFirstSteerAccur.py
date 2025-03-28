"""moco longitudinal first steer accur"""

#!/usr/bin/env python3

import logging
import os
import sys
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
    tag,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.core.utilities import debug

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MoCoSignals
from pl_parking.PLP.MF.MOCO.helpers import (
    calculate_steer_angle_velocity,
    check_hold_request_due_to_steer_angle,
    get_steer_angle_close_to_static_trigger,
    is_not_close_to_requested,
    is_vehicle_in_standstill,
)

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.1"
__status__ = "Development"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ALIAS = "SWRT_CNC_MOCO_LongitudinalFirstSteerAccur"

""" Steps required to create a new test case:

1. Define required signals in the Signals class


"""


signals_obj = MoCoSignals()


@teststep_definition(step_number=1, name="KPI", description=" ", expected_result=BooleanResult(TRUE))
@register_signals(ALIAS, MoCoSignals)
class Step1(TestStep):
    """moco longitudinal first steer accur test setup"""

    custom_report = fh.MOCOCustomTeststepReport

    def __init__(self):
        """Initialsie the test step"""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        active = 1
        try:
            self.result.details.update(
                {
                    "Plots": [],
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            plot_titles, plots, remarks = fh.rep([], 3)
            self.result.measured_result = NAN
            test_result = fc.INPUT_MISSING
            df = self.readers[ALIAS]

            df["is_not_close_to_requested_steer_angle"] = df.apply(
                lambda row: is_not_close_to_requested(
                    row["steerAngFrontAxle_rad"],
                    row["frontSteerAngReq_rad"],
                    (
                        constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_ACCUR_RAD
                        / constants.MoCo.Parameter.AP_V_STEER_RATIO_NU
                    ),
                ),
                axis=1,
            )

            df["steer_angle_difference_rad"] = df["steerAngFrontAxle_rad"] - df["frontSteerAngReq_rad"]
            df["is_not_close_to_requested_steer_angle"] = df["is_not_close_to_requested_steer_angle"].replace(
                {False: 0, True: 1}
            )

            "Verify that the vehicle is in standstill"
            df["calculated_standstill"] = df.apply(
                lambda row: is_vehicle_in_standstill(
                    row["standstillHoldCur_nu"], row["standstillSecureCur_nu"], row["motionStatus_nu"]
                ),
                axis=1,
            )

            "Calculate the Steer Angle Velocity"
            df = calculate_steer_angle_velocity(df)

            "Determine steer angle close to static when is triggered"
            df = get_steer_angle_close_to_static_trigger(df)

            "TestStep"
            "Filter data by longitudinal and lateral control request"

            df["calculated_standstill"] = df["calculated_standstill"].map({True: 1, False: 0})
            df_filtered = df[(df["activateLoCtrl"] == active) & (df["activateLaCtrl"] == active)]

            "Check precondition when steer angle is/are not close to requested"
            passed=[]
            if (df["is_not_close_to_requested_steer_angle"] == 1).any():
                df_filtered["calculated_hold_req_nu"] = df_filtered.apply(
                    lambda row: check_hold_request_due_to_steer_angle(
                        vehicle_standstill=row["calculated_standstill"],
                        not_close_to_requested=row["is_not_close_to_requested_steer_angle"],
                        angle_static=row["angle_close_to_static_triggered"],
                    ),
                    axis=1,
                )
                df["close_to_requested_steer_angle"] = df_filtered["is_not_close_to_requested_steer_angle"].map(
                    {True: 0, False: 1}
                )
                df["calculated_hold_req_nu"] = df_filtered["calculated_hold_req_nu"]
                df["calculated_hold_req_nu"].fillna(0, inplace=True)

                if (df["calculated_hold_req_nu"] == 1).any():
                    for _, car_pos_row in df_filtered.iterrows():
                        if car_pos_row["calculated_hold_req_nu"] == 1 and car_pos_row["holdReq_nu"] == 0:
                            passed.append(False)
                        else:
                            passed.append(True)
                    if all(passed):
                        self.result.measured_result = TRUE
                        test_result = fc.PASS
                        eval_text = "Conditions are satisfied"
                    else:
                        self.result.measured_result = FALSE
                        test_result = fc.FAIL
                        eval_text = "Conditions are not satisfied"

                    eval_0 = " ".join(
                        " Ensure that the component requests to hold the vehicle in standstill in case of current steer angle(s) is/are not "
                        "close to the requested steer angle(s) until current steer angle(s) is/are close to static).".split()
                    )

                    # Set table dataframe
                    signal_summary = pd.DataFrame(
                        {
                            "Evaluation": {
                                "1": eval_0,
                            },
                            "Result": {
                                "1": eval_text,
                            },
                        }
                    )

                    sig_sum = fh.build_html_table(signal_summary)
                    plot_titles.append("")
                    plots.append(sig_sum)
                    remarks.append("")
                    fig = go.Figure()

                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["activateLaCtrl"].values.tolist(),
                            mode="lines",
                            name="activateLaCtrl",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["activateLoCtrl"].values.tolist(),
                            mode="lines",
                            name="activateLoCtrl",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["is_not_close_to_requested_steer_angle"].values.tolist(),
                            mode="lines",
                            name="is_not_close_to_requested_steer_angle",
                        )
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["steerAngFrontAxle_rad"].values.tolist(),
                            mode="lines",
                            name="steerAngFrontAxle_rad",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["frontSteerAngReq_rad"].values.tolist(),
                            mode="lines",
                            name="frontSteerAngReq_rad",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["steer_angle_difference_rad"].values.tolist(),
                            mode="lines",
                            name="steer_angle_difference_rad",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["steer_angle_velocity"].values.tolist(),
                            mode="lines",
                            name="steer_angle_velocity",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["calculated_standstill"].values.tolist(),
                            mode="lines",
                            name="calculated_standstill",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["steer_angle_close_to_static"].values.tolist(),
                            mode="lines",
                            name="steer_angle_close_to_static",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["holdReq_nu"].values.tolist(),
                            mode="lines",
                            name="holdReq_nu",
                        )
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["calculated_hold_req_nu"].values.tolist(),
                            mode="lines",
                            name="calculated_hold_req_nu",
                        )
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=[df.index.values.min(), df.index.values.max()],
                            y=[
                                (
                                    constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_ACCUR_RAD
                                    / constants.MoCo.Parameter.AP_V_STEER_RATIO_NU
                                ),
                                (
                                    constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_ACCUR_RAD
                                    / constants.MoCo.Parameter.AP_V_STEER_RATIO_NU
                                ),
                            ],
                            mode="lines",
                            name="AP_C_PC_FIRST_STEER_ACCUR_RAD",
                            visible="legendonly",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=[df.index.values.min(), df.index.values.max()],
                            y=[
                                constants.MoCo.Parameter.AP_C_PC_MIN_STEER_VEL_RADPS,
                                constants.MoCo.Parameter.AP_C_PC_MIN_STEER_VEL_RADPS,
                            ],
                            mode="lines",
                            name="AP_C_PC_MIN_STEER_VEL_RADPS",
                            visible="legendonly",
                        )
                    )
                    fig.layout = go.Layout(
                        yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="MTS.Package.Timestamp"
                    )
                    fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

                    plot_titles.append("Graphical Overview")
                    plots.append(fig)
                    remarks.append("")

                    additional_results_dict = {
                        "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                        "Percent match [%]": {"value": test_result},
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

                    self.result.details["Additional_results"] = additional_results_dict
                else:
                    test_result = fc.NOT_ASSESSED
                    eval_text = "calculated_hold_req_nu is not set"
                    self.result.measured_result = NAN

                    eval_0 = " ".join(
                        " Ensure that the component requests to hold the vehicle in standstill in case of current steer angle(s) "
                        "is/are not close to the requested steer angle(s) "
                        "until current steer angle(s) is/are close to static).".split()
                    )
                    # Set table dataframe
                    signal_summary = pd.DataFrame(
                        {
                            "Evaluation": {
                                "1": eval_0,
                            },
                            "Result": {
                                "1": eval_text,
                            },
                        }
                    )
                    sig_sum = fh.build_html_table(signal_summary)

                    plot_titles.append("")
                    plots.append(sig_sum)
                    remarks.append("")
                    self.result.details["Step_result"] = test_result
                    plot_titles.append("")
                    remarks.append("")
                    fig = go.Figure()
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["activateLaCtrl"].values.tolist(),
                            mode="lines",
                            name="activateLaCtrl",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["activateLoCtrl"].values.tolist(),
                            mode="lines",
                            name="activateLoCtrl",
                        )
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["is_not_close_to_requested_steer_angle"].values.tolist(),
                            mode="lines",
                            name="is_not_close_to_requested_steer_angle",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["steerAngFrontAxle_rad"].values.tolist(),
                            mode="lines",
                            name="steerAngFrontAxle_rad",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["frontSteerAngReq_rad"].values.tolist(),
                            mode="lines",
                            name="frontSteerAngReq_rad",
                        )
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["angle_close_to_static_triggered"].values.tolist(),
                            mode="lines",
                            name="angle_close_to_static_triggered",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["steer_angle_difference_rad"].values.tolist(),
                            mode="lines",
                            name="steer_angle_difference_rad",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["steer_angle_velocity"].values.tolist(),
                            mode="lines",
                            name="steer_angle_velocity",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["calculated_standstill"].values.tolist(),
                            mode="lines",
                            name="calculated_standstill",
                        )
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["steer_angle_close_to_static"].values.tolist(),
                            mode="lines",
                            name="steer_angle_close_to_static",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["holdReq_nu"].values.tolist(),
                            mode="lines",
                            name="holdReq_nu",
                        )
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["calculated_hold_req_nu"].values.tolist(),
                            mode="lines",
                            name="calculated_hold_req_nu",
                        )
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=[df.index.values.min(), df.index.values.max()],
                            y=[
                                (
                                    constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_ACCUR_RAD
                                    / constants.MoCo.Parameter.AP_V_STEER_RATIO_NU
                                ),
                                (
                                    constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_ACCUR_RAD
                                    / constants.MoCo.Parameter.AP_V_STEER_RATIO_NU
                                ),
                            ],
                            mode="lines",
                            name="AP_C_PC_FIRST_STEER_ACCUR_RAD",
                            visible="legendonly",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=[df.index.values.min(), df.index.values.max()],
                            y=[
                                constants.MoCo.Parameter.AP_C_PC_MIN_STEER_VEL_RADPS,
                                constants.MoCo.Parameter.AP_C_PC_MIN_STEER_VEL_RADPS,
                            ],
                            mode="lines",
                            name="AP_C_PC_MIN_STEER_VEL_RADPS",
                            visible="legendonly",
                        )
                    )
                    fig.layout = go.Layout(
                        yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="MTS.Package.Timestamp"
                    )
                    fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
                    plot_titles.append("Graphical Overview")
                    plots.append(fig)
                    remarks.append("")
                    additional_results_dict = {
                        "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                        "Percent match [%]": {"value": "n/a"},
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

                    self.result.details["Additional_results"] = additional_results_dict

            else:
                test_result = fc.NOT_ASSESSED
                eval_text = "current steer angle(s) is/are close to the requested steer angle(s)"
                self.result.measured_result = NAN

                eval_0 = " ".join(
                    " Ensure that the component requests to hold the vehicle in standstill in case of current steer angle(s) is/are not "
                    "close to the requested steer angle(s) until current steer angle(s) is/are close to static).".split()
                )
                # Set table dataframe
                signal_summary = pd.DataFrame(
                    {
                        "Evaluation": {
                            "1": eval_0,
                        },
                        "Result": {
                            "1": eval_text,
                        },
                    }
                )
                sig_sum = fh.build_html_table(signal_summary)

                plot_titles.append("")
                plots.append(sig_sum)
                remarks.append("")
                self.result.details["Step_result"] = test_result
                plot_titles.append("")
                remarks.append("")
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["activateLaCtrl"].values.tolist(),
                        mode="lines",
                        name="activateLaCtrl",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["activateLoCtrl"].values.tolist(),
                        mode="lines",
                        name="activateLoCtrl",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["steerAngFrontAxle_rad"].values.tolist(),
                        mode="lines",
                        name="steerAngFrontAxle_rad",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["frontSteerAngReq_rad"].values.tolist(),
                        mode="lines",
                        name="frontSteerAngReq_rad",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["steer_angle_difference_rad"].values.tolist(),
                        mode="lines",
                        name="steer_angle_difference_rad",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["steer_angle_velocity"].values.tolist(),
                        mode="lines",
                        name="steer_angle_velocity",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["calculated_standstill"].values.tolist(),
                        mode="lines",
                        name="calculated_standstill",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["angle_close_to_static_triggered"].values.tolist(),
                        mode="lines",
                        name="angle_close_to_static_triggered",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["holdReq_nu"].values.tolist(),
                        mode="lines",
                        name="holdReq_nu",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=[df.index.values.min(), df.index.values.max()],
                        y=[
                            (
                                constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_ACCUR_RAD
                                / constants.MoCo.Parameter.AP_V_STEER_RATIO_NU
                            ),
                            (
                                constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_ACCUR_RAD
                                / constants.MoCo.Parameter.AP_V_STEER_RATIO_NU
                            ),
                        ],
                        mode="lines",
                        name="AP_C_PC_FIRST_STEER_ACCUR_RAD",
                        visible="legendonly",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=[df.index.values.min(), df.index.values.max()],
                        y=[
                            constants.MoCo.Parameter.AP_C_PC_MIN_STEER_VEL_RADPS,
                            constants.MoCo.Parameter.AP_C_PC_MIN_STEER_VEL_RADPS,
                        ],
                        mode="lines",
                        name="AP_C_PC_MIN_STEER_VEL_RADPS",
                        visible="legendonly",
                    )
                )
                fig.layout = go.Layout(
                    yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="MTS.Package.Timestamp"
                )
                fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
                plot_titles.append("Graphical Overview")
                plots.append(fig)
                remarks.append("")
                additional_results_dict = {
                    "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                    "Percent match [%]": {"value": "n/a"},
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

                self.result.details["Additional_results"] = additional_results_dict

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")

@tag("SWRT_CNC_MOCO_LongitudinalFirstSteerAccur")
@verifies("1407125")
@testcase_definition(
    name="MOCO Longitudinal First Steer Accur",
    description="Ensure that the component requests to hold the vehicle in standstill in case of current steer angle(s)"
    " is/are not close to the requested steer angle(s) until current steer angle(s) is/are close to static",
    group="steer",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SWRT_CNC_MOCO_LongitudinalFirstSteerAccur(TestCase):
    """Example test case."""

    custom_report = fh.MOCOCustomTestCase

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            Step1,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.
    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.
    This is only meant to jump start testcase debugging.
    """
    # Define your directory path to your measurements for debugging purposes
    test_bsigs = [r".\absolute_directory_path_to_your_measurement\file.erg"]

    debug(
        SWRT_CNC_MOCO_LongitudinalFirstSteerAccur,
        *test_bsigs,
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
