"""Check HMI Display for LSMF Active - Scanning"""

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

__author__="Serban Marius"

SIGNAL_DATA = "LSMF_ACTIVE_SCANNING"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        STATE_ON_HMI = "State_on_HMI"
        USER_ACTION = "User_action"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.STATE_ON_HMI: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="LSMF Active - Scanning Check",
    description="Verify that the HMI displays the scanning state when the AP function is active.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class LsmfActiveScanningCheck(TestStep):
    """LsmfActiveScanningCheck Test Step."""

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
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()
        user_action_sig = read_data["User_action"].tolist()

        t1_idx = None
        t2_idx = None

        evaluation1 = " "

        # Step 1: Detect the initial TOGGLE_AP_ACTIVE action to start scanning
        for cnt, action in enumerate(user_action_sig):
            if action == constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE:
                t1_idx = cnt
                break

        if t1_idx is None:
            test_result = fc.FAIL
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['User_action']} is FAILED, TOGGLE_AP_ACTIVE [{constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE}] action to start scanning was not detected.".split()
            )
        else:
            # Step 2: Verify the transition to PPC_SCANNING_IN state after the action
            for cnt in range(t1_idx, len(state_on_hmi_sig)):
                if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN:
                    t2_idx = cnt
                    break

            if t2_idx is None:
                test_result = fc.FAIL
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['State_on_HMI']} is FAILED, the system did not transition to PPC_SCANNING_IN [{constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN}] (scanning state) after TOGGLE_AP_ACTIVE [{constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE}] action.".split()
                )
            else:
                test_result = fc.PASS
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['State_on_HMI']} is PASSED, the system successfully transitioned to PPC_SCANNING_IN [{constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN}] (scanning state) at {time_signal[t2_idx]} [us] after the TOGGLE_AP_ACTIVE [{constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE}] action at {time_signal[t1_idx]} [us].".split()
                )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["LSMF Active - Scanning Evaluation"] = evaluation1

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_header_left="Evaluation")
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        # Generate chart if test result FAILED
        if test_result == fc.FAIL:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=user_action_sig, mode="lines", name=signal_name["User_action"]))
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
    name="LSMF Active - Scanning Check",
    description="Verify that the HMI displays scanning status when AP function is active.",
)
class LsmfActiveScanningTest(TestCase):
    """LsmfActiveScanningTest Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            LsmfActiveScanningCheck,
        ]
