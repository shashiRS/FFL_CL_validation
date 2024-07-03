"""Functional Test Helper - constants"""

from pathlib import Path

PASS = "passed"
FAIL = "failed"
# NOT_AVAILABLE = 'Not available'
NOT_ASSESSED = "not assessed"
CRASH = "crash"
GOOD = "good"
FAR = "far"
FP = "FP"
TP = "TP"
INPUT_MISSING = "input missing"
ERROR = "error with this part"
FUNCTIONAL_TEST = "Functional Tests"
SAFETY_TEST = "Safety Tests"
SMOKE_TEST = "Smoke Tests"
VEHICLE = "Vehicle"
SIM = "Sim"
VALID = "VALID"
HA22_CEM_FDP21P_OBJECT_ID_INVALID = 0
LIMIT_PERCENT = 1.00
PER_TEST_EXECUTION_TIME = "Execution_Time(hrs)"
PROJECT_NAME = "project_name"
TO_POPULATE_TO_EXCEL = False

# Reports Constants
REQ_ID = "Requirement ID"
TESTCASE_ID = "TestCase ID"
TEST_SAFETY_RELEVANT = "Safety Relevant"
TEST_DESCRIPTION = "Description"
TEST_RESULT = "Result"
FAILED_INDICES = "Output failed mts timestamps indices"
FAILED_SIGNAL = "Output failed signal"
LENGTH_OF_INDICES = "Length output failed  indices"
OUTPUT_TO_VERIFY = "Output to Verify"
INPUT_TO_VERIFY = "Input to Verify"
TESTCASE_ID_NOT_PROVIDED = "Not provided"
REQUIREMENT_ID_NOT_PROVIDED = "Not provided"
PLANNED_FOR_NOT_PROVIDED = "Not provided"
SAFETY_RELEVANT_NOT_PROVIDED = "Not provided"
SAFETY_RELEVANT_ANY = "Any"
SAFETY_RELEVANT_QM = "QM"
SAFETY_RELEVANT_ASIL_A = "ASIL-A"
SAFETY_RELEVANT_ASIL_B = "ASIL-B"
SAFETY_RELEVANT_ASIL_C = "ASIL-C"
SAFETY_RELEVANT_ASIL_D = "ASIL-D"
SIGNAL_FORM = "{}_{}"

PLANNED_FOR_MLC50 = "MLC50"
PLANNED_FOR_MLC55 = "MLC55"
PLANNED_FOR_MLC60 = "MLC60"
PLANNED_FOR_TBD = "TBD"
PLANNED_FOR_ANY = "Any"

# Max cycle time allowed is 50 milliseconds = 0.05 seconds
MAX_DIFF_TIMESTAMP = 0.05

# Value of an invalid object id
INVALID_ID = 255.0
INVALID_GenID_COH = 100
INVALID_ID_HA22 = 0
INVALID_ID_HA33 = 0

MAX_UINT16 = 65535

micro_second_to_seconds = 0.000001
centimeter_to_meter = 0.01

# ego vehicle Local Pose - Rotation Parameters Sig ( sig of yaw/pitch/roll) min, max default values from ICD
# ICD link:
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3340-0007b6c1
ICD_MinYawAng_RotationParam = -1.0
ICD_MaxYawAng_RotationParam = 0.05
ICD_DefaultPitchAng_RotationParam = -1.0
ICD_DefaultRollAng_RotationParam = -1.0

# ego vehicle Local Pose - Position Mean (mu of x,y,z) - min, max, default values from ICD
# ICD link:
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3330-0007b6c1
eVPosXMeanMin = -100000000.0
eVPosXMeanMax = 100000000
eVPosYMeanMin = -100000000.0
eVPosYMeanMax = 100000000
eVPosZMeanDefault = 0.0

# ego vehicle Translational Velocity Mean (mu of x, y, z) min, max default values from ICD
# ICD link:
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3279-0007b6c1
ICD_MinVelocityX = -100.0
ICD_MaxVelocityX = 100
ICD_MinVelocityY = -100.0
ICD_MaxVelocityY = 100
ICD_DefaultVelocityZ = 0.0

# ego vehicle Translational Acceleration mean (mu of x, y, z) min, max, default values from ICD
# ICD link:
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3299-0007b6c1
ICD_MinAccelerationX = -40.0
ICD_MaxAccelerationX = 15.0
ICD_MinAccelerationY = -40.0
ICD_MaxAccelerationY = 15.0
ICD_DefaultAccelerationZ = 0.0

# ego vehicle Angular Velocity mean ( mu of yaw, pitch, roll) min, max, default values from ICD
# ICD link:
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3289-0007b6c1
ICD_DefaultVelocityAngX = 0.0
ICD_DefaultVelocityAngY = 0.0
ICD_MinVelocityAngZ = -50.0
ICD_MaxVelocityAngZ = 50.0

# ego vehicle localPose- RotationParameters Mean ( mu of yaw, pitch, roll) min, max, default values from ICD
#    ICD link:
#    doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3341-0007b6c1
ICD_MinYawAng = -3.15
ICD_MaxYawAng = 3.15
ICD_DefaultYawAng_pitch = 0.0
ICD_DefaultYawAng_roll = 0.0

# ego vehicle position standard deviation icd values
# ICD link:
#     doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3333-0007b6c1
ICD_eVPosX_sd_min = -1.0
ICD_eVPosX_sd_max = 10.0
ICD_eVPosY_sd_min = -1.0
ICD_eVPosY_sd_max = 10.0
ICD_eVPosZ_sd_default = -1.0

# ego vehicle velocity angle sig default values and min and max
# ICD link:
#     doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3289-0007b6c1
ICD_DefaultVelocityAngXSig = -1.0
ICD_DefaultVelocityAngYSig = -1.0
ICD_MinVelocityAngZSig = -1.0
ICD_MaxVelocityAngZSig = 0.1

# ego vehicle angular acceleration mean icd value
# ICD link:
#     doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3311-0007b6c1
ICD_ego_angu_accel_x_mean_default = 0
ICD_ego_angu_accel_y_mean_default = 0
ICD_ego_angu_accel_z_mean_default = 0

# ego Vehicle Acceleration Trans x,y sig values between min-max values from ICD, z sig value should be default
# ICD link:
#   doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3299-0007b6c1
ICD_MinAccelerationTrans_SigX = -1
ICD_MaxAccelerationTrans_SigX = 0.01
ICD_MinAccelerationTrans_SigY = -1
ICD_MaxAccelerationTrans_SigY = 0.01
ICD_DefaultAccelerationTrans_SigZ = -1

# ego vehicle velocity standard deviation icd values
# ICD link:
#     doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3282-0007b6c1
ICD_ego_VelX_sd_min = -1.0
ICD_ego_VelX_sd_max = 1.0
ICD_ego_VelY_sd_min = -1.0
ICD_ego_VelY_sd_max = 1.0
ICD_ego_VelZ_sd_default = -1.0

# ego vehicle side slip angle standard deviation value from ICD
# ICD link:
#    doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3321-0007b6c1
ICD_ego_side_slip_angle_sd_min = -1.0
ICD_ego_side_slip_angle_sd_max = 0.05

# ego vehicle side slip angle mean values from ICD
# ICD link:
#    doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3320-0007b6c1
ICD_ego_side_slip_angle_mean_min = -3.15
ICD_ego_side_slip_angle_mean_max = 3.15

# ego vehicle angular acceleration standard deviation icd values
# ICD link:
#   doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3312-0007b6c1
ICD_ego_angu_accel_x_sd_default = -1.0
ICD_ego_angu_accel_y_sd_default = -1.0
ICD_ego_angu_accel_z_sd_default = -1.0

# ego motion state min and max values
# ICD link:
#    doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3323-0007b6c1
ICD_Probability_min = 0
ICD_Probability_max = 100

# Shape point state min, max values
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3487-0007b6c1
ICD_Shape_point_state_min = 0.0
ICD_Shape_point_state_max = 4.0

# ICD values for shape point coordinate:
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3489-0007b6c1
ICD_shape_point_pos_min = -50.0
ICD_shape_point_pos_max = 50.0

ICD_shape_point_pos_sd_min = 0.0
ICD_shape_point_pos_sd_max = 65535.0

#
difference_between_t6_and_t7 = 50000  # (microseconds)
additional_info = {
    "Class": {
        "Type": {"Version": "0.1", "ToolVersion": "xx"},
        "TargetObstacle": "Can",
        "DataProvider": "FDP_21P",
        "allowed_guardrail_gap": "2",
        "guardrail_gap_rate": "95",
        "rpARSx": "3.493",
        "rpARSy": "0",
        "camOffsetX": "1.7396",
        "camOffsetY": "0",
        "rpSRRFLx": "3.239",
        "rpSRRFLy": "0.880",
        "rpSRRFRx": "3.239",
        "rpSRRFRy": "-0.880",
        "rpSRRRRx": "-0.771",
        "rpSRRRRy": "-0.790",
        "rpSRRRLx": "-0.771",
        "rpSRRRLy": "0.790",
        "FtTpf39": {"ReferenceSensor": "ARS510"},
    }
}
# Default values for RMF
default0 = 0
default5 = 5
default17 = 17
default20 = 20
boundary_status_measured = 0
invalid_boundary_status = [1, 13, 14, 15]
invalid_array = 20
default_lane_value = 5
eSigStatus_invalid = 2
eSigStatus_Valid = 1
CAMERA_DEFAULT_LANE_BOUNDARY_RANGE = 0

# vdy input plugin ICD values
VDY_CycleCounterMin = 0.0
VDY_CycleCounterMax = 65535.0

VDY_MeasurementCounterMin = 0.0
VDY_MeasurementCounterMax = 65535.0

INVALID_OBJECT_ID_KB = 255
RANGE_CHECK_MIN = -999
RANGE_CHECK_MAX = 999

# default value for obstacle
MIN = 0.75
MAX = 3
UNDER_40M = 1.5

# RMF - The type of the LinearObject
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000032&urn=urn:telelogic::1-503e822e5ec3651e-O-3402-0007e74c
RMF_LT_UNKNOWN = 0
RMF_LT_LANE_MARKING = 1  # If lane boundary has this type the marking type is set
RMF_LT_GUARD_RAIL = 2
RMF_LT_VIRTUAL = 3  # If camera does not provide an entire lane boundary and it is created virtually.
RMF_LT_CURBSTONE = 4
RMF_LT_ROADEDGE = 5
# RMF_LT_ROAD_BOUNDARY = 6
# RMF_LT_BOTTS_DOTS = 7
RMF_LT_WALL = 8
# RMF_LT_HIGH_CURB = 9
# RMF_LT_LOW_CURB = 10
# RMF_LT_BARRIER = 11
# If part of lane boundary is extrapolated from neighboring camera lane boundary or from radar road boundary.
RMF_LT_EXTRAPOLATED = 12

# RMF - Colors
# Found There is no defined enumeration in the doors
RMF_LC_UNKNOWN = 0
RMF_LC_WHITE = 1
RMF_LC_YELLOW = 2
RMF_LC_RED = 3
RMF_LC_BLUE = 4

# Yaw angle check
YAW_ANGLE_MIN = -3.51
YAW_ANGLE_MAX = 3.51

# plausible values of height based on classification min, max
# reference : https://confluence-adas.zone2.agileci.conti.de/display/CEM200/Values+needed+for+TP+use+cases
height_min_max_for_class = {
    "probabilityCyclist": [0.5, 2.0],
    "probabilityCar": [0.5, 2.0],
    "probabilityTruck": [2.0, 4.0],
    "probabilityUnknown": [1.0, 2.5],
    "probabilityMotorbike": [1.0, 2.5],
    "probabilityPedestrian": [1.0, 2.75],
}

# Movement State
MOVEMENT_STATE_MOVING = 0
MOVEMENT_STATE_STOPPED = 6
MOVEMENT_STATE_STATIONARY = 1
MOVEMENT_STATE_ONCOMING = 2
MOVEMENT_STATE_CROSSING_LEFT = 3
MOVEMENT_STATE_CROSSING_RIGHT = 4

# Maintenance State for TPF ARS540BW11
MAIN_STATE_DELETED = 0
MAIN_STATE_NEW = 1
MAIN_STATE_MEASURED = 2
MAIN_STATE_PREDICTED = 3

UNCLASSIFIED = 7.0
UNCLASSIFIED_HONDA = 0
classific_dict = {
    "0.0": "Point",
    "1.0": "Car",
    "2.0": "Truck",
    "3.0": "Pedestrian",
    "4.0": "Motorcycle",
    "5.0": "Bicycle",
    "6.0": "Wide",
    "7.0": "Unclassified",
    "8.0": "Other Vehicles",
    "9.0": "TL",
    "10.0": "Max_diff_types",
}

classific_cam = {"0.0": "Bicycle", "1.0": "Car", "2.0": "Motorcycle", "3.0": "Pedestrian", "4.0": "Truck"}

# FTP Output array check
CAMERA_VALID_VALUES = [2, 3]
RADAR_VALID_VALUES = [1, 3]

# func_honda_tpf
PREDICTION_TIME_BLIND_SPOT = 5.0
OCCLUSION_TIME_BLIND_SPOT = 1.0
PREDICTED_STATE_HONDA = 1.0

PREDICTED_STATE_OBJECT = "predictedObject"

PREDICTED_STATE = 3.0
VALEO = "VALEO"
SRR = "SRR"
ARS = "ARS"
ARS540 = "ARS540"
VSPData = "VSPData"
APTIV_CAMERA = "Aptiv Camera"
APTIV_SRR = "Aptiv SRR"
NOT_AVAILABLE = "input missing"
TPF_PREFIX = "TPF"
RMF_PREFIX = "RMF"
SEF_PREFIX = "SEF"
EML_PREFIX = "EML"
VAL_PREFIX = "VAL"
COH_PREFIX = "COH"
ALCA_PREFIX = "ALCA"
BLOCKAGE = "Blockage"
VDY_PREFIX = "VDY"
ALL_SENSORS = "ALL_SENSORS"
ALL_CLUSTERS = "ALL_CLUSTERS"
ANY_CLUSTER = "ANY_CLUSTER"
OUTPUT_CLUSTERS = "OUTPUT_CLUSTERS"
INPUT = "Input"
OUTPUT = "Output"
HIP_HA22 = "HIP HA22"

base_string_input_plugin = "ARS540 Device.DPU_CEM200_50MS.CEM_ARS540_SyncRefARS540_0_DOITMeas."
base_string_output_plugin = "SIM VFB ALL.ARS540."

clusters_dict = {
    ARS540: {
        TPF_PREFIX: {
            INPUT: ["sig_m_fullObjectList.uiTimeStamp"],
            OUTPUT: [
                "tpfCartesianObjectList.sigHeader.eSigStatus",
                "sefAgpPolySetObjects.sSigHeader.eSigStatus",
                "sefAgpPolySetObjectsMos.sSigHeader.eSigStatus",
            ],
        },
        BLOCKAGE: {INPUT: ["sig_m_sensorBlockage.uiTimeStamp"], OUTPUT: ["valFovSignalList.sSigHeader.eSigStatus"]},
        VDY_PREFIX: {INPUT: ["sig_m_vehDyn.uiTimeStamp"], OUTPUT: ["emlEgoMotion.signalHeader.eSigStatus"]},
        RMF_PREFIX: {
            INPUT: [
                "sig_m_laneMatrix.uiTimeStamp",
                "sig_m_borderPolygons.uiTimeStamp",
                "sig_m_borderDistances.uiTimeStamp",
                "sig_m_roadEstimation.uiTimeStamp",
                "sig_m_roadType.uiTimeStamp",
                "sig_m_surfaceType.uiTimeStamp",
                "sig_m_roadSlope.uiTimeStamp",
                "sig_m_roadForks.uiTimeStamp",
                "sig_m_laneWidth.uiTimeStamp",
            ],
            OUTPUT: ["rmfRoadPatch.sSigHeader.eSigStatus"],
        },
    },
    APTIV_CAMERA: {
        TPF_PREFIX: {
            INPUT: ["sig_m_frontCameraObjectList.uiTimeStamp"],
            OUTPUT: ["tpfCartesianObjList.sigHeader.eSigStatus"],
        },
        RMF_PREFIX: {
            INPUT: ["sig_m_laneBoundariesLegacy.uiTimeStamp"],
            OUTPUT: ["rmfRoadPatch.sSigHeader.eSigStatus"],
        },
    },
    APTIV_SRR: {
        TPF_PREFIX: {
            INPUT: ["sig_m_recogSideRadar.uiTimeStamp"],
            OUTPUT: ["tpfCartesianObjectList.sigHeader.eSigStatus", "sefAgpPolySetObjects.sSigHeader.eSigStatus"],
        },
    },
}

# Lane boundary attributes
# Pattern Type - Camera
LANE_PATTERN_CAMERA = {0: "continous", 1: "dashed", 2: "dotted", 3: "other", 4: "no_pattern"}
# Pattern Type - CEM
LANE_PATTERN_CEM = {0: "unknown", 1: "no_pattern", 2: "continous", 3: "dashed", 4: "other", 5: "double", 6: "dotted"}
# Lane Color : Camera
LANE_COLOR_CAMERA = {0: "white", 1: "yellow", 2: "red", 3: "blue", 4: "green", 5: "other", 6: "none"}
# Lane Color : CEM
LANE_COLOR_CEM = {0: "unknown", 1: "white", 2: "yellow", 3: "red", 4: "blue", 5: "none"}

# ----------------------------------------------------------------------------------------------------------------------
# ARS540BW11 Safety Test Signal Manipulation
# when we manipulate at exact value at 3.0 time of mts time, we cannot have sudden change at output
BUFFER_TIME_ARS540BW11 = 0.05

START_TIME_ARS540BW11 = 17.0

END_TIME_TIMESTAMP_DECREASING = 17.0
END_TIME_FOUR_CYCLE_TIMESTAMP_DECREASING = 17.4

END_TIME_ONE_CYCLE_ARS540BW11 = 19.95
END_TIME_FOUR_CYCLE_ARS540BW11 = 19.95

TIME_FREEZE = "Time Freeze"
TIME_GREATER_THAN_T6 = "Time GT T6"
TIME_GREATER_THAN_500MS = "Time GT 500ms"
TIME_CONSECUTIVE = "Time Consecutive"
TIME_DECREASE = "Time Decrease"
INTENDED_RANGE = "Intended Range"
INPUT = "Input"
OUTPUT = "Output"
OUT_OF_RANGE = "Out of range"
CEM_FDP_21P = "CEM FDP 21P"
CEM_FDP_BASE = "CEM FDP BASE"
ALCA_FLAG = "ALCA FLAG"
ALCA_FLAG_RESET = "ALCA Flag Reset"

RADAR_INVALID = "Radar Invalid"
RADAR_FAILURE = "Radar Failure"
RADAR_STATUS = "Radar Status"
RADAR_BLOCKAGE = "Radar Blockage"

CAMERA_INVALID = "Camera Invalid"
CAMERA_FAILURE = "Camera Failure"

CEM_STATE = "CEM State"
SENSOR_STATE = "Sensor State"

CEM_FAILURE_STATE = "CEM Failure State"
TPF_CAMERA_TRIGGERED = "TPF CAMERA Triggered"

ODOMETRY = "Odometry"
ADCU_VDY = "ADCU_VDY"
ADCU_VDY_CLUSTER = "ADCU_VDY_CLUSTER"
SIG_STATUS = "eSIG STATUS"
ICC = "ICC"
RMF_DEFAULT_VALUE = "RMF Default Values"

RADAR = "Radar"
CAMERA = "Camera"

ONE_OF_FOUR = "-1 of 4"
TWO_OF_FOUR = "-2 of 4"
THREE_OF_FOUR = "-3 of 4"
FOUR_OF_FOUR = "-4 of 4"

ONE_OF_THREE = "-1 of 3"
TWO_OF_THREE = "-2 of 3"
THREE_OF_THREE = "-3 of 3"

TIMESTAMP_TEST = (
    TIME_FREEZE + ONE_OF_FOUR,
    TIME_FREEZE + TWO_OF_FOUR,
    TIME_FREEZE + THREE_OF_FOUR,
    TIME_FREEZE + FOUR_OF_FOUR,
    TIME_CONSECUTIVE + ONE_OF_FOUR,
    TIME_CONSECUTIVE + TWO_OF_FOUR,
    TIME_CONSECUTIVE + THREE_OF_FOUR,
    TIME_CONSECUTIVE + FOUR_OF_FOUR,
    TIME_GREATER_THAN_T6 + ONE_OF_FOUR,
    TIME_GREATER_THAN_T6 + TWO_OF_FOUR,
    TIME_GREATER_THAN_T6 + THREE_OF_FOUR,
    TIME_GREATER_THAN_T6 + FOUR_OF_FOUR,
)

SIG_STATUS_TEST = (
    RADAR_INVALID + ONE_OF_FOUR,
    RADAR_INVALID + TWO_OF_FOUR,
    RADAR_INVALID + THREE_OF_FOUR,
    RADAR_INVALID + FOUR_OF_FOUR,
    CAMERA_INVALID + ONE_OF_FOUR,
    CAMERA_INVALID + TWO_OF_FOUR,
    CAMERA_INVALID + THREE_OF_FOUR,
    CAMERA_INVALID + FOUR_OF_FOUR,
)

INTENDED_RANGE_TEST = (
    INTENDED_RANGE + ONE_OF_FOUR,
    INTENDED_RANGE + TWO_OF_FOUR,
    INTENDED_RANGE + THREE_OF_FOUR,
    INTENDED_RANGE + FOUR_OF_FOUR,
)

OUTPUT_INTENDED_RANGE_TEST = (
    OUTPUT + " " + INTENDED_RANGE + ONE_OF_FOUR,
    OUTPUT + " " + INTENDED_RANGE + TWO_OF_FOUR,
    OUTPUT + " " + INTENDED_RANGE + THREE_OF_FOUR,
    OUTPUT + " " + INTENDED_RANGE + FOUR_OF_FOUR,
)

RADAR_FAILURE_TEST = (RADAR_FAILURE + ONE_OF_THREE, RADAR_FAILURE + TWO_OF_THREE, RADAR_FAILURE + THREE_OF_THREE)

CAMERA_FAILURE_TEST = (CAMERA_FAILURE + ONE_OF_THREE, CAMERA_FAILURE + TWO_OF_THREE, CAMERA_FAILURE + THREE_OF_THREE)

STATIC_OBJECT = "Static_Object"
OBJECT = "Object"

OUTPUT_NO_CONTRIBUTION_TEST = (
    TIME_FREEZE + ONE_OF_FOUR,
    TIME_CONSECUTIVE + ONE_OF_FOUR,
    TIME_GREATER_THAN_T6 + ONE_OF_FOUR,
    INTENDED_RANGE + ONE_OF_FOUR,
    RADAR_INVALID + ONE_OF_FOUR,
    CAMERA_INVALID + ONE_OF_FOUR,
)

OUTPUT_SENSOR_STATE_TEST = (
    TIME_FREEZE + TWO_OF_FOUR,
    TIME_FREEZE + THREE_OF_FOUR,
    TIME_FREEZE + FOUR_OF_FOUR,
    TIME_CONSECUTIVE + TWO_OF_FOUR,
    TIME_CONSECUTIVE + THREE_OF_FOUR,
    TIME_CONSECUTIVE + FOUR_OF_FOUR,
    TIME_GREATER_THAN_T6 + TWO_OF_FOUR,
    TIME_GREATER_THAN_T6 + THREE_OF_FOUR,
    TIME_GREATER_THAN_T6 + FOUR_OF_FOUR,
    INTENDED_RANGE + TWO_OF_FOUR,
    INTENDED_RANGE + THREE_OF_FOUR,
    INTENDED_RANGE + FOUR_OF_FOUR,
    RADAR_INVALID + TWO_OF_FOUR,
    RADAR_INVALID + THREE_OF_FOUR,
    RADAR_INVALID + FOUR_OF_FOUR,
    CAMERA_INVALID + TWO_OF_FOUR,
    CAMERA_INVALID + THREE_OF_FOUR,
    CAMERA_INVALID + FOUR_OF_FOUR,
)

# bellow to be mentioned values that you don't want to find in output
SENSOR_CONTRIBUTION = {
    ARS540: {TPF_PREFIX: [1.0, 3.0, 9.0, 11.0], SEF_PREFIX: [0, 1], VDY_PREFIX: [1], RMF_PREFIX: [2249]},
    APTIV_CAMERA: {
        TPF_PREFIX: [8.0, 9.0, 10.0, 11.0],
        RMF_PREFIX: [2243],
    },
    APTIV_SRR: {
        TPF_PREFIX: [2.0, 3.0, 10.0, 11.0],
        SEF_PREFIX: [32834],
    },
    OUTPUT_CLUSTERS: {OUTPUT_CLUSTERS: [0, 2]},
}

INPUT_SIGNAL_MODIFICATION = {
    CAMERA_INVALID: [2.0],
    RADAR_INVALID: [2.0],
    TIME_GREATER_THAN_T6: [4368684987.0, 4368.0],
    INTENDED_RANGE: [5.0],
    TIME_CONSECUTIVE: [7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.0],
    TIME_FREEZE: [0.0],
    RADAR_FAILURE: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 255.0],
    CAMERA_FAILURE: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
    STATIC_OBJECT: [100.0],
    CEM_STATE: [2.0],
    TPF_CAMERA_TRIGGERED: [1.0],
    RADAR_BLOCKAGE: [0.0, 1.0],
}

DESCRIPTION = {
    OUTPUT + " " + INTENDED_RANGE: "For one or more signals of CEM Output Clusters not in intended range,"
    "the CEM-SW shall have Temporary Failure State",
    ONE_OF_FOUR: "For the Input Cluster of a sensor manipulated check for no contribution from it.",
    TWO_OF_FOUR: "For one or more Input Cluster's of a sensor manipulated for >= 4 cycles, \n"
    "check that Sensor Output State = Degraded",
    THREE_OF_FOUR: "For all the Input Cluster's of a sensor manipulated for >1 to <4 cycles, \n"
    "check that Sensor Output State = Degraded",
    FOUR_OF_FOUR: "For all the Input Cluster's of a sensor manipulated for >=4 cycles, \n"
    "check that Sensor Output State = Failed",
    ONE_OF_THREE: "For the Input Cluster of a sensor manipulated check for no contribution from it.",
    TWO_OF_THREE: "For all the Input Cluster's of a sensor manipulated for >1 to <4 cycles, \n"
    "check that Sensor Output State = Degraded",
    THREE_OF_THREE: "For all the Input Cluster's of a sensor manipulated for >=4 cycles, \n"
    "check that Sensor Output State = Failed",
    STATIC_OBJECT: "Check when input static objects are over drivable or underdrivable, they are not"
    "reported as static objects at CEM output",
    CEM_STATE: "Check for CEM state to be in Normal State",
    SENSOR_STATE: "Check for Sensor State to be Available",
    TPF_CAMERA_TRIGGERED: "Check if ADCAM contribution for any Object in Objectlist, "
    "when its SDMFlag is equal to Triggered.",
}

CAMERA_CATCH_UPDATE_RATE = 56
RADAR_CATCH_UPDATE_RATE = 55
RADAR_LEFT_CATCH_UPDATE_RATE = 55
RADAR_RIGHT_CATCH_UPDATE_RATE = 55
RADAR_REAR_LEFT_CATCH_UPDATE_RATE = 55
RADAR_REAR_RIGHT_CATCH_UPDATE_RATE = 55

SENSORS_UPDATE_RATE = [
    CAMERA_CATCH_UPDATE_RATE,
    RADAR_CATCH_UPDATE_RATE,
    RADAR_LEFT_CATCH_UPDATE_RATE,
    RADAR_RIGHT_CATCH_UPDATE_RATE,
    RADAR_REAR_LEFT_CATCH_UPDATE_RATE,
    RADAR_REAR_RIGHT_CATCH_UPDATE_RATE,
]

