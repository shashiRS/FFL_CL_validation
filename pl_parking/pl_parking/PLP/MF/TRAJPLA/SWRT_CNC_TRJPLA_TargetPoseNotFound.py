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

SIGNAL_DATA = "MF_TP_NOT_FOUND"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Target pose not found",
    description="TRJPLA shall not provide any target pose or parking path based on input conditions,",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TrjplaTargetPoseNotFound(TestStep):
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

        ap_state = read_data["ApState"].tolist()
        mp_state = read_data["MpState"].tolist()
        ra_state = read_data["RaState"].tolist()
        gp_state = read_data["GpState"].tolist()
        rm_state = read_data["RmState"].tolist()
        num_valid_poses = read_data["numValidPoses"].tolist()
        traj_valid_nu = read_data["trajValid_nu"].tolist()
        num_valid_ctrlpoints_nu = read_data["numValidCtrlPoints_nu"].tolist()

        num_valid_poses_nu = read_data["numValidPoses_nu"].tolist()
        num_valid_segments = read_data["numValidSegments"].tolist()
        anypath_found = read_data["anyPathFound"].tolist()

        for idx in range(0, len(ap_state)):
            if (
                ap_state[idx] == ConstantsTrajpla.AP_INACTIVE
                and mp_state[idx] == ConstantsTrajpla.MP_INACTIVE
                and ra_state[idx] == ConstantsTrajpla.RA_INACTIVE
                and gp_state[idx] == ConstantsTrajpla.GP_INACTIVE
                and rm_state[idx] == ConstantsTrajpla.RM_INACTIVE
            ) or (
                ap_state[idx] == ConstantsTrajpla.AP_AVG_FINISHED
                or mp_state[idx] == ConstantsTrajpla.MP_TRAIN_FINISHED
                or mp_state[idx] == ConstantsTrajpla.MP_RECALL_FINISHED
                or ra_state[idx] == ConstantsTrajpla.RA_AVG_FINISHED
                or gp_state[idx] == ConstantsTrajpla.GP_AVG_FINISHED
                or rm_state[idx] == ConstantsTrajpla.RM_AVG_FINISHED
            ):

                if (
                    num_valid_poses[idx] == 0
                    and traj_valid_nu[idx] == 0
                    and num_valid_ctrlpoints_nu[idx] == 0
                    and num_valid_poses_nu[idx] == 0
                    and num_valid_segments[idx] == 0
                    and anypath_found[idx] == 0
                ):
                    evaluation = " ".join(
                        f"The evaluation of signals {signal_name['numValidPoses']} and "
                        f"{signal_name['trajValid_nu']} and {signal_name['numValidCtrlPoints_nu']} and "
                        f"{signal_name['numValidPoses_nu']} and {signal_name['numValidSegments']} and "
                        f"{signal_name['anyPathFound']} is "
                        "PASSED".split()
                    )
                    eval_cond = True
                else:
                    evaluation = " ".join(
                        f"The evaluation of {signal_name['numValidPoses']} and "
                        f"{signal_name['trajValid_nu']} and {signal_name['numValidCtrlPoints_nu']} and "
                        f"{signal_name['numValidPoses_nu']} and {signal_name['numValidSegments']} and "
                        f"{signal_name['anyPathFound']} is "
                        f"FAILED at frame {idx}".split()
                    )
                    eval_cond = False
                    break

        if evaluation == "":
            evaluation = " ".join("Input conditions was never met").split()
            eval_cond = False

        if eval_cond:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        signal_summary[
            f"{signal_name['numValidPoses']} and {signal_name['trajValid_nu']} and "
            f"{signal_name['numValidCtrlPoints_nu']} and {signal_name['numValidPoses_nu']} and "
            f"{signal_name['numValidSegments']} and {signal_name['anyPathFound']}"
        ] = evaluation

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
        frame_number_list = list(range(0, len(ap_state)))
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=[
                            "Frames",
                            "apState",
                            "mpState",
                            "raState",
                            "trajValid_nu",
                            "numValidPoses",
                            "numValidCtrlPoints_nu",
                            "numValidPoses_nu",
                            "numValidSegments",
                            "anyPathFound",
                        ],
                        fill_color="paleturquoise",
                    ),
                    cells=dict(
                        values=[
                            frame_number_list,
                            ap_state,
                            mp_state,
                            ra_state,
                            traj_valid_nu,
                            num_valid_poses,
                            num_valid_ctrlpoints_nu,
                            num_valid_poses_nu,
                            num_valid_segments,
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

        # Create a table which contains all constants and their values.
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Constants", "Values"], fill_color="paleturquoise", align="left"),
                    cells=dict(
                        values=[
                            [
                                "AP_INACTIVE",
                                "GP_INACTIVE",
                                "RM_INACTIVE",
                                "RA_INACTIVE",
                                "MP_INACTIVE",
                                "AP_AVG_FINISHED",
                                "GP_AVG_FINISHED",
                                "RM_AVG_FINISHED",
                                "RA_AVG_FINISHED",
                                "MP_TRAIN_FINISHED",
                                "MP_RECALL_FINISHED",
                            ],
                            [0, 0, 0, 0, 0, 8, 6, 7, 4, 4, 5, 9],
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
            fc.REQ_ID: ["1492142"],
            fc.TESTCASE_ID: ["41474"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This testcase will verify that TRJPLA shall not provide any target pose or parking path based on "
                "input conditions of apState, gpState, rmState, raState and mpState."
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


@verifies("1492142")
@testcase_definition(
    name="SWRT_CNC_PAR230_TRJPLA_TargetPoseNotFound",
    description="Verify TRJPLA shall not provide any target pose or parking path.",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TrjplaTargetPoseNotFoundTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TrjplaTargetPoseNotFound,
        ]
