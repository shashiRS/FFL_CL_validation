"""Parking Marker Accuracy KPI"""

import logging

from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_side_load,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import math
import os
import sys
from collections import defaultdict

import pandas as pd

TRC_ROOT = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


import plotly.graph_objects as go
from tsf.core.common import PathSpecification
from tsf.io.sideload import JsonSideLoad

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import AssociationConstants
from pl_parking.PLP.CEM.ft_pcl_helper import FtPclHelper
from pl_parking.PLP.CEM.inputs.input_PmdReader import PMDReader
from pl_parking.PLP.CV.PMSD.constants import ConstantsPmsd

SIGNAL_DATA = "PMSD_EndPoints_AccuracyValues"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD Start and End points accuracy values",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
@register_side_load(
    alias="JsonGt",
    side_load=JsonSideLoad,  # type of side loaders
    # use folder=r"s3://par230-prod-data-lake-sim/gt_labels" incase running from caedge
    # use folder=os.path.join(TSF_BASE, "data", "CEM_json_gt") incase running locally
    path_spec=PathSpecification(
        folder=r"s3://par230-prod-data-lake-sim/gt_labels",
        extension=".json",
        s3=True,
    ),
    # Absolute path for the sideload.
)
class TestStepParkingLinesEndPointsAccuracy(TestStep):
    """Parking Marker False Positive Rate KPI"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step"""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarsk based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals

        all_camera_result = []
        all_camera_fail_dict = defaultdict(list)
        all_camera_plot_distance_dict = {}
        pmd_data = PMDReader(reader).convert_to_class()
        gt_data = self.side_load["JsonGt"]
        park_marker_gt = FtPclHelper.get_pmdlines_from_json_gt(gt_data)

        for camera, timeframe_list in pmd_data.items():
            each_camera_result = []
            each_camera_fail_dict = {}
            plot_distance_dict = {}
            frame_no = -1

            for pmd_timeframe in timeframe_list:
                frame_no = frame_no + 1
                if len(pmd_timeframe.pmd_lines) > 0:
                    target_timestamp = min(
                        park_marker_gt[camera].keys(), key=lambda k: abs(float(k) - pmd_timeframe.timestamp)
                    )

                    gt_with_closest_timestamp = park_marker_gt[camera].get(target_timestamp)

                    association = FtPclHelper.associate_pmd_to_ground_truth(
                        pmd_timeframe.pmd_lines,
                        gt_with_closest_timestamp,
                        AssociationConstants.PCL_ASSOCIATION_RADIUS,
                    )

                    for pmd, ground_truth in association[0]:
                        if ground_truth is not None:
                            pmd_start_x = pmd.line_start.x
                            pmd_start_y = pmd.line_start.y

                            gt_pmd_start_x = ground_truth.line_start.x
                            gt_pmd_start_y = ground_truth.line_start.y

                            # Considering car centre is at (0, 0)
                            endpoint_distance_from_car = math.sqrt((pmd_start_x - 0) ** 2 + (pmd_start_y - 0) ** 2)

                            # Distance between GT endpoints and detected end points
                            endpoint_and_gtpoint_distance = math.sqrt(
                                (abs(pmd_start_x) - abs(gt_pmd_start_x)) ** 2
                                + (abs(pmd_start_y) - abs(gt_pmd_start_y)) ** 2
                            )

                            entry = {frame_no: endpoint_and_gtpoint_distance}
                            plot_distance_dict.update(entry)

                            if (
                                ConstantsPmsd.AP_G_PMSD_MAXDIST_FAR_M
                                > endpoint_distance_from_car
                                >= ConstantsPmsd.AP_G_PMSD_MINDIST_FAR_M
                            ):
                                if endpoint_and_gtpoint_distance < ConstantsPmsd.AP_G_PMSD_ACCURACY_FAR_RANGE_M:
                                    each_camera_result.append(True)
                                    each_camera_fail_dict.setdefault(camera, []).append(True)
                                else:
                                    each_camera_result.append(False)
                                    each_camera_fail_dict.setdefault(camera, []).append(pmd_timeframe.timestamp)

                            elif (
                                ConstantsPmsd.AP_G_PMSD_MINDIST_FAR_M
                                > endpoint_distance_from_car
                                >= ConstantsPmsd.AP_G_PMSD_MAXDIST_CLOSE_M
                            ):
                                if endpoint_and_gtpoint_distance < ConstantsPmsd.AP_G_PMSD_ACCURACY_MID_RANGE_M:
                                    each_camera_result.append(True)
                                    each_camera_fail_dict.setdefault(camera, []).append(True)
                                else:
                                    each_camera_result.append(False)
                                    each_camera_fail_dict.setdefault(camera, []).append(pmd_timeframe.timestamp)
                            elif endpoint_distance_from_car <= ConstantsPmsd.AP_G_PMSD_MAXDIST_CLOSE_M:
                                if endpoint_and_gtpoint_distance <= ConstantsPmsd.AP_G_PMSD_ACCURACY_CLOSE_RANGE_M:
                                    each_camera_result.append(True)
                                    each_camera_fail_dict.setdefault(camera, []).append(True)
                                else:
                                    each_camera_result.append(False)
                                    each_camera_fail_dict.setdefault(camera, []).append(pmd_timeframe.timestamp)
                            else:
                                each_camera_result.append(False)
                                each_camera_fail_dict.setdefault(camera, []).append(pmd_timeframe.timestamp)
                        else:
                            # No ground truth is associated
                            entry = {frame_no: 0}
                            plot_distance_dict.update(entry)

                else:
                    # No pmd lines are detected
                    entry = {frame_no: 0}
                    plot_distance_dict.update(entry)

            all_camera_result.append(each_camera_result)
            all_camera_plot_distance_dict[camera] = plot_distance_dict

            if not each_camera_fail_dict:
                each_camera_fail_dict[camera] = "No pmd lines or associated ground truth found"
                all_camera_fail_dict.update(each_camera_fail_dict)
            else:
                all_camera_fail_dict.update(each_camera_fail_dict)

        final_result_list = []

        # Check if all lists are empty
        all_empty = all(len(inner_list) == 0 for inner_list in all_camera_result)
        if all_empty:
            evaluation = "No associated ground truth is found."
            signal_summary = pd.DataFrame(
                {
                    "Evaluation": {
                        "1": "PMSD shall detect the start and end of a parking marking with defined accuracy values in x and y position on flat surface for FRONT Camera",
                    },
                    "Result": {
                        "1": evaluation,
                    },
                    "Verdict": {
                        "1": "Not ASSESSED",
                    },
                }
            )

            sig_sum = fh.build_html_table(signal_summary, table_title="Detect Start and End point with accuracy")
            self.result.details["Plots"].append(sig_sum)
            test_result = fc.NOT_ASSESSED
        else:
            for i in range(len(all_camera_result)):
                if all(all_camera_result[i]):
                    final_result_list.append(True)
                else:
                    final_result_list.append(False)

            evaluation = ["", "", "", ""]
            for i, (_, value) in enumerate(all_camera_fail_dict.items()):
                if isinstance(value, str):
                    evaluation[i] = value
                elif not all(value):
                    evaluation[i] = "PMSD detect the start and end of a parking marking within the accuracy interval"
                else:
                    evaluation[i] = "Failed timestamps ", value

            test_result = fc.PASS if all(final_result_list) else fc.FAIL
            signal_summary = pd.DataFrame(
                {
                    "Evaluation": {
                        "1": "PMSD shall detect the start and end of a parking marking with defined accuracy values in x and y position on flat surface for FRONT Camera",
                        "2": "PMSD shall detect the start and end of a parking marking with defined accuracy values in x and y position on flat surface for REAR Camera",
                        "3": "PMSD shall detect the start and end of a parking marking with defined accuracy values in x and y position on flat surface for LEFT Camera",
                        "4": "PMSD shall detect the start and end of a parking marking with defined accuracy values in x and y position on flat surface for RIGHT Camera",
                    },
                    "Result": {
                        "1": evaluation[0],
                        "2": evaluation[1],
                        "3": evaluation[2],
                        "4": evaluation[3],
                    },
                    "Verdict": {
                        "1": "PASSED" if final_result_list[0] else "FAILED",
                        "2": "PASSED" if final_result_list[1] else "FAILED",
                        "3": "PASSED" if final_result_list[2] else "FAILED",
                        "4": "PASSED" if final_result_list[3] else "FAILED",
                    },
                }
            )

            sig_sum = fh.build_html_table(signal_summary, table_title="Detect Start and End point with accuracy")
            self.result.details["Plots"].append(sig_sum)

            camera = ["Front Camera", "Rear Camera", "Left Camera", "Right Camera"]
            for i in range(len(all_camera_plot_distance_dict)):
                keys_list = list(all_camera_plot_distance_dict[i].keys())
                values_list = list(all_camera_plot_distance_dict[i].values())
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=keys_list,
                        y=values_list,
                        mode="lines",
                        line=dict(color="green"),
                        name=f"Distance between parking lines and GT lines of {camera[i]}  [m]",
                    )
                )

                fig.layout = go.Layout(
                    xaxis=dict(title="Frame number"),
                    yaxis=dict(title="distance error [m]"),
                    title=dict(text=f"Distance Error of {camera[i]}", font_size=15),
                )
                plot_titles.append("")
                plots.append(fig)
                remarks.append("")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1987870"],
            fc.TESTCASE_ID: ["93983"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "The test passes if start and end of a parking marking are within the accuracy values in x and y position on flat surface"
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


@verifies("1987870")
@testcase_definition(
    name="SWRT_CNC_PMSD_ParkingLinesEndPointsAccuracy",
    description="The test passes if start and end of a parking marking are within the accuracy values in x and y position on flat surface",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class ParkingLinesEndPointsAccuracy(TestCase):
    """Parking lines end point accuracy test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepParkingLinesEndPointsAccuracy]
