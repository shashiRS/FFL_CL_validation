"""WheelStopper Accuracy KPI Test."""

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
from pl_parking.PLP.CEM.ft_ws_helper import FtWsHelper
from pl_parking.PLP.CEM.inputs.input_CemPclReader import PclDelimiterReader
from pl_parking.PLP.CEM.inputs.input_CemWsReader import WSDetectionReader
from pl_parking.PLP.CEM.inputs.input_PmdReader import PMDCamera

SIGNAL_DATA = "PFS_WS_Accuracy"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS WS Accuracy",
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
class TestStepFtWSAccuracy(TestStep):
    """WheelStopper Accuracy Test."""

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
        gt_data = self.side_load["JsonGT"]
        ws_gt = FtWsHelper.get_ws_from_json_gt(gt_data)
        pcl_data = PclDelimiterReader(reader).convert_to_class()
        ws_detection_data = WSDetectionReader(reader).convert_to_class()

        all_cem_ws_ground_truth_distances: typing.List[float] = []
        number_of_associated_cem_ws: typing.List[typing.Tuple[int, int]] = []

        for _, pcl_timeframe in enumerate(pcl_data):
            timeframe_nbr_associated_ws = 0

            if len(pcl_timeframe.wheel_stopper_array) > 0:
                gt_with_closest_timestamp = ws_gt.get(min(ws_gt.keys(), key=lambda k: abs(k - pcl_timeframe.timestamp)))
                association, _ = FtPclHelper.associate_pcl_to_ground_truth(
                    pcl_timeframe.wheel_stopper_array,
                    gt_with_closest_timestamp,
                    AssociationConstants.WS_ASSOCIATION_RADIUS,
                )
                timeframe_nbr_associated_ws = len(
                    [ground_truth for _, ground_truth in association if ground_truth is not None]
                )

                ws_ground_truth_distances = [
                    FtPclHelper.is_pcl_pcl_association_valid(
                        ws, ground_truth, AssociationConstants.WS_ASSOCIATION_RADIUS
                    )[1]
                    for ws, ground_truth in association
                    if ground_truth is not None
                ]

                all_cem_ws_ground_truth_distances += ws_ground_truth_distances

            number_of_associated_cem_ws.append((pcl_timeframe.timestamp, timeframe_nbr_associated_ws))

        all_ws_detection_ground_truth_distances: typing.List[float] = []
        all_ws_detection_ground_truth_distances_per_camera: typing.Dict[PMDCamera, typing.List[float]] = dict()
        number_of_associated_ws_detection: typing.Dict[PMDCamera, typing.List[typing.Tuple[int, int]]] = dict()
        for camera, timeframe_list in ws_detection_data.items():
            all_ws_detection_ground_truth_distances_per_camera[camera] = []
            number_of_associated_ws_detection[camera] = []

            for ws_timeframe in timeframe_list:
                timeframe_nbr_association = 0
                if len(ws_timeframe.pmd_lines) > 0:
                    gt_with_closest_timestamp = ws_gt.get(
                        min(ws_gt.keys(), key=lambda k: abs(k - pcl_timeframe.timestamp))
                    )
                    association, _ = FtPclHelper.associate_pmd_to_ground_truth(
                        ws_timeframe.pmd_lines, gt_with_closest_timestamp, AssociationConstants.WS_ASSOCIATION_RADIUS
                    )

                    ws_ground_truth_distances = [
                        FtPclHelper.is_pcl_pmd_association_valid(
                            ground_truth, ws, AssociationConstants.WS_ASSOCIATION_RADIUS
                        )[1]
                        for ws, ground_truth in association
                        if ground_truth is not None
                    ]

                    all_ws_detection_ground_truth_distances += ws_ground_truth_distances
                    all_ws_detection_ground_truth_distances_per_camera[camera] += ws_ground_truth_distances
                    timeframe_nbr_association = len(
                        [ground_truth for _, ground_truth in association if ground_truth is not None]
                    )

                number_of_associated_ws_detection[camera].append((ws_timeframe.timestamp, timeframe_nbr_association))

        avg_cem_ws_distance = np.mean(all_cem_ws_ground_truth_distances)
        avg_ws_detection_distance = np.mean(all_ws_detection_ground_truth_distances)

        if avg_ws_detection_distance >= avg_cem_ws_distance:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        # Average False Positive ratio table
        source_dist = [
            "CEM",
            "WS Detection",
            "WS Detection Front",
            "WS Detection Rear",
            "WS Detection Right",
            "WS Detection Left",
        ]
        values_dist = [
            avg_cem_ws_distance,
            avg_ws_detection_distance,
            np.mean(all_ws_detection_ground_truth_distances_per_camera[PMDCamera.FRONT]),
            np.mean(all_ws_detection_ground_truth_distances_per_camera[PMDCamera.REAR]),
            np.mean(all_ws_detection_ground_truth_distances_per_camera[PMDCamera.RIGHT]),
            np.mean(all_ws_detection_ground_truth_distances_per_camera[PMDCamera.LEFT]),
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
                y=[len(timeframe.wheel_stopper_array) for timeframe in pcl_data],
                mode="lines",
                name="Number of CEM WS",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[timeframe for timeframe, _ in number_of_associated_cem_ws],
                y=[nbr_associated_lines for _, nbr_associated_lines in number_of_associated_cem_ws],
                mode="lines",
                name="Number of associated CEM WS to the ground truth",
            )
        )
        plot_titles.append("CEM WS")
        plots.append(fig)
        remarks.append("")

        for camera, timeframe_list in ws_detection_data.items():
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=[timeframe.timestamp for timeframe in timeframe_list],
                    y=[len(timeframe.pmd_lines) for timeframe in timeframe_list],
                    mode="lines",
                    name=f"{camera._name_} camera number of WS detection",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=[timeframe for timeframe, _ in number_of_associated_ws_detection[camera]],
                    y=[nbr_associated_lines for _, nbr_associated_lines in number_of_associated_ws_detection[camera]],
                    mode="lines",
                    name=f"{camera._name_} camera number of associated WS detection",
                )
            )
            plot_titles.append(f"{camera._name_} camera WS detection")
            plots.append(fig)
            remarks.append("")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1530467"],
            fc.TESTCASE_ID: ["38843"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test case verifies that, in average CEM doesn't provide worse position"
                "for the wheelstopper than each input separately."
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


@verifies("1530467")
@testcase_definition(
    name="SWKPI_CNC_PFS_WheelstopperPositionAccuracy",
    description="This test case verifies that, in average CEM doesn't provide worse position"
    "for the wheelstopper than each input separately.",
)
class FtWSAccuracy(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtWSAccuracy]
