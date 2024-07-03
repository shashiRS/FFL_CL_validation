"""Example KPI"""  # this is a required docstring

"""import libraries"""
import logging
import os
import sys

import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
"""imports from tsf core"""
from tsf.core.results import DATA_NOK, FALSE, Result
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.io.signals import SignalDefinition

"""imports from current repo"""
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
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=2,
    name="KPI",  # this would be shown as a test step name in html report
    description=(
        "This is an example of a test step for a kpi test(usually have a numeric expected result).\
            and checks what the mean of all measured max value of velocity signal is < 2.7[m/s] "  # this would be shown as a test step description in html report
    ),
    expected_result=f"< {constants.GeneralConstants.V_MAX_L3} m/s",
    # OR
    # expected_result=ExpectedResult(
    #     operator=RelationOperator.LESS,
    #     numerator=constants.GeneralConstants.V_MAX_L3,
    #     unit="m/s",
    #     aggregate_function=AggregateFunction.MEAN,  # the AggregateFunction class have detailed info of how the overall result is calculated
    # ),  # this expected result would be compared with mean of measured_results and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepKpiExample(TestStep):
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
        # Make a constant with the reader for signals:
        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        # data nok verdicts are not evaluated in mean function
        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_summary = {}  # Initializing the dictionary with data for final evaluation table
        # Read measurement
        try:
            signals = self.readers[ALIAS].signals  # for bsig
        except Exception:
            signals = self.readers[ALIAS]  # for rrec
            signals[Signals.Columns.TIMESTAMP] = (
                signals.index
            )  # Make a dataframe(df) with all signals extracted from Signals class
        ap_time = signals[Signals.Columns.TIME]  # the info for specific signal are extracted from the bigger data frame
        velocity = signals[Signals.Columns.VELOCITY]

        # create an evaluation text for the moment when the test is passed
        evaluation = " ".join(f"The max value of {Signals.Columns.VELOCITY} is {max(velocity)} m/s.".split())

        # set the verdict of the test step

        self.result.measured_result = Result(
            max(velocity)
        )  # OR self.result.measured_result = Result.from_string(f"{max(velocity)}")

        # you have to correlate the signal with the evaluation text in the table
        signal_summary[Signals.Columns.VELOCITY] = evaluation
        remark = " ".join("Show the max value from velocity signal.".split())
        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plots.append(self.sig_sum)

        if self.result.measured_result in [FALSE, DATA_NOK] or bool(constants.GeneralConstants.ACTIVATE_PLOTS):
            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(go.Scatter(x=ap_time, y=velocity, mode="lines", name=Signals.Columns.VELOCITY))
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plots.append(fig)

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)


# Define the test case definition. This will include the name of the test case and a description of the test.
@testcase_definition(
    name="Test case example",
    description=("This an example of test case with one test step."),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class TestExample(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepKpiExample]  # in this list all the needed test steps are included
