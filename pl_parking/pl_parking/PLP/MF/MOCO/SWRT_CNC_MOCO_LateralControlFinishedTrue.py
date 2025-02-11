"""moco lateral control finished true"""

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

ALIAS = "SWRT_CNC_MOCO_LateralControlFinishedTrue"

""" Steps required to create a new test case:

1. Define required signals in the Signals class


"""


signals_obj = MoCoSignals()


@teststep_definition(step_number=1, name="KPI", description=" ", expected_result=BooleanResult(TRUE))
@register_signals(ALIAS, MoCoSignals)
class Step1(TestStep):
    """moco lateral control finished true"""

    custom_report = fh.MOCOCustomTeststepReport

    def __init__(self):
        """Initialsie the test step"""
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
                    row["steerAngReqRaw_rad"],
                    (
                        constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_ACCUR_RAD
                        / constants.MoCo.Parameter.AP_V_STEER_RATIO_NU
                    ),
                ),
                axis=1,
            )

            df["steer_angle_difference_rad"] = df["steerAngFrontAxle_rad"] - df["steerAngReqRaw_rad"]
            df["is_not_close_to_requested_steer_angle"] = df["is_not_close_to_requested_steer_angle"].replace(
                {False: 0, True: 1}
            )

            "Calculate the Steer Angle Velocity"
            df = calculate_steer_angle_velocity(df)

            "Determine steer angle close to static when is triggered"
            df = get_steer_angle_close_to_static_trigger(df)

            "Check precondition when steer angle is/are not close to requested"
            if (df["is_not_close_to_requested_steer_angle"] == 1).any():
                "Filtering for data when steer angle is/are close to requested"
                df["close_to_requested_steer_angle"] = df["is_not_close_to_requested_steer_angle"].map({1: 0, 0: 1})
                df["close_to_requested_steer_angle"].fillna(0, inplace=True)

            "TestStep"
            "Filter data by lateral control request and lateral operation mode control by path"
            df_filtered = df[
                (df["activateLaCtrl"] == 1)
                & (df["laCtrlRequestType"] == constants.MoCo.LaCtrlRequestType.LACTRL_BY_TRAJECTORY)
            ]

            df_filtered["angle_close_to_static_triggered"] = df["angle_close_to_static_triggered"]
            df_filtered["angle_close_to_static_triggered"].fillna(0, inplace=True)

            df_filtered["close_to_requested_steer_angle"] = df["close_to_requested_steer_angle"]
            df_filtered["close_to_requested_steer_angle"].fillna(0, inplace=True)

            passed = []
            df_filtered["Pass/Fail"] = 0
            new_df_filtered = df_filtered[
                (df_filtered["angle_close_to_static_triggered"] == 1)
                & (df_filtered["close_to_requested_steer_angle"] == 1)
            ]
            if len(new_df_filtered) > 0:
                for _, car_pos_row in new_df_filtered.iterrows():
                    if car_pos_row["lateralControlFinished_nu"] == 1:
                        passed.append(True)
                    else:
                        passed.append(False)

                "For plotting"
                df["lateralControlFinished_nu_filtered"] = new_df_filtered["lateralControlFinished_nu"]
                df["lateralControlFinished_nu_filtered"].fillna(0, inplace=True)

                if all(passed):
                    self.result.measured_result = TRUE
                    test_result = fc.PASS
                    eval_text = " ".join(
                        f"Current steer angle is close to Requested steer angle and "
                        f"current steer angle(s) is/are close to static,"
                        f"lateralControlFinished_nu is True, Satisfied the requirement"
                        f"Conditions: {test_result}.".split()
                    )
                else:
                    self.result.measured_result = FALSE
                    test_result = fc.FAIL
                    eval_text = " ".join(f"Conditions not satisfied." f"{test_result}.".split())

                eval_0 = " ".join(
                    " If the current steer angle(s) is/are close to static and is/are close to the requested steer angle(s), "
                    "ensure that the component shall output the finished lateral control information(mfControlStatusPort.lateralControlFinished_nu=true)".split()
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
                        y=df["close_to_requested_steer_angle"].values.tolist(),
                        mode="lines",
                        name="close_to_requested_steer_angle",
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
                        y=df["lateralControlFinished_nu_filtered"].values.tolist(),
                        mode="lines",
                        name="lateralControlFinished_nu_filtered",
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
                        y=df["steer_angle_velocity"].values.tolist(),
                        mode="lines",
                        name="steer_angle_velocity",
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
                        y=df["steerAngReqRaw_rad"].values.tolist(),
                        mode="lines",
                        name="steerAngReqRaw_rad",
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
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["laCtrlRequestType"].values.tolist(),
                        mode="lines",
                        name="laCtrlRequestType",
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
                eval_text = "Condition not satisfied"
                self.result.measured_result = NAN

                eval_0 = " ".join(
                    " If the current steer angle(s) is/are close to static and is/are close to the requested steer angle(s), ensure that the component "
                    " shall output the finished lateral control information(mfControlStatusPort.lateralControlFinished_nu=true).".split()
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
                        y=df["steerAngReqRaw_rad"].values.tolist(),
                        mode="lines",
                        name="steerAngReqRaw_rad",
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
                        y=df["lateralControlFinished_nu"].values.tolist(),
                        mode="lines",
                        name="lateralControlFinished_nu",
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
                        y=df["steerAngFrontAxle_rad"].values.tolist(),
                        mode="lines",
                        name="steerAngFrontAxle_rad",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["laCtrlRequestType"].values.tolist(),
                        mode="lines",
                        name="laCtrlRequestType",
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


@tag("SWRT_CNC_MOCO_LateralControlFinishedTrue")
@verifies("1407010")
@testcase_definition(
    name="MOCO Lateral Control Finished True",
    description="If the current steer angle(s) is/are close to static and is/are close to the requested steer angle(s), "
    "ensure that the component shall output the finished lateral control information(mfControlStatusPort.lateralControlFinished_nu=true)",
    group="steer",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SWRT_CNC_MOCO_LateralControlFinishedTrue(TestCase):
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
        SWRT_CNC_MOCO_LateralControlFinishedTrue,
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
