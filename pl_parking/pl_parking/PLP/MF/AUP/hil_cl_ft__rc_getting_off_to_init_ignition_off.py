"""Mode transition, RC Getting Off to Init, Ignition off"""

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

SIGNAL_DATA = "RC_GET_OFF_TO_INIT_IGNITION_OFF"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        GENERAL_MESSAGE = "General_message"
        HMI_INFO = "State_on_HMI"
        IGNITION = "Ignition"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Ignition turned off",
    description="Check RC function reaction if ignition is turned off.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupRcGetOffToInitRemoteIgnOffCheck(TestStep):
    """AupRcGetOffToInitRemoteIgnOffCheck Test Step."""

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
        ignition_sig = read_data["Ignition"].tolist()
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()

        t_getting_off_idx = None
        t_cancel_idx = None
        t_terminate_idx = None

        evaluation1 = ""

        """Evaluation part"""
        # Find when LEAVE_VEHICLE message appeares in APHMIGeneralMessage
        for cnt in range(0, len(general_message_sig)):
            if general_message_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralMessage.LEAVE_VEHICLE:
                t_getting_off_idx = cnt
                break

        # Find when the ignition is turned off
        for cnt in range(t_getting_off_idx or 0, len(ignition_sig)):
            if ignition_sig[cnt] == constants.HilCl.CarMaker.IGNITION_OFF:
                t_cancel_idx = cnt
                break

        # Find when parking core switches to init mode
        for cnt in range(t_cancel_idx or 0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_terminate_idx = cnt
                break

        # If every t_#_idx is not None then every required condition fulfilled in a correct order
        if t_getting_off_idx and t_cancel_idx and t_terminate_idx:
            test_result = fc.PASS
            evaluation1 = " ".join("The test for checking Mode transition from Getting off to Init is PASSED.".split())

        else:
            test_result = fc.FAIL
            evaluation1 = " ".join("The test for checking Mode transition from Getting off to Init is FAILED.".split())

        if t_getting_off_idx is None:
            evaluation1 += " ".join("The system did not transition to Getting off mode.".split())
        if t_cancel_idx is None:
            evaluation1 += " ".join("The ignition is not turned off.".split())
        if t_terminate_idx is None:
            evaluation1 += " ".join(
                "The system did transitioned from parking out phase after the ignition is turned off.".split()
            )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Mode transition, RC Getting Off to Init, Ignition off"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=ignition_sig, mode="lines", name=signal_name["Ignition"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=general_message_sig, mode="lines", name=signal_name["General_message"])
            )

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
    name="Ignition turned off",
    description="Check RC function reaction if ignition is turned off.",
)
class AupRcGetOffToInitRemoteIgnOff(TestCase):
    """AupRcGetOffToInitRemote Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupRcGetOffToInitRemoteIgnOffCheck,
        ]
