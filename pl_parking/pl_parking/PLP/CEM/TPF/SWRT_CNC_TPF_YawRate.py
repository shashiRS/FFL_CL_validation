"""TestCases checking the yaw rate of the detected object."""

import logging
import math
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

FT_TPF_YAW_RATE = "FT_TPF_YAW_RATE"

tpf_object = fh_tpf.TPFSignals()


@teststep_definition(
    step_number=1,
    name="YawRate",
    description="This test will verify if the yaw rate and yaw rate standard deviation provided by TPF are defined "
    "and are in [-pi, pi] rad/s and [0, 6] rad/s range.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPF_YAW_RATE, fh_tpf.TPFSignals)
class TestStepYawRate(TestStep):
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
        yawrate_error_list = []
        yawrate_sd_error_list = []
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        tpf_reader = self.readers[FT_TPF_YAW_RATE]
        tpf_reader = tpf_reader.iloc[10:]  # First timestamps might not be initialized, so remove them

        sig = tpf_object.Columns
        required_tpf_signals = [
            sig.SIGSTATUS,
            sig.SIGTIMESTAMP,
            (sig.OBJECTS_OBJECTCLASS, 0),
            (sig.OBJECTS_CLASSPROBABILITY, 0),
            (sig.OBJECTS_YAWRATE, 0),
            (sig.OBJECTS_YAWRATESTANDARDDEVIATION, 0),
            (sig.OBJECTS_ID, 0),
            sig.NUMBER_OF_OBJECTS,
        ]

        yawrate_description = "The evaluation of the signal is <b>PASSED</b>."
        yawrate_sd_description = "The evaluation of the signal is <b>PASSED</b>."

        number_of_unavailable_signals = 0
        for signal_name in required_tpf_signals:
            if signal_name not in list(tpf_reader.columns):
                number_of_unavailable_signals += 1

        if number_of_unavailable_signals == 0:
            # The yaw rate and yaw rate sd should be in [0, 2*pi] radians range and [0, 6] radians range.
            for _, row in tpf_reader.iterrows():
                number_of_objects = int(row[sig.NUMBER_OF_OBJECTS])
                signal_state = row[sig.SIGSTATUS]
                # Run the test only if the signal state is ok
                if signal_state == fc.AL_SIG_STATE_OK:
                    for object_index in range(number_of_objects):
                        object_yawrate = row[(sig.OBJECTS_YAWRATE, object_index)]
                        object_yawrate_sd = row[(sig.OBJECTS_YAWRATESTANDARDDEVIATION, object_index)]

                        if object_yawrate < -math.pi or object_yawrate > math.pi:
                            error_dict = {
                                "Signal name": tpf_object.get_properties()[sig.OBJECTS_YAWRATE],
                                "Timestamp": row[sig.SIGTIMESTAMP],
                                "Object ID": row[(sig.OBJECTS_ID, object_index)],
                                "Class": row[(sig.OBJECTS_OBJECTCLASS, object_index)],
                                "Confidence": row[(sig.OBJECTS_CLASSPROBABILITY, object_index)],
                                "yawrate": object_yawrate,
                                "yawrate SD": object_yawrate_sd,
                                "Description": "out of range",
                                "Expected result": "[-pi, .pi]",
                            }
                            if test_result != fc.FAIL:
                                yawrate_description = " ".join(
                                    f"The evaluation of the signal is <b>FAILED</b> at timestamp {error_dict['Timestamp']} "
                                    f"for object with ID {error_dict['Object ID']} and class {error_dict['Class']} and "
                                    f"confidence {error_dict['Confidence']} with <b>yaw rate</b> "
                                    f"{error_dict['Yaw Rate']} which is {error_dict['Description']} "
                                    f"({error_dict['Expected result']}).".split()
                                )
                            test_result = fc.FAIL
                            yawrate_error_list.append(error_dict)

                        if object_yawrate_sd < 0 or object_yawrate_sd > 6:
                            error_dict = {
                                "Signal name": tpf_object.get_properties()[sig.OBJECTS_YAWRATESTANDARDDEVIATION],
                                "Timestamp": row[sig.SIGTIMESTAMP],
                                "Object ID": row[(sig.OBJECTS_ID, object_index)],
                                "Class": row[(sig.OBJECTS_OBJECTCLASS, object_index)],
                                "Confidence": row[(sig.OBJECTS_CLASSPROBABILITY, object_index)],
                                "Yaw Rate": object_yawrate,
                                "Yaw Rate SD": object_yawrate_sd,
                                "Description": "out of range",
                                "Expected result": "[0, 6]",
                            }
                            if test_result != fc.FAIL:
                                yawrate_sd_description = " ".join(
                                    f"The evaluation of the signal is <b>FAILED</b> at timestamp {error_dict['Timestamp']} "
                                    f"for object with ID {error_dict['Object ID']} and class {error_dict['Class']} and "
                                    f"confidence {error_dict['Confidence']} with <b>yaw rate standard deviation</b> "
                                    f"{error_dict['Yaw Rate SD']} which is {error_dict['Description']} "
                                    f"({error_dict['Expected result']}).".split()
                                )
                            test_result = fc.FAIL
                            yawrate_sd_error_list.append(error_dict)
        else:
            yawrate_description = " ".join("Signal <b>not evaluated</b> because it is not available.".split())
            yawrate_sd_description = " ".join("Signal <b>not evaluated</b> because it is not available.".split())
            test_result = fc.NOT_ASSESSED

        signal_summary[tpf_object.get_properties()[sig.OBJECTS_YAWRATE][0]] = yawrate_description
        signal_summary[tpf_object.get_properties()[sig.OBJECTS_YAWRATESTANDARDDEVIATION][0]] = yawrate_sd_description
        remark = (
            "Yaw Rate and Yaw Rate Standard Deviation are verified to be available and in range.<br>"
            "-pi <= Yaw Rate <= pi [rad/s]<br>"
            "0 <= Yaw Rate Standard Deviation <= 6 [rad/s]<br>"
        )
        self.sig_sum = fh.convert_dict_to_pandas(
            signal_summary=signal_summary,
        )
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append(remark)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2032318"],
            fc.TESTCASE_ID: ["88703"],
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
    requirement="2032318",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_4spLAeVAEe6f_fKhM-zv_g&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@testcase_definition(
    name="YawRate",
    description="This test will verify if the yaw rate and yaw rate standard deviation provided by TPF are defined "
    "and are in [-pi, pi] rad/s and [0, 6] rad/s range.",
)
@register_inputs("/parking")
class YawRate(TestCase):
    """Timestamp test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepYawRate,
        ]
