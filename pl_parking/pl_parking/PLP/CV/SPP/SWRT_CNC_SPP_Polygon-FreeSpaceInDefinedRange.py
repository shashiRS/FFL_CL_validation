#!/usr/bin/env python3
"""Validation of Test Case SWRT_CNC_SPP_Polygon-FreeSpaceInDefinedRange."""

import logging
import os
import sys

from shapely import Polygon

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, get_color
from pl_parking.PLP.CV.SPP.constants import SensorSource, SppSigStatus
from pl_parking.PLP.CV.SPP.ft_helper import (
    SPPPreprocessor,
    SPPSignals,
    extract_coordinates,
    get_max_polygon_coords,
    get_number_of_polygons,
    get_polyline_num_vertices,
    get_polyline_vertex_start_index,
    get_polylines_sig_status,
)

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_pre_processor,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

__author__ = "<uib11434>"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "testcase_51988"


@teststep_definition(
    step_number=1,
    name="SWRT_CNC_SPP_Polygon-FreeSpaceInDefinedRange",
    description="Check if the free space polygon is enclosed in the defined range in each frame.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SPPSignals)
@register_pre_processor(alias="check_signals", pre_processor=SPPPreprocessor)
class SppPolygonFreeSpaceInDefinedRangeTestStep(TestStep):
    """Test step definition."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step."""
        super().__init__()
        self.test_result = fc.INPUT_MISSING
        self.sig_sum = None

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

        cameras = {
            SensorSource.SPP_FC_DATA: DATA_NOK,
            SensorSource.SPP_LSC_DATA: DATA_NOK,
            SensorSource.SPP_RC_DATA: DATA_NOK,
            SensorSource.SPP_RSC_DATA: DATA_NOK,
        }

        cameras_from_preprocessor, reader_df = self.pre_processors["check_signals"]
        for camera, pre_processor_result in cameras_from_preprocessor.items():
            frame_results = []
            eval_cond = False
            cam_evaluation = " ".join("Free space polygon is in the defined range".split())

            # get the availability of the signals
            signals_available, list_of_failed = pre_processor_result[0]

            if signals_available:
                # loop over the dataframe
                for frame, row in reader_df.iterrows():
                    polylines_sig_status = get_polylines_sig_status(camera, row)
                    number_of_polygons = get_number_of_polygons(camera, row)

                    if polylines_sig_status == SppSigStatus.AL_SIG_STATE_OK and number_of_polygons > 0:
                        eval_cond = True
                        frame_result = True
                        frame_failed_log = {}
                        polygon_not_in_range = []

                        max_polygon_coords = get_max_polygon_coords(camera)
                        max_polygon = Polygon(max_polygon_coords)

                        for number_of_polygon in range(number_of_polygons):
                            start_index = get_polyline_vertex_start_index(camera, number_of_polygon, row)
                            polygon_number_of_vertices = get_polyline_num_vertices(camera, number_of_polygon, row)
                            end_index = start_index + polygon_number_of_vertices

                            sim_polygon_coords = extract_coordinates(
                                camera=camera, start=start_index, end=end_index, row=row
                            )

                            if len(sim_polygon_coords) > 0:
                                # repeat the first point to create a 'closed loop'
                                sim_polygon_coords = sim_polygon_coords + (sim_polygon_coords[0],)
                                sim_polygon = Polygon(sim_polygon_coords)

                                if not max_polygon.contains(sim_polygon):
                                    frame_result = False
                                    polygon_not_in_range.append(
                                        f"Polygon[{number_of_polygon}]: {sim_polygon} is not in the defined range "
                                        f"{max_polygon}"
                                    )

                        frame_failed_log[frame] = polygon_not_in_range
                        frame_results.append(frame_result)

                        if len(frame_failed_log[frame]) > 0:
                            list_of_failed.append(frame_failed_log)

                if eval_cond:
                    if not all(frame_results):
                        cam_test_result = fc.FAIL
                        # create an evaluation text for the moment when the test is failed
                        cam_evaluation = " ".join(
                            f"The evaluation is FAILED in {len(list_of_failed)} cases: {list_of_failed[0]}".split()
                        )
                    else:
                        cam_test_result = fc.PASS
                    cameras.update({camera: cam_test_result})

                else:
                    cam_evaluation = " ".join(
                        "Preconditions are not meet: pSppPolylines.sSigHeader.eSigStatus != AL_SIG_STATE_OK and/or "
                        "pSppPolylines.numberOfPolygons <= 0 and/or pSppPolylines.numberOfPolylines <= 0".split()
                    )

            else:
                cam_evaluation = " ".join("Not all required signals are available in the bsig file. ".split())

            signal_summary[camera] = cam_evaluation

        remark = " ".join("Check that the free space polygon is enclosed in the defined range.".split())

        # The signal summary and observations will be converted to pandas
        # and finally the html table will be created with them
        self.sig_sum = fh.convert_dict_to_pandas(
            signal_summary=signal_summary,
            table_remark=remark,
            table_header_left="Camera Evaluation",
        )
        plots.append(self.sig_sum)

        if any(camera_test_result == DATA_NOK for camera_test_result in cameras.values()):
            self.test_result = fc.INPUT_MISSING
            self.result.measured_result = DATA_NOK
        elif any(camera_test_result == fc.FAIL for camera_test_result in cameras.values()):
            self.test_result = fc.FAIL
            self.result.measured_result = FALSE
        elif all(camera_test_result == fc.PASS for camera_test_result in cameras.values()):
            self.test_result = fc.PASS
            self.result.measured_result = TRUE

        result_df = {
            "Verdict": {"value": self.test_result.title(), "color": get_color(self.test_result)},
            fc.REQ_ID: ["1938856"],
            fc.TESTCASE_ID: ["51988"],
            fc.TEST_DESCRIPTION: ["Check if the free space polygon is enclosed in the defined range in each frame"],
        }

        self.result.details["Additional_results"] = result_df

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)


@verifies("L3_SPP_1938856, L3_SPP_1938857")
@testcase_definition(
    name="SWRT_CNC_SPP_Polygon-FreeSpaceInDefinedRange",
    description="This test verifies if the free space polygon is enclosed in the defined range for the current frame.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_TfSEENHaEe6vvdVFvzgyYA&componentURI=https%3A%2F%2Fjazz.conti.de%2F"
    "rm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg&oslc.configuration="
    "https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17100",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SppPolygonFreeSpaceInDefinedRange(TestCase):
    """Test case definition."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SppPolygonFreeSpaceInDefinedRangeTestStep,
        ]
