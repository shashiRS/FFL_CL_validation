#!/usr/bin/env python3
"""Defining  pmsd TruePositive testcases"""
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
from pl_parking.PLP.CV.PMSD.association import Association, VehicleLine

# from pl_parking.PLP.CV.PMSD.ft_helper import *
from pl_parking.PLP.CV.PMSD.ft_helper import PMSD_Line_Detection, PMSDSignals
from pl_parking.PLP.CV.PMSD.gps_utils import GPS_utils
from pl_parking.PLP.CV.PMSD.pmsd_kpi_base import Pmsd_Kpi_Base

EXAMPLE = "PMSD_TRUE_POSITIVE"


def true_positive(trans_gt_lines: list[VehicleLine], trans_pred_lines: list[VehicleLine]) -> int:
    """Calculates the number of true positive associations between ground truth and predicted lines."""
    return sum([1 for a, b, c in Association.simple_match(trans_gt_lines, trans_pred_lines) if c])


@teststep_definition(
    step_number=1,
    name="PMSD TruePositive",
    description="Parking Lines and true positive KPI",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, PMSDSignals)
class PMSDTruePositiveTestStep(TestStep):
    """PMSD True Positive Test Step"""

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
        all_mean_true_ratios = []
        all_mean_true_ratios_per_camera: dict[str, list[float]] = dict()
        for numLines in sorted(numLinesList):
            figures = [go.Figure() for _ in range(3)]
            cam_str = f'{numLines.split("_")[0]}'
            num_true_lines = []
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
                        element for element in PMSDSignals.Columns.__dict__.values() if f"{cam_str}_line" in element
                    ]
                    line_data = {key.split("_")[-1]: reader[key, line_num].loc[index] for key in columns}

                    pmsd_lines.append(PMSD_Line_Detection(**line_data))

                trans_pred_lines = [line.to_Vehicle() for line in pmsd_lines]
                trans_gt_lines = [line.to_vehicle(gps, -yaw) for line in gt_lines]

                num_true_lines.append(true_positive(trans_gt_lines, trans_pred_lines))
                num_all_lines.append(len(trans_gt_lines))

            mean_true_ratios = [f / l if l > 0 else 0 for f, l in zip(num_true_lines, num_all_lines)]  # noqa: E741
            mean_true_ratios_pos = [f / l for f, l in zip(num_true_lines, num_all_lines) if l > 0]  # noqa: E741
            all_mean_true_ratios += mean_true_ratios_pos
            all_mean_true_ratios_per_camera[cam_str] = mean_true_ratios_pos

            max_mean = max(mean_true_ratios) if len(mean_true_ratios) > 0 else 0
            table_result[f"{cam_str}"] = fc.PASS if max_mean < 0.1 else fc.FAIL

            figures[0].add_trace(
                go.Scatter(
                    x=list(range(len(mean_true_ratios))),
                    y=list(mean_true_ratios),
                    mode="lines",
                    line=dict(color="red"),
                    name="True positive rate",
                ),
            )
            plot_titles.append(f"Graphical Overview Mean True Positive Error ({cam_str})")
            mean_avg = sum(mean_true_ratios) / len(num_all_lines) if len(num_all_lines) > 0 else 0
            remarks.append(f"{cam_str} mean: {mean_avg:.2f}")
            figures[0].layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Frames",
                title="Mean True Positive Error",
            )

            figures[1].add_trace(
                go.Scatter(
                    x=list(range(len(num_true_lines))),
                    y=list(num_true_lines),
                    mode="lines",
                    line=dict(color="darkblue"),
                    name="True positive count",
                ),
            )
            plot_titles.append(f"Graphical Overview True Positive Count Error ({cam_str})")
            remarks.append(f"{cam_str} count: {sum(num_true_lines)} frame count: {len(num_true_lines)}")
            figures[1].layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Frames",
                title="Count True Positive Error",
            )

            figures[2].add_trace(
                go.Pie(
                    labels=["True Positive", "Rest"],
                    values=[sum(num_true_lines), sum(num_all_lines) - sum(num_true_lines)],
                    marker=dict(
                        colors=["green", "red"],
                    ),
                )
            )
            plot_titles.append(f"Graphical Overview Pie Chart ({cam_str})")
            remarks.append(f"{cam_str}")

            for fig in figures[:2]:
                fig.update_traces(showlegend=True, line=dict(width=1), selector=dict(type="scatter"))

            plots.extend(figures)

        source_true_positive = ["PmdAll", *all_mean_true_ratios_per_camera.keys()]
        values_true_positive = [
            np.mean(all_mean_true_ratios),
            *[np.mean(i) for i in all_mean_true_ratios_per_camera.values()],
        ]
        count_true_positive = [len(all_mean_true_ratios), *[len(i) for i in all_mean_true_ratios_per_camera.values()]]
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Source", "Average True Positive", "Count"]),
                    cells=dict(values=[source_true_positive, values_true_positive, count_true_positive]),
                )
            ]
        )
        plot_titles.append("Average True Positive rate for parking markers")
        plots.append(fig)
        remarks.append("")

        colors = ["green" if r == fc.PASS else "red" for r in table_result.values()]
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["True Positive Error Evaluation", "Summary"]),
                    cells=dict(
                        values=[list(table_result.keys()), list(table_result.values())], fill_color=[colors, colors]
                    ),
                )
            ]
        )

        plot_titles.insert(0, "True Positive Evaluation")
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

        self.result.details["Additional_results"] = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["TODO"],
            fc.TESTCASE_ID: ["TODO"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: ["Parking Lines and true positive KPI"],
            fc.TEST_RESULT: [test_result],
        }


@verifies("TODO")
@testcase_definition(
    name="PMSD TruePositive",
    description="",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class PMSDTruePositive(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PMSDTruePositiveTestStep,
        ]
