"""RA Mode Transition, Precondition Mode to Automated Reversing, Standstill"""

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

SIGNAL_DATA = "RA_PRE_TO_AUT_STAND"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USEER_ACTION = "User_action"
        HMI_INFO = "State_on_HMI"
        DRIVING_DIR = "Driv_dir"
        GENERAL_SCREEN = "General_screen"
        RA_POSS = "RA_possible"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USEER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
            self.Columns.GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
            self.Columns.RA_POSS: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral2.APHMIGeneralRevAssistPoss",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Standstill check",
    description="Check RA function reaction if standstill and all another precondition are fullfiled.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupRaPreToAutCheck(TestStep):
    """AupRaPreToAutCheck Test Step."""

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
        general_scrren_sig = read_data["General_screen"].tolist()
        user_act_sig = read_data["User_action"].tolist()
        driving_dir_sig = read_data["Driv_dir"].tolist()
        ra_poss_sig = read_data["RA_possible"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['General_screen']} signal is PASSED,"
            f" signal swithes to REVERSE_ASSIST ({constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST})"
            f" when standstill condition is also fulfilled.".split()
        )

        """Evaluation part"""

        # Find when APHMIGeneralRevAssistPoss set to TRUE
        for cnt in range(0, len(ra_poss_sig)):
            if ra_poss_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralRevAssistPoss.TRUE:
                t1_idx = cnt
                break

        if t1_idx is not None:

            # Find when driver taps on HMI to start RA
            for cnt in range(t1_idx, len(user_act_sig)):
                if user_act_sig[cnt] == constants.HilCl.Hmi.Command.TAP_ON_REVERSE_ASSIST:
                    t2_idx = cnt
                    break

            if t2_idx is not None:

                # Find when vehicle reach standstill
                for cnt in range(t1_idx, len(driving_dir_sig)):
                    if driving_dir_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL:
                        t3_idx = cnt
                        break

                if t3_idx is not None:
                    eval_cond = [True] * 1

                    states_dict = HilClFuntions.States(general_scrren_sig, t2_idx, len(general_scrren_sig), 1)

                    counter = 0
                    # counter == 1: This has to be REVERSE_ASSIST

                    # Keys contains the idx
                    for key in states_dict:
                        if counter == 1:
                            actual_value = constants.HilCl.Hmi.APHMIGeneralScreen.DICT_SCREEN.get(states_dict[key])
                            actual_number = int(states_dict[key])

                            if key < t3_idx:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['General_screen']} signal is FAILED,"
                                    f" signal switches into {actual_value} ({actual_number}) before vehicle reached stanstill.".split()
                                )
                                eval_cond[0] = False
                                break

                            if states_dict[key] != constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['General_screen']} signal is FAILED,"
                                    f" signal switches into {actual_value} ({actual_number}) but vehicle is in standstill and all another preconditions of"
                                    " Automated Reversing are fulfilled.".split()
                                )
                                eval_cond[0] = False
                                break
                            counter += 1
                        else:
                            counter += 1

                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Driv_dir']} signal is FAILED,"
                        f" signal never swithed to STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL})."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['User_action']} signal is FAILED,"
                    f" signal never swithed to TAP_ON_REVERSE_ASSIST ({constants.HilCl.Hmi.Command.TAP_ON_REVERSE_ASSIST:})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['RA_possible']} signal is FAILED,"
                f" signal never switched to TRUE ({constants.HilCl.Hmi.APHMIGeneralRevAssistPoss.TRUE}). RA maneuver never possible durin TestRun."
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
            "Required RA state change: Precondition Mode to Automated Reversinge. Reason: Ego vehicle is in standstill"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=time_signal, y=general_scrren_sig, mode="lines", name=signal_name["General_screen"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
            fig.add_trace(go.Scatter(x=time_signal, y=ra_poss_sig, mode="lines", name=signal_name["RA_possible"]))
            fig.add_trace(go.Scatter(x=time_signal, y=driving_dir_sig, mode="lines", name=signal_name["Driv_dir"]))

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
    name="RA Mode Transition, Precondition Mode to Automated Reversing, Standstill",
    description="The RA function shall transit from Automated Reversing Precondition Mode to Automated Reversing if the vehicle is in standstill.",
)
class AupRaPreToAut(TestCase):
    """AupRaPreToAut Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupRaPreToAutCheck,
        ]
