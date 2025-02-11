#!/usr/bin/env python3
"""Defining  pmsd Detected Parking Slot length testcases"""
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

SIGNAL_DATA = "PMSD_Detected_ParkingSlotsLength"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD detected parking slots length",
    description="This teststep checks pmsd detects potential parking slots that has a greater or equal length {"
    "AP_G_DES_MIN_SLOT_LENGTH_M} and width {AP_G_DES_MIN_SLOT_WIDTH_M}. ",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdDetectedParkingSlotsLengthTestStep(TestStep):
    """PMSD Detected Parking Slot Length Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def distance_length(self, points):
        """
        The distance between
        rc.Slots.parkingSlots[%].corner_1,
        rc.Slots.parkingSlots[%].corner_2 and
        rc.Slots.parkingSlots[%].corner_0
        rc.Slots.parkingSlots[%].corner_3
        should be greater or equal to {AP_G_DES_MIN_SLOT_LENGTH_M}
        """
        # Distance between conrner 1 and 2
        x1 = points[1][0]
        y1 = x1 = points[1][1]
        x2 = points[2][0]
        y2 = points[2][1]
        len_distance12 = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

        # Distance between conrner 0 and 3
        x1 = points[0][0]
        y1 = x1 = points[0][1]
        x2 = points[3][0]
        y2 = points[3][1]
        len_distance03 = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
        if (
            len_distance12 >= ConstantsPmsd.AP_G_DES_MIN_SLOT_LENGTH_M
            and len_distance03 >= ConstantsPmsd.AP_G_DES_MIN_SLOT_LENGTH_M
        ):
            return True
        else:
            return False

    def distance_width(self, points):
        """
        The distance between
        rc.Slots.parkingSlots[%].corner_0 and rc.Slots.parkingSlots[%].corner_1 (road side edge) and
        rc.Slots.parkingSlots[%].corner_2
        rc.Slots.parkingSlots[%].corner_3 (back side edge) should be greater or equal to {AP_G_DES_MIN_SLOT_WIDTH_M}
        """
        # Distance between corner 0 and 1
        x1 = points[0][0]
        y1 = points[0][1]
        x2 = points[1][0]
        y2 = points[1][1]
        len_width01 = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

        # Distance between corner 2 and 3
        x1 = points[2][0]
        y1 = points[2][1]
        x2 = points[3][0]
        y2 = points[3][1]
        len_width23 = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

        if (
            len_width01 >= ConstantsPmsd.AP_G_DES_MIN_SLOT_WIDTH_M
            and len_width23 >= ConstantsPmsd.AP_G_DES_MIN_SLOT_WIDTH_M
        ):
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
        width_evaluation = ["", "", "", ""]
        allcamera_length_list = []
        allcamera_width_list = []
        length_test_result_list = []
        width_test_result_list = []
        length_result_list = []
        width_result_list = []
        frame_dict = {}
        width_result_dict = {}
        length_test_result_dict = {}
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

                for key, value in frame_dict.items():
                    points = value

                    #  Skip the first few frames with zero coordinate values
                    if not all(map(lambda x: all(x), points)):
                        new_entry = {key: True}
                        length_test_result_dict.update(new_entry)
                        pass
                    else:
                        len_result = self.distance_length(points)
                        width_result = self.distance_width(points)
                        # Compute the result for length
                        if len_result:
                            new_entry = {key: True}
                            length_test_result_dict.update(new_entry)
                        else:
                            new_entry = {key: False}
                            length_test_result_dict.update(new_entry)

                        # # Compute the result for width
                        if width_result:
                            new_entry = {key: True}
                            width_result_dict.update(new_entry)
                        else:
                            new_entry = {key: False}
                            width_result_dict.update(new_entry)

            allcamera_length_list.append(length_test_result_dict)
            allcamera_width_list.append(width_result_dict)

        #  Process the angle list and direction list and compute the final test result for all cameras
        for i in range(len(allcamera_length_list)):
            for key, value in allcamera_length_list[i].items():
                if not value:
                    length_evaluation[i] = (
                        "parking slots does not have a greater or equal length { " "AP_G_DES_MIN_SLOT_LENGTH_M} at ",
                        key,
                    )
                    length_result_list.append(0)
                    break
                else:
                    length_evaluation[i] = (
                        "parking slots has a greater or equal length { " "AP_G_DES_MIN_SLOT_LENGTH_M}"
                    )
                    length_result_list.append(1)
            if all(length_result_list):
                length_test_result_list.append(True)
            else:
                length_test_result_list.append(False)

        for i in range(len(allcamera_width_list)):
            for key, value in allcamera_width_list[i].items():
                if not value:
                    width_evaluation[i] = (
                        "slots does not have a greater or equal width {AP_G_DES_MIN_SLOT_WIDTH_M} " "at",
                        key,
                    )
                    width_result_list.append(0)
                    break
                else:
                    width_evaluation[i] = "slots has a greater or equal width {AP_G_DES_MIN_SLOT_WIDTH_M}"
                    width_result_list.append(1)
            if all(width_result_list):
                width_test_result_list.append(True)
            else:
                width_test_result_list.append(False)

        test_result = fc.PASS if (all(length_test_result_list) and all(width_test_result_list)) else fc.FAIL

        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": "PMSD shall detect potential parking slots that has a greater or equal length {"
                    "AP_G_DES_MIN_SLOT_LENGTH_M} from FRONT Camera",
                    "2": "PMSD shall detect potential parking slots that has a greater or equal length {"
                    "AP_G_DES_MIN_SLOT_LENGTH_M} from REAR Camera",
                    "3": "PMSD shall detect potential parking slots that has a greater or equal length {"
                    "AP_G_DES_MIN_SLOT_LENGTH_M} from LEFT Camera",
                    "4": "PMSD shall detect potential parking slots that has a greater or equal length {"
                    "AP_G_DES_MIN_SLOT_LENGTH_M} from RIGHT Camera",
                    "5": "PMSD shall detect potential parking slots that has a greater or equal width"
                    " {AP_G_DES_MIN_SLOT_WIDTH_M} from FRONT Camera",
                    "6": "PMSD shall detect potential parking slots that has a greater or equal width"
                    " {AP_G_DES_MIN_SLOT_WIDTH_M} from REAR Camera",
                    "7": "PMSD shall detect potential parking slots that has a greater or equal width"
                    " {AP_G_DES_MIN_SLOT_WIDTH_M} from LEFT Camera",
                    "8": "PMSD shall detect potential parking slots that has a greater or equal width"
                    " {AP_G_DES_MIN_SLOT_WIDTH_M} from RIGHT Camera",
                },
                "Result": {
                    "1": length_evaluation[0],
                    "2": length_evaluation[1],
                    "3": length_evaluation[2],
                    "4": length_evaluation[3],
                    "5": width_evaluation[0],
                    "6": width_evaluation[1],
                    "7": width_evaluation[2],
                    "8": width_evaluation[3],
                },
                "Verdict": {
                    "1": "PASSED" if length_test_result_list[0] else "FAILED",
                    "2": "PASSED" if length_test_result_list[1] else "FAILED",
                    "3": "PASSED" if length_test_result_list[2] else "FAILED",
                    "4": "PASSED" if length_test_result_list[3] else "FAILED",
                    "5": "PASSED" if width_test_result_list[0] else "FAILED",
                    "6": "PASSED" if width_test_result_list[1] else "FAILED",
                    "7": "PASSED" if width_test_result_list[2] else "FAILED",
                    "8": "PASSED" if width_test_result_list[3] else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PFS Slot Coordinates")
        self.result.details["Plots"].append(sig_sum)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1988314"],
            fc.TESTCASE_ID: ["88175"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Verify pmsd shall detect potential parking slots that has a greater or equal length {"
                "AP_G_DES_MIN_SLOT_LENGTH_M} and width {AP_G_DES_MIN_SLOT_WIDTH_M}."
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


@verifies("1988314")
@testcase_definition(
    name="SWRT_CNC_PMSD_DetectedParkingSlotLength",
    description="Verify Detected Parking Slots length",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class PmsdDetectedParkingSlotsLength(TestCase):
    """Detected ParkingSlots length test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdDetectedParkingSlotsLengthTestStep,
        ]
