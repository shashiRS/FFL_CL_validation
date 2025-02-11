"""SWRT CNC TRAJPLA TestCases"""

import logging
import os

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
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, MfSignals
from pl_parking.PLP.MF.constants import ConstantsTrajpla as trajpla

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "MF_SELECTED_TP"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Selected target pose",
    description="Verify that Selected_Target_Pose is in TargetPosesPort.targetPoses[0], when valid path is available",
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
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """  # required docstring
        _log.debug("Starting processing...")
        # Update the details from the results page with the needed information
        # All the information from self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        try:
            t2 = None
            evaluation = ""
            signals = self.readers[SIGNAL_DATA]

            signal_summary = {}
            signal_name = example_obj._properties
            # Create a lists which will contain test status  and test result for each frame
            # based on test condition.
            frame_test_status = []
            frame_test_result = []

            ap_state = signals["ApState"]
            traj_valid = signals["trajValid_nu"]
            chosen_target_pose = signals["apChosenTargetPoseID_nu"]
            target_poseid = signals["poseId0"]
            num_valid_poses = signals["numValidPoses"]

            signals["ApState"] = ap_state.apply(lambda x: fh.get_status_label(x, trajpla.ApStates))

            for idx, val in enumerate(traj_valid):
                if val == trajpla.TRAJ_VALID:
                    t2 = idx
                    break
                frame_test_status.append("NA:trajValid_nu not True")
                frame_test_result.append(None)

            if t2 is not None:
                for idx in range(t2, len(traj_valid)):
                    if traj_valid.iloc[idx] == trajpla.TRAJ_VALID:
                        if num_valid_poses.iloc[idx] == 1:
                            if target_poseid.iloc[idx] == chosen_target_pose.iloc[idx]:
                                frame_test_status.append("Pass")
                                frame_test_result.append(True)
                            else:
                                if not evaluation:
                                    evaluation = " ".join(
                                        f"Failed: {signal_name['poseId0']} != {signal_name['apChosenTargetPoseID_nu']}"
                                        f"at frame {idx}".split()
                                    )
                                frame_test_status.append(f"Fail: {signal_name['poseId0']} != apChosenTargetPoseID_nu")
                                frame_test_result.append(False)
                        else:
                            frame_test_status.append("NA: Number of poses not relevant")
                            frame_test_result.append(None)
                            # if not evaluation:
                            #     evaluation = " ".join(f"Failed: {signal_name['numValidPoses']} != 1. <br>"
                            #                           f"{signal_name['numValidPoses']} = {num_valid_poses.iloc[idx]} "
                            #                           f"at frame {idx}".split())

                    else:
                        frame_test_status.append("NA:trajValid_nu is not true")
                        frame_test_result.append(None)
            else:
                frame_test_result.append(None)
                evaluation = " ".join(
                    "Evaluation not possible," f" {signal_name['trajValid_nu']} == True(1) was never found.".split()
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
                        f"{signal_name['trajValid_nu']} are met in the recording"
                    )
            else:
                verdict = fc.PASS
                self.result.measured_result = TRUE
                evaluation = "Passed"

            expected_val = f"{signal_name['poseId0']} = {signal_name['apChosenTargetPoseID_nu']}"

            signal_summary[f"{signal_name['poseId0']} <br>" f"{signal_name['apChosenTargetPoseID_nu']}"] = [
                expected_val,
                evaluation,
                verdict,
            ]

            remark = " ".join(
                f"{signal_name['poseId0']} = {signal_name['apChosenTargetPoseID_nu']}, when {signal_name['trajValid_nu']} is true".split()
            )
            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            # Create a table containing all signals and their status for each frame
            # for the purpose of analysis.
            frame_number_list = list(range(0, len(target_poseid)))
            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=ap_state,
                    mode="lines",
                    name=signal_name["ApState"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["ApState"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=traj_valid,
                    mode="lines",
                    name=signal_name["trajValid_nu"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br><extra></extra>",
                    text=signals["trajValid_nu"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=chosen_target_pose,
                    mode="lines",
                    name=signal_name["apChosenTargetPoseID_nu"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=target_poseid,
                    mode="lines",
                    name=signal_name["poseId0"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=num_valid_poses,
                    mode="lines",
                    name=signal_name["numValidPoses"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br><extra></extra>",
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
                title="Graphical Overview of Evaluated signals",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plots.append(fig)

            result_df = {
                "Verdict": {"value": verdict, "color": fh.get_color(verdict)},
                fc.REQ_ID: ["1670806"],
                fc.TESTCASE_ID: ["42018"],
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


@verifies("1670806")
@testcase_definition(
    name="SWRT_CNC_TRJPLA_SelectedTargetPose",
    description="The testcase verifies that, if a valid path is available (PlannedTrajPort.trajValid_nu  == true) "
    "for the given environmental model provided by ApParkingBoxPort and ApEnvModelPort, "
    "TRJPLA provides exclusively the Selected_Target_Pose in "
    "TargetPosesPort.targetPoses[0].",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_gQXtAHleEe6n7Ow9oWyCxw&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_p9KzlDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/parking")
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
