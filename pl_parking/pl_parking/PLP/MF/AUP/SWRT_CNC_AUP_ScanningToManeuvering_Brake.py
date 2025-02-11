"""
T1:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_SCANNING (1)

T2:
AP.hmiOutputPort.userActionHeadUnit_nu == TAP_ON_START_PARKING (18)

T3:
T2 + 3.0s

INT_ET2_ET3:
AP.PARKSMCoreStatusPort.parksmCoreState_nu != CORE_PARKING (2) && DM.Brake == 1
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
ALIAS = "SWRT_CNC_AUP_ScanningToManeuvering_Brake"


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
    name="Scanning To Maneuvering Brake",
    description=(
        "This test case verifies that the AutomatedParkingCore shall not transition from Scanning to Maneuvering if the driver has not released the brake."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ScanningToManeuvering_Brake_TS(TestStep):
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
            eval_cond_2 = False
            evaluation_1 = ""
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
            dm_brake = signals[Signals.Columns.DM_BRAKE]

            signals["status_user"] = act_head_unit.apply(lambda x: fh.get_status_label(x, aup.USER_ACTION))
            signals["status_core"] = core_state.apply(lambda x: fh.get_status_label(x, aup.CORE_STATUS))

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_1 = find_time_threshold(core_state, constants.AUPConstants.CORE_SCANNING)
            time_threshold_2 = find_time_threshold(act_head_unit, constants.AUPConstants.TAP_ON_START_PARKING)
            if time_threshold_2 is not None:
                time_threshold_3 = time_threshold_2 + 30
            else:
                time_threshold_3 = None

            if time_threshold_1 is not None:
                evaluation_1 = " ".join(
                    f"The signal {Signals.Columns.CORE_STATE} reach the CORE_SCANNING (1) state at"
                    f" timestamp <b>{round(time.iloc[time_threshold_1 + 10], 3)} s </b>".split()
                )
                eval_t1 = True
            else:
                evaluation_1 = f"The signal {Signals.Columns.CORE_STATE} does not reach the CORE_SCANNING (1) state."
                eval_t1 = False

            if time_threshold_3 is not None and time_threshold_2 is not None:
                interval = core_state.iloc[time_threshold_2:time_threshold_3]
                interval_brake = dm_brake.iloc[time_threshold_2:time_threshold_3]
                if (interval != constants.AUPConstants.CORE_PARKING).all() and (interval_brake == 1).all():
                    evaluation_3 = " ".join(
                        f"The evaluation PASSED because the signal {Signals.Columns.CORE_STATE} did not transition to CORE_PARKING (2) "
                        f"from the moment of user action - TAP_ON_START_PARKING(18) at timestamp <b>{round(time.iloc[time_threshold_2], 3)} s</b> "
                        f"until 3 seconds after that, and the signal {Signals.Columns.DM_BRAKE} == 1 throughout this interval. <br>".split()
                    )
                    eval_cond_2 = True
                else:
                    if (interval_brake == 1).all():
                        eval_neg = "== 1"
                    else:
                        eval_neg = "!= 1"
                    evaluation_3 = (
                        " ".join(
                            f"The evaluation FAILED because either the signal {Signals.Columns.DM_BRAKE} {eval_neg} "
                            f"during the interval from TAP_ON_START_PARKING(18) at timestamp <b>{round(time.iloc[time_threshold_2], 3)} s</b> "
                            f"to 3 seconds after that, indicating that the driver did not release the brake as expected, "
                            f"and the signal {Signals.Columns.CORE_STATE} transitioned to CORE_PARKING (2) "
                            f"within the same interval. <br>".split()
                        )
                        if (interval == aup.CORE_STATUS.CORE_PARKING).any()
                        else " ".join(
                            f"The evaluation FAILED because the signal {Signals.Columns.DM_BRAKE} {eval_neg} "
                            f"during the interval from TAP_ON_START_PARKING at timestamp <b>{round(time.iloc[time_threshold_2], 3)} s</b> "
                            f"to 3 seconds after that. <br>"
                            f"This indicates that the driver did not release the brake as expected. <br>".split()
                        )
                    )
                    eval_cond_2 = False

                # set the verdict of the test step
                if eval_cond_2 and eval_t1:
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
            verdict3 = "PASSED" if eval_cond_2 else "FAILED" if eval_cond_2 is False else "NOT ASSESSED"
            expected_val_1 = "AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_SCANNING (1)"
            expected_val_2 = "AP.PARKSMCoreStatusPort.parksmCoreState_nu != CORE_PARKING (2) && DM.Brake == 1"
            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T1"] = [expected_val_1, evaluation_1, verdict1]
            signal_summary["T2-T3"] = [expected_val_2, evaluation_3, verdict3]

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
            fig.add_trace(go.Scatter(x=time, y=dm_brake, mode="lines", name=Signals.Columns.DM_BRAKE))
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
            if time_threshold_2 is not None and time_threshold_3 is not None:
                fig.add_vrect(
                    x0=time.iat[time_threshold_2],
                    x1=time.iat[time_threshold_3],
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
    name="SWRT_CNC_AUP_ScanningToManeuvering_Brake",
    description=(
        "This test case verifies that the AutomatedParkingCore shall not transition from Scanning to Maneuvering if the driver has not released the brake."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ScanningToManeuvering_Brake_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [SWRT_CNC_AUP_ScanningToManeuvering_Brake_TS]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br><br>
                T1: <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> = CORE_SCANNING (1) <br>
                T2: <em>AP.hmiOutputPort.userActionHeadUnit_nu</em> = TAP_ON_START_PARKING (18) <br>
                T3: T2 + 3s <br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br><br>
                - T2-T3: <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> != CORE_PARKING (2) between T3 and T4 and <em>DM.Brake</em> == 1<br>
            </td>
        </tr>
    </table>


"""
