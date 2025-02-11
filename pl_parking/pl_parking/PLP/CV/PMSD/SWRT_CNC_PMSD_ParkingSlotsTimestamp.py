#!/usr/bin/env python3
"""Defining pmsd ParkingSlots Timestamp Field testcases"""
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

SIGNAL_DATA = "PMSD_ParkingSlotsTimestamp"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD ParkingSlots timestamp",
    description="This teststep checks list of detected Parking Slots provided by <PMSD> shall contain a time stamp field"
    "image",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdParkingSlotsTimestampTestStep(TestStep):
    """PMSD List of ParkingSlots Timestamp Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based
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

        try:
            print(df["PmsdSlot_Front_timestamp"])
            print("FC output signals are present")
            evaluation[0] = "FC ParkingSlots Timestamp field is present."
            FC_result = True
        except KeyError as err:
            evaluation[0] = "KeyError: " + str(err) + "Signal not found."
            FC_result = False

        try:
            print(df["PmsdSlot_Rear_timestamp"])
            print("RC output signals are present")
            evaluation[1] = "RC ParkingSlots Timestamp field is present."
            RC_result = True
        except KeyError as err:
            evaluation[1] = "KeyError: " + str(err) + "Signal not found."
            RC_result = False

        try:
            print(df["PmsdSlot_Left_timestamp"])
            print("LSC output signals are present")
            evaluation[2] = "LSC ParkingSlots Timestamp field is present."
            LSC_result = True
        except KeyError as err:
            evaluation[2] = "KeyError: " + str(err) + "Signal not found."
            LSC_result = False

        try:
            print(df["PmsdSlot_Right_timestamp"])
            print("RSC output signals are present")
            evaluation[3] = "RSC ParkingSlots Timestamp field is present."
            RSC_result = True
        except KeyError as err:
            evaluation[3] = "KeyError: " + str(err) + "Signal not found."
            RSC_result = False

        eval_cond = [
            FC_result,
            RC_result,
            LSC_result,
            RSC_result,
        ]

        test_result = fc.PASS if all(eval_cond) else fc.FAIL

        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": "Timestamp field for each detected Parking Slotsfrom front cam should be present",
                    "2": "Timestamp field for each detected Parking Slotsfrom rear camera should be present",
                    "3": "Timestamp field for each detected Parking Slotsfrom left camera should be present",
                    "4": "Timestamp field for each detected Parking Slotsfrom right camera should be present",
                },
                "Result": {
                    "1": evaluation[0],
                    "2": evaluation[1],
                    "3": evaluation[2],
                    "4": evaluation[3],
                },
                "Verdict": {
                    "1": "PASSED" if eval_cond[0] else "FAILED",
                    "2": "PASSED" if eval_cond[1] else "FAILED",
                    "3": "PASSED" if eval_cond[2] else "FAILED",
                    "4": "PASSED" if eval_cond[3] else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="Parking Slots Timestamp Field")
        self.result.details["Plots"].append(sig_sum)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1988304"],
            fc.TESTCASE_ID: ["83364"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test will verify that the list of detected Parking Slots provided by <PMSD> shall contain a "
                "time stamp field representing the point in time when the image was taken."
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


@verifies("1988304")
@testcase_definition(
    name="SWRT_CNC_PMSD_ParkingSlotsTimestamp",
    description="Verify ParkingSlots Timestamp",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class PmsdParkingSlotsTimestamp(TestCase):
    """ParkingSlotsTimestamp test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdParkingSlotsTimestampTestStep,
        ]
