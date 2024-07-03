"""CEM SGF Test Cases"""

import logging

from tsf.core.results import DATA_NOK, FALSE, NAN, TRUE, BooleanResult
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

import sys
import typing
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from tsf.core.utilities import debug

import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import CemSignals, CustomTeststepReport, rep
from pl_parking.PLP.CEM import polygon_helper
from pl_parking.PLP.CEM.constants import ConstantsCem, ElementClassification
from pl_parking.PLP.CEM.inputs.input_CemSgfReader import SGFReader
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import VedodoReader

SIGNAL_DATA = "CEM_SGF_Latency_Compensation"


# @specification
# Test script will:
#
# 1. Load all inputs needed for this test:
# 1.1. Load timestamps present in SGF output for every timeframe of the measurement.
# 1.2. Load timestamps present in the component responsible for providing the T7 timestamps.
# 2. Check if the timestamp that is present in the SGF output is matching the one provided by the component responsible for providing the T7 timestamps(Latency compensation).
# @script OutputLatencyCompensation
@teststep_definition(
    step_number=1,
    name="CEM-SGF Latency Compensation",
    description="This test checks that SGF shall provide its signals in the Vehicle coordinate system at T7.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFOutputAtT7(TestStep):
    """TestStep for SGF output at T7, utilizing a custom report."""

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
        data = pd.DataFrame()
        plot_titles, plots, remarks = rep([], 3)

        # Load signals
        reader = self.readers[SIGNAL_DATA].signals
        input_reader = SGFReader(reader)
        data["timestamp"] = input_reader.data["SGF_timestamp"]
        vedodo_buffer = VedodoReader(reader).convert_to_class()

        # Check if data has been provided to continue with the validation
        if len(data.timestamp) or len(vedodo_buffer.buffer):
            sgf_df = data.reset_index()
            t7_df = pd.DataFrame(vedodo_buffer.buffer)

            # Check that every timestamp that is present in the SGF output is matching the one provided by T7
            if sgf_df.timestamp.equals(t7_df.timestamp):
                test_result = fc.PASS
            # Otherwise test will fail
            else:
                # Create a detailed table to show timeframe failing and the corresponding values
                test_result = fc.FAIL
                matching_data = pd.DataFrame(sgf_df.timestamp == t7_df.timestamp)
                failed_cycles = matching_data.loc[~matching_data.timestamp].index
                sgf_failing = sgf_df.filter(items=failed_cycles, axis=0).timestamp
                t7_failing = t7_df.filter(items=failed_cycles, axis=0).timestamp
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Cycle count", "SGF output", "T7 timestamp"]),
                            cells=dict(values=[failed_cycles, sgf_failing, t7_failing]),
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
                        x=sgf_df.index, y=(sgf_df.timestamp - t7_df.timestamp) / 1e3, mode="lines", name="Offset"
                    )
                ]
            )

            plot_titles.append("SGF timestamp offset ms")
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
    name="CEM-SGF Latency Compensation",
    description="This test case checks that SGF shall provide its signals in the Vehicle coordinate system at T7.",
    doors_url="",
)
class FtSGFOutputAtT7(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFOutputAtT7]


# @specification
# Test script will:
# Read the follow data from the whole recording:
# 1. CarPC.EM_Thread.SefOutputAgp.u_Used_Elements. (N)
# 2. CarPC.EM_Thread.SefOutputAgp.a_Element[k].u_NumVertices, where k=0..N-1.
# 3. Check that each CarPC.EM_Thread.SefOutputAgp.a_Element[k].u_NumVertices value is less than or equal to {AP_G_MAX_NUM_POLY_VERTEX}.
# @script StaticObjectVertexLimitCheck
@teststep_definition(
    step_number=1,
    name="CEM-SGF vertex limit",
    description="This test checks that each Static Object polygon has at most {AP_E_MAX_NUM_POLY_VERTEX_NU} vertices.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFOutputVertexLimit(TestStep):
    """TestStep for SGF output vertex limit, utilizing a custom report."""

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

        # Erase cells with undefined values to avoid messing up the calculations.
        for _, row in static_object_df.iterrows():
            for i in range(input_reader.max_num_polygons):
                if i >= row["numPolygons"]:
                    row["numVertices_polygon", i] = np.nan

        max_vertices_polygon = [
            static_object_df["numVertices_polygon", i].max(skipna=True) for i in range(input_reader.max_num_polygons)
        ]
        vertex_limit_holds = all(
            max_vertices_polygon[i] <= ConstantsCem.AP_E_MAX_NUM_POLY_VERTEX_NU
            for i in range(input_reader.max_num_polygons)
        )

        test_result = fc.PASS if vertex_limit_holds else fc.FAIL

        # Add a summary plot with signals behaviour along the rrec
        fig = go.Figure(
            data=[
                go.Scatter(y=max_vertices_polygon, mode="lines", name="Offset"),
                go.Scatter(
                    y=[ConstantsCem.AP_E_MAX_NUM_POLY_VERTEX_NU] * input_reader.max_num_polygons,
                    mode="lines",
                    name="Max Vertex",
                ),
            ]
        )

        plot_titles.append("SGF Max Vertices")
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
    name="CEM-SGF vertex limit",
    description="This test case checks that each Static Object polygon has at most {AP_E_MAX_NUM_POLY_VERTEX_NU}"
    "vertices",
    doors_url="",
)
class FtSGFOutputVertexLimit(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFOutputVertexLimit]


# @specification
# Test script will:
# 1. Load CarPC.EM_Thread.SefOutputAgp.u_Used_Elements
# 2. For all timestamps, check that CarPC.EM_Thread.SefOutputAgp.u_Used_Elements is zero.
# @script StaticObstaclesOutsideHeightRangeIgnored
@teststep_definition(
    step_number=1,
    name="CEM-SGF height range",
    description="This test checks that Static Objects are only provided in the height range "
    "{AP_E_HEIGHT_WHEEL_TRAVER_MIN_M} to {AP_E_HEIGHT_HANGING_MAX_M}",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFOutputHeightRange(TestStep):
    """TestStep for SGF output height range, utilizing a custom report."""

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
        plot_titles, plots, remarks = rep([], 3)

        # Load signals
        reader = self.readers[SIGNAL_DATA].signals
        input_reader = SGFReader(reader)
        static_object_df = input_reader.data

        test_result = fc.PASS if static_object_df["numPolygons"].max() == 0 else fc.FAIL

        # Add a summary plot with signals behaviour along the rrec
        fig = go.Figure(data=[go.Scatter(y=static_object_df["numPolygons"], mode="lines", name="Offset")])

        plot_titles.append("SGF numPolygons")
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
    name="CEM-SGF height range",
    description=f"This test checks that Static Objects are only provided in the height range "
    f"{ConstantsCem.AP_E_HEIGHT_WHEEL_TRAVER_MIN_M} to {ConstantsCem.AP_E_HEIGHT_HANGING_MAX_M}",
    doors_url="",
)
class FtSGFOutputHeightRange(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFOutputHeightRange]


