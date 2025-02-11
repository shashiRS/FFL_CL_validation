"""Detect praking slot on driver's site"""

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

SIGNAL_DATA = "L1D_DETECT_SLOT_ON_LEFT SITE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        DETECTED_SLOT = "Detected_slot"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.DETECTED_SLOT: "MTS.MTA_ADC5.EM_DATA.EmApParkingBoxPort.numValidParkingBoxes_nu",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Parking slot detection check",
    description="Check system capable detect parking slot on drivers's side of ego vehicle.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class L1dLeftSlotDetectCheck(TestStep):
    """L1dLeftSlotDetectCheck Test Step."""

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
        hmi_state_sig = read_data["State_on_HMI"].tolist()
        detected_slot_sig = read_data["Detected_slot"].tolist()

        t_scanning_idx = None

        evaluation1 = " "

        """Evaluation part"""
        # Check begining of Scanning
        for cnt in range(0, len(hmi_state_sig)):
            if hmi_state_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN:
                t_scanning_idx = cnt
                break

        if t_scanning_idx is not None:
            # Check number of slots
            if max(detected_slot_sig) > 0:
                test_result = fc.PASS
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Detected_slot']} signal is PASSED."
                    f" Number of detected slot(s): {max(detected_slot_sig)}.".split()
                )
            else:
                test_result = fc.FAIL
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Detected_slot']} signal is FAILED."
                    f" Number of detected slot(s): {max(detected_slot_sig)} but there was at least one valid parking slot on the driver's side.".split()
                )

        else:
            test_result = fc.FAIL
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to PPC_SCANNING_IN ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN})."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Slot in driver's site"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=time_signal, y=hmi_state_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=detected_slot_sig, mode="lines", name=signal_name["Detected_slot"])
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
    name="Parking slot detection on driver's side.",
    description="In Scanning Mode, the SceneInterpretation shall provide a parking box if it is located on the driver's side of the ego vehicle.",
)
class L1dLeftSlotDetect(TestCase):
    """L1dLeftSlotDetect Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            L1dLeftSlotDetectCheck,
        ]
