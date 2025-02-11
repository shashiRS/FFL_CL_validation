#!/usr/bin/env python3
"""Defining  pmsd ParkingMarkingsStartandEndPoints testcases"""
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

        reader = self.readers[SIGNAL_DATA]

        df = reader.as_plain_df
        df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]

        evaluation = ["", "", "", ""]

        FC_lineStartX = df.loc[:, df.columns.str.contains("PMDCamera_Front_parkingLines_lineStartX")]
        FC_lineStartY = df.loc[:, df.columns.str.contains("PMDCamera_Front_parkingLines_lineStartY")]
        FC_lineEndX = df.loc[:, df.columns.str.contains("PMDCamera_Front_parkingLines_lineEndX")]
        FC_lineEndY = df.loc[:, df.columns.str.contains("PMDCamera_Front_parkingLines_lineEndY")]

        if FC_lineStartX.empty or FC_lineStartY.empty or FC_lineEndX.empty or FC_lineEndY.empty != 0:
            evaluation[0] = (
                "Front camera Parking Markings x and y End Points coordinates are not present in the measurement."
            )
            FC_result = False
        else:
            evaluation[0] = (
                "Front camera Parking Markings x and y End Points coordinates are present in the measurement."
            )
            FC_result = True

        RC_lineStartX = df.loc[:, df.columns.str.contains("PMDCamera_Rear_parkingLines_lineStartX")]
        RC_lineStartY = df.loc[:, df.columns.str.contains("PMDCamera_Rear_parkingLines_lineStartY")]
        RC_lineEndX = df.loc[:, df.columns.str.contains("PMDCamera_Rear_parkingLines_lineEndX")]
        RC_lineEndY = df.loc[:, df.columns.str.contains("PMDCamera_Rear_parkingLines_lineEndY")]

        if RC_lineStartX.empty or RC_lineStartY.empty or RC_lineEndX.empty or RC_lineEndY.empty != 0:
            evaluation[1] = (
                "Rear camera Parking Markings x and y End Points coordinates are not present in the measurement."
            )
            RC_result = False
        else:
            evaluation[1] = (
                "Rear camera Parking Markings x and y End Points coordinates are present in the measurement."
            )
            RC_result = True

        LSC_lineStartX = df.loc[:, df.columns.str.contains("PMDCamera_Left_parkingLines_lineStartX")]
        LSC_lineStartY = df.loc[:, df.columns.str.contains("PMDCamera_Left_parkingLines_lineStartY")]
        LSC_lineEndX = df.loc[:, df.columns.str.contains("PMDCamera_Left_parkingLines_lineEndX")]
        LSC_lineEndY = df.loc[:, df.columns.str.contains("PMDCamera_Left_parkingLines_lineEndY")]

        if LSC_lineStartX.empty or LSC_lineStartY.empty or LSC_lineEndX.empty or LSC_lineEndY.empty != 0:
            evaluation[2] = (
                "Left side camera Parking Markings x and y End Points coordinates are not present in the measurement."
            )
            LSC_result = False
        else:
            evaluation[2] = (
                "Left side camera Parking Markings x and y End Points coordinates are present in the measurement."
            )
            LSC_result = True

        RSC_lineStartX = df.loc[:, df.columns.str.contains("PMDCamera_Right_parkingLines_lineStartX")]
        RSC_lineStartY = df.loc[:, df.columns.str.contains("PMDCamera_Right_parkingLines_lineStartY")]
        RSC_lineEndX = df.loc[:, df.columns.str.contains("PMDCamera_Right_parkingLines_lineEndX")]
        RSC_lineEndY = df.loc[:, df.columns.str.contains("PMDCamera_Right_parkingLines_lineEndY")]

        if RSC_lineStartX.empty or RSC_lineStartY.empty or RSC_lineEndX.empty or RSC_lineEndY.empty != 0:
            evaluation[3] = (
                "Right side camera Parking Markings x and y End Points coordinates are not present in the measurement."
            )
            RSC_result = False
        else:
            evaluation[3] = (
                "Right side camera Parking Markings x and y End Points coordinates are present in the measurement."
            )
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
                "Signal Evaluation": {
                    "1": "PMSD_FC_DATA.ParkingLines.parkingLines[%].startPoint.x,PMSD_FC_DATA.ParkingLines.parkingLines[%].startPoint.y, PMSD_FC_DATA.ParkingLines.parkingLines[%].endPoint.x, PMSD_FC_DATA.ParkingLines.parkingLines[%].endPoint.y",
                    "2": "PMSD_RC_DATA.ParkingLines.parkingLines[%].startPoint.x,PMSD_RC_DATA.ParkingLines.parkingLines[%].startPoint.y, PMSD_RC_DATA.ParkingLines.parkingLines[%].endPoint.x, PMSD_RC_DATA.ParkingLines.parkingLines[%].endPoint.y",
                    "3": "PMSD_LSC_DATA.ParkingLines.parkingLines[%].startPoint.x,PMSD_LSC_DATA.ParkingLines.parkingLines[%].startPoint.y, PMSD_LSC_DATA.ParkingLines.parkingLines[%].endPoint.x, PMSD_LSC_DATA.ParkingLines.parkingLines[%].endPoint.y",
                    "4": "PMSD_RSC_DATA.ParkingLines.parkingLines[%].startPoint.x,PMSD_RSC_DATA.ParkingLines.parkingLines[%].startPoint.y, PMSD_RSC_DATA.ParkingLines.parkingLines[%].endPoint.x, PMSD_RSC_DATA.ParkingLines.parkingLines[%].endPoint.y",
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

        sig_sum = fh.build_html_table(signal_summary, table_title="PMSD Line Confidence")
        self.result.details["Plots"].append(sig_sum)

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
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_6xkTwNsGEe62R7UY0u3jZg&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class PmsdParkingMarkingsStartandEndPoints(TestCase):
    """ParkingMarkingsStartandEndPoints test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdParkingMarkingsStartandEndPointsTestStep,
        ]