# @specification
# Test script will:
# 1. Read all Static Object polygons from all timestamps. (See 38544: SWRT_CNC_PAR230_CEM_ReadingStaticObjectPolygonsFromSignals_Definition)
# 2. Check for each polygon that it is convex. (See 38545: SWRT_CNC_PAR230_CEM_CheckingTheConvexityOfAPolygon_Definition)
# @script ConvexStaticObjects
@teststep_definition(
    step_number=1,
    name="CEM-SGF convexity",
    description="This test checks that each Static Object is a convex polygon.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFOutputConvex(TestStep):
    """TestStep for SGF output convex, utilizing a custom report."""

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
        plot_titles, plots, remarks = rep([], 3)

        # Load signals
        reader = self.readers[SIGNAL_DATA].signals
        input_reader = SGFReader(reader)
        static_object_df = input_reader.data
        polygons_vertices = {}

        def are_all_polygons_convex():
            polygon_convex = []
            for _, row in static_object_df.iterrows():
                polygon_timestamp = {}
                for polygon_idx in range(int(row["numPolygons"])):
                    vertex_start_idx = int(row["vertexStartIndex_polygon", polygon_idx])
                    num_vertices = int(row["numVertices_polygon", polygon_idx])
                    vertex_list = [
                        np.array([row["vertex_x", vertex_idx], row["vertex_y", vertex_idx]])
                        for vertex_idx in range(vertex_start_idx, vertex_start_idx + num_vertices)
                    ]
                    if not polygon_helper.is_polygon_convex(vertex_list):
                        polygon_convex.append(False)
                        polygon_timestamp.setdefault(polygon_idx, vertex_list)
                    else:
                        polygon_convex.append(True)
                polygons_vertices.setdefault(row["SGF_timestamp"], polygon_timestamp)

            return polygon_convex

        test_result = fc.PASS if all(are_all_polygons_convex()) else fc.FAIL

        if test_result == fc.FAIL:
            failed_convexity_time = {time: polygon for time, polygon in polygons_vertices.items() if polygon}
            failed_convexity_idx = [list(time.keys()) for idx, time in failed_convexity_time.items()]
            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(values=["Timestamp", "Polygon ID"]),
                        cells=dict(values=[list(failed_convexity_time.keys()), failed_convexity_idx]),
                    )
                ]
            )
            plot_titles.append("Test Fail report")
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
    name="CEM-SGF convexity",
    description="This test case checks that each Static Object is a convex polygon.",
    doors_url="",
)
class FtSGFOutputConvex(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFOutputConvex]


# @specification
# Test script will:
# Test script will:
#
# 1. Read all Static Object polygons from all timestamps. (See 38544: SWRT_CNC_PAR230_CEM_ReadingStaticObjectPolygonsFromSignals_Definition )
# 2. Check for each polygon that its vertex order is counterclockwise. (See 38611: SWRT_CNC_PAR230_CEM_CheckingCCWVertexOrder)
# @script StaticObjectsPolygonsCounterclockwiseVertex
@teststep_definition(
    step_number=1,
    name="CEM-SGF ccw vertex order",
    description="This test checks that each Static Object is a polygon with counter-clockwise vertex order.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFOutputCCWVertexOrder(TestStep):
    """TestStep for SGF output with counterclockwise vertex order, utilizing a custom report."""

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
        polygons_vertices = {}

        def do_all_polygons_have_ccw_vertex_order():
            polygon_ccw_order = []
            for _, row in static_object_df.iterrows():
                polygon_timestamp = {}
                for polygon_idx in range(int(row["numPolygons"])):
                    vertex_start_idx = int(row["vertexStartIndex_polygon", polygon_idx])
                    num_vertices = int(row["numVertices_polygon", polygon_idx])
                    vertex_list = [
                        np.array([row["vertex_x", vertex_idx], row["vertex_y", vertex_idx]])
                        for vertex_idx in range(vertex_start_idx, vertex_start_idx + num_vertices)
                    ]
                    if not polygon_helper.is_vertex_order_counterclockwise_assuming_convex(vertex_list):
                        polygon_ccw_order.append(False)
                        polygon_timestamp.setdefault(polygon_idx, vertex_list)
                    else:
                        polygon_ccw_order.append(True)
                polygons_vertices.setdefault(row["SGF_timestamp"], polygon_timestamp)

            return polygon_ccw_order

        test_result = fc.PASS if all(do_all_polygons_have_ccw_vertex_order()) else fc.FAIL

        if test_result == fc.FAIL:
            failed_ccw_order_time = {time: polygon for time, polygon in polygons_vertices.items() if polygon}
            failed_ccw_order_idx = [list(time.keys()) for idx, time in failed_ccw_order_time.items()]
            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(values=["Timestamp", "Polygon ID"]),
                        cells=dict(values=[list(failed_ccw_order_time.keys()), failed_ccw_order_idx]),
                    )
                ]
            )
            plot_titles.append("Test Fail report")
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
    name="CEM-SGF ccw vertex order",
    description="This test case checks that each Static Object is a polygon with counter-clockwise vertex order.",
    doors_url="",
)
class FtSGFOutputCCWVertexOrder(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFOutputCCWVertexOrder]


