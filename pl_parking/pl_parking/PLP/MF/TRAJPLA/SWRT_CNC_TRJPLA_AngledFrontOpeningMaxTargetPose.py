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

SIGNAL_DATA = "MF_ANGLED_FRONT_MAX_TP"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Maximum target pose",
    description="TRJPLA shall provide maximum 2 target pose per angled parking box with opening towards front",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TrjplaAngledParkingFrontOpening(TestStep):
    """Defining teststep"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        t2 = None
        par_pose = None
        evaluation = ""
        read_data = self.readers[SIGNAL_DATA].signals

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)
        # Create a dictionary for containing overall test result summary
        signal_summary = {}
        signal_name = example_obj._properties
        # Create a dictionary which will contain test status for each timestamp
        # based on test condition.
        frame_data_dict = {}
        test_result_dict = {}

        ap_state = read_data["ApState"].tolist()
        parking_scenario_0 = read_data["parkingScenario_nu0"].tolist()
        num_valid_poses = read_data["numValidPoses"].tolist()

        for idx, val in enumerate(ap_state):
            if val == ConstantsTrajpla.AP_SCAN_IN or val == ConstantsTrajpla.AP_SCAN_OUT:
                t2 = idx
                break
            frame_data_dict[idx] = "apState != AP_SCAN_IN or AP_SCAN_OUT"

        for idx, val in enumerate(parking_scenario_0):
            if val == ConstantsTrajpla.ANGLED_PARKING_OPENING_TOWARDS_FRONT:
                par_pose = idx
                break

        if t2 is not None:
            if par_pose is not None:
                for idx in range(t2, len(ap_state)):
                    if parking_scenario_0[idx] == ConstantsTrajpla.ANGLED_PARKING_OPENING_TOWARDS_FRONT and (
                        ap_state[idx] == ConstantsTrajpla.AP_SCAN_IN or ap_state[idx] == ConstantsTrajpla.AP_SCAN_OUT
                    ):
                        if num_valid_poses[idx] <= ConstantsTrajpla.ANGLED_PARK_MAX_TARGET_POSE:
                            evaluation = " ".join(
                                f"The evaluation of {signal_name['parkingScenario_nu0']} and "
                                f"{signal_name['numValidPoses']} is PASSED"
                            )
                            test_result_dict[idx] = True
                            frame_data_dict[idx] = "Pass"
                        else:
                            evaluation = " ".join(
                                f"The evaluation of {signal_name['parkingScenario_nu0']} and "
                                f"{signal_name['numValidPoses']} is FAILED with more than 1 target pose per "
                                "angled parking box with opening towards back".split()
                            )
                            test_result_dict[idx] = False
                            frame_data_dict[idx] = (
                                "More than 1 target pose/angled parking box with opening towards back"
                            )
                    else:
                        frame_data_dict[idx] = "Input conditions not met"
            else:
                test_result_dict[0] = False
                evaluation = " ".join(
                    "Evaluation not possible, the value of signal "
                    f"{signal_name['parkingScenario_nu0']} was never equal to "
                    f"{ConstantsTrajpla.ANGLED_PARKING_OPENING_TOWARDS_FRONT}".split()
                )
        else:
            test_result_dict[0] = False
            evaluation = " ".join(
                "Evaluation not possible, the trigger value for                             "
                f" {signal_name['ApState']} was never found.".split()
            )

        if all(test_result_dict.values()):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        signal_summary[f"{signal_name['numValidPoses']} and {signal_name['parkingScenario_nu0']}"] = evaluation

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
        frame_number_list = list(range(0, len(ap_state)))
        frame_data_list = list(frame_data_dict.values())
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=["Frames", "apState", "ParkingScenario", "NumValidPoses", "Status"],
                        fill_color="paleturquoise",
                    ),
                    cells=dict(
                        values=[
                            frame_number_list,
                            ap_state,
                            parking_scenario_0,
                            num_valid_poses,
                            frame_data_list,
                        ],
                        fill=dict(
                            color=[
                                "rgb(245, 245, 245)",
                                "white",
                                "white",
                                "white",
                                [
                                    "rgba(250, 0, 0, 0.8)" if "More than 1 target" in val else "white"
                                    for val in frame_data_list
                                ],
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
                                "AP_INACTIVE",
                                "AP_SCAN_IN",
                                "AP_SCAN_OUT",
                                "AP_AVG_ACTIVE_IN",
                                "AP_AVG_ACTIVE_OUT",
                                "PARALLEL_PARKING",
                                "PERPENDICULAR_PARKING",
                                "ANGLED_PARKING_OPENING_TOWARDS_BACK",
                                "ANGLED_PARKING_OPENING_TOWARDS_FRONT",
                                "MAX_NUM_PLANNED_TRAJ_TYPES",
                            ],
                            [0, 1, 2, 3, 4, 0, 1, 2, 3, 10],
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
            fc.REQ_ID: ["1612330"],
            fc.TESTCASE_ID: ["42023"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This testcase will verify that If one of the following conditions is fullfilled:"
                "<SlotCtrlPort.planningCtrlPort.apState> == AP_SCAN_IN "
                "<SlotCtrlPort.planningCtrlPort.apState> == AP_SCAN_OUT TRJPLA shall provide maximum 1"
                "target pose per angled parking box with opening towards front in <TargetPosesPort.targetPoses>"
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


@verifies("1612328")
@testcase_definition(
    name="SWRT_CNC_TRJPLA_AngledFrontOpeningMaxTargetPose",
    description=(
        "Verify that TRJPLA shall provide maximum 1 target pose per angled parking box with opening towards front"
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TrjplaAngledParkingFrontOpeningTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TrjplaAngledParkingFrontOpening,
        ]
