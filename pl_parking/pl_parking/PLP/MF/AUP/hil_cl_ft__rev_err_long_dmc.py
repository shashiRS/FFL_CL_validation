"""Reversible error check. Reversible error: Longitudinal DMC report error"""

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

SIGNAL_DATA = "REV_ERR_LONG_DMC"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        LONGITUDINAL_DMC = "Long_DMC"
        HMI_INFO = "State_on_HMI"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.LONGITUDINAL_DMC: "MTS.ADAS_CAN.Conti_Veh_CAN.FunctionStates01.LoDMC_SystemState",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Longitudinal DMC error",
    description="Check system reaction for longitudinal DMC error",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupRevErrLongDmcCheck(TestStep):
    """AupRevErrLongDmcCheck Test Step."""

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
        long_dmc_state_sig = read_data["Long_DMC"].tolist()
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None

        evaluation1 = " ".join(
            f"The evaluation is PASSED, reversibel error is detected and it is presented in {signal_name['State_on_HMI']}."
            " Longitudinal DMC reports a reversible error".split()
        )

        """Evaluation part"""
        # Find when AP switches to Maneuvering
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = cnt
                break
        if t1_idx is not None:
            # Find when LongDMC report error
            for cnt in range(t1_idx, len(long_dmc_state_sig)):
                if long_dmc_state_sig[cnt] == constants.HilCl.DmcState.SYSTEM_ERROR:
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                # Find when LongDMC error solved
                for cnt in range(t2_idx, len(long_dmc_state_sig)):
                    if long_dmc_state_sig[cnt] != constants.HilCl.DmcState.SYSTEM_ERROR:
                        t3_idx = cnt
                        break
                    # If error not solved until end of measure, save last sample
                    if cnt == len(long_dmc_state_sig) - 1:
                        t3_idx = cnt
                        break

                if t3_idx is not None:
                    eval_cond = [True] * 1
                    states_dict = HilClFuntions.States(state_on_hmi_sig, t1_idx, (t2_idx + 1), 1)

                    # Keys contains the idx
                    for key in states_dict:
                        # Check value
                        if states_dict[key] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_REVERSIBLE_ERROR:
                            # Test PASSED
                            break

                        if key == list(states_dict.keys())[-1]:
                            # Tets FAILED
                            evaluation1 = " ".join(
                                "The evaluation is FAILED, AP function does not have a reversible error,"
                                " but the longitudinal DMC reports a reversible error.".split()
                            )
                            eval_cond[0] = False
                            break
                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        "The evaluation is FAILED, TestRun is not valid. Longitudinal DMC error is not"
                        " sloved during TestRun.".split()
                    )

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    "The evaluation is FAILED, TestRun is not valid. There is no longitudinal DMC error"
                    " during TestRun.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                "The evaluation is FAILED, TestRun is not valid. AP state never switched to Maneuvering mode.".split()
            )

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Reversibel error: Longitudinal DMC"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=long_dmc_state_sig, mode="lines", name=signal_name["Long_DMC"]))
            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))

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
    name="Reversible error detection, Longitudinal DMC report",
    description="The AP function shall have a reversible error, if the longitudinal DMC reports a reversible error",
)
class AupRevErrLongDmc(TestCase):
    """AupRevErrLongDmc Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    # Important information:
    # There is only longitudinal DMC error in used TestRun

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupRevErrLongDmcCheck,
        ]
