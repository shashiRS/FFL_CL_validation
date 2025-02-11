#!/usr/bin/env python3
"""Defining  pmsd Detected Parking Marking length testcases"""
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
from pl_parking.PLP.CV.PMSD.constants import ConstantsPmsd

SIGNAL_DATA = "PMSD_Detected_ParkingMarkingsLength"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD detected parking markings length",
    description="This teststep checks pmsd detects potential parking markings that has a greater or equal length {"
    "AP_G_DES_MIN_SLOT_LENGTH_M} and width {AP_G_DES_MIN_SLOT_WIDTH_M}. ",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdDetectedParkingMarkingsLengthTestStep(TestStep):
    """PMSD Detected Parking Slot Length Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def distance_length(self, points):
        """
        The detected parking marker length must be greater or equal to AP_G_PMSD_MIN_LENGTH_P_MARKING_SEG_M.

        The parking marker length is described as the lenght between the two endpoints. For example, the distance
        between:
        fc.ParkingLines.parkingLines[%].startPoint  AND fc.ParkingLines.parkingLines[%].endPoint
        """
        # Calculate distance between start and end point
        x1 = points[0][0]
        y1 = points[0][1]
        x2 = points[1][0]
        y2 = points[1][1]
        len_distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

        if len_distance >= ConstantsPmsd.AP_G_PMSD_MIN_LENGTH_P_MARKING_SEG_M:
            return True
        else:
            return False

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
        df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
        length_evaluation = ["", "", "", ""]
        allcamera_length_list = []
        length_test_result_list = []
        length_result_list = []
        frame_dict = {}
        length_test_result_dict = {}
        all_cameras = ["Front", "Rear", "Left", "Right"]

        for cam in all_cameras:

            # Extract parking lines length for all four corners and convert to readable format.
            startpoint_x = df.loc[:, df.columns.str.contains(f"PMDCamera_{cam}_parkingLines_lineStartX")]
            startpoint_y = df.loc[:, df.columns.str.contains(f"PMDCamera_{cam}_parkingLines_lineStartY")]
            endpoint_x = df.loc[:, df.columns.str.contains(f"PMDCamera_{cam}_parkingLines_lineEndX")]
            endpoint_y = df.loc[:, df.columns.str.contains(f"PMDCamera_{cam}_parkingLines_lineEndY")]

            for i, (a1, b1, c1, d1) in enumerate(zip(startpoint_x, startpoint_y, endpoint_x, endpoint_y)):
                startpointx = startpoint_x[a1].to_list()
                startpointy = startpoint_y[b1].to_list()
                endpointx = endpoint_x[c1].to_list()
                endpointy = endpoint_y[d1].to_list()

                for j1 in range(len(startpointx)):

                    new_entries = {
                        cam
                        + "_Parkingmarkings"
                        + str(i)
                        + "_Frame"
                        + str(j1): [
                            (startpointx[j1], startpointy[j1]),
                            (endpointx[j1], endpointy[j1]),
                        ]
                    }
                    frame_dict.update(new_entries)

                for key, value in frame_dict.items():
                    points = value
                    #  Skip the first few frames with zero coordinate values
                    if not all(map(lambda x: all(x), points)):
                        new_entry = {key: True}
                        length_test_result_dict.update(new_entry)
                        pass
                    else:
                        len_result = self.distance_length(points)

                        # Compute the result for length
                        if len_result:
                            new_entry = {key: True}
                            length_test_result_dict.update(new_entry)
                        else:
                            new_entry = {key: False}
                            length_test_result_dict.update(new_entry)

            allcamera_length_list.append(length_test_result_dict)

        #  Process the angle list and direction list and compute the final test result for all cameras

        for i in range(len(allcamera_length_list)):
            for key, value in allcamera_length_list[i].items():
                if not value:
                    length_evaluation[i] = (
                        "parking markings does not have a greater or equal length { "
                        "AP_G_PMSD_MIN_LENGTH_P_MARKING_SEG_M} at ",
                        key,
                    )
                    length_result_list.append(0)
                    break
                else:
                    length_evaluation[i] = (
                        "parking markings has a greater or equal length {AP_G_PMSD_MIN_LENGTH_P_MARKING_SEG_M}"
                    )
                    length_result_list.append(1)

            if all(length_result_list):
                length_test_result_list.append(True)
            else:
                length_test_result_list.append(False)

        test_result = fc.PASS if all(length_test_result_list) else fc.FAIL

        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": "PMSD shall detect potential parking markings that has a greater or equal length {"
                    "AP_G_PMSD_MIN_LENGTH_P_MARKING_SEG_M} from FRONT Camera",
                    "2": "PMSD shall detect potential parking markings that has a greater or equal length {"
                    "AP_G_PMSD_MIN_LENGTH_P_MARKING_SEG_M} from REAR Camera",
                    "3": "PMSD shall detect potential parking markings that has a greater or equal length {"
                    "AP_G_PMSD_MIN_LENGTH_P_MARKING_SEG_M} from LEFT Camera",
                    "4": "PMSD shall detect potential parking markings that has a greater or equal length {"
                    "AP_G_PMSD_MIN_LENGTH_P_MARKING_SEG_M} from RIGHT Camera",
                },
                "Result": {
                    "1": length_evaluation[0],
                    "2": length_evaluation[1],
                    "3": length_evaluation[2],
                    "4": length_evaluation[3],
                },
                "Verdict": {
                    "1": "PASSED" if length_test_result_list[0] else "FAILED",
                    "2": "PASSED" if length_test_result_list[1] else "FAILED",
                    "3": "PASSED" if length_test_result_list[2] else "FAILED",
                    "4": "PASSED" if length_test_result_list[3] else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PFS Slot Coordinates")
        self.result.details["Plots"].append(sig_sum)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1987857"],
            fc.TESTCASE_ID: ["89463"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Verify pmsd shall provide detected parking markings based on the semseg image fulfilling ALL of the "
                "following dimension conditions: The minimum length shall be at least {"
                "AP_G_PMSD_MIN_LENGTH_P_MARKING_SEG_M} m"
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


@verifies("1987857")
@testcase_definition(
    name="SWRT_CNC_PMSD_DetectedParkingMarkerLength",
    description="Verify Detected Parking Markings length",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class PmsdDetectedParkingMarkingsLength(TestCase):
    """Detected ParkingMarkings length test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdDetectedParkingMarkingsLengthTestStep,
        ]
