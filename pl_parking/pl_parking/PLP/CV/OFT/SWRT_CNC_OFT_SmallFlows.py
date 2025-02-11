"""Validation of test case SWRT_CNC_OFT_SmallFlows."""

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
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CV.OFT.ft_helper import OFTSignals

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "OFT_SmallFLows"

MIN_LIMIT_RANGE = 1
MAX_LIMIT_RANGE = 2
MIN_SMALL_FLOWS = 400


@teststep_definition(
    step_number=1,
    name="OFT Small flows",
    description="For each timestamp calculate the number of small flows and check if it is >= 400.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, OFTSignals)
class OftSmallFlowsTestStep(TestStep):
    """Test step definition."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step."""
        super().__init__()
        self.sig_sum = None

    def process(self):
        """Process the simulated file."""
        _log.debug("Starting processing...")

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)
        signal_summary = {}

        # extract all signals into a dataframe
        reader_data = self.readers[SIGNAL_DATA]
        reader_data = reader_data.reset_index(drop=True)
        reader_data.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in reader_data.columns]

        fc_x_curr_df = reader_data.filter(like=OFTSignals.Columns.XIMGCURRENT_FRONT)
        fc_y_curr_df = reader_data.filter(like=OFTSignals.Columns.YIMGCURRENT_FRONT)
        lsc_x_curr_df = reader_data.filter(like=OFTSignals.Columns.XIMGCURRENT_LEFT)
        lsc_y_curr_df = reader_data.filter(like=OFTSignals.Columns.YIMGCURRENT_LEFT)
        rc_x_curr_df = reader_data.filter(like=OFTSignals.Columns.XIMGCURRENT_REAR)
        rc_y_curr_df = reader_data.filter(like=OFTSignals.Columns.YIMGCURRENT_REAR)
        rsc_x_curr_df = reader_data.filter(like=OFTSignals.Columns.XIMGCURRENT_RIGHT)
        rsc_y_curr_df = reader_data.filter(like=OFTSignals.Columns.YIMGCURRENT_RIGHT)
        fc_x_prev_df = reader_data.filter(like=OFTSignals.Columns.XIMGPREVIOUS_FRONT)
        fc_y_prev_df = reader_data.filter(like=OFTSignals.Columns.YIMGPREVIOUS_FRONT)
        lsc_x_prev_df = reader_data.filter(like=OFTSignals.Columns.XIMGPREVIOUS_LEFT)
        lsc_y_prev_df = reader_data.filter(like=OFTSignals.Columns.YIMGPREVIOUS_LEFT)
        rc_x_prev_df = reader_data.filter(like=OFTSignals.Columns.XIMGPREVIOUS_REAR)
        rc_y_prev_df = reader_data.filter(like=OFTSignals.Columns.YIMGPREVIOUS_REAR)
        rsc_x_prev_df = reader_data.filter(like=OFTSignals.Columns.XIMGPREVIOUS_RIGHT)
        rsc_y_prev_df = reader_data.filter(like=OFTSignals.Columns.YIMGPREVIOUS_RIGHT)
        fc_x_curr_df_np = fc_x_curr_df.to_numpy()
        fc_y_curr_df_np = fc_y_curr_df.to_numpy()
        lsc_x_curr_df_np = lsc_x_curr_df.to_numpy()
        lsc_y_curr_df_np = lsc_y_curr_df.to_numpy()
        rc_x_curr_df_np = rc_x_curr_df.to_numpy()
        rc_y_curr_df_np = rc_y_curr_df.to_numpy()
        rsc_x_curr_df_np = rsc_x_curr_df.to_numpy()
        rsc_y_curr_df_np = rsc_y_curr_df.to_numpy()
        fc_x_prev_df_np = fc_x_prev_df.to_numpy()
        fc_y_prev_df_np = fc_y_prev_df.to_numpy()
        lsc_x_prev_df_np = lsc_x_prev_df.to_numpy()
        lsc_y_prev_df_np = lsc_y_prev_df.to_numpy()
        rc_x_prev_df_np = rc_x_prev_df.to_numpy()
        rc_y_prev_df_np = rc_y_prev_df.to_numpy()
        rsc_x_prev_df_np = rsc_x_prev_df.to_numpy()
        rsc_y_prev_df_np = rsc_y_prev_df.to_numpy()

        # obtain for each camera, an array that contains for each timestamp, the number of flows
        fc_num_flows = reader_data[OFTSignals.Columns.NUMFLOWS_FRONT].to_numpy()
        lsc_num_flows = reader_data[OFTSignals.Columns.NUMFLOWS_LEFT].to_numpy()
        rc_num_flows = reader_data[OFTSignals.Columns.NUMFLOWS_REAR].to_numpy()
        rsc_num_flows = reader_data[OFTSignals.Columns.NUMFLOWS_RIGHT].to_numpy()

        # timestamps status dictionary for all cameras
        fc_ts_status = {}
        lsc_ts_status = {}
        rc_ts_status = {}
        rsc_ts_status = {}

        fc_first_time_failed = 0
        lsc_first_time_failed = 0
        rc_first_time_failed = 0
        rsc_first_time_failed = 0

        for idx_ts in reader_data.index:
            # set, for each camera, current and previous coordinates
            fc_prev_coordinates = np.column_stack(
                (fc_x_prev_df_np[idx_ts][0 : fc_num_flows[idx_ts]], fc_y_prev_df_np[idx_ts][0 : fc_num_flows[idx_ts]])
            )
            fc_curr_coordinates = np.column_stack(
                (fc_x_curr_df_np[idx_ts][0 : fc_num_flows[idx_ts]], fc_y_curr_df_np[idx_ts][0 : fc_num_flows[idx_ts]])
            )

            lsc_prev_coordinates = np.column_stack(
                (
                    lsc_x_prev_df_np[idx_ts][0 : lsc_num_flows[idx_ts]],
                    lsc_y_prev_df_np[idx_ts][0 : lsc_num_flows[idx_ts]],
                )
            )
            lsc_curr_coordinates = np.column_stack(
                (
                    lsc_x_curr_df_np[idx_ts][0 : lsc_num_flows[idx_ts]],
                    lsc_y_curr_df_np[idx_ts][0 : lsc_num_flows[idx_ts]],
                )
            )

            rc_prev_coordinates = np.column_stack(
                (rc_x_prev_df_np[idx_ts][0 : rc_num_flows[idx_ts]], rc_y_prev_df_np[idx_ts][0 : rc_num_flows[idx_ts]])
            )
            rc_curr_coordinates = np.column_stack(
                (rc_x_curr_df_np[idx_ts][0 : rc_num_flows[idx_ts]], rc_y_curr_df_np[idx_ts][0 : rc_num_flows[idx_ts]])
            )

            rsc_prev_coordinates = np.column_stack(
                (
                    rsc_x_prev_df_np[idx_ts][0 : rsc_num_flows[idx_ts]],
                    rsc_y_prev_df_np[idx_ts][0 : rsc_num_flows[idx_ts]],
                )
            )
            rsc_curr_coordinates = np.column_stack(
                (
                    rsc_x_curr_df_np[idx_ts][0 : rsc_num_flows[idx_ts]],
                    rsc_y_curr_df_np[idx_ts][0 : rsc_num_flows[idx_ts]],
                )
            )

            # calculate, for each camera, the displacement between current and previous coordinates
            fc_displacement = np.linalg.norm(fc_curr_coordinates - fc_prev_coordinates, axis=1)
            lsc_displacement = np.linalg.norm(lsc_curr_coordinates - lsc_prev_coordinates, axis=1)
            rc_displacement = np.linalg.norm(rc_curr_coordinates - rc_prev_coordinates, axis=1)
            rsc_displacement = np.linalg.norm(rsc_curr_coordinates - rsc_prev_coordinates, axis=1)

            # calculate, for each camera, the number of small flows
            fc_num_small_flows = ((MIN_LIMIT_RANGE <= fc_displacement) & (fc_displacement < MAX_LIMIT_RANGE)).sum()
            lsc_num_small_flows = ((MIN_LIMIT_RANGE <= lsc_displacement) & (lsc_displacement < MAX_LIMIT_RANGE)).sum()
            rc_num_small_flows = ((MIN_LIMIT_RANGE <= rc_displacement) & (rc_displacement < MAX_LIMIT_RANGE)).sum()
            rsc_num_small_flows = ((MIN_LIMIT_RANGE <= rsc_displacement) & (rsc_displacement < MAX_LIMIT_RANGE)).sum()

            # set, for each camera, timestamp status
            if fc_num_small_flows < MIN_SMALL_FLOWS:
                fc_ts_status[reader_data["mts_ts"][idx_ts]] = "failed"
                if fc_first_time_failed == 0:
                    fc_first_time_failed = reader_data["mts_ts"][idx_ts]
            else:
                fc_ts_status[reader_data["mts_ts"][idx_ts]] = "passed"
            if lsc_num_small_flows < MIN_SMALL_FLOWS:
                lsc_ts_status[reader_data["mts_ts"][idx_ts]] = "failed"
                if lsc_first_time_failed == 0:
                    lsc_first_time_failed = reader_data["mts_ts"][idx_ts]
            else:
                lsc_ts_status[reader_data["mts_ts"][idx_ts]] = "passed"

            if rc_num_small_flows < MIN_SMALL_FLOWS:
                rc_ts_status[reader_data["mts_ts"][idx_ts]] = "failed"
                if rc_first_time_failed == 0:
                    rc_first_time_failed = reader_data["mts_ts"][idx_ts]
            else:
                rc_ts_status[reader_data["mts_ts"][idx_ts]] = "passed"

            if rsc_num_small_flows < MIN_SMALL_FLOWS:
                rsc_ts_status[reader_data["mts_ts"][idx_ts]] = "failed"
                if rsc_first_time_failed == 0:
                    rsc_first_time_failed = reader_data["mts_ts"][idx_ts]
            else:
                rsc_ts_status[reader_data["mts_ts"][idx_ts]] = "passed"

        # check, for each camera,  if test is passed for all timestamps
        fc_ts_check_all_passed = all(value == "passed" for value in fc_ts_status.values())
        lsc_ts_check_all_passed = all(value == "passed" for value in lsc_ts_status.values())
        rc_ts_check_all_passed = all(value == "passed" for value in rc_ts_status.values())
        rsc_ts_check_all_passed = all(value == "passed" for value in rsc_ts_status.values())

        # set, for each camera, test result and evaluation message
        if fc_ts_check_all_passed:
            fc_result = True
            fc_evaluation_message = f"The <b>evaluation</b> is <b>PASSED</b> for <b>FRONT CAMERA</b> because the number of small flows >= {MIN_SMALL_FLOWS}, for all timestamps."
        else:
            fc_result = False
            fc_evaluation_message = f"The <b>evaluation</b> is <b>FAILED</b> for <b>FRONT CAMERA</b> because for timestamp <b>{fc_first_time_failed}</b>, the number of small flows is < {MIN_SMALL_FLOWS}."

        if lsc_ts_check_all_passed:
            lsc_result = True
            lsc_evaluation_message = f"The <b>evaluation</b> is <b>PASSED</b> for <b>LEFT CAMERA</b> because the number of small flows >= {MIN_SMALL_FLOWS}, for all timestamps."
        else:
            lsc_result = False
            lsc_evaluation_message = f"The <b>evaluation</b> is <b>FAILED</b> for <b>LEFT CAMERA</b> because for timestamp <b>{lsc_first_time_failed}</b>, the number of small flows is < {MIN_SMALL_FLOWS}."

        if rc_ts_check_all_passed:
            rc_result = True
            rc_evaluation_message = f"The <b>evaluation</b> is <b>PASSED</b> for <b>REAR CAMERA</b> because the number of small flows >= {MIN_SMALL_FLOWS}, for all timestamps."
        else:
            rc_result = False
            rc_evaluation_message = f"The <b>evaluation</b> is <b>FAILED</b> for <b>REAR CAMERA</b> because for timestamp <b>{rc_first_time_failed}</b>, the number of small flows is < {MIN_SMALL_FLOWS}."

        if rsc_ts_check_all_passed:
            rsc_result = True
            rsc_evaluation_message = f"The <b>evaluation</b> is <b>PASSED</b> for <b>RIGHT CAMERA</b> because the number of small flows >= {MIN_SMALL_FLOWS}, for all timestamps."
        else:
            rsc_result = False
            rsc_evaluation_message = f"The <b>evaluation</b> is <b>FAILED</b> for <b>RIGHT CAMERA</b> because for timestamp <b>{rsc_first_time_failed}</b>, the number of small flows is < {MIN_SMALL_FLOWS}."

        cams_status_result = [
            fc_result,
            lsc_result,
            rc_result,
            rsc_result,
        ]
        test_result = fc.PASS if all(cams_status_result) else fc.FAIL

        signal_summary["FC_SMALL_FLOWS"] = fc_evaluation_message
        signal_summary["LSC_SMALL_FLOWS"] = lsc_evaluation_message
        signal_summary["RC_SMALL_FLOWS"] = rc_evaluation_message
        signal_summary["RSC_SMALL_FLOWS"] = rsc_evaluation_message

        remark = f"The number of small flows should be >={MIN_SMALL_FLOWS}."

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_remark=remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif test_result == fc.FAIL:
            self.result.measured_result = FALSE
        else:
            self.result.measured_result = DATA_NOK

        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")


@verifies("L3_Artemis_2143430")
@testcase_definition(
    name="SWRT_CNC_OFT_SmallFlows",
    description="This test case checks if the number of small flows is >=400.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FMD_3ElUMJtWEe6Zoo0NnU8erA&artifactInModule=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_AgSjxwL7Ee-JmbR7EsJ0UA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17100",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class OftSmallFlows(TestCase):
    """Test case definition."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [OftSmallFlowsTestStep]
