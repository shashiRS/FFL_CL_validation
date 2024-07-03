"""Wheelstopper False Positive KPI Test."""

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

SIGNAL_DATA = "PFS_WS_False_Positive"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS WS False Positive",
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
class TestStepFtWSFalsePositive(TestStep):
    """Calculate False Positive KPI"""

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
        gt_data = self.side_load["JsonGt"]
        ws_gt = FtWsHelper.get_ws_from_json_gt(gt_data)
        pcl_data = PclDelimiterReader(reader).convert_to_class()
        ws_detection_data = WSDetectionReader(reader).convert_to_class()

        cem_ws_false_positive_list: typing.List[float] = []
        number_of_associated_cem_ws: typing.List[typing.Tuple[int, int]] = []

        for _, pcl_timeframe in enumerate(pcl_data):
            timeframe_nbr_associated_ws = 0

            if len(pcl_timeframe.wheel_stopper_array) > 0:
                gt_with_closest_timestamp = ws_gt.get(min(ws_gt.keys(), key=lambda k: abs(k - pcl_timeframe.timestamp)))
                false_positive = FtPclHelper.calculate_cem_pcl_false_positive_iso(
                    pcl_timeframe.wheel_stopper_array,
                    gt_with_closest_timestamp,
                    AssociationConstants.WS_ASSOCIATION_RADIUS,
                )
                timeframe_nbr_associated_ws = len(pcl_timeframe.wheel_stopper_array) - (
                    len(pcl_timeframe.wheel_stopper_array) * false_positive
                )
                cem_ws_false_positive_list.append(false_positive)

            number_of_associated_cem_ws.append((pcl_timeframe.timestamp, timeframe_nbr_associated_ws))

        ws_detection_false_positive_list: typing.List[float] = []
        ws_detection_false_positive_per_camera: typing.Dict[PMDCamera, typing.List[float]] = dict()
        number_of_associated_ws_detection: typing.Dict[PMDCamera, typing.List[typing.Tuple[int, int]]] = dict()
        for camera, timeframe_list in ws_detection_data.items():
            ws_detection_false_positive_per_camera[camera] = []
            number_of_associated_ws_detection[camera] = []
            for ws_timeframe in timeframe_list:
                timeframe_nbr_associated_ws = 0

                if len(ws_timeframe.pmd_lines) > 0:
                    gt_with_closest_timestamp = ws_gt.get(
                        min(ws_gt.keys(), key=lambda k: abs(k - pcl_timeframe.timestamp))
                    )
                    false_positive = FtPclHelper.calculate_pmd_false_positive_iso(
                        ws_timeframe.pmd_lines,
                        gt_with_closest_timestamp,
                        AssociationConstants.WS_ASSOCIATION_RADIUS,
                    )
                    timeframe_nbr_associated_ws = (
                        len(ws_timeframe.pmd_lines) - len(ws_timeframe.pmd_lines) * false_positive
                    )

                    ws_detection_false_positive_list.append(false_positive)
                    ws_detection_false_positive_per_camera[camera].append(false_positive)

                number_of_associated_ws_detection[camera].append((ws_timeframe.timestamp, timeframe_nbr_associated_ws))

        avg_cem_ws_false_positive = np.mean(cem_ws_false_positive_list)
        avg_ws_detection_false_positive = np.mean(ws_detection_false_positive_list)

        if avg_ws_detection_false_positive >= avg_cem_ws_false_positive:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        # Average False Postive ration table
        source_false_positive = [
            "CEM",
            "WS Detection",
            "WS Detection Front",
            "WS Detection Rear",
            "WS Detection Right",
            "WS Detection Left",
        ]
        values_false_positive = [
            avg_cem_ws_false_positive,
            avg_ws_detection_false_positive,
            np.mean(ws_detection_false_positive_per_camera[PMDCamera.FRONT]),
            np.mean(ws_detection_false_positive_per_camera[PMDCamera.REAR]),
            np.mean(ws_detection_false_positive_per_camera[PMDCamera.RIGHT]),
            np.mean(ws_detection_false_positive_per_camera[PMDCamera.LEFT]),
        ]
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Source", "Average False Positive"]),
                    cells=dict(values=[source_false_positive, values_false_positive]),
                )
            ]
        )
        plot_titles.append("Average False Positive rate for wheelstoppers")
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
        plot_titles.append("Number of CEM WS")
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
            plot_titles.append(f"{camera._name_} camera number of WS detection")
            plots.append(fig)
            remarks.append("")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1530469"],
            fc.TESTCASE_ID: ["38844"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test checks if the wheel stopper false positive rate provided by CEM is not less than"
                "the wheel stopper false positive rate of the detections comparing with the ground truth data."
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


@verifies("1530469")
@testcase_definition(
    name="SWKPI_CNC_PFS_WheelstopperFalsePositiveRate",
    description="This test checks if the wheel stopper false positive rate provided by CEM is not less than"
    "the wheel stopper false positive rate of the detections comparing with the ground truth data.",
)
class FtWSFalsePositive(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtWSFalsePositive]
