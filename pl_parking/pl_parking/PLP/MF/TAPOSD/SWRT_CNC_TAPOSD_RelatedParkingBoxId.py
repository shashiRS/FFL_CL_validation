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

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "MF_RELATED_PARKING_BOX_ID"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Related Parking Box id",
    description="This testcase will verify That the Component shall provide for each target pose that it provides a parking box ID (relatedParkingBoxID)  <targetPosesPort.targetPoses.relatedParkingBoxID> which matches the ID of a given parking box <parkingBoxPort.parkingBoxes.parkingBoxID_nu>.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TaposdRelatedParkingBoxId(TestStep):
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
            evaluation = ""
            read_data = self.readers[SIGNAL_DATA]
            # plots and remarks need to have the same length
            plot_titles, plots, remarks = fh.rep([], 3)
            signal_summary = {}
            # Create a lists which will contain test status
            frame_test_status = []
            signal_name = example_obj._properties
            parkingBoxID = {}
            for idx in range(8):
                parkingBoxID[idx] = read_data[f"parkingBox{idx}"]
            relatedParkingBoxID = {}
            for idx in range(8):
                relatedParkingBoxID[idx] = read_data[f"relatedParkingBoxID_{idx}"]
            num_valid_parkingboxes = read_data["numValidParkingBoxes_nu"]
            num_valid_poses = read_data["numValidPoses"]
            eval_cond = True
            for idx in range(0, len(num_valid_poses)):
                ParkingBoxIdlist = []
                if num_valid_poses.iloc[idx] > 0:
                    for poses in range(int(num_valid_poses.iloc[idx])):
                        for val in range(int(num_valid_parkingboxes.iloc[idx])):
                            ParkingBoxIdlist.append(parkingBoxID[val].iloc[idx])
                        if relatedParkingBoxID[poses].iloc[idx] in ParkingBoxIdlist:
                            evaluation = " ".join(
                                "The evaluation of parkingBoxID and "
                                "relatedParkingBoxID is PASSED where target pose parking box ID (relatedParkingBoxID) matches the ID of a given parking box ".split()
                            )
                            eval_cond = True
                        else:
                            evaluation = " ".join(
                                f"The evaluation of parkingBoxID and "
                                f"relatedParkingBoxID is FAILED at frame {idx} where target pose parking box ID (relatedParkingBoxID) not matches the ID of a given parking box".split()
                            )
                            eval_cond = False
                            frame_test_status.append(
                                "fail:target pose parking box ID (relatedParkingBoxID) not matches the ID of a given parking box"
                            )
                            break
                    if eval_cond:
                        frame_test_status.append(
                            "Pass: target pose parking box ID (relatedParkingBoxID) matches the ID of a given parking box"
                        )
                else:
                    frame_test_status.append("Not evaluated")

            if eval_cond:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict = "passed" if eval_cond else "failed" if eval_cond is False else "not assessed"
            expected_val = "AP.targetPosesPort.targetPoses[%].relatedParkingBoxID is present in AP.parkingBoxPort.parkingBoxes[%]].parkingBoxID_nu"

            signal_summary["parkingBoxID and relatedParkingBoxID"] = [expected_val, evaluation, verdict]
            remark = " ".join(
                "The evaluation of parkingBoxID and "
                "relatedParkingBoxID is PASSED where target pose parking box ID (relatedParkingBoxID) matches the ID of a given parking box".split()
            )
            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)
            frame_number_list = list(range(0, len(num_valid_poses)))
            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=num_valid_poses,
                    mode="lines",
                    name=signal_name["numValidPoses"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=num_valid_parkingboxes,
                    mode="lines",
                    name=signal_name["numValidParkingBoxes_nu"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
            for i in range(int(max(num_valid_poses))):
                fig.add_trace(
                    go.Scatter(
                        x=frame_number_list,
                        y=parkingBoxID[i],
                        mode="lines",
                        name="parkingBoxID" + str(i),
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
                    text=frame_test_status,
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
                fc.REQ_ID: ["2431206"],
                fc.TESTCASE_ID: ["86373"],
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


@verifies("2430583")
@testcase_definition(
    name="SWRT_CNC_TAPOSD_RelatedParkingBoxId",
    description="Verify related parking box id",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_Gk2DQTnrEe-sxr1i_55q4Q&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_p9KzlDK_Ee6mrdm2_agUYg",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TaposdRelatedParkingBoxIdTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TaposdRelatedParkingBoxId,
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
