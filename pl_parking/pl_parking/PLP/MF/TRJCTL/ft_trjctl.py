#!/usr/bin/env python3
"""TRJCTL TestCase."""

import logging

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

import numpy as np
import plotly.graph_objects as go
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, MfSignals
from pl_parking.PLP.MF.constants import ConstantsTrajctl, GeneralConstants, PlotlyTemplate

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


SIGNAL_DATA = "MF_TRJCTL"

signals_obj = MfSignals()
step_1_result = fc.INPUT_MISSING


class StoreStepResults:
    """Class defined to store results of the teststeps."""

    def __init__(self):
        """Initialize the class."""
        self.step_1 = fc.INPUT_MISSING
        self.step_2 = fc.INPUT_MISSING

    def check_result(self):
        """Define the method."""
        if self.step_1 == fc.PASS and self.step_2 == fc.PASS:
            # self.case_result == fc.PASS
            return fc.PASS, "#28a745"
        elif self.step_1 == fc.INPUT_MISSING or self.step_2 == fc.INPUT_MISSING:
            # self.case_result == fc.INPUT_MISSING
            return fc.INPUT_MISSING, "rgb(33,39,43)"
        elif self.step_1 == fc.NOT_ASSESSED or self.step_2 == fc.NOT_ASSESSED:
            # self.case_result == fc.NOT_ASSESSED
            return fc.NOT_ASSESSED, "rgb(129, 133, 137)"
        else:
            # self.case_result == fc.FAIL
            return fc.FAIL, "#dc3545"


final_result = StoreStepResults()


