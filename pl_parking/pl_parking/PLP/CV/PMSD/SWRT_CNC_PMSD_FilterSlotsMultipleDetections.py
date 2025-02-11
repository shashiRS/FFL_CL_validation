#!/usr/bin/env python3
"""Defining pmsd Filter Detected Multiple Parking Slot testcases"""
import logging
import os

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


import math
from collections import defaultdict

import pandas as pd
import torch
from shapely.geometry import Polygon
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

SIGNAL_DATA = "PMSD_Detected_MultipleParkingSlots"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="Filter multiple detection of the same parking slot in same image",
    description="This teststep checks pmsd shall filter out multiple detections of the same parking slot detected on the same image. ",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdDetectedMultipleParkingSlotsTestStep(TestStep):
    """PMSD Filter Multiple Detected Parking Slot Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    # Function to truncate keys
    def truncate_keys(self, frame_dict, length):
        """Function to truncate keys of a dict till frame number"""
        return {k[:length]: v for k, v in frame_dict.items()}

    # Function to compute the intersection over union (IoU) between two rotated parallelograms
    def compute_iou(self, rot_parallelogram1, rot_parallelogram2):
        """
        Compute the Intersection over Union (IoU) between two parallelograms.

        Args:
            parallelogram1, parallelogram2: Each is a 4x2 numpy array representing the parallelogram's vertices.

        Returns:
            IoU value (float) between 0 and 1.
        """
        # Convert the rotated parallelogram (4 vertices) to Polygon object
        poly1 = Polygon(rot_parallelogram1)
        poly2 = Polygon(rot_parallelogram2)

        if not poly1.is_valid or not poly2.is_valid:
            return 0.0

        # Compute intersection area
        intersection = poly1.intersection(poly2).area

        # Compute union area
        union = poly1.union(poly2).area

        # Return IoU
        return intersection / union if union != 0 else 0.0

    def rotated_nms(self, boxes, scores, iou_threshold=0.6):
        """
        Perform Non-Maximum Suppression on a list of rotated parallelograms.

        Args:
            boxes (list of np.array): List of 4x2 arrays representing the rotated parallelograms (vertices).
            scores (torch.Tensor): A tensor of confidence scores corresponding to each box.
            iou_threshold (float): Threshold for the Intersection over Union (IoU) to decide suppression.

        Returns:
            List of indices of boxes to keep after suppression.
        """
        num_boxes = len(boxes)

        tensor = torch.tensor(scores)
        # Sort boxes by confidence score (descending order)
        sorted_indices = torch.argsort(tensor, descending=True)

        keep = []  # List to store indices of boxes to keep
        suppressed = torch.zeros(num_boxes, dtype=torch.bool)  # Track suppressed boxes

        for i in range(len(sorted_indices)):
            # Take the box with the highest score
            current_index = sorted_indices[i]

            # If the current box is already suppressed, skip it
            if suppressed[current_index]:
                continue

            # Add the current box to the keep list
            keep.append(current_index.item())

            # Suppress boxes with high IoU with the current box
            current_box = boxes[current_index.item()]
            ious = [self.compute_iou(current_box, boxes[idx.item()]) for idx in sorted_indices[i + 1 :]]

            # Mark boxes with IoU above the threshold as suppressed
            suppress_indices = [sorted_indices[i + 1 :][j] for j, iou in enumerate(ious) if iou > iou_threshold]
            suppressed[suppress_indices] = True

        return keep

    def contains_only_nan(self, lst):
        """
        Check if a list containing tuples has any nan values inside it..

        Args:
            list of tuples containing coordinates of boxes..

        Returns:
            Boolean value based on tuples values.
        """
        for tup in lst:
            if not all(math.isnan(x) for x in tup):  # Check if all values in the tuple are NaN
                return False
        return True

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
        evaluation = ["", "", "", ""]
        all_camera_final_result_dict = {}
        test_report_result = {}
        all_cameras = ["Front", "Rear", "Left", "Right"]

        for cam in all_cameras:
            all_slots_coordinate_dict = defaultdict(list)
            test_result_list = []
            test_result_dict = defaultdict(list)
            final_test_result_list = []
            final_test_result_dict = defaultdict(list)
            extracted_dict = defaultdict(list)
            final_list = []

            # Extract slot coordinates for all four corners and convert to readable format.
            fc_P0_x = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_P0_x")]
            fc_P0_y = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_P0_y")]
            fc_P1_x = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_P1_x")]
            fc_P1_y = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_P1_y")]
            fc_P2_x = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_P2_x")]
            fc_P2_y = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_P2_y")]
            fc_P3_x = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_P3_x")]
            fc_P3_y = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_P3_y")]
            existence_probability = df.loc[:, df.columns.str.contains(f"PmsdSlot_{cam}_existenceProbability")]
            for i in range(len(fc_P0_x)):
                frame_dict = {}
                for j1, column_name in enumerate(
                    zip(fc_P0_x, fc_P0_y, fc_P1_x, fc_P1_y, fc_P2_x, fc_P2_y, fc_P3_x, fc_P3_y, existence_probability)
                ):

                    corner_x0 = fc_P0_x[column_name[0]].iloc[i]
                    corner_y0 = fc_P0_y[column_name[1]].iloc[i]
                    corner_x1 = fc_P1_x[column_name[2]].iloc[i]
                    corner_y1 = fc_P1_y[column_name[3]].iloc[i]
                    corner_x2 = fc_P2_x[column_name[4]].iloc[i]
                    corner_y2 = fc_P2_y[column_name[5]].iloc[i]
                    corner_x3 = fc_P3_x[column_name[6]].iloc[i]
                    corner_y3 = fc_P3_y[column_name[7]].iloc[i]
                    confidence_score = existence_probability[column_name[8]].iloc[i]

                    new_key = cam + "_Frame" + str(i) + "_ParkingSlot" + str(j1)

                    new_entries = {
                        new_key: [
                            (corner_x0, corner_y0),
                            (corner_x1, corner_y1),
                            (corner_x2, corner_y2),
                            (corner_x3, corner_y3),
                            (confidence_score),
                        ]
                    }

                    frame_dict.update(new_entries)

                final_list.append(frame_dict)

            for frame_dict in final_list:
                for key, value in frame_dict.items():
                    points = value[:-1]

                    # Skip the frames with zero coordinate values
                    if not all(map(lambda x: all(x), points)):
                        continue
                    else:
                        all_slots_coordinate_dict[key].append(value)

            # Truncate keys to the first 15 characters
            truncated_dict = self.truncate_keys(all_slots_coordinate_dict, 15)
            keys_to_extract = truncated_dict.keys()

            # extracting keys using a for loop and conditional statement
            for key, value in all_slots_coordinate_dict.items():
                for k in keys_to_extract:
                    if key[:15] == k:
                        extracted_dict[k].append(value)

            # Compare the length of all slots of the same image and find out the filtered slots and compute
            # the result
            for key in extracted_dict:
                if (len(extracted_dict[key]) > 1) or (len(extracted_dict[key][0])) > 1:
                    p_list = []
                    parallelograms = []

                    for coord_list in extracted_dict[key]:
                        conf = coord_list[0][4]
                        is_parallelogram = self.contains_only_nan(coord_list[0][:-1])
                        if not is_parallelogram:
                            parallelograms.append(coord_list[0][:-1])
                            p_list.append(conf)
                            # Perform rotated NMS
                            keep_indices = self.rotated_nms(parallelograms, p_list, iou_threshold=0.6)

                            if len(keep_indices) == len(p_list):
                                result = True
                                test_result_list.append(result)
                            else:
                                result = False
                                test_result_list.append(result)
                                value = (
                                    "Frame: "
                                    + key
                                    + " - AlgoOutput is "
                                    + str(len(p_list))
                                    + " and actual filtered Slots are "
                                    + str(len(keep_indices))
                                )
                                test_result_dict[key].append(value)
                        else:
                            pass

                final_test_result_list.append(test_result_list)
                final_test_result_dict.update(test_result_dict)

            if any(False in nested_list for nested_list in final_test_result_list):
                test_report_result[cam] = False
            else:
                test_report_result[cam] = True

            all_camera_final_result_dict[cam] = final_test_result_dict

        for i, value in enumerate(all_camera_final_result_dict):
            if len(all_camera_final_result_dict[value]) != 0:
                failed_frames = all_camera_final_result_dict[value].values()
                evaluation[i] = (
                    "PMSD does not filter out multiple detections of the same parking slot detected on the same image at ",
                    failed_frames,
                )
            else:
                evaluation[i] = (
                    "PMSD filter out multiple detections of the same parking slot detected on the same image"
                )

        list_of_results = [v for k, v in test_report_result.items()]
        test_result = fc.PASS if all(list_of_results) else fc.FAIL

        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": "PMSD shall filter out multiple detections of the same parking slot detected on the same image for FRONT Camera",
                    "2": "PMSD shall filter out multiple detections of the same parking slot detected on the same image for REAR Camera",
                    "3": "PMSD shall filter out multiple detections of the same parking slot detected on the same image for LEFT Camera",
                    "4": "PMSD shall filter out multiple detections of the same parking slot detected on the same image for RIGHT Camera",
                },
                "Result": {
                    "1": evaluation[0],
                    "2": evaluation[1],
                    "3": evaluation[2],
                    "4": evaluation[3],
                },
                "Verdict": {
                    "1": "PASSED" if list_of_results[0] else "FAILED",
                    "2": "PASSED" if list_of_results[1] else "FAILED",
                    "3": "PASSED" if list_of_results[2] else "FAILED",
                    "4": "PASSED" if list_of_results[3] else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PFS Filter Multiple Slot Detections")
        self.result.details["Plots"].append(sig_sum)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1988315"],
            fc.TESTCASE_ID: ["92407"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Verify that the PMSD shall filter out multiple detections of the same parking slot detected on the same image."
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


@verifies("1988315")
@testcase_definition(
    name="SWRT_CNC_PMSD_FilterSlotsMultipleDetections",
    description="Verify multiple detections of the same parking slot detected on the same image",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class PmsdDetectedMultipleParkingSlots(TestCase):
    """Detected ParkingSlots multiple detections test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdDetectedMultipleParkingSlotsTestStep,
        ]
