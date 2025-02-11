#!/usr/bin/env python3
"""Defining  pmsd slot road side edge testcases"""
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

SIGNAL_DATA = "PMSD_RoadSide_SlotCorners"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD road side edge slot corners",
    description="This teststep checks that the pmsd define the road side edge of the detected parking slot between the "
    "first and second point.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdRoadSideEdgeSlotCornersTestStep(TestStep):
    """PMSD Road side edge slot corners"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def cal_avg(self, points):
        """Use dotproduct to find angle between vectors
        This always returns an angle between 0, pi
        """
        avg01_x = (points[0][0] + points[1][0]) / 2
        avg01_y = (points[0][1] + points[1][1]) / 2
        avg23_x = (points[2][0] + points[3][0]) / 2
        avg23_y = (points[2][1] + points[3][1]) / 2
        dis01 = avg01_x**2 + avg01_y**2
        dis23 = avg23_x**2 + avg23_y**2
        msg = None
        if abs(avg01_y) <= 7:
            msg = "Not on scanning road"
            return dis01, dis23, msg
        else:
            return dis01, dis23, msg

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
        evaluation = ["", "", "", ""]
        allcamera_list = []
        roadside_edge_test_result_dict = {}
        roadside_edge_result_list = []
        frame_dict = {}
        roadside_edge_test_result_list = []
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
                        roadside_edge_test_result_dict.update(new_entry)
                        pass
                    else:
                        dis01, dis23, msg = self.cal_avg(points)
                        if msg is None:
                            # Verify if distance01 is less than or equal to distance23
                            # update the result dict.
                            if dis01 <= dis23:
                                new_entry = {key: True}
                                roadside_edge_test_result_dict.update(new_entry)
                            else:
                                new_entry = {key: False}
                                roadside_edge_test_result_dict.update(new_entry)
                        else:
                            key = key + "_Not_OnScanning_Road"
                            new_entry = {key: True}
                            roadside_edge_test_result_dict.update(new_entry)
                            pass

            allcamera_list.append(roadside_edge_test_result_dict)

        #  Process the road side edge slot list and compute the final test result for all cameras
        for i in range(len(allcamera_list)):
            for key, value in allcamera_list[i].items():
                if not value:
                    evaluation[i] = (
                        "road side edge of the detected parking slot is not between the first and second point.",
                        key,
                    )
                    roadside_edge_result_list.append(False)
                    break
                else:
                    evaluation[i] = "Road side edge of the detected parking slot is between the first and second point."
                    roadside_edge_result_list.append(True)
            if all(roadside_edge_result_list):
                roadside_edge_test_result_list.append(True)
            else:
                roadside_edge_test_result_list.append(False)

        test_result = fc.PASS if all(roadside_edge_test_result_list) else fc.FAIL

        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": "<PMSD> shall define the road side edge of the detected parking slot between the first and "
                    "second point for FRONT Camera",
                    "2": "<PMSD> shall define the road side edge of the detected parking slot between the first and "
                    "second point for REAR Camera",
                    "3": "<PMSD> shall define the road side edge of the detected parking slot between the first and "
                    "second point for LEFT Camera",
                    "4": "<PMSD> shall define the road side edge of the detected parking slot between the first and "
                    "second point for RIGHT Camera",
                },
                "Result": {
                    "1": evaluation[0],
                    "2": evaluation[1],
                    "3": evaluation[2],
                    "4": evaluation[3],
                },
                "Verdict": {
                    "1": "PASSED" if roadside_edge_test_result_list[0] else "FAILED",
                    "2": "PASSED" if roadside_edge_test_result_list[1] else "FAILED",
                    "3": "PASSED" if roadside_edge_test_result_list[2] else "FAILED",
                    "4": "PASSED" if roadside_edge_test_result_list[3] else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PFS Slot Coordinates")
        self.result.details["Plots"].append(sig_sum)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1988312"],
            fc.TESTCASE_ID: ["87896"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Verify pmsd shall define the road side edge of the detected parking slot between the first and "
                "second point."
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


@verifies("1988312")
@testcase_definition(
    name="SWRT_CNC_PMSD_DefineSlotRoadSideEdge",
    description="Verify road side edge slot corners",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class PmsdRoadSideEdgeSlotCorners(TestCase):
    """Road side edge slot corners test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdRoadSideEdgeSlotCornersTestStep,
        ]
