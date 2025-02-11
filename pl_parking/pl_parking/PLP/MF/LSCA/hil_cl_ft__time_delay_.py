"""Check Time Delay for LSCA Deactivation"""

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

SIGNAL_DATA = "LSCA_DEACTIVATION_DELAY_CHECK"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        LSCA_STATE = "Lsca_state"
        USER_ACTION = "User_action"  # Signal for HMI button press

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.LSCA_STATE: "MTS.MTA_ADC5.MF_LSCA_DATA.statusPort.lscaOverallMode_nu",
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="LSCA deactivation delay check",
    description="The system shall deactivate LSCA within 200 ms after receiving the request via HMI.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class TimeReactionCheck(TestStep):
    """TimeReactionCheck Test Step."""

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
        lsca_status_sig = read_data["Lsca_state"].tolist()
        user_action_sig = read_data["User_action"].tolist()

        t1_idx = None
        t2_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Lsca_state']} is PASSED, the deactivation occures within {constants.HilCl.Lsca.REACTION_TIME_WITHOUT_OBSTACLES} ms.".split()
        )

        # Step 1: Detect if the HMI button to deactivate LSCA (TAP_ON_LSCA = 65) was pressed
        for cnt in range(0, len(user_action_sig)):
            if user_action_sig[cnt] == constants.HilCl.Hmi.Command.TAP_ON_LSCA:
                t1_idx = cnt
                break

        if t1_idx is None:
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['User_action']} is FAILED, LSCA deactivation request via HMI button was not detected.".split()
            )
        else:
            # Step 2: Monitor LSCA status and check for deactivation within 200 ms
            for cnt in range(t1_idx, len(lsca_status_sig)):
                if lsca_status_sig[cnt] == constants.HilCl.Lsca.LSCA_NOT_ACTIVE:
                    t2_idx = cnt
                    break

            if t2_idx is None:
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Lsca_state']} is FAILED, LSCA did not deactivate (transition from 1 to 0) after HMI button press.".split()
                )
            else:
                # Calculate the time difference between t2 and t1
                time_difference = (time_signal[t2_idx] - time_signal[t1_idx]) / 1000.0  # Convert to milliseconds
                if time_difference <= constants.HilCl.Lsca.REACTION_TIME_WITHOUT_OBSTACLES:
                    test_result = fc.PASS
                else:
                    test_result = fc.FAIL
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Lsca_state']} is FAILED, LSCA deactivation took {time_difference:.2f} ms (from the taping on HMI to the deactivation of the function), which exceeds the {constants.HilCl.Lsca.REACTION_TIME_WITHOUT_OBSTACLES} ms limit.".split()
                    )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["LSCA deactivation delay evaluation"] = evaluation1

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_header_left="Evaluation")
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        # Generate chart if test result FAILED
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=time_signal / constants.GeneralConstants.US_IN_MS,
                y=lsca_status_sig,
                mode="lines",
                name=signal_name["Lsca_state"],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=time_signal / constants.GeneralConstants.US_IN_MS,
                y=user_action_sig,
                mode="lines",
                name=signal_name["User_action"],
            )
        )
        fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [ms]")
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
    name="LSCA Deactivation Delay Check",
    description="The system shall deactivate LSCA within 200 ms after receiving the request via HMI button.",
)
class LscaDeactivationDelay(TestCase):
    """LscaDeactivationDelay Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TimeReactionCheck,
        ]
