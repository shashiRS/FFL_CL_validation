#!/usr/bin/env python3
"""Performance Tests for AP"""
import logging
import os
import sys
from abc import abstractmethod

import plotly.graph_objects as go
from tsf.core.results import DATA_NOK, FALSE, NAN, Result
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))  # nopep8
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
import pl_parking.common_ft_helper as fh  # nopep8
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, MfSignals

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

MF_AUP_SIGNALS = "MF_AUP_CORE"
signals_obj = MfSignals()


class BaseTeststep(TestStep):
    """Teststep that contains all generic functions that can be used by other test steps"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initializes the class instance with a default evaluation comment."""
        self.comment = "No problems during evaluation"
        super().__init__()

    @abstractmethod
    def process(self, **kwargs):
        """
        Abstract method to be implemented by subclasses for processing data.

        Parameters:
            **kwargs: Additional keyword arguments for processing.

        Returns:
            None
        """
        pass

    def is_end_position_reached_without_collision(self, signals):
        """
        Check if the end position is reached without collision.

        This method checks if the end position is reached without any collision during the maneuvering.

        Parameters:
            signals (DataFrame): A DataFrame containing signals related to the maneuvering.

        Returns:
            bool: True if the end position is reached without collision, False otherwise.
        """
        ap_state = signals[MfSignals.Columns.APSTATE]
        collision_count = signals[MfSignals.Columns.COLLISIONCOUNT]
        reached_status = signals[MfSignals.Columns.REACHEDSTATUS]

        is_ap_active = ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN
        collision_count_ap_active = collision_count.loc[is_ap_active].diff().cumsum()
        is_reached = reached_status > 0

        if ~is_ap_active.any():
            self.comment = (
                f"Evaluation not possible, Maneuvering function not active. "
                f"Signal '{signals_obj._properties[MfSignals.Columns.APSTATE]}' was "
                f"never '=={constants.GeneralConstants.AP_AVG_ACTIVE_IN}'"
            )
            return False
        elif (collision_count_ap_active > 0).any():
            self.comment = "Collision occured, test failed."
            return False

        elif ~is_reached.any():
            self.comment = (
                f"Evaluation not possible, {signals_obj._properties[MfSignals.Columns.REACHEDSTATUS]} "
                f"was not > 0 for 0.8s."
            )
            return False

        return True

    def create_report_data(self, plot_signals, time_s, signal_summary, remark):
        """
        Create data for generating a report.

        This method generates data necessary for creating a report including plot signals,
        time values, signal summary, and remarks.

        Parameters:
            plot_signals (dict): A dictionary containing plot signals.
            time_s (list): A list of time values.
            signal_summary (dict): A dictionary containing signal summaries.
            remark (str): A remark associated with the report data.

        Returns:
            None
        """
        plot_titles = []
        plots = []
        remarks = []

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plots.append(self.sig_sum)
        plot_titles.append("")
        remarks.append("")

        if self.result.measured_result in [FALSE, NAN, DATA_NOK] or bool(constants.GeneralConstants.ACTIVATE_PLOTS):
            self.fig = go.Figure()
            for sig_name, sig_values in plot_signals.items():
                self.fig.add_trace(go.Scatter(x=time_s, y=sig_values, mode="lines", name=sig_name))

            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            plots.append(self.fig.to_html(full_html=False, include_plotlyjs=False))
            plot_titles.append("")
            remarks.append("")

        # plots and remarks need to have the same length
        self.result.details["Plots"] = plots
        self.result.details["Plot_titles"] = plot_titles
        self.result.details["Remarks"] = remarks
        self.result.details["file_name"] = os.path.basename(self.artifacts[0].file_path)


