"""
T1:
start_of_measurement

T2:
"AP.hmiOutputPort.userActionHeadUnit_nu" == {TAP_ON_CONTINUE} (20)

T3:
end_of_measurement

ET2:
delay -0.1s: // PARK IN/OUT AND RM Active
("AP.planningCtrlPort.apStates" == {AP_AVG_ACTIVE_IN} (3)
OR "AP.planningCtrlPort.apStates" == {AP_AVG_ACTIVE_OUT}) (4)
AND "AP.headUnitVisualizationPort.screen_nu" == {REMOTE_APP_ACTIVE} (3)

delay 0.1s:
"AP.planningCtrlPort.apStates" == {AP_AVG_PAUSE}) (5)

INT_ET2_ET3:
"AP.planningCtrlPort.apStates" == {AP_AVG_FINISHED}) once (8)
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
ALIAS = "SWRT_CNC_AUP_ManeuveringState_Table_35_Req_2325962_2326048"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        ACT_HEAD_UNIT = "AP.hmiOutputPort.userActionHeadUnit_nu"
        AP_STATES = "AP.planningCtrlPort.apStates"
        SCREEN_NU = "AP.headUnitVisualizationPort.screen_nu"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.TIME: [
                "Time",
            ],
            self.Columns.ACT_HEAD_UNIT: [
                "AP.hmiOutputPort.userActionHeadUnit_nu",
            ],
            self.Columns.SCREEN_NU: [
                "AP.headUnitVisualizationPort.screen_nu",
            ],
            self.Columns.AP_STATES: [
                "AP.planningCtrlPort.apStates",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Maneuvering State Table 35 Req 2325962 2326048",
    description=(
        "This test case verifies that if AUP detects an HMI operation while Remote Control is active, then the RC will be paused and then finished."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringState_Table_35_Req_2325962_2326048_TS(TestStep):
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
            act_head_unit = signals[Signals.Columns.ACT_HEAD_UNIT]
            ap_states = signals[Signals.Columns.AP_STATES]
            screen_nu = signals[Signals.Columns.SCREEN_NU]

            signals["status_act_head_unit"] = act_head_unit.apply(lambda x: fh.get_status_label(x, aup.USER_ACTION))
            signals["status_ap_states"] = ap_states.apply(lambda x: fh.get_status_label(x, aup.AP_STATES))
            signals["status_screen_nu"] = screen_nu.apply(lambda x: fh.get_status_label(x, aup.SCREEN_NU))

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_2 = find_time_threshold(act_head_unit, aup.USER_ACTION.TAP_ON_CONTINUE)
            time_threshold_3 = len(time) - 1

            if time_threshold_2 is not None:
                evaluation_1 = " ".join(
                    f"The evaluation is PASSED because right before the signal <b>{Signals.Columns.ACT_HEAD_UNIT}</b> reaches "
                    f"the TAP_ON_CONTINUE (20) state at timestamp <b>{round(time.iloc[time_threshold_2], 3)} s </b><br>"
                    f" the signal {Signals.Columns.AP_STATES} is either in AP_AVG_ACTIVE_IN (3) or in AP_AVG_ACTIVE_OUT (4) state<br> AND "
                    f" the signal {Signals.Columns.SCREEN_NU} is REMOTE_APP_ACTIVE (3) <br>AND after that timestamp, signal {Signals.Columns.AP_STATES} "
                    f" reaches the AP_AVG_PAUSE (5), as expected. "
                    f"This confirms that AUP detects an HMI operation while Remote Control is active and then RC is paused and then finished".split()
                )
                eval_cond_1 = True  # set the evaluation condition as TRUE
                delay_neg_ap_1 = ap_states.iloc[time_threshold_2 - 10] != aup.AP_STATES.AP_AVG_ACTIVE_IN
                delay_neg_ap_2 = ap_states.iloc[time_threshold_2 - 10] != aup.AP_STATES.AP_AVG_ACTIVE_OUT
                delay_pos_ap = ap_states.iloc[time_threshold_2 + 10] != aup.AP_STATES.AP_AVG_PAUSE
                delay_neg_rm = screen_nu.iloc[time_threshold_2 - 10] != aup.SCREEN_NU.REMOTE_APP_ACTIVE

                if (delay_neg_ap_1 or delay_neg_ap_2) or delay_pos_ap or delay_neg_rm:
                    if (delay_neg_ap_1 and delay_neg_ap_2) and delay_pos_ap and delay_neg_rm:
                        evaluation_1 = " ".join(
                            f"The evaluation is FAILED because right <b>before</b> the signal {Signals.Columns.ACT_HEAD_UNIT} reaches<br> "
                            f"the TAP_ON_CONTINUE (20) state at timestamp <b>{round(time.iloc[time_threshold_2], 3)} s </b>:<br>"
                            f" - the signal {Signals.Columns.AP_STATES} is neither in AP_AVG_ACTIVE_IN (3) nor in AP_AVG_ACTIVE_OUT (4) state <br> "
                            f" - and the signal {Signals.Columns.SCREEN_NU} is not in REMOTE_APP_ACTIVE (3)<br> AND <b>after</b> that timestamp:<br> "
                            f"- signal {Signals.Columns.AP_STATES} doesn't reach the AP_AVG_PAUSE (5) state.<br> "
                            f"This means that AUP doesn't detect the HMI operation and RC doesn't transition to paused and then to finished.".split()
                        )
                    elif delay_neg_ap_1 and delay_neg_ap_2:
                        evaluation_1 = " ".join(
                            f"The evaluation is FAILED because right before the signal {Signals.Columns.ACT_HEAD_UNIT} reaches<br> "
                            f"the TAP_ON_CONTINUE (20) state at timestamp <b>{round(time.iloc[time_threshold_2], 3)} s </b>:<br>"
                            f"- the signal {Signals.Columns.AP_STATES} is neither in AP_AVG_ACTIVE_IN (3) nor in "
                            f"AP_AVG_ACTIVE_OUT (4) state.<br>This means that before the HMI detection, the AUP wasn't active.".split()
                        )
                    elif delay_pos_ap:
                        evaluation_1 = " ".join(
                            f"The evaluation is FAILED because after the signal {Signals.Columns.ACT_HEAD_UNIT} reaches<br> "
                            f"the TAP_ON_CONTINUE (20) state at timestamp <b>{round(time.iloc[time_threshold_2], 3)} s </b>:<br>"
                            f"- the signal {Signals.Columns.AP_STATES} doesn't reach the AP_AVG_PAUSE (5).<br>This means that after the "
                            f"HMI detection, the RC isn't paused".split()
                        )
                    elif delay_neg_rm:
                        evaluation_1 = " ".join(
                            f"The evaluation is FAILED because right before the signal {Signals.Columns.ACT_HEAD_UNIT} reaches<br> "
                            f"the TAP_ON_CONTINUE (20) state at timestamp <b>{round(time.iloc[time_threshold_2], 3)} s </b>:<br>"
                            f"- the signal {Signals.Columns.SCREEN_NU} is not in REMOTE_APP_ACTIVE (3).<br>This means that before the "
                            f"HMI detection, the RC wasn't active.".split()
                        )
                    eval_cond_1 = False
            else:
                # create an evaluation text for the moment when the threshold isn't found, set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_1 = " ".join(
                    f"Evaluation not possible, the trigger value ({Signals.Columns.ACT_HEAD_UNIT} == TAP_ON_CONTINUE (20) "
                    f"was never found.".split()
                )

            if time_threshold_2 is not None and time_threshold_3 is not None:
                evaluation_2 = " ".join(
                    f"The evaluation is PASSED because between the interval given by the signal {Signals.Columns.AP_STATES} <br>"
                    f"having the state TAP_ON_CONTINUE (20) and the end of the measurement <b>({round(time.iloc[time_threshold_2], 3)} - "
                    f"{round(time.iloc[time_threshold_3], 3)})</b>:<br>- the signal {Signals.Columns.RM_STATE} reaches the RM_AVG_FINISHED (4) state once <br>"
                    f"- and the signal {Signals.Columns.AP_STATES} also reaches the AP_AVG_FINISHED (8) state once. "
                    f"This confirms that after the RC/AUP is in paused state it will go into finished state once.".split()
                )
                eval_cond_2 = True  # set the evaluation condition as TRUE
                ap_interval = ap_states.iloc[time_threshold_2:time_threshold_3]

                mask_ap_finished = ap_interval.rolling(2).apply(
                    lambda x: x[0] != aup.AP_STATES.AP_AVG_FINISHED and x[1] == aup.AP_STATES.AP_AVG_FINISHED, raw=True
                )
                total_ap_finished = mask_ap_finished.sum()

                if total_ap_finished != 1:
                    evaluation_2 = " ".join(
                        f"The evaluation is FAILED because between the interval given by the signal {Signals.Columns.AP_STATES} <br>"
                        f"having the state TAP_ON_CONTINUE (20) and the end of the measurement <b>({round(time.iloc[time_threshold_2], 3)} - "
                        f"{round(time.iloc[time_threshold_3], 3)})</b>:<br> - the signal {Signals.Columns.AP_STATES} doesn't reach the AP_AVG_FINISHED (8) state once.<br>"
                        f"This means that AUP doesn't go into finished state just once until the end of measurement.".split()
                    )
                    eval_cond_2 = False
            else:
                # create an evaluation text for the moment when the threshold isn't found, set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_2 = " ".join(
                    f"Evaluation not possible, the trigger value ({Signals.Columns.ACT_HEAD_UNIT} == TAP_ON_CONTINUE (20) "
                    f"was never found.".split()
                )

            if eval_cond_1 and eval_cond_2:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict1 = "PASSED" if eval_cond_1 else "FAILED" if eval_cond_1 is False else "NOT ASSESSED"
            verdict2 = "PASSED" if eval_cond_2 else "FAILED" if eval_cond_2 is False else "NOT ASSESSED"
            expected_val_1 = """delay -0.1s: // PARK IN/OUT AND RM Active <br>\
                (AP.planningCtrlPort.apStates == AP_AVG_ACTIVE_IN (3) <br>\
                OR AP.planningCtrlPort.apStates == AP_AVG_ACTIVE_OUT) (4) <br>\
                AND AP.headUnitVisualizationPort.screen_nu == REMOTE_APP_ACTIVE (3) <br>\
                delay 0.1s: <br>\
                AP.planningCtrlPort.apStates == AP_AVG_PAUSE (5) <br>\
            """
            expected_val_2 = """
                AP.planningCtrlPort.apStates == AP_AVG_FINISHED once (8) <br>\
                """

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
                    y=act_head_unit,
                    mode="lines",
                    name=Signals.Columns.ACT_HEAD_UNIT,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_act_head_unit"],
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
    name="SWRT_CNC_AUP_ManeuveringState_Table_35_Req_2325962_2326048",
    description=(
        "This test case verifies that if AUP detects an HMI operation while Remote Control is active, then the RC will be paused and then finished."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringState_Table_35_Req_2325962_2326048_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_ManeuveringState_Table_35_Req_2325962_2326048_TS
        ]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br><br>
                T1: start_of_measurement <br>
                T2: <br>
                    <em>AP.hmiOutputPort.userActionHeadUnit_nu</em> == TAP_ON_CONTINUE (20) <br><br>
                T3: end_of_measurement<br><br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br>
                T2: <br>
                delay -0.1s: // PARK IN/OUT AND RM Active <br>
                    (<em>AP.planningCtrlPort.apStates</em> == AP_AVG_ACTIVE_IN (3) <br>
                    OR <em>AP.planningCtrlPort.apStates</em> == AP_AVG_ACTIVE_OUT) (4) <br>
                    AND <em>AP.headUnitVisualizationPort.screen_nu</em> == REMOTE_APP_ACTIVE (3) <br>
                delay 0.1s: <br>
                    <em>AP.planningCtrlPort.apStates</em> == AP_AVG_PAUSE (5) <br>
                T2 - T3: <br>
                <em>AP.planningCtrlPort.apStates</em> == AP_AVG_FINISHED once (8) <br>
            </td>
        </tr>
    </table>

"""
