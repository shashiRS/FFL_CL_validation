"""Stop Lines Fusion and Tracking Test."""

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
from pl_parking.PLP.CEM.inputs.input_CemPclReader import PclDelimiterReader

SIGNAL_DATA = "PFS_SL_Output"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS SL Output",
    description="This test case checks if PFS performs the fusion based on incoming stop line detections and provide "
    "a list of tracked Stop Lines.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSLOutput(TestStep):
    """Wheel Lockers Fusion and Tracking Test."""

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
        data_df = reader.as_plain_df
        evaluation = [""]

        try:
            sl_data = data_df[
                [
                    "PMDSl_Front_numberOfLines",
                    "PMDSl_Front_timestamp",
                    "PMDSl_Rear_numberOfLines",
                    "PMDSl_Rear_timestamp",
                    "PMDSl_Left_numberOfLines",
                    "PMDSl_Left_timestamp",
                    "PMDSl_Right_numberOfLines",
                    "PMDSl_Right_timestamp",
                ]
            ]

            # Check if there are PM in the data
            data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in data_df.columns]
            pcl_type = data_df.loc[:, data_df.columns.str.startswith("Cem_pcl_delimiterId")]

            # Get the first TS where there is an input in all cameras
            first_in_ts = min(
                [
                    sl_data[sl_data["PMDSl_Front_numberOfLines"] > 0]["PMDSl_Front_timestamp"].min(),
                    sl_data[sl_data["PMDSl_Rear_numberOfLines"] > 0]["PMDSl_Rear_timestamp"].min(),
                    sl_data[sl_data["PMDSl_Left_numberOfLines"] > 0]["PMDSl_Left_timestamp"].min(),
                    sl_data[sl_data["PMDSl_Right_numberOfLines"] > 0]["PMDSl_Right_timestamp"].min(),
                ]
            )

            # Get the last TS where there is an output in all cameras
            last_in_ts = max(
                [
                    sl_data[sl_data["PMDSl_Front_numberOfLines"] > 0]["PMDSl_Front_timestamp"].max(),
                    sl_data[sl_data["PMDSl_Rear_numberOfLines"] > 0]["PMDSl_Rear_timestamp"].max(),
                    sl_data[sl_data["PMDSl_Left_numberOfLines"] > 0]["PMDSl_Left_timestamp"].max(),
                    sl_data[sl_data["PMDSl_Right_numberOfLines"] > 0]["PMDSl_Right_timestamp"].max(),
                ]
            )

            delay = ConstantsCem.SYNC_INPUT_OUTPUT_CYCLES * ConstantsCem.CYCLE_PERIOD_TIME_MS
            first_out_ts = first_in_ts + (delay * 1e3)
            last_out_ts = last_in_ts + (delay * 1e3)

            if not pcl_type.empty:
                rows = []
                failed_timestamps = 0
                for _, cur_timeframe in enumerate(pcl_data):
                    sl_number = len(cur_timeframe.wheel_stopper_array)
                    cur_timestamp = cur_timeframe.timestamp
                    if cur_timestamp <= first_in_ts:
                        if sl_number != 0:
                            failed_timestamps += 1
                            values = [[cur_timestamp], [sl_number], ["First zone, no input SL"], ["No output"]]
                            rows.append(values)

                    elif first_in_ts <= cur_timestamp < first_out_ts:
                        if sl_number != 0:
                            failed_timestamps += 1
                            values = [[cur_timestamp], [sl_number], ["Second zone, input SL"], ["No output"]]
                            rows.append(values)

                    elif first_out_ts <= cur_timestamp < last_in_ts:
                        if sl_number == 0:
                            failed_timestamps += 1
                            values = [[cur_timestamp], [sl_number], ["Third zone, input SL"], ["Output available"]]
                            rows.append(values)

                    elif last_in_ts <= cur_timestamp < last_out_ts:
                        if sl_number == 0:
                            failed_timestamps += 1
                            values = [[cur_timestamp], [sl_number], ["Fourth zone, no input SL"], ["Output available"]]
                            rows.append(values)

                    else:
                        if sl_number != 0:
                            failed_timestamps += 1
                            values = [[cur_timestamp], [sl_number], ["Fifth zone, no input SL"], ["No output"]]
                            rows.append(values)

                if failed_timestamps:
                    test_result = fc.FAIL
                else:
                    test_result = fc.PASS

                header = ["Timestamp", "Number of output SL", "Evaluation section", "Expected result"]
                values = list(zip(*rows))
                fig = go.Figure(data=[go.Table(header=dict(values=header), cells=dict(values=values))])
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")

                sl_front = sl_data[["PMDSl_Front_numberOfLines", "PMDSl_Front_timestamp"]].drop_duplicates()
                sl_front = sl_front.loc[(sl_front["PMDSl_Front_timestamp"] != 0)]
                sl_rear = sl_data[["PMDSl_Rear_numberOfLines", "PMDSl_Rear_timestamp"]].drop_duplicates()
                sl_rear = sl_rear.loc[(sl_rear["PMDSl_Rear_timestamp"] != 0)]
                sl_left = sl_data[["PMDSl_Left_numberOfLines", "PMDSl_Left_timestamp"]].drop_duplicates()
                sl_left = sl_left.loc[(sl_left["PMDSl_Left_timestamp"] != 0)]
                sl_right = sl_data[["PMDSl_Right_numberOfLines", "PMDSl_Right_timestamp"]].drop_duplicates()
                sl_right = sl_right.loc[(sl_right["PMDSl_Right_timestamp"] != 0)]

                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=data_df["Cem_numPclDelimiters_timestamp"], y=data_df["Cem_numPclDelimiters"], name="Output"
                    )
                )
                fig.add_vrect(
                    x0=data_df["Cem_numPclDelimiters_timestamp"].iat[0],
                    x1=first_in_ts,
                    fillcolor="#F3E5F5",
                    layer="below",
                )
                fig.add_vrect(x0=first_in_ts, x1=first_out_ts, layer="below")
                fig.add_vrect(x0=first_out_ts, x1=last_in_ts, fillcolor="#F5F5F5", layer="below")
                fig.add_vrect(x0=last_in_ts, x1=last_out_ts, layer="below")
                fig.add_vrect(
                    x0=last_out_ts,
                    x1=data_df["Cem_numPclDelimiters_timestamp"].iat[-1],
                    fillcolor="#F3E5F5",
                    layer="below",
                )
                fig.add_trace(
                    go.Scatter(
                        x=sl_front["PMDSl_Front_timestamp"], y=sl_front["PMDSl_Front_numberOfLines"], name="sl_front"
                    )
                )
                fig.add_trace(
                    go.Scatter(x=sl_rear["PMDSl_Rear_timestamp"], y=sl_rear["PMDSl_Rear_numberOfLines"], name="sl_rear")
                )
                fig.add_trace(
                    go.Scatter(x=sl_left["PMDSl_Left_timestamp"], y=sl_left["PMDSl_Left_numberOfLines"], name="sl_left")
                )
                fig.add_trace(
                    go.Scatter(
                        x=sl_right["PMDSl_Right_timestamp"], y=sl_right["PMDSl_Right_numberOfLines"], name="sl_right"
                    )
                )
                plots.append(fig)
                plot_titles.append("Evaluated zones (Number of Wheel stoppers)")
                remarks.append("")

            else:
                test_result = fc.INPUT_MISSING
        except KeyError as err:
            test_result = fc.FAIL
            evaluation[0] = str(err)
            signal_summary["Detected_StopLines"] = evaluation[0]

        if evaluation is not None:
            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(values=["Signal Evaluation", "Summary"]),
                        cells=dict(values=[list(signal_summary.keys()), list(signal_summary.values())]),
                    )
                ]
            )

            plot_titles.append("Signal Evaluation")
            plots.append(fig)
            remarks.append("PFS Evaluation")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2260034"],
            fc.TESTCASE_ID: ["64796"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test case checks if PFS performs the fusion based on incoming stop line detections and provide "
                "a list of tracked Stop Lines."
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


@verifies("2260034")
@testcase_definition(
    name="SWRT_CNC_PFS_StopLinesFusionAndTracking",
    description="This test case checks if PFS performs Fusion of StopLines based on detections of StopLines.",
)
class FtSLOutput(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSLOutput]
