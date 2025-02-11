"""Parking Slot Accuracy KPI Test."""

import logging

import pandas as pd
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

TRC_ROOT = os.path.abspath(os.path.join(__file__, "", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

import typing

import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import AssociationConstants
from pl_parking.PLP.CEM.ft_slot_helper import FtSlotHelper
from pl_parking.PLP.CEM.inputs.input_CemSlotReader import Slot, SlotGtReader, SlotReader
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import VedodoReader, VedodoTimeframe

SIGNAL_DATA = "PFS_Slot_Accuracy"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Accuracy",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSlotAccuracy(TestStep):
    """Parking Slot Accuracy Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step"""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)
        test_result = fc.NOT_ASSESSED

        reader = self.readers[SIGNAL_DATA].signals
        slot_reader = SlotReader(reader)
        slot_data = slot_reader.convert_to_class()
        slot_gt_reader = SlotGtReader(reader)
        slot_gt_data = slot_gt_reader.convert_erg_to_class()
        vedodo_gt_reader = VedodoReader(reader)
        vedodo_gt_data = vedodo_gt_reader.convert_erg_gt_to_class()

        slot_accuracy: typing.Tuple[typing.List[float], typing.List[int]] = ([], [])
        ego_pose: VedodoTimeframe
        adjusted_slots: typing.List[Slot]

        frame_id = 0

        for time_frame in slot_data:
            ego_pose = vedodo_gt_data.buffer[frame_id]
            if time_frame.number_of_slots > 0 and ego_pose is not None:
                slot_gt_frame = slot_gt_data[frame_id]
                if slot_gt_frame.timestamp > 0:
                    adjusted_slots = FtSlotHelper.slot_to_vehicle(slot_gt_frame.parking_slots, ego_pose)
                    distance, used = FtSlotHelper.calculate_accuracy_correctness(
                        time_frame.parking_slots, adjusted_slots
                    )
                    slot_accuracy[0].append(distance)
                    slot_accuracy[1].append(used)
            frame_id += 1

        if sum(slot_accuracy[1]) > 0:
            average_slot_accuracy = sum(slot_accuracy[0]) / sum(slot_accuracy[1])
            max_slot_accuracy = max(slot_accuracy[0])

            if test_result != fc.FAIL:
                test_result = fc.PASS

            # Set table dataframe
            signal_summary = pd.DataFrame(
                {
                    "Average CEM Accuracy [m]": {
                        "1": average_slot_accuracy
                    },
                    "Max CEM Error [m]": {
                        "1": max_slot_accuracy
                    },
                    "Association  distance [m]": {
                        "1": AssociationConstants.MAX_SLOT_DISTANCE_ERG_KPI
                    },
                }
            )

            sig_sum = fh.build_html_table(signal_summary, table_title="Average scenario accuracy for slots")
            self.result.details["Plots"].append(sig_sum)

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
            fig.add_annotation(
                dict(
                    font=dict(color="black", size=12),
                    x = 0,
                    y = -0.12,
                    showarrow=False,
                    text="CEM Slot Association",
                    textangle=0,
                    xanchor="left",
                    xref="paper",
                    yref="paper",
                )
            )

            plot_titles.append("CEM Slot Association")
            plots.append(fig)

        else:
            test_result = fc.INPUT_MISSING

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: [""],
            fc.TESTCASE_ID: [""],
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


@testcase_definition(
    name="ParkingSlotAccuracy_synthetic_kpi",
    description="This test is used for development to calculate slot accuracy KPI on .erg input (both GT and "
    "measurement).",
)
class FtSlotAccuracy(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotAccuracy]