signal_dict_ARS420HA22_Object = {
    "accelX": "AccelerationX",
    "accelY": "AccelerationY",
    "age": "Age",
    "boxHeight": "BoxHeight",
    "boxLength": "BoxLength",
    "boxLengthVar": "BoxLengthVar",
    "boxWidth": "BoxWidth",
    "boxWidthVar": "BoxWidthVar",
    "boxYawAngle": "BoxYawAngle",
    "boxYawAngleVar": "BoxYawAngleVar",
    "brakeLight": "BrakeLight",
    "cameraCatch": "CameraCatch",
    "classification": "Classification",
    "confidence": "Confidence",
    "frontCtrCatch": "FrontCenterCatch",
    "frontLeftRadarCatch": "FrontLeftCatch",
    "frontRightRadarCatch": "FrontRightCatch",
    "id": "ID",
    "laneAssignment": "LaneAssignment",
    "positionX": "PositionX",
    "positionXVar": "PositionXVar",
    "positionY": "PositionY",
    "positionYVar": "PositionYVar",
    "predictedObject": "PredictedObject",
    "quickMovement": "QuickMovement",
    "rearLeftRadarCatch": "RearLeftCatch",
    "rearRightRadarCatch": "RearRightCatch",
    "referencePoint": "ReferencePoint",
    "turnIndicator": "TurnIndicator",
    "velocityX": "VelocityX",
    "velocityXVar": "VelocityXVar",
    "velocityY": "VelocityY",
    "velocityYVar": "VelocityYVar",
}

signal_dict_ARS420HA22_Obstacle = {
    "id": "ID",
    "age": "Age",
    "confidence": "Confidence",
    "frontCtrCatch": "FrontCtrCatch",
    "frontLeftRadarCatch": "FrontLeftRadarCatch",
    "frontRightRadarCatch": "FrontRightRadarCatch",
    "positionX": "PositionX",
    "positionXVar": "PositionXVar",
    "positionY": "PositionY",
    "positionYVar": "PositionYVar",
    "predictedObject": "PredictedObstacle",
    "rearLeftRadarCatch": "RearLeftRadarCatch",
    "velocityX": "VelocityX",
    "velocityXVar": "VelocityXVar",
    "velocityY": "VelocityY",
    "velocityYVar": "VelocityYVar",
    "rearRightRadarCatch": "RearRightRadarCatch",
}


# BMW SEF Measurement Status enum values
SEF_VERTEX_MEASURED = 0
SEF_VERTEX_INTERPOLATED = 1
SEF_VERTEX_HYPOTHESIS = 2

# BMW SEF region of interest
REGION_OF_INTEREST_X_MIN = 0
REGION_OF_INTEREST_X_MAX = 120
REGION_OF_INTEREST_Y_MIN = -20
REGION_OF_INTEREST_Y_MAX = 20

# BMW EML Handler Status
HANDLER_STATUS_CANCELED = 4

# tolerance for boundary length difference between cem and camera
length_difference_tolerance = 6.5

rmf_lane_width_min = [2, 4.6]
rmf_lane_width_max = [4.6, 2]

rmf_virtual_lane_width = {"min": 2, "max": 4.6}
BW_CAMERA_SIGNAL_PREFIX = "ARS540 Device.FCU.FCU_Lane_Boundaries."
# BMW SEF sensors ID
ARS540_SENSOR_ID = 2249
APTIV_SRR_SENSOR_ID = 32834

EURO = "EURO"
USA = "USA"
KOREA = "Korea"
CHINA = "China"
JAPAN = "Japan"

# vehicle dimensions
BMW_G11_WIDTH = 1.902
BMW_G11_LENGTH_FROM_REAR_BUMPER = 3.95

# Reports Constants
BW_SENSOR_PEDESTRIAN_CLASS = "probClassPedestrian"
BW_SENSOR_BICYCLE_CLASS = "probClassBicycle"
BW_SENSOR_CAR_CLASS = "probClassCar"
BW_SENSOR_TRUCK_CLASS = "probClassTruck"
BW_SENSOR_UNKNOWN_CLASS = "probClassUnknown"
BW_SENSOR_MOTOR_CYCLE_CLASS = "probClassMotorcycle"
BW_SENSOR_ANIMAL_CLASS = "probClassAnimal"
BW_SENSOR_HAZARD_CLASS = "probClassHazzard"

BW_SENSOR_CLASS = [
    BW_SENSOR_PEDESTRIAN_CLASS,
    BW_SENSOR_BICYCLE_CLASS,
    BW_SENSOR_CAR_CLASS,
    BW_SENSOR_TRUCK_CLASS,
    BW_SENSOR_UNKNOWN_CLASS,
    BW_SENSOR_MOTOR_CYCLE_CLASS,
    BW_SENSOR_ANIMAL_CLASS,
    BW_SENSOR_HAZARD_CLASS,
]

BW_CEM_PEDESTRIAN_CLASS = "probabilityPedestrian"
BW_CEM_BICYCLE_CLASS = "probabilityCyclist"
BW_CEM_CAR_CLASS = "probabilityCar"
BW_CEM_TRUCK_CLASS = "probabilityTruck"
BW_CEM_UNKNOWN_CLASS = "probabilityUnknown"
BW_CEM_MOTOR_CYCLE_CLASS = "probabilityMotorbike"

BW_CEM_CLASS = [
    BW_CEM_PEDESTRIAN_CLASS,
    BW_CEM_BICYCLE_CLASS,
    BW_CEM_CAR_CLASS,
    BW_CEM_TRUCK_CLASS,
    BW_CEM_UNKNOWN_CLASS,
    BW_CEM_MOTOR_CYCLE_CLASS,
]

SYS100_ANIMAL_CLASS = "probabilityAnimal"
SYS100_CAR_CLASS = "probabilityCar"
SYS100_BICYCLE_CLASS = "probabilityCyclist"
SYS100_EMERGENCY_VEHICLE_CLASS = "probabilityEmergencyVehicle"
SYS100_MOTOR_CYCLE_CLASS = "probabilityMotorbike"
SYS100_OTHER_VEHICLE_CLASS = "probabilityOtherVehicle"
SYS100_PEDESTRIAN_CLASS = "probabilityPedestrian"
SYS100_TRUCK_CLASS = "probabilityTruck"
SYS100_UNKNOWN_CLASS = "probabilityUnknown"

SYS100_CLASS = [
    SYS100_ANIMAL_CLASS,
    SYS100_CAR_CLASS,
    SYS100_BICYCLE_CLASS,
    SYS100_EMERGENCY_VEHICLE_CLASS,
    SYS100_MOTOR_CYCLE_CLASS,
    SYS100_OTHER_VEHICLE_CLASS,
    SYS100_PEDESTRIAN_CLASS,
    SYS100_TRUCK_CLASS,
    SYS100_UNKNOWN_CLASS,
]

MFC527_CLASS = [
    SYS100_CAR_CLASS,
    SYS100_BICYCLE_CLASS,
    SYS100_MOTOR_CYCLE_CLASS,
    SYS100_OTHER_VEHICLE_CLASS,
    SYS100_PEDESTRIAN_CLASS,
    SYS100_TRUCK_CLASS,
    SYS100_UNKNOWN_CLASS,
]

# doors link for signal min max
# doors://rbgs854a:40000/?version=2&prodID=0&view=0000000b&urn=urn:telelogic::1-503e822e5ec3651e-O-988-0007e749
BW11_RADAR_DEFAULT_ROAD_BOUNDARY_RANGE = 0
BW11_RMF_BOUNDARY_DEFAULT = 0
min_subsistence_probability = 50

IDEAL_FOV_SIGNAL_STRUCUTURE = "VAL_IFOV"
DEGRADATION_FOV_SIGNAL_STRUCTURE = "VAL_SensorDegradation"

# Lane Assignment
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-4312-0007b6c1
# UNKNOWN_REGION: Region ahead or behind the range of Lane description
# EGO: Lane within which Ego vehicle is driving
# L1: Lane immediate left to the Ego lane
# R1: Lane immediate right to the Ego lane
# L2: Lane immediate left to L1 lane
# R2: Lane immediate right to R1 lane
NOT_ASSIGNED = 0  # can not be assigned to a lane
EGO_LANE = 1  # EGO
NEXT_LANE_L = 2  # L1
NEXT_LANE_R = 3  # R1
NEXT_NEXT_LANE_L = 4  # L2
NEXT_NEXT_LANE_R = 5  # R2
LANE_NOT_PRESENT = 6  # can be assigned, but lane is not present in list

STATIC_OBJECT_SIGNALS_ARS = [
    "ARS540 Device.ClassCycle.MOS_FullObjectListMeas.obj[{}].probObstrOver",
    "ARS540 Device.ClassCycle.MOS_FullObjectListMeas.obj[{}].probObstrUnder",
]
STATIC_OBJECT_SIGNALS_ARS_VSP = [
    "VSPData.ClassCycle.MOS_FullObjectListMeas.obj[{}].probObstrOver",
    "VSPData.ClassCycle.MOS_FullObjectListMeas.obj[{}].probObstrUnder",
]
STATIC_OBJECT_SIGNALS_SRR = []
TPF_CAMERA_TRIGGERED_SIGNALS = ["SIM VFB ALL.FDP_Base.p_TpfOutputIf.aObject[{}].contributingSensors"]

# MeasurementCounter signals from sensors
MOS_COUNTER = "ARS540 Device.ClassCycle.MOS_FullObjectListMeas.sigHeader.uiMeasurementCounter"
MOS_COUNTER_VSP = "VSPData.ClassCycle.MOS_FullObjectListMeas.sigHeader.uiMeasurementCounter"
CAM_COUNTER = "ARS540 Device.SW_A53_0.FCU_ADCAM_ObjectList.sigHeader.uiMeasurementCounter"
CAM_COUNTER_VSP = "VSPData.FCU.FCU_ADCAM_ObjectList.sigHeader.uiMeasurementCounter"
SRR_COUNTER = "ARS540 Device.SW_A53_0.FCU_SRR_ObjectList.sigHeader.uiMeasurementCounter"
SRR_COUNTER_VSP = "VSPData.FCU.FCU_SRR_ObjectList.sigHeader.uiMeasurementCounter"
LANE_COUNTER = "ARS540 Device.FCU.FCU_Lane_Boundaries.sigHeader.uiMeasurementCounter"
LANE_COUNTER_VSP = "VSPData.FCU.FCU_Lane_Boundaries.sigHeader.uiMeasurementCounter"
ROAD_COUNTER = "ARS540 Device.ClassCycle.RIC_RoadEstimationMeas.sigHeader.uiMeasurementCounter"
ROAD_COUNTER_VSP = "VSPData.ClassCycle.RIC_RoadEstimationMeas.sigHeader.uiMeasurementCounter"
ROAD_TYPE_COUNTER = "ARS540 Device.ClassCycle.RIC_RoadTypeMeas.sigHeader.uiMeasurementCounter"
SEP2_COUNTER = "ARS540 Device.ClassCycle.SEP2_RadarFreespaceMeas.sigHeader.uiMeasurementCounter"
SEP2_COUNTER_VSP = "VSPData.ClassCycle.SEP2_RadarFreespaceMeas.sigHeader.uiMeasurementCounter"
VDY_COUNTER = "ARS540 Device.AlgoVehCycle.VDY_VehDynMeas.sigHeader.uiMeasurementCounter"
RPM1_COUNTER = "ARS540 Device.DataProcCycle.RPM1_SensorDampingMeas.sigHeader.uiMeasurementCounter"
RPM2_COUNTER = "ARS540 Device.ClassCycle.RPM2_SensorBlockageMeas.sigHeader.uiMeasurementCounter"


class Ars540bw11Constants:
    """Class containing constants specific to ARS540BW11."""

    SAFETY_TEST_XML_PATH = r"data\ars540bw11\safety_test"

    DYNAMIC_PROPERTY_STOPPED_START_SPEED = 1.8

    cem_validity = "CEM_Validity"
    cem_tpf = "CEM_Traffic_Participant_Fusion"
    cem_rmf = "CEM_Road_Model_Fusion"
    cem_sef = "CEM_Freespace_and_Static_Environemnt"
    cem_eml = "CEM_Ego_Motion_Localisation"
    cem_coh = "CEM_Coherence"

    sensor_mos = "Sensor_MOS_FullObjectListMeas"
    sensor_cam = "Sensor_FCU_ADCAM_ObjectList"
    sensor_srr = "Sensor_FCU_SRR_ObjectList"
    sensor_lane = "Sensor_FCU_Lane_Boundaries"
    sensor_ric_road = "Sensor_RIC_RoadEstimationMeas"
    sensor_sep2_radar = "Sensor_SEP2_RadarFreespaceMeas"
    sensor_vdy = "Sensor_VDY_VehDynMeas"
    adcam_fcu_meas_counter = "ADCAM_FCU_Meas_Counter"
    ars_road_meas_counter = "ARS_ROAD_Meas_Counter"
    camera_obj_counter = "ADCAM_Obj_Meas_Counter"
    fcu_navi_meas_counter = "FCU_Navi_MeasCounter"
    sig_status = "eSigStatus"
    cycle_counter = "cycle_counter"
    timestamp_fcu = "TimeStampFCU"
    timestamp_radar_road = "TimestampRadar"

    cem_base_string_map_to_icd = {
        cem_validity: "SIM VFB ALL.VAL.pValOutput",
        cem_tpf: "SIM VFB ALL.TPF2.tpObjectList",
        cem_rmf: "SIM VFB ALL.RMF.pRmfFusionIf_postCoh",
        cem_sef: "SIM VFB ALL.SEF.SefOutput",
        cem_eml: "SIM VFB ALL.EML.EmlOutput.egoVehKinematic",
        cem_coh: "SIM VFB ALL.COH.associationInterface",
    }

    sensor_base_string_map_to_icd = {
        sensor_mos: "ARS540 Device.ClassCycle.MOS_FullObjectListMeas",
        sensor_cam: "ARS540 Device.FCU.FCU_ADCAM_ObjectList",
        sensor_srr: "ARS540 Device.FCU.FCU_SRR_ObjectList",
        sensor_lane: "ARS540 Device.FCU.FCU_Lane_Boundaries",
        sensor_ric_road: "ARS540 Device.ClassCycle.RIC_RoadEstimationMeas",
        sensor_sep2_radar: "ARS540 Device.ClassCycle.SEP2_RadarFreespaceMeas",
        sensor_vdy: "ARS540 Device.AlgoVehCycle.VDY_VehDynMeas",
    }

    cluster_signal_prefix = {
        "INPUT_Clusters": [
            sensor_mos,
            sensor_cam,
            sensor_srr,
            sensor_lane,
            sensor_ric_road,
            sensor_sep2_radar,
            sensor_vdy,
        ],
        "OUTPUT_Clusters": [cem_validity, cem_tpf, cem_rmf, cem_sef, cem_eml, cem_coh],
    }
    CEM_STATE_OK = 2
    FAILURE_STATE_OK = 0

    SIG_STATUS_INVALID = 2
    SIG_STATUS_OK = 1
    SIG_STATUS_INIT = 0
    INCREASING_DIFFERENCE = 0

    # Contributing sensor values
    CONTRIBUTING_PREDICTED = 0
    CONTRIBUTING_ONLY_ARS = 1
    CONTRIBUTING_ONLY_SRR = 2
    CONTRIBUTING_ARS_SRR = 3
    CONTRIBUTING_ONLY_CAM = 8
    CONTRIBUTING_CAM_ARS = 9
    CONTRIBUTING_CAM_SRR = 10
    CONTRIBUTING_CAM_ARS_SRR = 11

    # cem initialization phase
    CEM_INIT_PHASE = 2
    # 50ms is considered between T6 and component Timestamp
    T7_T6_DIFFERENCE = 50000
    # the max difference is 2 cycles = 50ms * 3 = 100ms with 5% tolerance
    MIN_TIMESTAMP_TO_T7_DIFFERENCE = 150 - (5 * 150 / 100)
    MAX_TIMESTAMP_TO_T7_DIFFERENCE = 150 + (5 * 150 / 100)

    # TODO: Discuss with Venkatesh about this constants - maybe we can move them in another!!!
    OBJECT_IDENTIFIER = "Object Identifier"
    TEST_STATUS = "_TestStatus_"
    OVERALL_RESULT = "Overall_Result"
    TEST_DATE = "_TestDate_"

    POE = "PoE"  # probability of existence of ftp or rtp
    poe_integer_value = 0.5
    poe_percentage_value = 50.0

    # signal name for T6
    T6_SIGNAL = "SIM VFB ALL.EMF.EmfGlobalTimestamp.SigHeader.uiTimeStamp"

    SENSORID_ARS540 = 2249
    SENSORID_SRR_APTIV = 32834
    SENSORID_MFC_APTIV = 2243

    class RMF:
        # NEW RMF Signals
        lane_segment_lanes = "lane_segment_lanes"
        numLeftBoundaryParts = "numLeftBoundaryParts"
        numRightBoundaryParts = "numRightBoundaryParts"
        left_boundary = "left_boundary"
        right_boundary = "right_boundary"
        linear_objects_data = "linear_objects_data"
        center_line_start_index = "centerLine_startIndex"
        center_line_end_index = "centerLine_endIndex"
        start_Index = "startIndex"
        end_Index = "endIndex"
        points_data = "points_data"
        association_boundary_continuity = "association_boundary_continuity"
        boundary_continuity_start_index = "boundary_continuity_start_index"
        boundary_continuity_end_index = "boundary_continuity_end_index"
        boundary_continuity_value = "boundary_continuity_value"
        NumberOfOccupiedPositions = "NumberOfOccupiedPositions"
        num_Of_Lanes = "numOfLanes"
        num_of_linear_objects = "numLinearObjects"
        numBoundaryContinuity = "numBoundaryContinuity"
        FDP_BW11_Ego_Lane_Index = "FDP_BW11_Ego_Lane_Index"
        ego_lane_index = "Ego_lane_index"
        FDP_BW11_Ego_Road_Index = "FDP_BW11_Ego_Road_Index"
        ego_road_index = "Ego_road_index"
        num_of_points = "numOfPoints"
        leftLane = "leftLane"
        rightLane = "rightLane"
        road_segments = "Road_segments"
        number_of_road_segments = "numOfRoadSeg"
        road_type = "RoadType"
        rmf_lane_type = "type"
        rmf_lane_color = "color"
        rmf_lane_width = "width"
        rmf_lane_marking = "marking"
        timestamp_rmf = "TimestampRMF"
        direction = "Direction"
        road_boundary_age = 0.5
        fX = "fX"
        fY = "fY"
        id = "ID"
        Mpp_segment = "isMpp"
        boundary_lifetime = 0.5
        probability_no_crossing = 50
        association_boundary_continuity_default_range = 2000
        number_of_associations_boundary_continuity_arrays = 40
        invalid_data_qualifier = 1
        ego_road_index_default = 10
        nr_road_seg_default = 0
        distance_crossroad_min = 1
        distance_crossroad_max = 499
        index_default = 2000
        mpp_true = 1
        min_points_centerline = 2

        # tolerance for road boundary length difference between cem and radar/RROI
        road_boundary_tolerance = 10

        # minimum length considered for Camera input is 12 meters for <Extrapolated Radar> function
        min_length_camera = 12

        # Camera inputs that are not considered for <Extrapolated Radar> function,
        # only painted markings are taken in consideration
        camera_markings = [4, 9, 10]

        sensor_associations = "sensorAssociations"
        maintenance_state = "maintenanceState"
        associations = "associations."

        # camera signals
        camera_left_y_coordinate = "FCULeftCoefficient0"
        camera_right_y_coordinate = "FCURightCoefficient0"
        camera_next_right_y_coordinate = "FCUNextRightCoefficient0"
        camera_lane_counter = "ADCAM_FCU_Meas_Counter"
        camera_left_boundary = "CameraLeftBoundary"
        camera_right_boundary = "CameraRightBoundary"
        camera_status_left_boundary = "StatusMeasEgoLeftBoundary"
        camera_status_right_boundary = "StatusMeasEgoRightBoundary"
        camera_next_left_boundary = "CameraNextLeftBoundary"
        camera_next_right_boundary = "CameraNextRightBoundary"
        camera_status_next_left_boundary = "StatusMeasNextLeftBoundary"
        camera_status_next_right_boundary = "StatusMeasNextRightBoundary"
        camera_left_lane_color = "ColorLaneMarkingEgoLeft"
        camera_right_lane_color = "ColorLaneMarkingEgoRight"
        camera_left_lane_width = "LaneMarkingWidthEgoLeft"
        camera_right_lane_width = "LaneMarkingWidthLaneEgoRight"
        camera_left_lane_type = "TypeLaneMarkingEgoLeft"
        camera_right_lane_type = "TypeLaneMarkingEgoRight"
        camera_left_boundary_subsistence = "SubsistenceProbabilityEgoLeftBoundary"
        camera_right_boundary_subsistence = "SubsistenceProbabilityEgoRightBoundary"
        camera_data_qualifier = "Event_data_qualifier"

        # radar signals
        radar_road_confidence = "RoadConfidence"
        radar_left_boundary_range = "RadarLeftBoundaryRange"
        radar_right_boundary_range = "RadarRightBoundaryRange"
        radar_left_y_coordinate = "LeftLateralOffset"
        radar_right_y_coordinate = "RightLateralOffset"
        radar_road_counter = "ARS_ROAD_Meas_Counter"
        radar_roadtype_counter = "ARS_ROAD_TYPE_Meas_Counter"
        navimap_syncref_counter = "NaviMap_Meas_Counter"
        radar_left_border_type = "LeftBorderType"
        radar_right_border_type = "RightBorderType"

        # OLD RMF Signals
        lane_hypothesis_lanes = "lane_hypothesis_lanes"
        road_hypothesis = "Road_hypothesis"
        line = "line"
        num_of_lines = "numLines"
        points_from = "from"
        points_to = "to"
        center_line = "centerLine"
        geometries_lines_data = "geometries_lines_data"
        lines_points_index = "lines_points_index"

        # RMF - The type of the LinearObject
        RMF_LinearType_UNKNOWN = 1
        RMF_LinearType_LANE_MARKING = 2  # If lane boundary has this type the marking type is set
        RMF_LinearType_GUARD_RAIL = 3
        RMF_LinearType_VIRTUAL = 4  # If camera does not provide an entire lane boundary and it is created virtually.
        RMF_LinearType_CURBSTONE = 5
        RMF_LinearType_ROADEDGE = 6
        RMF_LinearType_WALL = 7
        # TODO: Check Extrapolated linear object type for ARS540BW11 is 10 or 12???
        RMF_LinearType_EXTRAPOLATED = 12

        rmf_liner_object_type = {
            0: "Invalid",
            1: "UNKNOWN",
            2: "LANEMARKING",
            3: "GUARDRAIL",
            4: "VIRTUAL",
            5: "CURBSTONE",
            6: "ROADEDGE",
            7: "WALL",
            8: "DELINEATOR",
            9: "PYLON",
        }

    class KPI:
        # Round value for EML KPI tests
        EML_KPI_ROUND_WITH_VALUE = 2

    class SYNCHRONIZE:
        ARS540BW11_SYNCHRONIZE_SAFETY = {
            TPF_PREFIX: {
                MOS_COUNTER: ["ARS_measurement_counter"],
                CAM_COUNTER: ["CAM_measurement_counter"],
                SRR_COUNTER: ["SRR_measurement_counter"],
                RPM2_COUNTER: ["RPM2_measurement_counter"],
                MOS_COUNTER_VSP: ["ARS_measurement_counter"],
                CAM_COUNTER_VSP: ["CAM_measurement_counter"],
                SRR_COUNTER_VSP: ["SRR_measurement_counter"],
            },
            SEF_PREFIX: {
                MOS_COUNTER: ["SIM VFB ALL.ARS540.syncRef.sig_m_fullObjectList.uiMeasurementCounter"],
                MOS_COUNTER_VSP: ["SIM VFB ALL.ARS540.syncRef.sig_m_fullObjectList.uiMeasurementCounter"],
                SEP2_COUNTER: ["SIM VFB ALL.ARS540.syncRef.sig_m_radarFreespace.uiMeasurementCounter"],
                # SRR_COUNTER: ['SIM VFB ALL.SRR_Aptiv.syncRef.sig_m_recogSideRadar.uiMeasurementCounter']
            },
            RMF_PREFIX: {
                ROAD_COUNTER: ["SIM VFB ALL.ARS540.syncRef.sig_m_roadEstimation.uiMeasurementCounter"],
                ROAD_TYPE_COUNTER: ["SIM VFB ALL.ARS540.syncRef.sig_m_roadType.uiMeasurementCounter"],
                LANE_COUNTER: ["SIM VFB ALL.MFC_Aptiv.syncRef.sig_m_laneBoundariesLegacy.uiMeasurementCounter"],
            },
            VDY_PREFIX: {VDY_COUNTER: ["SIM VFB ALL.ARS540.syncRef.sig_m_vehDyn.uiMeasurementCounter"]},
            EML_PREFIX: {VDY_COUNTER: ["SIM VFB ALL.ARS540.syncRef.sig_m_vehDyn.uiMeasurementCounter"]},
        }

    class VAL:
        adcam_sig_status = "ADCAM_sig_status"
        ars_sig_status = "ARS_sig_status"
        srr_sig_status = "SRR_sig_status"
        adcam_meas_counter = "ADCAM_measCounter"
        ars_meas_counter = "ARS540_measCounter"
        srr_meas_counter = "SRR_measCounter"
        mfc_sync_ref_meas_counter = "MFC_syncRef_meas_counter"
        ars_sync_ref_meas_counter = "ARS_syncRef_meas_counter"
        srr_sync_ref_meas_counter = "SRR_syncRef_meas_counter"

    class COH:
        CAMERA_LANE_MARKING_TYPE = {
            "UNKNOWN": 0,
            "DASHED": 1,
            "SOLID": 2,
            "DOTTED": 3,
            "ROAD_EDGE": 4,
            "DOUBLE_LINE_CROSS": 5,
            "DOUBLE_LINE_UNCROSS": 6,
            "MULTIPLE_LINES_CROSS": 7,
            "MULTIPLE_LINES_UNCROSS": 8,
            "CURB": 9,
            "SNOW_EDGE": 10,
            "STRUCTURED": 11,
            "NOT_AVAILABLE": 13,
            "ERROR": 14,
            "SIGNAL_NOT_FILLED": 15,
        }

        RADAR_BORDER_TYPE = {"UNKNOWN": 0, "GUARDRAIL": 1, "OTHER": 2}

        LANE_ASSIGN_CAM = {
            "UNDEFINED": 1,
            "EGO": 2,
            "LEFT": 3,
            "RIGHT": 4,
            "LEFT_BEYOND": 5,
            "RIGHT_BEYOND": 6,
            "ON_PAVE_LEFT": 7,
            "ON_PAVE_RIGHT": 8,
            "ON_BIKE_LANE_LEFT": 9,
            "ON_BIKE_LANE_RIGHT": 10,
            "INVALID": 255,
        }

        EGO = "ego"
        LEFT = "left"
        RIGHT = "right"

        UNKNOWN_DIRECTION = 0
        DRIVING_DIRECTION = 1
        OPPOSITE_DIRECTION = 2
        BIDIRECTIONAL = 3

        # RMF minimum lane detection is 0 m and maximum lane detection in front is 130 m due to extrapolation,
        # which is happening from 120m till 130 m, but only on Highway scenarios
        MIN_LANE_DETECT = 0
        MAX_LANE_DETECT = 130


