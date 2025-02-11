"""moco velocity limit when wheel closer to stopper"""

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
    calculate_upper_velocity_limit_max_lat_acc,
    calculate_upper_velocity_limit_max_lat_yaw_rate,
    check_active_replan,
    check_preview_distance,
    check_velocity_ramp_up,
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

ALIAS = "SWRT_CNC_MOCO_VelocityLimitWhenWheelCloserToStopper"

""" Steps required to create a new test case:
1. Define required signals in the Signals class
"""
signals_obj = MoCoSignals()


@teststep_definition(step_number=1, name="KPI", description=" ", expected_result=BooleanResult(TRUE))
@register_signals(ALIAS, MoCoSignals)
class Step1(TestStep):
    """moco velocity limit when wheel closer to stopper test setup"""

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
            test_result = fc.INPUT_MISSING
            self.result.measured_result = NAN
            df = self.readers[ALIAS]

            df = check_preview_distance(df)
            df = check_velocity_ramp_up(df)
            df = check_active_replan(df)
            df = calculate_upper_velocity_limit_max_lat_acc(df)
            df = calculate_upper_velocity_limit_max_lat_yaw_rate(df)

            df["check_if_any_wheel_closer"] = df["check_if_any_wheel_closer"].map({True: 1, False: 0})

            "TestStep"
            "Check and filter data by longitudinal control request"
            df_filtered = df[
                (df["activateLoCtrl"] == 1)
                & (df["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_TRAJECTORY)
            ]

            passed = []
            if not df_filtered.empty:
                ## Removed this for erg measurements as in erg files we don't have signal for this parameter so no use to consider this contact value for validation
                ## but need to consider this for rec measurements when required
                # df_filtered["ws_vel_reduced"] = constants.MoCo.Parameter.AP_C_FEAT_WS_VEL_REDUCED_NU
                for _, car_pos_row in df_filtered.iterrows():
                    if car_pos_row["checkReplan"]:
                        continue

                    if car_pos_row["check_if_any_wheel_closer"] and (
                        round(car_pos_row["velocityLimitReq_mps"], 3) != car_pos_row["calculated_velocityLimitReq_mps"]
                    ):
                        passed.append(False)
                    else:
                        passed.append(True)

                if all(passed):
                    self.result.measured_result = TRUE
                    test_result = fc.PASS
                    eval_text = " ".join(
                        f"The component is configured via parameter AP_C_FEAT_WS_VEL_REDUCED_NU ({constants.MoCo.Parameter.AP_C_FEAT_WS_VEL_REDUCED_NU}) and any wheel is closer (<) than "
                        f"AP_C_WFC_WS_VEL_DIST_THRESH_M({constants.MoCo.Parameter.AP_C_WFC_WS_VEL_DIST_THRESH_M})to a wheel stopper, the velocity is limited to upper limit "
                        f"AP_C_WFC_WS_VEL_LIMIT_MPS({constants.MoCo.Parameter.AP_C_WFC_WS_VEL_LIMIT_MPS}).".split()
                    )
                else:
                    self.result.measured_result = FALSE
                    test_result = fc.FAIL
                    eval_text = f"The component is not configured via parameter AP_C_FEAT_WS_VEL_REDUCED_NU ({constants.MoCo.Parameter.AP_C_FEAT_WS_VEL_REDUCED_NU})"

                eval_0 = " ".join(
                    f"Ensure that when the component is configured via parameter AP_C_FEAT_WS_VEL_REDUCED_NU ({constants.MoCo.Parameter.AP_C_FEAT_WS_VEL_REDUCED_NU}) and any wheel is closer (<) than "
                    f"AP_C_WFC_WS_VEL_DIST_THRESH_M({constants.MoCo.Parameter.AP_C_WFC_WS_VEL_DIST_THRESH_M})to a wheel stopper, the velocity is limited to upper limit "
                    f"AP_C_WFC_WS_VEL_LIMIT_MPS({constants.MoCo.Parameter.AP_C_WFC_WS_VEL_LIMIT_MPS}).".split()
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

                fig = get_plot_signals(df)

                plot_titles.append("Graphical Overview")
                plots.append(fig)
                remarks.append("")

                additional_results_dict = {
                    "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)}
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
                eval_text = "Preconditions are not met"
                self.result.measured_result = NAN

                eval_0 = " ".join(
                    f"Ensure that when the component is configured via parameter AP_C_FEAT_WS_VEL_REDUCED_NU ({constants.MoCo.Parameter.AP_C_FEAT_WS_VEL_REDUCED_NU}) and any wheel is closer (<) than "
                    f"AP_C_WFC_WS_VEL_DIST_THRESH_M({constants.MoCo.Parameter.AP_C_WFC_WS_VEL_DIST_THRESH_M})to a wheel stopper, the velocity is limited to upper limit "
                    f"AP_C_WFC_WS_VEL_LIMIT_MPS({constants.MoCo.Parameter.AP_C_WFC_WS_VEL_LIMIT_MPS}).".split()
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
                fig = get_plot_signals(df)
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


def get_plot_signals(df):
    """Plotting Signals"""
    fig = go.Figure()
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
            y=df["loCtrlRequestType"].values.tolist(),
            mode="lines",
            name="loCtrlRequestType",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["velocityLimitReqInterpolTraj_mps"].values.tolist(),
            mode="lines",
            name="velocityLimitReqInterpolTraj_mps",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["velocityLimitReq_mps"].values.tolist(),
            mode="lines",
            name="velocityLimitReq_mps",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["calculated_velocityLimitReq_mps"].values.tolist(),
            mode="lines",
            name="calculated_velocityLimitReq_mps",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["check_if_any_wheel_closer"].values.tolist(),
            mode="lines",
            name="check_if_any_wheel_closer",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["mNumOfReplanCalls"].values.tolist(),
            mode="lines",
            name="mNumOfReplanCalls",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["mReplanSuccessful_nu"].values.tolist(),
            mode="lines",
            name="mReplanSuccessful_nu",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["calculated_driving_resistance_FL"].values.tolist(),
            mode="lines",
            name="calculated_driving_resistance_FL",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["calculated_driving_resistance_RL"].values.tolist(),
            mode="lines",
            name="calculated_driving_resistance_RL",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["calculated_driving_resistance_RR"].values.tolist(),
            mode="lines",
            name="calculated_driving_resistance_RR",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["calculated_driving_resistance_FR"].values.tolist(),
            mode="lines",
            name="calculated_driving_resistance_FR",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["drivingResistanceType_0"].values.tolist(),
            mode="lines",
            name="drivingResistanceType_0",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["drivingResistanceType_1"].values.tolist(),
            mode="lines",
            name="drivingResistanceType_1",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["drivingResistanceType_2"].values.tolist(),
            mode="lines",
            name="drivingResistanceType_2",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["drivingResistanceType_3"].values.tolist(),
            mode="lines",
            name="drivingResistanceType_3",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[df.index.values.min(), df.index.values.max()],
            y=[
                constants.MoCo.Parameter.AP_C_WFC_WS_VEL_DIST_THRESH_M,
                constants.MoCo.Parameter.AP_C_WFC_WS_VEL_DIST_THRESH_M,
            ],
            mode="lines",
            name="AP_C_WFC_WS_VEL_DIST_THRESH_M",
            visible="legendonly",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[df.index.values.min(), df.index.values.max()],
            y=[
                constants.MoCo.Parameter.AP_C_WFC_WS_VEL_LIMIT_MPS,
                constants.MoCo.Parameter.AP_C_WFC_WS_VEL_LIMIT_MPS,
            ],
            mode="lines",
            name="AP_C_WFC_WS_VEL_LIMIT_MPS",
            visible="legendonly",
        )
    )

    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="MTS.Package.Timestamp"
    )
    fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
    return fig


@tag("SWRT_CNC_MOCO_VelocityLimitWhenWheelCloserToStopper")
@verifies("2613878")
@testcase_definition(
    name="MOCO Velocity Limit When Wheel Closer To Stopper",
    description="Ensure that when the component is configured via parameter {AP_C_FEAT_WS_VEL_REDUCED_NU} and any wheel is closer (<) than "
    "{AP_C_WFC_WS_VEL_DIST_THRESH_M} to a wheel stopper, the velocity is limited to upper limit {AP_C_WFC_WS_VEL_LIMIT_MPS}.",
    group="Wheelstopper",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SWRT_CNC_MOCO_VelocityLimitWhenWheelCloserToStopper(TestCase):
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
        SWRT_CNC_MOCO_VelocityLimitWhenWheelCloserToStopper,
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
