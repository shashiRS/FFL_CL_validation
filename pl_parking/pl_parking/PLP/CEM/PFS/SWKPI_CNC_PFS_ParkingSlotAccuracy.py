"""Parking Slot Accuracy KPI Test."""

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


import math
import typing

import pandas as pd
import plotly.graph_objects as go
from tsf.core.common import PathSpecification
from tsf.io.sideload import JsonSideLoad

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import AssociationConstants
from pl_parking.PLP.CEM.ft_slot_helper import FtSlotHelper
from pl_parking.PLP.CEM.inputs.input_CemSlotReader import SlotReader
from pl_parking.PLP.CEM.inputs.input_PmdSlotReader import PMDSlotReader

SIGNAL_DATA = "PFS_Slot_Accuracy"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Accuracy",
    description="This teststep checks that in average CEM doesn't provide worse position for the parking slots "
    "than each input separately.",
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
class TestStepFtSlotAccuracy(TestStep):
    """Parking Slot Accuracy Test."""

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
        test_result = fc.NOT_ASSESSED

        reader = self.readers[SIGNAL_DATA].signals
        slot_reader = SlotReader(reader)
        slot_data = slot_reader.convert_to_class()

        psd_reader = PMDSlotReader(reader)
        psd_data = psd_reader.convert_to_class()
        # Load GT data
        gt_data = self.side_load["JsonGt"]
        park_marker_gt = FtSlotHelper.get_slot_from_json_gt(gt_data)
        slot_accuracy: typing.Tuple[typing.List[float], typing.List[int]] = ([], [])

        for time_frame in slot_data:
            target_timestamp = min(park_marker_gt.keys(), key=lambda k: abs(float(k) - time_frame.timestamp))
            gt_with_closest_timestamp = park_marker_gt.get(target_timestamp)
            distance, used = FtSlotHelper.calculate_accuracy_correctness(
                time_frame.parking_slots, gt_with_closest_timestamp
            )
            slot_accuracy[0].append(distance)
            slot_accuracy[1].append(used)

        psd_accuracy: typing.List[typing.Tuple[typing.List[float], typing.List[int]]] = [
            ([], []),
            ([], []),
            ([], []),
            ([], []),
        ]

        for camera, data in psd_data.items():
            for time_frame in data:
                target_timestamp = min(park_marker_gt.keys(), key=lambda k: abs(float(k) - time_frame.timestamp))
                gt_with_closest_timestamp = park_marker_gt.get(target_timestamp)
                conf, used = FtSlotHelper.calculate_accuracy_correctness(
                    time_frame.parking_slots, gt_with_closest_timestamp
                )
                psd_accuracy[int(camera)][0].append(conf)
                psd_accuracy[int(camera)][1].append(used)

        if sum(slot_accuracy[1]) > 0:
            average_slot_accuracy = sum(slot_accuracy[0]) / sum(slot_accuracy[1])
            average_psd_accuracy = [sum(acc[0]) / sum(acc[1]) if sum(acc[1]) > 0 else math.inf for acc in psd_accuracy]

            for psd_acc in average_psd_accuracy:
                if psd_acc < average_slot_accuracy:
                    test_result = fc.FAIL
                    evaluation = (
                        "In average, PFS provides worse position for the parking slots than each input separately"
                    )
                    signal_summary["PFS_Slot_accuracy"] = evaluation

            if test_result != fc.FAIL:
                test_result = fc.PASS
                evaluation = (
                    "In average, PFS doesn't provide worse position for the parking slots than each input separately."
                )
                signal_summary["PFS_Slot_accuracy"] = evaluation

            # Create info graphs
            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(values=["Camera", "For PSD [m]", "For CEM [m]", "Association  distance [m]"]),
                        cells=dict(
                            values=[
                                psd_reader.camera_names,
                                average_psd_accuracy,
                                [average_slot_accuracy],
                                [AssociationConstants.MAX_SLOT_DISTANCE],
                            ]
                        ),
                    )
                ]
            )
            fig.layout = go.Layout(title=dict(text="Average scenario accuracy for slots", font_size=20))
            plot_titles.append("Average scenario accuracy for slots")
            plots.append(fig)
            remarks.append("")

            off = len(slot_data) - len(slot_accuracy[1])

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=slot_reader.data["CemSlot_timestamp"][off - 1 : -1],
                    y=slot_reader.data["CemSlot_numberOfSlots"][off - 1 : -1],
                    mode="lines",
                    name="CEM outputted slot",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=slot_reader.data["CemSlot_timestamp"][off - 1 : -1],
                    y=slot_accuracy[1],
                    mode="lines",
                    name="Associated CEM Slots",
                )
            )
            fig.layout = go.Layout(
                xaxis=dict(title="Timestamp [nsec]"),
                yaxis=dict(title="Slot accuracy"),
                title=dict(text="CEM Slot Association", font_size=20),
            )

            plot_titles.append("CEM Slot Association")
            plots.append(fig)
            remarks.append("")

            off = len(psd_data) - len(psd_accuracy[0][1])

            for i in range(4):
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=psd_reader.data["PmsdSlot_" + psd_reader.camera_names[i] + "_timestamp"][off - 1 : -1],
                        y=psd_reader.data["PmsdSlot_" + psd_reader.camera_names[i] + "_numberOfSlots"][off - 1 : -1],
                        mode="lines",
                        name=f"PSD {psd_reader.camera_names[i]} camera outputted slot",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=psd_reader.data["PmsdSlot_" + psd_reader.camera_names[i] + "_timestamp"][off - 1 : -1],
                        y=psd_accuracy[i][1],
                        mode="lines",
                        name=f"PSD {psd_reader.camera_names[i]} camera associated slot",
                    )
                )
                fig.layout = go.Layout(
                    xaxis=dict(title="Timestamp [nsec]"),
                    yaxis=dict(title="Psd accuracy"),
                    title=dict(text=f"PSD {psd_reader.camera_names[i]} camera Slot Association", font_size=20),
                )
                plot_titles.append(f"PSD {psd_reader.camera_names[i]} camera Slot Association")
                plots.append(fig)
                remarks.append("")

        else:
            test_result = fc.INPUT_MISSING
            evaluation = "Required input is missing"
            signal_summary["PFS_Slot_accuracy"] = evaluation

        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": "EnvironmentFusion in average doesn't provide worse position for the parking slots than each input separately.",
                },
                "Result": {
                    "1": evaluation,
                },
                "Verdict": {
                    "1": "PASSED" if test_result == "passed" else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PFS Parking slots accuracy")
        self.result.details["Plots"].append(sig_sum)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1530479"],
            fc.TESTCASE_ID: ["38848"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test case verifies that, in average CEM doesn't provide worse position for the parking slots "
                "than each input separately."
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


@verifies("1530479")
@testcase_definition(
    name="SWKPI_CNC_PFS_ParkingSlotAccuracy",
    description="This test case verifies that, in average CEM doesn't provide worse position for the parking slots "
    "than each input separately.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_r9kffU4mEe6M5-WQsF_-tQ&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36325",
)
@register_inputs("/parking")
class FtSlotAccuracy(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotAccuracy]
