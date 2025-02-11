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
SIGNAL_DATA = "CHIPS_REGRESSION"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        CHIPS_CYL_FC_Y_P0_SIG_STATUS = "Status of CHIPS_CYL FC P0, Y"
        CHIPS_CYL_FC_Y_P1_SIG_STATUS = "Status of CHIPS_CYL FC P1, Y"
        CHIPS_CYL_FC_UV_P0_SIG_STATUS = "Status of CHIPS_CYL FC P0, UV"
        CHIPS_CYL_FC_UV_P1_SIG_STATUS = "Status of CHIPS_CYL FC P1, UV"

        CHIPS_CYL_LSC_Y_P0_SIG_STATUS = "Status of CHIPS_CYL LSC P0, Y"
        CHIPS_CYL_LSC_Y_P1_SIG_STATUS = "Status of CHIPS_CYL LSC P1, Y"
        CHIPS_CYL_LSC_UV_P0_SIG_STATUS = "Status of CHIPS_CYL LSC P0, UV"
        CHIPS_CYL_LSC_UV_P1_SIG_STATUS = "Status of CHIPS_CYL LSC P1, UV"

        CHIPS_CYL_RC_Y_P0_SIG_STATUS = "Status of CHIPS_CYL RC P0, Y"
        CHIPS_CYL_RC_Y_P1_SIG_STATUS = "Status of CHIPS_CYL RC P1, Y"
        CHIPS_CYL_RC_UV_P0_SIG_STATUS = "Status of CHIPS_CYL RC P0, UV"
        CHIPS_CYL_RC_UV_P1_SIG_STATUS = "Status of CHIPS_CYL RC P1, UV"

        CHIPS_CYL_RSC_Y_P0_SIG_STATUS = "Status of CHIPS_CYL RSC P0, Y"
        CHIPS_CYL_RSC_Y_P1_SIG_STATUS = "Status of CHIPS_CYL RSC P1, Y"
        CHIPS_CYL_RSC_UV_P0_SIG_STATUS = "Status of CHIPS_CYL RSC P0, UV"
        CHIPS_CYL_RSC_UV_P1_SIG_STATUS = "Status of CHIPS_CYL RSC P1, UV"

        CHIPS_WIDE_FC_P0_SIG_STATUS = "Status of CHIPS_WIDE FC, P0"
        CHIPS_WIDE_FC_P1_SIG_STATUS = "Status of CHIPS_WIDE FC, P1"
        CHIPS_WIDE_FC_P2_SIG_STATUS = "Status of CHIPS_WIDE FC, P2"
        CHIPS_WIDE_FC_P3_SIG_STATUS = "Status of CHIPS_WIDE FC, P3"
        CHIPS_WIDE_FC_P4_SIG_STATUS = "Status of CHIPS_WIDE FC, P4"

        CHIPS_WIDE_LSC_P0_SIG_STATUS = "Status of CHIPS_WIDE LSC, P0"
        CHIPS_WIDE_LSC_P1_SIG_STATUS = "Status of CHIPS_WIDE LSC, P1"
        CHIPS_WIDE_LSC_P2_SIG_STATUS = "Status of CHIPS_WIDE LSC, P2"
        CHIPS_WIDE_LSC_P3_SIG_STATUS = "Status of CHIPS_WIDE LSC, P3"
        CHIPS_WIDE_LSC_P4_SIG_STATUS = "Status of CHIPS_WIDE LSC, P4"

        CHIPS_WIDE_RC_P0_SIG_STATUS = "Status of CHIPS_WIDE RC, P0"
        CHIPS_WIDE_RC_P1_SIG_STATUS = "Status of CHIPS_WIDE RC, P1"
        CHIPS_WIDE_RC_P2_SIG_STATUS = "Status of CHIPS_WIDE RC, P2"
        CHIPS_WIDE_RC_P3_SIG_STATUS = "Status of CHIPS_WIDE RC, P3"
        CHIPS_WIDE_RC_P4_SIG_STATUS = "Status of CHIPS_WIDE RC, P4"

        CHIPS_WIDE_RSC_P0_SIG_STATUS = "Status of CHIPS_WIDE RSC, P0"
        CHIPS_WIDE_RSC_P1_SIG_STATUS = "Status of CHIPS_WIDE RSC, P1"
        CHIPS_WIDE_RSC_P2_SIG_STATUS = "Status of CHIPS_WIDE RSC, P2"
        CHIPS_WIDE_RSC_P3_SIG_STATUS = "Status of CHIPS_WIDE RSC, P3"
        CHIPS_WIDE_RSC_P4_SIG_STATUS = "Status of CHIPS_WIDE RSC, P4"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["SIM VFB"]  # list of roots from a measurement

        self._properties = {
            self.Columns.CHIPS_CYL_FC_Y_P0_SIG_STATUS: [
                ".chips_cyl_fc.pOddCylYP0Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_CYL_FC_Y_P1_SIG_STATUS: [
                ".chips_cyl_fc.pOddCylYP1Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_CYL_FC_UV_P0_SIG_STATUS: [
                ".chips_cyl_fc.pOddCylUVP0Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_CYL_FC_UV_P1_SIG_STATUS: [
                ".chips_cyl_fc.pOddCylUVP1Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_CYL_LSC_Y_P0_SIG_STATUS: [
                ".chips_cyl_lsc.pOddCylYP0Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_CYL_LSC_Y_P1_SIG_STATUS: [
                ".chips_cyl_lsc.pOddCylYP1Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_CYL_LSC_UV_P0_SIG_STATUS: [
                ".chips_cyl_lsc.pOddCylUVP0Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_CYL_LSC_UV_P1_SIG_STATUS: [
                ".chips_cyl_lsc.pOddCylUVP1Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_CYL_RC_Y_P0_SIG_STATUS: [
                ".chips_cyl_rc.pOddCylYP0Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_CYL_RC_Y_P1_SIG_STATUS: [
                ".chips_cyl_rc.pOddCylYP1Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_CYL_RC_UV_P0_SIG_STATUS: [
                ".chips_cyl_rc.pOddCylUVP0Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_CYL_RC_UV_P1_SIG_STATUS: [
                ".chips_cyl_rc.pOddCylUVP1Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_CYL_RSC_Y_P0_SIG_STATUS: [
                ".chips_cyl_rsc.pOddCylYP0Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_CYL_RSC_Y_P1_SIG_STATUS: [
                ".chips_cyl_rsc.pOddCylYP1Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_CYL_RSC_UV_P0_SIG_STATUS: [
                ".chips_cyl_rsc.pOddCylUVP0Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_CYL_RSC_UV_P1_SIG_STATUS: [
                ".chips_cyl_rsc.pOddCylUVP1Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_FC_P0_SIG_STATUS: [
                ".chips_wide_fc.pOddWideYP0Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_FC_P1_SIG_STATUS: [
                ".chips_wide_fc.pOddWideYP1Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_FC_P2_SIG_STATUS: [
                ".chips_wide_fc.pOddWideYP2Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_FC_P3_SIG_STATUS: [
                ".chips_wide_fc.pOddWideYP3Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_FC_P4_SIG_STATUS: [
                ".chips_wide_fc.pOddWideYP4Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_LSC_P0_SIG_STATUS: [
                ".chips_wide_lsc.pOddWideYP0Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_LSC_P1_SIG_STATUS: [
                ".chips_wide_lsc.pOddWideYP1Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_LSC_P2_SIG_STATUS: [
                ".chips_wide_lsc.pOddWideYP2Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_LSC_P3_SIG_STATUS: [
                ".chips_wide_lsc.pOddWideYP3Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_LSC_P4_SIG_STATUS: [
                ".chips_wide_lsc.pOddWideYP4Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_RC_P0_SIG_STATUS: [
                ".chips_wide_rc.pOddWideYP0Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_RC_P1_SIG_STATUS: [
                ".chips_wide_rc.pOddWideYP1Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_RC_P2_SIG_STATUS: [
                ".chips_wide_rc.pOddWideYP2Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_RC_P3_SIG_STATUS: [
                ".chips_wide_rc.pOddWideYP3Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_RC_P4_SIG_STATUS: [
                ".chips_wide_rc.pOddWideYP4Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_RSC_P0_SIG_STATUS: [
                ".chips_wide_rsc.pOddWideYP0Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_RSC_P1_SIG_STATUS: [
                ".chips_wide_rsc.pOddWideYP1Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_RSC_P2_SIG_STATUS: [
                ".chips_wide_rsc.pOddWideYP2Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_RSC_P3_SIG_STATUS: [
                ".chips_wide_rsc.pOddWideYP3Image_0.signalHeader.eSigStatus",
            ],
            self.Columns.CHIPS_WIDE_RSC_P4_SIG_STATUS: [
                ".chips_wide_rsc.pOddWideYP4Image_0.signalHeader.eSigStatus",
            ],
        }
        # TODO : to be removed when excel files won't be used anymore
        # self._extension_map.update({".xlsx": CSVReader})
        # self._extension_map.update({".csv": CSVReader})


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="CHIPS_CYL Regression test",  # this would be shown as a test step name in html report
    description=("Check that Sig Status for CHIPS_CYL component is not error"),
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(SIGNAL_DATA, Signals)
class TestStepCHIPS_CYL(ft_helper.BaseStepRregressionTS):
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
        self.plots = []
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
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            signals = self.readers[SIGNAL_DATA]
            signal_names = [
                signals_obj.Columns.CHIPS_CYL_FC_Y_P0_SIG_STATUS,
                signals_obj.Columns.CHIPS_CYL_FC_Y_P1_SIG_STATUS,
                signals_obj.Columns.CHIPS_CYL_FC_UV_P0_SIG_STATUS,
                signals_obj.Columns.CHIPS_CYL_FC_UV_P1_SIG_STATUS,
                signals_obj.Columns.CHIPS_CYL_LSC_Y_P0_SIG_STATUS,
                signals_obj.Columns.CHIPS_CYL_LSC_Y_P1_SIG_STATUS,
                signals_obj.Columns.CHIPS_CYL_LSC_UV_P0_SIG_STATUS,
                signals_obj.Columns.CHIPS_CYL_LSC_UV_P1_SIG_STATUS,
                signals_obj.Columns.CHIPS_CYL_RC_Y_P0_SIG_STATUS,
                signals_obj.Columns.CHIPS_CYL_RC_Y_P1_SIG_STATUS,
                signals_obj.Columns.CHIPS_CYL_RC_UV_P0_SIG_STATUS,
                signals_obj.Columns.CHIPS_CYL_RC_UV_P1_SIG_STATUS,
                signals_obj.Columns.CHIPS_CYL_RSC_Y_P0_SIG_STATUS,
                signals_obj.Columns.CHIPS_CYL_RSC_Y_P1_SIG_STATUS,
                signals_obj.Columns.CHIPS_CYL_RSC_UV_P0_SIG_STATUS,
                signals_obj.Columns.CHIPS_CYL_RSC_UV_P1_SIG_STATUS,
            ]

            remark = "Check eSigStatus for CHIPS CYLINDRICAL , stage 0."
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


