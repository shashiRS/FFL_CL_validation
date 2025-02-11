"""TestCases checking the existence probability is in (0, 1] range."""

import logging
import os
import sys

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
import pl_parking.PLP.CEM.TPF.ft_helper as fh_tpf

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

FT_TPF_EXISTENCE_PROBABILITY = "FT_TPF_EXISTENCE_PROBABILITY"

tpf_object = fh_tpf.TPFSignals()


@teststep_definition(
    step_number=1,
    name="ExistenceProbability",
    description="This test will verify if the existence certainty is in (0, 1] range.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPF_EXISTENCE_PROBABILITY, fh_tpf.TPFSignals)
class TestStepExistenceProbability(TestStep):
    """Test step definition."""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")

        test_result = fc.PASS
        plot_titles, plots, remarks = fh.rep([], 3)
        signal_summary = {}
        error_list = []
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        tpf_reader = self.readers[FT_TPF_EXISTENCE_PROBABILITY]
        tpf_reader = tpf_reader.iloc[10:]  # First timestamps might not be initialized, so remove them

        sig = tpf_object.Columns
        required_tpf_signals = [
            sig.SIGSTATUS,
            sig.SIGTIMESTAMP,
            (sig.OBJECTS_OBJECTCLASS, 0),
            (sig.OBJECTS_CLASSPROBABILITY, 0),
            (sig.OBJECTS_EXISTENCECERTAINTY, 0),
            (sig.OBJECTS_ID, 0),
            sig.NUMBER_OF_OBJECTS,
        ]

        description = "The evaluation of the signal is <b>PASSED</b>."

        number_of_unavailable_signals = 0
        for signal_name in required_tpf_signals:
            if signal_name not in list(tpf_reader.columns):
                number_of_unavailable_signals += 1

        if number_of_unavailable_signals == 0:
            # Verify if the existence probability is in the defined range (0, 1]
            for _, row in tpf_reader.iterrows():
                number_of_objects = int(row[sig.NUMBER_OF_OBJECTS])
                signal_state = row[sig.SIGSTATUS]
                # Run the test only if the signal state is ok
                if signal_state == fc.AL_SIG_STATE_OK:
                    for object_index in range(number_of_objects):
                        object_confidence = row[(sig.OBJECTS_CLASSPROBABILITY, object_index)]
                        object_class = row[(sig.OBJECTS_OBJECTCLASS, object_index)]
                        existence_certainty = row[(sig.OBJECTS_EXISTENCECERTAINTY, object_index)]
                        if object_confidence <= 0 or object_confidence > 1:
                            error_dict = {
                                "Signal name": tpf_object.get_properties()[sig.OBJECTS_EXISTENCECERTAINTY],
                                "Timestamp": row[sig.SIGTIMESTAMP],
                                "Object ID": row[(sig.OBJECTS_ID, object_index)],
                                "Class": object_class,
                                "Confidence": object_confidence,
                                "Certainty": existence_certainty,
                                "Description": "out of range",
                                "Expected result": "(0, 1]",
                            }
                            if test_result != fc.FAIL:
                                description = " ".join(
                                    f"The evaluation of the signal is <b>FAILED</b> at timestamp {error_dict['Timestamp']} "
                                    f"for object with ID {error_dict['Object ID']} and class {error_dict['Class']} and "
                                    f"confidence <b>{error_dict['Confidence']}</b> with <b>object certainty>/b> "
                                    f"{error_dict['Certainty']} which is {error_dict['Description']} "
                                    f"({error_dict['Expected result']}).".split()
                                )
                            test_result = fc.FAIL
                            error_list.append(error_dict)
        else:
            description = " ".join("Signal <b>not evaluated</b> because it is not available.".split())
            test_result = fc.NOT_ASSESSED

        signal_summary[tpf_object.get_properties()[sig.OBJECTS_EXISTENCECERTAINTY][0]] = description
        remark = "Existence certainty should be in (0, 1] range."
        self.sig_sum = fh.convert_dict_to_pandas(
            signal_summary=signal_summary,
        )
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append(remark)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2032269"],
            fc.TESTCASE_ID: ["88683"],
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
    requirement="2032269",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_mKPRsOU-Ee6f_fKhM-zv_g&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@testcase_definition(
    name="ExistenceProbability",
    description="This test will verify if the existence certainty is in (0, 1] range.",
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
