"""
T1:
start_of_measurement

T2:
SignalManipulation.healthVector_leftCamBlockage = 1

T3:
SignalManipulation.additionalBCMStatusPort_ignitionOn_nu = 1

ET3:
delay -0.1s: // Engine is OFF
"AP.planningCtrlPort.apStates" == {AP_INACTIVE} (0)
"AP.psmDebugPort.stateVarPPC_nu" != {PPC_SCANNING_IN} (3)
delay 0.1s: // Engine is ON
"AP.planningCtrlPort.apStates" == {AP_INACTIVE} (0)
"AP.psmDebugPort.stateVarPPC_nu" != {PPC_SCANNING_IN} (3)
"AP.psmDebugPort.stateVarESM_nu" == {ESM_REVERSIBLE_ERROR} (2)
"AP.PARKSMCoreStatusPort.parksmCoreState_nu" == {CORE_ERROR } (5)
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
ALIAS = "SWRT_CNC_AUP_ManeuveringState_Table_76_Req_2325889_2325890_2326040"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        LEFT_CAM = "SignalManipulation.healthVector_leftCamBlockage"
        IGN_ON = "SignalManipulation.additionalBCMStatusPort_ignitionOn_nu"
        AP_STATES = "AP.planningCtrlPort.apStates"
        VAR_PPC = "AP.psmDebugPort.stateVarPPC_nu"
        VAR_ESM = "AP.psmDebugPort.stateVarESM_nu"
        CORE_STATE = "AP.PARKSMCoreStatusPort.parksmCoreState_nu"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.TIME: [
                "Time",
            ],
            self.Columns.LEFT_CAM: [
                "SignalManipulation.healthVector_leftCamBlockage",
            ],
            self.Columns.IGN_ON: [
                "SignalManipulation.additionalBCMStatusPort_ignitionOn_nu",
            ],
            self.Columns.AP_STATES: [
                "AP.planningCtrlPort.apStates",
            ],
            self.Columns.VAR_PPC: [
                "AP.psmDebugPort.stateVarPPC_nu",
            ],
            self.Columns.VAR_ESM: [
                "AP.psmDebugPort.stateVarESM_nu",
            ],
            self.Columns.CORE_STATE: [
                "AP.PARKSMCoreStatusPort.parksmCoreState_nu",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Maneuvering State Table 76 Req 2325889 2325890 2326040",
    description=(
        "This test case verifies that if AUPCore detected that the left camera is blocked (reversible error) \
            AUP will NOT transition from init state to scanning state when the ignition is turned on."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringState_Table_76_Req_2325889_2325890_2326040_TS(TestStep):
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
            left_cam = signals[Signals.Columns.LEFT_CAM]
            ign_on = signals[Signals.Columns.IGN_ON]
            ap_states = signals[Signals.Columns.AP_STATES]
            var_ppc = signals[Signals.Columns.VAR_PPC]
            var_esm = signals[Signals.Columns.VAR_ESM]
            core_state = signals[Signals.Columns.CORE_STATE]

            signals["status_ap_states"] = ap_states.apply(lambda x: fh.get_status_label(x, aup.AP_STATES))
            signals["status_var_ppc"] = var_ppc.apply(lambda x: fh.get_status_label(x, aup.PPC_STATE))
            signals["status_var_esm"] = var_esm.apply(lambda x: fh.get_status_label(x, aup.ESM_STATE))
            signals["status_core_state"] = core_state.apply(lambda x: fh.get_status_label(x, aup.CORE_STATUS))

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_2 = find_time_threshold(left_cam, 1)
            time_threshold_3 = find_time_threshold(ign_on, 1)

            if time_threshold_2 is not None:
                evaluation_1 = " ".join(
                    f"The evaluation is PASSED because the trigger value {Signals.Columns.LEFT_CAM} == 1 has been found at\
                        timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b>.<br>"
                    f"This confirms that the left camera is blocked.".split()
                )
                eval_cond_1 = True
            else:
                self.result.measured_result = FALSE
                evaluation_1 = " ".join(
                    f"Evaluation not possible, the trigger value {Signals.Columns.LEFT_CAM} == 1 was never found.".split()
                )

            if time_threshold_3 is not None:
                evaluation_2 = " ".join(
                    f"The evaluation is PASSED because <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_3], 3)}s</b> when the signal "
                    f"<b>{Signals.Columns.IGN_ON}</b> == 1: <br>"
                    f"- the signal {Signals.Columns.AP_STATES} == {signals['status_ap_states'].iloc[time_threshold_3 - 100]} ({ap_states.iloc[time_threshold_3 - 100]}) <br>"
                    f"- the signal {Signals.Columns.VAR_PPC} != {signals['status_var_ppc'].iloc[time_threshold_3 - 100]} ({var_ppc.iloc[time_threshold_3 - 100]}) <br>"
                    f"AND <b>after</b> that timestamp:<br>"
                    f"- the signal {Signals.Columns.AP_STATES} == {signals['status_ap_states'].iloc[time_threshold_3 + 100]} ({ap_states.iloc[time_threshold_3 + 100]}) <br>"
                    f"- the signal {Signals.Columns.VAR_PPC} == {signals['status_var_ppc'].iloc[time_threshold_3 + 100]} ({var_ppc.iloc[time_threshold_3 + 100]}) <br>"
                    f"- the signal {Signals.Columns.VAR_ESM} == {signals['status_var_esm'].iloc[time_threshold_3 + 100]} ({var_esm.iloc[time_threshold_3 + 100]}) <br>"
                    f"- the signal {Signals.Columns.CORE_STATE} == {signals['status_core_state'].iloc[time_threshold_3 + 100]} ({core_state.iloc[time_threshold_3 + 100]}) <br>"
                    f"This confirms that didn't AUP transitioned from init state to scanning state when the ignition was \
                        turned on and there was a reversible error present.".split()
                )
                eval_cond_2 = True  # set the evaluation condition as TRUE
                delay_neg_ap = ap_states.iloc[time_threshold_3 - 100] != aup.AP_STATES.AP_INACTIVE
                delay_neg_ppc = var_ppc.iloc[time_threshold_3 - 100] == aup.PPC_STATE.PPC_SCANNING_IN

                delay_pos_ap = ap_states.iloc[time_threshold_3 + 100] != aup.AP_STATES.AP_INACTIVE
                delay_pos_ppc = var_ppc.iloc[time_threshold_3 + 100] == aup.PPC_STATE.PPC_SCANNING_IN
                delay_pos_esm = var_esm.iloc[time_threshold_3 + 100] != aup.ESM_STATE.ESM_REVERSIBLE_ERROR
                delay_pos_core = core_state.iloc[time_threshold_3 + 100] != aup.CORE_STATUS.CORE_ERROR

                if delay_neg_ap or delay_neg_ppc or delay_pos_ap or delay_pos_ppc or delay_pos_esm or delay_pos_core:
                    reason = ""
                    if delay_neg_ap:
                        reason = " because <b>before</b> turning the ignition on, AUP wasn't in init state"
                    elif delay_neg_ppc:
                        reason = (
                            " because <b>before</b> turning the ignition on, PPC (appdemo_parksm) was in scanning state"
                        )
                    elif delay_pos_ap or delay_pos_ppc:
                        reason = " because <b>after</b> turning the ignition on, AUP didn't remain in init state and it transitioned to scanning state"
                    elif delay_pos_esm or delay_pos_core:
                        reason = " because <b>after</b> turning the ignition on, AUPCore didn't detect and/or didn't transition to error"
                    evaluation_2 = " ".join(
                        f"This evaluation is FAILED{reason}. <br>Evaluated signals have the following values/states:<br>"
                        f"<b>Before</b> the timestamp <b>{round(time.iloc[time_threshold_3], 3)}s</b> when {Signals.Columns.IGN_ON} == 1:<br>"
                        f"- the signal {Signals.Columns.AP_STATES} == {signals['status_ap_states'].iloc[time_threshold_3 - 100]} ({ap_states.iloc[time_threshold_3 - 100]}) <br>"
                        f"- the signal {Signals.Columns.VAR_PPC} == {signals['status_var_ppc'].iloc[time_threshold_3 - 100]} ({var_ppc.iloc[time_threshold_3 - 100]}) <br>"
                        f"<b>After</b> the timestamp <b>{round(time.iloc[time_threshold_3], 3)}s</b> when {Signals.Columns.IGN_ON} == 1:<br>"
                        f"- the signal {Signals.Columns.AP_STATES} == {signals['status_ap_states'].iloc[time_threshold_3 + 100]} ({ap_states.iloc[time_threshold_3 + 100]}) <br>"
                        f"- the signal {Signals.Columns.VAR_PPC} == {signals['status_var_ppc'].iloc[time_threshold_3 + 100]} ({var_ppc.iloc[time_threshold_3 + 100]}) <br>"
                        f"- the signal {Signals.Columns.VAR_ESM} == {signals['status_var_esm'].iloc[time_threshold_3 + 100]} ({var_esm.iloc[time_threshold_3 + 100]}) <br>"
                        f"- the signal {Signals.Columns.CORE_STATE} == {signals['status_core_state'].iloc[time_threshold_3 + 100]} ({core_state.iloc[time_threshold_3 + 100]}) <br>".split()
                    )
                    eval_cond_2 = False
            else:
                # create an evaluation text for the moment when the threshold isn't found, set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_2 = " ".join(
                    f"Evaluation not possible, the trigger value {Signals.Columns.IGN_ON} == 1 was never found.".split()
                )

            if eval_cond_1 and eval_cond_2:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict1 = "PASSED" if eval_cond_1 else "FAILED" if eval_cond_1 is False else "NOT ASSESSED"
            verdict2 = "PASSED" if eval_cond_2 else "FAILED" if eval_cond_2 is False else "NOT ASSESSED"
            expected_val_1 = "SignalManipulation.healthVector_leftCamBlockage = 1"
            expected_val_2 = """delay -0.1s:<br>\
                AP.planningCtrlPort.apStates == AP_INACTIVE (0)<br>\
                AP.psmDebugPort.stateVarPPC_nu != PPC_SCANNING_IN (3)<br>\
                delay 0.1s:<br>\
                AP.planningCtrlPort.apStates == AP_INACTIVE (0)<br>\
                AP.psmDebugPort.stateVarPPC_nu != PPC_SCANNING_IN (3)<br>\
                AP.psmDebugPort.stateVarESM_nu == ESM_REVERSIBLE_ERROR (2)<br>\
                AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_ERROR (5)"""

            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T2"] = [expected_val_1, evaluation_1, verdict1]
            signal_summary["T3"] = [expected_val_2, evaluation_2, verdict2]

            remark = html_remark
            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=left_cam,
                    mode="lines",
                    name=Signals.Columns.LEFT_CAM,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
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
                    y=var_ppc,
                    mode="lines",
                    name=Signals.Columns.VAR_PPC,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_var_ppc"],
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
    name="SWRT_CNC_AUP_ManeuveringState_Table_76_Req_2325889_2325890_2326040",
    description=(
        "This test case verifies that if AUPCore detected that the left camera is blocked (reversible error) \
            AUP will NOT transition from init state to scanning state when the ignition is turned on."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringState_Table_76_Req_2325889_2325890_2326040_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_ManeuveringState_Table_76_Req_2325889_2325890_2326040_TS
        ]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br>
                T1: start_of_measurement <br>
                T2: <br>
                    <em>SignalManipulation.healthVector_leftCamBlockage</em> == 1 <br>
                T3: <br>
                    <em>SignalManipulation.additionalBCMStatusPort_ignitionOn_nu</em> == 1 <br><br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br>
                T3: <br>
                delay -0.1s: // Engine is OFF<br>
                    <em>AP.planningCtrlPort.apStates</em> == AP_INACTIVE (0)<br>
                    <em>AP.psmDebugPort.stateVarPPC_nu</em> != PPC_SCANNING_IN (3)<br>
                delay 0.1s: // Engine is ON <br>
                    <em>AP.planningCtrlPort.apStates</em> == AP_INACTIVE (0)<br>
                    <em>AP.psmDebugPort.stateVarPPC_nu</em> != PPC_SCANNING_IN (3)<br>
                    <em>AP.psmDebugPort.stateVarESM_nu</em> == ESM_REVERSIBLE_ERROR (2)<br>
                    <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_ERROR (5)
            </td>
        </tr>
    </table>

"""
