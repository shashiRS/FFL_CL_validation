#!/usr/bin/env python3
"""SWKPI_CNC_SGF_StaticObstacleInflationRate"""

import logging
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from tsf.core.common import AggregateFunction, PathSpecification, RelationOperator
from tsf.core.results import DATA_NOK, ExpectedResult, Result
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_pre_processor,
    register_side_load,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.io.sideload import JsonSideLoad

import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    convert_dict_to_pandas,
    get_color,
    rep,
)
from pl_parking.PLP.CEM.constants import ConstantsSGF as cs
from pl_parking.PLP.CEM.SGF.ft_helper import SGFPreprocessorLoad, SGFSignals

TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "<uib11434>"
__copyright__ = "2023-2024, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "StaticObstacleInflationRate"
ALIAS_JSON = "static_obstacle_inflation_rate"
sgf_obj = SGFSignals()


@teststep_definition(
    step_number=1,
    name="Static Obstacle Inflation Rate",
    description=f"This test case checks if SGF provides Static Objects, whose maximal distances "
    f"from their corresponding StaticObstacles are less than {cs.AP_E_STA_OBJ_INFLATION_M} "
    f"in at least {cs.AP_E_STA_OBJ_INFLATION_RATE_NU}% of the occurrences.",
    expected_result=ExpectedResult(
        operator=RelationOperator.GREATER,
        numerator=cs.AP_E_STA_OBJ_INFLATION_RATE_NU,
        unit="%",
        aggregate_function=AggregateFunction.MEAN,
    ),
)
@register_signals(SIGNAL_DATA, SGFSignals)
@register_side_load(
    alias=ALIAS_JSON,
    side_load=JsonSideLoad,
    path_spec=PathSpecification(
        folder=r"s3://par230-prod-data-lake-sim/gt_labels/", extension=".json", s3=True
    ),
)
@register_pre_processor(alias="load_gt_and_sim_data", pre_processor=SGFPreprocessorLoad)
class TestStepStaticObstacleInflationRate(TestStep):
    """Test step definition."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step."""
        super().__init__()
        self.test_result = fc.INPUT_MISSING
        self.sig_sum = None

    @staticmethod
    def max_distance_to_overlap(non_overlap_poly, overlap_points):
        """Compute maximum distance from boundary points of non-overlapping region to overlap boundary."""
        max_distance = 0
        max_point_pair = None

        # Extract boundary points from the non-overlapping region
        boundary_points = list(non_overlap_poly.exterior.coords) if isinstance(non_overlap_poly, Polygon) else []
        if isinstance(non_overlap_poly, MultiPolygon):
            for poly in non_overlap_poly.geoms:
                boundary_points.extend(list(poly.exterior.coords))

        # Calculate the maximum distance from each non-overlap boundary point to the nearest overlap boundary
        for boundary_point in boundary_points:
            point_geom = Point(boundary_point)
            nearest_overlap_point = min(overlap_points, key=lambda p: point_geom.distance(Point(p)))
            distance_to_nearest = point_geom.distance(Point(nearest_overlap_point))

            # Update maximum distance
            if distance_to_nearest > max_distance:
                max_distance = distance_to_nearest
                max_point_pair = (boundary_point, nearest_overlap_point)

        return max_distance, max_point_pair

    @staticmethod
    def plot_polygons_with_distances(gt_polygon, sim_polygon, non_overlap_regions, overlap, max_distances):
        """Visualize polygons, overlap area, and maximum distance lines."""
        fig, ax = plt.subplots()

        if not gt_polygon.is_empty:
            # Plot polygon GT
            x, y = gt_polygon.exterior.xy
            ax.plot(x, y, color="green", label="Polygon GT")

        if not sim_polygon.is_empty:
            # Plot polygon SIM
            x, y = sim_polygon.exterior.xy
            ax.plot(x, y, color="blue", label="Polygon SIM")

        if not non_overlap_regions.is_empty:
            # Plot the non-overlapping regions of SIM
            if isinstance(non_overlap_regions, Polygon):
                # For single Polygon, plot it directly
                x, y = non_overlap_regions.exterior.xy
                ax.fill(x, y, color="blue", alpha=0.3, label="Non-overlapping area of SIM")
            elif isinstance(non_overlap_regions, MultiPolygon):
                # For MultiPolygon, plot each polygon individually
                for i, region in enumerate(non_overlap_regions.geoms):
                    x, y = region.exterior.xy
                    ax.fill(x, y, color="blue", alpha=0.3, label="Non-overlapping area of SIM" if i == 0 else "")

        if not overlap.is_empty:
            # Plot the overlapping area
            if isinstance(overlap, Polygon):
                # For single Polygon, plot it directly
                x, y = overlap.exterior.xy
                ax.fill(x, y, color="red", alpha=0.3, label="Overlap Area")
            elif isinstance(overlap, MultiPolygon):
                # For MultiPolygon, plot each polygon individually
                for i, region in enumerate(overlap.geoms):
                    x, y = region.exterior.xy
                    ax.fill(x, y, color="red", alpha=0.3, label="Overlap Area" if i == 0 else "")

        if max_distances:
            # Plot maximum distance lines
            for i, (max_dist, max_point_pair) in enumerate(max_distances):
                if max_point_pair is not None:
                    start, end = max_point_pair
                    line = LineString([start, end])
                    x, y = line.xy
                    ax.plot(x, y, color="purple", linestyle="--", label=f"Max Dist {i + 1} ({max_dist:.8f})")
                    ax.plot(start[0], start[1], "bo")  # Non-overlap boundary point
                    ax.plot(end[0], end[1], "ro")  # Nearest overlap point

        ax.set_aspect("equal")
        ax.legend()
        plt.xlabel("X Coordinates")
        plt.ylabel("Y Coordinates")
        plt.title("Maximum Distances from Non-Overlap Regions of SIM to Overlap Boundary")
        plt.show()

    def max_distances_non_overlap_to_overlap_boundary(self, gt_polygon, sim_polygon):
        """Compute and plot maximum distances from non-overlapping regions of SIM to overlap boundary of GT."""
        max_distances = []

        # Compute the overlapping area
        overlap = sim_polygon.intersection(gt_polygon)

        if not overlap.is_empty:
            # Compute the non-overlapping area of SIM
            sim_non_overlap_regions = sim_polygon.difference(gt_polygon)
            # Get the boundary points of the overlapping area
            overlap_points = []
            if isinstance(overlap, Polygon):
                overlap_points = list(overlap.exterior.coords)
            elif isinstance(overlap, MultiPolygon):
                for poly in overlap.geoms:  # Accessing individual polygons in MultiPolygon
                    overlap_points.extend(list(poly.exterior.coords))

            # Calculate maximum distance for each non-overlapping region
            if isinstance(sim_non_overlap_regions, Polygon):
                max_dist, max_point_pair = self.max_distance_to_overlap(sim_non_overlap_regions, overlap_points)
                max_distances.append((max_dist, max_point_pair))
            elif isinstance(sim_non_overlap_regions, MultiPolygon):
                for region in sim_non_overlap_regions.geoms:
                    max_dist, max_point_pair = self.max_distance_to_overlap(region, overlap_points)
                    max_distances.append((max_dist, max_point_pair))

            # Find the tuple with the greatest distance
            max_of_max_dist = max(max_distances, key=lambda x: x[0])

        else:
            # In case of no overlap between gt_polygon and sim_polygon, return a negative value
            max_of_max_dist = (-1, None)

        # Plot the polygons and the distances for visualisation purpose
        # self.plot_polygons_with_distances(gt_polygon, sim_polygon, sim_non_overlap_regions, overlap, max_distances)

        # Return maximal distance of non-overlapping area to GT
        return max_of_max_dist[0]

    @staticmethod
    def evaluate_results(distances):
        """
        Check if {AP_E_STA_OBJ_INFLATION_RATE_NU} of the values in the distances list are less than
        AP_E_STA_OBJ_INFLATION_M
        """
        distance_in_range = sum(1 for distance in distances if 0 <= distance < cs.AP_E_STA_OBJ_INFLATION_M)
        distance_in_range_percentage = distance_in_range * 100 / len(distances)
        if distance_in_range > len(distances) * cs.AP_E_STA_OBJ_INFLATION_RATE_NU / 100:
            test_result = fc.PASS
            evaluation = " ".join(
                f"The evaluation is <b>PASSED</b>, maximal distances from non-overlapping regions of SIM to "
                f"overlap boundary of GT are less than {cs.AP_E_STA_OBJ_INFLATION_M}m in "
                f"<b>{distance_in_range_percentage:.2f}%</b> of cases. "
                f"Minimum threshold is <b>{cs.AP_E_STA_OBJ_INFLATION_RATE_NU}%</b>".split()
            )
        else:
            test_result = fc.FAIL
            evaluation = " ".join(
                f"The evaluation is <b>FAILED</b>, maximal distances from non-overlapping regions of SIM to "
                f"overlap boundary of GT are less than {cs.AP_E_STA_OBJ_INFLATION_M}m in "
                f"<b>{distance_in_range_percentage:.2f}%</b> of cases. "
                f"Minimum threshold is <b>{cs.AP_E_STA_OBJ_INFLATION_RATE_NU}%</b>".split()
            )

        return test_result, evaluation

    def process(self):
        """Process the simulated files."""
        _log.debug("Starting processing...")

        # Update the details from the results page with the needed information. All the information from
        # self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Initializing the result with data nok
        self.result.measured_result = DATA_NOK

        # Create empty lists for titles, plots and remarks, if they are needed.
        # Plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)

        # Initializing the dictionary with data for final evaluation table
        signal_summary = {}
        # Initializes a list to store all the distances to be evaluated
        eval_distances = []
        # Initializes a list to store all the timestamps where distances are evaluated
        eval_timestamps = []

        summary_key = "Static Obstacle Inflation Rate"

        gt_df, sim_df = self.pre_processors["load_gt_and_sim_data"]
        plt_timestamp = sim_df[sgf_obj.Columns.SGF_TIMESTAMP].tolist()  # used for plotting

        if not gt_df.empty:
            # filter only valid outputs
            gt_df = gt_df[gt_df["gt_sig_status"] == "AL_SIG_STATE_OK"]
            # filter frames where only one convex Static Obstacle is present.
            gt_df = gt_df[gt_df["gt_no_of_objects"] == 1]

            # filter only valid outputs
            sim_df = sim_df[sim_df[sgf_obj.Columns.SGF_SIGSTATUS] == 1]
            # filter frames where only one convex Static Obstacle is present.
            sim_df = sim_df[sim_df[sgf_obj.Columns.SGF_NUMBER_OF_POLYGONS] == 1]

            gt_sgf_timestamp = gt_df["gt_sgf_timestamp"].tolist()
            sim_sgf_timestamp = sim_df[sgf_obj.Columns.SGF_TIMESTAMP].tolist()

            common_timestamps = [x for x in gt_sgf_timestamp if x in sim_sgf_timestamp]

            for timestamp in common_timestamps:

                gt_frame_data = gt_df[gt_df["gt_sgf_timestamp"] == timestamp]
                sim_frame_data = sim_df[sim_df[sgf_obj.Columns.SGF_TIMESTAMP] == timestamp]

                gt_vertex_x = gt_frame_data.filter(regex="gt_vertex_x").values
                gt_vertex_y = gt_frame_data.filter(regex="gt_vertex_y").values

                sim_vertex_x = sim_frame_data.filter(regex=sgf_obj.Columns.SGF_VERTEX_X).values
                sim_vertex_y = sim_frame_data.filter(regex=sgf_obj.Columns.SGF_VERTEX_Y).values

                # num of vertices per frame
                gt_num_vertices = gt_frame_data["gt_no_of_vertices"].values
                sim_num_vertices = sim_frame_data[sgf_obj.Columns.SGF_NUMBER_OF_VERTICES].values

                valid_gt_vertex_x = gt_vertex_x[0, 0 : gt_num_vertices[0]]
                valid_gt_vertex_y = gt_vertex_y[0, 0 : gt_num_vertices[0]]

                valid_sim_vertex_x = sim_vertex_x[0, 0 : sim_num_vertices[0]]
                valid_sim_vertex_y = sim_vertex_y[0, 0 : sim_num_vertices[0]]

                gt_polygon = Polygon(np.column_stack((valid_gt_vertex_x, valid_gt_vertex_y)))
                sim_polygon = Polygon(np.column_stack((valid_sim_vertex_x, valid_sim_vertex_y)))

                distance = self.max_distances_non_overlap_to_overlap_boundary(gt_polygon, sim_polygon)

                eval_timestamps.append(timestamp)
                eval_distances.append(distance)

            self.test_result, evaluation = self.evaluate_results(eval_distances)

        else:
            evaluation = " ".join("Ground truth data <b>not available</b>, evaluation can't be performed.".split())

        # Report result status
        if self.test_result == fc.INPUT_MISSING:
            self.result.measured_result = DATA_NOK
        elif self.test_result == fc.PASS:
            self.result.measured_result = Result(100, unit="%")
        elif self.test_result == fc.FAIL:
            self.result.measured_result = Result(0, unit="%")

        signal_summary[summary_key] = evaluation
        remark = " ".join("Inflation rate evaluation of Static Objects.".split())
        self.sig_sum = convert_dict_to_pandas(
            signal_summary=signal_summary, table_header_left="Evaluation", table_remark=remark
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        result_df = {
            "Verdict": {"value": self.test_result.title(), "color": get_color(self.test_result)},
            fc.REQ_ID: ["1522157"],
            fc.TESTCASE_ID: ["39290"],
            fc.TEST_DESCRIPTION: [
                f"Check if SGF provides Static Objects, whose maximal distances from their "
                f"corresponding Static Obstacles are less than {cs.AP_E_STA_OBJ_INFLATION_M} in at least "
                f"{cs.AP_E_STA_OBJ_INFLATION_RATE_NU}% of the occurrences."
            ],
        }

        self.result.details["Additional_results"] = result_df

        fig = go.Figure()

        # Flags to track legend
        added_no_overlap = False
        added_overlap = False
        added_above_threshold = False

        # Draw the horizontal line that represents the threshold
        fig.add_trace(
            go.Scatter(
                x=[min(plt_timestamp), max(plt_timestamp)],  # Span the whole x-axis
                y=[cs.AP_E_STA_OBJ_INFLATION_M, cs.AP_E_STA_OBJ_INFLATION_M],  # Constant y for horizontal line
                mode="lines",
                line=dict(color="green", width=2),
                name=f"Threshold Line at {cs.AP_E_STA_OBJ_INFLATION_M} meters",
                legendgroup="threshold",
                showlegend=True,
            )
        )

        for x, y in zip(eval_timestamps, eval_distances):
            # Draw a vertical line in orange for cases where no overlap between sim and gt polygons take place
            if y < 0:
                fig.add_trace(
                    go.Scatter(
                        x=[x, x],
                        y=[0, -0.1],
                        mode="lines+markers",
                        line=dict(color="orange", width=2),
                        name="No Overlapping Polygons",
                        legendgroup="no_overlap",
                        showlegend=not added_no_overlap,  # Show legend only for the first trace
                    )
                )
                added_no_overlap = True  # Mark legend as added
            # Draw a vertical line in blue for cases where distances are under the threshold
            else:
                fig.add_trace(
                    go.Scatter(
                        x=[x, x],
                        y=[0, min(y, cs.AP_E_STA_OBJ_INFLATION_M)],
                        mode="lines+markers",
                        line=dict(color="blue", width=2),
                        name="Distance in range",
                        legendgroup="overlap",
                        showlegend=not added_overlap,
                    )
                )
                added_overlap = True
                # Draw the distance in red for the part that exceeds the threshold
                if y > cs.AP_E_STA_OBJ_INFLATION_M:
                    fig.add_trace(
                        go.Scatter(
                            x=[x, x],
                            y=[cs.AP_E_STA_OBJ_INFLATION_M, y],
                            mode="lines+markers",
                            line=dict(color="red", width=2),
                            name="Distance that exceeds the threshold",
                            legendgroup="overlap",
                            showlegend=not added_above_threshold,
                        )
                    )
                    added_above_threshold = True

        if max(eval_distances) < cs.AP_E_STA_OBJ_INFLATION_M:
            y_min = -0.15
            y_max = cs.AP_E_STA_OBJ_INFLATION_M + 0.05
        else:
            y_min = -0.15
            y_max = max(eval_distances) + max(eval_distances) / 2

        fig.update_layout(
            xaxis=dict(range=[min(plt_timestamp), max(plt_timestamp)]),  # Explicit x-axis range
            yaxis=dict(range=[y_min, y_max]),  # Explicit y-axis range
        )

        fig["layout"]["xaxis"].update(title_text="SGF Timestamp")
        fig["layout"]["yaxis"].update(title_text="Maximal Distances")

        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

        # Add the plots in html page
        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")


@verifies("1522157")
@testcase_definition(
    name="SWKPI_CNC_SGF_StaticObstacleInflationRate",
    description=f"This test case checks if SGF provides Static Objects, whose maximal distances "
    f"from their corresponding Static Obstacles are less than {cs.AP_E_STA_OBJ_INFLATION_M} "
    f"in at least {cs.AP_E_STA_OBJ_INFLATION_RATE_NU}% of the occurrences.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_8OKH5UxLEe6M5-WQsF_-tQ&oslc_config.context=https%3A%2F%2F"
    "jazz.conti.de%2Fgc%2Fconfiguration%2F17099&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2F"
    "rm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class StaticObstacleInflationRate(TestCase):
    """Static Obstacle Inflation Rate test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepStaticObstacleInflationRate,
        ]