@teststep_definition(
    step_number=1,
    name="CEM-SGF order by distance",
    description="This test checks that Static Objects are ordered by their distance from the origin.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFOutputOrderedByDistance(TestStep):
    """TestStep for SGF output ordered by distance, utilizing a custom report."""

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

        def distance_from_origin(row, polygon_idx):
            vertex_start_idx = int(row["vertexStartIndex_polygon", polygon_idx])
            num_vertices = int(row["numVertices_polygon", polygon_idx])
            vertex_list = [
                np.array([row["vertex_x", vertex_idx], row["vertex_y", vertex_idx]])
                for vertex_idx in range(vertex_start_idx, vertex_start_idx + num_vertices)
            ]
            return polygon_helper.dist_of_point_from_polygon(np.array([0, 0]), vertex_list)

        def are_polygons_always_ordered_by_distance():
            ordered_by_distance = []
            polygon_distances = []
            for _, row in static_object_df.iterrows():
                distances = [distance_from_origin(row, polygon_idx) for polygon_idx in range(int(row["numPolygons"]))]
                if any(distances[i] > distances[i + 1] for i in range(len(distances) - 1)):
                    ordered_by_distance.append(False)
                else:
                    ordered_by_distance.append(True)
                polygon_distances.append(distances)
            return ordered_by_distance, polygon_distances

        polygons_ordered, polygons_distances = are_polygons_always_ordered_by_distance()

        test_result = fc.PASS if all(polygons_ordered) else fc.FAIL

        df = pd.DataFrame(polygons_distances)
        df["timestamp"] = static_object_df.SGF_timestamp
        df_melted = df.melt(id_vars=["timestamp"], var_name="polygonId", value_name="distance")

        # Add a summary plot with signals behaviour along the rrec
        fig = px.scatter(df_melted, x="polygonId", y="distance", animation_frame="timestamp")
        plot_titles.append("SGF Polygons distance")
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
    name="CEM-SGF order by distance",
    description="This test case checks that Static Objects are ordered by their distance from the origin.",
    doors_url="",
)
class FtSGFOutputOrderedByDistance(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFOutputOrderedByDistance]


# @specification
# Test script will:
# 1. Read all Static Object polygons from all timestamps. (See 38544: SWRT_CNC_PAR230_CEM_ReadingStaticObjectPolygonsFromSignals_Definition)
# 2. For each timestamp, rotate the vertices of the polygons to the ROI box coordinate system using the formula (x, y) -> (cos(theta)x - sin(theta)y, sin(theta)x + cos(theta)y) where theta = CarPC.EM_Thread.OdoEstimationPortAtCem.yawAngle_rad. (counterclockwise rotation by theta).
# 3. Check that  |x|<= AP_STATIC_OBJ_ROI and |y| <= AP_STATIC_OBJ_ROI for all rotated vertex (x, y)
# @script OutputInsideROI
@teststep_definition(
    step_number=1,
    name="CEM-SGF inside ROI",
    description="This test checks that each Static Object is enclosed in the Static Obstacle ROI.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFOutputInsideROI(TestStep):
    """TestStep for SGF output inside ROI (Region of Interest), utilizing a custom report."""

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
        test_result = NAN
        plot_titles, plots, remarks = rep([], 3)

        # Load signals
        reader = self.readers[SIGNAL_DATA].signals
        input_reader = SGFReader(reader)
        static_object_df = input_reader.data

        def rotate_ccw(p, theta):
            x, y = p
            return np.cos(theta) * x - np.sin(theta) * y, np.sin(theta) * x + np.cos(theta) * y

        def are_all_vertices_inside_ROI():
            vertices_inside_roi = []
            timestamp_data = []
            for _, row in static_object_df.iterrows():
                for polygon_idx in range(int(row["numPolygons"])):
                    vertex_start_idx = int(row["vertexStartIndex_polygon", polygon_idx])
                    num_vertices = int(row["numVertices_polygon", polygon_idx])
                    for vertex_idx in range(vertex_start_idx, vertex_start_idx + num_vertices):
                        p = (row["vertex_x", vertex_idx], row["vertex_y", vertex_idx])
                        p_aligned_with_ROI_box = rotate_ccw(p, row["yaw"])

                        if (
                            abs(p_aligned_with_ROI_box[0]) > ConstantsCem.AP_STATIC_OBJ_ROI
                            or abs(p_aligned_with_ROI_box[1]) > ConstantsCem.AP_STATIC_OBJ_ROI
                        ):
                            vertices_inside_roi.append(False)
                            validation = "outside ROI"
                        else:
                            vertices_inside_roi.append(True)
                            validation = "inside ROI"
                        polygon_data = {
                            "polygon_idx": polygon_idx,
                            "vertex_idx": vertex_idx,
                            "x": p_aligned_with_ROI_box[0],
                            "y": p_aligned_with_ROI_box[1],
                            "timestamp": row["SGF_timestamp"],
                            "roi": validation,
                        }
                        timestamp_data.append(polygon_data)
            return vertices_inside_roi, timestamp_data

        all_vertices_inside_roi, vertices_to_roi = are_all_vertices_inside_ROI()

        test_result = fc.PASS if all(all_vertices_inside_roi) else fc.FAIL

        # Add a summary plot with signals behaviour along the rrec
        df = pd.DataFrame(vertices_to_roi)

        # Add a summary plot with signals behaviour along the rrec
        fig = px.scatter(
            df,
            x="x",
            y="y",
            animation_frame="timestamp",
            color="polygon_idx",
            range_x=[min(df["x"]), max(df["x"])],
            range_y=[min(df["y"]), max(df["y"])],
        )
        plot_titles.append(f"SGF Polygons in ROI {ConstantsCem.AP_STATIC_OBJ_ROI} by {ConstantsCem.AP_STATIC_OBJ_ROI}")
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
    name="CEM-SGF inside ROI",
    description="This test case checks that each Static Object is enclosed in the Static Obstacle ROI.",
    doors_url="",
)
class FtSGFOutputInsideROI(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFOutputInsideROI]


@teststep_definition(
    step_number=1,
    name="CEM-SGF wheel traversable",
    description="This test checks that a confidence for each Static Object "
    "being wheel traversable is provided and is between 0 and 100.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFOutputWheelTraversable(TestStep):
    """TestStep for SGF output wheel traversable, utilizing a custom report."""

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

        if static_object_df.filter(regex="wheelTraversableConfidence_polygon").empty:
            test_result = fc.INPUT_MISSING
        else:
            # Erase cells with undefined values to avoid messing up the calculations.
            for _, row in static_object_df.iterrows():
                for i in range(int(row["numPolygons"]), input_reader.max_num_polygons):
                    row["wheelTraversableConfidence_polygon", i] = np.nan

            max_holds = all(
                static_object_df["wheelTraversableConfidence_polygon", i].max(skipna=True) <= 100
                for i in range(input_reader.max_num_polygons)
            )

            min_holds = all(
                static_object_df["wheelTraversableConfidence_polygon", i].min(skipna=True) >= 0
                for i in range(input_reader.max_num_polygons)
            )

            test_result = fc.PASS if max_holds and min_holds else fc.FAIL

            min_confidence = [
                static_object_df["wheelTraversableConfidence_polygon", i].min(skipna=True)
                for i in range(input_reader.max_num_polygons)
            ]
            max_confidence = [
                static_object_df["wheelTraversableConfidence_polygon", i].max(skipna=True)
                for i in range(input_reader.max_num_polygons)
            ]

            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(values=["Min Confidence", "Max Confidence"]),
                        cells=dict(values=[min_confidence, max_confidence]),
                    )
                ]
            )
            plot_titles.append("Confidence range by Object")
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
    name="CEM-SGF wheel traversable",
    description="This test checks that a confidence for each Static Object "
    "being wheel traversable is provided and is between 0 and 100.",
    doors_url="",
)
class FtSGFOutputWheelTraversable(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFOutputWheelTraversable]


