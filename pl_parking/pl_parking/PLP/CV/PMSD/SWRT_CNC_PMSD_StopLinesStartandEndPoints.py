#!/usr/bin/env python3
"""Defining  pmsd StopLineStartandEndPoints testcases"""
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

SIGNAL_DATA = "PMSD_StopLineStartandEndPoints"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD List of StopLine StartandEndPoints",
    description="This teststep checks StopLine StartandEndPoints",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdStopLineStartandEndPointsTestStep(TestStep):
    """PMSD StopLineStartandEndPoints Test."""

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
        signal_summary = {}

        reader = self.readers[SIGNAL_DATA].signals

        df = reader.as_plain_df
        df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
        evaluation = ["", "", "", ""]

        # Signal names must be added to common_ft_helper, once available
        FC_StopLineStartX = df.loc[:, df.columns.str.contains("PMDSl_Front_StopLines_lineStartX")]
        FC_StopLineStartY = df.loc[:, df.columns.str.contains("PMDSl_Front_StopLines_lineStartY")]
        FC_StopLineEndX = df.loc[:, df.columns.str.contains("PMDSl_Front_StopLines_lineEndX")]
        FC_StopLineEndY = df.loc[:, df.columns.str.contains("PMDSl_Front_StopLines_lineEndY")]

        if FC_StopLineStartX.empty or FC_StopLineStartY.empty or FC_StopLineEndX.empty or FC_StopLineEndY.empty:
            evaluation[0] = "FC Stop Lines XY End Points signals not found."
            FC_result = False
        else:
            evaluation[0] = "FC Stop Lines XY End Points signals are present."
            FC_result = True

        RC_StopLineStartX = df.loc[:, df.columns.str.contains("PMDSl_Rear_StopLines_lineStartX")]
        RC_StopLineStartY = df.loc[:, df.columns.str.contains("PMDSl_Rear_StopLines_lineStartY")]
        RC_StopLineEndX = df.loc[:, df.columns.str.contains("PMDSl_Rear_StopLines_lineEndX")]
        RC_StopLineEndY = df.loc[:, df.columns.str.contains("PMDSl_Rear_StopLines_lineEndY")]

        if RC_StopLineStartX.empty or RC_StopLineStartY.empty or RC_StopLineEndX.empty or RC_StopLineEndY.empty:
            evaluation[1] = "RC Stop Lines XY End Points signals not found."
            RC_result = False
        else:
            evaluation[1] = "RC Stop Lines XY End Points signals are present."
            RC_result = True

        LSC_StopLineStartX = df.loc[:, df.columns.str.contains("PMDSl_Left_StopLines_lineStartX")]
        LSC_StopLineStartY = df.loc[:, df.columns.str.contains("PMDSl_Left_StopLines_lineStartY")]
        LSC_StopLineEndX = df.loc[:, df.columns.str.contains("PMDSl_Left_StopLines_lineEndX")]
        LSC_StopLineEndY = df.loc[:, df.columns.str.contains("PMDSl_Left_StopLines_lineEndY")]

        if LSC_StopLineStartX.empty or LSC_StopLineStartY.empty or LSC_StopLineEndX.empty or LSC_StopLineEndY.empty:
            evaluation[2] = "LSC Stop Lines XY End Points signals not found."
            LSC_result = False
        else:
            evaluation[2] = "LSC Stop Lines XY End Points signals are present."
            LSC_result = True

        RSC_StopLineStartX = df.loc[:, df.columns.str.contains("PMDSl_Right_StopLines_lineStartX")]
        RSC_StopLineStartY = df.loc[:, df.columns.str.contains("PMDSl_Right_StopLines_lineStartY")]
        RSC_StopLineEndX = df.loc[:, df.columns.str.contains("PMDSl_Right_StopLines_lineEndX")]
        RSC_StopLineEndY = df.loc[:, df.columns.str.contains("PMDSl_Right_StopLines_lineEndY")]

        if RSC_StopLineStartX.empty or RSC_StopLineStartY.empty or RSC_StopLineEndX.empty or RSC_StopLineEndY.empty:
            evaluation[3] = "RSC Stop Lines XY End Points signals not found."
            RSC_result = False
        else:
            evaluation[3] = "RSC Stop Lines XY End Points signals are present."
            RSC_result = True

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
                    "1": "PMSD shall provide x,y coordinates for the start and end point of  the detected stop lines for Front Camera",
                    "2": "PMSD shall provide x,y coordinates for the start and end point of  the detected stop lines for Rear Camera",
                    "3": "PMSD shall provide x,y coordinates for the start and end point of  the detected stop lines for Left Camera",
                    "4": "PMSD shall provide x,y coordinates for the start and end point of  the detected stop lines for Right Camera",
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

        sig_sum = fh.build_html_table(signal_summary, table_title="PMSD StopLine Start and End Points")
        self.result.details["Plots"].append(sig_sum)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2261981"],
            fc.TESTCASE_ID: ["64459"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Verify the x,y coordinates for the start and end point of  the detected stop lines in Vehicle "
                "Coordinate system."
                ""
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


@verifies("2261981")
@testcase_definition(
    name="SWRT_CNC_PMSD_StopLineStartandEndPoints",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_HnqYuQ3ZEe-9Pf5VGwDpVA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
    description="Verify Stop Lines StartandEnd Points ",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class PmsdStopLineStartandEndPoints(TestCase):
    """StopLineStartandEndPoints test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdStopLineStartandEndPointsTestStep,
        ]
