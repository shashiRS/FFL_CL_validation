"""Test Case checking dynamic property of fused objects to be in the defined list"""

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

FT_TPF_DYNAMIC_PROPERTY = "FT_TPF_DYNAMIC_PROPERTY"

tpf_object = fh_tpf.TPFSignals()


@teststep_definition(
    step_number=1,
    name="ValidateDynamicProperty",
    description="This test will verify if the dynamic property of fused objects is within the defined list: unknown,"
    " moving, stationary or stopped.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPF_DYNAMIC_PROPERTY, fh_tpf.TPFSignals)
class TestStepDynamicProperty(TestStep):
    """Test step definition."""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the test-step."""
        super().__init__()
        self.sig_sum = None

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

        tpf_reader = self.readers[FT_TPF_DYNAMIC_PROPERTY]
        tpf_reader = tpf_reader.iloc[10:]  # First timestamps might not be initialized, so remove them

        sig = tpf_object.Columns
        required_tpf_signals = [
            sig.SIGSTATUS,
            sig.SIGTIMESTAMP,
            (sig.OBJECTS_ID, 0),
            (sig.OBJECTS_OBJECTCLASS, 0),
            sig.NUMBER_OF_OBJECTS,
            (sig.OBJECTS_DYNAMICPROPERTY, 0),
        ]

        description = "The evaluation of the signal is <b>PASSED</b>."

        number_of_unavailable_signals = 0
        for signal_name in required_tpf_signals:
            if signal_name not in list(tpf_reader.columns):
                number_of_unavailable_signals += 1

        if number_of_unavailable_signals == 0:
            # Verify if dynamic property of fused objects is in [0, 3] range
            for _, row in tpf_reader.iterrows():
                number_of_objects = int(row[sig.NUMBER_OF_OBJECTS])
                signal_state = row[sig.SIGSTATUS]
                # Run the test only if the signal state is ok
                if signal_state == fc.AL_SIG_STATE_OK:
                    for object_index in range(number_of_objects):
                        object_dynamic_property = row[(sig.OBJECTS_DYNAMICPROPERTY, object_index)]
                        object_class = row[(sig.OBJECTS_OBJECTCLASS, object_index)]
                        object_id = row[(sig.OBJECTS_ID, object_index)]

                        if (
                            object_dynamic_property != 0
                            and object_dynamic_property != 1
                            and object_dynamic_property != 2
                            and object_dynamic_property != 3
                        ):
                            error_dict = {
                                "Signal name": tpf_object.get_properties()[sig.OBJECTS_CLASSPROBABILITY],
                                "Timestamp": row[sig.SIGTIMESTAMP],
                                "Object ID": object_id,
                                "Class": object_class,
                                "Dynamic Property": object_dynamic_property,
                                "Description": "Dynamic Property outside of defined range [0, 3]",
                                "Expected result": "Dynamic Property to be within [0, 3] interval",
                            }
                            if test_result != fc.FAIL:
                                description = " ".join(
                                    f"The evaluation of the signal is <b>FAILED</b> at timestamp "
                                    f"{error_dict['Timestamp']} for object with ID {error_dict['Object ID']} and "
                                    f"class {error_dict['Class']} with dynamic property"
                                    f" <b>{error_dict['Dynamic Property']} which is {error_dict['Description']} "
                                    f"({error_dict['Expected result']}).".split()
                                )
                            test_result = fc.FAIL
                            error_list.append(error_dict)

        else:
            description = " ".join("Signal <b>not evaluated</b> because it is not available.".split())
            test_result = fc.NOT_ASSESSED

        signal_summary[tpf_object.get_properties()[sig.OBJECTS_DYNAMICPROPERTY][0]] = description
        remark = (
            "In each frame, check if dynamic property of fused objects is within [0, 3] range.<br/>"
            "UNKNOWN - 0 <br/>"
            "MOVING - 1 <br/>"
            "STATIONARY - 2 <br/>"
            "STOPPED - 3"
        )
        self.sig_sum = fh.convert_dict_to_pandas(
            signal_summary=signal_summary,
        )
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append(remark)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1599257"],
            fc.TESTCASE_ID: ["89681"],
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
    requirement="1599257",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_N41D4Gz7Ee6YqIugsJ-rgQ&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@testcase_definition(
    name="ValidateDynamicProperty",
    description="This test will verify if the dynamic property of fused objects is within the defined list: unknown,"
    " moving, stationary or stopped.",
)
@register_inputs("/parking")
class DynamicProperty(TestCase):
    """Timestamp test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepDynamicProperty,
        ]
