#!/usr/bin/env python3
"""SWRT CNC SGF CurbObjectsSemanticPolylines testcases"""
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

SIGNAL_DATA = "CurbObjectsFromSVCSemanticPolylines"
sgf_obj = SGFSignals()


@teststep_definition(
    step_number=1,
    name="Curb Objects From SVC Semantic Polylines",
    description="This test case checks in case SGF has curb output when only SVC semantic polylines input is received.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SGFSignals)
class TestStepCurbObjectsFromSVCSemanticPolyline(TestStep):
    """TestStep for analyzing static objects detected from SVC Semantic Point Cloud, utilizing a custom report."""

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

        signalEvaluated = sgf_obj.get_properties()[sgf_obj.Columns.SGF_OBJECT_SEMANTIC_CLASS][0]

        #Checking that only semantic polylines are received as a input
        polylinesFrontStatus  = static_object_df["SppPolylineListFront_eSigStatus"]
        polylinesRearStatus   = static_object_df["SppPolylineListRear_eSigStatus"]
        polylinesLeftStatus   = static_object_df["SppPolylineListLeft_eSigStatus"]
        polylinesRightStatus  = static_object_df["SppPolylineListRight_eSigStatus"]

        semanticPointsFrontStatus  = static_object_df["SppPointListFront_eSigStatus"]
        semanticPointsRearStatus = static_object_df["SppPointListRear_eSigStatus"]
        semanticPointsLeftStatus = static_object_df["SppPointListLeft_eSigStatus"]
        semanticPointsRightStatus = static_object_df["SppPointListRight_eSigStatus"]

        polylineStatus = (polylinesFrontStatus | polylinesRearStatus | polylinesLeftStatus | polylinesRightStatus)
        pointsStatus = (semanticPointsFrontStatus | semanticPointsRearStatus | semanticPointsLeftStatus | semanticPointsRightStatus)
        ussPointsStatus = static_object_df["UssPointList_eSigStatus"]

        #if any signal status is ok from points, we expect some points detections
        anyPointsDetected = ((pointsStatus & ussPointsStatus).sum() > 0)
        anyPolylineDetected = (polylineStatus.sum() > 0)

        description = "The evaluation of the signal is <b>PASSED</b>."
        if not anyPointsDetected & anyPolylineDetected:
            # filter only valid outputs
            static_object_df = static_object_df[static_object_df["SGF_sig_status"] == 1]
            static_object_df = static_object_df[static_object_df["numPolygons"] > 0]

            # num of static objects per frame
            numStaticObjects = static_object_df["numPolygons"].values
            numFrames = static_object_df.shape[0]
            objectClasses = static_object_df.filter(regex="semanticClass").values

            # if signals found
            if objectClasses.shape[1] > 0:
                curbAtTimestamps = []
                for i in range(numFrames):
                    objInFrame = numStaticObjects[i]
                    frameObjectsClasses = objectClasses[i, 0:objInFrame]
                    isACurb = frameObjectsClasses == 3
                    if np.any(isACurb):
                        curbAtTimestamps.append(static_object_df["SGF_timestamp"].values[i])
                if len(curbAtTimestamps) > 0:
                    test_result = fc.PASS
                else:
                    description = "The evaluation of the signal is <b>FAILED</b>."
                    test_result = fc.FAIL
            else:
                description = " ".join("Signal <b>not evaluated</b> because it is not available.".split())
                test_result = fc.NOT_ASSESSED
        else:
                description = " ".join("Signal <b>not evaluated</b> because input signals not available.".split())
                test_result = fc.NOT_ASSESSED

        signal_summary[signalEvaluated] = description

        remark = (
            "Curb objects should be detected if curbs are present in the recording and only svc polylines are available"
        )
        self.sig_sum = fh.convert_dict_to_pandas(
            signal_summary=signal_summary,
        )
        plot_titles.append("Checking if curb objects created based on SVC Semantic Polylines")
        plots.append(self.sig_sum)
        remarks.append(remark)
        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1995566"],
            fc.TESTCASE_ID: ["1522136"],
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
    requirement="1522136",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_8OJg5ExLEe6M5-WQsF_-tQ&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F23890&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg",
)
@testcase_definition(
    name="SWRT_CNC_SGF_CurbObjectsFromSVCSemanticPolylines",
    description="This test case checks in case SGF has curb output when only SVC semantic polylines input is received.",
)
@register_inputs("/parking")
class CurbObjectsFromSVCSemanticPolylines(TestCase):
    """Example test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepCurbObjectsFromSVCSemanticPolyline,
        ]
