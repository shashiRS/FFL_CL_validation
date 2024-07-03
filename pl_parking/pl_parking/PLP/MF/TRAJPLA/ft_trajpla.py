"""TRAJPLA functional test"""

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
from pl_parking.PLP.MF.constants import ConstantsTrajpla, GeneralConstants, PlotlyTemplate

SIGNAL_DATA = "MF_TRAJPLA"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="TRAJPLA",
    description=(
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TestStepFtParkingTrajpla(TestStep):
    """Test step class"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        t2 = None
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        read_data = self.readers[SIGNAL_DATA].signals
        self.test_result = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_summary = {}
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

        ap_state = read_data["ApState"]
        act_nr_strokes_greater_max_nr_strokes = read_data["ActNbStrokesGreaterMaxNbStrokes"]
        vhcl_v = read_data["Vhcl_v"]
        ap_time = read_data["time"]
        car_ay = read_data["Car_ay"]
        reached_status = read_data["ReachedStatus"].values.tolist()
        vhcl_yawrate = read_data["VhclYawRate"]
        car_ax = read_data["Car_ax"]
        ap_lat_dist_to_target = read_data["LatDistToTarget"]
        ap_long_dist_to_target = read_data["LongDistToTarget"]
        ap_yaw_diff_to_target = read_data["YawDiffToTarget"]
        ap_orientation_error = read_data["OrientationError"]
        ap_current_deviation = read_data["LateralError"]
        head_unit_screen = read_data["headUnitVisu_screen_nu"]
        ap_nr_crev_steps = read_data["NbCrevSteps"]

        if np.any(ap_state == GeneralConstants.AP_AVG_ACTIVE_IN):
            t2 = np.argmax(ap_state == GeneralConstants.AP_AVG_ACTIVE_IN)

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['NbCrevSteps']} is PASSED,             with values ="
            f" {ConstantsTrajpla.NB_CRV_STEPS_FALSE}.".split()
        )
        evaluation2 = " ".join(
            f"The evaluation of {signal_name['ActNbStrokesGreaterMaxNbStrokes']} is PASSED,             with values ="
            f" {ConstantsTrajpla.ACT_NB_STROKES_GREATER_MAX_NB_STROKES_FALSE}.".split()
        )
        evaluation3 = " ".join(
            f"The evaluation of {signal_name['Vhcl_v']} is PASSED,             with values <"
            f" {round(GeneralConstants.V_MAX_L3, 3)} m/s.".split()
        )
        if t2 is not None:
            eval_cond = [True] * 3
            ap_nr_crev_steps_mask = ap_nr_crev_steps.iloc[t2:] != ConstantsTrajpla.NB_CRV_STEPS_FALSE
            act_nr_strokes_greater_max_nr_strokes_mask = (
                act_nr_strokes_greater_max_nr_strokes.iloc[t2:]
                != ConstantsTrajpla.ACT_NB_STROKES_GREATER_MAX_NB_STROKES_FALSE
            )

            vhcl_v_mask = vhcl_v.iloc[t2:] >= GeneralConstants.V_MAX_L3

            if any(ap_nr_crev_steps_mask):
                idx = ap_nr_crev_steps_mask.index[ap_nr_crev_steps_mask][0]
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['NbCrevSteps']} is FAILED because                            "
                    f" the value is != 0 at timestamp {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[0] = False
            if any(act_nr_strokes_greater_max_nr_strokes_mask):
                idx = act_nr_strokes_greater_max_nr_strokes_mask.index[act_nr_strokes_greater_max_nr_strokes_mask][0]
                evaluation2 = " ".join(
                    f"The evaluation of {signal_name['ActNbStrokesGreaterMaxNbStrokes']} is                        "
                    f"     FAILED because the value is != 0 at timestamp {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[1] = False
            if any(vhcl_v_mask):
                idx = vhcl_v_mask.index[vhcl_v_mask][0]
                evaluation3 = " ".join(
                    f"The evaluation of {signal_name['Vhcl_v']} is FAILED because                                  "
                    f"       it has the max value equal to {vhcl_v.loc[idx]} m/s,                                      "
                    f"   and max accepted value is {round(GeneralConstants.V_MAX_L3, 3)} m/s.".split()
                )
                eval_cond[2] = False

            if all(eval_cond):
                self.test_result = fc.PASS
            else:
                self.test_result = fc.FAIL
        else:
            self.test_result = fc.NOT_ASSESSED
            evaluation1 = evaluation2 = evaluation3 = " ".join(
                "Evaluation not possible, the trigger value AP_AVG_ACTIVE_IN(3) for                            "
                f" {signal_name['ApState']} was never found.".split()
            )

        signal_summary[signal_name["NbCrevSteps"]] = evaluation1
        signal_summary[signal_name["ActNbStrokesGreaterMaxNbStrokes"]] = evaluation2
        signal_summary[signal_name["Vhcl_v"]] = evaluation3
        remark = " ".join(
            "Check that after .planningCtrlPort.apStates == 3, the speed does not exceed the accepted            "
            " value, number of strokes does not exceed the maximum accepted value and number of curvature steps is 0..".split()
        )
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif self.test_result == fc.FAIL:
            self.result.measured_result = FALSE
        else:
            self.result.measured_result = DATA_NOK

        if self.result.measured_result in [FALSE, DATA_NOK] or bool(GeneralConstants.ACTIVATE_PLOTS):
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(), y=ap_state.values.tolist(), mode="lines", name=signal_name["ApState"]
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=act_nr_strokes_greater_max_nr_strokes.values.tolist(),
                    mode="lines",
                    name=signal_name["ActNbStrokesGreaterMaxNbStrokes"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=ap_nr_crev_steps.values.tolist(),
                    mode="lines",
                    name=signal_name["NbCrevSteps"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(), y=vhcl_v.values.tolist(), mode="lines", name=signal_name["Vhcl_v"]
                )
            )
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        if np.any(head_unit_screen == GeneralConstants.MANEUVER_ACTIVE):
            T10 = np.argmax(head_unit_screen == GeneralConstants.MANEUVER_ACTIVE)
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
        T12 = t2

        # T15: "AP.headUnitVisualizationPort.screen_nu" == 5
        if np.any(head_unit_screen == GeneralConstants.MANEUVER_FINISH):
            T15 = np.argmax(head_unit_screen == GeneralConstants.MANEUVER_FINISH)

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
    name="MF TRAJPLA",
    description=(
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
)
class FtParkingTrajpla(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [TestStepFtParkingTrajpla]
