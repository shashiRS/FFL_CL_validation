#!/usr/bin/env python3
"""SWRT_CNC_SGF_UniqueStaticObjectID test case"""

import logging
import os
import sys

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from shapely.geometry import Polygon
from tsf.core.common import PathSpecification
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
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
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    convert_dict_to_pandas,
    get_color,
    rep,
)
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

SIGNAL_DATA = "UniqueStaticObjectID"
ALIAS_JSON = "unique_static_object_id"
sgf_obj = SGFSignals()


@teststep_definition(
    step_number=1,
    name="Unique Static Object ID",
    description="This test case checks that if the Static Obstacles are well-separated, then all Static Objects that "
    "overlap with a given Static Obstacle have the same ID. Furthermore, if two Static Objects overlap "
    "with different Static Obstacles, then their IDs are different.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SGFSignals)
@register_side_load(
    alias=ALIAS_JSON,
    side_load=JsonSideLoad,
    path_spec=PathSpecification(
        folder=os.path.join(TSF_BASE, "data", "SGF_json_gt"),
        extension=".json",
    ),
)
@register_pre_processor(alias="load_gt_and_sim_data", pre_processor=SGFPreprocessorLoad)
class TestStepUniqueStaticObjectID(TestStep):
    """Test step definition."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step."""
        super().__init__()
        self.test_result = DATA_NOK
        self.sig_sum = None

    @staticmethod
    def plot_polygons(timestamp, gt_polygons, sim_polygons):
        """Plot of GT and SIM Polygons"""
        for gt_polygon in gt_polygons:
            # Extract x, y coordinates for plotting
            x_gt, y_gt = gt_polygon.exterior.xy

            plt.plot(x_gt, y_gt, label="GT", color="green")

        for polygon in sim_polygons:
            sim_polygon = polygon["Polygon vertices"]
            if sim_polygon.geom_type == "Polygon":
                x_sim, y_sim = sim_polygon.exterior.xy
                plt.plot(x_sim, y_sim, label="SIM Polygon", color="red")
            elif sim_polygon.geom_type == "MultiPolygon":
                for poly in sim_polygon.geoms:
                    x_poly, y_poly = poly.exterior.xy
                    plt.plot(x_poly, y_poly, label="SIM Polygon", color="red")

        plt.xlabel("X")
        plt.ylabel("Y")
        plt.title(f"Plot of GT and SIM Polygons at {timestamp}")
        plt.grid(True)

        # Place the legend outside the plot
        plt.legend(loc="upper left", bbox_to_anchor=(1, 1))

        # Show the plot and keep the window open
        plt.show(block=True)

    @staticmethod
    def validate_ids(list_of_object_ids):
        """Get a list of IDs list and check if IDs are unique for different Obstacles and equal for the same."""
        are_unique = True
        reason = "All checks passed. Values are unique."
        multi_object_values = set()
        single_object_values = set()

        for sublist in list_of_object_ids:
            if len(sublist) > 1:  # Multi-objects for the same obstacle
                unique_values = set(sublist)
                if len(unique_values) > 1:  # All elements must be the same
                    are_unique = False
                    reason = (2, f"Different object ID values for same Obstacle: {unique_values}.")
                    return are_unique, reason

                multi_object_values.add(sublist[0])  # Add the unique value

            elif len(sublist) == 1:  # Single-object for one obstacle
                single_object_values.add(sublist[0])

        # Check for duplicates
        duplicate_values = multi_object_values & single_object_values
        if duplicate_values:
            are_unique = False
            reason = (1, f"Duplicate object ID values in the same frame: {duplicate_values}.")

        return are_unique, reason

    @staticmethod
    def load_gt_vertices(frame_data, vertex_start_index, vertex_end_index):
        """Extract vertices of each polygon from a start_index to an end_index. Each vertex will be a tuple.
        Return a list of vertices.
        """
        points = []
        for coord_idx in range(vertex_start_index, vertex_end_index):
            x = frame_data.iat[0, frame_data.columns.get_loc("gt_vertex_x_" + str(coord_idx))]
            y = frame_data.iat[0, frame_data.columns.get_loc("gt_vertex_y_" + str(coord_idx))]

            points.append((x, y))

        return points

    @staticmethod
    def load_sim_vertices(frame_data, vertex_start_index, vertex_end_index):
        """Extract vertices of each polygon from a start_index to an end_index. Each vertex will be a tuple.
        Return a list of vertices.
        """
        points = []
        for coord_idx in range(vertex_start_index, vertex_end_index):
            x = frame_data[sgf_obj.Columns.SGF_VERTEX_X, coord_idx].iloc[0]
            y = frame_data[sgf_obj.Columns.SGF_VERTEX_Y, coord_idx].iloc[0]

            points.append((x, y))

        return points

    def eval_static_object_ids(self, gt_df, sim_df):
        """Evaluation of Static Object IDs"""
        list_of_errors = []  # A list to store information for failed cases
        eval_cond = False  # True when there is at least one intersection between a GT polygon and a SIM polygon

        if gt_df.empty:
            test_result = fc.INPUT_MISSING
            evaluation = " ".join("Ground truth data <b>not available</b>, evaluation can't be performed.".split())

            return (
                test_result,
                evaluation,
                list_of_errors,
            )

        if sim_df.empty:
            test_result = fc.INPUT_MISSING
            evaluation = " ".join("Simulation data <b>not available</b>, evaluation can't be performed.".split())

            return test_result, evaluation, list_of_errors

        # filter only valid outputs
        gt_df = gt_df[gt_df["gt_sig_status"] == "AL_SIG_STATE_OK"]
        # filter frames where at least two Static Obstacle are present.
        gt_df = gt_df[gt_df["gt_no_of_objects"] >= 2]

        # filter only valid outputs
        sim_df = sim_df[sim_df[sgf_obj.Columns.SGF_SIGSTATUS] == 1]
        # filter frames where at least two Static Obstacle are present.
        sim_df = sim_df[sim_df[sgf_obj.Columns.SGF_NUMBER_OF_POLYGONS] >= 2]

        if gt_df.empty:
            test_result = fc.NOT_ASSESSED
            evaluation = " ".join(
                "There is no valid ground truth data: gt_sigStatus != 1, or number of polygons is less then 1. "
                "Evaluation can't be performed.".split()
            )

            return test_result, evaluation, list_of_errors

        if sim_df.empty:
            test_result = fc.NOT_ASSESSED
            evaluation = " ".join(
                "There is no valid simulation data: sim_sigStatus != 1 or number of polygons is less then 1. "
                "Evaluation can't be performed.".split()
            )

            return test_result, evaluation, list_of_errors

        gt_sgf_timestamp = gt_df["gt_sgf_timestamp"].tolist()
        sim_sgf_timestamp = sim_df[sgf_obj.Columns.SGF_TIMESTAMP].tolist()

        common_timestamps = [x for x in gt_sgf_timestamp if x in sim_sgf_timestamp]
        if common_timestamps:
            for timestamp in common_timestamps:
                gt_polygons = []
                sim_polygons = []
                overlap_ids = []

                gt_frame_data = gt_df[gt_df["gt_sgf_timestamp"] == timestamp]
                sim_frame_data = sim_df[sim_df[sgf_obj.Columns.SGF_TIMESTAMP] == timestamp]

                # num of objects per frame
                gt_num_objects = gt_frame_data["gt_no_of_objects"].values
                sim_num_objects = sim_frame_data[sgf_obj.Columns.SGF_NUMBER_OF_POLYGONS].values

                # Get GT polygons
                for i in range(0, gt_num_objects[0]):
                    gt_polygon_vertex_start_index = int(
                        gt_frame_data.iat[0, gt_frame_data.columns.get_loc("gt_vertex_start_index_" + str(i))]
                    )
                    gt_polygon_used_vertices = int(
                        gt_frame_data.iat[0, gt_frame_data.columns.get_loc("gt_used_vertices_" + str(i))]
                    )
                    gt_polygon_vertex_end_index = gt_polygon_vertex_start_index + gt_polygon_used_vertices

                    gt_polygons.append(
                        Polygon(
                            self.load_gt_vertices(
                                gt_frame_data, gt_polygon_vertex_start_index, gt_polygon_vertex_end_index
                            )
                        )
                    )

                # Get SIM polygons
                for i in range(0, sim_num_objects[0]):
                    sim_polygon_vertex_start_index = int(
                        sim_frame_data[sgf_obj.Columns.SGF_OBJECT_VERTEX_START_INDEX, i].iloc[0]
                    )
                    sim_polygon_used_vertices = int(sim_frame_data[sgf_obj.Columns.SGF_OBJECT_USED_VERTICES, i].iloc[0])
                    sim_polygon_vertex_end_index = sim_polygon_vertex_start_index + sim_polygon_used_vertices
                    sim_polygon_id = sim_frame_data[sgf_obj.Columns.SGF_OBJECT_ID, i].iloc[0]
                    sim_polygons.append(
                        {
                            "Polygon ID": sim_polygon_id,
                            "Polygon vertices": Polygon(
                                self.load_sim_vertices(
                                    sim_frame_data, sim_polygon_vertex_start_index, sim_polygon_vertex_end_index
                                )
                            ),
                        }
                    )

                # self.plot_polygons(timestamp, gt_polygons, sim_polygons)

                for gt_polygon in gt_polygons:
                    sim_ids = []
                    for sim_polygon in sim_polygons:
                        intersection = gt_polygon.intersection(sim_polygon["Polygon vertices"])
                        if intersection.area > 0.0:
                            eval_cond = True
                            sim_ids.append(sim_polygon["Polygon ID"])
                    if sim_ids:
                        overlap_ids.append(sim_ids)

                if overlap_ids:
                    unique, reason = self.validate_ids(overlap_ids)
                    if not unique:
                        err = {
                            "sgf_timestamp": timestamp,
                            "failed_reason": reason,
                        }
                        list_of_errors.append(err)

            if eval_cond:
                if len(list_of_errors) > 0:
                    test_result = fc.FAIL
                    evaluation = " ".join(
                        f"The evaluation is <b>FAILED</b> in {len(list_of_errors)} cases because not all Static object "
                        f"IDs are unique.".split()
                    )
                else:
                    test_result = fc.PASS
                    evaluation = " ".join(
                        "The evaluation is <b>PASSED</b> because all Static objects IDs are unique.".split()
                    )
            else:
                test_result = fc.NOT_ASSESSED
                evaluation = " ".join(
                    "There is no intersection between a GT polygon and any SIM polygon. "
                    "Evaluation can't be performed.".split()
                )
        else:
            test_result = fc.NOT_ASSESSED
            evaluation = " ".join("No simulation data matches any GT data. Evaluation can't be performed.".split())

        return test_result, evaluation, list_of_errors

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

        summary_key = "Unique Static Object ID"

        gt_df, sim_df = self.pre_processors["load_gt_and_sim_data"]

        self.test_result, evaluation, list_of_errors = self.eval_static_object_ids(gt_df, sim_df)

        # Report result status
        if self.test_result == fc.INPUT_MISSING or self.test_result == fc.NOT_ASSESSED:
            self.result.measured_result = DATA_NOK
        elif self.test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif self.test_result == fc.FAIL:
            self.result.measured_result = FALSE

        signal_summary[summary_key] = evaluation
        remark = " ".join(
            "Check that if the Static Obstacles are well-separated then all Static Objects that overlap "
            "with a given Static Obstacle have the same ID.<br/>"
            "Furthermore, if two Static Objects overlap with different Static Obstacles, "
            "then their IDs are different.".split()
        )
        self.sig_sum = convert_dict_to_pandas(
            signal_summary=signal_summary, table_header_left="Evaluation", table_remark=remark
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        result_df = {
            "Verdict": {"value": self.test_result.title(), "color": get_color(self.test_result)},
            fc.REQ_ID: ["1522115"],
            fc.TESTCASE_ID: ["39102"],
            fc.TEST_DESCRIPTION: ["Check if SGF provides an obstacle ID for each Static Object."],
        }

        self.result.details["Additional_results"] = result_df

        if list_of_errors:
            # Plot frame where Static Object IDs are not unique.
            fig = go.Figure()
            list_of_errors_df = pd.DataFrame(list_of_errors)

            failed_timestamps = list_of_errors_df["sgf_timestamp"]
            reason = list_of_errors_df["failed_reason"].str[0]
            additional_info = list_of_errors_df["failed_reason"].str[1]

            fig.add_trace(
                go.Scatter(
                    x=failed_timestamps,
                    y=reason,
                    name="Incorrect IDs of polygons",
                    mode="markers",
                    marker={"color": "red"},
                    customdata=additional_info,
                    hoverinfo="skip",
                    hovertemplate=("Timestamp: %{x}<br>" + "Reason: %{customdata}" + "<extra></extra>"),
                )
            )

            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            fig.update_yaxes(range=[0.0, max(reason) * 1.1], dtick=0.5)

            fig["layout"]["xaxis"].update(title_text="SGF Timestamp")
            fig["layout"]["yaxis"].update(title_text="Object ID")

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


@verifies("1522115")
@testcase_definition(
    name="Unique Static Object ID",
    description="This test case checks that if the Static Obstacles are well-separated, then all Static Objects that "
    "overlap with a given Static Obstacle have the same ID. Furthermore, if two Static Objects overlap "
    "with different Static Obstacles, then their IDs are different.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_8OI540xLEe6M5-WQsF_-tQ&oslc_config.context=https%3A%2F%2F"
    "jazz.conti.de%2Fgc%2Fconfiguration%2F36325&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2F"
    "rm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class UniqueStaticObjectID(TestCase):
    """Static Obstacle Inflation Rate test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepUniqueStaticObjectID,
        ]
