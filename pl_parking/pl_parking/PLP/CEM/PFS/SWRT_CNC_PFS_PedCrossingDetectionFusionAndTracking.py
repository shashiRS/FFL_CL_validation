"""Pedestrian Crossing Detection Fusion and Tracking Test."""

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

import pandas as pd

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
from pl_parking.PLP.CEM.inputs.input_CemPedCrossReader import PedCrossReader

SIGNAL_DATA = "PFS_PED_Output"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS Pedestrian Detection Output",
    description="Pedestrian Crossing Detection Fusion and Tracking Test",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPEDOutput(TestStep):
    """Pedestrian Crossing Detection Fusion and Tracking Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step"""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)
        signal_summary = {}
        evaluation = []

        # Note: Signals names to be updated here and in common_ft_helper available.
        try:
            reader = self.readers[SIGNAL_DATA]
            reader.as_plain_df.drop_duplicates(inplace=True)
            ped_reader = PedCrossReader(reader)
            ped_data = ped_reader.convert_to_class()
            psd_ped_data = reader.as_plain_df.filter(regex="PMDPEDCROS_")

            if any(reader.as_plain_df["Cem_numberOfPedCrossings"].values > 0):
                # Get the first TS where there is an input in all cameras
                first_in_ts = min(
                    [
                        psd_ped_data[psd_ped_data["PMDPEDCROS_Front_numberOfCrossings"] > 0][
                            "PMDPEDCROS_Front_timestamp"
                        ].min(),
                        psd_ped_data[psd_ped_data["PMDPEDCROS_Rear_numberOfCrossings"] > 0][
                            "PMDPEDCROS_Rear_timestamp"
                        ].min(),
                        psd_ped_data[psd_ped_data["PMDPEDCROS_Left_numberOfCrossings"] > 0][
                            "PMDPEDCROS_Left_timestamp"
                        ].min(),
                        psd_ped_data[psd_ped_data["PMDPEDCROS_Right_numberOfCrossings"] > 0][
                            "PMDPEDCROS_Right_timestamp"
                        ].min(),
                    ]
                )

                # Get the last TS where there is an output in all cameras
                last_in_ts = max(
                    [
                        psd_ped_data[psd_ped_data["PMDPEDCROS_Front_numberOfCrossings"] > 0][
                            "PMDPEDCROS_Front_timestamp"
                        ].max(),
                        psd_ped_data[psd_ped_data["PMDPEDCROS_Rear_numberOfCrossings"] > 0][
                            "PMDPEDCROS_Rear_timestamp"
                        ].max(),
                        psd_ped_data[psd_ped_data["PMDPEDCROS_Left_numberOfCrossings"] > 0][
                            "PMDPEDCROS_Left_timestamp"
                        ].max(),
                        psd_ped_data[psd_ped_data["PMDPEDCROS_Right_numberOfCrossings"] > 0][
                            "PMDPEDCROS_Right_timestamp"
                        ].max(),
                    ]
                )

                # Calculate delay
                delay = ConstantsCem.SYNC_INPUT_OUTPUT_CYCLES * ConstantsCem.CYCLE_PERIOD_TIME_MS
                first_out_ts = first_in_ts + (delay * 1e3)
                last_out_ts = last_in_ts + (delay * 1e3)

                rows = []
                failed_timestamps = 0
                for _, cur_timeframe in enumerate(ped_data):
                    ped_number = cur_timeframe.number_of_peds
                    cur_timestamp = cur_timeframe.timestamp
                    if cur_timestamp <= first_in_ts:
                        if ped_number != 0:
                            failed_timestamps += 1
                            values = [[cur_timestamp], [ped_number], ["First zone, no input"], ["No output"]]
                            rows.append(values)

                    elif first_in_ts <= cur_timestamp < first_out_ts:
                        if ped_number != 0:
                            failed_timestamps += 1
                            values = [[cur_timestamp], [ped_number], ["Second zone, input available"], ["No output"]]
                            rows.append(values)

                    elif first_out_ts <= cur_timestamp < last_out_ts:
                        if ped_number == 0:
                            failed_timestamps += 1
                            values = [[cur_timestamp], [ped_number], ["Third zone, input available"], ["Output"]]
                            rows.append(values)

                    elif first_out_ts <= cur_timestamp < last_out_ts:
                        if ped_number == 0:
                            failed_timestamps += 1
                            values = [[cur_timestamp], [ped_number], ["Fourth zone, input available"], ["Output"]]
                            rows.append(values)

                    else:
                        if ped_number != 0:
                            failed_timestamps += 1
                            values = [[cur_timestamp], [ped_number], ["Fifth zone, no input"], ["No output"]]
                            rows.append(values)

                if failed_timestamps:
                    test_result = fc.FAIL
                    evaluation = "PFS does not perform the fusion based on incoming pedestrian crossing"
                    "detections and provide a list of tracked Pedestrian Crossings."
                    signal_summary["PedCrossingsDetection_FusionAndTracking"] = evaluation
                else:
                    test_result = fc.PASS
                    evaluation = "PFS shall perform the fusion based on incoming pedestrian crossing "
                    "detections and provide a list of tracked Pedestrian Crossings."
                    signal_summary["PedCrossingsDetection_FusionAndTracking"] = evaluation

                header = ["Timestamp", "Number of output pedestrian", "Evaluation section", "Expected output"]
                values = list(zip(*rows))
                fig = go.Figure(data=[go.Table(header=dict(values=header), cells=dict(values=values))])
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")

                psd_ped_data = psd_ped_data.drop_duplicates()
                psd_ped_data = psd_ped_data.loc[(psd_ped_data["PMDPEDCROS_Front_timestamp"] != 0)]
                psd_ped_data = psd_ped_data.loc[(psd_ped_data["PMDPEDCROS_Rear_timestamp"] != 0)]
                psd_ped_data = psd_ped_data.loc[(psd_ped_data["PMDPEDCROS_Left_timestamp"] != 0)]
                psd_ped_data = psd_ped_data.loc[(psd_ped_data["PMDPEDCROS_Right_timestamp"] != 0)]
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=ped_reader.data["Cem_pedCrossings_timestamp"],
                        y=ped_reader.data["Cem_numberOfPedCrossings"],
                        name="Output",
                    )
                )
                fig.add_vrect(
                    x0=ped_reader.data["timestamp"].iat[0], x1=first_in_ts, fillcolor="#E1F5FE", layer="below"
                )
                fig.add_vrect(x0=first_in_ts, x1=first_out_ts, fillcolor="#BBDEFB", layer="below")
                fig.add_vrect(x0=first_out_ts, x1=last_in_ts, fillcolor="#F5F5F5", layer="below")
                fig.add_vrect(x0=last_in_ts, x1=last_out_ts, fillcolor="#E0E0E0", layer="below")
                fig.add_vrect(
                    x0=last_out_ts,
                    x1=ped_reader.data["Cem_pedCrossings_timestamp"].iat[-1],
                    fillcolor="#F3E5F5",
                    layer="below",
                )
                fig.add_trace(
                    go.Scatter(
                        x=psd_ped_data["PMDPEDCROS_Front_timestamp"],
                        y=psd_ped_data["PMDPEDCROS_Front_numberOfCrossings"],
                        name="psdFront",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=psd_ped_data["PMDPEDCROS_Rear_timestamp"],
                        y=psd_ped_data["PMDPEDCROS_Rear_numberOfCrossings"],
                        name="psdRear",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=psd_ped_data["PMDPEDCROS_Left_timestamp"],
                        y=psd_ped_data["PMDPEDCROS_Left_numberOfCrossings"],
                        name="psdLeft",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=psd_ped_data["PMDPEDCROS_Right_timestamp"],
                        y=psd_ped_data["PMDPEDCROS_Right_numberOfCrossings"],
                        name="psdRight",
                    )
                )

                plots.append(fig)
                plot_titles.append("Evaluated zones (Number of peds)")
                remarks.append("")

            else:
                test_result = fc.INPUT_MISSING
                evaluation = "Required input is missing"
                signal_summary["PedCrossingsDetection_FusionAndTracking"] = evaluation
        except KeyError as err:
            test_result = fc.FAIL
            evaluation = "Key Error " + str(err)
            signal_summary["PedCrossingsDetection_FusionAndTracking"] = evaluation

        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": "PFS shall perform the fusion based on incoming pedestrian crossing "
                    "detections and provide a list of tracked Pedestrian Crossings.",
                },
                "Result": {
                    "1": evaluation,
                },
                "Verdict": {
                    "1": "PASSED" if test_result == "passed" else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PFS Pedestrian Crossing Fusion and Tracking")
        self.result.details["Plots"].append(sig_sum)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2260042"],
            fc.TESTCASE_ID: ["69341"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test case checks if PFS shall perform the fusion based on incoming pedestrian crossing "
                "detections and provide a list of tracked Pedestrian Crossings."
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


@verifies("2260042")
@testcase_definition(
    name="SWRT_CNC_PFS_PedCrossingDetectionFusionAndTracking",
    description="This test case checks if PFS shall perform the fusion based on incoming pedestrian crossing "
    "detections and provide a list of tracked Pedestrian Crossings.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_dXbIpQ1IEe-9Pf5VGwDpVA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
class FtPEDOutput(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPEDOutput]
