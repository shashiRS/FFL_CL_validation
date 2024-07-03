#!/usr/bin/env python3
"""SWRT CNC SGF StaticObjectsSematicPointCloud testcases"""
import logging

from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
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

import plotly.graph_objects as go

import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import CemSignals, CustomTeststepReport, rep
from pl_parking.PLP.CEM.inputs.input_CemSgfReader import SGFReader

SIGNAL_DATA = "StaticObjectsFromSVCSemanticPointCloud"
example_obj = CemSignals()


# @specification
# Test script will:
# Read the follow data from the whole recording:
# 1. CarPC.EM_Thread.SefOutputAgp.u_Used_Elements. (N)
# 2. N must be greater than 0 for at least one timestamp
# @script StaticObjectsFromUSSSensor
@teststep_definition(
    step_number=1,
    name="Static Objects From SVC Semantic Point Cloud",
    description="This test case checks in case SGF has output when only SVC semantic point cloud input is received.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepStaticObjectsFromSVCSemanticPointCloud(TestStep):
    """TestStep for analyzing static objects detected from SVC Semantic Point Cloud, utilizing a custom report."""

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
        plot_titles, plots, remarks = rep([], 3)

        # Load signals
        reader = self.readers[SIGNAL_DATA].signals
        input_reader = SGFReader(reader)
        static_object_df = input_reader.data

        test_result = (
            fc.PASS if not static_object_df.numPolygons.empty and any(static_object_df.numPolygons > 0.0) else fc.FAIL
        )

        # Add a summary plot with signals behaviour along the rec
        fig = go.Figure(
            data=[
                go.Scatter(
                    x=static_object_df.SGF_timestamp, y=static_object_df.numPolygons, mode="lines", name="Num Polygons"
                )
            ]
        )

        plot_titles.append("SGF Num Polygons")
        plots.append(fig)
        remarks.append("")

        # Report result status
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


@verifies("1522133, 1522135, 1522136")
@testcase_definition(
    name="SWRT_CNC_SGF_StaticObjectsFromSVCSemanticPointCloud",
    description="This test case checks in case SGF has output when only SVC semantic point cloud input is received.",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class StaticObjectsFromSVCSemanticPointCloud(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepStaticObjectsFromSVCSemanticPointCloud,
        ]
