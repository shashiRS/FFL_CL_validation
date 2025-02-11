"""RA Mode Transition, Terminate to Inactive, Ignition off"""

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

SIGNAL_DATA = "RA_TERM_TO_INIT_IGN"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        GENERAL_MESSAGE = "General_message"
        IGNITION = "Car_ignition"
        CAN_ALIVE_SIG = "CAN_alive_sig"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
            self.Columns.CAN_ALIVE_SIG: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInSituationRear.Alive_APHMIInSituationRear",
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Ignition off check",
    description="Check RA function reaction if ignition set to off in terminate mode.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupRaTermToInitIgnCheck(TestStep):
    """AupRaTermToInitIgnCheck Test Step."""

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
        general_message_sig = read_data["General_message"].tolist()
        ignition_sig = read_data["Car_ignition"].tolist()
        can_alive_sig = read_data["CAN_alive_sig"].tolist()

        t1_idx = None  # RA set to terminate mode
        t2_idx = None  # Ignition off

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['General_message']} signal is PASSED,"
            f" there is no CAN communication after ignition set to OFF ({constants.HilCl.CarMaker.IGNITION_OFF})".split()
        )

        """Evaluation part"""
        # Find terminate mode
        for cnt, sig in enumerate(general_message_sig):
            if sig == constants.HilCl.Hmi.APHMIGeneralMessage.REVERSE_ASSIST_FINISHED:
                t1_idx = cnt
                break

        if t1_idx is not None:
            # Fin when ignition turn off
            for cnt in range(t1_idx, len(ignition_sig)):
                if ignition_sig[cnt] == constants.HilCl.CarMaker.IGNITION_OFF:
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                eval_cond = [True] * 1

                # Check alive signal after ignition off. This signal is a counter. Check next 400 ms
                if (
                    can_alive_sig[t2_idx] != can_alive_sig[t2_idx + 1]
                    and can_alive_sig[t2_idx] != can_alive_sig[t2_idx + 2]
                    and can_alive_sig[t2_idx] != can_alive_sig[t2_idx + 3]
                    and can_alive_sig[t2_idx] != can_alive_sig[t2_idx + 4]
                ):
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Car_ignition']} signal is FAILED,"
                        f" CAN communication not interrupted after ignition switched to OFF ({constants.HilCl.CarMaker.IGNITION_OFF})"
                        f" at {time_signal[t2_idx]} us.".split()
                    )
                    eval_cond[0] = False

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Car_ignition']} signal is FAILED, signal never switched to OFF"
                    f" ({constants.HilCl.CarMaker.IGNITION_OFF})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['General_message']} signal is FAILED, signal never switched to Terminate mode"
                f" ({constants.HilCl.Hmi.APHMIGeneralMessage.REVERSE_ASSIST_FINISHED})."
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

        signal_summary["Required RA state change: Terminate to Inactive. Reason: Ignition off"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=time_signal, y=general_message_sig, mode="lines", name=signal_name["General_message"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=ignition_sig, mode="lines", name=signal_name["Car_ignition"]))
            fig.add_trace(go.Scatter(x=time_signal, y=can_alive_sig, mode="lines", name=signal_name["CAN_alive_sig"]))

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
    name="RA Mode Transition, Terminate to Init, Ignition off",
    description="The RA function shall transit from Terminate to Inactive if the ignition of the ego vehicle is switched off",
)
class AupRaTermToInitIgn(TestCase):
    """AupRaTermToInitIgn Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupRaTermToInitIgnCheck,
        ]