class SYS100Constants:
    """Class containing constants specific to SYS100."""

    SYS100_FUNCTIONAL_TEST_JSON_PATH = (
        "trc/evaluation/functional_test_helper/" "helper_files/SYS100/SYS100_FunctionalTest.json"
    )

    CEM_STATE_OK = 2
    FAILURE_STATE_OK = 0

    # cem initialization phase
    CEM_INIT_PHASE = 2

    SIG_STATUS_INVALID = 2
    SIG_STATUS_OK = 1
    SIG_STATUS_INIT = 0
    INCREASING_DIFFERENCE = 0
    MAX_ASSUMED_TRAVELED_DISTANCE = 4

    # Sensor ID's
    ARS514_SENSOR_ID = 2073
    MFC527_SENSOR_ID = 2179

    # doors link for signal min max
    # doors://rbgs854a:40000/?version=2&prodID=0&view=0000000b&urn=urn:telelogic::1-503e822e5ec3651e-O-988-0007e749
    SYS100_RADAR_DEFAULT_ROAD_BOUNDARY_RANGE = 0
    SYS100_RMF_BOUNDARY_DEFAULT = 0
    SYS100_min_subsistence_probability = 50

    # 50ms is considered between T6 and component Timestamp
    T7_T6_DIFFERENCE = 50000

    # signal name for T6
    T6_SIGNAL = "SIM VFB CEM200.EMF.EmfGlobalTimestamp.SigHeader.uiTimeStamp"
    sig_status = "eSigStatus"
    cycle_counter = "cycle_counter"

    # ars_road_meas_counter = 'ARS_ROAD_Meas_Counter'
    # adcam_fcu_meas_counter = 'ADCAM_FCU_Meas_Counter'
    timestamp_fcu = "TimeStampFCU"

    sim_syncRef_CamObj_MeasCounter = "SYS100_CAM_Obj_MeasCounter"

    POE = "PoE"  # probability of existence of ftp or rtp
    poe_percentage_value = 50.0

    counter_value = {"TPF": 2, "RMF": 2, "EML": 1, "SEF": 2}

    class RMF:
        lane_segment_lanes = "lane_segment_lanes"
        FDP_SYS100_Ego_Road_Index = "FDP_SYS100_Ego_Road_Index"
        FDP_SYS100_Ego_Lane_Index = "FDP_SYS100_Ego_Lane_Index"
        sim_syncRef_Road_MeasCounter = "SYS100_ROAD_SyncRef_MeasCounter"
        sim_syncRef_CamLane_MeasCounter = "SYS100_CamLane_SyncRef_MeasCounter"
        ars_road_meas_counter = "ARS_ROAD_MeasCounter"
        cam_lane_meas_counter = "CAM_LANE_MeasCounter"
        ars5xx_road_timeStamp = "SYS100_ROAD_ars5xx_timeStamp"
        NumberOfOccupiedPositions = "NumberOfOccupiedPositions"
        num_Of_Lanes = "numOfLanes"
        number_of_road_segments = "numOfRoadSeg"
        numLeftBoundaryParts = "numLeftBoundaryParts"
        numRightBoundaryParts = "numRightBoundaryParts"
        ego_road_index = "Ego_road_index"
        ego_lane_index = "Ego_lane_index"
        road_type = "RoadType"
        rmf_lane_type = "LaneType"
        road_segments = "Road_segments"
        left_boundary = "left_boundary"
        right_boundary = "right_boundary"
        timestamp_rmf = "TimestampRMF"
        linear_objects_data = "linear_objects_data"
        start_Index = "startIndex"
        end_Index = "endIndex"
        points_data = "points_data"
        num_of_points = "numOfPoints"
        association_boundary_continuity = "association_boundary_continuity"
        associations = "associations."
        boundary_continuity_start_index = "boundary_continuity_start_index"
        boundary_continuity_end_index = "boundary_continuity_end_index"
        boundary_continuity_value = "boundary_continuity_value"
        id = "ID"
        num_of_linear_objects = "numLinearObjects"
        rmf_lane_color = "color"
        rmf_lane_width = "width"
        rmf_lane_marking = "marking"
        direction = "Direction"
        fX = "fX"
        fY = "fY"
        leftLane = "leftLane"
        rightLane = "rightLane"
        # Mpp_segment = 'isMpp'
        invalid_data_qualifier = 1
        boundary_lifetime = 0.5

        # default value for Ego Road Index
        ego_road_index_default = 10

        # tolerance for road boundary length difference between cem and radar/RROI
        road_boundary_tolerance = 10

        # minimum length considered for Camera input is 12 meters for <Extrapolated Radar> function
        min_length_camera = 12

        # Camera inputs that are not considered for <Extrapolated Radar> function,
        # only painted markings are taken in consideration
        camera_markings = [4, 9, 10]

        center_line_start_index = "centerLine_startIndex"
        center_line_end_index = "centerLine_endIndex"

        sensor_associations = "sensorAssociations"
        maintenance_state = "maintenanceState"

        # camera signals
        camera_left_y_coordinate = "FCULeftCoefficient0"
        camera_right_y_coordinate = "FCURightCoefficient0"
        camera_next_right_y_coordinate = "FCUNextRightCoefficient0"
        camera_lane_counter = "ADCAM_FCU_Meas_Counter"
        camera_left_boundary = "CameraLeftBoundary"
        camera_right_boundary = "CameraRightBoundary"
        camera_status_left_boundary = "StatusMeasEgoLeftBoundary"
        camera_status_right_boundary = "StatusMeasEgoRightBoundary"
        camera_next_left_boundary = "CameraNextLeftBoundary"
        camera_next_right_boundary = "CameraNextRightBoundary"
        camera_status_next_left_boundary = "StatusMeasNextLeftBoundary"
        camera_status_next_right_boundary = "StatusMeasNextRightBoundary"
        camera_left_lane_color = "ColorLaneMarkingEgoLeft"
        camera_right_lane_color = "ColorLaneMarkingEgoRight"
        camera_left_lane_width = "LaneMarkingWidthEgoLeft"
        camera_right_lane_width = "LaneMarkingWidthLaneEgoRight"
        camera_left_lane_type = "TypeLaneMarkingEgoLeft"
        camera_right_lane_type = "TypeLaneMarkingEgoRight"
        camera_left_boundary_subsistence = "SubsistenceProbabilityEgoLeftBoundary"
        camera_right_boundary_subsistence = "SubsistenceProbabilityEgoRightBoundary"
        camera_data_qualifier = "Event_data_qualifier"

        # radar signals
        radar_road_confidence = "RoadConfidence"
        radar_left_boundary_range = "RadarLeftBoundaryRange"
        radar_right_boundary_range = "RadarRightBoundaryRange"
        radar_left_y_coordinate = "LeftLateralOffset"
        radar_right_y_coordinate = "RightLateralOffset"

        # TODO: Linear Type for SYS100 !!!!
        # RMF - The type of the LinearObject
        RMF_LinearType_UNKNOWN = 1
        RMF_LinearType_LANE_MARKING = 2  # If lane boundary has this type the marking type is set
        RMF_LinearType_GUARD_RAIL = 3
        RMF_LinearType_VIRTUAL = 4  # If camera does not provide an entire lane boundary and it is created virtually.
        RMF_LinearType_CURBSTONE = 5
        RMF_LinearType_ROADEDGE = 6
        RMF_LinearType_WALL = 7
        # TODO: Check Extrapolated linear object type for SYS100!!!
        # RMF_LinearType_EXTRAPOLATED = 10

        # TODO: Linear Type for SYS100 !!!!
        rmf_liner_object_type = {
            0: "Invalid",
            1: "UNKNOWN",
            2: "LANEMARKING",
            3: "GUARDRAIL",
            4: "VIRTUAL",
            5: "CURBSTONE",
            6: "ROADEDGE",
            7: "WALL",
            8: "DELINEATOR",
            9: "PYLON",
        }

    TP_OBJECT_DYN_PROPERTY_MOVING = 0
    TP_OBJECT_DYN_PROPERTY_STATIONARY = 1
    TP_OBJECT_DYN_PROPERTY_UNKNOWN = 2
    TP_OBJECT_DYN_PROPERTY_STOPPED = 3
    TP_OBJECT_DYN_PROPERTY_PARKED = 4

    DYNAMIC_PROPERTY_STOPPED_START_SPEED = 1.8

    SEPARABILITY_DIST = 1.5

    MAIN_STATE_DELETED = 0
    MAIN_STATE_NEW = 1
    MAIN_STATE_MEASURED = 2
    MAIN_STATE_PREDICTED = 3


class Adc420ha22Constants:
    """Class containing constants specific to ADC429HA22."""

    SIGNAL_MANIPULATION_START_TIME = 8.72
    SIGNAL_MANIPULATION_END_TIME = 9.24
    parent_path = Path(__file__).parent.parent.parent.parent

    INCREASING_DIFFERENCE = 0
    CEM_STATE_OK = 2
    FAILURE_STATE_OK = 0
    VDY_STATE_IMPLAUSIBLE = 5
    SIG_STATUS_OK = 1

    SENSOR_ARS510 = " ARS510"
    SENSOR_CAMERA_VALEO = " CAMERA_VALEO"
    SENSOR_CAMERA_VALEO_LANE = " CAMERA_VALEO_LANE"
    SENSOR_SRR520_FL = " SRR520_FL"
    SENSOR_SRR520_FR = " SRR520_FR"
    SENSOR_SRR520_RL = " SRR520_RL"
    SENSOR_SRR520_RR = " SRR520_RR"

    sensor_cam = "Sensor_Valeo_ObjectList"
    sensor_srrfl_salone = "SRRFL_ObjectList_alone"

    SENSOR_ARS510_FREE_SPACE = "SENSOR_ARS510_FREE_SPACE"
    SENSOR_ARS510_OBJECT = "SENSOR_ARS510_OBJECT"
    SENSOR_ARS510_ALL_CLUSTERS = "SENSOR_ARS510_ALL_CLUSTERS"
    SENSOR_ARS510_ROAD = "SENSOR_ARS510_ROAD"
    SENSOR_ARS510_VDY = "SENSOR_ARS510_VDY"
    SENSOR_ARS510_RADAR_STATUS = "SENSOR_ARS510_RADAR_STATUS"

    SENSOR_SRR520_FL_FREE_SPACE = "SENSOR_SRR520_FL_FREE_SPACE"
    SENSOR_SRR520_FL_OBJECT = "SENSOR_SRR520_FL_OBJECT"
    SENSOR_SRR520_FL_ALL_CLUSTERS = "SENSOR_SRR520_FL_ALL_CLUSTERS"
    SENSOR_SRR520_FL_VDY = "SENSOR_SRR520_FL_VDY"
    SENSOR_SRR520_FL_RADAR_STATUS = "SENSOR_SRR520_FL_RADAR_STATUS"

    SENSOR_SRR520_FR_FREE_SPACE = "SENSOR_SRR520_FR_FREE_SPACE"
    SENSOR_SRR520_FR_OBJECT = "SENSOR_SRR520_FR_OBJECT"
    SENSOR_SRR520_FR_ALL_CLUSTERS = "SENSOR_SRR520_FR_ALL_CLUSTERS"
    SENSOR_SRR520_FR_VDY = "SENSOR_SRR520_FR_VDY"
    SENSOR_SRR520_FR_RADAR_STATUS = "SENSOR_SRR520_FR_RADAR_STATUS"

    SENSOR_SRR520_RL_FREE_SPACE = "SENSOR_SRR520_RL_FREE_SPACE"
    SENSOR_SRR520_RL_OBJECT = "SENSOR_SRR520_RL_OBJECT"
    SENSOR_SRR520_RL_ALL_CLUSTERS = "SENSOR_SRR520_RL_ALL_CLUSTERS"
    SENSOR_SRR520_RL_VDY = "SENSOR_SRR520_RL_VDY"
    SENSOR_SRR520_RL_RADAR_STATUS = "SENSOR_SRR520_RL_RADAR_STATUS"

    SENSOR_SRR520_RR_FREE_SPACE = "SENSOR_SRR520_RR_FREE_SPACE"
    SENSOR_SRR520_RR_OBJECT = "SENSOR_SRR520_RR_OBJECT"
    SENSOR_SRR520_RR_ALL_CLUSTERS = "SENSOR_SRR520_RR_ALL_CLUSTERS"
    SENSOR_SRR520_RR_VDY = "SENSOR_SRR520_RR_VDY"
    SENSOR_SRR520_RR_RADAR_STATUS = "SENSOR_SRR520_RR_RADAR_STATUS"

    SENSOR_CAMERA_VALEO_LANES = "SENSOR_CAMERA_VALEO_LANES"
    SENSOR_CAMERA_VALEO_OBJECT = "SENSOR_CAMERA_VALEO_OBJECT"
    SENSOR_CAMERA_VALEO_ALL_CLUSTERS = "SENSOR_CAMERA_VALEO_ALL_CLUSTERS"
    SENSOR_CAMERA_VALEO_CAM_FAILURE_INFO = "SENSOR_CAMERA_VALEO_CAM_FAILURE_INFO"
    SENSOR_CAMERA_VALEO_FC_GLOBAL_HOST_STATE = "SENSOR_CAMERA_VALEO_FC_GLOBAL_HOST_STATE"

    CEM_FDP_21P_TPF = "CEM_FDP_21P_TPF"
    CEM_FDP_21P_SEF = "CEM_FDP_21P_SEF"
    CEM_FDP_21P_VAL = "CEM_FDP_21P_VAL"
    CEM_FDP_21P_ALCA = "CEM_FDP_21P_ALCA"

    CEM_FDP_BASE_EML = "CEM_FDP_BASE_EML"
    CEM_FDP_BASE_RMF = "CEM_FDP_BASE_RMF"
    CEM_FDP_BASE_TPF = "CEM_FDP_BASE_TPF"
    CEM_FDP_BASE_COH = "CEM_FDP_BASE_COH"
    CEM_FDP_BASE_SEF = "CEM_FDP_BASE_SEF"
    CEM_FDP_BASE_VAL = "CEM_FDP_BASE_VAL"

    sig_status = "eSigStatus"
    timestamp_fcu = "TimeStampFCU"
    timestamp_radar_road = "TimestampRadar"
    RMF_num_points = "RMF No of Points"

    HA22_ARS_FRSP_ITEMS_PREFIX = "Local_ARS_CANFD.ARS510HA22_Private.ARS_FRSP_ITEMS_"
    HA22_ARS_FRSP_VERTEX_PREFIX = "Local_ARS_CANFD.ARS510HA22_Private.ARS_FRSP_VERTEX_"

    HA22_ARS_OBJECT_PREFIX = "Local_ARS_CANFD.ARS510HA22_Private.ARS_OBJ_"

    HA22_SRR_FL_OBJECT_PREFIX = "Local_SRR_FL_CANFD.SRR520HA22_FL_Private.SRR_OBJ_"
    HA22_SRR_FR_OBJECT_PREFIX = "Local_SRR_FR_CANFD.SRR520HA22_FR_Private.SRR_OBJ_"
    HA22_SRR_RL_OBJECT_PREFIX = "Local_SRR_RL_CANFD.SRR520HA22_RL_Private.SRR_OBJ_"
    HA22_SRR_RR_OBJECT_PREFIX = "Local_SRR_RR_CANFD.SRR520HA22_RR_Private.SRR_OBJ_"

    HA33_SRR_FL_OBJECT_PREFIX = "Local_SRR_FL_CANFD.SRR520HA33_FL_Private.SRR_OBJ_"
    HA33_SRR_FR_OBJECT_PREFIX = "Local_SRR_FR_CANFD.SRR520HA33_FR_Private.SRR_OBJ_"
    HA33_SRR_RL_OBJECT_PREFIX = "Local_SRR_RL_CANFD.SRR520HA33_RL_Private.SRR_OBJ_"
    HA33_SRR_RR_OBJECT_PREFIX = "Local_SRR_RR_CANFD.SRR520HA33_RR_Private.SRR_OBJ_"

    HA33_SRR_FL_OBJECT_ST_PREFIX = "Local_SRR_FL_CANFD.SRR520HA33_FL_Private.SRR_ECU_FCT_STATUS."
    HA33_SRR_FR_OBJECT_ST_PREFIX = "Local_SRR_FR_CANFD.SRR520HA33_FR_Private.SRR_ECU_FCT_STATUS."
    HA33_SRR_RL_OBJECT_ST_PREFIX = "Local_SRR_RL_CANFD.SRR520HA33_RL_Private.SRR_ECU_FCT_STATUS."
    HA33_SRR_RR_OBJECT_ST_PREFIX = "Local_SRR_RR_CANFD.SRR520HA33_RR_Private.SRR_ECU_FCT_STATUS."

    HA22_SRR_OBJECT_PREFIX = "SRR_OBJ_"
    HA22_SRR_FRSP_ITEMS_PREFIX = "SRR_FRSP_ITEMS_"
    HA22_SRR_FRSP_VERTEX_PREFIX = "SRR_FRSP_VERTEX_"

    HA22_CAMERA_VALEO_OBJECT_PREFIX = "Local_Valeo_CANFD.VSS-FC_Private.OIF_Info_"

    HA22_CEM_FDP_21P_TPF_PREFIX = "SIM VFB CEM200.FDP_21P."
    HA22_CEM_FDP_Base_TPF_PREFIX = "SIM VFB CEM200.FDP_Base."

    ICD_COLUMN_SIGNAL_NAME = "_Signal Name"
    ICD_COLUMN_MAX_RANGE = "phy. Max. Range"
    ICD_COLUMN_RANGE_MONITOR = "RangeMonitor"
    ICD_COLUMN_FACTOR = "Factor"

    map_icd_excel_name_to_sensor_signal_base_string = {
        # SENSOR_ARS510_FREE_SPACE: 'Local_ARS_CANFD.ARS510HA22_Private.ARS_FRSP_HEADER',
        SENSOR_ARS510_OBJECT: "Local_ARS_CANFD.ARS510HA22_Private.ARS_OBJ_STATUS",
        SENSOR_ARS510_ROAD: "Local_ARS_CANFD.ARS510HA22_Private",
        SENSOR_ARS510_VDY: "Local_ARS_CANFD.ARS510HA22_Private",
        SENSOR_ARS510_RADAR_STATUS: "Local_ARS_CANFD.ARS510HA22_Private",
        SENSOR_SRR520_FL_FREE_SPACE: "Local_SRR_FL_CANFD.SRR520HA22_FL_Private",
        SENSOR_SRR520_FL_OBJECT: HA22_SRR_FL_OBJECT_PREFIX,
        SENSOR_SRR520_FL_VDY: "Local_SRR_FL_CANFD.SRR520HA22_FL_Private",
        SENSOR_SRR520_FL_RADAR_STATUS: "Local_SRR_FL_CANFD.SRR520HA22_FL_Private.",
        SENSOR_SRR520_FR_FREE_SPACE: "Local_SRR_FR_CANFD.SRR520HA22_FR_Private",
        SENSOR_SRR520_FR_OBJECT: HA22_SRR_FR_OBJECT_PREFIX,
        SENSOR_SRR520_FR_VDY: "Local_SRR_FR_CANFD.SRR520HA22_FR_Private",
        SENSOR_SRR520_FR_RADAR_STATUS: "Local_SRR_FR_CANFD.SRR520HA22_FR_Private.",
        SENSOR_SRR520_RL_FREE_SPACE: "Local_SRR_RL_CANFD.SRR520HA22_RL_Private",
        SENSOR_SRR520_RL_OBJECT: HA22_SRR_RL_OBJECT_PREFIX,
        SENSOR_SRR520_RL_VDY: "Local_SRR_RL_CANFD.SRR520HA22_RL_Private",
        SENSOR_SRR520_RL_RADAR_STATUS: "Local_SRR_RL_CANFD.SRR520HA22_RL_Private.",
        SENSOR_SRR520_RR_FREE_SPACE: "Local_SRR_RR_CANFD.SRR520HA22_RR_Private",
        SENSOR_SRR520_RR_OBJECT: HA22_SRR_RR_OBJECT_PREFIX,
        SENSOR_SRR520_RR_VDY: "Local_SRR_RR_CANFD.SRR520HA22_RR_Private",
        SENSOR_SRR520_RR_RADAR_STATUS: "Local_SRR_RR_CANFD.SRR520HA22_RR_Private.",
        SENSOR_CAMERA_VALEO_LANES: "Local_Valeo_CANFD.VSS-FC_Private",
        SENSOR_CAMERA_VALEO_OBJECT: "Local_Valeo_CANFD.VSS-FC_Private.OIF_Info",
        # SENSOR_CAMERA_VALEO_CAM_FAILURE_INFO: "Local_Valeo_CANFD.VSS-FC_Private",
        SENSOR_CAMERA_VALEO_FC_GLOBAL_HOST_STATE: "Local_Valeo_CANFD.VSS-FC_Private",
    }

    ICD_EXCEL_NAMES = {
        "INPUT_Clusters": [
            SENSOR_ARS510_OBJECT,
            SENSOR_ARS510_ROAD,
            SENSOR_ARS510_VDY,
            SENSOR_ARS510_RADAR_STATUS,  # SENSOR_ARS510_FREE_SPACE,
            SENSOR_SRR520_FL_OBJECT,
            SENSOR_SRR520_FL_VDY,
            SENSOR_SRR520_FL_RADAR_STATUS,  # SENSOR_SRR520_FL_FREE_SPACE,
            SENSOR_SRR520_FR_OBJECT,
            SENSOR_SRR520_FR_VDY,
            SENSOR_SRR520_FR_RADAR_STATUS,  # SENSOR_SRR520_FR_FREE_SPACE,
            SENSOR_SRR520_RL_OBJECT,
            SENSOR_SRR520_RL_VDY,
            SENSOR_SRR520_RL_RADAR_STATUS,  # SENSOR_SRR520_RL_FREE_SPACE,
            SENSOR_SRR520_RR_OBJECT,
            SENSOR_SRR520_RR_VDY,
            SENSOR_SRR520_RR_RADAR_STATUS,  # SENSOR_SRR520_RR_FREE_SPACE,
            SENSOR_CAMERA_VALEO_LANES,
            SENSOR_CAMERA_VALEO_OBJECT,
            SENSOR_CAMERA_VALEO_FC_GLOBAL_HOST_STATE,
        ]
    }

    ICD_EXCEL_NAMES_TO_TC_NAME_MATCH = {
        "INPUT_Clusters": {
            SENSOR_ARS510_FREE_SPACE: "ARS510_SEF",
            SENSOR_ARS510_OBJECT: "ARS510_TPF",
            SENSOR_ARS510_ROAD: "ARS510_RMF",
            SENSOR_ARS510_VDY: "ARS510_VDY",
            SENSOR_ARS510_RADAR_STATUS: "ARS510_Radar Status",
            SENSOR_SRR520_FL_FREE_SPACE: "SRR520_FL_SEF",
            SENSOR_SRR520_FL_OBJECT: "SRR520_FL_TPF",
            SENSOR_SRR520_FL_VDY: "SRR520_FL_VDY",
            SENSOR_SRR520_FL_RADAR_STATUS: "SRR520_FL_Radar Status",
            SENSOR_SRR520_FR_FREE_SPACE: "SRR520_FR SEF",
            SENSOR_SRR520_FR_OBJECT: "SRR520_FR_TPF",
            SENSOR_SRR520_FR_VDY: "SRR520_FR_VDY",
            SENSOR_SRR520_FR_RADAR_STATUS: "SRR520_FR_Radar Status",
            SENSOR_SRR520_RL_FREE_SPACE: "SRR520_RL_SEF",
            SENSOR_SRR520_RL_OBJECT: "SRR520_RL_TPF",
            SENSOR_SRR520_RL_VDY: "SRR520_RL_VDY",
            SENSOR_SRR520_RL_RADAR_STATUS: "SRR520_RL_Radar Status",
            SENSOR_SRR520_RR_FREE_SPACE: "SRR520_RR_SEF",
            SENSOR_SRR520_RR_OBJECT: "SRR520_RR_TPF",
            SENSOR_SRR520_RR_VDY: "SRR520_RR_VDY",
            SENSOR_SRR520_RR_RADAR_STATUS: "SRR520_RR_Radar Status",
            SENSOR_CAMERA_VALEO_LANES: "CAMERA_VALEO_RMF",
            SENSOR_CAMERA_VALEO_OBJECT: "CAMERA_VALEO_TPF",
            SENSOR_CAMERA_VALEO_FC_GLOBAL_HOST_STATE: "CAMERA_VALEO_fc_global_host",
        }
    }

    SIG_STATUS_INVALID = 2
    SIG_STATUS_INIT = 0

    # cem initialization phase
    CEM_INIT_PHASE = 2
    # 50ms is considered between T6 and component Timestamp
    T7_T6_DIFFERENCE = 40000

    OBJECT_IDENTIFIER = "Object Identifier"
    TEST_STATUS = "_TestStatus_"
    OVERALL_RESULT = "Overall_Result"
    TEST_DATE = "_TestDate_"

    POE = "PoE"  # probability of existence of ftp or rtp
    poe_integer_value = 0.5
    poe_percentage_value = 50.0

    # signal name for T6
    T6_SIGNAL = "SIM VFB ALL.EMF.EmfGlobalTimestamp.SigHeader.uiTimeStamp"


# dynamic property for ARS540BW11
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3507-0007b6c1
TP_OBJECT_DYN_PROPERTY_MOVING = 0
TP_OBJECT_DYN_PROPERTY_STATIONARY = 1
TP_OBJECT_DYN_PROPERTY_ONCOMING = 2
TP_OBJECT_DYN_PROPERTY_CROSSING_LEFT = 3
TP_OBJECT_DYN_PROPERTY_CROSSING_RIGHT = 4
TP_OBJECT_DYN_PROPERTY_UNKNOWN = 5
TP_OBJECT_DYN_PROPERTY_STOPPED = 6
TP_OBJECT_DYN_PROPERTY_MAX_DIFF_TYPES = 7

# doors://rbgs854a:40000/?version=2&prodID=0&view=0000000a&urn=urn:telelogic::1-503e822e5ec3651e-O-920-00099d80
TP_OBJECT_MOVING_ARRAY = [0, 2, 3, 4]
TP_OBJECT_STATIONARY_ARRAY = [1, 6]
MAX_DETECT_RANGE_STATIONARY_CAR = 130
MAX_DETECT_RANGE_MOVING_CAR = 150

counter_value = {"TPF": 2, "RMF": 2, "EML": 1, "SEF": 1}

DEFAULT_POSITION = 255.0

L1_CHECK = False

SHAPE_POINT_STATE_MEASURED = 1
SHAPE_POINT_STATE_ASSUMED = 2

# according to https://jira-adas.zone2.agileci.conti.de/browse/CEM200-25054
MAX_TPF_PLAUSIBLE_VALUE_LENGTH_WIDTH = 20
MIN_TPF_PLAUSIBLE_VALUE_LENGTH_WIDTH = 0

OUTSIDE_FOV_FOR_ALL_SENSORS = 350

camera_boundary_type = {
    0: "UNKNOWN",
    1: "DASHED",
    2: "SOLID",
    3: "DOTTED",
    4: "ROAD_EDGE",
    5: "DOUBLE_LINE_CROSS",
    6: "DOUBLE_LINE_UNCROSS",
    7: "MULTIPLE_LINES_CROSS",
    8: "MULTIPLE_LINES_UNCROSS",
    9: "CURB",
    10: "SNOW_EDGE",
    11: "STRUCTURED",
    13: "NOT_AVAILABLE",
    14: "ERROR",
    15: "SIGNAL_NOT_FILLED",
}
rmf_boundary_type = {
    0: "UNKNOWN",
    1: "NONE",
    2: "SOLID",
    3: "DASHED",
    4: "OTHER",
    5: "DOUBLE",
    6: "DOTTED",
    7: "DECORATION",
}
camera_boundary_color = {0: "UNKNOWN", 1: "WHITE", 2: "YELLOW", 3: "BLUE", 4: "GREEN", 5: "RED"}
rmf_boundary_color = {0: "UNKNOWN", 1: "WHITE", 2: "YELLOW", 3: "RED", 4: "BLUE", 5: "GREEN"}

radar_road_type = {0: "UNKNOWN", 1: "CITY", 2: "COUNTRY", 3: "HIGHWAY"}
rmf_road_type = {0: "UNKNOWN", 1: "HIGHWAY", 2: "CITY", 3: "COUNTRY", 4: "OTHER"}

CAMERA_LANE_MARKING_TYPE = {
    "UNKNOWN": 0,
    "DASHED": 1,
    "SOLID": 2,
    "DOTTED": 3,
    "ROAD_EDGE": 4,
    "DOUBLE_LINE_CROSS": 5,
    "DOUBLE_LINE_UNCROSS": 6,
    "MULTIPLE_LINES_CROSS": 7,
    "MULTIPLE_LINES_UNCROSS": 8,
    "CURB": 9,
    "SNOW_EDGE": 10,
    "STRUCTURED": 11,
    "NOT_AVAILABLE": 13,
    "ERROR": 14,
    "SIGNAL_NOT_FILLED": 15,
}
RADAR_BORDER_TYPE = {"UNKNOWN": 0, "GUARDRAIL": 1, "OTHER": 2}
sensor_associations_maintenance_state = {"PREDICTED": 0, "MEASURED": 1, "EXTRAPOLATED": 2}

BMW_ALL_SENSORS_INVALID_ID = 0
validity_minimum_overlap = 95

# the RMF ROI (region of interest)
RROI = 130

# min target speed and max target speed for dynamic property stopped
MIN_TARGET_SPEED_FOR_STOPPED = 0
MAX_TARGET_SPEED_FOR_STOPPED = 1.8

SIGNAL_TYPE = "FDP_21P"
CEM_OUTPUT_CHECK_FDP_21P = True
# number of cycles a rmf lane boundary is still reported after camera stopped reporting it
lane_boundary_lifetime = 20

# ego lane and ego road boundaries lateral variance
lateral_variance_camera_radar = 0.25

ARS540BW11_SM_STATE_MERGE = 1

