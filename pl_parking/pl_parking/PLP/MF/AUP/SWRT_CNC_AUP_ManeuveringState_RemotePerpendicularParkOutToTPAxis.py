"""
T1:
AP.headUnitVisualizationPort.screen_nu == MANEUVER_FINISHED (5)

T2:
AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu == REM_TAP_ON_PARK_OUT (25)

T3:
AP.planningCtrlPort.apStates == AP_AVG_ACTIVE_OUT (4)

T4:
AP.planningCtrlPort.apStates == AP_AVG_PAUSE (5)

INT_ET3_ET4:
AP.planningCtrlPort.apPlanningSpecification == APPS_PARK_OUT_TO_TARGET_POSE (5)
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
ALIAS = "SWRT_CNC_AUP_ManeuveringState_RemotePerpendicularParkOutToTPAxis"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        SCREEN_NU = "AP.headUnitVisualizationPort.screen_nu"
        DEVICE_CM_QUANT = "AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu"
        AP_STATES = "AP.planningCtrlPort.apStates"
        PLANNING_SPECIFICATION = "AP.planningCtrlPort.apPlanningSpecification"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.TIME: [
                "Time",
            ],
            self.Columns.SCREEN_NU: [
                "AP.headUnitVisualizationPort.screen_nu",
            ],
            self.Columns.DEVICE_CM_QUANT: [
                "AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu",
            ],
            self.Columns.AP_STATES: [
                "AP.planningCtrlPort.apStates",
            ],
            self.Columns.PLANNING_SPECIFICATION: [
                "AP.planningCtrlPort.apPlanningSpecification",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Maneuvering State Remote Perpendicular ParkOut To TPAxis",
    description=(
        "This test case verifies that in case of Remote Parking out perpendicular the AutomatedParkingCore shall trigger that the path is followed until the target pose AXIS is reached."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringState_RemotePerpendicularParkOutToTPAxis_TS(TestStep):
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
            screen_nu = signals[Signals.Columns.SCREEN_NU]
            device_cm_quant = signals[Signals.Columns.DEVICE_CM_QUANT]
            ap_states = signals[Signals.Columns.AP_STATES]
            planning_spec = signals[Signals.Columns.PLANNING_SPECIFICATION]

            signals["status_screen"] = screen_nu.apply(lambda x: fh.get_status_label(x, aup.SCREEN_NU))
            signals["status_device"] = device_cm_quant.apply(lambda x: fh.get_status_label(x, aup.REMOTE_DEVICE))
            signals["status_ap_states"] = ap_states.apply(lambda x: fh.get_status_label(x, aup.AP_STATES))
            signals["status_planning_spec"] = planning_spec.apply(
                lambda x: fh.get_status_label(x, aup.PLANNING_SPECIFICATION)
            )

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_1 = find_time_threshold(screen_nu, aup.SCREEN_NU.MANEUVER_FINISHED)
            time_threshold_2 = find_time_threshold(device_cm_quant, aup.REMOTE_DEVICE.REM_TAP_ON_PARK_OUT)
            time_threshold_3 = (
                find_time_threshold(ap_states.iloc[time_threshold_2:], aup.AP_STATES.AP_AVG_ACTIVE_OUT)
                + time_threshold_2
            )
            time_threshold_4 = (
                find_time_threshold(ap_states.iloc[time_threshold_2:], aup.AP_STATES.AP_AVG_PAUSE) + time_threshold_2
            )

            if time_threshold_3 is not None and time_threshold_4 is not None:
                evaluation_1 = " ".join(
                    f"The evaluation is PASSED if between the interval given by the signal {Signals.Columns.AP_STATES} "
                    f"having the states AP_AVG_ACTIVE_OUT (4) and AP_AVG_PAUSE (5) ({round(time.iloc[time_threshold_3], 3)} - "
                    f"{round(time.iloc[time_threshold_4], 3)}), the signal {Signals.Columns.PLANNING_SPECIFICATION} reaches "
                    f"APPS_PARK_OUT_TO_TARGET_POSE (5) state, as expected. "
                    f"This confirms that the AUP core triggered that the path was followed until the target pose AXIS was reached.".split()
                )
                eval_cond_1 = True  # set the evaluation condition as TRUE
                plan_spec_interval = planning_spec.iloc[time_threshold_3:time_threshold_4]
                cond_negative = (plan_spec_interval != aup.PLANNING_SPECIFICATION.APPS_PARK_OUT_TO_TARGET_POSE).any()

                if cond_negative:
                    evaluation_1 = " ".join(
                        f"The evaluation FAILED if between the interval given by the signal {Signals.Columns.AP_STATES} "
                        f"having the states AP_AVG_ACTIVE_OUT (4) and AP_AVG_PAUSE (5) ({round(time.iloc[time_threshold_3], 3)} - "
                        f"{round(time.iloc[time_threshold_4], 3)}), the signal {Signals.Columns.PLANNING_SPECIFICATION} has a different value "
                        f"than APPS_PARK_OUT_TO_TARGET_POSE (5), which is unexpected.".split()
                    )
                    eval_cond_1 = False
            else:
                # create an evaluation text for the moment when the threshold isn't found, set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_1 = " ".join(
                    f"Evaluation not possible, the trigger values ({Signals.Columns.AP_STATES} == AP_AVG_ACTIVE_OUT (4) "
                    f"or {Signals.Columns.AP_STATES} == AP_AVG_PAUSE (5) were never found.".split()
                )

            if time_threshold_1 is not None:
                evaluation_2 = " ".join(
                    f"The signal {Signals.Columns.SCREEN_NU} reaches the MANEUVER_FINISHED (5) state at"
                    f" timestamp <b>{round(time.iloc[time_threshold_1], 3)} s </b>".split()
                )
                eval_cond_2 = True
            else:
                evaluation_2 = f"The signal {Signals.Columns.SCREEN_NU} does not reach the MANEUVER_FINISHED (5) state."
                eval_cond_2 = False

            if time_threshold_2 is not None:
                evaluation_3 = " ".join(
                    f"The signal {Signals.Columns.DEVICE_CM_QUANT} reachs the REM_TAP_ON_PARK_OUT (25) state at"
                    f" timestamp <b>{round(time.iloc[time_threshold_2], 3)} s </b>".split()
                )
                eval_cond_3 = True
            else:
                evaluation_3 = (
                    f"The signal {Signals.Columns.DEVICE_CM_QUANT} does not reach the REM_TAP_ON_PARK_OUT (25) state."
                )
                eval_cond_3 = False
                # set the verdict of the test step
            if eval_cond_1 and eval_cond_2 and eval_cond_3:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict1 = "PASSED" if eval_cond_1 else "FAILED" if eval_cond_1 is False else "NOT ASSESSED"
            verdict2 = "PASSED" if eval_cond_2 else "FAILED" if eval_cond_2 is False else "NOT ASSESSED"
            verdict3 = "PASSED" if eval_cond_3 else "FAILED" if eval_cond_3 is False else "NOT ASSESSED"
            expected_val_1 = "AP.headUnitVisualizationPort.screen_nu == MANEUVER_FINISHED (5)"
            expected_val_2 = "AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu == REM_TAP_ON_PARK_OUT (25)"
            expected_val_3 = "AP.planningCtrlPort.apPlanningSpecification == APPS_PARK_OUT_TO_TARGET_POSE (5)"

            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T1"] = [expected_val_1, evaluation_2, verdict2]
            signal_summary["T2"] = [expected_val_2, evaluation_3, verdict3]
            signal_summary["T3 - T4"] = [expected_val_3, evaluation_1, verdict1]

            remark = html_remark
            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=screen_nu,
                    mode="lines",
                    name=Signals.Columns.SCREEN_NU,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_screen"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=device_cm_quant,
                    mode="lines",
                    name=Signals.Columns.DEVICE_CM_QUANT,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_device"],
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
                    y=planning_spec,
                    mode="lines",
                    name=Signals.Columns.PLANNING_SPECIFICATION,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_planning_spec"],
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
            if time_threshold_4 is not None:
                fig.add_vline(
                    x=time.iat[time_threshold_4],
                    line_width=1,
                    line_dash="dash",
                    line_color="darkslategray",
                    annotation_text="T4",
                )
            if time_threshold_3 is not None and time_threshold_4 is not None:
                fig.add_vrect(
                    x0=time.iat[time_threshold_3],
                    x1=time.iat[time_threshold_4],
                    fillcolor="LimeGreen",
                    line_width=0,
                    opacity=0.3,
                    # annotation_text="T2-T4",
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
    name="SWRT_CNC_AUP_ManeuveringState_RemotePerpendicularParkOutToTPAxis",
    description=(
        "This test case verifies that in case of Remote Parking out perpendicular the AutomatedParkingCore shall trigger that the path is followed until the target pose AXIS is reached."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringState_RemotePerpendicularParkOutToTPAxis_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_ManeuveringState_RemotePerpendicularParkOutToTPAxis_TS
        ]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br><br>
                T1: <em>AP.headUnitVisualizationPort.screen_nu</em> == MANEUVER_FINISHED (5) <br>
                T2: <em>AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu</em> == REM_TAP_ON_PARK_OUT (25) <br>
                T3: <em>AP.planningCtrlPort.apStates</em> == AP_AVG_ACTIVE_OUT (4) <br>
                T4: <em>AP.planningCtrlPort.apStates</em> == AP_AVG_PAUSE (5) <br><br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br>
                T3-T4: <em>AP.planningCtrlPort.apPlanningSpecification</em> == APPS_PARK_OUT_TO_TARGET_POSE (5)<br>
            </td>
        </tr>
    </table>


"""
