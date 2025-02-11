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
SIGNAL_DATA = "CEM_R4_REGRESSION"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"

        CEM_LSMO_EGO_MOTION_OUTPUT_STATUS = "Status of CEM LSMO ego motion output"
        CEM_LSMO_ODOMETRY_STATUS = "Status of CEM LSMO odometry"
        CEM_PFS_PEDESTRIAN_CROSSING_OUTPUT_STATUS = "Status of CEM PFS pedestrian crossing output"
        CEM_LSMO_FWP_COMPONENT_RESPONSE_STATUS = "Status of CEM LSMO fwp component response"

        CEM_PFS_PCL_OUTPUT_STATUS = "Status of CEM PFS PCL output"
        CEM_PFS_PSD_OUTPUT_STATUS = "Status of CEM PFS PSD output"

        # CEM_PFS_FWP_COMPONENT_RESPONSE_STATUS = "Status of CEM PFS fwp component response"

        CEM_SGF_OUTPUT_STATUS = "Status of CEM SGF output"
        # CEM_SGF_FWP_COMPONENT_RESPONSE_STATUS = "Status of CEM SGF fwp component response"
        CEM_PFS_m_WsOutput = "m_WsOutput"
        CEM_PFS_m_StopLineOutput = "m_StopLineOutput"
        # CEM_TPF_FWP_COMPONENT_RESPONSE_STATUS = "Status of CEM TPF fwp component response"
        CEM_PFS_m_WheelLockerOutput = "m_WheelLockerOutput"
        CEM_TPF_TP_OBJECT_LIST_STATUS = "Status of CEM TPF tp object list"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["SIM VFB"]  # list of roots from a measurement

        self._properties = {
            self.Columns.CEM_LSMO_EGO_MOTION_OUTPUT_STATUS: [
                ".CEM200_LSMO.m_EgoMotionOutput.sSigHeader.eSigStatus",
            ],
            self.Columns.CEM_LSMO_ODOMETRY_STATUS: [
                ".CEM200_LSMO.m_Odometry.sSigHeader.eSigStatus",
            ],
            self.Columns.CEM_LSMO_FWP_COMPONENT_RESPONSE_STATUS: [
                ".CEM200_LSMO.m_fwpComponentResponse.sigHeader.eSigStatus",
            ],
            # self.Columns.CEM_PFS_FWP_COMPONENT_RESPONSE_STATUS: [
            #     ".CEM200_PFS.m_fwpComponentResponse.sigHeader.eSigStatus",
            # ],
            self.Columns.CEM_PFS_m_StopLineOutput: [
                ".CEM200_PFS.m_StopLineOutput.sigHeader.eSigStatus",
            ],
            self.Columns.CEM_PFS_m_WsOutput: [
                ".CEM200_PFS.m_WsOutput.sigHeader.eSigStatus",
            ],
            self.Columns.CEM_PFS_m_WheelLockerOutput: [
                ".CEM200_PFS.m_WheelLockerOutput.sigHeader.eSigStatus",
            ],
            self.Columns.CEM_PFS_PCL_OUTPUT_STATUS: [
                ".CEM200_PFS.m_PclOutput.sSigHeader.eSigStatus",
            ],
            self.Columns.CEM_PFS_PEDESTRIAN_CROSSING_OUTPUT_STATUS: [
                ".CEM200_PFS.m_PedestrianCrossingOutput.sSigHeader.eSigStatus",
            ],
            self.Columns.CEM_PFS_PSD_OUTPUT_STATUS: [
                ".CEM200_PFS.m_PsdOutput.sSigHeader.eSigStatus",
            ],
            self.Columns.CEM_SGF_OUTPUT_STATUS: [
                ".CEM200_SGF.m_SgfOutput.sSigHeader.eSigStatus",
            ],
            # self.Columns.CEM_SGF_FWP_COMPONENT_RESPONSE_STATUS: [
            #     ".CEM200_SGF.m_fwpComponentResponse.sigHeader.eSigStatus",
            # ],
            self.Columns.CEM_TPF_TP_OBJECT_LIST_STATUS: [
                ".CEM200_TPF2.m_tpObjectList.sSigHeader.eSigStatus",
            ],
            # self.Columns.CEM_TPF_FWP_COMPONENT_RESPONSE_STATUS: [
            #     ".CEM200_TPF2.m_fwpComponentResponse.sigHeader.eSigStatus",
            # ],
        }


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="CEM LSMO Regression test",  # this would be shown as a test step name in html report
    description=("Check that Sig Status for CEM LSMO component is not error"),
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(SIGNAL_DATA, Signals)
class TestStepCEM_LSMO(ft_helper.BaseStepRregressionTS):
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
                signals_obj.Columns.CEM_LSMO_EGO_MOTION_OUTPUT_STATUS,
                signals_obj.Columns.CEM_LSMO_ODOMETRY_STATUS,
                # signals_obj.Columns.CEM_LSMO_ODO_ESTIMATION_BUFFER_STATUS,
                # signals_obj.Columns.CEM_LSMO_ODO_ESTIMATION_STATUS,
                # signals_obj.Columns.CEM_LSMO_TRACE_DATA_STATUS,
                # signals_obj.Columns.CEM_LSMO_SYNC_REF_STATUS,
                # signals_obj.Columns.CEM_LSMO_BASE_CTRL_DATA_STATUS,
                # signals_obj.Columns.CEM_LSMO_SIG_M_PLSMO_INPUT_LIST_STATUS,
                # signals_obj.Columns.CEM_LSMO_CONTROL_TRIGGER_STATUS,
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


