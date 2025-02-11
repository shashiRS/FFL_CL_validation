"""
T1:
start_of_measurement

T2:
SignalManipulation.additionalBCMStatusPort_ignitionOn_nu = 0

T3: // ONLY TO SHOW THAT THE USER SELECTED PARK OUT
AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu = 25

T4: // START PARKING
AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu = 18

ET2:
delay 0.1s:
AP.planningCtrlPort.apStates == {AP_INACTIVE} (0)

ET4:
delay 0.1s:
AP.planningCtrlPort.apStates == {AP_SCAN_OUT} (2)
AP.CtrlCommandPort.ppcParkingMode_nu == {REMOTE_MANEUVERING} (7)
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
ALIAS = "SWRT_CNC_AUP_ManeuveringState_Table_78_Req_2325894"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        IGN_ON = "SignalManipulation.additionalBCMStatusPort_ignitionOn_nu"
        DEV_CM_QUANT = "AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu"
        AP_STATE = "AP.planningCtrlPort.apStates"
        PARK_MODE = "AP.CtrlCommandPort.ppcParkingMode_nu"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.TIME: [
                "Time",
            ],
            self.Columns.IGN_ON: [
                "SignalManipulation.additionalBCMStatusPort_ignitionOn_nu",
            ],
            self.Columns.DEV_CM_QUANT: [
                "AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu",
            ],
            self.Columns.AP_STATE: [
                "AP.planningCtrlPort.apStates",
            ],
            self.Columns.PARK_MODE: [
                "AP.CtrlCommandPort.ppcParkingMode_nu",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Maneuvering State Table 78 Req 2325894",
    description=(
        "This test case verifies that in case the ignition is switched off the AutomatedParkingCore shall transit \
            from Init to Scanning when a Remote Parking Out Maneuver was requested via a Remote device."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringState_Table_78_Req_2325894_TS(TestStep):
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

            eval_cond_1 = False
            eval_cond_2 = False
            eval_cond_3 = False
            evaluation_1 = ""
            evaluation_2 = ""
            evaluation_3 = ""

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
            ign_on = signals[Signals.Columns.IGN_ON]
            dev_cm_quant = signals[Signals.Columns.DEV_CM_QUANT]
            ap_state = signals[Signals.Columns.AP_STATE]
            park_mode = signals[Signals.Columns.PARK_MODE]

            signals["status_dev_cm_quant"] = dev_cm_quant.apply(lambda x: fh.get_status_label(x, aup.REMOTE_DEVICE))
            signals["status_ap_state"] = ap_state.apply(lambda x: fh.get_status_label(x, aup.AP_STATES))
            signals["status_park_mode"] = park_mode.apply(lambda x: fh.get_status_label(x, aup.PARKING_MODE))

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_2 = find_time_threshold(ign_on, 0)
            time_threshold_3 = find_time_threshold(dev_cm_quant, aup.REMOTE_DEVICE.REM_TAP_ON_PARK_OUT)
            time_threshold_4 = find_time_threshold(dev_cm_quant, aup.REMOTE_DEVICE.REM_TAP_ON_START_PARKING)

            if time_threshold_2 is not None:
                evaluation_1 = " ".join(
                    f"The evaluation is PASSED because <b>after</b> the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> when the signal "
                    f"{Signals.Columns.IGN_ON} == 0 <br>"
                    f"the signal {Signals.Columns.AP_STATE} == {signals['status_ap_state'].iloc[time_threshold_2 + 10]} ({ap_state.iloc[time_threshold_2 + 10]}) <br>"
                    f"This confirms that AUPCore was in Init state when ignition switch was OFF.".split()
                )
                eval_cond_1 = True

                delay_rm = ap_state.iloc[time_threshold_2 + 10] != aup.AP_STATES.AP_INACTIVE

                if delay_rm:
                    evaluation_1 = " ".join(
                        f"The evaluation is FAILED because <b>after</b> the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> when the signal<br>"
                        f"{Signals.Columns.IGN_ON} == 0 <br>"
                        f"the signal {Signals.Columns.AP_STATE} == {signals['status_ap_state'].iloc[time_threshold_2 + 10]} ({ap_state.iloc[time_threshold_2 + 10]}) <br><br>"
                        f"This means that AUPCore wasn't in Init state when ignition switch was OFF.".split()
                    )
                    eval_cond_1 = False
            else:
                self.result.measured_result = FALSE
                evaluation_1 = " ".join(
                    f"Evaluation not possible, the trigger value {Signals.Columns.IGN_ON} == 0 was never found.".split()
                )

            if time_threshold_3 is not None:
                evaluation_2 = " ".join(
                    f"The evaluation is PASSED because the trigger value <br>{Signals.Columns.DEV_CM_QUANT} == REM_TAP_ON_PARK_OUT (25) has been found at\
                        timestamp <b>{round(time.iloc[time_threshold_3], 3)}s</b>.<br><br> This confirms that the user selected 'Parking Out Maneuver' via a Remote Device.".split()
                )
                eval_cond_2 = True
            else:
                self.result.measured_result = FALSE
                evaluation_2 = " ".join(
                    f"Evaluation not possible, the trigger value {Signals.Columns.DEV_CM_QUANT} == REM_TAP_ON_PARK_OUT (25) was never found.".split()
                )

            if time_threshold_4 is not None:
                evaluation_3 = " ".join(
                    f"The evaluation is PASSED because <b>after</b> the timestamp <b>{round(time.iloc[time_threshold_4], 3)}s</b> when the signal <br>"
                    f"{Signals.Columns.DEV_CM_QUANT} == REM_TAP_ON_START_PARKING (18): <br>"
                    f"- the signal {Signals.Columns.AP_STATE} == {signals['status_ap_state'].iloc[time_threshold_4 + 10]} ({ap_state.iloc[time_threshold_4 + 10]}) <br>"
                    f"- the signal {Signals.Columns.PARK_MODE} == {signals['status_park_mode'].iloc[time_threshold_4 + 10]} ({park_mode.iloc[time_threshold_4 + 10]}) <br><br>"
                    f"This confirms that AUPCore tranistioned from Init to Scanning when the 'Parking Out Maneuver' was selected by the user <br>\
                        via Remote Device while the ignition switch was OFF.".split()
                )
                eval_cond_3 = True

                delay_rm = ap_state.iloc[time_threshold_4 + 10] != aup.AP_STATES.AP_SCAN_OUT
                delay_park = park_mode.iloc[time_threshold_4 + 10] != aup.PARKING_MODE.REMOTE_MANEUVERING

                if delay_rm or delay_park:
                    evaluation_3 = " ".join(
                        f"The evaluation is FAILED because <b>after</b> the timestamp <b>{round(time.iloc[time_threshold_4], 3)}s</b> when the signal <br>"
                        f"{Signals.Columns.DEV_CM_QUANT}== REM_TAP_ON_START_PARKING (18):<br>"
                        f"- the signal {Signals.Columns.AP_STATE} == {signals['status_ap_state'].iloc[time_threshold_4 + 10]} ({ap_state.iloc[time_threshold_4 + 10]}) <br>"
                        f"- the signal {Signals.Columns.PARK_MODE} == {signals['status_park_mode'].iloc[time_threshold_4 + 10]} ({park_mode.iloc[time_threshold_4 + 10]}) <br><br>"
                        f"This means that AUPCore didn't transition to Scanning when the 'Parking Out Maneuver' was selected by the user <br>\
                        via Remote Device and the ignition was OFF.".split()
                    )
                    eval_cond_3 = False
            else:
                self.result.measured_result = FALSE
                evaluation_3 = " ".join(
                    f"Evaluation not possible, the trigger value {Signals.Columns.DEV_CM_QUANT} == REM_TAP_ON_START_PARKING (18) was never found.".split()
                )

            if eval_cond_1 and eval_cond_2 and eval_cond_3:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict1 = "PASSED" if eval_cond_1 else "FAILED" if eval_cond_1 is False else "NOT ASSESSED"
            verdict2 = "PASSED" if eval_cond_2 else "FAILED" if eval_cond_2 is False else "NOT ASSESSED"
            verdict3 = "PASSED" if eval_cond_3 else "FAILED" if eval_cond_3 is False else "NOT ASSESSED"
            expected_val_1 = "delay 0.1:<br>\
                AP.planningCtrlPort.apStates == AP_INACTIVE (0)"
            expected_val_2 = "AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu = REM_TAP_ON_PARK_OUT (25)"
            expected_val_3 = "delay 0.1:<br>\
                AP.planningCtrlPort.apStates == AP_SCAN_OUT (2)<br>\
                AP.CtrlCommandPort.ppcParkingMode_nu == REMOTE_MANEUVERING (7)"

            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T2"] = [expected_val_1, evaluation_1, verdict1]
            signal_summary["T3"] = [expected_val_2, evaluation_2, verdict2]
            signal_summary["T4"] = [expected_val_3, evaluation_3, verdict3]

            remark = html_remark
            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=ign_on,
                    mode="lines",
                    name=Signals.Columns.IGN_ON,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=dev_cm_quant,
                    mode="lines",
                    name=Signals.Columns.DEV_CM_QUANT,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_dev_cm_quant"],
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
                    y=park_mode,
                    mode="lines",
                    name=Signals.Columns.PARK_MODE,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_park_mode"],
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
    name="SWRT_CNC_AUP_ManeuveringState_Table_78_Req_2325894",
    description=(
        "This test case verifies that in case the ignition is switched off the AutomatedParkingCore shall transit \
            from Init to Scanning when a Remote Parking Out Maneuver was requested via a Remote device."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringState_Table_78_Req_2325894_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_ManeuveringState_Table_78_Req_2325894_TS
        ]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br>
                T1: start_of_measurement <br>
                T2: <br>
                    <em>SignalManipulation.additionalBCMStatusPort_ignitionOn_nu</em> == 0 <br>
                T3: <br>
                    <em>AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu</em> == 25 <br>
                T4: <br>
                    <em>AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu</em> == 18 <br><br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br>
                T2: <br>
                delay 0.1s: <br>
                    <em>AP.planningCtrlPort.apStates</em> == AP_INACTIVE (0)<br>
                T4: <br>
                delay 0.1s: <br>
                    <em>AP.planningCtrlPort.apStates</em> == AP_SCAN_OUT (1)<br>
                    <em>AP.CtrlCommandPort.ppcParkingMode_nu</em> == REMOTE_MANEUVERING (7)<br>
            </td>
        </tr>
    </table>

"""
