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


import pandas as pd
import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import ConstantsCem

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
        signal_summary = {}

        reader = self.readers[SIGNAL_DATA].signals
        df = reader.as_plain_df

        # Output df
        pcl_data = df[["Cem_numPclDelimiters_timestamp", "Cem_pcl_eSigStatus", "Cem_numPclDelimiters"]]
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
                "PMDWs_Front_timestamp",
                "PMDWs_Front_eSigStatus",
                "PMDWs_Front_numberOfLines",
                "PMDWs_Rear_timestamp",
                "PMDWs_Rear_eSigStatus",
                "PMDWs_Rear_numberOfLines",
                "PMDWs_Left_timestamp",
                "PMDWs_Left_eSigStatus",
                "PMDWs_Left_numberOfLines",
                "PMDWs_Right_timestamp",
                "PMDWs_Right_eSigStatus",
                "PMDWs_Right_numberOfLines",
            ]
        ]
        # TODO: Signal status for all bsigs not available update common_ft_helper
        psd_data = df[
            [
                "PmsdSlot_Front_timestamp",
                "PmsdSlot_Front_eSigStatus",
                "PmsdSlot_Front_numberOfSlots",
                "PmsdSlot_Rear_timestamp",
                "PmsdSlot_Rear_eSigStatus",
                "PmsdSlot_Rear_numberOfSlots",
                "PmsdSlot_Left_timestamp",
                "PmsdSlot_Left_eSigStatus",
                "PmsdSlot_Left_numberOfSlots",
                "PmsdSlot_Right_timestamp",
                "PmsdSlot_Right_eSigStatus",
                "PmsdSlot_Right_numberOfSlots",
            ]
        ]

        df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
        pcl_type = df.loc[:, df.columns.str.startswith("Cem_pcl_delimiterId")]

        # TODO: Refactor pending
        if not pcl_type.empty:
            # PDM signals ranges
            pmd_ok_ts = [
                pmd_data.query("PMDCamera_Front_eSigStatus == 1")["PMDCamera_Front_timestamp"].min(),
                pmd_data.query("PMDCamera_Rear_eSigStatus == 1")["PMDCamera_Rear_timestamp"].min(),
                pmd_data.query("PMDCamera_Left_eSigStatus == 1")["PMDCamera_Left_timestamp"].min(),
                pmd_data.query("PMDCamera_Right_eSigStatus == 1")["PMDCamera_Right_timestamp"].min(),
            ]

            first_pmd_ts = min(pmd_ok_ts)
            all_pmd_ts = max(pmd_ok_ts)

            # WSD signal ranges
            wsd_ok_ts = [
                wsd_data.query("PMDWs_Front_eSigStatus == 1")["PMDWs_Front_timestamp"].min(),
                wsd_data.query("PMDWs_Rear_eSigStatus == 1")["PMDWs_Rear_timestamp"].min(),
                wsd_data.query("PMDWs_Left_eSigStatus == 1")["PMDWs_Left_timestamp"].min(),
                wsd_data.query("PMDWs_Right_eSigStatus == 1")["PMDWs_Right_timestamp"].min(),
            ]

            first_wsd_ts = min(wsd_ok_ts)
            all_wsd_ts = max(wsd_ok_ts)

            # PSD signal ranges
            psd_ok_ts = [
                psd_data.query("PmsdSlot_Front_eSigStatus == 1")["PmsdSlot_Front_timestamp"].min(),
                psd_data.query("PmsdSlot_Rear_eSigStatus == 1")["PmsdSlot_Rear_timestamp"].min(),
                psd_data.query("PmsdSlot_Left_eSigStatus == 1")["PmsdSlot_Left_timestamp"].min(),
                psd_data.query("PmsdSlot_Right_eSigStatus == 1")["PmsdSlot_Right_timestamp"].min(),
            ]

            first_psd_ts = min(psd_ok_ts)
            all_psd_ts = max(psd_ok_ts)

            # Get ok status ts PCL data
            first_in_ts = min(first_pmd_ts, first_wsd_ts)
            all_in_ts = max(all_wsd_ts, all_pmd_ts)

            # Find closest ts where input signal state changes from 0 to 1 PCL data
            pcl_first_closest_ts = pcl_data.loc[
                pcl_data["Cem_numPclDelimiters_timestamp"] > first_in_ts, "Cem_numPclDelimiters_timestamp"
            ].min()
            # Find closest ts where all inputs change from 0 to 1 PCL data
            pcl_all_closest_ts = pcl_data.loc[
                pcl_data["Cem_numPclDelimiters_timestamp"] > all_in_ts, "Cem_numPclDelimiters_timestamp"
            ].min()

            # Find closest ts where input signal state changes from 0 to 1 PS data
            psd_first_closest_ts = slot_data.loc[
                slot_data["CemSlot_timestamp"] > first_psd_ts, "CemSlot_timestamp"
            ].min()
            # Find closest ts where all inputs change from 0 to 1 PS data
            psd_all_closest_ts = slot_data.loc[slot_data["CemSlot_timestamp"] > all_psd_ts, "CemSlot_timestamp"].min()

            # Find ts where there must be data in the output
            processing_tolerance = ConstantsCem.CYCLE_PERIOD_TIME_MS * ConstantsCem.NUM_OF_CYCLES_FOR_OUTPUT * 1e3
            processing_end_ts = pcl_data.loc[
                pcl_data.Cem_numPclDelimiters_timestamp > pcl_first_closest_ts + processing_tolerance,
                "Cem_numPclDelimiters_timestamp",
            ].min()

            failing_section = []
            expected_result = []
            result_provided = []
            section_range = []

            # Confirm there is no output in the first section
            pcl_section_1st = pcl_data.loc[
                pcl_data["Cem_numPclDelimiters_timestamp"] < pcl_first_closest_ts,
                ["Cem_numPclDelimiters_timestamp", "Cem_numPclDelimiters"],
            ]
            psd_section_1st = slot_data.loc[
                slot_data["CemSlot_timestamp"] < psd_first_closest_ts, ["CemSlot_timestamp", "CemSlot_numberOfSlots"]
            ]
            if (pcl_section_1st["Cem_numPclDelimiters"] == 0).all() and (
                psd_section_1st["CemSlot_numberOfSlots"] == 0
            ).all():
                first_section_result = True
            else:
                first_section_result = False
                failing_section.append("First scenario")
                expected_result.append("Number of elements = 0")
                result_provided.append(
                    [pcl_section_1st["Cem_numPclDelimiters"].max(), psd_section_1st["CemSlot_numberOfSlots"].max()]
                )
                section_range.append(f"0 - {pcl_first_closest_ts}")

            # Confirm there is output in the second section
            pcl_section_2nd = pcl_data.loc[
                pcl_data["Cem_numPclDelimiters_timestamp"] > processing_end_ts,
                ["Cem_numPclDelimiters_timestamp", "Cem_numPclDelimiters"],
            ]
            psd_section_2nd = slot_data.loc[
                slot_data["CemSlot_timestamp"] > processing_end_ts, ["CemSlot_timestamp", "CemSlot_numberOfSlots"]
            ]
            if (pcl_section_2nd["Cem_numPclDelimiters"] > 0).all() and (
                psd_section_2nd["CemSlot_numberOfSlots"] > 0
            ).all():
                second_section_result = True
            else:
                first_section_result = False
                failing_section.append("Second scenario")
                expected_result.append("Number of elements > 0")
                result_provided.append(
                    [pcl_section_1st["Cem_numPclDelimiters"].min(), psd_section_1st["CemSlot_numberOfSlots"].min()]
                )
                section_range.append(f"{pcl_first_closest_ts} - end")

            # Test pass if all sections pass
            if first_section_result and second_section_result:
                test_result = fc.PASS
                evaluation = "PFS only processes input signals if their signal state is AL_SIG_STATE_OK"
                signal_summary["AL_SIG_STATE_OK"] = evaluation
            else:
                test_result = fc.FAIL
                evaluation = "PFS does not processes input signals if their signal state is AL_SIG_STATE_OK"
                signal_summary["AL_SIG_STATE_OK"] = evaluation
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
                fig.layout = go.Layout(title=dict(text="Test Fail report", font_size=20))
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")

            # Plot PMD data
            pcl_data = pcl_data.loc[(pcl_data["Cem_numPclDelimiters_timestamp"] != 0)].drop_duplicates()
            pmd_front = pmd_data.loc[(pmd_data["PMDCamera_Front_timestamp"] != 0)].drop_duplicates()
            pmd_rear = pmd_data.loc[(pmd_data["PMDCamera_Rear_timestamp"] != 0)].drop_duplicates()
            pmd_left = pmd_data.loc[(pmd_data["PMDCamera_Left_timestamp"] != 0)].drop_duplicates()
            pmd_right = pmd_data.loc[(pmd_data["PMDCamera_Right_timestamp"] != 0)].drop_duplicates()

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=pcl_data["Cem_numPclDelimiters_timestamp"], y=pcl_data["Cem_numPclDelimiters"], name="Output"
                )
            )
            fig.add_vrect(x0=pcl_data["Cem_numPclDelimiters_timestamp"].iat[0], x1=pcl_first_closest_ts, layer="below")
            fig.add_vrect(x0=processing_end_ts, x1=pcl_all_closest_ts, fillcolor="#E1F5FE", layer="below")
            fig.add_vrect(
                x0=pcl_all_closest_ts,
                x1=pcl_data["Cem_numPclDelimiters_timestamp"].iat[-1],
                fillcolor="#BBDEFB",
                layer="below",
            )
            fig.add_trace(
                go.Scatter(
                    x=pmd_front["PMDCamera_Front_timestamp"],
                    y=pmd_front["PMDCamera_Front_eSigStatus"],
                    name="pmd_front",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=pmd_rear["PMDCamera_Rear_timestamp"], y=pmd_rear["PMDCamera_Rear_eSigStatus"], name="pmd_rear"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=pmd_left["PMDCamera_Left_timestamp"], y=pmd_left["PMDCamera_Left_eSigStatus"], name="pmd_left"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=pmd_right["PMDCamera_Right_timestamp"],
                    y=pmd_right["PMDCamera_Right_eSigStatus"],
                    name="pmd_right",
                )
            )
            fig.layout = go.Layout(
                xaxis=dict(title="Timestamp [nsec]"),
                yaxis=dict(title="eSigStatus"),
                title=dict(text="Signal state PMD data", font_size=20),
            )
            plots.append(fig)
            plot_titles.append("Signal state PMD data")
            remarks.append("")

            # Plot WS data
            wsd_front = wsd_data.loc[(wsd_data["PMDWs_Front_timestamp"] != 0)].drop_duplicates()
            wsd_rear = wsd_data.loc[(wsd_data["PMDWs_Rear_timestamp"] != 0)].drop_duplicates()
            wsd_left = wsd_data.loc[(wsd_data["PMDWs_Left_timestamp"] != 0)].drop_duplicates()
            wsd_right = wsd_data.loc[(wsd_data["PMDWs_Right_timestamp"] != 0)].drop_duplicates()

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=pcl_data["Cem_numPclDelimiters_timestamp"], y=pcl_data["Cem_numPclDelimiters"], name="Output"
                )
            )
            fig.add_vrect(x0=pcl_data["Cem_numPclDelimiters_timestamp"].iat[0], x1=pcl_first_closest_ts, layer="below")
            fig.add_vrect(x0=processing_end_ts, x1=pcl_all_closest_ts, fillcolor="#E1F5FE", layer="below")
            fig.add_vrect(
                x0=pcl_all_closest_ts,
                x1=pcl_data["Cem_numPclDelimiters_timestamp"].iat[-1],
                fillcolor="#BBDEFB",
                layer="below",
            )
            fig.add_trace(
                go.Scatter(
                    x=wsd_front["PMDWs_Front_timestamp"], y=wsd_front["PMDWs_Front_eSigStatus"], name="wsd_front"
                )
            )
            fig.add_trace(
                go.Scatter(x=wsd_rear["PMDWs_Rear_timestamp"], y=wsd_rear["PMDWs_Rear_eSigStatus"], name="wsd_rear")
            )
            fig.add_trace(
                go.Scatter(x=wsd_left["PMDWs_Left_timestamp"], y=wsd_left["PMDWs_Left_eSigStatus"], name="wsd_left")
            )
            fig.add_trace(
                go.Scatter(
                    x=wsd_right["PMDWs_Right_timestamp"], y=wsd_right["PMDWs_Right_eSigStatus"], name="wsd_right"
                )
            )
            fig.layout = go.Layout(
                xaxis=dict(title="Timestamp [nsec]"),
                yaxis=dict(title="eSigStatus"),
                title=dict(text="Signal state WSD data", font_size=20),
            )
            plots.append(fig)
            plot_titles.append("Signal state WSD data")
            remarks.append("")

            # Plot PS data
            psd_data = psd_data.drop_duplicates()
            psd_data = psd_data.loc[(psd_data["PmsdSlot_Front_timestamp"] != 0)]
            psd_data = psd_data.loc[(psd_data["PmsdSlot_Rear_timestamp"] != 0)]
            psd_data = psd_data.loc[(psd_data["PmsdSlot_Left_timestamp"] != 0)]
            psd_data = psd_data.loc[(psd_data["PmsdSlot_Right_timestamp"] != 0)]
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(x=slot_data["CemSlot_timestamp"], y=slot_data["CemSlot_numberOfSlots"], name="Output")
            )
            fig.add_vrect(x0=slot_data["CemSlot_timestamp"].iat[0], x1=psd_first_closest_ts, layer="below")
            fig.add_vrect(x0=processing_end_ts, x1=psd_all_closest_ts, fillcolor="#E1F5FE", layer="below")
            fig.add_vrect(
                x0=psd_all_closest_ts,
                x1=pcl_data["Cem_numPclDelimiters_timestamp"].iat[-1],
                fillcolor="#F5F5F5",
                layer="below",
            )
            fig.add_trace(
                go.Scatter(
                    x=psd_data["PmsdSlot_Front_timestamp"], y=psd_data["PmsdSlot_Front_eSigStatus"], name="psdFront"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=psd_data["PmsdSlot_Rear_timestamp"], y=psd_data["PmsdSlot_Rear_eSigStatus"], name="psdRear"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=psd_data["PmsdSlot_Left_timestamp"], y=psd_data["PmsdSlot_Left_eSigStatus"], name="psdLeft"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=psd_data["PmsdSlot_Right_timestamp"], y=psd_data["PmsdSlot_Right_eSigStatus"], name="psdRight"
                )
            )
            fig.layout = go.Layout(
                xaxis=dict(title="Timestamp [nsec]"),
                yaxis=dict(title="eSigStatus"),
                title=dict(text="Signal state PSD data", font_size=20),
            )
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        else:
            test_result = fc.INPUT_MISSING
            evaluation = "Required input is missing"
            signal_summary["AL_SIG_STATE_OK"] = evaluation

        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": "EnvironmentFusion checks if PFS only processes input signals if their signal state is AL_SIG_STATE_OK",
                },
                "Result": {
                    "1": evaluation,
                },
                "Verdict": {
                    "1": "PASSED" if test_result == "passed" else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PFS Signal status OK")
        self.result.details["Plots"].append(sig_sum)

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
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_r9j4ck4mEe6M5-WQsF_-tQ&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36325",
)
class FtPCLAlSignalState(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPCLAlSignalState]
