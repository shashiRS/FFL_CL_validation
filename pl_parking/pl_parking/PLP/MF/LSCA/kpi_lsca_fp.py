#!/usr/bin/env python3
"""KPI for LSCA false positive"""

import base64
import json
import logging
import math
import os
import sys
from typing import List

import pandas as pd
import plotly.graph_objects as go
from tsf.core.common import AggregateFunction, PathSpecification, RelationOperator
from tsf.core.report import (
    ProcessingResult,
    ProcessingResultsList,
)
from tsf.core.results import DATA_NOK, GROUND_TRUTH_BROKEN, ExpectedResult, Result
from tsf.core.testcase import (
    CustomReportTestStep,
    TestCase,
    TestStep,
    register_inputs,
    register_side_load,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.db.results import TeststepResult
from tsf.io.sideload import JsonSideLoad
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "Pinzariu, George-Claudiu (uif94738)"
__copyright__ = "2024-2012, Continental AG"
__version__ = "1.0"
__status__ = "Development"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ALIAS = "FP_LSCA"
SIDE_LOAD_ALIAS = "GroundTruth"


class GroundTruthError(Exception):
    """Custom exception for specific use cases."""

    def __init__(self, message):
        super().__init__(message)


class CustomTeststepReport(CustomReportTestStep):
    """Custom test step report"""

    def overview(
        self,
        processing_details_list: ProcessingResultsList,
        teststep_result: List["TeststepResult"],
    ):
        """Method which customize the overview page in report"""
        try:
            s = ""
            file_counter = 0
            km_driven = 0.0
            driven_time = 0.0
            total_brake_events = 0
            fp_brake_events = 0
            self.result_list = []
            pr_list = processing_details_list

            for file in range(len(pr_list)):
                json_entries = ProcessingResult.from_json(pr_list.processing_result_files[file])
                file_counter += 1
                a = {"Measurement": json_entries["file_name"]}
                a.update(json_entries["Additional_results"])
                self.result_list.append(a)

                if "Km_driven" in json_entries.details:
                    km_driven += json_entries.details["Km_driven"]
                if "driven_time" in json_entries.details:
                    driven_time += json_entries.details["driven_time"]

                if "fp_brake_events" in json_entries.details:
                    fp_brake_events += json_entries.details["fp_brake_events"]
                if "total_brake_events" in json_entries.details:
                    total_brake_events += json_entries.details["total_brake_events"]

            additional_table = pd.DataFrame(
                {
                    "Number of measurements": {
                        "1": file_counter,
                    },
                    "Number of total braking interventions": {
                        "1": total_brake_events,
                    },
                    "Number of FP events": {
                        "1": fp_brake_events,
                    },
                    "Number of driven hours": {
                        "1": driven_time,
                    },
                }
            )

            s += "<br>"
            s += "<br>"
            s += "<h4>Evaluation results:</h4>"
            s += fh.build_html_table(additional_table)
            s += "<br>"
            s += "<br>"

            from json import dumps

            columns = []
            row_events = []
            for r in self.result_list:
                columns.extend(list(r.keys()))
                break

            for d in self.result_list:
                r = []
                for c in columns:
                    if c in d:
                        v = d[c]
                        if isinstance(v, dict):
                            if "color" in v:
                                r.append(
                                    str(
                                        f"""<span align="center" style="width: 100%; height: 100%; display: block;background-color: {v['color']}; color : #ffffff">{v['value']}</span>"""
                                    )
                                )
                            else:
                                r.append(
                                    str(
                                        f"""<span align="center" style="width: 100%; height: 100%; display: block">{v['value']}</span>"""
                                    )
                                )
                        elif "Measurement" in c:
                            r.append(
                                str(
                                    f"""<span align="center" style="background-color: {d['Verdict']['color']}; color : #ffffff">{v}</span>"""
                                )
                            )
                        else:
                            r.append(v)

                    else:
                        r.append("")
                row_events.append(r)

            column_names = [{"title": str(c)} for c in columns]
            additional_tables = (
                """
        <h2>Additional Information</h2>
<script>
var table_column_names = """
                + dumps(column_names)
                + """;
var table_rows_events =  """
                + dumps(row_events)
                + """
$(document).ready(function() {
$('#events_table').DataTable( {
paging:    true,
searching: true,
info:      true,
scrollX: true,
ordering: true,
data: table_rows_events,
columns: table_column_names
} );
});
</script>
<table class="table-sm table-striped compact nowrap" id="events_table">
</table>
"""
            )
            s += additional_tables

        except Exception:
            s += "<h6>No additional info available</h6>"
        return s

    def details(self, processing_details: ProcessingResult, teststep_result: "TeststepResult") -> str:
        """Method to customize the details page in report."""
        s = "<br>"
        m_res = teststep_result.measured_result
        e_res = teststep_result.teststep_definition.expected_results[None]
        (
            _,
            status,
        ) = e_res.compute_result_status(m_res)
        verdict = status.key.lower()

        if "data nok" in verdict:
            verdict = fc.NOT_ASSESSED
        s += (
            '<span align="center" style="width: 100%; height: 100%; display: block;background-color:'
            f' {fh.get_color(verdict)}; color : #ffffff">Step result: {verdict.upper()}</span>'
        )
        for k, v in processing_details.details.items():
            if "Plots" in k:
                s += "<div>"
                for plot in v:
                    s += plot
                s += "</div>"

        return s


import numpy as np


def transform_odo_obj_shape(coords, x_odo, y_odo, yaw):
    """Transform the coordinates based on the odometry position."""
    if all(coord == 0 for coord in coords):
        return coords

    rotation_matrix = np.array([[np.cos(yaw), -np.sin(yaw)], [np.sin(yaw), np.cos(yaw)]])
    for i in range(0, len(coords), 2):
        point = np.array(coords[i : i + 2])
        point_a = point[0], point[1]
        # First, apply the rotation to the point relative to origin (0,0)
        rotated_point_a = rotation_matrix @ point_a
        rotated_point_a = rotated_point_a + np.array([x_odo, y_odo])
        coords[i] = rotated_point_a[0]
        coords[i + 1] = rotated_point_a[1]

    return coords


def transform_coordinates_using_new_origin(old_origin, new_origin, coordinates):
    """
    Transform coordinates from an old origin to a new origin.

    Parameters:
    - old_origin: Tuple (x_old, y_old), the coordinates of the old origin.
    - new_origin: Tuple (x_new, y_new), the coordinates of the new origin.
    - coordinates: List of tuples [(x1, y1), (x2, y2), ...], the coordinates to transform.

    Returns:
    - List of transformed coordinates.
    """
    # new_origin = (0, 0)
    transformed_coords = []
    try:
        # Calculate the offset between old and new origins
        offset_x = new_origin[0] - old_origin[0]
        offset_y = new_origin[1] - old_origin[1]

        # Transform each coordinate
        for i in range(len(coordinates) - 1):
            transformed_coords.append(coordinates[i] + offset_x)
            transformed_coords.append(coordinates[i + 1] + offset_y)
        # transformed_coords = [(x + offset_x, y + offset_y) for x, y in coordinates]
        old_origin = tuple(old_origin)
        new_origin = tuple(new_origin)
    except Exception:

        return coordinates

    return transformed_coords


def calclate_euclidian_dist_between_points(car, object):
    """
    Calculate the Euclidean distance between two points in 2D space.

    :param point1: Tuple (x1, y1) - coordinates of the first point
    :param point2: Tuple (x2, y2) - coordinates of the second point
    :return: Distance between the two points
    """
    smallest_dist = []
    if object[0][0]:

        for idx, _ in enumerate(car[0]):
            x1, y1 = car[0][idx], car[1][idx]
            for idx2, _ in enumerate(object[0]):
                x2, y2 = object[0][idx2], object[1][idx2]
                smallest_dist.append(math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2))

        return round(min(smallest_dist), 2)
    return 0


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        ACTIVATE_BRAKE_INTERV = "ActivateBrakeIntervScreen"
        LSCA_STATE = "LSCAState"
        VELOCITY = "Velocity"
        STEERING_ANGLE = "SteeringAngle"
        TIMESTAMP = "mts_ts"
        LSCA_TIMESTAMP = "LSCA_ts"
        MINIMUM_DISTANCE = "MINIMUM_DISTANCE"
        DRIVEN_DISTANCE = "DRIVEN_DISTANCE"
        IS_ADC5X = "IS_ADC5X"
        NUM_DYN_OBJ = "NUM_DYN_OBJ"
        NUM_STAT_OBJ = "NUM_STAT_OBJ"
        ACTUAL_SIZE_STAT = "ACTUAL_SIZE_STAT"
        ACTUAL_SIZE_DYN = "ACTUAL_SIZE_DYN"
        STATIC_OBJ_SHAPE_X = "STATIC_OBJ_{}_SHAPE_ARRAY_{}_X"
        STATIC_OBJ_SHAPE_Y = "STATIC_OBJ_{}_SHAPE_ARRAY_{}_Y"
        DYNAMIC_OBJ_SHAPE_X = "DYNAMIC_OBJ_{}_SHAPE_ARRAY_{}_X"
        DYNAMIC_OBJ_SHAPE_Y = "DYNAMIC_OBJ_{}_SHAPE_ARRAY_{}_Y"
        odo_x = "odo_x"
        odo_y = "odo_y"
        odo_yaw = "odo_yaw"
        cem_sgf_numobj = "cem_sgf_numobj"
        cem_sgf_first_index_vertex = "cem_sgf_first_index_vertex"
        cem_sgf_used_vertices = "cem_sgf_used_vertices"
        cem_sgf_vertices_x = "cem_sgf_vertices_x"
        cem_sgf_vertices_y = "cem_sgf_vertices_y"
        cem_sgf_max_vertices = "cem_sgf_max_vertices"
        cem_tpf_numobj = "cem_tpf_numobj"
        TPF_OBJ_SHAPE_X = "TPF_OBJ_SHAPE_X_{}_{}"
        TPF_OBJ_SHAPE_Y = "TPF_OBJ_SHAPE_Y_{}_{}"
        TPF_REFERENCE_X = "TPF_REFERENCE_X"
        TPF_REFERENCE_Y = "TPF_REFERENCE_Y"
        GEAR = "GEAR"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.ACTIVATE_BRAKE_INTERV: [
                "SIM VFB.MfLsca1.hmiPort.activateBrakeInterventionScreen_nu",
                "MTA_ADC5.MF_LSCA_DATA.hmiPort.activateBrakeInterventionScreen_nu",
            ],
            self.Columns.LSCA_STATE: [
                "SIM VFB.MfLsca1.statusPort.brakingModuleState_nustatusPort.brakingModuleState_nu",
                "MTA_ADC5.MF_LSCA_DATA.statusPort.brakingModuleState_nu",
            ],
            self.Columns.NUM_DYN_OBJ: [
                "SIM VFB.SiCoreGeneric.m_collisionEnvironmentModelPort.numberOfDynamicObjects_u8",
                "MTA_ADC5.SI_DATA.m_collisionEnvironmentModelPort.numberOfDynamicObjects_u8",
            ],
            self.Columns.NUM_STAT_OBJ: [
                "SIM VFB.SiCoreGeneric.m_collisionEnvironmentModelPort.numberOfStaticObjects_u8",
                "MTA_ADC5.SI_DATA.m_collisionEnvironmentModelPort.numberOfStaticObjects_u8",
            ],
            self.Columns.ACTUAL_SIZE_STAT: [
                "SIM VFB.SiCoreGeneric.m_collisionEnvironmentModelPort.staticObjects[%].objShape_m.actualSize",
                "MTA_ADC5.SI_DATA.m_collisionEnvironmentModelPort.staticObjects[%].objShape_m.actualSize",
            ],
            self.Columns.ACTUAL_SIZE_DYN: [
                "SIM VFB.SiCoreGeneric.m_collisionEnvironmentModelPort.dynamicObjects[%].objShape_m.actualSize",
                "MTA_ADC5.SI_DATA.m_collisionEnvironmentModelPort.dynamicObjects[%].objShape_m.actualSize",
            ],
            self.Columns.VELOCITY: [
                "SIM VFB.SiCoreGeneric.m_egoMotionPort.vel_mps",
                "MTA_ADC5.SI_DATA.m_egoMotionPort.vel_mps",
            ],
            self.Columns.cem_sgf_numobj: [
                "SIM VFB.CEM200_SGF.m_SgfOutput.staticObjectsOutput.numberOfObjects",
                "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.numberOfObjects",
            ],
            self.Columns.cem_sgf_first_index_vertex: [
                "SIM VFB.CEM200_SGF.m_SgfOutput.staticObjectsOutput.objects[%].vertexStartIndex",
                "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.objects[%].vertexStartIndex",
            ],
            self.Columns.cem_sgf_used_vertices: [
                "SIM VFB.CEM200_SGF.m_SgfOutput.staticObjectsOutput.objects[%].usedVertices",
                "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectsOutput.objects[%].usedVertices",
            ],
            self.Columns.cem_sgf_vertices_x: [
                "SIM VFB.CEM200_SGF.m_SgfOutput.staticObjectVerticesOutput.vertices[%].x",
                "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectVerticesOutput.vertices[%].x",
            ],
            self.Columns.cem_sgf_vertices_y: [
                "SIM VFB.CEM200_SGF.m_SgfOutput.staticObjectVerticesOutput.vertices[%].y",
                "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectVerticesOutput.vertices[%].y",
            ],
            self.Columns.cem_sgf_max_vertices: [
                "SIM VFB.CEM200_SGF.m_SgfOutput.staticObjectVerticesOutput.numberOfVertices",
                "MTA_ADC5.CEM200_SGF_DATA.m_SgfOutput.staticObjectVerticesOutput.numberOfVertices",
            ],
            self.Columns.cem_tpf_numobj: [
                "SIM VFB.CEM200_TPF2.m_tpObjectList.numberOfObjects",
                "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.numberOfObjects",
            ],
            # self.Columns.cem_tpf_point_x: ["MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].point.x"],
            # self.Columns.cem_tpf_point_y: ["MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].point.y"],
            # self.Columns.MINIMUM_DISTANCE:
            # [
            #     "SIM VFB.PdCp1.procToLogicPort.minimalDistance_m",
            #     "MTA_ADC5.MF_PDWARNPROC_DATA.procToLogicPort.minimalDistance_m",
            # ],
            #     self.Columns.GEAR: [
            #     "MTA_ADC5.MF_TRJCTL_DATA.GearboxCtrlRequestPort.gearReq_nu",
            #     "SIM VFB.ApTrjctlGeneric.gearboxCtrlRequestPort.gearReq_nu",
            # ],
            self.Columns.DRIVEN_DISTANCE: [
                "SIM VFB.SiCoreGeneric.m_egoMotionPort.drivenDistance_m",
                "MTA_ADC5.SI_DATA.m_egoMotionPort.drivenDistance_m",
            ],
            self.Columns.LSCA_TIMESTAMP: [
                "SIM VFB.MfLsca1.hmiPort.sSigHeader.uiTimeStamp",
                "MTA_ADC5.MF_LSCA_DATA.hmiPort.sSigHeader.uiTimeStamp",
            ],
            self.Columns.odo_x: [
                "SIM VFB.VEDODO_0.m_odoEstimationOutputPort.odoEstimation.xPosition_m",
                "MTA_ADC5.MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.xPosition_m",
            ],
            self.Columns.odo_y: [
                "SIM VFB.VEDODO_0.m_odoEstimationOutputPort.odoEstimation.yPosition_m",
                "MTA_ADC5.MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.yPosition_m",
            ],
            self.Columns.odo_yaw: [
                "SIM VFB.VEDODO_0.m_odoEstimationOutputPort.odoEstimation.yawAngle_rad",
                "MTA_ADC5.MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.yawAngle_rad",
            ],
            # self.Columns.TPF_REFERENCE_X:
            # [   "SIM VFB.CEM200_TPF2.m_tpObjectList.objects[%].shapePoints.referencePoint.x",
            #     "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.referencePoint.x"],
            # self.Columns.TPF_REFERENCE_Y: ["SIM VFB.CEM200_TPF2.m_tpObjectList.objects[%].shapePoints.referencePoint.y",
            #     "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.referencePoint.y"],
        }
        self.MAX_STATIC_OBJ_COUNT = 16
        self.MAX_DYNAMIC_OBJ_COUNT = 10
        self.MAX_DYNAMIC_OBJ_SHAPE = 4
        self.MAX_STATIC_OBJ_SHAPE = 16
        #
        # MTA_ADC5.SI_DATA.m_collisionEnvironmentModelPort.staticObjects[].objShape_m.array[].y_dir
        static_objs = {}
        dynamic_objs = {}
        for obj in range(self.MAX_STATIC_OBJ_COUNT):
            for shape_array in range(self.MAX_STATIC_OBJ_SHAPE):
                static_objs[self.Columns.STATIC_OBJ_SHAPE_X.format(obj, shape_array)] = [
                    f"SIM VFB.SiCoreGeneric.m_collisionEnvironmentModelPort.staticObjects[{obj}].objShape_m.array[{shape_array}].x_dir",
                    f"MTA_ADC5.SI_DATA.m_collisionEnvironmentModelPort.staticObjects[{obj}].objShape_m.array[{shape_array}].x_dir",
                ]
                static_objs[self.Columns.STATIC_OBJ_SHAPE_Y.format(obj, shape_array)] = [
                    f"SIM VFB.SiCoreGeneric.m_collisionEnvironmentModelPort.staticObjects[{obj}].objShape_m.array[{shape_array}].y_dir",
                    f"MTA_ADC5.SI_DATA.m_collisionEnvironmentModelPort.staticObjects[{obj}].objShape_m.array[{shape_array}].y_dir",
                ]
        for obj in range(self.MAX_DYNAMIC_OBJ_COUNT):
            for shape_array in range(self.MAX_DYNAMIC_OBJ_SHAPE):
                dynamic_objs[self.Columns.DYNAMIC_OBJ_SHAPE_X.format(obj, shape_array)] = [
                    f"SIM VFB.SiCoreGeneric.m_collisionEnvironmentModelPort.dynamicObjects[{obj}].objShape_m.array[{shape_array}].x_dir",
                    f"MTA_ADC5.SI_DATA.m_collisionEnvironmentModelPort.dynamicObjects[{obj}].objShape_m.array[{shape_array}].x_dir",
                ]
                dynamic_objs[self.Columns.DYNAMIC_OBJ_SHAPE_Y.format(obj, shape_array)] = [
                    f"SIM VFB.SiCoreGeneric.m_collisionEnvironmentModelPort.dynamicObjects[{obj}].objShape_m.array[{shape_array}].y_dir",
                    f"MTA_ADC5.SI_DATA.m_collisionEnvironmentModelPort.dynamicObjects[{obj}].objShape_m.array[{shape_array}].y_dir",
                ]

        self.MAX_TPF_OBJ_COUNT = 100
        self.MAX_TPF_OBJ_SHAPE = 4

        tpf_objs = {}

        for obj in range(self.MAX_TPF_OBJ_COUNT):
            for shape_array in range(self.MAX_TPF_OBJ_SHAPE):
                tpf_objs[self.Columns.TPF_OBJ_SHAPE_X.format(obj, shape_array)] = [
                    f"SIM VFB.CEM200_TPF2.m_tpObjectList.objects[{obj}].shapePoints.points[{shape_array}].position.x",
                    f"MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[{obj}].shapePoints.points[{shape_array}].position.x",
                ]
                tpf_objs[self.Columns.TPF_OBJ_SHAPE_Y.format(obj, shape_array)] = [
                    f"SIM VFB.CEM200_TPF2.m_tpObjectList.objects[{obj}].shapePoints.points[{shape_array}].position.y",
                    f"MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[{obj}].shapePoints.points[{shape_array}].position.y",
                ]
        self._properties.update(static_objs)
        self._properties.update(dynamic_objs)
        # self._properties.update(tpf_objs)


