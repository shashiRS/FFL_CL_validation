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
SIGNAL_DATA = "PARAM_HANDLER_REGRESSION"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        PARAM_HANDLERStatusPort = "PARAM_HANDLERStatusPort"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["SIM VFB"]  # list of roots from a measurement

        signal_list = [
            ".PARAMETER_HANDLER_1.FC_bdParamsPort",
            ".PARAMETER_HANDLER_1.FC_cameraIntrinsics",
            ".PARAMETER_HANDLER_1.FC_chipsParameters",
            ".PARAMETER_HANDLER_1.FC_grappaParametersPort",
            ".PARAMETER_HANDLER_1.FC_ofcParamsPort",
            ".PARAMETER_HANDLER_1.FC_pmsdParamsPort",
            ".PARAMETER_HANDLER_1.FC_sppParamsPort",
            ".PARAMETER_HANDLER_1.FC_tppParamsPort",
            ".PARAMETER_HANDLER_1.LSC_EOLCalibrationExtrinsicsISO",
            ".PARAMETER_HANDLER_1.LSC_bdParamsPort",
            ".PARAMETER_HANDLER_1.LSC_cameraIntrinsics",
            ".PARAMETER_HANDLER_1.LSC_chipsParameters",
            ".PARAMETER_HANDLER_1.LSC_grappaParametersPort",
            ".PARAMETER_HANDLER_1.LSC_ofcParamsPort",
            ".PARAMETER_HANDLER_1.LSC_pmsdParamsPort",
            ".PARAMETER_HANDLER_1.LSC_sppParamsPort",
            ".PARAMETER_HANDLER_1.LSC_tppParamsPort",
            ".PARAMETER_HANDLER_1.RC_EOLCalibrationExtrinsicsISO",
            ".PARAMETER_HANDLER_1.RC_bdParamsPort",
            ".PARAMETER_HANDLER_1.RC_cameraIntrinsics",
            ".PARAMETER_HANDLER_1.RC_chipsParameters",
            ".PARAMETER_HANDLER_1.RC_grappaParametersPort",
            ".PARAMETER_HANDLER_1.RC_ofcParamsPort",
            ".PARAMETER_HANDLER_1.RC_pmsdParamsPort",
            ".PARAMETER_HANDLER_1.RC_sppParamsPort",
            ".PARAMETER_HANDLER_1.RC_tppParamsPort",
            ".PARAMETER_HANDLER_1.RSC_EOLCalibrationExtrinsicsISO",
            ".PARAMETER_HANDLER_1.RSC_bdParamsPort",
            ".PARAMETER_HANDLER_1.RSC_cameraIntrinsics",
            ".PARAMETER_HANDLER_1.RSC_chipsParameters",
            ".PARAMETER_HANDLER_1.RSC_grappaParametersPort",
            ".PARAMETER_HANDLER_1.RSC_ofcParamsPort",
            ".PARAMETER_HANDLER_1.RSC_pmsdParamsPort",
            ".PARAMETER_HANDLER_1.RSC_sppParamsPort",
            ".PARAMETER_HANDLER_1.RSC_tppParamsPort",
            ".PARAMETER_HANDLER_1.apParkingOutDataPortWrite",
            ".PARAMETER_HANDLER_1.artNvmDataPortWrite",
            ".PARAMETER_HANDLER_1.artParamsPort",
            ".PARAMETER_HANDLER_1.drivenPathDataPortWrite",
            ".PARAMETER_HANDLER_1.fc_DrvWarnSMCore_ParamsPort",
            ".PARAMETER_HANDLER_1.fc_DrvWarnSM_ParamsPort",
            ".PARAMETER_HANDLER_1.fc_MFHMIH_ParamsPort",
            ".PARAMETER_HANDLER_1.fc_MF_LSCA_ParamsPort",
            ".PARAMETER_HANDLER_1.fc_MF_Manager_ParamsPort",
            ".PARAMETER_HANDLER_1.fc_MF_ToneHandler_ParamsPort",
            ".PARAMETER_HANDLER_1.fc_MF_WhlProtectProc_ParamsPort",
            ".PARAMETER_HANDLER_1.fc_PARKSM_Core_ParamsPort",
            ".PARAMETER_HANDLER_1.fc_PARKSM_ParamsPort",
            ".PARAMETER_HANDLER_1.fc_PDCP_ParamsPort",
            ".PARAMETER_HANDLER_1.fc_TCE_ParamsPort",
            ".PARAMETER_HANDLER_1.fc_TRJCTL_ParamsPort",
            ".PARAMETER_HANDLER_1.fc_TRJPLA_ParamsPort",
            ".PARAMETER_HANDLER_1.fc_VEDODO_ParamsPort",
            ".PARAMETER_HANDLER_1.lvmdParams",
            ".PARAMETER_HANDLER_1.pfsParams",
            ".PARAMETER_HANDLER_1.sgfParams",
            ".PARAMETER_HANDLER_1.siParamsPort",
            ".PARAMETER_HANDLER_1.sys_Func_ParamsPort",
            ".PARAMETER_HANDLER_1.tpfParams",
            ".PARAMETER_HANDLER_1.ultrasonicCalibration",
            ".PARAMETER_HANDLER_1.vehicle_ParamsPort",
        ]
        signal_dict = {x.split(".")[-1]: [f"{x}.sSigHeader.eSigStatus"] for x in signal_list}

        self._properties = {
            self.Columns.PARAM_HANDLERStatusPort: [
                ".PARAMETER_HANDLER_1.FC_EOLCalibrationExtrinsicsISO.sSigHeader.eSigStatus",
            ],
        }
        self._properties.update(signal_dict)


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="MF PARAM_HANDLER Regression test",  # this would be shown as a test step name in html report
    description=("Check that Sig Status for MF PARAM_HANDLER component is not error"),
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(SIGNAL_DATA, Signals)
class TestStepMF_PARAM_HANDLER(ft_helper.BaseStepRregressionTS):
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
    name="MF PARAM_HANDLER Regression Test",
    description=("Check Sig Status for PARAM_HANDLER component"),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class PARAM_HANDLER_Regression(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepMF_PARAM_HANDLER]
