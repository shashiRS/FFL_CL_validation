"""Parking Marker Indie ROI Test."""

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

TRC_ROOT = os.path.abspath(os.path.join(__file__, "", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import ConstantsCem, ConstantsCemInput
from pl_parking.PLP.CEM.ft_pcl_helper import FtPclHelper
from pl_parking.PLP.CEM.inputs.input_CemPclReader import PclDelimiterReader

SIGNAL_DATA = "PFS_PCL_Field_of_View"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS PCL Field of View",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPCLFieldOfView(TestStep):
    """Parking Marker Indie ROI Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step"""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarsk based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        input_reader = PclDelimiterReader(reader)
        delimiter_data = input_reader.convert_to_class()

        data_df = input_reader.data.as_plain_df
        data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in data_df.columns]
        pcl_type = data_df.loc[:, data_df.columns.str.startswith("delimiterType")]

        if ConstantsCemInput.PCLEnum in pcl_type.values:
            rows = []
            failed = 0
            for time_frame in delimiter_data:
                for PCL in time_frame.pcl_delimiter_array:
                    closes_point = FtPclHelper.get_closest_point(PCL)
                    if (
                        abs(closes_point.x) > ConstantsCem.AP_G_DES_MAP_RANGE_M / 2
                        or abs(closes_point.y) > ConstantsCem.AP_G_DES_MAP_RANGE_M / 2
                    ):
                        failed += 1
                        values = [
                            [time_frame.timestamp],
                            [PCL.delimiter_id],
                            [closes_point.x],
                            [closes_point.y],
                            [ConstantsCem.AP_G_DES_MAP_RANGE_M],
                        ]
                        rows.append(values)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                header = ["Timestamp", "DelimiterID", "x", "y", "LIMIT_OUTPUT_FIELD_OF_VIEW"]
                fig = go.Figure(data=[go.Table(header=dict(values=header), cells=dict(values=values))])
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")
            else:
                test_result = fc.PASS

        else:
            test_result = fc.INPUT_MISSING

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1530457"],
            fc.TESTCASE_ID: ["38836"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test case checks if CEM's output contains only parking markers inside the limited field of view."
            ],
            fc.TEST_RESULT: [test_result],
        }

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


@verifies("1530457")
@testcase_definition(
    name="SWRT_CNC_PFS_ParkingMarkerInsideROI",
    description="This test case checks if CEM's output contains only parking markers inside the limited field of view.",
)
class FtPCLFieldOfView(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPCLFieldOfView]
