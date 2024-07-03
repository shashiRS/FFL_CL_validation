#!/usr/bin/env python3
"""Defining  pmsd LineAngle testcases"""
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
from pl_parking.PLP.MF.constants import GroundTruthConstants

EXAMPLE = "PMSD_ANGLE"


@teststep_definition(
    step_number=1,
    name="PMSD LineAngle",
    description="Parking Lines and line angle KPI",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, PMSDSignals)
class PMSDLineAngleTestStep(TestStep):
    """PMSD Line Angle Test Step"""

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
        all_mean_angles = []
        all_mean_angles_per_camera: dict[str, list[float]] = dict()
        for numLines in sorted(numLinesList):
            cam_str = f'{numLines.split("_")[0]}'
            # convert ASL to ISO
            # note: WHEEL_BASE varies from cat to car
            cam_x = -(reader[f"{cam_str}_posx"] - GroundTruthConstants.WHEEL_BASE) / 1000
            cam_y = -reader[f"{cam_str}_posy"] / 1000
            cams = np.vstack((cam_x, cam_y)).T
            fig = go.Figure()
            for range_m, color, th in [(2, "darkblue", 15), (5, "red", 20), (8, "green", 30)]:
                mean_angles = []
                num_all_lines = []
                for index, step in zip(reader.index, range(len(reader))):
                    cam = np.array(cams[step])
                    has_input = True
                    gps.setENUorigin(
                        *list(
                            reader[
                                [
                                    PMSDSignals.Columns.LATITUDE,
                                    PMSDSignals.Columns.LONGITUDE,
                                    PMSDSignals.Columns.ALTITUDE,
                                ]
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

                    # if not visualized and len(trans_pred_lines) > 0:
                    #     self.plot_lines(trans_gt_lines, trans_pred_lines, frame_num, prefix.split('.')[-1])
                    #     visualized = True

                    matched_lines = Association.simple_match(trans_gt_lines, trans_pred_lines)
                    angles = [
                        pred.angle(gt)
                        for pred, gt, is_true_pos in matched_lines
                        if is_true_pos and (np.linalg.norm(pred.seg_intersect(gt) - cam) < range_m)
                    ]  # check seg_intersect

                    mean_angles.append(np.mean(angles) if len(angles) > 0 else 0)
                    num_all_lines.append(len(angles))

                if range_m == 8:
                    mean_angles_pos = [i for i, l in zip(mean_angles, num_all_lines) if l > 0]  # noqa: E741
                    all_mean_angles += mean_angles_pos
                    all_mean_angles_per_camera[cam_str] = mean_angles_pos

                max_mean = max(mean_angles) if len(mean_angles) > 0 else 0
                table_result[f"{numLines}_{range_m}m"] = (
                    fc.PASS if max_mean < th else table_result[f"{numLines}_{range_m}m"]
                )
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(mean_angles))),
                        y=list(mean_angles),
                        mode="lines",
                        line=dict(color=color),
                        name=f"<{range_m}m",
                    )
                )

            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Frames",
                yaxis_title="Mean Angle Error",
            )
            fig.update_traces(showlegend=True, line=dict(width=1), selector=dict(type="scatter"))

            plot_titles.append(f"Graphical Overview Mean Angle Error ({numLines})")
            plots.append(fig)
            mean_angles_avg = sum(mean_angles) / len(mean_angles) if len(mean_angles) > 0 else 0
            remarks.append(f"{numLines} mean: {mean_angles_avg:.2f} , count: {len(mean_angles)}")

        source_angle = ["PMD All", *all_mean_angles_per_camera.keys()]
        values_angle = [np.mean(all_mean_angles), *[np.mean(i) for i in all_mean_angles_per_camera.values()]]
        count_angle = [len(all_mean_angles), *[len(i) for i in all_mean_angles_per_camera.values()]]
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Source", "Average Angle", "Count"]),
                    cells=dict(values=[source_angle, values_angle, count_angle]),
                )
            ]
        )
        plot_titles.append("Average Angle for parking markers")
        plots.append(fig)
        remarks.append("")

        colors = ["green" if r == fc.PASS else "red" for r in table_result.values()]
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Angle Error Evaluation", "Summary"]),
                    cells=dict(
                        values=[list(table_result.keys()), list(table_result.values())], fill_color=[colors, colors]
                    ),
                )
            ]
        )

        plot_titles.insert(0, "Angle Error Evaluation")
        plots.insert(0, fig)
        remarks.insert(0, "PMSD Evaluation")

        test_result = fc.PASS if has_input and all(r == fc.PASS for r in table_result.values()) else fc.FAIL
        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            self.result.details["Plots"].append(
                f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
            )
        # for plot_title in plot_titles:
        #     self.result.details["Plot_titles"].append(plot_title)
        # for remark in remarks:
        #     self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["L3_PMSD_397"],
            fc.TESTCASE_ID: ["L3_SW_PMSD_142"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: ["Parking Lines and line angle KPI"],
            fc.TEST_RESULT: [test_result],
        }


@verifies("L3_PMSD_397")
@testcase_definition(
    name="PMSD LineAngle",
    description="",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class PMSDLineAngle(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PMSDLineAngleTestStep,
        ]