# @specification
# Test script will:
#
# 1. Load the whole required data for testing
# 1.1. ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.numberOfObjects. (N)
# 1.2. ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.objects[k].heightConfidences.bodyTraversable, where k=0..N-1.
#
# 2. Check if ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.objects[k].heightConfidences.bodyTraversable exists and is between 0 and 100.
# @script StaticObjectOutputBodyTraversable
@teststep_definition(
    step_number=1,
    name="CEM-SGF body traversable",
    description="This test checks that a confidence for each Static Object "
    "being body traversable is provided and is between 0 and 100.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFOutputBodyTraversable(TestStep):
    """TestStep for SGF output body traversable, utilizing a custom report."""

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

        if static_object_df.filter(regex="bodyTraversableConfidence_polygon").empty:
            test_result = fc.INPUT_MISSING
        else:
            # Erase cells with undefined values to avoid messing up the calculations.
            for _, row in static_object_df.iterrows():
                for i in range(int(row["numPolygons"]), input_reader.max_num_polygons):
                    row["bodyTraversableConfidence_polygon", i] = np.nan

            max_holds = all(
                static_object_df["bodyTraversableConfidence_polygon", i].max(skipna=True) <= 100
                for i in range(input_reader.max_num_polygons)
            )

            min_holds = all(
                static_object_df["bodyTraversableConfidence_polygon", i].min(skipna=True) >= 0
                for i in range(input_reader.max_num_polygons)
            )

            test_result = fc.PASS if max_holds and min_holds else fc.FAIL

            min_confidence = [
                static_object_df["bodyTraversableConfidence_polygon", i].min(skipna=True)
                for i in range(input_reader.max_num_polygons)
            ]
            max_confidence = [
                static_object_df["bodyTraversableConfidence_polygon", i].max(skipna=True)
                for i in range(input_reader.max_num_polygons)
            ]

            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(values=["Min Confidence", "Max Confidence"]),
                        cells=dict(values=[min_confidence, max_confidence]),
                    )
                ]
            )
            plot_titles.append("Confidence range by Object")
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
    name="CEM-SGF body traversable",
    description="This test checks that a confidence for each Static Object "
    "being body traversable is provided and is between 0 and 100.",
    doors_url="",
)
class FtSGFOutputBodyTraversable(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFOutputBodyTraversable]


@teststep_definition(
    step_number=1,
    name="CEM-SGF High",
    description="This test checks that a confidence for each Static Object "
    "being high is provided and is between 0 and 100.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFOutputHigh(TestStep):
    """TestStep for SGF output high, utilizing a custom report."""

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

        if static_object_df.filter(regex="highConfidence_polygon").empty:
            test_result = fc.INPUT_MISSING
        else:
            # Erase cells with undefined values to avoid messing up the calculations.
            for _, row in static_object_df.iterrows():
                for i in range(int(row["numPolygons"]), input_reader.max_num_polygons):
                    row["highConfidence_polygon", i] = np.nan

            max_holds = all(
                static_object_df["highConfidence_polygon", i].max(skipna=True) <= 100
                for i in range(input_reader.max_num_polygons)
            )

            min_holds = all(
                static_object_df["highConfidence_polygon", i].min(skipna=True) >= 0
                for i in range(input_reader.max_num_polygons)
            )

            test_result = fc.PASS if max_holds and min_holds else fc.FAIL

            min_confidence = [
                static_object_df["highConfidence_polygon", i].min(skipna=True)
                for i in range(input_reader.max_num_polygons)
            ]
            max_confidence = [
                static_object_df["highConfidence_polygon", i].max(skipna=True)
                for i in range(input_reader.max_num_polygons)
            ]

            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(values=["Min Confidence", "Max Confidence"]),
                        cells=dict(values=[min_confidence, max_confidence]),
                    )
                ]
            )
            plot_titles.append("Confidence range by Object")
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
    name="CEM-SGF High",
    description="This test checks that a confidence for each Static Object "
    "being high is provided and is between 0 and 100.",
    doors_url="",
)
class FtSGFOutputHigh(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFOutputHigh]


# @specification
# Test script will:
#
# Read the following data from the whole recording:
# 1. ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.numberOfObjects. (N)
# 2. ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.objects[k].heightConfidences.hanging, where k=0..N-1.
# 3. ADC5xx_Device.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.objects[k].heightConfidences.hanging is an number between 0 and 100 in all cases
# @script ConfidenceForStaticObjectsHanging
@teststep_definition(
    step_number=1,
    name="CEM-SGF Hanging",
    description="This test checks that a confidence for each Static Object"
    " being hanging is provided and is between 0 and 100.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFOutputHanging(TestStep):
    """TestStep for SGF output hanging, utilizing a custom report."""

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

        if static_object_df.filter(regex="hangingConfidence_polygon").empty:
            test_result = fc.INPUT_MISSING
        else:
            # Erase cells with undefined values to avoid messing up the calculations.
            for _, row in static_object_df.iterrows():
                for i in range(int(row["numPolygons"]), input_reader.max_num_polygons):
                    row["hangingConfidence_polygon", i] = np.nan

            max_holds = all(
                static_object_df["hangingConfidence_polygon", i].max(skipna=True) <= 100
                for i in range(input_reader.max_num_polygons)
            )

            min_holds = all(
                static_object_df["hangingConfidence_polygon", i].min(skipna=True) >= 0
                for i in range(input_reader.max_num_polygons)
            )

            test_result = fc.PASS if max_holds and min_holds else fc.FAIL

            min_confidence = [
                static_object_df["hangingConfidence_polygon", i].min(skipna=True)
                for i in range(input_reader.max_num_polygons)
            ]
            max_confidence = [
                static_object_df["hangingConfidence_polygon", i].max(skipna=True)
                for i in range(input_reader.max_num_polygons)
            ]

            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(values=["Min Confidence", "Max Confidence"]),
                        cells=dict(values=[min_confidence, max_confidence]),
                    )
                ]
            )
            plot_titles.append("Confidence range by Object")
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
    name="CEM-SGF Hanging",
    description="This test case checks that a confidence for each Static Object"
    " being hanging is provided and is between 0 and 100.",
    doors_url="",
)
class FtSGFOutputHanging(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFOutputHanging]


