#!/usr/bin/env python3
"""SWRT_CNC_SGF_StaticObjectsSplitID"""

import logging
import os
import sys

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
__copyright__ = "2023-2024, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "StaticObjectsSplitID"
sgf_obj = SGFSignals()


@teststep_definition(
    step_number=1,
    name="Static Objects Split ID",
    description="This test case verifies that SGF gives a new 'u_id' for all static objects created by splitting "
    "an object in the previous timeframe",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SGFSignals)
class TestStepStaticObjectsSplitID(TestStep):
    """TestStep for evaluating IDs of a split Presumed Static Obstacle, utilizing a custom report."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()
        self.test_result = fc.INPUT_MISSING
        self.sig_sum = None

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
        description = ""

        # Load signals
        signals_df = self.readers[SIGNAL_DATA]
        # filter only valid outputs
        signals_df = signals_df[signals_df["SGF_sig_status"] == 1]
        # filter only frames where at least one obstacle id detected
        signals_df = signals_df[signals_df["numPolygons"] >= 1]

        signal_evaluated = sgf_obj.get_properties()[sgf_obj.Columns.SGF_OBJECT_ID][0]
        obstacle_id = signals_df.filter(regex="polygonId").values

        # num of static objects per frame
        num_objects = signals_df["numPolygons"].values
        num_frames = signals_df.shape[0]

        if obstacle_id.shape[1] > 0:
            previous_objects_id = np.array([0])
            for i in range(num_frames):
                obj_in_frame = num_objects[i]
                current_objects_id = obstacle_id[i, 0:obj_in_frame]
                if current_objects_id.size == 1 and previous_objects_id[0] != current_objects_id[0]:
                    previous_objects_id = current_objects_id
                elif previous_objects_id != 0 and previous_objects_id.size == 1 and current_objects_id.size == 2:
                    # Concatenate the previous and current objects IDs and check if they are unique
                    combined = np.concatenate((previous_objects_id, current_objects_id))
                    is_unique = len(np.unique(combined)) == combined.size

                    if not is_unique:
                        failed_timestamps = signals_df["SGF_timestamp"].values[i]
                        error_dict = {
                            "Signal name": signal_evaluated,
                            "Timestamp": failed_timestamps,
                            "Previous Objects ID": (1, previous_objects_id[0]),
                            "Current Objects IDs": (2, current_objects_id[0], current_objects_id[1]),
                            "Description": f"previous object ID is {previous_objects_id[0]} and "
                            f"current objects IDs are {current_objects_id[0], current_objects_id[1]}. "
                            f"They should be unique",
                        }
                        list_of_errors.append(error_dict)
                        description = " ".join(
                            f"The evaluation is <b>FAILED</b> at timestamp {error_dict['Timestamp']} "
                            f"because {error_dict['Description']}.".split()
                        )
                        self.test_result = fc.FAIL

                    else:
                        description = " ".join(
                            f"The evaluation is <b>PASSED</b> because the new objects IDs "
                            f"{current_objects_id[0], current_objects_id[1]} are both different than "
                            f"previous object ID {previous_objects_id[0]}.".split()
                        )
                        self.test_result = fc.PASS

                    break

        else:
            description = " ".join("Signal <b>not evaluated</b> because it is not available.".split())

        # Report result status
        if self.test_result == fc.INPUT_MISSING:
            self.result.measured_result = DATA_NOK
        elif self.test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif self.test_result == fc.FAIL:
            self.result.measured_result = FALSE

        signal_summary[signal_evaluated] = description
        remark = " ".join(
            "For each Presumed Static Obstacle created by splitting a Presumed Static Obstacle from previous SGF "
            "execution, a new obstacle ID should be provided.".split()
        )

        # The signal summary and observations will be converted to pandas
        # and finally the html table will be created with them
        self.sig_sum = convert_dict_to_pandas(signal_summary=signal_summary, table_remark=remark)

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.result.measured_result in [FALSE, DATA_NOK]:
            list_of_errors_df = pd.DataFrame(list_of_errors)
            previous_id = [str(list_of_errors_df["Previous Objects ID"][0][1])]
            current_ids = [
                str(list_of_errors_df["Current Objects IDs"][0][1])
                + ", "
                + str(list_of_errors_df["Current Objects IDs"][0][2])
            ]
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=list_of_errors_df["Timestamp"],
                    y=list_of_errors_df["Previous Objects ID"][0],
                    name="",
                    mode="markers",
                    marker={"color": "blue"},
                    customdata=previous_id,
                    hovertemplate="The ID of the object before split: %{customdata}",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=list_of_errors_df["Timestamp"],
                    y=list_of_errors_df["Current Objects IDs"][0],
                    name="",
                    mode="markers",
                    marker={"color": "red"},
                    customdata=current_ids,
                    hovertemplate="The IDs of the objects after split: %{customdata}",
                )
            )
            fig["layout"]["xaxis"].update(title_text="SGF Timestamp")
            fig["layout"]["yaxis"].update(title_text="Static Object ID")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=False)
            fig.update_yaxes(range=[0, 2.5], dtick=0.5)

            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        result_df = {
            "Verdict": {"value": self.test_result.title(), "color": get_color(self.test_result)},
            fc.REQ_ID: ["1522144"],
            fc.TESTCASE_ID: ["39122"],
            fc.TEST_DESCRIPTION: [
                "For each Presumed Static Obstacle created by splitting a Presumed Static Obstacle from previous SGF "
                "execution, a new obstacle ID is provided."
            ],
        }

        self.result.details["Additional_results"] = result_df

        # Add the plots in html page
        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")


@verifies("1522144")
@testcase_definition(
    name="SWRT_CNC_SGF_StaticObjectsSplitID",
    description="This test case verifies that SGF gives a new 'u_id' for all static objects created by splitting "
    "an object in the previous timeframe.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_8OJg7UxLEe6M5-WQsF_-tQ&componentURI=https%3A%2F%2Fjazz.conti.de%2F"
    "rm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration="
    "https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17100",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class StaticObjectsSplitID(TestCase):
    """Define the test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepStaticObjectsSplitID,
        ]
