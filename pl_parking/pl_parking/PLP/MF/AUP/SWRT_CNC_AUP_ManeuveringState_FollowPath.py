"""
T1:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_PARKING (2)

ET1:
delay -0.1s: AP.trajCtrlRequestPort.drivingModeReq_nu = NO_INTERVENTION (0)
delay 0.1s: AP.trajCtrlRequestPort.drivingModeReq_nu = FOLLOW_TRAJ (1)
"""  # this is a required docstring

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
ALIAS = "SWRT_CNC_AUP_ManeuveringState_FollowPath"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        CORE_STATE = "AP.PARKSMCoreStatusPort.parksmCoreState_nu"
        DRV_MODE_REQ = "AP.trajCtrlRequestPort.drivingModeReq_nu"

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
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Maneuvering State Follow Path",
    description=(
        "This test case verifies that in Maneuvering state the AutomatedParkingCore shall request to follow the calculated path."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringState_FollowPath_TS(TestStep):
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
        time_threshold = None
        eval_cond = False
        evaluation = ""
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
        try:
            t1 = core_state == aup.CORE_STATUS.CORE_PARKING
            signals["status_drv"] = drv_mode_req.apply(lambda x: fh.get_status_label(x, aup.DRIVING_MODE))
            signals["status_core"] = core_state.apply(lambda x: fh.get_status_label(x, aup.CORE_STATUS))

            if np.any(t1):
                time_threshold = np.argmax(t1)

            if time_threshold is not None:
                evaluation = " ".join(
                    f"The evaluation is PASSED at moment when {Signals.Columns.CORE_STATE} == "
                    f"CORE_PARKING ({aup.CORE_STATUS.CORE_PARKING}) (<b>{round(time.iloc[time_threshold], 3)} s</b>), "
                    f"the vehicle is following the calculated path after the automated maneuver initiated.".split()
                )
                eval_cond = True  # set the evaluation condition as TRUE
                delay_negative = drv_mode_req.iloc[time_threshold - 10] != aup.DRIVING_MODE.NO_INTERVENTION
                delay_posistive = drv_mode_req.iloc[time_threshold + 10] != aup.DRIVING_MODE.FOLLOW_TRAJ

                if delay_negative or delay_posistive:
                    if delay_negative and delay_posistive:
                        eval_neg = "has values different than NO_INTERVENTION (0) before the parking state, \
                        and is not following the path after the automated maneuver initiated"
                    elif delay_negative:
                        eval_neg = "has values different than NO_INTERVENTION (0) before the parking state"
                    else:
                        eval_neg = "is not following the path after the automated maneuver initiated"

                    evaluation = " ".join(
                        f"The evaluation of signal is FAILED at moment {Signals.Columns.CORE_STATE} == "
                        f" CORE_PARKING({aup.CORE_STATUS.CORE_PARKING}) (<b>{round(time.iloc[time_threshold], 3)} s</b>),"
                        f" because the vehicle {eval_neg},<br>"
                        f" the signal {Signals.Columns.DRV_MODE_REQ} has the following states: <br>"
                        f" before the automated maneuver initiated ( {round(time.iloc[time_threshold - 10], 3)} s ): {signals['status_drv'].iloc[time_threshold - 10]} ({drv_mode_req.iloc[time_threshold - 10]}), <br>"
                        f" after the automated maneuver initiate {round(time.iloc[time_threshold + 10], 3)} s: {signals['status_drv'].iloc[time_threshold + 10]} ({drv_mode_req.iloc[time_threshold + 10]}). <br>".split()
                    )

                    eval_cond = False

                # set the verdict of the test step
                if eval_cond:
                    self.result.measured_result = TRUE
                else:
                    self.result.measured_result = FALSE
            else:
                # create an evaluation text for the moment when the threshold it's not found,set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation = " ".join(
                    f"Evaluation not possible, the trigger value ({Signals.Columns.CORE_STATE} == {aup.CORE_STATUS.CORE_PARKING}) was never found.".split()
                )
            # you have to correlate the signal with the evaluation text in the table

            expected_val1 = f"delay -0.1s: {Signals.Columns.DRV_MODE_REQ} = NO_INTERVENTION (0)</br>\
            delay 0.1s: {Signals.Columns.DRV_MODE_REQ} = FOLLOW_TRAJ (1)</br>"
            verdict = "PASSED" if eval_cond else "FAILED" if eval_cond is False else "NOT ASSESSED"
            signal_summary["T1"] = [expected_val1, evaluation, verdict]
            # signal_summary[Signals.Columns.DRV_MODE_REQ] = evaluation
            remark = " ".join(
                f"Check that at moment of {Signals.Columns.CORE_STATE} == CORE_PARKING({constants.AUPConstants.CORE_PARKING}) ± 0.1s the signal "
                f"{Signals.Columns.DRV_MODE_REQ} has the following values: <br>"
                f"at delay -0.1s: AP.trajCtrlRequestPort.drivingModeReq_nu = NO_INTERVENTION (0) <br>"
                f" at delay 0.1s: AP.trajCtrlRequestPort.drivingModeReq_nu = FOLLOW_TRAJ (1) <br>".split()
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
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
                title="Maneuvering State Follow Path Graphical Overview",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            if time_threshold is not None:
                fig.add_vline(
                    x=time.iat[time_threshold],
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
    name="SWRT_CNC_AUP_ManeuveringState_FollowPath",
    description=(
        "This test case verifies that in Maneuvering state the AutomatedParkingCore shall request to follow the calculated path."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringState_FollowPath_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [SWRT_CNC_AUP_ManeuveringState_FollowPath_TS]  # in this list all the needed test steps are included
