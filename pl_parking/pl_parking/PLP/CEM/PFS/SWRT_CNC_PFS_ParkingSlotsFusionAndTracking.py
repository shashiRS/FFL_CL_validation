"""Parking Slots Fusion and Tracking Test."""

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
from pl_parking.PLP.CEM.constants import ConstantsCem
from pl_parking.PLP.CEM.inputs.input_CemSlotReader import SlotReader

SIGNAL_DATA = "PFS_Slot_Output"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS Slot Output",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSlotOutput(TestStep):
    """Parking Slots Fusion and Tracking Test."""

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
        reader.as_plain_df.drop_duplicates(inplace=True)
        slot_reader = SlotReader(reader)
        slot_data = slot_reader.convert_to_class()

        psd_data = reader.as_plain_df.filter(regex="PsdSlot_")

        if any(reader.as_plain_df["CemSlot_numberOfSlots"].values > 0):
            # Get the first TS where there is an input in all cameras
            first_in_ts = min(
                [
                    psd_data[psd_data["PsdSlot_Front_numberOfSlots"] > 0]["PsdSlot_Front_timestamp"].min(),
                    psd_data[psd_data["PsdSlot_Rear_numberOfSlots"] > 0]["PsdSlot_Rear_timestamp"].min(),
                    psd_data[psd_data["PsdSlot_Left_numberOfSlots"] > 0]["PsdSlot_Left_timestamp"].min(),
                    psd_data[psd_data["PsdSlot_Right_numberOfSlots"] > 0]["PsdSlot_Right_timestamp"].min(),
                ]
            )

            # Get the last TS where there is an output in all cameras
            last_in_ts = max(
                [
                    psd_data[psd_data["PsdSlot_Front_numberOfSlots"] > 0]["PsdSlot_Front_timestamp"].max(),
                    psd_data[psd_data["PsdSlot_Rear_numberOfSlots"] > 0]["PsdSlot_Rear_timestamp"].max(),
                    psd_data[psd_data["PsdSlot_Left_numberOfSlots"] > 0]["PsdSlot_Left_timestamp"].max(),
                    psd_data[psd_data["PsdSlot_Right_numberOfSlots"] > 0]["PsdSlot_Right_timestamp"].max(),
                ]
            )

            # Calculate delay
            delay = ConstantsCem.SYNC_INPUT_OUTPUT_CYCLES * ConstantsCem.CYCLE_PERIOD_TIME_MS
            first_out_ts = first_in_ts + (delay * 1e3)
            last_out_ts = last_in_ts + (delay * 1e3)

            rows = []
            failed_timestamps = 0
            for _, cur_timeframe in enumerate(slot_data):
                slots_number = cur_timeframe.number_of_slots
                cur_timestamp = cur_timeframe.timestamp
                if cur_timestamp <= first_in_ts:
                    if slots_number != 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [slots_number], ["First zone, no input"], ["No output"]]
                        rows.append(values)

                elif first_in_ts <= cur_timestamp < first_out_ts:
                    if slots_number != 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [slots_number], ["Second zone, input available"], ["No output"]]
                        rows.append(values)

                elif first_out_ts <= cur_timestamp < last_out_ts:
                    if slots_number == 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [slots_number], ["Third zone, input available"], ["Output"]]
                        rows.append(values)

                elif first_out_ts <= cur_timestamp < last_out_ts:
                    if slots_number == 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [slots_number], ["Fourth zone, input available"], ["Output"]]
                        rows.append(values)

                else:
                    if slots_number != 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [slots_number], ["Fifth zone, no input"], ["No output"]]
                        rows.append(values)

            if failed_timestamps:
                test_result = fc.FAIL
            else:
                test_result = fc.PASS

            header = ["Timestamp", "Number of output slots", "Evaluation section", "Expected output"]
            values = list(zip(*rows))
            fig = go.Figure(data=[go.Table(header=dict(values=header), cells=dict(values=values))])
            plot_titles.append("Test Fail report")
            plots.append(fig)
            remarks.append("")

            psd_data = psd_data.drop_duplicates()
            psd_data = psd_data.loc[(psd_data["PsdSlot_Front_timestamp"] != 0)]
            psd_data = psd_data.loc[(psd_data["PsdSlot_Rear_timestamp"] != 0)]
            psd_data = psd_data.loc[(psd_data["PsdSlot_Left_timestamp"] != 0)]
            psd_data = psd_data.loc[(psd_data["PsdSlot_Right_timestamp"] != 0)]
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=slot_reader.data["CemSlot_timestamp"], y=slot_reader.data["CemSlot_numberOfSlots"], name="Output"
                )
            )
            fig.add_vrect(x0=slot_reader.data["timestamp"].iat[0], x1=first_in_ts, fillcolor="#E1F5FE", layer="below")
            fig.add_vrect(x0=first_in_ts, x1=first_out_ts, fillcolor="#BBDEFB", layer="below")
            fig.add_vrect(x0=first_out_ts, x1=last_in_ts, fillcolor="#F5F5F5", layer="below")
            fig.add_vrect(x0=last_in_ts, x1=last_out_ts, fillcolor="#E0E0E0", layer="below")
            fig.add_vrect(
                x0=last_out_ts, x1=slot_reader.data["CemSlot_timestamp"].iat[-1], fillcolor="#F3E5F5", layer="below"
            )
            fig.add_trace(
                go.Scatter(
                    x=psd_data["PsdSlot_Front_timestamp"], y=psd_data["PsdSlot_Front_numberOfSlots"], name="psdFront"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=psd_data["PsdSlot_Rear_timestamp"], y=psd_data["PsdSlot_Rear_numberOfSlots"], name="psdRear"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=psd_data["PsdSlot_Left_timestamp"], y=psd_data["PsdSlot_Left_numberOfSlots"], name="psdLeft"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=psd_data["PsdSlot_Right_timestamp"], y=psd_data["PsdSlot_Right_numberOfSlots"], name="psdRight"
                )
            )

            plots.append(fig)
            plot_titles.append("Evaluated zones (Number of slots)")
            remarks.append("")

        else:
            test_result = fc.INPUT_MISSING

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1530478"],
            fc.TESTCASE_ID: ["38777"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                """This test case checks if PFS performs the fusion based on incoming parking slot
                detections and provide a list of tracked Parking Slots."""
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


@verifies("1530478")
@testcase_definition(
    name="SWRT_CNC_PFS_ParkingSlotsFusionAndTracking",
    description="""This test case checks if PFS performs the fusion based on incoming parking slot
        detections and provide a list of tracked Parking Slots.""",
)
class FtSlotOutput(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSlotOutput]
