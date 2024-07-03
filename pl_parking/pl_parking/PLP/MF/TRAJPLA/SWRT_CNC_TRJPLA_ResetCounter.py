"""SWRT CNC TRAJPLA TestCases"""

import logging
import os
import sys

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

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)


SIGNAL_DATA = "MF_RESET_COUNTER"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Trjpla Reset Counter",
    description="Verify <TargetPosesPort.resetCounter> == <.resetOriginResult.resetCounter_nu>",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TrjplaResetCounter(TestStep):
    """Defining teststep"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
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

        reset_counter = read_data["resetCounter"].tolist()
        reset_counter_nu = read_data["resetCounter_nu"].tolist()

        eval_cond = True
        for idx in range(0, len(reset_counter)):
            if reset_counter[idx] == reset_counter_nu[idx] and eval_cond:
                evaluation = " ".join(
                    f"The evaluation of {signal_name['resetCounter']} is PASSED, with values ="
                    f" {signal_name['resetCounter_nu']}.".split()
                )
                eval_cond = True
            else:
                evaluation = " ".join(
                    f"The evaluation of {signal_name['resetCounter']} is FAILED, because"
                    f" the value is != {signal_name['resetCounter_nu']} at "
                    f"frame {idx} s.".split()
                )
                eval_cond = False

        if eval_cond:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        signal_summary[f"{signal_name['resetCounter']} and {signal_name['resetCounter_nu']}"] = evaluation

        # Create an overall summary table
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
                x=list(range(0, len(reset_counter))),
                y=reset_counter,
                mode="lines",
            )
        )

        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Frames", yaxis_title="Reset Counter"
        )
        fig.update_traces(showlegend=False, line=dict(width=1), selector=dict(type="scatter"))
        plot_titles.append("Graphical Overview of TargetPosesPort.resetCounter")
        plots.append(fig)
        remarks.append("resetCounter")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=list(range(0, len(reset_counter_nu))),
                y=reset_counter_nu,
                mode="lines",
                line=dict(color="tomato"),
            )
        )

        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"),
            xaxis=dict(tickformat="14"),
            xaxis_title="Frames",
            yaxis_title="Reset Counter nu",
        )
        fig.update_traces(showlegend=False, line=dict(width=1), selector=dict(type="scatter"))
        plot_titles.append("Graphical Overview of ApEnvModelPort.resetOriginResult.resetCounter_nu")
        plots.append(fig)
        remarks.append("Origin resetCounter_nu")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1520660"],
            fc.TESTCASE_ID: ["42097"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This tescase will verfiy that TRJPLA shall transform its data to the new"
                "origin by using <ApEnvModelPort.resetOriginResult.originTransformation>"
                "(indicated by <TargetPosesPort.resetCounter> == <ApEnvModelPort.resetOriginResult.resetCounter_nu>)."
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


@verifies("1520660")
@testcase_definition(
    name="SWRT_CNC_PAR230_TRJPLA_ResetCounter",
    description="TRJPLA shall transform its data to the new origin",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TrjplaResetCounterTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TrjplaResetCounter,
        ]
