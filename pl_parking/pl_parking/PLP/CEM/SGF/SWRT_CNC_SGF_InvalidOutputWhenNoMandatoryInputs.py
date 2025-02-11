#!/usr/bin/env python3
"""SWRT CNC SGF CurbObjectsSematicPointCloud testcases"""
import logging

from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

import numpy as np

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)


import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import rep
from pl_parking.PLP.CEM.inputs.input_CemSgfReader import SGFReader
from pl_parking.PLP.CEM.SGF.ft_helper import SGFSignals

SIGNAL_DATA = "InvalidOutputWhenNoMandatoryInputs"
sgf_obj = SGFSignals()


@teststep_definition(
    step_number=1,
    name="SGF Invalid Output - No mandatory inputs",
    description="This test case checks in case SGF have no mandatory inputs provided that signals a invalid output",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SGFSignals)
class TestStepInvalidOutputNoMandatoryInputs(TestStep):
    """TestStep for analyzing invalid output detected when no madatory inputs provided, utilizing a custom report."""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        test_result = fc.NOT_ASSESSED
        plot_titles, plots, remarks = rep([], 3)
        signal_summary = {}

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Load signals
        reader = self.readers[SIGNAL_DATA].signals
        input_reader = SGFReader(reader)
        static_object_df = input_reader.data

        signalEvaluated = sgf_obj.get_properties()[sgf_obj.Columns.VEDODO_SIGSTATUS][0]

        requiredSignalsOk = True
        description = "The evaluation of the signal is <b>PASSED</b>."

        requiredInputSignals = ["VedodoOdometry_eSigStatus"] # atm, ego motion is the only mandatory input, camera blockage later
        requiredOutputSignals = ["SGF_sig_status", "SGF_timestamp"]
        #check inputs
        for signal in requiredInputSignals:
            if signal not in static_object_df.columns:
                requiredSignalsOk = False
                break
       #check outputs
        for signal in requiredOutputSignals:
            if signal not in static_object_df.columns:
                requiredSignalsOk = False
                break

        if not requiredSignalsOk:
            description = " ".join("Signal <b>not evaluated</b> because it is not available.".split())
            test_result = fc.NOT_ASSESSED
        else:
            #skip initialization in any measfreezed
            static_object_df = static_object_df[static_object_df["SGF_sig_status"] != 0]

            sgf_ts = static_object_df["SGF_timestamp"]

            #if vehicle odometry is ok, static object output should be ok, if no internal errors
            invalid_mask = (static_object_df["VedodoOdometry_eSigStatus"] != static_object_df["SGF_sig_status"])
            invalidTs = []

            if np.any(invalid_mask):
                test_result = fc.FAIL
                invalidTs = sgf_ts[invalid_mask].values
                pass_rate = len(invalidTs) / len(sgf_ts.values)
                error_dict = {
                    "Signal name": signalEvaluated,
                    "Timestamp": invalidTs,
                    "PassRate": pass_rate,
                    "Description": "signal state is not the expected one"
                }
                description = " ".join(
                    f"The evaluation of the signal is <b>FAILED</b> at timestamps {error_dict['Timestamp']} "
                    f"due to {error_dict['Description']} with a pass rate of "
                    f"({error_dict['PassRate']}).".split()
                )

            else:
                test_result = fc.PASS
                description = "The evaluation of the signal is <b>PASSED</b> with a pass rate of 100"

        signal_summary[signalEvaluated] = description
        remark = (
            "Static objects should be valid if all the mandatory inputs are available and valid(vehicle odometry) "
        )
        self.sig_sum = fh.convert_dict_to_pandas(
            signal_summary=signal_summary,
        )
        plot_titles.append("Checking if invalid state is signaled as expected")
        plots.append(self.sig_sum)
        remarks.append(remark)
        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2048828"],
            fc.TESTCASE_ID: ["90415"],
            fc.TEST_RESULT: [test_result],
        }

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif test_result == fc.NOT_ASSESSED:
            self.result.measured_result = DATA_NOK
        else:
            self.result.measured_result = FALSE

        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")

        self.result.details["Additional_results"] = result_df


@verifies(
    requirement="2048828",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_q9M5oOtNEe659sZ1Fpi4lA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F23890",
)
@testcase_definition(
    name="SWRT_CNC_SGF_InvalidOutputWhenNoMandatoryInputs",
    description="This test case checks in case SGF has invalid output if any of the mandatory inputs is missing.",
)
@register_inputs("/parking")
class InvalidOutputWhenNoMandatoryInputs(TestCase):
    """Example test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepInvalidOutputNoMandatoryInputs,
        ]
