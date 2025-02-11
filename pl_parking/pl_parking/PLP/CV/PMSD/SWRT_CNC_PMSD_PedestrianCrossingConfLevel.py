#!/usr/bin/env python3
"""Defining  pmsd Pedestrian Crossing ConfidenceLevel testcases"""
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

SIGNAL_DATA = "PMSD_PedestrianCrossings_Confidence"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD Confidence level of detected Pedestrian Crossings",
    description="This teststep checks Confidence level of detected Pedestrian Crossings",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdPedCrosConfidenceValueTestStep(TestStep):
    """PMSD PedestrianCrossings Confidence Test."""

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

        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        df = reader.as_plain_df
        df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]

        # TODO PMSD Pedestrian crossing signal are yet to be added in common_ft_helper.
        FC_Conf = df.loc[:, df.columns.str.contains("PMDPEDCROS_Front_lineConfidence")]
        RC_Conf = df.loc[:, df.columns.str.contains("PMDPEDCROS_Rear_lineConfidence")]
        LSC_Conf = df.loc[:, df.columns.str.contains("PMDPEDCROS_Left_lineConfidence")]
        RSC_Conf = df.loc[:, df.columns.str.contains("PMDPEDCROS_Right_lineConfidence")]

        evaluation = ["", "", "", ""]
        if not FC_Conf.empty:
            evaluation[0] = "confidence level for each detected PedestrianCrossings is present"
            FC_result = True
        else:
            evaluation[0] = "FC PedestrianCrossings confidence level is not present or not defined"
            FC_result = False

        if not RC_Conf.empty:
            evaluation[1] = "confidence level for each detected PedestrianCrossings is present"
            RC_result = True
        else:
            evaluation[1] = "RC PedestrianCrossings confidence level is not present or not defined"
            RC_result = False

        if not LSC_Conf.empty:
            evaluation[2] = "confidence level for each detected PedestrianCrossings is present"
            LSC_result = True
        else:
            evaluation[2] = "LSC PedestrianCrossings confidence level is not present or not defined"
            LSC_result = False

        if not RSC_Conf.empty:
            evaluation[3] = "confidence level for each detected PedestrianCrossings is present"
            RSC_result = True
        else:
            evaluation[3] = "RSC PedestrianCrossings confidence level is not present or not defined"
            RSC_result = False

        eval_cond = [
            FC_result,
            RC_result,
            LSC_result,
            RSC_result,
        ]

        test_result = fc.PASS if all(eval_cond) else fc.FAIL
        # Set table dataframe
        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": "Confidence level for each detected pedestrian crossing from front cam should be " "present",
                    "2": "Confidence level for each detected pedestrian crossing from rear camera should " "be present",
                    "3": "Confidence level for each detected pedestrian crossing from left camera should be " "present",
                    "4": "Confidence level for each detected pedestrian crossing from right camera should "
                    "be present",
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

        sig_sum = fh.build_html_table(signal_summary, table_title="PFS Init Reset Output Values State")
        self.result.details["Plots"].append(sig_sum)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2261989"],
            fc.TESTCASE_ID: ["64467"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Verify that the <PMSD> shall provide a confidence level for each detected pedestrian crossing."
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


@verifies("2261989")
@testcase_definition(
    name="SWRT_CNC_PMSD_PedestrianCrossingConfLevel",
    description="Verify PedestrianCrossings Confidence Value",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class PmsdPedCrosConfidenceLevel(TestCase):
    """ConfidenceLevel test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdPedCrosConfidenceValueTestStep,
        ]
