"""Parking Slot Scenario Confidence KPI Test."""

import logging

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

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

import pandas as pd

TRC_ROOT = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


import numpy as np
import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.ft_helper import generate_html_fraction, hex_to_rgba, load_json
from pl_parking.PLP.CEM.constants import AssociationConstants
from pl_parking.PLP.CEM.ft_slot_helper import FtSlotHelper
from pl_parking.PLP.CEM.inputs.input_CemSlotReader import SlotReader

SIGNAL_DATA = "PFS_Slot_Scenario_Confidence"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Scenario Confidence TP/FP rate",
    description="Calculate the true positive rate of pfs parking slot scenario confidences. It also calculates the false positive rate.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
# This part of code should be commented if running locally because it refers to Caedge GT path.
@register_side_load(
    alias="JsonGt",
    side_load=JsonSideLoad,
    path_spec=PathSpecification(folder=r"s3://par230-prod-data-lake-sim/gt_labels", extension=".json", s3=True),
)
class TestStepFtSlotScenarioConfidence(TestStep):
    """Parking Slot Scenario Confidence KPI Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step"""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarsk based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)
        test_result = fc.NOT_ASSESSED

        reader = self.readers[SIGNAL_DATA].signals
        slot_reader = SlotReader(reader)
        detected_slots = slot_reader.convert_to_class()
        # Local GT data path
        gt_json = os.path.join(TSF_BASE, "data", "CEM_json_gt", "JsonGt.json")
        gt_data = load_json(gt_json) if os.path.exists(gt_json) else self.side_load["JsonGt"]

        slot_gt = FtSlotHelper.get_slot_from_json_gt(gt_data)
        associated_gt_slots = []
        number_of_associated_gt_slots = []
        number_of_gt_slots = []
        number_of_detected_slots = []

        for detected_slot in detected_slots:
            number_of_detected_slots.append(detected_slot.number_of_slots)
            target_timestamp = min(slot_gt.keys(), key=lambda k: abs(float(k) - detected_slot.timestamp))
            gt_with_closest_timestamp = slot_gt.get(target_timestamp)

            if not all(detected_slot.timestamp == int(v.slot_timestamp) for v in gt_with_closest_timestamp):
                number_of_associated_gt_slots.append(0)
                associated_gt_slots.append(0)
                number_of_gt_slots.append(-1)
            elif detected_slot.number_of_slots < 1:
                associated_gt_slots.append(0)
                # Number of gt slots associated to detected slots
                number_of_associated_gt_slots.append(0)
                number_of_gt_slots.append(len(slot_gt[str(int(detected_slot.timestamp))]))
            else:
                number_of_gt_slots.append(len(slot_gt[str(int(detected_slot.timestamp))]))
                association = FtSlotHelper.associate_slot_list(
                    detected_slot.parking_slots,
                    gt_with_closest_timestamp,
                )
                associated_distances = []
                if association:
                    for asso in association.items():

                        gt_i, pcl_i = asso
                        detected_scenario = FtSlotHelper.get_slot_scenario(detected_slot.parking_slots[pcl_i])
                        gt_scenario = FtSlotHelper.get_slot_scenario(gt_with_closest_timestamp[gt_i])

                        if detected_scenario == gt_scenario:
                            associated_distances.append(1)
                        else:
                            associated_distances.append(0)

                    associated_gt_slots.append(np.mean(associated_distances) if len(associated_distances) > 0 else 0)
                    number_of_associated_gt_slots.append(
                        len([ground_truth for _, ground_truth in association.items() if ground_truth is not None])
                    )

        true_positive_rate = [
            associated_gt_slots[i] if tp > 0 else None for i, tp in enumerate(number_of_associated_gt_slots)
        ]

        # redundant: FP = 1-TP
        false_positive_rate = [
            (1 - associated_gt_slots[i]) if fp > 0 else None for i, fp in enumerate(number_of_associated_gt_slots)
        ]

        mean_tp = np.mean([v for v in true_positive_rate if v is not None])
        mean_fp = np.mean([v for v in false_positive_rate if v is not None])

        # Compute true positive results based on the max threshold
        if mean_tp * 100 > AssociationConstants.THRESHOLD_SLOT_SCENARIO_TRUE_POSITIVE:
            tpr_result_value = True
            TPR_description = f"The test has <b>PASSED</b> with the TPR {mean_tp*100:.3f}[%] (>= {AssociationConstants.THRESHOLD_SLOT_SCENARIO_TRUE_POSITIVE}[%])."
        else:
            tpr_result_value = False
            TPR_description = (
                f"The test has <b>FAILED</b> with the TPR {mean_tp*100:.3f}[%] being "
                f"less than the given threshold: {AssociationConstants.THRESHOLD_SLOT_SCENARIO_TRUE_POSITIVE}[%]."
            )

        # Compute false positive results based on the max threshold
        if mean_fp * 100 < AssociationConstants.THRESHOLD_SLOT_SCENARIO_FALSE_POSITIVE:
            fpr_result_value = True
            FPR_description = f"The test has <b>PASSED</b> with the FPR {mean_fp*100:.3f}[%] (<= {AssociationConstants.THRESHOLD_SLOT_SCENARIO_FALSE_POSITIVE}[%])."
        else:
            fpr_result_value = False
            FPR_description = (
                f"The test has <b>FAILED</b> with the FPR {mean_fp*100:.3f}[%] being "
                f"more than the given threshold: {AssociationConstants.THRESHOLD_SLOT_SCENARIO_FALSE_POSITIVE}[%]."
            )

        num_of_frames = len([tp for tp in true_positive_rate if tp is not None])
        data = {
            "TPR": [f"{mean_tp*100:.3f}" + "[%]"],
            "FPR": [f"{mean_fp*100:.3f}" + "[%]"],
            "Number of Frames": num_of_frames,
        }
        average_kpis_df = pd.DataFrame(data)
        plot_titles.append("")
        plots.append(fh.build_html_table(average_kpis_df))
        remarks.append("")

        # Plot summary table of true positive and false positive
        summary_data = pd.DataFrame(
            {
                "KPI": {"1": "TPR", "2": "FPR"},
                "Description": {"1": TPR_description, "2": FPR_description},
                "Verdict": {"1": tpr_result_value, "2": fpr_result_value},
            }
        )
        sig_sum = fh.build_html_table(summary_data, table_title="Parking Slots Scenario TPR/FPR")
        self.result.details["Plots"].append(sig_sum)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=[v.timestamp for v in detected_slots],
                y=[v for v in true_positive_rate],
                mode="lines",
                line=dict(color="green"),
                name="True positive slots",
            )
        )

        alpha = 0.3
        mean_tp = np.mean([v for v in true_positive_rate if v is not None])

        fig.add_trace(
            go.Scatter(
                x=[v.timestamp for v in detected_slots],
                y=[mean_tp] * len(detected_slots),
                mode="lines",
                line=dict(color=hex_to_rgba("#00ff00", alpha)),
                name="mean of true positive slots",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[v.timestamp for v in detected_slots],
                y=[v for v in false_positive_rate],
                mode="lines",
                line=dict(color="red"),
                name="False positive slots",
            )
        )
        mean_fp = np.mean([v for v in false_positive_rate if v is not None])
        fig.add_trace(
            go.Scatter(
                x=[v.timestamp for v in detected_slots],
                y=[mean_fp] * len(detected_slots),
                mode="lines",
                line=dict(color=hex_to_rgba("#ff0000", alpha)),
                name="mean of false positive slots",
            )
        )

        fig.layout = go.Layout(
            xaxis=dict(title="Timestamp [nsec]"),
            yaxis=dict(title="true/false positive ratio [1]"),
            title=dict(text="True/False positive ratio", font_size=36),
        )
        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

        test_result = fc.PASS if tpr_result_value else fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["TBD"],
            fc.TESTCASE_ID: ["TBD"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: ["This test case verifies the true positive of Slot Scenario Confidences."],
            fc.TEST_RESULT: [test_result],
        }

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

        kpi_description = "<h3>Description</h3>"  # Title of the description
        kpi_formulas = ""  # Formulas for KPIs
        kpi_formulas += generate_html_fraction("TPR", ["TP"], ["TP", "FP", "FN"])
        kpi_formulas += generate_html_fraction("FPR", ["FP"], ["TP", "FP", "FN"])
        kpi_legend = ""  # Definition
        kpi_legend += "<p>TPR - True Positive Rate (correctly detected occupied slots)</p>"
        kpi_legend += "<p>FPR - False Positive Rate (incorrectly detected occupied slots)</p>"
        kpi_legend += "<p>TP - Number of True Positive. detected == True and gt == True</p>"
        kpi_legend += "<p>FP - Number of False Positive. detected == True and gt == False </p>"
        kpi_description += kpi_formulas
        kpi_description += kpi_legend
        self.result.details["Plots"].append(kpi_description)


@verifies("TBD")
@testcase_definition(
    name="SWKPI_CNC_PFS_SlotScenarioConfidenceTPR",
    description="This test case verifies calculates the true positive rate and false positive rates for pfs parking slots scenario confidences.",
)
@register_inputs("/parking")
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class FtSlotScenarioConfidence(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""  # example of required docstring
        return [TestStepFtSlotScenarioConfidence]  # in this list all the needed test steps are included
