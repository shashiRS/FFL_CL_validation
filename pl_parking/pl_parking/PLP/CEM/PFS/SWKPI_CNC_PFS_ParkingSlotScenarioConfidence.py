"""Parking Slot Scenario Confidence KPI Test"""

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
from pl_parking.PLP.CEM.constants import AssociationConstants, GroundTruthCem
from pl_parking.PLP.CEM.ft_slot_helper import FtSlotHelper
from pl_parking.PLP.CEM.ground_truth.kml_parser import CemGroundTruthHelper
from pl_parking.PLP.CEM.ground_truth.vehicle_coordinates_helper import VehicleCoordinateHelper
from pl_parking.PLP.CEM.inputs.input_CemSlotReader import SlotReader
from pl_parking.PLP.CEM.inputs.input_DGPSReader import DGPSReader
from pl_parking.PLP.CEM.inputs.input_PsdSlotReader import PSDSlotReader

SIGNAL_DATA = "PFS_Slot_Scenario_Confidence_Special"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Scenario Confidence Special",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtScenarioConfidence(TestStep):
    """Test Parking Slot Scenario Confidence"""

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
        # Variables definition
        plot_titles, plots, remarks = rep([], 3)
        slot_confidence: typing.Tuple[typing.List[float], typing.List[int]] = ([], [])
        psd_confidence: typing.List[typing.Tuple[typing.List[float], typing.List[int]]] = [
            ([], []),
            ([], []),
            ([], []),
            ([], []),
        ]
        test_result = fc.NOT_ASSESSED

        # Load all signals information
        reader = self.readers[SIGNAL_DATA].signals
        dgps_buffer = DGPSReader(reader).convert_to_class()
        cem_ground_truth_utm = CemGroundTruthHelper.get_cem_ground_truth_from_files_list(
            [os.path.dirname(__file__) + "\\" + f_path for f_path in GroundTruthCem.kml_files]
        )
        slot_reader = SlotReader(reader)
        slot_data = slot_reader.convert_to_class()
        psd_reader = PSDSlotReader(reader)
        psd_data = psd_reader.convert_to_class()

        # Perform comparison of Ground truth against PFS data
        for time_frame in slot_data:
            dgps_pose = dgps_buffer.estimate_vehicle_pose(time_frame.timestamp)
            if dgps_pose is None:
                continue
            cem_ground_truth_iso = VehicleCoordinateHelper.cem_ground_truth_utm_to_vehicle(
                cem_ground_truth_utm, dgps_pose
            )
            conf, used = FtSlotHelper.calculate_scenario_confidence_correctness(
                time_frame.parking_slots, cem_ground_truth_iso.parking_slots
            )
            slot_confidence[0].append(conf)
            slot_confidence[1].append(used)

        # Perform comparison of Ground truth against each sensor independent data
        for camera, data in psd_data.items():
            for time_frame in data:
                dgps_pose = dgps_buffer.estimate_vehicle_pose(time_frame.timestamp)
                if dgps_pose is None:
                    continue
                cem_ground_truth_iso = VehicleCoordinateHelper.cem_ground_truth_utm_to_vehicle(
                    cem_ground_truth_utm, dgps_pose
                )
                conf, used = FtSlotHelper.calculate_scenario_confidence_correctness(
                    time_frame.parking_slots, cem_ground_truth_iso.parking_slots
                )
                psd_confidence[int(camera)][0].append(conf)
                psd_confidence[int(camera)][1].append(used)

        # Get average of slot confidence
        if sum(slot_confidence[1]) > 0:
            average_slot_confidence = sum(slot_confidence[0]) / sum(slot_confidence[1])
            average_psd_confidence = [sum(conf[0]) / sum(conf[1]) if sum(conf[1]) > 0 else 0 for conf in psd_confidence]

            # Check if Sensor confidence is greater than PFS confidence
            for psd_conf in average_psd_confidence:
                if psd_conf > average_slot_confidence:
                    test_result = fc.FAIL

            # If comparison didn't fail for any sensor, test will pass
            if test_result != fc.FAIL:
                test_result = fc.PASS

            # Create info graphs
            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(values=["Camera", "For PSD", "For CEM", "Association  distance"]),
                        cells=dict(
                            values=[
                                psd_reader.camera_names,
                                average_psd_confidence,
                                [average_slot_confidence],
                                [AssociationConstants.MAX_SLOT_DISTANCE],
                            ]
                        ),
                    )
                ]
            )
            plot_titles.append("Average scenario confidence for slots")
            plots.append(fig)
            remarks.append("")

            off = len(slot_data) - len(slot_confidence[1])

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
                    y=slot_confidence[1],
                    mode="lines",
                    name="Associated CEM Slots",
                )
            )

            plot_titles.append("CEM Slot Association")
            plots.append(fig)
            remarks.append("")

            off = len(psd_data) - len(psd_confidence[1][0])

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
                        y=psd_confidence[i][1],
                        mode="lines",
                        name=f"PSD {psd_reader.camera_names[i]} camera associated slot",
                    )
                )
                plot_titles.append(f"PSD {psd_reader.camera_names[i]} camera Slot Association")
                plots.append(fig)
                remarks.append("")
        # Check if there is no sensor association either
        else:
            if any(sum(confi[1]) > 0 for confi in psd_confidence):
                test_result = fc.INPUT_MISSING

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1530477"],
            fc.TESTCASE_ID: ["38847"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test case checks that, in average PFS doesn't provide worse scenario confidence estimation "
                "for the parking scenarios than each input separately."
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


@verifies("1530477")
@testcase_definition(
    name="SWKPI_CNC_PFS_ParkingSlotScenarioConfidence",
    description="This test case checks that, in average PFS doesn't provide worse scenario confidence estimation "
    "for the parking scenarios than each input separately.",
)
class FtScenarioConfidence(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtScenarioConfidence]
