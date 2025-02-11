"""
T1:
start_of_measurement

T2:// Pair and connect remote device
AP.remoteHMIOutputPort.paired_nu = 1
AP.remoteHMIOutputPort.connected_nu = 1

T3:// Pair and disconnect remote device
AP.remoteHMIOutputPort.paired_nu = 0
AP.remoteHMIOutputPort.connected_nu = 0

T4:
T3 + "AP_G_MAX_TIME_REM_DISCONNECT_S" (1s)

T5:
end_of_measurement

ET4:
delay -0.1s:
"AP.planningCtrlPort.apStates" == {AP_AVG_ACTIVE_IN} (3)
"AP.headUnitVisualizationPort.screen_nu" == {REMOTE_APP_ACTIVE} (3)

delay 0.1s:
"AP.planningCtrlPort.apStates" == {AP_AVG_PAUSE} (5)

INT_ET4_ET5:
"AP.planningCtrlPort.apStates" == {AP_AVG_FINISHED} once (8)
"""

"""import libraries"""
import logging
import os
import sys

import numpy as np
import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
"""imports from tsf core"""
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.io.signals import SignalDefinition

"""imports from current repo"""
import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport
from pl_parking.PLP.MF.AUP.SWRT_CNC_AUP_ManeuveringState_CancelAVG import convert_dict_to_pandas
from pl_parking.PLP.MF.constants import AUPConstants as aup

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "SWRT_CNC_AUP_ManeuveringState_Table_91_Req_2325963"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        RM_PAIRED = "AP.remoteHMIOutputPort.paired_nu"
        RM_CONNECTED = "AP.remoteHMIOutputPort.connected_nu"
        AP_STATE = "AP.planningCtrlPort.apStates"
        SCREEN_NU = "AP.headUnitVisualizationPort.screen_nu"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.TIME: [
                "Time",
            ],
            self.Columns.RM_PAIRED: [
                "AP.remoteHMIOutputPort.paired_nu",
            ],
            self.Columns.RM_CONNECTED: [
                "AP.remoteHMIOutputPort.connected_nu",
            ],
            self.Columns.AP_STATE: [
                "AP.planningCtrlPort.apStates",
            ],
            self.Columns.SCREEN_NU: [
                "AP.headUnitVisualizationPort.screen_nu",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Maneuvering State Table 91 Req 2325963",
    description=(
        "This test case verifies that in case or Remote parking, RM shall transition from Maneuvering to Terminate (Pause then Finished) if \
            the remote device is disconnected from the ego vehicle for longer than AP_G_MAX_TIME_REM_DISCONNECT_S seconds."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringState_Table_91_Req_2325963_TS(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
    """

    custom_report = MfCustomTeststepReport  # Specific overview

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    #
    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """  # required docstring
        _log.debug("Starting processing...")
        # Update the details from the results page with the needed information
        # All the information from self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        try:
            time_threshold_2 = None
            time_threshold_3 = None
            time_threshold_4 = None
            time_threshold_5 = None

            eval_cond_1 = False
            eval_cond_2 = False
            eval_cond_3 = False
            eval_cond_4 = False
            evaluation_1 = ""
            evaluation_2 = ""
            evaluation_3 = ""
            evaluation_4 = ""

            # signal_name = signals_obj._properties
            # Make a constant with the reader for signals:
            self.test_result = fc.INPUT_MISSING  # Result
            self.result.measured_result = DATA_NOK  # Initializing the result with data nok
            # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
            plot_titles, plots, remarks = fh.rep([], 3)

            signal_summary = {}  # Initializing the dictionary with data for final evaluation table

            signals = self.readers[ALIAS]
            signals[Signals.Columns.TIMESTAMP] = signals.index

            time = signals[Signals.Columns.TIME]
            rm_paired = signals[Signals.Columns.RM_PAIRED]
            rm_connected = signals[Signals.Columns.RM_CONNECTED]
            ap_state = signals[Signals.Columns.AP_STATE]
            screen_nu = signals[Signals.Columns.SCREEN_NU]

            signals["status_ap_state"] = ap_state.apply(lambda x: fh.get_status_label(x, aup.AP_STATES))
            signals["status_screen_nu"] = screen_nu.apply(lambda x: fh.get_status_label(x, aup.SCREEN_NU))

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_2 = find_time_threshold(rm_paired, 1) and find_time_threshold(rm_connected, 1)
            # Find the time when the remote device was disconnected after it was previously connected
            if time_threshold_2 is not None:
                time_threshold_3 = (
                    (find_time_threshold(rm_paired.iloc[time_threshold_2:], 0))
                    and (find_time_threshold(rm_connected.iloc[time_threshold_2:], 0))
                ) + time_threshold_2
            if time_threshold_3 is not None:
                time_threshold_4 = time_threshold_3 + aup.AP_G_MAX_TIME_REM_DISCONNECT_S * 100
            time_threshold_5 = len(time) - 1

            if time_threshold_2 is not None:
                evaluation_1 = " ".join(
                    f"The evaluation is PASSED because at timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> the signal "
                    f"{Signals.Columns.RM_PAIRED} == 1 and signal {Signals.Columns.RM_CONNECTED} == 1.<br>"
                    f"This confirms that the remote device has been paired and connected.".split()
                )
                eval_cond_1 = True
            else:
                self.result.measured_result = FALSE
                evaluation_1 = " ".join(
                    f"Evaluation not possible, the trigger ({Signals.Columns.RM_PAIRED} == 1 AND {Signals.Columns.RM_CONNECTED} == 1) was never found.".split()
                )

            if time_threshold_3 is not None:
                evaluation_2 = " ".join(
                    f"The evaluation is PASSED because at timestamp <b>{round(time.iloc[time_threshold_3], 3)}s</b> the signal "
                    f"{Signals.Columns.RM_PAIRED} == 0 and signal {Signals.Columns.RM_CONNECTED} == 0.<br>"
                    f"This confirms that the remote device has been disconnected.".split()
                )
                eval_cond_2 = True
            else:
                self.result.measured_result = FALSE
                evaluation_2 = " ".join(
                    f"Evaluation not possible, the trigger ({Signals.Columns.RM_PAIRED} == 0 AND {Signals.Columns.RM_CONNECTED} == 0) was never found.".split()
                )

            if time_threshold_4 is not None:
                evaluation_3 = " ".join(
                    f"The evaluation is PASSED because <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_4], 3)}s</b> when the maximum time hasn't passed:<br>"
                    f"- the signal {Signals.Columns.AP_STATE} is in AP_AVG_ACTIVE_IN (3) state<br><br>"
                    f"- the signal {Signals.Columns.SCREEN_NU} is in REMOTE_APP_ACTIVE (3) state<br> AND <b>after</b> that timestamp<br>"
                    f"- the signal {Signals.Columns.AP_STATE} transitions to AP_AVG_PAUSE (5) state, as expected.<br>"
                    f"This confirms that RM transitioned from Maneuvering to Pause when remote device has been disconnected and 1s has passed.".split()
                )
                eval_cond_3 = True

                delay_neg_rm = ap_state.iloc[time_threshold_2 - 10] != aup.AP_STATES.AP_AVG_ACTIVE_IN
                delay_pos_rm = ap_state.iloc[time_threshold_2 + 10] != aup.AP_STATES.AP_AVG_PAUSE
                delay_neg_screen = screen_nu.iloc[time_threshold_2 - 10] != aup.SCREEN_NU.REMOTE_APP_ACTIVE

                if delay_neg_rm or delay_pos_rm or delay_neg_screen:
                    if delay_neg_rm or delay_neg_screen:
                        evaluation_3 = " ".join(
                            f"The evaluation is FAILED because <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_4], 3)}s</b> when the maximum time allowed <b>hasn't</b> passed yet:<br>"
                            f"- the signal {Signals.Columns.AP_STATE} was in {signals['status_ap_state'].iloc[time_threshold_2 - 10]} ({ap_state.iloc[time_threshold_2 - 10]}) state<br>"
                            f"- the signal {Signals.Columns.SCREEN_NU} was in {signals['status_screen_nu'].iloc[time_threshold_2 - 10]} ({screen_nu.iloc[time_threshold_2 - 10]}) state<br> AND <b>after</b> that timestamp<br>"
                            f"- the signal {Signals.Columns.AP_STATE} was in {signals['status_ap_state'].iloc[time_threshold_2 + 10]} ({ap_state.iloc[time_threshold_2 + 10]}) state."
                            f"This means that RM wasn't in Maneuvering state when the remote device was disconnected.".split()
                        )
                    elif delay_pos_rm:
                        evaluation_3 = " ".join(
                            f"The evaluation is FAILED because <b>after</b> the timestamp <b>{round(time.iloc[time_threshold_4], 3)}s</b> when maximum time allowed has paased<br>"
                            f"- the signal {Signals.Columns.AP_STATE} == {signals['status_ap_state'].iloc[time_threshold_2 + 10]} ({ap_state.iloc[time_threshold_2 + 10]}) <br><br>"
                            f"This means that RM didn't transition to Pause state after 1s after the remote devices was disconnected.".split()
                        )
                    eval_cond_3 = False
            else:
                self.result.measured_result = FALSE
                evaluation_3 = (
                    "Evaluation not possible, the trigger T3 + AP_G_MAX_TIME_REM_DISCONNECT_S (1s) was never found"
                )

            if time_threshold_4 is not None and time_threshold_5 is not None:
                evaluation_4 = " ".join(
                    f"The evaluation is PASSED because <b>between</b> the interval <b>({round(time.iloc[time_threshold_4], 3)}, \
                        {round(time.iloc[time_threshold_5], 3)})s</b>: <br>"
                    f"the signal {Signals.Columns.AP_STATE} == AP_AVG_FINISHED (8) once <br><br>"
                    f"This confirms that RM transitioned from Maneuvering to Pause and then to Finished (once) when the remote device was disconnected for more than 1s.".split()
                )
                eval_cond_4 = True

                ap_state_finish = ap_state.iloc[time_threshold_2:time_threshold_3]

                mask_ap_finish = ap_state_finish.rolling(2).apply(
                    lambda x: x[0] != aup.AP_STATES.AP_AVG_FINISHED and x[1] == aup.AP_STATES.AP_AVG_FINISHED,
                    raw=True,
                )
                total_ap_finish = mask_ap_finish.sum()

                if total_ap_finish != 1:
                    evaluation_4 = " ".join(
                        f"The evaluation is FAILED because <b>between</b> the interval <b>({round(time.iloc[time_threshold_4], 3)}, \
                        {round(time.iloc[time_threshold_5], 3)})s</b>: <br>"
                        f"the signal {Signals.Columns.AP_STATE} != AP_AVG_FINISHED (8) once <br><br>"
                        f"This means that RM didn't transition from Pause to Finished once when remote device was diconnected for more than 1s.".split()
                    )
                    eval_cond_4 = False
            else:
                self.result.measured_result = FALSE
                evaluation_4 = " ".join(
                    f"Evaluation not possible, the trigger value {Signals.Columns.RM_CONNECTED} == 0 was never found.".split()
                )

            if eval_cond_1 and eval_cond_2 and eval_cond_3 and eval_cond_4:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict1 = "PASSED" if eval_cond_1 else "FAILED" if eval_cond_1 is False else "NOT ASSESSED"
            verdict2 = "PASSED" if eval_cond_2 else "FAILED" if eval_cond_2 is False else "NOT ASSESSED"
            verdict3 = "PASSED" if eval_cond_3 else "FAILED" if eval_cond_3 is False else "NOT ASSESSED"
            verdict4 = "PASSED" if eval_cond_4 else "FAILED" if eval_cond_4 is False else "NOT ASSESSED"
            expected_val_1 = "AP.remoteHMIOutputPort.paired_nu = 1<br>\
                AP.remoteHMIOutputPort.connected_nu = 1"
            expected_val_2 = "AP.remoteHMIOutputPort.paired_nu = 0<br>\
                AP.remoteHMIOutputPort.connected_nu = 0"
            expected_val_3 = (
                "delay -0.1:<br>\
                AP.planningCtrlPort.apStates == AP_AVG_ACTIVE_IN (3) <br>\
                AP.headUnitVisualizationPort.screen_nu == REMOTE_APP_ACTIVE (3) <br>\
                delay 0.1s: <br>\
                AP.planningCtrlPort.apState == AP_AVG_PAUSE (5)"
                ""
            )
            expected_val_4 = "AP.planningCtrlPort.apStates == AP_AVG_FINISHED once (8)"

            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T2"] = [expected_val_1, evaluation_1, verdict1]
            signal_summary["T3"] = [expected_val_2, evaluation_2, verdict2]
            signal_summary["T4"] = [expected_val_3, evaluation_3, verdict3]
            signal_summary["T4-T5"] = [expected_val_4, evaluation_4, verdict4]

            remark = html_remark
            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=rm_paired,
                    mode="lines",
                    name=Signals.Columns.RM_PAIRED,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=rm_connected,
                    mode="lines",
                    name=Signals.Columns.RM_CONNECTED,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=ap_state,
                    mode="lines",
                    name=Signals.Columns.AP_STATE,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_ap_state"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=screen_nu,
                    mode="lines",
                    name=Signals.Columns.SCREEN_NU,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_screen_nu"],
                )
            )
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
                title=" Graphical Overview",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            if time_threshold_2 is not None:
                fig.add_vline(
                    x=time.iat[time_threshold_2],
                    line_width=1,
                    line_dash="dash",
                    line_color="darkslategray",
                    annotation_text="T2",
                )
            if time_threshold_3 is not None:
                fig.add_vline(
                    x=time.iat[time_threshold_3],
                    line_width=1,
                    line_dash="dash",
                    line_color="darkslategray",
                    annotation_text="T3",
                )
            if time_threshold_4 is not None:
                fig.add_vline(
                    x=time.iat[time_threshold_4],
                    line_width=1,
                    line_dash="dash",
                    line_color="darkslategray",
                    annotation_text="T4",
                )
            if time_threshold_4 is not None and time_threshold_5 is not None:
                fig.add_vrect(
                    x0=time.iat[time_threshold_4],
                    x1=time.iat[time_threshold_5],
                    fillcolor="LimeGreen",
                    line_width=0,
                    opacity=0.3,
                    # annotation_text="T4-T5",
                    layer="below",
                )
            plots.append(fig)
        except Exception as e:
            _log.error(f"Error processing signals: {e}")
            self.result.measured_result = DATA_NOK
            self.sig_sum = f"<p>Error processing signals : {e}</p>"
            plots.append(self.sig_sum)

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)


