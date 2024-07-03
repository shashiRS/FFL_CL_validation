"""Furthest Parking Slots Detected Test."""

import logging

from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
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
from pl_parking.common_ft_helper import CemSignals, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import ConstantsCem
from pl_parking.PLP.CEM.ft_slot_helper import FtSlotHelper
from pl_parking.PLP.CEM.inputs.input_CemSlotReader import Slot, SlotReader
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import VedodoReader

SIGNAL_DATA = "PFS_Detect_Furthest_Slot"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Furthest Slot",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSlotFurthestSlotDeleted(TestStep):
    """Furthest Parking Slots Detected Test."""

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
        reader = self.readers[SIGNAL_DATA].signals
        inputReader = SlotReader(reader)
        vedodo_buffer = VedodoReader(reader).convert_to_class()
        slot_data = inputReader.convert_to_class()
        nbrTimeframes = len(slot_data)

        if any(reader.as_plain_df["CemSlot_numberOfSlots"].values > 0):
            failed = 0
            for i in range(nbrTimeframes - 1):
                prevTimeframe = slot_data[i]
                curTimeframe = slot_data[i + 1]

                relative_motion = vedodo_buffer.calc_relative_motion(prevTimeframe.timestamp, curTimeframe.timestamp)

                missing_slots: typing.List[Slot] = []

                if len(prevTimeframe.parking_slots) > 0 and len(curTimeframe.parking_slots) > 0:
                    if len(curTimeframe.parking_slots) == ConstantsCem.PCL_MAX_NUM_MARKERS:
                        missing_slots = FtSlotHelper.find_missing_slot_ids(prevTimeframe, curTimeframe)

                if len(missing_slots) > 0:
                    _, furthestPclDistance = FtSlotHelper.get_furthest_slot(curTimeframe)

                    for missing_slot in missing_slots:
                        transformed_line = FtSlotHelper.transform_slot(missing_slot, relative_motion)
                        if FtSlotHelper.distance_slot_vehicle(transformed_line) < furthestPclDistance:
                            failed += 1

            if failed:
                test_result = fc.FAIL
                fig = go.Figure(
                    data=[go.Table(header=dict(values=["Number of failed deleted slots"]), cells=dict(values=[failed]))]
                )
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")
            else:
                test_result = fc.PASS

        else:
            test_result = fc.INPUT_MISSING

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1530457"],
            fc.TESTCASE_ID: ["38845"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                f"""This test case checks if CEM deletes the furthest parking slots
                if the number of parking slots is larger than the {ConstantsCem.PSD_MAX_NUM_MARKERS}  limit."""
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


@verifies("1530457")
@testcase_definition(
    name="SWRT_CNC_PFS_FurthestParkingSlotsDeleted",
    description=f"""This test case checks if CEM deletes the furthest parking slots
        if the number of parking slots is larger than the {ConstantsCem.PSD_MAX_NUM_MARKERS}  limit.""",
)
class FtSlotFurthestSlotDeleted(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotFurthestSlotDeleted]
