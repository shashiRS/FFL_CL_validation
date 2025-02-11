"""Validation of test case SWRT_CNC_GDR_Detection_Area."""

import logging
import os
import sys

import pandas as pd
import plotly.graph_objects as go
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
from pl_parking.PLP.CV.GDR.ft_helper import GDRSignals

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "GDR_DetectionArea"

example_obj = GDRSignals()

NUM_POINTS = 6000
MIN_DISTANCE = 0
MAX_DISTANCE = 20


@teststep_definition(
    step_number=1,
    name="GDR Detection Area",
    description="Geometric Depth Reconstruction component shall output 3D points within the detection area.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, GDRSignals)
class GdrDetectionAreaTestStep(TestStep):
    """Test step definition."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step."""
        super().__init__()

    def process(self):
        """Process the simulated file."""
        _log.debug("Starting processing...")

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)
        signal_summary = {}

        reader_data = self.readers[SIGNAL_DATA]
        reader_data = reader_data.reset_index(drop=True)

        reader_data.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in reader_data.columns]

        timestamps = []
        fc_num_valid_pts = []
        fc_num_invalid_pts = []
        lsc_num_valid_pts = []
        lsc_num_invalid_pts = []
        rc_num_valid_pts = []
        rc_num_invalid_pts = []
        rsc_num_valid_pts = []
        rsc_num_invalid_pts = []

        # timestamps status dictionary for all cameras
        ts_status_fc = {}
        ts_status_lsc = {}
        ts_status_rc = {}
        ts_status_rsc = {}

        fc_first_time_failed = 0
        lsc_first_time_failed = 0
        rc_first_time_failed = 0
        rsc_first_time_failed = 0

        fc_num_points = reader_data[GDRSignals.Columns.NUM_POINTS_FRONT].to_numpy()
        lsc_num_points = reader_data[GDRSignals.Columns.NUM_POINTS_LEFT].to_numpy()
        rc_num_points = reader_data[GDRSignals.Columns.NUM_POINTS_REAR].to_numpy()
        rsc_num_points = reader_data[GDRSignals.Columns.NUM_POINTS_RIGHT].to_numpy()

        fc_x_df = reader_data.filter(like=GDRSignals.Columns.X_FRONT)
        fc_y_df = reader_data.filter(like=GDRSignals.Columns.Y_FRONT)
        lsc_x_df = reader_data.filter(like=GDRSignals.Columns.X_LEFT)
        lsc_y_df = reader_data.filter(like=GDRSignals.Columns.Y_LEFT)
        rc_x_df = reader_data.filter(like=GDRSignals.Columns.X_REAR)
        rc_y_df = reader_data.filter(like=GDRSignals.Columns.Y_REAR)
        rsc_x_df = reader_data.filter(like=GDRSignals.Columns.X_RIGHT)
        rsc_y_df = reader_data.filter(like=GDRSignals.Columns.Y_RIGHT)
        fc_x_df_np = fc_x_df.to_numpy()
        fc_y_df_np = fc_y_df.to_numpy()
        lsc_x_df_np = lsc_x_df.to_numpy()
        lsc_y_df_np = lsc_y_df.to_numpy()
        rc_x_df_np = rc_x_df.to_numpy()
        rc_y_df_np = rc_y_df.to_numpy()
        rsc_x_df_np = rsc_x_df.to_numpy()
        rsc_y_df_np = rsc_y_df.to_numpy()

        for idx_ts in reader_data.index:
            print("in for")
            timestamps.append(reader_data.loc[idx_ts, "mts_ts"])

            fc_points = pd.DataFrame(
                {"x": fc_x_df_np[idx_ts][0 : fc_num_points[idx_ts]], "y": fc_y_df_np[idx_ts][0 : fc_num_points[idx_ts]]}
            )
            lsc_points = pd.DataFrame(
                {
                    "x": lsc_x_df_np[idx_ts][0 : lsc_num_points[idx_ts]],
                    "y": lsc_y_df_np[idx_ts][0 : lsc_num_points[idx_ts]],
                }
            )
            rc_points = pd.DataFrame(
                {"x": rc_x_df_np[idx_ts][0 : rc_num_points[idx_ts]], "y": rc_y_df_np[idx_ts][0 : rc_num_points[idx_ts]]}
            )
            rsc_points = pd.DataFrame(
                {
                    "x": rsc_x_df_np[idx_ts][0 : rsc_num_points[idx_ts]],
                    "y": rsc_y_df_np[idx_ts][0 : rsc_num_points[idx_ts]],
                }
            )

            fc_invalid_pts = len(
                fc_points.loc[
                    (fc_points["x"] < MIN_DISTANCE)
                    | (fc_points["x"] > MAX_DISTANCE)
                    | (fc_points["y"] < MIN_DISTANCE)
                    | (fc_points["y"] > MAX_DISTANCE)
                ]
            )
            fc_valid_pts = len(fc_points) - fc_invalid_pts
            fc_num_invalid_pts.append(fc_invalid_pts)
            fc_num_valid_pts.append(fc_valid_pts)

            lsc_invalid_pts = len(
                lsc_points.loc[
                    (lsc_points["x"] < MIN_DISTANCE)
                    | (lsc_points["x"] > MAX_DISTANCE)
                    | (lsc_points["y"] < MIN_DISTANCE)
                    | (lsc_points["y"] > MAX_DISTANCE)
                ]
            )
            lsc_valid_pts = len(lsc_points) - lsc_invalid_pts
            lsc_num_invalid_pts.append(lsc_invalid_pts)
            lsc_num_valid_pts.append(lsc_valid_pts)

            rc_invalid_pts = len(
                rc_points.loc[
                    (rc_points["x"] < MIN_DISTANCE)
                    | (rc_points["x"] > MAX_DISTANCE)
                    | (rc_points["y"] < MIN_DISTANCE)
                    | (rc_points["y"] > MAX_DISTANCE)
                ]
            )
            rc_valid_pts = len(rc_points) - rc_invalid_pts
            rc_num_invalid_pts.append(rc_invalid_pts)
            rc_num_valid_pts.append(rc_valid_pts)

            rsc_invalid_pts = len(
                rsc_points.loc[
                    (rsc_points["x"] < MIN_DISTANCE)
                    | (rsc_points["x"] > MAX_DISTANCE)
                    | (rsc_points["y"] < MIN_DISTANCE)
                    | (rsc_points["y"] > MAX_DISTANCE)
                ]
            )
            rsc_valid_pts = len(rsc_points) - rsc_invalid_pts
            rsc_num_invalid_pts.append(rsc_invalid_pts)
            rsc_num_valid_pts.append(rsc_valid_pts)

            print(f"number of invalid points for fc is: {fc_num_valid_pts}")
            # set, for each camera, timestamp status
            if fc_invalid_pts != 0:
                ts_status_fc[reader_data["mts_ts"][idx_ts]] = "failed"
                if fc_first_time_failed == 0:
                    fc_first_time_failed = reader_data["mts_ts"][idx_ts]
            else:
                ts_status_fc[reader_data["mts_ts"][idx_ts]] = "passed"

            if lsc_invalid_pts != 0:
                ts_status_lsc[reader_data["mts_ts"][idx_ts]] = "failed"
                if lsc_first_time_failed == 0:
                    lsc_first_time_failed = reader_data["mts_ts"][idx_ts]
            else:
                ts_status_lsc[reader_data["mts_ts"][idx_ts]] = "passed"

            if rc_invalid_pts != 0:
                ts_status_rc[reader_data["mts_ts"][idx_ts]] = "failed"
                if rc_first_time_failed == 0:
                    rc_first_time_failed = reader_data["mts_ts"][idx_ts]
            else:
                ts_status_rc[reader_data["mts_ts"][idx_ts]] = "passed"

            if rsc_invalid_pts != 0:
                ts_status_rsc[reader_data["mts_ts"][idx_ts]] = "failed"
                if rsc_first_time_failed == 0:
                    rsc_first_time_failed = reader_data["mts_ts"][idx_ts]
            else:
                ts_status_rsc[reader_data["mts_ts"][idx_ts]] = "passed"

        # check, for each camera,  if test is passed for all timestamps
        ts_check_all_passed_fc = all(value == "passed" for value in ts_status_fc.values())
        ts_check_all_passed_lsc = all(value == "passed" for value in ts_status_lsc.values())
        ts_check_all_passed_rc = all(value == "passed" for value in ts_status_rc.values())
        ts_check_all_passed_rsc = all(value == "passed" for value in ts_status_fc.values())

        # set, for each camera, test result and evaluation message
        if ts_check_all_passed_fc:
            fc_result = True
            fc_evaluation_message = "The <b>evaluation</b> is <b>PASSED</b> for <b>FRONT CAMERA</b> for all timestamps."
        else:
            fc_result = False
            fc_evaluation_message = f"The <b>evaluation</b> is <b>FAILED</b> for <b>FRONT CAMERA</b> because for timestamp <b>{fc_first_time_failed}</b> point coordinates are not in range [0, 20]m."

        if ts_check_all_passed_lsc:
            lsc_result = True
            lsc_evaluation_message = "The <b>evaluation</b> is <b>PASSED</b> for <b>LEFT CAMERA</b> for all timestamps."
        else:
            lsc_result = False
            lsc_evaluation_message = f"The <b>evaluation</b> is <b>FAILED</b> for <b>LEFT CAMERA</b> because for timestamp <b>{lsc_first_time_failed}</b> point coordinates are not in range [0, 20]m."

        if ts_check_all_passed_rc:
            rc_result = True
            rc_evaluation_message = "The <b>evaluation<b/> is <b>PASSED</b> for <b>REAR CAMERA</b> for all timestamps."
        else:
            rc_result = False
            rc_evaluation_message = f"The <b>evaluation</b> is <b>FAILED</b> for <b>REAR CAMERA</b> because for timestamp <b>{rc_first_time_failed}</b> point coordinates are not in range [0, 20]m."

        if ts_check_all_passed_rsc:
            rsc_result = True
            rsc_evaluation_message = (
                "The <b>evaluation</b> is <b>PASSED</b> for <b>RIGHT CAMERA</b> for all timestamps."
            )
        else:
            rsc_result = False
            rsc_evaluation_message = f"The <b>evaluation</b> is <b>FAILED</b> for <b>RIGHT CAMERA</b> because for timestamp <b>{rsc_first_time_failed}</b> point coordinates are not in range [0, 20]m."
        print("Dupa evaluation message")
        cams_status_result = [
            fc_result,
            lsc_result,
            rc_result,
            rsc_result,
        ]
        test_result = fc.PASS if all(cams_status_result) else fc.FAIL

        signal_summary["FC_Detection_Area_CHECK"] = fc_evaluation_message
        signal_summary["LSC_Detection_Area_CHECK"] = lsc_evaluation_message
        signal_summary["RC_Detection_Area_CHECK"] = rc_evaluation_message
        signal_summary["RSC_Detection_Area_CHECK"] = rsc_evaluation_message

        remark = f"The GDR Detection area is between [{MIN_DISTANCE}, {MAX_DISTANCE}]."

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_remark=remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fc_status = pd.DataFrame(
            {
                "Timestamp": reader_data["mts_ts"],
                "FC_number_of_valid_points": fc_num_valid_pts,
                "FC_number_of_invalid_points": fc_num_invalid_pts,
            }
        )
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=fc_status["Timestamp"],
                y=fc_status["FC_number_of_valid_points"],
                marker={"color": "green"},
                name="Number of valid points",
                hovertemplate="Timestamp: %{x}" + "<br>Number of valid points: %{y}%",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=fc_status["Timestamp"],
                y=fc_status["FC_number_of_invalid_points"],
                marker={"color": "red"},
                name="Number of invalid points",
                hovertemplate="Timestamp: %{x}" + "<br>Number of invalid points: %{y}%",
            )
        )
        fig["layout"]["yaxis"].update(title_text="Number of valid and invalid points")
        fig["layout"]["xaxis"].update(title_text="Timestamps")
        fig.update_layout(hovermode="x unified")
        fig.update_traces(showlegend=True)
        remark = ""
        plot_titles.append("Front camera statistics")
        plots.append(fig)
        remarks.append(remark)

        lsc_status = pd.DataFrame(
            {
                "Timestamp": reader_data["mts_ts"],
                "LSC_number_of_valid_points": lsc_num_valid_pts,
                "LSC_number_of_invalid_points": lsc_num_invalid_pts,
            }
        )
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=lsc_status["Timestamp"],
                y=lsc_status["LSC_number_of_valid_points"],
                marker={"color": "green"},
                name="Number of valid points",
                hovertemplate="Timestamp: %{x}" + "<br>Number of valid points: %{y}%",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=lsc_status["Timestamp"],
                y=lsc_status["LSC_number_of_invalid_points"],
                marker={"color": "red"},
                name="Number of invalid points",
                hovertemplate="Timestamp: %{x}" + "<br>Number of invalid points: %{y}%",
            )
        )
        fig["layout"]["yaxis"].update(title_text="Number of valid and invalid points")
        fig["layout"]["xaxis"].update(title_text="Timestamps")
        fig.update_layout(hovermode="x unified")
        fig.update_traces(showlegend=True)
        remark = ""
        plot_titles.append("Left side camera statistics")
        plots.append(fig)
        remarks.append(remark)

        rc_status = pd.DataFrame(
            {
                "Timestamp": reader_data["mts_ts"],
                "RC_number_of_valid_points": rc_num_valid_pts,
                "RC_number_of_invalid_points": rc_num_invalid_pts,
            }
        )
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=rc_status["Timestamp"],
                y=rc_status["RC_number_of_valid_points"],
                marker={"color": "green"},
                name="Number of valid points",
                hovertemplate="Timestamp: %{x}" + "<br>Number of valid points: %{y}%",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=rc_status["Timestamp"],
                y=rc_status["RC_number_of_invalid_points"],
                marker={"color": "red"},
                name="Number of invalid points",
                hovertemplate="Timestamp: %{x}" + "<br>Number of invalid points: %{y}%",
            )
        )
        fig["layout"]["yaxis"].update(title_text="Number of valid and invalid points")
        fig["layout"]["xaxis"].update(title_text="Timestamps")
        fig.update_layout(hovermode="x unified")
        fig.update_traces(showlegend=True)
        remark = ""
        plot_titles.append("Rear camera statistics")
        plots.append(fig)
        remarks.append(remark)

        rsc_status = pd.DataFrame(
            {
                "Timestamp": reader_data["mts_ts"],
                "RSC_number_of_valid_points": rsc_num_valid_pts,
                "RSC_number_of_invalid_points": rsc_num_invalid_pts,
            }
        )
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=rsc_status["Timestamp"],
                y=rsc_status["RSC_number_of_valid_points"],
                marker={"color": "green"},
                name="Number of valid points",
                hovertemplate="Timestamp: %{x}" + "<br>Number of valid points: %{y}%",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=rsc_status["Timestamp"],
                y=rsc_status["RSC_number_of_invalid_points"],
                marker={"color": "red"},
                name="Number of invalid points",
                hovertemplate="Timestamp: %{x}" + "<br>Number of invalid points: %{y}%",
            )
        )
        fig["layout"]["yaxis"].update(title_text="Number of valid and invalid points")
        fig["layout"]["xaxis"].update(title_text="Timestamps")
        fig.update_layout(hovermode="x unified")
        fig.update_traces(showlegend=True)
        remark = ""
        plot_titles.append("Right side camera statistics")
        plots.append(fig)
        remarks.append(remark)

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


@verifies("L3_GDR_1781157")
@testcase_definition(
    name="GDR Detection Area",
    description="Geometric Depth Reconstruction component shall output 3D points within the detection area",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FMD_3ElUMJtWEe6Zoo0NnU8erA&artifactInModule=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_3xVsjptWEe6Zoo0NnU8erA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17100",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class GEOMGdrDetectionArea(TestCase):
    """Test case definition."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [GdrDetectionAreaTestStep]
