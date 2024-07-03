#!/usr/bin/env python3
"""Defining  pmsd StopLines ConfidenceLevel testcases"""
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

SIGNAL_DATA = "PMSD_StopLines_Confidence"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD Confidence level of detected StopLiness",
    description="This teststep checks Confidence level of detected StopLiness",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdSlConfidenceValueTestStep(TestStep):
    """PMSD StopLines Confidence Test."""

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
        df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]

        # TODO Wheel Locker signal are yet to be update in common_ft_helper.
        FC_Conf = df.loc[:, df.columns.str.contains("PMDSl_Front_lineConfidence")]
        RC_Conf = df.loc[:, df.columns.str.contains("PMDSl_Rear_lineConfidence")]
        LSC_Conf = df.loc[:, df.columns.str.contains("PMDSl_Left_lineConfidence")]
        RSC_Conf = df.loc[:, df.columns.str.contains("PMDSl_Right_lineConfidence")]

        evaluation = ["", "", "", ""]
        if not FC_Conf.empty:
            evaluation[0] = "confidence level for each detected StopLines is present"
            FC_result = True
        else:
            evaluation[0] = "FC StopLines confidence level is not present"
            FC_result = False

        if not RC_Conf.empty:
            evaluation[1] = "confidence level for each detected StopLines is present"
            RC_result = True
        else:
            evaluation[1] = "RC StopLines confidence level is not present"
            RC_result = False

        if not LSC_Conf.empty:
            evaluation[2] = "confidence level for each detected StopLines is present"
            LSC_result = True
        else:
            evaluation[2] = "LSC StopLines confidence level is not present"
            LSC_result = False

        if not RSC_Conf.empty:
            evaluation[3] = "confidence level for each detected StopLines is present"
            RSC_result = True
        else:
            evaluation[3] = "RSC StopLines confidence level is not present"
            RSC_result = False

        cond_bool = [
            FC_result,
            RC_result,
            LSC_result,
            RSC_result,
        ]

        test_result = fc.PASS if all(cond_bool) else fc.FAIL
        signal_summary["FC_StopLines_Conf"] = evaluation[0]
        signal_summary["RC_StopLines_Conf"] = evaluation[1]
        signal_summary["LSC_StopLines_Conf"] = evaluation[2]
        signal_summary["RSC_StopLines_Conf"] = evaluation[3]

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
            fc.REQ_ID: ["2261980"],
            fc.TESTCASE_ID: ["63217"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Verify that the <PMSD> shall provide a confidence level for each detected stop " "line."
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


@verifies("2261980")
@testcase_definition(
    name="SWRT_CNC_PMSD_StopLineConfLevel",
    description="Verify StopLines Confidence Value",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class PmsdSlConfidenceLevel(TestCase):
    """ConfidenceLevel test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdSlConfidenceValueTestStep,
        ]
