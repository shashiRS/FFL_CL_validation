#!/usr/bin/env python3
"""Validation of Test Case SWKPI_CNC_SPP_AveragePolygonAreaCoverage."""

import logging
import os
import sys

import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, get_color
from pl_parking.PLP.CV.SPP.constants import SensorSource, SppKPI, SppSemantics, SppSigStatus
from pl_parking.PLP.CV.SPP.frames.eval import EvalFrame
from pl_parking.PLP.CV.SPP.frames.ground_truth import GroundTruthFrame
from pl_parking.PLP.CV.SPP.frames.simulation import SimulationFrame
from pl_parking.PLP.CV.SPP.ft_helper import (
    SPPLoadGtAndSim,
    SPPSignals,
)

TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


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

__author__ = "<uib11434>"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "testcase_51068"
ALIAS_JSON = "tpr_polygons_coverage"
spp_obj = SPPSignals()


@teststep_definition(
    step_number=1,
    name="SWKPI_CNC_SPP_AveragePolygonAreaCoverage",
    description=f"Check if the Average Polygon Area Coverage exceed {SppKPI.SPP_AVERAGE_POLYGON_AREA_COVERAGE.value}% "
    f"of the ground truth that is in the defined range in at least "
    f"{SppKPI.SPP_POLYGON_AREA_COVERAGE_RATE.value}% of cases.",
    expected_result=ExpectedResult(
        operator=RelationOperator.GREATER,
        numerator=SppKPI.SPP_POLYGON_AREA_COVERAGE_RATE.value,
        unit="%",
        aggregate_function=AggregateFunction.MEAN,
    ),
)
@register_signals(SIGNAL_DATA, SPPSignals)
@register_side_load(
    alias=ALIAS_JSON,
    side_load=JsonSideLoad,
    path_spec=PathSpecification(
        folder=r"s3://par230-prod-data-lake-sim/gt_labels/", extension=".json", s3=True
    ),
)
@register_pre_processor(alias="load_gt_and_sim_data", pre_processor=SPPLoadGtAndSim)
class SppAveragePolygonAreaCoverageTestStep(TestStep):
    """Test step definition."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step."""
        super().__init__()
        self.test_result = fc.INPUT_MISSING
        self.sig_sum = None

    @staticmethod
    def eval_results(eval_polygons_coverage):
        """Evaluate if coverage of polygons are higher than a threshold"""
        coverage_in_range = sum(
            1
            for polygon_coverage in eval_polygons_coverage
            if polygon_coverage >= SppKPI.SPP_AVERAGE_POLYGON_AREA_COVERAGE.value
        )
        coverage_in_range_percentage = coverage_in_range * 100 / len(eval_polygons_coverage)
        if coverage_in_range_percentage < SppKPI.SPP_POLYGON_AREA_COVERAGE_RATE.value:
            cam_test_result = fc.FAIL
            cam_evaluation = " ".join(
                f"The evaluation is <b>FAILED</b>, "
                f"PolygonAreaCoverage is {coverage_in_range_percentage:.2f}%. "
                f"Minimum threshold is <b>{SppKPI.SPP_POLYGON_AREA_COVERAGE_RATE.value}%</b>".split()
            )
        else:
            cam_test_result = fc.PASS
            cam_evaluation = " ".join(
                f"The evaluation is <b>PASSED</b>, "
                f"AveragePolygonAreaCoverage is {coverage_in_range_percentage:.2f}%. "
                f"Minimum threshold is <b>{SppKPI.SPP_POLYGON_AREA_COVERAGE_RATE.value}%</b>".split()
            )
        return cam_test_result, cam_evaluation

    @staticmethod
    def plot_results(
        plt_spp_timestamp, failed_timestamps, failed_polygons_coverage, x_axis, plot_titles, plots, remarks
    ):
        """Plot all coverage of polygons that are lower than a threshold"""
        fig = go.Figure()

        # Flags to track legend
        added_coverage = False

        # Draw the horizontal line that represents the threshold
        fig.add_trace(
            go.Scatter(
                x=[min(plt_spp_timestamp), max(plt_spp_timestamp)],  # Span the whole x-axis
                y=[SppKPI.SPP_AVERAGE_POLYGON_AREA_COVERAGE.value, SppKPI.SPP_AVERAGE_POLYGON_AREA_COVERAGE.value],
                # Constant y for horizontal line
                mode="lines",
                line=dict(color="green", width=2),
                name=f"Threshold Line at {SppKPI.SPP_AVERAGE_POLYGON_AREA_COVERAGE.value} percentages",
                legendgroup="threshold",
                showlegend=True,
            )
        )

        for x, y in zip(failed_timestamps, failed_polygons_coverage):
            fig.add_trace(
                go.Scatter(
                    x=[x, x],
                    y=[0, y],
                    mode="lines+markers",
                    line=dict(color="red", width=2),
                    name="Coverage that does not reach the threshold",
                    legendgroup="coverage",
                    showlegend=not added_coverage,
                )
            )
            added_coverage = True

        fig.update_layout(
            xaxis=dict(range=[min(plt_spp_timestamp), max(plt_spp_timestamp)]),  # Explicit x-axis range
            yaxis=dict(range=[0, SppKPI.SPP_AVERAGE_POLYGON_AREA_COVERAGE.value * 1.1]),  # Explicit y-axis range
        )

        fig["layout"]["xaxis"].update(title_text=x_axis)
        fig["layout"]["yaxis"].update(title_text="Percentage of polygons intersection")

        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

    def average_polygon_area_coverage(
        self,
        gt_df,
        sim_df,
        polylines_timestamp,
        polylines_sig_status,
        polylines_number_of_polygons,
        polylines_vertex_start_index,
        polylines_num_vertices,
        vertex_x,
        vertex_y,
        vertex_z,
        boundary_type,
    ):
        """Calculate the coverage area of GT polygons by SIM polygons"""
        cam_test_result = DATA_NOK
        cam_evaluation = ""
        frames_to_be_evaluated = []
        # Initializing a list to store all coverage of polygons that will be evaluated
        eval_polygons_coverage = []
        # Initializing a list to store values of failed coverages
        failed_polygons_coverage = []
        # Initializes a list to store timestamps where coverage of polygons are failed
        failed_timestamps = []

        if gt_df.empty:
            cam_test_result = fc.INPUT_MISSING
            cam_evaluation = " ".join("Ground truth data <b>not available</b>, evaluation can't be performed.".split())

            return cam_test_result, cam_evaluation, failed_polygons_coverage, failed_timestamps

        if sim_df.empty:
            cam_test_result = fc.INPUT_MISSING
            cam_evaluation = " ".join("Simulation data <b>not available</b>, evaluation can't be performed.".split())

            return cam_test_result, cam_evaluation, failed_polygons_coverage, failed_timestamps

        # filter only valid outputs
        gt_df = gt_df[gt_df["gt_sig_status"] == "AL_SIG_STATE_OK"]
        # filter frames where at least one polygon is present.
        gt_df = gt_df[gt_df["gt_no_of_polygons"] >= 1]

        # filter only valid outputs
        sim_df = sim_df[sim_df[polylines_sig_status] == SppSigStatus.AL_SIG_STATE_OK]
        # filter frames where at least one polygon is present.
        sim_df = sim_df[sim_df[polylines_number_of_polygons] >= 1]

        if gt_df.empty:
            cam_test_result = fc.NOT_ASSESSED
            cam_evaluation = " ".join(
                f"There is no valid ground truth data: gt_sigStatus != {SppSigStatus.AL_SIG_STATE_OK}, "
                f"or number of polygons is less then 1. "
                f"Evaluation can't be performed.".split()
            )

            return cam_test_result, cam_evaluation, failed_polygons_coverage, failed_timestamps

        if sim_df.empty:
            cam_test_result = fc.NOT_ASSESSED
            cam_evaluation = " ".join(
                f"There is no valid simulation data: sim_sigStatus != {SppSigStatus.AL_SIG_STATE_OK} "
                f"or number of polygons is less then 1. "
                f"Evaluation can't be performed.".split()
            )

            return cam_test_result, cam_evaluation, failed_polygons_coverage, failed_timestamps

        recording_name_with_extention = os.path.split(self.artifacts[0].file_path)[1]
        recording_name = recording_name_with_extention.split(".bsig")[0]

        gt_spp_timestamp = gt_df["gt_spp_timestamp"].tolist()
        sim_spp_timestamp = sim_df[polylines_timestamp].tolist()

        common_timestamps = [x for x in gt_spp_timestamp if x in sim_spp_timestamp]
        if common_timestamps:
            for timestamp in common_timestamps:
                gtf = None
                sf = None

                gtf = GroundTruthFrame(timestamp=timestamp)

                if gtf.load(gt_camera_data=gt_df, boundary_type=boundary_type):
                    sf = SimulationFrame(timestamp=timestamp)
                    if not sf.load(
                        sim_df=sim_df,
                        polylines_timestamp=polylines_timestamp,
                        polylines_number_of_polygons=polylines_number_of_polygons,
                        polylines_vertex_start_index=polylines_vertex_start_index,
                        polylines_num_vertices=polylines_num_vertices,
                        vertex_x=vertex_x,
                        vertex_y=vertex_y,
                        vertex_z=vertex_z,
                        boundary_type=boundary_type,
                    ):
                        sf = None

                else:
                    gtf = None

                eval_frame = EvalFrame(recording=recording_name, gt=gtf, sim=sf, timestamp=timestamp)

                if eval_frame.valid:
                    frames_to_be_evaluated.append({timestamp: eval_frame.evaluate_frame_polygons(timestamp)})

            if len(frames_to_be_evaluated) > 0:
                for frame_to_be_evaluated in frames_to_be_evaluated:
                    if frame_to_be_evaluated:
                        timestamp, evaluated_polygons = next(iter(frame_to_be_evaluated.items()), None)
                        for evaluated_polygon in evaluated_polygons:
                            polygon_coverage = evaluated_polygon.get("Percentage_Coverage")
                            eval_polygons_coverage.append(polygon_coverage)
                            if polygon_coverage < SppKPI.SPP_AVERAGE_POLYGON_AREA_COVERAGE.value:
                                failed_polygons_coverage.append(polygon_coverage)
                                failed_timestamps.append(timestamp)

                cam_test_result, cam_evaluation = self.eval_results(eval_polygons_coverage)
            else:
                cam_evaluation = " ".join("No objects are available in GT and/or SIM".split())

        return cam_test_result, cam_evaluation, failed_polygons_coverage, failed_timestamps

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
        plot_titles, plots, remarks = fh.rep([], 3)

        # Initializing the dictionary with data for final evaluation table
        signal_summary = {}

        boundary_type = SppSemantics.DRIVABLE_AREA.name

        cameras_from_preprocessor, reader_df = self.pre_processors["load_gt_and_sim_data"]

        # Get the ground truth data for each camera sensor
        gt_fc_df = cameras_from_preprocessor[SensorSource.SPP_FC_DATA]
        gt_lsc_df = cameras_from_preprocessor[SensorSource.SPP_LSC_DATA]
        gt_rc_df = cameras_from_preprocessor[SensorSource.SPP_RC_DATA]
        gt_rsc_df = cameras_from_preprocessor[SensorSource.SPP_RSC_DATA]

        # Get simulation data for each camera sensor
        sim_fc_df = reader_df.filter(regex="fc_")
        sim_lsc_df = reader_df.filter(regex="lsc_")
        sim_rc_df = reader_df.filter(regex="rc_")
        sim_rsc_df = reader_df.filter(regex="rsc_")

        # TODO: remove duplicate frames
        gt_fc_df_unique = gt_fc_df.drop_duplicates(subset="gt_spp_timestamp", keep="first")
        sim_fc_df_unique = sim_fc_df.drop_duplicates(subset=spp_obj.Columns.FC_POLYLINES_TIMESTAMP, keep="first")

        gt_lsc_df_unique = gt_lsc_df.drop_duplicates(subset="gt_spp_timestamp", keep="first")
        sim_lsc_df_unique = sim_lsc_df.drop_duplicates(subset=spp_obj.Columns.LSC_POLYLINES_TIMESTAMP, keep="first")

        gt_rc_df_unique = gt_rc_df.drop_duplicates(subset="gt_spp_timestamp", keep="first")
        sim_rc_df_unique = sim_rc_df.drop_duplicates(subset=spp_obj.Columns.RC_POLYLINES_TIMESTAMP, keep="first")

        gt_rsc_df_unique = gt_rsc_df.drop_duplicates(subset="gt_spp_timestamp", keep="first")
        sim_rsc_df_unique = sim_rsc_df.drop_duplicates(subset=spp_obj.Columns.RSC_POLYLINES_TIMESTAMP, keep="first")

        fc_test_result, fc_evaluation, fc_failed_polygons_coverage, fc_failed_timestamps = (
            self.average_polygon_area_coverage(
                gt_fc_df_unique,
                sim_fc_df_unique,
                spp_obj.Columns.FC_POLYLINES_TIMESTAMP,
                spp_obj.Columns.FC_POLYLINES_SIG_STATUS,
                spp_obj.Columns.FC_POLYLINES_NUMBER_OF_POLYGONS,
                spp_obj.Columns.FC_POLYLINES_VERTEX_START_INDEX,
                spp_obj.Columns.FC_POLYLINES_NUM_VERTICES,
                spp_obj.Columns.FC_POLYLINES_VERTEX_X_COORD,
                spp_obj.Columns.FC_POLYLINES_VERTEX_Y_COORD,
                spp_obj.Columns.FC_POLYLINES_VERTEX_Z_COORD,
                boundary_type,
            )
        )

        lsc_test_result, lsc_evaluation, lsc_failed_polygons_coverage, lsc_failed_timestamps = (
            self.average_polygon_area_coverage(
                gt_lsc_df_unique,
                sim_lsc_df_unique,
                spp_obj.Columns.LSC_POLYLINES_TIMESTAMP,
                spp_obj.Columns.LSC_POLYLINES_SIG_STATUS,
                spp_obj.Columns.LSC_POLYLINES_NUMBER_OF_POLYGONS,
                spp_obj.Columns.LSC_POLYLINES_VERTEX_START_INDEX,
                spp_obj.Columns.LSC_POLYLINES_NUM_VERTICES,
                spp_obj.Columns.LSC_POLYLINES_VERTEX_X_COORD,
                spp_obj.Columns.LSC_POLYLINES_VERTEX_Y_COORD,
                spp_obj.Columns.LSC_POLYLINES_VERTEX_Z_COORD,
                boundary_type,
            )
        )

        rc_test_result, rc_evaluation, rc_failed_polygons_coverage, rc_failed_timestamps = (
            self.average_polygon_area_coverage(
                gt_rc_df_unique,
                sim_rc_df_unique,
                spp_obj.Columns.RC_POLYLINES_TIMESTAMP,
                spp_obj.Columns.RC_POLYLINES_SIG_STATUS,
                spp_obj.Columns.RC_POLYLINES_NUMBER_OF_POLYGONS,
                spp_obj.Columns.RC_POLYLINES_VERTEX_START_INDEX,
                spp_obj.Columns.RC_POLYLINES_NUM_VERTICES,
                spp_obj.Columns.RC_POLYLINES_VERTEX_X_COORD,
                spp_obj.Columns.RC_POLYLINES_VERTEX_Y_COORD,
                spp_obj.Columns.RC_POLYLINES_VERTEX_Z_COORD,
                boundary_type,
            )
        )

        rsc_test_result, rsc_evaluation, rsc_failed_polygons_coverage, rsc_failed_timestamps = (
            self.average_polygon_area_coverage(
                gt_rsc_df_unique,
                sim_rsc_df_unique,
                spp_obj.Columns.RSC_POLYLINES_TIMESTAMP,
                spp_obj.Columns.RSC_POLYLINES_SIG_STATUS,
                spp_obj.Columns.RSC_POLYLINES_NUMBER_OF_POLYGONS,
                spp_obj.Columns.RSC_POLYLINES_VERTEX_START_INDEX,
                spp_obj.Columns.RSC_POLYLINES_NUM_VERTICES,
                spp_obj.Columns.RSC_POLYLINES_VERTEX_X_COORD,
                spp_obj.Columns.RSC_POLYLINES_VERTEX_Y_COORD,
                spp_obj.Columns.RSC_POLYLINES_VERTEX_Z_COORD,
                boundary_type,
            )
        )

        if (
            fc_test_result == fc.INPUT_MISSING
            or lsc_test_result == fc.INPUT_MISSING
            or rc_test_result == fc.INPUT_MISSING
            or rsc_test_result == fc.INPUT_MISSING
        ):
            self.test_result = fc.INPUT_MISSING
            self.result.measured_result = DATA_NOK
        elif (
            fc_test_result == fc.NOT_ASSESSED
            or lsc_test_result == fc.NOT_ASSESSED
            or rc_test_result == fc.NOT_ASSESSED
            or rsc_test_result == fc.NOT_ASSESSED
        ):
            self.test_result = fc.NOT_ASSESSED
            self.result.measured_result = DATA_NOK
        elif (
            fc_test_result == fc.FAIL
            or lsc_test_result == fc.FAIL
            or rc_test_result == fc.FAIL
            or rsc_test_result == fc.FAIL
        ):
            self.test_result = fc.FAIL
            self.result.measured_result = Result(0, unit="%")
        elif (
            fc_test_result == fc.PASS
            or lsc_test_result == fc.PASS
            or rc_test_result == fc.PASS
            or rsc_test_result == fc.PASS
        ):
            self.test_result = fc.PASS
            self.result.measured_result = Result(100, unit="%")

        signal_summary[SensorSource.SPP_FC_DATA] = fc_evaluation
        signal_summary[SensorSource.SPP_LSC_DATA] = lsc_evaluation
        signal_summary[SensorSource.SPP_RC_DATA] = rc_evaluation
        signal_summary[SensorSource.SPP_RSC_DATA] = rsc_evaluation
        remark = " ".join(
            f"Check that SPP Polygons Area exceed {SppKPI.SPP_AVERAGE_POLYGON_AREA_COVERAGE.value}% of the ground "
            f"truth area in at least {SppKPI.SPP_POLYGON_AREA_COVERAGE_RATE.value}% of the occurrences.".split()
        )
        # The signal summary and observations will be converted to pandas
        # and finally the html table will be created with them
        self.sig_sum = fh.convert_dict_to_pandas(
            signal_summary=signal_summary,
            table_remark=remark,
            table_header_left="Camera Evaluation",
        )
        plots.append(self.sig_sum)

        result_df = {
            "Verdict": {"value": self.test_result.title(), "color": get_color(self.test_result)},
            fc.REQ_ID: ["1934709"],
            fc.TESTCASE_ID: ["51068"],
            fc.TEST_DESCRIPTION: [
                f"Check that SPP Polygons Area exceed {SppKPI.SPP_AVERAGE_POLYGON_AREA_COVERAGE.value}% of the "
                f"ground truth area in at least {SppKPI.SPP_POLYGON_AREA_COVERAGE_RATE.value}% of the occurrences."
            ],
        }

        self.result.details["Additional_results"] = result_df

        if fc_failed_polygons_coverage:
            fc_plt_spp_timestamp = sim_fc_df_unique[spp_obj.Columns.FC_POLYLINES_TIMESTAMP].tolist()
            fc_x_axis = "FC_SPP_Timestamp"
            self.plot_results(
                fc_plt_spp_timestamp,
                fc_failed_timestamps,
                fc_failed_polygons_coverage,
                fc_x_axis,
                plot_titles,
                plots,
                remarks,
            )

        if lsc_failed_polygons_coverage:
            lsc_plt_spp_timestamp = sim_lsc_df_unique[spp_obj.Columns.LSC_POLYLINES_TIMESTAMP].tolist()
            lsc_x_axis = "LSC_SPP_Timestamp"
            self.plot_results(
                lsc_plt_spp_timestamp,
                lsc_failed_timestamps,
                lsc_failed_polygons_coverage,
                lsc_x_axis,
                plot_titles,
                plots,
                remarks,
            )

        if rc_failed_polygons_coverage:
            rc_plt_spp_timestamp = sim_rc_df_unique[spp_obj.Columns.RC_POLYLINES_TIMESTAMP].tolist()
            rc_x_axis = "RC_SPP_Timestamp"
            self.plot_results(
                rc_plt_spp_timestamp,
                rc_failed_timestamps,
                rc_failed_polygons_coverage,
                rc_x_axis,
                plot_titles,
                plots,
                remarks,
            )

        if rsc_failed_polygons_coverage:
            rsc_plt_spp_timestamp = sim_rsc_df_unique[spp_obj.Columns.RSC_POLYLINES_TIMESTAMP].tolist()
            rsc_x_axis = "RSC_SPP_Timestamp"
            self.plot_results(
                rsc_plt_spp_timestamp,
                rsc_failed_timestamps,
                rsc_failed_polygons_coverage,
                rsc_x_axis,
                plot_titles,
                plots,
                remarks,
            )

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)


@verifies("1934709")
@testcase_definition(
    name="SWKPI_CNC_SPP_AveragePolygonAreaCoverage",
    description=f"This test will verify that the Average Polygon Area Coverage exceed "
    f"{SppKPI.SPP_AVERAGE_POLYGON_AREA_COVERAGE.value}% of the ground truth that is in the defined range "
    f"in at least {SppKPI.SPP_POLYGON_AREA_COVERAGE_RATE.value}% of cases.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_uFrjE9FaEe6vvdVFvzgyYA&componentURI=https%3A%2F%2Fjazz.conti.de%2F"
    "rm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg&oslc.configuration="
    "https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17100",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SppAveragePolygonAreaCoverage(TestCase):
    """Test case definition."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SppAveragePolygonAreaCoverageTestStep,
        ]
