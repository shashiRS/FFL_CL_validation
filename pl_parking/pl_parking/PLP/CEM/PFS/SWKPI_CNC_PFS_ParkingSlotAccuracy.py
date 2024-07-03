"""Parking Slot Accuracy KPI Test."""

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


import math
import typing

import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import AssociationConstants, GroundTruthCem
from pl_parking.PLP.CEM.ft_slot_helper import FtSlotHelper
from pl_parking.PLP.CEM.ground_truth.kml_parser import CemGroundTruthHelper
from pl_parking.PLP.CEM.ground_truth.vehicle_coordinates_helper import VehicleCoordinateHelper
from pl_parking.PLP.CEM.inputs.input_CemSlotReader import SlotReader
from pl_parking.PLP.CEM.inputs.input_DGPSReader import DGPSReader
from pl_parking.PLP.CEM.inputs.input_PsdSlotReader import PSDSlotReader

SIGNAL_DATA = "PFS_Slot_Accuracy"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Accuracy",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSlotAccuracy(TestStep):
    """Parking Marker Accuracy Test."""

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
        test_result = fc.NOT_ASSESSED

        reader = self.readers[SIGNAL_DATA].signals
        dgps_buffer = DGPSReader(reader).convert_to_class()
        cem_ground_truth_utm = CemGroundTruthHelper.get_cem_ground_truth_from_files_list(
            [os.path.dirname(__file__) + "\\" + f_path for f_path in GroundTruthCem.kml_files]
        )
        slot_reader = SlotReader(reader)
        slot_data = slot_reader.convert_to_class()
        psd_reader = PSDSlotReader(reader)
        psd_data = psd_reader.convert_to_class()

        slot_accuracy: typing.Tuple[typing.List[float], typing.List[int]] = ([], [])

        for time_frame in slot_data:
            dgps_pose = dgps_buffer.estimate_vehicle_pose(time_frame.timestamp)
            if dgps_pose is None:
                continue
            cem_ground_truth_iso = VehicleCoordinateHelper.cem_ground_truth_utm_to_vehicle(
                cem_ground_truth_utm, dgps_pose
            )
            distance, used = FtSlotHelper.calculate_accuracy_correctness(
                time_frame.parking_slots, cem_ground_truth_iso.parking_slots
            )
            slot_accuracy[0].append(distance)
            slot_accuracy[1].append(used)

        psd_accuracy: typing.List[typing.Tuple[typing.List[float], typing.List[int]]] = [
            ([], []),
            ([], []),
            ([], []),
            ([], []),
        ]

        for camera, data in psd_data.items():
            for time_frame in data:
                dgps_pose = dgps_buffer.estimate_vehicle_pose(time_frame.timestamp)
                if dgps_pose is None:
                    continue
                cem_ground_truth_iso = VehicleCoordinateHelper.cem_ground_truth_utm_to_vehicle(
                    cem_ground_truth_utm, dgps_pose
                )
                conf, used = FtSlotHelper.calculate_accuracy_correctness(
                    time_frame.parking_slots, cem_ground_truth_iso.parking_slots
                )
                psd_accuracy[int(camera)][0].append(conf)
                psd_accuracy[int(camera)][1].append(used)

        if sum(slot_accuracy[1]) > 0:
            average_slot_accuracy = sum(slot_accuracy[0]) / sum(slot_accuracy[1])
            average_psd_accuracy = [sum(acc[0]) / sum(acc[1]) if sum(acc[1]) > 0 else math.inf for acc in psd_accuracy]

            for psd_acc in average_psd_accuracy:
                if psd_acc < average_slot_accuracy:
                    test_result = fc.FAIL

            if test_result != fc.FAIL:
                test_result = fc.PASS

            # Create info graphs
            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(values=["Camera", "For PSD [m]", "For CEM [m]", "Association  distance [m]"]),
                        cells=dict(
                            values=[
                                psd_reader.camera_names,
                                average_psd_accuracy,
                                [average_slot_accuracy],
                                [AssociationConstants.MAX_SLOT_DISTANCE],
                            ]
                        ),
                    )
                ]
            )
            plot_titles.append("Average scenario accuracy for slots")
            plots.append(fig)
            remarks.append("")

            off = len(slot_data) - len(slot_accuracy[1])

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=slot_reader.data["CemSlot_timestamp"][off - 1 : -1],
                    y=slot_reader.data["CemSlot_numberOfSlots"][off - 1 : -1],
                    mode="lines",
                    name="CEM outputted slot",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=slot_reader.data["CemSlot_timestamp"][off - 1 : -1],
                    y=slot_accuracy[1],
                    mode="lines",
                    name="Associated CEM Slots",
                )
            )

            plot_titles.append("CEM Slot Association")
            plots.append(fig)
            remarks.append("")

            off = len(psd_data) - len(psd_accuracy[0][1])

            for i in range(4):
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=psd_reader.data["PsdSlot_" + psd_reader.camera_names[i] + "_timestamp"][off - 1 : -1],
                        y=psd_reader.data["PsdSlot_" + psd_reader.camera_names[i] + "_numberOfSlots"][off - 1 : -1],
                        mode="lines",
                        name=f"PSD {psd_reader.camera_names[i]} camera outputted slot",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=psd_reader.data["PsdSlot_" + psd_reader.camera_names[i] + "_timestamp"][off - 1 : -1],
                        y=psd_accuracy[i][1],
                        mode="lines",
                        name=f"PSD {psd_reader.camera_names[i]} camera associated slot",
                    )
                )
                plot_titles.append(f"PSD {psd_reader.camera_names[i]} camera Slot Association")
                plots.append(fig)
                remarks.append("")

        else:
            test_result = fc.INPUT_MISSING

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1530479"],
            fc.TESTCASE_ID: ["38848"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test case verifies that, in average CEM doesn't provide worse position for the parking slots "
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


@verifies("1530479")
@testcase_definition(
    name="SWKPI_CNC_PFS_ParkingSlotAccuracy",
    description="This test case verifies that, in average CEM doesn't provide worse position for the parking slots "
    "than each input separately.",
)
class FtSlotAccuracy(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotAccuracy]
