"""RA Mode Transition, Error to Inactive, Error cleared, Reversible Error"""

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

SIGNAL_DATA = "RA_ERROR_RO_INACTIVE_REV_ERR"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        GENERAL_SCREEN = "General_screen"
        PARKING_CORE_STATE = "State_on_HMI"
        ABS_SIGNAL = "ABS_act"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.PARKING_CORE_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
            self.Columns.ABS_SIGNAL: "MTS.ADAS_CAN.Conti_Veh_CAN.FunctionStates01.ABS_ActiveState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name=" Mode transition: From Error to Inactive",
    description="Check system reaction if reversible error is solved",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupRaErrInactRevCheck(TestStep):
    """AupRaErrInactRevCheck Test Step."""

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
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()
        abs_sig = read_data["ABS_act"].tolist()

        t_ra_begining_idx = None
        t_error_detected_idx = None
        t_abs_act_idx = None
        t_abs_deact_idx = None

        evaluation1 = "".join(
            f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED, state of signal switches to PPC_INACTIVE ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE})"
            f" when reversible erro is solved.".split()
        )

        """Evaluation part"""
        # Find when RA started
        for cnt, item in enumerate(general_scrren_sig):
            if item == constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                t_ra_begining_idx = cnt
                break

        if t_ra_begining_idx is not None:

            # Find when ABS activated
            for cnt in range(t_ra_begining_idx, len(abs_sig)):
                if abs_sig[cnt] == constants.HilCl.FunctionActivate.ABS_ACTIVE:
                    t_abs_act_idx = cnt
                    break

            if t_abs_act_idx is not None:

                # Find ABS deact
                for cnt in range(t_abs_act_idx, len(abs_sig)):
                    if abs_sig[cnt] != constants.HilCl.FunctionActivate.ABS_ACTIVE:
                        t_abs_deact_idx = cnt
                        break

                if t_abs_deact_idx is not None:

                    # Find issue detection
                    for cnt in range(t_abs_act_idx, len(state_on_hmi_sig)):
                        if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_REVERSIBLE_ERROR:
                            t_error_detected_idx = cnt
                            break

                    if t_error_detected_idx is not None:

                        # Check states
                        test_result = fc.PASS
                        self.result.measured_result = TRUE

                        states_dict = HilClFuntions.States(
                            state_on_hmi_sig, t_error_detected_idx, len(state_on_hmi_sig), 1
                        )

                        counter = 0

                        # Keys contains the idx
                        for key in states_dict:
                            if counter == 1:
                                actual_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE.get(
                                    states_dict[key]
                                )

                                actual_number = int(states_dict[key])

                                if key < t_abs_deact_idx:
                                    evaluation1 = " ".join(
                                        f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switches into {actual_value} ({actual_number}) at {time_signal[key]} us"
                                        f" before end of ABS intervetion ({time_signal[t_abs_deact_idx]} us).".split()
                                    )
                                    test_result = fc.FAIL
                                    self.result.measured_result = FALSE
                                    break

                                if states_dict[key] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE:
                                    evaluation1 = " ".join(
                                        f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switches to {actual_value} ({actual_number})"
                                        f" mode after solved reversible errorbut required state is PPC_INACTIVE ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE})".split()
                                    )
                                    test_result = fc.FAIL
                                    self.result.measured_result = FALSE
                                    break
                                counter += 1
                            else:
                                counter += 1

                    else:
                        test_result = fc.FAIL
                        self.result.measured_result = FALSE
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to PPC_REVERSIBLE_ERROR ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_REVERSIBLE_ERROR})."
                            " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                        )

                else:
                    test_result = fc.FAIL
                    self.result.measured_result = FALSE
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['ABS_act']} signal is FAILED, signal never switched out from ABS_ACTIVE ({constants.HilCl.FunctionActivate.ABS_ACTIVE})."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )

            else:
                test_result = fc.FAIL
                self.result.measured_result = FALSE
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['ABS_act']} signal is FAILED, signal never switched to ABS_ACTIVE ({constants.HilCl.FunctionActivate.ABS_ACTIVE})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['General_screen']} signal is FAILED, signal never switched to REVERSE_ASSIST ({constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST})."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        signal_summary["Required state change: Error to Inactive. Reason: Resolved reversible error"] = evaluation1

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
            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=abs_sig, mode="lines", name=signal_name["ABS_act"]))

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
    name="RA, Error to Inactive, Reversible error",
    description="If all the reversible and irreversible error cleared the function transit from Error to Inactive mode.",
)
class AupRaErrInactRev(TestCase):
    """AupRaErrInactRev Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupRaErrInactRevCheck,
        ]
