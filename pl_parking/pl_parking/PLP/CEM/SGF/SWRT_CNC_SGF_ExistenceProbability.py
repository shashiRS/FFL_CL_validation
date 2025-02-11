"""TestCases checking the existence probability is in (0, 1] range."""

import logging
import os
import sys

import numpy as np
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

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.PLP.CEM.inputs.input_CemSgfReader import SGFReader
from pl_parking.PLP.CEM.SGF.ft_helper import SGFSignals

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

SIGNAL_DATA = "FT_SGF_EXISTENCE_PROBABILITY"
sgf_obj = SGFSignals()


@teststep_definition(
    step_number=1,
    name="ExistenceProbability",
    description="This test will verify if the existence certainty is in (0, 1] range.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SGFSignals)
class TestStepExistenceProbability(TestStep):
    """Test step definition."""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")

        plot_titles, plots, remarks = fh.rep([], 3)
        signal_summary = {}
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        reader = self.readers[SIGNAL_DATA]
        input_reader = SGFReader(reader)
        static_object_df = input_reader.data

        # filter only valid outputs
        static_object_df = static_object_df[static_object_df["SGF_sig_status"] == 1]
        static_object_df = static_object_df[static_object_df["numPolygons"] > 0]

        # num of static objects per frame
        numStaticObjects = static_object_df["numPolygons"].values
        numFrames = static_object_df.shape[0]

        test_result = fc.PASS
        description = "The evaluation of the signal is <b>PASSED</b>."

        signalEvaluated = sgf_obj.get_properties()[sgf_obj.Columns.SGF_OBJECT_EXISTENCE_PROBABILITY][0]

        # this list contains the invalid timestamps, should be empty
        invalidTimestamps = []

        # existance prob array of shape(num frames, num of object)
        # existenceProbabilities[frameNum, objectNum]
        existenceProbabilities = static_object_df.filter(regex="existenceProbability").values

        for i in range(numFrames):
            objInFrame = numStaticObjects[i]
            frameObjExistanceProb = existenceProbabilities[i, 0:objInFrame]
            validConfidence = (frameObjExistanceProb >= 0) & (frameObjExistanceProb <= 1.0)
            if not np.all(validConfidence):
                invalidTimestamps.append(static_object_df["SGF_timestamp"].values[i])
                error_dict = {
                    "Signal name": signalEvaluated,
                    "Timestamp": static_object_df["SGF_timestamp"].values[i],
                    "Description": "out of range",
                    "Expected result": "(0, 1]",
                }
                description = " ".join(
                    f"The evaluation of the signal is <b>FAILED</b> at timestamp {error_dict['Timestamp']} "
                    f"due to {error_dict['Description']} "
                    f"({error_dict['Expected result']}).".split()
                )
                test_result = fc.FAIL

                break

        signal_summary[signalEvaluated] = description
        remark = "Existence certainty should be in (0, 1] range."
        self.sig_sum = fh.convert_dict_to_pandas(
            signal_summary=signal_summary,
        )
        plot_titles.append("Checking static objects confidence")
        plots.append(self.sig_sum)
        remarks.append(remark)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1995566"],
            fc.TESTCASE_ID: ["90410"],
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
    requirement="1995566",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_J04cYN-xEe62R7UY0u3jZg&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F23890&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg",
)
@testcase_definition(
    name="ExistenceProbability",
    description="This test will verify if the existence certainty is in [0.0, 1.0] range.",
)
@register_inputs("/parking")
class ExistenceProbability(TestCase):
    """Timestamp test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepExistenceProbability,
        ]
