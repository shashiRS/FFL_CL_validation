"""CEM PFS SLOT Test Cases"""

import logging

from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

import math
import typing

import pandas as pd
import plotly.graph_objects as go

import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import CemSignals, CustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import AssociationConstants, ConstantsCem, GroundTruthCem
from pl_parking.PLP.CEM.ft_slot_helper import FtSlotHelper
from pl_parking.PLP.CEM.ground_truth.kml_parser import CemGroundTruthHelper
from pl_parking.PLP.CEM.ground_truth.vehicle_coordinates_helper import VehicleCoordinateHelper
from pl_parking.PLP.CEM.inputs.input_CemSlotReader import Slot, SlotReader
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import VedodoReader
from pl_parking.PLP.CEM.inputs.input_DGPSReader import DGPSReader
from pl_parking.PLP.CEM.inputs.input_PsdSlotReader import PSDCamera, PSDSlotReader

SIGNAL_DATA = "CEM_PFS_Slot_Scenario_Confidence_Special"
example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Scenario Confidence Special",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtScenarioConfidence(TestStep):
    """TestStep for evaluating scenario confidence, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """Process data and update result details with plot-related information and the file name of the first artifact."""
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


@testcase_definition(
    name="CEM PFS Slot Scenario Confidence Special",
    description="This test case checks that, in average PFS doesn't provide worse scenario confidence estimation "
    "for the parking scenarios than each input separately.",
)
class FtScenarioConfidence(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtScenarioConfidence]


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Accuracy",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSlotAccuracy(TestStep):
    """TestStep for assessing slot accuracy, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """Process data and update result details with plot-related information and the file name of the first artifact."""
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


@testcase_definition(
    name="CEM PFS Slot Accuracy",
    description="This test case verifies that, in average CEM doesn't provide worse position for the parking slots "
    "than each input separately.",
)
class FtSlotAccuracy(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotAccuracy]


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Field of View",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSlotFieldOFView(TestStep):
    """TestStep for evaluating Field of View for slots, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """Process data and update result details with plot-related information and the file name of the first artifact."""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        input_reader = SlotReader(reader)
        slot_data = input_reader.convert_to_class()

        if any(reader.as_plain_df["CemSlot_numberOfSlots"].values > 0):
            rows = []
            failed = 0
            for time_frame in slot_data:
                for slot in time_frame.parking_slots:
                    closes_point = FtSlotHelper.get_closest_point(slot)
                    if (
                        abs(closes_point.x) > ConstantsCem.AP_G_DES_MAP_RANGE_M / 2
                        or abs(closes_point.y) > ConstantsCem.AP_G_DES_MAP_RANGE_M / 2
                    ):
                        failed += 1
                        values = [
                            [time_frame.timestamp],
                            [slot.slot_id],
                            [closes_point.x],
                            [closes_point.y],
                            [ConstantsCem.AP_G_DES_MAP_RANGE_M],
                        ]
                        rows.append(values)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Timestamp", "SlotID", "x", "y", "LIMIT_OUTPUT_FIELD_OF_VIEW"]),
                            cells=dict(values=values),
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


@testcase_definition(
    name="CEM PFS Slot Field of View",
    description=f"""This test case checks if CEM output contains only parking slots inside the limited
    {ConstantsCem.AP_G_DES_MAP_RANGE_M} x {ConstantsCem.AP_G_DES_MAP_RANGE_M} field of view.""",
)
class FtSlotFieldOFView(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotFieldOFView]


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Furthest Slot",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSlotFurthestSlotDeleted(TestStep):
    """TestStep for detecting the furthest deleted slot, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """Process data and update result details with plot-related information and the file name of the first artifact."""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)
        reader = self.readers[SIGNAL_DATA].signals
        inputReader = SlotReader(reader)
        vedodo_buffer = VedodoReader(reader).convert_to_class()
        slot_data = inputReader.convert_to_class()
        nbrTimeframes = len(slot_data)

        if any(reader.as_plain_df["CemSlot_numberOfSlots"].values > 0):
            failed = 0
            for i in range(nbrTimeframes - 1):
                prevTimeframe = slot_data[i]
                curTimeframe = slot_data[i + 1]

                relative_motion = vedodo_buffer.calc_relative_motion(prevTimeframe.timestamp, curTimeframe.timestamp)

                missing_slots: typing.List[Slot] = []

                if len(prevTimeframe.parking_slots) > 0 and len(curTimeframe.parking_slots) > 0:
                    if len(curTimeframe.parking_slots) == ConstantsCem.PCL_MAX_NUM_MARKERS:
                        missing_slots = FtSlotHelper.find_missing_slot_ids(prevTimeframe, curTimeframe)

                if len(missing_slots) > 0:
                    _, furthestPclDistance = FtSlotHelper.get_furthest_slot(curTimeframe)

                    for missing_slot in missing_slots:
                        transformed_line = FtSlotHelper.transform_slot(missing_slot, relative_motion)
                        if FtSlotHelper.distance_slot_vehicle(transformed_line) < furthestPclDistance:
                            failed += 1

            if failed:
                test_result = fc.FAIL
                fig = go.Figure(
                    data=[go.Table(header=dict(values=["Number of failed deleted slots"]), cells=dict(values=[failed]))]
                )
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")
            else:
                test_result = fc.PASS

        else:
            test_result = fc.INPUT_MISSING

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


