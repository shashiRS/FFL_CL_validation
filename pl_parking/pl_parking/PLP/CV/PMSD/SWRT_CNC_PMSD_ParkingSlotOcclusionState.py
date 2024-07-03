#!/usr/bin/env python3
"""Defining pmsd parking slot's existence probability testcases"""
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

SIGNAL_DATA = "PMSD_SlotOcclusionState"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD occlusion state of the potential parking slot's vertices.",
    description="This teststep checks occlusion state of the potential parking slot's vertices.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdSlotOcclusionStateTestStep(TestStep):
    """PMSD parking SlotOcclusionState Test."""

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

        FC_OcclusionState = df.loc[:, df.columns.str.contains("PsdSlot_Front_parkingLines_existenceProbability")]
        RC_OcclusionState = df.loc[:, df.columns.str.contains("PsdSlot_Rear_parkingLines_existenceProbability")]
        LSC_OcclusionState = df.loc[:, df.columns.str.contains("PsdSlot_Left_parkingLines_existenceProbability")]
        RSC_OcclusionState = df.loc[:, df.columns.str.contains("PsdSlot_Right_parkingLines_existenceProbability")]

        evaluation = ["", "", "", ""]
        if not FC_OcclusionState.empty:
            evaluation[0] = "FC parking slot's occlusion state is present"
            FC_result = True
        else:
            evaluation[0] = "FC parking slot's occlusion state is not present"
            FC_result = False

        if not RC_OcclusionState.empty:
            evaluation[1] = "RC parking slot's occlusion state is present"
            RC_result = True
        else:
            evaluation[1] = "RC parking slot's occlusion state is not present"
            RC_result = False

        if not LSC_OcclusionState.empty:
            evaluation[2] = "LSC parking slot's occlusion state is present"
            LSC_result = True
        else:
            evaluation[2] = "LSC parking slot's occlusion state is not present"
            LSC_result = False

        if not RSC_OcclusionState.empty:
            evaluation[3] = "RSC parking slot's occlusion state is present"
            RSC_result = True
        else:
            evaluation[3] = "RSC parking slot's occlusion state is not present"
            RSC_result = False

        cond_bool = [
            FC_result,
            RC_result,
            LSC_result,
            RSC_result,
        ]

        test_result = fc.PASS if all(cond_bool) else fc.FAIL
        signal_summary["FC_OcclusionState"] = evaluation[0]
        signal_summary["RC_OcclusionState"] = evaluation[1]
        signal_summary["LSC_OcclusionState"] = evaluation[2]
        signal_summary["RSC_OcclusionState"] = evaluation[3]

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
            fc.REQ_ID: ["1988320"],
            fc.TESTCASE_ID: ["61400"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Verify that PMSD provides the occlusion state of the potential parking slot's vertices."
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


@verifies("1988320")
@testcase_definition(
    name="SWRT_CNC_PMSD_ParkingSlotOcclusionState",
    description="Verify Parking Slots Occlusion State",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class PmsdSlotOcclusionState(TestCase):
    """Slots OcclusionState test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdSlotOcclusionStateTestStep,
        ]
