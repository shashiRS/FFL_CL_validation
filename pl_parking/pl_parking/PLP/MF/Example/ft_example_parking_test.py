"""Example functional test"""  # this is a required docstring

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

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "MF_EXAMPLE"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        SCREEN_NU = "Head Unit Visualization Screen"
        VELOCITY = "Velocity"
        APSTATE = "AP State"
        CARAX = "Car_ax"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.SCREEN_NU: [
                ".headUnitVisualizationPort.screen_nu",  # tail of signal which would be matched with a root string
            ],
            self.Columns.VELOCITY: [
                "Vhcl.v",  # also the full version of signal can be included
                ".Conti_Veh_CAN.VehVelocity.VehVelocityExt",  # a signal can have defined different version of paths for different type of measurements
            ],
            self.Columns.TIME: [
                "Time",
                "Another version of signal",
            ],
            self.Columns.APSTATE: [
                ".planningCtrlPort.apStates",
            ],
            self.Columns.CARAX: [
                "Car.ax",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Functional test 1",  # this would be shown as a test step name in html report
    description=(
        "This is an example of a test step for a functional test(usually have a boolean expected result).\
            Check that after Planning control port is 3 and the speed does not exceed the accepted value."
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepFtExample1(TestStep):
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
        # signal_name = signals_obj._properties
        # Make a constant with the reader for signals:
        self.test_result = fc.INPUT_MISSING  # Result
        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_summary = {}  # Initializing the dictionary with data for final evaluation table

        try:
            signals = self.readers[ALIAS].signals  # for bsig OR ergs
        except Exception:
            signals = self.readers[ALIAS]  # for rrec
            signals[Signals.Columns.TIMESTAMP] = signals.index

        ap_time = signals[Signals.Columns.TIME]  # the info for specific siganl are extracted from the bigger data frame
        ap_state = signals[Signals.Columns.APSTATE]  # take into consideration you need to use df methods
        velocity = signals[Signals.Columns.VELOCITY]

        # For this example, we will take as a threshold the moment when the value of ap_stat signal it's == Active
        # use enumerate instead of 'for in range(len(x))'

        # for idx, val in enumerate(ap_state):
        #     if val == constants.GeneralConstants.AP_AVG_ACTIVE_IN:
        #         time_threshold = idx
        #         break
        if np.any(ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN):
            time_threshold = np.argmax(ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN)
        # create an evaluation text for the moment when the test is passed
        evaluation = " ".join(
            f"The evaluation of {Signals.Columns.VELOCITY} is PASSED, with values <"
            f" {round(constants.GeneralConstants.V_MAX_L3, 3)} m/s.".split()
        )

        if time_threshold is not None:
            eval_cond = True  # set the evaluation condition as TRUE
            velocity_mask = velocity.iloc[time_threshold:] != constants.GeneralConstants.V_MAX_L3

            if any(velocity_mask):
                idx = velocity_mask.index[velocity_mask][0]
                # create an evaluation text for the moment when the test is failed
                evaluation = " ".join(
                    f"The evaluation of {Signals.Columns.VELOCITY} is FAILED because \
                    it has the max value greater than max accepted value \
                    {round(constants.GeneralConstants.V_MAX_L3, 3)} m/s \
                    at timestamp {round(ap_time.loc[idx], 3)} s..".split()
                )
                eval_cond = False  # set the evaluation condition as False
            # set the verdict of the test step
            if eval_cond:
                self.test_result = fc.PASS
            else:
                self.test_result = fc.FAIL
        else:
            # create an evaluation text for the moment when the threshold it's not found,set test_result to NOT_ASSESSED
            self.test_result = fc.NOT_ASSESSED
            evaluation = " ".join(
                f"Evaluation not possible, the trigger value {constants.GeneralConstants.AP_AVG_ACTIVE_IN} for"
                f" {Signals.Columns.APSTATE} was never found.".split()
            )
        # you have to correlate the signal with the evaluation text in the table
        signal_summary[Signals.Columns.VELOCITY] = evaluation
        remark = " ".join(
            f"Check that after .planningCtrlPort.apStates == {constants.GeneralConstants.AP_AVG_ACTIVE_IN}, the \
            speed does not exceed the accepted value.".split()
        )
        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plots.append(self.sig_sum)

        if self.test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif self.test_result == fc.FAIL:
            self.result.measured_result = FALSE
        else:
            self.result.measured_result = DATA_NOK
        if self.result.measured_result in [FALSE, DATA_NOK] or bool(constants.GeneralConstants.ACTIVATE_PLOTS):
            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(go.Scatter(x=ap_time, y=ap_state, mode="lines", name=Signals.Columns.APSTATE))
            fig.add_trace(go.Scatter(x=ap_time, y=velocity, mode="lines", name=Signals.Columns.VELOCITY))
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)


@teststep_definition(
    step_number=2,
    name="Functional test 2",  # this would be shown as a test step name in html report
    description=(
        "Check that after Planning control port is equal to 3, the maximum acceleration and speed does not             "
        "    exceed accepted values."
    ),
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepFtExample2(TestStep):
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

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        try:
            signals = self.readers[ALIAS].signals  # for bsig OR ergs
        except Exception:
            signals = self.readers[ALIAS]  # for rrec
            signals[Signals.Columns.TIMESTAMP] = signals.index

        ap_time = signals[Signals.Columns.TIME]
        ap_state = signals[Signals.Columns.APSTATE]
        car_ax = signals[Signals.Columns.CARAX]

        self.test_result = fc.INPUT_MISSING  # Result
        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        # "Ap.planningCtrlPort.apStates"[idx] == constants.ConstantsAupCore.THRESHOLD_T3
        t3 = None
        signal_summary = {}

        if np.any(ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN):
            t3 = np.argmax(ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN)
        evaluation1 = " ".join(
            f"The evaluation of {signals_obj._properties[Signals.Columns.CARAX]} is PASSED with values <            "
            f"                     {constants.ConstantsAupCore.LONG_ACC_EGO_MAX} m/s^2.".split()
        )
        eval_cond = True
        if t3 is not None:
            car_ax_mask = car_ax.iloc[t3:] >= constants.ConstantsAupCore.LONG_ACC_EGO_MAX

            if any(car_ax_mask):
                idx = car_ax_mask[car_ax_mask].idxmin()

                evaluation1 = " ".join(
                    f"The evaluation of {signals_obj._properties[Signals.Columns.CARAX]} is FAILED with a value"
                    f" >=                         {constants.ConstantsAupCore.LONG_ACC_EGO_MAX} m/s^2 at timestamp "
                    f"                       {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond = False

            if eval_cond:
                self.test_result = fc.PASS
            else:
                self.test_result = fc.FAIL
        else:
            evaluation1 = " ".join(
                "Evaluation not possible, the trigger value AP_AVG_ACTIVE_IN(3) for                            "
                f" {signals_obj._properties[Signals.Columns.APSTATE]} was never found.".split()
            )
            self.result.measured_result = DATA_NOK
            self.test_result = fc.NOT_ASSESSED
        signal_summary[Signals.Columns.CARAX] = evaluation1

        remark = " ".join(
            "Checks that after AP.planningCtrlPort.apStates == 3 (AP_AVG_ACTIVE_IN), the                 "
            "        maximum acceleration and speed does not                                                         "
            " exceed the accepted value".split()
        )
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plots.append(self.sig_sum)

        if self.test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif self.test_result == fc.FAIL:
            self.result.measured_result = FALSE
        else:
            self.result.measured_result = DATA_NOK

        if self.result.measured_result in [FALSE, DATA_NOK] or bool(constants.GeneralConstants.ACTIVATE_PLOTS):
            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(), y=car_ax.values.tolist(), mode="lines", name=Signals.Columns.CARAX
                )
            )

            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            # self.result.details["Plots"].append(
            #     self.fig.to_html(full_html=False, include_plotlyjs=False))
            plots.append(self.fig)

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)


# Define the test case definition. This will include the name of the test case and a description of the test.
@testcase_definition(
    name="Test case example",
    description=("This an example of test case with two test steps."),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class TestExample(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepFtExample1, TestStepFtExample2]  # in this list all the needed test steps are included
