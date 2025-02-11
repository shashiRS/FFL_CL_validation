"""
T1:
start_of_measurement

T2:
SignalManipulation.escInformationPort_ebdState_nu = {EBD_ACTIVE} (1)

T3:
T2 + {AP_G_EBD_TIME_THRESH_S} (0.5s)

ET3:
delay -0.1s:
AP.planningCtrlPort.apStates == {AP_AVG_PAUSE} (5)
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PAUSE (3)

delay 0.1s:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == {CORE_ERROR} (5)
AP.psmDebugPort.stateVarESM_nu == {ESM_REVERSIBLE_ERROR} (2)
AP.psmDebugPort.stateVarPPC_nu == {PPC_REVERSIBLE_ERROR} (15)
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
ALIAS = "SWRT_CNC_AUP_ManeuveringState_Table_157_Req_2711728_2326037"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        EBD_STATE = "SignalManipulation.escInformationPort_ebdState_nu"
        CORE_STATE = "AP.PARKSMCoreStatusPort.parksmCoreState_nu"
        AP_STATES = "AP.planningCtrlPort.apStates"
        VAR_ESM = "AP.psmDebugPort.stateVarESM_nu"
        VAR_PPC = "AP.psmDebugPort.stateVarPPC_nu"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.TIME: [
                "Time",
            ],
            self.Columns.EBD_STATE: [
                "SignalManipulation.escInformationPort_ebdState_nu",
            ],
            self.Columns.CORE_STATE: [
                "AP.PARKSMCoreStatusPort.parksmCoreState_nu",
            ],
            self.Columns.AP_STATES: [
                "AP.planningCtrlPort.apStates",
            ],
            self.Columns.VAR_ESM: [
                "AP.psmDebugPort.stateVarESM_nu",
            ],
            self.Columns.VAR_PPC: [
                "AP.psmDebugPort.stateVarPPC_nu",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Maneuvering State Table 157 Req 2711728 2326037",
    description=(
        "This test case verifies that in case the Automated Parking Core is in Terminate state and it receives the information that a\
            reversible error is present (EBD intervention is active for longer than AP_G_EBD_TIME_THRESH_S (0.5s))\
                then it should transition to Error state."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringState_Table_157_Req_2711728_2326037_TS(TestStep):
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
            ebd_state = signals[Signals.Columns.EBD_STATE]
            core_state = signals[Signals.Columns.CORE_STATE]
            ap_states = signals[Signals.Columns.AP_STATES]
            var_esm = signals[Signals.Columns.VAR_ESM]
            var_ppc = signals[Signals.Columns.VAR_PPC]

            signals["status_ebd_state"] = ebd_state.apply(lambda x: fh.get_status_label(x, aup.EBD_STATE))
            signals["status_core_state"] = core_state.apply(lambda x: fh.get_status_label(x, aup.CORE_STATUS))
            signals["status_ap_states"] = ap_states.apply(lambda x: fh.get_status_label(x, aup.AP_STATES))
            signals["status_var_esm"] = var_esm.apply(lambda x: fh.get_status_label(x, aup.ESM_STATE))
            signals["status_var_ppc"] = var_ppc.apply(lambda x: fh.get_status_label(x, aup.PPC_STATE))

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_2 = find_time_threshold(ebd_state, aup.EBD_STATE.EBD_ACTIVE)
            time_threshold_3 = int(time_threshold_2 + aup.AP_G_EBD_TIME_THRESH_S * 100)

            if time_threshold_2 is not None:
                evaluation_1 = " ".join(
                    f"The trigger value {Signals.Columns.EBD_STATE} == EBD_ACTIVE (1) has been found.".split()
                )
                eval_cond_1 = True
            else:
                self.result.measured_result = FALSE
                evaluation_1 = " ".join(
                    f"Evaluation not possible, the trigger value {Signals.Columns.EBD_STATE} == EBD_ACTIVE (1) was never found.".split()
                )

            if time_threshold_3 is not None:
                evaluation_2 = " ".join(
                    f"The evaluation is PASSED because <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> given by the signal "
                    f"{Signals.Columns.EBD_STATE} == EBD_ACTIVE (1): <br>"
                    f"- the signal {Signals.Columns.AP_STATES} == {signals['status_ap_states'].iloc[time_threshold_2 - 10]} ({ap_states.iloc[time_threshold_2 - 10]}) <br>"
                    f"- the signal {Signals.Columns.CORE_STATE} == {signals['status_core_state'].iloc[time_threshold_2 - 10]} ({core_state.iloc[time_threshold_2 - 10]}) <br>"
                    f"AND <b>after</b> that timestamp:<br>"
                    f"- the signal {Signals.Columns.CORE_STATE} == {signals['status_core_state'].iloc[time_threshold_2 + 10]} ({core_state.iloc[time_threshold_2 + 10]}) <br>"
                    f"- the signal {Signals.Columns.VAR_ESM} == {signals['status_var_esm'].iloc[time_threshold_2 + 10]} ({var_esm.iloc[time_threshold_2 + 10]}) <br>"
                    f"- the signal {Signals.Columns.VAR_PPC} == {signals['status_var_ppc'].iloc[time_threshold_2 + 10]} ({var_ppc.iloc[time_threshold_2 + 10]}) <br><br>"
                    f"This confirms that the Automated Parking Core transitioned from Terminate to Error state when the reversible error was inserted.".split()
                )
                eval_cond_2 = True

                delay_neg_ap = ap_states.iloc[time_threshold_2 - 10] != aup.AP_STATES.AP_AVG_PAUSE
                delay_neg_core = core_state.iloc[time_threshold_2 - 10] != aup.CORE_STATUS.CORE_PAUSE

                delay_pos_core = core_state.iloc[time_threshold_2 + 10] != aup.CORE_STATUS.CORE_ERROR
                delay_pos_esm = var_esm.iloc[time_threshold_2 + 10] != aup.ESM_STATE.ESM_REVERSIBLE_ERROR
                delay_pos_ppc = var_ppc.iloc[time_threshold_2 + 10] != aup.PPC_STATE.PPC_REVERSIBLE_ERROR

                if delay_neg_ap or delay_neg_core:
                    evaluation_2 = " ".join(
                        f"The evaluation is FAILED because <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> given by the signal<br>"
                        f"{Signals.Columns.EBD_STATE} == EBD_ACTIVE (1): <br>"
                        f"- the signal {Signals.Columns.AP_STATES} == {signals['status_ap_states'].iloc[time_threshold_2 - 10]} ({ap_states.iloc[time_threshold_2 - 10]}) <br>"
                        f"- the signal {Signals.Columns.CORE_STATE} == {signals['status_core_state'].iloc[time_threshold_2 - 10]} ({core_state.iloc[time_threshold_2 - 10]}) <br><br>"
                        f"This means that the Automated Parking Core wasn't in Terminate state when the reversible error was inserted.".split()
                    )
                    eval_cond_2 = False
                elif delay_pos_core or delay_pos_esm or delay_pos_ppc:
                    evaluation_2 = " ".join(
                        f"The evaluation is FAILED because <b>after</b> the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> given by the signal<br>"
                        f"{Signals.Columns.EBD_STATE} == 0: <br>"
                        f"- the signal {Signals.Columns.CORE_STATE} == {signals['status_core_state'].iloc[time_threshold_2 + 10]} ({core_state.iloc[time_threshold_2 + 10]}) <br>"
                        f"- the signal {Signals.Columns.VAR_ESM} == {signals['status_var_esm'].iloc[time_threshold_2 + 10]} ({var_esm.iloc[time_threshold_2 + 10]}) <br>"
                        f"- the signal {Signals.Columns.VAR_PPC} == {signals['status_var_ppc'].iloc[time_threshold_2 + 10]} ({var_ppc.iloc[time_threshold_2 + 10]}) <br><br>"
                        f"This means that the Automated Parking Core didn't transition to Error state after the reversible error was inserted.".split()
                    )
                    eval_cond_2 = False
            else:
                self.result.measured_result = FALSE
                evaluation_2 = (
                    "Evaluation not possible, the trigger value T2 + AP_G_EBD_TIME_THRESH_S (0.5s) was never found."
                )

            if eval_cond_1 and eval_cond_2:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict1 = "PASSED" if eval_cond_1 else "FAILED" if eval_cond_1 is False else "NOT ASSESSED"
            verdict2 = "PASSED" if eval_cond_2 else "FAILED" if eval_cond_2 is False else "NOT ASSESSED"
            expected_val_1 = "SignalManipulation.escInformationPort_ebdState_nu == EBD_ACTIVE (1)"
            expected_val_2 = "delay -0.1:<br>\
                AP.planningCtrlPort.apStates == AP_AVG_PAUSE (5)\
                AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PAUSE (3)<br>\
                delay 0.1:<br>\
                AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_ERROR (5)<br>\
                AP.psmDebugPort.stateVarESM_nu == ESM_REVERSIBLE_ERROR (2)<br>\
                AP.psmDebugPort.stateVarPPC_nu == PPC_REVERSIBLE_ERROR (15)"

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
                    y=ebd_state,
                    mode="lines",
                    name=Signals.Columns.EBD_STATE,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_ebd_state"],
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
                    y=var_ppc,
                    mode="lines",
                    name=Signals.Columns.VAR_PPC,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_var_ppc"],
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
    name="SWRT_CNC_AUP_ManeuveringState_Table_157_Req_2711728_2326037",
    description=(
        "This test case verifies that in case the Automated Parking Core is in Terminate state and it receives the information that a\
            reversible error is present (EBD intervention is active for longer than AP_G_EBD_TIME_THRESH_S (0.5s))\
                then it should transition to Error state."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringState_Table_157_Req_2711728_2326037_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_ManeuveringState_Table_157_Req_2711728_2326037_TS
        ]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br>
                T1: start_of_measurement <br>
                T2: <br>
                    <em>SignalManipulation.escInformationPort_ebdState_nu</em> == EBD_ACTIVE (1)<br>
                T3:<br>
                    T2 + AP_G_EBD_TIME_THRESH_S (0.5s)<br><br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br>
                T3: <br>
                delay -0.1s: <br>
                    <em>AP.planningCtrlPort.apStates</em> == AP_AVG_PAUSE  (5)<br>
                    <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_PAUSE (3)<br>
                delay 0.1s: <br>
                    <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_ERROR (5)<br>
                    <em>AP.psmDebugPort.stateVarESM_nu</em> == ESM_REVERSIBLE_ERROR (2)<br>
                    <em>AP.psmDebugPort.stateVarPPC_nu</em> == PPC_REVERSIBLE_ERROR (15)<br>
            </td>
        </tr>
    </table>

"""
