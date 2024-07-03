"""Parking Marker Accuracy KPI Test."""

import logging

from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_side_load,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

TRC_ROOT = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

import typing

import numpy as np
import plotly.graph_objects as go
from tsf.core.common import PathSpecification
from tsf.io.sideload import JsonSideLoad

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import AssociationConstants
from pl_parking.PLP.CEM.ft_pcl_helper import FtPclHelper
from pl_parking.PLP.CEM.inputs.input_CemPclReader import PclDelimiterReader
from pl_parking.PLP.CEM.inputs.input_PmdReader import PMDCamera, PMDReader

SIGNAL_DATA = "PFS_PCL_Accuracy"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS PCL Accuracy",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
@register_side_load(
    alias="JsonGt",
    side_load=JsonSideLoad,  # type of side loaders
    path_spec=PathSpecification(
        folder=os.path.join(TSF_BASE, "data", "CEM_json_gt"),
        extension=".json",
    ),
    # Absolute path for the sideload.
)
class TestStepFtPCLAccuracy(TestStep):
    """Test Parking Marker Accuracy"""

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
        pcl_data = PclDelimiterReader(reader).convert_to_class()
        pmd_data = PMDReader(reader).convert_to_class()
        gt_data = self.side_load["JsonGt"]
        park_marker_gt = FtPclHelper.get_pcl_from_json_gt(gt_data)

        all_pcl_ground_truth_distances: typing.List[float] = []
        number_of_associated_pcl: typing.Tuple[int, int] = []

        for _, pcl_timeframe in enumerate(pcl_data):
            if len(pcl_timeframe.pcl_delimiter_array) > 0:
                gt_with_closest_timestamp = park_marker_gt.get(
                    min(park_marker_gt.keys(), key=lambda k: abs(k - pcl_timeframe.timestamp))
                )
                association, _ = FtPclHelper.associate_pcl_to_ground_truth(
                    pcl_timeframe.pcl_delimiter_array,
                    gt_with_closest_timestamp,
                    AssociationConstants.PCL_ASSOCIATION_RADIUS,
                )
                pcl_ground_truth_distances = []
                for pcl, ground_truth in association:
                    if ground_truth is not None:
                        dist = FtPclHelper.is_pcl_pcl_association_valid(
                            pcl, ground_truth, AssociationConstants.PCL_ASSOCIATION_RADIUS
                        )[1:3]
                        pcl_ground_truth_distances.append(dist[0])
                        pcl_ground_truth_distances.append(dist[1])

                all_pcl_ground_truth_distances += pcl_ground_truth_distances
                number_of_associated_pcl.append(
                    (
                        pcl_timeframe.timestamp,
                        len([ground_truth for _, ground_truth in association if ground_truth is not None]),
                    )
                )

        all_pmd_ground_truth_distances: typing.List[float] = []
        all_pmd_ground_truth_distances_per_camera: typing.Dict[PMDCamera, typing.List[float]] = dict()
        number_of_associated_pmd: typing.Dict[PMDCamera, typing.List[typing.Tuple[int, int]]] = dict()
        for camera, timeframe_list in pmd_data.items():
            all_pmd_ground_truth_distances_per_camera[camera] = []
            number_of_associated_pmd[camera] = []

            for pmd_timeframe in timeframe_list:
                if len(pmd_timeframe.pmd_lines) > 0:
                    gt_with_closest_timestamp = park_marker_gt.get(
                        min(park_marker_gt.keys(), key=lambda k: abs(k - pcl_timeframe.timestamp))
                    )
                    association, _ = FtPclHelper.associate_pmd_to_ground_truth(
                        pmd_timeframe.pmd_lines, gt_with_closest_timestamp, AssociationConstants.PCL_ASSOCIATION_RADIUS
                    )
                    pmd_ground_truth_distances = []
                    for pmd, ground_truth in association:
                        if ground_truth is not None:
                            dist = FtPclHelper.is_pcl_pmd_association_valid(
                                ground_truth, pmd, AssociationConstants.PCL_ASSOCIATION_RADIUS
                            )[1:3]
                            pmd_ground_truth_distances.append(dist[0])
                            pmd_ground_truth_distances.append(dist[1])

                    all_pmd_ground_truth_distances += pmd_ground_truth_distances
                    all_pmd_ground_truth_distances_per_camera[camera] += pmd_ground_truth_distances
                    number_of_associated_pmd[camera].append(
                        (
                            pmd_timeframe.timestamp,
                            len([ground_truth for _, ground_truth in association if ground_truth is not None]),
                        )
                    )

        avg_pcl_distance = np.mean(all_pcl_ground_truth_distances)
        avg_pmd_distance = np.mean(all_pmd_ground_truth_distances)

        if avg_pmd_distance >= avg_pcl_distance:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1304537"],
            fc.TESTCASE_ID: ["37915"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test case verifies that, in average EnvironmentFusion doesn't provide worse position for "
                "the parking markers than each sensor separately. "
            ],
            fc.TEST_RESULT: [test_result],
        }

        self.result.details["Additional_results"] = result_df

        # Average False Positive ration table
        source_dist = ["CEM", "PMD", "PMD Front", "PMD Rear", "PMD Right", "PMD Left"]
        values_dist = [
            avg_pcl_distance,
            avg_pmd_distance,
            np.mean(all_pmd_ground_truth_distances_per_camera[PMDCamera.FRONT]),
            np.mean(all_pmd_ground_truth_distances_per_camera[PMDCamera.REAR]),
            np.mean(all_pmd_ground_truth_distances_per_camera[PMDCamera.RIGHT]),
            np.mean(all_pmd_ground_truth_distances_per_camera[PMDCamera.LEFT]),
        ]
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Source", "Average Distance from Ground Truth"]),
                    cells=dict(values=[source_dist, values_dist]),
                )
            ]
        )
        plot_titles.append("Average Distance from Ground Truth")
        plots.append(fig)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=[timeframe.timestamp for timeframe in pcl_data],
                y=[len(timeframe.pcl_delimiter_array) for timeframe in pcl_data],
                mode="lines",
                name="Number of CEM PCL",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[timeframe for timeframe, _ in number_of_associated_pcl],
                y=[nbr_associated_lines for _, nbr_associated_lines in number_of_associated_pcl],
                mode="lines",
                name="Number of associated CEM PCL",
            )
        )
        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

        for camera, timeframe_list in pmd_data.items():
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=[timeframe.timestamp for timeframe in timeframe_list[1:]],
                    y=[len(timeframe.pmd_lines) for timeframe in timeframe_list[1:]],
                    mode="lines",
                    name=f"{camera._name_} camera number of PMD",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=[timeframe for timeframe, _ in number_of_associated_pmd[camera]],
                    y=[nbr_associated_lines for _, nbr_associated_lines in number_of_associated_pmd[camera]],
                    mode="lines",
                    name=f"{camera._name_} camera number of associated PMD",
                )
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1530459"],
            fc.TESTCASE_ID: ["38840"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test case verifies that, in average CEM doesn't provide worse position for the parking markers"
                "than each input separately."
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


@verifies("1530459")
@testcase_definition(
    name="SWKPI_CNC_PFS_ParkingMarkerAccuracy",
    description="This test case verifies that, in average CEM doesn't provide worse position for the parking markers"
    "than each input separately.",
)
class FtPCLAccuracy(TestCase):
    """Test Parking Marker Accuracy"""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPCLAccuracy]
