"""Example functional test"""  # this is a required docstring

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

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "VELOCITY_TH"


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """
        Pentru semnale:
        ACTIVATE_BRAKE_INTERV <-> LSCA.staticBraking.EbaActive
        VELOCITY <-> Vhcl.v
        MINIMUM_DISTANCE <-> AP.shortestDistanceToHighObject_m (de investigat si ce se scrie in AP.pdwProcToLogicPort.minimalDistance_m)
        DRIVEN_DISTANCE <-> Nu cred ca are un echivalent - se poate calcula folosing Vhcl.sRoad intre 2 triger-e (e.g. intre LSCA.staticBraking.EbaActive == 1 si Vhcl.v < 0.01)
        TIME <-> Time
        """

        ACTIVATE_BRAKE_INTERV = "LSCA.staticBraking.EbaActive"
        VELOCITY = "Car.v"
        TIME = "Time"
        MINIMUM_DISTANCE = "MINIMUM_DISTANCE"
        MIN_DIST_HIGH_OBJ = "MIN_DIST_HIGH_OBJ"
        VELOCITY_ROAD = "VELOCITY_ROAD"
        ON_BRAKE_INTERV = "LSCA.staticBraking.EbaOn"
        SELECTOR_CTRL = "DM.SelectorCtrl"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = [
            (
                self.Columns.ACTIVATE_BRAKE_INTERV,
                [
                    "LSCA.staticBraking.EbaActive",
                ],
            ),
            (
                self.Columns.VELOCITY,
                [
                    "Car.v",
                ],
            ),
            (
                self.Columns.ON_BRAKE_INTERV,
                [
                    "LSCA.staticBraking.EbaOn",
                ],
            ),
            (
                self.Columns.TIME,
                [
                    "Time",
                ],
            ),
            (
                self.Columns.SELECTOR_CTRL,
                [
                    "DM.SelectorCtrl",
                ],
            ),
        ]


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="LSCA max speed threshold",  # this would be shown as a test step name in html report
    description=(
        "LSCA function should be active while within low-speed threshold, and inactive after the max speed threshold was passed."
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepVelocityTH(TestStep):
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
        # signal_name = signals_obj._properties
        # Make a constant with the reader for signals:
        self.test_result = fc.INPUT_MISSING  # Result
        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        signal_summary = {}  # Initializing the dictionary with data for final evaluation table
        T1 = None
        T2 = None

        signals = self.readers[ALIAS]
        signals[Signals.Columns.TIMESTAMP] = signals.index

        ap_time = signals[Signals.Columns.TIME]  # the info for specific signal are extracted from the bigger data frame
        eba_on = signals[Signals.Columns.ON_BRAKE_INTERV]  # take into consideration you need to use df methods
        car_v = signals[Signals.Columns.VELOCITY]
        selector_ctrl = signals[Signals.Columns.SELECTOR_CTRL]
        time_fail_1 = 0
        val_fail_1 = 0
        time_fail_2 = 0
        val_fail_2 = 0

        if selector_ctrl.iat[len(selector_ctrl) // 2] == 1:
            T1_mask = car_v > constants.LscaConstants.LSCA_B_FORW_SPEED_MIN_ON_MPS + 0.1
            T2_mask = car_v > constants.LscaConstants.LSCA_B_FORW_SPEED_MAX_ON_MPS
        else:
            T1_mask = car_v > constants.LscaConstants.LSCA_B_BACKW_SPEED_MIN_ON_MPS + 0.1
            T2_mask = car_v > constants.LscaConstants.LSCA_B_BACKW_SPEED_MAX_ON_MPS
        T1 = np.argmax(T1_mask)
        T2 = np.argmax(T2_mask)
        # de adaugat verificare pentru fata sau spate
        T3 = None if T2 is None or T2 == 0 else T2 - 1
        T4 = len(T1_mask) - 1

        for idx, val in enumerate(eba_on):
            if idx >= T1 and idx <= T3:
                if val != 1:
                    time_fail_1 = idx
                    val_fail_1 = int(val)
                    break
            if idx >= T2 and idx <= T4:
                if val != 0:
                    time_fail_2 = idx
                    val_fail_2 = int(val)
                    break

        eval_cond1 = eba_on.iloc[T1 : T3 + 1].eq(1).all() if T1 is not None and T3 is not None else None
        if eval_cond1:
            evaluation1 = " ".join(
                f" The signal Eba.On is set to 1 during the time interval from {round(ap_time.iat[T1],3)}[s] to {round(ap_time.iat[T3],3)}[s], indicating  \
                that the LSCA function is active when the car's velocity falls within the low-speed threshold range.".split()
            )
            verdict1 = "PASSED"
        elif not eval_cond1:
            evaluation1 = f"The LSCA function is disabled even though the velocity is in the valid range(Car.v = {round(car_v.iat[time_fail_1],3)}[m/s] when LSCA.staticBraking.EbaActive = {val_fail_1}, at {round(ap_time.iat[time_fail_1],3)}[s])."
            # evaluation1 = " ".join(
            # f" The signal Eba.On has values other than 1 during the interval from {round(ap_time.iat[T1],3)}[s] to {round(ap_time.iat[T3],3)}[s] range, \
            #     thus the LSCA function is inactive when the car's velocity falls within the low-speed threshold range.".split())
            verdict1 = "FAILED"
        else:
            evaluation1 = "The evaluation was not possible due to triggers values weren't found."
            verdict1 = "INVALID DATA"

        eval_cond2 = eba_on.iloc[T2 : T4 + 1].eq(0).all() if T2 is not None and T4 is not None else None
        if eval_cond2:
            evaluation2 = " ".join(
                f" The signal Eba.On is set to 0 during the time interval from {round(ap_time.iat[T2],3)}[s] to {round(ap_time.iat[T4],3)}[s], indicating  \
                that the LSCA function is active when the car's velocity falls within the low-speed threshold range.".split()
            )
            verdict2 = "PASSED"
        elif not eval_cond2:
            evaluation2 = f"The LSCA function is enabled event though the ego velocity is outside of the valid range(Car.v = {round(car_v.iat[time_fail_2],3)}[m/s] when LSCA.staticBraking.EbaActive = {val_fail_2}, at {round(ap_time.iat[time_fail_2],3)}[s])."
            # evaluation2 = " ".join(
            #     f" The signal Eba.On has values other than 0 during the interval from {round(ap_time.iat[T2],3)}[s] to {round(ap_time.iat[T4],3)}[s] range, \
            #         thus the LSCA function is inactive when the car's velocity falls within the low-speed threshold range.".split())
            verdict2 = "FAILED"
        else:
            evaluation2 = "The evaluation was not possible due to triggers values weren't found."
            verdict2 = "INVALID DATA"

        if eval_cond1 and eval_cond2:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["T1-T3"] = [Signals.Columns.ON_BRAKE_INTERV, evaluation1, verdict1]
        signal_summary["T2-T4"] = [Signals.Columns.ON_BRAKE_INTERV, evaluation2, verdict2]
        if selector_ctrl.iat[T2] == -1:
            remark = "".join(
                f"T1: Car.v > LSCA_B_BACKW_SPEED_MIN_ON_MPS({constants.LscaConstants.LSCA_B_BACKW_SPEED_MIN_ON_MPS})+0.1<br>   \
                T2: Car.v > LSCA_B_BACKW_SPEED_MAX_ON_MPS({constants.LscaConstants.LSCA_B_BACKW_SPEED_MAX_ON_MPS})<br>     \
                T3: T2 - 0.01<br>  \
                T4: end<br>    \
                ".split(
                    sep="\n"
                )
            )
        elif selector_ctrl.iat[T2] == 1:
            remark = f"T1: Car.v > LSCA_B_FORW_SPEED_MIN_ON_MPS({constants.LscaConstants.LSCA_B_FORW_SPEED_MIN_ON_MPS})+0.1<br>     \
                T2: Car.v > LSCA_B_FORW_SPEED_MAX_ON_MPS({constants.LscaConstants.LSCA_B_FORW_SPEED_MAX_ON_MPS})<br>   \
                T3: T2 - 0.01<br>  \
                T4: end<br>    \
                "
        else:
            remark = "TRIGGERS NOT FOUND"
        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
        plots.append(self.sig_sum)

        fig = go.Figure()
        # add the needed signals in the plot
        fig.add_trace(go.Scatter(x=ap_time, y=eba_on, mode="lines", name=Signals.Columns.ON_BRAKE_INTERV))
        fig.add_trace(go.Scatter(x=ap_time, y=car_v, mode="lines", name=Signals.Columns.VELOCITY))
        fig.add_trace(go.Scatter(x=ap_time, y=selector_ctrl, mode="lines", name=Signals.Columns.SELECTOR_CTRL))
        fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
        fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
        if T3 is not None and T1 is not None:
            fig.add_vrect(
                x0=ap_time.iat[T1],
                x1=ap_time.iat[T3],
                fillcolor="LightSalmon",
                line_width=0,
                opacity=0.3,
                # annotation_text="T1-T3",
                layer="below",
            )
        if T2 is not None and T4 is not None:
            fig.add_vrect(
                x0=ap_time.iat[T2],
                x1=ap_time.iat[T4],
                fillcolor="LimeGreen",
                line_width=0,
                opacity=0.3,
                # annotation_text="T2-T4",
                layer="below",
            )

        if T3 is not None:
            fig.add_vline(
                x=ap_time.iat[T3], line_width=1, line_dash="dash", line_color="darkslategray", annotation_text="T3"
            )
        if T4 is not None:
            fig.add_vline(
                x=ap_time.iat[T4], line_width=1, line_dash="dash", line_color="darkslategray", annotation_text="T4"
            )
        if T1 is not None:
            fig.add_vline(
                x=ap_time.iat[T1], line_width=1, line_dash="dash", line_color="darkslategray", annotation_text="T1"
            )
        if T2 is not None:
            fig.add_vline(
                x=ap_time.iat[T2], line_width=1, line_dash="dash", line_color="darkslategray", annotation_text="     T2"
            )

        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)


# Define the test case definition. This will include the name of the test case and a description of the test.
@testcase_definition(
    name="Velocity TH",
    description=("This test case verifies the LSCA maximum speed threshold."),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class TestLSCAVelocityTH(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepVelocityTH]  # in this list all the needed test steps are included


def convert_dict_to_pandas(
    signal_summary: dict,
    table_remark="",
    table_title="",
):
    """Converts a dictionary to a Pandas DataFrame and creates an HTML table."""
    # Create a DataFrame from the dictionary
    evaluation_summary = pd.DataFrame(
        {
            "Interval": {key: key for key, val in signal_summary.items()},
            "Signal Evaluation": {key: val[0] for key, val in signal_summary.items()},
            "Summary": {key: val[1] for key, val in signal_summary.items()},
            "Verdict": {key: val[2] for key, val in signal_summary.items()},
        }
    )

    # Generate HTML table using build_html_table function
    return fh.build_html_table(evaluation_summary, table_remark, table_title)
