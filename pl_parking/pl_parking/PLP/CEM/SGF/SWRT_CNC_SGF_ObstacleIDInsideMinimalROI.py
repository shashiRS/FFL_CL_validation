#!/usr/bin/env python3
"""SWRT_CNC_SGF_ObstacleIDInsideMinimalROI"""

import logging
import os
import sys

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
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    convert_dict_to_pandas,
    get_color,
    rep,
)
from pl_parking.PLP.CEM.SGF.ft_helper import SGFSignals

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "<uib11434>"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "ObstacleIDInsideMinimalROI"
sgf_obj = SGFSignals()


@teststep_definition(
    step_number=1,
    name="Obstacle ID Inside Minimal ROI",
    description="Check if as long as a Static Obstacle is detected inside the minimal static obstacle ROI and "
    "only referenced by a single obstacleId at a time , SGF shall use the same obstacle Id for these "
    "Static objects.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SGFSignals)
class TestStepObstacleIDInsideMinimalROI(TestStep):
    """TestStep for evaluating static objects ID, utilizing a custom report."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()
        self.test_result = fc.INPUT_MISSING
        self.sig_sum = None

    @staticmethod
    def find_mismatches(signal):
        """Check if all elements have the same value. In case not, return the positions of mismatches"""
        # Compare each element with the previous one using shift
        diff_series = signal != signal.shift()
        diff_indices = diff_series[diff_series].index

        # Ignore the first element (shift creates NaN at the start)
        diff_indices = diff_indices[1:]

        if len(diff_indices) > 0:
            # Return the indices of the mismatches
            return False, diff_indices
        return True, None

    def process(self):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        _log.debug("Starting processing...")

        # Update the details from the results page with the needed information. All the information from
        # self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks, if they are needed.
        # Plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)

        # Initializing the dictionary with data for final evaluation table
        signal_summary = {}

        list_of_errors = []

        # Load signals
        signals_df = self.readers[SIGNAL_DATA]
        # filter only valid outputs
        signals_df = signals_df[signals_df["SGF_sig_status"] == 1]
        # filter only frames where only one obstacle id detected
        signals_df = signals_df[signals_df["numPolygons"] == 1]
        signal_evaluated = sgf_obj.get_properties()[sgf_obj.Columns.SGF_OBJECT_ID][0]

        if not signals_df.empty:
            sgf_time = signals_df[sgf_obj.Columns.SGF_TIMESTAMP]
            obstacle_id = signals_df[sgf_obj.Columns.SGF_OBJECT_ID, 0]

            result, indices = self.find_mismatches(obstacle_id)

            if result is False:
                for idx in indices:
                    invalid_timestamp = signals_df.at[idx, sgf_obj.Columns.SGF_TIMESTAMP]
                    error_dict = {
                        "Signal name": signal_evaluated,
                        "Timestamp": invalid_timestamp,
                        "New object ID": signals_df.at[idx, (sgf_obj.Columns.SGF_OBJECT_ID, 0)],
                        "Description": "not the same ID is used for the detected obstacle in all the frames",
                    }
                    list_of_errors.append(error_dict)
                description = " ".join(
                    f"The evaluation is <b>FAILED</b> at timestamp {list_of_errors[0]['Timestamp']} "
                    f"because {list_of_errors[0]['Description']} ".split()
                )
                self.test_result = fc.FAIL
            else:
                description = (
                    "The test is <b>PASSED</b>, the same ID is used in all frames to identify the detected object."
                )
                self.test_result = fc.PASS
        else:
            description = "The test is <b>NOT ASSESSED</b>, no obstacle or more than one obstacle are present."
            self.test_result = fc.NOT_ASSESSED

        # Report result status
        if self.test_result == fc.INPUT_MISSING or self.test_result == fc.NOT_ASSESSED:
            self.result.measured_result = DATA_NOK
        elif self.test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif self.test_result == fc.FAIL:
            self.result.measured_result = FALSE

        signal_summary[signal_evaluated] = description
        remark = " ".join(
            "As long as a Static Obstacle is detected inside the minimal static obstacle ROI and only "
            "referenced by a single obstacleId at a time, SGF use the same obstacle Id for this "
            "Static object.".split()
        )

        # The signal summary and observations will be converted to pandas
        # and finally the html table will be created with them
        self.sig_sum = convert_dict_to_pandas(signal_summary=signal_summary, table_remark=remark)

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        result_df = {
            "Verdict": {"value": self.test_result.title(), "color": get_color(self.test_result)},
            fc.REQ_ID: ["1522142"],
            fc.TESTCASE_ID: ["39231"],
            fc.TEST_DESCRIPTION: [
                "Check if as long as a Static Obstacle is detected inside the minimal static obstacle ROI and "
                "only referenced by a single obstacleId at a time , SGF shall use the same obstacle Id for these "
                "Static objects."
            ],
        }

        self.result.details["Additional_results"] = result_df

        if self.result.measured_result is FALSE:
            list_of_errors_df = pd.DataFrame(list_of_errors)
            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(go.Scatter(x=sgf_time, y=obstacle_id, mode="lines", name=sgf_obj.Columns.SGF_OBJECT_ID))
            # Display where a new ID is assigned to the object
            fig.add_trace(
                go.Scatter(
                    x=list_of_errors_df["Timestamp"],
                    y=list_of_errors_df["New object ID"],
                    name="The new id of the object",
                    mode="markers",
                    marker={"color": "red"},
                    hovertemplate="New ID: %{y}" + "<br>SGF Timestamp: %{x}",
                )
            )
            fig["layout"]["xaxis"].update(title_text="SGF Timestamp")
            fig["layout"]["yaxis"].update(title_text="Object ID")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)

            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        # Add the plots in html page
        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")


@verifies("1522142")
@testcase_definition(
    name="SWRT_CNC_SGF_ObstacleIDInsideMinimalROI",
    description="This test case checks that as long as a Static Obstacle is detected inside the minimal static "
    "obstacle ROI and only referenced by a single obstacleId at a time (one Presumed Static Obstacle), "
    "SGF shall use the same obstacle Id for these Static objects.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_8OJg6UxLEe6M5-WQsF_-tQ&componentURI=https%3A%2F%2Fjazz.conti.de%2F"
    "rm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration="
    "https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17100",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class ObstacleIDInsideMinimalROI(TestCase):
    """Obstacle ID test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepObstacleIDInsideMinimalROI,
        ]
