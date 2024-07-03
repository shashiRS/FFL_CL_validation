"""Delete Further Parking Markers Test."""

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


import typing

import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import ConstantsCem, ConstantsCemInput
from pl_parking.PLP.CEM.ft_pcl_helper import FtPclHelper
from pl_parking.PLP.CEM.inputs.input_CemPclReader import PCLDelimiter, PclDelimiterReader
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import VedodoReader

SIGNAL_DATA = "PFS_PCL_Furthest_Line"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS PCL Furthest Line",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPCLFurthestLineDeleted(TestStep):
    """Delete Further Parking Markers Test."""

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
        inputReader = PclDelimiterReader(reader)
        vedodo_buffer = VedodoReader(reader).convert_to_class()
        delimiterData = inputReader.convert_to_class()
        nbrTimeframes = len(delimiterData)

        data_df = inputReader.data.as_plain_df
        data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in data_df.columns]
        pcl_type = data_df.loc[:, data_df.columns.str.startswith("delimiterType")]

        if ConstantsCemInput.PCLEnum in pcl_type.values:
            failed = 0
            for i in range(nbrTimeframes - 1):
                prevTimeframe = delimiterData[i]
                curTimeframe = delimiterData[i + 1]

                relative_motion = vedodo_buffer.calc_relative_motion(prevTimeframe.timestamp, curTimeframe.timestamp)

                missingPcls: typing.List[PCLDelimiter] = []

                if len(prevTimeframe.pcl_delimiter_array) > 0 and len(curTimeframe.pcl_delimiter_array) > 0:
                    if len(curTimeframe.pcl_delimiter_array) == ConstantsCem.PCL_MAX_NUM_MARKERS:
                        missingPcls = FtPclHelper.find_missing_pcl_line_ids(prevTimeframe, curTimeframe)

                if len(missingPcls) > 0:
                    _, furthestPclDistance = FtPclHelper.get_furthest_line(curTimeframe)

                    for missingLine in missingPcls:
                        transformed_line = FtPclHelper.transform_pcl(missingLine, relative_motion)
                        if FtPclHelper.distance_pcl_vehicle(transformed_line) < furthestPclDistance:
                            failed += 1

            if failed:
                test_result = fc.FAIL
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Number of failed deleted markers"]), cells=dict(values=[[failed]])
                        )
                    ]
                )
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")
            else:
                test_result = fc.PASS

        else:
            test_result = fc.INPUT_MISSING

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1530456"],
            fc.TESTCASE_ID: ["38882"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "In case the mentioned limit is reached, the furthest parking marking shall be deleted"
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


@verifies("1530456")
@testcase_definition(
    name="SWRT_CNC_PFS_DeleteFurthestParkingMarkers",
    description="In case the mentioned limit is reached, the furthest parking marking shall be deleted",
)
class FtPCLFurthestLineDeleted(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPCLFurthestLineDeleted]
