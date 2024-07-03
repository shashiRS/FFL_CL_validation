"""SWRT CNC TRAJPLA TestCases"""

import logging
import os

import plotly.graph_objects as go
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
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, MfSignals, rep
from pl_parking.PLP.MF.constants import ConstantsTrajpla

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


SIGNAL_DATA = "MF_NEW_SEGMENT_STARTED"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="New Segment Started",
    description="If a valid path is available, TRJPLA shall send <PlannedTrajPort.newSegmentStarted_nu> = true",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TrjplaNewStrokeStarted(TestStep):
    """Defining teststep"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        t2 = None
        evaluation = ""
        _log.debug("Starting processing...")

        read_data = self.readers[SIGNAL_DATA].signals

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)
        signal_summary = {}
        signal_name = example_obj._properties

        traj_valid = read_data["trajValid_nu"].tolist()
        new_segment = read_data["newSegmentStarted_nu"].tolist()

        for idx, val in enumerate(traj_valid):
            if val == ConstantsTrajpla.TRAJ_VALID:
                t2 = idx
                break

        if t2 is not None:
            for idx in range(t2, len(traj_valid)):
                if traj_valid[idx] == 1 and new_segment[idx] == 1:
                    evaluation = " ".join(
                        f"The evaluation of {signal_name['newSegmentStarted_nu']} and is PASSED, with values = True"
                        f" when {signal_name['trajValid_nu']} == "
                        f"{ConstantsTrajpla.TRAJ_VALID} at frame  {idx}".split()
                    )
                    eval_cond = True
                    break
                else:
                    evaluation = " ".join(
                        f"The evaluation of {signal_name['newSegmentStarted_nu']} and is FAILED, with values = False"
                        f" when {ConstantsTrajpla.TRAJ_VALID} == "
                        f"{ConstantsTrajpla.TRAJ_VALID} at frame  {idx} .".split()
                    )
                    eval_cond = False
                    break
        else:
            eval_cond = False
            evaluation = " ".join(
                "Evaluation not possible, the valid trajectory for                            "
                f" {signal_name['trajValid_nu']} was never found.".split()
            )

        if eval_cond:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        signal_summary[f"{signal_name['newSegmentStarted_nu']}"] = evaluation

        colors = "yellowgreen" if test_result != "failed" else "red"
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Signal Evaluation", "Summary"]),
                    cells=dict(
                        values=[list(signal_summary.keys()), list(signal_summary.values())], fill_color=[colors, colors]
                    ),
                )
            ]
        )

        plot_titles.append("Signal Evaluation")
        plots.append(fig)
        remarks.append("TRJPLA Evaluation")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=list(range(0, len(traj_valid))),
                y=traj_valid,
                mode="lines",
            )
        )

        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"),
            xaxis=dict(tickformat="14"),
            xaxis_title="Frames",
            yaxis_title="trajValid_nu",
        )
        fig.update_traces(showlegend=False, line=dict(width=1), selector=dict(type="scatter"))
        plot_titles.append("Graphical Overview of <PlannedTrajPort.trajValid_nu>")
        plots.append(fig)
        remarks.append("newSegmentStarted_nu")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=list(range(0, len(new_segment))),
                y=new_segment,
                mode="lines",
                line=dict(color="tomato"),
            )
        )

        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"),
            xaxis=dict(tickformat="14"),
            xaxis_title="Frames",
            yaxis_title="newSegmentStarted_nu",
        )
        fig.update_traces(showlegend=False, line=dict(width=1), selector=dict(type="scatter"))
        plot_titles.append("Graphical Overview of <PlannedTrajPort.newSegmentStarted_nu>")
        plots.append(fig)
        remarks.append("newSegmentStarted_nu")

        # Create a table containing all signals and their status for each frame
        # for the purpose of analysis.
        frame_number_list = list(range(0, len(traj_valid)))
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=["Frames", "trajValid_nu", "newSegmentStarted_nu"],
                        fill_color="paleturquoise",
                    ),
                    cells=dict(
                        values=[
                            frame_number_list,
                            traj_valid,
                            new_segment,
                        ],
                        fill=dict(
                            color=[
                                "rgb(245, 245, 245)",
                                "white",
                                "white",
                            ]
                        ),
                    ),
                )
            ]
        )
        plot_titles.append("Signals Summary")
        plots.append(fig)
        remarks.append("TRJPLA Evaluation")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1671345"],
            fc.TESTCASE_ID: ["42016"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This testcase will verify that If a valid path is output at the beginning of the "
                "parking maneuver TRJPLA shall send <PlannedTrajPort.newSegmentStarted_nu> = true."
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


@verifies("1671345")
@testcase_definition(
    name="SWRT_CNC_TRJPLA_NewSegmentStarted",
    description="Verify new segment started",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TrjplaNewStrokeStartedTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TrjplaNewStrokeStarted,
        ]
