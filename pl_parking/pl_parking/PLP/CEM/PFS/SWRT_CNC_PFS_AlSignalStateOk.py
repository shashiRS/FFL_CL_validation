"""AI Signal State OK Test."""

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
from pl_parking.PLP.CEM.inputs.input_PmdReader import PMDCamera

SIGNAL_DATA = "PFS_Al_Signal_State"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM-PFS Al Signal State",
    description="This test case checks if PFS only processes input signals if their signal state is AL_SIG_STATE_OK",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPCLAlSignalState(TestStep):
    """Test AI Signal State ok"""

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
        df = reader.as_plain_df

        # Output df
        pcl_data = df[["numPclDelimiters_timestamp", "Pcl_eSigStatus", "numPclDelimiters"]]
        slot_data = df[["CemSlot_timestamp", "CemSlot_eSigStatus", "CemSlot_numberOfSlots"]]
        # TODO: Empty cycles at the beginning of data ts=0 check if reset signal resets timestamps to apply filter
        # Input df
        pmd_data = df[
            [
                "PMDCamera_Front_timestamp",
                "PMDCamera_Front_eSigStatus",
                "PMDCamera_Front_numberOfLines",
                "PMDCamera_Rear_timestamp",
                "PMDCamera_Rear_eSigStatus",
                "PMDCamera_Rear_numberOfLines",
                "PMDCamera_Left_timestamp",
                "PMDCamera_Left_eSigStatus",
                "PMDCamera_Left_numberOfLines",
                "PMDCamera_Right_timestamp",
                "PMDCamera_Right_eSigStatus",
                "PMDCamera_Right_numberOfLines",
            ]
        ]
        wsd_data = df[
            [
                "CemWs_Front_timestamp",
                "CemWs_Front_eSigStatus",
                "CemWs_Front_numberOfLines",
                "CemWs_Rear_timestamp",
                "CemWs_Rear_eSigStatus",
                "CemWs_Rear_numberOfLines",
                "CemWs_Left_timestamp",
                "CemWs_Left_eSigStatus",
                "CemWs_Left_numberOfLines",
                "CemWs_Right_timestamp",
                "CemWs_Right_eSigStatus",
                "CemWs_Right_numberOfLines",
            ]
        ]
        # TODO: Signal status for all bsigs not available update common_ft_helper
        psd_data = df[
            [
                "PsdSlot_Front_timestamp",
                "PsdSlot_Front_eSigStatus",
                "PsdSlot_Front_numberOfSlots",
                "PsdSlot_Rear_timestamp",
                "PsdSlot_Rear_eSigStatus",
                "PsdSlot_Rear_numberOfSlots",
                "PsdSlot_Left_timestamp",
                "PsdSlot_Left_eSigStatus",
                "PsdSlot_Left_numberOfSlots",
                "PsdSlot_Right_timestamp",
                "PsdSlot_Rigth_eSigStatus",
                "PsdSlot_Right_numberOfSlots",
            ]
        ]

        df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
        pcl_type = df.loc[:, df.columns.str.startswith("delimiterType")]

        # TODO: Refactor pending
        if ConstantsCemInput.PCLEnum in pcl_type.values:
            # PDM signals ranges
            pmd_ok_ts = [
                pmd_data[PMDCamera.FRONT].query("signalState == 1")["timestamp"].min(),
                pmd_data[PMDCamera.REAR].query("signalState == 1")["timestamp"].min(),
                pmd_data[PMDCamera.LEFT].query("signalState == 1")["timestamp"].min(),
                pmd_data[PMDCamera.RIGHT].query("signalState == 1")["timestamp"].min(),
            ]

            first_pmd_ts = min(pmd_ok_ts)
            all_pmd_ts = max(pmd_ok_ts)

            # WSD signal ranges
            wsd_ok_ts = [
                wsd_data[PMDCamera.FRONT].query("signalState == 1")["timestamp"].min(),
                wsd_data[PMDCamera.REAR].query("signalState == 1")["timestamp"].min(),
                wsd_data[PMDCamera.LEFT].query("signalState == 1")["timestamp"].min(),
                wsd_data[PMDCamera.RIGHT].query("signalState == 1")["timestamp"].min(),
            ]

            first_wsd_ts = min(wsd_ok_ts)
            all_wsd_ts = max(wsd_ok_ts)

            # PSD signal ranges
            psd_ok_ts = [
                psd_data[psd_data["Front_signalState"] == 1]["Front_timestamp"].min(),
                psd_data[psd_data["Rear_signalState"] == 1]["Rear_timestamp"].min(),
                psd_data[psd_data["Left_signalState"] == 1]["Left_timestamp"].min(),
                psd_data[psd_data["Right_signalState"] == 1]["Right_timestamp"].min(),
            ]

            first_psd_ts = min(psd_ok_ts)
            all_psd_ts = max(psd_ok_ts)

            # Get ok status ts PCL data
            first_in_ts = min(first_pmd_ts, first_wsd_ts)
            all_in_ts = max(all_wsd_ts, all_pmd_ts)

            # Find closest ts where input signal state changes from 0 to 1 PCL data
            pcl_first_closest_ts = pcl_data.loc[pcl_data["timestamp"] > first_in_ts, "timestamp"].min()
            # Find closest ts where all inputs change from 0 to 1 PCL data
            pcl_all_closest_ts = pcl_data.loc[pcl_data["timestamp"] > all_in_ts, "timestamp"].min()

            # Find closest ts where input signal state changes from 0 to 1 PS data
            psd_first_closest_ts = slot_data.loc[slot_data["timestamp"] > first_psd_ts, "timestamp"].min()
            # Find closest ts where all inputs change from 0 to 1 PS data
            psd_all_closest_ts = slot_data.loc[slot_data["timestamp"] > all_psd_ts, "timestamp"].min()

            # Find ts where there must be data in the output
            processing_tolerance = ConstantsCem.CYCLE_PERIOD_TIME_MS * ConstantsCem.NUM_OF_CYCLES_FOR_OUTPUT * 1e3
            processing_end_ts = pcl_data.loc[
                pcl_data.timestamp > pcl_first_closest_ts + processing_tolerance, "timestamp"
            ].min()

            failing_section = []
            expected_result = []
            result_provided = []
            section_range = []

            # Confirm there is no output in the first section
            pcl_section_1st = pcl_data.loc[
                pcl_data["timestamp"] < pcl_first_closest_ts, ["timestamp", "numPclDelimiters"]
            ]
            psd_section_1st = slot_data.loc[
                slot_data["timestamp"] < psd_first_closest_ts, ["timestamp", "numberOfSlots"]
            ]
            if (pcl_section_1st["numPclDelimiters"] == 0).all() and (psd_section_1st["numberOfSlots"] == 0).all():
                first_section_result = True
            else:
                first_section_result = False
                failing_section.append("First scenario")
                expected_result.append("Number of elements = 0")
                result_provided.append(
                    [pcl_section_1st["numPclDelimiters"].max(), psd_section_1st["numberOfSlots"].max()]
                )
                section_range.append(f"0 - {pcl_first_closest_ts}")

            # Confirm there is output in the second section
            pcl_section_2nd = pcl_data.loc[pcl_data["timestamp"] > processing_end_ts, ["timestamp", "numPclDelimiters"]]
            psd_section_2nd = slot_data.loc[slot_data["timestamp"] > processing_end_ts, ["timestamp", "numberOfSlots"]]
            if (pcl_section_2nd["numPclDelimiters"] > 0).all() and (psd_section_2nd["numberOfSlots"] > 0).all():
                second_section_result = True
            else:
                first_section_result = False
                failing_section.append("Second scenario")
                expected_result.append("Number of elements > 0")
                result_provided.append(
                    [pcl_section_1st["numPclDelimiters"].min(), psd_section_1st["numberOfSlots"].min()]
                )
                section_range.append(f"{pcl_first_closest_ts} - end")

            # Test pass if all sections pass
            if first_section_result and second_section_result:
                test_result = fc.PASS
            else:
                test_result = fc.FAIL
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(
                                values=[
                                    "Failing section",
                                    "Expected output",
                                    "Number of elements PCL,PS",
                                    "Output section range",
                                ]
                            ),
                            cells=dict(values=[failing_section, expected_result, result_provided, section_range]),
                        )
                    ]
                )
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")

            # Plot PM data
            pcl_data = pcl_data.loc[(pcl_data["timestamp"] != 0)].drop_duplicates()
            pmd_front = pmd_data[PMDCamera.FRONT].loc[(pmd_data[PMDCamera.FRONT]["timestamp"] != 0)].drop_duplicates()
            pmd_rear = pmd_data[PMDCamera.REAR].loc[(pmd_data[PMDCamera.REAR]["timestamp"] != 0)].drop_duplicates()
            pmd_left = pmd_data[PMDCamera.LEFT].loc[(pmd_data[PMDCamera.LEFT]["timestamp"] != 0)].drop_duplicates()
            pmd_right = pmd_data[PMDCamera.RIGHT].loc[(pmd_data[PMDCamera.RIGHT]["timestamp"] != 0)].drop_duplicates()

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=pcl_data["timestamp"], y=pcl_data["numPclDelimiters"], name="Output"))
            fig.add_vrect(x0=pcl_data["timestamp"].iat[0], x1=pcl_first_closest_ts, layer="below")
            fig.add_vrect(x0=processing_end_ts, x1=pcl_all_closest_ts, fillcolor="#E1F5FE", layer="below")
            fig.add_vrect(x0=pcl_all_closest_ts, x1=pcl_data["timestamp"].iat[-1], fillcolor="#BBDEFB", layer="below")
            fig.add_trace(go.Scatter(x=pmd_front["timestamp"], y=pmd_front["signalState"], name="pmd_front"))
            fig.add_trace(go.Scatter(x=pmd_rear["timestamp"], y=pmd_rear["signalState"], name="pmd_rear"))
            fig.add_trace(go.Scatter(x=pmd_left["timestamp"], y=pmd_left["signalState"], name="pmd_left"))
            fig.add_trace(go.Scatter(x=pmd_right["timestamp"], y=pmd_right["signalState"], name="pmd_right"))
            plots.append(fig)
            plot_titles.append("Signal state PMD data")
            remarks.append("")

            # Plot WS data
            wsd_front = wsd_data[PMDCamera.FRONT].loc[(wsd_data[PMDCamera.FRONT]["timestamp"] != 0)].drop_duplicates()
            wsd_rear = wsd_data[PMDCamera.REAR].loc[(wsd_data[PMDCamera.REAR]["timestamp"] != 0)].drop_duplicates()
            wsd_left = wsd_data[PMDCamera.LEFT].loc[(wsd_data[PMDCamera.LEFT]["timestamp"] != 0)].drop_duplicates()
            wsd_right = wsd_data[PMDCamera.RIGHT].loc[(wsd_data[PMDCamera.RIGHT]["timestamp"] != 0)].drop_duplicates()

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=pcl_data["timestamp"], y=pcl_data["numPclDelimiters"], name="Output"))
            fig.add_vrect(x0=pcl_data["timestamp"].iat[0], x1=pcl_first_closest_ts, layer="below")
            fig.add_vrect(x0=processing_end_ts, x1=pcl_all_closest_ts, fillcolor="#E1F5FE", layer="below")
            fig.add_vrect(x0=pcl_all_closest_ts, x1=pcl_data["timestamp"].iat[-1], fillcolor="#BBDEFB", layer="below")
            fig.add_trace(go.Scatter(x=wsd_front["timestamp"], y=wsd_front["signalState"], name="wsd_front"))
            fig.add_trace(go.Scatter(x=wsd_rear["timestamp"], y=wsd_rear["signalState"], name="wsd_rear"))
            fig.add_trace(go.Scatter(x=wsd_left["timestamp"], y=wsd_left["signalState"], name="wsd_left"))
            fig.add_trace(go.Scatter(x=wsd_right["timestamp"], y=wsd_right["signalState"], name="wsd_right"))
            plots.append(fig)
            plot_titles.append("Signal state WSD data")
            remarks.append("")

            # Plot PS data
            psd_data = psd_data.drop_duplicates()
            psd_data = psd_data.loc[(psd_data["Front_timestamp"] != 0)]
            psd_data = psd_data.loc[(psd_data["Rear_timestamp"] != 0)]
            psd_data = psd_data.loc[(psd_data["Left_timestamp"] != 0)]
            psd_data = psd_data.loc[(psd_data["Right_timestamp"] != 0)]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=slot_data["timestamp"], y=slot_data["numberOfSlots"], name="Output"))
            fig.add_vrect(x0=slot_data["timestamp"].iat[0], x1=psd_first_closest_ts, layer="below")
            fig.add_vrect(x0=processing_end_ts, x1=psd_all_closest_ts, fillcolor="#E1F5FE", layer="below")
            fig.add_vrect(x0=psd_all_closest_ts, x1=pcl_data["timestamp"].iat[-1], fillcolor="#F5F5F5", layer="below")
            fig.add_trace(go.Scatter(x=psd_data["Front_timestamp"], y=psd_data["Front_signalState"], name="psdFront"))
            fig.add_trace(go.Scatter(x=psd_data["Rear_timestamp"], y=psd_data["Rear_signalState"], name="psdRear"))
            fig.add_trace(go.Scatter(x=psd_data["Left_timestamp"], y=psd_data["Left_signalState"], name="psdLeft"))
            fig.add_trace(go.Scatter(x=psd_data["Right_timestamp"], y=psd_data["Right_signalState"], name="psdRight"))
            plots.append(fig)
            plot_titles.append("Signal state PSD data")
            remarks.append("")

        else:
            test_result = fc.INPUT_MISSING

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1530449"],
            fc.TESTCASE_ID: ["39889"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test case checks if PFS only processes input signals if their signal state is AL_SIG_STATE_OK"
            ],
            fc.TEST_RESULT: [test_result],
        }

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = result_df


@verifies("1530449")
@testcase_definition(
    name="SWRT_CNC_PFS_AlSignalStateOk",
    description="This test case checks if PFS only processes input signals if their signal state is AL_SIG_STATE_OK",
)
class FtPCLAlSignalState(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPCLAlSignalState]
