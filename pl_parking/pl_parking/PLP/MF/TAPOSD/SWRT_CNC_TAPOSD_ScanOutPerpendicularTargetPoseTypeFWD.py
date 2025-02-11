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
from pl_parking.PLP.MF.constants import ConstantsTaposd, ConstantsTrajpla

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "MF_PERPENDICULAR_FWD_TP_TYPE"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Target pose type",
    description="For a given parking box in slot zero of the parking box port WHICH HAS scenario type PERPENDICULAR_PARKING "
    "WHERE the yaw angle of the current ego vehicle is within a range of +-90deg relative "
    "to the curb-to-road direction of the associated parking box (parked in backward), "
    "THERE TAPOSD shall provide 2 target pose of type T_PERP_PARKING_OUT_FWD with different target sides.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TaposdScanOutParpendicularFwdTargetPoseType(TestStep):
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
            parking_scenario_0 = read_data["parkingScenario_nu0"]
            parking_box_id_0 = read_data["parkingBox0"]
            num_valid_poses = read_data["numValidPoses"]

            signal_map = dict()
            signal_map["ApState"] = ap_state.apply(lambda x: fh.get_status_label(x, ConstantsTrajpla.ApStates))
            signal_map["parkingScenario_nu0"] = parking_scenario_0.apply(
                lambda x: fh.get_status_label(x, ConstantsTrajpla.ScenarioType)
            )

            related_parking_box_id = {}
            pose_type = {}
            target_side = {}
            for idx in range(8):
                related_parking_box_id[idx] = read_data[f"relatedParkingBoxID_{idx}"]
                pose_type[idx] = read_data[f"poseType{idx}"]
                target_side[idx] = read_data[f"targetPoseSide{idx}"]
                signal_map[f"poseType{idx}"] = pose_type[idx].apply(
                    lambda x: fh.get_status_label(x, ConstantsTrajpla.PoseType)
                )
                signal_map[f"targetSide{idx}"] = target_side[idx].apply(
                    lambda x: fh.get_status_label(x, ConstantsTaposd.TargetSide)
                )

            for idx, val in enumerate(ap_state):
                if val == ConstantsTrajpla.ApStates.AP_SCAN_OUT:
                    t2 = idx
                    break
                frame_test_status.append("apState not relevant")
                frame_test_result.append(None)

            for idx, val in enumerate(parking_scenario_0):
                if val == ConstantsTrajpla.ScenarioType.PERPENDICULAR_PARKING:
                    par_pose = idx
                    break

            if t2 is not None:
                if par_pose is not None:
                    for idx in range(t2, len(ap_state)):
                        if parking_scenario_0.iloc[idx] == ConstantsTrajpla.ScenarioType.PERPENDICULAR_PARKING and (
                            ap_state.iloc[idx] == ConstantsTrajpla.ApStates.AP_SCAN_OUT
                        ):
                            pose_count = 0
                            rgt_side_pose_count = 0
                            lft_side_pose_count = 0
                            if num_valid_poses.iloc[idx] > 0:
                                for i in range(int(num_valid_poses.iloc[idx])):
                                    if (
                                        related_parking_box_id[i].iloc[idx] == parking_box_id_0.iloc[idx]
                                        and pose_type[i].iloc[idx] == ConstantsTrajpla.PoseType.T_PERP_PARKING_OUT_FWD
                                    ):
                                        pose_count += 1
                                        if target_side[i].iloc[idx] == ConstantsTaposd.TargetSide.TS_RIGHT_SIDE:
                                            rgt_side_pose_count += 1
                                        if target_side[i].iloc[idx] == ConstantsTaposd.TargetSide.TS_LEFT_SIDE:
                                            lft_side_pose_count += 1

                                if (
                                    pose_count == ConstantsTrajpla.Parameter.PERP_PARK_MAX_TARGET_POSE
                                    and rgt_side_pose_count == 1
                                    and lft_side_pose_count == 1
                                ):
                                    frame_test_result.append(True)
                                    frame_test_status.append(
                                        f"Pass: Target Poses Count for Parking Box 0 = {pose_count}"
                                    )
                                else:
                                    if not evaluation:
                                        evaluation = " ".join(
                                            f"FAILED: Number of target poses of type T_PERP_PARKING_OUT_FWD for Parking Box 0 = {pose_count}<br>"
                                            f"Number of T_PERP_PARKING_OUT_FWD poses with target side TS_RIGHT_SIDE = {rgt_side_pose_count}<br>"
                                            f"Number of T_PERP_PARKING_OUT_FWD poses with target side TS_LEFT_SIDE = {lft_side_pose_count}<br>"
                                            f" at frame {idx}".split()
                                        )
                                    frame_test_result.append(False)
                                    frame_test_status.append(
                                        f"Fail: Target Poses T_PERP_PARKING_OUT_FWD Count  = {pose_count}<br>"
                                        f"T_PERP_PARKING_OUT_FWD Target Poses with TS_RIGHT_SIDE Count: {rgt_side_pose_count}<br>"
                                        f"T_PERP_PARKING_OUT_FWD Target Poses with TS_LEFT_SIDE Count: {lft_side_pose_count}"
                                    )
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
                        f"{signal_name['parkingScenario_nu0']} was never equal to PERPENDICULAR_PARKING"
                        f"({ConstantsTrajpla.ScenarioType.PERPENDICULAR_PARKING})".split()
                    )
            else:
                frame_test_result.append(None)
                evaluation = " ".join(
                    f"Evaluation not possible, the trigger value for {signal_name['ApState']} "
                    f"== AP_SCAN_OUT({ConstantsTrajpla.ApStates.AP_SCAN_OUT}) was never found.".split()
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
                f"Number of target poses type T_PERP_PARKING_OUT_FWD for Parking Box 0 = {ConstantsTrajpla.Parameter.PERP_PARK_MAX_TARGET_POSE}<br>"
                f"Number of T_PERP_PARKING_OUT_FWD target poses of Side TS_RIGHT_SIDE = 1<br>"
                f"Number of T_PERP_PARKING_OUT_FWD target poses of Side TS_LEFT_SIDE = 1"
            )

            signal_summary[
                "Number of target poses of type T_PERP_PARKING_OUT_FWD"
                f"({ConstantsTrajpla.PoseType.T_PERP_PARKING_OUT_FWD}) <br>"
                f"for parking box 0 of Scenario type PERPENDICULAR_PARKING"
                f"({ConstantsTrajpla.ScenarioType.PERPENDICULAR_PARKING})"
            ] = [expected_val, evaluation, verdict]

            remark = (
                f"For parking box of type PERPENDICULAR_PARKING({ConstantsTrajpla.ScenarioType.PERPENDICULAR_PARKING}), "
                f"check if {ConstantsTrajpla.Parameter.PERP_PARK_MAX_TARGET_POSE} target poses of "
                f"pose type T_PERP_PARKING_OUT_FWD({ConstantsTrajpla.PoseType.T_PERP_PARKING_OUT_FWD}), "
                f"with different target sides, TS_RIGHT_SIDE({ConstantsTaposd.TargetSide.TS_RIGHT_SIDE}) "
                f"and TS_LEFT_SIDE({ConstantsTaposd.TargetSide.TS_LEFT_SIDE}), are available"
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
                        y=target_side[i],
                        mode="lines",  # 'lines' or 'markers'
                        name=f"targetPoses_{i}.targetSide",
                        meta=f"targetPoses_{i}.targetSide",
                        hovertemplate="Frame: %{x}<br>Value: %{y}<br>%{meta}: %{text}<extra></extra>",
                        text=signal_map[f"targetSide{i}"],
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
                fc.REQ_ID: ["2442260"],
                fc.TESTCASE_ID: ["86964"],
                fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
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


@verifies("2442260")
@testcase_definition(
    name="SWRT_CNC_TAPOSD_ScanOutParpendicularFwdTargetPoseType",
    description=(
        "This testcase will verify that For a given parking box in slot zero of the parking box port WHICH HAS scenario type PERPENDICULAR_PARKING "
        "WHERE the yaw angle of the current ego vehicle is within a range of +-90deg relative "
        "to the curb-to-road direction of the associated parking box (parked in backward), "
        "THERE TAPOSD shall provide 2 target pose of type T_PERP_PARKING_OUT_FWD with different target sides."
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TaposdScanOutParpendicularFwdTargetPoseTypeTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TaposdScanOutParpendicularFwdTargetPoseType,
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
