#!/usr/bin/env python3
"""SWRT_CNC_SGF_StaticObjsSorted testcase"""

import logging
import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
"""imports from tsf core"""
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

"""imports from current repo"""
import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.CEM.polygon_helper as polygon_helper
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    convert_dict_to_pandas,
    get_color,
)
from pl_parking.PLP.CEM.SGF.ft_helper import SGFSignals

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


SIGNAL_DATA = "StaticObjsSorted"
sgf_obj = SGFSignals()


@teststep_definition(
    step_number=1,
    name="SWRT_CNC_SGF_StaticObjsSorted",
    description="Checks that SGF provides the list of Static Objects sorted by the distance from the "
    "origin of the vehicle coordinate system, where first element is the closest one.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SGFSignals)
class TestStepStaticObjsSorted(TestStep):
    """TestStep for evaluating if Static Objects are sorted by distance"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.test_result = fc.INPUT_MISSING
        self.sig_sum = None

    @staticmethod
    def distance_from_origin(row, polygon_idx):
        """Distance of a polygon from the origin"""
        vertex_start_idx = int(row["vertexStartIndex_polygon", polygon_idx])
        num_vertices = int(row["numVertices_polygon", polygon_idx])
        vertex_list = [
            np.array([row["vertex_x", vertex_idx], row["vertex_y", vertex_idx]])
            for vertex_idx in range(vertex_start_idx, vertex_start_idx + num_vertices)
        ]
        return polygon_helper.dist_of_point_from_polygon(np.array([0, 0]), vertex_list)

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        # Update the details from the results page with the needed information. All the information from
        # self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        # Create empty lists for titles, plots and remarks,if they are needed, plots
        # and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_summary = {}  # Initializing the dictionary with data for final evaluation table
        list_of_errors = []  # A list to store information for failed cases
        test_results = []  # A list to store result of each frame (True or False)

        signals_df = self.readers[SIGNAL_DATA]
        # filter only valid outputs when sigStatus is 1
        signals_df = signals_df[signals_df["SGF_sig_status"] == 1]
        # filter only where at least two objects exists, otherwise test is not relevant
        signals_df = signals_df[signals_df["numPolygons"] > 1]

        signal_evaluated = sgf_obj.get_properties()[sgf_obj.Columns.SGF_NUMBER_OF_POLYGONS][0]

        if not signals_df.empty:
            for _, row in signals_df.iterrows():
                unsorted_positions = []
                frame_result = True
                sgf_timestamp = int(row[sgf_obj.Columns.SGF_TIMESTAMP])
                polygon_distances = [
                    self.distance_from_origin(row, polygon_idx)
                    for polygon_idx in range(int(row[sgf_obj.Columns.SGF_NUMBER_OF_POLYGONS]))
                ]

                for i in range(1, len(polygon_distances)):
                    if polygon_distances[i - 1] > (polygon_distances[i] + 0.000001):   # tolerance added for avoiding false positives caused of floating point operations
                        unsorted_positions.append(i)
                #for i in range(1, len(polygon_distances)):
                #    if polygon_distances[i - 1] > polygon_distances[i]:   # tolerance could be added, ~5.-7. digit
                #        unsorted_positions.append(i)


                if len(unsorted_positions) > 0:
                    frame_result = False
                    err = {
                        "sgf_timestamp": sgf_timestamp,
                        "no_of_unsorted_objects": len(unsorted_positions),
                        "polygon_distances": polygon_distances,
                    }
                    list_of_errors.append(err)

                test_results.append(frame_result)

            if all(test_results):
                self.test_result = fc.PASS
                description = " ".join(
                    "The evaluation is <b>PASSED</b> because all Static objects provided by SGF "
                    "are sorted by the distance.".split()
                )
            else:
                description = " ".join(
                    f"The evaluation is <b>FAILED</b> at timestamp {list_of_errors[0]['sgf_timestamp']} "
                    f"because not all Static Objects are sorted by distance.".split()
                )
                self.test_result = fc.FAIL

        else:
            description = " ".join(
                "Test is <b>not evaluated</b> because number of Static Objects is less than two.".split()
            )

        # Report result status
        if self.test_result == fc.INPUT_MISSING:
            self.result.measured_result = DATA_NOK
        elif self.test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif self.test_result == fc.FAIL:
            self.result.measured_result = FALSE

        signal_summary[signal_evaluated] = description
        remark = " ".join(
            "SGF shall provide the list of Static Objects sorted by the distance from the origin of the vehicle "
            "coordinate system, where first element is the closest one.".split()
        )

        self.sig_sum = convert_dict_to_pandas(signal_summary=signal_summary, table_remark=remark)

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.result.measured_result in [FALSE, DATA_NOK]:
            list_of_errors_df = pd.DataFrame(list_of_errors)
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=list_of_errors_df["sgf_timestamp"],
                    y=list_of_errors_df["no_of_unsorted_objects"],
                    name="",
                    mode="markers",
                    marker={"color": "red"},
                    hovertemplate="Unsorted Objects: %{y}" + "<br>Time: %{x} [s]",
                )
            )
            fig["layout"]["xaxis"].update(title_text="SGF Timestamp")
            fig["layout"]["yaxis"].update(title_text="Number of unsorted Static Objects")

            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        result_df = {
            "Verdict": {"value": self.test_result.title(), "color": get_color(self.test_result)},
            fc.REQ_ID: ["1522109"],
            fc.TESTCASE_ID: ["38886"],
            fc.TEST_DESCRIPTION: [
                "Checks that SGF provides the list of Static Objects sorted by the distance from the "
                "origin of the vehicle coordinate system, where first element is the closest one."
            ],
        }

        self.result.details["Additional_results"] = result_df

        # Add the plots in html page
        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")


@verifies("1522109", "1522003")
@testcase_definition(
    name="SWRT_CNC_SGF_StaticObjsSorted",
    # TODO: add description and req link from DOORS NEXT
    description="This test case checks that SGF provides the list of Static Objects sorted by the distance "
    "from the origin of the vehicle coordinate system, where first element is the closest one.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_8OI54UxLEe6M5-WQsF_-tQ&oslc_config.context=https%3A%2F%2F"
    "jazz.conti.de%2Fgc%2Fconfiguration%2F17100&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2F"
    "rm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg",
)
class StaticObjsSorted(TestCase):
    """Static Objects Sorted test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [TestStepStaticObjsSorted]
