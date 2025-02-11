"""
T1:
start_of_measurement

T2:
SignalManipulation.escInformationPort_absState_nu = {ABS_ACTIVE} (1)

T3:
T2 + AP_G_ABS_TIME_THRESH_S (0.5s)

ET3:
delay -0.1s:
AP.planningCtrlPort.apStates == {AP_AVG_ACTIVE_IN} (3)
AP.PARKSMCoreStatusPort.parksmCoreState_nu == {CORE_PARKING} (2)

delay 0.1s:
(AP.planningCtrlPort.apStates == {AP_AVG_PAUSE}) (5))
OR (AP.psmDebugPort.stateVarESM_nu == {ESM_REVERSIBLE_ERROR} (2)
AP.PARKSMCoreStatusPort.parksmCoreState_nu == {CORE_ERROR} (5))

Case ApState == Pause:
Check if ApStates goes in Finish state after Pause State
AP.planningCtrlPort.apStates == {AP_AVG_FINISHED}) once (8)
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
ALIAS = "SWRT_CNC_AUP_ManeuveringState_Table_118_Req_2325960_2326036"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        ABS_STATE = "SignalManipulation.escInformationPort_absState_nu"
        AP_STATES = "AP.planningCtrlPort.apStates"
        CORE_STATE = "AP.PARKSMCoreStatusPort.parksmCoreState_nu"
        VAR_ESM = "AP.psmDebugPort.stateVarESM_nu"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.TIME: [
                "Time",
            ],
            self.Columns.ABS_STATE: [
                "SignalManipulation.escInformationPort_absState_nu",
            ],
            self.Columns.AP_STATES: [
                "AP.planningCtrlPort.apStates",
            ],
            self.Columns.CORE_STATE: [
                "AP.PARKSMCoreStatusPort.parksmCoreState_nu",
            ],
            self.Columns.VAR_ESM: [
                "AP.psmDebugPort.stateVarESM_nu",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Maneuvering State Table 118 Req 2325960 2326036",
    description=(
        "This test case verifies that AUPCore shall transition from Maneuvering to Terminate (Error or Pause-Finished) if \
            the AUPCore receives the information  that an ABS intervention is active for longer than 0.5 s."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringState_Table_118_Req_2325960_2326036_TS(TestStep):
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
            evaluation_1 = ""

            # signal_name = signals_obj._properties
            # Make a constant with the reader for signals:
            self.test_result = fc.INPUT_MISSING  # Result
            self.result.measured_result = DATA_NOK  # Initializing the result with data nok
            # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
            plot_titles, plots, remarks = fh.rep([], 3)

            signal_summary = {}  # Initializing the dictionary with data for final evaluation table

            signals = self.readers[ALIAS]
            signals[Signals.Columns.TIMESTAMP] = signals.index
            ABS_ACTIVE = 1

            time = signals[Signals.Columns.TIME]
            abs_state = signals[Signals.Columns.ABS_STATE]
            ap_states = signals[Signals.Columns.AP_STATES]
            core_state = signals[Signals.Columns.CORE_STATE]
            var_esm = signals[Signals.Columns.VAR_ESM]

            signals["status_ap_states"] = ap_states.apply(lambda x: fh.get_status_label(x, aup.AP_STATES))
            signals["status_core_state"] = core_state.apply(lambda x: fh.get_status_label(x, aup.CORE_STATUS))
            signals["status_var_esm"] = var_esm.apply(lambda x: fh.get_status_label(x, aup.ESM_STATE))
            signals["status_abs_state"] = abs_state.apply(lambda x: "ABS_ACTIVE" if x == 1 else "ABS_NOT_ACTIVE")

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_2 = find_time_threshold(abs_state, ABS_ACTIVE)
            if time_threshold_2 is not None:
                time_threshold_3 = time_threshold_2 + 50
            end_of_measurement = len(time) - 1

            if time_threshold_3 is not None:
                evaluation_1 = " ".join(
                    f"The evaluation is PASSED because <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_3], 3)}s</b> when the signal "
                    f"{Signals.Columns.ABS_STATE} is in ABS_ACTIVE (1) state: <br>"
                    f"- the signal {Signals.Columns.AP_STATES} == {signals['status_ap_states'].iloc[time_threshold_3 - 10]} ({ap_states.iloc[time_threshold_3 - 10]}) <br>"
                    f"- the signal {Signals.Columns.CORE_STATE} == {signals['status_core_state'].iloc[time_threshold_3 - 10]} ({core_state.iloc[time_threshold_3 - 10]}) <br>"
                    f"AND <b>after</b> that timestamp:<br>"
                    f"- the signal {Signals.Columns.AP_STATES} == {signals['status_ap_states'].iloc[time_threshold_3 + 10]} ({ap_states.iloc[time_threshold_3 + 10]}) <br>"
                    f"- the signal {Signals.Columns.VAR_ESM} == {signals['status_var_esm'].iloc[time_threshold_3 + 10]} ({var_esm.iloc[time_threshold_3 + 10]}) <br>"
                    f"- the signal {Signals.Columns.CORE_STATE} == {signals['status_core_state'].iloc[time_threshold_3 + 10]} ({core_state.iloc[time_threshold_3 + 10]}) <br><br>"
                    f"This confirms that AUPCore transitioned from Maneuvering to Terminate (Error or Pause-Finished) when the AUPCore received the<br>\
                        information  that an ABS intervention is active for longer than {aup.AP_G_ABS_TIME_THRESH_S} s.".split()
                )
                eval_cond_1 = True

                delay_neg_ap = ap_states.iloc[time_threshold_3 - 10] != aup.AP_STATES.AP_AVG_ACTIVE_IN
                delay_neg_core = core_state.iloc[time_threshold_3 - 10] != aup.CORE_STATUS.CORE_PARKING

                delay_pos_ap = ap_states.iloc[time_threshold_3 + 10] != aup.AP_STATES.AP_AVG_PAUSE
                delay_pos_var = var_esm.iloc[time_threshold_3 + 10] != aup.ESM_STATE.ESM_REVERSIBLE_ERROR
                delay_pos_core = core_state.iloc[time_threshold_3 + 10] != aup.CORE_STATUS.CORE_ERROR

                # Verify if the Pause state is present after Active state in the measurement
                time_active = find_time_threshold(ap_states, aup.AP_STATES.AP_AVG_ACTIVE_IN)
                ap_pause = (ap_states[time_active:] == aup.AP_STATES.AP_AVG_PAUSE).any()

                # If AP goes into PAUSE state, calculate how many times the transition from Pause to Finish is made
                if ap_pause:
                    # Take the time of APState == Pause after it was Active
                    time_pause = (
                        find_time_threshold(ap_states.iloc[time_active:], aup.AP_STATES.AP_AVG_PAUSE)
                    ) + time_active
                    ap_state_scenario = ap_states.iloc[time_pause:end_of_measurement]
                    mask_ap_finish = ap_state_scenario.rolling(2).apply(
                        lambda x: x[0] != aup.AP_STATES.AP_AVG_FINISHED and x[1] == aup.AP_STATES.AP_AVG_FINISHED,
                        raw=True,
                    )
                    total_ap_finish = mask_ap_finish.sum()

                    # Verify the transiton from Maneuvering to Pause and Finished
                    if (delay_pos_ap or total_ap_finish != 1) or (delay_neg_ap or delay_neg_core):
                        if delay_neg_ap or delay_neg_core:
                            evaluation_1 = " ".join(
                                f"The evaluation is FAILED because <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_3], 3)}s</b> when the signal"
                                f"{Signals.Columns.ABS_STATE} is in ABS_ACTIVE (1) state: <br>"
                                f"- the signal {Signals.Columns.AP_STATES} == {signals['status_ap_states'].iloc[time_threshold_3 - 10]} ({ap_states.iloc[time_threshold_3 - 10]}) <br>"
                                f"- the signal {Signals.Columns.CORE_STATE} == {signals['status_core_state'].iloc[time_threshold_3 - 10]} ({core_state.iloc[time_threshold_3 - 10]}) <br><br>"
                                f"This means that AUPCore wasn't in Maneuvering state when the AUPCore received  that an ABS intervention is active for longer than {aup.AP_G_ABS_TIME_THRESH_S} s.".split()
                            )
                        elif delay_pos_ap or total_ap_finish != 1:
                            evaluation_1 = " ".join(
                                f"The evaluation is FAILED because <b>after</b> the timestamp <b>{round(time.iloc[time_threshold_3], 3)}s</b> when the signal"
                                f"{Signals.Columns.ABS_STATE} is in ABS_ACTIVE (1) state: <br>"
                                f"- AUPCore didn't transition to Pause and then to Finished state when the AUPCore received the information  that an ABS intervention is active for longer than {aup.AP_G_ABS_TIME_THRESH_S} s.".split()
                            )
                        eval_cond_1 = False

                # Verify the transiton from Maneuvering to Error
                if (delay_neg_ap or delay_neg_core or delay_pos_var or delay_pos_core) and not ap_pause:
                    if delay_neg_ap or delay_neg_core:
                        evaluation_1 = " ".join(
                            f"The evaluation is FAILED because <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_3], 3)}s</b> when the signal"
                            f"{Signals.Columns.ABS_STATE} is in ABS_ACTIVE (1) state: <br>"
                            f"- the signal {Signals.Columns.AP_STATES} == {signals['status_ap_states'].iloc[time_threshold_3 - 10]} ({ap_states.iloc[time_threshold_3 - 10]}) <br>"
                            f"- the signal {Signals.Columns.CORE_STATE} == {signals['status_core_state'].iloc[time_threshold_3 - 10]} ({core_state.iloc[time_threshold_3 - 10]}) <br><br>"
                            f"This means that AUPCore wasn't in Maneuvering state when the AUPCore received the information  that an ABS intervention is active for longer than {aup.AP_G_ABS_TIME_THRESH_S} s.".split()
                        )
                    elif delay_pos_var or delay_pos_core:
                        evaluation_1 = " ".join(
                            f"The evaluation is FAILED because <b>after</b> the timestamp <b>{round(time.iloc[time_threshold_3], 3)}s</b> when the signal"
                            f"{Signals.Columns.ABS_STATE} is in ABS_ACTIVE (1) state: <br>"
                            f"- the signal {Signals.Columns.VAR_ESM} == {signals['status_var_esm'].iloc[time_threshold_3 + 10]} ({var_esm.iloc[time_threshold_3 + 10]}) <br>"
                            f"- the signal {Signals.Columns.CORE_STATE} == {signals['status_core_state'].iloc[time_threshold_3 + 10]} ({core_state.iloc[time_threshold_3 + 10]}) <br><br>"
                            f"This means that AUPCore didn't transition to Error state when the AUPCore received the information  that an ABS intervention is active for longer than {aup.AP_G_ABS_TIME_THRESH_S} s.".split()
                        )
                    eval_cond_1 = False

            else:
                self.result.measured_result = FALSE
                evaluation_1 = " ".join(
                    f"Evaluation not possible, the trigger value {Signals.Columns.ABS_STATE} == ABS_ACTIVE (1) was never found.".split()
                )

            if eval_cond_1:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict1 = "PASSED" if eval_cond_1 else "FAILED" if eval_cond_1 is False else "NOT ASSESSED"
            expected_val_1 = "delay -0.1s: <br>\
                    AP.planningCtrlPort.apStates == AP_AVG_ACTIVE_IN (3)<br>\
                    AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PARKING (2)<br>\
                    delay 0.1s: <br>\
                    (AP.planningCtrlPort.apStates == AP_AVG_PAUSE (5))<br>\
                    OR (AP.psmDebugPort.stateVarESM_nu == ESM_REVERSIBLE_ERROR (2)<br>\
                    AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_ERROR (5))<br>\
                    Case ApState == Pause:<br>\
                    Check if ApStates goes in Finish state after Pause stat<br>\
                    AP.planningCtrlPort.apStates == AP_AVG_FINISHED (5) once <br>"

            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T3"] = [expected_val_1, evaluation_1, verdict1]

            remark = html_remark
            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=abs_state,
                    mode="lines",
                    name=Signals.Columns.ABS_STATE,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_abs_state"],
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
                    y=var_esm,
                    mode="lines",
                    name=Signals.Columns.VAR_ESM,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_var_esm"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=core_state,
                    mode="lines",
                    name=Signals.Columns.CORE_STATE,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_core_state"],
                )
            )
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
                title=" Graphical Overview",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
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
    name="SWRT_CNC_AUP_ManeuveringState_Table_118_Req_2325960_2326036",
    description=(
        "This test case verifies that AUPCore shall transition from Maneuvering to Terminate (Error or Pause-Finished) if \
            the AUPCore receives the information  that an ABS intervention is active for longer than 0.5 s."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringState_Table_118_Req_2325960_2326036_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_ManeuveringState_Table_118_Req_2325960_2326036_TS
        ]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br>
                T1: start_of_measurement <br>
                T2:<em>SignalManipulation.escInformationPort_absState_nu </em> == ABS_ACTIVE (1) <br>
                T3: T2 +  AP_G_ABS_TIME_THRESH_S (0.5s)<br>

            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br>
                T3: <br>
                delay -0.1s: <br>
                    <em>AP.planningCtrlPort.apStates </em> == AP_AVG_ACTIVE_IN (3)<br>
                    <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_PARKING (2)<br>
                delay 0.1s: <br>
                    (<em>AP.planningCtrlPort.apStates</em> == AP_AVG_PAUSE (5) <br>
                    OR <em>AP.psmDebugPort.stateVarESM_nu</em> == ESM_REVERSIBLE_ERROR (2)<br>)
                    <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_ERROR (5)<br>
                Case ApState == Pause:<br>
                Check if ApStates goes in Finish state after Pause state<br>
                <em>AP.planningCtrlPort.apStates</em> == AP_AVG_FINISHED (5) once <br>
            </td>
        </tr>
    </table>

"""
