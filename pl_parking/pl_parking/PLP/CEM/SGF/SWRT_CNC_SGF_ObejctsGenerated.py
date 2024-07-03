"""SWRT CNC SGF ObejctsGenerated testcases"""

# from tsf.io.signals import SignalDefinition
# from tsf.core.results import FALSE, TRUE, BooleanResult

import logging

from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

import sys

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, CustomTeststepReport, rep
from pl_parking.PLP.CEM.inputs.input_CemSgfReader import SGFReader

SIGNAL_DATA = "StaticObjectsGenerated"
example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="SWRT_CNC_SGF_StaticObjectsGenerated",
    description="SGF shall provide a list of Static Objects describing the static obstacles around the vehicle.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepStaticObjectsGenerated(TestStep):
    """TestStep for evaluating the generation of static objects, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # Define variables
        test_result = fc.NOT_ASSESSED
        # data = pd.DataFrame()
        plot_titles, plots, remarks = rep([], 3)

        # Load signals
        reader = self.readers[SIGNAL_DATA].signals
        input_reader = SGFReader(reader)
        # static_object_df = input_reader.data

        if input_reader.number_of_objects > 0:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1522103"],
            fc.TESTCASE_ID: ["51917"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test checks that SGF provides a list of Static Objects describing the static obstacles around the vehicle."
            ],
            fc.TEST_RESULT: [test_result],
        }
        # Mandatory for creating the plot:
        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = result_df


@verifies("1522103")
@testcase_definition(
    name="SWRT_CNC_SGF_StaticObjectsGenerated",
    description=(
        "Verify that SGF shall provide a list of Static Objects describing the static obstacles around the vehicle."
    ),
    doors_url="",
)
class StaticObjectsGenerated(TestCase):
    """Static Objects Generated test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepStaticObjectsGenerated,
        ]
