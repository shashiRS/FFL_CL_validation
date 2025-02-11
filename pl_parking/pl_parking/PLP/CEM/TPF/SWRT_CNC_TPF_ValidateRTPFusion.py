"""Test Case checking if the RPT fusion was performed"""

import logging
import os
import sys

import pandas as pd
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
import pl_parking.PLP.CV.TPP.ft_helper as fh_tpp

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

FT_TPF_RTPFUSION = "FT_TPF_RTPFUSION"
FT_TPP_RTPFUSION = "FT_TPP_RTPFUSION"

tpf_object = fh_tpf.TPFSignals()
tpp_object = fh_tpp.TPPSignals()


def get_number_of_objects_for_current_frame_tpp(row: pd.Series) -> int:
    """
    Compute the sum of the number of cuboids and bounding boxes for each camera for the given time frame.
    :param row: Series containing a time frame.
    :return: Return the number of objects for the current frame.
    """
    number_of_objects = 0
    sig = tpp_object.Columns
    number_of_objects += int(row[sig.NUM_CUBOID_FRONT])
    number_of_objects += int(row[sig.NUM_BBOX_FRONT])
    number_of_objects += int(row[sig.NUM_CUBOID_REAR])
    number_of_objects += int(row[sig.NUM_BBOX_REAR])
    number_of_objects += int(row[sig.NUM_CUBOID_LEFT])
    number_of_objects += int(row[sig.NUM_BBOX_LEFT])
    number_of_objects += int(row[sig.NUM_CUBOID_RIGHT])
    number_of_objects += int(row[sig.NUM_BBOX_RIGHT])

    return number_of_objects


