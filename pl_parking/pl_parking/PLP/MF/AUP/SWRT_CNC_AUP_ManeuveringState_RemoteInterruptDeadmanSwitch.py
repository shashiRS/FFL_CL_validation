"""
T1:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PARKING (2)

T2:
AP.remoteHMIOutputPort.fingerPositionX_px == 4095
AP.remoteHMIOutputPort.fingerPositionY_px == 4095

ET2:
delay -0.1s: AP.trajCtrlRequestPort.drivingModeReq_nu == FOLLOW_TRAJ (1)
delay 0.1s:
AP.trajCtrlRequestPort.drivingModeReq_nu == MAKE_SECURE (3)
AP.trajCtrlRequestPort.emergencyBrakeRequest == True (1)
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
ALIAS = "SWRT_CNC_AUP_ManeuveringState_RemoteInterruptDeadmanSwitch"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        CORE_STATE = "AP.PARKSMCoreStatusPort.parksmCoreState_nu"
        POS_X = "AP.remoteHMIOutputPort.fingerPositionX_px"
        POS_Y = "AP.remoteHMIOutputPort.fingerPositionY_px"
        MODE_REQ = "AP.trajCtrlRequestPort.drivingModeReq_nu"
        BRAKE_REQUEST = "AP.trajCtrlRequestPort.emergencyBrakeRequest"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.CORE_STATE: [
                "AP.PARKSMCoreStatusPort.parksmCoreState_nu",
            ],
            self.Columns.TIME: [
                "Time",
            ],
            self.Columns.POS_X: [
                "AP.remoteHMIOutputPort.fingerPositionX_px",
            ],
            self.Columns.POS_Y: [
                "AP.remoteHMIOutputPort.fingerPositionY_px",
            ],
            self.Columns.MODE_REQ: [
                "AP.trajCtrlRequestPort.drivingModeReq_nu",
            ],
            self.Columns.BRAKE_REQUEST: [
                "AP.trajCtrlRequestPort.emergencyBrakeRequest",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Maneuvering State Remote Interrupt Deadman Switch",
    description=(
        "This test case verifies that in Maneuvering state, in case of remote control, the AutomatedParkingCore core \
            shall stop to follow the path and secure the vehicle in case it receives the information that the driver \
                stopped the actuating of the ExternalUserDevice/RemoteControl."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringState_RemoteInterruptDeadmanSwitch_TS(TestStep):
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
            time_threshold_1 = None
            time_threshold_2 = None
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
            core_state = signals[Signals.Columns.CORE_STATE]
            pos_x = signals[Signals.Columns.POS_X]
            pos_y = signals[Signals.Columns.POS_Y]
            mode_req = signals[Signals.Columns.MODE_REQ]
            brake_request = signals[Signals.Columns.BRAKE_REQUEST]

            signals["status_core"] = core_state.apply(lambda x: fh.get_status_label(x, aup.CORE_STATUS))
            signals["status_mode_req"] = mode_req.apply(lambda x: fh.get_status_label(x, aup.DRIVING_MODE))

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_1 = find_time_threshold(core_state, aup.CORE_STATUS.CORE_PARKING)

            t2_mask = (pos_x == 4095) & (pos_y == 4095)
            if np.any(t2_mask):
                time_threshold_2 = np.argmax(t2_mask)

            if time_threshold_2 is not None:
                evaluation_1 = " ".join(
                    f"The evaluation is PASSED if right <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> "
                    f"at which signals {Signals.Columns.POS_X} and<br> {Signals.Columns.POS_Y} take the value <b>4095<b/>:- the signal "
                    f"{Signals.Columns.MODE_REQ} is in FOLLOW_TRAJ (1) state<br> AND <b>after</b> that timestamp:<br> "
                    f"- the signal {Signals.Columns.MODE_REQ} goes into MAKE_SECURE (3) state<br>- and the signal "
                    f"{Signals.Columns.BRAKE_REQUEST} becomes True (1).<br>"
                    f"This confirms that the AUP stopped to follow the path and secure the vehicle when it recieved the information "
                    f"that the driver stopped the actuating of the RemoteControl/ExternalUserDevice.".split()
                )
                eval_cond_1 = True  # set the evaluation condition as TRUE
                delay_neg_mode = mode_req.iloc[time_threshold_2 - 10] != aup.DRIVING_MODE.FOLLOW_TRAJ
                delay_pos_mode = mode_req.iloc[time_threshold_2 + 10] != aup.DRIVING_MODE.MAKE_SECURE
                delay_pos_brake = brake_request.iloc[time_threshold_2 + 10] != 1

                if delay_neg_mode or delay_pos_mode or delay_pos_brake:
                    if delay_neg_mode and delay_pos_mode and delay_pos_brake:
                        evaluation_1 = " ".join(
                            f"The evaluation FAILED because at the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> when "
                            f"{Signals.Columns.POS_X} and <br> {Signals.Columns.POS_Y} take the value <b>4095</b>:<br>- signal {Signals.Columns.MODE_REQ} "
                            f"doesn't transition to MAKE_SECURE (3) state<br>- and signal {Signals.Columns.BRAKE_REQUEST} doesn't take the value 1<br>"
                            f"AND <b>before</b> that timestamp the signal {Signals.Columns.MODE_REQ} wasn't in FOLLOW_TRAJ (1) state.<br>"
                            f"This means that AUP doesn't stop following the path and doesn't secure the vehicle after receiving the information "
                            f"that the driver has stopped the actuating of the ExternalUSerDevice/RemoteControl".split()
                        )
                    elif delay_neg_mode:
                        evaluation_1 = " ".join(
                            f"The evaluation FAILED because <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> when "
                            f"{Signals.Columns.POS_X} and <br> {Signals.Columns.POS_Y} take the value <b>4095</b>:<br> the signal "
                            f"{Signals.Columns.MODE_REQ} wasn't in FOLLOW_TRAJ (1) state.<br>"
                            f"This means that before receiving the information that the driver has stopped the actuating of the "
                            f"ExternalUSerDevice/RemoteControl the AUP wasn't following the path.".split()
                        )
                    elif delay_pos_mode:
                        evaluation_1 = " ".join(
                            f"The evaluation FAILED because after the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> when "
                            f"{Signals.Columns.POS_X} and<br> {Signals.Columns.POS_Y} take the value <b>4095</b>:<br> the signal {Signals.Columns.MODE_REQ} "
                            f"doesn't transition to MAKE_SECURE (3) state.<br> This means that the AUP doesn't stop follwing the path".split()
                        )
                    elif delay_pos_brake:
                        evaluation_1 = " ".join(
                            f"The evaluation FAILED because right after the timestamp <b>{round(time.iloc[time_threshold_2], 3)} s</b> when "
                            f"{Signals.Columns.POS_X} and<br> {Signals.Columns.POS_Y} take the value <b>4095</b>:<br> the signal {Signals.Columns.BRAKE_REQUEST} "
                            f"doesn't take the value 1.<br> This means that the AUP doesn't secure the vehicle.".split()
                        )
                    eval_cond_1 = False

            else:
                # create an evaluation text for the moment when the threshold isn't found, set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_1 = " ".join(
                    f"Evaluation not possible, the trigger value ({Signals.Columns.POS_X} == 4095 and {Signals.Columns.POS_Y} == 4095) was never found.".split()
                )

            if time_threshold_1 is not None:
                evaluation_2 = " ".join(
                    f"The signal {Signals.Columns.CORE_STATE} reaches the state CORE_PARKING (2) "
                    f"at timestamp <b>{round(time.iloc[time_threshold_1], 3)} s</b>. ".split()
                )
                eval_cond_2 = True  # set the evaluation condition as TRUE
            else:
                evaluation_2 = " ".join(
                    f"The signal {Signals.Columns.CORE_STATE} doesn't reach the state CORE_PARKING (2).".split()
                )
                eval_cond_2 = False
                # set the verdict of the test step
            if eval_cond_1 and eval_cond_2:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict1 = "PASSED" if eval_cond_1 else "FAILED" if eval_cond_1 is False else "NOT ASSESSED"
            verdict2 = "PASSED" if eval_cond_2 else "FAILED" if eval_cond_2 is False else "NOT ASSESSED"
            expected_val_1 = "AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PARKING (2)"
            expected_val_2 = "delay -0.1s: AP.trajCtrlRequestPort.drivingModeReq_nu == FOLLOW_TRAJ (1)<br> \
                                delay 0.1s: AP.trajCtrlRequestPort.drivingModeReq_nu == MAKE_SECURE (3)<br> \
                                AP.trajCtrlRequestPort.emergencyBrakeRequest == True (1)"

            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T1"] = [expected_val_1, evaluation_2, verdict2]
            signal_summary["T2"] = [expected_val_2, evaluation_1, verdict1]

            remark = html_remark
            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=core_state,
                    mode="lines",
                    name=Signals.Columns.CORE_STATE,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_core"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=mode_req,
                    mode="lines",
                    name=Signals.Columns.MODE_REQ,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_mode_req"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=brake_request,
                    mode="lines",
                    name=Signals.Columns.BRAKE_REQUEST,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=pos_x,
                    mode="lines",
                    visible="legendonly",
                    name=Signals.Columns.POS_X,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=pos_y,
                    mode="lines",
                    visible="legendonly",
                    name=Signals.Columns.POS_Y,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
                title=" Graphical Overview",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            if time_threshold_1 is not None:
                fig.add_vline(
                    x=time.iat[time_threshold_1],
                    line_width=1,
                    line_dash="dash",
                    line_color="darkslategray",
                    annotation_text="T1",
                )
            if time_threshold_2 is not None:
                fig.add_vline(
                    x=time.iat[time_threshold_2],
                    line_width=1,
                    line_dash="dash",
                    line_color="darkslategray",
                    annotation_text="T2",
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
    name="SWRT_CNC_AUP_ManeuveringState_RemoteInterruptDeadmanSwitch",
    description=(
        "This test case verifies that in Maneuvering state, in case of remote control, the AutomatedParkingCore core shall stop to follow the path and secure the vehicle in case it receives the information that the driver stopped the actuating of the ExternalUserDevice/RemoteControl."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringState_RemoteInterruptDeadmanSwitch_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_ManeuveringState_RemoteInterruptDeadmanSwitch_TS
        ]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br><br>
                T1: <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_PARKING (2) <br>
                T2: <br>
                    <em>AP.remoteHMIOutputPort.fingerPositionX_px</em> == 4095 <br>
                    <em>AP.remoteHMIOutputPort.fingerPositionY_px</em> == 4095 <br><br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br>
                T2: <br>
                    delay -0.1s: <em>AP.trajCtrlRequestPort.drivingModeReq_nu</em> == FOLLOW_TRAJ (1) <br>
                    delay 0.1s: <br>
                        <em>AP.trajCtrlRequestPort.drivingModeReq_nu</em> == MAKE_SECURE  (3) <br>
                        <em>AP.trajCtrlRequestPort.emergencyBrakeRequest</em> == True (1) <br>

            </td>
        </tr>
    </table>


"""
