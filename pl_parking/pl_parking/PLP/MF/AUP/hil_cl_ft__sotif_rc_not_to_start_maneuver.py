"""Check Dead Man Switch Requirement for Starting Low-Speed Maneuver"""

import logging
import os
import sys

import plotly.graph_objects as go

log = logging.getLogger(__name__)
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
from pl_parking.common_ft_helper import MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.constants import PlotlyTemplate

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "Serban Marius"

SIGNAL_DATA = "DEADMAN_SWITCH_CHECK"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        REM_FINGER_X = "Rem_finger_x"
        REM_FINGER_Y = "Rem_finger_y"
        STATE_ON_HMI = "State_on_HMI"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.REM_FINGER_X: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutRemFingerPosX",
            self.Columns.REM_FINGER_Y: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutRemFingerPosY",
            self.Columns.STATE_ON_HMI: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Check Dead Man Switch Requirement",
    description="Verify that the system does not start low-speed maneuvering unless the dead man's switch is pressed by the driver.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class DeadManSwitchCheck(TestStep):
    """DeadManSwitchCheck Test Step."""

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
        rem_finger_x_sig = read_data["Rem_finger_x"].tolist()
        rem_finger_y_sig = read_data["Rem_finger_y"].tolist()
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()

        evaluation1 = " "

        # Step 1: Ensure the system was in scanning phase (PPC_SCANNING_IN)
        t_scanning_idx = None
        for cnt, state in enumerate(state_on_hmi_sig):
            if state == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN:
                t_scanning_idx = cnt
                break

        if t_scanning_idx is None:
            test_result = fc.FAIL
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} is FAILED. The system never entered the scanning phase ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN}).".split()
            )
        else:
            # Step 2: Check if the system transitions to PPC_PERFORM_PARKING while dead man's switch is NOT pressed
            dms_not_pressed = True
            for cnt, state in enumerate(state_on_hmi_sig):
                if (
                    rem_finger_x_sig[cnt] != constants.HilCl.Hmi.RemFingerPosition.DM_FINGER_POS_X
                    or rem_finger_y_sig[cnt] != constants.HilCl.Hmi.RemFingerPosition.DM_FINGER_POS_Y
                ):
                    if state == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                        test_result = fc.FAIL
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} is FAILED. The system started maneuvering while the dead man's switch was not pressed.".split()
                        )
                        dms_not_pressed = False
                        break
            if dms_not_pressed:
                test_result = fc.PASS
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['State_on_HMI']} is PASSED. The system did not start maneuvering while the dead man's switch was not pressed.".split()
                )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Dead Man Switch Requirement Evaluation"] = evaluation1

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_header_left="Evaluation")
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        # Generate chart if test result FAILED
        if test_result == fc.FAIL:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=time_signal, y=rem_finger_x_sig, mode="lines", name=signal_name["Rem_finger_x"]))
            fig.add_trace(go.Scatter(x=time_signal, y=rem_finger_y_sig, mode="lines", name=signal_name["Rem_finger_y"]))
            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        # Add the data in the table from Functional Test Filter Results
        additional_results_dict = {"Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)}}

        for plot in plots:
            if isinstance(plot, go.Figure):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="Dead Man Switch Requirement Test",
    description="Verify that the system does not start the low-speed maneuver unless the dead man's switch is pressed.",
)
class DeadManSwitchRequirementTest(TestCase):
    """DeadManSwitchRequirementTest Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            DeadManSwitchCheck,
        ]
