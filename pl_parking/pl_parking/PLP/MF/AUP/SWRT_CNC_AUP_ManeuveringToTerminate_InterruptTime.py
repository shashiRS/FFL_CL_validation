"""
T1:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PARKING (2)

T2:
AP.doorStatusPort.status.driver_nu == 1

T3:
T2 + {AP_G_MAX_INTERRUPT_TIME_S} s

ET2:
delay 0.01s: AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PAUSE (3)

ET3:
delay 0.01s: AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_FINISH (4)

unde: {AP_G_MAX_INTERRUPT_TIME_S} = 60s
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
ALIAS = "SWRT_CNC_AUP_ManeuveringToTerminate_InterruptTime"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        CORE_STATE = "AP.PARKSMCoreStatusPort.parksmCoreState_nu"
        STATUS_BELT = "AP.vehicleOccupancyStatusPort.beltBuckleStatus.driver_nu"
        ACT_HEAD_UNIT = "AP.hmiOutputPort.userActionHeadUnit_nu"
        VELOCITY = "Car.v"
        DM_BRAKE = "DM.Brake"
        DOOR_DRIVER = "AP.doorStatusPort.status.driver_nu"

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
            self.Columns.ACT_HEAD_UNIT: [
                "AP.hmiOutputPort.userActionHeadUnit_nu",
            ],
            self.Columns.STATUS_BELT: [
                "AP.vehicleOccupancyStatusPort.beltBuckleStatus.driver_nu",
            ],
            self.Columns.VELOCITY: [
                "Car.v",
            ],
            self.Columns.DM_BRAKE: [
                "DM.Brake",
            ],
            self.Columns.DOOR_DRIVER: [
                "AP.doorStatusPort.status.driver_nu",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Maneuvering To Terminate Interrupt Time",
    description=(
        f"This test case verifies that the AutomatedParkingCore shall transition from Maneuvering to Terminate if the maneuver is interrupted for longer than {aup.AP_G_MAX_INTERRUPT_TIME_S} s (tunable)."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringToTerminate_InterruptTime_TS(TestStep):
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
            eval_t1 = False
            eval_t2 = False
            eval_t3 = False
            evaluation_1 = None
            evaluation_2 = None
            evaluation_3 = None
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
            door_status = signals[Signals.Columns.DOOR_DRIVER]
            signals["status_door"] = door_status.apply(lambda x: fh.get_status_label(x, aup.DOOR_DRIVER))
            signals["status_core"] = core_state.apply(lambda x: fh.get_status_label(x, aup.CORE_STATUS))

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_1 = find_time_threshold(core_state, aup.CORE_STATUS.CORE_PARKING)
            time_threshold_2 = find_time_threshold(door_status, aup.DOOR_DRIVER.DOOR_STATUS_OPEN)

            # Calculate T3 (T2 + INTERRUPT_TIME_S)
            if time_threshold_2 is not None:
                if time_threshold_2 + 6000 < len(time) + 11:
                    time_threshold_3 = time_threshold_2 + 6000  # 6000 is the number of samples in 60s
                else:
                    time_threshold_3 = len(time) - 11

            meas_long = True if len(time) > 6110 else False

            # Evaluation Texts
            if time_threshold_1 is not None:
                evaluation_1 = " ".join(
                    f"The signal {Signals.Columns.CORE_STATE} reach the CORE_PARKING (2) state at"
                    f" timestamp <b>{round(time.iloc[time_threshold_1 + 10], 3)} s </b>".split()
                )
                eval_t1 = True
            else:
                evaluation_1 = f"The signal {Signals.Columns.CORE_STATE} does not reach the CORE_PARKING (2) state."
                eval_t1 = False

            if time_threshold_2 is not None:
                evaluation_2 = " ".join(
                    f"The evaluation is PASSED when {Signals.Columns.DOOR_DRIVER} reaches the DOOR_STATUS_OPEN (1) state at "
                    f"timestamp <b>{round(time.iloc[time_threshold_2], 3)} s</b>, as expected. "
                    f"This indicates that the parking is paused when the driver’s door is opened.".split()
                )
                eval_t2 = True
                delay_positive = core_state.iloc[time_threshold_2 + 1] != aup.CORE_STATUS.CORE_PAUSE
                if delay_positive:
                    evaluation_2 = " ".join(
                        f"The evaluation FAILED when {Signals.Columns.DOOR_DRIVER} reaches the DOOR_STATUS_OPEN (1) state at "
                        f"timestamp <b>{round(time.iloc[time_threshold_2], 3)} s</b>. <br>"
                        f"At this point, the signal {Signals.Columns.CORE_STATE} is in state {signals['status_core'].iloc[time_threshold_2 + 1]} "
                        f"({core_state.iloc[time_threshold_2 + 1]}), but it should have been in CORE_PAUSE ({aup.CORE_STATUS.CORE_PAUSE}) state.".split()
                    )
                    eval_t2 = False
            else:
                evaluation_2 = (
                    f"The signal {Signals.Columns.DOOR_DRIVER} does not reach the DOOR_STATUS_OPEN (1) state."
                )
                eval_t2 = False

            if time_threshold_3 is not None and meas_long:
                evaluation_3 = " ".join(
                    f"The evaluation is PASSED when {aup.AP_G_MAX_INTERRUPT_TIME_S} seconds pass from the moment when "
                    f"{Signals.Columns.DOOR_DRIVER} reaches the DOOR_STATUS_OPEN (1) state at "
                    f"timestamp <b>{round(time.iloc[time_threshold_3], 3)} s</b>, as expected. "
                    f"This indicates that the parking is terminated when the maneuver is interrupted for longer than {aup.AP_G_MAX_INTERRUPT_TIME_S} seconds.".split()
                )
                eval_t3 = True
                delay_positive = core_state.iloc[time_threshold_3 + 1] != aup.CORE_STATUS.CORE_FINISH
                if delay_positive:
                    evaluation_3 = " ".join(
                        f"The evaluation FAILED when {aup.AP_G_MAX_INTERRUPT_TIME_S} seconds pass from the moment when "
                        f"{Signals.Columns.DOOR_DRIVER} reaches the DOOR_STATUS_OPEN (1) state at "
                        f"timestamp <b>{round(time.iloc[time_threshold_3], 3)} s</b>. <br>"
                        f"At this point, the signal {Signals.Columns.CORE_STATE} is in state {signals['status_core'].iloc[time_threshold_3 + 1]} "
                        f"({core_state.iloc[time_threshold_3 + 1]}), but it should have transitioned to CORE_FINISH({aup.CORE_STATUS.CORE_FINISH}).".split()
                    )
                    eval_t3 = False
            elif time_threshold_3 is not None:
                evaluation_3 = " ".join(
                    f"The evaluation FAILED at the end of measurement because the time was not long enough to reach "
                    f"{aup.AP_G_MAX_INTERRUPT_TIME_S} seconds from when {Signals.Columns.DOOR_DRIVER} reached the DOOR_STATUS_OPEN (1) state at "
                    f"timestamp <b>{round(time.iloc[time_threshold_3], 3)} s</b>, despite the expected value being reached.".split()
                )
                eval_t3 = False
                delay_positive = core_state.iloc[time_threshold_3 + 1] != aup.CORE_STATUS.CORE_FINISH
                if delay_positive:
                    evaluation_3 = " ".join(
                        f"The evaluation FAILED at the end of measurement because the time was not long enough to reach "
                        f"{aup.AP_G_MAX_INTERRUPT_TIME_S} seconds from when {Signals.Columns.DOOR_DRIVER} reached the DOOR_STATUS_OPEN (1) state at "
                        f"timestamp <b>{round(time.iloc[time_threshold_3], 3)} s</b>. <br>"
                        f"At the end of measurement, the signal {Signals.Columns.CORE_STATE} is in state {signals['status_core'].iloc[time_threshold_3 + 1]} "
                        f"({core_state.iloc[time_threshold_3 + 1]}), but it should have transitioned to CORE_FINISH({aup.CORE_STATUS.CORE_FINISH}).".split()
                    )
            else:
                evaluation_3 = (
                    f"The signal {Signals.Columns.DOOR_DRIVER} does not reach the DOOR_STATUS_OPEN (1) state."
                )
                eval_t3 = False
            if eval_t2 and eval_t3 and eval_t1:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE
            # "This test case verifies that the AutomatedParkingCore shall transition from Maneuvering to Terminate if the maneuver is interrupted for longer than {AP_G_MAX_INTERRUPT_TIME_S} s (tunable)."
            # Final Verdicts
            verdict1 = "PASSED" if eval_t1 else "FAILED"
            verdict2 = "PASSED" if eval_t2 else "FAILED"
            verdict3 = "PASSED" if eval_t3 else "FAILED"
            expected_val_1 = "AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PARKING (2)"
            expected_val_2 = "delay 0.01s: AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PAUSE (3)"
            expected_val_3 = "delay 0.01s: AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_FINISH (4)"
            # Signal Summary
            signal_summary = {
                "T1": [expected_val_1, evaluation_1, verdict1],
                "T2": [expected_val_2, evaluation_2, verdict2],
                "T3": [expected_val_3, evaluation_3, verdict3],
            }

            remark = html_remark

            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            # Plot
            fig = go.Figure()
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
                    y=door_status,
                    mode="lines",
                    name=Signals.Columns.DOOR_DRIVER,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_door"],
                )
            )
            fig.layout = go.Layout(
                xaxis_title="Time [s]",
                title="Graphical Overview",
                yaxis=dict(tickformat="14"),
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
            plots.append(fig)

        except Exception as e:
            _log.error(f"Error processing signals: {e}")
            self.result.measured_result = DATA_NOK
            self.sig_sum = f"<p>Error processing signals: {e}</p>"
            plots.append(self.sig_sum)

        # Add the plots in HTML
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)


# Define the test case definition. This will include the name of the test case and a description of the test.
@testcase_definition(
    name="SWRT_CNC_AUP_ManeuveringToTerminate_InterruptTime",
    description=(
        "This test case verifies that the AutomatedParkingCore shall transition from Maneuvering to Terminate if the maneuver is interrupted for longer than {AP_G_MAX_INTERRUPT_TIME_S} s (tunable)."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringToTerminate_InterruptTime_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_ManeuveringToTerminate_InterruptTime_TS
        ]  # in this list all the needed test steps are included


html_remark = f"""

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br><br>
                T1: <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> = CORE_PARKING (2) <br>
                T2: <em>AP.doorStatusPort.status.driver_nu</em> = DOOR_STATUS_OPEN (1) <br>
                T3: T2 + {aup.AP_G_MAX_INTERRUPT_TIME_S} s<br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br><br>
                - T2: <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> != CORE_PAUSE (3) occurs just after T2<br>
                - T3: <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> != CORE_FINISH (4) occurs just after T3<br>
            </td>
        </tr>
    </table>

"""
