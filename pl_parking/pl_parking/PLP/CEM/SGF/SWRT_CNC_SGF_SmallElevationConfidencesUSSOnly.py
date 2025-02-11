#!/usr/bin/env python3
"""SWRT_CNC_SGF_SmallElevationConfidencesUSSOnly"""

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
from pl_parking.PLP.CEM.constants import ConstantsCem as cc
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

SIGNAL_DATA = "SmallElevationConfidencesUSSOnly"
example_obj = SGFSignals()


@teststep_definition(
    step_number=1,
    name="Small Elevation Confidences USS Only",
    description="This test case checks in case SGF has only USS input and do not contain elevation information, "
    "SGF shall provide the output Static Objects elevation category confidences lower than "
    "{AP_E_STA_OBJ_ELEV_CONF_MIN_NU} confidences.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SGFSignals)
class TestStepSmallElevationConfidencesUSSOnly(TestStep):
    """TestStep for analyzing small evaluation confidence for objects detected only from USS."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()
        self.test_result = fc.INPUT_MISSING
        self.sig_sum = None

    @staticmethod
    def check_object_confidence(reader, signal, index, frame, number_of_objects):
        """Check if object confidence is lower than threshold {AP_E_STA_OBJ_ELEV_CONF_MIN_NU}"""
        list_of_errors = []
        test_result = True
        description = (
            "The evaluation is <b>PASSED</b>: "
            f"Value of '{signal}' is always lower then <b>{cc.AP_E_STA_OBJ_ELEV_CONF_MIN_NU}</b> for all static "
            f"objects."
        )
        for i in range(0, number_of_objects):
            confidence = reader.at[index, (signal, i)]
            if confidence >= cc.AP_E_STA_OBJ_ELEV_CONF_MIN_NU:
                err = {
                    "sgf_timestamp": frame,
                    "sgf_confidence": confidence,
                }
                if test_result is True:
                    # Store the description for the first error only
                    description = " ".join(
                        f"The evaluation is <b>FAILED</b> at timestamp {err['sgf_timestamp']} "
                        f"because value of '{signal}' is {err['sgf_confidence']}. It should be lower than "
                        f"<b>{cc.AP_E_STA_OBJ_ELEV_CONF_MIN_NU}</b>.".split()
                    )
                test_result = False
                list_of_errors.append(err)
        return test_result, description, list_of_errors

    def process(self):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        _log.debug("Starting processing...")

        # Define variables
        # A list to store result of each frame True or False
        hang_conf_results = []
        high_conf_results = []
        body_tr_conf_results = []
        wheel_tr_conf_results = []
        precondition = False

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

        # Load signals
        reader = self.readers[SIGNAL_DATA]

        hang_conf_description = ""
        high_conf_description = ""
        body_tr_conf_description = ""
        wheel_tr_conf_description = ""

        # Confidence signals used for evaluation
        object_hanging_confidence = SGFSignals.Columns.SGF_OBJECT_HANGING_CONFIDENCE
        object_high_confidence = SGFSignals.Columns.SGF_OBJECT_HIGH_CONFIDENCE
        object_body_traversable_confidence = SGFSignals.Columns.SGF_OBJECT_BODY_TRAVERSABLE_CONFIDENCE
        object_wheel_traversable_confidence = SGFSignals.Columns.SGF_OBJECT_WHEEL_TRAVERSABLE_CONFIDENCE

        sgf_timestamps = reader.get(SGFSignals.Columns.SGF_TIMESTAMP)

        for index, value in sgf_timestamps.items():
            number_of_objects = reader.at[index, SGFSignals.Columns.SGF_NUMBER_OF_POLYGONS]
            sgf_sig_status = reader.at[index, SGFSignals.Columns.SGF_SIGSTATUS]
            uss_point_list_sig_status = reader.at[index, SGFSignals.Columns.USS_POINT_LIST_SIGSTATUS]

            spp_point_list_front_sig_status = reader.at[index, SGFSignals.Columns.SPP_POINT_LIST_FRONT_SIGSTATUS]
            spp_point_list_rear_sig_status = reader.at[index, SGFSignals.Columns.SPP_POINT_LIST_REAR_SIGSTATUS]
            spp_point_list_left_sig_status = reader.at[index, SGFSignals.Columns.SPP_POINT_LIST_LEFT_SIGSTATUS]
            spp_point_list_right_sig_status = reader.at[index, SGFSignals.Columns.SPP_POINT_LIST_RIGHT_SIGSTATUS]
            spp_polyline_list_front_sig_status = reader.at[index, SGFSignals.Columns.SPP_POLYLINE_LIST_FRONT_SIGSTATUS]
            spp_polyline_list_rear_sig_status = reader.at[index, SGFSignals.Columns.SPP_POLYLINE_LIST_REAR_SIGSTATUS]
            spp_polyline_list_left_sig_status = reader.at[index, SGFSignals.Columns.SPP_POLYLINE_LIST_LEFT_SIGSTATUS]
            spp_polyline_list_right_sig_status = reader.at[index, SGFSignals.Columns.SPP_POLYLINE_LIST_RIGHT_SIGSTATUS]

            if (
                sgf_sig_status == 1
                and uss_point_list_sig_status == 1
                and spp_point_list_front_sig_status == 0
                and spp_point_list_rear_sig_status == 0
                and spp_point_list_left_sig_status == 0
                and spp_point_list_right_sig_status == 0
                and spp_polyline_list_front_sig_status == 0
                and spp_polyline_list_rear_sig_status == 0
                and spp_polyline_list_left_sig_status == 0
                and spp_polyline_list_right_sig_status == 0
                and number_of_objects > 0
            ):
                precondition = True

                hang_conf_result, hang_conf_description, hang_conf_failed_log = self.check_object_confidence(
                    reader=reader,
                    signal=object_hanging_confidence,
                    index=index,
                    frame=value,
                    number_of_objects=number_of_objects,
                )
                high_conf_result, high_conf_description, high_conf_failed_log = self.check_object_confidence(
                    reader=reader,
                    signal=object_high_confidence,
                    index=index,
                    frame=value,
                    number_of_objects=number_of_objects,
                )
                body_tr_conf_result, body_tr_conf_description, body_tr_conf_failed_log = self.check_object_confidence(
                    reader=reader,
                    signal=object_body_traversable_confidence,
                    index=index,
                    frame=value,
                    number_of_objects=number_of_objects,
                )
                wheel_tr_conf_result, wheel_tr_conf_description, wheel_tr_conf_failed_log = (
                    self.check_object_confidence(
                        reader=reader,
                        signal=object_wheel_traversable_confidence,
                        index=index,
                        frame=value,
                        number_of_objects=number_of_objects,
                    )
                )

                hang_conf_results.append(hang_conf_result)
                high_conf_results.append(high_conf_result)
                body_tr_conf_results.append(body_tr_conf_result)
                wheel_tr_conf_results.append(wheel_tr_conf_result)

        if precondition:
            if (
                not all(hang_conf_results)
                or not all(high_conf_results)
                or not all(body_tr_conf_results)
                or not all(wheel_tr_conf_results)
            ):
                self.test_result = fc.FAIL
            else:
                self.test_result = fc.PASS
        else:
            self.test_result = fc.NOT_ASSESSED

            hang_conf_description = " ".join("Not ALL preconditions are met".split())
            high_conf_description = " ".join("Not ALL preconditions are met".split())
            body_tr_conf_description = " ".join("Not ALL preconditions are met".split())
            wheel_tr_conf_description = " ".join("Not ALL preconditions are met".split())

        # Generate the summary report
        signal_summary[example_obj.get_properties()[SGFSignals.Columns.SGF_OBJECT_HANGING_CONFIDENCE][0]] = (
            hang_conf_description
        )
        signal_summary[example_obj.get_properties()[SGFSignals.Columns.SGF_OBJECT_HIGH_CONFIDENCE][0]] = (
            high_conf_description
        )
        signal_summary[example_obj.get_properties()[SGFSignals.Columns.SGF_OBJECT_BODY_TRAVERSABLE_CONFIDENCE][0]] = (
            body_tr_conf_description
        )
        signal_summary[example_obj.get_properties()[SGFSignals.Columns.SGF_OBJECT_WHEEL_TRAVERSABLE_CONFIDENCE][0]] = (
            wheel_tr_conf_description
        )

        remark = " ".join(
            "SGF provide the output Static Objects elevation category confidences lower than "
            f"{cc.AP_E_STA_OBJ_ELEV_CONF_MIN_NU} in case a static object is detected only based on "
            f"USS sensor and do not contain elevation information.".split()
        )

        # The signal summary and observations will be converted to pandas
        # and finally the html table will be created with them
        self.sig_sum = convert_dict_to_pandas(signal_summary=signal_summary, table_remark=remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        result_df = {
            "Verdict": {"value": self.test_result.title(), "color": get_color(self.test_result)},
            fc.REQ_ID: ["1522129"],
            fc.TESTCASE_ID: ["39106"],
            fc.TEST_DESCRIPTION: [
                "Check if SGF provide the output Static Objects elevation category confidences lower than "
                f"{cc.AP_E_STA_OBJ_ELEV_CONF_MIN_NU} in case SGF has only USS input and do not contain "
                "elevation information."
            ],
        }

        # Report result status
        if self.test_result == fc.INPUT_MISSING or self.test_result == fc.NOT_ASSESSED:
            self.result.measured_result = DATA_NOK
        elif self.test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif self.test_result == fc.FAIL:
            self.result.measured_result = FALSE

        # Add the plots in html page
        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")

        self.result.details["Additional_results"] = result_df


@verifies("1522129")
@testcase_definition(
    name="SWRT_CNC_SGF_SmallElevationConfidencesUSSOnly",
    description="This test case checks in case SGF has only USS input and do not contain elevation information, "
    "SGF shall provide the output Static Objects elevation category confidences lower than "
    "{AP_E_STA_OBJ_ELEV_CONF_MIN_NU} confidences.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_8OJg30xLEe6M5-WQsF_-tQ&componentURI=https%3A%2F%2Fjazz.conti.de%2F"
    "rm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration="
    "https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17100",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SmallElevationConfidencesUSSOnly(TestCase):
    """Test case definition."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepSmallElevationConfidencesUSSOnly,
        ]
