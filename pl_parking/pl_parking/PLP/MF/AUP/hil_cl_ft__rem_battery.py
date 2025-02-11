"""SOTIF, Remote controller battery level"""

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

SIGNAL_DATA = "SOTIF_REM_BAT_LVL"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        REM_BAT_LVL = "Rem_battery_level"
        REM_GENERAL_MESSAGE = "Rem_general_message"
        REM_USER_ACTION = "Rem_user_action"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.REM_BAT_LVL: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutBatteryLevelRem",
            self.Columns.REM_GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral2.APHMIGeneralMessageRemote",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Remote device batterly level check",
    description="Check system reaction if levle of battery is under the defined limit when user want to start remote parking maneuver.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class SotifRemBattCheck(TestStep):
    """SotifRemBattCheck Test Step."""

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
        rem_message_sig = read_data["Rem_general_message"].tolist()
        rem_battery_lvl_sig = read_data["Rem_battery_level"].tolist()

        t_baterry_low_idx = None
        t_low_battery_detected_idx = None
        t_perform_parking_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['State_on_HMI']} signal and {signal_name['Rem_general_message']} is PASSED. {signal_name['State_on_HMI']} signal does not switch to"
            f" PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}) when driver want to start maneuvering and"
            f" {signal_name['Rem_battery_level']} signal presents LOW_ENERGY ({constants.HilCl.Hmi.APHMIGeneralMessageRemote.LOW_ENERGY}).".split()
        )

        """Evaluation part"""

        # Find when battery level is under the limit
        for cnt, item in enumerate(rem_battery_lvl_sig):
            if item < constants.HilCl.SotifParameters.REM_BATTERY_LIMIT_LOW:
                t_baterry_low_idx = cnt
                break

        if t_baterry_low_idx is not None:
            eval_cond = [True] * 2

            # Check states after battery low event
            for cnt in range(t_baterry_low_idx, len(state_on_hmi_sig)):
                if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:

                    eval_cond[0] = False
                    t_perform_parking_idx = cnt
                    break

            # Check remote message after battery low event
            for cnt in range(t_baterry_low_idx, len(rem_message_sig)):
                if rem_message_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralMessageRemote.LOW_ENERGY:
                    t_low_battery_detected_idx = cnt
                    break

            if t_low_battery_detected_idx is None:

                eval_cond[1] = False

            if eval_cond[0] is False and eval_cond[1] is False:
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['State_on_HMI']} signal and {signal_name['Rem_general_message']} is FAILED. {signal_name['State_on_HMI']} signal switches to"
                    f" PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}) at {time_signal[t_perform_parking_idx]} us and"
                    f" {signal_name['Rem_battery_level']} signal does not present LOW_ENERGY ({constants.HilCl.Hmi.APHMIGeneralMessageRemote.LOW_ENERGY})"
                    f" but battery level is below {constants.HilCl.SotifParameters.REM_BATTERY_LIMIT_LOW} % since {time_signal[t_baterry_low_idx]} us.".split()
                )
            elif eval_cond[0] is True and eval_cond[1] is False:
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Rem_general_message']} signal is FAILED, value of signal does not switch to LOW_ENERGY ({constants.HilCl.Hmi.APHMIGeneralMessageRemote.LOW_ENERGY})"
                    f" but value of battery level was below {constants.HilCl.SotifParameters.REM_BATTERY_LIMIT_LOW} %.".split()
                )

            elif eval_cond[0] is False and eval_cond[1] is True:
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, system switches to PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}) at {time_signal[cnt]} us"
                    f" but value of battery level was never below {constants.HilCl.SotifParameters.REM_BATTERY_LIMIT_LOW} %.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Rem_battery_level']} signal is FAILED, value of battery level was never below {constants.HilCl.SotifParameters.REM_BATTERY_LIMIT_LOW} %."
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

        signal_summary["System shall not start maneuvering and shall show a message about low battery level"] = (
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
            fig.add_trace(
                go.Scatter(x=time_signal, y=rem_message_sig, mode="lines", name=signal_name["Rem_general_message"])
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=rem_battery_lvl_sig, mode="lines", name=signal_name["Rem_battery_level"])
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
    name="SOTIF, Battery level of remote device is low.",
    description=f"The low speed maneuvering process shall not started"
    f" if the battery level of the remote controller is below {constants.HilCl.SotifParameters.REM_BATTERY_LIMIT_LOW} %",
)
class SotifRemBatt(TestCase):
    """SotifRemBatt Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SotifRemBattCheck,
        ]
