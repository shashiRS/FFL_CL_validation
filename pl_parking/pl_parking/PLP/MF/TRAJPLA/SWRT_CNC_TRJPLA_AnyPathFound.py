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
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, MfSignals
from pl_parking.PLP.MF.constants import ConstantsTrajpla

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "MF_ANY_PATH_FOUND"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Target pose fully reachable status",
    description=(
        "If there is at least one reachable target pose, TRJPLA shall send <TargetPosesPort.anyPathFound> = true.,"
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TrjplaAnyPathFound(TestStep):
    """Defining teststep"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        t2 = None
        evaluation = ""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        read_data = self.readers[SIGNAL_DATA].signals
        test_result = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        signal_summary = {}
        signal_name = example_obj._properties

        reachable_status = read_data["targetPoseRechableStatus0"].tolist()
        anypath_found = read_data["anyPathFound"].tolist()

        for idx, val in enumerate(reachable_status):
            if val == ConstantsTrajpla.TP_FULLY_REACHABLE:
                t2 = idx
                break

        if t2 is not None:
            eval_cond = True
            for idx in range(t2, len(reachable_status)):
                if reachable_status[idx] == ConstantsTrajpla.TP_FULLY_REACHABLE and eval_cond:
                    if anypath_found[idx] == 1:
                        evaluation = " ".join(
                            f"The evaluation of {signal_name['anyPathFound']} and "
                            f"{signal_name['targetPoseRechableStatus0']} is PASSED".split()
                        )
                        eval_cond = True
                    else:
                        evaluation = " ".join(
                            f"The evaluation of {signal_name['anyPathFound']} and is FAILED, with values ="
                            f" when {signal_name['targetPoseRechableStatus0']} == {ConstantsTrajpla.TP_FULLY_REACHABLE} at frame "
                            f" {idx}.".split()
                        )
                        eval_cond = False
                        break
        else:
            eval_cond = False
            evaluation = " ".join("Evaluation not possible, fully reachable target pose was never found.".split())

        if eval_cond:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        signal_summary[f"{signal_name['anyPathFound']} and {signal_name['targetPoseRechableStatus0']}"] = evaluation

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

        # Create a table containing all signals and their status for each frame
        # for the purpose of analysis.
        frame_number_list = list(range(0, len(reachable_status)))
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=["Frames", "Reachable_Status", "AnyPathFound"],
                        fill_color="paleturquoise",
                    ),
                    cells=dict(
                        values=[
                            frame_number_list,
                            reachable_status,
                            anypath_found,
                        ],
                        align="left",
                    ),
                )
            ]
        )
        plot_titles.append("Signals Summary")
        plots.append(fig)
        remarks.append("TRJPLA Evaluation")

        fig = go.Figure()
        frame_list = list(range(0, len(anypath_found)))
        fig.add_trace(
            go.Scatter(
                x=frame_list,
                y=reachable_status,
                mode="lines",
            )
        )

        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"),
            xaxis=dict(tickformat="14"),
            xaxis_title="Frames",
            yaxis_title="TP Reachable Status",
        )
        fig.update_traces(showlegend=False, line=dict(width=1), selector=dict(type="scatter"))
        plot_titles.append("Graphical Overview of <TargetPosesPort.targetPoses.reachableStatus>")
        plots.append(fig)
        remarks.append("ReachableStatus")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=frame_list,
                y=anypath_found,
                mode="lines",
                line=dict(color="yellowgreen"),
            )
        )

        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Frames", yaxis_title="AnyPathFound"
        )
        fig.update_traces(showlegend=False, line=dict(width=1), selector=dict(type="scatter"))
        plot_titles.append("Graphical Overview of <TargetPosesPort.anyPathFound>")
        plots.append(fig)
        remarks.append("anyPathFound")

        # Create a table which contains all constants and their values.
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Constants", "Values"], fill_color="paleturquoise", align="left"),
                    cells=dict(
                        values=[
                            [
                                "TP_NOT_VALID",
                                "TP_NOT_REACHABLE",
                                "TP_FULLY_REACHABLE",
                                "TP_SAFE_ZONE_REACHABLE",
                                "TP_MANUAL_FWD_REACHABLE",
                                "TP_MANUAL_BWD_REACHABLE",
                                "MAX_NUM_POSE_REACHABLE_STATUS",
                            ],
                            [0, 1, 2, 3, 4, 5, 6],
                        ],
                        align="left",
                    ),
                )
            ]
        )

        plot_titles.append("Abbreviations")
        plots.append(fig)
        remarks.append("TRJPLA Evaluation")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1493111"],
            fc.TESTCASE_ID: ["41483"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This testcase will verify if there is at least one reachable target pose "
                "(<TargetPosesPort.targetPoses.reachableStatus == TP_FULLY_REACHABLE>) for the given"
                " environmental model provided by <ApParkingBoxPort> and <ApEnvModelPort>, TRJPLA shall "
                "send <TargetPosesPort.anyPathFound> = true."
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


@verifies("1493111")
@testcase_definition(
    name="SWRT_CNC_TRJPLA_AnyPathFound",
    description="Verify Target pose fully reachable status",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TrjplaAnyPathFoundTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TrjplaAnyPathFound,
        ]
