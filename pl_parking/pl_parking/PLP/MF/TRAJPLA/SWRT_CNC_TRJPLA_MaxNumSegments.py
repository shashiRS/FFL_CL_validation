"""SWRT CNC TRAJPLA TestCases
SWRT_CNC_TRJPLA_MaxNumSegments.py
Test scenario: Scenario can have ParkIn or Parkout maneuver into a parking slot of any type
"""

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
        f"TRJPLA shall send maximum AP_P_MAX_NUM_SEGMENTS_IN_PATH_NU({ConstantsTrajpla.Parameter.AP_P_MAX_NUM_SEGMENTS_IN_PATH_NU}) "
        f"number of segments and specify the actual number in TrajPlanVisuPort.numValidSegments"
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
        _log.debug("Starting processing...")
        # Update the details from the results page with the needed information
        # All the information from self.result.details is transferred to
        # report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # Create empty lists for titles, plots and remarks,if they are needed,
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        try:
            t2 = None
            evaluation = ""
            read_data = self.readers[SIGNAL_DATA]
            signal_summary = {}
            signal_name = example_obj._properties
            self.result.measured_result = DATA_NOK  # Initializing the result with data nok
            # Create a lists which will contain test status  and test result for each frame
            # based on test condition.
            frame_test_status = []
            frame_test_result = []

            traj_valid = read_data["trajValid_nu"]
            num_valid_segments = read_data["numValidSegments"]

            for idx, val in enumerate(traj_valid):
                if val == ConstantsTrajpla.TRAJ_VALID:
                    t2 = idx
                    break
                frame_test_status.append("NA:trajValid_nu not True")
                frame_test_result.append(None)

            if t2 is not None:
                for idx in range(t2, len(traj_valid)):
                    if traj_valid.iloc[idx] == ConstantsTrajpla.TRAJ_VALID:
                        if num_valid_segments.iloc[idx] <= ConstantsTrajpla.Parameter.AP_P_MAX_NUM_SEGMENTS_IN_PATH_NU:
                            frame_test_status.append("Pass")
                            frame_test_result.append(True)
                        else:
                            if not evaluation:
                                evaluation = " ".join(
                                    f"Failed: {signal_name['numValidSegments']} = {num_valid_segments.iloc[idx]} "
                                    f"at frame {idx}".split()
                                )
                            frame_test_status.append(
                                f"Fail: numValidSegments > "
                                f"{ConstantsTrajpla.Parameter.AP_P_MAX_NUM_SEGMENTS_IN_PATH_NU}"
                            )
                            frame_test_result.append(False)
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
                        f"Evaluation not possible, valid trajectory "
                        f"{signal_name['trajValid_nu']} == True(1) not found"
                    )
            else:
                verdict = fc.PASS
                self.result.measured_result = TRUE
                evaluation = "Passed"

            expected_val = (
                f"{signal_name['numValidSegments']} <= AP_P_MAX_NUM_SEGMENTS_IN_PATH_NU"
                f"({ConstantsTrajpla.Parameter.AP_P_MAX_NUM_SEGMENTS_IN_PATH_NU})"
            )

            signal_summary[
                f"{signal_name['numValidSegments']} <= AP_P_MAX_NUM_SEGMENTS_IN_PATH_NU"
                f"({ConstantsTrajpla.Parameter.AP_P_MAX_NUM_SEGMENTS_IN_PATH_NU}), "
                f"when {signal_name['trajValid_nu']} = {ConstantsTrajpla.TRAJ_VALID}"
            ] = [expected_val, evaluation, verdict]

            remark = (
                f"Check if {signal_name['numValidSegments']} <= AP_P_MAX_NUM_SEGMENTS_IN_PATH_NU"
                f"({ConstantsTrajpla.Parameter.AP_P_MAX_NUM_SEGMENTS_IN_PATH_NU}), "
                f"for all frames where {signal_name['trajValid_nu']} = {ConstantsTrajpla.TRAJ_VALID}"
            )
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            frame_number_list = list(range(0, len(traj_valid)))
            # add graph for  evaluated signals
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=traj_valid,
                    mode="lines",
                    name="trajValid_nu",
                    hovertemplate="Frame: %{x}<br>Value: %{y}<extra></extra>",
                ),
            )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=num_valid_segments,
                    mode="lines",
                    name="numValidSegments",
                    hovertemplate="Frame: %{x}<br>Value: %{y}<extra></extra>",
                ),
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
                fc.REQ_ID: ["1517121"],
                fc.TESTCASE_ID: ["41543"],
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


@verifies("1517101")
@testcase_definition(
    name="SWRT_CNC_TRJPLA_MaxNumSegments",
    description="This testcase will verify that If a valid path is available (PlannedTrajPort.trajValid_nu == true) "
    "for the given environmental model provided by ApParkingBoxPort and ApEnvModelPort, "
    "TRJPLA shall send up to AP_P_MAX_NUM_SEGMENTS_IN_PATH_NU consecutive segments "
    "of the planned path in TrajPlanVisuPort.plannedGeometricPath and "
    "specify the actual number by setting TrajPlanVisuPort.numValidSegments accordingly.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_fLtxQEsrEe6M5-WQsF_-tQ&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_p9KzlDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17100",
)
@register_inputs("/parking")
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
