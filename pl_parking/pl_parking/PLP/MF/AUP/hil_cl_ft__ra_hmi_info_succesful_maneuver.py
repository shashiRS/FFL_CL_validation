"""Testing if HMI displays correct information about the success of the maneuver"""

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

SIGNAL_DATA = "HMI MANEUVER FINISHED MESSAGE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        GENERAL_MESSAGE = "General_message"
        GENERAL_SCREEN = "General_screen"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
            self.Columns.GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="HMI message on finishing maneuver",
    description="Check if the message regarding finished RA maneuver is displayed in HMI.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupRAHMIMesSuccessCheck(TestStep):
    """AupRAHMIMesSuccessCheck Test Step."""

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
        ra_state = read_data["General_message"].tolist()
        state_on_hmi_sig = read_data["General_screen"].tolist()

        t_terminate_idx = None
        t_aut_rev_idx = None
        t_aut_rev_done_idx = None

        evaluation1 = ""

        """Evaluation part"""
        # Find when parking core switches to automated reverse mode
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                t_aut_rev_idx = cnt
                break

        # Find when the maneuver ends
        for cnt in range(t_aut_rev_idx or 0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] != constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                t_aut_rev_done_idx = cnt
                break

        # Find when the message regarding finished maneuver is displayed
        for cnt in range(t_aut_rev_done_idx or 0, len(ra_state)):
            if ra_state[cnt] == constants.HilCl.Hmi.APHMIGeneralMessage.REVERSE_ASSIST_FINISHED:
                t_terminate_idx = cnt
                break

        # If every t_#_idx is not None then every required condition fulfilled in a correct order
        if t_terminate_idx and t_aut_rev_idx and t_aut_rev_done_idx:
            test_result = fc.PASS
            evaluation1 = " ".join("The test for checking HMI information displaying is PASSED.".split())

        else:
            test_result = fc.FAIL
            evaluation1 = " ".join("The test for checking HMI information displaying is FAILED.".split())

        if t_terminate_idx is None:
            evaluation1 = " ".join("The system did not displayed the message maneuver finished message on HMI.".split())
        if t_aut_rev_idx is None:
            evaluation1 = " ".join("The system did not transition to Automated reversing mode ".split())
        if t_aut_rev_done_idx is None:
            evaluation1 = " ".join("The system did not transition out from Automated reversing mode ".split())

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["HMI message regarding successful maneuver"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["General_screen"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=ra_state, mode="lines", name=signal_name["General_message"]))

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
    name="HMI message on finishing maneuver",
    description="Check if the message regarding finished RA maneuver is displayed in HMI.",
)
class AupRAHMIMesSuccess(TestCase):
    """AupRAHMIMesSuccess Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupRAHMIMesSuccessCheck,
        ]
