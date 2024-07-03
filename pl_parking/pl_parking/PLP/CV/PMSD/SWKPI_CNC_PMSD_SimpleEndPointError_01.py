"""Parking Lines and simple end point error KPI"""

import logging
import os
from collections import defaultdict

import numpy as np
import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CV.PMSD.association import Association

# from pl_parking.PLP.CV.PMSD.ft_helper import *
from pl_parking.PLP.CV.PMSD.ft_helper import PMSD_Line_Detection, PMSDSignals
from pl_parking.PLP.CV.PMSD.gps_utils import GPS_utils
from pl_parking.PLP.CV.PMSD.pmsd_kpi_base import Pmsd_Kpi_Base

EXAMPLE = "PMSD_SIMPLE_ENDPOINT"


@teststep_definition(
    step_number=1,
    name="Simple end point mean distance error",
    description="Parking Lines and simple end point error KPI",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, PMSDSignals)
class PMSDSimpleEndPointDistance(TestStep):
    """TestStep for evaluating PMSD Simple End Point Distance, utilizing a mf custom report."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """Process data and update result details with plot-related information and the file name of the first artifact."""
        _log.debug("Starting processing...")

        reader = self.readers[EXAMPLE].signals.as_plain_df

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)
        table_result = defaultdict(lambda: fc.FAIL)

        gps = GPS_utils()
        gps.setENUorigin(
            *list(
                reader[
                    [PMSDSignals.Columns.LATITUDE, PMSDSignals.Columns.LONGITUDE, PMSDSignals.Columns.ALTITUDE]
                ].iloc[0]
            )
        )
        gt_lines = Pmsd_Kpi_Base.get_gt_lines(gps)

        numLinesList = [element for element in reader.columns if "numberOfLines" in element]
        all_mean_endpoints = []
        all_mean_endpoints_per_camera: dict[str, list[float]] = dict()
        for numLines in sorted(numLinesList):
            fig = go.Figure()
            cam_str = f'{numLines.split("_")[0]}'
            mean_endpoints = []
            simple_endpoint_distances_list = []
            num_all_lines = []
            for index in reader.index:
                has_input = True
                gps.setENUorigin(
                    *list(
                        reader[
                            [PMSDSignals.Columns.LATITUDE, PMSDSignals.Columns.LONGITUDE, PMSDSignals.Columns.ALTITUDE]
                        ].loc[index]
                    )
                )

                yaw = reader[PMSDSignals.Columns.HEADING].loc[index]
                pmsd_lines: list[PMSD_Line_Detection] = []

                for line_num in range(reader[numLines].loc[index]):
                    columns = [
                        element
                        for element in PMSDSignals.Columns.__dict__.values()
                        if f"{numLines.split('_')[0]}_line" in element
                    ]
                    line_data = {key.split("_")[-1]: reader[key, line_num].loc[index] for key in columns}

                    pmsd_lines.append(PMSD_Line_Detection(**line_data))

                trans_pred_lines = [line.to_Vehicle() for line in pmsd_lines]
                trans_gt_lines = [line.to_vehicle(gps, -yaw) for line in gt_lines]

                matched_lines = Association.simple_match(trans_gt_lines, trans_pred_lines)
                simple_endpoint_distances = [
                    pred.simple_endpoint_distance_line(gt) for pred, gt, is_true_pos in matched_lines if is_true_pos
                ]
                simple_endpoint_distances_list.append(sum(simple_endpoint_distances))
                mean_endpoints.append(np.mean(simple_endpoint_distances) if len(simple_endpoint_distances) > 0 else 0)
                num_all_lines.append(len(simple_endpoint_distances))

            expected_threshold = 1
            max_mean = max(mean_endpoints) if len(mean_endpoints) > 0 else 0
            table_result[f"{numLines}"] = fc.PASS if max_mean < 1 else fc.FAIL

            # Graphical overview of mean simple end point distance error for each camera
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(mean_endpoints))),
                    y=list(mean_endpoints),
                    mode="lines",
                    line=dict(color="tomato"),
                    name="mean endpoint error",
                )
            )
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Frames",
                yaxis_title="Simple EndPoint Distance Error",
            )
            fig.update_traces(showlegend=True, line=dict(width=1), selector=dict(type="scatter"))

            plot_titles.append(f"Graphical Overview Mean Simple EndPoint DistanceError ({numLines.split('.')[-1]})")
            plots.append(fig)
            mean_endpoints_pos = [i for i, l in zip(mean_endpoints, num_all_lines) if l > 0]  # noqa: E741
            all_mean_endpoints += mean_endpoints_pos
            all_mean_endpoints_per_camera[cam_str] = mean_endpoints_pos
            mean_endpoints_avg = sum(mean_endpoints) / len(mean_endpoints) if len(mean_endpoints) > 0 else 0
            remarks.append(
                f"{numLines} total mean error: {mean_endpoints_avg:.2f}, "
                f"Expected mean threshold: "
                f"{expected_threshold} , Frame count:"
                f" {len(mean_endpoints)}"
            )

        #  Summary report of all the four cameras with pass fail result
        source_angle = ["PMD All", *all_mean_endpoints_per_camera.keys()]
        values_angle = [np.mean(all_mean_endpoints), *[np.mean(i) for i in all_mean_endpoints_per_camera.values()]]
        count_angle = [len(all_mean_endpoints), *[len(i) for i in all_mean_endpoints_per_camera.values()]]
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Source", "Average Simple Endpoint", "Count"]),
                    cells=dict(values=[source_angle, values_angle, count_angle]),
                )
            ]
        )
        plot_titles.append("Average Simple Endpoint for parking markers")
        plots.append(fig)
        remarks.append("")

        colors = ["green" if r == fc.PASS else "red" for r in table_result.values()]
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Simple EndPoint Distance Error Evaluation", "Summary"]),
                    cells=dict(
                        values=[list(table_result.keys()), list(table_result.values())], fill_color=[colors, colors]
                    ),
                )
            ]
        )

        plot_titles.insert(0, "Simple EndPoint Distance Error Evaluation")
        plots.insert(0, fig)
        remarks.insert(0, "PMSD Evaluation")

        # Test Report Creation
        test_result = fc.PASS if has_input and all(r == fc.PASS for r in table_result.values()) else fc.FAIL
        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            self.result.details["Plots"].append(
                f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
            )

        self.result.details["Additional_results"] = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1517130"],
            fc.TESTCASE_ID: ["39435"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: ["Parking Lines and simple endpoint error distance KPI"],
            fc.TEST_RESULT: [test_result],
        }


@verifies("1517130")
@testcase_definition(
    name="SWKPI_CNC_PMSD_SimpleEndPointError_01",
    description="Parking Lines and simple endpoint error distance KPI",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class PMSDSimpleEndPointDistanceTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PMSDSimpleEndPointDistance,
        ]