@teststep_definition(
    step_number=2,
    name="CHIPS_WIDE Regression test",  # this would be shown as a test step name in html report
    description=("Check that Sig Status for CHIPS_WIDE component is not error"),
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(SIGNAL_DATA, Signals)
class TestStepCHIPS_WIDE(ft_helper.BaseStepRregressionTS):
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
        self.plots = []
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
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            signals = self.readers[SIGNAL_DATA]
            signal_names = [
                signals_obj.Columns.CHIPS_WIDE_FC_P0_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_FC_P1_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_FC_P2_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_FC_P3_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_FC_P4_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_LSC_P0_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_LSC_P1_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_LSC_P2_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_LSC_P3_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_LSC_P4_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_RC_P0_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_RC_P1_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_RC_P2_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_RC_P3_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_RC_P4_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_RSC_P0_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_RSC_P1_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_RSC_P2_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_RSC_P3_SIG_STATUS,
                signals_obj.Columns.CHIPS_WIDE_RSC_P4_SIG_STATUS,
            ]
            # self.plots = []
            remark = "Check eSigStatus for CHIPS WIDE , stage 0."
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
    name="CHIPS Regression Test",
    description=("Check Sig Status for CHIPS_CYL component"),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class CHIPS_Regression(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepCHIPS_CYL, TestStepCHIPS_WIDE]
