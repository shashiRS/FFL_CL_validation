"""Mode transition, Automated Reversing Precondition Mode to Automated Reversing, Timeout"""

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

SIGNAL_DATA = "RA_AUT_PRE_TOAUT_TIME"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USEER_ACTION = "User_action"
        HMI_INFO = "State_on_HMI"
        GENERAL_SCREEN = "General_screen"
        RA_POSSIBLE = "RA_possible"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USEER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
            self.Columns.RA_POSSIBLE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral2.APHMIGeneralRevAssistPoss",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Timeout check",
    description="Check RA function reaction if START RA is sent in time treshold.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupRaAutPreToAutTimeCheck(TestStep):
    """AupRaAutPreToAutTimeCheck Test Step."""

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
        general_scrren_sig = read_data["General_screen"].tolist()
        user_act_sig = read_data["User_action"].tolist()
        ra_poss_sig = read_data["RA_possible"].tolist()

        t1_idx = None
        t2_idx = None

        """Evaluation part"""
        # Find when RA is possibly
        for idx, item in enumerate(ra_poss_sig):
            if item == constants.HilCl.Hmi.APHMIGeneralRevAssistPoss.TRUE:
                t1_idx = idx
                break

        if t1_idx is not None:
            # Find driver activate starts RA
            for cnt in range(t1_idx, len(user_act_sig)):
                if user_act_sig[cnt] == constants.HilCl.Hmi.Command.TAP_ON_REVERSE_ASSIST:
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                # Find when system switch to RA
                eval_cond = [True] * 1

                states_dict = HilClFuntions.States(general_scrren_sig, t1_idx, len(general_scrren_sig), 1)

                counter = 0
                # Keys contains the idx
                # Check mode
                for key in states_dict:
                    if counter == 1:
                        actual_value = constants.HilCl.Hmi.APHMIGeneralScreen.DICT_SCREEN.get(states_dict[key])

                        time_of_tap = time_signal[t2_idx]
                        time_of_switch = time_signal[key]
                        delta_time = time_of_switch - time_of_tap

                        if key < t2_idx:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['General_screen']} signal is FAILED, signal switches into {actual_value} at {time_signal[key]} us"
                                f" before driver taps on TAP_ON_REVERSE_ASSIST ({constants.HilCl.Hmi.Command.TAP_ON_REVERSE_ASSIST})".split()
                            )
                            eval_cond[0] = False
                            break

                        # Check if system switched not into REVERSE_ASSIST
                        if states_dict[key] != constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                            if delta_time < constants.HilCl.ApThreshold.RA_G_ACTIVATION_REQUEST_TIMEOUT * 1e6:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['General_screen']} signal is FAILED, signal switches into {actual_value} at {time_signal[key]} us"
                                    f" but requiered sate is REVERSE_ASSIST ({constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST}) because delta time between user action"
                                    f" and system reaction is {delta_time} us. íThis value is less then {constants.HilCl.ApThreshold.RA_G_ACTIVATION_REQUEST_TIMEOUT * 1e6} us.".split()
                                )
                                eval_cond[0] = False
                                break

                        # Check if system switched into REVERSE_ASSIST but reaction time was not correct
                        if states_dict[key] == constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                            if delta_time > (constants.HilCl.ApThreshold.RA_G_ACTIVATION_REQUEST_TIMEOUT * 1e6):
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['General_screen']} signal is FAILED, signal switches into {actual_value} at {time_signal[key]} us."
                                    f" Reaction time of system is {delta_time} us but"
                                    f" requiered reaction time is {constants.HilCl.ApThreshold.RA_G_ACTIVATION_REQUEST_TIMEOUT * 1e6} us.".split()
                                )
                                eval_cond[0] = False
                                break

                        # Check PASSEd state
                        if states_dict[key] == constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['General_screen']} signal is PASSED, signal switches into {actual_value} at {time_signal[key]} us."
                                f" Reaction time of the system is {delta_time} us."
                                f" This value is less than requiered reaction time ({constants.HilCl.ApThreshold.RA_G_ACTIVATION_REQUEST_TIMEOUT * 1e6} us).".split()
                            )
                            break

                        counter += 1

                    else:
                        counter += 1
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['User_action']} signal is FAILED, signal never switched"
                    f" to TAP_ON_REVERSE_ASSIST ({constants.HilCl.Hmi.Command.TAP_ON_REVERSE_ASSIST})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['RA_possible']} signal is FAILED, signal never switched to TRUE"
                f" ({constants.HilCl.Hmi.APHMIGeneralRevAssistPoss.TRUE})."
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

        signal_summary[
            "Required RA state change: Automated Reversing Precondition Mode to Automated Reversing. Reason: No time out"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=general_scrren_sig, mode="lines", name=signal_name["General_screen"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=ra_poss_sig, mode="lines", name=signal_name["RA_possible"]))
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
    name="Mode transition: Automated Reversing Precondition Mode to Automated Reversing, Timeout",
    description="The RA function shall switch from Automated Reversing Precondition Mode to Automated Reversing"
    f" if activation request timeout {constants.HilCl.ApThreshold.RA_G_ACTIVATION_REQUEST_TIMEOUT} has not exceeded.",
)
class AupRaAutPreToAutTime(TestCase):
    """AupRaAutPreToAutTime Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupRaAutPreToAutTimeCheck,
        ]
