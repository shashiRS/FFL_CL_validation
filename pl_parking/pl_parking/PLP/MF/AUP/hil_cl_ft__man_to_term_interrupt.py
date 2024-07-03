"""Mode Transition check, Maneuvering to Terminate: Interruption"""

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

SIGNAL_DATA = "MANEUVER_TO_TERMINATE_INTERRUPT"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USEER_ACTION = "User_action"
        HMI_INFO = "State_on_HMI"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USEER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Maneuvering to Terminate check",
    description="Check interrupt time dependence of mode transition",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupManTermInterCheck(TestStep):
    """AupManTermInterCheck Test Step."""

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
        user_act_sig = read_data["User_action"].tolist()
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None
        evaluation1 = " ".join(
            f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED, signal switches to Terminate mode when interruption is longer than"
            f" {constants.HilCl.ApThreshold.AP_G_MAX_INTERRUPT_TIME_S} s".split()
        )

        """Evaluation part"""
        # Find when AP switches to Maneuvering mode
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = cnt
                break
        if t1_idx is not None:
            # Find user action(s) on HMI
            for cnt in range(t1_idx, len(user_act_sig)):
                if user_act_sig[cnt] == constants.HilCl.Hmi.Command.TAP_ON_INTERRUPT:
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                # Find user action(s) on HMI
                for cnt in range(t2_idx, len(user_act_sig)):
                    if user_act_sig[cnt] == constants.HilCl.Hmi.Command.TAP_ON_CONTINUE:
                        t3_idx = cnt
                        break

                if t3_idx is not None:
                    eval_cond = [True] * 1
                    counter = 0
                    requiered_sate = None
                    relation_string = ""

                    # counter == 0 : This is Maneuvering mode, because states are collected from the begining of Maneuvering.
                    # counter == 1: This has to be Terminate mode in this case. System has to switch from Maneuvering to Terminate

                    # Collect states of AP after switch to Maneuvering event
                    states_dict = HilClFuntions.States(state_on_hmi_sig, t1_idx, len(state_on_hmi_sig), 1)

                    # Calculate legnth of interruption
                    calc_interruption = time_signal[t3_idx] - time_signal[t2_idx]
                    calc_interruption = calc_interruption * 1e-6

                    # Check lenght of interruption and decide the requiered state
                    if calc_interruption > constants.HilCl.ApThreshold.AP_G_MAX_INTERRUPT_TIME_S:
                        requiered_sate = constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS
                        relation_string = " ".join("longer")
                    else:
                        requiered_sate = constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING
                        relation_string = " ".join("not longer")

                    # Keys contains the idx
                    # Check mode after Maneuvering mode
                    for key in states_dict:
                        if counter == 1:
                            actual_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE.get(
                                states_dict[key]
                            )

                            if key < t2_idx:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switches to {actual_value} at {time_signal[key]} us before interruption.".split()
                                )
                                eval_cond[0] = False
                                break

                            if states_dict[key] != requiered_sate:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, time of interruption is {calc_interruption} s."
                                    f" This value is {relation_string} than {constants.HilCl.ApThreshold.AP_G_MAX_INTERRUPT_TIME_S} s."
                                    f" State of signal is {actual_value} at {time_signal[key]} us but requiered mode is {requiered_sate}.".split()
                                )
                                eval_cond[0] = False
                                break
                        else:
                            counter += 1
                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['User_action']} signal is FAILED, driver never try to continue parking.".split()
                    )

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['User_action']} signal is FAILED, parking maneuver was never interrupted by driver.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to Maneuvering mode.".split()
            )

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Required AP state change: Maneuvering to Terminate. Reason: Interruption longer than limit"] = (
            evaluation1
        )

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))

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
    name="Mode transition: Maneuvering to Terminate",
    description=f"The maneuver is interrupted for longer than {constants.HilCl.ApThreshold.AP_G_MAX_INTERRUPT_TIME_S} s (tunable).",
)
class FtCommon(TestCase):
    """AupManTermInter Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupManTermInterCheck,
        ]
