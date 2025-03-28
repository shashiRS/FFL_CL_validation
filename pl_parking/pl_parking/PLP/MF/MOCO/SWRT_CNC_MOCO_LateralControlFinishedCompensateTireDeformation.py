"""moco lateral control finished compensate tire deformation"""

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
    calculate_additional_front_steer_angle_request_delta,
    calculate_steer_angle_velocity,
    get_steer_angle_close_to_static_trigger,
    is_not_close_to_requested,
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

ALIAS = "SWRT_CNC_MOCO_LateralControlFinishedCompensateTireDeformation"

""" Steps required to create a new test case:

1. Define required signals in the Signals class


"""


signals_obj = MoCoSignals()


@teststep_definition(step_number=1, name="KPI", description=" ", expected_result=BooleanResult(TRUE))
@register_signals(ALIAS, MoCoSignals)
class Step1(TestStep):
    """moco lateral control finished compensate tire deformation test setup"""

    custom_report = fh.MOCOCustomTeststepReport

    def __init__(self):
        """Initialise the test step"""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")

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

            "Calculate the Steer Angle Velocity"
            df = calculate_steer_angle_velocity(df)

            "Determine steer angle close to static when is triggered"
            df = abs(get_steer_angle_close_to_static_trigger(df))

            df = calculate_additional_front_steer_angle_request_delta(df)

            "Check precondition when steer angle is/are close to requested"
            if (df["is_not_close_to_requested_steer_angle"] == 0).any():

                df["close_to_requested_steer_angle"] = df["is_not_close_to_requested_steer_angle"].map({1: 0, 0: 1})

                df["close_to_requested_steer_angle"].fillna(0, inplace=True)

            "Filter data by  lateral control request"
            df_filtered = df[
                (df["activateLaCtrl"] == 1)
                & (df["laCtrlRequestType"] == constants.MoCo.LaCtrlRequestType.LACTRL_COMF_ANGLE_ADJUSTMENT)
            ]

            if not df_filtered.empty:
                passed = []
                if (df_filtered["steer_angle_close_to_static"] == 1).any() and (df_filtered["close_to_requested_steer_angle"] == 1).any():
                    if (df_filtered["target_value"] == df_filtered["steerAngReqFront_rad"]).any():
                        for _, car_pos_row in df_filtered.iterrows():
                            if (car_pos_row["lateralControlFinished_nu"] == 1):
                                passed.append(True)
                            else:
                                passed.append(False)
                        if all(passed):
                            self.result.measured_result = TRUE
                            test_result = fc.PASS
                            eval_text = "Conditions for finished lateral control are satisfied and lateralControlFinished_nu is set to true."
                        else:
                            self.result.measured_result = FALSE
                            test_result = fc.FAIL
                            eval_text = "Conditions for finished lateral control are satisfied but lateralControlFinished_nu is not set to true for all."

                        eval_0 = " ".join(
                            "Ensure that the component shall output the finished lateral control information (mfControlStatusPort.lateralControlFinished_nu=true),"
                            " when the conditions which indicate a finished lateral control are fulfilled".split()
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
                                y=df["laCtrlRequestType"].values.tolist(),
                                mode="lines",
                                name="laCtrlRequestType",
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
                                y=df["steerAngReqFront_rad"].values.tolist(),
                                mode="lines",
                                name="steerAngReqFront_rad",
                            )
                        )
                        fig.add_trace(
                            go.Scatter(
                                x=df.index.values.tolist(),
                                y=df["steer_angle_delta"].values.tolist(),
                                mode="lines",
                                name="steer_angle_delta",
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
                                y=df["steer_angle_close_to_static"].values.tolist(),
                                mode="lines",
                                name="steer_angle_close_to_static",
                            )
                        )
                        fig.add_trace(
                            go.Scatter(
                                x=df.index.values.tolist(),
                                y=df["lateralControlFinished_nu"].values.tolist(),
                                mode="lines",
                                name="lateralControlFinished_nu",
                            )
                        )
                        fig.add_trace(
                            go.Scatter(
                                x=df.index.values.tolist(),
                                y=df["steerAngReqRaw_rad"].values.tolist(),
                                mode="lines",
                                name="steerAngReqRaw_rad",
                            )
                        )

                        fig.add_trace(
                            go.Scatter(
                                x=df.index.values.tolist(),
                                y=df["target_value"].values.tolist(),
                                mode="lines",
                                name="target_value",
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
                        eval_text = "target value is not set"
                        self.result.measured_result = NAN

                        eval_0 = " ".join(
                            "Ensure that the component shall output the finished lateral control information (mfControlStatusPort.lateralControlFinished_nu=true),"
                            " when the conditions which indicate a finished lateral control are fulfilled".split()
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
                                y=df["laCtrlRequestType"].values.tolist(),
                                mode="lines",
                                name="laCtrlRequestType",
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
                                y=df["steer_angle_delta"].values.tolist(),
                                mode="lines",
                                name="steer_angle_delta",
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
                                y=df["steer_angle_close_to_static"].values.tolist(),
                                mode="lines",
                                name="steer_angle_close_to_static",
                            )
                        )
                        fig.add_trace(
                            go.Scatter(
                                x=df.index.values.tolist(),
                                y=df["lateralControlFinished_nu"].values.tolist(),
                                mode="lines",
                                name="lateralControlFinished_nu",
                            )
                        )
                        fig.add_trace(
                            go.Scatter(
                                x=df.index.values.tolist(),
                                y=df["steerAngReqRaw_rad"].values.tolist(),
                                mode="lines",
                                name="steerAngReqRaw_rad",
                            )
                        )
                        fig.add_trace(
                            go.Scatter(
                                x=df.index.values.tolist(),
                                y=df["target_value"].values.tolist(),
                                mode="lines",
                                name="target_value",
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
                    eval_text = "current steer angle(s) is/are not close to the requested steer angle(s) and is/are not close to static"
                    self.result.measured_result = NAN

                    eval_0 = " ".join(
                        "Ensure that the component shall output the finished lateral control information (mfControlStatusPort.lateralControlFinished_nu=true),"
                            " when the conditions which indicate a finished lateral control are fulfilled".split()
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
                            y=df["laCtrlRequestType"].values.tolist(),
                            mode="lines",
                            name="laCtrlRequestType",
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
                            y=df["steer_angle_delta"].values.tolist(),
                            mode="lines",
                            name="steer_angle_delta",
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
                            y=df["steer_angle_close_to_static"].values.tolist(),
                            mode="lines",
                            name="steer_angle_close_to_static",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["lateralControlFinished_nu"].values.tolist(),
                            mode="lines",
                            name="lateralControlFinished_nu",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df.index.values.tolist(),
                            y=df["steerAngReqRaw_rad"].values.tolist(),
                            mode="lines",
                            name="steerAngReqRaw_rad",
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
                            y=df["target_value"].values.tolist(),
                            mode="lines",
                            name="target_value",
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
                eval_text = "Preconditions not met"
                self.result.measured_result = NAN

                eval_0 = " ".join(
                    "Ensure that the component shall output the finished lateral control information (mfControlStatusPort.lateralControlFinished_nu=true),"
                    " when the conditions which indicate a finished lateral control are fulfilled".split()
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
                        y=df["laCtrlRequestType"].values.tolist(),
                        mode="lines",
                        name="laCtrlRequestType",
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
                        y=df["steer_angle_delta"].values.tolist(),
                        mode="lines",
                        name="steer_angle_delta",
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
                        y=df["steer_angle_close_to_static"].values.tolist(),
                        mode="lines",
                        name="steer_angle_close_to_static",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["lateralControlFinished_nu"].values.tolist(),
                        mode="lines",
                        name="lateralControlFinished_nu",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["steerAngReqRaw_rad"].values.tolist(),
                        mode="lines",
                        name="steerAngReqRaw_rad",
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
                        y=df["target_value"].values.tolist(),
                        mode="lines",
                        name="target_value",
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

@tag("SWRT_CNC_MOCO_LateralControlFinishedCompensateTireDeformation")
@verifies("1974653")
@testcase_definition(
    name="MOCO Lateral Control Finished Compensate Tire Deformation",
    description="Ensure that the component shall output the finished lateral control information (mfControlStatusPort.lateralControlFinished_nu=true),"
                " when the conditions which indicate a finished lateral control are fulfilled.",
    group="steer",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SWRT_CNC_MOCO_LateralControlFinishedCompensateTireDeformation(TestCase):
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
        SWRT_CNC_MOCO_LateralControlFinishedCompensateTireDeformation,
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
