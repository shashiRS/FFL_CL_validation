#!/usr/bin/env python3
"""Defining  pmsd Stop lines Timestamp Field testcases"""
import logging
import os

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

SIGNAL_DATA = "PMSD_Stoplines_Timestamp"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD Stoplines timestamp",
    description="This teststep checks list of detected wheel lockers provided by <PMSD> shall contain a time stamp "
    "field representing the point in time when the image was taken",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdStoplinesTimestampTestStep(TestStep):
    """PMSD Stoplines Timestamp Test."""

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

        reader = self.readers[SIGNAL_DATA].signals
        df = reader.as_plain_df

        evaluation = ["", "", "", ""]

        # TODO Wheel Locker signal are yet to be update in common_ft_helper.
        try:
            print(df["PMDSl_Front_timestamp"])
            print("FC output signals are present")
            evaluation[0] = "FC Stoplines Timestamp field is present."
            FC_result = True
        except KeyError as err:
            evaluation[0] = "KeyError: " + str(err) + "Signal not found."
            FC_result = False

        try:
            print(df["PMDSl_Rear_timestamp"])
            print("RC output signals are present")
            evaluation[1] = "RC Stoplines Timestamp field is present."
            RC_result = True
        except KeyError as err:
            evaluation[1] = "KeyError: " + str(err) + "Signal not found."
            RC_result = False

        try:
            print(df["PMDSl_Left_timestamp"])
            print("LSC output signals are present")
            evaluation[2] = "LSC Stoplines Timestamp field is present."
            LSC_result = True
        except KeyError as err:
            evaluation[2] = "KeyError: " + str(err) + "Signal not found."
            LSC_result = False

        try:
            print(df["PMDSl_Right_timestamp"])
            print("RSC output signals are present")
            evaluation[3] = "RSC Stoplines Timestamp field is present."
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
                "Evaluation": {
                    "1": "Front Camera Stoplines Timestamp field is present",
                    "2": "Rear Camera Stoplines Timestamp field is present",
                    "3": "Left Camera Stoplines Timestamp field is present",
                    "4": "Right Camera Stoplines Timestamp field is present",
                },
                "Result": {
                    "1": evaluation[0],
                    "2": evaluation[1],
                    "3": evaluation[2],
                    "4": evaluation[3],
                },
                "Verdict": {
                    "1": "PASSED" if cond_bool[0] else "FAILED",
                    "2": "PASSED" if cond_bool[1] else "FAILED",
                    "3": "PASSED" if cond_bool[2] else "FAILED",
                    "4": "PASSED" if cond_bool[3] else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PMSD StopLine Timestamp")
        self.result.details["Plots"].append(sig_sum)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2261977"],
            fc.TESTCASE_ID: ["63215"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test will verify that list of stop lines provided by <PMSD> shall contain a time stamp field "
                "representing the point in time when the image was taken."
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


@verifies("2261977")
@testcase_definition(
    name="SWRT_CNC_PMSD_StopLineTimestamp",
    description="Verify Stoplines Timestamp",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class PmsdStoplinesTimestamp(TestCase):
    """StoplinesTimestamp test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdStoplinesTimestampTestStep,
        ]
