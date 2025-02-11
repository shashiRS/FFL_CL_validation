"""Helper file for SGF Test Scripts."""

import pandas as pd
from tsf.core.testcase import PreProcessor
from tsf.io.signals import SignalDefinition


class SGFSignals(SignalDefinition):
    """SGF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        SGF_TIMESTAMP = "SGF_timestamp"
        SGF_SIGSTATUS = "SGF_sig_status"
        SGF_NUMBER_OF_POLYGONS = "numPolygons"
        SGF_OBJECT_ID = "polygonId"
        SGF_OBJECT_ASSOCIATED_OBJECT_ID = "associatedObjectId"
        SGF_OBJECT_VERTEX_START_INDEX = "vertexStartIndex_polygon"
        SGF_OBJECT_USED_VERTICES = "numVertices_polygon"
        SGF_OBJECT_EXISTENCE_PROBABILITY = "existenceProbability"
        SGF_OBJECT_WHEEL_TRAVERSABLE_CONFIDENCE = "wheelTraversableConfidence_polygon"
        SGF_OBJECT_BODY_TRAVERSABLE_CONFIDENCE = "bodyTraversableConfidence_polygon"
        SGF_OBJECT_HIGH_CONFIDENCE = "highConfidence_polygon"
        SGF_OBJECT_HANGING_CONFIDENCE = "hangingConfidence_polygon"
        SGF_OBJECT_SEMANTIC_CLASS = "semanticClass_polygon"
        SGF_OBJECT_IS_GROUPED = "isGrouped_polygon"
        SGF_OBJECT_IS_ASSOCIATED = "isAssociated_polygon"
        SGF_NUMBER_OF_VERTICES = "numberOfVertices"
        SGF_VERTEX_X = "vertex_x"
        SGF_VERTEX_Y = "vertex_y"
        TPF_DYNAMIC_PROPERTY = "dynamicProperty"
        EM_EGOMOTIONPORT_SIGSTATUS = "EgoMotionPort_eSigStatus"
        EM_EGOMOTIONPORT_CYCLE_COUNTER = "EgoMotionPort_uiCycleCounter"
        EM_EGOMOTIONPORT_TIMESTAMP = "EgoMotionPort_uiTimeStamp"
        USS_POINT_LIST_SIGSTATUS = "UssPointList_eSigStatus"
        SPP_POINT_LIST_FRONT_SIGSTATUS = "SppPointListFront_eSigStatus"
        SPP_POINT_LIST_REAR_SIGSTATUS = "SppPointListRear_eSigStatus"
        SPP_POINT_LIST_LEFT_SIGSTATUS = "SppPointListLeft_eSigStatus"
        SPP_POINT_LIST_RIGHT_SIGSTATUS = "SppPointListRight_eSigStatus"
        SPP_POLYLINE_LIST_FRONT_SIGSTATUS = "SppPolylineListFront_eSigStatus"
        SPP_POLYLINE_LIST_REAR_SIGSTATUS = "SppPolylineListRear_eSigStatus"
        SPP_POLYLINE_LIST_LEFT_SIGSTATUS = "SppPolylineListLeft_eSigStatus"
        SPP_POLYLINE_LIST_RIGHT_SIGSTATUS = "SppPolylineListRight_eSigStatus"
        VEDODO_SIGSTATUS = "VedodoOdometry_eSigStatus"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        # self._root = ["AP", "ADC5xx_Device", "M7board.EM_Thread", "CarPC.EM_Thread", "MTA_ADC5", ""]

        self._properties = self.get_properties()

    def get_properties(self):
        """Generate a string of signals to be read."""
        signal_dict = {}

        signal_dict[self.Columns.SGF_TIMESTAMP] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.sSigHeader.uiTimeStamp",
        ]
        signal_dict[self.Columns.SGF_SIGSTATUS] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.sSigHeader.eSigStatus",
        ]
        signal_dict[self.Columns.SGF_NUMBER_OF_POLYGONS] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.numberOfObjects",
        ]
        signal_dict[self.Columns.SGF_OBJECT_ID] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.objects[%].obstacleId",
        ]
        signal_dict[self.Columns.SGF_OBJECT_ASSOCIATED_OBJECT_ID] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.objects[%].associatedDynamicObjectId",
        ]
        signal_dict[self.Columns.SGF_OBJECT_VERTEX_START_INDEX] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.objects[%].vertexStartIndex",
        ]
        signal_dict[self.Columns.SGF_OBJECT_USED_VERTICES] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.objects[%].usedVertices",
        ]
        signal_dict[self.Columns.SGF_OBJECT_EXISTENCE_PROBABILITY] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.objects[%].existenceProbability",
        ]
        signal_dict[self.Columns.SGF_OBJECT_WHEEL_TRAVERSABLE_CONFIDENCE] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.objects[%].heightConfidences.wheelTraversable",
        ]
        signal_dict[self.Columns.SGF_OBJECT_BODY_TRAVERSABLE_CONFIDENCE] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.objects[%].heightConfidences.bodyTraversable",
        ]
        signal_dict[self.Columns.SGF_OBJECT_HIGH_CONFIDENCE] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.objects[%].heightConfidences.high",
        ]
        signal_dict[self.Columns.SGF_OBJECT_HANGING_CONFIDENCE] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.objects[%].heightConfidences.hanging",
        ]
        signal_dict[self.Columns.SGF_OBJECT_SEMANTIC_CLASS] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.objects[%].semanticType",
        ]
        signal_dict[self.Columns.SGF_OBJECT_IS_GROUPED] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.objects[%].isGrouped",
        ]
        signal_dict[self.Columns.SGF_OBJECT_IS_ASSOCIATED] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.objects[%].isAssociated",
        ]
        signal_dict[self.Columns.SGF_NUMBER_OF_VERTICES] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectVerticesOutput.numberOfVertices",
        ]
        signal_dict[self.Columns.SGF_VERTEX_X] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectVerticesOutput.vertices[%].x",
        ]
        signal_dict[self.Columns.SGF_VERTEX_Y] = [
            "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectVerticesOutput.vertices[%].y",
        ]
        signal_dict[self.Columns.TPF_DYNAMIC_PROPERTY] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].dynamicProperty",
        ]
        signal_dict[self.Columns.EM_EGOMOTIONPORT_SIGSTATUS] = [
            "MTA_ADC5.CEM200_LSMO_DATA.m_EgoMotionOutput.sSigHeader.eSigStatus",
        ]
        signal_dict[self.Columns.EM_EGOMOTIONPORT_CYCLE_COUNTER] = [
            "MTA_ADC5.CEM200_LSMO_DATA.m_EgoMotionOutput.sSigHeader.uiMeasurementCounter",
        ]
        signal_dict[self.Columns.EM_EGOMOTIONPORT_TIMESTAMP] = [
            "MTA_ADC5.CEM200_LSMO_DATA.m_EgoMotionOutput.sSigHeader.uiTimeStamp",
        ]
        signal_dict[self.Columns.USS_POINT_LIST_SIGSTATUS] = [
            "MTA_ADC5.CEM200_SGF_DATA.syncRef.m_sig_m_UssPointList.eSigStatus",
        ]
        signal_dict[self.Columns.SPP_POINT_LIST_FRONT_SIGSTATUS] = [
            "MTA_ADC5.CEM200_SGF_DATA.syncRef.m_sig_m_pSppPointListFront.eSigStatus",
        ]
        signal_dict[self.Columns.SPP_POINT_LIST_REAR_SIGSTATUS] = [
            "MTA_ADC5.CEM200_SGF_DATA.syncRef.m_sig_m_pSppPointListRear.eSigStatus",
        ]
        signal_dict[self.Columns.SPP_POINT_LIST_LEFT_SIGSTATUS] = [
            "MTA_ADC5.CEM200_SGF_DATA.syncRef.m_sig_m_pSppPointListLeft.eSigStatus",
        ]
        signal_dict[self.Columns.SPP_POINT_LIST_RIGHT_SIGSTATUS] = [
            "MTA_ADC5.CEM200_SGF_DATA.syncRef.m_sig_m_pSppPointListRight.eSigStatus",
        ]
        signal_dict[self.Columns.SPP_POLYLINE_LIST_FRONT_SIGSTATUS] = [
            "MTA_ADC5.CEM200_SGF_DATA.syncRef.m_sig_m_pSppPolylineListFront.eSigStatus",
        ]
        signal_dict[self.Columns.SPP_POLYLINE_LIST_REAR_SIGSTATUS] = [
            "MTA_ADC5.CEM200_SGF_DATA.syncRef.m_sig_m_pSppPolylineListRear.eSigStatus",
        ]
        signal_dict[self.Columns.SPP_POLYLINE_LIST_LEFT_SIGSTATUS] = [
            "MTA_ADC5.CEM200_SGF_DATA.syncRef.m_sig_m_pSppPolylineListLeft.eSigStatus",
        ]
        signal_dict[self.Columns.SPP_POLYLINE_LIST_RIGHT_SIGSTATUS] = [
            "MTA_ADC5.CEM200_SGF_DATA.syncRef.m_sig_m_pSppPolylineListRight.eSigStatus",
        ]
        signal_dict[self.Columns.VEDODO_SIGSTATUS] = [
            "MTA_ADC5.CEM200_SGF_DATA.syncRef.m_sig_m_Odometry.eSigStatus",
        ]
        return signal_dict


class SGFPreprocessorLoad(PreProcessor):
    """Preprocessor class to load GT and SIM data."""

    def pre_process(self):
        """Load GT and SIM data."""
        gt_data = self.side_load[list(self.side_load.keys())[0]]
        sim_data = self.readers[list(self.readers.keys())[0]]

        gt_stream_data = self.transform_data_to_dataframe(gt_data["Sgf"])

        # TODO: remove this code when/if GT data era ok
        # Remove duplicate rows based on 'gt_timestamp' column, keeping the first occurrence
        gt_data_unique = gt_stream_data.drop_duplicates(subset="gt_sgf_timestamp", keep="first")
        sim_data_unique = sim_data.drop_duplicates(subset=SGFSignals.Columns.SGF_TIMESTAMP, keep="first")

        return gt_data_unique, sim_data_unique

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
                "gt_sgf_timestamp": int(data["sSigHeader"]["uiTimeStamp"]),
                "gt_no_of_objects": data["staticObjectsOutput"]["numberOfObjects"],
                "gt_no_of_vertices": data["staticObjectVerticesOutput"]["numberOfVertices"],
            }

            for i, objects in enumerate(data["staticObjectsOutput"]["objects"]):
                flat_item[f"gt_obstacle_id_{i}"] = objects["obstacleId"]
                flat_item[f"gt_associated_dynamic_object_id_{i}"] = objects["associatedDynamicObjectId"]
                flat_item[f"gt_vertex_start_index_{i}"] = objects["vertexStartIndex"]
                flat_item[f"gt_used_vertices_{i}"] = objects["usedVertices"]
                flat_item[f"gt_existence_probability_{i}"] = objects["existenceProbability"]
                flat_item[f"gt_confidence_wheel_traversable_{i}"] = objects["heightConfidences"]["wheelTraversable"]
                flat_item[f"gt_confidence_body_traversable_{i}"] = objects["heightConfidences"]["bodyTraversable"]
                flat_item[f"gt_confidence_high_{i}"] = objects["heightConfidences"]["high"]
                flat_item[f"gt_confidence_hanging_{i}"] = objects["heightConfidences"]["hanging"]
                flat_item[f"gt_semantic_type_{i}"] = objects["semanticType"]
                flat_item[f"gt_is_grouped_{i}"] = objects["isGrouped"]
                flat_item[f"gt_is_associated_{i}"] = objects["isAssociated"]

            for i, vert in enumerate(data["staticObjectVerticesOutput"]["vertices"]):
                flat_item[f"gt_vertex_x_{i}"] = vert["x"]
                flat_item[f"gt_vertex_y_{i}"] = vert["y"]

            flat_data.append(flat_item)

        # Creating DataFrame
        df = pd.DataFrame(flat_data)

        return df


class SGFPreprocessorLoadForSGF(PreProcessor):
    """Preprocessor class to load GT and SIM data."""

    def pre_process(self):
        """Load GT and SIM data."""
        gt_data = self.side_load[list(self.side_load.keys())[0]]
        sim_data = self.readers[list(self.readers.keys())[0]]

        gt_stream_data = self.transform_data_to_dataframe(gt_data["Sgf"])

        # TODO: remove this code when/if GT data era ok
        # Remove duplicate rows based on 'gt_timestamp' column, keeping the first occurrence
        gt_data_unique = gt_stream_data.drop_duplicates(subset="gt_sgf_timestamp", keep="first")
        sim_data_unique = sim_data.drop_duplicates(subset=SGFSignals.Columns.SGF_TIMESTAMP, keep="first")
        gt_data_unique = gt_stream_data.drop_duplicates(subset="gt_sgf_timestamp", keep="first")
        sim_data_unique = sim_data.drop_duplicates(subset=SGFSignals.Columns.SGF_TIMESTAMP, keep="first")

        return gt_data_unique, sim_data_unique

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
                "gt_sgf_timestamp": int(data["sSigHeader"]["uiTimeStamp"]),
                "gt_no_of_objects": data["staticObjectsOutput"]["numberOfObjects"],
                "gt_no_of_vertices": data["staticObjectVerticesOutput"]["numberOfVertices"],
            }

            for i, objects in enumerate(data["staticObjectsOutput"]["objects"]):
                flat_item[f"gt_obstacle_id_{i}"] = objects["obstacleId"]
                flat_item[f"gt_associated_dynamic_object_id_{i}"] = objects["associatedDynamicObjectId"]
                flat_item[f"gt_vertex_start_index_{i}"] = objects["vertexStartIndex"]
                flat_item[f"gt_used_vertices_{i}"] = objects["usedVertices"]
                flat_item[f"gt_existence_probability_{i}"] = objects["existenceProbability"]
                flat_item[f"gt_confidence_wheel_traversable_{i}"] = objects["heightConfidences"]["wheelTraversable"]
                flat_item[f"gt_confidence_body_traversable_{i}"] = objects["heightConfidences"]["bodyTraversable"]
                flat_item[f"gt_confidence_high_{i}"] = objects["heightConfidences"]["high"]
                flat_item[f"gt_confidence_hanging_{i}"] = objects["heightConfidences"]["hanging"]
                flat_item[f"gt_semantic_type_{i}"] = objects["semanticType"]
                flat_item[f"gt_is_grouped_{i}"] = objects["isGrouped"]
                flat_item[f"gt_is_associated_{i}"] = objects["isAssociated"]

            for i, vert in enumerate(data["staticObjectVerticesOutput"]["vertices"]):
                flat_item[f"gt_vertex_x_{i}"] = vert["x"]
                flat_item[f"gt_vertex_y_{i}"] = vert["y"]

            flat_data.append(flat_item)

        # Creating DataFrame
        df = pd.DataFrame(flat_data)

        return df
