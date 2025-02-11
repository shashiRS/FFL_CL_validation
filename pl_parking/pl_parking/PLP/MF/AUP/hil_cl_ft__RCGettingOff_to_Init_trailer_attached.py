"""RC state switches from RC Getting Off to Init if deactivation is triggered by "Trailer is attached"."""
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
    verifies,
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

__author__ = "VALERICA ATUDOSIEI"

SIGNAL_DATA = "RCGETTINGOFF_TO_INIT_TRAILER"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        GENERAL_MESSAGE = "General_message"
        HMI_INFO = "State_on_HMI"
        TRAILER_STATE = "Trailer_state"
        USER_ACTION_REMOTE = "User_action_remote"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.TRAILER_STATE: "MTS.IO_CAN_Conti_Veh_CAN.Trailer.TrailerConnection",
            self.Columns.USER_ACTION_REMOTE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionRem",
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Transition mode check - RC Getting Off to Init, trailer attached",
    description="Check the transition from RC Getting Off to Init after trailer is attached.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class RCGettingOffToInitTrailerAttachedCheck(TestStep):
    """RCGettingOffToInitTrailerAttachedCheck Test Step."""

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

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        HMI_Info = read_data["State_on_HMI"].tolist()
        user_act_sig = read_data["User_action_remote"].tolist()
        trailer_state = read_data["Trailer_state"].tolist()
        general_message_sig = read_data["General_message"].tolist()
        t1_getting_off_idx = None
        t2_trailer_connected = None
        t3_after_delay_added = None
        trigger_state = True
        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation of AVG State {signal_name['State_on_HMI']} signal is PASSED,"
            f" signal switches to Init - ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE})".split()
        )

        """Evaluation part"""
        # Find when LEAVE_VEHICLE message appeares in APHMIGeneralMessage
        for cnt in range(0, len(general_message_sig)):
            if general_message_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralMessage.LEAVE_VEHICLE:
                t1_getting_off_idx = cnt
                break
        if t1_getting_off_idx is not None:
            # Find the moment when trailer is attached
            for i in range(t1_getting_off_idx, len(HMI_Info)):
                if trailer_state[i] == constants.HilCl.TrailerConnection.OK_TRAILERCONNECTION:
                    t2_trailer_connected = i
                    break
            if t2_trailer_connected is not None:
                # Check if the system is in RC Getting Off until trailer is attached
                for _ in range(t1_getting_off_idx, t2_trailer_connected):
                    if general_message_sig[cnt] != constants.HilCl.Hmi.APHMIGeneralMessage.LEAVE_VEHICLE:
                        trigger_state = False
                        break
                if trigger_state:
                    # taking the timestamp of t2_idx in order to check the reaction 0.5s after
                    t2_timestamp = time_signal[t2_trailer_connected]
                    for y in range(t2_trailer_connected, len(HMI_Info)):
                        if abs(( float(t2_timestamp) - float(time_signal[y]) ) / 10**6) > constants.DgpsConstants.THRESOLD_TIME_S:
                            t3_after_delay_added = y
                            break
                    if t3_after_delay_added is not None:
                        # check the reaction of the system after the added delay
                        if HMI_Info[t3_after_delay_added] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE:
                            test_result = fc.FAIL
                            eval_cond = [False] * 1
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                                f" system didn't change the state to Init after trailer is attached( != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE}).".split()
                            )
                    else:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"TC Failed because the scenario finished before the delay finished ({constants.DgpsConstants.THRESOLD_TIME_S})".split()
                        )
                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"TC Failed because the system is not in RC Getting Off before trailer is attached (APHMIGeneralMessage != {constants.HilCl.Hmi.APHMIGeneralMessage.LEAVE_VEHICLE})".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                            f" trailer not connected (TrailerConnection !={constants.HilCl.TrailerConnection.OK_TRAILERCONNECTION}).".split()
                        )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"TC Failed because system not in RC Getting Off state ({signal_name['General_message']} != {constants.HilCl.Hmi.APHMIGeneralMessage.LEAVE_VEHICLE}).".split()
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
            "Check the reaction of the system during RC Getting Off if trailer is attached"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=general_message_sig, mode="lines", name=signal_name["General_message"]))
        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=trailer_state, mode="lines", name=signal_name["Trailer_state"]))
        fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action_remote"]))
        fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
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

@verifies(
    requirement="1145126",
)
@testcase_definition(
    name="RC Getting Off to Init transition, trailer is attached",
    description="The function shall switch from RC Getting Off to Init mode if trailer is attached.",
    doors_url="https://jazz.conti.de/rm4/resources/BI_5N7qLhS-Ee6D0fn3IY9AdA?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
class RCGettingOffToInitTrailerAttached(TestCase):
    """RCGettingOffToInitTrailerAttached Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            RCGettingOffToInitTrailerAttachedCheck,
        ]
