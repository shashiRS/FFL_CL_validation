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

SIGNAL_DATA = "MF_MAX_NUM_SEGMENTS"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Max num segments",
    description=(
        "TRJPLA shall send max num of segments and specify the actual number in TrajPlanVisuPort.numValidSegments"
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TrjplaMaxNumSegments(TestStep):
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

        traj_valid = read_data["trajValid_nu"].tolist()
        num_valid_segments = read_data["numValidSegments"].tolist()

        for idx, val in enumerate(traj_valid):
            if val == ConstantsTrajpla.TRAJ_VALID:
                t2 = idx
                break

        if t2 is not None:
            eval_cond = True
            for idx in range(t2, len(traj_valid)):
                if traj_valid[idx] == ConstantsTrajpla.TRAJ_VALID:
                    if num_valid_segments[idx] <= ConstantsTrajpla.AP_P_MAX_NUM_SEGMENTS_IN_PATH_NU and eval_cond:
                        evaluation = " ".join(
                            f"The evaluation of {signal_name['trajValid_nu']} and "
                            f"{signal_name['numValidSegments']} is PASSED".split()
                        )
                        eval_cond = True
                    else:
                        evaluation = " ".join(
                            f"The evaluation of {signal_name['trajValid_nu']} and "
                            f"{signal_name['numValidSegments']} is FAILED at frame {idx}".split()
                        )
                        eval_cond = False
                        break
        else:
            eval_cond = False
            evaluation = " ".join("Evaluation not possible, traj valid was never found.".split())

        if eval_cond:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        signal_summary[f"{signal_name['trajValid_nu']} and {signal_name['numValidSegments']}"] = evaluation

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

        frame_list = list(range(0, len(traj_valid)))
        # Create a table containing all signals and their status for each frame
        # for the purpose of analysis.
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=["Frames", "trajValid_nu", "numValidSegments"],
                        fill_color="paleturquoise",
                    ),
                    cells=dict(
                        values=[
                            frame_list,
                            traj_valid,
                            num_valid_segments,
                        ]
                    ),
                )
            ]
        )
        plot_titles.append("Signals Summary")
        plots.append(fig)
        remarks.append("TRJPLA Evaluation")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1517121"],
            fc.TESTCASE_ID: ["41543"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                " TRJPLA shall send up to AP_P_MAX_NUM_SEGMENTS_IN_PATH_NU consecutive segments of the planned path "
                "in <TrajPlanVisuPort.plannedGeometricPath> and specify the actual number by setting "
                "<TrajPlanVisuPort.numValidSegments> accordingly.  "
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


@verifies("1517101")
@testcase_definition(
    name="SWRT_CNC_TRJPLA_MaxNumSegments",
    description="Verify max num of segments",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TrjplaMaxNumSegmentsTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TrjplaMaxNumSegments,
        ]
