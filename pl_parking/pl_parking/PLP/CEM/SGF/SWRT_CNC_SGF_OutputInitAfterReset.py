"""SWRT CNC SGF OutputInitAerReset testcases"""

# from tsf.io.signals import SignalDefinition
# from tsf.core.results import FALSE, TRUE, BooleanResult

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

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

import sys

import numpy as np
import plotly.express as px
import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, CustomTeststepReport, rep
from pl_parking.PLP.CEM.inputs.input_CemSgfReader import SGFReader

SIGNAL_DATA = "OutputInitAfterReset"
example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="SWRT_CNC_SGF_OutputInitAfterReset",
    description="This test case checks if after an Init request received, SGF resets its outputs to the default initialized values and states.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepOutputInitAfterReset(TestStep):
    """TestStep for initializing output after a reset operation, employing a custom report."""

    custom_report = CustomTeststepReport

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
        # Define variables
        test_result = fc.NOT_ASSESSED
        # data = pd.DataFrame()
        plot_titles, plots, remarks = rep([], 3)

        # Load signals
        reader = self.readers[SIGNAL_DATA].signals
        input_reader = SGFReader(reader)
        static_object_df = input_reader.data  # noqa: F841

        # (init request received)
        # if output values = default values
        #     test_result = fc.PASS
        # else
        #     test_result = fc.FAIL

        # NOTE: The TESTSTEP requires updating/modification to ensure relevance. Temporarily added noqa statements
        #               to prevent Jenkins issues for other users.
        # Find ts where signal state changes from ok to init
        motion_data = motion_data.drop_duplicates()  # noqa: F821
        motion_data["EgoMotionPort_eSigStatus"] = motion_data["EgoMotionPort_eSigStatus"].astype(float)
        reset_ts = motion_data.loc[
            motion_data["EgoMotionPort_eSigStatus"].diff() == -1, "EgoMotionPort_uiTimeStamp"
        ].min()
        if np.isnan(reset_ts):
            _log.error("No reset found in data")
            test_result = fc.NOT_ASSESSED

        else:
            # Verify if signal output is in state init after reset
            motion_data.set_index("EgoMotionPort_uiTimeStamp", inplace=True)
            reset_section = motion_data[motion_data.index == reset_ts]
            result_columns = (reset_section == 0).all()

            if result_columns.all():
                test_result = fc.PASS
            else:
                test_result = fc.FAIL
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=result_columns.index.str.split("_").str[1]),
                            cells=dict(values=result_columns.values.tolist()),
                        )
                    ]
                )
                plot_titles.append("Test Fail report Output Signal in Init state")
                plots.append(fig)
                remarks.append("")

            # Plot data
            motion_data = motion_data.loc[(motion_data.index != 0)].drop_duplicates()
            fig = px.line(motion_data, x=motion_data.index, y=motion_data.columns)
            fig.add_vrect(x0=reset_ts, x1=motion_data.index.max(), fillcolor="#F5F5F5", layer="below")
            plots.append(fig)
            plot_titles.append("Output signal values")
            remarks.append("")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1522102"],
            fc.TESTCASE_ID: ["42381"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test case checks if after an Init request received, SGF resets its outputs to the default initialized values and states."
            ],
            fc.TEST_RESULT: [test_result],
        }
        # Mandatory for creating the plot:
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
    description=(
        "This test case checks if after an Init request received, SGF resets its outputs to the default initialized values and states."
    ),
    doors_url="",
)
class OutputInitAfterReset(TestCase):
    """Output Init After Reset test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepOutputInitAfterReset,
        ]
