"""Check the reaction of the system in case driver take the steering wheel control during RA active."""

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

SIGNAL_DATA = "RA_INTERRUPT_MAN_STEER"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USER_ACTION = "User_action"
        GENERAL_MESSAGE = "General_message"
        GENERAL_SCREEN = "General_screen"
        CURRENT_STEER_TRQ = "Current_steer_trq"
        DRIVER_HANDS_ON_DET = "Driver_hands_det"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
            self.Columns.CURRENT_STEER_TRQ: "CM.IO_CAN_Conti_Veh_CAN.VehInput01.CurrentSteerWhlTrq",
            self.Columns.DRIVER_HANDS_ON_DET: "CM.IO_CAN_Conti_Veh_CAN.VehInput01.DriverHandsOnDetection",
        }


example_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="Notification to the driver in case RA Interrupted",
    description="Check the behavior of the system in case the driver manually change the position of the steering wheel during RA",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class SystemAbortedManualSteerRACheck(TestStep):
    """SystemAbortedManualSteerRACheck Test Step."""

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
        user_act_sig = read_data["User_action"].tolist()
        general_screen = read_data["General_screen"].tolist()
        current_steer_trq = read_data["Current_steer_trq"].tolist()
        driver_hands_on_det = read_data["Driver_hands_det"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None
        t4_idx = None

        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation of APHMIGeneralMessage PASSED signal switch to REVERSE_ASSIST_CANCELLED ({signal_name['General_message']} =="
            f" {constants.HilCl.Hmi.APHMIGeneralMessage.REVERSE_ASSIST_CANCELLED}).".split()
        )

        """Evaluation part"""
        # Find the moment when RA feature is selected by the driver
        for idx, item in enumerate(user_act_sig):
            if item == constants.HilCl.Hmi.Command.TAP_ON_REVERSE_ASSIST:
                t1_idx = idx
                break

        # If RA not selected, TC Failed
        if t1_idx is not None:
            # Find the moment when RA start the maneuver
            for cnt in range(t1_idx, len(general_screen)):
                if general_screen[cnt] == constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                    t2_idx = cnt
                    break
            if t2_idx is not None:
                # Find the moment when driver takes the control of the stering wheel changing the position of it
                for i in range(t2_idx,len(general_screen)):
                    precondition = ( (current_steer_trq[i] * 0.01 ) - 12 ) * ( (0.01 * driver_hands_on_det[i]) - 1)
                    if precondition > constants.HilCl.ApThreshold.AP_S_STEERING_TORQUE_THRESH_NM:
                        t3_idx = i
                        break
                if t3_idx is not None:
                    # taking the timestamp of t3_idx in order to check the reaction of the system 0.5s after
                    t3_timestamp = time_signal[t3_idx]
                    for x in range(t3_idx, len(general_screen)):
                        if abs(( float(t3_timestamp) - float(time_signal[x]) ) / 10**6) > constants.DgpsConstants.THRESOLD_TIME_S:
                            t4_idx = x
                            break
                    # check if after 0.5s the system provide the notification to the driver
                    if t4_idx is not None:
                        if general_message_sig[t4_idx] != constants.HilCl.Hmi.APHMIGeneralMessage.REVERSE_ASSIST_CANCELLED:
                            eval_cond = [False] * 1
                            evaluation1 = " ".join(
                            "The system didn't provide the notification to the driver after changing the steering wheel position "
                            f"({signal_name['General_message']} != {constants.HilCl.Hmi.APHMIGeneralMessage.REVERSE_ASSIST_CANCELLED}) within 500ms.".split()
                            )
                    else:
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                        f"TC Failed because the scenario finished before the added delay ({constants.HilCl.ApThreshold.AP_G_ROLLED_DIST_OUT_THRESH_M}).".split()
                        )
                else:
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                    "TC Failed because steering angle position has not been changed during RA active.".split()
                    )
            else:
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                        f"TC Failed because AP function didn't start the RA ( {signal_name['General_screen']} !="
                        f" {constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST}).".split()
                    )
        else:
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                    f"TC Failed because the driver never selected the RA option ( {signal_name['User_action']} !="
                    f" {constants.HilCl.Hmi.Command.TAP_ON_REVERSE_ASSIST}).".split()
                )

        signal_summary["Check the reaction of the system in case the driver change the steering wheel position during RA active"] = evaluation1

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=general_message_sig, mode="lines", name=signal_name["General_message"]))
        fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
        fig.add_trace(go.Scatter(x=time_signal, y=general_screen, mode="lines", name=signal_name["General_screen"]))
        fig.add_trace(go.Scatter(x=time_signal, y=current_steer_trq, mode="lines", name=signal_name["Current_steer_trq"]))
        fig.add_trace(go.Scatter(x=time_signal, y=driver_hands_on_det, mode="lines", name=signal_name["Driver_hands_det"]))
        fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[us]")
        fig.update_layout(PlotlyTemplate.lgt_tmplt)

        plot_titles.append("")
        plots.append(fig)
        remarks.append("")


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
    name="RA interrupted",
    description=f"The RA feature shall switch to REVERSE_ASSIST_CANCELED({constants.HilCl.Hmi.APHMIGeneralMessage.REVERSE_ASSIST_CANCELLED}) after steering wheel pos has been manually changed",
    doors_url="https://jazz.conti.de/rm4/resources/BI_4Mt_gBELEe-6Fe3A58PPug?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F26252"
)
class SystemAbortedManualSteerRA(TestCase):
    """SystemAbortedManualSteerRA Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    # Important information:
    # This script check the behavior of the system in case a snow/sand/soil pile is present in front of the ego vehicle while driving

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SystemAbortedManualSteerRACheck,
        ]
