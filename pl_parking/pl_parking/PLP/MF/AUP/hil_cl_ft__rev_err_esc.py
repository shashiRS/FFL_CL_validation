"""Reversible error check. Reversible error: ESC  intervention."""

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

SIGNAL_DATA = "REV_ERR_ESC"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        ESC_STATE = "ESC_state"
        HMI_INFO = "State_on_HMI"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.ESC_STATE: "MTS.ADAS_CAN.Conti_Veh_CAN.FunctionStates01.ESC_ActiveState",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="ESC intervention",
    description=(
        "Check system reaction if ESC intervention is longer than"
        f" {constants.HilCl.ApThreshold.AP_G_ESC_TIME_THRESH_S} s"
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupRevErrEscCheck(TestStep):
    """AupRevErrEscCheck Test Step."""

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
        esc_state_sig = read_data["ESC_state"].tolist()

        t_act_idx = None
        t_deact_idx = None
        t_parking_idx = None
        esc_time = None
        evaluation1 = " ".join(
            f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED, state of signal swithces to"
            f" PPC_REVERSIBLE_ERROR ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_REVERSIBLE_ERROR}) if reversible error is detected."
            " Reversible error is an ESC  intervention and it is longer than"
            f" {constants.HilCl.ApThreshold.AP_G_ESC_TIME_THRESH_S} s".split()
        )

        """Evaluation part"""
        # Find parking
        for cnt, item in enumerate(state_on_hmi_sig):
            if item == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_parking_idx = cnt
                break

        if t_parking_idx is not None:
            # Find ESC  activation and deactivation
            for cnt in range(t_parking_idx, len(esc_state_sig)):
                if esc_state_sig[cnt] == constants.HilCl.FunctionActivate.ESC_ACTIVE:
                    t_act_idx = cnt
                    break

            if t_act_idx is not None:

                # Find ESC  deact
                for cnt in range(t_act_idx, len(esc_state_sig)):
                    if esc_state_sig[cnt] != constants.HilCl.FunctionActivate.ESC_ACTIVE:
                        t_deact_idx = cnt
                        break

                if t_deact_idx is not None:
                    # Calculate lenght of ESC
                    esc_time = time_signal[t_deact_idx] - time_signal[t_act_idx]
                    # Set time to sec
                    esc_time = esc_time * 1e-6

                    # Compare with limit
                    if esc_time > constants.HilCl.ApThreshold.AP_G_ESC_TIME_THRESH_S:
                        eval_cond = [True] * 1

                        states_dict = HilClFuntions.States(state_on_hmi_sig, t_act_idx, len(state_on_hmi_sig), 1)

                        counter = 0

                        # Keys contains the idx
                        for key in states_dict:
                            if counter == 1:
                                actual_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE.get(
                                    states_dict[key]
                                )
                                actual_number = int(states_dict[key])

                                reaction_time = time_signal[key] - time_signal[t_act_idx]
                                reaction_time = reaction_time * 1e-6  # Set to sec

                                if (
                                    reaction_time < constants.HilCl.ApThreshold.AP_G_ESC_TIME_THRESH_S
                                    and states_dict[key]
                                    == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_REVERSIBLE_ERROR
                                ):
                                    test_result = fc.FAIL
                                    eval_cond = [False] * 1
                                    evaluation1 = " ".join(
                                        f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, value of signal"
                                        f" switches to PPC_REVERSIBLE_ERROR ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_REVERSIBLE_ERROR})."
                                        f" Reaction time of the system is {reaction_time} sec. This values is less then AP_G_ESC_TIME_THRESH_S"
                                        f" ({constants.HilCl.ApThreshold.AP_G_ESC_TIME_THRESH_S}) sec. System shall not detect reversible error in this case.".split()
                                    )

                                if (
                                    states_dict[key]
                                    != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_REVERSIBLE_ERROR
                                ):
                                    evaluation1 = " ".join(
                                        f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switches to {actual_value} ({actual_number}) mode."
                                        f" Lenght of ESC  intervetion is {esc_time} sec."
                                        f" Requiered state is PPC_REVERSIBLE_ERROR ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_REVERSIBLE_ERROR})".split()
                                    )
                                    eval_cond[0] = False
                                    break
                                counter += 1

                            else:
                                counter += 1
                    else:
                        eval_cond = [True] * 1
                        # Check reversible error in whole measurement after activation
                        for cnt in range(t_act_idx, len(state_on_hmi_sig)):
                            if (
                                state_on_hmi_sig[cnt]
                                == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_REVERSIBLE_ERROR
                            ):
                                eval_cond[0] = False
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, value of signal switches to PPC_REVERSIBLE_ERROR"
                                    f" ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_REVERSIBLE_ERROR}) at {time_signal[cnt]} us but ESC  intervention is"
                                    f" less then AP_G_ESC_TIME_THRESH_S ({constants.HilCl.ApThreshold.AP_G_ESC_TIME_THRESH_S}) sec.".split()
                                )
                                break
                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['ESC_state']} signal is FAILED, value of signal never switched out from ESC _ACTIVE ({constants.HilCl.FunctionActivate.ESC_ACTIVE})."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['ESC_state']} signal is FAILED, value of signal never switched to ESC _ACTIVE ({constants.HilCl.FunctionActivate.ESC_ACTIVE})."
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

        signal_summary["Reversibel error: ESC  intervention"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=esc_state_sig, mode="lines", name=signal_name["ESC_state"]))

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
    name="Reversible error detection, ESC  intervention",
    description=(
        "The AP function shall have a reversible error, if an ESC  intervention is active for longer than"
        f" {constants.HilCl.ApThreshold.AP_G_ESC_TIME_THRESH_S} s."
    ),
)
class AupRevErrEsc(TestCase):
    """AupRevErrEsc Test Case."""

    custom_report = MfHilClCustomTestcaseReport
    # Important information:
    # There is only ESC  intervention in used TestRun

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupRevErrEscCheck,
        ]
