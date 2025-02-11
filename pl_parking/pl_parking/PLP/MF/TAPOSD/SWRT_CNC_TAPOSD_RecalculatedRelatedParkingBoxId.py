"""SWRT CNC TAPOSD TestCases"""

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
from pl_parking.PLP.MF.constants import ConstantsTrajpla

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "MF_RECALCULATED_RELATED_PARKING_BOX_ID"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Recalculated Related Parking Box id",
    description="This testcase will verify That the Component shall provide a recalculated target pose with the same associated parking Box ID <targetPosesPort.targetPoses.relatedParkingBoxID> as"
    " the original target pose during the AVG Park in mode <SlotCtrlPort.planningCtrlPort.apState> == AP_AVG_ACTIVE_IN.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TaposdRecalculatedRelatedParkingBoxId(TestStep):
    """defining tetstep"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
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
        try:
            t2 = None
            evaluation = ""
            read_data = self.readers[SIGNAL_DATA]
            # plots and remarks need to have the same length
            plot_titles, plots, remarks = fh.rep([], 3)
            signal_summary = {}
            frame_data_dict = {}
            signal_name = example_obj._properties
            ap_state = read_data["ApState"]
            num_valid_poses = read_data["numValidPoses"]
            poseID = {}
            for idx in range(8):
                poseID[idx] = read_data[f"poseId{idx}"]
            relatedParkingBoxID = {}
            for idx in range(8):
                relatedParkingBoxID[idx] = read_data[f"relatedParkingBoxID_{idx}"]
            read_data["ApState"] = ap_state.apply(lambda x: fh.get_status_label(x, ConstantsTrajpla.ApStates))
            for idx, val in enumerate(ap_state):
                if val == ConstantsTrajpla.ApStates.AP_AVG_ACTIVE_IN:
                    t2 = idx
                    break
                frame_data_dict[idx] = "apState != AP_AVG_ACTIVE_IN"
            eval_cond = True
            if t2 is not None:
                if (
                    ap_state.iloc[idx - 1] == ConstantsTrajpla.ApStates.AP_SCAN_IN
                    and ap_state.iloc[idx] == ConstantsTrajpla.ApStates.AP_AVG_ACTIVE_IN
                ):
                    if num_valid_poses.iloc[idx - 1] > 0:
                        for poses in range(int(num_valid_poses.iloc[idx - 1])):
                            if poseID[0].iloc[idx] == poseID[poses].iloc[idx - 1]:
                                x = poses
                    if relatedParkingBoxID[0].iloc[idx] == relatedParkingBoxID[x].iloc[idx - 1]:
                        eval_cond = True
                        frame_data_dict[idx] = "Pass"
                    else:
                        eval_cond = False
                        frame_data_dict[idx] = "fail"
                if eval_cond:
                    for idx in range(t2 + 1, len(ap_state)):
                        if (
                            num_valid_poses.iloc[idx] > 0
                            and ap_state.iloc[idx] == ConstantsTrajpla.ApStates.AP_AVG_ACTIVE_IN
                        ):
                            if relatedParkingBoxID[0].iloc[idx] == relatedParkingBoxID[0].iloc[idx - 1]:
                                evaluation = " ".join(
                                    "The evaluation of ApState and "
                                    "relatedParkingBoxID is PASSED where recalculated target pose with the same associated parking Box ID as the original target pose ".split()
                                )
                                eval_cond = True
                                frame_data_dict[idx] = "Pass"
                            else:
                                evaluation = " ".join(
                                    f"The evaluation of ApState and "
                                    f"relatedParkingBoxID is FAILED at frame {idx} where recalculated target pose does not have same associated parking Box ID as the original target pose".split()
                                )
                                eval_cond = False
                                frame_data_dict[idx] = "fail"
                                break
                        else:
                            frame_data_dict[idx] = "Not evaluated"
            else:
                eval_cond = False
                evaluation = " ".join("Evaluation not possible, ApState Active in was never found.".split())

            if eval_cond:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict = "passed" if eval_cond else "failed" if eval_cond is False else "not assessed"
            expected_val = "AP.targetPosesPort.targetPoses[%].relatedParkingBoxID of recalculated target pose should have same associated parking Box ID as the original target pose"

            signal_summary["ApState and relatedParkingBoxID"] = [expected_val, evaluation, verdict]

            remark = " ".join(
                f"check the relatedParkingBoxID where a recalculated target pose has the same associated parking Box ID as the original target pose when the following"
                f"conditions is met: <br>"
                f"{signal_name['ApState']} = AP_AVG_ACTIVE_IN({ConstantsTrajpla.ApStates.AP_AVG_ACTIVE_IN})<br>".split()
            )
            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            frame_number_list = list(range(0, len(num_valid_poses)))
            frame_data_list = list(frame_data_dict.values())
            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=ap_state,
                    mode="lines",
                    name=signal_name["ApState"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=read_data["ApState"],
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
            for i in range(int(max(num_valid_poses))):
                fig.add_trace(
                    go.Scatter(
                        x=frame_number_list,
                        y=poseID[i],
                        mode="lines",
                        name="poseId" + str(i),
                        hovertemplate="Frame: %{x}<br>Value: %{y}<br><extra></extra>",
                    )
                )
            for i in range(int(max(num_valid_poses))):
                fig.add_trace(
                    go.Scatter(
                        x=frame_number_list,
                        y=relatedParkingBoxID[i],
                        mode="lines",
                        name="relatedParkingBoxID_" + str(i),
                        hovertemplate="Frame: %{x}<br>Value: %{y}<br><extra></extra>",
                    )
                )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=[0] * len(frame_number_list),
                    mode="lines",  # 'lines' or 'markers'
                    name="Test Status",
                    hovertemplate="Frame: %{x}<br><br>status: %{text}<extra></extra>",
                    text=frame_data_list,
                )
            )
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="frame_number",
                title="Graphical Overview of Evaluated Signals",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plots.append(fig)

            result_df = {
                "Verdict": {"value": verdict, "color": fh.get_color(verdict)},
                fc.REQ_ID: ["2436293"],
                fc.TESTCASE_ID: ["86390"],
                fc.TEST_SAFETY_RELEVANT: [fc.SAFETY_RELEVANT_QM],
            }
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
        self.result.details["Additional_results"] = result_df


@verifies("2436293")
@testcase_definition(
    name="SWRT_CNC_TAPOSD_RecalculatedRelatedParkingBoxId",
    description="Verify Recalculated related parking box id",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_c2E7wDoOEe-sxr1i_55q4Q&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_p9KzlDK_Ee6mrdm2_agUYg",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TaposdRecalculatedRelatedParkingBoxIdTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TaposdRecalculatedRelatedParkingBoxId,
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