signals_obj = Signals()

local_run = False  # Evaluate only in cloud

gt_data_path = (
    PathSpecification(folder=r"s3://par230-prod-data-lake-sim/gt_labels/", suffix="_lsca", extension=".json", s3=True)
    if not local_run
    else PathSpecification(folder=r"D:\Measurements\PLP_61441", suffix="_lsca", extension=".json")
)


# TODO
# 1. GT will be modified, a longer max distance will be required
# 2. LSCA thresholds for FP will have to be updated
# 3. GT will have coordinates to be plotted
@teststep_definition(
    step_number=1,
    name="FP KPI",
    description="Check if a braking event is classified as a FP (if the car brakes and there is no obstacle in front/back of the car).",
    expected_result=ExpectedResult(
        1.0,
        operator=RelationOperator.LESS_OR_EQUAL,
        unit="event/hour",
        aggregate_function=AggregateFunction.KPI,
    ),
)
@register_side_load(
    alias=SIDE_LOAD_ALIAS,
    side_load=JsonSideLoad,  # type of side loaders
    path_spec=gt_data_path,
    # Absolute path for the sideload.
)
@register_signals(ALIAS, Signals)
class FalsePositiveStep(TestStep):
    """Test step class"""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")

        try:
            FRONT_KEY = "front"
            REAR_KEY = "rear"
            FP_MIN_DIST = "No object in GT"
            DRIVING_DIRECTION = FRONT_KEY
            # ACTIVATION_PERCENTAGE = 95 # %
            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "driven_time": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            plots = []
            vertice_template = ["cem_sgf_vertices_x_{}", "cem_sgf_vertices_y_{}"]
            # tpf_vertices_template = ["TPF_OBJ_SHAPE_X_{}_{}",
            #                     "TPF_OBJ_SHAPE_Y_{}_{}"]
            VELOCITY_THRESHOLD = 10  # km/h
            test_result = fc.INPUT_MISSING
            total_brake_events = 0
            fp_brake_events = 0
            remark = "<b>Criteria for evaluation</b><br>\
                            If a brake is detected, check if there is an object in the GT data. If there is no object, the event is classified as a False Positive.<br>"
            hours_of_driving = 0
            evaluation_text = ""
            gt_detected_data = {}
            obj_template = []
            fp_ts = []
            object_df = pd.DataFrame()

            df = self.readers[ALIAS]
            df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]

            df[Signals.Columns.TIMESTAMP] = df.index
            df.set_index(Signals.Columns.LSCA_TIMESTAMP, inplace=True)
            duplicate_indexes = df.index.duplicated()
            df = df[~duplicate_indexes]

            lsca_state = df[Signals.Columns.LSCA_STATE]

            velocity = df[Signals.Columns.VELOCITY]
            velocity = velocity * constants.GeneralConstants.MPS_TO_KMPH
            df[Signals.Columns.TIMESTAMP] -= df[Signals.Columns.TIMESTAMP].iat[0]
            df[Signals.Columns.TIMESTAMP] /= constants.GeneralConstants.US_IN_S

            df[Signals.Columns.DRIVEN_DISTANCE] -= df[Signals.Columns.DRIVEN_DISTANCE].iat[0]
            # df[Signals.Columns.DRIVEN_DISTANCE] /= constants.GeneralConstants.M_TO_KM
            distance_recording = df[Signals.Columns.DRIVEN_DISTANCE]
            driven_km = distance_recording[distance_recording > 0]

            # Get individual brake events from recording
            # Ex: Signal '0001110010110' would mean 3 separate LSCA activations
            # It takes 2 rows at a time and check if first element is != than the second
            mask_brake_events = lsca_state.rolling(2).apply(
                lambda x: x[0] == 0 and x[1] == constants.LSCAState.LSCA_STATE_INTERVENTION, raw=True
            )

            # Get the number of seconds that have passed from frame to frame
            seconds = df[Signals.Columns.TIMESTAMP].rolling(2).apply(lambda x: x[1] - x[0], raw=True)
            velocity_df_filtered = pd.concat([seconds, velocity], axis=1)
            velocity_mask = velocity.abs() < VELOCITY_THRESHOLD
            velocity_df_filtered = velocity_df_filtered[velocity_mask]
            seconds_under_10_kmh = velocity_df_filtered[Signals.Columns.TIMESTAMP].sum()
            hours_of_driving = seconds_under_10_kmh / constants.GeneralConstants.S_IN_HOURS
            total_brake_events = mask_brake_events.sum()
            timestamp_brake_events = [row for row, val in mask_brake_events.items() if val == 1]

            # Check if the ground truth data is available and correctly written
            try:
                gt_data = self.side_load[SIDE_LOAD_ALIAS]
                gt_data = gt_data["SectorBasedDistance"]
            except Exception as err:
                # Create a table to display a small error message and a download link for the JSON file
                # then stop the processing
                json_string = json.dumps(gt_data, indent=4)
                json_bytes = json_string.encode("utf-8")  # Encode to bytes
                base64_encoded = base64.b64encode(json_bytes).decode(
                    "utf-8"
                )  # Base64 encode and decode back to a string
                json_download = (
                    f'<a href="data:application/json;base64,{base64_encoded}" download="sample.json">Download JSON</a>'
                )
                table = fh.build_html_table(pd.DataFrame({"GroundTruth error": [str(err), json_download]}))
                self.result.details["Plots"].append(table)
                self.result.measured_result = GROUND_TRUTH_BROKEN
                return

            # Check if the objects are in front or rear of the car

            for item in gt_data:
                if item.get(FRONT_KEY, None):
                    DRIVING_DIRECTION = FRONT_KEY
                    break
                elif item.get(REAR_KEY, None):
                    DRIVING_DIRECTION = REAR_KEY
                    break

            # Get the distance between the car and the object in the GT data
            for item in gt_data:
                if item.get(DRIVING_DIRECTION):
                    val = item.get(DRIVING_DIRECTION)[0]

                    gt_detected_data[item["Timestamp"]] = (
                        round(val["distanceValue"], 3),
                        round(val["distanceError"], 3),
                    )
                else:
                    gt_detected_data[item["Timestamp"]] = (FP_MIN_DIST, FP_MIN_DIST)

            # Check if the brake events are following the GT data
            # If brake event is detected, check if any object is present in GT data at that timestamp
            for brake_ts in timestamp_brake_events:
                if gt_detected_data.get(brake_ts)[0] == FP_MIN_DIST:
                    fp_brake_events += 1
                    fp_ts.append(round(df[Signals.Columns.TIMESTAMP].loc[brake_ts], 2))

            # Check if LSCA is active in the recording
            # percentage = (lsca_state == constants.LSCAState.LSCA_STATE_DEACTIVATED).mean() * 100
            # if percentage <= ACTIVATION_PERCENTAGE:
            if lsca_state.max() == constants.LSCAState.LSCA_STATE_DEACTIVATED:

                self.result.measured_result = DATA_NOK
                test_result = fc.NOT_ASSESSED
                evaluation_text = f"LSCA component was in state DEACTIVATED the whole time, with signal {signals_obj._properties[Signals.Columns.LSCA_STATE][0]} == {constants.LSCAState.LSCA_STATE_DEACTIVATED}."
                # Dismiss hours of driving, as the component was not active
                hours_of_driving = 0
            else:
                self.result.measured_result = Result(fp_brake_events, hours_of_driving)

                if fp_brake_events > 0:
                    test_result = fc.FAIL
                    evaluation_text = f"LSCA component intervened while no object was present in GT, at timestamps: {', '.join(map(str, fp_ts))} [s]."
                else:
                    test_result = fc.PASS
                    evaluation_text = "LSCA component had no FP events."

            ############################## This part is just for visualization purposes ##############################
            for obj in range(signals_obj.MAX_STATIC_OBJ_COUNT):
                obj_template.clear()
                for shape_array in range(signals_obj.MAX_STATIC_OBJ_SHAPE):
                    obj_template.append(signals_obj.Columns.STATIC_OBJ_SHAPE_X.format(obj, shape_array))
                    obj_template.append(signals_obj.Columns.STATIC_OBJ_SHAPE_Y.format(obj, shape_array))

                object_df[f"Static_Obj_{obj}"] = df[obj_template].apply(lambda row: row.values.tolist(), axis=1)
            for obj in range(signals_obj.MAX_DYNAMIC_OBJ_COUNT):
                obj_template.clear()
                for shape_array in range(signals_obj.MAX_DYNAMIC_OBJ_SHAPE):
                    obj_template.append(signals_obj.Columns.DYNAMIC_OBJ_SHAPE_X.format(obj, shape_array))
                    obj_template.append(signals_obj.Columns.DYNAMIC_OBJ_SHAPE_Y.format(obj, shape_array))

                object_df[f"Dynamic_Obj_{obj}"] = df[obj_template].apply(lambda row: row.values.tolist(), axis=1)

            vertices_count = max(df[Signals.Columns.cem_sgf_max_vertices])

            if vertices_count > 0:
                df["vertices"] = df[[x.format(i) for i in range(vertices_count) for x in vertice_template]].apply(
                    lambda row: row.values.tolist(), axis=1
                )
            #         max_tpf_vertices = max(df[Signals.Columns.cem_tpf_numobj])
            #         for i in range(max_tpf_vertices):
            #             df[f"tpf_vertices_{i}"] = df[[x.format(i,j)for j in range(signals_obj.MAX_TPF_OBJ_SHAPE) for x in tpf_vertices_template]].apply(
            #     lambda row: row.values.tolist(), axis=1
            # )

            collected_info = {
                ts: {
                    "static": [],
                    "ts": df[Signals.Columns.TIMESTAMP].loc[ts],
                    "sgf_vertices": [],
                    "tpf_vertices": [],
                    #   "gt_object" :transform_odo_obj_shape(GT_OBJ_SHAPE[DRIVING_DIRECTION].copy(),
                    #                                         df[Signals.Columns.odo_x].loc[ts],
                    #                  df[Signals.Columns.odo_y].loc[ts],
                    #                  df[Signals.Columns.odo_yaw].loc[ts])
                    #       ,
                    #   "gt_distance": gt_detected_data[ts],
                    "ego_vehicle": [
                        df[Signals.Columns.odo_x].loc[ts],
                        df[Signals.Columns.odo_y].loc[ts],
                        df[Signals.Columns.odo_yaw].loc[ts],
                    ],
                    # "dynamic":[],} for ts in list(gt_detected_data.keys())}
                    "dynamic": [],
                }
                for ts in timestamp_brake_events
            }
            for key, _ in collected_info.items():
                if df[Signals.Columns.NUM_DYN_OBJ].loc[key] > 0:
                    for obj in range(df[Signals.Columns.NUM_DYN_OBJ].loc[key]):
                        actual_size = (
                            df[f"{Signals.Columns.ACTUAL_SIZE_DYN}_{obj}"].loc[key] * 2
                        )  # take into account the y axis also
                        collected_info[key]["dynamic"].append(
                            transform_odo_obj_shape(
                                object_df[f"Dynamic_Obj_{obj}"].loc[key][:actual_size],
                                collected_info[key]["ego_vehicle"][0],
                                collected_info[key]["ego_vehicle"][1],
                                collected_info[key]["ego_vehicle"][2],
                            )
                        )
                else:
                    collected_info[key]["dynamic"].append([None, None, None, None])
                if df[Signals.Columns.NUM_STAT_OBJ].loc[key] > 0:
                    for obj in range(df[Signals.Columns.NUM_STAT_OBJ].loc[key]):
                        actual_size = (
                            df[f"{Signals.Columns.ACTUAL_SIZE_STAT}_{obj}"].loc[key] * 2
                        )  # take into account the y axis also
                        collected_info[key]["static"].append(
                            transform_odo_obj_shape(
                                object_df[f"Static_Obj_{obj}"].loc[key][:actual_size],
                                collected_info[key]["ego_vehicle"][0],
                                collected_info[key]["ego_vehicle"][1],
                                collected_info[key]["ego_vehicle"][2],
                            )
                        )
                else:
                    collected_info[key]["static"].append([None, None, None, None])
                if df["cem_sgf_numobj"].loc[key] > 0:
                    for obj in range(df["cem_sgf_numobj"].loc[key]):
                        start_index = df[f"cem_sgf_first_index_vertex_{obj}"].loc[key] * 2
                        # start_index = df[f"cem_sgf_first_index_vertex_{obj}"].loc[12967697] * 2

                        end_index = df[f"cem_sgf_used_vertices_{obj}"].loc[key] * 2 + start_index
                        # end_index = df[f"cem_sgf_used_vertices_{obj}"].loc[12967697]* 2
                        # array_slice = df["vertices"].loc[key][start_index:end_index]
                        # vertices = df[f"cem_sgf_vertices_x_{obj}"].loc[key][start_index:end_index]
                        try:
                            collected_info[key]["sgf_vertices"].append(
                                transform_odo_obj_shape(
                                    df["vertices"].loc[key][start_index:end_index],
                                    collected_info[key]["ego_vehicle"][0],
                                    collected_info[key]["ego_vehicle"][1],
                                    collected_info[key]["ego_vehicle"][2],
                                )
                            )
                        except Exception:
                            collected_info[key]["sgf_vertices"].append([None, None, None, None])
                else:
                    collected_info[key]["sgf_vertices"].append([None, None, None, None])
                # if df["cem_tpf_numobj"].loc[key] > 0:
                #     for obj in range(df["cem_tpf_numobj"].loc[key]):
                #         coords = transform_coordinates_using_new_origin([df[f"{Signals.Columns.TPF_REFERENCE_X}_{obj}"].loc[key],
                #                                                 df[f"{Signals.Columns.TPF_REFERENCE_Y}_{obj}"].loc[key]],
                #                                                 [collected_info[key]["ego_vehicle"][0],
                #                                              collected_info[key]["ego_vehicle"][1]],
                #                                                df[f"tpf_vertices_{obj}"].loc[key])
                #         # coords = transform_odo_obj_shape(coords,
                #         #                                     collected_info[key]["ego_vehicle"][0],
                #         #                                     collected_info[key]["ego_vehicle"][1],
                #         #                                     collected_info[key]["ego_vehicle"][2])
                #         collected_info[key]["tpf_vertices"].append(coords)
                #         #collected_info[key]["tpf_vertices"].append(df[f"tpf_vertices_{obj}"].loc[key])

                # else:
                #     collected_info[key]["tpf_vertices"].append([None,None,None,None])
                if len(collected_info[key]["sgf_vertices"]) < vertices_count:
                    for _ in range(vertices_count - len(collected_info[key]["sgf_vertices"])):
                        collected_info[key]["sgf_vertices"].append([None, None, None, None])

                if len(collected_info[key]["static"]) < max(df[Signals.Columns.NUM_STAT_OBJ]):
                    for _ in range(max(df[Signals.Columns.NUM_STAT_OBJ]) - len(collected_info[key]["static"])):
                        collected_info[key]["static"].append([None, None, None, None])

                if len(collected_info[key]["dynamic"]) < max(df[Signals.Columns.NUM_DYN_OBJ]):
                    for _ in range(max(df[Signals.Columns.NUM_DYN_OBJ]) - len(collected_info[key]["dynamic"])):
                        collected_info[key]["dynamic"].append([None, None, None, None])
                # if len(collected_info[key]["tpf_vertices"]) < max_tpf_vertices:
                #     for i in range(max_tpf_vertices-len(collected_info[key]["tpf_vertices"])):
                #         collected_info[key]["tpf_vertices"].append([None,None,None,None])

            fig_with_fames = go.Figure()
            global_x_min = float("inf")
            global_x_max = float("-inf")
            global_y_min = float("inf")
            global_y_max = float("-inf")
            first_frame = True

            frames = []

            for key, val in collected_info.items():

                frame_data = []  # np.rad2deg(val.get('ego_vehicle',None)[0][2])
                new_origin_x, new_origin_y, new_origin_yaw = val.get("ego_vehicle", None)

                vehicle_plot = constants.DrawCarLayer.draw_car(new_origin_x, new_origin_y, new_origin_yaw)
                car_x = vehicle_plot[0][0]
                car_y = vehicle_plot[0][1]
                vehicle_plot = vehicle_plot[1]
                global_x_min = min(global_x_min, min(car_x))
                global_x_max = max(global_x_max, max(car_x))
                global_y_min = min(global_y_min, min(car_y))
                global_y_max = max(global_y_max, max(car_y))

                # Parking box coordinates for the current frame (if they exist)
                # if val.get("static", None):  # Only create the parking box trace if coordinates exist
                for coords in val["static"]:
                    # coords = val["static"]
                    x_coords_static, y_coords_static = coords[::2], coords[1::2]
                    smallest_dist = calclate_euclidian_dist_between_points(
                        [car_x, car_y], [x_coords_static, y_coords_static]
                    )
                    x_coords_static += x_coords_static[:1]
                    y_coords_static += y_coords_static[:1]
                    is_pb_found = True if x_coords_static[0] else False
                    x_coords_static_plot = x_coords_static
                    y_coords_static_plot = y_coords_static
                    if x_coords_static_plot[0]:
                        global_x_min = min(global_x_min, min(x_coords_static_plot))
                        global_x_max = max(global_x_max, max(x_coords_static_plot))
                        global_y_min = min(global_y_min, min(y_coords_static_plot))
                        global_y_max = max(global_y_max, max(y_coords_static_plot))
                    static_obj_trace = go.Scatter(
                        x=x_coords_static_plot,
                        y=y_coords_static_plot,
                        showlegend=True if is_pb_found else False,
                        mode="lines",
                        line=dict(color="black"),
                        fill="toself",  # Fill the polygon
                        # fillcolor="black",
                        # fillcolor='rgba(255, 0, 0, 0.3)' if val["verdict"][pb_id] == "FAIL" else\
                        #         "rgba(0, 255, 0, 0.3)" if val["verdict"][pb_id] == "PASS" else "rgba(239, 239, 240, 0.3)",  # Semi-transparent red fill
                        name="SI Static Object<br>" f"Distance to car {smallest_dist} m",
                        text=[
                            f"Timestamp: {val['ts']}<br>" f"X: {x_coords_static[x]}<br>" f"Y: {ycoord}"
                            for x, ycoord in enumerate(y_coords_static)
                        ],
                        hoverinfo="text",
                    )

                    # Add the parking box trace to the figure, then add to frame_data
                    if first_frame:
                        fig_with_fames.add_trace(static_obj_trace)
                        frame_data.append(static_obj_trace)
                    else:
                        frame_data.append(static_obj_trace)

                # Dynamic object coordinates for the current frame (if they exist)
                for coords in val["dynamic"]:

                    x_coords_dynamic, y_coords_dynamic = coords[::2], coords[1::2]
                    smallest_dist = calclate_euclidian_dist_between_points(
                        [car_x, car_y], [x_coords_dynamic, y_coords_dynamic]
                    )
                    x_coords_dynamic += x_coords_dynamic[:1]
                    y_coords_dynamic += y_coords_dynamic[:1]
                    is_pb_found = True if x_coords_dynamic[0] else False
                    x_coords_dynamic_plot = x_coords_dynamic
                    y_coords_dynamic_plot = y_coords_dynamic

                    if x_coords_dynamic_plot[0]:
                        global_x_min = min(global_x_min, min(x_coords_dynamic_plot))
                        global_x_max = max(global_x_max, max(x_coords_dynamic_plot))
                        global_y_min = min(global_y_min, min(y_coords_dynamic_plot))
                        global_y_max = max(global_y_max, max(y_coords_dynamic_plot))
                    dynamic_obj_trace = go.Scatter(
                        x=x_coords_dynamic_plot,
                        y=y_coords_dynamic_plot,
                        showlegend=True if is_pb_found else False,
                        mode="lines",
                        fill="toself",  # Fill the polygon
                        # fillcolor="black",
                        line=dict(color="black"),
                        name="SI Dynamic object<br>" f"Distance to car {smallest_dist} m",
                        text=[
                            f"Timestamp: {val['ts']}<br>" f"X: {x_coords_dynamic[x]}<br>" f"Y: {ycoord}"
                            for x, ycoord in enumerate(y_coords_dynamic)
                        ],
                        hoverinfo="text",
                    )

                    # Add the parking box trace to the figure, then add to frame_data
                    if first_frame:
                        fig_with_fames.add_trace(dynamic_obj_trace)
                        frame_data.append(dynamic_obj_trace)
                    else:
                        frame_data.append(dynamic_obj_trace)

                for coords in val["sgf_vertices"]:

                    x_coords_gt, y_coords_gt = coords[::2], coords[1::2]
                    smallest_dist = calclate_euclidian_dist_between_points([car_x, car_y], [x_coords_gt, y_coords_gt])

                    x_coords_gt += x_coords_gt[:1]
                    y_coords_gt += y_coords_gt[:1]
                    is_pb_found = True if x_coords_gt[0] else False
                    x_coords_sgf_plot = x_coords_gt
                    y_coords_sgf_plot = y_coords_gt

                    if x_coords_sgf_plot[0]:
                        global_x_min = min(global_x_min, min(x_coords_sgf_plot))
                        global_x_max = max(global_x_max, max(x_coords_sgf_plot))
                        global_y_min = min(global_y_min, min(y_coords_sgf_plot))
                        global_y_max = max(global_y_max, max(y_coords_sgf_plot))
                    sgf_obj_trace = go.Scatter(
                        x=x_coords_sgf_plot,
                        y=y_coords_sgf_plot,
                        showlegend=True if is_pb_found else False,
                        mode="lines",
                        fill="toself",  # Fill the polygon
                        fillcolor="#ffc107",
                        line=dict(color="black"),
                        name="SGF object<br>" f"Distance to car {smallest_dist} m",
                        text=[
                            f"Timestamp: {val['ts']}<br>" f"X: {x_coords_gt[x]}<br>" f"Y: {ycoord}"
                            for x, ycoord in enumerate(y_coords_gt)
                        ],
                        hoverinfo="text",
                    )

                    # Add the parking box trace to the figure, then add to frame_data
                    if first_frame:
                        fig_with_fames.add_trace(sgf_obj_trace)
                        frame_data.append(sgf_obj_trace)
                    else:
                        frame_data.append(sgf_obj_trace)

                # for coords in val["tpf_vertices"]:

                #     x_coords_sgf, y_coords_sgf = coords[::2], coords[1::2]
                #     smallest_dist = calclate_euclidian_dist_between_points([car_x,car_y],[x_coords_sgf,y_coords_sgf])

                #     x_coords_sgf += x_coords_sgf[:1]
                #     y_coords_sgf += y_coords_sgf[:1]
                #     is_pb_found = True if x_coords_sgf[0] else False
                #     x_coords_sgf_plot = x_coords_sgf
                #     y_coords_sgf_plot = y_coords_sgf

                #     if x_coords_sgf_plot[0]:
                #         global_x_min = min(global_x_min, min(x_coords_sgf_plot))
                #         global_x_max = max(global_x_max, max(x_coords_sgf_plot))
                #         global_y_min = min(global_y_min, min(y_coords_sgf_plot))
                #         global_y_max = max(global_y_max, max(y_coords_sgf_plot))
                #     sgf_obj_trace = go.Scatter(
                #         x=x_coords_sgf_plot,
                #         y=y_coords_sgf_plot,
                #         showlegend=True if is_pb_found else False,
                #         mode="lines",
                #         fill="toself",  # Fill the polygon
                #         fillcolor="#ffc107",
                #         line=dict(color="black"),
                #         name="TPF object<br>"
                #             f"Distance to car {smallest_dist} m",
                #         text=[
                #             f"Timestamp: {val['ts']}<br>" f"X: {x_coords_sgf[x]}<br>" f"Y: {ycoord}"
                #             for x, ycoord in enumerate(y_coords_sgf)
                #         ],
                #         hoverinfo="text",
                #     )

                #     # Add the parking box trace to the figure, then add to frame_data
                #     if first_frame:
                #         fig.add_trace(sgf_obj_trace)
                #         frame_data.append(sgf_obj_trace)
                #     else:
                #         frame_data.append(sgf_obj_trace)
                #     x_coords_gt, y_coords_gt = val.get("gt_object")[::2], val.get("gt_object")[1::2]
                #     smallest_dist = val.get("gt_distance")[0]
                #     smallest_dist_error = val.get("gt_distance")[1]
                #     if smallest_dist == FP_MIN_DIST:
                #         smallest_dist = f"> {FP_MIN_DIST}"
                #         x_coords_gt = [None,None]
                #         y_coords_gt = [None,None]
                #     else:
                #         x_coords_gt = [x + smallest_dist for x in x_coords_gt]
                #     #x_coords_gt += x_coords_gt[:1]
                #    # y_coords_gt += y_coords_gt[:1]
                #     is_pb_found = True
                #     #x_coords_sgf_plot = x_coords_gt
                #     #y_coords_sgf_plot = y_coords_gt

                #     #if x_coords_sgf_plot[0]:
                #     global_x_min = min(global_x_min, min(x_coords_gt))
                #     global_x_max = max(global_x_max, max(x_coords_gt))
                #     global_y_min = min(global_y_min, min(y_coords_gt))
                #     global_y_max = max(global_y_max, max(y_coords_gt))
                #     gt_obj_scatter = go.Scatter(
                #         x=x_coords_gt,
                #         y=y_coords_gt,
                #         showlegend=True if is_pb_found else False,
                #         mode="lines",
                #        # fill="toself",  # Fill the polygon
                #         #fillcolor="#ffc107",
                #         line=dict(color="black", width=4),
                #         name="GT<br>"
                #             f"Distance to car {smallest_dist} m",
                #         text=[
                #             f"Timestamp: {val['ts']}<br>" f"Distance: {smallest_dist} m<br>" f"Distance error: {smallest_dist_error}"
                #         ],
                #         hoverinfo="text",
                #     )

                #     # Add the parking box trace to the figure, then add to frame_data
                #     if first_frame:
                #         fig_with_fames.add_trace(gt_obj_scatter)
                #         frame_data.append(gt_obj_scatter)
                #     else:
                #         frame_data.append(gt_obj_scatter)

                if first_frame:
                    for p in vehicle_plot:
                        fig_with_fames.add_trace(p)
                for p in vehicle_plot:
                    frame_data.append(p)
                first_frame = False

                frames.append(go.Frame(data=frame_data, name=str(collected_info[key]["ts"])))
            ap_time = df["mts_ts"].values.tolist()
            ap_time = [round(i, 2) for i in ap_time]
            # Add frames to the figure
            fig_with_fames.frames = frames

            # Configure the slider
            # sliders = [
            #     dict(
            #         steps=[
            #             dict(
            #                 method="animate",
            #                 args=[
            #                     [str(collected_info[key]["ts"])],  # The frame name is the timestamp
            #                     dict(
            #                         mode="immediate",
            #                         frame=dict(duration=1500, redraw=True),
            #                         transition=dict(duration=300),
            #                     ),
            #                 ],
            #                 label=str(collected_info[key]["ts"]),
            #             )
            #             for key in collected_info.keys()
            #         ],
            #         active=0,
            #         transition=dict(duration=300),
            #         x=0,  # Slider position
            #         xanchor="left",
            #         y=0,
            #         bgcolor="#FFA500",
            #         yanchor="top",
            #     )
            # ]
            # Add slider to layout
            fig_with_fames.update_layout(
                dragmode="pan",
                title="Visualization of the False Positive events",
                showlegend=True,
                xaxis=dict(range=[(global_x_min - 2), (global_x_max + 2)]),
                yaxis=dict(range=[(global_y_min - 2), (global_y_max + 2)]),
                # sliders=sliders,
                height=1000,
                # xaxis_title="Time [s]",
                # updatemenus=[
                #     dict(
                #         type="buttons",
                #         showactive=False,
                #         direction="left",
                #         y=-0.2,  # Adjust this value to position the buttons below the slider
                #         x=0.5,  # Center the buttons horizontally (optional)
                #         xanchor="center",  # Anchor to the center of the button container
                #         yanchor="top",  # Anchor to the top of the button container
                #         buttons=[
                #             dict(
                #                 label="Play",
                #                 method="animate",
                #                 args=[None, dict(frame=dict(duration=1500, redraw=True), fromcurrent=True)],
                #             ),
                #             # args=[None, dict(frame=dict(duration=500, redraw=True), fromcurrent=True)]
                #             dict(
                #                 label="Pause",
                #                 method="animate",
                #                 args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")],
                #             ),
                #         ],
                #     )
                # ],
            )
            fig_with_fames.update_layout(
                modebar=dict(
                    bgcolor="rgba(255, 255, 255, 0.8)",  # Optional: background color for mode bar
                    activecolor="#FFA500",  # Optional: active color for mode bar buttons
                )
            )

            plots.append(fh.build_html_table(pd.DataFrame({"Evaluation": [evaluation_text]}), remark))
            if fp_brake_events > 0:
                plots.append(fig_with_fames)

            signal_fig = go.Figure()

            signal_fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=lsca_state.values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.LSCA_STATE][0],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>"
                        f"LSCA State:<br>"
                        f"{constants.LSCAState.get_variable_name(state)}"
                        for idx, state in enumerate(lsca_state.values.tolist())
                    ],
                    hoverinfo="text",
                    hoverlabel=dict(font=dict(color="white")),  # Set the hover text color to white
                )
            )

            signal_fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=velocity.values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.VELOCITY][0],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>"
                        f"Velocity:<br>"
                        f"{state * constants.GeneralConstants.MPS_TO_KMPH:.2f} km/h<br>"
                        f"{state:.2f} m/s"
                        for idx, state in enumerate(df[Signals.Columns.VELOCITY].values.tolist())
                    ],
                    hoverinfo="text",
                    hoverlabel=dict(font=dict(color="white")),  # Set the hover text color to white
                )
            )

            signal_fig.layout = go.Layout(
                yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]"
            )
            signal_fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plots.append(signal_fig)

            additional_results_dict = {
                "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                "Driven distance [m]": {"value": f"{driven_km.iat[-1]:.2f}"},
                "Braking events": {"value": f"{total_brake_events}"},
                "FP events": {"value": f"{fp_brake_events}"},
                "Processed time (< 10 km/h) [s]": {"value": f"{seconds_under_10_kmh:.2f}"},
            }

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
            self.result.details["total_brake_events"] = total_brake_events
            self.result.details["driven_time"] = hours_of_driving
            self.result.details["fp_brake_events"] = fp_brake_events
            self.result.details["Additional_results"] = additional_results_dict
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("988208")
@testcase_definition(
    name="FP LSCA with GT",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_WqNP5dHtEe2iKqc0KPO99Q&vvc.configuration=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fcm%2Fstream%2F_bMgUkM-3Ee2iKqc0KPO99Q&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_lWHOEPvsEeqIqKySVwTVNQ%2Fcomponents%2F_u4eQYMlKEe2iKqc0KPO99Q",
    description="FP Braking Rate in free driving scenarios (real parkings, slow moving in dense traffic).",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class LscaFalsePositive(TestCase):
    """Test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            FalsePositiveStep,
        ]
