"""Output Latency Compensation Test."""

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

import pandas as pd
import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.inputs.input_CemSlotReader import SlotReader
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import VedodoReader

SIGNAL_DATA = "PFS_Latency_Compensation"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM-PFS Latency Compensation",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPFSOutputAtT7(TestStep):
    """Output Latency Compensation Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step"""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarsk based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)
        data = pd.DataFrame()

        reader = self.readers[SIGNAL_DATA].signals
        input_reader = SlotReader(reader)
        data["timestamp"] = input_reader.data["CemSlot_timestamp"]
        vedodo_buffer = VedodoReader(reader).convert_to_class()

        # Check if data has been provided to continue with the validation
        if len(data.timestamp) or len(vedodo_buffer.buffer):
            pfs_df = data.reset_index()
            t7_df = pd.DataFrame(vedodo_buffer.buffer)

            # Check that every timestamp that is present in the PFS output is matching the one provided by T7.
            if pfs_df.timestamp.equals(t7_df.timestamp):
                test_result = fc.PASS
            # Otherwise test will fail
            else:
                # Create a detailed table to show timeframe failing and the corresponding values
                test_result = fc.FAIL
                matching_data = pd.DataFrame(pfs_df.timestamp == t7_df.timestamp)
                failed_cycles = matching_data.loc[~matching_data.timestamp].index
                pfs_failing = pfs_df.filter(items=failed_cycles, axis=0).timestamp
                t7_failing = t7_df.filter(items=failed_cycles, axis=0).timestamp
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Cycle count", "PFS output", "T7 timestamp"]),
                            cells=dict(values=[failed_cycles, pfs_failing, t7_failing]),
                        )
                    ]
                )
                plot_titles.append("Test Fail report for not matching timestamps")
                plots.append(fig)
                remarks.append("")

            # Add a summary plot with signals behaviour along the rrec
            fig = go.Figure(
                data=[
                    go.Scatter(
                        x=pfs_df.index, y=(pfs_df.timestamp - t7_df.timestamp) / 1e3, mode="lines", name="Offset"
                    )
                ]
            )

            plot_titles.append("PFS timestamp offset ms")
            plots.append(fig)
            remarks.append("")

        else:
            test_result = fc.INPUT_MISSING

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1530454"],
            fc.TESTCASE_ID: ["39027"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                """This test case checks if PFS provides its signals in the Vehicle coordinate system at T7"""
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


@verifies("1530454")
@testcase_definition(
    name="SWRT_CNC_PFS_OutputLatencyCompensation",
    description="This test case checks if PFS provides its signals in the Vehicle coordinate system at T7",
)
class FtPFSOutputAtT7(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPFSOutputAtT7]
