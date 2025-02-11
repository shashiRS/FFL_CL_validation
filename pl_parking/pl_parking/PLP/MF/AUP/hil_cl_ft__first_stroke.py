"""Checking if the ego vehicle does not leave the designated maneuvering area while performing AUP."""

import logging
import os
import sys

import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.io.mdf import MDFSignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import HilClFuntions, MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.constants import PlotlyTemplate

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
from itertools import groupby

SIGNAL_DATA = "MANEUVER_AREA_CHECK_FIRST"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        POS_Y = "Pos_y"
        POS_X = "Pos_x"
        HEADING_ANGLE = "Heading_angle"
        PARKING_CORE_STATE = "Parking_core_state"
        GEAR_STATE = "Gear_state"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.POS_X: "CM.Car.tx",
            self.Columns.POS_Y: "CM.Car.ty",
            self.Columns.HEADING_ANGLE: "CM.Car.Yaw",
            self.Columns.PARKING_CORE_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.GEAR_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralCurrentGear",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Checking the maneuvering trajectory",
    description="Check the maneuvering is correctly happening based on the maneuvering area constrain.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupManeuveringFirstStrokeCheck(TestStep):
    """AupManeuveringFirstStrokeCheck Test Step."""

    custom_report = MfHilClCustomTeststepReport

    def __init__(self):
        """Init test."""
        super().__init__()

    def process(self, **kwargs):
        """
        This function processes the recorded signal from measurement file, set the result of the test,
        generate plots and additional results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        read_data = self.readers[SIGNAL_DATA]
        test_result = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        """Prepare sinals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        pos_x = read_data["Pos_x"]
        pos_y = read_data["Pos_y"]
        ego_heading = read_data["Heading_angle"]
        p_core_state_sig = read_data["Parking_core_state"]
        gear_state_sig = read_data["Gear_state"]

        print(gear_state_sig)

        sorted = []
        for _, group in groupby(
            zip(pos_x, pos_y, ego_heading, p_core_state_sig, gear_state_sig, time_signal),
            key=lambda x: (x[0], x[1], x[2], x[3], x[4]),
        ):
            sorted.append(list(group)[-1])
        pos_x, pos_y, ego_heading, p_core_state_sig, gear_state_sig, time_signal = zip(*sorted)

        gear_state_prev = None
        t1_idx = None
        t2_idx = None
        t3_idx = None
        maneuver_area_plot = None
        evaluation1 = " "

        """Evaluation part"""
        # Find when the AP start maneuvering
        for cnt in range(0, len(p_core_state_sig)):
            if p_core_state_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = cnt
                gear_state_prev = gear_state_sig[cnt]
                break

        # Find when the second stroke starts
        for cnt in range(t1_idx or 0, len(p_core_state_sig)):
            if gear_state_sig[cnt] != gear_state_prev:
                t2_idx = cnt
                break

        for cnt in range(t1_idx or 0, len(p_core_state_sig)):
            if p_core_state_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS:
                t3_idx = cnt
                break

        if t1_idx is not None and t2_idx is not None and t3_idx is not None:
            eval_cond, maneuver_area_plot_info, ego_plot_info = HilClFuntions.maneuver_area_check(
                positions_x=pos_x[t2_idx : t2_idx + 1],
                positions_y=pos_y[t2_idx : t2_idx + 1],
                heading_angle=ego_heading[t2_idx : t2_idx + 1],
                ego_wheelbase=constants.HilCl.CarShape.CAR_R_AXLE_TO_F_RONT_AXLE,
                ego_front_overhang=constants.HilCl.CarShape.CAR_F_AXLE_TO_FRONT,
                ego_rear_overhang=constants.HilCl.CarShape.CAR_R_AXLE_TO_HITCH,
                ego_width=constants.HilCl.CarShape.CAR_R_AXLE_TO_SIDE * 2,
                left_d=constants.HilCl.ManeuveringArea.PAR_IN_D_1,
                rear_d=constants.HilCl.ManeuveringArea.PAR_IN_D_2,
                right_d=constants.HilCl.ManeuveringArea.PAR_IN_D_3,
                front_d=constants.HilCl.ManeuveringArea.PAR_IN_D_4,
                parking_pos_x=pos_x[t3_idx],
                parking_pos_y=pos_y[t3_idx],
            )
            # maneuver_area_plot = HilClFuntions.create_slider_graph(ego_plot_info, maneuver_area_plot_info, timestamps=())

        elif t1_idx is None:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join("The evaluation is FAILED, AP function never turned to MANEUVERING.".split())
        elif t3_idx is None:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                "The evaluation is FAILED, AP function did not finished the maneuver in the recording.".split()
            )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join("The evaluation is FAILED, invalid TestRun.".split())
        if all(eval_cond):
            test_result = fc.PASS
            evaluation1 = " ".join(
                "The evaluation is PASSED, AP function does reach the maneuvering area at the end of the first stroke.".split()
            )
        else:
            test_result = fc.FAIL
            evaluation1 = " ".join(
                "The evaluation is Failed, AP function does not reach the maneuvering area at the end of the first stroke.".split()
            )
        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["First stroke while maneuvering"] = evaluation1

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=pos_x, mode="lines", name=signal_name["Pos_x"]))
            fig.add_trace(go.Scatter(x=time_signal, y=pos_y, mode="lines", name=signal_name["Pos_y"]))
            fig.add_trace(go.Scatter(x=time_signal, y=ego_heading, mode="lines", name=signal_name["Heading_angle"]))
            fig.add_trace(go.Scatter(x=time_signal, y=gear_state_sig, mode="lines", name=signal_name["Gear_state"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=p_core_state_sig, mode="lines", name=signal_name["Parking_core_state"])
            )

            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(fig)

            if maneuver_area_plot is not None:
                plots.append(maneuver_area_plot)

            remarks.append("")

        """Calculate parameters to additional table"""

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
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
    name="Maneuvering first stroke",
    description="Checking, that the AUP function uses the first stroke to go into the maneuvering area, if the maneuver starts from outside of the area.",
)
class AupManeuveringFirstStroke(TestCase):
    """AupFirstStroke Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupManeuveringFirstStrokeCheck,
        ]