@teststep_definition(
    step_number=1,
    name="CEM-SGF Semantic Class",
    description="This test checks that semantic class for each Static Object is provided.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFOutputSemanticClass(TestStep):
    """TestStep for SGF output semantic class, utilizing a custom report."""

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

        def are_values_in_enum(values):
            for value in values:
                if np.isnan(value):
                    continue
                try:
                    # check if value appears in the enum
                    ElementClassification(int(value))
                except ValueError:
                    return False
            return True

        # Erase cells with undefined values to avoid messing up the calculations.
        for _, row in static_object_df.iterrows():
            for i in range(int(row["numPolygons"]), input_reader.max_num_polygons):
                row["semanticClass_polygon", i] = np.nan

        values_correct = all(
            are_values_in_enum(static_object_df["semanticClass_polygon", i].unique())
            for i in range(input_reader.max_num_polygons)
        )

        test_result = fc.PASS if values_correct else fc.FAIL

        semantic_class = [
            are_values_in_enum(static_object_df["semanticClass_polygon", i].unique())
            for i in range(input_reader.max_num_polygons)
        ]

        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Object ID", "All values are enum"]),
                    cells=dict(values=[list(range(0, input_reader.max_num_polygons)), semantic_class]),
                )
            ]
        )
        plot_titles.append("Valid Semantic Class by Object")
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
    name="CEM-SGF Semantic Class",
    description="This test case checks that semantic class for each Static Object is provided.",
    doors_url="",
)
class FtSGFOutputSemanticClass(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFOutputSemanticClass]


# @specification
# Test script will:
# 1. Load all Static Objects information from SGF output in every timestamp.
# 2. Create an empty dictionary (map), where the key represents the "static_object", and its value represents the last timeframe id the " static_object " is observed.
# 3. For each timeframe, iterate over each single detected static obstacle:
# 3.1. Retrieve the last timeframe id when a static obstacle with the same " static_object " is detected from the created dictionary.
# 3.1.1. Check if the following conditions are true:
# 3.1.1.1. The last timeframe id when a static obstacle with the same " static_object " is detected is equal to the current timeframe id – 1 and
# 3.1.1.2. The last timeframe id when a static obstacle with the same " static_object " is detected is smaller or equal to the current timeframe id -  AP_E_STA_OBJ_ID_REUSE_TIME_S.
# 3.1.1.3. If there is no static obstacle with the same " static_object " found in the dictionary then the dictionary is updated in the entry " static_object " with the current timeframe id, otherwise the test fails.
# @script StaticObjectIDReuse
@teststep_definition(
    step_number=1,
    name="CEM-SGF Static Object Id Reuse",
    description="""This test checks that in case SGF stops providing
    a Static Object with a particular Obstacle ID, the ID is not used again
    for a new Static Object for at least {ConstantsCem.AP_E_STA_OBJ_ID_REUSE_TIME_S} seconds.""",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFIDReuse(TestStep):
    """TestStep for SGF ID reuse, utilizing a custom report."""

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
        static_object_df.reset_index(drop=True, inplace=True)

        test_result = fc.NOT_ASSESSED

        # Erase cells with undefined values to avoid messing up the calculations.
        for _, row in static_object_df.iterrows():
            for i in range(int(row["numPolygons"]), input_reader.max_num_polygons):
                row["polygonId", i] = np.nan

        # invalid_id = 0.0
        if input_reader.max_num_polygons:
            # Find usage of each Static Object ID
            observation_times: typing.Dict[int, int] = {}
            # Iterate over each timeframe
            for idx, time_frame in enumerate(static_object_df.iterrows()):
                # Iterate over each object
                for static_obj_idx in range(input_reader.max_num_polygons):
                    static_obj = time_frame[1]["polygonId", static_obj_idx]
                    # Find if static object ID was already used
                    if static_obj in observation_times:
                        last_idx = int(observation_times[static_obj])
                        # Check if it was used in a cycle different from the previous one and the elapsed time > thresh
                        delta_time_id_usage = (
                            static_object_df.SGF_timestamp[idx] - static_object_df.SGF_timestamp[last_idx]
                        )
                        threshold = ConstantsCem.AP_E_STA_OBJ_ID_REUSE_TIME_S / fc.micro_second_to_seconds
                        if not (last_idx == idx - 1) and (delta_time_id_usage > threshold):
                            test_result = fc.FAIL
                            fig = go.Figure(
                                data=[
                                    go.Table(
                                        header=dict(
                                            values=["Cycle count", "Last observation cycle count", "Static Obj ID"]
                                        ),
                                        cells=dict(values=[[idx], [observation_times[idx]], [static_obj]]),
                                    )
                                ]
                            )
                            plot_titles.append("Test Fail report")
                            plots.append(fig)
                            remarks.append("")

                    observation_times[static_obj] = idx
                if test_result == fc.FAIL:
                    break
            # If test didn't fail
            if test_result != fc.FAIL:
                test_result = fc.PASS
                ids = [
                    go.Scatter(
                        x=static_object_df.SGF_timestamp,
                        y=element[1],
                        mode="lines",
                        showlegend=True,
                        name=f"{element[0][0]} [{element[0][1]}]",
                    )
                    for element in static_object_df.items()
                    if "polygonId" in element[0][0] and element[1].max()
                ]
                fig = go.Figure(data=ids)
                plot_titles.append("Test Pass report")
                plots.append(fig)
                remarks.append("")

        # No static objects detected
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
    name="CEM-SGF Static Object Id Reuse",
    description=f"""This test checks that in case SGF stops providing
    a Static Object with a particular Obstacle ID, the ID is not used again
    for a new Static Object for at least {ConstantsCem.AP_E_STA_OBJ_ID_REUSE_TIME_S} seconds.""",
    doors_url="",
)
class FtSGFIDReuse(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFIDReuse]


