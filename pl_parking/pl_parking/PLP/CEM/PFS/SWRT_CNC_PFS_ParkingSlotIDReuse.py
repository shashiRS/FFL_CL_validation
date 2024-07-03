"""Parking Slot ID Reuse Test."""

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
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import ConstantsCem
from pl_parking.PLP.CEM.inputs.input_CemSlotReader import SlotReader

SIGNAL_DATA = "PFS_Slot_Id_Reuse"
example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Id Reuse",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSlotIDReuse(TestStep):
    """Parking Slot ID Reuse Test."""

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
        input_reader = SlotReader(reader)
        slot_data = input_reader.convert_to_class()

        observation_times: typing.Dict[int, int] = {}

        if any(reader.as_plain_df["CemSlot_numberOfSlots"].values > 0):
            rows = []
            failed = 0
            for idx, time_frame in enumerate(slot_data):
                for slot in time_frame.parking_slots:
                    if slot.slot_id in observation_times:
                        if not (observation_times[slot.slot_id] == idx - 1) or (
                            observation_times[slot.slot_id] < idx - ConstantsCem.AP_E_SLOT_ID_REUSE_LIMIT_NU
                        ):
                            failed += 1
                            values = [[idx], [observation_times[idx]], [slot.slot_id]]
                            rows.append(values)

                    observation_times[slot.slot_id] = idx

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Cycle count", "Last observation cycle count", "Slot ID"]),
                            cells=dict(values=values),
                        )
                    ]
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
            fc.REQ_ID: ["1530482"],
            fc.TESTCASE_ID: ["38849"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                f"""This test checks that in case CEM stops providing
                a parking slot with a particular ID, the ID is not used again
                for a new Parking Slot for at least {ConstantsCem.AP_E_SLOT_ID_REUSE_LIMIT_NU} cycles."""
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


@verifies("1530482")
@testcase_definition(
    name="SWRT_CNC_PFS_ParkingSlotIDReuse",
    description=f"""This test checks that in case CEM stops providing
        a parking slot with a particular ID, the ID is not used again
        for a new Parking Slot for at least {ConstantsCem.AP_E_SLOT_ID_REUSE_LIMIT_NU} cycles.""",
)
class FtSlotIDReuse(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotIDReuse]
