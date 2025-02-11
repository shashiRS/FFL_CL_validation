#!/usr/bin/env python3
"""Defining  pmsd Parking Markings Timestamp Field testcases"""
import logging
import os

import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


import pandas as pd
from tsf.core.results import FALSE, TRUE, BooleanResult
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
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CV.PMSD.constants import PlotlyTemplate

SIGNAL_DATA = "PMSD_ParkingMarkingsTimestamp"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD detected parking markings timestamp",
    description="This teststep checks list of detected parking markings shall contain a timestamp field in the input "
    "image",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdParkingMarkingsTimestampTestStep(TestStep):
    """PMSD List of Parking Markings Timestamp Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarsk based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)
        signal_summary = {}

        reader = self.readers[SIGNAL_DATA]
        df = reader.as_plain_df

        evaluation = ["", "", "", ""]

        try:
            print(df["PMDCamera_Front_timestamp"])
            evaluation[0] = "FC Parking Markings Timestamp has values in the measurement."
            FC_result = True
        except KeyError as err:
            evaluation[0] = "KeyError: " + str(err) + "Signal not found."
            FC_result = False

        try:
            print(df["PMDCamera_Rear_timestamp"])
            evaluation[1] = "RC Parking Markings Timestamp has values in the measurement."
            RC_result = True
        except KeyError as err:
            evaluation[1] = "KeyError: " + str(err) + "Signal not found."
            RC_result = False

        try:
            print(df["PMDCamera_Left_timestamp"])
            evaluation[2] = "LSC Parking Markings Timestamp has values in the measurement."
            LSC_result = True
        except KeyError as err:
            evaluation[2] = "KeyError: " + str(err) + "Signal not found."
            LSC_result = False

        try:
            print(df["PMDCamera_Right_timestamp"])
            evaluation[3] = "RSC Parking Markings Timestamp has values in the measurement."
            RSC_result = True
        except KeyError as err:
            evaluation[3] = "KeyError: " + str(err) + "Signal not found."
            RSC_result = False

        cond_bool = [
            FC_result,
            RC_result,
            LSC_result,
            RSC_result,
        ]

        test_result = fc.PASS if all(cond_bool) else fc.FAIL

        signal_summary = pd.DataFrame(
            {
                "Signal Evaluation": {
                    "1": "PMSD_FC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
                    "2": "PMSD_RC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
                    "3": "PMSD_LSC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
                    "4": "PMSD_RSC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
                },
                "Result": {
                    "1": evaluation[0],
                    "2": evaluation[1],
                    "3": evaluation[2],
                    "4": evaluation[3],
                },
                "Verdict": {
                    "1": "PASSED" if FC_result else "FAILED",
                    "2": "PASSED" if RC_result else "FAILED",
                    "3": "PASSED" if LSC_result else "FAILED",
                    "4": "PASSED" if RSC_result else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PMSD Parking Markings Timestamp")
        self.result.details["Plots"].append(sig_sum)

        #  Plots for all four cameras
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=list(range(len(df["PMDCamera_Front_timestamp"]))),
                y=df["PMDCamera_Front_timestamp"].to_list(),
                mode="lines",
                name="PMSD_FC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=list(range(len(df["PMDCamera_Rear_timestamp"]))),
                y=df["PMDCamera_Rear_timestamp"].to_list(),
                mode="lines",
                name="PMSD_RC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=list(range(len(df["PMDCamera_Left_timestamp"]))),
                y=df["PMDCamera_Left_timestamp"].to_list(),
                mode="lines",
                name="PMSD_LSC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=list(range(len(df["PMDCamera_Right_timestamp"]))),
                y=df["PMDCamera_Right_timestamp"].to_list(),
                mode="lines",
                name="PMSD_RSC_DATA.ParkingLines.sSigHeader.uiTimeStamp",
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Frames", yaxis_title="Timestamp[s]"
        )
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        plot_titles.append("Timstamp representation")
        plots.append(fig)
        remarks.append("")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1987855"],
            fc.TESTCASE_ID: ["58796"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Verify list of detected parking markings provided by <PMSD> shall contain a time "
                "stamp field representing the point in time when the image was taken."
            ],
            fc.TEST_RESULT: [test_result],
        }

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE
        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = result_df


@verifies("1987855")
@testcase_definition(
    name="SWRT_CNC_PMSD_ParkingMarkingsTimestamp",
    description="Verify Parking Markings Timestamp",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_NkGtENsEEe62R7UY0u3jZg&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class PmsdParkingMarkingsTimestamp(TestCase):
    """ParkingMarkingsTimestamp test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdParkingMarkingsTimestampTestStep,
        ]
