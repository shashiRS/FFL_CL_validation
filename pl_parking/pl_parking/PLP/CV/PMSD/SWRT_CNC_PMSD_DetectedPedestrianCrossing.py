#!/usr/bin/env python3
"""Defining  pmsd Detected Pedestrian Crossing testcases"""
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
from pl_parking.PLP.CV.PMSD.constants import ConstantsPmsd, PlotlyTemplate

SIGNAL_DATA = "PMSD_List_of_Detected_Ped_Crossing"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD Detected Pedestrian Crossing",
    description="This teststep checks Detected Pedestrian Crossing in the input image",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdDetectedPedestrianCrossingTestStep(TestStep):
    """PMSD Detected Pedestrian Crossing Test."""

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
        pmd_ped_data = []
        evaluation = ["", "", "", ""]

        try:
            pmd_ped_data = df[
                [
                    "PMDPEDCROS_Front_numberOfCrossings",
                    "PMDPEDCROS_Rear_numberOfCrossings",
                    "PMDPEDCROS_Left_numberOfCrossings",
                    "PMDPEDCROS_Right_numberOfCrossings",
                ]
            ]

            print("All output signals are present")
            if (pmd_ped_data["PMDPEDCROS_Front_numberOfCrossings"] >= ConstantsPmsd.NUM_PED_CROSSING_MIN).all() and (
                pmd_ped_data["PMDPEDCROS_Front_numberOfCrossings"] <= ConstantsPmsd.NUM_PED_CROSSING_MAX
            ).all():
                FC_result = True
                evaluation[0] = "Front Camera Pedestrian Crossing Detection are present"
            else:
                FC_result = False
                evaluation[0] = "Front Camera Pedestrian Crossing Detection are not within the range"

            if (pmd_ped_data["PMDPEDCROS_Rear_numberOfCrossings"] >= ConstantsPmsd.NUM_PED_CROSSING_MIN).all() and (
                pmd_ped_data["PMDPEDCROS_Rear_numberOfCrossings"] <= ConstantsPmsd.NUM_PED_CROSSING_MAX
            ).all():
                RC_result = True
                evaluation[1] = "Rear Camera Pedestrian Crossing Detection are present"
            else:
                RC_result = False
                evaluation[1] = "Rear Camera Pedestrian Crossing Detection are not within the range"

            if (pmd_ped_data["PMDPEDCROS_Left_numberOfCrossings"] >= ConstantsPmsd.NUM_PED_CROSSING_MIN).all() and (
                pmd_ped_data["PMDPEDCROS_Left_numberOfCrossings"] <= ConstantsPmsd.NUM_PED_CROSSING_MAX
            ).all():
                LSC_result = True
                evaluation[2] = "Left Side Camera Pedestrian Crossing Detection are present"
            else:
                LSC_result = False
                evaluation[2] = "Left Side Camera Pedestrian Crossing Detection are not within the range"

            if (pmd_ped_data["PMDPEDCROS_Right_numberOfCrossings"] >= ConstantsPmsd.NUM_PED_CROSSING_MIN).all() and (
                pmd_ped_data["PMDPEDCROS_Right_numberOfCrossings"] <= ConstantsPmsd.NUM_PED_CROSSING_MAX
            ).all():
                RSC_result = True
                evaluation[3] = "Right Side Camera Pedestrian Crossing Detection are present"
            else:
                RSC_result = False
                evaluation[3] = "Right Side Camera Pedestrian Crossing Detection are not within the range"
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

        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": "Front Camera Pedestrian Crossing Detection should be present",
                    "2": "Rear Camera Pedestrian Crossing Detection should be present",
                    "3": "Left Camera Pedestrian Crossing Detection should be present",
                    "4": "Right Camera Pedestrian Crossing Detection should be present",
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

        sig_sum = fh.build_html_table(signal_summary, table_title="PMSD Detected Pedestrian Crossings")
        self.result.details["Plots"].append(sig_sum)

        if len(pmd_ped_data) != 0:
            for camera, _ in pmd_ped_data.items():
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(pmd_ped_data[camera]))),
                        y=pmd_ped_data[camera].values.tolist(),
                        mode="lines",
                        name=f"{camera} Num Pedestrian Crossing Detection",
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
                        text=f"{camera} Num Pedestrian Crossing Detection",
                        textangle=0,
                        xanchor="left",
                        xref="paper",
                        yref="paper",
                    )
                )
                plots.append(fig)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2261986"],
            fc.TESTCASE_ID: ["64461"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: ["Verify detected pedestrian crossings in the input image"],
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


@verifies("2261986")
@testcase_definition(
    name=":SWRT_CNC_PMSD_DetectedPedestrianCrossing",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_HnqYvg3ZEe-9Pf5VGwDpVA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
    description="Verify Detected Pedestrian Crossing",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class PmsdDetectedPedestrianCrossing(TestCase):
    """Detected Pedestrian Crossing test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdDetectedPedestrianCrossingTestStep,
        ]