@teststep_definition(
    step_number=2,
    name="CEM PFS Regression test",  # this would be shown as a test step name in html report
    description=("Check that Sig Status for CEM PFS component is not error"),
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(SIGNAL_DATA, Signals)
class TestStepCEM_PFS(ft_helper.BaseStepRregressionTS):
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
                # signals_obj.Columns.CEM_PFS_FWP_COMPONENT_RESPONSE_STATUS,
                signals_obj.Columns.CEM_PFS_PCL_OUTPUT_STATUS,
                signals_obj.Columns.CEM_PFS_PEDESTRIAN_CROSSING_OUTPUT_STATUS,
                signals_obj.Columns.CEM_PFS_PSD_OUTPUT_STATUS,
                signals_obj.Columns.CEM_PFS_m_StopLineOutput,
                signals_obj.Columns.CEM_PFS_m_WheelLockerOutput,
                signals_obj.Columns.CEM_PFS_m_WsOutput,
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


@teststep_definition(
    step_number=3,
    name="CEM SGF Regression test",  # this would be shown as a test step name in html report
    description=("Check that Sig Status for CEM SGF component is not error"),
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(SIGNAL_DATA, Signals)
class TestStepCEM_SGF(ft_helper.BaseStepRregressionTS):
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
                signals_obj.Columns.CEM_SGF_OUTPUT_STATUS,
                # signals_obj.Columns.CEM_SGF_FWP_COMPONENT_RESPONSE_STATUS,
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


# @teststep_definition(
#     step_number=4,
#     name="CEM SVC Regression test",  # this would be shown as a test step name in html report
#     description=(
#         "Check that Sig Status for CEM SVC component is not error"
#     ),
#     expected_result=BooleanResult(
#         TRUE
#     ),  # this expected result would be compared with measured_result and give a verdict
# )
# @register_signals(SIGNAL_DATA, Signals)
# class TestStepCEM_SVC(ft_helper.BaseStepRregressionTS):
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
#                 signals_obj.Columns.CEM_SVC_FWP_COMPONENT_RESPONSE_STATUS,
#                 signals_obj.Columns.CEM_SVC_POINT_LIST_STATUS,
#                 signals_obj.Columns.CEM_SVC_POLYLINE_LIST_STATUS,
#                 signals_obj.Columns.CEM_SVC_TRACE_DATA_STATUS,
#             ]
#             self.plots = []
#             super().process(signals=signals,signal_names=signal_names,signals_obj=signals_obj)
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


@teststep_definition(
    step_number=4,
    name="CEM TPF Regression test",  # this would be shown as a test step name in html report
    description=("Check that Sig Status for CEM TPF component is not error"),
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(SIGNAL_DATA, Signals)
class TestStepCEM_TPF(ft_helper.BaseStepRregressionTS):
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
                # signals_obj.Columns.CEM_TPF_FWP_COMPONENT_RESPONSE_STATUS,
                signals_obj.Columns.CEM_TPF_TP_OBJECT_LIST_STATUS,
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


# @teststep_definition(
#     step_number=5,
#     name="CEM USS Regression test",  # this would be shown as a test step name in html report
#     description=(
#         "Check that Sig Status for CEM USS component is not error"
#     ),
#     expected_result=BooleanResult(
#         TRUE
#     ),  # this expected result would be compared with measured_result and give a verdict
# )
# @register_signals(SIGNAL_DATA, Signals)
# class TestStepCEM_USS(ft_helper.BaseStepRregressionTS):
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
#                 signals_obj.Columns.CEM_USS_OUTPUT_STATUS,
#                 signals_obj.Columns.CEM_USS_FWP_COMPONENT_RESPONSE_STATUS,
#                 signals_obj.Columns.CEM_USS_TRACE_DATA_STATUS,
#             ]
#             self.plots = []
#             super().process(signals=signals,signal_names=signal_names,signals_obj=signals_obj)
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
    name="CEM Regression Test",
    description=("Check Sig Status for CEM component"),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class CEM_Regression(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            TestStepCEM_LSMO,
            TestStepCEM_PFS,
            TestStepCEM_SGF,
            # TestStepCEM_SVC,
            TestStepCEM_TPF,
            # TestStepCEM_USS
        ]
