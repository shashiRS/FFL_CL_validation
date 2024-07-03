"""Reversible error check. Reversible error: ABS intervention."""

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

SIGNAL_DATA = "REV_ERR_ABS"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        ABS_STATE = "ABS_state"
        HMI_INFO = "State_on_HMI"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.ABS_STATE: "MTS.ADAS_CAN.Conti_Veh_CAN.FunctionStates01.ABS_ActiveState",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="ABS intervention",
    description=(
        "Check system reaction if ABS intervention is longer than"
        f" {constants.HilCl.ApThreshold.AP_G_ABS_TIME_THRESH_S} s"
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupRevErrAbsCheck(TestStep):
    """AupRevErrAbsCheck Test Step."""

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
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        """Prepare sinals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()
        abs_state_sig = read_data["ABS_state"].tolist()

        act_idx = []
        deact_idx = []
        act_time = []
        t1_idx = None
        evaluation1 = " ".join(
            f"The evaluation is PASSED, reversibel error is detected and it is presented in {signal_name['State_on_HMI']}."
            " Reversible error is an ABS intervention and it is longer than"
            f" {constants.HilCl.ApThreshold.AP_G_ABS_TIME_THRESH_S} s".split()
        )

        """Evaluation part"""
        # Find where ABS get active
        act_idx = HilClFuntions.RisingEdge(abs_state_sig, 0)
        deact_idx = HilClFuntions.FallingEdge(abs_state_sig, 0)

        # Find when AP state switch to Maneuvering
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = cnt
                break

        # Check conditions of TestRun
        # Condition 1: At least one ABS activation
        # Condition 2: Number of activations and number of deactivations are the same
        # Condition 3: AP function switched into Maneuvering mode before ABS intervention
        if len(act_idx) != 0 and len(act_idx) == len(deact_idx) and t1_idx is not None:
            eval_cond = [True] * 1

            if t1_idx > act_idx[0]:
                eval_cond[0] = False
                evaluation1 = " ".join(
                    "The evaluation is FAILED, ABS activated before AP function switched into Maneuvereing mode.".split()
                )
            else:
                # Check all ABS activity
                for cnt in range(0, len(act_idx)):
                    act_time = time_signal[deact_idx[cnt]] - time_signal[act_idx[cnt]]
                    act_time = round(act_time * 1e-6, 4)

                    # Collect AP state between actual ABS activity
                    for index in range(act_idx[cnt], deact_idx[cnt] + 1):
                        if (
                            state_on_hmi_sig[index]
                            == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_REVERSIBLE_ERROR
                        ):
                            # Check system reaction time
                            delta_time = time_signal[index] - time_signal[act_idx[cnt]]
                            delta_time *= 1e-6
                            if delta_time < constants.HilCl.ApThreshold.AP_G_ABS_TIME_THRESH_S:
                                evaluation1 = " ".join(
                                    f"The evaluation is FAILED, AP system detectes reversible error earlier than"
                                    f" AP_G_ABS_TIME_THRESH_S ({constants.HilCl.ApThreshold.AP_G_ABS_TIME_THRESH_S} s)."
                                    f" Detection time is {delta_time}".split()
                                )
                                eval_cond[0] = False
                                break
                            else:
                                # Test PASSED: Reversible error detected, Issue detected after AP_G_ABS_TIME_THRESH_S
                                break

                        # There was no isse detection by AP functionality
                        if index == deact_idx[cnt]:
                            evaluation1 = " ".join(
                                "The evaluation is FAILED, AP system does not detect reversible error,"
                                f" but ABS intervention is {act_time} s and this value is greater"
                                f" than {constants.HilCl.ApThreshold.AP_G_ABS_TIME_THRESH_S} s.".split()
                            )
                            eval_cond[0] = False
                            break

        elif len(act_idx) != 0 and len(act_idx) == len(deact_idx) and t1_idx is None:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                "The evaluation is FAILED, AP funtion never switched into Maneuvering mode in TestRun.".split()
            )

        elif len(act_idx) == 0 and len(act_idx) == len(deact_idx) and t1_idx is not None:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join("The evaluation is FAILED, no ABS intervention in TestRun.".split())

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join("The evaluation is FAILED, invalide TestRun.".split())

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Reversibel error: ABS intervention"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=abs_state_sig, mode="lines", name=signal_name["ABS_state"]))

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
    name="Reversible error detection, ABS intervention",
    description=(
        "The AP function shall have a reversible error, if an ABS intervention is active for longer than"
        f" {constants.HilCl.ApThreshold.AP_G_ABS_TIME_THRESH_S} s."
    ),
)
class FtCommon(TestCase):
    """AupRevErrAbs Test Case."""

    custom_report = MfHilClCustomTestcaseReport
    # Important information:
    # There is only ABS intervention in used TestRun

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupRevErrAbsCheck,
        ]
