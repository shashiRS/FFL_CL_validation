"""RC getting off inform the driver via HMI"""

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

SIGNAL_DATA = "RC_GET_OFF_INFORM_VIA_HMI"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        GENERAL_MESSAGE = "General_message"
        USER_ACTION_REMOTE = "User_action_remote"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
            self.Columns.USER_ACTION_REMOTE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionRem",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Remote maneuvering infrom driver via HMI",
    description="Check RC function informs the driver that vehicle shall be left by all passenger and driver.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupRcGetOffInformHMICheck(TestStep):
    """AupRcGetOffInformHMICheck Test Step."""

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
        general_message_sig = read_data["General_message"].tolist()
        user_act_sig = read_data["User_action_remote"].tolist()

        t_getting_off_idx = None
        t_remote_idx = None

        evaluation1 = ""

        """Evaluation part"""
        # Find when driver starts remote park
        for cnt in range(0, len(user_act_sig)):
            if user_act_sig[cnt] == constants.HilCl.Hmi.RemCommand.REM_TAP_ON_PARK_IN:
                t_remote_idx = cnt
                break

        # Find when LEAVE_VEHICLE message appears in APHMIGeneralMessage
        for cnt in range(t_remote_idx or 0, len(general_message_sig)):
            if general_message_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralMessage.LEAVE_VEHICLE:
                t_getting_off_idx = cnt
                break

        # If every t_#_idx is not None then every required condition fulfilled in a correct order
        if t_getting_off_idx and t_remote_idx:
            test_result = fc.PASS
            evaluation1 = " ".join(
                f"The test for inform driver while remote parking is PASSED. "
                f"After the signal {signal_name['User_action_remote']} changes "
                f"to {constants.HilCl.Hmi.RemCommand.REM_TAP_ON_PARK_IN}, "
                f"the signal {signal_name['General_message']} value shall change "
                f"to {constants.HilCl.Hmi.APHMIGeneralMessage.LEAVE_VEHICLE}. ".split()
            )

        else:
            test_result = fc.FAIL
            evaluation1 = " ".join(
                "The test for inform driver while remote parking is FAILED. "
                f"After the signal {signal_name['User_action_remote']} changes "
                f"to {constants.HilCl.Hmi.RemCommand.REM_TAP_ON_PARK_IN}, "
                f"the signal {signal_name['General_message']} value shall change "
                f"to {constants.HilCl.Hmi.APHMIGeneralMessage.LEAVE_VEHICLE}. ".split()
            )

        if t_getting_off_idx is None:
            evaluation1 += " ".join("The system did not informed the driver to leave vehicle.".split())
        if t_remote_idx is None:
            evaluation1 += " ".join("The driver did not press start on the remote device".split())

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["RC getting off inform the driver via HMI"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action_remote"])
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=general_message_sig, mode="lines", name=signal_name["General_message"])
            )

            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(fig)
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
    name="Remote maneuvering infrom driver via HMI",
    description="Check RC function informs the driver that vehicle shall be left by all passenger and driver.",
)
class AupRcGetOffInformHMI(TestCase):
    """AupRcGetOffInformHMI Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupRcGetOffInformHMICheck,
        ]