class GenericPositionTeststep(BaseTeststep):
    """Generic processing of checking position target deviation"""

    def process(self, evaluated_signal_name, threshold_signal_name, **kwargs):
        """
        Process evaluated signals to determine if end position is reached without collision.

        Parameters:
            evaluated_signal_name (str): Name of the evaluated signal.
            threshold_signal_name (str): Name of the threshold signal.

        Returns:
            None
        """
        _log.debug("Starting processing...")

        self.result.measured_result = DATA_NOK

        signals = self.readers[MF_AUP_SIGNALS].signals
        time_s = signals[MfSignals.Columns.TIME]
        reached_status = signals[MfSignals.Columns.REACHEDSTATUS]
        evaluated_signal = signals[evaluated_signal_name]
        threshold_signal = signals[threshold_signal_name]

        is_reached = reached_status > 0
        is_reached_duration = time_s.diff().cumsum() - time_s.diff().cumsum().where(~is_reached).ffill().fillna(0)

        max_deviation_from_target = None

        if self.is_end_position_reached_without_collision(signals):
            reached_duration_threshold = constants.GeneralConstants.T_POSE_REACHED
            t_duration_threshold = time_s.loc[is_reached_duration > reached_duration_threshold].iloc[0]
            t_is_reached = t_duration_threshold - constants.GeneralConstants.T_POSE_REACHED

            signals_reached_range = signals.loc[time_s >= t_is_reached]

            evaluated_signal_in_reached_range = signals_reached_range[evaluated_signal_name]
            max_deviation_from_target = evaluated_signal_in_reached_range.max()
            self.result.measured_result = Result(max_deviation_from_target)

        signal_summary = {evaluated_signal_name: f"Value: {max_deviation_from_target}. {self.comment}"}
        remark = (
            "Check that after the target has reached the desired position "
            f" ({signals_obj._properties[MfSignals.Columns.REACHEDSTATUS]} "
            f"> 0 for 0.8s), the deviations to target position are below thresholds."
        )
        plot_signals = {
            MfSignals.Columns.REACHEDSTATUS: reached_status,
            evaluated_signal_name: evaluated_signal,
            threshold_signal_name: threshold_signal,
            MfSignals.Columns.COLLISIONCOUNT: signals[MfSignals.Columns.COLLISIONCOUNT],
        }

        self.create_report_data(plot_signals, time_s, signal_summary, remark)


@teststep_definition(
    step_number=1,
    name="Longitudinal Position Check",
    description="Check the deviations from longitudinal target position after finishing the parking maneuver.",
)
@register_signals(MF_AUP_SIGNALS, MfSignals)
class AupPerformanceLongPosition(GenericPositionTeststep):
    """Check the deviations from longitudinal target position after finishing the parking maneuver."""

    def process(self, **kwargs):
        """Evaluate longitudinal target position deviations."""
        evaluated_signal_name = MfSignals.Columns.LONGDISTTOTARGET
        threshold_signal_name = MfSignals.Columns.LONGMAXDEVIATION
        super().process(evaluated_signal_name, threshold_signal_name)


@teststep_definition(
    step_number=2,
    name="Lateral Position Check",
    description="Check the deviations from lateral target position after finishing the parking maneuver.",
)
@register_signals(MF_AUP_SIGNALS, MfSignals)
class AupPerformanceLatPosition(GenericPositionTeststep):
    """Check the deviations from lateral target position after finishing the parking maneuver."""

    def process(self, **kwargs):
        """Evaluate longitudinal target position deviations."""
        evaluated_signal_name = MfSignals.Columns.LATDISTTOTARGET
        threshold_signal_name = MfSignals.Columns.LATMAXDEVIATION
        super().process(evaluated_signal_name, threshold_signal_name)


@teststep_definition(
    step_number=3,
    name="Yaw Position Check",
    description="Check the deviations from yaw target position after finishing the parking maneuver.",
)
@register_signals(MF_AUP_SIGNALS, MfSignals)
class AupPerformanceYawPosition(GenericPositionTeststep):
    """Check the deviations from yaw target position after finishing the parking maneuver."""

    def process(self, **kwargs):
        """Evaluate yaw target position deviations."""
        evaluated_signal_name = MfSignals.Columns.YAWDIFFTOTARGET
        threshold_signal_name = MfSignals.Columns.YAWMAXDEVIATION
        super().process(evaluated_signal_name, threshold_signal_name)


