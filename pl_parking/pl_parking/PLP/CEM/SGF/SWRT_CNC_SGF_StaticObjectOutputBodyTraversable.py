"""Example functional test"""  # this is a required docstring

"""import libraries"""
import logging
import os
import sys

import numpy as np
import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
"""imports from tsf core"""
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)

"""imports from current repo"""
import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    rep,
)
from pl_parking.PLP.CEM.inputs.input_CemSgfReader import SGFReader
from pl_parking.PLP.CEM.SGF.ft_helper import SGFSignals

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "MF_EXAMPLE_2"
sgf_obj = SGFSignals()


"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="SWRT_CNC_SGF_StaticObjectOutputBodyTraversable",  # this would be shown as a test step name in html report
    description=(
        "This test case checks that SGF provides the confidence for Static Objects being body traversable and this confidence is between 0 and 1."
    ),  # this would be shown as a test step description in html report
    doors_url="https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_or7dMJpREe6OHr4fEH59Xg#action=com.ibm.rqm.planning.home.actionDispatcher&subAction=viewTestCase&id=38892",
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, SGFSignals)
class TestStepFtSGFOutputBodyTraversable(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    This test case checks that SGF provides the confidence for Static Objects being body traversable and this confidence is between 0 and 1.

    Detail
    ------

    The script will:

        1. Load the whole required data for testing
        1.1. MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.numberOfObjects. (N)
        1.2. MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.objects[k].heightConfidences.bodyTraversable, where k=0..N-1.

        2. Check if MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.objects[k].heightConfidences.bodyTraversable exists and is between 0 and 1.
    """

    custom_report = MfCustomTeststepReport  # Specific overview

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    #
    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # Define variables
        test_result = fc.NOT_ASSESSED
        plot_titles, plots, remarks = rep([], 3)

        # Load signals
        reader = self.readers[ALIAS].signals
        input_reader = SGFReader(reader)
        static_object_df = input_reader.data

        if static_object_df.filter(regex="highConfidence_polygon").empty:
            test_result = fc.INPUT_MISSING
        else:
            # Erase cells with undefined values to avoid messing up the calculations.
            for _, row in static_object_df.iterrows():
                for i in range(int(row["numPolygons"]), input_reader.max_num_polygons):
                    row["highConfidence_polygon", i] = np.nan

            max_holds = all(
                static_object_df["highConfidence_polygon", i].max(skipna=True) <= 1
                for i in range(input_reader.max_num_polygons)
            )

            min_holds = all(
                static_object_df["highConfidence_polygon", i].min(skipna=True) >= 0
                for i in range(input_reader.max_num_polygons)
            )

            test_result = fc.PASS if max_holds and min_holds else fc.FAIL

            min_confidence = [
                static_object_df["highConfidence_polygon", i].min(skipna=True)
                for i in range(input_reader.max_num_polygons)
            ]
            max_confidence = [
                static_object_df["highConfidence_polygon", i].max(skipna=True)
                for i in range(input_reader.max_num_polygons)
            ]

            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(values=["Min Confidence", "Max Confidence"]),
                        cells=dict(values=[min_confidence, max_confidence]),
                    )
                ]
            )
            plot_titles.append("Confidence range by Object")
            plots.append(fig)
            remarks.append("")

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


# Define the test case definition. This will include the name of the test case and a description of the test.
@testcase_definition(
    name="SWRT_CNC_SGF_StaticObjectOutputBodyTraversable",
    description="This test checks that a confidence for each Static Object "
    "being body traversable is provided and is between 0 and 1.",
    doors_url="https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_or7dMJpREe6OHr4fEH59Xg#action=com.ibm.rqm.planning.home.actionDispatcher&subAction=viewTestCase&id=38892",
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class FtSGFOutputBodyTraversable(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepFtSGFOutputBodyTraversable]  # in this list all the needed test steps are included