# yaw angle bounds for turning 90 degrees
MIN_BOUND_YAW = [0, 0.4]
MAX_BOUND_YAW = 1.4
REQUESTED_ANGLE = [0.785, 2.356]
VALID_TURN_DIFFERENCE = 0.95
MAX_BOUND_YAW_SIMULTANEOUSLY_TURNING = 1.0

# the minimum valid probability for under and over drivable object
MIN_PROBABILITY_UNDER_OVER = 50.0

# Default Signal -1 = Not Available
EML_DEFAULT_MINUS1 = -1

SENSOR_CATCH_VALID = 1
SENSOR_CATCH_VALUE_ZERO = 0

# SIG STATUS SIGNAL ENUM DEFINITION As PER DOORS ICD DOCUMENT
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000023&urn=urn:telelogic::1-503e822e5ec3651e-O-3425-0007b6c1
AL_SIG_STATE_INIT = 0
AL_SIG_STATE_OK = 1
AL_SIG_STATE_INVALID = 2.0
AL_SIG_STATE_INVALID_POSITION_X = 7.0

FID_CEM_RECRANKING_FLAG_SET = 1.0
FID_TEMP_FAILURE_FLAG_RESET = 0.0
FID_CEM_RECRANKING_FLAG_RESET = 0.0
FID_TEMP_FAILURE_FLAG_SET = 1.0

CEM_FDP_BASE_OBJ_ID_INVALID = 255
CEM_FDP_21P_OBJ_ID_INVALID = 0

# SENSOR OUTPUT STATE ENUM VALUES DOORS LINK
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000058&urn=urn:telelogic::1-503e822e5ec3651e-O-6750-0009b482
SENSOR_OUTPUT_FAILURE_STATUS_UNKNOWN = 0
SENSOR_OUTPUT_FAILURE_STATUS_IMPLAUSIBLE = 1.0
SENSOR_OUTPUT_FAILURE_STATUS_PLAUSIBLE = 2

SYSTEM_STATUS = {
    SENSOR_OUTPUT_FAILURE_STATUS_UNKNOWN: "Unknown",
    SENSOR_OUTPUT_FAILURE_STATUS_IMPLAUSIBLE: "Implausible",
    SENSOR_OUTPUT_FAILURE_STATUS_PLAUSIBLE: "Plausible",
}
CAM_FAILURE_INFO = "cam_failure_info"
FC_GLOBAL_HOST = "fc_global_host"
SW_VERSION_INFO = "sw_version_info"

# SIM OUTPUT SENSOR ERROR
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000058&urn=urn:telelogic::1-503e822e5ec3651e-O-12345679-0009b482
E2E_ERROR_NORMAL = 0
TIMEOUT_ERROR_NORMAL = 0
E2E_ERROR_FAILURE = 1
TIMEOUT_ERROR_FAILURE = 1

ALCA_STATUS_RESET = 0.0
ALCA_STATUS_SET = 1.0

# HA22 VDY STATE ID DOORS ICD ENUM VALUES
# ----------------------------------------------------------------------------------------------------------------------
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000058&urn=urn:telelogic::1-503e822e5ec3651e-O-7064-0009b482
VDY_IO_STATE_VALID = 0  # (Normal)
VDY_IO_STATE_INVALID = 1  # (Failure, not usable)
VDY_IO_STATE_NOTAVAIL = 2  # (Failure, not usable)
VDY_IO_STATE_DECREASED = 3  # (Normal)
VDY_IO_STATE_SUBSTITUE = 4  # (Failure, not usable)
VDY_IO_STATE_INPLAUSIBLE = 5.0  # (state not used)
VDY_IO_STATE_INIT = 15  # (initialization, not usable)
VDY_IO_STATE_CALC = 6  # (initialization, not usable)

RMF_DEFAULT_VALUE_ZERO = 0.0
CAM_INTERNAL_FAILURE = 1

# To turn on or Off synchronization , by default it is set off ie false
IS_SYNCHRONIZATION_NEEDED = False

# ADC420HA22 SAFETY TEST
# ----------------------------------------------------------------------------------------------------------------------
SENSOR_ARS510 = " ARS510"
SENSOR_CAMERA_VALEO = " CAMERA_VALEO"
SENSOR_CAMERA_VALEO_OBJECT = " CAMERA_VALEO_OBJECT"
SENSOR_CAMERA_VALEO_LANE = " CAMERA_VALEO_LANE"
SENSOR_SRR520_FL = " SRR520_FL"
SENSOR_SRR520_FR = " SRR520_FR"
SENSOR_SRR520_RL = " SRR520_RL"
SENSOR_SRR520_RR = " SRR520_RR"
SENSOR_NOT_AVAILABLE = "SENSOR_NOT_AVAILABLE"
CLUSTER_NOT_AVAILABLE = "CLUSTER_NOT_AVAILABLE"
SENSOR_ARS_CATCH = "ARSCatch"
SENSOR_SRR_FL_CATCH = "SRRFLCatch"
SENSOR_SRR_FR_CATCH = "SRRFRCatch"
SENSOR_SRR_RL_CATCH = "SRRRLCatch"
SENSOR_SRR_RR_CATCH = "SRRRRCatch"
SENSOR_CAMERA_CATCH = "CAMCatch"
SENSOR_COMBINED = " SENSOR_COMBINED"

SIGNAL_OUT_OF_RANGE = " Signal out of range"
SIG_STATUS_VEHICLE = "CEM SIG_STATUS(Vehicle)"
SIG_STATUS_SIM = "CEM SIG_STATUS(SIM)"
OBJ_STATUS = "No of object"
CYCLE_COUNTER = "Cycle counter"
HA22_TOW_MODE = "TOW MODE"

HA22_FUSION = "01 Fusion"
HA22_PERCEPTION_RANGE = "02 Perception Range"
HA22_NOT_ALL_CLUSTERS = "03 Not All Clusters"
HA22_ALL_CLUSTERS = "04 All Clusters"
HA22_SENSOR_OUTPUT_STATE = "03 Sensor Output State"
HA22_CEM_OUTPUT_STATE = "CEM Output State"
HA22_DEM_OUTPUT_STATE = "DEM Output State"
HA22_VDY_DELAY_33CYCLES = "33 Cycle Delay"
E2E = "E2E"
TIMEOUT = "TIMEOUT"

PERCEPTION_RANGE_VALUE_ZERO = 0.0

# HA22 CEM OUTPUT STATE DOORS ICD ENUM VALUES
# ----------------------------------------------------------------------------------------------------------------------
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000058&urn=urn:telelogic::1-503e822e5ec3651e-O-6756-0009b482
HA22_CEM_OUTPUT_STATE_INIT = 0.0
HA22_CEM_OUTPUT_STATE_NORMAL = 1.0
HA22_CEM_OUTPUT_STATE_TEMPORARY_FAILURE = 2.0
HA22_CEM_OUTPUT_STATE_PERMANENT_FAILURE = 3.0
HA22_CEM_OUTPUT_STATE_OFF = 4.0

HA22_ALCA_SIGNAL_MANIPULATION_START_TIME = 100.0
HA22_ALCA_SIGNAL_MANIPULATION_END_TIME = 200.0

HA22_TOW_MODE_SAFETY_START_TIME = 4.0
HA22_TOW_MODE_SAFETY_END_TIME = 41.0

HA22_CEM_OUTPUT_CYCLE_COUNT = 33

# HA22 Radar FAILURE SIGNAL enum values
# ----------------------------------------------------------------------------------------------------------------------
RADAR_FAILURE_OPMODE_UNKNOWN = 0.0
RADAR_FAILURE_OPMODE_INIT = 1.0
RADAR_FAILURE_OPMODE_NORMAL = 2.0
RADAR_FAILURE_OPMODE_DEGRADED = 4.0
RADAR_FAILURE_OPMODE_BLOCKED = 8.0
RADAR_FAILURE_OPMODE_FAILURE = 16.0

RADAR_FAILURE_BLKG_UNKNOWN = 1.0
RADAR_FAILURE_BLKG_NORMAL = 2.0
RADAR_FAILURE_BLKG_LOW_IMPACT = 4.0
RADAR_FAILURE_BLKG_MED_IMPACT = 8.0
RADAR_FAILURE_BLKG_HIGH_IMPACT = 16.0
RADAR_FAILURE_BLKG_FULL_BLOCKAGE = 32.0

RADAR_FAILURE_ALN_UNKNOWN = 0.0
RADAR_FAILURE_ALN_INIT = 1.0
RADAR_FAILURE_ALN_CORRECTED = 2.0
RADAR_FAILURE_ALN_MAX_CORRECTION = 4.0
RADAR_FAILURE_ALN_PERMANENTKY_MISALIGNED = 8.0

RADAR_FAILURE_TEMPSTATE_NOTAVILABLE = 1.0
RADAR_FAILURE_TEMPSTATE_NORMAL = 2.0
RADAR_FAILURE_TEMPSTATE_LIMITED = 4.0
RADAR_FAILURE_TEMPSTATE_SHUTDOWN = 8.0

RADAR_FAILURE_ERRORSTATE_UNKNOWN = 0.0
RADAR_FAILURE_ERRORSTATE_NORMAL = 1.0
RADAR_FAILURE_ERRORSTATE_INTERNAL_FAILURE = 2.0
RADAR_FAILURE_ERRORSTATE_EXTERNAL_FAILURE = 4.0
RADAR_FAILURE_ERRORSTATE_HEATER_CIRMALF = 8.0
RADAR_FAILURE_ERRORSTATE_CLOCK_SYNC_FAILURE = 32.0

CAM_FAILURE_FC_OFF = 0.0
CAM_FAILURE_FC_INITIALIZATION = 1.0
CAM_FAILURE_FC_ON_FLASH_UPDATE = 2.0
CAM_FAILURE_FC_NORMAL_OPERATION = 3.0
CAM_FAILURE_FC_CALIBRATION = 4.0
CAM_FAILURE_FC_ERROR = 5.0

VDY_ERR_STATE_UNKNOWN = 0.0
VDY_ERR_STATE_ACTIVE = 1.0
VDY_ERR_STATE_INACTIVE = 2.0

HA22_CEM_DEM_TEMP_SET_STATE = 1.0

# HA22 sensor input timestamp signal manipulation value
# ----------------------------------------------------------------------------------------------------------------------
HA22_TEST_CASE_TO_INPUT_SIGNAL_VALUE_MAPPING = {
    "ADCU VDY Time Freeze": [2575255494],
    "ADCU VDY Time GT T6": [2583560843],
    "ADCU VDY Time GT 500ms": [4294967295],
    "ADCU VDY Out of range": [41.0],
    "ADCU VDY Time Decrease": [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
    TIME_DECREASE: [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
    TIME_FREEZE: [1520.0],
    TIME_GREATER_THAN_T6: [7250.0],
    TIME_GREATER_THAN_500MS: [4294967295.0],
    RADAR_INVALID: [2.0],
}

# HA22 INPUT TIMESTAMP Signal
# ----------------------------------------------------------------------------------------------------------------------
HA22_INPUT_TIMESTAMP_ARS_SEF_SIGNAL = "Local_ARS_CANFD.ARS510HA22_Private.ARS_FRSP_HEADER.uiTimeStampGlobSec_FRSP"
HA22_INPUT_TIMESTAMP_ARS_TPF_SIGNAL = "Local_ARS_CANFD.ARS510HA22_Private.ARS_OBJ_STATUS.uiTimeStampGlobSec_OBJ_STS"
HA22_INPUT_TIMESTAMP_ARS_RMF_SIGNAL = "Local_ARS_CANFD.ARS510HA22_Private.ARS_ROAD.uiTimeStampGlobSec_RD"
HA22_INPUT_TIMESTAMP_ARS_VDY_SIGNAL = "Local_ARS_CANFD.ARS510HA22_Private.ARS_VDY.uiTimeStampGlobSec_VDY"

HA22_INPUT_TIMESTAMP_ARS_SEF_SIGNAL_NANO = "Local_ARS_CANFD.ARS510HA22_Private.ARS_FRSP_HEADER.uiTimeStampGlobNsec_FRSP"
HA22_INPUT_TIMESTAMP_ARS_TPF_SIGNAL_NANO = (
    "Local_ARS_CANFD.ARS510HA22_Private.ARS_OBJ_STATUS." "uiTimeStampGlobNsec_OBJ_STS"
)
HA22_INPUT_TIMESTAMP_ARS_RMF_SIGNAL_NANO = "Local_ARS_CANFD.ARS510HA22_Private.ARS_ROAD.uiTimeStampGlobNSec_RD"
HA22_INPUT_TIMESTAMP_ARS_VDY_SIGNAL_NANO = "Local_ARS_CANFD.ARS510HA22_Private.ARS_VDY.uiTimeStampGlobNsec_VDY"

HA22_INPUT_TIMESTAMP_CAMERA_TPF_SIGNAL = "Local_Valeo_CANFD.VSS-FC_Private.OIF_Info_0.TIMESTAMP_SYNC_OIF_SEC"
HA22_INPUT_TIMESTAMP_CAMERA_RMF_SIGNAL = "Local_Valeo_CANFD.VSS-FC_Private.LANES_Info_1.TIMESTAMP_SYNC_LANES_SEC"

HA22_INPUT_TIMESTAMP_SRR520_FL_TPF_SIGNAL = (
    "Local_SRR_FL_CANFD.SRR520HA22_FL_Private." "SRR_OBJ_STATUS.uiTimeStampGlobSec_ObjSts"
)
HA22_INPUT_TIMESTAMP_SRR520_FL_SEF_SIGNAL = (
    "Local_SRR_FL_CANFD.SRR520HA22_FL_Private." "SRR_FRSP_HEADER.uiTimeStampGlobSec_FrSp"
)
HA22_INPUT_TIMESTAMP_SRR520_FL_VDY_SIGNAL = "Local_SRR_FL_CANFD.SRR520HA22_FL_Private." "SRR_VDY.uiTimeStampGlobSec_VDY"

HA22_INPUT_TIMESTAMP_SRR520_FL_TPF_SIGNAL_NANO = (
    "Local_SRR_FL_CANFD.SRR520HA22_FL_Private." "SRR_OBJ_STATUS.uiTimeStampGlobNsec_ObjSts"
)
HA22_INPUT_TIMESTAMP_SRR520_FL_SEF_SIGNAL_NANO = (
    "Local_SRR_FL_CANFD.SRR520HA22_FL_Private." "SRR_FRSP_HEADER.uiTimeStampGlobNsec_FrSp"
)
HA22_INPUT_TIMESTAMP_SRR520_FL_VDY_SIGNAL_NANO = (
    "Local_SRR_FL_CANFD.SRR520HA22_FL_Private." "SRR_VDY.uiTimeStampGlobNsec_VDY"
)

HA22_INPUT_TIMESTAMP_SRR520_FR_TPF_SIGNAL = (
    "Local_SRR_FR_CANFD.SRR520HA22_FR_Private." "SRR_OBJ_STATUS.uiTimeStampGlobSec_ObjSts"
)
HA22_INPUT_TIMESTAMP_SRR520_FR_SEF_SIGNAL = (
    "Local_SRR_FR_CANFD.SRR520HA22_FR_Private." "SRR_FRSP_HEADER.uiTimeStampGlobSec_FrSp"
)
HA22_INPUT_TIMESTAMP_SRR520_FR_VDY_SIGNAL = "Local_SRR_FR_CANFD.SRR520HA22_FR_Private." "SRR_VDY.uiTimeStampGlobSec_VDY"

HA22_INPUT_TIMESTAMP_SRR520_FR_TPF_SIGNAL_NANO = (
    "Local_SRR_FR_CANFD.SRR520HA22_FR_Private." "SRR_OBJ_STATUS.uiTimeStampGlobNsec_ObjSts"
)
HA22_INPUT_TIMESTAMP_SRR520_FR_SEF_SIGNAL_NANO = (
    "Local_SRR_FR_CANFD.SRR520HA22_FR_Private." "SRR_FRSP_HEADER.uiTimeStampGlobNsec_FrSp"
)
HA22_INPUT_TIMESTAMP_SRR520_FR_VDY_SIGNAL_NANO = (
    "Local_SRR_FR_CANFD.SRR520HA22_FR_Private." "SRR_VDY.uiTimeStampGlobNsec_VDY"
)

HA22_INPUT_TIMESTAMP_SRR520_RL_TPF_SIGNAL = (
    "Local_SRR_RL_CANFD.SRR520HA22_RL_Private." "SRR_OBJ_STATUS.uiTimeStampGlobSec_ObjSts"
)
HA22_INPUT_TIMESTAMP_SRR520_RL_SEF_SIGNAL = (
    "Local_SRR_RL_CANFD.SRR520HA22_RL_Private." "SRR_FRSP_HEADER.uiTimeStampGlobSec_FrSp"
)
HA22_INPUT_TIMESTAMP_SRR520_RL_VDY_SIGNAL = "Local_SRR_RL_CANFD.SRR520HA22_RL_Private." "SRR_VDY.uiTimeStampGlobSec_VDY"

HA22_INPUT_TIMESTAMP_SRR520_RL_TPF_SIGNAL_NANO = (
    "Local_SRR_RL_CANFD.SRR520HA22_RL_Private." "SRR_OBJ_STATUS.uiTimeStampGlobNsec_ObjSts"
)
HA22_INPUT_TIMESTAMP_SRR520_RL_SEF_SIGNAL_NANO = (
    "Local_SRR_RL_CANFD.SRR520HA22_RL_Private." "SRR_FRSP_HEADER.uiTimeStampGlobNsec_FrSp"
)
HA22_INPUT_TIMESTAMP_SRR520_RL_VDY_SIGNAL_NANO = (
    "Local_SRR_RL_CANFD.SRR520HA22_RL_Private." "SRR_VDY.uiTimeStampGlobNsec_VDY"
)

HA22_INPUT_TIMESTAMP_SRR520_RR_TPF_SIGNAL = (
    "Local_SRR_RR_CANFD.SRR520HA22_RR_Private." "SRR_OBJ_STATUS.uiTimeStampGlobSec_ObjSts"
)
HA22_INPUT_TIMESTAMP_SRR520_RR_SEF_SIGNAL = (
    "Local_SRR_RR_CANFD.SRR520HA22_RR_Private." "SRR_FRSP_HEADER.uiTimeStampGlobSec_FrSp"
)
HA22_INPUT_TIMESTAMP_SRR520_RR_VDY_SIGNAL = "Local_SRR_RR_CANFD.SRR520HA22_RR_Private." "SRR_VDY.uiTimeStampGlobSec_VDY"

HA22_INPUT_TIMESTAMP_SRR520_RR_TPF_SIGNAL_NANO = (
    "Local_SRR_RR_CANFD.SRR520HA22_RR_Private." "SRR_OBJ_STATUS.uiTimeStampGlobNsec_ObjSts"
)
HA22_INPUT_TIMESTAMP_SRR520_RR_SEF_SIGNAL_NANO = (
    "Local_SRR_RR_CANFD.SRR520HA22_RR_Private." "SRR_FRSP_HEADER.uiTimeStampGlobNsec_FrSp"
)
HA22_INPUT_TIMESTAMP_SRR520_RR_VDY_SIGNAL_NANO = (
    "Local_SRR_RR_CANFD.SRR520HA22_RR_Private." "SRR_VDY.uiTimeStampGlobNsec_VDY"
)

HA22_ARS_CANFD_BLOCKAGESTATUS = "Local_ARS_CANFD.ARS510HA22_Private.ARS_ECU_FCT_STATUS.e_SP_BlockageStatus"
HA22_SRR_FL_CANFD_BLOCKAGESTATUS = "Local_SRR_FL_CANFD.SRR520HA22_FL_Private.SRR_ECU_FCT_STATUS.e_SP_BlockageStatus"
HA22_SRR_FR_CANFD_BLOCKAGESTATUS = "Local_SRR_FR_CANFD.SRR520HA22_FR_Private.SRR_ECU_FCT_STATUS.e_SP_BlockageStatus"
HA22_VALEO_CANFD_BLOCKAGESTATUS = "Local_Valeo_CANFD.VSS-FC_Private.CAM_Failure_Info.CAM_INTERNAL_FAILURE"

HA22_CEM_FDP_BASE_RMF_OUTPUT_NUM_LINEAR_OBJ = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.numLinearObjects"
HA22_CEM_FDP_BASE_RMF_OUTPUT_NUM_POINTS = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.numPoints"
HA22_CEM_FDP_BASE_RMF_OUTPUT_NUM_BOUNDARY = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.associations.numBoundaryContinuity"
HA22_CEM_FDP_BASE_RMF_OUTPUT_NUM_LANE_COUNTS = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.associations.numLaneCounts"
HA22_CEM_FDP_BASE_RMF_OUTPUT_NUM_SENSOR = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.associations.numSensorAssociations"
HA22_CEM_FDP_BASE_RMF_OUTPUT_NUM_SLOPES = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.associations.numSlopes"
HA22_CEM_FDP_BASE_RMF_OUTPUT_LANE_NUM_CONNECTIONS = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.laneTopology.numConnections"
HA22_CEM_FDP_BASE_RMF_OUTPUT_NUM_LANE_SEGMENTS = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.laneTopology.numLaneSegments"
HA22_CEM_FDP_BASE_RMF_OUTPUT_ROAD_NUM_CONNECTIONS = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.roadTopology.numConnections"
HA22_CEM_FDP_BASE_RMF_OUTPUT_NUM_ROAD_SEGMENTS = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.roadTopology.numRoadSegments"
# HA22 INPUT Sig Status Signal
# ----------------------------------------------------------------------------------------------------------------------
HA22_INPUT_SIG_STATUS_ARS_TPF_SIGNAL = "Local_ARS_CANFD.ARS510HA22_Private.ARS_OBJ_STATUS.SigStatus_OBJ_STS"
HA22_INPUT_SIG_STATUS_ARS_SEF_SIGNAL = "Local_ARS_CANFD.ARS510HA22_Private.ARS_FRSP_HEADER.SigStatus_FRSP"
HA22_INPUT_SIG_STATUS_ARS_RMF_SIGNAL = "Local_ARS_CANFD.ARS510HA22_Private.ARS_ROAD.eSigStatus_RD"

HA22_INPUT_SIG_STATUS_SRR520_FL_TPF_SIGNAL = "Local_SRR_FL_CANFD.SRR520HA22_FL_Private.SRR_OBJ_STATUS.SigStatus_ObjSts"
HA22_INPUT_SIG_STATUS_SRR520_FR_TPF_SIGNAL = "Local_SRR_FR_CANFD.SRR520HA22_FR_Private.SRR_OBJ_STATUS.SigStatus_ObjSts"
HA22_INPUT_SIG_STATUS_SRR520_RL_TPF_SIGNAL = "Local_SRR_RL_CANFD.SRR520HA22_RL_Private.SRR_OBJ_STATUS.SigStatus_ObjSts"
HA22_INPUT_SIG_STATUS_SRR520_RR_TPF_SIGNAL = "Local_SRR_RR_CANFD.SRR520HA22_RR_Private.SRR_OBJ_STATUS.SigStatus_ObjSts"

# HA22 Vehicle  SIG_STATUS SIGNAL
# FDP_BASE
HA22_VEHICLE_FDP_BASE_SIG_STATUS_TPF_SIGNAL = "ADC4xx.FDP_Base.p_TpfOutputIf.sSigHeader.eSigStatus"
HA22_VEHICLE_FDP_BASE_SIG_STATUS_EML_SIGNAL = "ADC4xx.FDP_Base.p_EmlOutputIf.sigHeader.eSigStatus"
HA22_VEHICLE_FDP_BASE_SIG_STATUS_RMF_SIGNAL = "ADC4xx.FDP_Base.p_RmfOutputIf.sMetaData.sSigHeader.eSigStatus"
HA22_VEHICLE_FDP_BASE_SIG_STATUS_SEF_SIGNAL = "ADC4xx.FDP_Base.p_FsfOutputIf.sSigHeader.eSigStatus"
HA22_VEHICLE_FDP_BASE_SIG_STATUS_VAL_SIGNAL = "ADC4xx.FDP_Base.p_ValOutputIf.sSigHeader.eSigStatus"

# HA22 CEM OUTPUT NO_OF_OBJECT_SIGNAL
HA22_OUTPUT_SIG_STATUS_SEF_NO_OF_OBS_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_NumObsInfo.numberOfObstacles"
HA22_OUTPUT_SIG_STATUS_TPF_NO_OF_OBJ_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_NumObjInfo.numberOfObjects"
HA22_OUTPUT_SIG_STATUS_RMF_NO_OF_POINTS_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_NumPtsInfo.numberOfPoints"

# HA22 CEM OUTPUT FDP_BASE NO_OF_OBJECT_SIGNAL
HA22_OUTPUT_VEHICLE_TPF_NO_OF_OBJ_SIGNAL = "ADC4xx.FDP_21P.FDP_NumObjInfo.numberOfObjects"
HA22_OUTPUT_VEHICLE_SEF_NO_OF_OBS_SIGNAL = "ADC4xx.FDP_21P.FDP_NumObsInfo.numberOfObstacles"
HA22_OUTPUT_VEHICLE_RMF_NO_OF_POINTS_SIGNAL = "ADC4xx.FDP_21P.FDP_NumPtsInfo.numberOfPoints"

HA22_TOW_MODE_SIGNAL = "Global_Vehicle_CAN2_HS.Vehicle_CAN2_Public.IMG_22C."

# HA22 CEM OUTPUT CYCLE_COUNTER_SIGNAL
HA22_OUTPUT_SIG_STATUS_TPF_CYCLE_COUNT_SIGNAL = "SIM VFB CEM200.FDP_Base.p_TpfOutputIf.sSigHeader.uiCycleCounter"

# HA22 INPUT Radar Failure Signal Dictionary mapping as the signals do not change except prefix
# ----------------------------------------------------------------------------------------------------------------------
HA22_SENSOR_FAILURE_INPUT_FAILURE_SIGNAL_PREFIX = {
    SENSOR_ARS510: "Local_ARS_CANFD.ARS510HA22_Private.ARS_ECU_FCT_STATUS.",
    SENSOR_SRR520_FL: "Local_SRR_FL_CANFD.SRR520HA22_FL_Private.SRR_ECU_FCT_STATUS.",
    SENSOR_SRR520_FR: "Local_SRR_FR_CANFD.SRR520HA22_FR_Private.SRR_ECU_FCT_STATUS.",
    SENSOR_SRR520_RL: "Local_SRR_RL_CANFD.SRR520HA22_RL_Private.SRR_ECU_FCT_STATUS.",
    SENSOR_SRR520_RR: "Local_SRR_RR_CANFD.SRR520HA22_RR_Private.SRR_ECU_FCT_STATUS.",
    SENSOR_CAMERA_VALEO: "Local_Valeo_CANFD.VSS-FC_Private.",
}

HA22_SENSOR_FAILURE_OUTPUT_SIP_COMMUNICATION_ERROR_SIGNAL_PREFIX = {
    SENSOR_ARS510: "SIM VFB CEM200.ARS510.ARS510E2EFctStatus.",
    SENSOR_SRR520_FL: "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_fl.",
    SENSOR_SRR520_FR: "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_fr.",
    SENSOR_SRR520_RL: "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_rl.",
    SENSOR_SRR520_RR: "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_rr.",
    SENSOR_CAMERA_VALEO: "SIM VFB CEM200.Valeo.ValeoE2EFctStatus.",
}

HA22_ADC4xx_T6_TIME_SIGNAL = "ADC4xx.EMF.EmfGlobalTimestamp.SigHeader.uiTimeStamp"

HA22_CEM_OUTPUT_STATE_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU.sigCemSwcStatus"
HA22_INPUT_SIG_STATUS_ADCU_VDY_SIGNAL = "ADC4xx.IPVDY.VehDyn_t.sSigHeader.eSigStatus"
HA22_INPUT_SIG_STATUS_ARS_POSITION = "Local_ARS_CANFD.ARS510HA22_Private.ARS_ECU_FCT_STATUS.f_positionX"
HA22_INPUT_SIG_STATUS_SRR_POSITION = "Local_SRR_FL_CANFD.SRR520HA22_FL_Private.SRR_ECU_FCT_STATUS.f_positionX"
HA22_INPUT_VALEO = "Local_Valeo_CANFD.VSS-FC_Private.OIF_Info_2.OIF_Height_STD_1"

HA22_CEM_FDP_BASE_TPF_SIG_STATUS_SIGNAL = "SIM VFB CEM200.FDP_Base.p_TpfOutputIf.sSigHeader.eSigStatus"
HA22_CEM_FDP_BASE_SEF_SIG_STATUS_SIGNAL = "SIM VFB CEM200.FDP_Base.p_FsfOutputIf.sSigHeader.eSigStatus"
HA22_CEM_FDP_BASE_EML_SIG_STATUS_SIGNAL = "SIM VFB CEM200.FDP_Base.p_EmlOutputIf.sigHeader.eSigStatus"
HA22_CEM_FDP_BASE_RMF_SIG_STATUS_SIGNAL = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.sigHeader.eSigStatus"
HA22_CEM_FDP_BASE_COH_SIG_STATUS_SIGNAL = "SIM VFB CEM200.FDP_Base.p_CemAssocOutputIf.SigHeader.eSigStatus"
HA22_CEM_FDP_BASE_EML_EGO_VEH_SIG_STATUS_SIGNAL = "SIM VFB CEM200.EML.EmlOutput.egoVehKinematic.sigHeader.eSigStatus"

HA22_CEM_OUTPUT_STATE_ARS_PLAUSIBILITY_STATUS = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigFrontRadarPlausibilityFailureStatus"
)
HA22_CEM_OUTPUT_STATE_CAMERA_PLAUSIBILITY_STATUS = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigCameraPlausibilityFailureStatus"
)
HA22_CEM_OUTPUT_STATE_SRR_FR_PLAUSIBILITY_STATUS = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigFrontRightRadarPlausibilityFailureStatus"
)
HA22_CEM_OUTPUT_STATE_SRR_FL_PLAUSIBILITY_STATUS = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigFrontLeftRadarPlausibilityFailureStatus"
)
HA22_CEM_OUTPUT_STATE_SRR_RR_PLAUSIBILITY_STATUS = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigRearRightRadarPlausibilityFailureStatus"
)
HA22_CEM_OUTPUT_STATE_SRR_RL_PLAUSIBILITY_STATUS = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigRearLeftRadarPlausibilityFailureStatus"
)
# HIP_HA22 SIGNALS
HA22_FID_CEM_RECRANKING_STATE_FLAG = "SIM VFB CEM200.HIP_HA22.fidFailureFlagMeasFreeze.FidInCemReCrankingStateFlag"
HA22_FID_TEMP_FAILURE_FLAG = "SIM VFB CEM200.HIP_HA22.fidFailureFlagMeasFreeze.fidInTempFailureFlag"

