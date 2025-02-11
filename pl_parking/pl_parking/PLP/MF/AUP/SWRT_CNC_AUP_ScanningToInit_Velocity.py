"""
T1:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_SCANNING (1)

T2:
Car.v > AP_G_V_SCANNING_THRESH_OFF_MPS

INT_ET1_ET2:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_SCANNING (1)

ET2:
delay 0.1s: AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_INIT (0)

AP_G_V_SCANNING_THRESH_OFF_MPS = 11.250 m/s

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
ALIAS = "SWRT_CNC_AUP_ScanningToInit_Velocity"


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
    name="Scanning To Init Velocity",
    description=(
        f"This test case verifies that the AutomatedParkingCore shall transition from Scanning to Init when a vehicle ego vehicle is driving forward with a velocity above {aup.AP_G_V_SCANNING_THRESH_OFF_MPS} m/s."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ScanningToInit_Velocity_TS(TestStep):
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
        self.test_result = fc.INPUT_MISSING  # Result
        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        try:
            time_threshold_1 = None
            time_threshold_2 = None
            eval_cond_1 = False
            eval_cond_2 = False
            evaluation_1 = ""
            evaluation_2 = ""
            # signal_name = signals_obj._properties
            # Make a constant with the reader for signals:

            # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
            plot_titles, plots, remarks = fh.rep([], 3)

            signal_summary = {}  # Initializing the dictionary with data for final evaluation table

            signals = self.readers[ALIAS]
            signals[Signals.Columns.TIMESTAMP] = signals.index

            time = signals[Signals.Columns.TIME]
            core_state = signals[Signals.Columns.CORE_STATE]
            velocity = signals[Signals.Columns.VELOCITY]

            signals["status_core"] = core_state.apply(lambda x: fh.get_status_label(x, aup.CORE_STATUS))
            signals["status_velocity"] = velocity.apply(
                lambda x: "Above Threshold" if x > aup.AP_G_V_SCANNING_THRESH_OFF_MPS else "Below Threshold"
            )

            # def find_time_threshold(signal, state):
            #     trigger = signal == state
            #     if np.any(trigger):
            #         return np.argmax(trigger)
            #     return None
            t1_mask_core = core_state == aup.CORE_STATUS.CORE_SCANNING
            t1_mask_velocity = velocity > 0.1 # 0.1 m/s meaning the car started moving
            if np.any(t1_mask_core) and np.any(t1_mask_velocity):
                time_threshold_1 = np.argmax(t1_mask_core & t1_mask_velocity)
            # time_threshold_1 = find_time_threshold(core_state, aup.CORE_STATUS.CORE_SCANNING)
            velocity_mask = velocity > aup.AP_G_V_SCANNING_THRESH_OFF_MPS
            if np.any(velocity_mask):
                time_threshold_2 = np.argmax(velocity_mask)

            if time_threshold_1 is not None and time_threshold_2 is not None:
                evaluation_1 = " ".join(
                    f"The evaluation is PASSED for the interval between the start of Scanning<b>{round(time.iloc[time_threshold_1], 3)} s</b> and when {Signals.Columns.VELOCITY} "
                    f"reaches a value above  {aup.AP_G_V_SCANNING_THRESH_OFF_MPS} m/s at timestamp <b>{round(time.iloc[time_threshold_2], 3)} s</b>. "
                    f"This confirms that the vehicle remained in Scanning while velocity was below the speed threshold.".split()
                )
                eval_cond_1 = True  # set the evaluation condition as TRUE
                core_state_interval_1 = core_state.iloc[time_threshold_1:time_threshold_2]
                cond_negative = (core_state_interval_1 != aup.CORE_STATUS.CORE_SCANNING).any()

                if cond_negative:
                    evaluation_1 = " ".join(
                        f"The evaluation is FAILED  for the interval between the start of Scanning<b>{round(time.iloc[time_threshold_1], 3)} s</b> and when {Signals.Columns.VELOCITY} "
                        f"reaches a value above  {aup.AP_G_V_SCANNING_THRESH_OFF_MPS} m/s at timestamp <b>{round(time.iloc[time_threshold_2], 3)} s</b>. "
                        f"This shows that the vehicle did not remained in Scanning while velocity was below the speed threshold. <br>".split()
                    )
                    eval_cond_1 = False
            else:
                # create an evaluation text for the moment when the threshold isn't found, set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_1 = " ".join("Evaluation not possible, the trigger values were never found.".split())

            if time_threshold_2 is not None:
                evaluation_2 = " ".join(
                    f"The evaluation is PASSED when {Signals.Columns.VELOCITY} reaches a value above  {aup.AP_G_V_SCANNING_THRESH_OFF_MPS} m/s at "
                    f"timestamp <b>{round(time.iloc[time_threshold_2 + 10], 3)} s</b>, as expected. "
                    f"This indicates that the AUP transitioned to Init after the ego vehicle is driving with a velocity above.".split()
                )
                eval_cond_2 = True  # set the evaluation condition as TRUE
                cond_negative = core_state.iloc[time_threshold_2 + 10] != aup.CORE_STATUS.CORE_INIT
                if cond_negative:
                    evaluation_2 = " ".join(
                        f"The evaluation FAILED when {Signals.Columns.VELOCITY} reached a value above  {aup.AP_G_V_SCANNING_THRESH_OFF_MPS} m/s at "
                        f"timestamp <b>{round(time.iloc[time_threshold_2], 3)} s</b>. "
                        f"After the vehicle's velocity accelerated, the signal {Signals.Columns.CORE_STATE} did not transition to the expected "
                        f"Init state. At timestamp <b>{round(time.iloc[time_threshold_2 + 10], 3)} s</b>, the signal was in state "
                        f"{signals['status_core'].iloc[time_threshold_2 + 10]} ({core_state.iloc[time_threshold_2 + 10]}), "
                        f"which is incorrect.".split()
                    )
                    eval_cond_2 = False

                # set the verdict of the test step
                if eval_cond_2 and eval_cond_1:
                    self.result.measured_result = TRUE
                else:
                    self.result.measured_result = FALSE
            else:
                # create an evaluation text for the moment when the threshold it's not found,set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_1 = evaluation_2 = " ".join(
                    "Evaluation not possible, the trigger value  was never found.".split()
                )

            verdict1 = "PASSED" if eval_cond_1 else "FAILED" if eval_cond_1 is False else "NOT ASSESSED"
            verdict2 = "PASSED" if eval_cond_2 else "FAILED" if eval_cond_2 is False else "NOT ASSESSED"
            expected_val_1 = "AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_SCANNING (1)"
            expected_val_2 = "delay 0.1s: AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_INIT (0)"
            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T1 - T2"] = [expected_val_1, evaluation_1, verdict1]
            signal_summary["T2"] = [expected_val_2, evaluation_2, verdict2]

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
                    y=velocity,
                    mode="lines",
                    name=Signals.Columns.VELOCITY,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_velocity"],
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

            if time_threshold_1 is not None and time_threshold_2 is not None:
                fig.add_vrect(
                    x0=time.iat[time_threshold_1],
                    x1=time.iat[time_threshold_2],
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
    name="SWRT_CNC_AUP_ScanningToInit_Velocity",
    description=(
        f"This test case verifies that the AutomatedParkingCore shall transition from Scanning to Init when a vehicle ego vehicle is driving forward with a velocity above {aup.AP_G_V_SCANNING_THRESH_OFF_MPS} m/s."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ScanningToInit_Velocity_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [SWRT_CNC_AUP_ScanningToInit_Velocity_TS]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br><br>
                T1: <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> = CORE_SCANNING (1)  <br>
                T2: <em>Car.v </em> > AP_G_V_SCANNING_THRESH_OFF_MPS (11.250 m/s) <br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br><br>
                - T1-T2: <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu </em> == CORE_SCANNING (1) <br>
                - T2: <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_INIT (0) just after T2<br>
            </td>
        </tr>
    </table>


"""
