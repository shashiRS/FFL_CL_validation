"""Check Visual Alert at LSCA Activation"""

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

SIGNAL_DATA = "LSCA_VISUAL_ALERT_CHECK"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        LSCA_BRAKE_REQ = "Lsca_brake_req"
        VISUAL_ALERT = "Visual_alert"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.LSCA_BRAKE_REQ: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCEmergencyHoldRequest",
            self.Columns.VISUAL_ALERT: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral2.APHMIGeneralMessageRemote",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="LSCA visual alert at braking check",
    description="The system shall provide a visual alert to the driver at the moment of LSCA activation.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class LscaVisualAlertWhenCheck(TestStep):
    """LscaVisualAlertWhenCheck Test Step."""

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

        read_data = self.readers[SIGNAL_DATA].signals
        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        lsca_brake_req_sig = read_data["Lsca_brake_req"].tolist()
        visual_alert_sig = read_data["Visual_alert"].tolist()

        t1_idx = None
        t2_idx = None

        evaluation1 = " "

        # Step 1: Detect if LSCA brake request is triggered
        for cnt in range(0, len(lsca_brake_req_sig)):
            if lsca_brake_req_sig[cnt] == constants.HilCl.Lsca.BRAKE_REQUEST:
                t1_idx = cnt
                break

        if t1_idx is None:
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Lsca_brake_req']} is FAILED, no LSCA brake request was detected.".split()
            )
        else:
            # Step 2: Check if the visual alert is triggered at the same time as the LSCA brake request
            for cnt in range(t1_idx, len(visual_alert_sig)):
                if visual_alert_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralMessageRemote.VERY_CLOSE_TO_OBJECTS:
                    t2_idx = cnt
                    break

            if t2_idx is not None and time_signal[t2_idx] == time_signal[t1_idx]:
                test_result = fc.PASS
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Visual_alert']} is PASSED, visual alert was triggered at {time_signal[t2_idx]:.2f} [us] when LSCA braking activation occured at {time_signal[t1_idx]:.2f} [us].".split()
                )
            else:
                test_result = fc.FAIL
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Visual_alert']} is FAILED, visual alert was not triggered at {time_signal[t1_idx]:.2f} [us] when LSCA braking activation occured.".split()
                )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["LSCA visual alert at braking evaluation"] = evaluation1

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_header_left="Evaluation")
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        # Generate chart if test result FAILED
        if test_result == fc.FAIL:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=time_signal, y=visual_alert_sig, mode="lines", name=signal_name["Visual_alert"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=lsca_brake_req_sig, mode="lines", name=signal_name["Lsca_brake_req"])
            )
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
    name="LSCA Visual Alert at Braking Check",
    description="The system shall provide a visual alert to the driver at the moment of LSCA activation (emergency hold request).",
)
class LscaVisualAlertTest(TestCase):
    """LscaVisualAlertTest Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            LscaVisualAlertWhenCheck,
        ]
