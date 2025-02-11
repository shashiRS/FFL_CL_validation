"""
T1:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_SCANNING (1)

T2:
AP.hmiOutputPort.userActionHeadUnit_nu == TAP_ON_START_PARKING (18)

T3:
AP.hmiOutputPort.userActionHeadUnit_nu == NO_USER_ACTION (0)

ET2:
delay -0.01s: AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_SCANNING (1)

ET3:
delay 0.1s: AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PARKING (2)
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
ALIAS = "SWRT_CNC_AUP_ScanningToManeuvering_DriverConfirmation"


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
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Scanning To Maneuvering Driver Confirmation",
    description=(
        "This test case verifies that the AutomatedParkingCore shall not transition from Scanning to Maneuvering before the driver has confirmed the maneuver."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ScanningToManeuvering_DriverConfirmation_TS(TestStep):
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
            act_head_unit = signals[Signals.Columns.ACT_HEAD_UNIT]

            signals["status_user"] = act_head_unit.apply(lambda x: fh.get_status_label(x, aup.USER_ACTION))
            signals["status_core"] = core_state.apply(lambda x: fh.get_status_label(x, aup.CORE_STATUS))

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_1 = find_time_threshold(core_state, aup.CORE_STATUS.CORE_SCANNING)
            time_threshold_2 = find_time_threshold(act_head_unit, aup.USER_ACTION.TAP_ON_START_PARKING)
            time_threshold_3 = (
                find_time_threshold(act_head_unit.iloc[time_threshold_2:], aup.USER_ACTION.NO_USER_ACTION)
                + time_threshold_2
            )

            if time_threshold_1 is not None:
                evaluation_1 = " ".join(
                    f"The signal {Signals.Columns.CORE_STATE} reach the CORE_SCANNING (1) state at"
                    f" timestamp <b>{round(time.iloc[time_threshold_1 + 10], 3)} s </b>".split()
                )
                eval_t1 = True
            else:
                evaluation_1 = f"The signal {Signals.Columns.CORE_STATE} does not reach the CORE_SCANNING (1) state."
                eval_t1 = False

            if time_threshold_2 is not None:
                evaluation_2 = " ".join(
                    f"The evaluation is PASSED at the moment when {Signals.Columns.ACT_HEAD_UNIT} == TAP_ON_START_PARKING"
                    f"({constants.AUPConstants.TAP_ON_START_PARKING}) (<b>{round(time.iloc[time_threshold_2], 3)} s</b>) with the expected value. <br>"
                    f"This indicates that the AUP core remained in scanning mode until the user confirmed the parking. <br>".split()
                )
                eval_cond_2 = True  # set the evaluation condition as TRUE
                delay_negative = core_state.iloc[time_threshold_2 - 1] != constants.AUPConstants.CORE_SCANNING

                if delay_negative:
                    evaluation_2 = " ".join(
                        f"The evaluation FAILED at the moment when {Signals.Columns.ACT_HEAD_UNIT} == TAP_ON_START_PARKING"
                        f"({constants.AUPConstants.TAP_ON_START_PARKING}) (<b>{round(time.iloc[time_threshold_2], 3)} s</b>), "
                        f"because the signal {Signals.Columns.CORE_STATE} was in the following state before the user confirmed the parking "
                        f"at {round(time.iloc[time_threshold_2 - 1], 3)} s: {signals['status_core'].iloc[time_threshold_2 - 1]} ({core_state.iloc[time_threshold_2 - 1]}). <br>".split()
                    )
                    eval_cond_2 = False

            if time_threshold_3 is not None:
                evaluation_3 = " ".join(
                    f"The evaluation is PASSED at the moment when {Signals.Columns.ACT_HEAD_UNIT} == NO_USER_ACTION"
                    f"({constants.AUPConstants.NO_USER_ACTION}) (<b>{round(time.iloc[time_threshold_3], 3)} s</b>) with the expected value. <br>"
                    f"This indicates that the AUP core begins the maneuver only after the user confirms the parking. <br>".split()
                )
                eval_cond_3 = True  # set the evaluation condition as TRUE
                delay_posistive = core_state.iloc[time_threshold_3 + 10] != constants.AUPConstants.CORE_PARKING

                if delay_negative or delay_posistive:
                    evaluation_3 = " ".join(
                        f"The evaluation FAILED at the moment when {Signals.Columns.ACT_HEAD_UNIT} == NO_USER_ACTION"
                        f"({constants.AUPConstants.NO_USER_ACTION}) (<b>{round(time.iloc[time_threshold_3], 3)} s</b>), "
                        f"because the signal {Signals.Columns.CORE_STATE} was in the following state after the user confirmed the parking "
                        f"at {round(time.iloc[time_threshold_3 + 10], 3)} s: {signals['status_core'].iloc[time_threshold_3 + 10]} ({core_state.iloc[time_threshold_3 + 10]}). <br>".split()
                    )
                    eval_cond_3 = False

                # set the verdict of the test step
                if eval_cond_2 and eval_t1 and eval_cond_3:
                    self.result.measured_result = TRUE
                else:
                    self.result.measured_result = FALSE
            else:
                # create an evaluation text for the moment when the threshold it's not found,set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_3 = " ".join(
                    f"Evaluation not possible, the trigger value ({Signals.Columns.ACT_HEAD_UNIT} == TAP_ON_START_PARKING (18)) was never found.".split()
                )
            verdict1 = "PASSED" if eval_t1 else "FAILED" if eval_t1 is False else "NOT ASSESSED"
            verdict2 = "PASSED" if eval_cond_2 else "FAILED" if eval_cond_2 is False else "NOT ASSESSED"
            verdict3 = "PASSED" if eval_cond_3 else "FAILED" if eval_cond_3 is False else "NOT ASSESSED"
            expected_val_1 = "AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_SCANNING (1)"
            expected_val_2 = "delay -0.01s: AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_SCANNING (1)"
            expected_val_3 = "delay 0.1s: AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PARKING (2)"
            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T1"] = [expected_val_1, evaluation_1, verdict1]
            signal_summary["T2"] = [expected_val_2, evaluation_2, verdict2]
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
                    text=signals["status_core"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=act_head_unit,
                    mode="lines",
                    name=Signals.Columns.ACT_HEAD_UNIT,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_user"],
                )
            )
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
                title="Graphical Overview",
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
    name="SWRT_CNC_AUP_ScanningToManeuvering_DriverConfirmation",
    description=(
        "This test case verifies that the AutomatedParkingCore shall not transition from Scanning to Maneuvering before the driver has confirmed the maneuver."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ScanningToManeuvering_DriverConfirmation_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_ScanningToManeuvering_DriverConfirmation_TS
        ]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br><br>
                T1: <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> = CORE_SCANNING (1) <br>
                T2: <em>AP.hmiOutputPort.userActionHeadUnit_nu</em> = TAP_ON_START_PARKING (18) <br>
                T3: <em>AP.hmiOutputPort.userActionHeadUnit_nu</em> = NO_USER_ACTION (0) <br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br><br>
                - ET2: <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_SCANNING (1) occurs just before T2 <br>
                - ET3: <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_PARKING (2) occurs just after T3<br>
            </td>
        </tr>
    </table>


"""
