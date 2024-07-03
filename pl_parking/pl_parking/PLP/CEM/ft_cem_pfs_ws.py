"""CEM PFS WS Test Cases"""

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

import typing

import numpy as np
import plotly.graph_objects as go

import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import CemSignals, CustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import AssociationConstants, ConstantsCem, ConstantsCemInput, GroundTruthCem
from pl_parking.PLP.CEM.ft_pcl_helper import FtPclHelper
from pl_parking.PLP.CEM.ground_truth.kml_parser import CemGroundTruthHelper
from pl_parking.PLP.CEM.ground_truth.vehicle_coordinates_helper import VehicleCoordinateHelper
from pl_parking.PLP.CEM.inputs.input_CemPclReader import PclDelimiterReader
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import VedodoReader
from pl_parking.PLP.CEM.inputs.input_CemWsReader import WSDetectionReader
from pl_parking.PLP.CEM.inputs.input_DGPSReader import DGPSReader
from pl_parking.PLP.CEM.inputs.input_PmdReader import PMDCamera

SIGNAL_DATA = "CEM_PFS_WS_Accuracy"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS WS Accuracy",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtWSAccuracy(TestStep):
    """TestStep for assessing accuracy in WS, utilizing a custom report."""

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
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        dgps_buffer = DGPSReader(reader).convert_to_class()
        cem_ground_truth_utm = CemGroundTruthHelper.get_cem_ground_truth_from_files_list(
            [os.path.dirname(__file__) + "\\" + f_path for f_path in GroundTruthCem.kml_files]
        )
        pcl_data = PclDelimiterReader(reader).convert_to_class()
        ws_detection_data = WSDetectionReader(reader).convert_to_class()

        all_cem_ws_ground_truth_distances: typing.List[float] = []
        number_of_associated_cem_ws: typing.List[typing.Tuple[int, int]] = []

        for _, pcl_timeframe in enumerate(pcl_data):
            dgps_pose = dgps_buffer.estimate_vehicle_pose(pcl_timeframe.timestamp)
            timeframe_nbr_associated_ws = 0

            if dgps_pose is not None and len(pcl_timeframe.wheel_stopper_array) > 0:
                ws_ground_truth_iso = VehicleCoordinateHelper.pcl_utm_to_vehicle(
                    cem_ground_truth_utm.wheelstoppers, dgps_pose
                )
                association, _ = FtPclHelper.associate_pcl_to_ground_truth(
                    pcl_timeframe.wheel_stopper_array, ws_ground_truth_iso, AssociationConstants.WS_ASSOCIATION_RADIUS
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
                dgps_pose = dgps_buffer.estimate_vehicle_pose(ws_timeframe.timestamp)
                if dgps_pose is not None and len(ws_timeframe.pmd_lines) > 0:
                    ws_ground_truth_iso = VehicleCoordinateHelper.pcl_utm_to_vehicle(
                        cem_ground_truth_utm.wheelstoppers, dgps_pose
                    )
                    association, _ = FtPclHelper.associate_pmd_to_ground_truth(
                        ws_timeframe.pmd_lines, ws_ground_truth_iso, AssociationConstants.WS_ASSOCIATION_RADIUS
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
    name="CEM PFS WS Accuracy",
    description="This test case verifies that, in average CEM doesn't provide worse position"
    "for the wheelstopper than each input separately.",
)
class FtWSAccuracy(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtWSAccuracy]


@teststep_definition(
    step_number=1,
    name="CEM PFS WS False Positive",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtWSFalsePositive(TestStep):
    """TestStep for evaluating False Positive cases in WS, utilizing a custom report."""

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
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        dgps_buffer = DGPSReader(reader).convert_to_class()
        cem_ground_truth_utm = CemGroundTruthHelper.get_cem_ground_truth_from_files_list(
            [os.path.dirname(__file__) + "\\" + f_path for f_path in GroundTruthCem.kml_files]
        )
        pcl_data = PclDelimiterReader(reader).convert_to_class()
        ws_detection_data = WSDetectionReader(reader).convert_to_class()

        cem_ws_false_positive_list: typing.List[float] = []
        number_of_associated_cem_ws: typing.List[typing.Tuple[int, int]] = []

        for _, pcl_timeframe in enumerate(pcl_data):
            dgps_pose = dgps_buffer.estimate_vehicle_pose(pcl_timeframe.timestamp)
            timeframe_nbr_associated_ws = 0

            if dgps_pose is not None and len(pcl_timeframe.wheel_stopper_array) > 0:
                false_positive = FtPclHelper.calculate_cem_pcl_false_positive_utm(
                    dgps_pose,
                    pcl_timeframe.wheel_stopper_array,
                    cem_ground_truth_utm.wheelstoppers,
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
                dgps_pose = dgps_buffer.estimate_vehicle_pose(ws_timeframe.timestamp)
                timeframe_nbr_associated_ws = 0

                if dgps_pose is not None and len(ws_timeframe.pmd_lines) > 0:
                    false_positive = FtPclHelper.calculate_pmd_false_positive_utm(
                        dgps_pose,
                        ws_timeframe.pmd_lines,
                        cem_ground_truth_utm.wheelstoppers,
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
    name="CEM PFS WS False Positive",
    description="This test checks if the wheel stopper false positive rate provided by CEM is not less than"
    "the wheel stopper false positive rate of the detections comparing with the ground truth data.",
)
class FtWSFalsePositive(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtWSFalsePositive]


@teststep_definition(
    step_number=1,
    name="CEM PFS WS Field of View",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtWSFieldOfView(TestStep):
    """TestStep for assessing Field of View in WS, utilizing a custom report."""

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
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        pcl_reader = PclDelimiterReader(reader)
        pcl_data = pcl_reader.convert_to_class()

        data_df = pcl_reader.data.as_plain_df
        data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in data_df.columns]
        pcl_type = data_df.loc[:, data_df.columns.str.startswith("delimiterType")]

        if ConstantsCemInput.WSEnum in pcl_type.values:
            rows = []
            failed = 0
            for time_frame in pcl_data:
                for ws in time_frame.wheel_stopper_array:
                    if (abs(ws.start_point.x) or abs(ws.end_point.x)) > ConstantsCem.AP_G_DES_MAP_RANGE_M / 2 or (
                        abs(ws.start_point.y) or abs(ws.end_point.y)
                    ) > ConstantsCem.AP_G_DES_MAP_RANGE_M / 2:
                        failed += 1
                        values = [
                            [time_frame.timestamp],
                            [ws.delimiter_type],
                            [ws.delimiter_id],
                            [ws.start_point.x],
                            [ws.start_point.y],
                            [ws.end_point.x],
                            [ws.end_point.y],
                            [ConstantsCem.AP_G_DES_MAP_RANGE_M],
                        ]
                        rows.append(values)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(
                                values=[
                                    "Timestamp",
                                    "DelimiterType",
                                    "WSID",
                                    "x_start",
                                    "y_start",
                                    "x_end",
                                    "y_end",
                                    "LIMIT_OUTPUT_FOV",
                                ]
                            ),
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
    name="CEM PFS WS Field of View",
    description=f"""This test case checks if PFS only provides wheel stoppers which has both points inside and
                {ConstantsCem.AP_G_DES_MAP_RANGE_M} x {ConstantsCem.AP_G_DES_MAP_RANGE_M} m area centered around
                the origin of vehicle coordinate system.""",
)
class FtWSFieldOfView(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtWSFieldOfView]


@teststep_definition(
    step_number=1,
    name="CEM PFS WS ID Maintenance",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtWSIdMaintenance(TestStep):
    """TestStep for maintaining ID in WS, utilizing a custom report."""

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
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        pcl_data = PclDelimiterReader(reader).convert_to_class()
        ws_detection_data = WSDetectionReader(reader).convert_to_class()
        vedodo_buffer = VedodoReader(reader).convert_to_class()

        data_df = reader.as_plain_df
        data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in data_df.columns]
        pcl_type = data_df.loc[:, data_df.columns.str.startswith("delimiterType")]

        if ConstantsCemInput.WSEnum in pcl_type.values:
            rows = []
            failed = 0
            evaluated_cycles = 0
            for index, curTimeframe in enumerate(pcl_data):
                if index == 0:
                    continue

                prev_time_frame = pcl_data[index - 1]
                relative_motion_output = vedodo_buffer.calc_relative_motion(
                    curTimeframe.timestamp, prev_time_frame.timestamp
                )

                transformed_prev_ws = [
                    FtPclHelper.transform_pcl(ws, relative_motion_output) for ws in prev_time_frame.wheel_stopper_array
                ]

                ws_ts_index = [
                    FtPclHelper.get_PMD_timeframe_index(
                        curTimeframe.timestamp, prev_time_frame.timestamp, ws_detection_data[camera]
                    )
                    for camera in PMDCamera
                ]

                ws_timeframes = [
                    ws_detection_data[camera][ws_ts_index[int(camera)]]
                    for camera in PMDCamera
                    if ws_ts_index[int(camera)] is not None
                ]

                updated_ws = FtPclHelper.get_marker_with_associated_input(
                    transformed_prev_ws, ws_timeframes, AssociationConstants.WS_ASSOCIATION_RADIUS
                )

                associations = FtPclHelper.associate_PCL_list(
                    curTimeframe.wheel_stopper_array, updated_ws, AssociationConstants.WS_ASSOCIATION_RADIUS
                )

                for prev_ixd, curr_index in associations.items():
                    evaluated_cycles += 1
                    if updated_ws[prev_ixd].delimiter_id != curTimeframe.wheel_stopper_array[curr_index].delimiter_id:
                        failed += 1
                        values = [
                            [curTimeframe.timestamp],
                            [updated_ws[prev_ixd].delimiter_id],
                            [curTimeframe.wheel_stopper_array[curr_index].delimiter_id],
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

                fig0 = go.Figure(
                    data=[go.Table(header=dict(values=["Evaluated cycles"]), cells=dict(values=[evaluated_cycles]))]
                )
                plot_titles.append("Number of evaluated cycles")
                plots.append(fig0)
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
    name="CEM PFS WS ID Maintenance",
    description="This test case checks if the same ID is given for a wheel stopper detection"
    "which is received in the current cycle and is associated to a wheel stopper"
    "which PFS provided in the previous cycle with a unique ID.",
)
class FtWSIdMaintenance(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtWSIdMaintenance]


@teststep_definition(
    step_number=1,
    name="CEM PFS WS Output",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtWSOutput(TestStep):
    """TestStep for evaluating output in WS, utilizing a custom report."""

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
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        pcl_data = PclDelimiterReader(reader).convert_to_class()
        data_df = reader.as_plain_df
        ws_data = data_df[
            [
                "CemWs_Front_numberOfLines",
                "CemWs_Front_timestamp",
                "CemWs_Rear_numberOfLines",
                "CemWs_Rear_timestamp",
                "CemWs_Left_numberOfLines",
                "CemWs_Left_timestamp",
                "CemWs_Right_numberOfLines",
                "CemWs_Right_timestamp",
            ]
        ]

        # Check if there are PM in the data
        data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in data_df.columns]
        pcl_type = data_df.loc[:, data_df.columns.str.startswith("delimiterType")]

        # Get the first TS where there is an input in all cameras
        first_in_ts = min(
            [
                ws_data[ws_data["CemWs_Front_numberOfLines"] > 0]["CemWs_Front_timestamp"].min(),
                ws_data[ws_data["CemWs_Rear_numberOfLines"] > 0]["CemWs_Rear_timestamp"].min(),
                ws_data[ws_data["CemWs_Left_numberOfLines"] > 0]["CemWs_Left_timestamp"].min(),
                ws_data[ws_data["CemWs_Right_numberOfLines"] > 0]["CemWs_Right_timestamp"].min(),
            ]
        )

        # Get the last TS where there is an output in all cameras
        last_in_ts = max(
            [
                ws_data[ws_data["CemWs_Front_numberOfLines"] > 0]["CemWs_Front_timestamp"].max(),
                ws_data[ws_data["CemWs_Rear_numberOfLines"] > 0]["CemWs_Rear_timestamp"].max(),
                ws_data[ws_data["CemWs_Left_numberOfLines"] > 0]["CemWs_Left_timestamp"].max(),
                ws_data[ws_data["CemWs_Right_numberOfLines"] > 0]["CemWs_Right_timestamp"].max(),
            ]
        )

        delay = ConstantsCem.SYNC_INPUT_OUTPUT_CYCLES * ConstantsCem.CYCLE_PERIOD_TIME_MS
        first_out_ts = first_in_ts + (delay * 1e3)
        last_out_ts = last_in_ts + (delay * 1e3)

        if ConstantsCemInput.WSEnum in pcl_type.values:
            rows = []
            failed_timestamps = 0
            for _, cur_timeframe in enumerate(pcl_data):
                ws_number = len(cur_timeframe.wheel_stopper_array)
                cur_timestamp = cur_timeframe.timestamp
                if cur_timestamp <= first_in_ts:
                    if ws_number != 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [ws_number], ["First zone, no input WS"], ["No output"]]
                        rows.append(values)

                elif first_in_ts <= cur_timestamp < first_out_ts:
                    if ws_number != 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [ws_number], ["Second zone, input WS"], ["No output"]]
                        rows.append(values)

                elif first_out_ts <= cur_timestamp < last_in_ts:
                    if ws_number == 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [ws_number], ["Third zone, input WS"], ["Output available"]]
                        rows.append(values)

                elif last_in_ts <= cur_timestamp < last_out_ts:
                    if ws_number == 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [ws_number], ["Fourth zone, no input WS"], ["Output available"]]
                        rows.append(values)

                else:
                    if ws_number != 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [ws_number], ["Fifth zone, no input WS"], ["No output"]]
                        rows.append(values)

            if failed_timestamps:
                test_result = fc.FAIL
            else:
                test_result = fc.PASS

            header = ["Timestamp", "Number of output WS", "Evaluation section", "Expected result"]
            values = list(zip(*rows))
            fig = go.Figure(data=[go.Table(header=dict(values=header), cells=dict(values=values))])
            plot_titles.append("Test Fail report")
            plots.append(fig)
            remarks.append("")

            ws_front = ws_data[["CemWs_Front_numberOfLines", "CemWs_Front_timestamp"]].drop_duplicates()
            ws_front = ws_front.loc[(ws_front["CemWs_Front_timestamp"] != 0)]
            ws_rear = ws_data[["CemWs_Rear_numberOfLines", "CemWs_Rear_timestamp"]].drop_duplicates()
            ws_rear = ws_rear.loc[(ws_rear["CemWs_Rear_timestamp"] != 0)]
            ws_left = ws_data[["CemWs_Left_numberOfLines", "CemWs_Left_timestamp"]].drop_duplicates()
            ws_left = ws_left.loc[(ws_left["CemWs_Left_timestamp"] != 0)]
            ws_right = ws_data[["CemWs_Right_numberOfLines", "CemWs_Right_timestamp"]].drop_duplicates()
            ws_right = ws_right.loc[(ws_right["CemWs_Right_timestamp"] != 0)]

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(x=data_df["numPclDelimiters_timestamp"], y=data_df["numPclDelimiters"], name="Output")
            )
            fig.add_vrect(
                x0=data_df["numPclDelimiters_timestamp"].iat[0], x1=first_in_ts, fillcolor="#F3E5F5", layer="below"
            )
            fig.add_vrect(x0=first_in_ts, x1=first_out_ts, layer="below")
            fig.add_vrect(x0=first_out_ts, x1=last_in_ts, fillcolor="#F5F5F5", layer="below")
            fig.add_vrect(x0=last_in_ts, x1=last_out_ts, layer="below")
            fig.add_vrect(
                x0=last_out_ts, x1=data_df["numPclDelimiters_timestamp"].iat[-1], fillcolor="#F3E5F5", layer="below"
            )
            fig.add_trace(
                go.Scatter(
                    x=ws_front["CemWs_Front_timestamp"], y=ws_front["CemWs_Front_numberOfLines"], name="ws_front"
                )
            )
            fig.add_trace(
                go.Scatter(x=ws_rear["CemWs_Rear_timestamp"], y=ws_rear["CemWs_Rear_numberOfLines"], name="ws_rear")
            )
            fig.add_trace(
                go.Scatter(x=ws_left["CemWs_Left_timestamp"], y=ws_left["CemWs_Left_numberOfLines"], name="ws_left")
            )
            fig.add_trace(
                go.Scatter(
                    x=ws_right["CemWs_Right_timestamp"], y=ws_right["CemWs_Right_numberOfLines"], name="ws_right"
                )
            )
            plots.append(fig)
            plot_titles.append("Evaluated zones (Number of Wheel stoppers)")
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
    name="CEM PFS WS Output",
    description="This test case checks if PFS performs the fusion based on incoming wheel stopper detections"
    "and provide a list of tracked Wheel Stoppers.",
)
class FtWSOutput(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtWSOutput]


