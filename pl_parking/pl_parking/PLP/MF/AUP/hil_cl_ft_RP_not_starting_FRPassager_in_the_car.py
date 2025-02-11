"""The system shall not start the low speed maneuvering procedure if the front left passager is in the car  (remote parking only)."""
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

SIGNAL_DATA = "RP_NOT_START_FRPASS_DET"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USEER_ACTION_REM = "User_action_rem"
        HMI_INFO = "State_on_HMI"
        SEAT_OCCUPANCY_STATE_FRPASS = "Seat_occupancy_state_frpass"
        USER_ACTION = "User_action"
        FINGER_POS_X = "Finger_pos_x"
        FINGER_POS_Y = "Finger_pos_y"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USEER_ACTION_REM: "MTS.IO_CAN_AP_Private_CAN.APHMIOut1.APHMIOutUserActionRem",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.SEAT_OCCUPANCY_STATE_FRPASS: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput02.seatOccupancyStatus_frontRight",
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.FINGER_POS_X: "MTS.IO_CAN_AP_Private_CAN.APHMIOut2.APHMIOutRemFingerPosX",
            self.Columns.FINGER_POS_Y: "MTS.IO_CAN_AP_Private_CAN.APHMIOut2.APHMIOutRemFingerPosY",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="RP not starting FR passager present",
    description="Check if the system is not starting the remote parking maneuver if the front right passager is detected in the car.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class RPNotStartingFRPassagerInTheCarCheck(TestStep):
    """RPNotStartingFRPassagerInTheCarCheck Test Step."""

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

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        user_act_rem = read_data["User_action_rem"].tolist()
        HMI_Info = read_data["State_on_HMI"].tolist()
        user_act_sig = read_data["User_action"].tolist()
        seat_occupancy_state_frpass = read_data["Seat_occupancy_state_frpass"].tolist()
        Finger_pos_X = read_data["Finger_pos_x"].tolist()
        Finger_pos_Y = read_data["Finger_pos_y"].tolist()

        t1_idx = None
        t2_idx = None

        evaluation1 = " ".join(
            f"The evaluation of AVG State {signal_name['State_on_HMI']} signal is PASSED,"
            f" the signal is not switching to PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})".split()
        )

        """Evaluation part"""
        # Find when user activate the AP function
        for idx, item in enumerate(user_act_sig):
            if item == constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE:
                t1_idx = idx
                break

        if t1_idx is not None:
            eval_cond = [True] * 1

            # Find the moment when DeadMan switch is pressed
            for cnt in range(t1_idx, len(user_act_rem)):
                if Finger_pos_X[cnt] == constants.HilCl.Hmi.RemFingerPosition.DM_FINGER_POS_X and \
                   Finger_pos_Y[cnt] == constants.HilCl.Hmi.RemFingerPosition.DM_FINGER_POS_Y and \
                   seat_occupancy_state_frpass[cnt] == constants.HilCl.Seat.DRIVERS_OCCUPIED:
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                for i in range (t2_idx, len(HMI_Info)):
                    if HMI_Info[i] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                            f" AVG start the parking maneuver while front right passager still in the car (state == {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})".split()
                        )
                        break
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                    f" the driver didn't press the DeadMan switch"
                    f" ({signal_name['Finger_pos_x']} != {constants.HilCl.Hmi.RemFingerPosition.DM_FINGER_POS_X} and"
                    f" {signal_name['Finger_pos_y']} != {constants.HilCl.Hmi.RemFingerPosition.DM_FINGER_POS_Y}).".split()
                )
        else:
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['User_action']} is Failed, AP never active (signal value != {constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE})".split()
            )

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary[
            "Check the reaction of the system in case a front right passager is present in the car (remote parking only)."
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=user_act_rem, mode="lines", name=signal_name["User_action_rem"]))
        fig.add_trace(go.Scatter(x=time_signal, y=seat_occupancy_state_frpass, mode="lines", name=signal_name["Seat_occupancy_state_frpass"]))
        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=Finger_pos_X, mode="lines", name=signal_name["Finger_pos_x"]))
        fig.add_trace(go.Scatter(x=time_signal, y=Finger_pos_Y, mode="lines", name=signal_name["Finger_pos_y"]))
        fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
        fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
        fig.update_layout(PlotlyTemplate.lgt_tmplt)

        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

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
    name="Not starting RP during front right passager presence",
    description=f"In case the front right passager is still in the car, the system shall not start the low speed parking maneuver"
                f" (AVG != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})",
    doors_url="https://jazz.conti.de/rm4/resources/BI_BpGOEd09Ee62R7UY0u3jZg?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17892",
)
class RPNotStartingFRPassagerInTheCar(TestCase):
    """RPNotStartingFRPassagerInTheCar Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            RPNotStartingFRPassagerInTheCarCheck,
        ]
