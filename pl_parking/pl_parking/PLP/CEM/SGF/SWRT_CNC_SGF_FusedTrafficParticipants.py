#!/usr/bin/env python3
"""SWRT_CNC_SGF_FusedTrafficParticipants testcases"""

import logging
import os
import sys

import numpy as np
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
from pl_parking.PLP.CEM.SGF.ft_helper import SGFSignals

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "FusedTrafficParticipants"
sgf_obj = SGFSignals()


@teststep_definition(
    step_number=1,
    name="Fused Traffic Participants",
    description="This test case checks if SGF uses Fused Traffic Participants of TPF for the Fusion.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SGFSignals)
class TestStepFusedTrafficParticipants(TestStep):
    """TestStep for analyzing objects detected from TPF, utilizing a custom report."""

    custom_report = fh.MfCustomTeststepReport

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
        plot_titles, plots, remarks = fh.rep([], 3)

        # Initializing the dictionary with data for final evaluation table
        signal_summary = {}

        # Load signals
        signals_df = self.readers[SIGNAL_DATA]

        # filter only valid outputs
        signals_df = signals_df[signals_df["SGF_sig_status"] == 1]
        signals_df = signals_df[signals_df["numPolygons"] > 0]

        signal_evaluated = sgf_obj.get_properties()[sgf_obj.Columns.SGF_OBJECT_ASSOCIATED_OBJECT_ID][0]
        sgf_time = signals_df[sgf_obj.Columns.SGF_TIMESTAMP]
        associated_object = signals_df.filter(regex="associatedObjectId").values

        # num of static objects per frame
        num_objects = signals_df["numPolygons"].values
        num_frames = signals_df.shape[0]

        if associated_object.shape[1] > 0:
            associated_dynamic_obj_timestamps = []
            for i in range(num_frames):
                obj_in_frame = num_objects[i]
                frame_associated_objects = associated_object[i, 0:obj_in_frame]
                is_associated = frame_associated_objects >= 1 and frame_associated_objects < 255
                # check if for at least one static object 'associatedDynamicObjectId' is not empty
                if np.any(is_associated):
                    associated_dynamic_obj_timestamps.append(signals_df["SGF_timestamp"].values[i])
            if len(associated_dynamic_obj_timestamps) > 0:
                description = (
                    "The evaluation is <b>PASSED</b> because there is at least one static objects where "
                    "associatedDynamicObjectId is not empty."
                )
                self.test_result = fc.PASS
            else:
                description = (
                    "The evaluation is <b>FAILED</b> because associatedDynamicObjectId is empty for all "
                    "static objects."
                )
                self.test_result = fc.FAIL
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
            "Check if there is at least one static objects where associatedDynamicObjectId is not empty.".split()
        )
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary=signal_summary, table_remark=remark)

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        result_df = {
            "Verdict": {"value": self.test_result.title(), "color": fh.get_color(self.test_result)},
            fc.REQ_ID: ["2032217"],
            fc.TESTCASE_ID: ["91204"],
            fc.TEST_DESCRIPTION: [
                "Check if there is at least one static objects where associatedDynamicObjectId is not empty."
            ],
        }

        self.result.details["Additional_results"] = result_df

        if self.result.measured_result in [FALSE, DATA_NOK]:
            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(
                go.Scatter(
                    x=sgf_time,
                    y=signals_df[sgf_obj.Columns.SGF_OBJECT_ASSOCIATED_OBJECT_ID, 0],
                    mode="lines",
                    name=sgf_obj.Columns.SGF_OBJECT_ASSOCIATED_OBJECT_ID,
                )
            )
            fig["layout"]["xaxis"].update(title_text="SGF Timestamp")
            fig["layout"]["yaxis"].update(title_text="Associated Dynamic Object ID")

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


@verifies("2032217")
@testcase_definition(
    name="SWRT_CNC_SGF_FusedTrafficParticipants testcases",
    description="This test case checks if SGF uses Fused Traffic Participants of TPF for the Fusion.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_sp2h0OUwEe6f_fKhM-zv_g&componentURI=https%3A%2F%2Fjazz.conti.de%2F"
    "rm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration="
    "https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17100",
)
@register_inputs("/parking")
class FusedTrafficParticipants(TestCase):
    """Fused traffic participants test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepFusedTrafficParticipants,
        ]
