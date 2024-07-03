#!/usr/bin/env python3
"""VEDODO TestCase."""

import math
import os
import sys

import numpy as np
import plotly.graph_objects as go

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))  # nopep8
if TRC_ROOT not in sys.path:  # nopep8
    sys.path.append(TRC_ROOT)  # nopep8

import logging

# nopep8
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult  # nopep8

# nopep8
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)

import pl_parking.common_constants as fc  # nopep8
import pl_parking.common_ft_helper as fh  # nopep8
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    rep,  # nopep8
)
from pl_parking.PLP.MF.constants import ConstantsVedodo, GeneralConstants, PlotlyTemplate

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

SIGNAL_DATA = "MF_VEDODO"

example_obj = fh.MfSignals()


@teststep_definition(
    step_number=1,
    name="VEDODO",
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, fh.MfSignals)
class TestStepVedodo(TestStep):
    """Vedodo Test Step definition."""

    custom_report = MfCustomTeststepReport

    @staticmethod
    def calc_odo_error(x_gt, y_gt, psi_gt, psi_odo, x_odo, y_odo):
        """Method from mf_sil repository-> AUP_EVAL_STET_KPIs_L1_L3.py
        Calculates longitudinal and lateral error.
        """
        leng = len(x_gt)
        drivenDist_m = 0.0
        drivenDist_arr_m = np.zeros(leng)
        abs_err_long_m = np.zeros(leng)
        abs_err_lat_m = np.zeros(leng)
        abs_err_yaw_rad = np.zeros(leng)
        relErrLong_perc = np.zeros(leng)
        relErrLat_perc = np.zeros(leng)
        relErrYaw = np.zeros(leng)

        if len(x_gt) == len(y_gt) == len(psi_gt) == len(x_odo) == len(y_odo) == len(psi_odo):
            for idx, val in enumerate(psi_gt):
                p_gt = [[x_gt[idx]], [y_gt[idx]]]
                p_odo = [[x_odo[idx]], [y_odo[idx]]]
                p_gt_ll = p_gt
                """Calculate orthogonal point - Lotpunkt"""
                a = np.array([[math.cos(val), -math.sin(val)], [math.sin(val), math.cos(val)]])  # val = psi_gt[idx]

                b = np.subtract(p_odo, p_gt)
                x = np.matmul(np.linalg.inv(a), b)
                lp = p_gt + np.multiply(x[0], [[math.cos(val)], [math.sin(val)]])

                """Calculate absolute error"""
                abs_err_long_m[idx] = np.linalg.norm(np.subtract(lp, p_gt))
                abs_err_lat_m[idx] = np.linalg.norm(np.subtract(lp, p_odo))
                abs_err_yaw_rad[idx] = np.abs(np.subtract(psi_odo[idx], val))  # val = psi_gt[idx]

                """Calculate driven distance"""
                if idx > 0:
                    # delta_Dist_m = np.linalg.norm(np.subtract(p_gt, p_gt_ll))
                    drivenDist_m = drivenDist_m + np.linalg.norm(np.subtract(p_gt, p_gt_ll))
                    drivenDist_arr_m[idx] = drivenDist_m
                # p_gt_ll = p_gt

                """Calculate relative error"""
                if drivenDist_m != 0.0:
                    relErrLong_perc[idx] = abs_err_long_m[idx] / drivenDist_m * 100.0
                    relErrLat_perc[idx] = abs_err_lat_m[idx] / drivenDist_m * 100.0
                    relErrYaw[idx] = abs_err_yaw_rad[idx] / drivenDist_m
                else:
                    relErrLong_perc[idx] = 0.0
                    relErrLat_perc[idx] = 0.0
                    relErrYaw[idx] = 0.0

        return (
            abs_err_long_m,
            abs_err_lat_m,
            relErrLong_perc,
            relErrLat_perc,
            abs_err_yaw_rad,
            drivenDist_arr_m,
            relErrYaw,
        )

    @staticmethod
    def check_yaw_rate_cond(odo_yaw_rate_radps, car_yaw_rate_radps, idx) -> tuple:
        """NOT(ABS(DIFF(NP_rad2deg(""AP.odoEstimationPort.yawRate_radps""),NP_rad2deg(""Car.YawRate"")))>
        "&YawRateVEDODO_max&" for 500ms).
        """
        MS_IN_S = 1000
        diff_yaw_rate = abs(np.rad2deg(odo_yaw_rate_radps[idx:]) - np.rad2deg(car_yaw_rate_radps[idx:]))

        total_time = 0
        idx_last = None
        yaw_rate_idx = None

        for indx, val in enumerate(diff_yaw_rate):
            if val > ConstantsVedodo.THRESHOLD_YAW_RATE:
                if idx_last is not None:
                    # to be updated
                    total_time += indx - idx_last
                    if (
                        round(total_time, ConstantsVedodo.NB_DECIMALS)
                        >= ConstantsVedodo.TIME_THRESHOLD_YAW_RATE_MS / MS_IN_S
                    ):
                        yaw_rate_idx = indx
                        # return False, indx
                        return False, yaw_rate_idx

                idx_last = indx
            else:
                total_time = 0
                idx_last = None
        return True, None

    # ==================================================================================
    # Implementation of scipy.signal.savgol_filter
    # ==================================================================================
    @staticmethod
    def savitzky_golay(y, window_size, order, deriv=0, rate=1):
        """A Savitzky Golay filter is a digital filter that can be applied to a set of digital data points for the
        purpose of smoothing the data, that is, to increase the precision of the data without distorting the
        signal tendency. This is achieved, in a process known as convolution, by fitting successive sub-sets of
        adjacent data points with a low-degree polynomial by the method of linear least squares
        """
        try:
            window_size = np.abs(np.int(window_size))
            order = np.abs(np.int(order))
        except ValueError:
            raise ValueError("window_size and order have to be of type int")  # noqa: B904
        if window_size % 2 != 1 or window_size < 1:
            raise TypeError("window_size size must be a positive odd number")
        if window_size < order + 2:
            raise TypeError("window_size is too small for the polynomials order")
        order_range = range(order + 1)
        half_window = (window_size - 1) // 2
        # precompute coefficients
        b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window + 1)])
        m = np.linalg.pinv(b).A[deriv] * rate**deriv * math.factorial(deriv)
        # pad the signal at the extremes with
        # values taken from the signal itself
        firstvals = y[0] - np.abs(y[1 : half_window + 1][::-1] - y[0])
        lastvals = y[-1] + np.abs(y[-half_window - 1 : -1][::-1] - y[-1])
        y = np.concatenate((firstvals, y, lastvals))
        return np.convolve(m[::-1], y, mode="valid")

    # ========================================================================================================
    # iterating  a dynamic sliding window with a default value of delta_dist along the distance array and get
    # the max error value in every iteration
    # ========================================================================================================
    @staticmethod
    def maxError_distWindow(r1, r2, delta_dist):
        """r1 - distance, r2 - error"""
        b = len(r1)
        MaxValueYEachIt = np.zeros(b)  # Preallocate array

        for i in range(b):
            ind = np.searchsorted(r1, r1[i] + delta_dist, side="right")  # Find the index using binary search
            ind_arr = min(ind - 1, b - 1)  # Ensure index is within bounds

            if i != ind_arr:
                MaxValueYEachIt[i] = np.amax(r2[i : ind_arr + 1])
            else:
                MaxValueYEachIt[i] = np.amax(r2[i : ind + 1])

        return MaxValueYEachIt

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        plot_titles, plots, remarks = rep([], 3)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        read_data = self.readers[SIGNAL_DATA].signals
        self.test_result = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)

        maxOdoErrX_m = None
        maxOdoErrY_m = None
        maxOdoErrYaw_deg = None

        signal_summary = {}
        t2 = None
        signal_name = example_obj._properties

        ap_odo_cm_ref_x_pos_m = read_data["ApOdoCmRefXPosM"].tolist()
        ap_odo_cm_ref_y_pos_m = read_data["ApOdoCmRefYPosM"].tolist()
        ap_odo_cm_ref_yaw_ang_rad = read_data["ApOdoCmRefYawAngRad"].tolist()
        ap_odo_estim_yaw_ang_rad = read_data["ApOdoEstimYawAngRad"].tolist()
        ap_odo_estim_x_pos_m = read_data["ApOdoEstimXPosM"].tolist()
        ap_odo_estim_y_pos_m = read_data["ApOdoEstimYPosM"].tolist()
        ap_odo_estim_yaw_rate_radps = read_data["ApOdoEstimYawRateRadps"].tolist()
        longi_velocity = read_data["longiVelocity"].tolist()
        steer_ang_front_axle_rad = read_data["steerAngFrontAxle_rad"].tolist()
        motion_status_nu = read_data["motionStatus_nu"].tolist()
        steering_wheel_angle_rad = read_data["steeringWheelAngle_rad"].tolist()
        steering_wheel_angle_velocity_radps = read_data["steeringWheelAngleVelocity_radps"].tolist()
        lateral_acceleration_mps2 = read_data["lateralAcceleration_mps2"].tolist()
        longitudinal_acceleration_mps2 = read_data["longitudinalAcceleration_mps2"].tolist()
        yaw_rate_radps = read_data["yawRate_radps"].tolist()
        car_yaw_rate = read_data["CarYawRate"].tolist()
        car_vx = read_data["Car_vx"].tolist()
        car_ax = read_data["Car_ax"].tolist()
        car_ay = read_data["Car_ay"].tolist()
        lat_slope = read_data["LatSlope"].tolist()
        long_slope = read_data["LongSlope"].tolist()
        pitch_angle_rad = read_data["pitchAngle_rad"].tolist()
        ap_time = read_data["time"].tolist()
        # headUnitVisu_screen_nu = read_data['headUnitVisu_screen_nu'].tolist()

        """Calculate Odometry Error"""
        (
            abs_err_long_m,
            abs_err_lat_m,
            relErrLong_perc,
            relErrLat_perc,
            abs_err_yaw_rad,
            drivenDist_arr_m,
            relErrYaw,
        ) = self.calc_odo_error(
            ap_odo_cm_ref_x_pos_m,
            ap_odo_cm_ref_y_pos_m,
            ap_odo_cm_ref_yaw_ang_rad,
            ap_odo_estim_yaw_ang_rad,
            ap_odo_estim_x_pos_m,
            ap_odo_estim_y_pos_m,
        )

        """convert the Yaw in degree"""
        abs_err_yaw_deg = np.around(np.rad2deg(abs_err_yaw_rad), ConstantsVedodo.NB_DECIMALS)

        latErr_1m_VS = self.maxError_distWindow(
            drivenDist_arr_m, abs_err_lat_m, ConstantsVedodo.SLIDE_WINDOW_DISTANCE_1
        )
        absErrYaw_1m_VS = self.maxError_distWindow(
            drivenDist_arr_m, abs_err_yaw_deg, ConstantsVedodo.SLIDE_WINDOW_DISTANCE_1
        )
        longErr_1m_VS = self.maxError_distWindow(
            abs_err_long_m, abs_err_long_m, ConstantsVedodo.SLIDE_WINDOW_DISTANCE_1
        )

        """ignore the first samples, because they might not be relevant"""
        for idx, val in enumerate(ap_time):
            if val > ConstantsVedodo.THRESHOLD_TIME_S:
                t2 = idx
                break

        if t2 is not None:
            idx = t2
            odo_yaw_rate_radps = ap_odo_estim_yaw_rate_radps[idx:]
            car_yaw_rate_radps = car_yaw_rate[idx:]

            maxOdoErrX_m = np.around(np.amax(np.abs(abs_err_long_m[t2:])), 3)
            maxOdoErrY_m = np.around(np.amax(np.abs(abs_err_lat_m[t2:])), 3)
            maxOdoErrYaw_deg = np.around(np.amax(abs_err_yaw_deg), 3)

            evaluation1 = " ".join(
                f"Evaluation for abs_err_long_m is PASSED, with values < {ConstantsVedodo.MAX_ERR_DIST_M}".split()
            )
            evaluation2 = " ".join(
                f"Evaluation for abs_err_lat_m is PASSED, with values < {ConstantsVedodo.MAX_ERR_DIST_M}".split()
            )
            evaluation3 = " ".join(
                f"Evaluation for abs_err_yaw_deg is PASSED, with values < {ConstantsVedodo.MAX_ERR_YAW_DEG}".split()
            )
            evaluation4 = " ".join(
                "Evaluation for yaw rate check is PASSED, with difference             <"
                f" {ConstantsVedodo.THRESHOLD_YAW_RATE} for {ConstantsVedodo.THRESHOLD_TIME_S}s".split()
            )
            yawrate_violation_mask, yawrate_violation_timestamp = self.check_yaw_rate_cond(
                odo_yaw_rate_radps, car_yaw_rate_radps, idx
            )
            evaluation5 = " ".join(
                "Evaluation for longErr_1m(Maximum error for 1 m window) is PASSED, with                     values <"
                f" {ConstantsVedodo.MAX_ERR_DIST_M}".split()
            )
            evaluation6 = " ".join(
                "Evaluation for latErr_1m(Maximum error for 1 m window) is PASSED, with                     values <"
                f" {ConstantsVedodo.MAX_ERR_DIST_M}".split()
            )
            evaluation7 = " ".join(
                "Evaluation for absErrYaw_1m(Maximum error for 1 m window) is PASSED, with                     values"
                f" < {ConstantsVedodo.MAX_ERR_YAW_DEG_1M}".split()
            )
            cond_bool = [
                all(abs_err_long_m[idx:] < ConstantsVedodo.MAX_ERR_DIST_M),
                all(abs_err_lat_m[idx:] < ConstantsVedodo.MAX_ERR_DIST_M),
                all(abs_err_yaw_deg[idx:] < ConstantsVedodo.MAX_ERR_YAW_DEG),
                yawrate_violation_mask,
                all(longErr_1m_VS[idx:] < ConstantsVedodo.MAX_ERR_DIST_M),
                all(latErr_1m_VS[idx:] < ConstantsVedodo.MAX_ERR_DIST_M),
                all(absErrYaw_1m_VS[idx:] < ConstantsVedodo.MAX_ERR_YAW_DEG_1M),
            ]

            if all(cond_bool):
                self.test_result = fc.PASS
            else:
                self.test_result = fc.FAIL

            if cond_bool[0] is False:
                violation_mask = abs_err_long_m[idx:] >= ConstantsVedodo.MAX_ERR_DIST_M
                violation_timestamp = violation_mask.argmax() + idx
                evaluation1 = " ".join(
                    "Evaluation for signal abs_err_long_m is FAILED with value                "
                    f" {abs_err_long_m[violation_timestamp]} m at timestamp {violation_timestamp / 100} ms instead of <"
                    f"                 {ConstantsVedodo.MAX_ERR_DIST_M} m.".split()
                )

            if cond_bool[1] is False:
                violation_mask = abs_err_lat_m[idx:] >= ConstantsVedodo.MAX_ERR_DIST_M
                violation_timestamp = violation_mask.argmax() + idx
                evaluation2 = " ".join(
                    "Evaluation for signal abs_err_lat_m is FAILED with value                "
                    f" {abs_err_lat_m[violation_timestamp]} m at timestamp {violation_timestamp / 100} ms              "
                    f"   instead of < {ConstantsVedodo.MAX_ERR_DIST_M} m.".split()
                )

            if cond_bool[2] is False:
                violation_mask = abs_err_yaw_deg[idx:] >= ConstantsVedodo.MAX_ERR_YAW_DEG
                violation_timestamp = violation_mask.argmax() + idx
                evaluation3 = " ".join(
                    "Evaluation for signal abs_err_yaw_deg is FAILED with value                "
                    f" {abs_err_yaw_deg[violation_timestamp]} deg at timestamp {violation_timestamp / 100} ms instead"
                    f" of                 < {ConstantsVedodo.MAX_ERR_YAW_DEG} deg.".split()
                )

            if cond_bool[3] is False:
                violation_mask = yawrate_violation_mask
                violation_timestamp = yawrate_violation_timestamp
                evaluation4 = " ".join(
                    "Yaw rate check is FAILED, with difference >                "
                    f" {ConstantsVedodo.THRESHOLD_YAW_RATE} for {ConstantsVedodo.THRESHOLD_TIME_S} s at timestamp      "
                    f"           {violation_timestamp / 100} ms.".split()
                )

            if cond_bool[4] is False:
                violation_mask = longErr_1m_VS[idx:] >= ConstantsVedodo.MAX_ERR_DIST_M
                violation_timestamp = violation_mask.argmax() + idx
                evaluation5 = " ".join(
                    "Evaluation for signal longErr_1m(Maximum error for 1 m window) is FAILED with value              "
                    f"   {longErr_1m_VS[violation_timestamp]} m at timestamp {violation_timestamp / 100} ms instead of"
                    f" <                 {ConstantsVedodo.MAX_ERR_DIST_M} m.".split()
                )

            if cond_bool[5] is False:
                violation_mask = latErr_1m_VS[idx:] >= ConstantsVedodo.MAX_ERR_DIST_M
                violation_timestamp = violation_mask.argmax() + idx
                evaluation6 = " ".join(
                    "Evaluation for signal latErr_1m(Maximum error for 1 m window) is FAILED with value               "
                    f"  {latErr_1m_VS[violation_timestamp]} m at timestamp {violation_timestamp / 100} ms              "
                    f"   instead of < {ConstantsVedodo.MAX_ERR_DIST_M} m.".split()
                )

            if cond_bool[6] is False:
                violation_mask = absErrYaw_1m_VS[idx:] >= ConstantsVedodo.MAX_ERR_YAW_DEG_1M
                violation_timestamp = violation_mask.argmax() + idx
                evaluation7 = " ".join(
                    "Evaluation for signal absErrYaw_1m(Maximum error for 1 m window) is FAILED with value            "
                    f"     {absErrYaw_1m_VS[violation_timestamp]} deg at timestamp {violation_timestamp / 100} ms"
                    f" instead of                 < {ConstantsVedodo.MAX_ERR_YAW_DEG_1M} deg.".split()
                )
        else:
            self.test_result = fc.NOT_ASSESSED
            evaluation1 = evaluation2 = evaluation3 = evaluation5 = evaluation6 = evaluation7 = evaluation4 = " ".join(
                f"Evaluation not possible, the trigger value for {signal_name['time']} was not > than                  "
                f"   {ConstantsVedodo.THRESHOLD_TIME_S}".split()
            )
        signal_summary["abs_err_long_m"] = evaluation1
        signal_summary["abs_err_lat_m"] = evaluation2
        signal_summary["abs_err_yaw_deg"] = evaluation3
        signal_summary["yaw rate"] = evaluation4
        signal_summary["longErr_1m(Maximum error for 1 m window)"] = evaluation5
        signal_summary["latErr_1m(Maximum error for 1 m window)"] = evaluation6
        signal_summary["absErrYaw_1m(Maximum error for 1 m window)"] = evaluation7
        # remark = "Check for values after time > 0.05 (THRESHOLD_TIME_S)"
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif self.test_result == fc.FAIL:
            self.result.measured_result = FALSE
        else:
            self.result.measured_result = DATA_NOK

        """Plot the graphics"""
        if self.result.measured_result in [FALSE, DATA_NOK] or bool(GeneralConstants.ACTIVATE_PLOTS):
            if not t2:
                t2 = (
                    0  # this was done in order to be able to see the whole signals on the graphics when t2 is not found
                )

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=ap_time[t2:],
                    y=list(np.array(ap_odo_cm_ref_x_pos_m[t2:]) - ap_odo_cm_ref_x_pos_m[t2]),
                    mode="lines",
                    name=signal_name["ApOdoCmRefXPosM"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time[t2:],
                    y=list(np.array(ap_odo_estim_x_pos_m[t2:]) - ap_odo_estim_x_pos_m[t2]),
                    mode="lines",
                    name=signal_name["ApOdoEstimXPosM"],
                )
            )
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            fig.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="xEgoRACur[m]",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append(" ")
            plots.append(fig)
            remarks.append("")

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=ap_time[t2:],
                    y=list(np.array(ap_odo_estim_y_pos_m[t2:]) - ap_odo_estim_y_pos_m[t2]),
                    mode="lines",
                    name=signal_name["ApOdoEstimYPosM"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time[t2:],
                    y=list(np.array(ap_odo_cm_ref_y_pos_m[t2:]) - ap_odo_cm_ref_y_pos_m[t2]),
                    mode="lines",
                    name=signal_name["ApOdoCmRefYPosM"],
                )
            )
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            fig.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="yEgoRACur[m]",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=ap_time[t2:],
                    y=ap_odo_cm_ref_yaw_ang_rad[t2:],
                    mode="lines",
                    name=signal_name["ApOdoCmRefYawAngRad"],
                )
            )
            fig.add_trace(
                go.Scatter(x=ap_time, y=ap_odo_estim_yaw_ang_rad, mode="lines", name=signal_name["ApOdoEstimYawAngRad"])
            )
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            fig.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="yawAngEgoRaCur[rad]",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ap_time[t2:], y=abs_err_long_m[t2:], mode="lines", name="abs_err_long_m"))
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_traces(showlegend=True, name="abs_err_long_m")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            fig.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="LongitudinalPosError[m]",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append(" ")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ap_time[t2:], y=abs_err_lat_m[t2:], mode="lines", name="abs_err_lat_m"))
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_traces(showlegend=True, name="abs_err_lat_m")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            fig.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="LateralPositionError[m]",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append(" ")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ap_time[t2:], y=abs_err_yaw_deg[t2:], mode="lines", name="abs_err_yaw_deg"))
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_traces(showlegend=True, name="abs_err_yaw_deg")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            fig.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="abs_err_yaw_deg[deg]",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ap_time[t2:], y=car_vx, mode="lines", name=signal_name["Car_vx"]))
            fig.add_trace(
                go.Scatter(x=ap_time[t2:], y=longi_velocity[t2:], mode="lines", name=signal_name["longiVelocity"])
            )
            fig.add_trace(
                go.Scatter(x=ap_time[t2:], y=motion_status_nu[t2:], mode="lines", name=signal_name["motionStatus_nu"])
            )
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            fig.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="Vehicle Velocity[m/s]",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=ap_time[t2:],
                    y=np.rad2deg(steer_ang_front_axle_rad[t2:]),
                    mode="lines",
                    name=signal_name["steerAngFrontAxle_rad"],
                )
            )
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_traces(showlegend=True, name=signal_name["steerAngFrontAxle_rad"])
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            fig.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="Steer Angle[deg]",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=ap_time[t2:],
                    y=np.rad2deg(steering_wheel_angle_rad[t2:]),
                    mode="lines",
                    name=signal_name["steeringWheelAngle_rad"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time[t2:],
                    y=np.rad2deg(steering_wheel_angle_velocity_radps[t2:]),
                    mode="lines",
                    name=signal_name["steeringWheelAngleVelocity_radps"],
                )
            )
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            fig.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="SteeringWheelAngle[deg;deg/s]",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=ap_time[t2:],
                    y=lateral_acceleration_mps2[t2:],
                    mode="lines",
                    name=signal_name["lateralAcceleration_mps2"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time[t2:],
                    y=longitudinal_acceleration_mps2[t2:],
                    mode="lines",
                    name=signal_name["longitudinalAcceleration_mps2"],
                )
            )
            fig.add_trace(go.Scatter(x=ap_time[t2:], y=car_ax, mode="lines", name=signal_name["Car_ax"]))
            fig.add_trace(go.Scatter(x=ap_time[t2:], y=car_ay, mode="lines", name=signal_name["Car_ay"]))
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            fig.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="Acceleration[m/s2]",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=ap_time[t2:], y=np.rad2deg(yaw_rate_radps[t2:]), mode="lines", name=signal_name["yawRate_radps"]
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time[t2:], y=np.rad2deg(car_yaw_rate[t2:]), mode="lines", name=signal_name["CarYawRate"]
                )
            )
            # fig.add_trace(
            #     go.Scatter(x=ap_time[t2:], y=np.rad2deg(ap_odo_estim_yaw_rate_radps[t2:]), mode='lines',
            #                name=signal_ap_odo_estim_yaw_rate_radps))

            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            fig.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="YawRate[deg/s]",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(x=ap_time[t2:], y=np.rad2deg(lat_slope[t2:]), mode="lines", name=signal_name["LatSlope"])
            )
            fig.add_trace(
                go.Scatter(x=ap_time[t2:], y=np.rad2deg(long_slope[t2:]), mode="lines", name=signal_name["LongSlope"])
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time[t2:], y=np.rad2deg(pitch_angle_rad[t2:]), mode="lines", name=signal_name["pitchAngle_rad"]
                )
            )
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            fig.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="Slope[deg]",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ap_time[t2:], y=latErr_1m_VS[t2:], mode="lines", name="latErr_1m_VS"))
            fig.add_trace(go.Scatter(x=ap_time[t2:], y=absErrYaw_1m_VS[t2:], mode="lines", name="absErrYaw_1m_VS"))
            fig.add_trace(go.Scatter(x=ap_time[t2:], y=longErr_1m_VS[t2:], mode="lines", name="longErr_1m_VS"))
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            fig.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="Maximum errors for 1 m window",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {"value": self.test_result.title(), "color": fh.get_color(self.test_result)},
            "SimulationTime[s]": {"value": round(ap_time[-1], 3), "color": fh.apply_color(ap_time[-1], 200, "<")},
            "max longitudinal odo err [m]": {"value": maxOdoErrX_m, "color": fh.apply_color(maxOdoErrX_m, 0, ">=")},
            "max lateral odo err [m]": {"value": maxOdoErrY_m, "color": fh.apply_color(maxOdoErrY_m, 0, ">=")},
            "max yaw odo err [deg]": {"value": maxOdoErrYaw_deg, "color": fh.apply_color(maxOdoErrYaw_deg, 0, ">=")},
            "max lateral odo err (1m)  [m]": {
                "value": round(np.max(latErr_1m_VS[t2:]), 3) if t2 else "None",
                "color": fh.apply_color(np.max(latErr_1m_VS[t2:]), 0, ">=") if t2 else "rgb(33,39,43)",
            },
            "max yaw odo err (1m)  [deg]": {
                "value": round(np.max(absErrYaw_1m_VS[t2:]), 3) if t2 else "None",
                "color": fh.apply_color(np.max(absErrYaw_1m_VS[t2:]), 0, ">=") if t2 else "rgb(33,39,43)",
            },
            "max longitudinal odo err (1m)  [m]": {
                "value": round(np.max(longErr_1m_VS[t2:]), 3) if t2 else "None",
                "color": fh.apply_color(np.max(longErr_1m_VS[t2:]), 0, ">=") if t2 else "rgb(33,39,43)",
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
    name="MF VEDODO",
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
)
class Vedodo(TestCase):
    """Vedodo test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [TestStepVedodo]
