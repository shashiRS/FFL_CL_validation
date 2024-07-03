"""Parking Slot ID Maintenance Test."""

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


import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.ft_slot_helper import FtSlotHelper
from pl_parking.PLP.CEM.inputs.input_CemSlotReader import SlotReader
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import VedodoReader
from pl_parking.PLP.CEM.inputs.input_PsdSlotReader import PSDCamera, PSDSlotReader

SIGNAL_DATA = "PFS_Slot_ID_Maintenance"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot ID Maintenance",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSlotMainID(TestStep):
    """Parking Slot ID Maintenance Test."""

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
        slot_data = SlotReader(reader).convert_to_class()
        psd_data = PSDSlotReader(reader).convert_to_class()
        vedodo_buffer = VedodoReader(reader).convert_to_class()

        if any(reader.as_plain_df["CemSlot_numberOfSlots"].values > 0):
            rows = []
            failed = 0
            for index, curTimeframe in enumerate(slot_data):
                if index == 0:
                    continue
                prevTimeframe = slot_data[index - 1]
                relative_motion_output = vedodo_buffer.calc_relative_motion(
                    curTimeframe.timestamp, prevTimeframe.timestamp
                )

                transformed_prevSlots = [
                    FtSlotHelper.transform_slot(slot, relative_motion_output) for slot in prevTimeframe.parking_slots
                ]

                psd_timeframe_index = [
                    FtSlotHelper.get_PSD_timeframe_index(
                        curTimeframe.timestamp, prevTimeframe.timestamp, psd_data[camera]
                    )
                    for camera in PSDCamera
                ]

                psd_timeframes = [
                    psd_data[camera][psd_timeframe_index[int(camera)]]
                    for camera in PSDCamera
                    if psd_timeframe_index[int(camera)] is not None
                ]

                updatedSlots = FtSlotHelper.get_solts_with_associated_input(transformed_prevSlots, psd_timeframes)

                associations = FtSlotHelper.associate_slot_list(curTimeframe.parking_slots, updatedSlots)

                for prev_ixd, curr_index in associations.items():
                    if updatedSlots[prev_ixd].slot_id != curTimeframe.parking_slots[curr_index].slot_id:
                        failed += 1
                        values = [
                            [curTimeframe.timestamp],
                            [updatedSlots[prev_ixd].slot_id],
                            [curTimeframe.parking_slots[curr_index].slot_id],
                        ]
                        rows.append(values)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Timestamp", "Prev Slot ID", "Curr Slot ID"]), cells=dict(values=values)
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
            fc.REQ_ID: ["1530481"],
            fc.TESTCASE_ID: ["39534"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                """This test checks that EnvironmentFusion maintains the identifier of each parking slot if a parking
                slot detection is received in the current timeframe and can be associated to a parking slot already
                received in previous time frames."""
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


@verifies("1530481")
@testcase_definition(
    name="SWRT_CNC_PFS_ParkingSlotIDMaintenance",
    description="""This test checks that EnvironmentFusion maintains the identifier of each parking slot if a parking
        slot detection is received in the current timeframe and can be associated to a parking slot already
        received in previous time frames.""",
)
class FtSlotMainID(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotMainID]
