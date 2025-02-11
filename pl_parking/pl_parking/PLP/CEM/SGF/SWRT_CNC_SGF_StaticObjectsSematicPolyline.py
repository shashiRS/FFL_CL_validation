#!/usr/bin/env python3
"""SWRT_CNC_SGF_StaticObjectsSematicPolyline"""

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
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    convert_dict_to_pandas,
    get_color,
    rep,
)
from pl_parking.PLP.CEM.SGF.ft_helper import SGFSignals

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "<uib11434>"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "StaticObjectsFromSVCSemanticPolyline"
example_obj = SGFSignals()


@teststep_definition(
    step_number=1,
    name="Static Objects From SVC Semantic Polyline",
    description="This test case checks if SGF has output for curb objects when only SVC semantic polyline input is received.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SGFSignals)
class TestStepStaticObjectsFromSVCSemanticPolyline(TestStep):
    """TestStep for analyzing static objects detected from SVC Semantic polyline, utilizing a custom report."""

    custom_report = MfCustomTeststepReport

    # TODO: update info when a re-simulated bsig file is available
    TEST_CASE_MAP = {
        "SWRT_CNC_SGF_StaticObjectsSematicPolyline": {
            "Recording Name": "2024.09.16_at_11.45.50_radar-mi_9029_PLP-56405_scenario2_1_extract",
            "Start Timestamp": 33172695,
            "End Timestamp": 63673551,
        }
    }

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()
        self.test_result = fc.INPUT_MISSING
        self.sig_sum = None

    @staticmethod
    def get_test_case_inputs(test_script_filename, test_case_map):
        """Get the necessary input for test case evaluation."""
        recording_name = None
        start_timestamp = None
        end_timestamp = None
        test_case = test_case_map.get(test_script_filename, None)
        if test_case is not None:
            recording_name = test_case.get("Recording Name", None)
            start_timestamp = test_case.get("Start Timestamp", None)
            end_timestamp = test_case.get("End Timestamp", None)

        return recording_name, start_timestamp, end_timestamp

    def process(self):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        _log.debug("Starting processing...")

        # Define variables
        test_pass_rate = 50.0  # [percentage]

        # Update the details from the results page with the needed information. All the information from
        # self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks, if they are needed.
        # Plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)

        # Initializing the dictionary with data for final evaluation table
        signal_summary = {}

        # Initializing the list for preconditions checks
        precondition = []

        # Load signals
        reader = self.readers[SIGNAL_DATA]

        recording_name_with_extention = os.path.split(self.artifacts[0].file_path)[1]
        recording_name = recording_name_with_extention.split(".bsig")[0]
        test_script_filename = os.path.basename(__file__).split(".py")[0]

        # extract rec name and timestamps from TEST_CASE_MAP dictionary
        expected_rec_name, start_timestamp, end_timestamp = self.get_test_case_inputs(
            test_script_filename, self.TEST_CASE_MAP
        )
        if expected_rec_name is not None:
            if recording_name == expected_rec_name:
                # TODO: uncomment when a re-simulated bsig is available
                # uss_point_list_sig_status = reader.get(SGFSignals.Columns.USS_POINT_LIST_SIGSTATUS)
                # spp_point_list_front_sig_status = reader.get(SGFSignals.Columns.SPP_POINT_LIST_FRONT_SIGSTATUS)
                # spp_point_list_rear_sig_status = reader.get(SGFSignals.Columns.SPP_POINT_LIST_REAR_SIGSTATUS)
                # spp_point_list_left_sig_status = reader.get(SGFSignals.Columns.SPP_POINT_LIST_LEFT_SIGSTATUS)
                # spp_point_list_right_sig_status = reader.get(SGFSignals.Columns.SPP_POINT_LIST_RIGHT_SIGSTATUS)
                spp_polyline_list_front_sig_status = reader.get(SGFSignals.Columns.SPP_POLYLINE_LIST_FRONT_SIGSTATUS)
                spp_polyline_list_rear_sig_status = reader.get(SGFSignals.Columns.SPP_POLYLINE_LIST_REAR_SIGSTATUS)
                spp_polyline_list_left_sig_status = reader.get(SGFSignals.Columns.SPP_POLYLINE_LIST_LEFT_SIGSTATUS)
                spp_polyline_list_right_sig_status = reader.get(SGFSignals.Columns.SPP_POLYLINE_LIST_RIGHT_SIGSTATUS)
                sgf_timestamps = reader.get(SGFSignals.Columns.SGF_TIMESTAMP)
                number_of_objects = reader.get(SGFSignals.Columns.SGF_NUMBER_OF_POLYGONS)

                start_index = int(sgf_timestamps[sgf_timestamps == start_timestamp].index[0])
                end_index = int(sgf_timestamps[sgf_timestamps == end_timestamp].index[0])

                # TODO: uncomment the inputs check when a re-simulated bsig is available
                # check if SGF received data only from SVC spp_polyline
                # if not (uss_point_list_sig_status.loc[start_index:end_index] == 0).all():
                #     precondition.append(False)
                # if not (spp_point_list_front_sig_status.loc[start_index:end_index] == 0).all():
                #     precondition.append(False)
                # if not (spp_point_list_rear_sig_status.loc[start_index:end_index] == 0).all():
                #     precondition.append(False)
                # if not (spp_point_list_left_sig_status.loc[start_index:end_index] == 0).all():
                #     precondition.append(False)
                # if not (spp_point_list_right_sig_status.loc[start_index:end_index] == 0).all():
                #     precondition.append(False)
                if not spp_polyline_list_front_sig_status.loc[start_index:end_index].isin([1, 2]).all():
                    precondition.append(False)
                if not spp_polyline_list_rear_sig_status.loc[start_index:end_index].isin([1, 2]).all():
                    precondition.append(False)
                if not spp_polyline_list_left_sig_status.loc[start_index:end_index].isin([1, 2]).all():
                    precondition.append(False)
                if not spp_polyline_list_right_sig_status.loc[start_index:end_index].isin([1, 2]).all():
                    precondition.append(False)

                if any(element is False for element in precondition):
                    description = " ".join("Not ALL preconditions are met".split())
                else:
                    # count of values grater than 0 for a subset of the Series
                    subset = number_of_objects.loc[start_index:end_index]
                    detected = (subset > 0).sum()
                    total_count = len(subset)

                    detection_rate = detected / total_count * 100

                    if detection_rate >= test_pass_rate:
                        self.test_result = fc.PASS
                        description = " ".join(
                            f"The test is <B>PASSED</b> because the object detection rate is {detection_rate:.2f}%. "
                            f"The minimum threshold is {test_pass_rate}%.".split()
                        )
                    else:
                        self.test_result = fc.FAIL
                        description = " ".join(
                            f"The test is <B>FAILED</b> because the object detection rate is {detection_rate:.2f}%. "
                            f"The minimum threshold is {test_pass_rate}%.".split()
                        )
            else:
                description = " ".join(f"Simulation file for recording {expected_rec_name} is missing".split())
        else:
            description = " ".join("Expected recording is missing, check TEST_CASE_MAP".split())

        summary_key = example_obj.get_properties()[SGFSignals.Columns.SGF_NUMBER_OF_POLYGONS][0]
        signal_summary[summary_key] = description

        remark = " ".join("Check if SGF has output for curb when only SVC semantic polyline input is received.".split())

        # The signal summary and observations will be converted to pandas
        # and finally the html table will be created with them
        self.sig_sum = convert_dict_to_pandas(
            signal_summary=signal_summary,
            table_remark=remark,
        )
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        # Report result status
        if self.test_result == fc.INPUT_MISSING:
            self.result.measured_result = DATA_NOK
        elif self.test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif self.test_result == fc.FAIL:
            self.result.measured_result = FALSE

        result_df = {
            "Verdict": {"value": self.test_result.title(), "color": get_color(self.test_result)},
            fc.REQ_ID: ["1522133, 1522137, 1995547"],
            fc.TESTCASE_ID: ["39239"],
            fc.TEST_DESCRIPTION: [
                "Check if SGF has output for curb when only SVC semantic polyline input is received."
            ],
        }

        self.result.details["Additional_results"] = result_df

        # Add the plots in html page
        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")


@verifies("1522133, 1522137")
@testcase_definition(
    name="SWRT_CNC_SGF_StaticObjectsSematicPolyline",
    description="This test case checks if SGF has output when only SVC semantic polyline input is received.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_rqqA0N-tEe62R7UY0u3jZg&oslc_config.context=https%3A%2F%2F"
    "jazz.conti.de%2Fgc%2Fconfiguration%2F17100&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2F"
    "rm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class StaticObjectsFromSVCSemanticPolyline(TestCase):
    """Test case definition."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepStaticObjectsFromSVCSemanticPolyline,
        ]
