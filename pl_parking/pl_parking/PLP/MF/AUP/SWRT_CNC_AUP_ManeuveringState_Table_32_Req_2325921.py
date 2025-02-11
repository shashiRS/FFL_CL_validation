"""
T1:
start_of_measurement

T2: // Select parking slot
"AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu" == {REM_TAP_ON_PARKING_SPACE_1} (1)

T3:
T2 + {AP_G_MAX_WAIT_TIME_REM_S} (120s)

ET3:
delay -0.1s:
"AP.planningCtrlPort.apStates" == {AP_SCAN_OUT} (2)

delay 0.1s:
"AP.planningCtrlPort.apStates" == {AP_INACTIVE} (0)
"AP.CtrlCommandPort.stdRequest_nu" == {STD_REQ_INIT} (1)
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
from pl_parking.PLP.MF.constants import HilCl as hil

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "SWRT_CNC_AUP_ManeuveringState_Table_32_Req_2325921"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        DEVICE_CM_QUANT = "AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu"
        AP_STATES = "AP.planningCtrlPort.apStates"
        STD_REQUEST = "AP.CtrlCommandPort.stdRequest_nu"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.TIME: [
                "Time",
            ],
            self.Columns.DEVICE_CM_QUANT: [
                "AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu",
            ],
            self.Columns.AP_STATES: [
                "AP.planningCtrlPort.apStates",
            ],
            self.Columns.STD_REQUEST: [
                "AP.CtrlCommandPort.stdRequest_nu",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Maneuvering State Table 32 Req 2325921",
    description=(
        "This test case verifies that in case of Remote Control is scanning phase and no input is received after AP_G_MAX_WAIT_TIME_REM_S (120s),\
                the Remote Control should become inactive."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringState_Table_32_Req_2325921_TS(TestStep):
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
            eval_cond_1 = False
            eval_cond_2 = False
            evaluation_1 = ""
            evaluation_2 = ""
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
            device_cm_qaunt = signals[Signals.Columns.DEVICE_CM_QUANT]
            ap_states = signals[Signals.Columns.AP_STATES]
            std_request = signals[Signals.Columns.STD_REQUEST]

            signals["status_device_cm_quant"] = device_cm_qaunt.apply(
                lambda x: fh.get_status_label(x, aup.REMOTE_DEVICE)
            )
            signals["status_ap_states"] = ap_states.apply(lambda x: fh.get_status_label(x, aup.AP_STATES))
            signals["status_std_request"] = std_request.apply(lambda x: fh.get_status_label(x, aup.STD_REQUEST))

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_2 = find_time_threshold(device_cm_qaunt, aup.REMOTE_DEVICE.REM_TAP_ON_PARKING_SPACE_1)

            # Calculate T3 (T2 + AP_G_MAX_WAIT_TIME_REM_S)
            if time_threshold_2 is not None:
                if time_threshold_2 + (hil.ApThreshold.AP_G_MAX_WAIT_TIME_REM_S) * 100 < len(time) + 11:
                    time_threshold_3 = time_threshold_2 + (hil.ApThreshold.AP_G_MAX_WAIT_TIME_REM_S) * 100
                else:
                    time_threshold_3 = len(time) - 11

            meas_long = True if len(time) > ((hil.ApThreshold.AP_G_MAX_WAIT_TIME_REM_S) * 100 + 10) else False

            if time_threshold_3 is not None and meas_long:
                evaluation_1 = " ".join(
                    f"The evaluation is PASSED because right <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_3], 3)}s</b>:<br>"
                    f"- the signal {Signals.Columns.AP_STATES} is in AP_SCAN_OUT (2) state <br> AND <b>after</b> that timestamp:<br>- the signal"
                    f"{Signals.Columns.AP_STATES} is in AP_INACTIVE (0) state<br>- and the signal {Signals.Columns.STD_REQUEST}"
                    f"goes into STD_REQ_INIT (1) state.<br>"
                    f"This confirms that if no input is received after AP_G_MAX_WAIT_TIME_REM_S (120s),the Remote Control becomes inactive.".split()
                )
                eval_cond_1 = True  # set the evaluation condition as TRUE
                delay_neg_rm = ap_states.iloc[time_threshold_3 - 10] != aup.AP_STATES.AP_SCAN_OUT
                delay_pos_rm = ap_states.iloc[time_threshold_3 + 10] != aup.AP_STATES.AP_INACTIVE
                delay_pos_std = std_request.iloc[time_threshold_3 + 10] != aup.STD_REQUEST.STD_REQ_INIT

                if delay_neg_rm or delay_pos_rm or delay_pos_std:
                    if delay_neg_rm and delay_pos_rm and delay_pos_std:
                        evaluation_1 = " ".join(
                            f"The evaluation FAILED because right <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_3], 3)}s:</b><br>"
                            f"- signal {Signals.Columns.AP_STATES} wasn't in AP_SCAN_OUT (2) state<br> AND <b>after</b> that timestamp:<br>"
                            f"- the signal {Signals.Columns.AP_STATES} doesn't transition to AP_INACTIVE (0) state<br>- and signal "
                            f"{Signals.Columns.STD_REQUEST} doesn't reach the STD_REQ_INIT (1) state.".split()
                        )
                    elif delay_neg_rm:
                        evaluation_1 = " ".join(
                            f"The evaluation FAILED because right <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_3], 3)}s:</b><br>"
                            f"signal {Signals.Columns.AP_STATES} wasn't in AP_SCAN_OUT (2) state.".split()
                        )
                    elif delay_pos_rm:
                        evaluation_1 = " ".join(
                            f"The evaluation FAILED because <b>after</b> the timestamp <b>{round(time.iloc[time_threshold_3], 3)}s</b><br>"
                            f"the signal {Signals.Columns.AP_STATES} doesn't transition to AP_INACTIVE (0) state.<br>"
                            f"This means that the maximum allowed time for the RC to become inactive after receiving no input is not respected.".split()
                        )
                    elif delay_pos_std:
                        evaluation_1 = " ".join(
                            f"The evaluation FAILED because <b>after</b> the timestamp <b>{round(time.iloc[time_threshold_3], 3)}s</b><br>"
                            f"the signal {Signals.Columns.STD_REQUEST} doesn't transition to STD_REQ_INIT (1) state.".split()
                        )
                    eval_cond_1 = False

            else:
                # create an evaluation text for the moment when the threshold isn't found, set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_1 = " ".join(
                    f"Evaluation not possible, the trigger value ({Signals.Columns.DEVICE_CM_QUANT} == REM_TAP_ON_PARKING_SPACE_1 (1) + 120s was never found.".split()
                )

            if time_threshold_2 is not None:
                evaluation_2 = " ".join(
                    f"The signal {Signals.Columns.DEVICE_CM_QUANT} reaches the state REM_TAP_ON_PARKING_SPACE_1 (1) "
                    f"at timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b>.<br>"
                    f"This confirms that a parking slot has been selected".split()
                )
                eval_cond_2 = True  # set the evaluation condition as TRUE
            else:
                evaluation_2 = " ".join(
                    f"The signal {Signals.Columns.DEVICE_CM_QUANT} doesn't reach the state REM_TAP_ON_PARKING_SPACE_1 (1).".split()
                )
                eval_cond_2 = False
                # set the verdict of the test step
            if eval_cond_1 and eval_cond_2:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict1 = "PASSED" if eval_cond_1 else "FAILED" if eval_cond_1 is False else "NOT ASSESSED"
            verdict2 = "PASSED" if eval_cond_2 else "FAILED" if eval_cond_2 is False else "NOT ASSESSED"
            expected_val_1 = "AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu == REM_TAP_ON_PARKING_SPACE_1 (1)"
            expected_val_2 = "delay -0.1s: AP.planningCtrlPort.apStates == AP_SCAN_OUT (2) <br>\
                delay 0.1s: AP.planningCtrlPort.apStates == AP_INACTIVE (0)<br> \
            AP.CtrlCommandPort.stdRequest_nu == STD_REQ_INIT (1)"

            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T2"] = [expected_val_1, evaluation_2, verdict2]
            signal_summary["T3"] = [expected_val_2, evaluation_1, verdict1]

            remark = html_remark
            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=device_cm_qaunt,
                    mode="lines",
                    name=Signals.Columns.DEVICE_CM_QUANT,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_device_cm_quant"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=ap_states,
                    mode="lines",
                    name=Signals.Columns.AP_STATES,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_ap_states"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=std_request,
                    mode="lines",
                    name=Signals.Columns.STD_REQUEST,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br><extra></extra>",
                    text=signals["status_std_request"],
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
    name="SWRT_CNC_AUP_ManeuveringState_Table_32_Req_2325921",
    description=(
        "This test case verifies that in case of Remote Control - scanning phase no input is received after AP_G_MAX_WAIT_TIME_REM_S (120s),\
                the Remote Control should become inactive."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringState_Table_32_Req_2325921_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_ManeuveringState_Table_32_Req_2325921_TS
        ]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br><br>
                T1: start_of_measurement <br>
                T2: //Select parking slot <br>
                    <em>AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu</em> == REM_TAP_ON_PARKING_SPACE_1 (1) <br>
                T3:<br>
                    T2 + AP_G_MAX_WAIT_TIME_REM_S (120s) <br><br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br>
                T3: <br>
                    delay -0.1s: <em>AP.planningCtrlPort.apStates</em> == AP_SCAN_OUT (2) <br>
                    delay 0.1s: <br>
                        <em>AP.planningCtrlPort.apStates</em> == AP_INACTIVE  (0) <br>
                        <em>AP.CtrlCommandPort.stdRequest_nu</em> == STD_REQ_INIT (1) <br>

            </td>
        </tr>
    </table>


"""
