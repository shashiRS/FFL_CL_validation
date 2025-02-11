"""SGF Output Reset TestCase."""

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
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.SGF.ft_helper import SGFSignals

SIGNAL_DATA = "SGF_Output_Reset"

example_obj = SGFSignals()


@teststep_definition(
    step_number=1,
    name="CEM-SGF Output reset",
    description="This test case checks if an Init request received,SGF shall reset its outputs to the default",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SGFSignals)
class TestStepFtSGFReset(TestStep):
    """TestStep for resetting SGF module, utilizing a custom report."""

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

        reader = self.readers[SIGNAL_DATA]
        data_df = reader.as_plain_df

        data_df = data_df.drop_duplicates()
        data_df["SGF_sig_status"] = data_df["SGF_sig_status"].astype(float)

        # Check when the state changes from OK(1) to init(0) state
        reset_ts = data_df.loc[data_df["SGF_sig_status"].diff() == -1, "SGF_timestamp"].min()

        if np.isnan(reset_ts):
            test_result = fc.NOT_ASSESSED
            evaluation = ["No reset data found"]
            signal_summary["InitReset_result"] = evaluation
        else:
            # Verify if signal output is in state init after reset
            data_df.set_index("SGF_timestamp", inplace=True)
            reset_section = data_df[data_df.index == reset_ts]
            result_columns = (reset_section["numPolygons"] == 0).all()

            if result_columns.all():
                test_result = fc.PASS
                evaluation = "SGF reset values to default, if init request is received"
                signal_summary["InitReset_result"] = evaluation
            else:
                test_result = fc.FAIL
                evaluation = "SGF doesn't reset values to default, if init request is received"
                signal_summary["InitReset_result"] = evaluation

        # Set table dataframe
        signal_summary = pd.DataFrame(
            {
                "Evaluation": {"1": "If init request received[1-0], SGF shall reset its output values to default[0]"},
                "Result": {"1": evaluation},
                "Verdict": {"1": test_result},
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="SGF Init Reset Output Values State")
        self.result.details["Plots"].append(sig_sum)

        # Plot eSig state data
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=[*range(len(data_df))],
                y=data_df["SGF_sig_status"].values.tolist(),
                mode="lines",
                name="sSigHeader.eSigStatus",
                line=dict(color="darkblue"),
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"),
            xaxis=dict(tickformat="14"),
            xaxis_title="Frames",
            yaxis_title="SGF_Output_eSigStatus",
        )
        plots.append(fig)

        # Plot numberOfObjects data
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=[*range(len(data_df))],
                y=data_df["numPolygons"].values.tolist(),
                mode="lines",
                name="staticObjectOutput.numberOfObjects",
                line=dict(color="darkblue"),
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"),
            xaxis=dict(tickformat="14"),
            xaxis_title="Frames",
            yaxis_title="SGF_Output_numberOfObjects",
        )
        plots.append(fig)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1522102"],
            fc.TESTCASE_ID: ["42381"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Verify if an Init request is received, SGF shall reset its internal state and determine its output based on sensor information received only after the Init request."
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


@verifies("1522102")
@testcase_definition(
    name="SWRT_CNC_SGF_OutputInitAfterReset",
    description="This test case checks  if after an Init request received, SGF sets all output signals to state AL_SIG_STATE_INIT and sets all other values on the output to 0.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_8OI51kxLEe6M5-WQsF_-tQ&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36325",
)
class FtSGFReset(TestCase):
    """CEM-SGF Output reset Test Case"""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFReset]
