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

SIGNAL_DATA = "MF_SELECTED_TP"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Selected target pose",
    description="If a valid path is available, TRJPLA shall provide exclusively the Selected_Target_Pose",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TrjplaSelectedTargetPose(TestStep):
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
        chosen_target_pose = read_data["apChosenTargetPoseID_nu"].tolist()
        target_poseid = read_data["poseId0"].tolist()

        for idx, val in enumerate(traj_valid):
            if val == ConstantsTrajpla.TRAJ_VALID:
                t2 = idx
                break

        if t2 is not None:
            eval_cond = True
            for idx in range(t2, len(traj_valid)):
                if traj_valid[idx] == ConstantsTrajpla.TRAJ_VALID:
                    if target_poseid[idx] == chosen_target_pose[idx] and eval_cond:
                        evaluation = " ".join(
                            f"The evaluation of {signal_name['apChosenTargetPoseID_nu']} and "
                            f"{signal_name['poseId0']} is PASSED".split()
                        )
                        eval_cond = True
                    else:
                        evaluation = " ".join(
                            f"The evaluation of {signal_name['apChosenTargetPoseID_nu']} and "
                            f"{signal_name['poseId0']} is FAILED at frame {idx}".split()
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

        signal_summary[f"{signal_name['poseId0']} and {signal_name['apChosenTargetPoseID_nu']}"] = evaluation

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
        frame_list = list(range(0, len(target_poseid)))
        fig.add_trace(
            go.Scatter(
                x=frame_list,
                y=target_poseid,
                mode="lines",
            )
        )

        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"),
            xaxis=dict(tickformat="14"),
            xaxis_title="Frames",
            yaxis_title="Selected Target Pose Id",
        )
        fig.update_traces(showlegend=False, line=dict(width=1), selector=dict(type="scatter"))
        plot_titles.append("Graphical Overview of <TargetPosesPort.targetPoses[0].pose_ID>")
        plots.append(fig)
        remarks.append("TargetPoseId")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=frame_list,
                y=chosen_target_pose,
                mode="lines",
                line=dict(color="yellowgreen"),
            )
        )

        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"),
            xaxis=dict(tickformat="14"),
            xaxis_title="Frames",
            yaxis_title="Chosen Target Pose Id",
        )
        fig.update_traces(showlegend=False, line=dict(width=1), selector=dict(type="scatter"))
        plot_titles.append("Graphical Overview of <SlotCtrlPort.PlanningCtrlPort.apChosenTargetPoseId_nu>")
        plots.append(fig)
        remarks.append("ChosenTargetPoseId")

        # Create a table containing all signals and their status for each frame
        # for the purpose of analysis.
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=["Frames", "trajValid_nu", "SelectedTargetPoseId", "ChosenTargetPoseId"],
                        fill_color="paleturquoise",
                    ),
                    cells=dict(
                        values=[
                            frame_list,
                            traj_valid,
                            target_poseid,
                            chosen_target_pose,
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
            fc.REQ_ID: ["1670806"],
            fc.TESTCASE_ID: ["42018"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "If a valid path is available (<PlannedTrajPort.trajValid_nu>  == true) for the given"
                "environmental model provided by <ApParkingBoxPort> and <ApEnvModelPort>, "
                "TRJPLA shall provide exclusively the Selected_Target_Pose in "
                "<TargetPosesPort.targetPoses[0]>."
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


@verifies("1670806")
@testcase_definition(
    name="SWRT_CNC_PAR230_TRJPLA_SelectedTargetPose",
    description="Verify Selected_Target_Pose in <TargetPosesPort.targetPoses[0]>",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TrjplaTargetPoseTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TrjplaSelectedTargetPose,
        ]
