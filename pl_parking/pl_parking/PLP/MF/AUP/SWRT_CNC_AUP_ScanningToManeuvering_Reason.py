"""
T1:
AP.doorStatusPort.status.driver_nu == DOOR_STATUS_OPEN (1)

ET1:
delay -0.01s: AP.apUserInformationPort.generalUserInformation_nu == NO_MESSAGE (0)
delay 1.0s: AP.apUserInformationPort.generalUserInformation_nu == CLOSE_DOOR_OR_START_REMOTE (15)
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
ALIAS = "SWRT_CNC_AUP_ScanningToManeuvering_Reason"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        CORE_STATE = "AP.PARKSMCoreStatusPort.parksmCoreState_nu"
        STATUS_DRIVER = "AP.doorStatusPort.status.driver_nu"
        ACT_HEAD_UNIT = "AP.hmiOutputPort.userActionHeadUnit_nu"
        USER_INFO = "AP.apUserInformationPort.generalUserInformation_nu"

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
            self.Columns.STATUS_DRIVER: [
                "AP.doorStatusPort.status.driver_nu",
            ],
            self.Columns.USER_INFO: [
                "AP.apUserInformationPort.generalUserInformation_nu",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Scanning To Maneuvering Reason",
    description=(
        "This test case verifies that in case a transition condition to Maneuvering state is not fulfilled, the AutomatedParkingCore shall provide an information about the reason not to transition to Maneuvering state."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ScanningToManeuvering_Reason_TS(TestStep):
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
            eval_t1 = False
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

            time = signals[Signals.Columns.TIME]
            user_info = signals[Signals.Columns.USER_INFO]
            status_driver = signals[Signals.Columns.STATUS_DRIVER]

            signals["status_door"] = status_driver.apply(lambda x: fh.get_status_label(x, aup.DOOR_DRIVER))
            signals["status_user"] = user_info.apply(lambda x: fh.get_status_label(x, aup.HMI_MESSAGE))

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_1 = find_time_threshold(status_driver, aup.DOOR_DRIVER.DOOR_STATUS_OPEN)

            # This test case verifies that in case a transition condition
            # to Maneuvering state is not fulfilled, the AutomatedParkingCore
            # shall provide an information about the reason not to transition to Maneuvering state.
            if time_threshold_1 is not None:
                evaluation_1 = " ".join(
                    f"The evaluation PASSED at the moment when {Signals.Columns.STATUS_DRIVER} == DOOR_STATUS_OPEN ({aup.DOOR_DRIVER.DOOR_STATUS_OPEN}) "
                    f"at timestamp <b>{round(time.iloc[time_threshold_1], 3)} s</b>, meeting the expected conditions. <br>"
                    f"The AUP Core did not had an information message just before the door was opened. <br>".split()
                )
                eval_cond_1 = True  # set the evaluation condition as TRUE
                delay_negative = user_info.iloc[time_threshold_1 - 1] != aup.HMI_MESSAGE.NO_MESSAGE
                delay_positive = user_info.iloc[time_threshold_1 + 100] != aup.HMI_MESSAGE.CLOSE_DOOR_OR_START_REMOTE

                if delay_negative or delay_positive:
                    evaluation_1 = " ".join(
                        f"The evaluation FAILED at the moment when {Signals.Columns.STATUS_DRIVER} == DOOR_STATUS_OPEN ({aup.DOOR_DRIVER.DOOR_STATUS_OPEN}) "
                        f"(<b>{round(time.iloc[time_threshold_1], 3)} s</b>). <br>"
                        f"The signal {Signals.Columns.USER_INFO} did not provide the expected information about the reason not to transition to Maneuvering state.<br>"
                        f" - At time <b>{round(time.iloc[time_threshold_1 - 1], 3)} s</b>, it was in state "
                        f"{signals['status_user'].iloc[time_threshold_1 - 1]} ({user_info.iloc[time_threshold_1 - 1]}), instead of the expected NO_MESSAGE (0) state. <br>"
                        f" - At time <b>{round(time.iloc[time_threshold_1 - 1], 3)} s</b>, it was in state "
                        f"{signals['status_user'].iloc[time_threshold_1 - 1]} ({user_info.iloc[time_threshold_1 - 1]}), instead of the expected CLOSE_DOOR_OR_START_REMOTE (15) state. <br>".split()
                    )
                    eval_cond_1 = False
            else:
                evaluation_1 = " ".join(
                    f"The evaluation FAILED because the signal {Signals.Columns.STATUS_DRIVER} did not reach the DOOR_STATUS_OPEN (1) state. <br>"
                    f"This indicates that the driver door was not opened during the measurement. <br>".split()
                )
                eval_cond_1 = False

            # set the verdict of the test step
            if eval_cond_1:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict1 = "PASSED" if eval_t1 else "FAILED" if eval_t1 is False else "NOT ASSESSED"

            expected_val_1 = "delay -0.01s: AP.apUserInformationPort.generalUserInformation_nu == NO_MESSAGE (0) <br>\
                            delay 1.0s: AP.apUserInformationPort.generalUserInformation_nu == CLOSE_DOOR_OR_START_REMOTE (15)<br>"

            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T1"] = [expected_val_1, evaluation_1, verdict1]

            remark = html_remark
            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            fig = go.Figure()
            # add the needed signals in the plot

            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=user_info,
                    mode="lines",
                    name=Signals.Columns.USER_INFO,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_user"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=status_driver,
                    mode="lines",
                    name=Signals.Columns.STATUS_DRIVER,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_door"],
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
    name="SWRT_CNC_AUP_ScanningToManeuvering_Reason",
    description=(
        "This test case verifies that in case a transition condition to Maneuvering state is not fulfilled, the AutomatedParkingCore shall provide an information about the reason not to transition to Maneuvering state."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ScanningToManeuvering_Reason_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [SWRT_CNC_AUP_ScanningToManeuvering_Reason_TS]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br><br>
                T1: <em>AP.doorStatusPort.status.driver_nu</em> = DOOR_STATUS_OPEN (1)<br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br><br>
                - Before T1: <em>AP.apUserInformationPort.generalUserInformation_nu</em> = NO_MESSAGE (0) occurs just before T1.<br>
                - After T1: <em>AP.apUserInformationPort.generalUserInformation_nu</em> = CLOSE_DOOR_OR_START_REMOTE (15) occurs just after T1.
            </td>
        </tr>
    </table>


"""