HA22_OUTPUT_SIG_STATUS_OBJECT_TPF_SIGNAL = "SIM VFB CEM200.FDP_Base.p_TpfOutputIf.sSigHeader.eSigStatus"

HA22_OUTPUT_SIG_STATUS_SEF_SIGNAL = "SIM VFB CEM200.FDP_Base.p_FsfOutputIf.sSigHeader.eSigStatus"
HA22_OUTPUT_SIG_STATUS_EML_SIGNAL = "SIM VFB CEM200.FDP_Base.p_EmlOutputIf.sigHeader.eSigStatus"
HA22_OUTPUT_SIG_STATUS_COH_SIGNAL = "SIM VFB CEM200.FDP_Base.p_CemAssocOutputIf.SigHeader.eSigStatus"
HA22_OUTPUT_SIG_STATUS_RMF_SIGNAL = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.sigHeader.eSigStatus"
HA22_OUTPUT_SIG_STATUS_VAL_SIGNAL = "SIM VFB CEM200.FDP_Base.p_ValOutputIf.sSigHeader.eSigStatus"

HA22_SENSOR_FAILURE_OUTPUT_SIP_COMMUNICATION_E2E_ERROR_SIGNAL_SUFFIX = "E2E_ERROR"
HA22_SENSOR_FAILURE_OUTPUT_SIP_COMMUNICATION_TIMEOUT_ERROR_SIGNAL_SUFFIX = "TIMEOUT_ERROR"

SENSOR_ARS510_INPUT_FAILURE_SIGNAL_PREFIX = "Local_ARS_CANFD.ARS510HA22_Private.ARS_ECU_FCT_STATUS."

SENSOR_SRR520_FL_INPUT_FAILURE_SIGNAL_PREFIX = "Local_SRR_FL_CANFD.SRR520HA22_FL_Private.SRR_ECU_FCT_STATUS."
SENSOR_SRR520_FR_INPUT_FAILURE_SIGNAL_PREFIX = "Local_SRR_FR_CANFD.SRR520HA22_FR_Private.SRR_ECU_FCT_STATUS."
SENSOR_SRR520_RL_INPUT_FAILURE_SIGNAL_PREFIX = "Local_SRR_RL_CANFD.SRR520HA22_RL_Private.SRR_ECU_FCT_STATUS."
SENSOR_SRR520_RR_INPUT_FAILURE_SIGNAL_PREFIX = "Local_SRR_RR_CANFD.SRR520HA22_RR_Private.SRR_ECU_FCT_STATUS."

HA22_SENSOR_ARS510_OUTPUT_SIP_COMMUNICATION_E2E_ERROR_SIGNAL = "SIM VFB CEM200.ARS510.ARS510E2EFctStatus.E2E_ERROR"
HA22_SENSOR_ARS510_OUTPUT_SIP_COMMUNICATION_TIMEOUT_ERROR_SIGNAL = (
    "SIM VFB CEM200." "ARS510.ARS510E2EFctStatus.TIMEOUT_ERROR"
)

HA22_SRR520_FL_OUTPUT_SIP_COMMUNICATION_E2E_ERROR_SIGNAL = "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_fl.E2E_ERROR"
HA22_SRR520_FL_OUTPUT_SIP_COMMUNICATION_TIMEOUT_ERROR_SIGNAL = (
    "SIM VFB CEM200.SRR520." "SRR520E2EFctStatus_fl.TIMEOUT_ERROR"
)

HA22_SRR520_FR_OUTPUT_SIP_COMMUNICATION_E2E_ERROR_SIGNAL = "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_fr.E2E_ERROR"
HA22_SRR520_FR_OUTPUT_SIP_COMMUNICATION_TIMEOUT_ERROR_SIGNAL = (
    "SIM VFB CEM200.SRR520." "SRR520E2EFctStatus_fr.TIMEOUT_ERROR"
)

HA22_SRR520_RL_OUTPUT_SIP_COMMUNICATION_E2E_ERROR_SIGNAL = "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_rl.E2E_ERROR"
HA22_SRR520_RL_OUTPUT_SIP_COMMUNICATION_TIMEOUT_ERROR_SIGNAL = (
    "SIM VFB CEM200." "SRR520.SRR520E2EFctStatus_rl.TIMEOUT_ERROR"
)

HA22_SRR520_RR_OUTPUT_SIP_COMMUNICATION_E2E_ERROR_SIGNAL = "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_rr.E2E_ERROR"
HA22_SRR520_RR_OUTPUT_SIP_COMMUNICATION_TIMEOUT_ERROR_SIGNAL = (
    "SIM VFB CEM200.SRR520." "SRR520E2EFctStatus_rr.TIMEOUT_ERROR"
)

HA22_VEHICLE_SIP_SIG_STATUS_CAMERA_RMF_SIGNAL = "ADC4xx.Valeo.sRoadPatch.sSigHeader.eSigStatus"

# HA22 INPUT CAMERA FAILURE SIGNAL Dictionary mapping as the signals do not change except PREFIX
# ----------------------------------------------------------------------------------------------------------------------
SENSOR_CAMERA_VALEO_INPUT_FAILURE_SIGNAL_PREFIX = "Local_Valeo_CANFD.VSS-FC_Private."

# HA22 INPUT ARS SIGNAL PREFIX
# ----------------------------------------------------------------------------------------------------------------------
SENSOR_ARS510_SIGNAL_PREFIX = "Local_ARS_CANFD.ARS510HA22_Private."

HA22_SENSOR_CAMERA_VALEO_OUTPUT_SIP_COMMUNICATION_E2E_ERROR_SIGNAL = "SIM VFB CEM200.Valeo.ValeoE2EFctStatus.E2E_ERROR"
HA22_SENSOR_CAMERA_VALEO_OUTPUT_SIP_COMMUNICATION_TIMEOUT_ERROR_SIGNAL = (
    "SIM VFB CEM200.Valeo." "ValeoE2EFctStatus.TIMEOUT_ERROR"
)
HA22_VEHICLE_FAILURE_STATUS_CAMERA_SIGNAL = "ADC4xx.FDP_21P.FDP_SystemStatusADCU.sigCameraPlausibilityFailureStatus"

# HA22 OUTPUT SIG STATUS SIGNAL
# ----------------------------------------------------------------------------------------------------------------------
HA22_OUTPUT_SIP_SIG_STATUS_ARS_SEF_SIGNAL = "SIM VFB CEM200.ARS510.AgpPolySetFreespaceARS510.sSigHeader.eSigStatus"
HA22_OUTPUT_SIP_SIG_STATUS_ARS_RMF_SIGNAL = "SIM VFB CEM200.ARS510.RoadPatchARS510.sSigHeader.eSigStatus"

HA22_OUTPUT_SIP_SIG_STATUS_CAMERA_RMF_SIGNAL = "SIM VFB CEM200.Valeo.sRoadPatch.sSigHeader.eSigStatus"
HA22_OUTPUT_SIG_STATUS_SRR520_SEF_SIGNAL = "SIM VFB CEM200.SRR520.syncRef.sig_m_SrrFreespaceInfoSyncRef"
HA22_OUTPUT_SIP_SIG_STATUS_CAMERA_TPF_SIGNAL = "SIM VFB CEM200.Valeo.tpfCartesianObjectList.sigHeader.eSigStatus"
HA22_OUTPUT_SIP_SIG_STATUS_ARS_TPF_SIGNAL = "SIM VFB CEM200.ARS510.tpfCartesianObjectList.sigHeader.eSigStatus"
HA22_OUTPUT_SIP_SIG_STATUS_SRR_FL_TPF_SIGNAL = "SIM VFB CEM200.SRR520.tpfCartesianObjectList_fl.sigHeader.eSigStatus"
HA22_OUTPUT_SIP_SIG_STATUS_SRR_FR_TPF_SIGNAL = "SIM VFB CEM200.SRR520.tpfCartesianObjectList_fr.sigHeader.eSigStatus"
HA22_OUTPUT_SIP_SIG_STATUS_SRR_RL_TPF_SIGNAL = "SIM VFB CEM200.SRR520.tpfCartesianObjectList_rl.sigHeader.eSigStatus"
HA22_OUTPUT_SIP_SIG_STATUS_SRR_RR_TPF_SIGNAL = "SIM VFB CEM200.SRR520.tpfCartesianObjectList_rr.sigHeader.eSigStatus"
HA22_OUTPUT_SIG_STATUS_ARS_EMO_SIGNAL = "SIM VFB CEM200.ARS510.EmoCemARS510.signalHeader.eSigStatus"
HA22_OUTPUT_SIG_STATUS_EMF_SIGNAL = "SIM VFB CEM200.EMF.EmfGlobalTimestamp.SigHeader.eSigStatus"
HA22_OUTPUT_SIG_STATUS_EMF_ERROR_SIGNAL = "SIM VFB CEM200.EMF.EmfReceivedErrors.m_signalHeader.eSigStatus"
HA22_OUTPUT_SIG_STATUS_SEF_OUTPUT_SIGNAL = "SIM VFB CEM200.SEF.SefOutput.signalHeader.eSigStatus"

# HA22 DEM SIGNALS
# ----------------------------------------------------------------------------------------------------------------------

HA22_CEM_FDP21P_DEM_VALEO_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_DemCameraStatus.sigCameraPlausibilityDemStatus"
HA22_CEM_FDP21P_DEM_TEMPORARY_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_DemCemTemporaryStatus.cemTemporayFailureDemStatus"
HA22_CEM_FDP21P_DEM_PERMANENT_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_DemCemPermanentStatus.cempermanentFailureDemStatus"
HA22_CEM_FDP21P_DEM_ODOMETRY_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_DemOdometryRadarStatus." "sigOdometryAdcuPlausibilityDemStatus"
)
HA22_CEM_FDP21P_DEM_ARS_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_DemFrontRadarStatus.sigFrontRadarPlausibilityDemStatus"
HA22_CEM_FDP21P_DEM_SRR_RR_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_DemRearRightRadarStatus." "sigRearRightRadarPlausibilityDemStatus"
)
HA22_CEM_FDP21P_DEM_SRR_RL_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_DemRearLeftRadarStatus." "sigReartLeftRadarPlausibilityDemStatus"
)
HA22_CEM_FDP21P_DEM_SRR_FR_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_DemFrontRightRadarStatus." "sigFrontRightRadarPlausibilityDemStatus"
)
HA22_CEM_FDP21P_DEM_SRR_FL_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_DemFrontleftRadarStatus." "sigFrontLeftRadarPlausibilityDemStatus"
)

# HA22 OUTPUT PERCEPTION RANGE SIGNAL
# ----------------------------------------------------------------------------------------------------------------------
HA22_OUTPUT_PERCEPTION_RANGE_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_ValidityData.positionX"

# HA22 OUTPUT FAILURE STATUS SIGNAL
# ----------------------------------------------------------------------------------------------------------------------
HA22_OUTPUT_FAILURE_STATUS_ARS_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigFrontRadarPlausibilityFailureStatus"
)

HA22_OUTPUT_FAILURE_STATUS_CAMERA_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigCameraPlausibilityFailureStatus"
)

HA22_OUTPUT_FAILURE_STATUS_SRR520_FL_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigFrontLeftRadarPlausibilityFailureStatus"
)
HA22_OUTPUT_FAILURE_STATUS_SRR520_FR_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigFrontRightRadarPlausibilityFailureStatus"
)
HA22_OUTPUT_FAILURE_STATUS_SRR520_RL_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigRearLeftRadarPlausibilityFailureStatus"
)
HA22_OUTPUT_FAILURE_STATUS_SRR520_RR_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigRearRightRadarPlausibilityFailureStatus"
)
HA22_OUTPUT_FAILURE_STATUS_ODOMETRY_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigOdometryAdcuPlausibilityFailureStatus"
)

HA22_OUTPUT_CEM_ALCA_STATUS_LEFT = "SIM VFB CEM200.FDP_21P.FDP_AlcaPermissionLeft.CemAlcaPermissionLeftStatus"
HA22_OUTPUT_CEM_ALCA_STATUS_RIGHT = "SIM VFB CEM200.FDP_21P.FDP_AlcaPermissionRight.CemAlcaPermissionRightStatus"

HA22_INPUT_LONGITUDINAL_ADCU_VDY_SIGNAL = "ADC4xx.IPVDY.VehDyn_t.Longitudinal.Accel"

# HA22 FDP_BASE
# ----------------------------------------------------------------------------------------------------------------------
HA22_SIM_FDP_BASE_TPF_MEASUREMENT_COUNTER = "SIM VFB CEM200.FDP_Base.p_TpfOutputIf.sSigHeader.uiMeasurementCounter"
HA22_SIM_FDP_BASE_VAL_MEASUREMENT_COUNTER = "SIM VFB CEM200.FDP_Base.p_ValOutputIf.sSigHeader.uiMeasurementCounter"
HA22_SIM_FDP_BASE_EML_MEASUREMENT_COUNTER = (
    "SIM VFB CEM200.EML.EmlOutput.egoVehKinematic.sigHeader." "uiMeasurementCounter"
)
HA22_SIM_FDP_BASE_RMF_MEASUREMENT_COUNTER = (
    "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.sMetaData." "sSigHeader.uiMeasurementCounter"
)
HA22_SIM_FDP_BASE_SEF_MEASUREMENT_COUNTER = "SIM VFB CEM200.FDP_Base.p_FsfOutputIf.sSigHeader.uiCycleCounter"

HA22_VEHICLE_FDP_BASE_TPF_MEASUREMENT_COUNTER = "ADC4xx.FDP_Base.p_TpfOutputIf.sSigHeader.uiMeasurementCounter"
HA22_VEHICLE_FDP_BASE_VAL_MEASUREMENT_COUNTER = "ADC4xx.FDP_Base.p_ValOutputIf.sSigHeader.uiMeasurementCounter"
HA22_VEHICLE_FDP_BASE_EML_MEASUREMENT_COUNTER = "ADC4xx.FDP_Base.p_EmlOutputIf.sigHeader.uiMeasurementCounter"
HA22_VEHICLE_FDP_BASE_RMF_MEASUREMENT_COUNTER = (
    "ADC4xx.FDP_Base.p_RmfOutputIf.sMetaData.sSigHeader." "uiMeasurementCounter"
)
HA22_VEHICLE_FDP_BASE_SEF_MEASUREMENT_COUNTER = "ADC4xx.FDP_Base.p_FsfOutputIf.sSigHeader.uiMeasurementCounter"

HA22_SIM_FDP_BASE_TPF_TIMESTAMP = "SIM VFB CEM200.FDP_Base.p_TpfOutputIf.sSigHeader.uiTimeStamp"
HA22_SIM_FDP_BASE_VAL_TIMESTAMP = "SIM VFB CEM200.FDP_Base.p_ValOutputIf.sSigHeader.uiTimeStamp"
HA22_SIM_FDP_BASE_EML_TIMESTAMP = "SIM VFB CEM200.EML.EmlOutput.egoVehKinematic.sigHeader.uiTimeStamp"
HA22_SIM_FDP_BASE_RMF_TIMESTAMP = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.sMetaData.sSigHeader.uiTimeStamp"
HA22_SIM_FDP_BASE_SEF_TIMESTAMP = "SIM VFB CEM200.FDP_Base.p_FsfOutputIf.sSigHeader.uiTimeStamp"

HA22_VEHICLE_FDP_BASE_TPF_TIMESTAMP = "ADC4xx.FDP_Base.p_TpfOutputIf.sSigHeader.uiTimeStamp"
HA22_VEHICLE_FDP_BASE_VAL_TIMESTAMP = "ADC4xx.FDP_Base.p_ValOutputIf.sSigHeader.uiTimeStamp"
HA22_VEHICLE_FDP_BASE_EML_TIMESTAMP = "ADC4xx.FDP_Base.p_EmlOutputIf.sigHeader.uiTimeStamp"
HA22_VEHICLE_FDP_BASE_RMF_TIMESTAMP = "ADC4xx.FDP_Base.p_RmfOutputIf.sMetaData.sSigHeader.uiTimeStamp"
HA22_VEHICLE_FDP_BASE_SEF_TIMESTAMP = "ADC4xx.FDP_Base.p_FsfOutputIf.sSigHeader.uiTimeStamp"
#  HA22 FDP BASE RMF SIGNALS
# ----------------------------------------------------------------------------------------------------------------------
HA22_FDP_BASE_RMF_LINEAR_OBJ = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.numLinearObjects"
HA22_FDP_BASE_RMF_POINTS = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.numPoints"
HA22_FDP_BASE_RMF_ASSOCIATION_BOUNDRY = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.associations.numBoundaryContinuity"
HA22_FDP_BASE_RMF_ASSOCIATION_LANE = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.associations.numLaneCounts"
HA22_FDP_BASE_RMF_ASSOCIATION_SENSOR = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.associations.numSensorAssociations"
HA22_FDP_BASE_RMF_ASSOCIATION_SLOPE = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.associations.numSlopes"
HA22_FDP_BASE_RMF_LANE_TOPOLOGY_CONNECTION = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.laneTopology.numConnections"
HA22_FDP_BASE_RMF_LANE_TOPOLOGY_SEGMENT = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.laneTopology.numLaneSegments"
HA22_FDP_BASE_RMF_ROAD_TOPOLOGY_CONNECTION = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.roadTopology.numConnections"
HA22_FDP_BASE_RMF_ROAD_TOPOLOGY_SEGMENT = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.roadTopology.numRoadSegments"

# HA22 SENSOR OBJECTS FOV
# ----------------------------------------------------------------------------------------------------------------------
HA22_ARS_SENSOR_OBJECTS_FOV = "SIM VFB CEM200.ARS510.tpfCartesianObjectList.objects[0].objectDynamics.position.posX"
HA22_VALEO_SENSOR_OBJECTS_FOV = "SIM VFB CEM200.Valeo.tpfCartesianObjectList.objects[0].objectDynamics.position.posX"
HA22_SRR_FL_SENSOR_OBJECTS_FOV = (
    "SIM VFB CEM200.SRR520.tpfCartesianObjectList_fl.objects[0]." "objectDynamics.position.posX"
)
HA22_SRR_FR_SENSOR_OBJECTS_FOV = (
    "SIM VFB CEM200.SRR520.tpfCartesianObjectList_fr.objects[0]" ".objectDynamics.position.posX"
)
HA22_SRR_RL_SENSOR_OBJECTS_FOV = (
    "SIM VFB CEM200.SRR520.tpfCartesianObjectList_rl.objects[0]" ".objectDynamics.position.posX"
)
HA22_SRR_RR_SENSOR_OBJECTS_FOV = (
    "SIM VFB CEM200.SRR520.tpfCartesianObjectList_rr.objects[0]" ".objectDynamics.position.posX"
)

# HA22 Odometry Signal
# ----------------------------------------------------------------------------------------------------------------------
HA22_INPUT_ARS_VDY_SIGNAL_PREFIX = "Local_ARS_CANFD.ARS510HA22_Private.ARS_VDY."

HA22_INPUT_SRR520_FL_VDY_SIGNAL_PREFIX = "Local_SRR_FL_CANFD.SRR520HA22_FL_Private.SRR_VDY."
HA22_INPUT_SRR520_FR_VDY_SIGNAL_PREFIX = "Local_SRR_FR_CANFD.SRR520HA22_FR_Private.SRR_VDY."
HA22_INPUT_SRR520_RL_VDY_SIGNAL_PREFIX = "Local_SRR_RL_CANFD.SRR520HA22_RL_Private.SRR_VDY."
HA22_INPUT_SRR520_RR_VDY_SIGNAL_PREFIX = "Local_SRR_RR_CANFD.SRR520HA22_RR_Private.SRR_VDY."

ADC420HA22_FUNCTIONAL_TEST_JSON_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA22/helper_files/" "ADC420HA22_FunctionalTest.json"
)
ADC420HA33_FUNCTIONAL_TEST_JSON_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA33/helper_files/" "ADC420HA33_FunctionalTest.json"
)
ADC420HA22_SAFETY_TEST_XML_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA22/helper_files/" "ADC420HA22_Safety.xml"
)
ADC420HA22_SIGNAL_TEST_SEF_JSON_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA22/helper_files/" "SignalTestConfig_SEF.json"
)
ADC420HA22_SIGNAL_TEST_TPF_JSON_PATH = (
    "trc/evaluation/functional_test_helper/" "helper_files/ARS540BW11/SignalTestConfig_TPF.json"
)
ADC420HA33_SIGNAL_TEST_TPF_JSON_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA33/helper_files/" "ADC420HA33_FunctionalTest.json"
)

ARS540BW11_FUNCTIONAL_TEST_JSON_PATH = (
    "trc/evaluation/functional_test_cases/ARS540BW11/helper_files/" "ARS540BW11_FunctionalTest.json"
)

ARS540BW11_FUNCTIONAL_TEST_XML_PATH = "trc/evaluation/functional_test_cases/ARS540BW11/helper_files/"

KB_FUNCTIONAL_TEST_JSON_PATH = "trc/evaluation/functional_test_helper/helper_files/MFC525CM10/KB_FunctionalTest.json"
KB_SIGNAL_TEST_JSON_PATH = "trc/evaluation/functional_test_helper/helper_files/ARS540BW11/SignalTestConfig_KB.json"

ARS540BW11_RANGE_CHECK_ARS540_XML_PATH = (
    "trc/evaluation/functional_test_helper/" "helper_files/ARS540BW11/range_check_ars540.xml"
)
ARS540BW11_RANGE_CHECK_MFC_APTIV_XML_PATH = (
    "trc/evaluation/functional_test_helper/" "helper_files/ARS540BW11/range_check_mfc_aptiv.xml"
)
ARS540BW11_RANGE_CHECK_SRR_APTIV_XML_PATH = (
    "trc/evaluation/functional_test_helper/" "helper_files/ARS540BW11/range_check_srr_aptiv.xml"
)
ARS540BW11_RANGE_CHECK_FDP_BASE_XML_PATH = (
    "trc/evaluation/functional_test_helper/" "helper_files/ARS540BW11/range_check_fdp_base.xml"
)
# XML files of range check path

ADC420HA22_RANGE_CHECK_FDP_BASE_XML_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA22/helper_files/" "range_check_fdp_base.xml"
)
ADC420HA22_RANGE_CHECK_FDP_21P_XML_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA22/helper_files/" "range_check_fdp_21p.xml"
)
ADC420HA22_RANGE_CHECK_IPVDY_XML_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA22/helper_files/" "range_check_ipvdy.xml"
)
ADC420HA22_RANGE_CHECK_ARS510_XML_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA22/helper_files/" "range_check_ars510.xml"
)
ADC420HA22_RANGE_CHECK_SRR520_XML_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA22/helper_files/" "range_check_srr520.xml"
)
ADC420HA22_RANGE_CHECK_VALEO_XML_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA22/helper_files/" "range_check_valeo.xml"
)

ADC420HA33_RANGE_CHECK_FDP_BASE_XML_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA33/helper_files/" "range_check_fdp_base.xml"
)
ADC420HA33_RANGE_CHECK_FDP_21P_XML_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA33/helper_files/" "range_check_fdp_21p.xml"
)
ADC420HA33_RANGE_CHECK_IPVDY_XML_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA33/helper_files/" "range_check_ipvdy.xml"
)
ADC420HA33_RANGE_CHECK_ARS510_XML_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA33/helper_files/" "range_check_ars510.xml"
)
ADC420HA33_RANGE_CHECK_SRR520_XML_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA33/helper_files/" "range_check_srr520.xml"
)
ADC420HA33_RANGE_CHECK_VALEO_XML_PATH = (
    "trc/evaluation/functional_test_cases/ADC420HA33/helper_files/" "range_check_valeo.xml"
)

HA22_ARS_FRSP_ITEMS_PREFIX = "Local_ARS_CANFD.ARS510HA22_Private.ARS_FRSP_ITEMS_"
HA33_ARS_FRSP_ITEMS_PREFIX = "Local_ARS_CANFD.ARS510HA33_Privat.ARS_FRSP_ITEMS_"
HA22_ARS_FRSP_VERTEX_PREFIX = "Local_ARS_CANFD.ARS510HA22_Private.ARS_FRSP_VERTEX_"
HA33_ARS_FRSP_VERTEX_PREFIX = "Local_ARS_CANFD.ARS510HA33_Privat.ARS_FRSP_VERTEX_"

HA22_ARS_OBJECT_PREFIX = "Local_ARS_CANFD.ARS510HA22_Private.ARS_OBJ_"
HA33_ARS_OBJECT_PREFIX = "Local_ARS_CANFD.ARS510HA33_Private.ARS_OBJ_"

HA22_SRR_FL_OBJECT_PREFIX = "Local_SRR_FL_CANFD.SRR520HA22_FL_Private.SRR_OBJ_"
HA22_SRR_FR_OBJECT_PREFIX = "Local_SRR_FR_CANFD.SRR520HA22_FR_Private.SRR_OBJ_"
HA22_SRR_RL_OBJECT_PREFIX = "Local_SRR_RL_CANFD.SRR520HA22_RL_Private.SRR_OBJ_"
HA22_SRR_RR_OBJECT_PREFIX = "Local_SRR_RR_CANFD.SRR520HA22_RR_Private.SRR_OBJ_"

HA33_SRR_FL_OBJECT_PREFIX = "Local_SRR_FL_CANFD.SRR520HA33_FL_Private.SRR_OBJ_"
HA33_SRR_FR_OBJECT_PREFIX = "Local_SRR_FR_CANFD.SRR520HA33_FR_Private.SRR_OBJ_"
HA33_SRR_RL_OBJECT_PREFIX = "Local_SRR_RL_CANFD.SRR520HA33_RL_Private.SRR_OBJ_"
HA33_SRR_RR_OBJECT_PREFIX = "Local_SRR_RR_CANFD.SRR520HA33_RR_Private.SRR_OBJ_"

HA22_SRR_OBJECT_PREFIX = "SRR_OBJ_"
HA22_SRR_FRSP_ITEMS_PREFIX = "SRR_FRSP_ITEMS_"
HA22_SRR_FRSP_VERTEX_PREFIX = "SRR_FRSP_VERTEX_"

HA22_CAMERA_VALEO_OBJECT_PREFIX = "Local_Valeo_CANFD.VSS-FC_Private.OIF_Info"
HA33_CAMERA_VALEO_OBJECT_PREFIX = "Local_Valeo_CANFD.VSS-FC_Private.OIF_Info"