@teststep_definition(
    step_number=1,
    name="CEM-SGF Max Cycle Tracking",
    description="This test checks that SGF shall be able to provide Static Objects, which were detected"
    "only in earlier SGF executions.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFMaxCycleTracking(TestStep):
    """TestStep for SGF maximum cycle tracking, utilizing a custom report."""

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
        sgf_output_df = input_reader.data
        sgf_output_df.reset_index(drop=True, inplace=True)

        svc_df = sgf_output_df.filter(regex="SvcOutput")
        uss_df = sgf_output_df.filter(regex="UssOutput")
        svc_polyline_df = sgf_output_df.filter(regex="SvcPolylineOutput")
        tp_object_df = sgf_output_df.filter(regex="TpfOutput")  # ToDo: Confirm tp data shall be used

        if svc_df.empty or svc_polyline_df.empty or uss_df.empty or tp_object_df.empty:
            test_result = fc.INPUT_MISSING
        else:
            # Filter data to drop the section where CEM is receiving detections.
            # Filter SvcPointList
            no_svc_point_data = svc_df[
                (svc_df[("SvcOutput", 0)] == 0)
                & (svc_df[("SvcOutput", 1)] == 0)
                & (svc_df[("SvcOutput", 2)] == 0)
                & (svc_df[("SvcOutput", 3)] == 0)
            ].index.values

            # Filter SvcPolyline
            no_svc_polyline_data = svc_polyline_df[
                (svc_polyline_df[("SvcPolylineOutput", 0)] == 0)
                & (svc_polyline_df[("SvcPolylineOutput", 1)] == 0)
                & (svc_polyline_df[("SvcPolylineOutput", 2)] == 0)
                & (svc_polyline_df[("SvcPolylineOutput", 3)] == 0)
            ].index.values

            # Filter UssOutput
            no_uss_data = uss_df[(uss_df["UssOutput"] == 0)].index.values

            # Filter TPFOutput
            no_tpf_data = tp_object_df[(tp_object_df["TpfOutput"] == 0)].index.values

            if no_svc_point_data.size and no_svc_polyline_data.size and no_uss_data.size and no_tpf_data.size:
                # No CEM Detections during some sections of the recording.
                # Drop cycles were at least one input was received.
                no_svc_data = set(no_svc_point_data).intersection(set(no_svc_polyline_data))
                no_cem_data = list(set(no_uss_data).intersection(set(no_tpf_data)).intersection(no_svc_data))
                failed_cycles = []
                sgf_failure = []
                no_cem_input = []
                for meas_idx, meas in enumerate(no_cem_data):
                    # Get first cycle where no inputs were received and remove following ones if consecutive.
                    if not meas_idx:
                        no_cem_input.append(meas)
                        continue
                    # If next index is not consecutive add it to no CEM input list.
                    if meas != no_cem_data[meas_idx - 1] + 1:
                        no_cem_input.append(meas)
                for cycle in no_cem_input:
                    thresh_cycle = cycle + ConstantsCem.MAX_CYCLE_NUM
                    if thresh_cycle <= len(sgf_output_df):
                        sgf_output_subset = sgf_output_df["numPolygons"][cycle:thresh_cycle]
                        if sgf_output_subset.all() >= 0:
                            if sgf_output_df["numPolygons"][thresh_cycle + 1] >= 0:
                                # SGF keeps tracking detected objects after {MAX_CYCLE_NUM} of CEM not providing inputs.
                                failed_cycles.append(cycle)
                                sgf_failure.append("Tracking objects after Thresh")
                        else:
                            # SGF doesn't keep the track of detected objects for at least {MAX_CYCLE_NUM} after there
                            # is no input from CEM.
                            failed_cycles.append(cycle)
                            sgf_failure.append("Looses tracking before Thresh")

                if not failed_cycles:
                    test_result = fc.PASS
                else:
                    test_result = fc.FAIL
                    fig = go.Figure(
                        data=[
                            go.Table(
                                header=dict(values=["Last Cycle with CEM input", "SGF failure", "Cycles Threshold"]),
                                cells=dict(
                                    values=[
                                        failed_cycles,
                                        sgf_failure,
                                        [ConstantsCem.MAX_CYCLE_NUM] * len(failed_cycles),
                                    ]
                                ),
                            )
                        ]
                    )
                    plot_titles.append("Test Fail report")
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
    name="CEM-SGF Max Cycle Tracking",
    description="This test case checks that SGF shall be able to provide Static Objects, which were detected"
    "only in earlier SGF executions.",
    doors_url="",
)
class FtSGFMaxCycleTracking(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFMaxCycleTracking]


