#!/usr/bin/env python3
"""Defining  pmsd ParkingMarkingsStartandEndPoints testcases"""
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

SIGNAL_DATA = "PMSD_ParkingMarkingsStartandEndPoints"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD List of ParkingMarkings StartandEndPoints",
    description="This teststep checks ParkingMarkings StartandEndPoints",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdParkingMarkingsStartandEndPointsTestStep(TestStep):
    """PMSD ParkingMarkingsStartandEndPoints Test."""

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

        evaluation = ["", "", "", ""]

        FC_lineStartX = df.loc[:, df.columns.str.contains("PMDCamera_Front_parkingLines_lineStartX")]
        FC_lineStartY = df.loc[:, df.columns.str.contains("PMDCamera_Front_parkingLines_lineStartY")]
        FC_lineEndX = df.loc[:, df.columns.str.contains("PMDCamera_Front_parkingLines_lineEndX")]
        FC_lineEndY = df.loc[:, df.columns.str.contains("PMDCamera_Front_parkingLines_lineEndY")]

        if FC_lineStartX.empty or FC_lineStartY.empty or FC_lineEndX.empty or FC_lineEndY.empty != 0:
            evaluation[0] = "FC Parking Markings XY End Points signals not found."
            FC_result = False
        else:
            evaluation[0] = "FC Parking Markings XY End Points signals are present."
            FC_result = True

        RC_lineStartX = df.loc[:, df.columns.str.contains("PMDCamera_Rear_parkingLines_lineStartX")]
        RC_lineStartY = df.loc[:, df.columns.str.contains("PMDCamera_Rear_parkingLines_lineStartY")]
        RC_lineEndX = df.loc[:, df.columns.str.contains("PMDCamera_Rear_parkingLines_lineEndX")]
        RC_lineEndY = df.loc[:, df.columns.str.contains("PMDCamera_Rear_parkingLines_lineEndY")]

        if RC_lineStartX.empty or RC_lineStartY.empty or RC_lineEndX.empty or RC_lineEndY.empty != 0:
            evaluation[1] = "RC Parking Markings XY End Points signals not found."
            RC_result = False
        else:
            evaluation[1] = "RC Parking Markings XY End Points signals are present."
            RC_result = True

        LSC_lineStartX = df.loc[:, df.columns.str.contains("PMDCamera_Left_parkingLines_lineStartX")]
        LSC_lineStartY = df.loc[:, df.columns.str.contains("PMDCamera_Left_parkingLines_lineStartY")]
        LSC_lineEndX = df.loc[:, df.columns.str.contains("PMDCamera_Left_parkingLines_lineEndX")]
        LSC_lineEndY = df.loc[:, df.columns.str.contains("PMDCamera_Left_parkingLines_lineEndY")]

        if LSC_lineStartX.empty or LSC_lineStartY.empty or LSC_lineEndX.empty or LSC_lineEndY.empty != 0:
            evaluation[2] = "LSC Parking Markings XY End Points signals not found."
            LSC_result = False
        else:
            evaluation[2] = "LSC Parking Markings XY End Points signals are present."
            LSC_result = True

        RSC_lineStartX = df.loc[:, df.columns.str.contains("PMDCamera_Right_parkingLines_lineStartX")]
        RSC_lineStartY = df.loc[:, df.columns.str.contains("PMDCamera_Right_parkingLines_lineStartY")]
        RSC_lineEndX = df.loc[:, df.columns.str.contains("PMDCamera_Right_parkingLines_lineEndX")]
        RSC_lineEndY = df.loc[:, df.columns.str.contains("PMDCamera_Right_parkingLines_lineEndY")]

        if RSC_lineStartX.empty or RSC_lineStartY.empty or RSC_lineEndX.empty or RSC_lineEndY.empty != 0:
            evaluation[3] = "RSC Parking Markings XY End Points signals not found."
            RSC_result = False
        else:
            evaluation[3] = "RSC Parking Markings XY End Points signals are present."
            RSC_result = True

        cond_bool = [
            FC_result,
            RC_result,
            LSC_result,
            RSC_result,
        ]

        test_result = fc.PASS if all(cond_bool) else fc.FAIL
        signal_summary["FC_ParkingLinesXYCoordinates"] = evaluation[0]
        signal_summary["RC_ParkingLinesXYCoordinates"] = evaluation[1]
        signal_summary["LSC_ParkingLinesXYCoordinates"] = evaluation[2]
        signal_summary["RSC_ParkingLinesXYCoordinates"] = evaluation[3]

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
            fc.REQ_ID: ["1987866"],
            fc.TESTCASE_ID: ["58800"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Verify the x,y coordinates for the start and end point of  the detected parking marking in Vehicle Coordinate system."
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


@verifies("1987866")
@testcase_definition(
    name="SWRT_CNC_PMSD_ParkingMarkingsStartandEndPoints",
    description="Verify Parking Markings StartandEnd Points ",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class PmsdParkingMarkingsStartandEndPoints(TestCase):
    """ParkingMarkingsStartandEndPoints test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdParkingMarkingsStartandEndPointsTestStep,
        ]