HA22_CEM_FDP_21P_TPF_PREFIX = "SIM VFB CEM200.FDP_21P"
HA22_CEM_FDP_Base_TPF_PREFIX = "SIM VFB CEM200.FDP_Base"
HA22_CEM_FDP_21P_SEF_PREFIX = "SIM VFB CEM200.FDP_21P"

ICD_COLUMN_SIGNAL_NAME = "_Signal Name"
ICD_COLUMN_MAX_RANGE = "phy. Max. Range"
ICD_COLUMN_MIN_RANGE = "phy. Min. Range"
ICD_COLUMN_RANGE_MONITOR = "RangeMonitor"
ICD_COLUMN_FACTOR = "Factor"
ICD_COLUMN_DEFAULT = "default"
ICD_COLUMN_TESTNAME = "test name"

HA22_ICD_EXCEL_FOLDER_PATH = "scripts/adc420ha22/ICD"
HA33_ICD_EXCEL_FOLDER_PATH = "scripts/adc420ha33/ICD"
ICD_EXCEL_FOLDER_PATH = "scripts/{}/ICD"
TRC_MTS_CONFIG_PATH = "config/mts/{}"
HA22_SAFETY_XMLS_PATH = "data/adc420ha22/Input Out of range/CFG+XML/FUSION_PERCEPTION_NOT_ALL_CLUSTERS"
HA22_ALL_SAFETY_XMLS_PATH = "data/adc420ha22/Input Out of range/CFG+XML/ALL_CLUSTERS"
HA22_TRC_MTS_CONFIG_PATH = "config/mts/ADC420HA22"
HA33_TRC_MTS_CONFIG_PATH = "config/mts/ADC420HA33"

SENSOR_ARS510_INPUT_FAILURE_SIGNAL_PREFIX_HA33 = "Local_ARS_CANFD.ARS510HA33_Private.ARS_ECU_FCT_STATUS."

SENSOR_SRR520_FL_INPUT_FAILURE_SIGNAL_PREFIX_HA33 = "Local_SRR_FL_CANFD.SRR520HA33_FL_Private.SRR_ECU_FCT_STATUS."
SENSOR_SRR520_FR_INPUT_FAILURE_SIGNAL_PREFIX_HA33 = "Local_SRR_FR_CANFD.SRR520HA33_FR_Private.SRR_ECU_FCT_STATUS."
SENSOR_SRR520_RL_INPUT_FAILURE_SIGNAL_PREFIX_HA33 = "Local_SRR_RL_CANFD.SRR520HA33_RL_Private.SRR_ECU_FCT_STATUS."
SENSOR_SRR520_RR_INPUT_FAILURE_SIGNAL_PREFIX_HA33 = "Local_SRR_RR_CANFD.SRR520HA33_RR_Private.SRR_ECU_FCT_STATUS."

HA33_TOW_MODE_SIGNAL = "Global_Vehicle_CAN2_HS.Global_CAN_RVU_Ch2_HS.IMG_22B."

SENSOR_CAMERA_VALEO_INPUT_FAILURE_SIGNAL_PREFIX_HA33 = "Local_Valeo_CANFD.VSS-FC_Private."
# E2E AND TIMEOUT INPUT SIGNALS
# ----------------------------------------------------------------------------------------------------------------------
E2E_ARS_INPUT_SIGNAL_FREESPACE = "SIM VFB CEM200.ARS510.ARS510E2EFreeSpace.E2E_ERROR"
E2E_ARS_INPUT_SIGNAL_RADAR_STATUS = "SIM VFB CEM200.ARS510.ARS510E2EFctStatus.E2E_ERROR"
E2E_ARS_INPUT_SIGNAL_TPF = "SIM VFB CEM200.ARS510.ARS510E2EObjectList.E2E_ERROR"
E2E_ARS_INPUT_SIGNAL_RMF = "SIM VFB CEM200.ARS510.ARS510E2ERoad.E2E_ERROR"
E2E_ARS_INPUT_SIGNAL_VDY = "SIM VFB CEM200.ARS510.ARS510E2EVdy.E2E_ERROR"

TIMEOUT_ARS_INPUT_SIGNAL_FREESPACE = "SIM VFB CEM200.ARS510.ARS510E2EFreeSpace.TIMEOUT_ERROR"
TIMEOUT_ARS_INPUT_SIGNAL_RADAR_STATUS = "SIM VFB CEM200.ARS510.ARS510E2EFctStatus.TIMEOUT_ERROR"
TIMEOUT_ARS_INPUT_SIGNAL_TPF = "SIM VFB CEM200.ARS510.ARS510E2EObjectList.TIMEOUT_ERROR"
TIMEOUT_ARS_INPUT_SIGNAL_RMF = "SIM VFB CEM200.ARS510.ARS510E2ERoad.TIMEOUT_ERROR"
TIMEOUT_ARS_INPUT_SIGNAL_VDY = "SIM VFB CEM200.ARS510.ARS510E2EVdy.TIMEOUT_ERROR"

E2E_SRR_FL_INPUT_SIGNAL_FREESPACE = "SIM VFB CEM200.SRR520.SRR520E2EFreespace_fl.E2E_ERROR"
E2E_SRR_FL_INPUT_SIGNAL_TPF = "SIM VFB CEM200.SRR520.SRR520E2EObjectList_fl.E2E_ERROR"
E2E_SRR_FL_INPUT_SIGNAL_RADAR_STATUS = "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_fl.E2E_ERROR"
E2E_SRR_FL_INPUT_SIGNAL_VDY = "SIM VFB CEM200.SRR520.SRR520E2EVdy_fl.E2E_ERROR"

TIMEOUT_SRR_FL_INPUT_SIGNAL_FREESPACE = "SIM VFB CEM200.SRR520.SRR520E2EFreespace_fl.TIMEOUT_ERROR"
TIMEOUT_SRR_FL_INPUT_SIGNAL_TPF = "SIM VFB CEM200.SRR520.SRR520E2EObjectList_fl.TIMEOUT_ERROR"
TIMEOUT_SRR_FL_INPUT_SIGNAL_RADAR_STATUS = "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_fl.TIMEOUT_ERROR"
TIMEOUT_SRR_FL_INPUT_SIGNAL_VDY = "SIM VFB CEM200.SRR520.SRR520E2EVdy_fl.TIMEOUT_ERROR"

E2E_SRR_FR_INPUT_SIGNAL_FREESPACE = "SIM VFB CEM200.SRR520.SRR520E2EFreespace_fr.E2E_ERROR"
E2E_SRR_FR_INPUT_SIGNAL_TPF = "SIM VFB CEM200.SRR520.SRR520E2EObjectList_fr.E2E_ERROR"
E2E_SRR_FR_INPUT_SIGNAL_RADAR_STATUS = "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_fr.E2E_ERROR"
E2E_SRR_FR_INPUT_SIGNAL_VDY = "SIM VFB CEM200.SRR520.SRR520E2EVdy_fr.E2E_ERROR"

TIMEOUT_SRR_FR_INPUT_SIGNAL_FREESPACE = "SIM VFB CEM200.SRR520.SRR520E2EFreespace_fr.TIMEOUT_ERROR"
TIMEOUT_SRR_FR_INPUT_SIGNAL_TPF = "SIM VFB CEM200.SRR520.SRR520E2EObjectList_fr.TIMEOUT_ERROR"
TIMEOUT_SRR_FR_INPUT_SIGNAL_RADAR_STATUS = "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_fr.TIMEOUT_ERROR"
TIMEOUT_SRR_FR_INPUT_SIGNAL_VDY = "SIM VFB CEM200.SRR520.SRR520E2EVdy_fr.TIMEOUT_ERROR"

E2E_SRR_RL_INPUT_SIGNAL_FREESPACE = "SIM VFB CEM200.SRR520.SRR520E2EFreespace_rl.E2E_ERROR"
E2E_SRR_RL_INPUT_SIGNAL_TPF = "SIM VFB CEM200.SRR520.SRR520E2EObjectList_rl.E2E_ERROR"
E2E_SRR_RL_INPUT_SIGNAL_RADAR_STATUS = "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_rl.E2E_ERROR"
E2E_SRR_RL_INPUT_SIGNAL_VDY = "SIM VFB CEM200.SRR520.SRR520E2EVdy_rl.E2E_ERROR"

TIMEOUT_SRR_RL_INPUT_SIGNAL_FREESPACE = "SIM VFB CEM200.SRR520.SRR520E2EFreespace_rl.TIMEOUT_ERROR"
TIMEOUT_SRR_RL_INPUT_SIGNAL_TPF = "SIM VFB CEM200.SRR520.SRR520E2EObjectList_rl.TIMEOUT_ERROR"
TIMEOUT_SRR_RL_INPUT_SIGNAL_RADAR_STATUS = "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_rl.TIMEOUT_ERROR"
TIMEOUT_SRR_RL_INPUT_SIGNAL_VDY = "SIM VFB CEM200.SRR520.SRR520E2EVdy_rl.TIMEOUT_ERROR"

E2E_SRR_RR_INPUT_SIGNAL_FREESPACE = "SIM VFB CEM200.SRR520.SRR520E2EFreespace_rr.E2E_ERROR"
E2E_SRR_RR_INPUT_SIGNAL_TPF = "SIM VFB CEM200.SRR520.SRR520E2EObjectList_rr.E2E_ERROR"
E2E_SRR_RR_INPUT_SIGNAL_RADAR_STATUS = "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_rr.E2E_ERROR"
E2E_SRR_RR_INPUT_SIGNAL_VDY = "SIM VFB CEM200.SRR520.SRR520E2EVdy_rr.E2E_ERROR"

TIMEOUT_SRR_RR_INPUT_SIGNAL_FREESPACE = "SIM VFB CEM200.SRR520.SRR520E2EFreespace_rr.TIMEOUT_ERROR"
TIMEOUT_SRR_RR_INPUT_SIGNAL_TPF = "SIM VFB CEM200.SRR520.SRR520E2EObjectList_rr.TIMEOUT_ERROR"
TIMEOUT_SRR_RR_INPUT_SIGNAL_RADAR_STATUS = "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_rr.IS_UPDATED"
TIMEOUT_SRR_RR_INPUT_SIGNAL_VDY = "SIM VFB CEM200.SRR520.SRR520E2EVdy_rr.TIMEOUT_ERROR"

E2E_VALEO_INPUT_RADAR_STATUS = "SIM VFB CEM200.Valeo.ValeoE2EFctStatus.E2E_ERROR"
E2E_VALEO_INPUT_RADAR_TPF = "SIM VFB CEM200.Valeo.ValeoE2EObjectList.E2E_ERROR"
E2E_VALEO_INPUT_RADAR_RMF = "SIM VFB CEM200.Valeo.ValeoE2ELanes.E2E_ERROR"

TIMEOUT_VALEO_INPUT_RADAR_STATUS = "SIM VFB CEM200.Valeo.ValeoE2EFctStatus.TIMEOUT_ERROR"
TIMEOUT_VALEO_INPUT_RADAR_TPF = "SIM VFB CEM200.Valeo.ValeoE2EObjectList.TIMEOUT_ERROR"
TIMEOUT_VALEO_INPUT_RADAR_RMF = "SIM VFB CEM200.Valeo.ValeoE2ELanes.TIMEOUT_ERROR"

E2E_ERROR_FLAG_STATE_ONE = 1.0
E2E_ERROR_FLAG_STATE_ZERO = 0
TIMEOUT_ERROR_FLAG_STATE_ONE = 1.0
TIMEOUT_ERROR_FLAG_STATE_ZERO = 0

HA33_VDY_DELAY_33CYCLES = "33 Cycle Delay"
HA33_DEM_OUTPUT_STATE = "DEM Output State"

HA33_CEM_DEM_TEMP_SET_STATE = 1.0

# HA33 INPUT Sig Status Signal
# ----------------------------------------------------------------------------------------------------------------------
HA33_INPUT_SIG_STATUS_ARS_TPF_SIGNAL = "Local_ARS_CANFD.ARS510HA33_Private.ARS_OBJ_STATUS.SigStatus_OBJ_STS"
HA33_INPUT_SIG_STATUS_ARS_SEF_SIGNAL = "Local_ARS_CANFD.ARS510HA33_Private.ARS_FRSP_HEADER.SigStatus_FRSP"
HA33_INPUT_SIG_STATUS_ARS_RMF_SIGNAL = "Local_ARS_CANFD.ARS510HA33_Private.ARS_ROAD.eSigStatus_RD"

HA33_INPUT_SIG_STATUS_SRR520_FL_TPF_SIGNAL = "Local_SRR_FL_CANFD.SRR520HA33_FL_Private.SRR_OBJ_STATUS.SigStatus_ObjSts"
HA33_INPUT_SIG_STATUS_SRR520_FR_TPF_SIGNAL = "Local_SRR_FR_CANFD.SRR520HA33_FR_Private.SRR_OBJ_STATUS.SigStatus_ObjSts"
HA33_INPUT_SIG_STATUS_SRR520_RL_TPF_SIGNAL = "Local_SRR_RL_CANFD.SRR520HA33_RL_Private.SRR_OBJ_STATUS.SigStatus_ObjSts"
HA33_INPUT_SIG_STATUS_SRR520_RR_TPF_SIGNAL = "Local_SRR_RR_CANFD.SRR520HA33_RR_Private.SRR_OBJ_STATUS.SigStatus_ObjSts"

# HA33 Vehicle  SIG_STATUS SIGNAL
# FDP_BASE
HA33_VEHICLE_FDP_BASE_SIG_STATUS_TPF_SIGNAL = "ADC4xx.FDP_Base.p_TpfOutputIf.sSigHeader.eSigStatus"
HA33_VEHICLE_FDP_BASE_SIG_STATUS_EML_SIGNAL = "ADC4xx.FDP_Base.p_EmlOutputIf.sigHeader.eSigStatus"
HA33_VEHICLE_FDP_BASE_SIG_STATUS_RMF_SIGNAL = "ADC4xx.FDP_Base.p_RmfOutputIf.sigHeader.eSigStatus"
HA33_VEHICLE_FDP_BASE_SIG_STATUS_SEF_SIGNAL = "ADC4xx.FDP_Base.p_FsfOutputIf.sSigHeader.eSigStatus"
HA33_VEHICLE_FDP_BASE_SIG_STATUS_VAL_SIGNAL = "ADC4xx.FDP_Base.p_ValOutputIf.sSigHeader.eSigStatus"

HA22_INPUT_TIMESTAMP_ADCU_VDY_SIGNAL = "ADC4xx.IPVDY.VehDyn_t.sSigHeader.uiTimeStamp"

# SMOKE TEST PROJECT SELECTION
PROJECT_TYPE_HA22 = "ADC420HA22"
PROJECT_TYPE_HA33 = "ADC420HA33"
PROJECT_SELECTION_HONDA = "ADC420HA33"

TEST_TYPE = ["positive"]
HA22_ONE_CYCLE_TIME = 0.04  # 40 ms one cycle time for HA22

RADAR_SENSOR_ARS510 = "Local_ARS_CANFD.ARS510HA22_Private.ARS_ECU_FCT_STATUS."
RADAR_SENSOR_SRR520_FL = "Local_SRR_FL_CANFD.SRR520HA22_FL_Private.SRR_ECU_FCT_STATUS."
RADAR_SENSOR_SRR520_FR = "Local_SRR_FR_CANFD.SRR520HA22_FR_Private.SRR_ECU_FCT_STATUS."
RADAR_SENSOR_SRR520_RL = "Local_SRR_RL_CANFD.SRR520HA22_RL_Private.SRR_ECU_FCT_STATUS."
RADAR_SENSOR_SRR520_RR = "Local_SRR_RR_CANFD.SRR520HA22_RR_Private.SRR_ECU_FCT_STATUS."
CAMERA_FAILURE_VALEO = "Local_Valeo_CANFD.VSS-FC_Private.CAM_Failure_Info"

# HA22 Start, End time of signal manipulation
# ----------------------------------------------------------------------------------------------------------------------
HA22_SIGNAL_MANIPULATION_START_TIME = 8.72  # set to default as 8.72
HA22_SIGNAL_MANIPULATION_END_TIME = 9.24  # set to default as 9.24
HA22_OUTPUT_FAILED_ACCEPTABLE_SAMPLES_COUNT = 3
# Consider above variables carefully for input out of range testing <-----------

constant_signal_dict = {
    "data.ALCAPermissionR": "CemAlcaPermissionRightStatus",
    "data.ALCAPermissionL": "CemAlcaPermissionLeftStatus",
    "::fdp_base::Cem200LongMotStates(::fdp_base::Cem200LongMotStates::LONG_MOT_STATE_MOVE)": 0,
    "::fdp_base::Cem200LongMotStates(::fdp_base::Cem200LongMotStates::LONG_MOT_STATE_STDST)": 3,
    "::fdp_base::CEM_MeasStatus(::fdp_base::CEM_MeasStatus::VERTEX_HYPOTHESIS)": 2,
    "::fdp_base::CEM_MeasStatus(::fdp_base::CEM_MeasStatus::VERTEX_MEASURED)": 0,
    "::fdp_base::CEM_HeightProperty(::fdp_base::CEM_HeightProperty::STATIC_OBSTACLE)": 0,
    "::fdp_base::CEM_HeightProperty(::fdp_base::CEM_HeightProperty::STATIC_UNDERDRIVABLE)": 2,
    # adding dummy values , check with vinod
    "::fdp_base::CEM_TP_t_ObjMaintenanceStates("
    "::fdp_base::CEM_TP_t_ObjMaintenanceStates::TP_OBJECT_MT_STATE_DELETED)": 0,
    "::fdp_base::CEM_TP_t_ObjMaintenanceStates("
    "::fdp_base::CEM_TP_t_ObjMaintenanceStates::TP_OBJECT_MT_STATE_PREDICTED)": 3,
    "cem::AlgoSignalState_t::AL_SIG_STATE_INVALID": 2,
    "::fdp_base::CEM_TP_t_ObjSplitMergeStates(::fdp_base::CEM_TP_t_ObjSplitMergeStates::TP_OBJECT_SM_STATE_NONE)": 0,
    "::fdp_base::CEM_TP_t_ObjSplitMergeStates(::fdp_base::CEM_TP_t_ObjSplitMergeStates::TP_OBJECT_SM_STATE_SPLIT)": 2,
    "::fdp_base::TP_t_ObjShapePointState(::fdp_base::TP_t_ObjShapePointState::TP_OBJECT_SHAPE_POINT_STATE_INVALID)": 0,
    "::fdp_base::TP_t_ObjShapePointState("
    "::fdp_base::TP_t_ObjShapePointState::TP_OBJECT_SHAPE_POINT_STATE_MAX_DIFF_TYPES)": 4,
    "::fdp_base::CEM_TP_t_ObjClassifications(::fdp_base::CEM_TP_t_ObjClassifications::TP_OBJECT_CLASS_POINT)": 0,
    "::fdp_base::CEM_TP_t_ObjClassifications("
    "::fdp_base::CEM_TP_t_ObjClassifications::TP_OBJECT_CLASS_MAX_DIFF_TYPES)": 10,
    "::fdp_base::CEM_TP_t_ObjDynamicProperties("
    "::fdp_base::CEM_TP_t_ObjDynamicProperties::TP_OBJECT_DYN_PROPERTY_MOVING)": 0,
    "::fdp_base::CEM_TP_t_ObjDynamicProperties("
    "::fdp_base::CEM_TP_t_ObjDynamicProperties::TP_OBJECT_DYN_PROPERTY_STOPPED)": 6,
    "::fdp_base::CEM_TP_t_ObjStatusBrakeLight("
    "::fdp_base::CEM_TP_t_ObjStatusBrakeLight::TP_ADD_ATTR_OBJ_BRAKE_LIGHT_UNKNOWN)": 0,
    "::fdp_base::CEM_TP_t_ObjStatusBrakeLight("
    "::fdp_base::CEM_TP_t_ObjStatusBrakeLight::TP_ADD_ATTR_OBJ_BRAKE_LIGHT_HEAVY_BREAKING)": 3,
    "::fdp_base::CEM_TP_t_ObjStatusTurnIndicator("
    "::fdp_base::CEM_TP_t_ObjStatusTurnIndicator::TP_ADD_ATTR_OBJ_TURN_INDICATOR_UNKNOWN)": 0,
    "::fdp_base::CEM_TP_t_ObjStatusTurnIndicator("
    "::fdp_base::CEM_TP_t_ObjStatusTurnIndicator::TP_ADD_ATTR_OBJ_TURN_INDICATOR_HAZARD_FLASHING)": 4,
    "::fdp_base::CEM_TP_t_ObjStatusTurnIndicator("
    "::fdp_base::CEM_TP_t_ObjStatusTurnIndicator::TP_ADD_ATTR_OBJ_TURN_INDICATOR_SNA)": 255,
    "::fdp_base::TP_t_ObjOcclusionStates(::fdp_base::TP_t_ObjOcclusionStates::TP_OBJECT_OCCL_NONE)": 0,
    "::fdp_base::TP_t_ObjOcclusionStates(::fdp_base::TP_t_ObjOcclusionStates::TP_OBJECT_OCCL_FULL)": 3,
    "::fdp_base::CEM_AlgoSignalState_t(::fdp_base::CEM_AlgoSignalState_t::AL_SIG_STATE_OK)": 1,
    "::fdp_base::CohLaneAssocState_t(::fdp_base::CohLaneAssocState_t::COH_ASSOC_STATE_INVALID)": 0,
    "::fdp_base::LaneAssignment_t(::fdp_base::LaneAssignment_t::UNKNOWN_REGION)": 0,
    "::fdp_base::LaneAssignment_t(::fdp_base::LaneAssignment_t::R2)": 5,
    "::fdp_base::AlgoSignalState_t(::cem::AlgoSignalState_t::AL_SIG_STATE_OK)": 1,
    "::fdp_base::AlgoSignalState_t(::cem::AlgoSignalState_t::AL_SIG_STATE_INVALID)": 2,
    "::fdp_base::linearObjectTypeEnum(::fdp_base::linearObjectTypeEnum::LINOBJTYPE_INVALID)": 0,
    "::fdp_base::linearObjectTypeEnum(::fdp_base::linearObjectTypeEnum::LINOBJTYPE_PYLON)": 9,
    "::fdp_base::subTypeEnum(::fdp_base::subTypeEnum::RMF_UNSPECIFIED)": 0,
    "::fdp_base::subTypeEnum(::fdp_base::subTypeEnum::RMF_LM_DECORATION)": 7,
    "::fdp_base::propertyIntEnum(::fdp_base::propertyIntEnum::RMF_UNSPECIFIED)": 0,
    "::fdp_base::propertyIntEnum(::fdp_base::propertyIntEnum::RMF_LC_NONE)": 6,
    "::fdp_base::roadTypeEnum(::fdp_base::roadTypeEnum::RMF_RT_UNKNOWN)": 0,
    "::fdp_base::roadTypeEnum(::fdp_base::roadTypeEnum::RMF_RT_OTHER)": 4,
    "::fdp_base::safetyQualifierEnum(::fdp_base::safetyQualifierEnum::RMF_SAFETY_QM)": 0,
    "::fdp_base::safetyQualifierEnum(::fdp_base::safetyQualifierEnum::RMF_SAFETY_ASIL_B)": 1,
    "::fdp_base::directionEnum(::fdp_base::directionEnum::RMF_LD_UNKNOWN)": 0,
    "::fdp_base::directionEnum(::fdp_base::directionEnum::RMF_LD_BIDIRECTIONAL)": 3,
    "::fdp_base::laneConnectionTypeEnum(::fdp_base::laneConnectionTypeEnum::RMF_LCT_SPLIT)": 0,
    "::fdp_base::laneConnectionTypeEnum(::fdp_base::laneConnectionTypeEnum::RMF_LCT_ATTRIBUTE_CHANGE)": 2,
    "::fdp_base::segmentTypeEnum(::fdp_base::segmentTypeEnum::RMF_ART_ROAD_SEGMENT)": 0,
    "::fdp_base::segmentTypeEnum(::fdp_base::segmentTypeEnum::RMF_ART_LANE_SEGMENT)": 1,
    "::fdp_base::interpolationTypeEnum(::fdp_base::interpolationTypeEnum::RMF_ARIT_DISCRETE)": 0,
    "::fdp_base::interpolationTypeEnum(::fdp_base::interpolationTypeEnum::RMF_ARIT_UNKNOWN)": 2,
    "::fdp_base::maintenanceStateEnum(::fdp_base::maintenanceStateEnum::RMF_SAS_PREDICTED)": 0,
    "::fdp_base::maintenanceStateEnum(::fdp_base::maintenanceStateEnum::RMF_SAS_EXTRAPOLATED)": 2,
    "::fdp_base::CohLaneAssocState_t(::fdp_base::CohLaneAssocState_t::COH_ASSOC_STATE_VALID)": 1,
}

# TODO: below is copy of ha33 constants need to rectify

"""Functional Test Helper - constants ha33"""

# PREDICTED_STATE = 3.0
# VALEO = 'VALEO'
# SRR = 'SRR'
# ARS = 'ARS'
ARS540 = "ARS540"
# VSPData = 'VSPData'
APTIV_CAMERA = "Aptiv Camera"
APTIV_SRR = "Aptiv SRR"
TPF_PREFIX = "TPF"
RMF_PREFIX = "RMF"
SEF_PREFIX = "SEF"
BLOCKAGE = "Blockage"
VDY_PREFIX = "VDY"
OUTPUT_CLUSTERS = "OUTPUT_CLUSTERS"

HIP_HA33 = "HIP HA33"

TIME_FREEZE = "Time Freeze"
TIME_GREATER_THAN_T6 = "Time GT T6"
TIME_GREATER_THAN_500MS = "Time GT 500ms"
TIME_CONSECUTIVE = "Time Consecutive"
TIME_DECREASE = "Time Decrease"
INTENDED_RANGE = "Intended Range"
OUT_OF_RANGE = "Out of range"
RADAR_INVALID = "Radar Invalid"
RADAR_FAILURE = "Radar Failure"
# RADAR_STATUS = 'Radar Status'
RADAR_BLOCKAGE = "Radar Blockage"

CAMERA_INVALID = "Camera Invalid"
CAMERA_FAILURE = "Camera Failure"

CEM_STATE = "CEM State"
SENSOR_STATE = "Sensor State"

TPF_CAMERA_TRIGGERED = "TPF CAMERA Triggered"
ADCU_VDY = "ADCU VDY"
ONE_OF_FOUR = "-1 of 4"
TWO_OF_FOUR = "-2 of 4"
THREE_OF_FOUR = "-3 of 4"
FOUR_OF_FOUR = "-4 of 4"

ONE_OF_THREE = "-1 of 3"
TWO_OF_THREE = "-2 of 3"
THREE_OF_THREE = "-3 of 3"

STATIC_OBJECT = "Static_Object"
CAMERA_CATCH_UPDATE_RATE = 56
RADAR_CATCH_UPDATE_RATE = 55
RADAR_LEFT_CATCH_UPDATE_RATE = 55
RADAR_RIGHT_CATCH_UPDATE_RATE = 55
RADAR_REAR_LEFT_CATCH_UPDATE_RATE = 55
RADAR_REAR_RIGHT_CATCH_UPDATE_RATE = 55

BW_SENSOR_PEDESTRIAN_CLASS = "probClassPedestrian"
BW_SENSOR_BICYCLE_CLASS = "probClassBicycle"
BW_SENSOR_CAR_CLASS = "probClassCar"
BW_SENSOR_TRUCK_CLASS = "probClassTruck"
BW_SENSOR_UNKNOWN_CLASS = "probClassUnknown"
BW_SENSOR_MOTOR_CYCLE_CLASS = "probClassMotorcycle"

# BW_SENSOR_CLASS = [BW_SENSOR_PEDESTRIAN_CLASS, BW_SENSOR_BICYCLE_CLASS, BW_SENSOR_CAR_CLASS, BW_SENSOR_TRUCK_CLASS,
#                    BW_SENSOR_UNKNOWN_CLASS, BW_SENSOR_MOTOR_CYCLE_CLASS]

BW_CEM_PEDESTRIAN_CLASS = "probabilityPedestrian"
BW_CEM_BICYCLE_CLASS = "probabilityCyclist"
BW_CEM_CAR_CLASS = "probabilityCar"
BW_CEM_TRUCK_CLASS = "probabilityTruck"
BW_CEM_UNKNOWN_CLASS = "probabilityUnknown"
BW_CEM_MOTOR_CYCLE_CLASS = "probabilityMotorbike"


