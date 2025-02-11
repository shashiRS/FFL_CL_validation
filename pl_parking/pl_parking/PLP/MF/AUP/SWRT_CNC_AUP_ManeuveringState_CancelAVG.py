"""
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PARKING (2)

T2:
AP.hmiOutputPort.userActionHeadUnit_nu == TAP_ON_CANCEL (22)

T2:
delay -0.1s: AP.trajCtrlRequestPort.drivingModeReq_nu = FOLLOW_TRAJ (1)
delay 0.1s: AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_FINISH (4)
"""

"""import libraries"""
import logging
import os
import sys

import numpy as np
import pandas as pd
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
from pl_parking.PLP.MF.constants import AUPConstants as aup

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "SWRT_CNC_AUP_ManeuveringState_HMICancel"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        CORE_STATE = "AP.PARKSMCoreStatusPort.parksmCoreState_nu"
        DRV_MODE_REQ = "AP.trajCtrlRequestPort.drivingModeReq_nu"
        ACT_HEAD_UNIT = "AP.hmiOutputPort.userActionHeadUnit_nu"

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
            self.Columns.ACT_HEAD_UNIT: [
                "AP.hmiOutputPort.userActionHeadUnit_nu",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Maneuvering State HMI Cancel",
    description=(
        "This test case verifies that in Maneuvering state the AutomatedParkingCore shall provide the possibility to the driver to cancel/terminate the maneuver."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringState_HMICancel_TS(TestStep):
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
            act_head_unit = signals[Signals.Columns.ACT_HEAD_UNIT]

            t1 = core_state == aup.CORE_STATUS.CORE_PARKING
            t2 = act_head_unit == aup.USER_ACTION.TAP_ON_CANCEL
            signals["state_core"] = core_state.apply(lambda x: fh.get_status_label(x, aup.CORE_STATUS))
            signals["state_action"] = act_head_unit.apply(lambda x: fh.get_status_label(x, aup.USER_ACTION))
            signals["state_drv"] = drv_mode_req.apply(lambda x: fh.get_status_label(x, aup.DRIVING_MODE))

            if np.any(t1):
                time_threshold_1 = np.argmax(t1)
            if np.any(t2):
                time_threshold_2 = np.argmax(t2)

            if time_threshold_1 is not None:
                evaluation_1 = " ".join(
                    f"The signal {Signals.Columns.CORE_STATE} reach the CORE_PARKING (2) state at"
                    f" timestamp <b>{round(time.iloc[time_threshold_1], 3)} s </b>".split()
                )
                eval_t1 = True
            else:
                evaluation_1 = f"The signal {Signals.Columns.CORE_STATE} does not reach the CORE_PARKING (2) state."
                eval_t1 = False

            if time_threshold_2 is not None:
                evaluation_2 = " ".join(
                    f"The evaluation PASSED at the moment when {Signals.Columns.ACT_HEAD_UNIT} == "
                    f"TAP_ON_CANCEL ({aup.USER_ACTION.TAP_ON_CANCEL}) (<b>{round(time.iloc[time_threshold_2], 3)} s</b>). <br>"
                    f"The maneuver was terminated following the driver's decision to cancel it. <br>".split()
                )

                eval_cond = True  # set the evaluation condition as TRUE
                delay_negative = drv_mode_req.iloc[time_threshold_2 - 10] != aup.DRIVING_MODE.FOLLOW_TRAJ
                delay_posistive = core_state.iloc[time_threshold_2 + 10] != aup.CORE_STATUS.CORE_FINISH

                if delay_negative or delay_posistive:
                    if delay_negative and delay_posistive:
                        eval_neg = "the vehicle didn't follow the trajectory and the maneuver was not finished after the driver's decision to cancel it"
                    elif delay_negative:
                        eval_neg = "the vehicle didn't follow the trajectory after the driver's decision to cancel it"
                    else:
                        eval_neg = "the maneuver was not finished after the driver's decision to cancel it"
                    evaluation_2 = " ".join(
                        f"The evaluation FAILED at the moment when {Signals.Columns.ACT_HEAD_UNIT} == "
                        f"TAP_ON_CANCEL ({aup.USER_ACTION.TAP_ON_CANCEL}) (<b>{round(time.iloc[time_threshold_2], 3)} s</b>). <br>"
                        f"This occurred because {eval_neg}. <br>"
                        f"Prior to the driver's cancellation of the maneuver (<b>{round(time.iloc[time_threshold_2 - 10], 3)} s</b>), "
                        f"the signal {Signals.Columns.DRV_MODE_REQ} was in state "
                        f"{signals['state_drv'].iloc[time_threshold_2 - 10]} ({int(drv_mode_req.iloc[time_threshold_2 - 10])}). <br>"
                        f"Following the driver's cancellation (<b>{round(time.iloc[time_threshold_2 + 10], 3)} s</b>), "
                        f"the signal {Signals.Columns.CORE_STATE} was in state "
                        f"{signals['state_core'].iloc[time_threshold_2 + 10]} ({int(core_state.iloc[time_threshold_2 + 10])}). <br>".split()
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
                    f"Evaluation not possible, the trigger value ({Signals.Columns.ACT_HEAD_UNIT} == {constants.AUPConstants.TAP_ON_CANCEL}) was never found.".split()
                )
            verdict1 = "PASSED" if eval_t1 else "FAILED" if eval_t1 is False else "NOT ASSESSED"
            verdict2 = "PASSED" if eval_cond else "FAILED" if eval_cond is False else "NOT ASSESSED"
            expected_val_1 = "AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PARKING (2)"
            expected_val_2 = "delay -0.1s: AP.trajCtrlRequestPort.drivingModeReq_nu == FOLLOW_TRAJ (1)</br>\
            delay 0.1s: AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_FINISH (4)</br>"
            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T1"] = [expected_val_1, evaluation_1, verdict1]
            signal_summary["T2"] = [expected_val_2, evaluation_2, verdict2]

            # signal_summary[Signals.Columns.CORE_STATE] = evaluation_1
            # signal_summary[Signals.Columns.ACT_HEAD_UNIT] = evaluation_2
            remark = " ".join(
                f"Check that at moment of {Signals.Columns.ACT_HEAD_UNIT} == TAP_ON_CANCEL({constants.AUPConstants.TAP_ON_CANCEL}) ± 0.1s the following "
                f"conditions are met: <br>"
                f"at delay -0.1s: AP.trajCtrlRequestPort.drivingModeReq_nu == FOLLOW_TRAJ (1) <br>"
                f"at delay 0.1s: AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_FINISH (4) <br>".split()
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
                    text=signals["state_core"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=drv_mode_req,
                    mode="lines",
                    name=Signals.Columns.DRV_MODE_REQ,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["state_drv"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=act_head_unit,
                    mode="lines",
                    name=Signals.Columns.ACT_HEAD_UNIT,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["state_action"],
                )
            )
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
                title="Maneuvering State HMI Cancel Graphical Overview",
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
    name="SWRT_CNC_AUP_ManeuveringState_HMICancel",
    description=(
        "This test case verifies that in Maneuvering state the AutomatedParkingCore shall provide the possibility to the driver to cancel/terminate the maneuver."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringState_HMICancel_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [SWRT_CNC_AUP_ManeuveringState_HMICancel_TS]  # in this list all the needed test steps are included


def convert_dict_to_pandas(
    signal_summary: dict,
    table_remark="",
    table_title="",
):
    """Converts a dictionary to a Pandas DataFrame and creates an HTML table."""
    # Create a DataFrame from the dictionary
    evaluation_summary = pd.DataFrame(
        {
            "Evaluation Timeframe": {key: key for key, val in signal_summary.items()},
            "Expected Values": {key: val[0] for key, val in signal_summary.items()},
            "Summary": {key: val[1] for key, val in signal_summary.items()},
            "Verdict": {key: val[2] for key, val in signal_summary.items()},
        }
    )

    # Generate HTML table using build_html_table function
    return fh.build_html_table(evaluation_summary, table_remark, table_title)
