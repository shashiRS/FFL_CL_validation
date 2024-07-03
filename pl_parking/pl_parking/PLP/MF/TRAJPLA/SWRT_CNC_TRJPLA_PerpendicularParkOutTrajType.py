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
SIGNAL_DATA = "MF_PERPENDICULAR_PARKOUT_TRAJ"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Verify planned traj type.",
    description=" TRJPLA shall send planned traj type based on selected target pose type.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TrjplaPerpParkOutTrajType(TestStep):
    """Defining teststep"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        t2 = None
        par_pose = None
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
        traj_type = read_data["trajType_nu"].tolist()
        pose_type = read_data["poseType0"].tolist()

        for idx, val in enumerate(traj_valid):
            if val == ConstantsTrajpla.TRAJ_VALID:
                t2 = idx
                break

        for idx, val in enumerate(pose_type):
            if val == ConstantsTrajpla.T_PERP_PARKING_OUT_FWD or val == ConstantsTrajpla.T_PERP_PARKING_OUT_BWD:
                par_pose = idx
                break

        eval_cond = True
        if t2 is not None:
            if par_pose is not None:
                for idx in range(t2, len(traj_valid)):
                    if traj_valid[idx] == ConstantsTrajpla.TRAJ_VALID and (
                        pose_type[idx] == ConstantsTrajpla.T_PERP_PARKING_OUT_FWD
                        or pose_type[idx] == ConstantsTrajpla.T_PERP_PARKING_OUT_BWD
                    ):
                        if traj_type[idx] == ConstantsTrajpla.PERP_PARK_OUT_TRAJ and eval_cond:
                            evaluation = " ".join(
                                f"The evaluation of {signal_name['trajType_nu']} and is PASSED, with values ="
                                f" {ConstantsTrajpla.PERP_PARK_OUT_TRAJ} when {signal_name['poseType0']} == "
                                f"{ConstantsTrajpla.T_PERP_PARKING_OUT_FWD} or "
                                f"{ConstantsTrajpla.T_PERP_PARKING_OUT_BWD}.".split()
                            )
                            eval_cond = True
                        else:
                            evaluation = " ".join(
                                f"The evaluation of {signal_name['trajType_nu']} is FAILED, with values ="
                                f" {ConstantsTrajpla.PERP_PARK_OUT_TRAJ} when {signal_name['poseType0']} == "
                                f"{ConstantsTrajpla.T_PERP_PARKING_OUT_FWD} or "
                                f"{ConstantsTrajpla.T_PERP_PARKING_OUT_BWD} at frame "
                                f" {idx} s.".split()
                            )
                            eval_cond = False
                            break
            else:
                eval_cond = False
                evaluation = " ".join(
                    "Evaluation not possible, the value of signal {signal_name['poseType0']} was "
                    "never equal to "
                    f"{ConstantsTrajpla.T_PERP_PARKING_OUT_FWD} or"
                    f"{ConstantsTrajpla.T_PERP_PARKING_OUT_BWD}".split()
                )
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

        signal_summary[f"{signal_name['poseType0']} and {signal_name['trajType_nu']}"] = evaluation

        # Create an overall summary table
        colors = "yellowgreen" if test_result != "failed" else "red"
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=["Signal Evaluation", "Summary"],
                        fill_color="paleturquoise",
                        align=["left", "center"],
                        height=40,
                    ),
                    cells=dict(
                        values=[list(signal_summary.keys()), list(signal_summary.values())],
                        fill_color=[colors, colors],
                        align=["left", "center"],
                        font_size=12,
                        height=30,
                    ),
                )
            ]
        )
        plot_titles.append("Signal Evaluation")
        plots.append(fig)
        remarks.append("TRJPLA Evaluation")

        # Create a table containing all signals and their status for each frame
        # for the purpose of analysis.
        frame_number_list = list(range(0, len(traj_valid)))
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=["Frames", "trajValid_nu", "Target Pose Type", "TrajType"],
                        fill_color="paleturquoise",
                    ),
                    cells=dict(
                        values=[
                            frame_number_list,
                            traj_valid,
                            pose_type,
                            traj_type,
                        ],
                        fill=dict(
                            color=[
                                "rgb(245, 245, 245)",
                                "white",
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

        # Create a table which contains all constants and their values.
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Constants", "Values"], fill_color="paleturquoise", align="left"),
                    cells=dict(
                        values=[
                            [
                                "TRAJ_VALID",
                                "T_PARALLEL_PARKING",
                                "T_PERP_PARKING_FWD",
                                "T_PERP_PARKING_BWD",
                                "T_ANGLED_PARKING_STANDARD",
                                "T_ANGLED_PARKING_REVERSE",
                                "T_REM_MAN_FWD",
                                "T_REM_MAN_BWD",
                                "T_PERP_PARKING_OUT_FWD",
                                "T_PERP_PARKING_OUT_BWD",
                                "T_PAR_PARKING_OUT",
                                "T_ANGLED_PARKING_STANDARD_OUT",
                                "T_ANGLED_PARKING_REVERSE_OUT",
                                "T_UNDEFINED",
                                "PAR_PARK_IN_TRAJ",
                                "PERP_PARK_IN_TRAJ",
                                "PERP_PARK_OUT_TRAJ",
                                "PAR_PARK_OUT_TRAJ",
                                "REMOTE_MAN_TRAJ",
                                "UNDO_TRAJ",
                                "MAX_NUM_PLANNED_TRAJ_TYPES",
                            ],
                            [1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 21, 1, 0, 2, 3, 4, 5, 6],
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
            fc.REQ_ID: ["1500183"],
            fc.TESTCASE_ID: ["41524"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "If a valid path is available and the Selected_Target_Pose"
                " is of type T_PERP_PARKING_OUT_FWD or T_PERP_PARKING_OUT_BWD, TRJPLA"
                " shall send <PlannedTrajPort.trajType> = PERP_PARK_OUT_TRAJ."
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


@verifies("1500183")
@testcase_definition(
    name="SWRT_CNC_TRJPLA_PerpendicularParkOutTrajType",
    description="This testcase will verify the planned traj type, based on selected target pose type.",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TrjplaPerpParkOutTrajTypeTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TrjplaPerpParkOutTrajType,
        ]
