"""Parking Marker False Positive Rate KPI"""

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

import os
import sys

TRC_ROOT = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

import typing

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from tsf.core.common import PathSpecification
from tsf.io.sideload import JsonSideLoad

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import AssociationConstants
from pl_parking.PLP.CEM.ft_pcl_helper import FtPclHelper
from pl_parking.PLP.CEM.inputs.input_CemPclReader import PclDelimiterReader
from pl_parking.PLP.CEM.inputs.input_PmdReader import PMDCamera, PMDReader

SIGNAL_DATA = "PFS_ParkingMarker_FalsePositiveRate"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS PCL False Positive",
    description="This teststep checks if the false positive rate of the PCL lines is lower or"
    "equal to the false positive ratio of the PMD lines.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
@register_side_load(
    alias="JsonGt",
    side_load=JsonSideLoad,  # type of side loaders
    # use folder=os.path.join(TSF_BASE, "data", "CEM_json_gt") incase running locally
    path_spec=PathSpecification(
        folder=r"s3://par230-prod-data-lake-sim/gt_labels",
        extension=".json", s3=True,
    ),
)
class TestStepFtPCLFalsePositive(TestStep):
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
        signal_summary = {}

        reader = self.readers[SIGNAL_DATA].signals

        pcl_data = PclDelimiterReader(reader).convert_to_class()
        pmd_data = PMDReader(reader).convert_to_class()
        gt_data = self.side_load["JsonGt"]
        park_marker_gt = FtPclHelper.get_pcl_from_json_gt(gt_data)
        pmd_lines_gt = FtPclHelper.get_pmdlines_from_json_gt(gt_data)
        number_associated_pcl: typing.List[typing.Tuple[int, int]] = []
        pcl_false_positive_list: typing.List[float] = []

        for _, pcl_timeframe in enumerate(pcl_data):
            timeframe_nbr_associated_lines = 0
            if len(pcl_timeframe.pcl_delimiter_array) > 0:
                target_timestamp = min(park_marker_gt.keys(), key=lambda k: abs(float(k) - pcl_timeframe.timestamp))
                gt_with_closest_timestamp = park_marker_gt.get(target_timestamp)

                false_positive = FtPclHelper.calculate_cem_pcl_false_positive_iso(
                    pcl_timeframe.pcl_delimiter_array,
                    gt_with_closest_timestamp,
                    AssociationConstants.PCL_ASSOCIATION_RADIUS,
                )

                timeframe_nbr_associated_lines = len(pcl_timeframe.pcl_delimiter_array) - false_positive * len(
                    pcl_timeframe.pcl_delimiter_array
                )

                pcl_false_positive_list.append(false_positive)

            number_associated_pcl.append((pcl_timeframe.timestamp, timeframe_nbr_associated_lines))

        pmd_false_positive_list: typing.List[float] = []
        pmd_false_positive_per_camera: typing.Dict[PMDCamera, typing.List[float]] = dict()
        pmd_number_associated_lines: typing.Dict[PMDCamera, typing.List[typing.Tuple[int, int]]] = dict()

        for camera, timeframe_list in pmd_data.items():
            pmd_false_positive_per_camera[camera] = []
            pmd_number_associated_lines[camera] = []
            pmd_gt = pmd_lines_gt[camera]
            for pmd_timeframe in timeframe_list:
                timeframe_nbr_associated_lines = 0
                if len(pmd_timeframe.pmd_lines) > 0:
                    target_timestamp = min(pmd_gt.keys(), key=lambda k: abs(float(k) - pmd_timeframe.timestamp))
                    gt_with_closest_timestamp = pmd_gt.get(target_timestamp)
                    false_positive = FtPclHelper.calculate_pmd_false_positive_iso(
                        pmd_timeframe.pmd_lines,
                        gt_with_closest_timestamp,
                        AssociationConstants.PCL_ASSOCIATION_RADIUS,
                    )

                    timeframe_nbr_associated_lines = len(pmd_timeframe.pmd_lines) - false_positive * len(
                        pmd_timeframe.pmd_lines
                    )

                    pmd_false_positive_list.append(false_positive)
                    pmd_false_positive_per_camera[camera].append(false_positive)

                pmd_number_associated_lines[camera].append((pmd_timeframe.timestamp, timeframe_nbr_associated_lines))

        avg_pcl_false_positive = np.mean(pcl_false_positive_list)
        avg_pmd_false_positive = np.mean(pmd_false_positive_list)

        if avg_pcl_false_positive <= avg_pmd_false_positive:
            test_result = fc.PASS
            evaluation = "The false positive rate of the PCL lines is lower or equal to the false positive ratio of the PMD lines."
            signal_summary["PFS_ParkingMarker_accuracy"] = evaluation
        else:
            test_result = fc.FAIL
            evaluation = "The false positive rate of the PCL lines is not lower or equal to the false positive ratio of the PMD lines."
            signal_summary["PFS_ParkingMarker_accuracy"] = evaluation

        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": "Check if the false positive rate of the PCL lines is lower or equal to the false positive ratio of the PMD lines.",
                },
                "Result": {
                    "1": evaluation,
                },
                "Verdict": {
                    "1": "PASSED" if test_result == "passed" else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PFS Parking Markers accuracy")
        self.result.details["Plots"].append(sig_sum)

        # Average False Positive ration table
        source_false_positive = ["CEM", "PMD", "PMD Front", "PMD Rear", "PMD Right", "PMD Left"]
        values_false_positive = [
            avg_pcl_false_positive,
            avg_pmd_false_positive,
            np.mean(pmd_false_positive_per_camera[PMDCamera.FRONT]),
            np.mean(pmd_false_positive_per_camera[PMDCamera.REAR]),
            np.mean(pmd_false_positive_per_camera[PMDCamera.RIGHT]),
            np.mean(pmd_false_positive_per_camera[PMDCamera.LEFT]),
        ]
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Source", "Average False Positive"]),
                    cells=dict(values=[source_false_positive, values_false_positive]),
                )
            ]
        )
        fig.layout = go.Layout(title=dict(text="Average False Positive rate for parking markers", font_size=20))
        plot_titles.append("Average False Positive rate for parking markers")
        plots.append(fig)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=[timeframe.timestamp for timeframe in pcl_data],
                y=[len(timeframe.pcl_delimiter_array) for timeframe in pcl_data],
                mode="lines",
                name="Number of CEM PCL",
            )
        )
        fig.layout = go.Layout(
            xaxis=dict(title="Timestamp [nsec]"),
            yaxis=dict(title="pcl_delimiter"),
            title=dict(text="Number of CEM PCL", font_size=20),
        )
        fig.add_trace(
            go.Scatter(
                x=[timestamp for timestamp, _ in number_associated_pcl],
                y=[nbr_associated for _, nbr_associated in number_associated_pcl],
                mode="lines",
                name="Number of associated CEM PCL to the ground truth",
            )
        )
        fig.layout = go.Layout(
            xaxis=dict(title="Timestamp [nsec]"),
            yaxis=dict(title="associated_pcl"),
            title=dict(text="Number of associated CEM PCL", font_size=20),
        )
        plot_titles.append("Number of CEM PCL")
        plots.append(fig)
        remarks.append("")

        for camera, timeframe_list in pmd_data.items():
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=[timeframe.timestamp for timeframe in timeframe_list[1:]],
                    y=[len(timeframe.pmd_lines) for timeframe in timeframe_list[1:]],
                    mode="lines",
                    name=f"{camera._name_} camera number of PMD",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=[timestamp for timestamp, _ in (pmd_number_associated_lines[camera])[1:]],
                    y=[nbr_associated for _, nbr_associated in (pmd_number_associated_lines[camera])[1:]],
                    mode="lines",
                    name=f"{camera._name_} camera number of associated PMD to the ground truth",
                )
            )
            fig.layout = go.Layout(
                xaxis=dict(title="Timestamp [nsec]"),
                yaxis=dict(title="associated_pmd"),
                title=dict(text=f"{camera._name_} camera number of associated PMD", font_size=20),
            )
            plot_titles.append(f"{camera._name_} camera number of PMD")
            plots.append(fig)
            remarks.append("")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1530458"],
            fc.TESTCASE_ID: ["38841"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "The test passes if the false positive rate of the PCL lines is lower or "
                "equal to the false positive ratio of the PMD lines."
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


@verifies("1530458")
@testcase_definition(
    name="SWKPI_CNC_PFS_ParkingMarkerFalsePositiveRate",
    description="The test passes if the false positive rate of the PCL lines is lower or"
    "equal to the false positive ratio of the PMD lines.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_r9j4fE4mEe6M5-WQsF_-tQ&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36325",
)
@register_inputs("/parking")
class FtPCLFalsePositive(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPCLFalsePositive]
