"""PFS Output Reset TestCase."""

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


import numpy as np
import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep

SIGNAL_DATA = "PFS_Output_Reset"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM-PFS Output reset",
    description="This test case checks if an Init request received,PFS shall reset its outputs to the default",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPFSReset(TestStep):
    """TestStep for resetting PFS module, utilizing a custom report."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)
        signal_summary = {}

        reader = self.readers[SIGNAL_DATA].signals
        data_df = reader.as_plain_df

        pfs_data = data_df.filter(regex="Cem")

        pfs_data = pfs_data.drop_duplicates()
        pfs_data["Cem_pcl_eSigStatus"] = pfs_data["Cem_pcl_eSigStatus"].astype(float)

        reset_ts = pfs_data.loc[pfs_data["Cem_pcl_eSigStatus"].diff() == -1, "Cem_numPclDelimiters_timestamp"].min()

        # Removing timestamp signals from the df and keeping only the relevant signals to be checked for default
        # values.

        pfs_data = pfs_data.drop(columns=["CemSlot_timestamp", "CemWs_timestamp"])

        if np.isnan(reset_ts):
            test_result = fc.FAIL
            evaluation = ["No reset data found"]
            signal_summary["InitReset_result"] = evaluation
        else:
            # Verify if signal output is in state init after reset
            pfs_data.set_index("Cem_numPclDelimiters_timestamp", inplace=True)
            reset_section = pfs_data[pfs_data.index == reset_ts]
            result_columns = (reset_section == 0).all()

            if result_columns.all():
                test_result = fc.PASS
                evaluation = ["PFS reset values to default, if init request is received"]
                signal_summary["InitReset_result"] = evaluation
            else:
                test_result = fc.FAIL
                evaluation = ["PFS doesn't reset values to default, if init request is received"]
                signal_summary["InitReset_result"] = evaluation

        # Set table dataframe
        signal_summary = pd.DataFrame(
            {
                "Evaluation": {"1": "If init request received[1-0], PFS shall reset its output values to default[0]"},
                "Result": {"1": evaluation},
                "Verdict": {"1": test_result},
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PFS Init Reset Output Values State")
        self.result.details["Plots"].append(sig_sum)

        # Plot data
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=[*range(len(pfs_data))],
                y=pfs_data["Cem_pcl_eSigStatus"].values.tolist(),
                mode="lines",
                name="sSigHeader.eSigStatus",
                line=dict(color="darkblue"),
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"),
            xaxis=dict(tickformat="14"),
            xaxis_title="Frames",
            yaxis_title="Cem_pcl_eSigStatus",
        )
        plots.append(fig)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1530451"],
            fc.TESTCASE_ID: ["42630"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Verify if an Init request is received, PFS shall reset its outputs to the default" "initialized values"
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


@verifies("1530451")
@testcase_definition(
    name="SWRT_CNC_PFS_OutputInitAfterReset",
    description="This test case checks if an Init request is received, PFS shall reset its outputs to the default "
    "initialized values",
)
class FtPFSReset(TestCase):
    """CEM-PFS Output reset Test Case"""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPFSReset]
