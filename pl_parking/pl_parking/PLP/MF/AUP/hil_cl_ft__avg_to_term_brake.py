"""Inform the reason about AVG Termination: when Brake applied"""

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

"__author__ = Rakesh Kyathsandra Jayaramu"

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "AVG_TO_TERMINATE_BRAKE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        BRAKE = "Brake"
        HMI_INFO = "State_on_HMI"
        GENERAL_MESSAGE = "General_message"
        GENERAL_SCREEN = "General_screen"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput06.BrakePressureDriver",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
            self.Columns.GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="AVG to Terminate",
    description="Check reason for AVG termination",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AvgToTerminationBrakeCheck(TestStep):
    """AvgToTerminationBrakeCheck Test Step."""

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
        brake_sig = read_data["Brake"].tolist()
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()
        gen_message_sig = read_data["General_message"].tolist()
        general_screen_sig = read_data["General_screen"].tolist()

        t_maneuvering_idx = None
        t_brake_idx = None
        t_terminate_idx = None
        evaluation1 = " ".join(
            f"The evaluation of {signal_name['General_screen']} signal is MANEUVER_INTERRUPTED, signal switches to Terminate mode when brake pressure, caused by the braking"
            f" pedal, is higher than {constants.HilCl.ApThreshold.AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR} bar,"
            f" inform the driver to RELEASE_BRAKE".split()
        )

        """Evaluation part"""
        # Find when parking core switches to Maneuvering mode
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_maneuvering_idx = cnt
                break

        # Find when the break pedal exceeds limit
        for cnt in range(t_maneuvering_idx or 0, len(brake_sig)):
            if brake_sig[cnt] > constants.HilCl.ApThreshold.AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR:
                t_brake_idx = cnt
                break

        # Find when parking core switches to terminate mode and inform the reason
        for cnt in range(t_brake_idx or 0, len(general_screen_sig)):
            if (
                general_screen_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralScreen.MANEUVER_INTERRUPTED
                and gen_message_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralMessage.RELEASE_BRAKE
            ):
                t_terminate_idx = cnt
                break

        # If every t_#_idx is not None then every required condition fulfilled in a correct order
        if t_terminate_idx and t_maneuvering_idx and t_brake_idx:
            test_result = fc.PASS
            evaluation1 = " ".join(
                f"The test for checking Mode transition from AVG to Terminate is PASSED. {evaluation1}.".split()
            )
        else:
            test_result = fc.FAIL
            evaluation1 = " ".join("The test for checking Mode transition from AVG to Terminate is FAILED.".split())

        if t_maneuvering_idx is None:
            evaluation1 = " ".join(
                "The system did not transition to Maneuvering mode after the vehicle  was secured.".split()
            )
        if t_brake_idx is None:
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Brake']} signal is FAILED, brake pressure, caused by the braking pedal,"
                f" never higher than {constants.HilCl.ApThreshold.AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR} bar.".split()
            )
        if t_terminate_idx is None:
            evaluation1 = " ".join(
                "The system did not transition to Terminate mode after the vehicle  was secured.".split()
            )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary[
            "Required AVG state change: AVG to Terminate. Reason: Brake pressure, caused by the braking pedal"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=brake_sig, mode="lines", name=signal_name["Brake"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=general_screen_sig, mode="lines", name=signal_name["General_screen"])
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=gen_message_sig, mode="lines", name=signal_name["General_message"])
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
    name="Mode transition: AVG to Terminate",
    description="The ego vehicle shall transit from AVG to Terminate mode, when " "the break pedal exceeds the limit.",
)
class AvgToTerminationBrake(TestCase):
    """AvgToTerminationBrake Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AvgToTerminationBrakeCheck,
        ]