@teststep_definition(
    step_number=1,
    name="ValidateRTPFusion",
    description="This test will verify if the RTP fusion is performed by checking if TPF is providing output FTPs when "
    "TPP is providing dynamic objects.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPF_RTPFUSION, fh_tpf.TPFSignals)
@register_signals(FT_TPP_RTPFUSION, fh_tpp.TPPSignals)
class TestStepValidateRTPFusion(TestStep):
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

        tpf_reader = self.readers[FT_TPF_RTPFUSION]
        tpp_reader = self.readers[FT_TPP_RTPFUSION]
        tpf_reader = tpf_reader.iloc[10:]  # First timestamps might not be initialized, so remove them
        tpp_reader = tpp_reader.iloc[10:]  # First timestamps might not be initialized, so remove them

        sig_tpf = tpf_object.Columns
        sig_tpp = tpp_object.Columns
        required_tpf_signals = [
            sig_tpf.SIGSTATUS,
            sig_tpf.SIGTIMESTAMP,
            sig_tpf.NUMBER_OF_OBJECTS,
        ]
        required_tpp_signals = [
            sig_tpp.SIGTIMESTAMP_FRONT,
            sig_tpp.SIGSTATUS_FRONT,
            sig_tpp.NUM_CUBOID_FRONT,
            sig_tpp.NUM_BBOX_FRONT,
            sig_tpp.SIGTIMESTAMP_REAR,
            sig_tpp.SIGSTATUS_REAR,
            sig_tpp.NUM_CUBOID_REAR,
            sig_tpp.NUM_BBOX_REAR,
            sig_tpp.SIGTIMESTAMP_LEFT,
            sig_tpp.SIGSTATUS_LEFT,
            sig_tpp.NUM_CUBOID_LEFT,
            sig_tpp.NUM_BBOX_LEFT,
            sig_tpp.SIGTIMESTAMP_RIGHT,
            sig_tpp.SIGSTATUS_RIGHT,
            sig_tpp.NUM_CUBOID_RIGHT,
            sig_tpp.NUM_BBOX_RIGHT,
        ]

        description = "The evaluation of the signal is <b>PASSED</b>."

        # Count how many of the required signals are not available
        number_of_unavailable_signals = 0
        for signal_name in required_tpf_signals:
            if signal_name not in list(tpf_reader.columns):
                number_of_unavailable_signals += 1
        for signal_name in required_tpp_signals:
            if signal_name not in list(tpp_reader.columns):
                number_of_unavailable_signals += 1

        if number_of_unavailable_signals == 0:
            # Verify if TPF provides FTPs when RTPs are received
            idx_2 = 0  # index before the previous index
            idx_1 = 0  # previous index
            idx_0 = 0  # current index
            step = 0  # used to make sure all the indexes were populated
            for idx, row in tpf_reader.iterrows():  # Remember the last 3 indexes
                idx_2 = idx_1  # index before the previous index
                idx_1 = idx_0  # previous index
                idx_0 = idx  # current index
                # Check the last 3 time frames for TPP detections
                if step > 3:
                    number_of_tpf_objects = int(row[sig_tpf.NUMBER_OF_OBJECTS])
                    signal_state = row[sig_tpf.SIGSTATUS]
                    # Run the test only if the signal ValidateRTPFusion is ok
                    if signal_state == fc.AL_SIG_STATE_OK:
                        # If there are any detections then TPF is performing fusion
                        # If there are no FTP output, check if there are any input TPs provided
                        if number_of_tpf_objects == 0:
                            # Both readers will have the same number of rows because the same recording is used
                            current_tpp_row = tpp_reader[tpp_reader["mts_ts"] == idx_0]
                            prev_tpp_row_1 = tpp_reader[tpp_reader["mts_ts"] == idx_1]
                            prev_tpp_row_2 = tpp_reader[tpp_reader["mts_ts"] == idx_2]
                            current_tpp_num_obj = get_number_of_objects_for_current_frame_tpp(current_tpp_row)
                            prev_tpp_num_obj_1 = get_number_of_objects_for_current_frame_tpp(prev_tpp_row_1)
                            prev_tpp_num_obj_2 = get_number_of_objects_for_current_frame_tpp(prev_tpp_row_2)

                            tpp_num_obj = current_tpp_num_obj + prev_tpp_num_obj_1 + prev_tpp_num_obj_2

                            # FTP is 0 but RTP > 0 -> TPF shall provide FTP
                            if (
                                current_tpp_num_obj > 0
                                and prev_tpp_num_obj_1 > 0  # At least 1 RTP on the current frame
                                and prev_tpp_num_obj_2  # At least 1 RTP on the previous frame
                                > 0  # At least 1 RTP on the frame before the previous
                            ):
                                error_dict = {
                                    "Signal name": tpf_object.get_properties()[sig_tpf.NUMBER_OF_OBJECTS],
                                    "Timestamp": row[sig_tpf.SIGTIMESTAMP],
                                    "Description": "no FTPs provided",
                                    "Expected result": f"number of RTP on the last 3 frames: {tpp_num_obj}",
                                }
                                if test_result != fc.FAIL:
                                    description = " ".join(
                                        f"The evaluation of the signal is <b>FAILED</b> at timestamp "
                                        f"{error_dict['Timestamp']} with {error_dict['Description']} "
                                        f"({error_dict['Expected result']}).".split()
                                    )
                                test_result = fc.FAIL
                                error_list.append(error_dict)
                step += 1
        else:
            description = " ".join("Signal <b>not evaluated</b> because required signals are not available.".split())
            test_result = fc.NOT_ASSESSED

        signal_summary[tpf_object.get_properties()[sig_tpf.NUMBER_OF_OBJECTS][0]] = description
        remark = (
            "TPF is expected to provide fused traffic participants(FTP) when it receives traffic participants(RTP) "
            "on the previous frames.<br>"
            "If at least one object is received on each of the last 3 time frames, then TPF shall provide at least one "
            "FTP."
        )
        self.sig_sum = fh.convert_dict_to_pandas(
            signal_summary=signal_summary,
        )
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append(remark)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1521990"],
            fc.TESTCASE_ID: ["90178"],
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
    requirement="1521990",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_zEzBpkxJEe6M5-WQsF_-tQ&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@testcase_definition(
    name="ValidateRTPFusion",
    description="This test will verify if the RTP fusion is performed by checking if TPF is providing output FTPs "
    "when TPP is providing dynamic objects.",
)
@register_inputs("/parking")
class ValidateRTPFusion(TestCase):
    """Timestamp test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepValidateRTPFusion,
        ]