# Define the test case definition. This will include the name of the test case and a description of the test.
@testcase_definition(
    name="SWRT_CNC_AUP_ManeuveringState_Table_91_Req_2325963",
    description=(
        "This test case verifies that in case or Remote parking, RM shall transition from Maneuvering to Terminate (Pause then Finished) if \
            the remote device is disconnected from the ego vehicle for longer than AP_G_MAX_TIME_REM_DISCONNECT_S seconds."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringState_Table_91_Req_2325963_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_ManeuveringState_Table_91_Req_2325963_TS
        ]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br>
                T1: start_of_measurement <br>
                T2: <br>
                    <em>AP.remoteHMIOutputPort.paired_nu</em> == 1 <br>
                    <em>AP.remoteHMIOutputPort.connected_nu</em> == 1 <br>
                T3: <br>
                    <em>AP.remoteHMIOutputPort.paired_nu</em> == 0 <br>
                    <em>AP.remoteHMIOutputPort.connected_nu</em> == 0 <br>
                T4:<br>
                    T3 + AP_G_MAX_TIME_REM_DISCONNECT_S (1s)<br>
                T5:<br>
                end_of_measurement<br><br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br>
                T2: <br>
                delay -0.1s: <br>
                    <em>AP.planningCtrlPort.apStates</em> == AP_AVG_ACTIVE_IN (3) <br>
                    <em>AP.headUnitVisualizationPort.screen_nu</em> == REMOTE_APP_ACTIVE (3) <br>
                delay 0.1s: <br>
                    <em>AP.planningCtrlPort.apStates</em> == AP_AVG_PAUSE (5) <br>
                T2 - T3: <br>
                <em>AP.planningCtrlPort.apStates</em> == AP_AVG_FINISHED (8) <br>
            </td>
        </tr>
    </table>

"""