class Adc420HA33Constants:
    """Class containing constants specific to ADC429HA33."""

    SIGNAL_MANIPULATION_START_TIME = 8.72
    SIGNAL_MANIPULATION_END_TIME = 9.24
    parent_path = Path(__file__).parent.parent.parent.parent

    INCREASING_DIFFERENCE = 0
    CEM_STATE_OK = 2
    FAILURE_STATE_OK = 0
    VDY_STATE_IMPLAUSIBLE = 5
    SIG_STATUS_OK = 1

    SENSOR_ARS510 = "ARS510"
    SENSOR_CAMERA_VALEO = "CAMERA_VALEO"
    SENSOR_CAMERA_VALEO_LANE = "CAMERA_VALEO_LANE"
    SENSOR_SRR520_FL = "SRR520_FL"
    SENSOR_SRR520_FR = "SRR520_FR"
    SENSOR_SRR520_RL = "SRR520_RL"
    SENSOR_SRR520_RR = "SRR520_RR"

    sensor_cam = "Sensor_Valeo_ObjectList"
    sensor_srrfl_salone = "SRRFL_ObjectList_alone"

    SENSOR_ARS510_FREE_SPACE = "SENSOR_ARS510_FREE_SPACE"
    SENSOR_ARS510_OBJECT = "SENSOR_ARS510_OBJECT"
    SENSOR_ARS510_ALL_CLUSTERS = "SENSOR_ARS510_ALL_CLUSTERS"
    SENSOR_ARS510_ROAD = "SENSOR_ARS510_ROAD"
    SENSOR_ARS510_VDY = "SENSOR_ARS510_VDY"
    SENSOR_ARS510_RADAR_STATUS = "SENSOR_ARS510_RADAR_STATUS"

    SENSOR_SRR520_FL_FREE_SPACE = "SENSOR_SRR520_FL_FREE_SPACE"
    SENSOR_SRR520_FL_OBJECT = "SENSOR_SRR520_FL_OBJECT"
    SENSOR_SRR520_FL_ALL_CLUSTERS = "SENSOR_SRR520_FL_ALL_CLUSTERS"
    SENSOR_SRR520_FL_VDY = "SENSOR_SRR520_FL_VDY"
    SENSOR_SRR520_FL_RADAR_STATUS = "SENSOR_SRR520_FL_RADAR_STATUS"

    SENSOR_SRR520_FR_FREE_SPACE = "SENSOR_SRR520_FR_FREE_SPACE"
    SENSOR_SRR520_FR_OBJECT = "SENSOR_SRR520_FR_OBJECT"
    SENSOR_SRR520_FR_ALL_CLUSTERS = "SENSOR_SRR520_FR_ALL_CLUSTERS"
    SENSOR_SRR520_FR_VDY = "SENSOR_SRR520_FR_VDY"
    SENSOR_SRR520_FR_RADAR_STATUS = "SENSOR_SRR520_FR_RADAR_STATUS"

    SENSOR_SRR520_RL_FREE_SPACE = "SENSOR_SRR520_RL_FREE_SPACE"
    SENSOR_SRR520_RL_OBJECT = "SENSOR_SRR520_RL_OBJECT"
    SENSOR_SRR520_RL_ALL_CLUSTERS = "SENSOR_SRR520_RL_ALL_CLUSTERS"
    SENSOR_SRR520_RL_VDY = "SENSOR_SRR520_RL_VDY"
    SENSOR_SRR520_RL_RADAR_STATUS = "SENSOR_SRR520_RL_RADAR_STATUS"

    SENSOR_SRR520_RR_FREE_SPACE = "SENSOR_SRR520_RR_FREE_SPACE"
    SENSOR_SRR520_RR_OBJECT = "SENSOR_SRR520_RR_OBJECT"
    SENSOR_SRR520_RR_ALL_CLUSTERS = "SENSOR_SRR520_RR_ALL_CLUSTERS"
    SENSOR_SRR520_RR_VDY = "SENSOR_SRR520_RR_VDY"
    SENSOR_SRR520_RR_RADAR_STATUS = "SENSOR_SRR520_RR_RADAR_STATUS"

    SENSOR_CAMERA_VALEO_LANES = "SENSOR_CAMERA_VALEO_LANES"
    SENSOR_CAMERA_VALEO_OBJECT = "SENSOR_CAMERA_VALEO_OBJECT"
    SENSOR_CAMERA_VALEO_ALL_CLUSTERS = "SENSOR_CAMERA_VALEO_ALL_CLUSTERS"
    SENSOR_CAMERA_VALEO_CAM_FAILURE_INFO = "SENSOR_CAMERA_VALEO_CAM_FAILURE_INFO"
    SENSOR_CAMERA_VALEO_FC_GLOBAL_HOST_STATE = "SENSOR_CAMERA_VALEO_FC_GLOBAL_HOST_STATE"

    SENSOR_ARS510_E2E_OBJECT = "m_ars510ObjListE2eStatus"
    SENSOR_ARS510_E2E_FREE_SPACE = "m_ars510FreeSpaceE2eStatus"
    SENSOR_ARS510_E2E_ROAD = "m_ars510RoadE2eStatus"
    SENSOR_ARS510_E2E_VDY = "m_ars510VdyE2eStatus"
    SENSOR_ARS510_E2E_RADAR_STATUS = "m_ars510FctE2eStatus"

    SENSOR_ARS510_E2E_TIMEOUT_OBJECT = "m_ars510ObjListE2eStatus"
    SENSOR_ARS510_E2E_TIMEOUT_FREE_SPACE = "m_ars510FreeSpaceE2eStatus"
    SENSOR_ARS510_E2E_TIMEOUT_ROAD = "m_ars510RoadE2eStatus"
    SENSOR_ARS510_E2E_TIMEOUT_VDY = "m_ars510VdyE2eStatus"
    SENSOR_ARS510_E2E_TIMEOUT_RADAR_STATUS = "m_ars510FctE2eStatus"

    SENSOR_SRR520_FL_E2E_FREE_SPACE = "m_srr520(Fl)FreeSpaceE2eStatus"
    SENSOR_SRR520_FL_E2E_OBJECT = "m_srr520(Fl)ObjListE2eStatus"
    SENSOR_SRR520_FL_E2E_VDY = "m_srr520(Fl)VdyE2eStatus"
    SENSOR_SRR520_FL_E2E_RADAR_STATUS = "m_srr520(Fl)FctE2eStatus"

    SENSOR_SRR520_FL_E2E_TIMEOUT_FREE_SPACE = "m_srr520(Fl)FreeSpaceE2eStatus"
    SENSOR_SRR520_FL_E2E_TIMEOUT_OBJECT = "m_srr520(Fl)ObjListE2eStatus"
    SENSOR_SRR520_FL_E2E_TIMEOUT_VDY = "m_srr520(Fl)VdyE2eStatus"
    SENSOR_SRR520_FL_E2E_TIMEOUT_RADAR_STATUS = "m_srr520(Fl)FctE2eStatus"

    SENSOR_SRR520_FR_E2E_FREE_SPACE = "m_srr520(Fr)FreeSpaceE2eStatus"
    SENSOR_SRR520_FR_E2E_OBJECT = "m_srr520(Fr)ObjListE2eStatus"
    SENSOR_SRR520_FR_E2E_VDY = "m_srr520(Fr)VdyE2eStatus"
    SENSOR_SRR520_FR_E2E_RADAR_STATUS = "m_srr520(Fr)FctE2eStatus"

    SENSOR_SRR520_FR_E2E_TIMEOUT_FREE_SPACE = "m_srr520(Fr)FreeSpaceE2eStatus"
    SENSOR_SRR520_FR_E2E_TIMEOUT_OBJECT = "m_srr520(Fr)ObjListE2eStatus"
    SENSOR_SRR520_FR_E2E_TIMEOUT_VDY = "m_srr520(Fr)VdyE2eStatus"
    SENSOR_SRR520_FR_E2E_TIMEOUT_RADAR_STATUS = "m_srr520(Fr)FctE2eStatus"

    SENSOR_SRR520_RL_E2E_FREE_SPACE = "m_srr520(Rl)FreeSpaceE2eStatus"
    SENSOR_SRR520_RL_E2E_OBJECT = "m_srr520(Rl)ObjListE2eStatus"
    SENSOR_SRR520_RL_E2E_VDY = "m_srr520(Rl)VdyE2eStatus"
    SENSOR_SRR520_RL_E2E_RADAR_STATUS = "m_srr520(Rl)FctE2eStatus"

    SENSOR_SRR520_RL_E2E_TIMEOUT_FREE_SPACE = "m_srr520(Rl)FreeSpaceE2eStatus"
    SENSOR_SRR520_RL_E2E_TIMEOUT_OBJECT = "m_srr520(Rl)ObjListE2eStatus"
    SENSOR_SRR520_RL_E2E_TIMEOUT_VDY = "m_srr520(Rl)VdyE2eStatus"
    SENSOR_SRR520_RL_E2E_TIMEOUT_RADAR_STATUS = "m_srr520(Rl)FctE2eStatus"

    SENSOR_SRR520_RR_E2E_FREE_SPACE = "m_srr520(Rr)FreeSpaceE2eStatus"
    SENSOR_SRR520_RR_E2E_OBJECT = "m_srr520(Rr)ObjListE2eStatus"
    SENSOR_SRR520_RR_E2E_VDY = "m_srr520(Rr)VdyE2eStatus"
    SENSOR_SRR520_RR_E2E_RADAR_STATUS = "m_srr520(Rr)FctE2eStatus"

    SENSOR_SRR520_RR_E2E_TIMEOUT_FREE_SPACE = "m_srr520(Rr)FreeSpaceE2eStatus"
    SENSOR_SRR520_RR_E2E_TIMEOUT_OBJECT = "m_srr520(Rr)ObjListE2eStatus"
    SENSOR_SRR520_RR_E2E_TIMEOUT_VDY = "m_srr520(Rr)VdyE2eStatus"
    SENSOR_SRR520_RR_E2E_TIMEOUT_RADAR_STATUS = "m_srr520(Rr)FctE2eStatus"

    SENSOR_CAMERA_VALEO_E2E_LANES = "m_valeoLanesE2eStatus"
    SENSOR_CAMERA_VALEO_E2E_OBJECT = "m_valeoFcObjListE2eStatus"
    SENSOR_CAMERA_VALEO_E2E_RADAR_STATUS = "m_valeoFctE2eStatus"

    SENSOR_CAMERA_VALEO_TIMEOUT_LANES = "m_valeoLanesE2eStatus"
    SENSOR_CAMERA_VALEO_TIMEOUT_OBJECT = "m_valeoFcObjListE2eStatus"
    SENSOR_CAMERA_VALEO_TIMEOUT_RADAR_STATUS = "m_valeoFctE2eStatus"

    CEM_FDP_21P_TPF = "CEM_FDP_21P_TPF"
    CEM_FDP_21P_SEF = "CEM_FDP_21P_SEF"
    CEM_FDP_21P_VAL = "CEM_FDP_21P_VAL"
    CEM_FDP_21P_ALCA = "CEM_FDP_21P_ALCA"

    CEM_FDP_BASE_EML = "CEM_FDP_BASE_EML"
    CEM_FDP_BASE_RMF = "CEM_FDP_BASE_RMF"
    CEM_FDP_BASE_TPF = "CEM_FDP_BASE_TPF"
    CEM_FDP_BASE_COH = "CEM_FDP_BASE_COH"
    CEM_FDP_BASE_SEF = "CEM_FDP_BASE_SEF"
    CEM_FDP_BASE_VAL = "CEM_FDP_BASE_VAL"

    sig_status = "eSigStatus"
    timestamp_fcu = "TimeStampFCU"
    timestamp_radar_road = "TimestampRadar"
    RMF_num_points = "RMF No of Points"

    HA33_ARS_FRSP_ITEMS_PREFIX = "Local_ARS_CANFD.ARS510HA33_Private.ARS_FRSP_ITEMS_"
    HA33_ARS_FRSP_VERTEX_PREFIX = "Local_ARS_CANFD.ARS510HA33_Private.ARS_FRSP_VERTEX_"

    HA33_ARS_OBJECT_PREFIX = "Local_ARS_CANFD.ARS510HA33_Private.ARS_OBJ_"

    HA33_SRR_FL_OBJECT_PREFIX = "Local_SRR_FL_CANFD.SRR520HA33_FL_Private.SRR_OBJ_"
    HA33_SRR_FR_OBJECT_PREFIX = "Local_SRR_FR_CANFD.SRR520HA33_FR_Private.SRR_OBJ_"
    HA33_SRR_RL_OBJECT_PREFIX = "Local_SRR_RL_CANFD.SRR520HA33_RL_Private.SRR_OBJ_"
    HA33_SRR_RR_OBJECT_PREFIX = "Local_SRR_RR_CANFD.SRR520HA33_RR_Private.SRR_OBJ_"

    HA33_SRR_OBJECT_PREFIX = "SRR_OBJ_"
    HA33_SRR_FRSP_ITEMS_PREFIX = "SRR_FRSP_ITEMS_"
    HA33_SRR_FRSP_VERTEX_PREFIX = "SRR_FRSP_VERTEX_"

    HA33_CAMERA_VALEO_OBJECT_PREFIX = "Local_Valeo_CANFD.VSS-FC_Private.OIF_Info_"

    HA33_CEM_FDP_21P_TPF_PREFIX = "SIM VFB CEM200.FDP_21P."
    HA33_CEM_FDP_Base_TPF_PREFIX = "SIM VFB CEM200.FDP_Base."

    ICD_COLUMN_SIGNAL_NAME = "_Signal Name"
    ICD_COLUMN_MAX_RANGE = "phy. Max. Range"
    ICD_COLUMN_RANGE_MONITOR = "RangeMonitor"
    ICD_COLUMN_FACTOR = "Factor"

    cem_base_string_map_to_icd_base = {
        CEM_FDP_BASE_EML: "SIM VFB CEM200.FDP_Base",
        CEM_FDP_BASE_RMF: "SIM VFB CEM200.FDP_Base",
        CEM_FDP_BASE_TPF: "SIM VFB CEM200.FDP_Base",
        CEM_FDP_BASE_COH: "SIM VFB CEM200.FDP_Base",
    }

    cem_base_string_map_to_icd_21p = {
        CEM_FDP_21P_TPF: "SIM VFB CEM200.FDP_21P",
        CEM_FDP_21P_SEF: "SIM VFB CEM200.FDP_21P",
        CEM_FDP_21P_VAL: "SIM VFB CEM200.FDP_21P",
        CEM_FDP_21P_ALCA: "SIM VFB CEM200.FDP_21P",
    }

    map_icd_excel_name_to_sensor_signal_base_string = {
        SENSOR_ARS510_FREE_SPACE: "Local_ARS_CANFD.ARS510HA33_Private.ARS_FRSP_HEADER",
        SENSOR_ARS510_OBJECT: "Local_ARS_CANFD.ARS510HA33_Private.ARS_OBJ_STATUS",
        SENSOR_ARS510_ROAD: "Local_ARS_CANFD.ARS510HA33_Private",
        SENSOR_ARS510_VDY: "Local_ARS_CANFD.ARS510HA33_Private",
        SENSOR_ARS510_RADAR_STATUS: "Local_ARS_CANFD.ARS510HA33_Private",
        SENSOR_SRR520_FL_FREE_SPACE: "Local_SRR_FL_CANFD.SRR520HA33_FL_Private",
        SENSOR_SRR520_FL_OBJECT: HA33_SRR_FL_OBJECT_PREFIX,
        SENSOR_SRR520_FL_VDY: "Local_SRR_FL_CANFD.SRR520HA33_FL_Private",
        SENSOR_SRR520_FL_RADAR_STATUS: "Local_SRR_FL_CANFD.SRR520HA33_FL_Private.SRR_ECU_FCT_STATUS.",
        SENSOR_SRR520_FR_FREE_SPACE: "Local_SRR_FR_CANFD.SRR520HA33_FR_Private",
        SENSOR_SRR520_FR_OBJECT: HA33_SRR_FR_OBJECT_PREFIX,
        SENSOR_SRR520_FR_VDY: "Local_SRR_FR_CANFD.SRR520HA33_FR_Private",
        SENSOR_SRR520_FR_RADAR_STATUS: "Local_SRR_FR_CANFD.SRR520HA33_FR_Private.SRR_ECU_FCT_STATUS.",
        SENSOR_SRR520_RL_FREE_SPACE: "Local_SRR_RL_CANFD.SRR520HA33_RL_Private",
        SENSOR_SRR520_RL_OBJECT: HA33_SRR_RL_OBJECT_PREFIX,
        SENSOR_SRR520_RL_VDY: "Local_SRR_RL_CANFD.SRR520HA33_RL_Private",
        SENSOR_SRR520_RL_RADAR_STATUS: "Local_SRR_RL_CANFD.SRR520HA33_RL_Private.SRR_ECU_FCT_STATUS.",
        SENSOR_SRR520_RR_FREE_SPACE: "Local_SRR_RR_CANFD.SRR520HA33_RR_Private",
        SENSOR_SRR520_RR_OBJECT: HA33_SRR_RR_OBJECT_PREFIX,
        SENSOR_SRR520_RR_VDY: "Local_SRR_RR_CANFD.SRR520HA33_RR_Private",
        SENSOR_SRR520_RR_RADAR_STATUS: "Local_SRR_RR_CANFD.SRR520HA33_RR_Private.SRR_ECU_FCT_STATUS.",
        SENSOR_CAMERA_VALEO_LANES: "Local_Valeo_CANFD.VSS-FC_Private",
        SENSOR_CAMERA_VALEO_OBJECT: "Local_Valeo_CANFD.VSS-FC_Private.OIF_Info",
        # SENSOR_CAMERA_VALEO_CAM_FAILURE_INFO: "Local_Valeo_CANFD.VSS-FC_Private",
        SENSOR_CAMERA_VALEO_FC_GLOBAL_HOST_STATE: "Local_Valeo_CANFD.VSS-FC_Private",
    }

    ICD_EXCEL_NAMES = {
        "INPUT_Clusters": [
            SENSOR_ARS510_OBJECT,
            SENSOR_ARS510_ROAD,
            SENSOR_ARS510_VDY,
            SENSOR_ARS510_RADAR_STATUS,
            #  SENSOR_ARS510_FREE_SPACE,
            #  SENSOR_SRR520_FL_FREE_SPACE,
            SENSOR_SRR520_FL_OBJECT,
            SENSOR_SRR520_FL_VDY,
            SENSOR_SRR520_FL_RADAR_STATUS,
            # SENSOR_SRR520_FR_FREE_SPACE,
            SENSOR_SRR520_FR_OBJECT,
            SENSOR_SRR520_FR_VDY,
            SENSOR_SRR520_FR_RADAR_STATUS,
            # SENSOR_SRR520_RL_FREE_SPACE,
            SENSOR_SRR520_RL_OBJECT,
            SENSOR_SRR520_RL_VDY,
            SENSOR_SRR520_RL_RADAR_STATUS,
            # SENSOR_SRR520_RR_FREE_SPACE,
            SENSOR_SRR520_RR_OBJECT,
            SENSOR_SRR520_RR_VDY,
            SENSOR_SRR520_RR_RADAR_STATUS,
            SENSOR_CAMERA_VALEO_LANES,
            SENSOR_CAMERA_VALEO_OBJECT,
            SENSOR_CAMERA_VALEO_FC_GLOBAL_HOST_STATE,
        ]
    }

    SIG_STATUS_INVALID = 2
    SIG_STATUS_INIT = 0

    # cem initialization phase
    CEM_INIT_PHASE = 2
    # 50ms is considered between T6 and component Timestamp
    T7_T6_DIFFERENCE = 40000

    OBJECT_IDENTIFIER = "Object Identifier"
    TEST_STATUS = "_TestStatus_"
    OVERALL_RESULT = "Overall_Result"
    TEST_DATE = "_TestDate_"

    POE = "PoE"  # probability of existence of ftp or rtp
    poe_integer_value = 0.5
    poe_percentage_value = 50.0

    # signal name for T6
    T6_SIGNAL = "SIM VFB ALL.EMF.EmfGlobalTimestamp.SigHeader.uiTimeStamp"


# SENSOR OUTPUT STATE ENUM VALUES DOORS LINK
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000058&urn=urn:telelogic::1-503e822e5ec3651e-O-6750-0009b482
SENSOR_OUTPUT_FAILURE_STATUS_UNKNOWN = 0
SENSOR_OUTPUT_FAILURE_STATUS_IMPLAUSIBLE = 1.0
SENSOR_OUTPUT_FAILURE_STATUS_PLAUSIBLE = 2

# ADC420HA33 SAFETY TEST
# ----------------------------------------------------------------------------------------------------------------------
SENSOR_ARS510 = "ARS510"
SENSOR_CAMERA_VALEO = "CAMERA_VALEO"
# SENSOR_CAMERA_VALEO_OBJECT = ' CAMERA_VALEO_OBJECT'
# SENSOR_CAMERA_VALEO_LANE = ' CAMERA_VALEO_LANE'
SENSOR_SRR520_FL = "SRR520_FL"
SENSOR_SRR520_FR = "SRR520_FR"
SENSOR_SRR520_RL = "SRR520_RL"
SENSOR_SRR520_RR = "SRR520_RR"
HA33_TOW_MODE = "TOW MODE"

HA33_FUSION = "01 Fusion"
HA33_PERCEPTION_RANGE = "02 Perception Range"
HA33_NOT_ALL_CLUSTERS = "03 Not All Clusters"
HA33_ALL_CLUSTERS = "04 All Clusters"
HA33_SENSOR_OUTPUT_STATE = "03 Sensor Output State"
HA33_CEM_OUTPUT_STATE = "CEM Output State"
# E2E = 'E2E'
# TIMEOUT = ' TIMEOUT'

#
# PERCEPTION_RANGE_VALUE_ZERO = 0.

# HA33 CEM OUTPUT STATE DOORS ICD ENUM VALUES
# ----------------------------------------------------------------------------------------------------------------------
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000058&urn=urn:telelogic::1-503e822e5ec3651e-O-6756-0009b482
HA33_CEM_OUTPUT_STATE_INIT = 0.0
HA33_CEM_OUTPUT_STATE_NORMAL = 1.0
HA33_CEM_OUTPUT_STATE_TEMPORARY_FAILURE = 2.0
HA33_CEM_OUTPUT_STATE_PERMANENT_FAILURE = 3.0
HA33_CEM_OUTPUT_STATE_OFF = 4.0

# HA33 Start, End time of signal manipulation
# ----------------------------------------------------------------------------------------------------------------------
HA33_ONE_CYCLE_TIME = 0.04  # 40 ms one cycle time for HA33
HA33_SIGNAL_MANIPULATION_START_TIME = 8.72
HA33_SIGNAL_MANIPULATION_END_TIME = 9.24

HA33_ALCA_SIGNAL_MANIPULATION_START_TIME = 100.0
HA33_ALCA_SIGNAL_MANIPULATION_END_TIME = 200.0

HA33_TOW_MODE_SAFETY_START_TIME = 4.0
HA33_TOW_MODE_SAFETY_END_TIME = 41.0

HA33_CEM_OUTPUT_CYCLE_COUNT = 33
# HA33 sensor input timestamp signal manipulation value
# ----------------------------------------------------------------------------------------------------------------------
HA33_TEST_CASE_TO_INPUT_SIGNAL_VALUE_MAPPING = {
    "ADCU VDY_Time Freeze": [769789945],
    "ADCU VDY_Time GT T6": [770789946],
    "ADCU VDY_Time GT 500ms": [771789946],
    "ADCU VDY_Out of range": [41.0],
    "ADCU VDY_Time Decrease": [
        769789945,
        768789945,
        767789945,
        766789945,
        765789945,
        764789945,
        763789945,
        762789945,
        761789945,
        760789945,
    ],
    TIME_DECREASE: [[769.0, 768.0, 767.0, 766.0, 765.0, 764.0, 763.0, 762.0, 761.0, 760.0], [0.0]],
    TIME_FREEZE: [769.0, 0.0],
    TIME_GREATER_THAN_T6: [770.0, 0.0],
    TIME_GREATER_THAN_500MS: [771.0, 0.0],
    RADAR_INVALID: [2.0],
}

# HA33 INPUT TIMESTAMP Signal
# ----------------------------------------------------------------------------------------------------------------------
HA33_INPUT_TIMESTAMP_ARS_SEF_SIGNAL = "Local_ARS_CANFD.ARS510HA33_Private.ARS_FRSP_HEADER.uiTimeStampGlobSec_FRSP"
HA33_INPUT_TIMESTAMP_ARS_TPF_SIGNAL = "Local_ARS_CANFD.ARS510HA33_Private.ARS_OBJ_STATUS.uiTimeStampGlobSec_OBJ_STS"
HA33_INPUT_TIMESTAMP_ARS_RMF_SIGNAL = "Local_ARS_CANFD.ARS510HA33_Private.ARS_ROAD.uiTimeStampGlobSec_RD"
HA33_INPUT_TIMESTAMP_ARS_VDY_SIGNAL = "Local_ARS_CANFD.ARS510HA33_Private.ARS_VDY.uiTimeStampGlobSec_VDY"

HA33_INPUT_TIMESTAMP_ARS_SEF_SIGNAL_NANO = (
    "Local_ARS_CANFD.ARS510HA33_Private.ARS_FRSP_HEADER." "uiTimeStampGlobNsec_FRSP"
)
HA33_INPUT_TIMESTAMP_ARS_TPF_SIGNAL_NANO = (
    "Local_ARS_CANFD.ARS510HA33_Private.ARS_OBJ_STATUS." "uiTimeStampGlobNsec_OBJ_STS"
)
HA33_INPUT_TIMESTAMP_ARS_RMF_SIGNAL_NANO = "Local_ARS_CANFD.ARS510HA33_Private.ARS_ROAD.uiTimeStampGlobNSec_RD"
HA33_INPUT_TIMESTAMP_ARS_VDY_SIGNAL_NANO = "Local_ARS_CANFD.ARS510HA33_Private.ARS_VDY.uiTimeStampGlobNsec_VDY"

HA33_INPUT_TIMESTAMP_CAMERA_TPF_SIGNAL = "Local_Valeo_CANFD.VSS-FC_Private.OIF_Info_0." "TIMESTAMP_SYNC_OIF_SEC"
HA33_INPUT_TIMESTAMP_CAMERA_RMF_SIGNAL = "Local_Valeo_CANFD.VSS-FC_Private.LANES_Info_1." "TIMESTAMP_SYNC_LANES_SEC"

HA33_INPUT_TIMESTAMP_SRR520_FL_TPF_SIGNAL = (
    "Local_SRR_FL_CANFD.SRR520HA33_FL_Private." "SRR_OBJ_STATUS.uiTimeStampGlobSec_ObjSts"
)
HA33_INPUT_TIMESTAMP_SRR520_FL_SEF_SIGNAL = (
    "Local_SRR_FL_CANFD.SRR520HA33_FL_Private." "SRR_FRSP_HEADER.uiTimeStampGlobSec_FrSp"
)
HA33_INPUT_TIMESTAMP_SRR520_FL_VDY_SIGNAL = "Local_SRR_FL_CANFD.SRR520HA33_FL_Private." "SRR_VDY.uiTimeStampGlobSec_VDY"

HA33_INPUT_TIMESTAMP_SRR520_FL_TPF_SIGNAL_NANO = (
    "Local_SRR_FL_CANFD.SRR520HA33_FL_Private." "SRR_OBJ_STATUS.uiTimeStampGlobNsec_ObjSts"
)
HA33_INPUT_TIMESTAMP_SRR520_FL_SEF_SIGNAL_NANO = (
    "Local_SRR_FL_CANFD.SRR520HA33_FL_Private." "SRR_FRSP_HEADER.uiTimeStampGlobNsec_FrSp"
)
HA33_INPUT_TIMESTAMP_SRR520_FL_VDY_SIGNAL_NANO = (
    "Local_SRR_FL_CANFD.SRR520HA33_FL_Private." "SRR_VDY.uiTimeStampGlobNsec_VDY"
)

HA33_INPUT_TIMESTAMP_SRR520_FR_TPF_SIGNAL = (
    "Local_SRR_FR_CANFD.SRR520HA33_FR_Private." "SRR_OBJ_STATUS.uiTimeStampGlobSec_ObjSts"
)
HA33_INPUT_TIMESTAMP_SRR520_FR_SEF_SIGNAL = (
    "Local_SRR_FR_CANFD.SRR520HA33_FR_Private." "SRR_FRSP_HEADER.uiTimeStampGlobSec_FrSp"
)
HA33_INPUT_TIMESTAMP_SRR520_FR_VDY_SIGNAL = "Local_SRR_FR_CANFD.SRR520HA33_FR_Private." "SRR_VDY.uiTimeStampGlobSec_VDY"

