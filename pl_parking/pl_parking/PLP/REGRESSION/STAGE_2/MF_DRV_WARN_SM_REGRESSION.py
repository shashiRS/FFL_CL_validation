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
SIGNAL_DATA = "mf_drv_warn_sm_REGRESSION"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        MF_DRV_WARN_SM_APP_TO_CORE_SM_STATUS = (
            "Status of Driving Warning State Machine app to core state machine signal"
        )
        MF_DRV_WARN_DEBUG_STATUS = "Status of Driving Warning State Machine debug signal"
        MF_DRV_WARN_STATUS = "Status of Driving Warning State Machine signal"
        MF_DRV_WARN_LOGIC_TO_PROC_STATUS = "Status of Driving Warning State Machine logic to proc signal"

        # drvWarnCoreDebugPort = "drvWarnCoreDebugPort"
        drvWarnCoreStatusPort = "drvWarnCoreStatusPort"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["SIM VFB"]  # list of roots from a measurement

        self._properties = {
            self.Columns.MF_DRV_WARN_SM_APP_TO_CORE_SM_STATUS: [
                ".MFDrvWarnSM1.appToCoreSMPort.sSigHeader.eSigStatus",
            ],
            self.Columns.MF_DRV_WARN_DEBUG_STATUS: [
                ".MFDrvWarnSM1.drvWarnDebugPort.sSigHeader.eSigStatus",
            ],
            self.Columns.MF_DRV_WARN_STATUS: [
                ".MFDrvWarnSM1.drvWarnStatusPort.sSigHeader.eSigStatus",
            ],
            self.Columns.MF_DRV_WARN_LOGIC_TO_PROC_STATUS: [
                ".MFDrvWarnSM1.logicToProcPort.sSigHeader.eSigStatus",
            ],
            # self.Columns.drvWarnCoreDebugPort: [
            #     ".MFDrvWarnSMCore1.drvWarnCoreDebugPort.sigHeader.eSigStatus",
            # ],
            self.Columns.drvWarnCoreStatusPort: [
                ".MFDrvWarnSMCore1.drvWarnCoreStatusPort.sSigHeader.eSigStatus",
            ],
            # self.Columns.MF_DRV_WARN_CORE_STATUS: [
            #     ".MFDrvWarnSMCore1.drvWarnCoreStatusPort.sSigHeader.eSigStatus",
            # ],
            # self.Columns.MF_DRV_WARN_CORE_TRACE_DATA_STATUS: [
            #     ".MFDrvWarnSMCore1.m_traceData.sigHeader.eSigStatus",
            # ],
        }
        # TODO : to be removed when excel files won't be used anymore


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="MF Driving warning state machine Regression test",  # this would be shown as a test step name in html report
    description=("Check that Sig Status for MF Driving warning state machine component is not error"),
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(SIGNAL_DATA, Signals)
class TestStep_DrvWarnSM(ft_helper.BaseStepRregressionTS):
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


# @teststep_definition(
#     step_number=2,
#     name="MF Driving warning state machine Core Regression test",  # this would be shown as a test step name in html report
#     description=("Check that Sig Status for MF Driving warning state machine Core component is not error"),
#     expected_result=BooleanResult(
#         TRUE
#     ),  # this expected result would be compared with measured_result and give a verdict
# )
# @register_signals(SIGNAL_DATA, Signals)
# class TestStep_DrvWarnSMCORE(ft_helper.BaseStepRregressionTS):
#     """testcase that can be tested by a simple pass/fail test.
#     This is a required docstring in which you can add more details about what you verify in test step
#     Objective
#     ---------
#     ...
#     Detail
#     ------
#     ...
#     """

#     custom_report = MfCustomTeststepReport  # Specific overview

#     def __init__(self):
#         """Initialize the teststep."""
#         super().__init__()

#     def process(self, **kwargs):
#         """
#         The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
#         evaluation results.
#         """  # required docstring
#         try:
#             _log.debug("Starting processing...")
#             # Update the details from the results page with the needed information
#             # All the information from self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
#             self.result.details.update(
#                 {
#                     "Plots": [],
#                     "file_name": os.path.basename(self.artifacts[0].file_path),
#                 }
#             )
#             signals = self.readers[SIGNAL_DATA]
#             signal_names = [
#                 signals_obj.Columns.MF_DRV_WARN_SM_CORE_DEBUG_STATUS,
#                 signals_obj.Columns.MF_DRV_WARN_CORE_STATUS,
#                 signals_obj.Columns.MF_DRV_WARN_CORE_TRACE_DATA_STATUS,
#             ]
#             self.plots = []
#             super().process(signals=signals, signal_names=signal_names, signals_obj=signals_obj)
#             additional_results_dict = {
#                 "Verdict": {"value": self.test_result.title(), "color": fh.get_color(self.test_result)},
#             }

#             # Add the plots in html page
#             for plot in self.plots:
#                 if "plotly.graph_objs._figure.Figure" in str(type(plot)):
#                     self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
#                 else:
#                     self.result.details["Plots"].append(plot)
#             self.result.details["Additional_results"] = additional_results_dict

#         except Exception:
#             exc_type, exc_obj, exc_tb = sys.exc_info()
#             fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
#             print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


# Define the test case definition. This will include the name of the test case and a description of the test.
@testcase_definition(
    name="MF Driving warning state machine Regression Test",
    description=("Check Sig Status for Driving warning state machine component"),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class DrvWarnSM_Regression(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStep_DrvWarnSM]