# @specification
# Test script will:
# 1. Load SGF inputs needed for testing:
# 1.1. Load SvcPointList.
# 1.2. Load SvcPolylineList.
# 1.3. Load USS data.
# 1.4. Load TP data
# 1.5. Load SGF output.
# 2. Split data according to each scenario:
# 2.1. Get first timestamp where any of the input’s sig_state == OK
# 2.2. Get first timestamp where sig_state changes to OK = (1) for all the cameras.
# 3. Check following conditions:
# 3.1. Confirm that in first part of the recording there is no SGF output.
# 3.2. Starting from timestamp obtained in step 2.1 + time tolerance(15 cycles) through the end of the recording, confirm SGF output provide > 0 and <= 4 objects.
# 3.3. Timestamp obtained in step 2.2 is used to split last section in plot generated
# @script SGF_SigStateOK
@teststep_definition(
    step_number=1,
    name="CEM-SGF AL Signal State",
    description="SGF shall only process input signals if their signal state is AL_SIG_STATE_OK",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFSigStateOk(TestStep):
    """TestStep for SGF signal state, utilizing a custom report."""

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
        self.result.measured_result = NAN
        plot_titles, plots, remarks = rep([], 3)

        # Load signals
        reader = self.readers[SIGNAL_DATA].signals
        input_reader = SGFReader(reader)
        sgf_output_df = input_reader.data
        sgf_inputs_df = sgf_output_df[["SvcSigState", "SvcPolylineSigState", "TpfSigState", "UssSigState"]].copy()
        sgf_input_timestamp_df = sgf_output_df[
            ["SvcTimestamp", "SvcPolylineTimestamp", "TpfTimestamp", "UssTimestamp"]
        ].copy()
        # sgf_input_timestamp_df_nan = np.where(sgf_input_timestamp_df == 0, np.nan, sgf_input_timestamp_df)
        all_input_timestamps_ok = [
            max(sgf_input_timestamp_df[sensor_input]) for sensor_input in sgf_input_timestamp_df.columns
        ]
        if len(sgf_inputs_df.columns) < 4:
            test_result = fc.INPUT_MISSING  # noqa: F841
        elif not all(all_input_timestamps_ok):
            self.result.measured_result = DATA_NOK
        else:
            # Get first time when any of the input’s sig_state == OK and find SGF output for it.
            # ToDo: Confirm time tolerance
            processing_tolerance = ConstantsCem.CYCLE_PERIOD_TIME_MS * ConstantsCem.NUM_OF_CYCLES_FOR_OUTPUT * 1e3
            first_section_end = sgf_inputs_df[sgf_inputs_df.isin([fc.AL_SIG_STATE_OK]).any(axis=1)].index[0]
            first_section_end_time = sgf_input_timestamp_df.loc[first_section_end].min()
            sgf_output_closest = sgf_output_df.loc[sgf_output_df.SGF_timestamp > first_section_end_time].index[0]

            # Get timestamp where sig_state changes to OK = (1) for all the cameras.
            camera_sig_state = sgf_inputs_df.filter(regex="Svc")
            second_section_end = camera_sig_state[camera_sig_state.isin([fc.AL_SIG_STATE_OK]).all(axis=1)].index[0]
            second_section_end_time = sgf_input_timestamp_df.loc[second_section_end].min()
            sgf_output_closest_next = sgf_output_df.loc[sgf_output_df.SGF_timestamp > second_section_end_time].index[0]

            failing_section = []
            expected_result = []
            result_provided = []
            section_range = []

            # Confirm there is no SGF output at first section
            if max(sgf_output_df.loc[:sgf_output_closest, "numPolygons"]) == 0:
                first_section_result = True
            else:
                first_section_result = False
                failing_section.append("First scenario")
                expected_result.append("numPolygons = 0")
                result_provided.append(max(sgf_output_df.loc[:sgf_output_closest, "numPolygons"]))
                section_range.append(
                    f"{sgf_output_df.SGF_timestamp.iat[0]} - " f"{sgf_output_df.SGF_timestamp[sgf_output_closest]}"
                )

            # Starting from next timestamp after one obtained in step 2.1
            # Confirm SGF output provide > 0 and <= 4 objects.
            second_section_start_time = first_section_end_time + processing_tolerance
            output_second_section_time = sgf_output_df.loc[
                sgf_output_df.SGF_timestamp > second_section_start_time
            ].index[0]
            outputs_from_valid_inputs = sgf_output_df.loc[output_second_section_time:, "numPolygons"]

            if min(outputs_from_valid_inputs) > 0 and max(outputs_from_valid_inputs) <= 4:
                second_section_result = True
            else:
                second_section_result = False
                failing_section.append("Second scenario")
                expected_result.append("0 < numPolygons <= 4")
                result_provided.append(f"min: {min(outputs_from_valid_inputs)} max: {max(outputs_from_valid_inputs)}")
                section_range.append(
                    f"{sgf_output_df.SGF_timestamp[output_second_section_time]} - "
                    f"{sgf_output_df.SGF_timestamp.iat[-1]}"
                )

            # Test will pass if all sections pass
            if first_section_result and second_section_result:
                self.result.measured_result = fc.PASS
            else:
                self.result.measured_result = fc.FAIL
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(
                                values=[
                                    "Failing section",
                                    "SGF expected Objects",
                                    "SGF Objects provided",
                                    "Output section range",
                                ]
                            ),
                            cells=dict(values=[failing_section, expected_result, result_provided, section_range]),
                        )
                    ]
                )
                plot_titles.append("Test Fail Summary")
                plots.append(fig)
                remarks.append("")

            # Add a summary plot with signals behaviour along the rrec
            fig = go.Figure(
                data=[
                    go.Scatter(
                        x=sgf_output_df.SGF_timestamp, y=sgf_output_df.numPolygons, mode="lines", name="SGF output"
                    ),
                    go.Scatter(
                        x=sgf_input_timestamp_df.Front_SvcTimestamp,
                        y=sgf_inputs_df.Front_SvcSigState,
                        mode="lines",
                        name="sigState_Front_Svc",
                    ),
                    go.Scatter(
                        x=sgf_input_timestamp_df.Rear_SvcTimestamp,
                        y=sgf_inputs_df.Rear_SvcSigState,
                        mode="lines",
                        name="sigState_Rear_Svc",
                    ),
                    go.Scatter(
                        x=sgf_input_timestamp_df.Left_SvcTimestamp,
                        y=sgf_inputs_df.Left_SvcSigState,
                        mode="lines",
                        name="sigState_Left_Svc",
                    ),
                    go.Scatter(
                        x=sgf_input_timestamp_df.Right_SvcTimestamp,
                        y=sgf_inputs_df.Right_SvcSigState,
                        mode="lines",
                        name="sigState_Right_Svc",
                    ),
                    go.Scatter(
                        x=sgf_input_timestamp_df.UssTimestamp,
                        y=sgf_inputs_df.UssSigState,
                        mode="lines",
                        name="sigState_Uss",
                    ),
                ]
            )

            fig.add_vrect(
                x0=sgf_output_df.SGF_timestamp.iat[0],
                x1=sgf_output_df.SGF_timestamp[sgf_output_closest],
                fillcolor="#BBDEFB",
                layer="below",
            )

            fig.add_vrect(
                x0=sgf_output_df.SGF_timestamp[output_second_section_time],
                x1=sgf_output_df.SGF_timestamp[sgf_output_closest_next],
                fillcolor="#BBDEFB",
                layer="below",
            )

            fig.add_vrect(
                x0=sgf_output_df.SGF_timestamp[sgf_output_closest_next],
                x1=sgf_output_df.SGF_timestamp.iat[-1],
                fillcolor="#BBDEFB",
                layer="below",
            )

            plot_titles.append(f"Test {self.result.measured_result} report")
            plots.append(fig)
            remarks.append("")

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@testcase_definition(
    name="CEM-SGF AL Signal State",
    description="This test case checks that SGF shall only process input signals if their signal state "
    "is AL_SIG_STATE_OK",
    doors_url="",
)
class FtSGFSigStateOk(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFSigStateOk]


@teststep_definition(
    step_number=1,
    name="CEM-SGF special case WS",
    description="This test case checks if CEM has output when only SVC wheel stopper input is received.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFSpecialCaseWS(TestStep):
    """TestStep for SGF special case WS, utilizing a custom report."""

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

        # # Add a summary plot with signals behaviour along the rrec
        fig = go.Figure(
            data=[
                go.Scatter(
                    x=static_object_df.SGF_timestamp,
                    y=static_object_df.numPolygons,
                    mode="lines",
                    name="SGF detected Objects",
                )
            ]
        )

        plot_titles.append("SGF Output based on SVC wheel stopper input")
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
    name="CEM-SGF special case WS",
    description="This test case checks if CEM has output when only SVC wheel stopper input is received.",
    doors_url="",
)
class FtSGFSpecialCaseWS(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFSpecialCaseWS]


