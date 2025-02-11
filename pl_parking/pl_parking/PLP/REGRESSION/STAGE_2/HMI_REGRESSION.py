"""Example functional test"""  # this is a required docstring

"""import libraries"""
import logging
import os
import sys

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
"""imports from tsf core"""
from tsf.core.results import TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.io.signals import SignalDefinition

"""imports from current repo"""
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.REGRESSION.ft_helper as ft_helper
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport

__author__ = "Pinzariu George Claudiu <uif94738>"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
SIGNAL_DATA = "HMI_REGRESSION"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        apUserInteractionPort = "apUserInteractionPort"
        headUnitVisualizationPort = "headUnitVisualizationPort"
        hmiInputPort = "hmiInputPort"
        lvmdUserInteractionPort = "lvmdUserInteractionPort"
        mfHmiHDebugPort = "mfHmiHDebugPort"
        pdcUserInteractionPort = "pdcUserInteractionPort"
        remoteVisualizationPort = "remoteVisualizationPort"
        surroundViewRequestPort = "surroundViewRequestPort"
        uiManagerOutputPortToUIHelper = "uiManagerOutputPortToUIHelper"
        userDefinedSlotPort = "userDefinedSlotPort"
        visuInputPort = "visuInputPort"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["SIM VFB"]  # list of roots from a measurement

        self._properties = {
            self.Columns.apUserInteractionPort: [
                ".HMIH1.apUserInteractionPort.sSigHeader.eSigStatus",
            ],
            self.Columns.headUnitVisualizationPort: [
                ".HMIH1.headUnitVisualizationPort.sSigHeader.eSigStatus",
            ],
            self.Columns.hmiInputPort: [
                ".HMIH1.hmiInputPort.sSigHeader.eSigStatus",
            ],
            self.Columns.lvmdUserInteractionPort: [
                ".HMIH1.lvmdUserInteractionPort.sSigHeader.eSigStatus",
            ],
            self.Columns.mfHmiHDebugPort: [
                ".HMIH1.mfHmiHDebugPort.sSigHeader.eSigStatus",
            ],
            self.Columns.pdcUserInteractionPort: [
                ".HMIH1.pdcUserInteractionPort.sSigHeader.eSigStatus",
            ],
            self.Columns.remoteVisualizationPort: [
                ".HMIH1.remoteVisualizationPort.sSigHeader.eSigStatus",
            ],
            self.Columns.surroundViewRequestPort: [
                ".HMIH1.surroundViewRequestPort.sSigHeader.eSigStatus",
            ],
            self.Columns.uiManagerOutputPortToUIHelper: [
                ".HMIH1.uiManagerOutputPortToUIHelper.sSigHeader.eSigStatus",
            ],
            self.Columns.userDefinedSlotPort: [
                ".HMIH1.userDefinedSlotPort.sSigHeader.eSigStatus",
            ],
            self.Columns.visuInputPort: [
                ".HMIH1.visuInputPort.sSigHeader.eSigStatus",
            ],
        }
        # TODO : to be removed when excel files won't be used anymore


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="HMI Regression tests.",  # this would be shown as a test step name in html report
    description=("Check that Sig Status for HMI component is not error"),
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(SIGNAL_DATA, Signals)
class TestStepHmih1(ft_helper.BaseStepRregressionTS):
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
        """  # required docstring
        try:
            _log.debug("Starting processing...")
            # Update the details from the results page with the needed information
            # All the information from self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
            self.result.details.update(
                {
                    "Plots": [],
                    "Result_ratio": None,
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )

            signals = self.readers[SIGNAL_DATA]
            signal_names = [x for x in signals_obj._properties.keys()]
            self.plots = []
            super().process(signals=signals, signal_names=signal_names, signals_obj=signals_obj)
            additional_results_dict = {
                "Verdict": {"value": self.test_result.title(), "color": fh.get_color(self.test_result)},
            }

            # Add the plots in html page
            for plot in self.plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
            self.result.details["Additional_results"] = additional_results_dict

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


# Define the test case definition. This will include the name of the test case and a description of the test.
@testcase_definition(
    name="HMI Regression Test",
    description=("Check Sig Status for HMI component"),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class HMI_Regression(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepHmih1]
