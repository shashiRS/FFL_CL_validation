"""TAPOSD functional test"""

import logging
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import plotly.graph_objects as go

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.core.utilities import debug

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport
from pl_parking.PLP.MF.constants import ConstantsTaposd, GeneralConstants, HeadUnitVisuPortScreenVal, PlotlyTemplate

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


SIGNAL_DATA = "MF_TAPOSD"
example_obj = fh.MfSignals()


class StoreStepResults:
    """Initializes variables for multiple steps and provides a method
    to check their status and return corresponding results and color codes.
    """

    def __init__(self):
        """Initialize object attributes."""
        self.step_1 = fc.INPUT_MISSING
        self.step_2 = fc.INPUT_MISSING
        self.step_3 = fc.INPUT_MISSING

    def check_result(self):
        """
        The function `check_result` checks the status of multiple steps and returns a corresponding result and color code.
        :return: The `check_result` method is returning a tuple with two values. The first value is one of the constants
        `fc.PASS`, `fc.INPUT_MISSING`, `fc.NOT_ASSESSED`, or `fc.FAIL` based on the conditions checked in the method. The
        second value is a color code represented as a string.
        """
        if self.step_1 == fc.PASS and self.step_2 == fc.PASS:
            # if self.step_1 == fc.PASS and self.step_2 == fc.PASS and self.step_3 == fc.PASS:
            return fc.PASS, "#28a745"
        elif self.step_1 == fc.INPUT_MISSING or self.step_2 == fc.INPUT_MISSING:
            # elif self.step_1 == fc.INPUT_MISSING or self.step_2 == fc.INPUT_MISSING or self.step_3 == fc.INPUT_MISSING:
            return fc.INPUT_MISSING, "rgb(33,39,43)"
        elif self.step_1 == fc.NOT_ASSESSED or self.step_2 == fc.NOT_ASSESSED:
            # elif self.step_1 == fc.NOT_ASSESSED or self.step_2 == fc.NOT_ASSESSED: or self.step_3 == fc.NOT_ASSESSED:
            return fc.NOT_ASSESSED, "rgb(129, 133, 137)"
        else:
            return fc.FAIL, "#dc3545"


verdict_obj = StoreStepResults()


