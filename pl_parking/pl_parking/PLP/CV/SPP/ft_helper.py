"""Helper file for SPP Test Scripts."""

import logging

import numpy as np
import pandas as pd
from tsf.core.results import DATA_NOK
from tsf.core.testcase import PreProcessor
from tsf.io.signals import SignalDefinition

from pl_parking.PLP.CV.SPP.camera_utils import createCylindricalCamera
from pl_parking.PLP.CV.SPP.constants import (
    TEST_CASE_MAP,
    SensorSource,
    SppOperationalRange,
    SppPolygon,
    SppSemantics,
    SppSemPoints,
)
from pl_parking.PLP.CV.SPP.constants import SppPolylines as Polylines

_log = logging.getLogger(__name__)

Empty_Dataframe = pd.DataFrame(columns=["timestamp", "bsig_index", "label_present"]).set_index("timestamp")


class SPPPreprocessor(PreProcessor):
    """Preprocessor class to compute all data before the teststeps."""

    def pre_process(self):
        """Preprocess the data."""
        reader_df = self.readers[list(self.readers.keys())[0]]

        cameras = {
            SensorSource.SPP_FC_DATA: DATA_NOK,
            SensorSource.SPP_LSC_DATA: DATA_NOK,
            SensorSource.SPP_RC_DATA: DATA_NOK,
            SensorSource.SPP_RSC_DATA: DATA_NOK,
        }
        cameras_to_be_returned = {
            SensorSource.SPP_FC_DATA: [],
            SensorSource.SPP_LSC_DATA: [],
            SensorSource.SPP_RC_DATA: [],
            SensorSource.SPP_RSC_DATA: [],
        }

        for camera, _ in cameras.items():
            list_of_required_signals = []

            if camera is SensorSource.SPP_FC_DATA:
                list_of_required_signals.append(SPPSignals.Columns.FC_POLYLINES_TIMESTAMP)
                list_of_required_signals.append(SPPSignals.Columns.FC_POLYLINES_SIG_STATUS)
                list_of_required_signals.append(SPPSignals.Columns.FC_POLYLINES_NUMBER_OF_POLYGONS)
                list_of_required_signals.append(SPPSignals.Columns.FC_POLYLINES_NUMBER_OF_POLYLINES)
                list_of_required_signals.append(SPPSignals.Columns.FC_SEMPOINTS_INDICATOR_FLAG)
                list_of_required_signals.append(SPPSignals.Columns.FC_SEMPOINTS_SIG_STATUS)

                for polyline_idx in range(Polylines.SPP_MAX_NUMBER_POLYLINES):
                    list_of_required_signals.append(
                        SPPSignals.Columns.FC_POLYLINES_VERTEX_START_INDEX + str(polyline_idx)
                    )
                    list_of_required_signals.append(SPPSignals.Columns.FC_POLYLINES_NUM_VERTICES + str(polyline_idx))
                    list_of_required_signals.append(SPPSignals.Columns.FC_POLYLINES_CONFIDENCE + str(polyline_idx))
                    list_of_required_signals.append(SPPSignals.Columns.FC_POLYLINES_SEMANTIC + str(polyline_idx))

                for coord_idx in range(Polylines.SPP_MAX_NUMBER_VERTICES):
                    list_of_required_signals.append(SPPSignals.Columns.FC_POLYLINES_VERTEX_X_COORD + str(coord_idx))
                    list_of_required_signals.append(SPPSignals.Columns.FC_POLYLINES_VERTEX_Y_COORD + str(coord_idx))
                    list_of_required_signals.append(SPPSignals.Columns.FC_POLYLINES_VERTEX_Z_COORD + str(coord_idx))

            elif camera is SensorSource.SPP_LSC_DATA:
                list_of_required_signals.append(SPPSignals.Columns.LSC_POLYLINES_TIMESTAMP)
                list_of_required_signals.append(SPPSignals.Columns.LSC_POLYLINES_SIG_STATUS)
                list_of_required_signals.append(SPPSignals.Columns.LSC_POLYLINES_NUMBER_OF_POLYGONS)
                list_of_required_signals.append(SPPSignals.Columns.LSC_POLYLINES_NUMBER_OF_POLYLINES)
                list_of_required_signals.append(SPPSignals.Columns.LSC_SEMPOINTS_INDICATOR_FLAG)
                list_of_required_signals.append(SPPSignals.Columns.LSC_SEMPOINTS_SIG_STATUS)

                for polyline_idx in range(Polylines.SPP_MAX_NUMBER_POLYLINES):
                    list_of_required_signals.append(
                        SPPSignals.Columns.LSC_POLYLINES_VERTEX_START_INDEX + str(polyline_idx)
                    )
                    list_of_required_signals.append(SPPSignals.Columns.LSC_POLYLINES_NUM_VERTICES + str(polyline_idx))
                    list_of_required_signals.append(SPPSignals.Columns.LSC_POLYLINES_CONFIDENCE + str(polyline_idx))
                    list_of_required_signals.append(SPPSignals.Columns.LSC_POLYLINES_SEMANTIC + str(polyline_idx))

                for coord_idx in range(Polylines.SPP_MAX_NUMBER_VERTICES):
                    list_of_required_signals.append(SPPSignals.Columns.LSC_POLYLINES_VERTEX_X_COORD + str(coord_idx))
                    list_of_required_signals.append(SPPSignals.Columns.LSC_POLYLINES_VERTEX_Y_COORD + str(coord_idx))
                    list_of_required_signals.append(SPPSignals.Columns.LSC_POLYLINES_VERTEX_Z_COORD + str(coord_idx))

            elif camera is SensorSource.SPP_RC_DATA:
                list_of_required_signals.append(SPPSignals.Columns.RC_POLYLINES_TIMESTAMP)
                list_of_required_signals.append(SPPSignals.Columns.RC_POLYLINES_SIG_STATUS)
                list_of_required_signals.append(SPPSignals.Columns.RC_POLYLINES_NUMBER_OF_POLYGONS)
                list_of_required_signals.append(SPPSignals.Columns.RC_POLYLINES_NUMBER_OF_POLYLINES)
                list_of_required_signals.append(SPPSignals.Columns.RC_SEMPOINTS_INDICATOR_FLAG)
                list_of_required_signals.append(SPPSignals.Columns.RC_SEMPOINTS_SIG_STATUS)

                for polyline_idx in range(Polylines.SPP_MAX_NUMBER_POLYLINES):
                    list_of_required_signals.append(
                        SPPSignals.Columns.RC_POLYLINES_VERTEX_START_INDEX + str(polyline_idx)
                    )
                    list_of_required_signals.append(SPPSignals.Columns.RC_POLYLINES_NUM_VERTICES + str(polyline_idx))
                    list_of_required_signals.append(SPPSignals.Columns.RC_POLYLINES_CONFIDENCE + str(polyline_idx))
                    list_of_required_signals.append(SPPSignals.Columns.RC_POLYLINES_SEMANTIC + str(polyline_idx))

                for coord_idx in range(Polylines.SPP_MAX_NUMBER_VERTICES):
                    list_of_required_signals.append(SPPSignals.Columns.RC_POLYLINES_VERTEX_X_COORD + str(coord_idx))
                    list_of_required_signals.append(SPPSignals.Columns.RC_POLYLINES_VERTEX_Y_COORD + str(coord_idx))
                    list_of_required_signals.append(SPPSignals.Columns.RC_POLYLINES_VERTEX_Z_COORD + str(coord_idx))

            elif camera is SensorSource.SPP_RSC_DATA:
                list_of_required_signals.append(SPPSignals.Columns.RSC_POLYLINES_TIMESTAMP)
                list_of_required_signals.append(SPPSignals.Columns.RSC_POLYLINES_SIG_STATUS)
                list_of_required_signals.append(SPPSignals.Columns.RSC_POLYLINES_NUMBER_OF_POLYGONS)
                list_of_required_signals.append(SPPSignals.Columns.RSC_POLYLINES_NUMBER_OF_POLYLINES)
                list_of_required_signals.append(SPPSignals.Columns.RSC_SEMPOINTS_INDICATOR_FLAG)
                list_of_required_signals.append(SPPSignals.Columns.RSC_SEMPOINTS_SIG_STATUS)

                for polyline_idx in range(Polylines.SPP_MAX_NUMBER_POLYLINES):
                    list_of_required_signals.append(
                        SPPSignals.Columns.RSC_POLYLINES_VERTEX_START_INDEX + str(polyline_idx)
                    )
                    list_of_required_signals.append(SPPSignals.Columns.RSC_POLYLINES_NUM_VERTICES + str(polyline_idx))
                    list_of_required_signals.append(SPPSignals.Columns.RSC_POLYLINES_CONFIDENCE + str(polyline_idx))
                    list_of_required_signals.append(SPPSignals.Columns.RSC_POLYLINES_SEMANTIC + str(polyline_idx))

                for coord_idx in range(Polylines.SPP_MAX_NUMBER_VERTICES):
                    list_of_required_signals.append(SPPSignals.Columns.RSC_POLYLINES_VERTEX_X_COORD + str(coord_idx))
                    list_of_required_signals.append(SPPSignals.Columns.RSC_POLYLINES_VERTEX_Y_COORD + str(coord_idx))
                    list_of_required_signals.append(SPPSignals.Columns.RSC_POLYLINES_VERTEX_Z_COORD + str(coord_idx))

            # check the availability of the signals
            cameras_to_be_returned[camera].append(check_signals_availability(list_of_required_signals, reader_df))

        return cameras_to_be_returned, reader_df


class SPPLoadGtAndSim(PreProcessor):
    """Preprocessor class to load GT and SIM data before the teststeps."""

    def pre_process(self):
        """Load GT and SIM data."""
        sim_df = self.readers[list(self.readers.keys())[0]]
        gt_data = self.side_load[list(self.side_load.keys())[0]]

        cameras_to_be_returned = {
            SensorSource.SPP_FC_DATA: DATA_NOK,
            SensorSource.SPP_LSC_DATA: DATA_NOK,
            SensorSource.SPP_RC_DATA: DATA_NOK,
            SensorSource.SPP_RSC_DATA: DATA_NOK,
        }

        for camera, _ in cameras_to_be_returned.items():
            gt_stream_data = self.get_json_gt_data(gt_data, camera)
            cameras_to_be_returned[camera] = gt_stream_data

        return cameras_to_be_returned, sim_df

    def get_json_gt_data(self, gt_data, camera):
        """From the json file, get the ground truth data for a specific camera as a dataframe"""
        if camera is SensorSource.SPP_FC_DATA:
            gt_df = self.transform_data_to_dataframe(gt_data["SppFront"])
            return gt_df
        if camera is SensorSource.SPP_LSC_DATA:
            gt_df = self.transform_data_to_dataframe(gt_data["SppLeft"])
            return gt_df
        if camera is SensorSource.SPP_RC_DATA:
            gt_df = self.transform_data_to_dataframe(gt_data["SppRear"])
            return gt_df
        if camera is SensorSource.SPP_RSC_DATA:
            gt_df = self.transform_data_to_dataframe(gt_data["SppRight"])
            return gt_df

    @staticmethod
    def transform_data_to_dataframe(gt_data):
        """
        From the json file, get the ground truth data as a dataframe
        Transform a list of dictionaries into a pandas DataFrame.

        Parameters:
        gt_data (list): List of dictionaries to be converted into a DataFrame.

        Returns:
        pd.DataFrame: A DataFrame containing the processed data.
        """
        flat_data = []

        for data in gt_data:
            flat_item = {
                "gt_sig_status": data["sSigHeader"]["eSigStatus"],
                "gt_spp_timestamp": int(data["sSigHeader"]["uiTimeStamp"]),
                "gt_no_of_polygons": data["numberOfPolygons"],
                "gt_no_of_polylines": data["numberOfPolylines"],
            }

            for i, polylines in enumerate(data["polylines"]):
                flat_item[f"gt_vertex_start_index_{i}"] = polylines["vertexStartIndex"]
                flat_item[f"gt_num_vertices_{i}"] = polylines["numVertices"]
                flat_item[f"gt_semantic_{i}"] = polylines["semantic"]
                flat_item[f"gt_confidence_{i}"] = polylines["confidence"]

            for i, vert in enumerate(data["vertices"]):
                flat_item[f"gt_vertex_x_{i}"] = vert["xM"]
                flat_item[f"gt_vertex_y_{i}"] = vert["yM"]
                flat_item[f"gt_vertex_z_{i}"] = vert["zM"]

            flat_data.append(flat_item)

        # Creating DataFrame
        df = pd.DataFrame(flat_data)

        return df


