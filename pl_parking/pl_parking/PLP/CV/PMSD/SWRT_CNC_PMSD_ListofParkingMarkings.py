#!/usr/bin/env python3
"""Defining  pmsd ListofParkingMarkings testcases"""
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
from pl_parking.PLP.CV.PMSD.constants import ConstantsPmsd

SIGNAL_DATA = "PMSD_List_of_ParkingMarkings"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD detected parking markings",
    description="This teststep checks detected parking markings in the input image",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdListParkingMarkingsTestStep(TestStep):
    """PMSD Line Confidence Test."""

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
        pmd_data = []
        evaluation = ["", "", "", ""]

        try:
            pmd_data = df[
                [
                    "PMDCamera_Front_numberOfLines",
                    "PMDCamera_Rear_numberOfLines",
                    "PMDCamera_Left_numberOfLines",
                    "PMDCamera_Right_numberOfLines",
                ]
            ]

            print("All output signals are present")
            if (pmd_data["PMDCamera_Front_numberOfLines"] >= ConstantsPmsd.NUM_PARKING_LINES_MIN).any() and (
                pmd_data["PMDCamera_Front_numberOfLines"] <= ConstantsPmsd.NUM_PARKING_LINES_MAX
            ).any():
                FC_result = True
                evaluation[0] = "Front Camera Parking Markings are present"
            else:
                FC_result = False
                evaluation[0] = "Front Camera Parking Markings are not within the range"

            if (pmd_data["PMDCamera_Rear_numberOfLines"] >= ConstantsPmsd.NUM_PARKING_LINES_MIN).any() and (
                pmd_data["PMDCamera_Rear_numberOfLines"] <= ConstantsPmsd.NUM_PARKING_LINES_MAX
            ).any():
                RC_result = True
                evaluation[1] = "Rear Camera Parking Markings are present"
            else:
                RC_result = False
                evaluation[1] = "Rear Camera Parking Markings are not within the range"

            if (pmd_data["PMDCamera_Left_numberOfLines"] >= ConstantsPmsd.NUM_PARKING_LINES_MIN).any() and (
                pmd_data["PMDCamera_Left_numberOfLines"] <= ConstantsPmsd.NUM_PARKING_LINES_MAX
            ).any():
                LSC_result = True
                evaluation[2] = "Left Side Camera Parking Markings are present"
            else:
                LSC_result = False
                evaluation[2] = "Left Side Camera Parking Markings are not within the range"

            if (pmd_data["PMDCamera_Right_numberOfLines"] >= ConstantsPmsd.NUM_PARKING_LINES_MIN).any() and (
                pmd_data["PMDCamera_Right_numberOfLines"] <= ConstantsPmsd.NUM_PARKING_LINES_MAX
            ).any():
                RSC_result = True
                evaluation[3] = "Right Side Camera Parking Markings are present"
            else:
                RSC_result = False
                evaluation[3] = "Right Side Camera Parking Markings are not within the range"
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
                    "1": "Front Camera Parking Markings Detections should be present",
                    "2": "Rear Camera Parking Markings Detections should be present",
                    "3": "Left Camera Parking Markings Detections should be present",
                    "4": "Right Camera Parking Markings Detections should be present",
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

        sig_sum = fh.build_html_table(signal_summary, table_title="PMSD List of ParkingMarkings")
        self.result.details["Plots"].append(sig_sum)

        if len(pmd_data) != 0:
            for camera, _ in pmd_data.items():
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(pmd_data[camera]))),
                        y=pmd_data[camera].values.tolist(),
                        mode="lines",
                        name=f"{camera} Num Parking Lines",
                        line=dict(color="darkblue"),
                    )
                )
                fig.layout = go.Layout(
                    yaxis=dict(tickformat="14"),
                    xaxis=dict(tickformat="14"),
                    xaxis_title="Frames",
                    yaxis_title=f"{camera}",
                )

                plot_titles.append(f"{camera} Num Parking Lines")
                plots.append(fig)
                remarks.append("")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1987812"],
            fc.TESTCASE_ID: ["59793"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: ["Verify detected parking markings in the input image"],
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


@verifies("1987812")
@testcase_definition(
    name="SWRT_CNC_PMSD_ListofParkingMarkings",
    description="Verify Detected Parking Markings",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class PmsdListofParkingMarkings(TestCase):
    """ListofParkingMarkings test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdListParkingMarkingsTestStep,
        ]