# @specification
# Test script will:
# 1. Load the whole required data for testing:
# 1.1. CarPC.EM_Thread.SefOutputAgp.u_Used_Elements. (N)
# 1.2. CarPC.EM_Thread.SefOutputAgp.a_Element[k].e_ElementClassification, where k=0..N-1.
# 2. For each element check if the value of e_ElementClassification is Unknown.
# @script UnknownClassStaticObjectsUSSOnly
@teststep_definition(
    step_number=1,
    name="CEM-SGF special case SUSS",
    description="This test checks the output static objects are given " "Unknown" " semantic class.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFSpecialCaseSUSS(TestStep):
    """TestStep for SGF special cases USS, utilizing a custom report."""

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

        def are_all_values_unknown(values):
            return all(
                np.isnan(value) or ElementClassification(int(value)) == ElementClassification.AGP_CLASS_UNKNOWN
                for value in values
            )

        # Erase cells with undefined values to avoid messing up the calculations.
        for _, row in static_object_df.iterrows():
            for i in range(int(row["numPolygons"]), input_reader.max_num_polygons):
                row["semanticClass_polygon", i] = np.nan

        values_correct = all(
            are_all_values_unknown(static_object_df["semanticClass_polygon", i].unique())
            for i in range(input_reader.max_num_polygons)
        )

        test_result = fc.PASS if values_correct else fc.FAIL

        unique_semantic_class = [
            are_all_values_unknown(static_object_df["semanticClass_polygon", i].unique())
            for i in range(input_reader.max_num_polygons)
        ]

        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Object ID", "Semantic Class Unknown"]),
                    cells=dict(values=[list(range(0, input_reader.max_num_polygons)), unique_semantic_class]),
                )
            ]
        )
        plot_titles.append("Test report of " "Unknown" " semantic class")
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
    name="CEM-SGF special case SUSS",
    description="This test case checks the output static objects are given " "Unknown" " semantic class.",
    doors_url="",
)
class FtSGFSpecialCaseSUSS(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFSpecialCaseSUSS]


@teststep_definition(
    step_number=1,
    name="CEM-SGF special case HUSS",
    description="This test checks that static objects output have "
    "elevation categories confidence < {PAR_ELEV_MIN_CONFIDENCE}",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSGFSpecialCaseHUSS(TestStep):
    """TestStep for SGF special cases HUSS, utilizing a custom report."""

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
        objs_df = input_reader.data

        if objs_df.filter(regex="hangingConfidence_polygon").empty:
            test_result = fc.INPUT_MISSING
        else:
            # Checking the elevation category confidence of all detected static objects,
            # which shall be lower than PAR_ELEV_MIN_CONFIDENCE

            def confidence_below_threshold(df, elevation_category):
                elevation_confidence = []
                max_elevation_confi = {}
                for i in range(input_reader.max_num_polygons):
                    object_max_confi = df[elevation_category, i].max(skipna=True)
                    elevation_confidence.append(object_max_confi < ConstantsCem.AP_E_STA_OBJ_ELEV_CONF_MIN_NU)
                    max_elevation_confi[i] = object_max_confi
                return all(elevation_confidence), max_elevation_confi

            high_confi, max_high_confi = confidence_below_threshold(objs_df, "highConfidence_polygon")
            hanging_confi, max_hanging_confi = confidence_below_threshold(objs_df, "hangingConfidence_polygon")
            body_traversable_confi, max_body_traversable_confi = confidence_below_threshold(
                objs_df, "bodyTraversableConfidence_polygon"
            )
            wheel_traversable_confi, max_wheel_traversable_confi = confidence_below_threshold(
                objs_df, "wheelTraversableConfidence_polygon"
            )

            test_result = (
                fc.PASS
                if (high_confi and hanging_confi and body_traversable_confi and wheel_traversable_confi)
                else fc.FAIL
            )

            objects_used = list(range(input_reader.max_num_polygons))
            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(
                            values=[
                                "Object ID",
                                "Max High confidence",
                                "Max Hanging confidence",
                                "Max Body Traversable confidence",
                                "Max Wheel Traversable confidence",
                                "AP E STA OBJ ELEV CONF MIN NU",
                            ]
                        ),
                        cells=dict(
                            values=[
                                objects_used,
                                list(max_high_confi.values()),
                                list(max_hanging_confi.values()),
                                list(max_body_traversable_confi.values()),
                                list(max_wheel_traversable_confi.values()),
                                [ConstantsCem.AP_E_STA_OBJ_ELEV_CONF_MIN_NU] * input_reader.max_num_polygons,
                            ]
                        ),
                    )
                ]
            )
            plot_titles.append("Test report of Elevation Confidence")
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
    name="CEM-SGF special case HUSS",
    description="This test checks that static objects output have "
    "elevation categories confidence < {PAR_ELEV_MIN_CONFIDENCE}",
    doors_url="",
)
class FtSGFSpecialCaseHUSS(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFSpecialCaseHUSS]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.
    """
    test_bsigs = [
        r"C:\Users\uic05849\OneDrive - Continental AG\CEM\bsig_measurments\1_2023.11.13_at_10.34.03_camera-mi_128.bsig"
    ]

    debug(
        # [FtSGFOutputAtT7, FtSGFOutputVertexLimit, FtSGFOutputHeightRange, FtSGFOutputConvex,
        # FtSGFOutputCCWVertexOrder, FtSGFOutputOrderedByDistance, FtSGFOutputInsideROI, FtSGFOutputWheelTraversable,
        # FtSGFOutputBodyTraversable, FtSGFOutputHigh, FtSGFOutputHanging, FtSGFOutputSemanticClass, FtSGFIDReuse,
        # FtSGFMaxCycleTracking, FtSGFSigStateOk, FtSGFSpecialCaseUSS, FtSGFSpecialCaseSPTS,
        # FtSGFSpecialCaseWS, FtSGFSpecialCaseSUSS, FtSGFSpecialCaseHUSS],
        [FtSGFSigStateOk],
        *test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
        kpi_report=False,
        dev_report=True,
        # statistics=StatisticsExample,
    )
    _log.debug("All done.")


if __name__ == "__main__":
    working_directory = Path(r"D:\carrots\CEM")

    out_folder = working_directory / "out"

    main(temp_dir=out_folder, open_explorer=True)
