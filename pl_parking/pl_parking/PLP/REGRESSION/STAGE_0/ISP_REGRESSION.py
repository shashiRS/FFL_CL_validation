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

__author__ = "Dana Frunza"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
SIGNAL_DATA = "ISP_REGRESSION"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        ISP_FC_Y_SIG_STATUS = "Status of ISP FC, Y"
        ISP_FC_UV_SIG_STATUS = "Status of ISP FC, UV"
        ISP_LSC_Y_SIG_STATUS = "Status of ISP LSC, Y"
        ISP_LSC_UV_SIG_STATUS = "Status of ISP LSC, UV"
        ISP_RC_Y_SIG_STATUS = "Status of ISP RC, Y"
        ISP_RC_UV_SIG_STATUS = "Status of ISP RC, UV"
        ISP_RSC_Y_SIG_STATUS = "Status of ISP RSC, Y"
        ISP_RSC_UV_SIG_STATUS = "Status of ISP RSC, UV"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["SIM VFB"]  # list of roots from a measurement
        self._properties = {
            self.Columns.ISP_FC_Y_SIG_STATUS: [
                ".isp_fc.pImageYOdd.signalHeader.eSigStatus",
            ],
            self.Columns.ISP_FC_UV_SIG_STATUS: [
                ".isp_fc.pImageUVOdd.signalHeader.eSigStatus",
            ],
            self.Columns.ISP_LSC_Y_SIG_STATUS: [
                ".isp_lsc.pImageYOdd.signalHeader.eSigStatus",
            ],
            self.Columns.ISP_LSC_UV_SIG_STATUS: [
                ".isp_lsc.pImageUVOdd.signalHeader.eSigStatus",
            ],
            self.Columns.ISP_RC_Y_SIG_STATUS: [
                ".isp_rc.pImageYOdd.signalHeader.eSigStatus",
            ],
            self.Columns.ISP_RC_UV_SIG_STATUS: [
                ".isp_rc.pImageUVOdd.signalHeader.eSigStatus",
            ],
            self.Columns.ISP_RSC_Y_SIG_STATUS: [
                ".isp_rsc.pImageYOdd.signalHeader.eSigStatus",
            ],
            self.Columns.ISP_RSC_UV_SIG_STATUS: [
                ".isp_rsc.pImageUVOdd.signalHeader.eSigStatus",
            ],
        }
        # TODO : to be removed when excel files won't be used anymore


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="ISP Regression test",  # this would be shown as a test step name in html report
    description=("Check that Sig Status for ISP component is not error"),
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(SIGNAL_DATA, Signals)
class TestStepISP(ft_helper.BaseStepRregressionTS):
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
        self.plots = []

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
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            signals = self.readers[SIGNAL_DATA]
            signal_names = [
                signals_obj.Columns.ISP_FC_Y_SIG_STATUS,
                signals_obj.Columns.ISP_FC_UV_SIG_STATUS,
                signals_obj.Columns.ISP_LSC_Y_SIG_STATUS,
                signals_obj.Columns.ISP_LSC_UV_SIG_STATUS,
                signals_obj.Columns.ISP_RC_Y_SIG_STATUS,
                signals_obj.Columns.ISP_RC_UV_SIG_STATUS,
                signals_obj.Columns.ISP_RSC_Y_SIG_STATUS,
                signals_obj.Columns.ISP_RSC_UV_SIG_STATUS,
            ]

            remark = "Check eSigStatus for ISP, stage 0."
            super().process(signals=signals, signal_names=signal_names, signals_obj=signals_obj, remark=remark)
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
    name="ISP Regression Test",
    description=("Check Sig Status for ISP component"),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class ISPRegression(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepISP]
