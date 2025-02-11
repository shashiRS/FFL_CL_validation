"""

T1:
start_of_measuremen

T2:
"SignalManipulation.eSCInformationPort_brakePressureDriver_bar" > {AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR} (15 Bar)

T3:
end_of_measurement

ET2:
delay -0.1s: // RM Active
"AP.planningCtrlPort.apStates" == {AP_AVG_ACTIVE_IN} (3)
"AP.headUnitVisualizationPort.screen_nu" == {REMOTE_APP_ACTIVE} (3)

delay 0.1s:
"AP.planningCtrlPort.apStates" == {AP_AVG_PAUSE} (5)

INT_ET2_ET3:
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

ALIAS = "SWRT_CNC_AUP_ManeuveringState_Table_43_Req_2325962_2326051"


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        SEAT_OCC = "SignalManipulation.vehicleOccupancyStatusPort_seatOccupancyStatus_driver_nu"
        AP_STATE = "AP.planningCtrlPort.apStates"
        SCREEN_NU = "AP.headUnitVisualizationPort.screen_nu"
        DRIVER_INTERVENTION = "AP.LaDMCStatusPort.driverIntervention_nu"
        BRAKE_PRESSURE = "SignalManipulation.escInformationPort_brakePressureDriver_bar"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]

        self._properties = {
            self.Columns.TIME: [
                "Time",
            ],
            self.Columns.SEAT_OCC: [
                "SignalManipulation.vehicleOccupancyStatusPort_seatOccupancyStatus_driver_nu",
            ],
            self.Columns.AP_STATE: [
                "AP.planningCtrlPort.apStates",
            ],
            self.Columns.SCREEN_NU: [
                "AP.headUnitVisualizationPort.screen_nu",
            ],
            self.Columns.DRIVER_INTERVENTION: [
                "AP.LaDMCStatusPort.driverIntervention_nu",
            ],
            self.Columns.BRAKE_PRESSURE: [
                "SignalManipulation.escInformationPort_brakePressureDriver_bar",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Maneuvering State Table 43 Req 2325962 2326051",
    description=(
        "This test case verifies that during Remote Maneuvering a condition is triggered (brake pedal operation), AutomatedParkingCore transition to other state while \
        the brake pressure detected and if it is higher than AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR(15) ."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringState_Table_43_Req_2325962_2326051_TS(TestStep):
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
            brake_pressure = signals[Signals.Columns.BRAKE_PRESSURE]
            ap_state = signals[Signals.Columns.AP_STATE]
            screen_nu = signals[Signals.Columns.SCREEN_NU]

            signals["status_ap_state"] = ap_state.apply(lambda x: fh.get_status_label(x, aup.AP_STATES))
            signals["status_screen_nu"] = screen_nu.apply(lambda x: fh.get_status_label(x, aup.SCREEN_NU))
            signals["status_pressure"] = brake_pressure.apply(
                lambda x: "Below Threshold" if x < aup.AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR else "Above Threshold"
            )

            def find_time_threshold(signal, state):
                trigger = signal > state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_2 = find_time_threshold(brake_pressure, aup.AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR)
            time_threshold_3 = len(time) - 1

            if time_threshold_2 is not None:
                evaluation_1 = " ".join(
                    f"The evaluation is PASSED because <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> when "
                    f"the signal <b>{Signals.Columns.BRAKE_PRESSURE}</b> > AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR (15 Bar)<br>"
                    f"- the signal {Signals.Columns.AP_STATE} is in AP_AVG_ACTIVE_IN (3) state<br><br>"
                    f"- the signal {Signals.Columns.SCREEN_NU} is in REMOTE_APP_ACTIVE (3) state<br> AND <b>after</b> that timestamp<br>"
                    f"- the signal {Signals.Columns.AP_STATE} transitions to AP_AVG_PAUSE (5) state, as expected.<br>"
                    f"This confirms that Remote Control went from active to paused when AUP detected an brake pressure above the threshold.".split()
                )
                eval_cond_1 = True  # set the evaluation condition as TRUE
                delay_neg_rm = ap_state.iloc[time_threshold_2 - 10] != aup.AP_STATES.AP_AVG_ACTIVE_IN
                delay_pos_rm = ap_state.iloc[time_threshold_2 + 10] != aup.AP_STATES.AP_AVG_PAUSE
                delay_neg_screen = screen_nu.iloc[time_threshold_2 - 10] != aup.SCREEN_NU.REMOTE_APP_ACTIVE

                if delay_neg_rm or delay_pos_rm or delay_neg_screen:
                    evaluation_1 = " ".join(
                        f"The evaluation is FAILED because <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> when "
                        f"the signal <b>{Signals.Columns.BRAKE_PRESSURE}</b> > AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR (15 Bar)<br>"
                        f"- the signal {Signals.Columns.AP_STATE} was in {signals['status_ap_state'].iloc[time_threshold_2 - 10]} ({ap_state.iloc[time_threshold_2 - 10]}) state<br>"
                        f"- the signal {Signals.Columns.SCREEN_NU} was in {signals['status_screen_nu'].iloc[time_threshold_2 - 10]} ({screen_nu.iloc[time_threshold_2 - 10]}) state<br> AND <b>after</b> that timestamp<br>"
                        f"- the signal {Signals.Columns.AP_STATE} was in {signals['status_ap_state'].iloc[time_threshold_2 + 10]} ({ap_state.iloc[time_threshold_2 + 10]}) state.".split()
                    )

                    eval_cond_1 = False
            else:
                # create an evaluation text for the moment when the threshold isn't found, set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_1 = " ".join(
                    f"Evaluation not possible, the trigger value {Signals.Columns.BRAKE_PRESSURE}  >  AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR (15 Bar)  was never found.".split()
                )

            if time_threshold_2 is not None and time_threshold_3 is not None:
                evaluation_2 = " ".join(
                    f"The evaluation is PASSED because between the interval given by the signal <b>{Signals.Columns.BRAKE_PRESSURE}</b> "
                    f">  AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR (15 Bar) and the end of the measurement <b>({round(time.iloc[time_threshold_2], 3)}  "
                    f"- {round(time.iloc[time_threshold_3], 3)})</b>:<br>- the signal {Signals.Columns.AP_STATE} reaches "
                    f"the AP_AVG_FINISHED (8) state once.<br>"
                    f"This confirms that after the RC is in paused state (due to a higher brake pressure) it goes into finished state once.".split()
                )
                eval_cond_2 = True  # set the evaluation condition as TRUE
                rm_interval = ap_state.iloc[time_threshold_2:time_threshold_3]

                mask_rm_finished = rm_interval.rolling(2).apply(
                    lambda x: x[0] != aup.AP_STATES.AP_AVG_FINISHED and x[1] == aup.AP_STATES.AP_AVG_FINISHED, raw=True
                )
                total_rm_finished = mask_rm_finished.sum()

                if total_rm_finished != 1:
                    evaluation_2 = " ".join(
                        f"The evaluation is FAILED because between the interval given by the signal <b>{Signals.Columns.BRAKE_PRESSURE}</b>"
                        f" >  AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR (15 Bar) and the end of the measurement <b>({round(time.iloc[time_threshold_2], 3)}"
                        f"- {round(time.iloc[time_threshold_3], 3)})</b>:<br>- the signal {Signals.Columns.AP_STATE} doesn't reach "
                        f"the AP_AVG_FINISHED (8) state once.<br>This means that after the RC is in paused state (due to a higher brake pressure) it didn't go into finished state once.".split()
                    )
                eval_cond_2 = False
            else:
                # create an evaluation text for the moment when the threshold isn't found, set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_2 = " ".join(
                    f"Evaluation not possible, the trigger value {Signals.Columns.BRAKE_PRESSURE}  >  AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR (15 Bar)   was never found.".split()
                )

            if eval_cond_1 and eval_cond_2:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict1 = "PASSED" if eval_cond_1 else "FAILED" if eval_cond_1 is False else "NOT ASSESSED"
            verdict2 = "PASSED" if eval_cond_2 else "FAILED" if eval_cond_2 is False else "NOT ASSESSED"
            expected_val_1 = """delay -0.1s:\
                AP.planningCtrlPort.apStates == AP_AVG_ACTIVE_IN (3) <br>\
                AP.headUnitVisualizationPort.screen_nu == REMOTE_APP_ACTIVE (3) <br>\
                delay 0.1s: <br>\
                AP.planningCtrlPort.apState == AP_AVG_PAUSE (5)"""
            expected_val_2 = "AP.planningCtrlPort.apStates == AP_AVG_FINISHED once (8)"

            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T2"] = [expected_val_1, evaluation_1, verdict1]
            signal_summary["T2 - T3"] = [expected_val_2, evaluation_2, verdict2]

            remark = html_remark
            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=brake_pressure,
                    mode="lines",
                    name=Signals.Columns.BRAKE_PRESSURE,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_pressure"],
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
            if time_threshold_2 is not None and time_threshold_3 is not None:
                fig.add_vrect(
                    x0=time.iat[time_threshold_2],
                    x1=time.iat[time_threshold_3],
                    fillcolor="LimeGreen",
                    line_width=0,
                    opacity=0.3,
                    # annotation_text="T2-T3",
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
    name="SWRT_CNC_AUP_ManeuveringState_Table_43_Req_2325962_2326051",
    description=(
        "This test case verifies that during Remote Maneuvering a condition is triggered (brake pedal operation), AutomatedParkingCore transition to other state while \
        the brake pressure detected and if it is higher than AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR(15) ."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringState_Table_43_Req_2325962_2326051_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_ManeuveringState_Table_43_Req_2325962_2326051_TS
        ]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br><br>
                T1: start_of_measurement <br>
                T2: <br>
                    <em>SignalManipulation.escInformationPort_brakePressureDriver_bar</em> > AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR (15 Bar)<br>
                T3: end_of_measurement<br><br>
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
