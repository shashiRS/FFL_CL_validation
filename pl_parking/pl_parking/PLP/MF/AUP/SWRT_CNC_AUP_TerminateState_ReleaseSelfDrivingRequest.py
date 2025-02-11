"""
T1:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PARKING (2)

T2:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PAUSE (3)

ET1:
within 0.08s: AP.avgaGuidanceRequestPort.automatedVehicleGuidanceRequest != AVGA_NONE (0)

ET2:
within 0.08s: AP.avgaGuidanceRequestPort.automatedVehicleGuidanceRequest == AVGA_NONE (0)

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
ALIAS = "SWRT_CNC_AUP_TerminateState_ReleaseSelfDrivingRequest"


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
        GUIDANCE_REQUEST = "AP.avgaGuidanceRequestPort.automatedVehicleGuidanceRequest"

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
            self.Columns.GUIDANCE_REQUEST: [
                "AP.avgaGuidanceRequestPort.automatedVehicleGuidanceRequest",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Terminate State Release Self Driving Request",
    description=(
        "This test case verifies that in Terminate state the AutomatedParkingCore shall release the self driving request for the supervision provider."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_TerminateState_ReleaseSelfDrivingRequest_TS(TestStep):
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
            guidance_request = signals[Signals.Columns.GUIDANCE_REQUEST]

            signals["status_core"] = core_state.apply(lambda x: fh.get_status_label(x, aup.CORE_STATUS))
            signals["status_guidance"] = guidance_request.apply(lambda x: fh.get_status_label(x, aup.GUIDANCE_REQUEST))

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_1 = find_time_threshold(core_state, aup.CORE_STATUS.CORE_PARKING)
            if time_threshold_1 is not None:
                time_threshold_2 = (
                    find_time_threshold(core_state.iloc[time_threshold_1:], aup.CORE_STATUS.CORE_PAUSE)
                    + time_threshold_1
                )

            if time_threshold_1 is not None:
                evaluation_1 = " ".join(
                    f"The evaluation is PASSED when {Signals.Columns.CORE_STATE} reaches the CCORE_PARKING (2) at timestamp<b>{round(time.iloc[time_threshold_1], 3)} s</b> . "
                    f"This confirms that  AutomatedParkingCore did not released the self driving request for the supervision provider while parking.".split()
                )
                eval_cond_1 = True  # set the evaluation condition as TRUE
                cond_negative = guidance_request.iloc[time_threshold_1 + 8] == aup.GUIDANCE_REQUEST.AVGA_NONE

                if cond_negative:
                    evaluation_1 = " ".join(
                        f"The evaluation FAILED when {Signals.Columns.CORE_STATE} reached the CORE_PARKING (2) state at "
                        f"timestamp <b>{round(time.iloc[time_threshold_1], 3)} s</b>. "
                        f"When parking started, the signal {Signals.Columns.GUIDANCE_REQUEST} had the state"
                        f"AP_SUCCESS (1) . At timestamp <b>{round(time.iloc[time_threshold_1 + 8], 3)} s</b>, the signal was in state "
                        f"which is incorrect.".split()
                    )
                    eval_cond_1 = False
            else:
                # create an evaluation text for the moment when the threshold isn't found, set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_1 = " ".join("Evaluation not possible, the trigger values were never found.".split())

            if time_threshold_2 is not None:
                evaluation_2 = " ".join(
                    f"The evaluation is PASSED when {Signals.Columns.CORE_STATE} reaches the CORE_PAUSE (3) state at "
                    f"timestamp <b>{round(time.iloc[time_threshold_2 + 8], 3)} s</b>, as expected. "
                    f"This indicates that the  AutomatedParkingCore released the self driving request for the supervision provider.".split()
                )
                eval_cond_2 = True  # set the evaluation condition as TRUE
                cond_negative = guidance_request.iloc[time_threshold_2 + 8] != aup.GUIDANCE_REQUEST.AVGA_NONE
                if cond_negative:
                    evaluation_2 = " ".join(
                        f"The evaluation FAILED when {Signals.Columns.CORE_STATE} reached the CORE_PAUSE (3) state at "
                        f"timestamp <b>{round(time.iloc[time_threshold_2], 3)} s</b>. "
                        f"After the parking paused, the signal {Signals.Columns.GUIDANCE_REQUEST} did not transition to the expected "
                        f"AP_SUCCESS (1) state. At timestamp <b>{round(time.iloc[time_threshold_2 + 8], 3)} s</b>, the signal was in state "
                        f"{signals['status_guidance'].iloc[time_threshold_2 + 8]} ({core_state.iloc[time_threshold_2 + 8]}), "
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
                    "Evaluation not possible, the trigger values were never found.".split()
                )

            verdict1 = "PASSED" if eval_cond_1 else "FAILED" if eval_cond_1 is False else "NOT ASSESSED"
            verdict2 = "PASSED" if eval_cond_2 else "FAILED" if eval_cond_2 is False else "NOT ASSESSED"
            expected_val_1 = "within 0.08s: AP.avgaGuidanceRequestPort.automatedVehicleGuidanceRequest != AVGA_NONE (0)"
            expected_val_2 = "within 0.08s: AP.avgaGuidanceRequestPort.automatedVehicleGuidanceRequest == AVGA_NONE (0)"
            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T1"] = [expected_val_1, evaluation_1, verdict1]
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
                    y=guidance_request,
                    mode="lines",
                    name=Signals.Columns.GUIDANCE_REQUEST,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_guidance"],
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
    name="SWRT_CNC_AUP_TerminateState_ReleaseSelfDrivingRequest",
    description=(
        "This test case verifies that in Terminate state the AutomatedParkingCore shall release the self driving request for the supervision provider."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_TerminateState_ReleaseSelfDrivingRequest_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_TerminateState_ReleaseSelfDrivingRequest_TS
        ]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br><br>
                T1: <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> = CORE_PARKING (2)  <br>
                T2: <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu </em> = CORE_PAUSE (3) <br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br><br>
                - T1: <em> AP.avgaGuidanceRequestPort.automatedVehicleGuidanceRequest</em> != AVGA_NONE (0) just after T1<br>
                - T2: <em> AP.avgaGuidanceRequestPort.automatedVehicleGuidanceRequest</em> == AVGA_NONE (0) just after T2<br>
            </td>
        </tr>
    </table>


"""
