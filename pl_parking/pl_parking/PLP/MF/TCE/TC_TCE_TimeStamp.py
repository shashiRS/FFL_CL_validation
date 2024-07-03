#!/usr/bin/env python3
"""This is the test case to check the times stamps are in microseconds or not"""

import logging
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.core.utilities import debug
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import MfCustomTeststepReport, convert_dict_to_pandas, get_color, rep
from pl_parking.PLP.MF.constants import PlotlyTemplate
from pl_parking.PLP.MF.TCE.constants import CarMakerUrl

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


__author__ = "Anil A, uie64067"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.0.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

READER_NAME = "TceTimeStamp"


class TceSignals(SignalDefinition):
    """Tce signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TIME"
        tceDebugPortTs = "tceDebugPortTs"
        tceEstimatePortTs = "tceEstimatePortTs"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.tceEstimatePortTs: CarMakerUrl.tceEstimatePortTs,
            self.Columns.tceDebugPortTs: CarMakerUrl.tceDebugPortTs,
            self.Columns.TIME: CarMakerUrl.time,
        }


def is_microseconds_format(time_value):
    """Validating the timestamp in microseconds format or not"""
    try:
        # Check if the time value is numeric
        float_time = float(time_value)

        # Check if the time value is within a reasonable range
        if 1e4 <= float_time <= 1e20:  # Adjust the range as per your requirement
            return True
        else:
            return False
    except ValueError:
        return False


def evaluation_result(time_format_result, sig_type):
    """Evaluate and validate the result to display the results in report"""
    if not time_format_result:
        evaluation = f"Evaluation of {sig_type} TimeStamp is not in microseconds format, Hence test results is FAILED."
        test_result = False
    else:
        evaluation = f"Evaluation of {sig_type} TimeStamp is in microseconds format, Hence test results is PASSED."
        test_result = fc.PASS
    return test_result, evaluation


@teststep_definition(
    step_number=1,
    name="The TCE shall provide the timestamp of the provided data in microseconds.",
    description="The TCE shall provide the timestamp of the provided data in microseconds.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, TceSignals)
class TceTimeStamp(TestStep):
    """Test case for TCE TimeStamp.

    Objective
    ---------

    The TCE shall provide the timestamp of the provided data in microseconds.

    Detail
    ------

    The TCE shall provide the timestamp of the provided data in microseconds.
    """

    custom_report = MfCustomTeststepReport

    def __init__(self):
        super().__init__()
        self.sig_sum = None

    def process(self, **kwargs):
        """Evaluating test case"""
        _log.debug("Starting processing...")
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)
        df: pd.DataFrame = self.readers[READER_NAME].signals
        ap_time = list(df[TceSignals.Columns.TIME])
        ts_debug = list(df[TceSignals.Columns.tceDebugPortTs])
        ts_est = list(df[TceSignals.Columns.tceEstimatePortTs])

        # Init variables
        signal_summary = dict()
        algo_ts_microseconds_format = True
        ref_ts_microseconds_format = True
        for algo, gt in zip(ts_debug[3:], ts_est[3:]):  # to skip first 3 timestamp
            if not is_microseconds_format(algo):
                algo_ts_microseconds_format = False
                break
            if not is_microseconds_format(gt):
                ref_ts_microseconds_format = False
                break

        algo_test_result, algo_evaluation = evaluation_result(algo_ts_microseconds_format, "Estimate")
        ref_test_result, ref_evaluation = evaluation_result(ref_ts_microseconds_format, "Debug")

        if algo_test_result and ref_test_result:
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[f"{CarMakerUrl.tceDebugPortTs}"] = ref_evaluation
        signal_summary[f"{CarMakerUrl.tceEstimatePortTs}"] = algo_evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("TceTimeStamp Graph")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=ts_est,
                mode="lines",
                name=CarMakerUrl.tceEstimatePortTs,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=ts_debug,
                mode="lines",
                name=CarMakerUrl.tceDebugPortTs,
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]", yaxis_title="Time[µs]"
        )
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        fig.add_annotation(
            dict(
                font=dict(color="black", size=12),
                x=0,
                y=-0.12,
                showarrow=False,
                text="Estimated VS GT TimeStamp",
                textangle=0,
                xanchor="left",
                xref="paper",
                yref="paper",
            )
        )
        plot_titles.append(" ")
        plots.append(fig)
        remarks.append("")

        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": get_color(test_result)},
            fc.REQ_ID: ["1676129"],
            fc.TESTCASE_ID: ["41319"],
            fc.TEST_RESULT: [test_result],
        }
        self.result.details["Additional_results"] = additional_results_dict


@verifies("ReqID_1676129")
@testcase_definition(
    name="TCE TimeStamp test case.",
    description="TCE TimeStamp in microseconds test case.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fj"
    "azz.conti.de%2Frm4%2Fresources%2FBI_yDTniXpAEe6n7Ow9oWyCxw&oslc_config.context=https%3A%2F%2Fjazz.conti"
    ".de%2Fgc%2Fconfiguration%2F17099&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28P"
    "vtEeqIqKySVwTVNQ%2Fcomponents%2F__9Yt9nfVEe6n7Ow9oWyCxw",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TceTimeStampTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TceTimeStamp,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        TceTimeStampTestCase,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
        kpi_report=False,
        dev_report=True,
    )
    return testrun_id, cp


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"
    out_folder = working_directory / "out"

    main(temp_dir=out_folder, open_explorer=True)
