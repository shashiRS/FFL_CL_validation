#!/usr/bin/env python3
"""Max velocity steering wheel TestCase."""

import logging
import os
import sys

import pandas as pd
import plotly.graph_objects as go

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", "..", ".."))  # nopep8
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
from tsf.core.common import AggregateFunction, RelationOperator
from tsf.core.results import ExpectedResult, Result
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, calc_table_height

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


SIGNAL_DATA = "MAX_VELOCITY_STEERING_WHEEL"
signal_obj = fh.MfSignals()


@teststep_definition(
    step_number=1,
    name="Max velocity steering wheel",
    description="Absolute steering wheel velocity during parking maneuver should be < 0.38 rad/s.",
    expected_result=ExpectedResult(
        constants.ConstantsMaxSteeringWheelVelocity.THRESHOLD,
        operator=RelationOperator.LESS,
        unit="radps",
        aggregate_function=AggregateFunction.ALL,
    ),
)
@register_signals(SIGNAL_DATA, fh.MfSignals)
class Step1(TestStep):
    """Test Step definition."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self, **kwargs):
        """Process the test result."""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        try:
            df = self.readers[SIGNAL_DATA].signals
            signal_name = signal_obj._properties

            self.test_result = fc.INPUT_MISSING
            verdict_color = "rgb(33,39,43)"  # fc.InputMissing
            # plots and remarks need to have the same length
            plot_titles, plots, remarks = fh.rep([], 3)
            eval_cond = [False] * 3
            park_in_out_mask = None
            state_mask = None
            sg_velocity_angular = "steeringWheelAngleVelocity_radps"
            sg_parksm_cor_status = "ParkSmCoreStatus"
            sg_park_out_in = "headUnitVisu_screen_nu"

            time = df[fh.MfSignals.Columns.TIME]
            state_var = df[sg_parksm_cor_status]
            ang_vel_steer_wheel = df[sg_velocity_angular]
            ppc_parking_mode_in = df[sg_park_out_in].to_numpy()
            ppc_parking_mode_out = df[sg_park_out_in].to_numpy()

            parking_mode_in_mask = ppc_parking_mode_in == constants.HeadUnitVisuPortScreenVal.MANEUVER_ACTIVE
            parking_mode_out_mask = ppc_parking_mode_out == constants.HeadUnitVisuPortScreenVal.MANEUVER_ACTIVE
            park_in_out_mask = parking_mode_in_mask | parking_mode_out_mask
            state_mask = state_var == constants.ParkSmCoreStatus.PERFORM_PARKING
            ang_vel_steer_wheel_filtered = ang_vel_steer_wheel * state_mask * park_in_out_mask

            max_ang_vel_steer_wheel_radps = ang_vel_steer_wheel_filtered.abs().max()

            if park_in_out_mask.any():
                eval_cond[0] = True
            if state_mask.any():
                eval_cond[1] = True
            if max_ang_vel_steer_wheel_radps < constants.ConstantsMaxSteeringWheelVelocity.THRESHOLD:
                eval_cond[2] = True

            if all(eval_cond):
                self.test_result = fc.PASS
                verdict_color = "#28a745"
                # self.result.measured_result = TRUE
            else:
                self.test_result = fc.FAIL
                verdict_color = "#dc3545"
                # self.result.measured_result = FALSE
            self.result.measured_result = Result(max_ang_vel_steer_wheel_radps, unit="radps")

            # Set condition strings
            cond_0 = " ".join(
                f"{signal_name[sg_park_out_in]} or {signal_name[sg_park_out_in]} should be in active                   "
                f"          state({constants.GeneralConstants.ACTIVE_STATE})".split()
            )
            cond_1 = " ".join(
                f"In signal {signal_name[sg_parksm_cor_status]}, the status should be set to                "
                f" PERFORM_PARKING({constants.ParkSmCoreStatus.PERFORM_PARKING}).".split()
            )
            cond_2 = " ".join(
                "The maximum angular velocity of the steering wheel should not exceed the threshold               "
                f" ({constants.ConstantsMaxSteeringWheelVelocity.THRESHOLD} rad/s).".split()
            )

            # # Set table dataframe
            signal_summary = pd.DataFrame(
                {
                    "Condition": {
                        "0": cond_0,
                        "1": cond_1,
                        "2": cond_2,
                    },
                    "Result": {
                        "0": (
                            " ".join("Either of the signals is in active state.".split())
                            if eval_cond[0]
                            else " ".join("Neither of the signals is in active state.".split())
                        ),
                        "1": (
                            " ".join(
                                f"The state PERFORM_PARKING({constants.ParkSmCoreStatus.PERFORM_PARKING})              "
                                "           was found.".split()
                            )
                            if eval_cond[1]
                            else " ".join(
                                f"The state PERFORM_PARKING({constants.ParkSmCoreStatus.PERFORM_PARKING})              "
                                "           was not found.".split()
                            )
                        ),
                        "2": (
                            " ".join("Maximum angular velocity of steering wheel was not exceeded.".split())
                            if eval_cond[2] and eval_cond[1]
                            else (
                                " ".join(
                                    "Maximum angular velocity of steering wheel was exceeded with value =             "
                                    f"            {max_ang_vel_steer_wheel_radps:.5f} rad/s.".split()
                                )
                                if eval_cond[1]
                                else " ".join(
                                    f"The state PERFORM_PARKING({constants.ParkSmCoreStatus.PERFORM_PARKING})          "
                                    "               was not found.".split()
                                )
                            )
                        ),
                    },
                    "Verdict": {
                        "0": "PASSED" if eval_cond[0] else "FAILED",
                        "1": "PASSED" if eval_cond[1] else "FAILED",
                        "2": "PASSED" if eval_cond[2] and eval_cond[1] else "FAILED",
                    },
                }
            )

            # Create table with eval conditions from the summary dict
            sig_sum = go.Figure(
                data=[
                    go.Table(
                        columnwidth=[50, 20, 7],
                        header=dict(
                            values=list(signal_summary.columns),
                            fill_color="rgb(255,165,0)",
                            font=dict(size=12, family="Arial", color="rgb(0,0,0)"),
                            align="center",
                        ),
                        cells=dict(
                            values=[signal_summary[col] for col in signal_summary.columns],
                            height=40,
                            align="center",
                            font=dict(size=12),
                        ),
                    )
                ]
            )
            sig_sum.update_layout(
                constants.PlotlyTemplate.lgt_tmplt, height=calc_table_height(signal_summary["Condition"].to_dict())
            )
            plot_titles.append("Condition Evaluation")
            plots.append(sig_sum)
            remarks.append("")

            if self.test_result == fc.FAIL or bool(constants.GeneralConstants.ACTIVATE_PLOTS):
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=time.tolist(),
                        y=df[sg_parksm_cor_status].values.tolist(),
                        mode="lines",
                        name=signal_name[sg_parksm_cor_status],
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=time.tolist(),
                        y=df[sg_park_out_in].values.tolist(),
                        mode="lines",
                        name=f"{signal_name[sg_park_out_in]}",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=time.tolist(),
                        y=df[sg_park_out_in].values.tolist(),
                        mode="lines",
                        name=f"{signal_name[sg_park_out_in]}",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=time.tolist(),
                        y=df[sg_velocity_angular].values.tolist(),
                        mode="lines",
                        name=f"{signal_name[sg_velocity_angular]}",
                    )
                )

                fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]")
                fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

                plot_titles.append("Graphical overview")
                plots.append(fig)
                remarks.append("")

            for plot in plots:
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)

            additional_results_dict = {
                "Verdict": {"value": self.test_result.title(), "color": verdict_color},
                "Expected [rad/s]": {"value": f"< {constants.ConstantsMaxSteeringWheelVelocity.THRESHOLD}"},
                "Measured [rad/s]": {"value": f"{max_ang_vel_steer_wheel_radps:.5f}"},
            }

            self.result.details["Additional_results"] = additional_results_dict
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@testcase_definition(
    name="MF MAX VELOCITY STEERING WHEEL",
    description="Absolute steering wheel velocity during parking maneuver should be < 0.38 rad/s.",
)
class MaxVelocitySteeringWheel(TestCase):
    """Max Velocity Steering Wheel test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step1,
        ]
