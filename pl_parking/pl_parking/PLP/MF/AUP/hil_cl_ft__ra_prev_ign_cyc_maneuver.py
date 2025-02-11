"""RA automated maneuver after previous ignition cycle"""

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

SIGNAL_DATA = "RA_MANEUVER_AFTER_PREV_IGN_CYC"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        GENERAL_SCREEN = "General_screen"
        IGNITION = "Car_ignition"
        USER_ACTION = "User_action"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="RA maneuver after previous ignition cycle",
    description="Check if RA function is capable performing the RA maneuver in the next ignition cycle.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupRaPrevIgnCycCheck(TestStep):
    """AupRaPrevIgnCycCheck Test Step."""

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
        ignition_sig = read_data["Car_ignition"].tolist()
        user_action_sig = read_data["User_action"].tolist()

        t_ign_off_idx = None
        t_ign_on_idx = None
        t_maneuver_idx = None
        t_toggle_idx = None

        evaluation1 = ""

        """Evaluation part"""

        # Find when the AP set to active
        for cnt in range(0, len(user_action_sig)):
            if user_action_sig == constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE:
                t_toggle_idx = cnt
                break

        # Find when ignition turned off
        for cnt in range(t_toggle_idx or 0, len(ignition_sig)):
            if ignition_sig == constants.HilCl.CarMaker.IGNITION_OFF:
                t_ign_off_idx = cnt
                break

        # Find when ignition turned on
        for cnt in range(t_ign_off_idx or 0, len(ignition_sig)):
            if ignition_sig == constants.HilCl.CarMaker.IGNITION_ON:
                t_ign_on_idx = cnt
                break

        # Find when RA function activates
        for cnt in range(t_ign_on_idx or 0, len(general_screen_sig)):
            if general_screen_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                t_maneuver_idx = cnt
                break

        # If every t_#_idx is not None then every required condition fulfilled in a correct order
        if t_ign_off_idx and t_ign_on_idx and t_maneuver_idx:
            test_result = fc.PASS
            evaluation1 = " ".join(
                "The test for checking system capability of performing maneuver in the next ignition cycle is PASSED.".split()
            )

        else:
            test_result = fc.FAIL
            evaluation1 = " ".join(
                "The test for checking system capability of performing maneuver in the next ignition cycle is FAILED.".split()
            )

        if t_ign_off_idx is None:
            evaluation1.join("The ignition was not turned off.".split())
        if t_ign_on_idx is None:
            evaluation1.join("The ignition was not turned on".split())
        if t_maneuver_idx is None:
            evaluation1.join("The system did not transitioned to Automated reversing state.".split())

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["RA automated maneuver after previous ignition cycle"] = evaluation1

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
            fig.add_trace(go.Scatter(x=time_signal, y=user_action_sig, mode="lines", name=signal_name["User_action"]))
            fig.add_trace(go.Scatter(x=time_signal, y=ignition_sig, mode="lines", name=signal_name["Car_ignition"]))

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
    name="RA maneuver after previous ignition cycle",
    description="Check if RA function is capable performing the RA maneuver in the next ignition cycle.",
)
class AupRaPrevIgnCyc(TestCase):
    """AupRaPrevIgnCyc Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupRaPrevIgnCycCheck,
        ]