@teststep_definition(
    step_number=1,
    name="TAPOSD 1",
    description=(
        "Check that target pose deviation signals are below defined thresholds (check is done at the end of the"
        " maneuver)."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, fh.MfSignals)
class Taposd1(TestStep):
    """Test step class"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        read_data = self.readers[SIGNAL_DATA].signals
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        idx_last = None
        total_time = 0
        first_valid_index = None
        signal_name = example_obj._properties

        ap_time = read_data["time"]
        ap_lat_dist_to_target = read_data["LatDistToTarget"]
        ap_long_dist_to_target = read_data["LongDistToTarget"]
        ap_yaw_diff_to_target = read_data["YawDiffToTarget"]

        reached_status = read_data["ReachedStatus"].tolist()
        ap_lat_max_dev = read_data["LatMaxDeviation"]
        ap_long_max_dev = read_data["LongMaxDeviation"]
        ap_yaw_max_dev = read_data["YawMaxDeviation"]

        self.test_result: str = fc.INPUT_MISSING
        self.sig_sum = None
        self.fig = None

        signal_summary = {}
        t_start_evaluation = None
        total_time = 0
        idx_last = None
        first_valid_index = None

        """the index of the dataframe when AP.targetPosesPort.selectedPoseData.reachedStatus >0 for 0.8s """
        for idx, val in enumerate(reached_status):
            if val > 0:
                if idx_last is not None:
                    total_time += (idx - idx_last) / GeneralConstants.IDX_TO_S
                    if first_valid_index is None:
                        first_valid_index = idx
                    if round(total_time, 6) >= GeneralConstants.T_POSE_REACHED:
                        t_start_evaluation = first_valid_index
                        break
                idx_last = idx
            else:
                idx_last = None
                total_time = 0

        evaluation0 = " ".join(
            f"The evaluation is PASSED, all values for                 {signal_name['LatDistToTarget']} are < values of"
            f" {signal_name['LatMaxDeviation']}.".split()
        )
        evaluation1 = " ".join(
            f"The evaluation is PASSED, all values for                 {signal_name['LongDistToTarget']} are < values"
            f" of {signal_name['LongMaxDeviation']}.".split()
        )
        evaluation2 = " ".join(
            f"The evaluation is PASSED, all values for                 {signal_name['YawDiffToTarget']} are < values of"
            f" {signal_name['YawMaxDeviation']}.".split()
        )

        if t_start_evaluation is not None:
            """check if TARGET_POSE_DEV_LAT, TARGET_POSE_DEV_LONG and TARGET_POSE_DEV_YAW are lower than
            the maximum signal for each signal"""

            eval_cond = [True] * 3

            ap_lat_dist_to_target_mask = np.absolute(
                ap_lat_dist_to_target.iloc[t_start_evaluation:] >= ap_lat_max_dev.iloc[t_start_evaluation:]
            )
            ap_long_dist_to_target_mask = np.absolute(
                ap_long_dist_to_target.iloc[t_start_evaluation:] >= ap_long_max_dev.iloc[t_start_evaluation:]
            )
            ap_yaw_diff_to_target_mask = np.absolute(
                ap_yaw_diff_to_target.iloc[t_start_evaluation:] >= ap_yaw_max_dev.iloc[t_start_evaluation:]
            )

            if any(ap_lat_dist_to_target_mask):
                idx = ap_lat_dist_to_target_mask[ap_lat_dist_to_target_mask].idxmin()
                evaluation0 = " ".join(
                    f"The evaluation for {signal_name['LatDistToTarget']} is FAILED, the value is                  "
                    f"       >= {signal_name['LatMaxDeviation']} at timestamp {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[0] = False

            if any(ap_long_dist_to_target_mask):
                idx = ap_long_dist_to_target_mask[ap_long_dist_to_target_mask].idxmin()
                evaluation1 = " ".join(
                    f"The evaluation for {signal_name['LongDistToTarget']} is FAILED, the value is                 "
                    f"        >= {signal_name['LongMaxDeviation']} at timestamp {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[1] = False

                if any(ap_yaw_diff_to_target_mask):
                    idx = ap_yaw_diff_to_target_mask[ap_yaw_diff_to_target_mask].idxmin()
                    evaluation2 = " ".join(
                        f"The evaluation for {signal_name['YawDiffToTarget']} is FAILED, the value is                  "
                        f"       >= {signal_name['YawMaxDeviation']} at timestamp {round(ap_time.loc[idx], 3)} s.".split()
                    )
                    eval_cond[2] = False

            if all(eval_cond):
                self.test_result = fc.PASS
            else:
                self.test_result = fc.FAIL

        else:
            self.test_result = fc.NOT_ASSESSED
            evaluation0 = evaluation1 = evaluation2 = " ".join(
                f"Evaluation not possible, {signal_name['ReachedStatus']} was not > 0 for 0.8s.".split()
            )

        signal_summary[signal_name["LatDistToTarget"]] = evaluation0
        signal_summary[signal_name["LongDistToTarget"]] = evaluation1
        signal_summary[signal_name["YawDiffToTarget"]] = evaluation2

        remark = " ".join(
            "Check that after the target has reached the desired position               "
            " (.targetPosesPort.selectedPoseData.reachedStatus > 0 for 0.8s), no deviations are present.".split()
        )
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)

        if self.test_result == fc.PASS:
            verdict_obj.step_1 = fc.PASS
            self.result.measured_result = TRUE
        elif self.test_result == fc.FAIL:
            verdict_obj.step_1 = fc.FAIL
            self.result.measured_result = FALSE
        else:
            verdict_obj.step_1 = fc.NOT_ASSESSED
            self.result.measured_result = DATA_NOK

        if self.result.measured_result in [FALSE, DATA_NOK] or bool(GeneralConstants.ACTIVATE_PLOTS):
            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(x=ap_time.values.tolist(), y=reached_status, mode="lines", name=signal_name["ReachedStatus"])
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=ap_lat_dist_to_target.values.tolist(),
                    mode="lines",
                    name=signal_name["LatDistToTarget"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=ap_lat_max_dev.values.tolist(),
                    mode="lines",
                    name=signal_name["LatMaxDeviation"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=ap_long_dist_to_target.values.tolist(),
                    mode="lines",
                    name=signal_name["LongDistToTarget"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=ap_long_max_dev.values.tolist(),
                    mode="lines",
                    name=signal_name["LongMaxDeviation"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=ap_yaw_diff_to_target.values.tolist(),
                    mode="lines",
                    name=signal_name["YawDiffToTarget"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=ap_yaw_max_dev.values.tolist(),
                    mode="lines",
                    name=signal_name["YawMaxDeviation"],
                )
            )

            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(PlotlyTemplate.lgt_tmplt)

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig:
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=2,
    name="TAPOSD 2",
    description="Check that the vehicle is inside defined PB at the end of the maneuver and that there no collisions.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, fh.MfSignals)
class Taposd2(TestStep):
    """Test Step class"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        read_data = self.readers[SIGNAL_DATA].signals
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        # print(self.result.details["Additional_results"])
        max_car_ay = None
        max_car_ax = None
        time_for_parking = None
        max_speed = None
        max_yaw_rate = None
        mean_speed = None
        max_lat_dist = None
        max_long_dist = None
        max_yaw_diff = None
        max_or_err = None
        max_current_dev = None
        max_long_dist_error = None
        max_lat_dist_error = None
        max_yaw_dist_error = None
        sim_time = None

        T10 = None
        T11 = None
        T12 = None
        T15 = None
        idx_last = None
        total_time = 0
        first_valid_index = None
        signal_name = example_obj._properties

        ap_time = read_data["time"]

        head_unit_screen = read_data["headUnitVisu_screen_nu"]
        car_ay = read_data["Car_ay"]
        car_ax = read_data["Car_ax"]

        ap_state = read_data["ApState"]
        ap_lat_dist_to_target = read_data["LatDistToTarget"]
        ap_long_dist_to_target = read_data["LongDistToTarget"]
        ap_yaw_diff_to_target = read_data["YawDiffToTarget"]
        ap_orientation_error = read_data["OrientationError"]
        ap_current_deviation = read_data["LateralError"]
        ap_long_diff_optimal_tp = read_data["longDiffOptimalTP_TargetPose"]
        ap_lat_diff_optimal_tp = read_data["latDiffOptimalTP_TargetPose"]
        ap_yaw_diff_optimal_tp = read_data["yawDiffOptimalTP_TargetPose"]
        head_unit_screen = read_data["headUnitVisu_screen_nu"]
        reached_status = read_data["ReachedStatus"].tolist()
        vhcl_yawrate = read_data["VhclYawRate"]
        vhcl_v = read_data["Vhcl_v"]

        car_outside = read_data["car_outside_PB"]
        static_0 = read_data["staticStructColidesTarget_Pose_0"]
        static_1 = read_data["staticStructColidesTarget_Pose_1"]
        static_2 = read_data["staticStructColidesTarget_Pose_2"]
        static_3 = read_data["staticStructColidesTarget_Pose_3"]
        static_4 = read_data["staticStructColidesTarget_Pose_4"]
        static_5 = read_data["staticStructColidesTarget_Pose_5"]
        static_6 = read_data["staticStructColidesTarget_Pose_6"]
        static_7 = read_data["staticStructColidesTarget_Pose_7"]

        self.test_result: str = fc.INPUT_MISSING
        self.sig_sum = None
        self.fig = None

        t2_start_evaluation = None
        signal_summary = {}

        if np.any(head_unit_screen == HeadUnitVisuPortScreenVal.MANEUVER_FINISHED):
            t2_start_evaluation = np.argmax(head_unit_screen == HeadUnitVisuPortScreenVal.MANEUVER_FINISHED)

        evaluation0 = " ".join(
            f"The evaluation of {signal_name['car_outside_PB']} is PASSED, with             values !="
            f" {ConstantsTaposd.OUTSIDE_PB} for the whole time period.".split()
        )
        evaluation1 = " ".join(
            f"The evaluation of {signal_name['staticStructColidesTarget_Pose_0']} is PASSED, with             values !="
            f" {ConstantsTaposd.COLLISION} for the whole time period.".split()
        )
        evaluation2 = " ".join(
            f"The evaluation of {signal_name['staticStructColidesTarget_Pose_1']} is PASSED, with             values !="
            f" {ConstantsTaposd.COLLISION} for the whole time period.".split()
        )

        evaluation3 = " ".join(
            f"The evaluation of {signal_name['staticStructColidesTarget_Pose_2']} is PASSED, with             values !="
            f" {ConstantsTaposd.COLLISION} for the whole time period.".split()
        )

        evaluation4 = " ".join(
            f"The evaluation of {signal_name['staticStructColidesTarget_Pose_3']} is PASSED, with             values !="
            f" {ConstantsTaposd.COLLISION} for the whole time period.".split()
        )

        evaluation5 = " ".join(
            f"The evaluation of {signal_name['staticStructColidesTarget_Pose_4']} is PASSED, with             values !="
            f" {ConstantsTaposd.COLLISION} for the whole time period.".split()
        )

        evaluation6 = " ".join(
            f"The evaluation of {signal_name['staticStructColidesTarget_Pose_5']} is PASSED, with             values !="
            f" {ConstantsTaposd.COLLISION} for the whole time period.".split()
        )

        evaluation7 = " ".join(
            f"The evaluation of {signal_name['staticStructColidesTarget_Pose_6']} is PASSED, with             values !="
            f" {ConstantsTaposd.COLLISION} for the whole time period.".split()
        )

        evaluation8 = " ".join(
            f"The evaluation of {signal_name['staticStructColidesTarget_Pose_7']} is PASSED,            with values !="
            f" {ConstantsTaposd.COLLISION} for the whole time period.".split()
        )

        car_outside_mask = car_outside.iloc[t2_start_evaluation:] == 1
        static_0_mask = static_0.iloc[t2_start_evaluation:] == 1
        static_1_mask = static_1.iloc[t2_start_evaluation:] == 1
        static_2_mask = static_2.iloc[t2_start_evaluation:] == 1
        static_3_mask = static_3.iloc[t2_start_evaluation:] == 1
        static_4_mask = static_4.iloc[t2_start_evaluation:] == 1
        static_5_mask = static_5.iloc[t2_start_evaluation:] == 1
        static_6_mask = static_6.iloc[t2_start_evaluation:] == 1
        static_7_mask = static_7.iloc[t2_start_evaluation:] == 1

        # t2_start_evaluation = idx
        if t2_start_evaluation is not None:
            eval_cond = [True] * 9

            if any(car_outside_mask):
                idx = car_outside_mask[car_outside_mask].idxmin()

                evaluation0 = " ".join(
                    "The evaluation is FAILED, the value of                        "
                    f" {signal_name['car_outside_PB']} == {ConstantsTaposd.OUTSIDE_PB}                        "
                    f" instead of != {ConstantsTaposd.OUTSIDE_PB} at timestamp                        "
                    f" {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[0] = False

                if any(static_0_mask):
                    idx = static_0_mask[static_0_mask].idxmin()
                    evaluation1 = " ".join(
                        "The evaluation is FAILED, the value of                        "
                        f" {signal_name['staticStructColidesTarget_Pose_0']} == {ConstantsTaposd.COLLISION}            "
                        f"             instead of != {ConstantsTaposd.COLLISION} at timestamp                        "
                        f" {round(ap_time.loc[idx], 3)} s.".split()
                    )
                    eval_cond[1] = False

                if any(static_1_mask):
                    idx = static_1_mask[static_1_mask].idxmin()
                    evaluation2 = " ".join(
                        "The evaluation is FAILED, the value of                        "
                        f" {signal_name['staticStructColidesTarget_Pose_1']} == {ConstantsTaposd.COLLISION}            "
                        f"             instead of != {ConstantsTaposd.COLLISION} at timestamp                        "
                        f" {round(ap_time.loc[idx], 3)} s.".split()
                    )
                    eval_cond[2] = False

                if any(static_2_mask):
                    idx = static_2_mask[static_2_mask].idxmin()
                    evaluation3 = " ".join(
                        "The evaluation is FAILED, the value of                        "
                        f" {signal_name['staticStructColidesTarget_Pose_2']} == {ConstantsTaposd.COLLISION}            "
                        f"             instead of != {ConstantsTaposd.COLLISION} at timestamp                        "
                        f" {round(ap_time.loc[idx], 3)} s.".split()
                    )
                    eval_cond[3] = False

                if any(static_3_mask):
                    idx = static_3_mask[static_3_mask].idxmin()
                    evaluation4 = " ".join(
                        "The evaluation is FAILED, the value of                        "
                        f" {signal_name['staticStructColidesTarget_Pose_3']} == {ConstantsTaposd.COLLISION}            "
                        f"             instead of != {ConstantsTaposd.COLLISION} at timestamp                        "
                        f" {round(ap_time.loc[idx], 3)} s.".split()
                    )
                    eval_cond[4] = False

                if any(static_4_mask):
                    idx = static_4_mask[static_4_mask].idxmin()
                    evaluation5 = " ".join(
                        "The evaluation is FAILED, the value of                        "
                        f" {signal_name['staticStructColidesTarget_Pose_4']} == {ConstantsTaposd.COLLISION}            "
                        f"             instead of != {ConstantsTaposd.COLLISION} at timestamp                        "
                        f" {round(ap_time.loc[idx], 3)} s.".split()
                    )
                    eval_cond[5] = False

                if any(static_5_mask):
                    idx = static_5_mask[static_5_mask].idxmin()
                    evaluation6 = " ".join(
                        "The evaluation is FAILED, the value of                        "
                        f" {signal_name['staticStructColidesTarget_Pose_5']} == {ConstantsTaposd.COLLISION}            "
                        f"             instead of != {ConstantsTaposd.COLLISION} at timestamp                        "
                        f" {round(ap_time.loc[idx], 3)} s.".split()
                    )
                    eval_cond[6] = False

                if any(static_6_mask):
                    idx = static_6_mask[static_6_mask].idxmin()
                    evaluation7 = " ".join(
                        "The evaluation is FAILED, the value of                        "
                        f" {signal_name['staticStructColidesTarget_Pose_6']} == {ConstantsTaposd.COLLISION}            "
                        f"             instead of != {ConstantsTaposd.COLLISION} at timestamp                        "
                        f" {round(ap_time.loc[idx], 3)} s".split()
                    )
                    eval_cond[7] = False

                if any(static_7_mask):
                    idx = static_7_mask[static_7_mask].idxmin()
                    evaluation8 = " ".join(
                        "The evaluation is FAILED, the value of                        "
                        f" {signal_name['staticStructColidesTarget_Pose_7']} == {ConstantsTaposd.COLLISION}            "
                        f"             instead of != {ConstantsTaposd.COLLISION} at timestamp                        "
                        f" {round(ap_time.loc[idx], 3)} s.".split()
                    )
                    eval_cond[8] = False

            if all(eval_cond):
                self.test_result = fc.PASS
            else:
                self.test_result = fc.FAIL

        else:
            self.test_result = fc.NOT_ASSESSED
            evaluation0 = evaluation1 = evaluation2 = evaluation3 = evaluation4 = evaluation5 = evaluation6 = (
                evaluation7
            ) = evaluation8 = " ".join(
                "Evaluation not possible, the trigger value                    "
                f" MANEUVER_FINISHED({HeadUnitVisuPortScreenVal.MANEUVER_FINISHED})  for                    "
                f" {signal_name['headUnitVisu_screen_nu']} was never found.".split()
            )

        signal_summary[signal_name["car_outside_PB"]] = evaluation0
        signal_summary[signal_name["staticStructColidesTarget_Pose_0"]] = evaluation1
        signal_summary[signal_name["staticStructColidesTarget_Pose_1"]] = evaluation2
        signal_summary[signal_name["staticStructColidesTarget_Pose_2"]] = evaluation3
        signal_summary[signal_name["staticStructColidesTarget_Pose_3"]] = evaluation4
        signal_summary[signal_name["staticStructColidesTarget_Pose_4"]] = evaluation5
        signal_summary[signal_name["staticStructColidesTarget_Pose_5"]] = evaluation6
        signal_summary[signal_name["staticStructColidesTarget_Pose_6"]] = evaluation7
        signal_summary[signal_name["staticStructColidesTarget_Pose_7"]] = evaluation8
        remark = " ".join(
            "Check that after .headUnitVisualizationPort.screen_nu == 5(MANEUVER_FINISHED) the vehicle               "
            " is inside defined PB and that there no collisions.".split()
        )
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.test_result == fc.PASS:
            verdict_obj.step_2 = fc.PASS
            self.result.measured_result = TRUE
        elif self.test_result == fc.FAIL:
            verdict_obj.step_2 = fc.FAIL
            self.result.measured_result = FALSE
        else:
            verdict_obj.step_2 = fc.NOT_ASSESSED
            self.result.measured_result = DATA_NOK

        if self.result.measured_result in [FALSE, DATA_NOK] or bool(GeneralConstants.ACTIVATE_PLOTS):
            self.fig = go.Figure()

            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=car_outside.values.tolist(),
                    mode="lines",
                    name=signal_name["car_outside_PB"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=static_0.values.tolist(),
                    mode="lines",
                    name=signal_name["staticStructColidesTarget_Pose_0"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=static_1.values.tolist(),
                    mode="lines",
                    name=signal_name["staticStructColidesTarget_Pose_1"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=static_2.values.tolist(),
                    mode="lines",
                    name=signal_name["staticStructColidesTarget_Pose_2"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=static_3.values.tolist(),
                    mode="lines",
                    name=signal_name["staticStructColidesTarget_Pose_3"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=static_4.values.tolist(),
                    mode="lines",
                    name=signal_name["staticStructColidesTarget_Pose_4"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=static_5.values.tolist(),
                    mode="lines",
                    name=signal_name["staticStructColidesTarget_Pose_5"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=static_6.values.tolist(),
                    mode="lines",
                    name=signal_name["staticStructColidesTarget_Pose_6"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=static_7.values.tolist(),
                    mode="lines",
                    name=signal_name["staticStructColidesTarget_Pose_7"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=head_unit_screen.values.tolist(),
                    mode="lines",
                    name=signal_name["headUnitVisu_screen_nu"],
                )
            )
            self.fig.layout = go.Layout(yaxis=dict(tickformat="20"), xaxis=dict(tickformat="20"), xaxis_title="Time[s]")
            self.fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        # T10: "AP.headUnitVisualizationPort.screen_nu" == 17
        # for idx, val in enumerate(head_unit_screen):
        #     if val == GeneralConstants.MANEUVER_ACTIVE:
        #         T10 = idx # 868
        #         break
        if np.any(head_unit_screen == HeadUnitVisuPortScreenVal.MANEUVER_ACTIVE):
            T10 = np.argmax(head_unit_screen == HeadUnitVisuPortScreenVal.MANEUVER_ACTIVE)

        # T15: "AP.headUnitVisualizationPort.screen_nu" == 5
        T15 = t2_start_evaluation

        # T11: "AP.targetPosesPort.selectedPoseData.reachedStatus" >0 for 0.8 sec
        for idx, val in enumerate(reached_status):
            if val > 0:
                if idx_last is not None:
                    total_time += (idx - idx_last) / GeneralConstants.IDX_TO_S
                    if first_valid_index is None:
                        first_valid_index = idx
                    if round(total_time, 6) >= GeneralConstants.T_POSE_REACHED:
                        T11 = first_valid_index  # 4621
                        break
                idx_last = idx
            else:
                idx_last = None
                total_time = 0

        # T12: "AP.planningCtrlPort.apStates" == 3
        # for i, val in enumerate(ap_state):
        #     if val == GeneralConstants.AP_AVG_ACTIVE_IN:
        #         T12 = i # 1515
        #         break
        if np.any(ap_state == GeneralConstants.AP_AVG_ACTIVE_IN):
            T12 = np.argmax(ap_state == GeneralConstants.AP_AVG_ACTIVE_IN)

        # calc for every element in the table
        if T10 is not None and T15 is not None:
            time_for_parking = round(abs(ap_time.iloc[T15] - ap_time.iloc[T10]), 3)
        else:
            time_for_parking = "n.a"

        if T12 is not None:
            max_car_ay = np.around(np.amax(np.abs(car_ay.iloc[T12:])), 3)
            max_car_ax = np.around(np.amax(np.abs(car_ax.iloc[T12:])), 3)
            max_speed = np.around(np.amax(np.abs(vhcl_v.iloc[T12:])), 3)
            max_yaw_rate = np.around(np.amax(np.abs(np.rad2deg(vhcl_yawrate.iloc[T12:]))), 3)
            max_or_err = np.around(np.amax(np.abs(np.rad2deg(ap_orientation_error.iloc[T12:]))), 3)
            max_current_dev = np.around(np.amax(np.abs(ap_current_deviation.iloc[T12:])), 3)
            sim_time = round(max(ap_time.iloc[T12:]), 3)
        else:
            max_car_ay = "n.a"
            max_car_ax = "n.a"
            max_speed = "n.a"
            max_yaw_rate = "n.a"
            max_or_err = "n.a"
            max_current_dev = "n.a"
            sim_time = "n.a"

        if T12 is not None and T15 is not None:
            mean_speed = np.around(np.mean(np.abs(vhcl_v.iloc[T12:T15])), 3)
        else:
            mean_speed = "n.a"

        if T11 is not None:
            max_lat_dist = np.around(np.amax(np.abs(ap_lat_dist_to_target.iloc[T11:])), 3)
            max_long_dist = np.around(np.amax(np.abs(ap_long_dist_to_target.iloc[T11:])), 3)
            max_yaw_diff = np.around(np.amax(np.rad2deg(np.abs(ap_yaw_diff_to_target.iloc[T11:]))), 3)
        else:
            max_lat_dist = "n.a"
            max_long_dist = "n.a"
            max_yaw_diff = "n.a"
        max_long_dist_error = np.around(np.amax(ap_long_diff_optimal_tp), 3)
        max_lat_dist_error = np.around(np.amax(ap_lat_diff_optimal_tp), 3)
        max_yaw_dist_error = np.around(np.amax(ap_yaw_diff_optimal_tp), 3)

        """Add the data in the table from Functional Test Filter Results"""
        verdict, color = verdict_obj.check_result()
        # color = '#28a745' if verdict_obj.check_result(
        # ) else 'rgb(33,39,43)' if final_result == fc.INPUT_MISSING else '#dc3545'
        try:
            additional_results_dict = {
                "Verdict": {"value": verdict.title(), "color": color},
                "SimulationTime[s]": {"value": sim_time, "color": fh.apply_color(sim_time, 200, "<", 20, ">=<=")},
                "Time for Parking[s]": {
                    "value": time_for_parking,
                    "color": fh.apply_color(time_for_parking, 200, "<", 20, ">=<="),
                },
                "max Car.ay[m/s^2]": {"value": max_car_ay, "color": fh.apply_color(max_car_ay, 1, "<", 0.5, ">=<=")},
                "max YawRate[deg/s]": {
                    "value": max_yaw_rate,
                    "color": fh.apply_color(max_yaw_rate, 25, "<", 10, ">=<="),
                },
                "max VehicleSpeed [m/s]": {
                    "value": max_speed,
                    "color": fh.apply_color(max_speed, 2.7, "<", 1.35, ">=<="),
                },
                "mean VehicleSpeed [m]": {
                    "value": mean_speed,
                    "color": fh.apply_color(mean_speed, 0.3, ">", 0.5, ">=<="),
                },
                "max Car.ax[m/s^2]": {"value": max_car_ax, "color": fh.apply_color(max_car_ax, 2, "<", 1, ">=<=")},
                "max abs latDistToTarget[m] ": {
                    "value": max_lat_dist,
                    "color": fh.apply_color(max_lat_dist, 0.05, "<", 0.3, ">=<="),
                },
                "max abs longDistToTarget[m] ": {
                    "value": max_long_dist,
                    "color": fh.apply_color(max_long_dist, 0.10, "<", 0.05, ">=<="),
                },
                "max abs yawDiffToTarget[deg] ": {
                    "value": max_yaw_diff,
                    "color": fh.apply_color(max_yaw_diff, 1.0, "<", 0.5, ">=<="),
                },
                "max abs OrientationError[deg] ": {
                    "value": max_or_err,
                    "color": fh.apply_color(max_or_err, 1, "<", 2, ">=<="),
                },
                "max abs currentDeviation[m] ": {
                    "value": max_current_dev,
                    "color": fh.apply_color(max_current_dev, 0.03, "<", 0.05, ">=<="),
                },
                "max LongDistErrorOTP_TargetPoses[m]": {
                    "value": max_long_dist_error,
                    "color": fh.apply_color(max_long_dist_error, -1, "==", [0, 0.2], "[>=<]"),
                },
                "max LatDistErrorOTP_TargetPose[m]": {
                    "value": max_lat_dist_error,
                    "color": fh.apply_color(max_lat_dist_error, -1, "==", [0, 0.1], "[>=<]"),
                },
                "max YawDistErrorOTP_TargetPose[deg]": {
                    "value": max_yaw_dist_error,
                    "color": fh.apply_color(max_yaw_dist_error, -1, "==", [0, 2], "[>=<]"),
                },
            }
        except Exception:
            additional_results_dict = {
                "Verdict": {"value": verdict.title(), "color": color},
            }
        self.result.details["Additional_results"] = additional_results_dict


@teststep_definition(
    step_number=3,
    name="TAPOSD THIRD",
    description="""Check if measurements contain Optimal Target Pose.isPresent_nu(==1).""",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, fh.MfSignals)
class Taposd3(TestStep):
    """Test step class"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        read_data = self.readers[SIGNAL_DATA].signals
        # final_result = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        # max_car_ay = None
        # max_car_ax = None
        # time_for_parking = None
        # max_speed = None
        # max_yaw_rate = None
        # mean_speed = None
        # max_lat_dist = None
        # max_long_dist = None
        # max_yaw_diff = None
        # max_or_err = None
        # max_current_dev = None
        # max_long_dist_error = None
        # max_lat_dist_error = None
        # max_yaw_dist_error = None
        # sim_time = None

        # T10 = None
        # T11 = None
        # T12 = None
        # T15 = None
        # idx_last = None
        # total_time = 0
        # first_valid_index = None

        ap_time = read_data[fh.MfSignals.Columns.TIME].tolist()
        head_unit_screen = read_data[fh.MfSignals.Columns.HEADUNITVISU_SCREEN_NU].tolist()
        optimal_tp_x = read_data[fh.MfSignals.Columns.OPTIMALTARGETPOSE_x].tolist()
        optimal_tp_y = read_data[fh.MfSignals.Columns.OPTIMALTARGETPOSE_y].tolist()
        optimal_tp_yaw = read_data[fh.MfSignals.Columns.OPTIMALTARGETPOSE_yaw].tolist()
        cm_tp_x = read_data[fh.MfSignals.Columns.CMTARGETPOSE_x].tolist()
        cm_tp_y = read_data[fh.MfSignals.Columns.OPTIMALTARGETPOSE_y].tolist()
        cm_tp_yaw = read_data[fh.MfSignals.Columns.OPTIMALTARGETPOSE_yaw].tolist()

        # car_ay = read_data["Car_ay"].tolist()
        # car_ax = read_data["Car_ax"].tolist()
        # ap_state = read_data["ApState"].tolist()
        # ap_lat_dist_to_target = read_data["LatDistToTarget"].tolist()
        # ap_long_dist_to_target = read_data["LongDistToTarget"].tolist()
        # ap_yaw_diff_to_target = read_data["YawDiffToTarget"].tolist()
        # ap_orientation_error = read_data["OrientationError"].tolist()
        # ap_current_deviation = read_data["LateralError"].tolist()
        # ap_long_diff_optimal_tp = read_data["longDiffOptimalTP_TargetPose"].tolist()
        # ap_lat_diff_optimal_tp = read_data["latDiffOptimalTP_TargetPose"].tolist()
        # ap_yaw_diff_optimal_tp = read_data["yawDiffOptimalTP_TargetPose"].tolist()
        head_unit_screen = read_data["headUnitVisu_screen_nu"].tolist()
        # reached_status = read_data["ReachedStatus"].tolist()
        # vhcl_yawrate = read_data["VhclYawRate"].tolist()
        # vhcl_v = read_data["Vhcl_v"].tolist()

        self.test_result: str = fc.INPUT_MISSING
        self.sig_sum = None
        self.fig = None

        t2_start_evaluation = None
        signal_summary = {}
        self.test_result: str = fc.INPUT_MISSING
        x_list = []
        y_list = []
        yaw_list = []

        for idx, val in enumerate(head_unit_screen):
            if val == HeadUnitVisuPortScreenVal.MANEUVER_FINISHED:
                t2_start_evaluation = idx
                break

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['CMTargetPose_x_m']} is PASSED because difference with            "
            f" {signal_name['OptimalTargetPose_x_m']} is <= 0 while MANEUVER FINISHED".split()
        )
        evaluation2 = " ".join(
            f"The evaluation of {signal_name['CMTargetPose_y_m']} is PASSED because difference with            "
            f" {signal_name['OptimalTargetPose_y_m']} is <= 0 while MANEUVER FINISHED".split()
        )
        evaluation3 = " ".join(
            f"The evaluation of {signal_name['CMTargetPose_yaw_rad']} is PASSED because difference with            "
            f" {signal_name['OptimalTargetPose_yaw_rad']} is <= 0 while MANEUVER FINISHED".split()
        )

        x_list = [abs(abs(val1) - abs(val2)) for (val1, val2) in zip(optimal_tp_x, cm_tp_x)]
        y_list = [abs(abs(val1) - abs(val2)) for (val1, val2) in zip(optimal_tp_y, cm_tp_y)]
        yaw_list = [abs(abs(val1) - abs(val2)) for (val1, val2) in zip(optimal_tp_yaw, cm_tp_yaw)]

        if t2_start_evaluation is not None:
            eval_cond = [True] * 3
            for idx, _val in enumerate(head_unit_screen[t2_start_evaluation:], start=t2_start_evaluation):
                if x_list[idx] > 0 and eval_cond[0] is True:
                    evaluation1 = " ".join(
                        "The evaluation is FAILED, the value of                        "
                        f" {signal_name['CMTargetPose_x_m']} is different than                        "
                        f" {signal_name['OptimalTargetPose_x_m']}                         at timestamp"
                        f" {round(ap_time[idx], 3)} s.".split()
                    )
                    eval_cond[0] = False
                if y_list[idx] > 0 and eval_cond[1] is True:
                    evaluation2 = " ".join(
                        "The evaluation is FAILED, the value of                        "
                        f" {signal_name['CMTargetPose_y_m']} is different than                        "
                        f" {signal_name['OptimalTargetPose_y_m']}                         at timestamp"
                        f" {round(ap_time[idx], 3)} s.".split()
                    )
                    eval_cond[1] = False
                if yaw_list[idx] > 0 and eval_cond[2] is True:
                    evaluation3 = " ".join(
                        "The evaluation is FAILED, the value of                        "
                        f" {signal_name['CMTargetPose_yaw_rad']} is different than                        "
                        f" {signal_name['OptimalTargetPose_yaw_rad']}                         at timestamp"
                        f" {round(ap_time[idx], 3)} s.".split()
                    )
                    eval_cond[2] = False
            if all(eval_cond):
                self.test_result = fc.PASS
            else:
                self.test_result = fc.FAIL

        else:
            self.test_result = fc.NOT_ASSESSED
            # eval_cond = [False] * 3
            evaluation1 = evaluation2 = evaluation3 = " ".join(
                "Evaluation not possible, the trigger value                    "
                f" MANEUVER_FINISHED({HeadUnitVisuPortScreenVal.MANEUVER_FINISHED})  for                    "
                f" {signal_name['headUnitVisu_screen_nu']} was never found.".split()
            )

        signal_summary[signal_name["CMTargetPose_x_m"]] = evaluation1
        signal_summary[signal_name["CMTargetPose_y_m"]] = evaluation2
        signal_summary[signal_name["CMTargetPose_yaw_rad"]] = evaluation3

        self.sig_sum = fh.convert_dict_to_pandas(
            signal_summary, table_remark="Check if measurements contain Optimal Target Pose coordinates are fulfilled."
        )
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.test_result == fc.PASS:
            verdict_obj.step_3 = fc.PASS
            self.result.measured_result = TRUE
        elif self.test_result == fc.FAIL:
            verdict_obj.step_3 = fc.FAIL
            self.result.measured_result = FALSE
        else:
            verdict_obj.step_3 = fc.NOT_ASSESSED
            self.result.measured_result = DATA_NOK

        if self.result.measured_result in [FALSE, DATA_NOK] or bool(GeneralConstants.ACTIVATE_PLOTS):
            self.fig = go.Figure()

            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(), y=optimal_tp_x, mode="lines", name=signal_name["OptimalTargetPose_x_m"]
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(), y=optimal_tp_y, mode="lines", name=signal_name["OptimalTargetPose_y_m"]
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=optimal_tp_yaw,
                    mode="lines",
                    name=signal_name["OptimalTargetPose_yaw_rad"],
                )
            )
            self.fig.add_trace(
                go.Scatter(x=ap_time.values.tolist(), y=cm_tp_x, mode="lines", name=signal_name["CMTargetPose_x_m"])
            )
            self.fig.add_trace(
                go.Scatter(x=ap_time.values.tolist(), y=cm_tp_y, mode="lines", name=signal_name["CMTargetPose_y_m"])
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(), y=cm_tp_yaw, mode="lines", name=signal_name["CMTargetPose_yaw_rad"]
                )
            )
            self.fig.add_trace(go.Scatter(x=ap_time.values.tolist(), y=x_list, mode="lines", name="x difference"))
            self.fig.add_trace(go.Scatter(x=ap_time.values.tolist(), y=y_list, mode="lines", name="y difference"))
            self.fig.add_trace(go.Scatter(x=ap_time.values.tolist(), y=yaw_list, mode="lines", name="yaw difference"))
            self.fig.layout = go.Layout(yaxis=dict(tickformat="20"), xaxis=dict(tickformat="20"), xaxis_title="Time[s]")
            self.fig.update_layout(PlotlyTemplate.lgt_tmplt)

        if self.fig:
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("Test Graphics third evaluation")

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)
        # # T10: "AP.headUnitVisualizationPort.screen_nu" == 17
        # for idx, val in enumerate(head_unit_screen):
        #     if val == GeneralConstants.MANEUVER_ACTIVE:
        #         T10 = idx
        #         break

        # # T15: "AP.headUnitVisualizationPort.screen_nu" == 5
        # for i, val in enumerate(head_unit_screen):
        #     if val == GeneralConstants.MANEUVER_FINISH:
        #         T15 = i
        #         break

        # # T11: "AP.targetPosesPort.selectedPoseData.reachedStatus" >0 for 0.8 sec
        # for idx, val in enumerate(reached_status):
        #     if val > 0:
        #         if idx_last is not None:
        #             total_time += (idx - idx_last) / GeneralConstants.IDX_TO_S
        #             if first_valid_index is None:
        #                 first_valid_index = idx
        #             if round(total_time, 6) >= GeneralConstants.T_POSE_REACHED:
        #                 T11 = first_valid_index
        #                 break
        #         idx_last = idx
        #     else:
        #         idx_last = None
        #         total_time = 0

        # # T12: "AP.planningCtrlPort.apStates" == 3
        # for i, val in enumerate(ap_state):
        #     if val == GeneralConstants.AP_AVG_ACTIVE_IN:
        #         T12 = i
        #         break

        # # calc for every element in the table
        # if T10 is not None and T15 is not None:
        #     time_for_parking = round(abs(ap_time[T15] - ap_time[T10]), 3)
        # else:
        #     time_for_parking = "n.a"

        # if T12 is not None:
        #     max_car_ay = np.around(np.amax(np.abs(car_ay[T12:])), 3)
        #     max_car_ax = np.around(np.amax(np.abs(car_ax[T12:])), 3)
        #     max_speed = np.around(np.amax(np.abs(vhcl_v[T12:])), 3)
        #     max_yaw_rate = np.around(np.amax(np.abs(np.rad2deg(vhcl_yawrate[T12:]))), 3)
        #     max_or_err = np.around(np.amax(np.abs(np.rad2deg(ap_orientation_error[T12:]))), 3)
        #     max_current_dev = np.around(np.amax(np.abs(ap_current_deviation[T12:])), 3)
        #     sim_time = round(max(ap_time[T12:]), 3)
        # else:
        #     max_car_ay = "n.a"
        #     max_car_ax = "n.a"
        #     max_speed = "n.a"
        #     max_yaw_rate = "n.a"
        #     max_or_err = "n.a"
        #     max_current_dev = "n.a"
        #     sim_time = "n.a"
        #     final_result = fc.INPUT_MISSING

        # if T12 is not None and T15 is not None:
        #     mean_speed = np.around(np.mean(np.abs(vhcl_v[T12:T15])), 3)
        # else:
        #     mean_speed = "n.a"

        # if T11 is not None:
        #     max_lat_dist = np.around(np.amax(np.abs(ap_lat_dist_to_target[T11:])), 3)
        #     max_long_dist = np.around(np.amax(np.abs(ap_long_dist_to_target[T11:])), 3)
        #     max_yaw_diff = np.around(np.amax(np.rad2deg(np.abs(ap_yaw_diff_to_target[T11:]))), 3)
        # else:
        #     max_lat_dist = "n.a"
        #     max_long_dist = "n.a"
        #     max_yaw_diff = "n.a"
        # max_long_dist_error = np.around(np.amax(ap_long_diff_optimal_tp), 3)
        # max_lat_dist_error = np.around(np.amax(ap_lat_diff_optimal_tp), 3)
        # max_yaw_dist_error = np.around(np.amax(ap_yaw_diff_optimal_tp), 3)

        # """Add the data in the table from Functional Test Filter Results"""
        # verdict, color = verdict_obj.check_result()
        # # color = '#28a745' if verdict_obj.check_result(
        # # ) else 'rgb(33,39,43)' if final_result == fc.INPUT_MISSING else '#dc3545'
        # additional_results_dict = {
        #     "Verdict": {"value": verdict.title(),
        #                 "color": color},
        #     "SimulationTime[s]": {"value": sim_time,
        #                           "color": fh.apply_color(sim_time, 200, '<', 20, '><')},
        #     "Time for Parking[s]": {"value": time_for_parking,
        #                             "color": fh.apply_color(time_for_parking, 200, '<', 20, '><')},
        #     "max Car.ay[m/s^2]": {"value": max_car_ay,
        #                           "color": fh.apply_color(max_car_ay, 1, "<", 0.5, '><')},
        #     "max YawRate[deg/s]": {"value": max_yaw_rate,
        #                            "color": fh.apply_color(max_yaw_rate, 25, "<", 10, '><')},
        #     "max VehicleSpeed [m/s]": {"value": max_speed,
        #                                "color": fh.apply_color(max_speed, 2.7, "<", 1.35, '><')},
        #     "mean VehicleSpeed [m]": {"value": mean_speed,
        #                               "color": fh.apply_color(mean_speed, 0.3, ">", 0.5, '><')},
        #     "max Car.ax[m/s^2]": {"value": max_car_ax,
        #                           "color": fh.apply_color(max_car_ax, 2, "<", 1, '><')},
        #     "max abs latDistToTarget[m] ": {"value": max_lat_dist,
        #                                     "color": fh.apply_color(max_lat_dist, 0.05, "<", 0.3, '><')},
        #     "max abs longDistToTarget[m] ": {"value": max_long_dist,
        #                                      "color": fh.apply_color(max_long_dist, 0.10, "<", 0.05, '><')},
        #     "max abs yawDiffToTarget[deg] ": {"value": max_yaw_diff,
        #                                       "color": fh.apply_color(max_yaw_diff, 1.0, "<", 0.5, '><')},
        #     "max abs OrientationError[deg] ": {"value": max_or_err,
        #                                        "color": fh.apply_color(max_or_err, 1, "<", 2, '><')},
        #     "max abs currentDeviation[m] ": {"value": max_current_dev,
        #                                      "color": fh.apply_color(max_current_dev, 0.03, "<", 0.05, '><')},
        #     "max LongDistErrorOTP_TargetPoses[m]": {"value": max_long_dist_error,
        #                                             "color": fh.apply_color(max_long_dist_error, -1,
        #                                                                              '==', [0, 0.2], '>=<')},
        #     "max LatDistErrorOTP_TargetPose[m]": {"value": max_lat_dist_error,
        #                                           "color": fh.apply_color(max_lat_dist_error, -1,
        #                                                                            '==', [0, 0.1], '>=<')},
        #     "max YawDistErrorOTP_TargetPose[deg]": {"value": max_yaw_dist_error,
        #                                             "color": fh.apply_color(max_yaw_dist_error, -1,
        #                                                                              '==', [0, 0.2], '>=<')},
        # }
        # self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="MF TAPOSD",
    description=(
        "Check that target pose deviation signals are below defined thresholds at the end of measurement and that after"
        " the maneuver finished vehicle is inside defined Parking Box."
    ),
)
class FtParkingTaposd(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Taposd1,
            Taposd2,
            #
            # Taposd3
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.
    """
    # test_bsigs = [data_folder / f"test_input_{k}.bsig" for k in range(3)]
    # os.makedirs(data_folder, exist_ok=True)
    # for b in test_bsigs:
    #     generate_bsig(b)
    test_bsigs = r"D:\masuratori_dana\mf_sil\mf_sil_1\mf_sil\tests\SIL\CarMaker\SimOutput\AP_AutoTestExecution\AUPSim_NUC_ParRight_ST-0201_B.erg"
    debug(
        FtParkingTaposd,
        *test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
        # statistics=StatisticsExample,
        kpi_report=False,
        dev_report=True,
    )
    _log.debug("All done.")


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"
    out_folder = working_directory / "out"

    main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)
