"""RA Mode Transition, Precondition Mode to Automated Reversing, gear shifted R"""

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

SIGNAL_DATA = "RA_PRE_TO_AUT_GEAR_R"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USER_ACTION = "User_action"
        PARKING_CORE_STATE = "Parking_core_state"
        DRIVING_DIR = "Driv_dir"
        GENERAL_SCREEN = "General_screen"
        GENERAL_MESSAGE = "General_message"
        CAR_SPEED = "Car_speed"
        RA_POSS = "RA_possible"
        GEAR = "Gear"
        BRAKE = "Brake"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.PARKING_CORE_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
            self.Columns.GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
            self.Columns.CAR_SPEED: "MTS.ADAS_CAN.Conti_Veh_CAN.Tachometer.SpeedoSpeed",
            self.Columns.RA_POSS: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral2.APHMIGeneralRevAssistPoss",
            self.Columns.GEAR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralCurrentGear",
            self.Columns.BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput06.BrakePressureDriver",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Mode transition check",
    description="Check RA function switches from Precondition Mode to Automated Reversing if gear is shifted to R.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupRaPreToAutCheckGearR(TestStep):
    """AupRaPreToAutCheckGearR Test Step."""

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
        general_screen_sig = read_data["General_screen"].tolist()
        general_message_sig = read_data["General_message"].tolist()
        user_act_sig = read_data["User_action"].tolist()
        driving_dir_sig = read_data["Driv_dir"].tolist()
        ra_poss_sig = read_data["RA_possible"].tolist()
        gear_sig = read_data["Gear"].tolist()
        brake_sig = read_data["Brake"].tolist()

        t_arp_idx = None
        t_hmi_idx = None
        t_standstill_idx = None
        t_brake_idx = None
        t_gear_idx = None
        t_aut_rev_idx = None

        evaluation1 = ""

        """Evaluation part"""
        # Find when APHMIGeneralRevAssistPoss set to TRUE --> System in Automated Reversing Precondition Mode
        for cnt in range(0, len(ra_poss_sig)):
            if ra_poss_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralRevAssistPoss.TRUE:
                t_arp_idx = cnt
                break

        # Find when driver taps on HMI to start RA
        for cnt in range(t_arp_idx or 0, len(user_act_sig)):
            if user_act_sig[cnt] == constants.HilCl.Hmi.Command.TAP_ON_REVERSE_ASSIST:
                t_hmi_idx = cnt
                break

        # Find when vehicle reach standstill
        for cnt in range(t_arp_idx or 0, len(driving_dir_sig)):
            if driving_dir_sig[
                cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL:
                t_standstill_idx = cnt
                break

        # Find when brake pedal released
        for cnt in range(t_arp_idx or 0, len(brake_sig)):
            if brake_sig[cnt] == 0:
                t_brake_idx = cnt
                break

        # Find when gear is set to Reverse
        for cnt in range(t_arp_idx or 0, len(gear_sig)):
            if gear_sig[cnt] == constants.HilCl.Gear.GEAR_R:
                t_gear_idx = cnt
                break

        # Find when parking core switches to automated reverse mode
        for cnt in range(t_arp_idx or 0, len(general_screen_sig)):
            if general_screen_sig[
                cnt] == constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                t_aut_rev_idx = cnt
                break

        # If every t_#_idx is not None then every required condition fulfilled in a correct order
        if t_arp_idx and t_hmi_idx and t_standstill_idx and t_brake_idx and t_gear_idx and t_aut_rev_idx:
            if t_gear_idx <= t_aut_rev_idx:
                test_result = fc.PASS
                evaluation1 = " ".join(
                    "The test for checking Mode transition from Precondition Mode to Automated Reversing is PASSED.".split()
                )
            else:
                test_result = fc.FAIL
                evaluation1 = " ".join(
                    "The test for checking Mode transition from Automated reversing to Terminate is FAILED.".split()
                )

        else:
            test_result = fc.FAIL
            evaluation1 = " ".join(
                "The test for checking Mode transition from Automated reversing to Terminate is FAILED.".split()
            )

        if t_arp_idx is None:
            evaluation1.join(
                "The system did not transition to Automated Reversing Precondition Mode.".split()
            )
        if t_hmi_idx is None:
            evaluation1.join("There was no HMI input to engage reverse assist function.".split())
        if t_standstill_idx is None:
            evaluation1.join("The vehicle was not braked to a standstill.".split())
        if t_brake_idx is None:
            evaluation1.join("The brake pedal was not released.".split())
        if t_gear_idx is None:
            evaluation1.join("The gear was not shifted to reverse.".split())
        if t_aut_rev_idx is None:
            evaluation1.join("The system did not transition to Automated reversing mode.".split())

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary[
            "Required RA state change: Precondition Mode to Automated Reversing. Reason: Gear shifted to reverse"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=time_signal, y=general_screen_sig, mode="lines", name=signal_name["General_screen"])
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=general_message_sig, mode="lines", name=signal_name["General_message"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
            fig.add_trace(go.Scatter(x=time_signal, y=ra_poss_sig, mode="lines", name=signal_name["RA_possible"]))
            fig.add_trace(go.Scatter(x=time_signal, y=gear_sig, mode="lines", name=signal_name["Gear"]))
            fig.add_trace(go.Scatter(x=time_signal, y=brake_sig, mode="lines", name=signal_name["Brake"] + " [bar]"))
            fig.add_trace(go.Scatter(x=time_signal, y=driving_dir_sig, mode="lines", name=signal_name["Driv_dir"]))

            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        """Calculate parameters to additional table"""
        sw_combatibility = (  # Remainder: Update if SW changed and script working well
            "swfw_apu_adc5-2.1.0-DR2-PLP-B1-PAR230"
        )

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            "Used SW version": {"value": sw_combatibility},
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
    name="RA Mode Transition, Precondition Mode to Automated Reversing, Gear R",
    description="The RA function shall transit from Automated Reversing Precondition Mode to Automated Reversing if the gear is switched to Reverse.",
)
class AupRaPreToAutGear(TestCase):
    """AupRaPreToAut Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupRaPreToAutCheckGearR,
        ]
