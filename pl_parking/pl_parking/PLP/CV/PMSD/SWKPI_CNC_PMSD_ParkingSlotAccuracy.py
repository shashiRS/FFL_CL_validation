"""Parking Slot Accuracy KPI Test."""

import logging
import os
import sys
import typing

import numpy as np
import plotly.graph_objects as go
from tsf.core.common import PathSpecification
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
from tsf.io.sideload import JsonSideLoad

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CV.PMSD.constants import AssociationConstants
from pl_parking.PLP.CV.PMSD.ft_helper import PMSDSignals
from pl_parking.PLP.CV.PMSD.ft_slot_helper import FtSlotHelper
from pl_parking.PLP.CV.PMSD.inputs.input_PmdReader import PMDCamera, PMDReader
from pl_parking.PLP.CV.PMSD.inputs.input_PsdPmsdSlotReader import PSDSlotReader as SlotReader

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "PMSD_KPI_Slot_Accuracy"

example_obj = PMSDSignals()


@teststep_definition(
    step_number=1,
    name="CV PMSD KPI Slot Accuracy",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, PMSDSignals)
@register_side_load(
    alias="JsonGt",
    side_load=JsonSideLoad,  # type of side loaders
    path_spec=PathSpecification(
        folder=os.path.join(TSF_BASE, "data", "CEM_json_gt"),
        extension=".json",
    ),
    # Absolute path for the sideload.
)
class TestStepFtSlotAccuracy(TestStep):
    """Test Parking Slot Accuracy"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step"""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remark based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        detected_slots = SlotReader(reader).convert_to_class()
        gt_data = self.side_load["JsonGt"]
        gt_slots = FtSlotHelper.get_slot_from_json_gt(gt_data)

        associated_gt_slots_per_camera: typing.Dict[PMDCamera, typing.List[float]] = dict()
        number_of_gt_slots_per_camera: typing.Dict[PMDCamera, typing.List[int]] = dict()
        number_of_detected_slots_per_camera: typing.Dict[PMDCamera, typing.List[typing.Tuple[int, int]]] = dict()
        number_of_associated_gt_slots_per_camera: typing.Dict[PMDCamera, typing.List[int]] = dict()

        for _, camera in enumerate(PMDCamera):
            associated_gt_slots_per_camera[camera] = []
            number_of_associated_gt_slots_per_camera[camera] = []
            number_of_gt_slots_per_camera[camera] = []
            number_of_detected_slots_per_camera[camera] = []
            gt_slot = gt_slots[camera]
            for detected_slot in detected_slots[camera]:
                number_of_detected_slots_per_camera[camera].append(
                    (detected_slot.timestamp, detected_slot.number_of_slots))
                gt_with_closest_timestamp = gt_slot.get(
                    min(gt_slot.keys(), key=lambda k: abs(k - detected_slot.timestamp))
                )
                if not all(
                        detected_slot.timestamp == v.slot_timestamp for v in gt_with_closest_timestamp):
                    number_of_associated_gt_slots_per_camera[camera].append(0)
                    associated_gt_slots_per_camera[camera].append(0)
                    number_of_gt_slots_per_camera[camera].append(-1)
                elif detected_slot.number_of_slots < 1:
                    associated_gt_slots_per_camera[camera].append(0)
                    number_of_associated_gt_slots_per_camera[camera].append(0)
                    number_of_gt_slots_per_camera[camera].append(len(gt_slot[int(detected_slot.timestamp)]))
                else:
                    number_of_gt_slots_per_camera[camera].append(len(gt_slot[int(detected_slot.timestamp)]))
                    association = FtSlotHelper.associate_slot_list(
                        detected_slot.parking_slots,
                        gt_with_closest_timestamp,
                    )
                    slot_ground_truth_distances = []
                    for asso in association.items():
                        gt_i, pcl_i = asso
                        dist = FtSlotHelper.adjust_slot_distance(detected_slot.parking_slots[pcl_i],
                                                                 gt_with_closest_timestamp[gt_i])
                        slot_ground_truth_distances.append(dist)

                    associated_gt_slots_per_camera[camera].append(
                        np.mean(slot_ground_truth_distances) if len(slot_ground_truth_distances) > 0 else 0)
                    number_of_associated_gt_slots_per_camera[camera].append(
                        len([ground_truth for _, ground_truth in association.items() if ground_truth is not None]))

        avg_distances_per_camera: typing.Dict[PMDCamera, typing.List[float]] = dict()
        for camera in PMDCamera:
            avg_distances_per_camera[camera] = [d
                                                if d > 0 and number_of_gt_slots_per_camera[camera][i] > 0 else None
                                                for i, d in
                                                enumerate(associated_gt_slots_per_camera[camera])]
            cam_name = PMDReader.get_camera_strings()[camera]
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=[v.timestamp for v in detected_slots[camera]],
                    y=[v for v in avg_distances_per_camera[camera]],
                    mode="lines",
                    line=dict(color="green"),
                    name=f"Distance of {cam_name} slots [m]",
                )
            )
            fig.layout = go.Layout(
                xaxis=dict(title="Frames [ns]"),
                yaxis=dict(title="distance error [m]"),
                title=dict(text=f"Distance Error of {cam_name}", font_size=36)
            )
            fig.add_trace(
                go.Scatter(
                    x=[v.timestamp for v in detected_slots[camera]],
                    y=[np.mean([v for v in avg_distances_per_camera[camera] if v is not None])] * len(
                        detected_slots[camera]),
                    mode="lines",
                    line=dict(color="red", dash="dash"),
                    name=f"mean Distance of {cam_name} slots [deg]",
                )
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        source_of_distances: typing.List[str] = ["Slot All"]
        avg_slot_distances: typing.List[float] = [
            np.mean([d for distances_cam in avg_distances_per_camera.values() for d in distances_cam if d is not None])]
        num_of_frames: typing.List[float] = [
            len([d for distances_cam in avg_distances_per_camera.values() for d in distances_cam if d is not None])]
        for camera in PMDCamera:
            avg_slot_distances.append(np.mean([tp for tp in avg_distances_per_camera[camera] if tp is not None]))
            source_of_distances.append(f"Slot {PMDReader.get_camera_strings()[camera]}")
            num_of_frames.append(len([tp for tp in avg_distances_per_camera[camera] if tp is not None]))

        colors = ["green" if d < AssociationConstants.THRESHOLD_SLOT_DISTANCE_IN_M else "red" for d in
                  avg_slot_distances]
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Source", "Average Distance Error [deg]", "Number of frames"]),
                    cells=dict(values=[source_of_distances, avg_slot_distances, num_of_frames],
                               fill_color=[colors, colors]),
                )
            ]
        )
        plot_titles.append("Average Distance")
        plots.append(fig)
        remarks.append("")

        if avg_slot_distances[0] < AssociationConstants.THRESHOLD_SLOT_DISTANCE_IN_M:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL
        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["TBD"],
            fc.TESTCASE_ID: ["TBD"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test case verifies the accuracy of detected slots."
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


@verifies("TBD")
@testcase_definition(
    name="SWKPI_CNC_PMSD_KPI_ParkingSlotAccuracy",
    description="This test case verifies the accuracy of detected slots.",
)
class FtSlotAccuracy(TestCase):
    """Test Parking Slot Accuracy"""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotAccuracy]
