"""Parking Marker Fusion and Tracking Test."""

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
from pl_parking.PLP.CEM.constants import ConstantsCem, ConstantsCemInput
from pl_parking.PLP.CEM.inputs.input_CemPclReader import PclDelimiterReader

SIGNAL_DATA = "PFS_PCL_Output"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS PCL Output",
    description="This test case checks if PFS performs the fusion based on incoming parking marker detections"
    "and provide a list of tracked Parking Markers.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPCLOutput(TestStep):
    """Parking Marker Fusion and Tracking Test."""

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
        pcl_data = PclDelimiterReader(reader).convert_to_class()
        data_df = reader.as_plain_df
        pmd_data = data_df[
            [
                "PMDCamera_Front_numberOfLines",
                "PMDCamera_Front_timestamp",
                "PMDCamera_Rear_numberOfLines",
                "PMDCamera_Rear_timestamp",
                "PMDCamera_Left_numberOfLines",
                "PMDCamera_Left_timestamp",
                "PMDCamera_Right_numberOfLines",
                "PMDCamera_Right_timestamp",
            ]
        ]

        # Check if there are PM in the data
        data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in data_df.columns]
        pcl_type = data_df.loc[:, data_df.columns.str.startswith("delimiterType")]

        # Get the first TS where there is an input in all cameras
        first_in_ts = min(
            [
                pmd_data[pmd_data["PMDCamera_Front_numberOfLines"] > 0]["PMDCamera_Front_timestamp"].min(),
                pmd_data[pmd_data["PMDCamera_Rear_numberOfLines"] > 0]["PMDCamera_Rear_timestamp"].min(),
                pmd_data[pmd_data["PMDCamera_Left_numberOfLines"] > 0]["PMDCamera_Left_timestamp"].min(),
                pmd_data[pmd_data["PMDCamera_Right_numberOfLines"] > 0]["PMDCamera_Right_timestamp"].min(),
            ]
        )

        # Get the last TS where there is an output in all cameras
        last_in_ts = max(
            [
                pmd_data[pmd_data["PMDCamera_Front_numberOfLines"] > 0]["PMDCamera_Front_timestamp"].max(),
                pmd_data[pmd_data["PMDCamera_Rear_numberOfLines"] > 0]["PMDCamera_Rear_timestamp"].max(),
                pmd_data[pmd_data["PMDCamera_Left_numberOfLines"] > 0]["PMDCamera_Left_timestamp"].max(),
                pmd_data[pmd_data["PMDCamera_Right_numberOfLines"] > 0]["PMDCamera_Right_timestamp"].max(),
            ]
        )

        # Calculate delay
        delay = ConstantsCem.SYNC_INPUT_OUTPUT_CYCLES * ConstantsCem.CYCLE_PERIOD_TIME_MS
        first_out_ts = first_in_ts + (delay * 1e3)
        last_out_ts = last_in_ts + (delay * 1e3)

        if ConstantsCemInput.PCLEnum in pcl_type.values:
            rows = []
            failed_timestamps = 0
            for _, cur_timeframe in enumerate(pcl_data):
                pcl_number = len(cur_timeframe.pcl_delimiter_array)
                cur_timestamp = cur_timeframe.timestamp
                if cur_timestamp <= first_in_ts:
                    if pcl_number != 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [pcl_number], ["First zone, no input marker"], ["No output"]]
                        rows.append(values)

                elif first_in_ts <= cur_timestamp < first_out_ts:
                    if pcl_number != 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [pcl_number], ["Second zone, input markers"], ["No output"]]
                        rows.append(values)

                elif first_out_ts <= cur_timestamp < last_in_ts:
                    if pcl_number == 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [pcl_number], ["Third zone, input markers"], ["Output available"]]
                        rows.append(values)

                elif last_in_ts <= cur_timestamp < last_out_ts:
                    if pcl_number == 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [pcl_number], ["Fourth zone, no input marker"], ["Output available"]]
                        rows.append(values)

                else:
                    if pcl_number != 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [pcl_number], ["Fifth zone, no input markers"], ["No output"]]
                        rows.append(values)

            if failed_timestamps:
                test_result = fc.FAIL
            else:
                test_result = fc.PASS

            # Plots
            header = ["Timestamp", "Number of output markers", "Evaluation section", "Expected result"]
            values = list(zip(*rows))
            fig = go.Figure(data=[go.Table(header=dict(values=header), cells=dict(values=values))])
            plot_titles.append("Test Fail report")
            plots.append(fig)
            remarks.append("")

            pmd_front = pmd_data[["PMDCamera_Front_numberOfLines", "PMDCamera_Front_timestamp"]].drop_duplicates()
            pmd_front = pmd_front.loc[(pmd_front["PMDCamera_Front_timestamp"] != 0)]
            pmd_rear = pmd_data[["PMDCamera_Rear_numberOfLines", "PMDCamera_Rear_timestamp"]].drop_duplicates()
            pmd_rear = pmd_rear.loc[(pmd_rear["PMDCamera_Rear_timestamp"] != 0)]
            pmd_left = pmd_data[["PMDCamera_Left_numberOfLines", "PMDCamera_Left_timestamp"]].drop_duplicates()
            pmd_left = pmd_left.loc[(pmd_left["PMDCamera_Left_timestamp"] != 0)]
            pmd_right = pmd_data[["PMDCamera_Right_numberOfLines", "PMDCamera_Right_timestamp"]].drop_duplicates()
            pmd_right = pmd_right.loc[(pmd_right["PMDCamera_Right_timestamp"] != 0)]

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(x=data_df["numPclDelimiters_timestamp"], y=data_df["numPclDelimiters"], name="Output")
            )
            fig.add_vrect(
                x0=data_df["numPclDelimiters_timestamp"].iat[0], x1=first_in_ts, fillcolor="#F3E5F5", layer="below"
            )
            fig.add_vrect(x0=first_in_ts, x1=first_out_ts, layer="below")
            fig.add_vrect(x0=first_out_ts, x1=last_in_ts, fillcolor="#F5F5F5", layer="below")
            fig.add_vrect(x0=last_in_ts, x1=last_out_ts, layer="below")
            fig.add_vrect(
                x0=last_out_ts, x1=data_df["numPclDelimiters_timestamp"].iat[-1], fillcolor="#F3E5F5", layer="below"
            )
            fig.add_trace(
                go.Scatter(
                    x=pmd_front["PMDCamera_Front_timestamp"],
                    y=pmd_front["PMDCamera_Front_numberOfLines"],
                    name="pmd_front",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=pmd_rear["PMDCamera_Rear_timestamp"], y=pmd_rear["PMDCamera_Rear_numberOfLines"], name="pmd_rear"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=pmd_left["PMDCamera_Left_timestamp"], y=pmd_left["PMDCamera_Left_numberOfLines"], name="pmd_left"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=pmd_right["PMDCamera_Right_timestamp"],
                    y=pmd_right["PMDCamera_Right_numberOfLines"],
                    name="pmd_right",
                )
            )
            plots.append(fig)
            plot_titles.append("Evaluated zones")
            remarks.append("")

        else:
            test_result = fc.INPUT_MISSING

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1530455"],
            fc.TESTCASE_ID: ["38841"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test case checks if PFS performs the fusion based on incoming parking marker detections"
                "and provide a list of tracked Parking Markers."
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


@verifies("1530455")
@testcase_definition(
    name="SWRT_CNC_PFS_ParkingMarkerFusionAndTracking",
    description="This test case checks if PFS performs the fusion based on incoming parking marker detections"
    "and provide a list of tracked Parking Markers.",
)
class FtPCLOutput(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPCLOutput]
