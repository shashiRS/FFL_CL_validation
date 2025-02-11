"""
T1:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PARKING (2)

T2:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PAUSE (3)

T3:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_FINISH (4)

INT_ET1_ET2:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PARKING (2)
AP.planningCtrlPort.apStates == AP_AVG_ACTIVE_IN (3)

INT_ET2_ET3:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PAUSE (3)
AP.planningCtrlPort.apStates == AP_AVG_PAUSE (5)

ET3:
AP.planningCtrlPort.apStates == AP_AVG_FINISHED (8)
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
ALIAS = "SWRT_CNC_AUP_ManeuveringToTerminate_SlotShrinking"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        CORE_STATE = "AP.PARKSMCoreStatusPort.parksmCoreState_nu"
        AP_STATES = "AP.planningCtrlPort.apStates"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.TIME: [
                "Time",
            ],
            self.Columns.CORE_STATE: [
                "AP.PARKSMCoreStatusPort.parksmCoreState_nu",
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
    name="Maneuvering State To Terminate Success",
    description=(
        "This test case verifies that the AutomatedParkingCore shall transition from Maneuvering to Terminate if the system receives \
            information that there is reference vehicle movement detected in selected slot and slot is no longer available."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringToTerminate_SlotShrinking_TS(TestStep):
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
            time_threshold_3 = None

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
            core_state = signals[Signals.Columns.CORE_STATE]
            ap_states = signals[Signals.Columns.AP_STATES]

            signals["status_core_state"] = core_state.apply(lambda x: fh.get_status_label(x, aup.CORE_STATUS))
            signals["status_ap_states"] = ap_states.apply(lambda x: fh.get_status_label(x, aup.AP_STATES))

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            # Find the trigger time and make sure that they are in sequence T1 < T2 < T3
            time_threshold_1 = find_time_threshold(core_state, aup.CORE_STATUS.CORE_PARKING)

            # Check if state Pasue is present in erg after state Parking
            if time_threshold_1 is not None:
                time_threshold_2 = (
                    find_time_threshold(core_state[time_threshold_1:], aup.CORE_STATUS.CORE_PAUSE) + time_threshold_1
                )
                # Check if state Finish is present in erg after state Pause
                if time_threshold_2 is not None:
                    core_finish_check = (core_state.iloc[time_threshold_2:] == aup.CORE_STATUS.CORE_FINISH).any()
                    if core_finish_check:
                        time_threshold_3 = (
                            find_time_threshold(core_state[time_threshold_2:], aup.CORE_STATUS.CORE_FINISH)
                            + time_threshold_2
                        )
                    else:
                        self.result.measured_result = FALSE
                else:
                    self.result.measured_result = FALSE
            else:
                self.result.measured_result = FALSE

            if time_threshold_1 is not None and time_threshold_2 is not None:
                evaluation_1 = " ".join(
                    f"The evaluation is PASSED because between the interval <b>[{round(time.iloc[time_threshold_1], 3)},{round(time.iloc[time_threshold_2], 3)}) s</b> given by the signals "
                    f"{Signals.Columns.CORE_STATE} == CORE_PARKING (2) and {Signals.Columns.CORE_STATE} == CORE_PAUSE (3): <br>"
                    f"- the signal {Signals.Columns.CORE_STATE} == CORE_PARKING (2) <br>"
                    f"- the signal {Signals.Columns.AP_STATES} ==  AP_AVG_ACTIVE_IN (3) <br><br>"
                    f"This confirms that AUP transitioned to Maneuvering state when the automated parking maneuvering was selected and stayed <br>\
                        in this state until it received the information that the parking slot was no longer available.".split()
                )
                eval_cond_1 = True

                interval_core = core_state.iloc[time_threshold_1 : (time_threshold_2 - 1)]
                core_park = (interval_core != aup.CORE_STATUS.CORE_PARKING).any()

                interval_ap = ap_states.iloc[time_threshold_1 : (time_threshold_2 - 1)]
                ap_active = (interval_ap != aup.AP_STATES.AP_AVG_ACTIVE_IN).any()

                if core_park or ap_active:
                    evaluation_1 = " ".join(
                        f"The evaluation is FAILED because between the interval <b>[{round(time.iloc[time_threshold_1], 3)},{round(time.iloc[time_threshold_2], 3)}) s</b> given by the signals "
                        f"{Signals.Columns.CORE_STATE} == CORE_PARKING (2) and {Signals.Columns.CORE_STATE} == CORE_PAUSE (3): <br>"
                        f"- the signal {Signals.Columns.AP_STATES} != CORE_PARKING (2) <br>"
                        f"- the signal {Signals.Columns.CORE_STATE} != AP_AVG_ACTIVE_IN (3) <br><br>"
                        f"This means that the AUP didn't transition to Maneuvering state after the automated parking maneuvering was selected and/or AUP dind't <br>\
                            stayed in this state until it received the information that the parking slot was no longer available.".split()
                    )
                    eval_cond_1 = False
            elif time_threshold_1 is None:
                self.result.measured_result = FALSE
                evaluation_1 = " ".join(
                    f"Evaluation not possible, the trigger {Signals.Columns.CORE_STATE} == CORE_PARKING (2) was never found.".split()
                )
            elif time_threshold_2 is None:
                self.result.measured_result = FALSE
                evaluation_1 = " ".join(
                    f"Evaluation not possible, the trigger {Signals.Columns.CORE_STATE} == CORE_PAUSE (3) after CORE_PARKING (2) state was never found.".split()
                )

            if time_threshold_2 is not None and time_threshold_3 is not None:
                evaluation_2 = " ".join(
                    f"The evaluation is PASSED because between the interval <b>[{round(time.iloc[time_threshold_2], 3)},{round(time.iloc[time_threshold_3], 3)}) s</b> given by the signals "
                    f"{Signals.Columns.CORE_STATE} == CORE_PAUSE (3) and {Signals.Columns.CORE_STATE} == CORE_FINISH (4): <br>"
                    f"- the signal {Signals.Columns.CORE_STATE} == CORE_PAUSE (3) <br>"
                    f"- the signal {Signals.Columns.AP_STATES} ==  AP_AVG_PAUSE (5) <br><br>"
                    f"This confirms that AUP transitioned to Pause state after it received the information that the parking slot was no <br>\
                        longer available and AUP stayed in this state until it transitioned to Finished state.".split()
                )
                eval_cond_2 = True

                interval_core = core_state.iloc[time_threshold_2 : (time_threshold_3 - 1)]
                core_pause = (interval_core != aup.CORE_STATUS.CORE_PAUSE).any()

                interval_ap = ap_states.iloc[time_threshold_2 : (time_threshold_3 - 1)]
                ap_pause = (interval_ap != aup.AP_STATES.AP_AVG_PAUSE).any()

                if core_pause or ap_pause:
                    evaluation_2 = " ".join(
                        f"The evaluation is FAILED because between the interval <b>[{round(time.iloc[time_threshold_2], 3)},{round(time.iloc[time_threshold_3], 3)}) s</b> given by the signals "
                        f"{Signals.Columns.CORE_STATE} == CORE_PAUSE (3) and {Signals.Columns.CORE_STATE} == CORE_FINISH (4): <br>"
                        f"- the signal {Signals.Columns.AP_STATES} != CORE_PAUSE (3) <br>"
                        f"- the signal {Signals.Columns.CORE_STATE} != AP_AVG_PAUSE (5) <br><br>"
                        f"This means that the AUP didn't transition to Pause state after it received the information that the parking slot was no longer available or <br>\
                            AUP didn't remained in that state until it transitioned to Finished.".split()
                    )
                    eval_cond_2 = False
            elif time_threshold_2 is None:
                self.result.measured_result = FALSE
                evaluation_2 = " ".join(
                    f"Evaluation not possible, the trigger {Signals.Columns.CORE_STATE} == CORE_PAUSE (3) after CORE_PARKING (2) state was never found.".split()
                )
            elif time_threshold_3 is None:
                self.result.measured_result = FALSE
                evaluation_2 = " ".join(
                    f"Evaluation not possible, the trigger {Signals.Columns.CORE_STATE} == CORE_FINISH (4) after CORE_PAUSE (3) state was never found.".split()
                )

            if time_threshold_3 is not None:
                evaluation_3 = " ".join(
                    f"The evaluation is PASSED because at the timestamp <b>{round(time.iloc[time_threshold_3], 3)} s</b> given by the signal "
                    f"{Signals.Columns.CORE_STATE} == CORE_FINISH (4) <br>"
                    f"the signal {Signals.Columns.AP_STATES} ==  AP_AVG_FINISHED (8) <br><br>"
                    f"This confirms that AUP transitioned from Pause to Finished state after it received the information that the parking slot was no longer available.".split()
                )
                eval_cond_3 = True

                ap_finished = ap_states.iloc[time_threshold_3] != aup.AP_STATES.AP_AVG_FINISHED

                if ap_finished:
                    evaluation_3 = " ".join(
                        f"The evaluation is FAILED because at the timestamp <b>{round(time.iloc[time_threshold_3], 3)} s</b> given by the signal "
                        f"{Signals.Columns.CORE_STATE} == CORE_FINISH (4) <br>"
                        f"the signal {Signals.Columns.AP_STATES} !=  AP_AVG_FINISHED (8) <br><br>"
                        f"This means that AUP didn't transition from Pause to Finished state after it received the information that the parking slot was no longer available.".split()
                    )
            else:
                self.result.measured_result = FALSE
                evaluation_3 = " ".join(
                    f"Evaluation not possible, the trigger {Signals.Columns.CORE_STATE} == CORE_FINISH (4) after CORE_PAUSE (3) state was never found.".split()
                )

            if eval_cond_1 and eval_cond_2 and eval_cond_3:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict1 = "PASSED" if eval_cond_1 else "FAILED" if eval_cond_1 is False else "NOT ASSESSED"
            verdict2 = "PASSED" if eval_cond_2 else "FAILED" if eval_cond_2 is False else "NOT ASSESSED"
            verdict3 = "PASSED" if eval_cond_3 else "FAILED" if eval_cond_3 is False else "NOT ASSESSED"
            expected_val_1 = "AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PARKING (2)<br>\
                AP.planningCtrlPort.apStates == AP_AVG_ACTIVE_IN (3)"
            expected_val_2 = "AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PAUSE (3)<br>\
                AP.planningCtrlPort.apStates == AP_AVG_PAUSE (5)"
            expected_val_3 = "AP.planningCtrlPort.apStates == AP_AVG_FINISHED (8)"

            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T1-T2"] = [expected_val_1, evaluation_1, verdict1]
            signal_summary["T2-T3"] = [expected_val_2, evaluation_2, verdict2]
            signal_summary["T3"] = [expected_val_3, evaluation_3, verdict3]

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
            if time_threshold_3 is not None:
                fig.add_vline(
                    x=time.iat[time_threshold_3],
                    line_width=1,
                    line_dash="dash",
                    line_color="darkslategray",
                    annotation_text="T3",
                )
            if time_threshold_1 is not None and time_threshold_2 is not None:
                fig.add_vrect(
                    x0=time.iat[time_threshold_1],
                    x1=time.iat[time_threshold_2],
                    fillcolor="LimeGreen",
                    line_width=0,
                    opacity=0.3,
                    layer="below",
                )
            if time_threshold_2 is not None and time_threshold_3 is not None:
                fig.add_vrect(
                    x0=time.iat[time_threshold_2],
                    x1=time.iat[time_threshold_3],
                    fillcolor="LimeGreen",
                    line_width=0,
                    opacity=0.3,
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
    name="SWRT_CNC_AUP_ManeuveringToTerminate_SlotShrinking",
    description=(
        "This test case verifies that the AutomatedParkingCore shall transition from Maneuvering to Terminate if the system receives \
            information that there is reference vehicle movement detected in selected slot and slot is no longer available."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringToTerminate_SlotShrinking_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_ManeuveringToTerminate_SlotShrinking_TS
        ]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br>
                T1:<br>
                    <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_PARKING (2) <br>
                T2:<br>
                    <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_PAUSE (3) <br>
                T3:<br>
                    <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_FINISH (4) <br><br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br>
                T1-T2: <br>
                    <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_PAUSE (3)<br>
                    <em>AP.planningCtrlPort.apStates</em> == AP_AVG_ACTIVE_IN (3)<br>
                T2-T3: <br>
                    <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_PAUSE (3)<br>
                    <em>AP.planningCtrlPort.apStates</em> == AP_AVG_PAUSE (5)<br>
                T3: <br>
                    <em>AP.planningCtrlPort.apStates</em> == AP_AVG_FINISHED (8)<br>
            </td>
        </tr>
    </table>

"""
