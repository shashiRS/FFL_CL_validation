"""SWRT CNC TRAJPLA TestCases"""

import logging
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
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
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, MfSignals, rep
from pl_parking.PLP.MF.constants import ConstantsTrajpla

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "MF_ANGLED_BACK_IN_TP_TYPE"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Maximum target pose",
    description="For a given parking box of scenario type ANGLED_PARKING_OPENING_TOWARDS_BACK, TAPOSD shall provide 1 target pose of type T_ANGLED_PARKING_STANDARD, in SCAN IN mode.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TaposdScanInAngledBackOpeningTargetPoseType(TestStep):
    """Defining teststep"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        # Update the details from the results page with the needed information
        # All the information from self.result.details is transferred to
        # report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # Create empty lists for titles, plots and remarks,if they are needed,
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)

        try:
            t2 = None
            par_pose = None
            evaluation = ""
            read_data = self.readers[SIGNAL_DATA]

            # Create a dictionary for containing overall test result summary
            signal_summary = {}
            signal_name = example_obj._properties

            self.result.measured_result = DATA_NOK  # Initializing the result with data nok
            # Create a lists which will contain test status  and test result for each frame
            # based on test condition.
            frame_test_status = []
            frame_test_result = []

            ap_state = read_data["ApState"]
            parking_box_id_0 = read_data["parkingBox0"]
            parking_scenario_0 = read_data["parkingScenario_nu0"]
            num_valid_poses = read_data["numValidPoses"]

            signal_map = dict()
            signal_map["ApState"] = ap_state.apply(lambda x: fh.get_status_label(x, ConstantsTrajpla.ApStates))
            signal_map["parkingScenario_nu0"] = parking_scenario_0.apply(
                lambda x: fh.get_status_label(x, ConstantsTrajpla.ScenarioType)
            )
            related_parking_box_id = {}
            pose_type = {}
            for idx in range(8):
                related_parking_box_id[idx] = read_data[f"relatedParkingBoxID_{idx}"]
                pose_type[idx] = read_data[f"poseType{idx}"]
                signal_map[f"poseType{idx}"] = pose_type[idx].apply(
                    lambda x: fh.get_status_label(x, ConstantsTrajpla.PoseType)
                )

            for idx, val in enumerate(ap_state):
                if val == ConstantsTrajpla.ApStates.AP_SCAN_IN:
                    t2 = idx
                    break
                frame_test_status.append("apState not relevant")
                frame_test_result.append(None)

            for idx, val in enumerate(parking_scenario_0):
                if val == ConstantsTrajpla.ScenarioType.ANGLED_PARKING_OPENING_TOWARDS_BACK:
                    par_pose = idx
                    break

            if t2 is not None:
                if par_pose is not None:
                    for idx in range(t2, len(ap_state)):
                        if parking_scenario_0.iloc[
                            idx
                        ] == ConstantsTrajpla.ScenarioType.ANGLED_PARKING_OPENING_TOWARDS_BACK and (
                            ap_state.iloc[idx] == ConstantsTrajpla.ApStates.AP_SCAN_IN
                        ):
                            pose_count = 0
                            if num_valid_poses.iloc[idx] > 0:
                                for i in range(int(num_valid_poses.iloc[idx])):
                                    if (
                                        related_parking_box_id[i].iloc[idx] == parking_box_id_0.iloc[idx]
                                        and pose_type[i].iloc[idx]
                                        == ConstantsTrajpla.PoseType.T_ANGLED_PARKING_STANDARD
                                    ):
                                        pose_count += 1

                                if pose_count == ConstantsTrajpla.Parameter.ANGLED_PARK_MAX_TARGET_POSE:
                                    frame_test_result.append(True)
                                    frame_test_status.append(
                                        f"Pass: Target Poses Count for Parking Box 0 = {pose_count}"
                                    )
                                else:
                                    if not evaluation:
                                        evaluation = " ".join(
                                            f"FAILED: Number of target poses of type T_ANGLED_PARKING_STANDARD"
                                            f"for Parking Box 0 = {pose_count} at frame {idx}".split()
                                        )
                                    frame_test_result.append(False)
                                    frame_test_status.append(f"Fail: Target Poses Count = {pose_count}")
                            else:
                                frame_test_status.append("NA: Valid poses not found")
                                frame_test_result.append(None)
                        else:
                            frame_test_status.append("NA: ApState or Scenario Type not relevant")
                            frame_test_result.append(None)
                else:
                    frame_test_result.append(None)
                    evaluation = " ".join(
                        "Evaluation not possible, the value of signal "
                        f"{signal_name['parkingScenario_nu0']} was never equal to ANGLED_PARKING_OPENING_TOWARDS_BACK"
                        f"({ConstantsTrajpla.ScenarioType.ANGLED_PARKING_OPENING_TOWARDS_BACK})".split()
                    )
            else:
                frame_test_result.append(None)
                evaluation = " ".join(
                    f"Evaluation not possible, the trigger value for {signal_name['ApState']} "
                    f"== AP_SCAN_IN({ConstantsTrajpla.ApStates.AP_SCAN_IN}) was never found.".split()
                )

            if False in frame_test_result:
                verdict = fc.FAIL
                self.result.measured_result = FALSE
            elif frame_test_result == [None] * len(frame_test_result):
                verdict = fc.FAIL
                self.result.measured_result = FALSE
                if not evaluation:
                    evaluation = (
                        f"Evaluation not possible, check if trigger conditions for "
                        f"{signal_name['ApState']} or {signal_name['parkingScenario_nu0']}"
                        f" are met in the recording"
                    )
            else:
                verdict = fc.PASS
                self.result.measured_result = TRUE
                evaluation = "Passed"

            expected_val = (
                f"Number of target poses of type T_ANGLED_PARKING_STANDARD"
                f"({ConstantsTrajpla.PoseType.T_ANGLED_PARKING_STANDARD}) for Parking Box 0"
                f" = {ConstantsTrajpla.Parameter.ANGLED_PARK_MAX_TARGET_POSE}"
            )

            signal_summary[
                "Number of target poses of type T_ANGLED_PARKING_STANDARD"
                f"({ConstantsTrajpla.PoseType.T_ANGLED_PARKING_STANDARD}) <br>"
                f"for parking box 0 of Scenario type ANGLED_PARKING_OPENING_TOWARDS_BACK"
                f"({ConstantsTrajpla.ScenarioType.ANGLED_PARKING_OPENING_TOWARDS_BACK})"
            ] = [expected_val, evaluation, verdict]

            remark = (
                f"Check if Number of target poses of pose type T_ANGLED_PARKING_STANDARD({ConstantsTrajpla.PoseType.T_ANGLED_PARKING_STANDARD})"
                f" per parking box of type ANGLED_PARKING_OPENING_TOWARDS_BACK"
                f" == {ConstantsTrajpla.Parameter.ANGLED_PARK_MAX_TARGET_POSE}"
            )
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            frame_number_list = list(range(0, len(ap_state)))

            # add plots
            fig = go.Figure()
            for i in range(int(max(num_valid_poses))):
                fig.add_trace(
                    go.Scatter(
                        x=frame_number_list,
                        y=related_parking_box_id[i],
                        mode="lines",  # 'lines' or 'markers'
                        name=f"targetPoses_{i}.relatedParkingBoxID",
                        meta=f"targetPoses_{i}.relatedParkingBoxID",
                        hovertemplate="%{meta}:<br>Frame: %{x}<br>Value: %{y}<extra></extra>",
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=frame_number_list,
                        y=pose_type[i],
                        mode="lines",  # 'lines' or 'markers'
                        name=f"targetPoses_{i}.type",
                        meta=f"targetPoses_{i}.type",
                        hovertemplate="Frame: %{x}<br>Value: %{y}<br>%{meta}: %{text}<extra></extra>",
                        text=signal_map[f"poseType{i}"],
                    )
                )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=ap_state,
                    mode="lines",  # 'lines' or 'markers'
                    name="apState",
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br>apState: %{text}<extra></extra>",
                    text=signal_map["ApState"],
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=parking_box_id_0,
                    mode="lines",  # 'lines' or 'markers'
                    name=".parkingBoxes_0.parkingBoxID_nu",
                    hovertemplate=".parkingBoxes_0.parkingBoxID_nu<br>Frame: %{x}<br>Value: %{y}<extra></extra>",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=parking_scenario_0,
                    mode="lines",  # 'lines' or 'markers'
                    name="parkingBoxes_0.parkingScenario_nu",
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br>scenario type: %{text}<extra></extra>",
                    text=signal_map["parkingScenario_nu0"],
                )
            )
            if True in frame_test_result or False in frame_test_result:
                fig.add_trace(
                    go.Scatter(
                        x=frame_number_list,
                        y=[0] * len(frame_number_list),
                        mode="lines",  # 'lines' or 'markers'
                        name="Test Status",
                        hovertemplate="Frame: %{x}<br><br>status: %{text}<extra></extra>",
                        text=frame_test_status,
                    )
                )

            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Frames",
                showlegend=True,
                title="Graphical Overview of Evaluated signals",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)

            res_valid = (np.array(frame_test_result)) != np.array(None)
            res_valid_int = [int(elem) for elem in res_valid]
            res_valid_int.insert(0, 0)
            eval_start = [i - 1 for i in range(1, len(res_valid_int)) if res_valid_int[i] - res_valid_int[i - 1] == 1]
            eval_stop = [i - 1 for i in range(1, len(res_valid_int)) if res_valid_int[i] - res_valid_int[i - 1] == -1]
            if len(eval_start) > 0:
                for i in range(len(eval_start)):
                    fig.add_vline(
                        x=eval_start[i],
                        line_width=1,
                        line_dash="dash",
                        line_color="darkslategray",
                        annotation_text=f"t{i + 1}Start",
                    )
            if len(eval_stop) > 0:
                for i in range(len(eval_stop)):
                    fig.add_vline(
                        x=eval_stop[i],
                        line_width=1,
                        line_dash="dash",
                        line_color="darkslategray",
                        annotation_text=f"t{i + 1}Stop",
                    )

            plots.append(fig)

            result_df = {
                "Verdict": {"value": verdict.title(), "color": fh.get_color(verdict)},
                fc.REQ_ID: ["2435155"],
                fc.TESTCASE_ID: ["86514"],
                fc.TEST_SAFETY_RELEVANT: [fc.SAFETY_RELEVANT_QM],
                fc.TEST_RESULT: [verdict],
            }
            self.result.details["Additional_results"] = result_df

        except Exception as e:
            _log.error(f"Error processing signals: {e}")
            self.result.measured_result = DATA_NOK
            self.sig_sum = f"<p>Error processing signals : {e}</p>"
            plots.append(self.sig_sum)

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)


@verifies("2435155")
@testcase_definition(
    name="SWRT_CNC_TAPOSD_ScanInAngledBackOpeningTargetPoseType",
    description=(
        "This testcase will verify that, For a given parking box of scenario type ANGLED_PARKING_OPENING_TOWARDS_BACK, "
        "TAPOSD shall provide 1 target pose of type T_ANGLED_PARKING_STANDARD, in SCAN IN mode"
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TaposdScanInAngledBackOpeningTargetPoseTypeTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TaposdScanInAngledBackOpeningTargetPoseType,
        ]


def convert_dict_to_pandas(
    signal_summary: dict,
    table_remark="",
    table_title="",
):
    """Converts a dictionary to a Pandas DataFrame and creates an HTML table."""
    # Create a DataFrame from the dictionary
    evaluation_summary = pd.DataFrame(
        {
            "Signal Summary": {key: key for key, val in signal_summary.items()},
            "Expected Values": {key: val[0] for key, val in signal_summary.items()},
            "Summary": {key: val[1] for key, val in signal_summary.items()},
            "Verdict": {key: val[2] for key, val in signal_summary.items()},
        }
    )

    # Generate HTML table using build_html_table function
    return fh.build_html_table(evaluation_summary, table_remark, table_title)
