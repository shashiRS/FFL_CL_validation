#!/usr/bin/env python3
"""Defining  pmsd Detected Parking Slot testcases"""
import logging
import os

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import math

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

SIGNAL_DATA = "PMSD_Detected_ParkingSlots"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD detected parking slots",
    description="This teststep checks detected parking slots A convex quadrilateral on the ground plane in the "
    "vehicle's coordinate system, with its points ordered counter-clockwise.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdDetectedParkingSlotsTestStep(TestStep):
    """PMSD Detected Parking Slot Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def angle(self, x1, y1, x2, y2):
        """Use dotproduct to find angle between vectors
        This always returns an angle between 0, 360
        """
        dot = x1 * x2 + y1 * y2
        det = x1 * y2 - y1 * x2
        angle = math.atan2(-det, -dot) + math.pi
        return math.degrees(angle)

    def cross_sign(self, x1, y1, x2, y2):
        """
        True if cross is positive
        False if negative or zero
        """
        return x1 * y2 > x2 * y1

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
        angle_evaluation = ["", "", "", ""]
        direction_evaluation = ["", "", "", ""]
        allcamera_angle_list = []
        allcamera_direction_list = []
        angle_test_result_list = []
        direction_test_result_list = []
        angle_result_list = []
        direction_result_list = []
        frame_dict = {}
        angle_test_result_dict = {}
        direction_test_result_dict = {}
        all_cameras = ["Front", "Rear", "Left", "Right"]

        for cam in all_cameras:
            # Extract slot coordinates for all four corners and convert to readable format.
            fc_P0_x = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_P0_x")]
            fc_P0_y = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_P0_y")]
            fc_P1_x = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_P1_x")]
            fc_P1_y = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_P1_y")]
            fc_P2_x = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_P2_x")]
            fc_P2_y = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_P2_y")]
            fc_P3_x = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_P3_x")]
            fc_P3_y = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_P3_y")]

            for i, (a1, b1, c1, d1, e1, f1, g1, h1) in enumerate(
                zip(fc_P0_x, fc_P0_y, fc_P1_x, fc_P1_y, fc_P2_x, fc_P2_y, fc_P3_x, fc_P3_y)
            ):

                fc_p0_x = fc_P0_x[a1].to_list()
                fc_p0_y = fc_P0_y[b1].to_list()
                fc_p1_x = fc_P1_x[c1].to_list()
                fc_p1_y = fc_P1_y[d1].to_list()
                fc_p2_x = fc_P2_x[e1].to_list()
                fc_p2_y = fc_P2_y[f1].to_list()
                fc_p3_x = fc_P3_x[g1].to_list()
                fc_p3_y = fc_P3_y[h1].to_list()

                for j1 in range(len(fc_p0_x)):
                    new_entries = {
                        cam
                        + "_Parkingslot"
                        + str(i)
                        + "_Frame"
                        + str(j1): [
                            (fc_p0_x[j1], fc_p0_y[j1]),
                            (fc_p1_x[j1], fc_p1_y[j1]),
                            (fc_p2_x[j1], fc_p2_y[j1]),
                            (fc_p3_x[j1], fc_p3_y[j1]),
                        ]
                    }
                    frame_dict.update(new_entries)

                angle_list = []
                for key, value in frame_dict.items():
                    points = value

                    #  Skip the first few frames with zero coordinate values
                    if not all(map(lambda x: all(x), points)):
                        new_entry = {key: True}
                        angle_test_result_dict.update(new_entry)
                        pass
                    else:
                        for i in range(len(points)):
                            p1 = points[i]
                            ref = points[i - 1]
                            p2 = points[i - 2]
                            x1, y1 = p1[0] - ref[0], p1[1] - ref[1]
                            x2, y2 = p2[0] - ref[0], p2[1] - ref[1]
                            angle_list.append(self.angle(x1, y1, x2, y2))

                            # Verify that the vertices are ordered in counter clock wise for a camera for all the
                            # frames and update the direction result dict.
                            if self.cross_sign(x1, y1, x2, y2):
                                new_entry = {key: True}
                                direction_test_result_dict.update(new_entry)
                                print("Inner Angle")
                            else:
                                new_entry = {key: False}
                                direction_test_result_dict.update(new_entry)
                                print("Outer Angle")

                        # Verify if all the angles of a camera are less than 180 degrees for all the frames and
                        # update the result dict.
                        if all(
                            flag < 180 and dirflag or flag >= 180 and not dirflag
                            for flag, dirflag in zip(angle_list, direction_test_result_dict.keys())
                        ):
                            new_entry = {key: True}
                            angle_test_result_dict.update(new_entry)
                        else:
                            new_entry = {key: False}
                            angle_test_result_dict.update(new_entry)

            allcamera_angle_list.append(angle_test_result_dict)
            allcamera_direction_list.append(direction_test_result_dict)

        #  Process the angle list and direction list and compute the final test result for all cameras
        for i in range(len(allcamera_angle_list)):
            for key, value in allcamera_angle_list[i].items():
                if not value:
                    angle_evaluation[i] = "Slot is not a convex quadriteral at ", key
                    angle_result_list.append(0)
                    break
                else:
                    angle_evaluation[i] = "Slot forms convex quadriteral"
                    angle_result_list.append(1)
            if all(angle_result_list):
                angle_test_result_list.append(True)
            else:
                angle_test_result_list.append(False)

        for i in range(len(allcamera_direction_list)):
            for key, value in allcamera_angle_list[i].items():
                if not value:
                    direction_evaluation[i] = "Slot do not have its points ordered counter-clockwise at", key
                    direction_result_list.append(0)
                    break
                else:
                    direction_evaluation[i] = "All slots has its points ordered counter-clockwise"
                    direction_result_list.append(1)
            if all(direction_result_list):
                direction_test_result_list.append(True)
            else:
                direction_test_result_list.append(False)

        test_result = fc.PASS if (all(angle_test_result_list) and all(direction_test_result_list)) else fc.FAIL

        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": "PMSD shall define a detected parking slots as a convex quadrilateral on the "
                    "ground plane from FRONT Camera",
                    "2": "PMSD shall define a detected parking slots as a convex quadrilateral on the "
                    "ground plane from REAR Camera",
                    "3": "PMSD shall define a detected parking slots as a convex quadrilateral on the "
                    "ground plane from LEFT Camera",
                    "4": "PMSD shall define a detected parking slots as a convex quadrilateral on the "
                    "ground plane from RIGHT Camera",
                    "5": "PMSD shall define a detected parking slots on the ground plane with its points ordered "
                    "counter-clockwise from FRONT Camera",
                    "6": "PMSD shall define a detected parking slots on the ground plane with its points ordered "
                    "counter-clockwise from REAR Camera",
                    "7": "PMSD shall define a detected parking slots on the ground plane with its points ordered "
                    "counter-clockwise from LEFT Camera",
                    "8": "PMSD shall define a detected parking slots on the ground plane with its points ordered "
                    "counter-clockwise from RIGHT Camera",
                },
                "Result": {
                    "1": angle_evaluation[0],
                    "2": angle_evaluation[1],
                    "3": angle_evaluation[2],
                    "4": angle_evaluation[3],
                    "5": direction_evaluation[0],
                    "6": direction_evaluation[1],
                    "7": direction_evaluation[2],
                    "8": direction_evaluation[3],
                },
                "Verdict": {
                    "1": "PASSED" if angle_test_result_list[0] else "FAILED",
                    "2": "PASSED" if angle_test_result_list[1] else "FAILED",
                    "3": "PASSED" if angle_test_result_list[2] else "FAILED",
                    "4": "PASSED" if angle_test_result_list[3] else "FAILED",
                    "5": "PASSED" if direction_test_result_list[0] else "FAILED",
                    "6": "PASSED" if direction_test_result_list[1] else "FAILED",
                    "7": "PASSED" if direction_test_result_list[2] else "FAILED",
                    "8": "PASSED" if direction_test_result_list[3] else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PFS Slot Coordinates")
        self.result.details["Plots"].append(sig_sum)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1988309"],
            fc.TESTCASE_ID: ["87533"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Verify pmsd defines slots as a convex quadrilateral on the ground plane in the "
                "vehicle's coordinate system, with its points ordered counter-clockwise."
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


@verifies("1988309")
@testcase_definition(
    name="SWRT_CNC_PMSD_SlotConvexQuadrilateral",
    description="Verify Detected Parking Slots",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class PmsdDetectedParkingSlots(TestCase):
    """Detected ParkingSlots test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdDetectedParkingSlotsTestStep,
        ]
