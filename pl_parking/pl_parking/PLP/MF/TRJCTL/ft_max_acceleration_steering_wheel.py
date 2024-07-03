#!/usr/bin/env python3
"""Max acceleration steering wheel TestCase."""

import logging
import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.signal import iirfilter, sosfiltfilt

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", "..", ".."))  # nopep8
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
# PlotlyTemplate, ParkingModes,LateralErrorConstants,GeneralConstants
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

SIGNAL_DATA = "ACCELERATION_STEERING_WHEEL"
signal_obj = fh.MfSignals()


@teststep_definition(
    step_number=1,
    name="Max acceleration steering wheel",
    description="Check that during parking maneuver, the absolute steering wheel acceleration is below the threshold.",
    expected_result=ExpectedResult(
        constants.ConstantsMaxSteeringWheelAcc.THRESHOLD,
        operator=RelationOperator.LESS,
        unit="radps",
        aggregate_function=AggregateFunction.MEDIAN,
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

    def __calc_angular_accel(self, time_stamp_us, ang_vel, TIME_STEP_US, CUTOFF_FREQ):
        """Calculate angular acceleration from angular velocity, resampling and filtering it.

        :param time_stamp_us: time stamp signal in microsends
        :param ang_vel: angular velocity signal
        :param constants.ConstantsMaxSteeringWheelAcc.TIME_STEP_US: time step used for resampling of the data
        :param cuttoff_freq: cuttoff frequency used for filtering the angular acceleration
        :return ang_accel_resampl: angular acceleration

        """
        # Calculate angular acceleration of the steering wheel
        time_diff_s = 0.01
        ang_vel_diff = ang_vel.diff()
        ang_accel_calc = ang_vel_diff / time_diff_s
        ang_accel_calc.values[0] = 0

        # Resampling the angular acceleration of the steering wheel
        # ang_accel_resampl = self.__resampling_data(ang_accel_calc, TIME_STEP_US)
        ang_accel_resampl = ang_accel_calc

        # Filtering the angular acceleration of the steering wheel
        sample_freq = 1 / TIME_STEP_US * constants.GeneralConstants.US_IN_S
        ang_accel_resampl = self.__iir_sos_low_pass_filter(ang_accel_resampl, CUTOFF_FREQ, sample_freq)

        return ang_accel_resampl

    @staticmethod
    def __iir_sos_low_pass_filter(signal, CUTOFF_FREQ, sample_freq, filter_order=1):
        """Filtering signal: -  iirfilter filter form scipy.signal package
                              -  sosfiltfilt from scipy.signal package used for generation of the
                                    filtered signal.

        :param signal: signal which will be filtered
        :param cuttoff_freq: cuttoff frequency used for filtering
        :param sample_freq: sample frequency
        :filter_order: the order of the filter
        :return signal_filtered: signal filtered
        """
        critical_freq = 2 * CUTOFF_FREQ / sample_freq
        sos = iirfilter(filter_order, critical_freq, btype="lowpass", output="sos")
        signal_filtered = sosfiltfilt(sos, signal)

        return signal_filtered

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
            eval_cond = [False] * 5

            parking_mode_in_mask = None
            parking_mode_out_mask = None
            state_mask = None
            parking_filter = None
            time = None

            sg_velocity_angular = "steeringWheelAngleVelocity_radps"
            sg_parksm_cor_status = "ParkSmCoreStatus"
            sg_park_out_in = "headUnitVisu_screen_nu"

            time = df[fh.MfSignals.Columns.TIME]

            state_var = df[sg_parksm_cor_status]
            ang_vel_steer_wheel = df[sg_velocity_angular]
            ppc_parking_mode_in = df[sg_park_out_in].to_numpy()
            ppc_parking_mode_out = df[sg_park_out_in].to_numpy()
            time_stamp_us = pd.Series(state_var.index, index=state_var.index)

            # Calculate angular acceleration of the steering wheel

            ang_accel_steer_wheel = self.__calc_angular_accel(
                time_stamp_us,
                ang_vel_steer_wheel,
                constants.ConstantsMaxSteeringWheelAcc.TIME_STEP_US,
                constants.ConstantsMaxSteeringWheelAcc.CUTOFF_FREQ,
            )

            # Filtering the signals to obtain the values only when ego is performing park_in/park_out
            parking_mode_in_mask = ppc_parking_mode_in == constants.GeneralConstants.ACTIVE_STATE
            parking_mode_out_mask = ppc_parking_mode_out == constants.GeneralConstants.ACTIVE_STATE
            state_mask = state_var == constants.ParkSmCoreStatus.PERFORM_PARKING
            parking_filter = state_mask & (parking_mode_in_mask | parking_mode_out_mask)

            # # Resampling the filter signal for performing parking in or out
            # parking_filter_resampl = self.__resampling_data(
            #     parking_filter, constants.ConstantsMaxSteeringWheelAcc.TIME_STEP_US, signal_type='filter')
            ang_accel_steer_wheel_filtered = ang_accel_steer_wheel * state_mask

            max_ang_accel_steer_wheel_radps = np.max(np.abs(ang_accel_steer_wheel_filtered))

            if (parking_mode_in_mask | parking_mode_out_mask).any():
                eval_cond[0] = True
            if state_mask.any():
                eval_cond[1] = True
            if parking_filter.any():
                eval_cond[2] = True
            if pd.DataFrame(parking_filter).any().values:
                eval_cond[3] = True
            if max_ang_accel_steer_wheel_radps < constants.ConstantsMaxSteeringWheelAcc.THRESHOLD:
                eval_cond[4] = True

            if all(eval_cond):
                self.test_result = fc.PASS
                verdict_color = "#28a745"
                # self.result.measured_result = TRUE
            else:
                self.test_result = fc.FAIL
                verdict_color = "#dc3545"
                # self.result.measured_result = FALSE
            self.result.measured_result = Result(max_ang_accel_steer_wheel_radps, unit="radps")

            # Set condition strings
            cond_0 = " ".join(
                f"{signal_name[sg_park_out_in]} or {signal_name[sg_park_out_in]} should be in active                "
                f" state({constants.GeneralConstants.ACTIVE_STATE})".split()
            )
            cond_1 = " ".join(
                f"In signal {signal_name[sg_parksm_cor_status]}, the status should be set to                "
                f" PERFORM_PARKING({constants.ParkSmCoreStatus.PERFORM_PARKING}).".split()
            )
            cond_2 = " ".join("The conditions from above should be true at the same time.".split())

            cond_3 = " ".join(
                "Maximum absolute steering wheel acceleration should not exceed the threshold                "
                f" ({constants.ConstantsMaxSteeringWheelAcc.THRESHOLD} rad/s) when the above conditions                "
                " are true.".split()
            )  # value result after some calc

            # # Set table dataframe
            signal_summary = pd.DataFrame(
                {
                    "Condition": {
                        "0": cond_0,
                        "1": cond_1,
                        "2": cond_2,
                        "3": cond_3,
                    },
                    "Result": {
                        "0": (
                            " ".join("Park in is in active state.".split())
                            if sg_park_out_in
                            else (
                                " ".join("Park out is in active state.".split())
                                if sg_park_out_in
                                else " ".join("Neither of the signals is in active state.".split())
                            )
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
                            " ".join("Both conditions were fulfilled.".split())
                            if eval_cond[2]
                            else (
                                " ".join("The first condition passed while second one failed.".split())
                                if not eval_cond[1] and eval_cond[0]
                                else (
                                    " ".join("The first condition failed while second one passed.".split())
                                    if eval_cond[1] and not eval_cond[0]
                                    else " ".join("Both conditions failed.".split())
                                )
                            )
                        ),
                        "3": (
                            " ".join("The threshold was not exceeded.".split())
                            if eval_cond[4] and eval_cond[2]
                            else (
                                " ".join(
                                    "The threshold was exceeded with value                        ="
                                    f" {max_ang_accel_steer_wheel_radps:.2f} rad/s.".split()
                                )
                                if eval_cond[2]
                                else " ".join(
                                    "The signal was not set to                        "
                                    f" PERFORM_PARKING({constants.ParkSmCoreStatus.PERFORM_PARKING})".split()
                                )
                            )
                        ),
                    },
                    "Verdict": {
                        "0": "PASSED" if eval_cond[0] else "FAILED",
                        "1": "PASSED" if eval_cond[1] else "FAILED",
                        "2": "PASSED" if eval_cond[2] else "FAILED",
                        "3": "PASSED" if eval_cond[4] and eval_cond[2] else "FAILED",
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
                fig.add_trace(
                    go.Scatter(x=time.tolist(), y=ang_accel_steer_wheel, mode="lines", name="Angular Acceleration")
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
                "Expected [rad/s^2]": {"value": f"< {constants.ConstantsMaxSteeringWheelAcc.THRESHOLD}"},
                "Measured [rad/s^2]": {"value": f"{max_ang_accel_steer_wheel_radps:.2f}"},
            }

            self.result.details["Additional_results"] = additional_results_dict
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@testcase_definition(
    name="MF MAX ACCELERATION STEERING WHEEL",
    description="Check that during parking maneuver, the absolute steering wheel acceleration is below the threshold.",
)
class MaxAccSteeringWheel(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step1,
        ]