class SPPSignals(SignalDefinition):
    """SPP signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        # Front Camera #
        FC_BASE_CTRL_DATA_OP_MODE = "fc_basectrldata_opmode"
        FC_EOL_CAMERA_EXTRINSICS_SIG_STATUS = "fc_camera_extrinsics_sig_status"
        FC_EOL_CAMERA_EXTRINSICS_POS_X = "fc_camera_extrinsics_x"
        FC_EOL_CAMERA_EXTRINSICS_POS_Y = "fc_camera_extrinsics_y"
        FC_EOL_CAMERA_EXTRINSICS_POS_Z = "fc_camera_extrinsics_z"
        FC_IMAGE_INTRINSICS_SIG_STATUS = "fc_image_intrinsics_sig_status"
        FC_IMAGE_INTRINSICS_FOCAL_X = "fc_image_intrinsics_fx"
        FC_IMAGE_INTRINSICS_FOCAL_Y = "fc_image_intrinsics_fy"
        FC_IMAGE_INTRINSICS_CENTER_X = "fc_image_intrinsics_cx"
        FC_IMAGE_INTRINSICS_CENTER_Y = "fc_image_intrinsics_cy"
        FC_POLYLINES_TIMESTAMP = "fc_polylines_timestamp"
        FC_POLYLINES_SIG_STATUS = "fc_polylines_sig_status"
        FC_POLYLINES_NUMBER_OF_POLYGONS = "fc_polylines_number_of_polygons"
        FC_POLYLINES_NUMBER_OF_POLYLINES = "fc_polylines_number_of_polylines"
        FC_POLYLINES_VERTEX_START_INDEX = "fc_polylines_vertex_start_index_"
        FC_POLYLINES_NUM_VERTICES = "fc_polylines_num_vertices_"
        FC_POLYLINES_CONFIDENCE = "fc_polylines_confidence_"
        FC_POLYLINES_SEMANTIC = "fc_polylines_semantic_"
        FC_POLYLINES_VERTEX_X_COORD = "fc_vertex_x_"
        FC_POLYLINES_VERTEX_Y_COORD = "fc_vertex_y_"
        FC_POLYLINES_VERTEX_Z_COORD = "fc_vertex_z_"
        FC_SEMPOINTS_TIMESTAMP = "fc_sempoints_timestamp"
        FC_SEMPOINTS_SIG_STATUS = "fc_sempoints_sig_status"
        FC_SEMPOINTS_NUM_POINTS = "fc_sempoints_num_points"
        FC_SEMPOINTS_POINTLIST_ID = "fc_semPoints_pointList_id_"
        FC_SEMPOINTS_POINTLIST_X = "fc_semPoints_pointList_x_"
        FC_SEMPOINTS_POINTLIST_Y = "fc_semPoints_pointList_y_"
        FC_SEMPOINTS_POINTLIST_Z = "fc_semPoints_pointList_z_"
        FC_SEMPOINTS_POINTLIST_X_STDDEV = "fc_semPoints_pointList_xStdDev_"
        FC_SEMPOINTS_POINTLIST_Y_STDDEV = "fc_semPoints_pointList_yStdDev_"
        FC_SEMPOINTS_POINTLIST_Z_STDDEV = "fc_semPoints_pointList_zStdDev_"
        FC_SEMPOINTS_POINTLIST_CONFIDENCE = "fc_semPoints_pointList_confidence_"
        FC_SEMPOINTS_POINTLIST_AGE = "fc_semPoints_pointList_age_"
        FC_SEMPOINTS_POINTLIST_SEMANTIC = "fc_semPoints_pointList_semantic_"
        FC_SEMPOINTS_POINTLIST_SEMANTIC_CONFIDENCE = "fc_semPoints_pointList_semanticConfidence_"
        FC_SEMPOINTS_INDICATOR_FLAG = "fc_sem_points_indicator_flag"

        # Left Side Camera #
        LSC_BASE_CTRL_DATA_OP_MODE = "lsc_basectrldata_opmode"
        LSC_EOL_CAMERA_EXTRINSICS_SIG_STATUS = "lsc_camera_extrinsics_sig_status"
        LSC_EOL_CAMERA_EXTRINSICS_POS_X = "lsc_camera_extrinsics_x"
        LSC_EOL_CAMERA_EXTRINSICS_POS_Y = "lsc_camera_extrinsics_y"
        LSC_EOL_CAMERA_EXTRINSICS_POS_Z = "lsc_camera_extrinsics_z"
        LSC_IMAGE_INTRINSICS_SIG_STATUS = "lsc_image_intrinsics_sig_status"
        LSC_IMAGE_INTRINSICS_FOCAL_X = "lsc_image_intrinsics_fx"
        LSC_IMAGE_INTRINSICS_FOCAL_Y = "lsc_image_intrinsics_fy"
        LSC_IMAGE_INTRINSICS_CENTER_X = "lsc_image_intrinsics_cx"
        LSC_IMAGE_INTRINSICS_CENTER_Y = "lsc_image_intrinsics_cy"
        LSC_POLYLINES_TIMESTAMP = "lsc_polylines_timestamp"
        LSC_POLYLINES_SIG_STATUS = "lsc_polylines_sig_status"
        LSC_POLYLINES_NUMBER_OF_POLYGONS = "lsc_polylines_number_of_polygons"
        LSC_POLYLINES_NUMBER_OF_POLYLINES = "lsc_polylines_number_of_polylines"
        LSC_POLYLINES_VERTEX_START_INDEX = "lsc_polylines_vertex_start_index_"
        LSC_POLYLINES_NUM_VERTICES = "lsc_polylines_num_vertices_"
        LSC_POLYLINES_CONFIDENCE = "lsc_polylines_confidence_"
        LSC_POLYLINES_SEMANTIC = "lsc_polylines_semantic_"
        LSC_POLYLINES_VERTEX_X_COORD = "lsc_vertex_x_"
        LSC_POLYLINES_VERTEX_Y_COORD = "lsc_vertex_y_"
        LSC_POLYLINES_VERTEX_Z_COORD = "lsc_vertex_z_"
        LSC_SEMPOINTS_TIMESTAMP = "lsc_sempoints_timestamp"
        LSC_SEMPOINTS_SIG_STATUS = "lsc_sempoints_sig_status"
        LSC_SEMPOINTS_NUM_POINTS = "lsc_sempoints_num_points"
        LSC_SEMPOINTS_POINTLIST_ID = "lsc_semPoints_pointList_id_"
        LSC_SEMPOINTS_POINTLIST_X = "lsc_semPoints_pointList_x_"
        LSC_SEMPOINTS_POINTLIST_Y = "lsc_semPoints_pointList_y_"
        LSC_SEMPOINTS_POINTLIST_Z = "lsc_semPoints_pointList_z_"
        LSC_SEMPOINTS_POINTLIST_X_STDDEV = "lsc_semPoints_pointList_xStdDev_"
        LSC_SEMPOINTS_POINTLIST_Y_STDDEV = "lsc_semPoints_pointList_yStdDev_"
        LSC_SEMPOINTS_POINTLIST_Z_STDDEV = "lsc_semPoints_pointList_zStdDev_"
        LSC_SEMPOINTS_POINTLIST_CONFIDENCE = "lsc_semPoints_pointList_confidence_"
        LSC_SEMPOINTS_POINTLIST_AGE = "lsc_semPoints_pointList_age_"
        LSC_SEMPOINTS_POINTLIST_SEMANTIC = "lsc_semPoints_pointList_semantic_"
        LSC_SEMPOINTS_POINTLIST_SEMANTIC_CONFIDENCE = "lsc_semPoints_pointList_semanticConfidence_"
        LSC_SEMPOINTS_INDICATOR_FLAG = "lsc_sem_points_indicator_flag"

        # Rear Camera #
        RC_BASE_CTRL_DATA_OP_MODE = "rc_basectrldata_opmode"
        RC_EOL_CAMERA_EXTRINSICS_SIG_STATUS = "rc_camera_extrinsics_sig_status"
        RC_EOL_CAMERA_EXTRINSICS_POS_X = "rc_camera_extrinsics_x"
        RC_EOL_CAMERA_EXTRINSICS_POS_Y = "rc_camera_extrinsics_y"
        RC_EOL_CAMERA_EXTRINSICS_POS_Z = "rc_camera_extrinsics_z"
        RC_IMAGE_INTRINSICS_SIG_STATUS = "rc_image_intrinsics_sig_status"
        RC_IMAGE_INTRINSICS_FOCAL_X = "rc_image_intrinsics_fx"
        RC_IMAGE_INTRINSICS_FOCAL_Y = "rc_image_intrinsics_fy"
        RC_IMAGE_INTRINSICS_CENTER_X = "rc_image_intrinsics_cx"
        RC_IMAGE_INTRINSICS_CENTER_Y = "rc_image_intrinsics_cy"
        RC_GDRPOINTLIST_TIMESTAMP = "rc_gdrpointlist_timestamp"
        RC_SEMSEG_TIMESTAMP = "rc_semseg_timestamp"
        RC_POLYLINES_TIMESTAMP = "rc_polylines_timestamp"
        RC_POLYLINES_SIG_STATUS = "rc_polylines_sig_status"
        RC_POLYLINES_NUMBER_OF_POLYGONS = "rc_polylines_number_of_polygons"
        RC_POLYLINES_NUMBER_OF_POLYLINES = "rc_polylines_number_of_polylines"
        RC_POLYLINES_VERTEX_START_INDEX = "rc_polylines_vertex_start_index_"
        RC_POLYLINES_NUM_VERTICES = "rc_polylines_num_vertices_"
        RC_POLYLINES_CONFIDENCE = "rc_polylines_confidence_"
        RC_POLYLINES_SEMANTIC = "rc_polylines_semantic_"
        RC_POLYLINES_VERTEX_X_COORD = "rc_vertex_x_"
        RC_POLYLINES_VERTEX_Y_COORD = "rc_vertex_y_"
        RC_POLYLINES_VERTEX_Z_COORD = "rc_vertex_z_"
        RC_SEMPOINTS_TIMESTAMP = "rc_sempoints_timestamp"
        RC_SEMPOINTS_SIG_STATUS = "rc_sempoints_sig_status"
        RC_SEMPOINTS_NUM_POINTS = "rc_sempoints_num_points"
        RC_SEMPOINTS_POINTLIST_ID = "rc_semPoints_pointList_id_"
        RC_SEMPOINTS_POINTLIST_X = "rc_semPoints_pointList_x_"
        RC_SEMPOINTS_POINTLIST_Y = "rc_semPoints_pointList_y_"
        RC_SEMPOINTS_POINTLIST_Z = "rc_semPoints_pointList_z_"
        RC_SEMPOINTS_POINTLIST_X_STDDEV = "rc_semPoints_pointList_xStdDev_"
        RC_SEMPOINTS_POINTLIST_Y_STDDEV = "rc_semPoints_pointList_yStdDev_"
        RC_SEMPOINTS_POINTLIST_Z_STDDEV = "rc_semPoints_pointList_zStdDev_"
        RC_SEMPOINTS_POINTLIST_CONFIDENCE = "rc_semPoints_pointList_confidence_"
        RC_SEMPOINTS_POINTLIST_AGE = "rc_semPoints_pointList_age_"
        RC_SEMPOINTS_POINTLIST_SEMANTIC = "rc_semPoints_pointList_semantic_"
        RC_SEMPOINTS_POINTLIST_SEMANTIC_CONFIDENCE = "rc_semPoints_pointList_semanticConfidence_"
        RC_SEMPOINTS_INDICATOR_FLAG = "rc_sem_points_indicator_flag"

        # Right Side Camera #
        RSC_BASE_CTRL_DATA_OP_MODE = "rsc_basectrldata_opmode"
        RSC_EOL_CAMERA_EXTRINSICS_SIG_STATUS = "rsc_camera_extrinsics_sig_status"
        RSC_EOL_CAMERA_EXTRINSICS_POS_X = "rsc_camera_extrinsics_x"
        RSC_EOL_CAMERA_EXTRINSICS_POS_Y = "rsc_camera_extrinsics_y"
        RSC_EOL_CAMERA_EXTRINSICS_POS_Z = "rsc_camera_extrinsics_z"
        RSC_IMAGE_INTRINSICS_SIG_STATUS = "rsc_image_intrinsics_sig_status"
        RSC_IMAGE_INTRINSICS_FOCAL_X = "rsc_image_intrinsics_fx"
        RSC_IMAGE_INTRINSICS_FOCAL_Y = "rsc_image_intrinsics_fy"
        RSC_IMAGE_INTRINSICS_CENTER_X = "rsc_image_intrinsics_cx"
        RSC_IMAGE_INTRINSICS_CENTER_Y = "rsc_image_intrinsics_cy"
        RSC_GDRPOINTLIST_TIMESTAMP = "rsc_gdrpointlist_timestamp"
        RSC_SEMSEG_TIMESTAMP = "rsc_semseg_timestamp"
        RSC_POLYLINES_TIMESTAMP = "rsc_polylines_timestamp"
        RSC_POLYLINES_SIG_STATUS = "rsc_polylines_sig_status"
        RSC_POLYLINES_NUMBER_OF_POLYGONS = "rsc_polylines_number_of_polygons"
        RSC_POLYLINES_NUMBER_OF_POLYLINES = "rsc_polylines_number_of_polylines"
        RSC_POLYLINES_VERTEX_START_INDEX = "rsc_polylines_vertex_start_index_"
        RSC_POLYLINES_NUM_VERTICES = "rsc_polylines_num_vertices_"
        RSC_POLYLINES_CONFIDENCE = "rsc_polylines_confidence_"
        RSC_POLYLINES_SEMANTIC = "rsc_polylines_semantic_"
        RSC_POLYLINES_VERTEX_X_COORD = "rsc_vertex_x_"
        RSC_POLYLINES_VERTEX_Y_COORD = "rsc_vertex_y_"
        RSC_POLYLINES_VERTEX_Z_COORD = "rsc_vertex_z_"
        RSC_SEMPOINTS_TIMESTAMP = "rsc_sempoints_timestamp"
        RSC_SEMPOINTS_SIG_STATUS = "rsc_sempoints_sig_status"
        RSC_SEMPOINTS_NUM_POINTS = "rsc_sempoints_num_points"
        RSC_SEMPOINTS_POINTLIST_ID = "rsc_semPoints_pointList_id_"
        RSC_SEMPOINTS_POINTLIST_X = "rsc_semPoints_pointList_x_"
        RSC_SEMPOINTS_POINTLIST_Y = "rsc_semPoints_pointList_y_"
        RSC_SEMPOINTS_POINTLIST_Z = "rsc_semPoints_pointList_z_"
        RSC_SEMPOINTS_POINTLIST_X_STDDEV = "rsc_semPoints_pointList_xStdDev_"
        RSC_SEMPOINTS_POINTLIST_Y_STDDEV = "rsc_semPoints_pointList_yStdDev_"
        RSC_SEMPOINTS_POINTLIST_Z_STDDEV = "rsc_semPoints_pointList_zStdDev_"
        RSC_SEMPOINTS_POINTLIST_CONFIDENCE = "rsc_semPoints_pointList_confidence_"
        RSC_SEMPOINTS_POINTLIST_AGE = "rsc_semPoints_pointList_age_"
        RSC_SEMPOINTS_POINTLIST_SEMANTIC = "rsc_semPoints_pointList_semantic_"
        RSC_SEMPOINTS_POINTLIST_SEMANTIC_CONFIDENCE = "rsc_semPoints_pointList_semanticConfidence_"
        RSC_SEMPOINTS_INDICATOR_FLAG = "rsc_sem_points_indicator_flag"

        TEST = "failed_test_signal"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = self.get_properties()

    def get_properties(self):
        """Get signals names."""
        signal_dict = {
            # self.Columns.MTS_TS: "MTS.Package.TimeStamp",
            self.Columns.FC_BASE_CTRL_DATA_OP_MODE: "MTA_ADC5.SPP_FC_DATA.syncRef.m_baseCtrlData.eOpMode",
            self.Columns.FC_EOL_CAMERA_EXTRINSICS_SIG_STATUS: "MTA_ADC5.PARAMETER_HANDLER_DATA.FC_EOLCalibrationExtrinsicsISO.sSigHeader.eSigStatus",
            self.Columns.FC_EOL_CAMERA_EXTRINSICS_POS_X: "MTA_ADC5.PARAMETER_HANDLER_DATA.FC_EOLCalibrationExtrinsicsISO.posX_mm",
            self.Columns.FC_EOL_CAMERA_EXTRINSICS_POS_Y: "MTA_ADC5.PARAMETER_HANDLER_DATA.FC_EOLCalibrationExtrinsicsISO.posY_mm",
            self.Columns.FC_EOL_CAMERA_EXTRINSICS_POS_Z: "MTA_ADC5.PARAMETER_HANDLER_DATA.FC_EOLCalibrationExtrinsicsISO.posZ_mm",
            self.Columns.FC_IMAGE_INTRINSICS_SIG_STATUS: "MTA_ADC5.GRAPPA_FC_IMAGE.GrappaSemSegFcImage.signalHeader.eSigStatus",
            self.Columns.FC_IMAGE_INTRINSICS_FOCAL_X: "MTA_ADC5.GRAPPA_FC_IMAGE.GrappaSemSegFcImage.imageHeader.intrinsics.focalX",
            self.Columns.FC_IMAGE_INTRINSICS_FOCAL_Y: "MTA_ADC5.GRAPPA_FC_IMAGE.GrappaSemSegFcImage.imageHeader.intrinsics.focalY",
            self.Columns.FC_IMAGE_INTRINSICS_CENTER_X: "MTA_ADC5.GRAPPA_FC_IMAGE.GrappaSemSegFcImage.imageHeader.intrinsics.centerX",
            self.Columns.FC_IMAGE_INTRINSICS_CENTER_Y: "MTA_ADC5.GRAPPA_FC_IMAGE.GrappaSemSegFcImage.imageHeader.intrinsics.centerY",
            self.Columns.FC_POLYLINES_TIMESTAMP: "MTA_ADC5.SPP_FC_DATA.pSppPolylines.sSigHeader.uiTimeStamp",
            self.Columns.FC_POLYLINES_SIG_STATUS: "MTA_ADC5.SPP_FC_DATA.pSppPolylines.sSigHeader.eSigStatus",
            self.Columns.FC_POLYLINES_NUMBER_OF_POLYGONS: "MTA_ADC5.SPP_FC_DATA.pSppPolylines.numberOfPolygons",
            self.Columns.FC_POLYLINES_NUMBER_OF_POLYLINES: "MTA_ADC5.SPP_FC_DATA.pSppPolylines.numberOfPolylines",
            self.Columns.FC_SEMPOINTS_TIMESTAMP: "MTA_ADC5.SPP_FC_DATA.pSppSemPoints.sSigHeader.uiTimeStamp",
            self.Columns.FC_SEMPOINTS_SIG_STATUS: "MTA_ADC5.SPP_FC_DATA.pSppSemPoints.sSigHeader.eSigStatus",
            self.Columns.FC_SEMPOINTS_NUM_POINTS: "MTA_ADC5.SPP_FC_DATA.pSppSemPoints.numPoints",
            self.Columns.FC_SEMPOINTS_INDICATOR_FLAG: "MTA_ADC5.SPP_FC_DATA.pSppSemPoints.bIsLatencyCompensated",
            self.Columns.LSC_BASE_CTRL_DATA_OP_MODE: "MTA_ADC5.SPP_LSC_DATA.syncRef.m_baseCtrlData.eOpMode",
            self.Columns.LSC_EOL_CAMERA_EXTRINSICS_SIG_STATUS: "MTA_ADC5.PARAMETER_HANDLER_DATA.LSC_EOLCalibrationExtrinsicsISO.sSigHeader.eSigStatus",
            self.Columns.LSC_EOL_CAMERA_EXTRINSICS_POS_X: "MTA_ADC5.PARAMETER_HANDLER_DATA.LSC_EOLCalibrationExtrinsicsISO.posX_mm",
            self.Columns.LSC_EOL_CAMERA_EXTRINSICS_POS_Y: "MTA_ADC5.PARAMETER_HANDLER_DATA.LSC_EOLCalibrationExtrinsicsISO.posY_mm",
            self.Columns.LSC_EOL_CAMERA_EXTRINSICS_POS_Z: "MTA_ADC5.PARAMETER_HANDLER_DATA.LSC_EOLCalibrationExtrinsicsISO.posZ_mm",
            self.Columns.LSC_IMAGE_INTRINSICS_SIG_STATUS: "MTA_ADC5.GRAPPA_LSC_IMAGE.GrappaSemSegLscImage.signalHeader.eSigStatus",
            self.Columns.LSC_IMAGE_INTRINSICS_FOCAL_X: "MTA_ADC5.GRAPPA_LSC_IMAGE.GrappaSemSegLscImage.imageHeader.intrinsics.focalX",
            self.Columns.LSC_IMAGE_INTRINSICS_FOCAL_Y: "MTA_ADC5.GRAPPA_LSC_IMAGE.GrappaSemSegLscImage.imageHeader.intrinsics.focalY",
            self.Columns.LSC_IMAGE_INTRINSICS_CENTER_X: "MTA_ADC5.GRAPPA_LSC_IMAGE.GrappaSemSegLscImage.imageHeader.intrinsics.centerX",
            self.Columns.LSC_IMAGE_INTRINSICS_CENTER_Y: "MTA_ADC5.GRAPPA_LSC_IMAGE.GrappaSemSegLscImage.imageHeader.intrinsics.centerY",
            self.Columns.LSC_POLYLINES_TIMESTAMP: "MTA_ADC5.SPP_LSC_DATA.pSppPolylines.sSigHeader.uiTimeStamp",
            self.Columns.LSC_POLYLINES_SIG_STATUS: "MTA_ADC5.SPP_LSC_DATA.pSppPolylines.sSigHeader.eSigStatus",
            self.Columns.LSC_POLYLINES_NUMBER_OF_POLYGONS: "MTA_ADC5.SPP_LSC_DATA.pSppPolylines.numberOfPolygons",
            self.Columns.LSC_POLYLINES_NUMBER_OF_POLYLINES: "MTA_ADC5.SPP_LSC_DATA.pSppPolylines.numberOfPolylines",
            self.Columns.LSC_SEMPOINTS_TIMESTAMP: "MTA_ADC5.SPP_LSC_DATA.pSppSemPoints.sSigHeader.uiTimeStamp",
            self.Columns.LSC_SEMPOINTS_SIG_STATUS: "MTA_ADC5.SPP_LSC_DATA.pSppSemPoints.sSigHeader.eSigStatus",
            self.Columns.LSC_SEMPOINTS_NUM_POINTS: "MTA_ADC5.SPP_LSC_DATA.pSppSemPoints.numPoints",
            self.Columns.LSC_SEMPOINTS_INDICATOR_FLAG: "MTA_ADC5.SPP_LSC_DATA.pSppSemPoints.bIsLatencyCompensated",
            self.Columns.RC_BASE_CTRL_DATA_OP_MODE: "MTA_ADC5.SPP_RC_DATA.syncRef.m_baseCtrlData.eOpMode",
            self.Columns.RC_EOL_CAMERA_EXTRINSICS_SIG_STATUS: "MTA_ADC5.PARAMETER_HANDLER_DATA.RC_EOLCalibrationExtrinsicsISO.sSigHeader.eSigStatus",
            self.Columns.RC_EOL_CAMERA_EXTRINSICS_POS_X: "MTA_ADC5.PARAMETER_HANDLER_DATA.RC_EOLCalibrationExtrinsicsISO.posX_mm",
            self.Columns.RC_EOL_CAMERA_EXTRINSICS_POS_Y: "MTA_ADC5.PARAMETER_HANDLER_DATA.RC_EOLCalibrationExtrinsicsISO.posY_mm",
            self.Columns.RC_EOL_CAMERA_EXTRINSICS_POS_Z: "MTA_ADC5.PARAMETER_HANDLER_DATA.RC_EOLCalibrationExtrinsicsISO.posZ_mm",
            self.Columns.RC_IMAGE_INTRINSICS_SIG_STATUS: "MTA_ADC5.GRAPPA_RC_IMAGE.GrappaSemSegRcImage.signalHeader.eSigStatus",
            self.Columns.RC_IMAGE_INTRINSICS_FOCAL_X: "MTA_ADC5.GRAPPA_RC_IMAGE.GrappaSemSegRcImage.imageHeader.intrinsics.focalX",
            self.Columns.RC_IMAGE_INTRINSICS_FOCAL_Y: "MTA_ADC5.GRAPPA_RC_IMAGE.GrappaSemSegRcImage.imageHeader.intrinsics.focalY",
            self.Columns.RC_IMAGE_INTRINSICS_CENTER_X: "MTA_ADC5.GRAPPA_RC_IMAGE.GrappaSemSegRcImage.imageHeader.intrinsics.centerX",
            self.Columns.RC_IMAGE_INTRINSICS_CENTER_Y: "MTA_ADC5.GRAPPA_RC_IMAGE.GrappaSemSegRcImage.imageHeader.intrinsics.centerY",
            self.Columns.RC_POLYLINES_TIMESTAMP: "MTA_ADC5.SPP_RC_DATA.pSppPolylines.sSigHeader.uiTimeStamp",
            self.Columns.RC_POLYLINES_SIG_STATUS: "MTA_ADC5.SPP_RC_DATA.pSppPolylines.sSigHeader.eSigStatus",
            self.Columns.RC_POLYLINES_NUMBER_OF_POLYGONS: "MTA_ADC5.SPP_RC_DATA.pSppPolylines.numberOfPolygons",
            self.Columns.RC_POLYLINES_NUMBER_OF_POLYLINES: "MTA_ADC5.SPP_RC_DATA.pSppPolylines.numberOfPolylines",
            self.Columns.RC_SEMPOINTS_TIMESTAMP: "MTA_ADC5.SPP_RC_DATA.pSppSemPoints.sSigHeader.uiTimeStamp",
            self.Columns.RC_SEMPOINTS_SIG_STATUS: "MTA_ADC5.SPP_RC_DATA.pSppSemPoints.sSigHeader.eSigStatus",
            self.Columns.RC_SEMPOINTS_NUM_POINTS: "MTA_ADC5.SPP_RC_DATA.pSppSemPoints.numPoints",
            self.Columns.RC_SEMPOINTS_INDICATOR_FLAG: "MTA_ADC5.SPP_RC_DATA.pSppSemPoints.bIsLatencyCompensated",
            self.Columns.RSC_BASE_CTRL_DATA_OP_MODE: "MTA_ADC5.SPP_RSC_DATA.syncRef.m_baseCtrlData.eOpMode",
            self.Columns.RSC_EOL_CAMERA_EXTRINSICS_SIG_STATUS: "MTA_ADC5.PARAMETER_HANDLER_DATA.RSC_EOLCalibrationExtrinsicsISO.sSigHeader.eSigStatus",
            self.Columns.RSC_EOL_CAMERA_EXTRINSICS_POS_X: "MTA_ADC5.PARAMETER_HANDLER_DATA.RSC_EOLCalibrationExtrinsicsISO.posX_mm",
            self.Columns.RSC_EOL_CAMERA_EXTRINSICS_POS_Y: "MTA_ADC5.PARAMETER_HANDLER_DATA.RSC_EOLCalibrationExtrinsicsISO.posY_mm",
            self.Columns.RSC_EOL_CAMERA_EXTRINSICS_POS_Z: "MTA_ADC5.PARAMETER_HANDLER_DATA.RSC_EOLCalibrationExtrinsicsISO.posZ_mm",
            self.Columns.RSC_IMAGE_INTRINSICS_FOCAL_X: "MTA_ADC5.GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.imageHeader.intrinsics.focalX",
            self.Columns.RSC_IMAGE_INTRINSICS_SIG_STATUS: "MTA_ADC5.GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.signalHeader.eSigStatus",
            self.Columns.RSC_IMAGE_INTRINSICS_FOCAL_Y: "MTA_ADC5.GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.imageHeader.intrinsics.focalY",
            self.Columns.RSC_IMAGE_INTRINSICS_CENTER_X: "MTA_ADC5.GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.imageHeader.intrinsics.centerX",
            self.Columns.RSC_IMAGE_INTRINSICS_CENTER_Y: "MTA_ADC5.GRAPPA_RSC_IMAGE.GrappaSemSegRscImage.imageHeader.intrinsics.centerY",
            self.Columns.RSC_POLYLINES_TIMESTAMP: "MTA_ADC5.SPP_RSC_DATA.pSppPolylines.sSigHeader.uiTimeStamp",
            self.Columns.RSC_POLYLINES_SIG_STATUS: "MTA_ADC5.SPP_RSC_DATA.pSppPolylines.sSigHeader.eSigStatus",
            self.Columns.RSC_POLYLINES_NUMBER_OF_POLYGONS: "MTA_ADC5.SPP_RSC_DATA.pSppPolylines.numberOfPolygons",
            self.Columns.RSC_POLYLINES_NUMBER_OF_POLYLINES: "MTA_ADC5.SPP_RSC_DATA.pSppPolylines.numberOfPolylines",
            self.Columns.RSC_SEMPOINTS_TIMESTAMP: "MTA_ADC5.SPP_RSC_DATA.pSppSemPoints.sSigHeader.uiTimeStamp",
            self.Columns.RSC_SEMPOINTS_SIG_STATUS: "MTA_ADC5.SPP_RSC_DATA.pSppSemPoints.sSigHeader.eSigStatus",
            self.Columns.RSC_SEMPOINTS_NUM_POINTS: "MTA_ADC5.SPP_RSC_DATA.pSppSemPoints.numPoints",
            self.Columns.RSC_SEMPOINTS_INDICATOR_FLAG: "MTA_ADC5.SPP_RSC_DATA.pSppSemPoints.bIsLatencyCompensated",
        }

        for idx in range(0, Polylines.SPP_MAX_NUMBER_POLYLINES):
            signal_dict[self.Columns.FC_POLYLINES_VERTEX_START_INDEX + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppPolylines.polylines[{idx}].vertexStartIndex"
            )
            signal_dict[self.Columns.FC_POLYLINES_NUM_VERTICES + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppPolylines.polylines[{idx}].numVertices"
            )
            signal_dict[self.Columns.FC_POLYLINES_CONFIDENCE + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppPolylines.polylines[{idx}].confidence"
            )
            signal_dict[self.Columns.FC_POLYLINES_SEMANTIC + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppPolylines.polylines[{idx}].semantic"
            )

            signal_dict[self.Columns.LSC_POLYLINES_VERTEX_START_INDEX + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppPolylines.polylines[{idx}].vertexStartIndex"
            )
            signal_dict[self.Columns.LSC_POLYLINES_NUM_VERTICES + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppPolylines.polylines[{idx}].numVertices"
            )
            signal_dict[self.Columns.LSC_POLYLINES_CONFIDENCE + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppPolylines.polylines[{idx}].confidence"
            )
            signal_dict[self.Columns.LSC_POLYLINES_SEMANTIC + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppPolylines.polylines[{idx}].semantic"
            )

            signal_dict[self.Columns.RC_POLYLINES_VERTEX_START_INDEX + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppPolylines.polylines[{idx}].vertexStartIndex"
            )
            signal_dict[self.Columns.RC_POLYLINES_NUM_VERTICES + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppPolylines.polylines[{idx}].numVertices"
            )
            signal_dict[self.Columns.RC_POLYLINES_CONFIDENCE + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppPolylines.polylines[{idx}].confidence"
            )
            signal_dict[self.Columns.RC_POLYLINES_SEMANTIC + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppPolylines.polylines[{idx}].semantic"
            )

            signal_dict[self.Columns.RSC_POLYLINES_VERTEX_START_INDEX + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppPolylines.polylines[{idx}].vertexStartIndex"
            )
            signal_dict[self.Columns.RSC_POLYLINES_NUM_VERTICES + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppPolylines.polylines[{idx}].numVertices"
            )
            signal_dict[self.Columns.RSC_POLYLINES_CONFIDENCE + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppPolylines.polylines[{idx}].confidence"
            )
            signal_dict[self.Columns.RSC_POLYLINES_SEMANTIC + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppPolylines.polylines[{idx}].semantic"
            )

        for idx in range(0, Polylines.SPP_MAX_NUMBER_VERTICES):
            signal_dict[self.Columns.FC_POLYLINES_VERTEX_X_COORD + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppPolylines.vertices[{idx}].x_m"
            )
            signal_dict[self.Columns.FC_POLYLINES_VERTEX_Y_COORD + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppPolylines.vertices[{idx}].y_m"
            )
            signal_dict[self.Columns.FC_POLYLINES_VERTEX_Z_COORD + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppPolylines.vertices[{idx}].z_m"
            )

            signal_dict[self.Columns.LSC_POLYLINES_VERTEX_X_COORD + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppPolylines.vertices[{idx}].x_m"
            )
            signal_dict[self.Columns.LSC_POLYLINES_VERTEX_Y_COORD + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppPolylines.vertices[{idx}].y_m"
            )
            signal_dict[self.Columns.LSC_POLYLINES_VERTEX_Z_COORD + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppPolylines.vertices[{idx}].z_m"
            )

            signal_dict[self.Columns.RC_POLYLINES_VERTEX_X_COORD + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppPolylines.vertices[{idx}].x_m"
            )
            signal_dict[self.Columns.RC_POLYLINES_VERTEX_Y_COORD + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppPolylines.vertices[{idx}].y_m"
            )
            signal_dict[self.Columns.RC_POLYLINES_VERTEX_Z_COORD + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppPolylines.vertices[{idx}].z_m"
            )

            signal_dict[self.Columns.RSC_POLYLINES_VERTEX_X_COORD + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppPolylines.vertices[{idx}].x_m"
            )
            signal_dict[self.Columns.RSC_POLYLINES_VERTEX_Y_COORD + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppPolylines.vertices[{idx}].y_m"
            )
            signal_dict[self.Columns.RSC_POLYLINES_VERTEX_Z_COORD + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppPolylines.vertices[{idx}].z_m"
            )

        for idx in range(0, SppSemPoints.SPP_SEMPOINTS_MAX_NUMBER_VERTICES):
            signal_dict[self.Columns.FC_SEMPOINTS_POINTLIST_ID + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppSemPoints.pointList[{idx}].id"
            )
            signal_dict[self.Columns.FC_SEMPOINTS_POINTLIST_X + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppSemPoints.pointList[{idx}].x_m"
            )
            signal_dict[self.Columns.FC_SEMPOINTS_POINTLIST_Y + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppSemPoints.pointList[{idx}].y_m"
            )
            signal_dict[self.Columns.FC_SEMPOINTS_POINTLIST_Z + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppSemPoints.pointList[{idx}].z_m"
            )
            signal_dict[self.Columns.FC_SEMPOINTS_POINTLIST_X_STDDEV + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppSemPoints.pointList[{idx}].xStdDev_mm"
            )
            signal_dict[self.Columns.FC_SEMPOINTS_POINTLIST_Y_STDDEV + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppSemPoints.pointList[{idx}].yStdDev_mm"
            )
            signal_dict[self.Columns.FC_SEMPOINTS_POINTLIST_Z_STDDEV + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppSemPoints.pointList[{idx}].zStdDev_mm"
            )
            signal_dict[self.Columns.FC_SEMPOINTS_POINTLIST_CONFIDENCE + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppSemPoints.pointList[{idx}].confidence"
            )
            signal_dict[self.Columns.FC_SEMPOINTS_POINTLIST_AGE + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppSemPoints.pointList[{idx}].uAge"
            )
            signal_dict[self.Columns.FC_SEMPOINTS_POINTLIST_SEMANTIC + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppSemPoints.pointList[{idx}].semantic"
            )
            signal_dict[self.Columns.FC_SEMPOINTS_POINTLIST_SEMANTIC_CONFIDENCE + str(idx)] = (
                f"MTA_ADC5.SPP_FC_DATA.pSppSemPoints.pointList[{idx}].semanticConfidence"
            )

            signal_dict[self.Columns.LSC_SEMPOINTS_POINTLIST_ID + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppSemPoints.pointList[{idx}].id"
            )
            signal_dict[self.Columns.LSC_SEMPOINTS_POINTLIST_X + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppSemPoints.pointList[{idx}].x_m"
            )
            signal_dict[self.Columns.LSC_SEMPOINTS_POINTLIST_Y + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppSemPoints.pointList[{idx}].y_m"
            )
            signal_dict[self.Columns.LSC_SEMPOINTS_POINTLIST_Z + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppSemPoints.pointList[{idx}].z_m"
            )
            signal_dict[self.Columns.LSC_SEMPOINTS_POINTLIST_X_STDDEV + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppSemPoints.pointList[{idx}].xStdDev_mm"
            )
            signal_dict[self.Columns.LSC_SEMPOINTS_POINTLIST_Y_STDDEV + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppSemPoints.pointList[{idx}].yStdDev_mm"
            )
            signal_dict[self.Columns.LSC_SEMPOINTS_POINTLIST_Z_STDDEV + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppSemPoints.pointList[{idx}].zStdDev_mm"
            )
            signal_dict[self.Columns.LSC_SEMPOINTS_POINTLIST_CONFIDENCE + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppSemPoints.pointList[{idx}].confidence"
            )
            signal_dict[self.Columns.LSC_SEMPOINTS_POINTLIST_AGE + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppSemPoints.pointList[{idx}].uAge"
            )
            signal_dict[self.Columns.LSC_SEMPOINTS_POINTLIST_SEMANTIC + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppSemPoints.pointList[{idx}].semantic"
            )
            signal_dict[self.Columns.LSC_SEMPOINTS_POINTLIST_SEMANTIC_CONFIDENCE + str(idx)] = (
                f"MTA_ADC5.SPP_LSC_DATA.pSppSemPoints.pointList[{idx}].semanticConfidence"
            )

            signal_dict[self.Columns.RC_SEMPOINTS_POINTLIST_ID + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppSemPoints.pointList[{idx}].id"
            )
            signal_dict[self.Columns.RC_SEMPOINTS_POINTLIST_X + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppSemPoints.pointList[{idx}].x_m"
            )
            signal_dict[self.Columns.RC_SEMPOINTS_POINTLIST_Y + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppSemPoints.pointList[{idx}].y_m"
            )
            signal_dict[self.Columns.RC_SEMPOINTS_POINTLIST_Z + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppSemPoints.pointList[{idx}].z_m"
            )
            signal_dict[self.Columns.RC_SEMPOINTS_POINTLIST_X_STDDEV + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppSemPoints.pointList[{idx}].xStdDev_mm"
            )
            signal_dict[self.Columns.RC_SEMPOINTS_POINTLIST_Y_STDDEV + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppSemPoints.pointList[{idx}].yStdDev_mm"
            )
            signal_dict[self.Columns.RC_SEMPOINTS_POINTLIST_Z_STDDEV + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppSemPoints.pointList[{idx}].zStdDev_mm"
            )
            signal_dict[self.Columns.RC_SEMPOINTS_POINTLIST_CONFIDENCE + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppSemPoints.pointList[{idx}].confidence"
            )
            signal_dict[self.Columns.RC_SEMPOINTS_POINTLIST_AGE + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppSemPoints.pointList[{idx}].uAge"
            )
            signal_dict[self.Columns.RC_SEMPOINTS_POINTLIST_SEMANTIC + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppSemPoints.pointList[{idx}].semantic"
            )
            signal_dict[self.Columns.RC_SEMPOINTS_POINTLIST_SEMANTIC_CONFIDENCE + str(idx)] = (
                f"MTA_ADC5.SPP_RC_DATA.pSppSemPoints.pointList[{idx}].semanticConfidence"
            )

            signal_dict[self.Columns.RSC_SEMPOINTS_POINTLIST_ID + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppSemPoints.pointList[{idx}].id"
            )
            signal_dict[self.Columns.RSC_SEMPOINTS_POINTLIST_X + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppSemPoints.pointList[{idx}].x_m"
            )
            signal_dict[self.Columns.RSC_SEMPOINTS_POINTLIST_Y + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppSemPoints.pointList[{idx}].y_m"
            )
            signal_dict[self.Columns.RSC_SEMPOINTS_POINTLIST_Z + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppSemPoints.pointList[{idx}].z_m"
            )
            signal_dict[self.Columns.RSC_SEMPOINTS_POINTLIST_X_STDDEV + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppSemPoints.pointList[{idx}].xStdDev_mm"
            )
            signal_dict[self.Columns.RSC_SEMPOINTS_POINTLIST_Y_STDDEV + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppSemPoints.pointList[{idx}].yStdDev_mm"
            )
            signal_dict[self.Columns.RSC_SEMPOINTS_POINTLIST_Z_STDDEV + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppSemPoints.pointList[{idx}].zStdDev_mm"
            )
            signal_dict[self.Columns.RSC_SEMPOINTS_POINTLIST_CONFIDENCE + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppSemPoints.pointList[{idx}].confidence"
            )
            signal_dict[self.Columns.RSC_SEMPOINTS_POINTLIST_AGE + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppSemPoints.pointList[{idx}].uAge"
            )
            signal_dict[self.Columns.RSC_SEMPOINTS_POINTLIST_SEMANTIC + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppSemPoints.pointList[{idx}].semantic"
            )
            signal_dict[self.Columns.RSC_SEMPOINTS_POINTLIST_SEMANTIC_CONFIDENCE + str(idx)] = (
                f"MTA_ADC5.SPP_RSC_DATA.pSppSemPoints.pointList[{idx}].semanticConfidence"
            )

        return signal_dict


def check_signals_availability(list_of_signals, df):
    """Check if all required signals are available in the bsig file."""
    signal_availability = True
    list_of_missing_signals = []

    for signal in list_of_signals:
        if signal not in df:
            signal_availability = False
            list_of_missing_signals.append(f'Signal "{signal}" is not available in the bsig file')

    return signal_availability, list_of_missing_signals


def extract_polylines(camera, start, end, row):
    """
    Get all the polylines.

    :param camera
    :param start
    :param end
    :param row
    :return: a list of tuples. Each vertex will be a tuple. Each polyline will be a tuple of tuples.
    """
    polylines = []

    for polyline_idx in range(start, end):
        polyline_vertices = ()

        vertex_start_index = get_polyline_vertex_start_index(camera, polyline_idx, row)
        vertex_end_index = vertex_start_index + get_polyline_num_vertices(camera, polyline_idx, row)

        for coord_idx in range(vertex_start_index, vertex_end_index):
            x = get_vertex_x(camera, coord_idx, row)
            y = get_vertex_y(camera, coord_idx, row)
            z = get_vertex_z(camera, coord_idx, row)

            polyline_vertices = polyline_vertices + ((x, y, z),)

        polylines.append(polyline_vertices)

    return polylines


def extract_coordinates(camera, start, end, row):
    """
    Get all the vertices.

    :param camera
    :param start
    :param end
    :param row
    :return: each vertex will be a tuple. each polyline will be a tuple of tuples.
    """
    polyline_vertices = ()
    for coord_idx in range(start, end):
        x = get_vertex_x(camera, coord_idx, row)
        y = get_vertex_y(camera, coord_idx, row)
        z = get_vertex_z(camera, coord_idx, row)

        polyline_vertices = polyline_vertices + ((x, y, z),)

    return polyline_vertices


def check_num_vertices_range(camera, start, end, min_number_of_points, frame, row):
    """
    Loops over a list of elements and check that each polygon has at least {SPP_MIN_NUMBER_PTS_POLYGON} points.

    :param camera
    :param start
    :param end
    :param min_number_of_points
    :param frame
    :param row
    :return: result, not_in_range_elements
    """
    not_in_range_elements = []

    if camera is SensorSource.SPP_FC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.FC_POLYLINES_NUM_VERTICES
            + str(i)
            + f" = {int(row[SPPSignals.Columns.FC_POLYLINES_NUM_VERTICES + str(i)])}"
            f" is lower than {min_number_of_points}"
            for i in range(start, end)
            if int(row[SPPSignals.Columns.FC_POLYLINES_NUM_VERTICES + str(i)]) < min_number_of_points
        ]

    elif camera is SensorSource.SPP_LSC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.LSC_POLYLINES_NUM_VERTICES
            + str(i)
            + f" = {int(row[SPPSignals.Columns.LSC_POLYLINES_NUM_VERTICES + str(i)])}"
            f" is lower than {min_number_of_points}"
            for i in range(start, end)
            if int(row[SPPSignals.Columns.LSC_POLYLINES_NUM_VERTICES + str(i)]) < min_number_of_points
        ]

    elif camera is SensorSource.SPP_RC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.RC_POLYLINES_NUM_VERTICES
            + str(i)
            + f" = {int(row[SPPSignals.Columns.RC_POLYLINES_NUM_VERTICES + str(i)])}"
            f" is lower than {min_number_of_points}"
            for i in range(start, end)
            if int(row[SPPSignals.Columns.RC_POLYLINES_NUM_VERTICES + str(i)]) < min_number_of_points
        ]

    elif camera is SensorSource.SPP_RSC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.RSC_POLYLINES_NUM_VERTICES
            + str(i)
            + f" = {int(row[SPPSignals.Columns.RSC_POLYLINES_NUM_VERTICES + str(i)])}"
            f" is lower than {min_number_of_points}"
            for i in range(start, end)
            if int(row[SPPSignals.Columns.RSC_POLYLINES_NUM_VERTICES + str(i)]) < min_number_of_points
        ]

    if len(not_in_range_elements) > 0:
        return False, {frame: not_in_range_elements}
    else:
        return True, {frame: not_in_range_elements}


def check_polylines_confidence_range(camera, start, end, frame, row):
    """
    Loops over a list of elements and check that each polyline's confidence is in range [0, 1].

    :param camera
    :param start
    :param end
    :param frame
    :param row
    :return: result, not_in_range_elements.
    """
    not_in_range_elements = []

    if camera is SensorSource.SPP_FC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.FC_POLYLINES_CONFIDENCE
            + str(i)
            + f" = {int(row[SPPSignals.Columns.FC_POLYLINES_CONFIDENCE + str(i)])} is not in range [0, 1]"
            for i in range(start, end)
            if not (0 <= int(row[SPPSignals.Columns.FC_POLYLINES_CONFIDENCE + str(i)]) <= 1)
        ]

    elif camera is SensorSource.SPP_LSC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.LSC_POLYLINES_CONFIDENCE
            + str(i)
            + f" = {int(row[SPPSignals.Columns.LSC_POLYLINES_CONFIDENCE + str(i)])} is not in range [0, 1]"
            for i in range(start, end)
            if not (0 <= int(row[SPPSignals.Columns.LSC_POLYLINES_CONFIDENCE + str(i)]) <= 1)
        ]

    elif camera is SensorSource.SPP_RC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.RC_POLYLINES_CONFIDENCE
            + str(i)
            + f" = {int(row[SPPSignals.Columns.RC_POLYLINES_CONFIDENCE + str(i)])} is not in range [0, 1]"
            for i in range(start, end)
            if not (0 <= int(row[SPPSignals.Columns.RC_POLYLINES_CONFIDENCE + str(i)]) <= 1)
        ]

    elif camera is SensorSource.SPP_RSC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.RSC_POLYLINES_CONFIDENCE
            + str(i)
            + f" = {int(row[SPPSignals.Columns.RSC_POLYLINES_CONFIDENCE + str(i)])} is not in range [0, 1]"
            for i in range(start, end)
            if not (0 <= int(row[SPPSignals.Columns.RSC_POLYLINES_CONFIDENCE + str(i)]) <= 1)
        ]

    if len(not_in_range_elements) > 0:
        return False, {frame: not_in_range_elements}
    else:
        return True, {frame: not_in_range_elements}


def check_polyline_semantic_value(camera, start, end, frame, row):
    """
    Loops over a list of elements and check that each polyline's semantic has one of the following values [3, 4, 6].

    :param camera
    :param start
    :param end
    :param frame
    :param row
    :return: result, not_in_range_elements.
    """
    not_in_range_elements = []

    if camera is SensorSource.SPP_FC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.FC_POLYLINES_SEMANTIC
            + str(i)
            + f" = {int(row[SPPSignals.Columns.FC_POLYLINES_SEMANTIC + str(i)])} is not in range [3, 4, 6]"
            for i in range(start, end)
            if not (
                int(row[SPPSignals.Columns.FC_POLYLINES_SEMANTIC + str(i)]) == SppSemantics.STATIC_OBSTACLE.value
                or int(row[SPPSignals.Columns.FC_POLYLINES_SEMANTIC + str(i)]) == SppSemantics.DYNAMIC_OBSTACLE.value
                or int(row[SPPSignals.Columns.FC_POLYLINES_SEMANTIC + str(i)]) == SppSemantics.CURB.value
            )
        ]

    elif camera is SensorSource.SPP_LSC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.LSC_POLYLINES_SEMANTIC
            + str(i)
            + f" = {int(row[SPPSignals.Columns.LSC_POLYLINES_SEMANTIC + str(i)])} is not in range [3, 4, 6]"
            for i in range(start, end)
            if not (
                int(row[SPPSignals.Columns.LSC_POLYLINES_SEMANTIC + str(i)]) == SppSemantics.STATIC_OBSTACLE.value
                or int(row[SPPSignals.Columns.LSC_POLYLINES_SEMANTIC + str(i)]) == SppSemantics.DYNAMIC_OBSTACLE.value
                or int(row[SPPSignals.Columns.LSC_POLYLINES_SEMANTIC + str(i)]) == SppSemantics.CURB.value
            )
        ]

    if camera is SensorSource.SPP_RC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.RC_POLYLINES_SEMANTIC
            + str(i)
            + f" = {int(row[SPPSignals.Columns.RC_POLYLINES_SEMANTIC + str(i)])} is not in range [3, 4, 6]"
            for i in range(start, end)
            if not (
                int(row[SPPSignals.Columns.RC_POLYLINES_SEMANTIC + str(i)]) == SppSemantics.STATIC_OBSTACLE.value
                or int(row[SPPSignals.Columns.RC_POLYLINES_SEMANTIC + str(i)]) == SppSemantics.DYNAMIC_OBSTACLE.value
                or int(row[SPPSignals.Columns.RC_POLYLINES_SEMANTIC + str(i)]) == SppSemantics.CURB.value
            )
        ]

    elif camera is SensorSource.SPP_RSC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.RSC_POLYLINES_SEMANTIC
            + str(i)
            + f" = {int(row[SPPSignals.Columns.RSC_POLYLINES_SEMANTIC + str(i)])} is not in range [3, 4, 6]"
            for i in range(start, end)
            if not (
                int(row[SPPSignals.Columns.RSC_POLYLINES_SEMANTIC + str(i)]) == SppSemantics.STATIC_OBSTACLE.value
                or int(row[SPPSignals.Columns.RSC_POLYLINES_SEMANTIC + str(i)]) == SppSemantics.DYNAMIC_OBSTACLE.value
                or int(row[SPPSignals.Columns.RSC_POLYLINES_SEMANTIC + str(i)]) == SppSemantics.CURB.value
            )
        ]

    if len(not_in_range_elements) > 0:
        return False, {frame: not_in_range_elements}
    else:
        return True, {frame: not_in_range_elements}


def check_polygon_semantic_value(camera, start, end, frame, row):
    """
    Loops over a list of elements.

    :param camera
    :param start
    :param end
    :param frame
    :param row
    :return: result, not_in_range_elements.
    """
    not_in_range_elements = []

    if camera is SensorSource.SPP_FC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.FC_POLYLINES_SEMANTIC
            + str(i)
            + f" = {int(row[SPPSignals.Columns.FC_POLYLINES_SEMANTIC + str(i)])} is less than 0"
            for i in range(start, end)
            if int(row[SPPSignals.Columns.FC_POLYLINES_SEMANTIC + str(i)]) < 0
        ]

    elif camera is SensorSource.SPP_LSC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.LSC_POLYLINES_SEMANTIC
            + str(i)
            + f" = {int(row[SPPSignals.Columns.LSC_POLYLINES_SEMANTIC + str(i)])} is less than 0"
            for i in range(start, end)
            if int(row[SPPSignals.Columns.LSC_POLYLINES_SEMANTIC + str(i)]) < 0
        ]

    elif camera is SensorSource.SPP_RC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.RC_POLYLINES_SEMANTIC
            + str(i)
            + f" = {int(row[SPPSignals.Columns.RC_POLYLINES_SEMANTIC + str(i)])} is less than 0"
            for i in range(start, end)
            if int(row[SPPSignals.Columns.RC_POLYLINES_SEMANTIC + str(i)]) < 0
        ]

    elif camera is SensorSource.SPP_RSC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.RSC_POLYLINES_SEMANTIC
            + str(i)
            + f" = {int(row[SPPSignals.Columns.RSC_POLYLINES_SEMANTIC + str(i)])} is less than 0"
            for i in range(start, end)
            if int(row[SPPSignals.Columns.RSC_POLYLINES_SEMANTIC + str(i)]) < 0
        ]

    if len(not_in_range_elements) > 0:
        return False, {frame: not_in_range_elements}
    else:
        return True, {frame: not_in_range_elements}


def check_number_of_polylines(number_of_polylines, frame):
    """
    Loops over a list of elements.

    :param number_of_polylines
    :param frame
    :return: result, failed_elements
    """
    failed_elements = []

    if number_of_polylines < 0:
        failed_elements.append(f"The number of polylines is {number_of_polylines} < 0")
        return False, {frame: failed_elements}
    else:
        return True, {frame: failed_elements}


def check_first_polylines(camera, number_of_polygons, number_of_polylines, frame, row):
    """
    Loops over a list of elements.

    :param camera
    :param number_of_polylines
    :param number_of_polygons
    :param frame
    :param row
    :return: result, failed_elements.
    """
    sum_of_polygons_num_vertices = 0
    sum_of_polylines_num_vertices = 0
    failed_elements = []

    # compute the number of vertices for the m polylines
    for m in range(number_of_polygons):
        if camera is SensorSource.SPP_FC_DATA:
            sum_of_polygons_num_vertices = sum_of_polygons_num_vertices + int(
                row[SPPSignals.Columns.FC_POLYLINES_NUM_VERTICES + str(m)]
            )
        elif camera is SensorSource.SPP_LSC_DATA:
            sum_of_polygons_num_vertices = sum_of_polygons_num_vertices + int(
                row[SPPSignals.Columns.LSC_POLYLINES_NUM_VERTICES + str(m)]
            )
        elif camera is SensorSource.SPP_RC_DATA:
            sum_of_polygons_num_vertices = sum_of_polygons_num_vertices + int(
                row[SPPSignals.Columns.RC_POLYLINES_NUM_VERTICES + str(m)]
            )
        elif camera is SensorSource.SPP_RSC_DATA:
            sum_of_polygons_num_vertices = sum_of_polygons_num_vertices + int(
                row[SPPSignals.Columns.RSC_POLYLINES_NUM_VERTICES + str(m)]
            )

    # compute the number of vertices for the n polylines
    for n in range(number_of_polygons, number_of_polygons + number_of_polylines):
        if camera is SensorSource.SPP_FC_DATA:
            sum_of_polylines_num_vertices = sum_of_polylines_num_vertices + int(
                row[SPPSignals.Columns.FC_POLYLINES_NUM_VERTICES + str(n)]
            )
        elif camera is SensorSource.SPP_LSC_DATA:
            sum_of_polylines_num_vertices = sum_of_polylines_num_vertices + int(
                row[SPPSignals.Columns.LSC_POLYLINES_NUM_VERTICES + str(n)]
            )
        elif camera is SensorSource.SPP_RC_DATA:
            sum_of_polylines_num_vertices = sum_of_polylines_num_vertices + int(
                row[SPPSignals.Columns.RC_POLYLINES_NUM_VERTICES + str(n)]
            )
        elif camera is SensorSource.SPP_RSC_DATA:
            sum_of_polylines_num_vertices = sum_of_polylines_num_vertices + int(
                row[SPPSignals.Columns.RSC_POLYLINES_NUM_VERTICES + str(n)]
            )

    # check if number of "m" polylines is grater than number of "n" polyline
    # m = number of polygons, n = number of polylines
    if sum_of_polygons_num_vertices < sum_of_polylines_num_vertices:
        failed_elements.append(
            f"Number of polygon vertices = {sum_of_polygons_num_vertices}, "
            f"Number of polylines vertices = {sum_of_polylines_num_vertices}"
        )

    if len(failed_elements) > 0:
        return False, {frame: failed_elements}
    else:
        return True, {frame: failed_elements}


def check_polygon_vertex_start_index(camera, number_of_polygons, frame, row):
    """
    Loops over a list of elements.

    :param camera
    :param number_of_polygons
    :param frame
    :param row
    :return: result, wrong_computation_vertex_start_index.
    """
    wrong_computation_vertex_start_index = []

    if camera is SensorSource.SPP_FC_DATA:
        if number_of_polygons > 1:
            wrong_computation_vertex_start_index = [
                SPPSignals.Columns.FC_POLYLINES_VERTEX_START_INDEX + str(i) + " is wrong computed"
                for i in range(1, number_of_polygons)
                if int(row[SPPSignals.Columns.FC_POLYLINES_VERTEX_START_INDEX + str(i)])
                != int(row[SPPSignals.Columns.FC_POLYLINES_VERTEX_START_INDEX + str(i - 1)])
                + int(row[SPPSignals.Columns.FC_POLYLINES_NUM_VERTICES + str(i - 1)])
            ]

        if int(row[SPPSignals.Columns.FC_POLYLINES_VERTEX_START_INDEX + str(0)]) != 0:
            wrong_computation_vertex_start_index.append(
                SPPSignals.Columns.FC_POLYLINES_VERTEX_START_INDEX + str(0) + " is wrong computed"
            )

    elif camera is SensorSource.SPP_LSC_DATA:
        if number_of_polygons > 1:
            wrong_computation_vertex_start_index = [
                SPPSignals.Columns.LSC_POLYLINES_VERTEX_START_INDEX + str(i) + " is wrong computed"
                for i in range(1, number_of_polygons)
                if int(row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_START_INDEX + str(i)])
                != int(row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_START_INDEX + str(i - 1)])
                + int(row[SPPSignals.Columns.LSC_POLYLINES_NUM_VERTICES + str(i - 1)])
            ]

        if int(row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_START_INDEX + str(0)]) != 0:
            wrong_computation_vertex_start_index.append(
                SPPSignals.Columns.LSC_POLYLINES_VERTEX_START_INDEX + str(0) + " is wrong computed"
            )

    elif camera is SensorSource.SPP_RC_DATA:
        if number_of_polygons > 1:
            wrong_computation_vertex_start_index = [
                SPPSignals.Columns.RC_POLYLINES_VERTEX_START_INDEX + str(i) + " is wrong computed"
                for i in range(1, number_of_polygons)
                if int(row[SPPSignals.Columns.RC_POLYLINES_VERTEX_START_INDEX + str(i)])
                != int(row[SPPSignals.Columns.RC_POLYLINES_VERTEX_START_INDEX + str(i - 1)])
                + int(row[SPPSignals.Columns.RC_POLYLINES_NUM_VERTICES + str(i - 1)])
            ]

        if int(row[SPPSignals.Columns.RC_POLYLINES_VERTEX_START_INDEX + str(0)]) != 0:
            wrong_computation_vertex_start_index.append(
                SPPSignals.Columns.RC_POLYLINES_VERTEX_START_INDEX + str(0) + " is wrong computed"
            )

    elif camera is SensorSource.SPP_RSC_DATA:
        if number_of_polygons > 1:
            wrong_computation_vertex_start_index = [
                SPPSignals.Columns.RSC_POLYLINES_VERTEX_START_INDEX + str(i) + " is wrong computed"
                for i in range(1, number_of_polygons)
                if int(row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_START_INDEX + str(i)])
                != int(row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_START_INDEX + str(i - 1)])
                + int(row[SPPSignals.Columns.RSC_POLYLINES_NUM_VERTICES + str(i - 1)])
            ]

        if int(row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_START_INDEX + str(0)]) != 0:
            wrong_computation_vertex_start_index.append(
                SPPSignals.Columns.RSC_POLYLINES_VERTEX_START_INDEX + str(0) + " is wrong computed"
            )

    if len(wrong_computation_vertex_start_index) > 0:
        return False, {frame: wrong_computation_vertex_start_index}
    else:
        return True, {frame: wrong_computation_vertex_start_index}


def check_x_coord_range(camera, frame, row, start_vertex_index, end_vertex_index):
    """
    Loops over a list of elements and check the X coordinate of the vertices.

    :param camera
    :param frame
    :param row
    :param start_vertex_index
    :param end_vertex_index
    :return: result, not_in_range_elements.
    """
    not_in_range_elements = []

    if camera is SensorSource.SPP_FC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.FC_POLYLINES_VERTEX_X_COORD
            + str(i)
            + f" = {row[SPPSignals.Columns.FC_POLYLINES_VERTEX_X_COORD + str(i)]} is out of range [-15, 15]"
            for i in range(start_vertex_index, end_vertex_index)
            if abs(row[SPPSignals.Columns.FC_POLYLINES_VERTEX_X_COORD + str(i)])
            > SppOperationalRange.SPP_OPERATIONAL_RANGE_LONGITUDINAL
        ]
    elif camera is SensorSource.SPP_LSC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.LSC_POLYLINES_VERTEX_X_COORD
            + str(i)
            + f" = {row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_X_COORD + str(i)]} is out of range [-15, 15]"
            for i in range(start_vertex_index, end_vertex_index)
            if abs(row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_X_COORD + str(i)])
            > SppOperationalRange.SPP_OPERATIONAL_RANGE_LONGITUDINAL
        ]
    if camera is SensorSource.SPP_RC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.RC_POLYLINES_VERTEX_X_COORD
            + str(i)
            + f" = {row[SPPSignals.Columns.RC_POLYLINES_VERTEX_X_COORD + str(i)]} is out of range [-15, 15]"
            for i in range(start_vertex_index, end_vertex_index)
            if abs(row[SPPSignals.Columns.RC_POLYLINES_VERTEX_X_COORD + str(i)])
            > SppOperationalRange.SPP_OPERATIONAL_RANGE_LONGITUDINAL
        ]
    elif camera is SensorSource.SPP_RSC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.RSC_POLYLINES_VERTEX_X_COORD
            + str(i)
            + f" = {row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_X_COORD + str(i)]} is out of range [-15, 15]"
            for i in range(start_vertex_index, end_vertex_index)
            if abs(row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_X_COORD + str(i)])
            > SppOperationalRange.SPP_OPERATIONAL_RANGE_LONGITUDINAL
        ]

    if len(not_in_range_elements) > 0:
        return False, {frame: not_in_range_elements}
    else:
        return True, {frame: not_in_range_elements}


def check_y_coord_range(camera, frame, row, start_vertex_index, end_vertex_index):
    """
    Loops over a list of elements and check the Y coordinate of the vertices.

    :param camera
    :param frame
    :param row
    :param start_vertex_index
    :param end_vertex_index
    :return: result, not_in_range_elements.
    """
    not_in_range_elements = []

    if camera is SensorSource.SPP_FC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.FC_POLYLINES_VERTEX_Y_COORD
            + str(i)
            + f" = {row[SPPSignals.Columns.FC_POLYLINES_VERTEX_Y_COORD + str(i)]} is out of range [-10, 10]"
            for i in range(start_vertex_index, end_vertex_index)
            if abs(row[SPPSignals.Columns.FC_POLYLINES_VERTEX_Y_COORD + str(i)])
            > SppOperationalRange.SPP_OPERATIONAL_RANGE_LONGITUDINAL
        ]
    elif camera is SensorSource.SPP_LSC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.LSC_POLYLINES_VERTEX_Y_COORD
            + str(i)
            + f" = {row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_Y_COORD + str(i)]} is out of range [-10, 10]"
            for i in range(start_vertex_index, end_vertex_index)
            if abs(row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_Y_COORD + str(i)])
            > SppOperationalRange.SPP_OPERATIONAL_RANGE_LONGITUDINAL
        ]
    if camera is SensorSource.SPP_RC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.RC_POLYLINES_VERTEX_Y_COORD
            + str(i)
            + f" = {row[SPPSignals.Columns.RC_POLYLINES_VERTEX_Y_COORD + str(i)]} is out of range [-10, 10]"
            for i in range(start_vertex_index, end_vertex_index)
            if abs(row[SPPSignals.Columns.RC_POLYLINES_VERTEX_Y_COORD + str(i)])
            > SppOperationalRange.SPP_OPERATIONAL_RANGE_LONGITUDINAL
        ]
    elif camera is SensorSource.SPP_RSC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.RSC_POLYLINES_VERTEX_Y_COORD
            + str(i)
            + f" = {row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_Y_COORD + str(i)]} is out of range [-10, 10]"
            for i in range(start_vertex_index, end_vertex_index)
            if abs(row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_Y_COORD + str(i)])
            > SppOperationalRange.SPP_OPERATIONAL_RANGE_LONGITUDINAL
        ]

    if len(not_in_range_elements) > 0:
        return False, {frame: not_in_range_elements}
    else:
        return True, {frame: not_in_range_elements}


def check_z_coord_range(camera, frame, row, start_vertex_index, end_vertex_index):
    """
    Loops over a list of elements and check the Z coordinate of the vertices.

    :param camera
    :param frame
    :param row
    :param start_vertex_index
    :param end_vertex_index
    :return: result, not_in_range_elements.
    """
    not_in_range_elements = []

    if camera is SensorSource.SPP_FC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.FC_POLYLINES_VERTEX_Z_COORD
            + str(i)
            + f" = {row[SPPSignals.Columns.FC_POLYLINES_VERTEX_Z_COORD + str(i)]} is out of range [-1e-6, +1e-6]"
            for i in range(start_vertex_index, end_vertex_index)
            if abs(0 - row[SPPSignals.Columns.FC_POLYLINES_VERTEX_Z_COORD + str(i)]) > 1e-6
        ]
    elif camera is SensorSource.SPP_LSC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.LSC_POLYLINES_VERTEX_Z_COORD
            + str(i)
            + f" = {row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_Z_COORD + str(i)]} is out of range [-1e-6, +1e-6]"
            for i in range(start_vertex_index, end_vertex_index)
            if abs(0 - row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_Z_COORD + str(i)]) > 1e-6
        ]
    if camera is SensorSource.SPP_RC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.RC_POLYLINES_VERTEX_Z_COORD
            + str(i)
            + f" = {row[SPPSignals.Columns.RC_POLYLINES_VERTEX_Z_COORD + str(i)]} is out of range [-1e-6, +1e-6]"
            for i in range(start_vertex_index, end_vertex_index)
            if abs(0 - row[SPPSignals.Columns.RC_POLYLINES_VERTEX_Z_COORD + str(i)]) > 1e-6
        ]
    elif camera is SensorSource.SPP_RSC_DATA:
        not_in_range_elements = [
            SPPSignals.Columns.RSC_POLYLINES_VERTEX_Z_COORD
            + str(i)
            + f" = {row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_Z_COORD + str(i)]} is out of range [-1e-6, +1e-6]"
            for i in range(start_vertex_index, end_vertex_index)
            if abs(0 - row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_Z_COORD + str(i)]) > 1e-6
        ]

    if len(not_in_range_elements) > 0:
        return False, {frame: not_in_range_elements}
    else:
        return True, {frame: not_in_range_elements}


def get_max_polygon_coords(camera):
    """Check the sensor source and return the points which describe the maximum polygon."""
    if camera is SensorSource.SPP_FC_DATA:
        return SppPolygon.FC_MAX_POLYGON
    elif camera is SensorSource.SPP_LSC_DATA:
        return SppPolygon.LSC_MAX_POLYGON
    elif camera is SensorSource.SPP_RC_DATA:
        return SppPolygon.RC_MAX_POLYGON
    elif camera is SensorSource.SPP_RSC_DATA:
        return SppPolygon.RSC_MAX_POLYGON


def get_polylines_timestamp(camera, row):
    """Check the sensor source and return the timestamp."""
    if camera is SensorSource.SPP_FC_DATA:
        return int(row[SPPSignals.Columns.FC_POLYLINES_TIMESTAMP])
    elif camera is SensorSource.SPP_LSC_DATA:
        return int(row[SPPSignals.Columns.LSC_POLYLINES_TIMESTAMP])
    elif camera is SensorSource.SPP_RC_DATA:
        return int(row[SPPSignals.Columns.RC_POLYLINES_TIMESTAMP])
    elif camera is SensorSource.SPP_RSC_DATA:
        return int(row[SPPSignals.Columns.RSC_POLYLINES_TIMESTAMP])


def get_polylines_sig_status(camera, row):
    """Check the sensor source and return the value of SigStatus for Polyline structure."""
    if camera is SensorSource.SPP_FC_DATA:
        return int(row[SPPSignals.Columns.FC_POLYLINES_SIG_STATUS])
    elif camera is SensorSource.SPP_LSC_DATA:
        return int(row[SPPSignals.Columns.LSC_POLYLINES_SIG_STATUS])
    elif camera is SensorSource.SPP_RC_DATA:
        return int(row[SPPSignals.Columns.RC_POLYLINES_SIG_STATUS])
    elif camera is SensorSource.SPP_RSC_DATA:
        return int(row[SPPSignals.Columns.RSC_POLYLINES_SIG_STATUS])


def get_number_of_polygons(camera, row):
    """Check the sensor source and return the number of polygons."""
    if camera is SensorSource.SPP_FC_DATA:
        return int(row[SPPSignals.Columns.FC_POLYLINES_NUMBER_OF_POLYGONS])
    elif camera is SensorSource.SPP_LSC_DATA:
        return int(row[SPPSignals.Columns.LSC_POLYLINES_NUMBER_OF_POLYGONS])
    elif camera is SensorSource.SPP_RC_DATA:
        return int(row[SPPSignals.Columns.RC_POLYLINES_NUMBER_OF_POLYGONS])
    elif camera is SensorSource.SPP_RSC_DATA:
        return int(row[SPPSignals.Columns.RSC_POLYLINES_NUMBER_OF_POLYGONS])


def get_number_of_polylines(camera, row):
    """Check the sensor source and return the number of polylines."""
    if camera is SensorSource.SPP_FC_DATA:
        return int(row[SPPSignals.Columns.FC_POLYLINES_NUMBER_OF_POLYLINES])
    elif camera is SensorSource.SPP_LSC_DATA:
        return int(row[SPPSignals.Columns.LSC_POLYLINES_NUMBER_OF_POLYLINES])
    elif camera is SensorSource.SPP_RC_DATA:
        return int(row[SPPSignals.Columns.RC_POLYLINES_NUMBER_OF_POLYLINES])
    elif camera is SensorSource.SPP_RSC_DATA:
        return int(row[SPPSignals.Columns.RSC_POLYLINES_NUMBER_OF_POLYLINES])


def get_polyline_vertex_start_index(camera, index, row):
    """Check the sensor source and return the start index of vertex of a polyline."""
    if camera is SensorSource.SPP_FC_DATA:
        return int(row[SPPSignals.Columns.FC_POLYLINES_VERTEX_START_INDEX + str(index)])
    elif camera is SensorSource.SPP_LSC_DATA:
        return int(row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_START_INDEX + str(index)])
    elif camera is SensorSource.SPP_RC_DATA:
        return int(row[SPPSignals.Columns.RC_POLYLINES_VERTEX_START_INDEX + str(index)])
    elif camera is SensorSource.SPP_RSC_DATA:
        return int(row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_START_INDEX + str(index)])


def get_polyline_num_vertices(camera, index, row):
    """Check the sensor source and return the number of vertices of a polyline."""
    if camera is SensorSource.SPP_FC_DATA:
        return int(row[SPPSignals.Columns.FC_POLYLINES_NUM_VERTICES + str(index)])
    elif camera is SensorSource.SPP_LSC_DATA:
        return int(row[SPPSignals.Columns.LSC_POLYLINES_NUM_VERTICES + str(index)])
    elif camera is SensorSource.SPP_RC_DATA:
        return int(row[SPPSignals.Columns.RC_POLYLINES_NUM_VERTICES + str(index)])
    elif camera is SensorSource.SPP_RSC_DATA:
        return int(row[SPPSignals.Columns.RSC_POLYLINES_NUM_VERTICES + str(index)])


def get_polyline_semantic(camera, index, row):
    """Check the sensor source and return the semantics of a polyline."""
    if camera is SensorSource.SPP_FC_DATA:
        return int(row[SPPSignals.Columns.FC_POLYLINES_SEMANTIC + str(index)])
    elif camera is SensorSource.SPP_LSC_DATA:
        return int(row[SPPSignals.Columns.LSC_POLYLINES_SEMANTIC + str(index)])
    elif camera is SensorSource.SPP_RC_DATA:
        return int(row[SPPSignals.Columns.RC_POLYLINES_SEMANTIC + str(index)])
    elif camera is SensorSource.SPP_RSC_DATA:
        return int(row[SPPSignals.Columns.RSC_POLYLINES_SEMANTIC + str(index)])


def get_vertex_x(camera, index, row):
    """Check the sensor source and return the X coordinate of a vertex."""
    if camera is SensorSource.SPP_FC_DATA:
        return row[SPPSignals.Columns.FC_POLYLINES_VERTEX_X_COORD + str(index)]
    elif camera is SensorSource.SPP_LSC_DATA:
        return row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_X_COORD + str(index)]
    elif camera is SensorSource.SPP_RC_DATA:
        return row[SPPSignals.Columns.RC_POLYLINES_VERTEX_X_COORD + str(index)]
    elif camera is SensorSource.SPP_RSC_DATA:
        return row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_X_COORD + str(index)]


def get_vertex_y(camera, index, row):
    """Check the sensor source and return the Y coordinate of a vertex."""
    if camera is SensorSource.SPP_FC_DATA:
        return row[SPPSignals.Columns.FC_POLYLINES_VERTEX_Y_COORD + str(index)]
    elif camera is SensorSource.SPP_LSC_DATA:
        return row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_Y_COORD + str(index)]
    elif camera is SensorSource.SPP_RC_DATA:
        return row[SPPSignals.Columns.RC_POLYLINES_VERTEX_Y_COORD + str(index)]
    elif camera is SensorSource.SPP_RSC_DATA:
        return row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_Y_COORD + str(index)]


def get_vertex_z(camera, index, row):
    """Check the sensor source and return the Z coordinate of a vertex."""
    if camera is SensorSource.SPP_FC_DATA:
        return row[SPPSignals.Columns.FC_POLYLINES_VERTEX_Z_COORD + str(index)]
    elif camera is SensorSource.SPP_LSC_DATA:
        return row[SPPSignals.Columns.LSC_POLYLINES_VERTEX_Z_COORD + str(index)]
    elif camera is SensorSource.SPP_RC_DATA:
        return row[SPPSignals.Columns.RC_POLYLINES_VERTEX_Z_COORD + str(index)]
    elif camera is SensorSource.SPP_RSC_DATA:
        return row[SPPSignals.Columns.RSC_POLYLINES_VERTEX_Z_COORD + str(index)]


def get_sempoints_sig_status(camera, row):
    """Check the sensor source and return the value of SigStatus for SemPoints structure."""
    if camera is SensorSource.SPP_FC_DATA:
        return int(row[SPPSignals.Columns.FC_SEMPOINTS_SIG_STATUS])
    elif camera is SensorSource.SPP_LSC_DATA:
        return int(row[SPPSignals.Columns.LSC_SEMPOINTS_SIG_STATUS])
    elif camera is SensorSource.SPP_RC_DATA:
        return int(row[SPPSignals.Columns.RC_SEMPOINTS_SIG_STATUS])
    elif camera is SensorSource.SPP_RSC_DATA:
        return int(row[SPPSignals.Columns.RSC_SEMPOINTS_SIG_STATUS])


def get_sempoints_indicator_flag(camera, row):
    """Check the sensor source and return the value of SEMPOINTS_INDICATOR_FLAG."""
    if camera is SensorSource.SPP_FC_DATA:
        return int(row[SPPSignals.Columns.FC_SEMPOINTS_INDICATOR_FLAG])
    elif camera is SensorSource.SPP_LSC_DATA:
        return int(row[SPPSignals.Columns.LSC_SEMPOINTS_INDICATOR_FLAG])
    elif camera is SensorSource.SPP_RC_DATA:
        return int(row[SPPSignals.Columns.RC_SEMPOINTS_INDICATOR_FLAG])
    elif camera is SensorSource.SPP_RSC_DATA:
        return int(row[SPPSignals.Columns.RSC_SEMPOINTS_INDICATOR_FLAG])


def get_spp_op_mode(camera, row):
    """Check the sensor source and return the value of SPP_OP_MODE."""
    if camera is SensorSource.SPP_FC_DATA:
        return int(row[SPPSignals.Columns.FC_BASE_CTRL_DATA_OP_MODE])
    elif camera is SensorSource.SPP_LSC_DATA:
        return int(row[SPPSignals.Columns.LSC_BASE_CTRL_DATA_OP_MODE])
    elif camera is SensorSource.SPP_RC_DATA:
        return int(row[SPPSignals.Columns.RC_BASE_CTRL_DATA_OP_MODE])
    elif camera is SensorSource.SPP_RSC_DATA:
        return int(row[SPPSignals.Columns.RSC_BASE_CTRL_DATA_OP_MODE])


def get_bsig_timestamp(camera, reader_df):
    """Get all timestamps for a recording from bsig file."""
    timestamps = []
    for _, row in reader_df.iterrows():
        if camera is SensorSource.SPP_FC_DATA:
            timestamp = int(row[SPPSignals.Columns.FC_POLYLINES_TIMESTAMP])
        elif camera is SensorSource.SPP_LSC_DATA:
            timestamp = int(row[SPPSignals.Columns.LSC_POLYLINES_TIMESTAMP])
        elif camera is SensorSource.SPP_RC_DATA:
            timestamp = int(row[SPPSignals.Columns.RC_POLYLINES_TIMESTAMP])
        elif camera is SensorSource.SPP_RSC_DATA:
            timestamp = int(row[SPPSignals.Columns.RSC_POLYLINES_TIMESTAMP])

        timestamps.append(timestamp)

    return timestamps


def get_label_timestamp(stream_data):
    """Get all timestamps for a recording from label.

    Parameters:
    stream_data (DataFrame):
    """
    timestamps = stream_data["gt_timestamp"].tolist()

    return timestamps


def get_timestamp_df(gt_timestamps, sim_timestamps) -> pd.DataFrame:
    """
    Fuses the bsig and databases timestamps (labeled frames).

    :param gt_timestamps:
    :param sim_timestamps :
    :return:
    """
    db_timestamps = np.array(gt_timestamps, dtype=np.int64)
    if db_timestamps.size == 0:
        _log.warning("No database label timestamps found!")
        return Empty_Dataframe

    bsig_timestamps = np.array(sim_timestamps, dtype=np.int64)
    if bsig_timestamps.size == 0:
        _log.warning("No bsig timestamps found !")
        return Empty_Dataframe

    # create dataframe from label timestamps
    db_timestamp_df = pd.DataFrame(
        {"timestamp": db_timestamps, "label_present": [True] * len(db_timestamps)}
    ).set_index("timestamp")

    # create dataframe from bsig timestamps
    bsig_timestamp_df = pd.DataFrame(
        {"timestamp": bsig_timestamps, "bsig_index": [i for i in range(len(bsig_timestamps))]}
    ).set_index("timestamp")

    # join bsig and label timestamps
    timestamp_df = bsig_timestamp_df.join(db_timestamp_df, how="outer")

    # fill in False values for all frames in which we only have bsig data
    timestamp_df["label_present"].fillna(False, inplace=True)
    # fill in -1 values for all frames in which we only have database data
    timestamp_df["bsig_index"].fillna(-1, inplace=True)
    # pandas converts the column 'bsig_index' to float to cope for NaN values, thus cast now back to int32
    timestamp_df["bsig_index"] = timestamp_df["bsig_index"].astype("int32")

    # find duplicate timestamps
    where_duplicate_timestamps_mask = timestamp_df.index.duplicated(keep="first")
    duplicates_found = any(where_duplicate_timestamps_mask)
    if duplicates_found:
        _log.error(f"Removing the duplicate timestamps in {timestamp_df.index[where_duplicate_timestamps_mask].values}")
        timestamp_df.index.drop_duplicates(keep="first")

    timestamp_df.sort_index()  # timestamps should be in ascending order

    return timestamp_df


def get_test_case_inputs(test_script_filename, camera):
    """Get the necessary input for test case evaluation."""
    recording_name = None
    start_timestamp = None
    end_timestamp = None
    test_case = TEST_CASE_MAP.get(test_script_filename, None)
    if test_case is not None:
        camera_side = test_case.get(camera, None)
        if camera_side is not None:
            recording_name = camera_side.get("Recording Name", None)
            start_timestamp = camera_side.get("Start Timestamp", None)
            end_timestamp = camera_side.get("End Timestamp", None)

            # return recording_name, start_timestamp, end_timestamp

    return recording_name, start_timestamp, end_timestamp


def get_json_gt_data(gt_data, camera):
    """From the json file, get the ground truth data for a specific camera as a dataframe"""
    if camera is SensorSource.SPP_FC_DATA:
        gt_df = flatten_data_to_dataframe(gt_data["SppFront"])
        return gt_df
    if camera is SensorSource.SPP_LSC_DATA:
        gt_df = flatten_data_to_dataframe(gt_data["SppLeft"])
        return gt_df
    if camera is SensorSource.SPP_RC_DATA:
        gt_df = flatten_data_to_dataframe(gt_data["SppRear"])
        return gt_df
    if camera is SensorSource.SPP_RSC_DATA:
        gt_df = flatten_data_to_dataframe(gt_data["SppRight"])
        return gt_df


def flatten_data_to_dataframe(gt_data):
    """
    Flatten a list of dictionaries with nested structures into a pandas DataFrame.

    Parameters:
    gt_data (list): List of dictionaries to be flattened and converted into a DataFrame.

    Returns:
    pd.DataFrame: A flattened DataFrame containing the processed data.
    """
    flat_data = []

    for data in gt_data:
        flat_item = {
            "gt_status": data["sSigHeader"]["eSigStatus"],
            "gt_timestamp": int(data["sSigHeader"]["uiTimeStamp"]),
            "gt_no_of_polygons": data["numberOfPolygons"],
            "gt_no_of_polylines": data["numberOfPolylines"],
        }

        # Flattening 'polylines'
        for i, polylines in enumerate(data["polylines"]):
            flat_item[f"gt_vertex_start_index_{i}"] = polylines["vertexStartIndex"]
            flat_item[f"gt_num_vertices_{i}"] = polylines["numVertices"]
            flat_item[f"gt_semantic_{i}"] = polylines["semantic"]
            # flat_item[f'gt_confidence_{i}'] = polylines['confidence']

        # Flattening 'vertices'
        for i, vert in enumerate(data["vertices"]):
            flat_item[f"gt_vertex_x_{i}"] = vert["xM"]
            flat_item[f"gt_vertex_y_{i}"] = vert["yM"]
            flat_item[f"gt_vertex_z_{i}"] = vert["zM"]

        flat_data.append(flat_item)

    # Creating DataFrame
    df = pd.DataFrame(flat_data)

    return df


def createCamera(sensorSource: SensorSource, data: pd.DataFrame):
    """
    Create cylindrical camera used in SPP.
    ----------
    Parameters
    ----------
    sensorSource : SensorSource
        Camera identifier : FRONT, LEFT, REAR, RIGHT
    data : pd.DataFrame
            pandas Dataframe with all signals required by SPP component
    Returns
    -------
        camera: A cylindrical reference camera
    """
    cameraExtrinsicsSigStatus, imageIntrinsicsSigStatus = None, None
    camera_pos_x, camera_pos_y, camera_pos_z = None, None, None
    focal_x, focal_y = None, None
    center_x, center_y = None, None
    cameraId = None
    if sensorSource is SensorSource.SPP_FC_DATA:
        cameraId = 1
        cameraExtrinsicsSigStatus = SPPSignals.Columns.FC_EOL_CAMERA_EXTRINSICS_SIG_STATUS
        imageIntrinsicsSigStatus = SPPSignals.Columns.FC_IMAGE_INTRINSICS_SIG_STATUS
        camera_pos_x = SPPSignals.Columns.FC_EOL_CAMERA_EXTRINSICS_POS_X
        camera_pos_y = SPPSignals.Columns.FC_EOL_CAMERA_EXTRINSICS_POS_Y
        camera_pos_z = SPPSignals.Columns.FC_EOL_CAMERA_EXTRINSICS_POS_Z
        focal_x = SPPSignals.Columns.FC_IMAGE_INTRINSICS_FOCAL_X
        focal_y = SPPSignals.Columns.FC_IMAGE_INTRINSICS_FOCAL_Y
        center_x = SPPSignals.Columns.FC_IMAGE_INTRINSICS_CENTER_X
        center_y = SPPSignals.Columns.FC_IMAGE_INTRINSICS_CENTER_Y
    elif sensorSource is SensorSource.SPP_LSC_DATA:
        cameraId = 2
        cameraExtrinsicsSigStatus = SPPSignals.Columns.LSC_EOL_CAMERA_EXTRINSICS_SIG_STATUS
        imageIntrinsicsSigStatus = SPPSignals.Columns.LSC_IMAGE_INTRINSICS_SIG_STATUS
        camera_pos_x = SPPSignals.Columns.LSC_EOL_CAMERA_EXTRINSICS_POS_X
        camera_pos_y = SPPSignals.Columns.LSC_EOL_CAMERA_EXTRINSICS_POS_Y
        camera_pos_z = SPPSignals.Columns.LSC_EOL_CAMERA_EXTRINSICS_POS_Z
        focal_x = SPPSignals.Columns.LSC_IMAGE_INTRINSICS_FOCAL_X
        focal_y = SPPSignals.Columns.LSC_IMAGE_INTRINSICS_FOCAL_Y
        center_x = SPPSignals.Columns.LSC_IMAGE_INTRINSICS_CENTER_X
        center_y = SPPSignals.Columns.LSC_IMAGE_INTRINSICS_CENTER_Y
    elif sensorSource is SensorSource.SPP_RC_DATA:
        cameraId = 4
        cameraExtrinsicsSigStatus = SPPSignals.Columns.RC_EOL_CAMERA_EXTRINSICS_SIG_STATUS
        imageIntrinsicsSigStatus = SPPSignals.Columns.RC_IMAGE_INTRINSICS_SIG_STATUS
        camera_pos_x = SPPSignals.Columns.RC_EOL_CAMERA_EXTRINSICS_POS_X
        camera_pos_y = SPPSignals.Columns.RC_EOL_CAMERA_EXTRINSICS_POS_Y
        camera_pos_z = SPPSignals.Columns.RC_EOL_CAMERA_EXTRINSICS_POS_Z
        focal_x = SPPSignals.Columns.RC_IMAGE_INTRINSICS_FOCAL_X
        focal_y = SPPSignals.Columns.RC_IMAGE_INTRINSICS_FOCAL_Y
        center_x = SPPSignals.Columns.RC_IMAGE_INTRINSICS_CENTER_X
        center_y = SPPSignals.Columns.RC_IMAGE_INTRINSICS_CENTER_Y
    elif sensorSource is SensorSource.SPP_RSC_DATA:
        cameraId = 3
        cameraExtrinsicsSigStatus = SPPSignals.Columns.RSC_EOL_CAMERA_EXTRINSICS_SIG_STATUS
        imageIntrinsicsSigStatus = SPPSignals.Columns.RSC_IMAGE_INTRINSICS_SIG_STATUS
        camera_pos_x = SPPSignals.Columns.RSC_EOL_CAMERA_EXTRINSICS_POS_X
        camera_pos_y = SPPSignals.Columns.RSC_EOL_CAMERA_EXTRINSICS_POS_Y
        camera_pos_z = SPPSignals.Columns.RSC_EOL_CAMERA_EXTRINSICS_POS_Z
        focal_x = SPPSignals.Columns.RSC_IMAGE_INTRINSICS_FOCAL_X
        focal_y = SPPSignals.Columns.RSC_IMAGE_INTRINSICS_FOCAL_Y
        center_x = SPPSignals.Columns.RSC_IMAGE_INTRINSICS_CENTER_X
        center_y = SPPSignals.Columns.RSC_IMAGE_INTRINSICS_CENTER_Y
    else:
        return None

    requiredSignalsFound = True
    existingColumns = data.colums
    if (cameraExtrinsicsSigStatus not in existingColumns) or (imageIntrinsicsSigStatus not in existingColumns):
        _log.error("Signal sig status for image intrinsics / camera extrinsics")
        requiredSignalsFound = False
    elif (
        (camera_pos_x not in existingColumns)
        or (camera_pos_y not in existingColumns)
        or (camera_pos_z not in existingColumns)
    ):
        _log.error("missing camera extrinsics from parameter handler")
        requiredSignalsFound = False
    elif (
        (focal_x not in existingColumns)
        or (focal_y not in existingColumns)
        or (center_x not in existingColumns)
        or (center_y not in existingColumns)
    ):
        _log.error("missing image intrinsics signals from grapa")
        requiredSignalsFound = False

    if requiredSignalsFound:
        validMecalDataIdxs = data[data[cameraExtrinsicsSigStatus] == 1]
        if len(validMecalDataIdxs) > 0:
            validMecalDataRow = data[validMecalDataIdxs[0]]
            x = validMecalDataRow[camera_pos_x]
            y = validMecalDataRow[camera_pos_y]
            z = validMecalDataRow[camera_pos_z]
            validGrappaIdxs = data[data[imageIntrinsicsSigStatus] == 1]
            if len(validGrappaIdxs) > 0:
                validGrappaDataRow = data[validGrappaIdxs[0]]
                fx = validGrappaDataRow[focal_x]
                fy = validGrappaDataRow[focal_y]
                cx = validGrappaDataRow[center_x]
                cy = validGrappaDataRow[center_y]
                camera = createCylindricalCamera(cameraId, x, y, z, fx, fy, cx, cy)
                return camera
            else:
                _log.error("Cylindrical camera cannot be created. No valid intrinsics values found")
                return None
        else:
            _log.error("Cylindrical camera cannot be created. No valid extrinsics values found")
            return None

    else:
        _log.error("Cylindrical camera cannot be created.Required signals not found")
        return None
