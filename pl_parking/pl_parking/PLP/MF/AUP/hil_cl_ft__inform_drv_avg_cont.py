"""Driver Interaction during Automated Vehicle Guidance, Provide a means enabling the driver to continue the current maneuver"""

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

SIGNAL_DATA = "INFORM_DRIVER_AVG_ACTIVE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USEER_ACTION = "User_action"
        HMI_INFO = "State_on_HMI"
        AVG_TYPE = "AVG_type"
        CONTINUE_POSSIBLE = "Continue_possible"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USEER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.CONTINUE_POSSIBLE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralContinuePoss",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Inform driver about possibility of continue",
    description="Check system inform driver about possibility of continue.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class CommonInfDrvAvgContCheck(TestStep):
    """CommonInfDrvAvgContCheck Test Step."""

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
        user_action_sig = read_data["User_action"].tolist()
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()
        continue_poss_sig = read_data["Continue_possible"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None
        t4_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Continue_possible']} signal is PASSED, value of signal is TRUE"
            f" ({constants.HilCl.Hmi.APHMIGeneralContinuePoss.TRUE}) while possible to continue the interrupted manuever.".split()
        )

        """Evaluation part"""
        # Find when Ap switches to Maneuvering mode
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = cnt
                break

        if t1_idx is not None:
            # Find interruption
            for cnt in range(t1_idx, len(user_action_sig)):
                if user_action_sig[cnt] == constants.HilCl.Hmi.Command.TAP_ON_INTERRUPT:
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                eval_cond = [True] * 1

                threshold = constants.HilCl.ApThreshold.AP_G_MAX_INTERRUPT_TIME_S * 1e6
                threshold += time_signal[t2_idx]

                # Find when Poss signal switch to TRUE
                for cnt in range(t2_idx, len(continue_poss_sig)):
                    if continue_poss_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralContinuePoss.TRUE:
                        t3_idx = cnt
                        break

                if t3_idx is not None:

                    # Find when state of Poss signal switch to FALSE
                    for cnt in range(t3_idx, len(continue_poss_sig)):
                        if continue_poss_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralContinuePoss.FALSE:
                            t4_idx = cnt
                            break

                    if t4_idx is not None:
                        eval_cond = [True] * 1

                        # Compare reaction time and threshold
                        if time_signal[t4_idx] > threshold:
                            eval_cond[0] = False
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Continue_possible']} signal is FAILED, state of signal"
                                f" switched to FALSE ({constants.HilCl.Hmi.APHMIGeneralContinuePoss.FALSE}) at {time_signal[t4_idx]} us but limit is {threshold} us.".split()
                            )

                    else:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Continue_possible']} signal is FAILED, state of signal"
                            f" never switched out from TRUE ({constants.HilCl.Hmi.APHMIGeneralContinuePoss.TRUE}) after iterruption."
                            " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                        )
                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Continue_possible']} signal is FAILED, state of signal"
                        f" never switched to TRUE ({constants.HilCl.Hmi.APHMIGeneralContinuePoss.TRUE}) after iterruption."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['User_action']} signal is FAILED, state of signal"
                    f" never switched to TAP_ON_INTERRUPT ({constants.HilCl.Hmi.Command.TAP_ON_INTERRUPT})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, sigal never switched to Maneuvering"
                f" ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})."
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

        signal_summary["Provide a means enabling the driver to continue the current maneuver"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=user_action_sig, mode="lines", name=signal_name["User_action"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=continue_poss_sig, mode="lines", name=signal_name["Continue_possible"])
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
    name="Driver Interaction during Automated Vehicle Guidance",
    description="The function shall provide a means enabling the driver to continue the current maneuver.",
)
class CommonInfDrvAvgCont(TestCase):
    """CommonInfDrvAvgCont Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CommonInfDrvAvgContCheck,
        ]