@teststep_definition(
    step_number=1,
    name="CEM PFS WS Unique ID",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtWSUniqueID(TestStep):
    """TestStep for ensuring unique ID in WS, utilizing a custom report."""

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
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        input_reader = PclDelimiterReader(reader)
        delimiter_data = input_reader.convert_to_class()

        # Check if there are PM in the data
        data_df = input_reader.data.as_plain_df
        data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in data_df.columns]
        pcl_type = data_df.loc[:, data_df.columns.str.startswith("delimiterType")]

        if ConstantsCemInput.WSEnum in pcl_type.values:
            rows = []
            failed = 0
            for time_frame in delimiter_data:
                ids = []
                for ws in time_frame.wheel_stopper_array:
                    if ws.delimiter_id in ids:
                        failed += 1
                        values = [[time_frame.timestamp], [ws.delimiter_id]]
                        rows.append(values)
                    else:
                        ids.append(ws.delimiter_id)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(
                    data=[go.Table(header=dict(values=["Timestamp", "DelimiterID"]), cells=dict(values=values))]
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
    name="CEM PFS WS Unique ID",
    description="This test checks that CEM provides an identifier for each wheel stopper,"
    "and the identifier is unique in each timeframe.",
)
class FtWSUniqueID(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtWSUniqueID]
