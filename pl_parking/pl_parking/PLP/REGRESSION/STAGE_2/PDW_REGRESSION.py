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

# import port_status

__author__ = "Radu Irina Maria"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
SIGNAL_DATA = "PDW_REGRESSION"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        # PDW_TRACE_DATA_STATUS = "Status of PDW trace data Signal"
        PDW_DEBUG_SIG_STATUS = "Status of PDW Debug Signal"
        PDW_DRIVING_TUBE_STATUS = "Status of PDW driving tube Signal"
        PDW_SECTORS_SIG_STATUS = "Status of PDW sectors Signal"
        PDW_PROC_TO_LOGIC_SIG_STATUS = "Status of PDW proc to logic Signal"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["SIM VFB"]  # list of roots from a measurement

        self._properties = {
            # self.Columns.PDW_TRACE_DATA_STATUS: [
            #     ".PdCp1.m_traceData.sigHeader.eSigStatus",
            # ],
            self.Columns.PDW_DEBUG_SIG_STATUS: [
                ".PdCp1.pdcpDebugPort.sSigHeader.eSigStatus",
            ],
            self.Columns.PDW_DRIVING_TUBE_STATUS: [
                ".PdCp1.pdcpDrivingTubePort.sSigHeader.eSigStatus",
            ],
            self.Columns.PDW_SECTORS_SIG_STATUS: [
                ".PdCp1.pdcpSectorsPort.sSigHeader.eSigStatus",
            ],
            self.Columns.PDW_PROC_TO_LOGIC_SIG_STATUS: [
                ".PdCp1.procToLogicPort.sSigHeader.eSigStatus",
            ],
        }
        # TODO : to be removed when excel files won't be used anymore


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="MF PDW Regression test",  # this would be shown as a test step name in html report
    description=("Check that Sig Status for MF PDW component is not error"),
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(SIGNAL_DATA, Signals)
class TestStepMF_PDW(ft_helper.BaseStepRregressionTS):
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
            signal_names = [
                # signals_obj.Columns.PDW_TRACE_DATA_STATUS,
                signals_obj.Columns.PDW_DEBUG_SIG_STATUS,
                signals_obj.Columns.PDW_DRIVING_TUBE_STATUS,
                signals_obj.Columns.PDW_SECTORS_SIG_STATUS,
                signals_obj.Columns.PDW_PROC_TO_LOGIC_SIG_STATUS,
            ]
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
    name="MF PDW Regression Test",
    description=("Check Sig Status for PDW component"),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class PDW_Regression(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepMF_PDW]
