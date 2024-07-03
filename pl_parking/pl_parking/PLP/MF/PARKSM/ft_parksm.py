"""PARKSM TEST for mf_sil."""

import logging
import os
import sys

import numpy as np
import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
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
from pl_parking.PLP.MF.constants import GeneralConstants, PlotlyTemplate

SIGNAL_DATA = "MF_PARKSM"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="PARKSM",
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TestStepFtParkingParkSM(TestStep):
    """Test step that checks if it takes less than 200s to start and complete the maneuver.
    Check if AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and
    AP.headUnitVisualizationPort.screen_nu ==5(MANEUVER_FINISHED) are within 200 s.
    """

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """
        This function processes data related to head unit visualization screens and generates plots and remarks based on the
        evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        read_data = self.readers[SIGNAL_DATA].signals
        self.test_result = fc.INPUT_MISSING  # Result

        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        evaluation = None
        signal_summary = {}

        # index of time signal when the trigger value of 'Ap.headUnitVisualizationPort.screen_nu' = 17(MANEUVER_ACTIVE)
        idx_threshold_one = None
        # index of time signal when the trigger value of 'Ap.headUnitVisualizationPort.screen_nu' = 5(MANEUVER_FINISHED)
        idx_threshold_two = None

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
        time_for_parking = None
        sim_time = None
        T10 = None
        T11 = None
        T12 = None
        T15 = None
        idx_last = None
        total_time = 0
        first_valid_index = None
        signal_name = example_obj._properties

        head_unit_screen = read_data["headUnitVisu_screen_nu"]
        ap_time = read_data["time"].values.tolist()
        car_ay = read_data["Car_ay"].values.tolist()
        ap_state = read_data["ApState"].values.tolist()
        reached_status = read_data["ReachedStatus"].values.tolist()
        vhcl_yawrate = read_data["VhclYawRate"].values.tolist()
        vhcl_v = read_data["Vhcl_v"].values.tolist()
        car_ax = read_data["Car_ax"].values.tolist()
        ap_lat_dist_to_target = read_data["LatDistToTarget"].values.tolist()
        ap_long_dist_to_target = read_data["LongDistToTarget"].values.tolist()
        ap_yaw_diff_to_target = read_data["YawDiffToTarget"].values.tolist()
        ap_orientation_error = read_data["OrientationError"].values.tolist()
        ap_current_deviation = read_data["LateralError"].values.tolist()
        ap_wheel_angle_acceleration = read_data["wheelAngleAcceleration"].values.tolist()
        ap_driving_mode = read_data["ApDrivingModeReq"].values.tolist()
        ap_traj_ctrl_active = read_data["ApTrajCtrlActive"].values.tolist()
        ap_traj_request_port = read_data["trajCtrlRequestPort"].values.tolist()
        ap_state_var_ppc = read_data["stateVarPPC"].values.tolist()
        ap_state_var_esm = read_data["stateVarESM"].values.tolist()
        ap_state_var_vsm = read_data["stateVarVSM"].values.tolist()
        ap_state_var_dm = read_data["stateVarDM"].values.tolist()
        ap_state_var_rdm = read_data["stateVarRDM"].values.tolist()

        # T10: "AP.headUnitVisualizationPort.screen_nu" == 17
        if np.any(head_unit_screen == GeneralConstants.MANEUVER_ACTIVE):
            idx = np.argmax(head_unit_screen == GeneralConstants.MANEUVER_ACTIVE)
            idx_threshold_one = ap_time[idx]
            T10 = idx

        # T15: "AP.headUnitVisualizationPort.screen_nu" == 5
        if np.any(head_unit_screen == GeneralConstants.MANEUVER_FINISH):
            idx = np.argmax(head_unit_screen == GeneralConstants.MANEUVER_FINISH)
            idx_threshold_two = ap_time[idx]
            T15 = idx

        if idx_threshold_one is not None and idx_threshold_two is not None:
            if idx_threshold_one < 200 and idx_threshold_two < 200:
                self.test_result = fc.PASS
                evaluation = " ".join(
                    f"The condition for {signal_name['headUnitVisu_screen_nu']} is PASSED,                             "
                    f"            with values for MANEUVER_ACTIVE({GeneralConstants.MANEUVER_ACTIVE})                  "
                    f"                       and MANEUVER_FINISH({GeneralConstants.MANEUVER_FINISH})                   "
                    "                      both within 200 s.".split()
                )
            else:
                self.test_result = fc.FAIL
                evaluation = " ".join("The condition is FAILED, the time was > 200 s.".split())
        else:
            self.test_result = fc.NOT_ASSESSED
            if idx_threshold_two is None and idx_threshold_one is None:
                evaluation = " ".join(
                    "The condition is FAILED, the values                                        "
                    f" MANEUVER_ACTIVE({GeneralConstants.MANEUVER_ACTIVE}) and                                        "
                    f" MANEUVER_FINISH({GeneralConstants.MANEUVER_FINISH}) were never found".split()
                )
            elif idx_threshold_one is None:
                evaluation = " ".join(
                    "Evaluation not possible, the value                                        "
                    f" MANEUVER_ACTIVE({GeneralConstants.MANEUVER_ACTIVE}) was never found".split()
                )
            elif idx_threshold_two is None:
                evaluation = " ".join(
                    "Evaluation not possible, the value                                        "
                    f" MANEUVER_FINISH({GeneralConstants.MANEUVER_FINISH}) was never found".split()
                )

        signal_summary[signal_name["headUnitVisu_screen_nu"]] = evaluation
        remark = " ".join(
            "Check if it takes less than 200s to start and complete the maneuver. Check if                           "
            " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE)                           and"
            " AP.headUnitVisualizationPort.screen_nu == 5(MANEUVER_FINISHED) are within 200 s.".split()
        )
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif self.test_result == fc.NOT_ASSESSED:
            self.result.measured_result = DATA_NOK
        else:
            self.result.measured_result = FALSE

        if self.result.measured_result in [FALSE, DATA_NOK] or bool(GeneralConstants.ACTIVATE_PLOTS):
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=ap_time, y=car_ax, mode="lines", name=signal_name["Car_ax"]))
            fig.add_trace(go.Scatter(x=ap_time, y=car_ay, mode="lines", name=signal_name["Car_ay"]))
            fig.add_trace(go.Scatter(x=ap_time, y=vhcl_v, mode="lines", name=signal_name["Vhcl_v"]))
            fig.add_trace(
                go.Scatter(x=ap_time, y=ap_long_dist_to_target, mode="lines", name=signal_name["LongDistToTarget"])
            )
            fig.add_trace(
                go.Scatter(x=ap_time, y=ap_lat_dist_to_target, mode="lines", name=signal_name["LatDistToTarget"])
            )
            fig.add_trace(
                go.Scatter(x=ap_time, y=ap_yaw_diff_to_target, mode="lines", name=signal_name["YawDiffToTarget"])
            )
            fig.add_trace(go.Scatter(x=ap_time, y=vhcl_yawrate, mode="lines", name=signal_name["VhclYawRate"]))
            fig.add_trace(go.Scatter(x=ap_time, y=ap_state, mode="lines", name=signal_name["ApState"]))
            fig.add_trace(go.Scatter(x=ap_time, y=reached_status, mode="lines", name=signal_name["ReachedStatus"]))
            fig.layout = go.Layout(yaxis=dict(tickformat="20"), xaxis=dict(tickformat="20"), xaxis_title="Time[s]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            fig.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="Evaluation 1",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

            fig2 = go.Figure()
            fig2.add_trace(
                go.Scatter(
                    x=ap_time, y=ap_wheel_angle_acceleration, mode="lines", name=signal_name["wheelAngleAcceleration"]
                )
            )
            fig2.layout = go.Layout(yaxis=dict(tickformat="20"), xaxis=dict(tickformat="20"), xaxis_title="Time[s]")
            fig2.update_traces(showlegend=True, name=signal_name["wheelAngleAcceleration"])
            fig2.update_layout(PlotlyTemplate.lgt_tmplt)
            fig2.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="Steering wheel angle acceleration",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append("")
            plots.append(fig2)
            remarks.append("")

            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=ap_time, y=ap_state, mode="lines", name=signal_name["ApState"]))
            fig3.layout = go.Layout(yaxis=dict(tickformat="20"), xaxis=dict(tickformat="20"), xaxis_title="Time[s]")
            fig3.update_traces(showlegend=True, name=signal_name["ApState"])
            fig3.update_layout(PlotlyTemplate.lgt_tmplt)
            fig3.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="Planning control port",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append("")
            plots.append(fig3)
            remarks.append("")

            fig4 = go.Figure()
            fig4.add_trace(go.Scatter(x=ap_time, y=ap_driving_mode, mode="lines", name=signal_name["ApDrivingModeReq"]))
            fig4.add_trace(
                go.Scatter(x=ap_time, y=ap_traj_ctrl_active, mode="lines", name=signal_name["ApTrajCtrlActive"])
            )
            fig4.add_trace(
                go.Scatter(x=ap_time, y=ap_traj_request_port, mode="lines", name=signal_name["trajCtrlRequestPort"])
            )
            fig4.layout = go.Layout(yaxis=dict(tickformat="20"), xaxis=dict(tickformat="20"), xaxis_title="Time[s]")
            fig4.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(fig4)
            remarks.append("")
            fig4.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="Driving mode request",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            fig5 = go.Figure()
            fig5.add_trace(go.Scatter(x=ap_time, y=ap_state_var_ppc, mode="lines", name=signal_name["stateVarPPC"]))
            fig5.add_trace(go.Scatter(x=ap_time, y=ap_state_var_esm, mode="lines", name=signal_name["stateVarESM"]))
            fig5.add_trace(go.Scatter(x=ap_time, y=ap_state_var_vsm, mode="lines", name=signal_name["stateVarVSM"]))
            fig5.add_trace(go.Scatter(x=ap_time, y=ap_state_var_dm, mode="lines", name=signal_name["stateVarDM"]))
            fig5.add_trace(go.Scatter(x=ap_time, y=ap_state_var_rdm, mode="lines", name=signal_name["stateVarRDM"]))
            fig5.layout = go.Layout(yaxis=dict(tickformat="20"), xaxis=dict(tickformat="20"), xaxis_title="Time[s]")
            fig5.update_layout(PlotlyTemplate.lgt_tmplt)
            fig5.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x=0,
                    y=-0.12,
                    showarrow=False,
                    text="PARKSM PPC state",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )
            plot_titles.append("")
            plots.append(fig5)
            remarks.append("")

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
        if np.any(ap_state == GeneralConstants.AP_AVG_ACTIVE_IN):
            T12 = np.argmax(ap_state == GeneralConstants.AP_AVG_ACTIVE_IN)

        # calc for every element in the table
        if T10 is not None and T15 is not None:
            time_for_parking = round(abs(ap_time[T15] - ap_time[T10]), 3)
        else:
            time_for_parking = "n.a"

        if T12 is not None:
            max_car_ay = np.around(np.amax(np.abs(car_ay[T12:])), 3)
            max_car_ax = np.around(np.amax(np.abs(car_ax[T12:])), 3)
            max_speed = np.around(np.amax(np.abs(vhcl_v[T12:])), 3)
            max_yaw_rate = np.around(np.amax(np.abs(np.rad2deg(vhcl_yawrate[T12:]))), 3)
            max_or_err = np.around(np.amax(np.abs(np.rad2deg(ap_orientation_error[T12:]))), 3)
            max_current_dev = np.around(np.amax(np.abs(ap_current_deviation[T12:])), 3)
            sim_time = round(max(ap_time[T12:]), 3)
        else:
            max_car_ay = "n.a"
            max_car_ax = "n.a"
            max_speed = "n.a"
            max_yaw_rate = "n.a"
            max_or_err = "n.a"
            max_current_dev = "n.a"
            sim_time = "n.a"

        if T12 is not None and T15 is not None:
            mean_speed = np.around(np.mean(np.abs(vhcl_v[T12:T15])), 3)
        else:
            mean_speed = "n.a"

        if T11 is not None:
            max_lat_dist = np.around(np.amax(np.abs(ap_lat_dist_to_target[T11:])), 3)
            max_long_dist = np.around(np.amax(np.abs(ap_long_dist_to_target[T11:])), 3)
            max_yaw_diff = np.around(np.amax(np.rad2deg(np.abs(ap_yaw_diff_to_target[T11:]))), 3)
        else:
            max_lat_dist = "n.a"
            max_long_dist = "n.a"
            max_yaw_diff = "n.a"

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {"value": self.test_result.title(), "color": fh.get_color(self.test_result)},
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
    name="MF PARKSM",
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
)
class FtParkingParkSM(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [TestStepFtParkingParkSM]
