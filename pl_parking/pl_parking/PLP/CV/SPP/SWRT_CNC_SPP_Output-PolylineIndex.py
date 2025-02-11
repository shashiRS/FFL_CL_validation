#!/usr/bin/env python3
"""Validation of Test Case SWRT_CNC_SPP_Output-PolylineIndex."""

import logging
import os
import sys

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, get_color
from pl_parking.PLP.CV.SPP.constants import SensorSource, SppPolylines, SppSigStatus
from pl_parking.PLP.CV.SPP.ft_helper import (
    SPPPreprocessor,
    SPPSignals,
    get_number_of_polygons,
    get_number_of_polylines,
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

SIGNAL_DATA = "testcase_52205"


@teststep_definition(
    step_number=1,
    name="SWRT_CNC_SPP_Output-PolylineIndex",
    description="Check if the SPP function provides an index for each polyline.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SPPSignals)
@register_pre_processor(alias="check_signals", pre_processor=SPPPreprocessor)
class SppOutputPolylineIndexTestStep(TestStep):
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
            ts_01_result = fc.PASS
            ts_02_result = fc.PASS
            ts_03_result = fc.PASS
            ts_01_frame_results = []
            ts_02_frame_results = []
            ts_03_frame_results = []
            eval_cond = False
            cam_evaluation = " ".join(
                "All vertice start index are in range. "
                "All vertices start index are in ascending order. "
                "All vertices start index are computed correctly.".split()
            )

            # get the availability of the signals
            signals_available, list_of_failed = pre_processor_result[0]

            if signals_available:
                # loop over the dataframe
                for frame, row in reader_df.iterrows():
                    polylines_sig_status = get_polylines_sig_status(camera, row)
                    number_of_polygons = get_number_of_polygons(camera, row)
                    number_of_polylines = get_number_of_polylines(camera, row)

                    if (
                        polylines_sig_status == SppSigStatus.AL_SIG_STATE_OK
                        and number_of_polygons > 0
                        and number_of_polylines > 0
                    ):
                        eval_cond = True
                        polylines_vertex_start_index_list = self.create_polylines_vertex_start_index(
                            camera, row, number_of_polygons, number_of_polylines
                        )

                        # create a list with num_vertices of polylines
                        polylines_num_vertices_list = self.create_polylines_num_vertices(
                            camera, row, number_of_polygons, number_of_polylines
                        )

                        # check that each vertex_start_index is grater than 3 and less than # {Polyline_Max_Vertices}
                        ts_01_frame_result, ts_01_failed_log = self.check_vertex_start_index_range(
                            camera, number_of_polylines, number_of_polygons, frame, row
                        )
                        ts_01_frame_results.append(ts_01_frame_result)
                        if len(ts_01_failed_log[frame]) > 0:
                            list_of_failed.append(ts_01_failed_log)

                        # check if vertex_start_index are in ascending order
                        ts_02_frame_result, ts_02_failed_log = self.check_vertex_start_index_sorted(
                            camera, polylines_vertex_start_index_list, number_of_polygons, frame
                        )
                        ts_02_frame_results.append(ts_02_frame_result)
                        if len(ts_02_failed_log[frame]) > 0:
                            list_of_failed.append(ts_02_failed_log)

                        # check if vertex_start_index[i] = vertex_start_index[i-1] + num_vertices[i-1]
                        ts_03_frame_result, ts_03_failed_log = self.check_vertex_start_index_computation(
                            camera,
                            polylines_vertex_start_index_list,
                            polylines_num_vertices_list,
                            number_of_polygons,
                            frame,
                        )
                        ts_03_frame_results.append(ts_03_frame_result)
                        if len(ts_03_failed_log[frame]) > 0:
                            list_of_failed.append(ts_02_failed_log)

                if eval_cond:
                    if not all(ts_01_frame_results):
                        ts_01_result = fc.FAIL
                        # create an evaluation text for the moment when the test is failed
                        cam_evaluation = " ".join("At least one vertex_start_index is out of range. ".split())
                    if not all(ts_02_frame_results):
                        ts_02_result = fc.FAIL
                        # create an evaluation text for the moment when the test is failed
                        cam_evaluation = " ".join(
                            "In at least one frame, vertex_start_index are not in ascending order. ".split()
                        )
                    if not all(ts_03_frame_results):
                        ts_03_result = fc.FAIL
                        # create an evaluation text for the moment when the test is failed
                        cam_evaluation = " ".join(
                            "In at least one frame, vertex_start_index is not computed correctly.".split()
                        )

                    if ts_01_result == fc.FAIL or ts_02_result == fc.FAIL or ts_03_result == fc.FAIL:
                        cam_test_result = fc.FAIL
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

        remark = " ".join(
            f"Check that all vertices are in range [{3},{SppPolylines.SPP_MAX_NUMBER_VERTICES}]. "
            "Check that all vertices are in ascending order. "
            "Check that all vertices are computed correctly: v[i] = v[i-1] + num_vertex[i-1].".split()
        )

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
            fc.REQ_ID: ["1565885"],
            fc.TESTCASE_ID: ["52205"],
            fc.TEST_DESCRIPTION: ["Check if SPP function provide an index for each polyline"],
        }

        self.result.details["Additional_results"] = result_df

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)

    @staticmethod
    def create_polylines_vertex_start_index(camera, row, number_of_polygons: int, number_of_polylines: int):
        """Create a list with vertex_start_index of polylines and return it."""
        polylines_vertex_start_index_list = []

        if camera is SensorSource.SPP_FC_DATA:
            polylines_vertex_start_index_list = [
                int(row[SPPSignals.Columns.FC_POLYLINES_VERTEX_START_INDEX + str(idx)])
                for idx in range(number_of_polygons, number_of_polygons + number_of_polylines)
            ]
        elif camera is SensorSource.SPP_LSC_DATA:
            polylines_vertex_start_index_list = [
                int(row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_START_INDEX + str(idx)])
                for idx in range(number_of_polygons, number_of_polygons + number_of_polylines)
            ]
        elif camera is SensorSource.SPP_RC_DATA:
            polylines_vertex_start_index_list = [
                int(row[SPPSignals.Columns.RC_POLYLINES_VERTEX_START_INDEX + str(idx)])
                for idx in range(number_of_polygons, number_of_polygons + number_of_polylines)
            ]
        elif camera is SensorSource.SPP_RSC_DATA:
            polylines_vertex_start_index_list = [
                int(row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_START_INDEX + str(idx)])
                for idx in range(number_of_polygons, number_of_polygons + number_of_polylines)
            ]
        return polylines_vertex_start_index_list

    @staticmethod
    def create_polylines_num_vertices(camera, row, number_of_polygons: int, number_of_polylines: int):
        """Create a list with num_vertices of polylines and return it."""
        polylines_num_vertices_list = []

        if camera is SensorSource.SPP_FC_DATA:
            polylines_num_vertices_list = [
                int(row[SPPSignals.Columns.FC_POLYLINES_NUM_VERTICES + str(idx)])
                for idx in range(number_of_polygons, number_of_polygons + number_of_polylines)
            ]
        elif camera is SensorSource.SPP_LSC_DATA:
            polylines_num_vertices_list = [
                int(row[SPPSignals.Columns.LSC_POLYLINES_NUM_VERTICES + str(idx)])
                for idx in range(number_of_polygons, number_of_polygons + number_of_polylines)
            ]
        elif camera is SensorSource.SPP_RC_DATA:
            polylines_num_vertices_list = [
                int(row[SPPSignals.Columns.RC_POLYLINES_NUM_VERTICES + str(idx)])
                for idx in range(number_of_polygons, number_of_polygons + number_of_polylines)
            ]
        elif camera is SensorSource.SPP_RSC_DATA:
            polylines_num_vertices_list = [
                int(row[SPPSignals.Columns.RSC_POLYLINES_NUM_VERTICES + str(idx)])
                for idx in range(number_of_polygons, number_of_polygons + number_of_polylines)
            ]
        return polylines_num_vertices_list

    @staticmethod
    def check_vertex_start_index_range(camera, number_of_polylines, number_of_polygons, frame, row):
        """
        Loops over a list of elements.

        :param camera
        :param number_of_polylines
        :param number_of_polygons
        :param frame
        :param row
        :return: result, not_in_range_elements
        """
        not_in_range_elements = []

        if camera is SensorSource.SPP_FC_DATA:
            not_in_range_elements = [
                SPPSignals.Columns.FC_POLYLINES_VERTEX_START_INDEX
                + str(i)
                + f" = {int(row[SPPSignals.Columns.FC_POLYLINES_VERTEX_START_INDEX + str(i)])}"
                f" is not in range [{3},{SppPolylines.SPP_MAX_NUMBER_VERTICES}]"
                for i in range(number_of_polygons, number_of_polygons + number_of_polylines)
                if int(row[SPPSignals.Columns.FC_POLYLINES_VERTEX_START_INDEX + str(i)]) < 3
                or int(row[SPPSignals.Columns.FC_POLYLINES_VERTEX_START_INDEX + str(i)])
                > SppPolylines.SPP_MAX_NUMBER_VERTICES
            ]

        elif camera is SensorSource.SPP_LSC_DATA:
            not_in_range_elements = [
                SPPSignals.Columns.LSC_POLYLINES_VERTEX_START_INDEX
                + str(i)
                + f" = {int(row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_START_INDEX + str(i)])}"
                f" is not in range [{3},{SppPolylines.SPP_MAX_NUMBER_VERTICES}]"
                for i in range(number_of_polygons, number_of_polygons + number_of_polylines)
                if int(row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_START_INDEX + str(i)]) < 3
                or int(row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_START_INDEX + str(i)])
                > SppPolylines.SPP_MAX_NUMBER_VERTICES
            ]

        elif camera is SensorSource.SPP_RC_DATA:
            not_in_range_elements = [
                SPPSignals.Columns.RC_POLYLINES_VERTEX_START_INDEX
                + str(i)
                + f" = {int(row[SPPSignals.Columns.RC_POLYLINES_VERTEX_START_INDEX + str(i)])}"
                f" is not in range [{3},{SppPolylines.SPP_MAX_NUMBER_VERTICES}]"
                for i in range(number_of_polygons, number_of_polygons + number_of_polylines)
                if int(row[SPPSignals.Columns.RC_POLYLINES_VERTEX_START_INDEX + str(i)]) < 3
                or int(row[SPPSignals.Columns.RC_POLYLINES_VERTEX_START_INDEX + str(i)])
                > SppPolylines.SPP_MAX_NUMBER_VERTICES
            ]

        elif camera is SensorSource.SPP_RSC_DATA:
            not_in_range_elements = [
                SPPSignals.Columns.RSC_POLYLINES_VERTEX_START_INDEX
                + str(i)
                + f" = {int(row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_START_INDEX + str(i)])}"
                f" is not in range [{3},{SppPolylines.SPP_MAX_NUMBER_VERTICES}]"
                for i in range(number_of_polygons, number_of_polygons + number_of_polylines)
                if int(row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_START_INDEX + str(i)]) < 3
                or int(row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_START_INDEX + str(i)])
                > SppPolylines.SPP_MAX_NUMBER_VERTICES
            ]

        if len(not_in_range_elements) > 0:
            return False, {frame: not_in_range_elements}
        else:
            return True, {frame: not_in_range_elements}

    @staticmethod
    def check_vertex_start_index_sorted(camera, input_list: list, number_of_polygons: int, frame: int):
        """
        Loops over a list of elements.

        :param camera
        :param input_list: A list with values of all vertex_start_index
        :param number_of_polygons
        :param frame
        :return: result, list_of_unsorted_elements
        """
        unsorted_elements = []

        if not all(input_list[i] <= input_list[i + 1] for i in range(len(input_list) - 1)):
            if camera is SensorSource.SPP_FC_DATA:
                unsorted_elements = [
                    SPPSignals.Columns.FC_POLYLINES_VERTEX_START_INDEX + str(number_of_polygons + i) + " is unsorted"
                    for i in range(len(input_list) - 1)
                    if input_list[i] > input_list[i + 1]
                ]
                return False, {frame: unsorted_elements}

            elif camera is SensorSource.SPP_LSC_DATA:
                unsorted_elements = [
                    SPPSignals.Columns.LSC_POLYLINES_VERTEX_START_INDEX + str(number_of_polygons + i) + " is unsorted"
                    for i in range(len(input_list) - 1)
                    if input_list[i] > input_list[i + 1]
                ]
                return False, {frame: unsorted_elements}

            elif camera is SensorSource.SPP_RC_DATA:
                unsorted_elements = [
                    SPPSignals.Columns.RC_POLYLINES_VERTEX_START_INDEX + str(number_of_polygons + i) + " is unsorted"
                    for i in range(len(input_list) - 1)
                    if input_list[i] > input_list[i + 1]
                ]
                return False, {frame: unsorted_elements}

            elif camera is SensorSource.SPP_RSC_DATA:
                unsorted_elements = [
                    SPPSignals.Columns.RSC_POLYLINES_VERTEX_START_INDEX + str(number_of_polygons + i) + " is unsorted"
                    for i in range(len(input_list) - 1)
                    if input_list[i] > input_list[i + 1]
                ]
                return False, {frame: unsorted_elements}

        return True, {frame: unsorted_elements}

    @staticmethod
    def check_vertex_start_index_computation(
        camera, vertex_start_index_list: list, num_vertices_list: list, number_of_polygons: int, frame: int
    ):
        """
        Loops over start_vertex_index list and num_vertices list.

        :param camera
        :param vertex_start_index_list: A list with values of all vertex_start_index
        :param num_vertices_list: A list with values of all num_vertices
        :param number_of_polygons
        :param frame
        :return: result, wrong_computation_vertex_start_index
        """
        wrong_computation_vertex_start_index = []

        if camera is SensorSource.SPP_FC_DATA:
            wrong_computation_vertex_start_index = [
                SPPSignals.Columns.FC_POLYLINES_VERTEX_START_INDEX + str(number_of_polygons + i) + " is wrong computed"
                for i in range(1, len(vertex_start_index_list))
                if vertex_start_index_list[i] != vertex_start_index_list[i - 1] + num_vertices_list[i - 1]
            ]

        elif camera is SensorSource.SPP_LSC_DATA:
            wrong_computation_vertex_start_index = [
                SPPSignals.Columns.LSC_POLYLINES_VERTEX_START_INDEX + str(number_of_polygons + i) + " is wrong computed"
                for i in range(1, len(vertex_start_index_list))
                if vertex_start_index_list[i] != vertex_start_index_list[i - 1] + num_vertices_list[i - 1]
            ]

        elif camera is SensorSource.SPP_RC_DATA:
            wrong_computation_vertex_start_index = [
                SPPSignals.Columns.RC_POLYLINES_VERTEX_START_INDEX + str(number_of_polygons + i) + " is wrong computed"
                for i in range(1, len(vertex_start_index_list))
                if vertex_start_index_list[i] != vertex_start_index_list[i - 1] + num_vertices_list[i - 1]
            ]

        elif camera is SensorSource.SPP_RSC_DATA:
            wrong_computation_vertex_start_index = [
                SPPSignals.Columns.RSC_POLYLINES_VERTEX_START_INDEX + str(number_of_polygons + i) + " is wrong computed"
                for i in range(1, len(vertex_start_index_list))
                if vertex_start_index_list[i] != vertex_start_index_list[i - 1] + num_vertices_list[i - 1]
            ]

        if len(wrong_computation_vertex_start_index) > 0:
            return False, {frame: wrong_computation_vertex_start_index}
        else:
            return True, {frame: wrong_computation_vertex_start_index}


@verifies("L3_SPP_1565885")
@testcase_definition(
    name="SWRT_CNC_SPP_Output-PolylineIndex",
    description="This test verifies if the SPP function provides an index for each polyline.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_aDFNOF-oEe6hyY-R-i-gng&componentURI=https%3A%2F%2Fjazz.conti.de%2F"
    "rm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg&oslc.configuration="
    "https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17100",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SppOutputPolylineIndex(TestCase):
    """Test case definition."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SppOutputPolylineIndexTestStep,
        ]
