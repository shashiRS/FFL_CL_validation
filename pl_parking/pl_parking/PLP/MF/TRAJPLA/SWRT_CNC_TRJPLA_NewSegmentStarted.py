"""SWRT CNC TRAJPLA TestCases
SWRT_CNC_TRJPLA_NewSegmentStarted.py
Test Scenario: Can be tested with any Scenario where a valid trajectory is available
"""

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
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, MfSignals, rep
from pl_parking.PLP.MF.constants import ConstantsTrajpla

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


SIGNAL_DATA = "MF_NEW_SEGMENT_STARTED"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="New Segment Started",
    description="If a valid path is available, TRJPLA shall send PlannedTrajPort.newSegmentStarted_nu = true",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TrjplaNewStrokeStarted(TestStep):
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
            evaluation = ""
            read_data = self.readers[SIGNAL_DATA]
            signal_summary = {}
            signal_name = example_obj._properties
            frame_data_dict = {}

            traj_valid = read_data["trajValid_nu"]
            new_segment = read_data["newSegmentStarted_nu"]

            for idx, val in enumerate(traj_valid):
                if val == ConstantsTrajpla.TRAJ_VALID:
                    t2 = idx
                    break
                frame_data_dict[idx] = "trajValid_nu not true"

            eval_cond = None
            if t2 is not None:
                for idx in range(t2, len(traj_valid)):
                    if traj_valid.iloc[idx] == 1 and new_segment.iloc[idx] == 1:
                        evaluation = " ".join(
                            f"The evaluation of {signal_name['newSegmentStarted_nu']} and is PASSED, with values = {new_segment.iloc[idx]}"
                            f" when {signal_name['trajValid_nu']} == "
                            f"{ConstantsTrajpla.TRAJ_VALID} at frame  {idx}".split()
                        )
                        eval_cond = True
                        frame_data_dict[idx] = "Pass"
                        break
                    else:
                        evaluation = " ".join(
                            f"Failed:  at frame  {idx}, with values {signal_name['newSegmentStarted_nu']} "
                            f"= {new_segment.iloc[idx]}"
                            f" and {signal_name['trajValid_nu']} = "
                            f"{traj_valid.iloc[idx]}.".split()
                        )
                        eval_cond = False
                        frame_data_dict[idx] = "Fail"
                        break
            else:
                eval_cond = None
                evaluation = " ".join(
                    "Evaluation not possible, the valid trajectory                            "
                    f" {signal_name['trajValid_nu']} == True(1) was never found.".split()
                )

            if eval_cond is True:
                test_result = fc.PASS
                self.result.measured_result = TRUE
            elif eval_cond is False:
                test_result = fc.FAIL
                self.result.measured_result = FALSE
            else:
                test_result = fc.FAIL
                self.result.measured_result = FALSE
                if not evaluation:
                    evaluation = "Evaluation not possible, check if valid trajectory is available"

            expected_val = f"{signal_name['newSegmentStarted_nu']} = True(1)"
            signal_summary[
                f"{signal_name['newSegmentStarted_nu']} = True(1), when {signal_name['trajValid_nu']} becomes True({ConstantsTrajpla.TRAJ_VALID})"
            ] = [expected_val, evaluation, test_result]
            remark = (
                f"Check if {signal_name['newSegmentStarted_nu']} = True(1), when {signal_name['trajValid_nu']} "
                f"becomes True({ConstantsTrajpla.TRAJ_VALID}) (at rising edge in {signal_name['trajValid_nu']})"
            )
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            # Add plot for  trajValid_nu
            frame_number_list = list(range(0, len(traj_valid)))
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=frame_number_list, y=traj_valid, mode="lines", name="trajValid_nu"))
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=new_segment,
                    mode="lines",
                    name="newSegmentStarted_nu",
                    hovertemplate="Frame: %{x}<br>Value: %{y}<extra></extra>",
                ),
            )
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Frames",
                showlegend=True,
                title="Graphical Overview of Evaluated signals",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            if eval_cond is not None:
                fig.add_vline(
                    x=t2,
                    line_width=1,
                    line_dash="dash",
                    line_color="darkslategray",
                    annotation_text=f"Eval:{test_result}",
                )

            plots.append(fig)

            result_df = {
                "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                fc.REQ_ID: ["1671345"],
                fc.TESTCASE_ID: ["42016"],
                fc.TEST_SAFETY_RELEVANT: [fc.SAFETY_RELEVANT_QM],
                fc.TEST_RESULT: [test_result],
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


@verifies("1671345")
@testcase_definition(
    name="SWRT_CNC_TRJPLA_NewSegmentStarted",
    description="This testcase will verify that If a valid path is output at the beginning of the parking maneuver "
    "(rising edge in PlannedTrajPort.trajValid_nu) for the given environmental model "
    "provided by ApParkingBoxPort and ApEnvModelPort. "
    "TRJPLA shall send PlannedTrajPort.newSegmentStarted_nu = true.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_ZtSAMHluEe6n7Ow9oWyCxw&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_p9KzlDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class TrjplaNewStrokeStartedTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TrjplaNewStrokeStarted,
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