@testcase_definition(
    name="CEM PFS Slot Furthest Slot",
    description=f"""This test case checks if CEM deletes the furthest parking slots
        if the number of parking slots is larger than the {ConstantsCem.PSD_MAX_NUM_MARKERS}  limit.""",
)
class FtSlotFurthestSlotDeleted(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotFurthestSlotDeleted]


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Id Reuse",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSlotIDReuse(TestStep):
    """TestStep for assessing slot ID reuse, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """Process data and update result details with plot-related information and the file name of the first artifact."""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        input_reader = SlotReader(reader)
        slot_data = input_reader.convert_to_class()

        observation_times: typing.Dict[int, int] = {}

        if any(reader.as_plain_df["CemSlot_numberOfSlots"].values > 0):
            rows = []
            failed = 0
            for idx, time_frame in enumerate(slot_data):
                for slot in time_frame.parking_slots:
                    if slot.slot_id in observation_times:
                        if not (observation_times[slot.slot_id] == idx - 1) or (
                            observation_times[slot.slot_id] < idx - ConstantsCem.AP_E_SLOT_ID_REUSE_LIMIT_NU
                        ):
                            failed += 1
                            values = [[idx], [observation_times[idx]], [slot.slot_id]]
                            rows.append(values)

                    observation_times[slot.slot_id] = idx

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Cycle count", "Last observation cycle count", "Slot ID"]),
                            cells=dict(values=values),
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


@testcase_definition(
    name="CEM PFS Slot Id Reuse",
    description=f"""This test checks that in case CEM stops providing
        a parking slot with a particular ID, the ID is not used again
        for a new Parking Slot for at least {ConstantsCem.AP_E_SLOT_ID_REUSE_LIMIT_NU} cycles.""",
)
class FtSlotIDReuse(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotIDReuse]


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot ID Maintenance",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSlotMainID(TestStep):
    """TestStep for maintaining main slot ID, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """Process data and update result details with plot-related information and the file name of the first artifact."""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        slot_data = SlotReader(reader).convert_to_class()
        psd_data = PSDSlotReader(reader).convert_to_class()
        vedodo_buffer = VedodoReader(reader).convert_to_class()

        if any(reader.as_plain_df["CemSlot_numberOfSlots"].values > 0):
            rows = []
            failed = 0
            for index, curTimeframe in enumerate(slot_data):
                if index == 0:
                    continue
                prevTimeframe = slot_data[index - 1]
                relative_motion_output = vedodo_buffer.calc_relative_motion(
                    curTimeframe.timestamp, prevTimeframe.timestamp
                )

                transformed_prevSlots = [
                    FtSlotHelper.transform_slot(slot, relative_motion_output) for slot in prevTimeframe.parking_slots
                ]

                psd_timeframe_index = [
                    FtSlotHelper.get_PSD_timeframe_index(
                        curTimeframe.timestamp, prevTimeframe.timestamp, psd_data[camera]
                    )
                    for camera in PSDCamera
                ]

                psd_timeframes = [
                    psd_data[camera][psd_timeframe_index[int(camera)]]
                    for camera in PSDCamera
                    if psd_timeframe_index[int(camera)] is not None
                ]

                updatedSlots = FtSlotHelper.get_solts_with_associated_input(transformed_prevSlots, psd_timeframes)

                associations = FtSlotHelper.associate_slot_list(curTimeframe.parking_slots, updatedSlots)

                for prev_ixd, curr_index in associations.items():
                    if updatedSlots[prev_ixd].slot_id != curTimeframe.parking_slots[curr_index].slot_id:
                        failed += 1
                        values = [
                            [curTimeframe.timestamp],
                            [updatedSlots[prev_ixd].slot_id],
                            [curTimeframe.parking_slots[curr_index].slot_id],
                        ]
                        rows.append(values)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Timestamp", "Prev Slot ID", "Curr Slot ID"]), cells=dict(values=values)
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


