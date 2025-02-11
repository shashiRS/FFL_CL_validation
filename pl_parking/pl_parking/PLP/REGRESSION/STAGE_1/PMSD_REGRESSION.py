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
SIGNAL_DATA = "PMSD_REGRESSION"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        PMSD_FC_PARKING_LINES_SIG_STATUS = "Status of PMSD FC, Parking Lines"
        PMSD_FC_SLOTS_SIG_STATUS = "Status of PMSD FC, Slots"
        PMSD_FC_WHEEL_STOPPER_LINES_SIG_STATUS = "Status of PMSD FC, Wheel Stopper Lines"
        PMSD_LSC_PARKING_LINES_SIG_STATUS = "Status of PMSD LSC, Parking Lines"
        PMSD_LSC_SLOTS_SIG_STATUS = "Status of PMSD LSC, Slots"
        PMSD_LSC_WHEEL_STOPPER_LINES_SIG_STATUS = "Status of PMSD LSC, Wheel Stopper Lines"
        PMSD_RC_PARKING_LINES_SIG_STATUS = "Status of PMSD RC, Parking Lines"
        PMSD_RC_SLOTS_SIG_STATUS = "Status of PMSD RC, Slots"
        PMSD_RC_WHEEL_STOPPER_LINES_SIG_STATUS = "Status of PMSD RC, Wheel Stopper Lines"
        PMSD_RSC_PARKING_LINES_SIG_STATUS = "Status of PMSD RSC, Parking Lines"
        PMSD_RSC_SLOTS_SIG_STATUS = "Status of PMSD RSC, Slots"
        PMSD_RSC_WHEEL_STOPPER_LINES_SIG_STATUS = "Status of PMSD RSC, Wheel Stopper Lines"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()
        """
        """
        self._root = ["SIM VFB"]  # list of roots from a measurement
        signal_list = [
            ".PMSDINSTANCE_fc.PedestrianCrossings",
            ".PMSDINSTANCE_fc.PedestrianCrossings",
            ".PMSDINSTANCE_fc.PedestrianCrossings",
            ".PMSDINSTANCE_fc.Slots",
            ".PMSDINSTANCE_fc.StopLines",
            ".PMSDINSTANCE_fc.WheelLockerList",
            ".PMSDINSTANCE_fc.WheelStopperLines",
            ".PMSDINSTANCE_lsc.ParkingLines",
            ".PMSDINSTANCE_lsc.PedestrianCrossings",
            ".PMSDINSTANCE_lsc.Slots",
            ".PMSDINSTANCE_lsc.StopLines",
            ".PMSDINSTANCE_lsc.WheelLockerList",
            ".PMSDINSTANCE_lsc.WheelStopperLines",
            ".PMSDINSTANCE_rc.ParkingLines",
            ".PMSDINSTANCE_rc.PedestrianCrossings",
            ".PMSDINSTANCE_rc.Slots",
            ".PMSDINSTANCE_rc.StopLines",
            ".PMSDINSTANCE_rc.WheelLockerList",
            ".PMSDINSTANCE_rc.WheelStopperLines",
            ".PMSDINSTANCE_rsc.ParkingLines",
            ".PMSDINSTANCE_rsc.PedestrianCrossings",
            ".PMSDINSTANCE_rsc.Slots",
            ".PMSDINSTANCE_rsc.StopLines",
            ".PMSDINSTANCE_rsc.WheelLockerList",
            ".PMSDINSTANCE_rsc.WheelStopperLines",
        ]
        signal_dict = {x.split(".")[-1]: [f"{x}.sSigHeader.eSigStatus"] for x in signal_list}
        self._properties = {
            self.Columns.PMSD_FC_PARKING_LINES_SIG_STATUS: [
                ".PMSDINSTANCE_fc.ParkingLines.sSigHeader.eSigStatus",
            ],
        }
        self._properties.update(signal_dict)
        # TODO : to be removed when excel files won't be used anymore


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="PMSD Regression test",  # this would be shown as a test step name in html report
    description=("Check that Sig Status for PMSD component is not error"),
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(SIGNAL_DATA, Signals)
class TestStepPMSD(ft_helper.BaseStepRregressionTS):
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
    name="PMSD Regression Test",
    description=("Check Sig Status for PMSD component"),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class PMSDRegression(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepPMSD]
