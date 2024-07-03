#!/usr/bin/env python3
"""Defining  pmsd List of stop lines testcases"""
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
from pl_parking.PLP.CV.PMSD.constants import ConstantsPmsd
from pl_parking.PLP.MF.constants import PlotlyTemplate

SIGNAL_DATA = "PMSD_List_of_stop_lines"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD detected stop lines",
    description="This teststep checks detected stop lines in ROI in input image",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdListstoplinesTestStep(TestStep):
    """PMSD Stoplines Test."""

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
        pmd_data = []

        evaluation = ["", "", "", ""]
        # TODO Stop line signals are yet to be update in common_ft_helper.
        try:
            pmd_data = df[
                [
                    "PMDSl_Front_numberOfLines",
                    "PMDSl_Rear_numberOfLines",
                    "PMDSl_Left_numberOfLines",
                    "PMDSl_Right_numberOfLines",
                ]
            ]

            print("All output signals are present")

            if (pmd_data["PMDSl_Front_numberOfLines"] >= ConstantsPmsd.NUM_STOPLINE_MIN).any() and (
                pmd_data["PMDSl_Front_numberOfLines"] <= ConstantsPmsd.NUM_STOPLINE_MAX
            ).any():
                FC_result = True
                evaluation[0] = "Front Camera stop lines are present"
            else:
                FC_result = False
                evaluation[0] = "Front Camera stop lines are not within the range"

            if (pmd_data["PMDSl_Rear_numberOfLines"] >= ConstantsPmsd.NUM_WHEELSTOPPER_MIN).any() and (
                pmd_data["PMDSl_Rear_numberOfLines"] <= ConstantsPmsd.NUM_STOPLINE_MAX
            ).any():
                RC_result = True
                evaluation[1] = "Rear Camera stop lines are present"
            else:
                RC_result = False
                evaluation[1] = "Rear Camera stop lines are not within the range"

            if (pmd_data["PMDSl_Left_numberOfLines"] >= ConstantsPmsd.NUM_WHEELSTOPPER_MIN).any() and (
                pmd_data["PMDSl_Left_numberOfLines"] <= ConstantsPmsd.NUM_STOPLINE_MAX
            ).any():
                LSC_result = True
                evaluation[2] = "Left Side Camera stop lines are present"
            else:
                LSC_result = False
                evaluation[2] = "Left Side Camera stop lines are not within the range"

            if (pmd_data["PMDSl_Right_numberOfLines"] >= ConstantsPmsd.NUM_WHEELSTOPPER_MIN).any() and (
                pmd_data["PMDSl_Right_numberOfLines"] <= ConstantsPmsd.NUM_STOPLINE_MAX
            ).any():
                RSC_result = True
                evaluation[3] = "Right Side Camera stop lines are present"
            else:
                RSC_result = False
                evaluation[3] = "Right Side Camera stop lines are not within the range"
        except KeyError as err:
            print("KeyError: ", err, " Signal not found.")
            FC_result = RC_result = LSC_result = RSC_result = False
            evaluation[0] = evaluation[1] = evaluation[2] = evaluation[3] = str(err)

        cond_bool = [
            FC_result,
            RC_result,
            LSC_result,
            RSC_result,
        ]

        test_result = fc.PASS if all(cond_bool) else fc.FAIL

        signal_summary["FC_Detected_stop_lines"] = evaluation[0]
        signal_summary["RC_Detected_stop_lines"] = evaluation[1]
        signal_summary["LSC_Detected_stop_lines"] = evaluation[2]
        signal_summary["RSC_Detected_stop_lines"] = evaluation[3]

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

        if len(pmd_data) != 0:
            for camera, _ in pmd_data.items():
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(pmd_data[camera]))),
                        y=pmd_data[camera].values.tolist(),
                        mode="lines",
                        name=f"{camera} Num stop lines",
                        line=dict(color="darkblue"),
                    )
                )
                fig.layout = go.Layout(
                    yaxis=dict(tickformat="14"),
                    xaxis=dict(tickformat="14"),
                    xaxis_title="Frames",
                    yaxis_title=f"{camera}",
                )
                fig.update_layout(PlotlyTemplate.lgt_tmplt)
                fig.add_annotation(
                    dict(
                        font=dict(color="black", size=12),
                        x=0,
                        y=-0.12,
                        showarrow=False,
                        text=f"{camera}",
                        textangle=0,
                        xanchor="left",
                        xref="paper",
                        yref="paper",
                    )
                )
                plot_titles.append("")
                plots.append(fig)
                remarks.append("")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2261975"],
            fc.TESTCASE_ID: ["63213"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: ["Verify that PMSD provides detected stop lines in <ROI> for the input <Image>."],
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


@verifies("2261975")
@testcase_definition(
    name="SWRT_CNC_PMSD_ListofStopLines",
    description="Verify Detected stop lines",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class PmsdListofstoplines(TestCase):
    """Listofstop lines test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdListstoplinesTestStep,
        ]