@teststep_definition(
    step_number=4,
    name="Maneuvering Time",
    description="Check the duration of the parking maneuver.",
)
@register_signals(MF_AUP_SIGNALS, MfSignals)
class AupPerformanceManeuveringTime(BaseTeststep):
    """Check the duration of the parking maneuver."""

    def process(self, **kwargs):
        """Evaluate maneuvering duration and generate a report."""
        _log.debug("Starting processing...")
        self.result.measured_result = DATA_NOK

        signals = self.readers[MF_AUP_SIGNALS].signals
        time_s = signals[MfSignals.Columns.TIME]
        ap_state = signals[MfSignals.Columns.APSTATE]
        ap_maneuver_duration = None

        if self.is_end_position_reached_without_collision(signals):
            ap_start_ts = time_s[ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN].iloc[0]
            ap_end_ts = time_s[ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN].iloc[-1]
            ap_maneuver_duration = ap_end_ts - ap_start_ts
            self.result.measured_result = Result(ap_maneuver_duration)

        signal_summary = {"Maneuvering Time": f"Value: {ap_maneuver_duration}. {self.comment}"}
        remark = (
            f"Check that the duration of {signals_obj._properties[MfSignals.Columns.APSTATE]} "
            f"being in state 3 is less than a specific threshold"
        )
        plot_signals = {
            MfSignals.Columns.REACHEDSTATUS: signals[MfSignals.Columns.REACHEDSTATUS],
            MfSignals.Columns.APSTATE: ap_state,
            MfSignals.Columns.COLLISIONCOUNT: signals[MfSignals.Columns.COLLISIONCOUNT],
        }
        self.create_report_data(plot_signals, time_s, signal_summary, remark)


@teststep_definition(
    step_number=5,
    name="Number of Strokes",
    description="Check the number of strokes of the parking maneuver.",
)
@register_signals(MF_AUP_SIGNALS, MfSignals)
class AupPerformanceNumberStrokes(BaseTeststep):
    """Check the number of strokes of the parking maneuver."""

    def process(self, **kwargs):
        """Evaluate maximum number of strokes and generate a report."""
        _log.debug("Starting processing...")
        self.result.measured_result = DATA_NOK

        signals = self.readers[MF_AUP_SIGNALS].signals
        time_s = signals[MfSignals.Columns.TIME]

        number_of_strokes = signals[MfSignals.Columns.NUMBEROFSTROKES]
        max_number_of_strokes = number_of_strokes.max()

        if self.is_end_position_reached_without_collision(signals):
            self.result.measured_result = Result(max_number_of_strokes)

        signal_summary = {"Maximum number of Strokes": f"Value: {max_number_of_strokes}. {self.comment}"}
        remark = (
            f"Check that the number of {signals_obj._properties[MfSignals.Columns.NUMBEROFSTROKES]} "
            f"is less than a specific threshold."
        )
        plot_signals = {
            MfSignals.Columns.REACHEDSTATUS: signals[MfSignals.Columns.REACHEDSTATUS],
            MfSignals.Columns.NUMBEROFSTROKES: number_of_strokes,
            MfSignals.Columns.COLLISIONCOUNT: signals[MfSignals.Columns.COLLISIONCOUNT],
        }
        self.create_report_data(plot_signals, time_s, signal_summary, remark)


@verifies("req-001")
@testcase_definition(
    name="Performance Tests for AP",
    description=(
        "Evaluate performance of the AP function with respect to the metrics "
        "target position deviation, maneuvering time and number of strokes"
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
class ApPerformance(TestCase):
    """Test case for evaluating performance."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Return the test steps for evaluating the performance of AP functions."""
        return [
            AupPerformanceLongPosition,
            AupPerformanceLatPosition,
            AupPerformanceYawPosition,
            AupPerformanceManeuveringTime,
            AupPerformanceNumberStrokes,
        ]
