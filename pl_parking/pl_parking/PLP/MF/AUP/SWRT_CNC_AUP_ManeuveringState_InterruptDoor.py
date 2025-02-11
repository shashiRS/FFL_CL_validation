"""
T1:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PARKING (2)

T2:
AP.doorStatusPort.status.driver_nu == 1

ET2:
delay -0.1s: AP.trajCtrlRequestPort.drivingModeReq_nu == FOLLOW_TRAJ (1)
delay 0.1s: AP.trajCtrlRequestPort.drivingModeReq_nu == MAKE_SECURE (3)
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
ALIAS = "SWRT_CNC_AUP_ManeuveringState_InterruptDoor"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        CORE_STATE = "AP.PARKSMCoreStatusPort.parksmCoreState_nu"
        DRV_MODE_REQ = "AP.trajCtrlRequestPort.drivingModeReq_nu"
        DOOR_DRIVER = "AP.doorStatusPort.status.driver_nu"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.CORE_STATE: [
                "AP.PARKSMCoreStatusPort.parksmCoreState_nu",
            ],
            self.Columns.DRV_MODE_REQ: [
                "AP.trajCtrlRequestPort.drivingModeReq_nu",
            ],
            self.Columns.TIME: [
                "Time",
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
    name="Maneuvering State Interrupt Door",
    description=(
        "This test case verifies that in Maneuvering state the AutomatedParkingCore core shall stop to follow the path and secure the vehicle in case there is a vehicle state deactivation condition (driver door)."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringState_InterruptDoor_TS(TestStep):
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
        time_threshold_1 = None
        time_threshold_2 = None
        eval_cond = False
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
        core_state = signals[Signals.Columns.CORE_STATE]
        drv_mode_req = signals[Signals.Columns.DRV_MODE_REQ]
        door_driver = signals[Signals.Columns.DOOR_DRIVER]
        try:
            t1 = core_state == aup.CORE_STATUS.CORE_PARKING
            t2 = door_driver == 1

            if np.any(t1):
                time_threshold_1 = np.argmax(t1)
            if np.any(t2):
                time_threshold_2 = np.argmax(t2)

            signals["status_drv"] = drv_mode_req.apply(lambda x: fh.get_status_label(x, aup.DRIVING_MODE))
            signals["status_core"] = core_state.apply(lambda x: fh.get_status_label(x, aup.CORE_STATUS))
            signals["status_door"] = door_driver.apply(lambda x: fh.get_status_label(x, aup.DOOR_DRIVER))

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
                    f"The evaluation PASSED at the moment when {Signals.Columns.DOOR_DRIVER} == DOOR_STATUS_OPEN "
                    f"({aup.DOOR_DRIVER.DOOR_STATUS_OPEN}) (<b>{round(time.iloc[time_threshold_2], 3)} s</b>). <br>"
                    f"As expected, the Automated Parking Core (AUP Core) stopped following the path and secured the vehicle upon detecting "
                    f"a vehicle state deactivation condition triggered by the driver's door being opened.".split()
                )

                eval_cond = True  # set the evaluation condition as TRUE
                delay_negative = drv_mode_req.iloc[time_threshold_2 - 10] != constants.AUPConstants.FOLLOW_TRAJ
                delay_posistive = drv_mode_req.iloc[time_threshold_2 + 10] != constants.AUPConstants.MAKE_SECURE

                if delay_negative or delay_posistive:

                    string_neg = (
                        "inconsistent with the expected FOLLOW_TRAJ state"
                        if delay_negative
                        else "consistent with the expected FOLLOW_TRAJ state"
                    )
                    string_pos = (
                        "inconsistent with the expected MAKE_SECURE state"
                        if delay_posistive
                        else "consistent with the expected MAKE_SECURE state"
                    )

                    evaluation_2 = " ".join(
                        f"The evaluation FAILED at the moment when {Signals.Columns.DOOR_DRIVER} == DOOR_STATUS_OPEN"
                        f"({aup.DOOR_DRIVER.DOOR_STATUS_OPEN}) (<b>{round(time.iloc[time_threshold_2], 3)} s</b>). <br>"
                        f"The signal {Signals.Columns.DRV_MODE_REQ} did not meet expectations: <br>"
                        f" - Before the driver's door was opened (<b>{round(time.iloc[time_threshold_2 - 10], 3)} s</b>), "
                        f"the signal was in state {signals['status_drv'].iloc[time_threshold_2 - 10]} "
                        f"({drv_mode_req.iloc[time_threshold_2 - 10]}), which is {string_neg}. <br>"
                        f" - After the driver's door was opened (<b>{round(time.iloc[time_threshold_2 + 10], 3)} s</b>), "
                        f"the signal transitioned to state {signals['status_drv'].iloc[time_threshold_2 + 10]} "
                        f"({drv_mode_req.iloc[time_threshold_2 + 10]}), which is {string_pos}. <br>".split()
                    )

                    eval_cond = False

                # set the verdict of the test step
                if eval_cond and eval_t1:
                    self.result.measured_result = TRUE
                else:
                    self.result.measured_result = FALSE
            else:
                # create an evaluation text for the moment when the threshold it's not found,set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_2 = " ".join(
                    f"Evaluation not possible, the trigger value ({Signals.Columns.DOOR_DRIVER} == DOOR_STATUS_OPEN (1)) was never found.".split()
                )
            # you have to correlate the signal with the evaluation text in the table

            verdict1 = "PASSED" if eval_t1 else "FAILED" if eval_t1 is False else "NOT ASSESSED"
            verdict2 = "PASSED" if eval_cond else "FAILED" if eval_cond is False else "NOT ASSESSED"
            expected_val_1 = "AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PARKING (2)"
            expected_val_2 = " ".join(
                "at delay -0.1s: AP.trajCtrlRequestPort.drivingModeReq_nu == FOLLOW_TRAJ (1) <br>"
                "at delay 0.1s:AP.trajCtrlRequestPort.drivingModeReq_nu == MAKE_SECURE (3) <br>".split()
            )
            signal_summary["T1"] = [expected_val_1, evaluation_1, verdict1]
            signal_summary["T2"] = [expected_val_2, evaluation_2, verdict2]
            remark = " ".join(
                f"Check that at moment of {Signals.Columns.DOOR_DRIVER} == DOOR_STATUS_OPEN(1) ± 0.1s the following "
                f"conditions are met: <br>"
                f"at delay -0.1s: AP.trajCtrlRequestPort.drivingModeReq_nu == FOLLOW_TRAJ (1) <br>"
                f"at delay 0.1s:AP.trajCtrlRequestPort.drivingModeReq_nu == MAKE_SECURE (3) <br>".split()
            )
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
                    y=drv_mode_req,
                    mode="lines",
                    name=Signals.Columns.DRV_MODE_REQ,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_drv"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=door_driver,
                    mode="lines",
                    name=Signals.Columns.DOOR_DRIVER,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_door"],
                )
            )
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
                title="Maneuvering State Interrupt Door Graphical Overview",
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
    name="SWRT_CNC_AUP_ManeuveringState_InterruptDoor",
    description=(
        "This test case verifies that in Maneuvering state the AutomatedParkingCore core shall stop to follow the path and secure the vehicle in case there is a vehicle state deactivation condition (driver door)."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringState_InterruptDoor_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [SWRT_CNC_AUP_ManeuveringState_InterruptDoor_TS]  # in this list all the needed test steps are included