@testcase_definition(
    name="CEM PFS Slot ID Maintenance",
    description="""This test checks that EnvironmentFusion maintains the identifier of each parking slot if a parking
        slot detection is received in the current timeframe and can be associated to a parking slot already
        received in previous time frames.""",
)
class FtSlotMainID(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotMainID]


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Number Limit",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSlotNumberLimit(TestStep):
    """TestStep for assessing the number limit of slots, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """Process data and update result details with plot-related information and the file name of the first artifact."""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        input_reader = SlotReader(reader)
        slot_data = input_reader.convert_to_class()

        if any(reader.as_plain_df["CemSlot_numberOfSlots"].values > 0):
            rows = []
            failed = 0
            for time_frame in slot_data:
                if time_frame.number_of_slots > ConstantsCem.PSD_MAX_NUM_MARKERS:
                    failed += 1
                    values = [[time_frame.timestamp], [time_frame.number_of_slots], [len(time_frame.parking_slots)]]
                    rows.append(values)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Timestamp", "numberSlots", "Outputted slot number"]),
                            cells=dict(values=values),
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


@testcase_definition(
    name="CEM PFS Slot Number Limit",
    description=f"""This test case checks if CEM limits the number
        of parking slots to {ConstantsCem.PSD_MAX_NUM_MARKERS}.""",
)
class FtSlotNumberLimit(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotNumberLimit]


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Scenario Confidence",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSlotScenario(TestStep):
    """TestStep for evaluating slot scenario, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """Process data and update result details with plot-related information and the file name of the first artifact."""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)
        test_result = fc.NOT_ASSESSED

        reader = self.readers[SIGNAL_DATA].signals
        dgps_buffer = DGPSReader(reader).convert_to_class()
        cem_ground_truth_utm = CemGroundTruthHelper.get_cem_ground_truth_from_files_list(
            [os.path.dirname(__file__) + "\\" + r"config\cem_ground_truth\mring_parking_slots.kml"]
        )
        slot_reader = SlotReader(reader)
        slot_data = slot_reader.convert_to_class()
        psd_reader = PSDSlotReader(reader)
        psd_data = psd_reader.convert_to_class()

        slot_confidence: typing.Tuple[typing.List[float], typing.List[int]] = ([], [])

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

        psd_confidence: typing.List[typing.Tuple[typing.List[float], typing.List[int]]] = [
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
                conf, used = FtSlotHelper.calculate_scenario_confidence_correctness(
                    time_frame.parking_slots, cem_ground_truth_iso.parking_slots
                )
                psd_confidence[int(camera)][0].append(conf)
                psd_confidence[int(camera)][1].append(used)

        if sum(slot_confidence[1]) > 0:
            average_slot_confidence = sum(slot_confidence[0]) / sum(slot_confidence[1])
            average_psd_confidence = [sum(conf[0]) / sum(conf[1]) if sum(conf[1]) > 0 else 0 for conf in psd_confidence]

            for psd_conf in average_psd_confidence:
                if psd_conf > average_slot_confidence:
                    test_result = fc.FAIL

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

        else:
            test_result = fc.INPUT_MISSING

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


@testcase_definition(
    name="CEM PFS Slot Scenario Confidence",
    description="This test case checks that, in average CEM doesn't provide worse scenario confidence estimation "
    "for the parking scenarios than each input separately.",
)
class FtSlotScenario(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotScenario]


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Unique ID",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSlotUniqueID(TestStep):
    """TestStep for ensuring unique slot ID, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """Process data and update result details with plot-related information and the file name of the first artifact."""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        input_reader = SlotReader(reader)
        slot_data = input_reader.convert_to_class()

        if any(reader.as_plain_df["CemSlot_numberOfSlots"].values > 0):
            rows = []
            failed = 0
            for time_frame in slot_data:
                ids = []
                for slot in time_frame.parking_slots:
                    if slot.slot_id in ids:
                        failed += 1
                        values = [[time_frame.timestamp], [slot.slot_id]]
                        rows.append(values)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(data=[go.Table(header=dict(values=["Timestamp", "SlotID"]), cells=dict(values=values))])
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")
            else:
                test_result = fc.PASS

        else:
            test_result = fc.INPUT_MISSING

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


@testcase_definition(
    name="CEM PFS Slot Unique ID",
    description="This test checks that CEM provides a unique identifier for each parking slots.",
)
class FtSlotUniqueID(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotUniqueID]


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Output",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSlotOutput(TestStep):
    """TestStep for evaluating slot output, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """Process data and update result details with plot-related information and the file name of the first artifact."""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        reader.as_plain_df.drop_duplicates(inplace=True)
        slot_reader = SlotReader(reader)
        slot_data = slot_reader.convert_to_class()

        psd_data = reader.as_plain_df.filter(regex="PsdSlot_")

        if any(reader.as_plain_df["CemSlot_numberOfSlots"].values > 0):
            # Get the first TS where there is an input in all cameras
            first_in_ts = min(
                [
                    psd_data[psd_data["PsdSlot_Front_numberOfSlots"] > 0]["PsdSlot_Front_timestamp"].min(),
                    psd_data[psd_data["PsdSlot_Rear_numberOfSlots"] > 0]["PsdSlot_Rear_timestamp"].min(),
                    psd_data[psd_data["PsdSlot_Left_numberOfSlots"] > 0]["PsdSlot_Left_timestamp"].min(),
                    psd_data[psd_data["PsdSlot_Right_numberOfSlots"] > 0]["PsdSlot_Right_timestamp"].min(),
                ]
            )

            # Get the last TS where there is an output in all cameras
            last_in_ts = max(
                [
                    psd_data[psd_data["PsdSlot_Front_numberOfSlots"] > 0]["PsdSlot_Front_timestamp"].max(),
                    psd_data[psd_data["PsdSlot_Rear_numberOfSlots"] > 0]["PsdSlot_Rear_timestamp"].max(),
                    psd_data[psd_data["PsdSlot_Left_numberOfSlots"] > 0]["PsdSlot_Left_timestamp"].max(),
                    psd_data[psd_data["PsdSlot_Right_numberOfSlots"] > 0]["PsdSlot_Right_timestamp"].max(),
                ]
            )

            # Calculate delay
            delay = ConstantsCem.SYNC_INPUT_OUTPUT_CYCLES * ConstantsCem.CYCLE_PERIOD_TIME_MS
            first_out_ts = first_in_ts + (delay * 1e3)
            last_out_ts = last_in_ts + (delay * 1e3)

            rows = []
            failed_timestamps = 0
            for _, cur_timeframe in enumerate(slot_data):
                slots_number = cur_timeframe.number_of_slots
                cur_timestamp = cur_timeframe.timestamp
                if cur_timestamp <= first_in_ts:
                    if slots_number != 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [slots_number], ["First zone, no input"], ["No output"]]
                        rows.append(values)

                elif first_in_ts <= cur_timestamp < first_out_ts:
                    if slots_number != 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [slots_number], ["Second zone, input available"], ["No output"]]
                        rows.append(values)

                elif first_out_ts <= cur_timestamp < last_out_ts:
                    if slots_number == 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [slots_number], ["Third zone, input available"], ["Output"]]
                        rows.append(values)

                elif first_out_ts <= cur_timestamp < last_out_ts:
                    if slots_number == 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [slots_number], ["Fourth zone, input available"], ["Output"]]
                        rows.append(values)

                else:
                    if slots_number != 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [slots_number], ["Fifth zone, no input"], ["No output"]]
                        rows.append(values)

            if failed_timestamps:
                test_result = fc.FAIL
            else:
                test_result = fc.PASS

            header = ["Timestamp", "Number of output slots", "Evaluation section", "Expected output"]
            values = list(zip(*rows))
            fig = go.Figure(data=[go.Table(header=dict(values=header), cells=dict(values=values))])
            plot_titles.append("Test Fail report")
            plots.append(fig)
            remarks.append("")

            psd_data = psd_data.drop_duplicates()
            psd_data = psd_data.loc[(psd_data["PsdSlot_Front_timestamp"] != 0)]
            psd_data = psd_data.loc[(psd_data["PsdSlot_Rear_timestamp"] != 0)]
            psd_data = psd_data.loc[(psd_data["PsdSlot_Left_timestamp"] != 0)]
            psd_data = psd_data.loc[(psd_data["PsdSlot_Right_timestamp"] != 0)]
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=slot_reader.data["CemSlot_timestamp"], y=slot_reader.data["CemSlot_numberOfSlots"], name="Output"
                )
            )
            fig.add_vrect(x0=slot_reader.data["timestamp"].iat[0], x1=first_in_ts, fillcolor="#E1F5FE", layer="below")
            fig.add_vrect(x0=first_in_ts, x1=first_out_ts, fillcolor="#BBDEFB", layer="below")
            fig.add_vrect(x0=first_out_ts, x1=last_in_ts, fillcolor="#F5F5F5", layer="below")
            fig.add_vrect(x0=last_in_ts, x1=last_out_ts, fillcolor="#E0E0E0", layer="below")
            fig.add_vrect(
                x0=last_out_ts, x1=slot_reader.data["CemSlot_timestamp"].iat[-1], fillcolor="#F3E5F5", layer="below"
            )
            fig.add_trace(
                go.Scatter(
                    x=psd_data["PsdSlot_Front_timestamp"], y=psd_data["PsdSlot_Front_numberOfSlots"], name="psdFront"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=psd_data["PsdSlot_Rear_timestamp"], y=psd_data["PsdSlot_Rear_numberOfSlots"], name="psdRear"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=psd_data["PsdSlot_Left_timestamp"], y=psd_data["PsdSlot_Left_numberOfSlots"], name="psdLeft"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=psd_data["PsdSlot_Right_timestamp"], y=psd_data["PsdSlot_Right_numberOfSlots"], name="psdRight"
                )
            )

            plots.append(fig)
            plot_titles.append("Evaluated zones (Number of slots)")
            remarks.append("")

        else:
            test_result = fc.INPUT_MISSING

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


@testcase_definition(
    name="CEM PFS Slot Output",
    description="""This test case checks if PFS performs the fusion based on incoming parking slot
        detections and provide a list of tracked Parking Slots.""",
)
class FtSlotOutput(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotOutput]


@teststep_definition(
    step_number=1,
    name="CEM-PFS Latency Compensation",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPFSOutputAtT7(TestStep):
    """TestStep for PFS output at T7, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """Process data and update result details with plot-related information and the file name of the first artifact."""
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


@testcase_definition(
    name="CEM-PFS Latency Compensation",
    description="This test case checks if PFS provides its signals in the Vehicle coordinate system at T7",
)
class FtPFSOutputAtT7(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPFSOutputAtT7]
