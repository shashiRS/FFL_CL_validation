#!/usr/bin/env python3
"""SWKPI_CNC_SGF_PresumedStaticObstaclesSVCRate test case"""

import logging
import os
import sys

import numpy as np
from tsf.core.common import AggregateFunction, PathSpecification, RelationOperator
from tsf.core.results import DATA_NOK, ExpectedResult, Result
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_pre_processor,
    register_side_load,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.io.sideload import JsonSideLoad

import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    convert_dict_to_pandas,
    get_color,
    rep,
)
from pl_parking.PLP.CEM.constants import ConstantsSGF as cs
from pl_parking.PLP.CEM.SGF.ft_helper import SGFPreprocessorLoadForSGF, SGFSignals

TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "<uib11434>"
__copyright__ = "2023-2024, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "PresumedStaticObstacle"
ALIAS_JSON = "presumed_static_obstacle"
sgf_obj = SGFSignals()


@teststep_definition(
    step_number=1,
    name="Presumed Static Obstacle",
    description=f"This test checks if SGF creates a Presumed Static Obstacle "
    f"and output corresponding Static Objects in at least {cs.AP_E_STA_OBJ_SVC_TP_RATE_NU}% of the occurrences.",
    expected_result=ExpectedResult(
        operator=RelationOperator.GREATER,
        numerator=cs.AP_E_STA_OBJ_SVC_TP_RATE_NU,
        unit="%",
        aggregate_function=AggregateFunction.MEAN,
    ),
)
@register_signals(SIGNAL_DATA, SGFSignals)
@register_side_load(
    alias=ALIAS_JSON,
    side_load=JsonSideLoad,
    path_spec=PathSpecification(
        folder=os.path.join(TSF_BASE, "data", "CEM_json_gt"),
        extension=".json",
    ),
)
@register_pre_processor(alias="load_gt_and_sim_data", pre_processor=SGFPreprocessorLoadForSGF)
class TestStepPresumedStaticObstacle(TestStep):
    """Test step definition."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step."""
        super().__init__()
        self.test_result = fc.INPUT_MISSING
        self.sig_sum = None

    @staticmethod
    def evaluate_results(true_positive_count, object_count):
        """
        Check if the true positive ratio of the detected objects are more than
        AP_E_STA_OBJ_SVC_TP_RATE_NU
        """
        true_positive_ratio = np.round(true_positive_count / object_count * 100, 2)  # percentage

        if true_positive_ratio >= cs.AP_E_STA_OBJ_SVC_TP_RATE_NU:
            test_result = fc.PASS
            evaluation = " ".join(
                f"The evaluation is <b>PASSED</b>, for {true_positive_ratio} % of {object_count} objects were a presumed static obstacle correctly assigned. "
                f"Minimum acceptable ratio is <b>{cs.AP_E_STA_OBJ_SVC_TP_RATE_NU}%</b>".split()
            )
        else:
            test_result = fc.FAIL
            evaluation = " ".join(
                f"The evaluation is <b>FAILED</b>, for {true_positive_ratio} % of {object_count} objects were a presumed static obstacle correctly assigned. "
                f"Minimum acceptable ratio is <b>{cs.AP_E_STA_OBJ_SVC_TP_RATE_NU}%</b>".split()
            )

        return test_result, evaluation, true_positive_ratio

    def process(self):
        """Process the simulated files."""
        _log.debug("Starting processing...")

        # Update the details from the results page with the needed information. All the information from
        # self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Initializing the result with data nok
        self.result.measured_result = DATA_NOK

        # Create empty lists for titles, plots and remarks, if they are needed.
        # Plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)
        signal_summary = {}

        summary_key = "Presumed Static Obstacles"

        gt_df, sim_df = self.pre_processors["load_gt_and_sim_data"]

        if not gt_df.empty:
            # filter only valid outputs
            gt_df = gt_df[gt_df["gt_sig_status"] == "AL_SIG_STATE_OK"]
            # filter frames where no convex Static Obstacle is present.
            gt_df = gt_df[gt_df["gt_no_of_objects"] > 0]

            # filter only valid outputs
            sim_df = sim_df[sim_df[sgf_obj.Columns.SGF_SIGSTATUS] == 1]
            # filter frames where no convex Static Obstacle is present.
            sim_df = sim_df[sim_df[sgf_obj.Columns.SGF_NUMBER_OF_POLYGONS] > 0]

            gt_sgf_timestamp = gt_df["gt_sgf_timestamp"].tolist()
            sim_sgf_timestamp = sim_df[sgf_obj.Columns.SGF_TIMESTAMP].tolist()

            common_timestamps = [x for x in gt_sgf_timestamp if x in sim_sgf_timestamp]
            true_positive = []  # objects correctly detected
            not_detected_timestamps = []  # objects should have been detected, but weren't
            object_count = 0

            for timestamp in common_timestamps:

                gt_frame_data = gt_df[gt_df["gt_sgf_timestamp"] == timestamp]
                sim_frame_data = sim_df[sim_df[sgf_obj.Columns.SGF_TIMESTAMP] == timestamp]

                for row in sim_frame_data.iterrows():
                    sim_obj_found_in_gt = False
                    i = 0
                    while (not sim_obj_found_in_gt) and (i < row[1].numPolygons):

                        gt_obj_id = int(gt_frame_data["gt_obstacle_id_0"].item())
                        sim_obj_id = int(row[1].iloc[3].item())
                        if gt_obj_id == sim_obj_id:
                            sim_obj_found_in_gt = True
                            true_positive.append((timestamp, gt_obj_id))
                        i = i + 1

                if not sim_obj_found_in_gt:
                    not_detected_timestamps.append(timestamp)  # timestamps in which the object was not detected
                object_count = (
                    object_count + gt_frame_data["gt_no_of_objects"].item()
                )  # count all objects in all timestamps

            self.test_result, evaluation, true_positive_ratio = self.evaluate_results(len(true_positive), object_count)

        else:
            evaluation = " ".join("Ground truth data <b>not available</b>, evaluation can't be performed.".split())

        # Report result status
        if self.test_result == fc.INPUT_MISSING:
            self.result.measured_result = DATA_NOK
        elif self.test_result == fc.PASS:
            self.result.measured_result = Result(true_positive_ratio, unit="%")
        elif self.test_result == fc.FAIL:
            self.result.measured_result = Result(true_positive_ratio, unit="%")

        signal_summary[summary_key] = evaluation
        remark = " ".join("Inflation rate evaluation of Static Objects.".split())
        self.sig_sum = convert_dict_to_pandas(
            signal_summary=signal_summary, table_header_left="Evaluation", table_remark=remark
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        result_df = {
            "Verdict": {"value": self.test_result.title(), "color": get_color(self.test_result)},
            fc.REQ_ID: ["1522150"],
            fc.TESTCASE_ID: ["39285"],
            fc.TEST_DESCRIPTION: [
                f"This test checks if SGF creates a Presumed Static Obstacle "
                f"and output corresponding Static Objects in at least {cs.AP_E_STA_OBJ_SVC_TP_RATE_NU}% of the occurrences."
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


@verifies("1522150")
@testcase_definition(
    name="SWKPI_CNC_SGF_PresumedStaticObstaclesSVCRate",
    description=f"This test checks if SGF creates a Presumed Static Obstacle "
    f"and output corresponding Static Objects in at least {cs.AP_E_STA_OBJ_SVC_TP_RATE_NU}% of the occurrences.",
    doors_url="https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_or7dMJpREe6OHr4fEH59Xg#action=com.ibm.rqm.planning.home.actionDispatcher&subAction=viewTestCase&id=39285",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class PresumedStaticObstacle(TestCase):
    """Presumed Static Obstacle test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepPresumedStaticObstacle]
