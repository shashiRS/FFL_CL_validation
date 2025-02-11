"""Reversible error. Systetm shall inform the driver"""

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

SIGNAL_DATA = "REV_ERR_INFO"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        GENEREAL_SCREEN = "Gen_screen"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.GENEREAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Inform driver about reversible error.",
    description="Check sent information to the driver in case of reversible error.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupRevErrorInfoCheck(TestStep):
    """AupRevErrorInfoCheck Test Step."""

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
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()
        gem_screen_sig = read_data["Gen_screen"].tolist()

        t_parking_idx = None
        t_detection_idx = None
        t_end_of_error_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Gen_screen']} signal is PASSED, value of signal was DIAG_ERROR ({constants.HilCl.Hmi.APHMIGeneralScreen.DIAG_ERROR}) while reversible error was detected."
            f" Maximum aloved delay between detection and switch to DIAG_ERROR ({constants.HilCl.Hmi.APHMIGeneralScreen.DIAG_ERROR}) is one sample.".split()
        )

        """Evaluation part"""
        # Find parking
        for cnt, item in enumerate(state_on_hmi_sig):
            if item == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_parking_idx = cnt
                break

        if t_parking_idx is not None:
            # Find reversible error detection
            for cnt in range(t_parking_idx, len(state_on_hmi_sig)):
                if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_REVERSIBLE_ERROR:
                    t_detection_idx = cnt
                    break

            if t_detection_idx is not None:
                eval_cond = [True] * 1

                # Find reversible error deactivation
                for cnt in range(t_detection_idx, len(state_on_hmi_sig)):
                    if state_on_hmi_sig[cnt] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_REVERSIBLE_ERROR:
                        t_end_of_error_idx = cnt
                        break
                    if cnt == len(state_on_hmi_sig) - 1:
                        t_end_of_error_idx = len(state_on_hmi_sig) - 1
                        break

                # Check general screen during reversible error
                for cnt in range(t_detection_idx + 1, t_end_of_error_idx):
                    # Begining of range is t_detection_idx + 1. Reason: Wait one sample for system reaction. This part is describen in Test Case
                    if gem_screen_sig[cnt] != constants.HilCl.Hmi.APHMIGeneralScreen.DIAG_ERROR:

                        actual_value = constants.HilCl.Hmi.APHMIGeneralScreen.DICT_SCREEN.get(gem_screen_sig[cnt])
                        actual_number = int(gem_screen_sig[cnt])

                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Gen_screen']} signal is FAILED, signal switched to {actual_value} ({actual_number}) at {time_signal[cnt]} us"
                            f" but reversible error is active ({signal_name['State_on_HMI']} == PPC_REVERSIBLE_ERROR [{constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_REVERSIBLE_ERROR}])  until {time_signal[t_end_of_error_idx]} us.".split()
                        )
                        break

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, value of signal never switched to PPC_REVERSIBLE_ERROR ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_REVERSIBLE_ERROR})."
                    " There was no detected reversible error in the TestRun."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, value of signal never switched to PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Inform driver about reversible error"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=gem_screen_sig, mode="lines", name=signal_name["Gen_screen"]))

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
    name="Information about reversible error",
    description=(
        "In case function is terminated because of reversible error, then the function shall inform the driver about the error."
    ),
)
class AupRevErrorInfo(TestCase):
    """AupRevErrorInfo Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupRevErrorInfoCheck,
        ]
