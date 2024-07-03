#!/usr/bin/env python3
"""Defining  pmsd Parking Markings Timestamp Field testcases"""
import logging
import os

import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


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

        reader = self.readers[SIGNAL_DATA].signals
        df = reader.as_plain_df

        evaluation = ["", "", "", ""]

        try:
            print(df["PMDCamera_Front_timestamp"])
            print("FC output signals are present")
            evaluation[0] = "FC Parking Markings Timestamp field is present."
            FC_result = True
        except KeyError as err:
            evaluation[0] = "KeyError: " + str(err) + "Signal not found."
            FC_result = False

        try:
            print(df["PMDCamera_Rear_timestamp"])
            print("RC output signals are present")
            evaluation[1] = "RC Parking Markings Timestamp field is present."
            RC_result = True
        except KeyError as err:
            evaluation[1] = "KeyError: " + str(err) + "Signal not found."
            RC_result = False

        try:
            print(df["PMDCamera_Left_timestamp"])
            print("LSC output signals are present")
            evaluation[2] = "LSC Parking Markings Timestamp field is present."
            LSC_result = True
        except KeyError as err:
            evaluation[2] = "KeyError: " + str(err) + "Signal not found."
            LSC_result = False

        try:
            print(df["PMDCamera_Right_timestamp"])
            print("RSC output signals are present")
            evaluation[3] = "RSC Parking Markings Timestamp field is present."
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

        signal_summary["FCParkingMarkingsTimestamp"] = evaluation[0]
        signal_summary["RCParkingMarkingsTimestamp"] = evaluation[1]
        signal_summary["LSCParkingMarkingsTimestamp"] = evaluation[2]
        signal_summary["RSCParkingMarkingsTimestamp"] = evaluation[3]

        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Signal Evaluation", "Summary"]),
                    cells=dict(values=[list(signal_summary.keys()), list(signal_summary.values())]),
                )
            ]
        )

        plot_titles.append("Signal Evaluation")
        plots.append(fig)
        remarks.append("PMSD Evaluation")

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
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class PmsdParkingMarkingsTimestamp(TestCase):
    """ParkingMarkingsTimestamp test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdParkingMarkingsTimestampTestStep,
        ]