@teststep_definition(
    step_number=1,
    name="TRJCTL 1",
    description=(
        "Check that orientation error, current deviation, vehicle speed and vehicle acceleration are within thresholds"
        " (check is done after apStates == 3 until the end of the simulation."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TestStepFtParkingTrajctl(TestStep):
    """TRJCTL Test Step definition."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        read_data = self.readers[SIGNAL_DATA].signals
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = signals_obj._properties

        car_ay = read_data["Car_ay"]
        ap_state = read_data["ApState"]
        vhcl_yaw_rate = read_data["VhclYawRate"]
        vhcl_v = read_data["Vhcl_v"]
        car_ax = read_data["Car_ax"]
        ap_orientation_error = read_data["OrientationError"]
        ap_current_deviation = read_data["LateralError"]
        ap_dist_to_stop_req_inter_extrapol_traj = read_data["ApDistToStopReqInterExtrapolTraj"]
        ap_time = read_data["time"]

        self.test_result: str = fc.INPUT_MISSING
        self.sig_sum = None
        self.fig = None
        t2 = None
        signal_summary = {}

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Car_ay']} is PASSED with values <                 than"
            f" {ConstantsTrajctl.LAT_ACC_EGO_MAX} m/s^2 ".split()
        )
        evaluation2 = " ".join(
            f"The evaluation of {signal_name['VhclYawRate']} is PASSED with values <                 than"
            f" {ConstantsTrajctl.YAWRATE_MAX} rad/s.".split()
        )
        evaluation3 = " ".join(
            f"The evaluation of {signal_name['Vhcl_v']} is PASSED with values <                 than"
            f" {GeneralConstants.V_MAX_L3} m/s.".split()
        )
        evaluation4 = " ".join(
            f"The evaluation of {signal_name['Car_ax']} is PASSED with values <                 than"
            f" {ConstantsTrajctl.LONG_ACC_EGO_MAX} m/s^2.".split()
        )
        evaluation5 = " ".join(
            f"The evaluation of {signal_name['Vhcl_v']} is PASSED because average value is >                 than"
            f" {ConstantsTrajctl.V_AVERAGE_MIN_PERPENDICULAR} m/s.".split()
        )
        evaluation6 = " ".join(
            f"The evaluation of {signal_name['OrientationError']} is PASSED with values <                 than"
            f" {ConstantsTrajctl.ANGLE_DEVIATION_MAX} rad.".split()
        )
        evaluation7 = " ".join(
            f"The evaluation of {signal_name['LateralError']} is PASSED with values <                 than"
            f" {ConstantsTrajctl.LAT_DEVIATION_MAX} m.".split()
        )
        evaluation8 = " ".join(
            f"The evaluation of {signal_name['ApDistToStopReqInterExtrapolTraj']} is PASSED                 with values"
            f" > than {ConstantsTrajctl.AP_LO_STOP_ACCURACY_NEG} m.".split()
        )

        if np.any(ap_state == GeneralConstants.AP_AVG_ACTIVE_IN):
            t2 = np.argmax(ap_state == GeneralConstants.AP_AVG_ACTIVE_IN)

        if t2 is not None:
            eval_cond = [True] * 8
            car_ay_mask = abs(car_ay.iloc[t2:]) >= ConstantsTrajctl.LAT_ACC_EGO_MAX
            vhcl_yaw_rate_mask = abs(vhcl_yaw_rate.iloc[t2:]) >= ConstantsTrajctl.YAWRATE_MAX
            vhcl_v_mask = abs(vhcl_v.iloc[t2:]) >= GeneralConstants.V_MAX_L3
            car_ax_mask = abs(car_ax.iloc[t2:]) >= ConstantsTrajctl.LONG_ACC_EGO_MAX
            vhcl_v_mean = np.average(vhcl_v)  # TO BE REVIEWED
            ap_orientation_error_mask = abs(ap_orientation_error.iloc[t2:]) >= ConstantsTrajctl.ANGLE_DEVIATION_MAX
            ap_current_deviation_mask = abs(ap_current_deviation.iloc[t2:]) >= ConstantsTrajctl.LAT_DEVIATION_MAX
            ap_dist_to_stop_req_inter_extrapol_traj_mask = (
                ap_dist_to_stop_req_inter_extrapol_traj.iloc[t2:]
            ) <= ConstantsTrajctl.AP_LO_STOP_ACCURACY_NEG

            if any(car_ay_mask):
                idx = car_ay_mask.index[car_ay_mask][0]
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Car_ay']} is FAILED because the value                       "
                    f" is >= {ConstantsTrajctl.LAT_ACC_EGO_MAX} m/s^2 at                         timestamp"
                    f" {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[0] = False

            if any(vhcl_yaw_rate_mask):
                idx = vhcl_yaw_rate_mask.index[vhcl_yaw_rate_mask][0]
                evaluation2 = " ".join(
                    f"The evaluation of {signal_name['VhclYawRate']} is FAILED because the value                   "
                    f"     is >= {ConstantsTrajctl.YAWRATE_MAX} rad/s at                         timestamp"
                    f" {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[1] = False

            if any(vhcl_v_mask):
                idx = vhcl_v_mask.index[vhcl_v_mask][0]
                evaluation3 = " ".join(
                    f"The evaluation of {signal_name['Vhcl_v']} is FAILED because the value                       "
                    f" is >= {GeneralConstants.V_MAX_L3} m/s at                         timestamp"
                    f" {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[2] = False

            if any(car_ax_mask):
                idx = car_ax_mask.index[car_ax_mask][0]
                evaluation4 = " ".join(
                    f"The evaluation of {signal_name['Car_ax']} is FAILED because the value                        "
                    f" is >= {ConstantsTrajctl.LONG_ACC_EGO_MAX} m/s^2 at                         timestamp"
                    f" {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[3] = False

            if vhcl_v_mean <= ConstantsTrajctl.V_AVERAGE_MIN_PERPENDICULAR and eval_cond[4]:
                evaluation5 = " ".join(
                    f"The evaluation of {signal_name['Vhcl_v']} is FAILED because the average value is <=          "
                    f"               {ConstantsTrajctl.V_AVERAGE_MIN_PERPENDICULAR} m/s.".split()
                )
                eval_cond[4] = False

            if any(ap_orientation_error_mask):
                idx = ap_orientation_error_mask.index[ap_orientation_error_mask][0]
                evaluation6 = " ".join(
                    f"The evaluation of {signal_name['OrientationError']} is FAILED because the value              "
                    f"           is >= {ConstantsTrajctl.ANGLE_DEVIATION_MAX} rad                         at"
                    f" timestamp {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[5] = False

            if any(ap_current_deviation_mask):
                idx = ap_current_deviation_mask.index[ap_current_deviation_mask][0]
                evaluation7 = " ".join(
                    f"The evaluation of {signal_name['LateralError']} is FAILED because the value                  "
                    f"       is >= {ConstantsTrajctl.LAT_DEVIATION_MAX} m                         at timestamp"
                    f" {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[6] = False

            if any(ap_dist_to_stop_req_inter_extrapol_traj_mask):
                idx = ap_dist_to_stop_req_inter_extrapol_traj_mask.index[ap_dist_to_stop_req_inter_extrapol_traj_mask][
                    0
                ]
                evaluation8 = " ".join(
                    f"The evaluation of {signal_name['ApDistToStopReqInterExtrapolTraj']} is                       "
                    f"  FAILED because the value is <= {ConstantsTrajctl.AP_LO_STOP_ACCURACY_NEG} m                "
                    f"         at timestamp {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[7] = False
            if all(eval_cond):
                self.result.measured_result = TRUE
                final_result.step_1 = fc.PASS

            else:
                self.result.measured_result = FALSE
                final_result.step_1 = fc.FAIL

        else:
            final_result.step_1 = fc.NOT_ASSESSED
            self.result.measured_result = DATA_NOK

            evaluation1 = evaluation2 = evaluation3 = evaluation4 = evaluation5 = evaluation6 = evaluation7 = (
                evaluation8
            ) = " ".join(
                "Evaluation not possible, the trigger value AP_AVG_ACTIVE_IN                   "
                f" ({GeneralConstants.AP_AVG_ACTIVE_IN}) for                     {signal_name['ApState']} was never"
                " found.".split()
            )

        self.test_result = final_result.step_1
        signal_summary[signal_name["Car_ay"]] = evaluation1
        signal_summary[signal_name["VhclYawRate"]] = evaluation2
        signal_summary[signal_name["Vhcl_v"]] = evaluation3
        signal_summary[signal_name["Car_ax"]] = evaluation4
        signal_summary[f' {signal_name["Vhcl_v"]}'] = evaluation5
        signal_summary[signal_name["OrientationError"]] = evaluation6
        signal_summary[signal_name["LateralError"]] = evaluation7
        signal_summary[signal_name["ApDistToStopReqInterExtrapolTraj"]] = evaluation8

        remark = " ".join(
            "Check that orientation error, current deviation, vehicle speed and vehicle acceleration are           "
            " within thresholds (check is done after .planningCtrlPort.apStates == 3 until the end of the simulation..".split()
        )
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.result.measured_result in [FALSE, DATA_NOK] or bool(GeneralConstants.ACTIVATE_PLOTS):
            self.fig = go.Figure()

            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=ap_state.values.tolist(),
                    mode="lines",
                    name=signal_name["ApState"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(), y=car_ax.values.tolist(), mode="lines", name=signal_name["Car_ax"]
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(), y=car_ay.values.tolist(), mode="lines", name=signal_name["Car_ay"]
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=ap_dist_to_stop_req_inter_extrapol_traj.values.tolist(),
                    mode="lines",
                    name=signal_name["ApDistToStopReqInterExtrapolTraj"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=vhcl_yaw_rate.values.tolist(),
                    mode="lines",
                    name=signal_name["VhclYawRate"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=ap_current_deviation.values.tolist(),
                    mode="lines",
                    name=signal_name["LateralError"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=ap_orientation_error.values.tolist(),
                    mode="lines",
                    name=signal_name["OrientationError"],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(), y=vhcl_v.values.tolist(), mode="lines", name=signal_name["Vhcl_v"]
                )
            )
            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(PlotlyTemplate.lgt_tmplt)

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
    name="TRJCTL 2",
    description=(
        " Check that target pose deviation signals are below defined thresholds (check is done after    "
        f" {signals_obj._properties[MfSignals.Columns.REACHEDSTATUS]} > 0 for 0.8s until end of sim)."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TestStepFtParkingTrajctl2(TestStep):
    """TRJCTL Test Step definition."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        read_data = self.readers[SIGNAL_DATA].signals
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

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
        sim_time = None

        T10 = None
        T11 = None
        T12 = None
        T15 = None
        idx_last = None
        total_time = 0
        first_valid_index = None
        signal_name = signals_obj._properties

        car_ay = read_data["Car_ay"]
        ap_state = read_data["ApState"]
        vhcl_yaw_rate = read_data["VhclYawRate"]
        vhcl_v = read_data["Vhcl_v"]
        car_ax = read_data["Car_ax"]
        ap_lat_dist_to_target = read_data["LatDistToTarget"]
        ap_long_dist_to_target = read_data["LongDistToTarget"]
        ap_yaw_diff_to_target = read_data["YawDiffToTarget"]
        ap_orientation_error = read_data["OrientationError"]
        ap_current_deviation = read_data["LateralError"]
        head_unit_screen = read_data["headUnitVisu_screen_nu"]
        ap_lat_max_dev = read_data["LatMaxDeviation"]
        ap_long_max_dev = read_data["LongMaxDeviation"]
        ap_yaw_max_dev = read_data["YawMaxDeviation"]
        ap_time = read_data["time"]
        reached_status = read_data["ReachedStatus"].tolist()

        self.test_result: str = fc.INPUT_MISSING
        self.sig_sum = None
        self.fig = None

        t3 = None
        signal_summary = {}
        total_time = 0
        idx_last = None
        first_valid_index = None

        # final_verdict = fc.INPUT_MISSING

        for idx, val in enumerate(reached_status):
            if val > 0:
                if idx_last is not None:
                    total_time += (idx - idx_last) / GeneralConstants.IDX_TO_S
                    if first_valid_index is None:
                        first_valid_index = idx - 1
                    if round(total_time, 6) >= GeneralConstants.T_POSE_REACHED:
                        t3 = first_valid_index
                        break
                idx_last = idx
            else:
                idx_last = None
                total_time = 0

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['LatDistToTarget']}             is PASSED with values < values of"
            f" {signal_name['LatMaxDeviation']}.".split()
        )
        evaluation2 = " ".join(
            f"The evaluation of {signal_name['LongDistToTarget']}             is PASSED with values < values of"
            f" {signal_name['LongMaxDeviation']}.".split()
        )
        evaluation3 = " ".join(
            f"The evaluation of {signal_name['YawDiffToTarget']}             is PASSED with values < values of"
            f" {signal_name['YawMaxDeviation']}.".split()
        )

        if t3 is not None:
            ap_lat_dist_to_target_mask = abs(ap_lat_dist_to_target.iloc[t3:]) >= ap_lat_max_dev[t3:]
            ap_long_dist_to_target_mask = abs(ap_long_dist_to_target.iloc[t3:]) >= ap_long_max_dev[t3:]
            ap_yaw_diff_to_target_mask = abs(ap_yaw_diff_to_target.iloc[t3:]) >= ap_yaw_max_dev[t3:]

            eval_cond = [True] * 3
            # if abs(ap_lat_dist_to_target[idx]) >= ap_lat_max_dev[idx] and eval_cond[0]:
            if any(ap_lat_dist_to_target_mask):
                idx = ap_lat_dist_to_target_mask.index[ap_lat_dist_to_target_mask][0]
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['LatDistToTarget']} is                        FAILED because"
                    f" the value is >= {ap_lat_max_dev.loc[idx]} m at timestamp                        "
                    f" {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[0] = False

            # if abs(ap_long_dist_to_target[idx]) >= ap_long_max_dev[idx] and eval_cond[1]:
            if any(ap_long_dist_to_target_mask):
                idx = ap_long_dist_to_target_mask.index[ap_long_dist_to_target_mask][0]
                evaluation2 = " ".join(
                    f"The evaluation of {signal_name['LongDistToTarget']}                         is FAILED because"
                    f" the value is >= {ap_long_max_dev.loc[idx]} m at timestamp                        "
                    f" {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[1] = False

            # if abs(ap_yaw_diff_to_target[idx]) >= ap_yaw_max_dev[idx] and eval_cond[2]:
            if any(ap_yaw_diff_to_target_mask):
                idx = ap_yaw_diff_to_target_mask.index[ap_yaw_diff_to_target_mask][0]
                evaluation3 = " ".join(
                    f"The evaluation of {signal_name['YawDiffToTarget']}                         is FAILED because"
                    f" the value is >= {ap_yaw_max_dev.loc[idx]} rad at timestamp                        "
                    f" {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[2] = False
            if all(eval_cond):
                self.result.measured_result = TRUE
                final_result.step_2 = fc.PASS
            else:
                self.result.measured_result = FALSE
                final_result.step_2 = fc.FAIL

        else:
            final_result.step_2 = fc.NOT_ASSESSED
            self.result.measured_result = DATA_NOK
            # eval_cond = [False] * 8
            evaluation1 = f"Evaluation not possible, ({signal_name['ReachedStatus']} was not > 0 for 0.8s)."
            evaluation2 = f"Evaluation not possible, ({signal_name['ReachedStatus']} was not > 0 for 0.8s)."
            evaluation3 = f"Evaluation not possible, ({signal_name['ReachedStatus']} was not > 0 for 0.8s)."

        self.test_result = final_result.step_2
        signal_summary[signal_name["LatDistToTarget"]] = evaluation1
        signal_summary[signal_name["LongDistToTarget"]] = evaluation2
        signal_summary[signal_name["YawDiffToTarget"]] = evaluation3
        remark = " ".join(
            "Check that target pose deviation signals are below defined thresholds (check is done                    "
            " after .targetPosesPort.selectedPoseData.reachedStatus > 0 for 0.8s until end of sim).".split()
        )
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.result.measured_result in [FALSE, DATA_NOK] or bool(GeneralConstants.ACTIVATE_PLOTS):
            self.fig = go.Figure()

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
                    y=ap_long_dist_to_target.values.tolist(),
                    mode="lines",
                    name=signal_name["LongDistToTarget"],
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
                    y=ap_lat_max_dev.values.tolist(),
                    mode="lines",
                    name=signal_name["LatMaxDeviation"],
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
                    y=ap_yaw_max_dev.values.tolist(),
                    mode="lines",
                    name=signal_name["YawMaxDeviation"],
                )
            )
            self.fig.add_trace(
                go.Scatter(x=ap_time.values.tolist(), y=reached_status, mode="lines", name=signal_name["ReachedStatus"])
            )
            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

        verdict, color = final_result.check_result()

        # T10: "AP.headUnitVisualizationPort.screen_nu" == 17
        # for idx, val in enumerate(head_unit_screen):
        #     if val == GeneralConstants.MANEUVER_ACTIVE:
        #         T10 = idx
        #         break
        if np.any(head_unit_screen == GeneralConstants.MANEUVER_ACTIVE):
            T10 = np.argmax(head_unit_screen == GeneralConstants.MANEUVER_ACTIVE)

        # T15: "AP.headUnitVisualizationPort.screen_nu" == 5
        # for i, val in enumerate(head_unit_screen):
        #     if val == GeneralConstants.MANEUVER_FINISH:
        #         T15 = i
        #         break
        if np.any(head_unit_screen == GeneralConstants.MANEUVER_FINISH):
            T15 = np.argmax(head_unit_screen == GeneralConstants.MANEUVER_FINISH)

        # T11: "AP.targetPosesPort.selectedPoseData.reachedStatus" >0 for 0.8 sec
        for idx, val in enumerate(reached_status):
            if val > 0:
                if idx_last is not None:
                    total_time += (idx - idx_last) / GeneralConstants.IDX_TO_S
                    if first_valid_index is None:
                        first_valid_index = idx
                    if round(total_time, 6) >= GeneralConstants.T_POSE_REACHED:
                        T11 = first_valid_index
                        break
                idx_last = idx
            else:
                idx_last = None
                total_time = 0

        # T12: "AP.planningCtrlPort.apStates" == 3
        # for i, val in enumerate(ap_state):
        #     if val == GeneralConstants.AP_AVG_ACTIVE_IN:
        #         T12 = i
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
            max_yaw_rate = np.around(np.amax(np.abs(np.rad2deg(vhcl_yaw_rate.iloc[T12:]))), 3)
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

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {"value": verdict.title(), "color": color},
            "SimulationTime[s]": {"value": sim_time, "color": fh.apply_color(sim_time, 200, "<", 20, ">=<=")},
            "Time for Parking[s]": {
                "value": time_for_parking,
                "color": fh.apply_color(time_for_parking, 200, "<", 20, ">=<="),
            },
            "max Car.ay[m/s^2]": {"value": max_car_ay, "color": fh.apply_color(max_car_ay, 1, "<", 0.5, ">=<=")},
            "max YawRate[deg/s]": {"value": max_yaw_rate, "color": fh.apply_color(max_yaw_rate, 25, "<", 10, ">=<=")},
            "max VehicleSpeed [m/s]": {"value": max_speed, "color": fh.apply_color(max_speed, 2.7, "<", 1.35, ">=<=")},
            "mean VehicleSpeed [m]": {"value": mean_speed, "color": fh.apply_color(mean_speed, 0.3, ">", 0.5, ">=<=")},
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


@testcase_definition(
    name="MF TRJCTL",
    description=(
        f"Check if the KPI for TRJCTL is passed between 'AP{signals_obj._properties[MfSignals.Columns.APSTATE]}       "
        " ' == 3 and end of sim.         Check if the KPI for TRJCTL is passed between"
        f" 'AP{signals_obj._properties[MfSignals.Columns.REACHEDSTATUS]}' >0        for 0.8 s and end of sim."
    ),
)
class FtParkingTrajctl(TestCase):
    """TRJCTL test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [TestStepFtParkingTrajctl, TestStepFtParkingTrajctl2]