HA33_INPUT_TIMESTAMP_SRR520_FR_TPF_SIGNAL_NANO = (
    "Local_SRR_FR_CANFD.SRR520HA33_FR_Private." "SRR_OBJ_STATUS.uiTimeStampGlobNsec_ObjSts"
)
HA33_INPUT_TIMESTAMP_SRR520_FR_SEF_SIGNAL_NANO = (
    "Local_SRR_FR_CANFD.SRR520HA33_FR_Private." "SRR_FRSP_HEADER.uiTimeStampGlobNsec_FrSp"
)
HA33_INPUT_TIMESTAMP_SRR520_FR_VDY_SIGNAL_NANO = (
    "Local_SRR_FR_CANFD.SRR520HA33_FR_Private." "SRR_VDY.uiTimeStampGlobNsec_VDY"
)

HA33_INPUT_TIMESTAMP_SRR520_RL_TPF_SIGNAL = (
    "Local_SRR_RL_CANFD.SRR520HA33_RL_Private." "SRR_OBJ_STATUS.uiTimeStampGlobSec_ObjSts"
)
HA33_INPUT_TIMESTAMP_SRR520_RL_SEF_SIGNAL = (
    "Local_SRR_RL_CANFD.SRR520HA33_RL_Private." "SRR_FRSP_HEADER.uiTimeStampGlobSec_FrSp"
)
HA33_INPUT_TIMESTAMP_SRR520_RL_VDY_SIGNAL = "Local_SRR_RL_CANFD.SRR520HA33_RL_Private." "SRR_VDY.uiTimeStampGlobSec_VDY"

HA33_INPUT_TIMESTAMP_SRR520_RL_TPF_SIGNAL_NANO = (
    "Local_SRR_RL_CANFD.SRR520HA33_RL_Private." "SRR_OBJ_STATUS.uiTimeStampGlobNsec_ObjSts"
)
HA33_INPUT_TIMESTAMP_SRR520_RL_SEF_SIGNAL_NANO = (
    "Local_SRR_RL_CANFD.SRR520HA33_RL_Private." "SRR_FRSP_HEADER.uiTimeStampGlobNsec_FrSp"
)
HA33_INPUT_TIMESTAMP_SRR520_RL_VDY_SIGNAL_NANO = (
    "Local_SRR_RL_CANFD.SRR520HA33_RL_Private." "SRR_VDY.uiTimeStampGlobNsec_VDY"
)

HA33_INPUT_TIMESTAMP_SRR520_RR_TPF_SIGNAL = (
    "Local_SRR_RR_CANFD.SRR520HA33_RR_Private." "SRR_OBJ_STATUS.uiTimeStampGlobSec_ObjSts"
)
HA33_INPUT_TIMESTAMP_SRR520_RR_SEF_SIGNAL = (
    "Local_SRR_RR_CANFD.SRR520HA33_RR_Private." "SRR_FRSP_HEADER.uiTimeStampGlobSec_FrSp"
)
HA33_INPUT_TIMESTAMP_SRR520_RR_VDY_SIGNAL = "Local_SRR_RR_CANFD.SRR520HA33_RR_Private." "SRR_VDY.uiTimeStampGlobSec_VDY"

HA33_INPUT_TIMESTAMP_SRR520_RR_TPF_SIGNAL_NANO = (
    "Local_SRR_RR_CANFD.SRR520HA33_RR_Private." "SRR_OBJ_STATUS.uiTimeStampGlobNsec_ObjSts"
)
HA33_INPUT_TIMESTAMP_SRR520_RR_SEF_SIGNAL_NANO = (
    "Local_SRR_RR_CANFD.SRR520HA33_RR_Private." "SRR_FRSP_HEADER.uiTimeStampGlobNsec_FrSp"
)
HA33_INPUT_TIMESTAMP_SRR520_RR_VDY_SIGNAL_NANO = (
    "Local_SRR_RR_CANFD.SRR520HA33_RR_Private." "SRR_VDY.uiTimeStampGlobNsec_VDY"
)

# HA33 CEM OUTPUT NO_OF_OBJECT_SIGNAL
HA33_OUTPUT_SIG_STATUS_SEF_NO_OF_OBS_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_NumObsInfo.numberOfObstacles"
HA33_OUTPUT_SIG_STATUS_TPF_NO_OF_OBJ_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_NumObjInfo.numberOfObjects"
HA33_OUTPUT_SIG_STATUS_RMF_NO_OF_POINTS_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_NumPtsInfo.numberOfPoints"

# HA33 CEM OUTPUT FDP_BASE NO_OF_OBJECT_SIGNAL
HA33_OUTPUT_VEHICLE_TPF_NO_OF_OBJ_SIGNAL = "ADC4xx.FDP_21P.FDP_NumObjInfo.numberOfObjects"
HA33_OUTPUT_VEHICLE_SEF_NO_OF_OBS_SIGNAL = "ADC4xx.FDP_21P.FDP_NumObsInfo.numberOfObstacles"
HA33_OUTPUT_VEHICLE_RMF_NO_OF_POINTS_SIGNAL = "ADC4xx.FDP_21P.FDP_NumPtsInfo.numberOfPoints"

# HA33 CEM OUTPUT CYCLE_COUNTER_SIGNAL
HA33_OUTPUT_SIG_STATUS_TPF_CYCLE_COUNT_SIGNAL = "SIM VFB CEM200.FDP_Base.p_TpfOutputIf.sSigHeader.uiCycleCounter"

# HA33 INPUT Radar Failure Signal Dictionary mapping as the signals do not change except prefix
# ----------------------------------------------------------------------------------------------------------------------
HA33_SENSOR_FAILURE_INPUT_FAILURE_SIGNAL_PREFIX = {
    SENSOR_ARS510: "Local_ARS_CANFD.ARS510HA33_Private.ARS_ECU_FCT_STATUS.",
    SENSOR_SRR520_FL: "Local_SRR_FL_CANFD.SRR520HA33_FL_Private.SRR_ECU_FCT_STATUS.",
    SENSOR_SRR520_FR: "Local_SRR_FR_CANFD.SRR520HA33_FR_Private.SRR_ECU_FCT_STATUS.",
    SENSOR_SRR520_RL: "Local_SRR_RL_CANFD.SRR520HA33_RL_Private.SRR_ECU_FCT_STATUS.",
    SENSOR_SRR520_RR: "Local_SRR_RR_CANFD.SRR520HA33_RR_Private.SRR_ECU_FCT_STATUS.",
    SENSOR_CAMERA_VALEO: "Local_Valeo_CANFD.VSS-FC_Private.",
}

HA33_SENSOR_FAILURE_OUTPUT_SIP_COMMUNICATION_ERROR_SIGNAL_PREFIX = {
    SENSOR_ARS510: "SIM VFB CEM200.ARS510.ARS510E2EFctStatus.",
    SENSOR_SRR520_FL: "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_fl.",
    SENSOR_SRR520_FR: "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_fr.",
    SENSOR_SRR520_RL: "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_rl.",
    SENSOR_SRR520_RR: "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_rr.",
    SENSOR_CAMERA_VALEO: "SIM VFB CEM200.Valeo.ValeoE2EFctStatus.",
}

HA33_ADC4xx_T6_TIME_SIGNAL = "ADC4xx.EMF.EmfGlobalTimestamp.SigHeader.uiTimeStamp"

HA33_CEM_OUTPUT_STATE_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU.sigCemSwcStatus"
HA33_INPUT_SIG_STATUS_ADCU_VDY_SIGNAL = "ADC4xx.IPVDY.VehDyn_t.sSigHeader.eSigStatus"
HA33_INPUT_SIG_STATUS_ARS_POSITION = "Local_ARS_CANFD.ARS510HA33_Private.ARS_ECU_FCT_STATUS.f_positionX"
HA33_INPUT_SIG_STATUS_SRR_POSITION = "Local_SRR_FL_CANFD.SRR520HA33_FL_Private.SRR_ECU_FCT_STATUS.f_positionX"
HA33_INPUT_VALEO = "Local_Valeo_CANFD.VSS-FC_Private.OIF_Info_2.OIF_Height_STD_1"

HA33_CEM_FDP_BASE_TPF_SIG_STATUS_SIGNAL = "SIM VFB CEM200.FDP_Base.p_TpfOutputIf.sSigHeader.eSigStatus"
HA33_CEM_FDP_BASE_SEF_SIG_STATUS_SIGNAL = "SIM VFB CEM200.FDP_Base.p_FsfOutputIf.sSigHeader.eSigStatus"
HA33_CEM_FDP_BASE_EML_SIG_STATUS_SIGNAL = "SIM VFB CEM200.FDP_Base.p_EmlOutputIf.sigHeader.eSigStatus"
HA33_CEM_FDP_BASE_RMF_SIG_STATUS_SIGNAL = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.sigHeader.eSigStatus"
HA33_CEM_FDP_BASE_COH_SIG_STATUS_SIGNAL = "SIM VFB CEM200.FDP_Base.p_CemAssocOutputIf.SigHeader.eSigStatus"
HA33_CEM_FDP_BASE_EML_EGO_VEH_SIG_STATUS_SIGNAL = "SIM VFB CEM200.EML.EmlOutput.egoVehKinematic.sigHeader.eSigStatus"

HA33_CEM_OUTPUT_STATE_ARS_PLAUSIBILITY_STATUS = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigFrontRadarPlausibilityFailureStatus"
)
HA33_CEM_OUTPUT_STATE_CAMERA_PLAUSIBILITY_STATUS = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigCameraPlausibilityFailureStatus"
)
HA33_CEM_OUTPUT_STATE_SRR_FR_PLAUSIBILITY_STATUS = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigFrontRightRadarPlausibilityFailureStatus"
)
HA33_CEM_OUTPUT_STATE_SRR_FL_PLAUSIBILITY_STATUS = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigFrontLeftRadarPlausibilityFailureStatus"
)
HA33_CEM_OUTPUT_STATE_SRR_RR_PLAUSIBILITY_STATUS = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigRearRightRadarPlausibilityFailureStatus"
)
HA33_CEM_OUTPUT_STATE_SRR_RL_PLAUSIBILITY_STATUS = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigRearLeftRadarPlausibilityFailureStatus"
)
# HIP_HA33 SIGNALS
HA33_FID_CEM_RECRANKING_STATE_FLAG = "SIM VFB CEM200.HIP_HA22.fidFailureFlagMeasFreeze.FidInCemReCrankingStateFlag"
HA33_FID_TEMP_FAILURE_FLAG = "SIM VFB CEM200.HIP_HA22.fidFailureFlagMeasFreeze.fidInTempFailureFlag"

HA33_OUTPUT_SIG_STATUS_OBJECT_TPF_SIGNAL = "SIM VFB CEM200.FDP_Base.p_TpfOutputIf.sSigHeader.eSigStatus"

HA33_OUTPUT_SIG_STATUS_SEF_SIGNAL = "SIM VFB CEM200.FDP_Base.p_FsfOutputIf.sSigHeader.eSigStatus"
HA33_OUTPUT_SIG_STATUS_EML_SIGNAL = "SIM VFB CEM200.FDP_Base.p_EmlOutputIf.sigHeader.eSigStatus"
HA33_OUTPUT_SIG_STATUS_COH_SIGNAL = "SIM VFB CEM200.FDP_Base.p_CemAssocOutputIf.SigHeader.eSigStatus"
HA33_OUTPUT_SIG_STATUS_RMF_SIGNAL = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.sigHeader.eSigStatus"
HA33_OUTPUT_SIG_STATUS_VAL_SIGNAL = "SIM VFB CEM200.FDP_Base.p_ValOutputIf.sSigHeader.eSigStatus"

HA33_SENSOR_FAILURE_OUTPUT_SIP_COMMUNICATION_E2E_ERROR_SIGNAL_SUFFIX = "E2E_ERROR"
HA33_SENSOR_FAILURE_OUTPUT_SIP_COMMUNICATION_TIMEOUT_ERROR_SIGNAL_SUFFIX = "TIMEOUT_ERROR"
#

HA33_SENSOR_ARS510_OUTPUT_SIP_COMMUNICATION_E2E_ERROR_SIGNAL = "SIM VFB CEM200.ARS510.ARS510E2EFctStatus.E2E_ERROR"
HA33_SENSOR_ARS510_OUTPUT_SIP_COMMUNICATION_TIMEOUT_ERROR_SIGNAL = (
    "SIM VFB CEM200." "ARS510.ARS510E2EFctStatus.TIMEOUT_ERROR"
)

HA33_SRR520_FL_OUTPUT_SIP_COMMUNICATION_E2E_ERROR_SIGNAL = "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_fl.E2E_ERROR"
HA33_SRR520_FL_OUTPUT_SIP_COMMUNICATION_TIMEOUT_ERROR_SIGNAL = (
    "SIM VFB CEM200.SRR520." "SRR520E2EFctStatus_fl.TIMEOUT_ERROR"
)

HA33_SRR520_FR_OUTPUT_SIP_COMMUNICATION_E2E_ERROR_SIGNAL = "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_fr.E2E_ERROR"
HA33_SRR520_FR_OUTPUT_SIP_COMMUNICATION_TIMEOUT_ERROR_SIGNAL = (
    "SIM VFB CEM200.SRR520." "SRR520E2EFctStatus_fr.TIMEOUT_ERROR"
)

HA33_SRR520_RL_OUTPUT_SIP_COMMUNICATION_E2E_ERROR_SIGNAL = "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_rl.E2E_ERROR"
HA33_SRR520_RL_OUTPUT_SIP_COMMUNICATION_TIMEOUT_ERROR_SIGNAL = (
    "SIM VFB CEM200." "SRR520.SRR520E2EFctStatus_rl.TIMEOUT_ERROR"
)

HA33_SRR520_RR_OUTPUT_SIP_COMMUNICATION_E2E_ERROR_SIGNAL = "SIM VFB CEM200.SRR520.SRR520E2EFctStatus_rr.E2E_ERROR"
HA33_SRR520_RR_OUTPUT_SIP_COMMUNICATION_TIMEOUT_ERROR_SIGNAL = (
    "SIM VFB CEM200.SRR520." "SRR520E2EFctStatus_rr.TIMEOUT_ERROR"
)

HA33_VEHICLE_SIP_SIG_STATUS_CAMERA_RMF_SIGNAL = "ADC4xx.Valeo.sRoadPatch.sSigHeader.eSigStatus"

# HA33 INPUT CAMERA FAILURE SIGNAL Dictionary mapping as the signals do not change except PREFIX
# ----------------------------------------------------------------------------------------------------------------------
# SENSOR_CAMERA_VALEO_INPUT_FAILURE_SIGNAL_PREFIX = 'Local_Valeo_CANFD.VSS-FC_Private.'
#
# # HA33 INPUT ARS SIGNAL PREFIX
# # ------------------------------------------------------------------------------------------------------------------
# ----
# SENSOR_ARS510_SIGNAL_PREFIX = 'Local_ARS_CANFD.ARS510HA33_Private.'

HA33_SENSOR_CAMERA_VALEO_OUTPUT_SIP_COMMUNICATION_E2E_ERROR_SIGNAL = "SIM VFB CEM200.Valeo.ValeoE2EFctStatus.E2E_ERROR"
HA33_SENSOR_CAMERA_VALEO_OUTPUT_SIP_COMMUNICATION_TIMEOUT_ERROR_SIGNAL = (
    "SIM VFB CEM200.Valeo." "ValeoE2EFctStatus.TIMEOUT_ERROR"
)
HA33_VEHICLE_FAILURE_STATUS_CAMERA_SIGNAL = "ADC4xx.FDP_21P.FDP_SystemStatusADCU.sigCameraPlausibilityFailureStatus"
# HA33 OUTPUT SIG STATUS SIGNAL
# ----------------------------------------------------------------------------------------------------------------------
HA33_OUTPUT_SIP_SIG_STATUS_ARS_SEF_SIGNAL = "SIM VFB CEM200.ARS510.AgpPolySetFreespaceARS510.sSigHeader.eSigStatus"
HA33_OUTPUT_SIP_SIG_STATUS_ARS_RMF_SIGNAL = "SIM VFB CEM200.ARS510.RoadPatchARS510.sSigHeader.eSigStatus"

HA33_OUTPUT_SIP_SIG_STATUS_CAMERA_RMF_SIGNAL = "SIM VFB CEM200.Valeo.sRoadPatch.sSigHeader.eSigStatus"
HA33_OUTPUT_SIG_STATUS_SRR520_SEF_SIGNAL = "SIM VFB CEM200.SRR520.syncRef.sig_m_SrrFreespaceInfoSyncRef"
HA33_OUTPUT_SIP_SIG_STATUS_CAMERA_TPF_SIGNAL = "SIM VFB CEM200.Valeo.tpfCartesianObjectList.sigHeader.eSigStatus"

# HA33 OUTPUT PERCEPTION RANGE SIGNAL
# ----------------------------------------------------------------------------------------------------------------------
HA33_OUTPUT_PERCEPTION_RANGE_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_ValidityData.positionX"

# HA33 OUTPUT FAILURE STATUS SIGNAL
# ----------------------------------------------------------------------------------------------------------------------
HA33_OUTPUT_FAILURE_STATUS_ARS_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigFrontRadarPlausibilityFailureStatus"
)

HA33_OUTPUT_FAILURE_STATUS_CAMERA_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigCameraPlausibilityFailureStatus"
)

HA33_OUTPUT_FAILURE_STATUS_SRR520_FL_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigFrontLeftRadarPlausibilityFailureStatus"
)
HA33_OUTPUT_FAILURE_STATUS_SRR520_FR_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigFrontRightRadarPlausibilityFailureStatus"
)
HA33_OUTPUT_FAILURE_STATUS_SRR520_RL_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigRearLeftRadarPlausibilityFailureStatus"
)
HA33_OUTPUT_FAILURE_STATUS_SRR520_RR_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigRearRightRadarPlausibilityFailureStatus"
)
HA33_OUTPUT_FAILURE_STATUS_ODOMETRY_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_SystemStatusADCU." "sigOdometryAdcuPlausibilityFailureStatus"
)

HA33_OUTPUT_CEM_ALCA_STATUS_LEFT = "SIM VFB CEM200.FDP_21P.FDP_AlcaPermissionLeft.CemAlcaPermissionLeftStatus"
HA33_OUTPUT_CEM_ALCA_STATUS_RIGHT = "SIM VFB CEM200.FDP_21P.FDP_AlcaPermissionRight.CemAlcaPermissionRightStatus"

HA33_INPUT_LONGITUDINAL_ADCU_VDY_SIGNAL = "ADC4xx.IPVDY.VehDyn_t.Longitudinal.Accel"

# HA33 Odometry Signal
# ----------------------------------------------------------------------------------------------------------------------
HA33_INPUT_ARS_VDY_SIGNAL_PREFIX = "Local_ARS_CANFD.ARS510HA33_Private.ARS_VDY."

HA33_INPUT_SRR520_FL_VDY_SIGNAL_PREFIX = "Local_SRR_FL_CANFD.SRR520HA33_FL_Private.SRR_VDY."
HA33_INPUT_SRR520_FR_VDY_SIGNAL_PREFIX = "Local_SRR_FR_CANFD.SRR520HA33_FR_Private.SRR_VDY."
HA33_INPUT_SRR520_RL_VDY_SIGNAL_PREFIX = "Local_SRR_RL_CANFD.SRR520HA33_RL_Private.SRR_VDY."
HA33_INPUT_SRR520_RR_VDY_SIGNAL_PREFIX = "Local_SRR_RR_CANFD.SRR520HA33_RR_Private.SRR_VDY."

ADC420HA33_SAFETY_TEST_XML_PATH = (
    "trc/evaluation/functional_test_helper/" "helper_files/ADC420HA33/ADC420HA33_Safety.xml"
)
ADC420HA33_SIGNAL_TEST_SEF_JSON_PATH = (
    "trc/evaluation/functional_test_helper/" "helper_files/ADC420HA33/SignalTestConfig_SEF.json"
)

SYS100_FUNCTIONAL_TEST_JSON_PATH = (
    "trc/evaluation/functional_test_helper/" "helper_files/SYS100/SYS100_FunctionalTest.json"
)

HA33_ARS_FRSP_ITEMS_PREFIX = "Local_ARS_CANFD.ARS510HA33_Private.ARS_FRSP_ITEMS_"
HA33_ARS_FRSP_VERTEX_PREFIX = "Local_ARS_CANFD.ARS510HA33_Private.ARS_FRSP_VERTEX_"

HA33_ARS_OBJECT_PREFIX = "Local_ARS_CANFD.ARS510HA33_Private.ARS_OBJ_"

HA33_SRR_FL_OBJECT_PREFIX = "Local_SRR_FL_CANFD.SRR520HA33_FL_Private."
HA33_SRR_FR_OBJECT_PREFIX = "Local_SRR_FR_CANFD.SRR520HA33_FR_Private."
HA33_SRR_RL_OBJECT_PREFIX = "Local_SRR_RL_CANFD.SRR520HA33_RL_Private."
HA33_SRR_RR_OBJECT_PREFIX = "Local_SRR_RR_CANFD.SRR520HA33_RR_Private."

HA33_SRR_FL_OBJECT_ST_PREFIX = "Local_SRR_FL_CANFD.SRR520HA33_FL_Private.SRR_ECU_FCT_STATUS."
HA33_SRR_FR_OBJECT_ST_PREFIX = "Local_SRR_FR_CANFD.SRR520HA33_FR_Private.SRR_ECU_FCT_STATUS."
HA33_SRR_RL_OBJECT_ST_PREFIX = "Local_SRR_RL_CANFD.SRR520HA33_RL_Private.SRR_ECU_FCT_STATUS."
HA33_SRR_RR_OBJECT_ST_PREFIX = "Local_SRR_RR_CANFD.SRR520HA33_RR_Private.SRR_ECU_FCT_STATUS."

HA22_SRR_FL_OBJECT_ST_PREFIX = "Local_SRR_FL_CANFD.SRR520HA22_FL_Private.SRR_ECU_FCT_STATUS."
HA22_SRR_FR_OBJECT_ST_PREFIX = "Local_SRR_FR_CANFD.SRR520HA22_FR_Private.SRR_ECU_FCT_STATUS."
HA22_SRR_RL_OBJECT_ST_PREFIX = "Local_SRR_RL_CANFD.SRR520HA22_RL_Private.SRR_ECU_FCT_STATUS."
HA22_SRR_RR_OBJECT_ST_PREFIX = "Local_SRR_RR_CANFD.SRR520HA22_RR_Private.SRR_ECU_FCT_STATUS."

SRR_OBJECT_PREFIX = "SRR_OBJ_"
SRR_FRSP_ITEMS_PREFIX = "SRR_FRSP_ITEMS_"
SRR_FRSP_VERTEX_PREFIX = "SRR_FRSP_VERTEX_"

HA33_CEM_FDP_21P_TPF_PREFIX = "SIM VFB CEM200.FDP_21P"
HA33_CEM_FDP_Base_TPF_PREFIX = "SIM VFB CEM200.FDP_Base"
HA33_CEM_FDP_21P_SEF_PREFIX = "SIM VFB CEM200.FDP_21P"

HA33_SAFETY_XMLS_PATH = "data/adc420HA33/safety_test"

HA33_INPUT_TIMESTAMP_ADCU_VDY_SIGNAL = "ADC4xx.IPVDY.VehDyn_t.sSigHeader.uiTimeStamp"
HA33_OUTPUT_FAILED_ACCEPTABLE_SAMPLES_COUNT = 3
HA33_ARS_CANFD_BLOCKAGESTATUS = "Local_ARS_CANFD.ARS510HA33_Private.ARS_ECU_FCT_STATUS.e_SP_BlockageStatus"
HA33_SRR_FL_CANFD_BLOCKAGESTATUS = "Local_SRR_FL_CANFD.SRR520HA33_FL_Private.SRR_ECU_FCT_STATUS.e_SP_BlockageStatus"
HA33_SRR_FR_CANFD_BLOCKAGESTATUS = "Local_SRR_FR_CANFD.SRR520HA33_FR_Private.SRR_ECU_FCT_STATUS.e_SP_BlockageStatus"
HA33_VALEO_CANFD_BLOCKAGESTATUS = "Local_Valeo_CANFD.VSS-FC_Private." "CAM_Failure_Info.CAM_INTERNAL_FAILURE"

HA33_CEM_FDP_BASE_RMF_OUTPUT_NUM_LINEAR_OBJ = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.numLinearObjects"
HA33_CEM_FDP_BASE_RMF_OUTPUT_NUM_POINTS = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.numPoints"
HA33_CEM_FDP_BASE_RMF_OUTPUT_NUM_BOUNDARY = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.associations.numBoundaryContinuity"
HA33_CEM_FDP_BASE_RMF_OUTPUT_NUM_LANE_COUNTS = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.associations.numLaneCounts"
HA33_CEM_FDP_BASE_RMF_OUTPUT_NUM_SENSOR = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.associations.numSensorAssociations"
HA33_CEM_FDP_BASE_RMF_OUTPUT_NUM_SLOPES = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.associations.numSlopes"
HA33_CEM_FDP_BASE_RMF_OUTPUT_LANE_NUM_CONNECTIONS = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.laneTopology.numConnections"
HA33_CEM_FDP_BASE_RMF_OUTPUT_NUM_LANE_SEGMENTS = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.laneTopology.numLaneSegments"
HA33_CEM_FDP_BASE_RMF_OUTPUT_ROAD_NUM_CONNECTIONS = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.roadTopology.numConnections"
HA33_CEM_FDP_BASE_RMF_OUTPUT_NUM_ROAD_SEGMENTS = "SIM VFB CEM200.FDP_Base.p_RmfOutputIf.roadTopology.numRoadSegments"

# HA22 DEM SIGNALS
# ----------------------------------------------------------------------------------------------------------------------

HA33_CEM_FDP21P_DEM_VALEO_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_DemCameraStatus.sigCameraPlausibilityDemStatus"
HA33_CEM_FDP21P_DEM_TEMPORARY_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_DemCemTemporaryStatus.cemTemporayFailureDemStatus"
HA33_CEM_FDP21P_DEM_PERMANENT_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_DemCemPermanentStatus.cempermanentFailureDemStatus"
HA33_CEM_FDP21P_DEM_ODOMETRY_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_DemOdometryRadarStatus." "sigOdometryAdcuPlausibilityDemStatus"
)
HA33_CEM_FDP21P_DEM_ARS_SIGNAL = "SIM VFB CEM200.FDP_21P.FDP_DemFrontRadarStatus.sigFrontRadarPlausibilityDemStatus"
HA33_CEM_FDP21P_DEM_SRR_RR_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_DemRearRightRadarStatus." "sigRearRightRadarPlausibilityDemStatus"
)
HA33_CEM_FDP21P_DEM_SRR_RL_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_DemRearLeftRadarStatus." "sigReartLeftRadarPlausibilityDemStatus"
)
HA33_CEM_FDP21P_DEM_SRR_FR_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_DemFrontRightRadarStatus." "sigFrontRightRadarPlausibilityDemStatus"
)
HA33_CEM_FDP21P_DEM_SRR_FL_SIGNAL = (
    "SIM VFB CEM200.FDP_21P.FDP_DemFrontleftRadarStatus." "sigFrontLeftRadarPlausibilityDemStatus"
)

HA33_RADAR_SENSOR_ARS510 = "Local_ARS_CANFD.ARS510HA33_Private.ARS_ECU_FCT_STATUS."
HA33_RADAR_SENSOR_SRR520_FL = "Local_SRR_FL_CANFD.SRR520HA33_FL_Private.SRR_ECU_FCT_STATUS."
HA33_RADAR_SENSOR_SRR520_FR = "Local_SRR_FR_CANFD.SRR520HA33_FR_Private.SRR_ECU_FCT_STATUS."
HA33_RADAR_SENSOR_SRR520_RL = "Local_SRR_RL_CANFD.SRR520HA33_RL_Private.SRR_ECU_FCT_STATUS."
HA33_RADAR_SENSOR_SRR520_RR = "Local_SRR_RR_CANFD.SRR520HA33_RR_Private.SRR_ECU_FCT_STATUS."
HA33_CAMERA_FAILURE_VALEO = "Local_Valeo_CANFD.VSS-FC_Private.CAM_Failure_Info"
