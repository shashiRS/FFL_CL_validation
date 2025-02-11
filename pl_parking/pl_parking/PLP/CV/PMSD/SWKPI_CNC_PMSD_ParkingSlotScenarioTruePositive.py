"""Parking Slot Scenario True Positive / False Positive KPI Test."""
import json
import logging
import os
import sys
import typing

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from tsf.core.common import PathSpecification
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
from tsf.io.sideload import JsonSideLoad

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CV.PMSD.constants import AssociationConstants
from pl_parking.PLP.CV.PMSD.ft_helper import PMSDSignals, hex_to_rgba
from pl_parking.PLP.CV.PMSD.ft_slot_helper import FtSlotHelper
from pl_parking.PLP.CV.PMSD.inputs.input_PmdReader import PMDCamera, PMDReader
from pl_parking.PLP.CV.PMSD.inputs.input_PsdPmsdSlotReader import PSDSlotReader as SlotReader

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "PMSD_KPI_Slot_Scenario_TruePositive_FalsePositive"

example_obj = PMSDSignals()


@teststep_definition(
    step_number=1,
    name="CV PMSD KPI Slot TruePositive",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, PMSDSignals)
@register_side_load(
    alias="JsonGt",
    side_load=JsonSideLoad,
    path_spec=PathSpecification(folder=r"s3://par230-prod-data-lake-sim/gt_labels", extension=".json", s3=True),
)
class TestStepFtSlotTruePositive(TestStep):
    """Test Parking Slot True Positive / False Positive"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step"""
        super().__init__()

    def load_json(self, path: str):
        """
        Load JSON data from a file.

        Parameters:
        - filepath: str, the path to the JSON file.

        Returns:
        - data: dictionary, the parsed JSON data.
        """
        try:
            with open(path) as file:
                data = json.load(file)
        except FileNotFoundError:
            _log.error("Ground truth file not found.")
            data = "Ground truth file not found."
        return data

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remark based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        detected_slots = SlotReader(reader).convert_to_class()
        gt_json = os.path.join(TSF_BASE, "data", "CEM_json_gt", "JsonGt.json")
        gt_data = self.load_json(gt_json) if os.path.exists(gt_json) else self.side_load["JsonGt"]
        gt_slots = FtSlotHelper.get_slot_from_json_gt_new(gt_data)

        associated_gt_slots_per_camera: typing.Dict[PMDCamera, typing.List[float]] = dict()
        number_of_gt_slots_per_camera: typing.Dict[PMDCamera, typing.List[int]] = dict()
        number_of_detected_slots_per_camera: typing.Dict[PMDCamera, typing.List[typing.Tuple[int, int]]] = dict()
        number_of_associated_gt_slots_per_camera: typing.Dict[PMDCamera, typing.List[int]] = dict()

        for _, camera in enumerate(PMDCamera):
            associated_gt_slots_per_camera[camera] = []
            number_of_associated_gt_slots_per_camera[camera] = []
            number_of_gt_slots_per_camera[camera] = []
            number_of_detected_slots_per_camera[camera] = []
            gt_slot = gt_slots[camera]
            for detected_slot in detected_slots[camera]:
                number_of_detected_slots_per_camera[camera].append(
                    (detected_slot.timestamp, detected_slot.number_of_slots))
                gt_with_closest_timestamp = gt_slot.get(
                    min(gt_slot.keys(), key=lambda k: abs(k - detected_slot.timestamp))
                )
                if not all(
                        detected_slot.timestamp == v.slot_timestamp for v in gt_with_closest_timestamp):
                    number_of_associated_gt_slots_per_camera[camera].append(0)
                    associated_gt_slots_per_camera[camera].append(0)
                    number_of_gt_slots_per_camera[camera].append(-1)
                elif detected_slot.number_of_slots < 1:
                    associated_gt_slots_per_camera[camera].append(0)
                    number_of_associated_gt_slots_per_camera[camera].append(0)
                    number_of_gt_slots_per_camera[camera].append(len(gt_slot[int(detected_slot.timestamp)]))
                else:
                    number_of_gt_slots_per_camera[camera].append(len(gt_slot[int(detected_slot.timestamp)]))
                    association = FtSlotHelper.associate_slot_list(
                        detected_slot.parking_slots,
                        gt_with_closest_timestamp,
                    )
                    associated_distances = []
                    for asso in association.items():
                        gt_i, pcl_i = asso
                        detected_scenario = FtSlotHelper.get_slot_scenario(detected_slot.parking_slots[pcl_i])
                        gt_scenario = FtSlotHelper.get_slot_scenario(gt_with_closest_timestamp[gt_i])
                        if detected_scenario == gt_scenario:
                            associated_distances.append(1)
                        else:
                            associated_distances.append(0)

                    associated_gt_slots_per_camera[camera].append(
                        np.mean(associated_distances) if len(associated_distances) > 0 else 0)
                    number_of_associated_gt_slots_per_camera[camera].append(
                        len([ground_truth for _, ground_truth in association.items() if ground_truth is not None]))

        true_positive_per_camera: typing.Dict[PMDCamera, typing.List[float]] = dict()
        false_positive_per_camera: typing.Dict[PMDCamera, typing.List[float]] = dict()
        for camera in PMDCamera:
            true_positive_per_camera[camera] = [associated_gt_slots_per_camera[camera][i]
                                                if tp > 0 else None
                                                for i, tp in
                                                enumerate(number_of_associated_gt_slots_per_camera[camera])]
            # redundant: FP = 1-TP
            false_positive_per_camera[camera] = [(1 - associated_gt_slots_per_camera[camera][i])
                                                 if fp > 0 else None
                                                 for i, fp in
                                                 enumerate(number_of_associated_gt_slots_per_camera[camera])]
            cam_name = PMDReader.get_camera_strings()[camera]
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=[v.timestamp for v in detected_slots[camera]],
                    y=[v for v in true_positive_per_camera[camera]],
                    mode="lines",
                    line=dict(color="green"),
                    name=f"True positive {cam_name} slots",
                )
            )
            alpha = 0.3
            sigma_tp = np.var([v for v in true_positive_per_camera[camera] if v is not None])
            mean_tp = np.mean([v for v in true_positive_per_camera[camera] if v is not None])
            fig.add_trace(
                go.Scatter(
                    x=[v.timestamp for v in detected_slots[camera]],
                    y=[mean_tp - sigma_tp] * len(detected_slots[camera]),
                    mode="lines",
                    line=dict(color=hex_to_rgba('#00ff00', alpha)),
                    name=f"mean of true positive {cam_name} slots",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=[v.timestamp for v in detected_slots[camera]],
                    y=[mean_tp + sigma_tp] * len(detected_slots[camera]),
                    mode="lines",
                    fill='tonexty',
                    fillcolor=hex_to_rgba('#00ff00', alpha),
                    line=dict(color=hex_to_rgba('#00ff00', alpha)),
                    showlegend=False
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=[v.timestamp for v in detected_slots[camera]],
                    y=[v for v in false_positive_per_camera[camera]],
                    mode="lines",
                    line=dict(color="red"),
                    name=f"False positive {cam_name} slots",
                )
            )
            sigma_fp = np.var([v for v in false_positive_per_camera[camera] if v is not None])
            mean_fp = np.mean([v for v in false_positive_per_camera[camera] if v is not None])
            fig.add_trace(
                go.Scatter(
                    x=[v.timestamp for v in detected_slots[camera]],
                    y=[mean_fp - sigma_fp] * len(detected_slots[camera]),
                    mode="lines",
                    line=dict(color=hex_to_rgba('#ff0000', alpha)),
                    name=f"mean of false positive {cam_name} slots",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=[v.timestamp for v in detected_slots[camera]],
                    y=[mean_fp + sigma_fp] * len(detected_slots[camera]),
                    mode="lines",
                    fill='tonexty',
                    fillcolor=hex_to_rgba('#ff0000', alpha),
                    line=dict(color=hex_to_rgba('#ff0000', alpha)),
                    showlegend=False
                )
            )
            fig.layout = go.Layout(
                xaxis=dict(title="Frames [nsec]"),
                yaxis=dict(title="true/false positive ratio [1]"),
                title=dict(text=f"True/False positive ratio of {cam_name}", font_size=36)
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        source_dist: typing.List[str] = ["Slot All"]
        avg_slot_true_positives: typing.List[float] = [
            np.mean([t for tp in true_positive_per_camera.values() for t in tp if t is not None])]
        avg_slot_false_positives: typing.List[float] = [
            np.mean([f for fp in false_positive_per_camera.values() for f in fp if f is not None])]
        num_of_frames: typing.List[float] = [
            len([t for tp in true_positive_per_camera.values() for t in tp if t is not None]) +
            len([f for fp in false_positive_per_camera.values() for f in fp if f is not None])]
        for camera in PMDCamera:
            avg_slot_true_positives.append(np.mean([tp for tp in true_positive_per_camera[camera] if tp is not None]))
            avg_slot_false_positives.append(np.mean([fp for fp in false_positive_per_camera[camera] if fp is not None]))
            source_dist.append(f"Slot {PMDReader.get_camera_strings()[camera]}")
            num_of_frames.append(len([tp for tp in true_positive_per_camera[camera] if tp is not None]) +
                                 len([fp for fp in false_positive_per_camera[camera] if fp is not None]))

        colors_tp = ["green" if d > AssociationConstants.THRESHOLD_SLOT_SCENARIO_TRUE_POSITIVE else "red" for d in
                     avg_slot_true_positives]
        colors_fp = ["green" if d < AssociationConstants.THRESHOLD_SLOT_SCENARIO_FALSE_POSITIVE else "red" for d in
                     avg_slot_false_positives]
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=["Source", "Average True Positive", "Average False Positive", "Number of frames"]),
                    cells=dict(values=[source_dist, avg_slot_true_positives, avg_slot_false_positives, num_of_frames],
                               fill_color=["lightblue", colors_tp, colors_fp, "lightblue"], font=dict(color='white')),
                )
            ]
        )
        remark = "Slot Scenario (perpendicular, parallel, angled) confidence levels are detected by CNN OD."
        signal_summary = {}
        for camera in PMDCamera:
            cam_name = PMDReader.get_camera_strings()[camera]
            sig_cam_name = PMDReader.get_signal_camera_name()[camera]
            sig_name = f"MTA_ADC5.PMSD_{sig_cam_name}_DATA.Slots.parkingSlots[%].parkingScenarioConfidence"
            evaluation_tp = f"True positive rate for Slot {cam_name} scenarios (perpendicular,parallel,angled) > {100 * AssociationConstants.THRESHOLD_SLOT_SCENARIO_TRUE_POSITIVE}%"
            evaluation_fp = f"False positive rate for Slot {cam_name} scenarios (perpendicular,parallel,angled) < {100 * AssociationConstants.THRESHOLD_SLOT_SCENARIO_FALSE_POSITIVE}%"
            is_pass_tp = avg_slot_true_positives[
                             int(camera) + 1] > AssociationConstants.THRESHOLD_SLOT_SCENARIO_TRUE_POSITIVE
            is_pass_fp = avg_slot_false_positives[
                             int(camera) + 1] < AssociationConstants.THRESHOLD_SLOT_SCENARIO_FALSE_POSITIVE
            signal_summary["True positive: " + sig_name] = [evaluation_tp, "PASS" if is_pass_tp else "FAIL"]
            signal_summary["False positive: " + sig_name] = [evaluation_fp, "PASS" if is_pass_fp else "FAIL"]

        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
        plots.insert(0, self.sig_sum)

        plot_titles.append("Average True/False positive")
        plots.append(fig)
        remarks.append("")

        # 0: for all the cameras
        if (avg_slot_true_positives[0] > AssociationConstants.THRESHOLD_SLOT_SCENARIO_TRUE_POSITIVE) and \
                (avg_slot_false_positives[0] < AssociationConstants.THRESHOLD_SLOT_SCENARIO_FALSE_POSITIVE):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL
        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["TBD"],
            fc.TESTCASE_ID: ["TBD"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test case verifies the true/false positive of detected slots."
            ],
            fc.TEST_RESULT: [test_result],
        }
        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = result_df

@verifies("TBD")
@testcase_definition(
    name="SWKPI_CNC_PMSD_KPI_ParkingSlotTruePositive",
    description="This test case verifies the true/false positive of detected slot scenario.",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class FtSlotTruePositive(TestCase):
    """Test Parking Slot Scenario True/False Positive"""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotTruePositive]


def convert_dict_to_pandas(
        signal_summary: dict,
        table_remark="",
        table_title="",
):
    """Converts a dictionary to a Pandas DataFrame and creates an HTML table."""
    # Create a DataFrame from the dictionary
    evaluation_summary = pd.DataFrame(
        {
            "Signal Evaluation": {key: key for key, val in signal_summary.items()},
            "Summary": {key: val[0] for key, val in signal_summary.items()},
            "Verdict": {key: val[1] for key, val in signal_summary.items()},
        }
    )

    # Generate HTML table using build_html_table function
    return fh.build_html_table(evaluation_summary, table_remark, table_title)
