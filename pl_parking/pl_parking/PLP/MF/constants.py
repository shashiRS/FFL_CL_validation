"""File used to store all constants used in kpis from MF directory"""

from collections import Counter
from enum import IntEnum

import numpy as np


class ParkingMachineStates:
    """Defining the constants for parking machine states"""

    PPC_INACTIVE = 0
    PPC_BEHAVIOR_INACTIVE = 1
    PPC_SCANNING_INACTIVE = 2
    PPC_SCANNING_IN = 3
    PPC_SCANNING_OUT = 4
    PPC_SCANNING_RM = 5
    PPC_PARKING_INACTIVE = 6
    PPC_PREPARE_PARKING = 7
    PPC_PERFORM_PARKING = 8
    PPC_PARKING_PAUSE = 9
    PPC_PARKING_FAILED = 10
    PPC_OFFER_HANDOVER = 11
    PPC_SUCCESS = 12
    PPC_PARKING_CANCELED = 13
    PPC_IRREVERSIBLE_ERROR = 14
    PPC_REVERSIBLE_ERROR = 15
    PPC_DEMO_OFF = 23
    PPC_SCANNING_GP = 24


class SignalsNumber:
    """Defining the constants for parking signals"""

    START_INDEX = 1
    REF_ID_US_POINT_NUMBER = 257
    REF_ID_CEM_ELEMENT_POINT_NUMBER = 65
    SFM_POINT_NUMBER = 1001
    PCL_NUMBER = 50
    RTA_EV_CONT_NUMBER = 128
    CURRENT_TASK_START = 130  # from profilinganalysis.cpp of ultrasonic tool
    PARK_LINE_NUMBER = 10
    RUN_TIME_STEP_NUMBERS = 34


class RunTimeId(IntEnum):
    """Enumerates the different runtime IDs"""

    US_CORRELATOR = 0  # not found in c++ code of ultrasonic
    US_DRV_SPI = 1
    RTARUN = 32
    CFG_MGR = 33
    VEHICLE_SIGNALS = 34
    VEDODO = 35
    TRJCTL = 36
    MEASFREEZE_CAN = 37
    TCE = 38
    US_DRV = 64
    VEHICLE_SIGNALS_EM = 65
    US_PROCESSING = 66
    US_EM = 67
    US_PSI = 68
    APPDEMO_PARKSM = 69
    MF_PARKSM_CORE = 70
    MF_TRJPLA = 71
    MF_LSCA = 72
    MF_MANAGER = 73
    MF_PDW = 74
    MF_DRV = 75
    APPDEMO_HMIH = 76
    MEASFREEZE_EM = 77
    APPDEMO_DRV = 78
    APPDEMO_TONH = 80
    MF_WHLPROTECT = 81


class RtaEvents(IntEnum):
    """Enumerates the different RTA events"""

    RTA_EVT_MARKER = 0
    RTA_EVT_ALGOSTART = 1
    RTA_EVT_ALGOEND = 2
    RTA_EVT_TASKSWITCH = 3
    RTA_EVT_TASKRDY = 4
    RTA_EVT_SAMPLEVALUE = 5
    RTA_EVT_SAMPLESELECT = 6
    RTA_EVT_MAX_TYPES = 7


class TransfToOdomConstants:
    """Defining the constants regarding M7board.EM_Thread.ApEnvModelPort.transformationToOdometry signals"""

    NB_SIGNALS = 3
    X_COORD = 0
    Y_COORD = 1
    ANGLE = 2


class SiSlotShrinkageConstants:
    """THRESOLD_TIME_S and THRESOLD_WIDTH_M are used to overcome possible sampling frequency issues in this KPI"""

    THRESOLD_TIME_S = 0.5
    THRESOLD_WIDTH_M = 0.5


class ParkingScenario:
    """Defining the constants for parking scenarios"""

    PARALLEL_PARKING = 0
    PERPENDICULAR_PARKING = 1
    ANGLED_PARKING_OPENING_TOWARDS_BACK = 2
    ANGLED_PARKING_OPENING_TOWARDS_FRONT = 3
    GARAGE_PARKING = 4
    DIRECT_PARKING = 5
    MAX_NUM_PARKING_SCENARIO_TYPES = 6


class ParkingModes:
    """Defining the constants for parking modes"""

    PARKING_MODE_NOT_VALID = 0
    PARK_IN = 1
    PARK_OUT = 2
    GARAGE_PARKING_IN = 3
    GARAGE_PARKING_OUT = 4
    TRAINED_PARKING_TRAIN = 5
    TRAINED_PARKING_REPLAY = 6
    REMOTE_MANEUVERING = 7
    UNDO_MANEUVER = 8


class ConstantsNbPlannedStrokes:
    """Defining the constants for number of planned strokes"""

    THRESHOLD_STROKES = 3
    MAX_VALID_SEGMENTS = 25


class ConstantsParkingSlotType:
    """Defining the constants for parking slot types test"""

    NUMBER_OF_BOXES = 1


class ConstantsPlannedStrokes:
    """Defining the constants for planned number of strokes test"""

    NB_STROKES = 3


class DgpsBoxesColumns:
    """Stores the names of the corners coordinates signals"""

    BOX_1_CORNER_LEFT_X_1 = "Box1CornerLeftX1"
    BOX_1_CORNER_LEFT_Y_1 = "Box1CornerLeftY1"
    BOX_1_CORNER_RIGHT_X_1 = "Box1CornerRighttX1"
    BOX_1_CORNER_RIGHT_Y_1 = "Box1CornerRightY1"
    BOX_1_CORNER_LEFT_X_2 = "Box1CornerLeftX2"
    BOX_1_CORNER_LEFT_Y_2 = "Box1CornerLeftY2"
    BOX_1_CORNER_RIGHT_X_2 = "Box1CornerRightX2"
    BOX_1_CORNER_RIGHT_Y_2 = "Box1CornerRightY2"
    BOX_2_CORNER_LEFT_X_1 = "Box2CornerLeftX1"
    BOX_2_CORNER_LEFT_Y_1 = "Box2CornerLeftY1"
    BOX_2_CORNER_RIGHT_X_1 = "Box2CornerRighttX1"
    BOX_2_CORNER_RIGHT_Y_1 = "Box2CornerRightY1"
    BOX_2_CORNER_LEFT_X_2 = "Box2CornerLeftX2"
    BOX_2_CORNER_LEFT_Y_2 = "Box2CornerLeftY2"
    BOX_2_CORNER_RIGHT_X_2 = "Box2CornerRightX2"
    BOX_2_CORNER_RIGHT_Y_2 = "Box2CornerRightY2"


class StaticObjectsShapeConstants:
    """Defining the constants regarding M7board.EM_Thread.ApEnvModelPort.staticObjects.objShape_m signals"""

    NB_OBJ_SHAPE = 20
    NB_STATIC_OBJ = 31

    # Name defined for the signal in EntryParkingSignals class
    NAME_COLUMN_DF = "StaticObjectShape"


class DgpsConstants:
    """
    THRESOLD_TIME_S and THRESOLD_WIDTH_M are used to overcome possible
    sampling frequency issues in obtaining the reference point
    """

    THRESOLD_TIME_S = 0.5
    THRESOLD_ANGLE_DEG = 1
    THRESOLD_DISTANCE_M = 1
    INVALID_VALUE_SLOT_SHRINKAGE = 999.0

    # Width of the Boxes [m]
    WIDTH_BOX_M = 1.6


class ConstantsSiSlotShrinkage:
    """Defining the constants for SI Slot Shrinkage test"""

    SI_SHRINKAGE_RANGE = [-20.0, 20.0]
    NUMBER_OF_BOXES = 1


class ConstantsUsemLeagLagShrinkage:
    """Defining the constants for Usem Lead Lag Shrinkage test"""

    LEAD_RANGE = [-10.0, 10.0]
    LAG_RANGE = [-10.0, 10.0]
    SLOT_SHRINKAGE_RANGE = [-20.0, 20.0]
    USEM_KPI_EXPECTED = 1


class ConstantsVelocity:
    """Defining the constants for Velocity test"""

    MAX_SPEED_THRESHOLD = 20  # Km/h


class ParkingBoxConstants:
    """Defining the constants regarding parking box"""

    NB_COORDINATES = 8
    X_COORD_RIGHT_TOP = 0
    Y_COORD_RIGHT_TOP = 1
    X_COORD_LEFT_TOP = 2
    Y_COORD_LEFT_TOP = 3
    X_COORD_LEFT_BOTTOM = 4
    Y_COORD_LEFT_BOTTOM = 5
    X_COORD_RIGHT_BOTTOM = 6
    Y_COORD_RIGHT_BOTTOM = 7
    NB_PARKING_BOXES = 3
    X_LENGTH_THRESHOLD = 0
    Y_LENGTH_THRESHOLD = 0
    X_WIDTH_THRESHOLD = 0
    Y_WIDTH_THRESHOLD = 0
    # Minimum and maximum thresholds for length and width of the parking box
    LEN_MIN = 0
    LEN_MAX = 0
    WID_MIN = 0
    WID_MAX = 0
    # Name defined for the signal in EntryParkingSignals class
    NAME_COLUMN_DF = "SlotCoordinates"


class EgoPoseApConstants:
    """Defining the constants regarding M7board.EM_Thread.ApEnvModelPort.egoVehiclePoseForAP signals"""

    NB_SIGNALS = 3
    X_COORD = 0
    Y_COORD = 1
    YAW_ANGLE = 2

    # Name defined for the signal in EntryParkingSignals class
    NAME_COLUMN_DF = "EgoPositionAP"


class GeneralConstants:
    """Defining general constants"""

    MANEUVER_ACTIVE = 17
    MANEUVER_FINISH = 5
    AP_AVG_ACTIVE_IN = 3
    T_POSE_REACHED = 0.8  # unit [s]
    IDX_TO_S = 100
    V_MAX_L3 = 2.777777778  # unit [m/s]
    M_TO_CM = 100
    NANOSEC_IN_MILLISEC = 1000
    US_IN_S = 1000000
    S_IN_HOURS = 3600
    M_TO_KM = 1000
    ACTIVATE_PLOTS = False
    # time step in milliseconds:
    TIME_STEP = 33
    KM_TO_M = 1000
    ACTIVE_STATE = 1
    INVALID_VALUE_OFFSET_GT_DATA = 9999999.0
    MS_IN_S = 1000
    NANOSEC_IN_MILLISEC = 1000
    M_TO_MM = 1000
    MPS_TO_KMPH = 3.6
    PERCENTILE_RATE = 100
    NUMBERr_SLOTCOORDS_SIGNALS = 8
    NUMBER_SLOTCOORDS_ARRAY = 4
    STAND_STILL = 0.01


class ConstantsVedodo:
    """Defining the constants used in vedodo test"""

    NB_DECIMALS = 5
    PI_TO_DEG = 180
    TIME_THRESHOLD_YAW_RATE_MS = 500  # unit [ms]
    MAX_ERR_DIST_M = 0.1  # unit [m]
    MAX_ERR_YAW_DEG = 0.9  # unit [deg]
    THRESHOLD_TIME_S = 0.05  # unit [s]
    THRESHOLD_YAW_RATE = 0.6  # unit [deg/s]
    SLIDE_WINDOW_DISTANCE_1 = 1  # unit [m]
    SLIDE_WINDOW_DISTANCE_5 = 5  # unit [m]
    MAX_ERR_YAW_DEG_1M = 0.3  # unit [deg]


class ConstantsSlotDetection:
    """Defining the constants used in slot detection test"""

    CAR_LENGTH = 4.767  # unit [m]
    CAR_WIDTH = 1.832  # unit [m]
    CAR_OVERHANG = 1.096  # unit [m]
    TIME_DELAY = 0.6  # unit [s]
    NO_ROAD_VALUE = 0
    TRUE_VALUE = 1
    EXPORTED_SLOTS_NUMBER = 2
    EXPORTED_SLOT_VERTICES_NUMBER = 4
    MARKER_TO_SLOT_VERTEX_MAX_DIST = CAR_WIDTH  # unit [m]


class ConstantsTrajctl:
    """Defining the constants used in trajctl test"""

    LAT_ACC_EGO_MAX = 10.0  # unit [m/s^2]
    LONG_ACC_EGO_MAX = 10.0  # unit [m/s^2]
    YAWRATE_MAX = 0.698131111  # unit [rad/s]
    V_AVERAGE_MIN_PERPENDICULAR = 0.01  # unit [m/s]
    ANGLE_DEVIATION_MAX = 0.052333333  # unit [rad]
    LAT_DEVIATION_MAX = 0.05  # unit [m]
    AP_LO_STOP_ACCURACY_NEG = -0.04  # unit [m]


class ConstantsTrajpla:
    """Defining the constants used in trajpla test"""

    ACT_NB_STROKES_GREATER_MAX_NB_STROKES_FALSE = 0
    NB_CRV_STEPS_FALSE = 0
    FAIL_REASON = 0
    PATH_FOUND = 1
    TRAJ_VALID = 1
    T_PARALLEL_PARKING = 0
    T_PERP_PARKING_FWD = 1
    T_PERP_PARKING_BWD = 2
    T_ANGLED_PARKING_STANDARD = 3
    T_ANGLED_PARKING_REVERSE = 4
    T_REM_MAN_FWD = 5
    T_REM_MAN_BWD = 6
    T_PERP_PARKING_OUT_FWD = 7
    T_PERP_PARKING_OUT_BWD = 8
    T_PAR_PARKING_OUT = 9
    T_ANGLED_PARKING_STANDARD_OUT = 10
    T_ANGLED_PARKING_REVERSE_OUT = 11
    T_UNDO = 12
    T_GP_FWD = 13
    T_GP_BWD = 14
    T_GP_OUT_FWD = 15
    T_GP_OUT_BWD = 16
    T_GP_FWD_AXIS = 17
    T_GP_BWD_AXIS = 18
    T_GP_OUT_FWD_AXIS = 19
    T_GP_OUT_BWD_AXIS = 20
    T_UNDEFINED = 21
    PAR_PARK_IN_TRAJ = 1
    PERP_PARK_IN_TRAJ = 0
    PERP_PARK_OUT_TRAJ = 2
    PAR_PARK_OUT_TRAJ = 3
    REMOTE_MAN_TRAJ = 4
    UNDO_TRAJ = 5
    MAX_NUM_PLANNED_TRAJ_TYPES = 6
    TP_NOT_VALID = 0
    TP_NOT_REACHABLE = 1
    TP_FULLY_REACHABLE = 2
    TP_SAFE_ZONE_REACHABLE = 3
    TP_MANUAL_FWD_REACHABLE = 4
    TP_MANUAL_BWD_REACHABLE = 5
    MAX_NUM_POSE_REACHABLE_STATUS = 6
    AP_INACTIVE = 0
    AP_SCAN_IN = 1
    AP_SCAN_OUT = 2
    AP_AVG_ACTIVE_IN = 3
    AP_AVG_ACTIVE_OUT = 4
    AP_AVG_PAUSE = 5
    AP_AVG_UNDO = 6
    AP_ACTIVE_HANDOVER_AVAILABLE = 7
    AP_AVG_FINISHED = 8
    PARALLEL_PARKING = 0
    PERPENDICULAR_PARKING = 1
    ANGLED_PARKING_OPENING_TOWARDS_BACK = 2
    ANGLED_PARKING_OPENING_TOWARDS_FRONT = 3
    GARAGE_PARKING = 4
    DIRECT_PARKING = 5
    MAX_NUM_PARKING_SCENARIO_TYPES = 10
    PARALLEL_PARK_MAX_TARGET_POSE = 1
    PERP_PARK_MAX_TARGET_POSE = 2
    ANGLED_PARK_MAX_TARGET_POSE = 1
    MP_RECALL_FINISHED = 9
    MP_TRAIN_FINISHED = 5
    RA_AVG_FINISHED = 4
    RM_AVG_FINISHED = 4
    GP_AVG_FINISHED = 7
    AP_AVG_FINISHED = 8
    AP_INACTIVE = 0
    GP_INACTIVE = 0
    RM_INACTIVE = 0
    MP_INACTIVE = 0
    RA_INACTIVE = 0
    AP_P_MAX_NUM_POSES_IN_PATH_NU = 1000
    AP_P_MAX_NUM_SEGMENTS_IN_PATH_NU = 25


class ConstantsNuc:
    """Defining the constants used in NUC test"""

    PLANNING_CONTROL_ACTIVE = 1
    DRIVING_MODE_REQUEST_TRUE = 1
    TRAJ_CTRL_ACTIVE = 1
    USE_CASE_FALSE = 0


class ConstantsTaposd:
    """Defining the constants used in TAPOSD test"""

    OUTSIDE_PB = 1
    COLLISION = 1


class HeadUnitVisuPortMsgVal:
    """Defining the constants regarding head unit visu port message signal"""

    INTERNAL_SYSTEM_ERROR = 19
    PARKING_CANCELLED = 4
    MAX_WAITING_TIME_EXCEEDED = 23
    PARKING_CANCELLED_THROTTLE = 29
    PARKING_CANCELLED_STEER = 30
    PARKING_FAILED = 32


class HeadUnitVisuPortScreenVal:
    """Defining the constants regarding head unit visu port screen signal"""

    SYSTEM_NOT_ACTIVE = 0
    SCANNING_ACTIVE = 1
    PARKING_SPACE_SELECTION = 2
    REMOTE_APP_ACTIVE = 3
    MANEUVER_ACTIVE = 17
    MANEUVER_FINISHED = 5
    MANEUVER_INTRRERUPTED = 6
    UNDO_MANEUVER_ACTIVE = 7
    START_REMOTE_APP = 8
    PARK_OUT_INIT = 9
    PARK_OUT_SIDE = 10
    MENU_REM = 11
    MANEUVER_ACTIVE_LONG_MAN = 12
    REM_SV = 13
    REM_MAN = 14
    REM_MAN_ACTIVE = 15
    GARAGE_PARKING_START = 16


class ConstantsAupCore:
    """Defining the constants used in AUP test"""

    STEER_ANGLE_REQ_MIN = 0.1  # unit [rad]
    V_MIN = 0.002777778  # unit [m/s]
    T_SIM_MAX_START = 10.0  # unit [s]
    T_SIM_MAX = 200.0  # unit [s]
    AUP_CYCLE_TIME_MAX = 9999.0
    LAT_ACC_EGO_MAX = 10.0  # unit [m/s^2]
    YAW_RATE_MAX = 0.698131111  # unit [rad/s]
    LONG_ACC_EGO_MAX = 10.0  # unit [m/s^2]
    TOGGLE_AP_ACTIVE = 28


class PlotlyTemplate:
    """Defining the constants used in plotly graphs"""

    lgt_tmplt = {"margin": dict(r=0, l=0, t=50, b=0)}


class Platforms:
    """Defining the constants regarding functional tests platform"""

    # Functional tests platform
    VEHICLE = "Vehicle"
    SIM = "Sim"
    GT = "GT"
    ANY = "Any"


class ConstantsLSCA:
    """Defining the constants regarding lsca test"""

    VAL_LSCA = 2


class ConstantsDeviation:
    """Defining the constants used in deviation tests"""

    INVALID_VALUE_DEVIATION = 999999.0
    LATERAL_THRESHOLD = 15.0
    LONGITUDINAL_THRESHOLD = 15.0


class GearReqConstants:
    """Defining the constants regarding M7board.CAN_Thread.GearboxCtrlRequestPort.gearReq_nu signal"""

    GEAR_D = 11
    GEAR_R = 13


class TargetPoss(IntEnum):
    """Enumerates the different types of target parking positions"""

    T_PARALLEL_PARKING = 0
    T_PERP_PARKING_FORWARD = 1
    T_PERP_PARKING_BACKWARD = 2
    T_ANGLED_PARKING_STANDARD = 3
    T_ANGLED_PARKING_REVERSE = 4


class ConstantsNbAdditionalStrokes:
    """Defining the constants used in number of additional strokes test"""

    THRESHOLD_ANG_FRONT_STROKES = 2.0
    THRESHOLD_ANG_BACK_STROKES = 2.0
    THRESHOLD_PAR_STROKES = 2.0
    THRESHOLD_PERP_STROKES = 3.0
    THRESHOLD_ADDITIONAL_STROKES = 0.0


class CoreStopStatus(IntEnum):
    """Enumerates the different park core stop reasons"""

    PARKING_NO_STOP = 0
    PARKING_FAILED_TPD_LOST = 1
    PARKING_FAILED_PATH_LOST = 2
    PARKING_SUCCESS = 3


class ParkCoreStatus(IntEnum):
    """Enumerates the different park core status"""

    CORE_SCANNING = 1
    CORE_PARKING = 2
    CORE_PAUSE = 3
    CORE_FINISH = 4
    CORE_ERROR = 5


class ConstantsMaxLongiDeceleration:
    """Defining the constants used in max longitudinal deceleration"""

    THRESHOLD_MAX_LONG_ACC = 1.5


class ConstantsMaxSteeringWheelAcc:
    """Defining the constants used in max steering wheel acceleration test"""

    THRESHOLD = 5  # rad/s^2
    TIME_STEP_US = 10**4
    CUTOFF_FREQ = 3


class ConstantsMaxSteeringWheelVelocity:
    """Defining the constants used in max steering wheel velocity test"""

    THRESHOLD = 0.38  # rad/s


class ConstantsMaxEgoYawRate:
    """Defining the constants used in max ego yaw rate test"""

    THRESHOLD = 1.2  # rad/s


class ParkSmCoreStatus(IntEnum):
    """Enumerates the different parking modes core statuses"""

    INVALID_VALUE = 0
    SCANNING_IN = 1
    PERFORM_PARKING = 2


class ConstantsYawPositionAccuracy:
    """Defining the constants used in yaw position accuracy test"""

    THRESHOLD = 0.0872


class TargetPosesPortType(IntEnum):
    """Defining the constants for target poses"""

    T_PARALLEL_PARKING = 0
    T_PERP_PARKING_FWD = 1
    T_PERP_PARKING_BWD = 2
    T_ANGLED_PARKING_FWD = 3
    T_ANGLED_PARKING_BWD = 4


class TargetPosesPortReachableStatus(IntEnum):
    """Defining the constants for target poses reachable status"""

    TP_NOT_VALID = 0
    TP_NOT_REACHABLE = 1
    TP_FULLY_REACHABLE = 2
    TP_SAFE_ZONE_REACHABLE = 3
    TP_MANUAL_FWD_REACHABLE = 4
    TP_MANUAL_BWD_REACHABLE = 5
    MAX_NUM_POSE_REACHABLE_STATUS = 6


class LateralErrorConstants:
    """Defining the constants used in lateral error test"""

    THRESHOLD = 5.0  # cm
    M_TO_CM_COEF = 100


class OrientationError:
    """Defining the constants used in orientation error test"""

    THRESHOLD = 1.0


class StrokeConstants:
    """Defining the constants used in average number of strokes test"""

    PARKING_SUCCESS_VALUE = 3

    EXPECTED_PERPENDICULAR_BACKWARDS_STROKES = 5
    EXPECTED_PERPENDICULAR_FORWARD_STROKES = 4
    EXPECTED_PARALLEL_LARGE_STROKES = 4
    EXPECTED_PARALLEL_MEDIUM_STROKES = 6
    EXPECTED_PARALLEL_SMALL_STROKES = 8

    LARGE_THRESHOLD = 1.4
    SMALL_THRESHOLD = 1

    DISTANCE_LIMIT = 0.05
    SPEED_THRESHOLD_HI = 0.1
    SPEED_THRESHOLD_LO = 0


class AccuracyThreshold:
    """Defining the constants used in fusion tests"""

    THRESHOLD_RANGE = [-0.5, 0.15]  # metres
    MANEUVER_END = 1


class SlotPersistenceFusion:
    """Manages the validity and consolidation of parking slot data."""

    INVALID_PARKING_BOX_NUMBER = 0


class GroundTruthDataConstants:
    """Defining the Ground Truth Data Constants used for detected lines, Park Markers and ego of the vehicle"""

    ROTATION_ANGLE = -np.pi / 2  # The value was taken from Ultrasonic tool C++ code
    EGO_MIDDLE_POINT_X_M = 1.281
    THRESHOLD_DISTANCE_DETECTED_LINES_M = 0.3
    IDX_MAX_SIGNALS_DETECTED_LINES = 9


class UltraSonicSensorsPoints:
    """Points relative to GPS point of the ego [meters]"""

    POINT_1_X = 3.14
    POINT_1_Y = 0.88
    POINT_2_X = 3.44
    POINT_2_Y = 0.72
    POINT_3_X = 3.65
    POINT_3_Y = 0.28
    POINT_4_X = 3.65
    POINT_4_Y = -0.3
    POINT_5_X = 3.44
    POINT_5_Y = -0.74
    POINT_6_X = 3.14
    POINT_6_Y = -0.9
    POINT_7_X = -0.36
    POINT_7_Y = -0.89
    POINT_8_X = -0.95
    POINT_8_Y = -0.68
    POINT_9_X = -1.09
    POINT_9_Y = -0.28
    POINT_10_X = -1.09
    POINT_10_Y = 0.28
    POINT_11_X = -0.95
    POINT_11_Y = 0.68
    POINT_12_X = -0.36
    POINT_12_Y = 0.89


class LSCAConstants:
    """Defining the constants used in LSCA KPIs"""

    MAX_DIST_TO_GT = 0.5
    MIN_HEIGHT_GEOM_POINT = 0.2
    OFFSET_X_AXIS = -2.786


class GroundTruthParkSlot(IntEnum):
    """Defining the constants for coordinates of GT parking slot"""

    LEFT_DOWN_POINT = 0
    LEFT_UP_POINT = 1
    RIGHT_DOWN_POINT = 2
    RIGHT_UP_POINT = 3


class Coordinates(IntEnum):
    """Defining the constants for coordinates of Wheelstopper groundtruth data"""

    X_AXIS = 0
    Y_AXIS = 1
    START_POINT = 0
    END_POINT = 1


class GroundTruthConstants(IntEnum):
    """Defining the constants used in aa test"""

    GT_TIME_STEP = 33
    WHEEL_BASE = 2790
    GT_DETECTION_FRONT_REAR = 8
    GT_DETECTION_LEFT_RIGHT = 12
    FRONT_OVERHANG = 872
    REAR_OVERHANG = 1108


class LscaConstants:
    """Defining the constants used in LSCA KPI"""

    DEACTIVATE = 0
    ACTIVATE = 1
    FALSE_POSITIVE = 255

    MAX_ALLOWED_ACTIVATIONS = 1  # threshold for True Positive KPI
    SAFETY_MARGIN_CRASH = 1.0  # cm
    SAFETY_MARGIN_STATIC = 20.0  # cm
    SAFETY_MARGIN_DYNAMIC = 100.0  # cm
    # Counter object to add up offset thresholds
    # unit : cm
    OFFSET_PLAN = Counter(
        {
            1: 0.55,
            2: 1.11,
            3: 1.66,
            4: 2.22,
            5: 2.77,
            6: 3.32,
            7: 3.88,
            8: 4.44,
            9: 5.0,
            10: 5.54,
        }
    )
    OFFSET_UNCERTAIN = Counter(
        {
            1: 5,
            2: 5,
            3: 5,
            4: 5,
            5: 7.71,
            6: 11,
            7: 15.1,
            8: 20,
            9: 25,
            10: 30,
        }
    )
    DISTANCE_TO_OBJ = OFFSET_PLAN + OFFSET_UNCERTAIN


class PDWConstants:
    """Defining the constants used in PDW KPI"""

    GREEN_ZONE = (2.55, 1.7)
    YELLOW_ZONE = (1.7, 0.85)
    RED_ZONE = 0.85
    NUMBER_SECTORS = 4
    SECTOR_MAPPING = {
        "FRONT": {
            0: 0,
            1: 1,
            2: 2,
            3: 3,
        },
        "REAR": {
            0: 11,
            1: 10,
            2: 9,
            3: 8,
        },
    }


class HilCl:
    """HIL CL related constans"""

    class Hmi:
        """Defining the constants regarding HMI commands"""

        class Command:
            """Defining the constants regarding HmiCommands"""

            TAP_ON_START_SELECTION = 17
            TAP_ON_START_PARKING = 18
            TAP_ON_INTERRUPT = 19
            TAP_ON_CONTINUE = 20
            TAP_ON_START_REMOTE_PARKING = 24
            TAP_ON_SWITCH_DIRECTION = 25
            TAP_ON_SWITCH_ORIENTATION = 26
            TOGGLE_AP_ACTIVE = 28
            TAP_ON_LSCA_RELEASE_BRAKE = 29

        class HeadUnit:
            """Defining the constants regarding HeadUnit states"""

            SYSTEM_NOT_ACTIVE = 0
            SCANNING_ACTIVE = 1
            PARKING_SPACE_SELECTION = 2
            REMOTE_APP_ACTIVE = 3
            MANEUVER_ACTIVE = 4
            MANEUVER_FINISHED = 5
            MANEUVER_INTRRERUPTED = 6
            UNDO_MANEUVER_ACTIVE = 7
            START_REMOTE_APP = 8
            PARK_OUT_INIT = 9
            PARK_OUT_SIDE = 10
            MENU_REM = 11
            MANEUVER_ACTIVE_LONG_MAN = 12
            REM_SV = 13
            REM_MAN = 14
            REM_MAN_ACTIVE = 15
            GARAGE_PARKING_START = 16
            PDC_ACTIVe = 17
            GP_START = 18
            GP_MANEUVER_ACTIVE = 19
            DIAG_ERROR = 20

            dict_head_unit = {
                0: "SYSTEM_NOT_ACTIVE",
                1: "SCANNING_ACTIVE",
                2: "PARKING_SPACE_SELECTION",
                3: "REMOTE_APP_ACTIVE",
                4: "MANEUVER_ACTIVE",
                5: "MANEUVER_FINISHED",
                6: "MANEUVER_INTRRERUPTED",
                7: "UNDO_MANEUVER_ACTIVE",
                8: "START_REMOTE_APP",
                9: "PARK_OUT_INIT",
                10: "PARK_OUT_SIDE",
                11: "MENU_REM",
                12: "MANEUVER_ACTIVE_LONG_MAN",
                13: "REM_SV",
                14: "REM_MAN",
                15: "REM_MAN_ACTIVE",
                16: "GARAGE_PARKING_START",
                17: "PDC_ACTIVe",
                18: "GP_START",
                19: "GP_MANEUVER_ACTIVE",
                20: "DIAG_ERROR",
            }

        class ParkingProcedureCtrlState:
            """Defining the constants regarding ParkingProcedureCtrlState"""

            PPC_INACTIVE = 0
            PPC_BEHAVIOR_INACTIVE = 1
            PPC_SCANNING_INACTIVE = 2
            PPC_SCANNING_IN = 3
            PPC_SCANNING_OUT = 4
            PPC_SCANNING_RM = 5
            PPC_PARKING_INACTIVE = 6
            PPC_PREPARE_PARKING = 7
            PPC_PERFORM_PARKING = 8
            PPC_PARKING_PAUSE = 9
            PPC_PARKING_FAILED = 10
            PPC_OFFER_HANDOVER = 11
            PPC_SUCCESS = 12
            PPC_PARKING_CANCELED = 13
            PPC_IRREVERSIBLE_ERROR = 14
            PPC_REVERSIBLE_ERROR = 15
            PPC_DEMO_OFF = 23

            DICT_CTRL_STATE = {
                0: "PPC_INACTIVE",
                1: "PPC_BEHAVIOR_INACTIVE",
                2: "PPC_SCANNING_INACTIVE",
                3: "PPC_SCANNING_IN",
                4: "PPC_SCANNING_OUT",
                5: "PPC_SCANNING_RM",
                6: "PPC_PARKING_INACTIVE",
                7: "PPC_PREPARE_PARKING",
                8: "PPC_PERFORM_PARKING",
                9: "PPC_PARKING_PAUSE",
                10: "PPC_PARKING_FAILED",
                11: "PPC_OFFER_HANDOVER",
                12: "PPC_SUCCESS",
                13: "PPC_PARKING_CANCELED",
                14: "PPC_IRREVERSIBLE_ERROR",
                15: "PPC_REVERSIBLE_ERROR",
                23: "PPC_DEMO_OFF",
            }

        class APHMIGeneralMessage:
            """Defining the constants regarding APHMIGeneralMessage states"""

            NO_DRIVER_DETECTED_ON_SEAT = 18

    class StaticDynamic:
        """Defining the constants regarding AUP dynamic and static object detection"""

        LIMIT_OF_STAICK_SPEED = 0.2  # [m/s]

    class CarShape:
        """Defining the constants regarding Car shape"""

        CAR_R_AXLE_TO_FRONT = 3.671  # [m]
        CAR_R_AXLE_TO_F_RONT_AXLE = 2.786  # [m]
        CAR_R_AXLE_TO_SIDE = 0.7195  # [m]
        CAR_R_AXLE_TO_HITCH = 1.096  # [m]
        CAR_F_AXLE_TO_FRONT = 0.885  # [m]

    class ManeuveringArea:
        """Defining the constants regarding maneuvering areas"""

        # Perpendicular parking in, backward
        PERP_IN_B_D_1 = 8
        PERP_IN_B_D_2 = 0.3
        PERP_IN_B_D_3 = 1
        PERP_IN_B_D_4 = 5
        PERP_IN_B_D_5 = 0.6
        # Perpendicular parking in, forward
        PERP_IN_F_D_1 = 8
        PERP_IN_F_D_2 = 0.3
        PERP_IN_F_D_3 = 5
        PERP_IN_F_D_5 = 0.6
        # Parallel parking in
        PAR_IN_D_1 = 6
        PAR_IN_D_2 = 0.3
        PAR_IN_D_3 = 3
        PAR_IN_D_4 = 3
        PAR_IN_D_5 = 0.6
        # Parallel parking out
        PAR_OUT_D_1 = 4
        PAR_OUT_D_2 = 3
        PAR_OUT_D_3 = 3
        PAR_OUT_D_4 = 0.6

    class Gear:
        """Defining the constants regarding ego vehicle gear"""

        GEAR_N = 0
        GEAR_P = 9
        GEAR_S = 10
        GEAR_D = 11
        GEAR_R = 13
        GEAR_NOT_DEFINED = 14
        GEAR_ERROR = 15

    class CarMaker:
        """Defining the constants regarding CarMaker"""

        ZERO_SPEED = 0.001  # It comes from SIL minimaneuver commands
        ZORE_STEERING_SPEED = 0.007
        IGNITION_OFF = 0
        IGNITION_ON = 1

        class Door:
            """Defining the constants regarding Door states"""

            ALL_CLOSED = 0
            FRONT_LEFT_OPEN = 1
            FRONT_RIGHT_OPEN = 2
            REAR_LEFT_OPEN = 4
            REAR_RIGHT_OPEN = 8
            ENG_HOOD_OPEN = 16
            TRUNK_OPEN = 32

            DICT_DOORS = {
                0: "ALL_CLOSED",
                1: "FRONT_LEFT_OPEN",
                2: "FRONT_RIGHT_OPEN",
                4: "REAR_LEFT_OPEN",
                8: "REAR_RIGHT_OPEN",
                16: "ENG_HOOD_OPEN",
                32: "TRUNK_OPEN",
            }

        """Defining the constants regarding Trailer state"""

        CONNECTED = 1
        NOT_CONNECTED = 0

    class Seat:
        """Defining the constants regarding seats"""

        DRIVERS_OCCUPIED = 3
        DRIVERS_FREE = 2

    class SeatBelt:
        """Defining the constants regarding seat belts"""

        DRIVERS_CLOSED = 3
        DRIVERS_OPEN = 2

    class Door:
        """Defining the constants regarding doors"""

        OPEN = 1
        CLOSED = 2

    class Brake:
        """Defining the constants regarding parking brake states"""

        PARK_BRAKE_SET = 1

    class Lsca:
        """Defining the constants regarding LSCA values"""

        LSCA_NOT_ACTIVE = 0
        LSCA_ACTIVE = 1
        LSCA_B_FORW_SPEED_MIN_ON_MPS = 0.01
        LSCA_B_FORW_SPEED_MAX_ON_MPS = 2.78
        LSCA_B_BACKW_SPEED_MIN_ON_MPS = 0.01
        LSCA_B_BACKW_SPEED_MAX_ON_MPS = 2.78
        LSCA_B_STANDSTILL_TIME_S = 1  # [sec]

        BRAKE_REQUEST = 1
        REAR_WARNING_ACTIVE = 1

    class ApStates:
        """Defining the constants regarding Ap states"""

        AP_INACTIVE = 0
        AP_SCAN_IN = 1
        AP_SCAN_OUT = 2
        AP_AVG_ACTIVE_IN = 3
        AP_AVG_ACTIVE_OUT = 4
        AP_AVG_PAUSE = 5
        AP_AVG_UNDO = 6
        AP_ACTIVE_HANDOVER_AVAILABLE = 7
        AP_AVG_FINISHED = 8

    class ApThreshold:
        """Defining the constants regarding Ap thresholds"""

        # Limit(s) for time
        AP_G_ABS_TIME_THRESH_S = 0.5
        AP_G_EBD_TIME_THRESH_S = 0.5
        AP_G_ESC_TIME_THRESH_S = 0.5
        AP_G_TCS_TIME_THRESH_S = 0.5
        AP_REACT_TIME_WINDOW = 500000  # [us]
        AP_G_MAX_INTERRUPT_TIME_S = 60
        AP_G_FIRST_STEER_LIMIT_TIME_S = 1
        # Limit(s) for speed
        AP_G_MAX_AVG_V_MPS = 2.778
        AP_G_MAX_AVG_YAW_RATE_RADPS = 1
        AP_V_MAX_STEER_ANG_VEL_RADPS = 0.64
        AP_G_V_SCANNING_THRESH_ON_MPS = 2.77
        AP_G_V_SCANNING_THRESH_OFF_MPS = 11.250
        # Limit(s) for acceleration
        AP_G_MAX_AVG_LONG_ACCEL_MPS2 = 0.5
        AP_G_MAX_DECEL_COMFORTABLE_MPS2 = 0.5
        AP_G_MAX_AVG_LAT_ACCEL_MPS2 = 1
        AP_C_PC_MAX_STEER_ACC_RADPS2 = 4.2
        AP_C_PC_FIRST_STEER_ACC_RADPS2 = 2.2
        # Limit(s) for jerk
        AP_G_MAX_AVG_LON_JERK_COMF_MPS3 = 3
        # Limit(s) for distance
        AP_G_ROLLED_DIST_IN_THRESH_M = 1
        # Limit(s) for %
        AP_G_THROTTLE_THRESH_PERC = 10
        # Limit(s) for brake
        AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR = 15

    class FunctionActivate:
        """Defining the constants regarding function activate"""

        ABS_ACTIVE = 1
        TCS_ACTIVE = 1
        ESC_ACTIVE = 1
        EBD_ACTIVE = 1
        LSCA_ACTIVE = 1

    class DmcState:
        """Defining the constants regarding DMC states"""

        INVALID = 3
        SYSTEM_ERROR = 2
        SYSTEM_NOT_AVAILABLE = 1
        SYSTEM_AVAILABLE__nu = 0

    class HeightClases:
        """Defining the constants regarding heigh classes"""

        UNKNOWN = 0
        WHEEL_TRAVERSABLE = 1
        BODY_TRAVERSABLE = 2
        DOOR_OPENABLE = 3
        HIGH_OBSTACLE = 4
        HANGING_OBSTACLE = 5
        LOWER_BUMPER_HEIGHT = 6
        MAX_NUM_HEIGHT_TYPES = 7

    class HeightLimits:
        """Defining the constants regarding heigh limits"""

        AP_G_MIN_HEIGHT_OBSTACLE_M = 0
        AP_G_MAX_HEIGHT_WHEEL_TRAVER_M = 0.05
        AP_G_MAX_HEIGHT_BODY_TRAVER_M = 0.17

    class ParkingCoreState:
        """Defining the constants regarding parking core states"""

        CORE_INIT = 0
        CORE_SCANNING = 1
        CORE_PARKING = 2
        CORE_PAUSE = 3
        CORE_FINISH = 4
        CORE_ERROR = 5

        dict_p_state = {
            0: "CORE_INIT",
            1: "CORE_SCANNING",
            2: "CORE_PARKING",
            3: "CORE_PAUSE",
            4: "CORE_FINISH",
            5: "CORE_ERROR",
        }

    class PDW:
        """Defining contants related to PDW functionality"""

        # Function activation  speed thresholds
        class Thresholds:
            MIN_SPEED_THRESHOLD_MPS = 0.01  # mps
            MAX_SPEED_THRESHOLD_MPS = 5.56
            MIN_DISTANCE_DETECTION = 0  # meters
            MAX_DISTANCE_DETECTION = 2.55

        # Function states
        class States:
            INIT = 0
            OFF = 1
            ACTIVATED_BY_R_GEAR = 2
            ACTIVATED_BY_BUTTON = 3
            AUTOMATICALLY_ACTIVATED = 4
            FAILURE = 5

        # PDW Button:
        class Button:
            PDW_TAP_ON = 35  # decimal value

        class Gear:
            class Manual:
                INVALID = 15
                NEUTRAL = 0
                REVERSE = 10
                PARK = 11
                FIRST = 1

            class Automatic:
                NEUTRAL = 0
                FORWARD = 1
                REVERSE = 3
                PARK = 2
                INVALID = 7

        # EPB state:
        class EPB_state:
            VALID = 0
            INVALID = 1
            NotAvailable = 3

        class Veh_Motion:
            class Wheel_dir:
                FORWARD = 0
                REVERSE = 1
                INVALID = 3

        class FTTI:
            SYSTEM = 600000

        class DrivingTubeDisplay:
            NONE = 0
            FRONT = 1
            REAR = 2
            BOTH = 3

    class DoorOpen:
        DOORS_CLOSED = 0
        LEFT_FRONT_DOOR_OPEN = 1
        RIGHT_FRONT_DOOR_OPEN = 2
        LEFT_BACK_DOOR_OPEN = 4
        RIGHT_BACK_DOOR_OPEN = 8
        TRUNK_OPEN = 16
        ENGINE_HOOD_OPEN = 32

    class TrailerHitchStatus:
        NOT_FOLDED = 0
        FOLDED = 1
        NOT_INSTALLED = 2


class RCA_LSCA:
    """Defining the constants regarding RCA LSCA"""

    AL_SIG_STATE_INIT = 0
    AL_SIG_STATE_OK = 1
    AL_SIG_STATE_INVALID = 2
    EGOMOTIONPORT_motionState_nu = (0, 1)
    EGOMOTIONPORT_pitch_rad = (-3.14159265359, 3.14159265359)
    EGOMOTIONPORT_roll_rad = (-3.14159265359, 3.14159265359)
    EGOMOTIONPORT_frontWheelAngle_rad = (-0.8, 0.8)
    EGOMOTIONPORT_rearWheelAngle_rad = (-0.8, 0.8)


class RootCauseAnalysis:
    """Defining the constants regarding Root cause analysis tests"""

    NO_SLOT_SELECT = 255
    # APHMIOutScreenRem
    SYSTEM_NOT_ACTIVE = 0
    SCANNING_ACTIVE = 1
    PARKING_SPACE_SELECTION = 2
    REMOTE_APP_ACTIVE = 3
    MANEUVER_ACTIVE = 4
    MANEUVER_FINISHED = 5
    MANEUVER_INTERRUPTED = 6
    UNDO_MANEUVER_ACTIVE = 7
    START_REMOTE_APP = 8
    PARK_OUT_INIT = 9
    PARK_OUT_SIDE = 10
    MENU_REM = 11
    MANEUVER_ACTIVE_LONG_MAN = 12
    REM_SV = 13
    REM_MAN = 14
    REM_MAN_ACTIVE = 15
    KEY_CONTROL_ACTIVE = 16


class ConstantsMPmaneuver:
    """Defining the constants used in Mem Park test"""

    MP_MAX_DIST_TO_SAVEDPOSE_X = 0.1  # unit [m]
    MP_MAX_DIST_TO_SAVEDPOSE_Y = 0.1  # unit [m]
    MP_MAX_DIST_TO_SAVEDPOSE_YAWR = 0.175  # unit [rad]
    MP_END_MANEUVER = 7  # MP Maneuver finished
    MP_CONFIRM_SLOT = 53  # Slot confirmation


class MoCo:
    """File used to store all constants used in MOCO kpis"""

    class Direction:
        """Defining the constants for directions"""

        DIRECTION_REVERSE: int = -1
        DIRECTION_UNDEFINED: int = 0
        DIRECTION_FORWARD: int = 1

    class LoDMCHoldRequestType:
        """Defining the constants for LoDMC hold request types"""

        LODMC_HOLD_REQ_OFF: int = 0
        LODMC_HOLD_REQ_ON: int = 1
        LODMC_HOLD_REQ_RAMP_TO_DRIVER: int = 2

    class MotionState:
        """Defining the constants for motion states"""

        ODO_STANDSTILL: int = 0
        ODO_NO_STANDSTILL: int = 1

    class LoCtrlRequestType:
        """Defining the constants for LoCtrl request types"""

        LOCTRL_OFF: int = 0
        LOCTRL_BY_TRAJECTORY: int = 1
        LOCTRL_BY_DISTANCE: int = 2
        LOCTRL_BY_VELOCITY: int = 3
        LOCTRL_BY_DISTANCE_VELOCITY: int = 4
        LOCTRL_BY_ACCELERATION: int = 5
        LOCTRL_VELOCITY_LIMITATION: int = 6
        LOCTRL_EMERGENCY_STOP: int = 7

    class LaCtrlRequestType:
        """Defining the constants for LaCtrl request types"""

        LACTRL_OFF: int = 0
        LACTRL_BY_TRAJECTORY: int = 1
        LACTRL_BY_ANGLE_FRONT: int = 2
        LACTRL_BY_ANGLE_REAR: int = 3
        LACTRL_BY_ANGLE_FRONT_REAR: int = 4
        LACTRL_BY_TORQUE: int = 5
        LACTRL_BY_CURVATURE: int = 6
        LACTRL_COMF_ANGLE_ADJUSTMENT: int = 7
        MAX_NUM_LA_REQUEST_TYPES: int = 8

    class RequestedDrivingDir:
        """Defining the constants for requested driving directions"""

        NOT_RELEVANT: int = 0
        FORWARD: int = 1
        BACKWARD: int = 2

    class Parameter:
        """
        :param FIRST_STEER_ACCUR_RAD: The accuracy threshold for considering angle as 'close'
        :param MIN_STEER_VEL_RADPS: The minimum threshold for the steer angle velocity to be considered close to static.
        :param AP_M_MAX_NUM_TRAJ_CTRL_POINTS: The number of trajectory control points in the planned path.
        :param AP_C_PC_FAIL_MAX_LAT_ERROR_M:  Maximum allowed absolute deviation from calculated trajectory
        :param AP_C_PC_FAIL_MAX_YAW_ERROR_RAD: Maximum allowed absolute yaw angle (orientation) error from calculated trajectory.
        :param AP_C_PC_FIRST_STEER_VEL_RADPS: Maximum steer angle velocity for ramping steer angle to desired value for
            first steering (at wheels).
        :param AP_C_PC_MIN_STEER_VEL_RADPS: Minimum steer angle velocity for ramping steer angle to desired value for first
            steering (at wheels)
        :param AP_C_PC_FIRST_STEER_ACC_RADPS2: Maximum steer angle acceleration for ramping steer angle to desired value
            for first steering (at wheels)

        :param AP_C_KPI_PASS_MAX_LAT_ERROR_M: Maximum allowed absolute lateral deviation from calculated trajectory to pass the KPI
        :param AP_C_KPI_FAIL_MAX_LAT_ERROR_M: Maximum allowed absolute lateral deviation from calculated trajectory to not fail/accept the KPI
        :param AP_C_KPI_SUCCESS_RATE_MAX_LAT_ERROR_PASSED_PERCENT: Success rate for absolute lateral error KPI for passed threshold
        :param AP_C_KPI_SUCCESS_RATE_MAX_LAT_ERROR_ACCEPT_PERCENT: Success rate for absolute lateral error KPI for acceptable threshold

        """

        FIRST_STEER_ACCUR_RAD: float = 0.1746  # radians
        MIN_STEER_VEL_RADPS: float = 0.04267  # rad/s

        LOCTRL_EMERGENCY_STOP: int = 7
        LODMC_HOLD_REQ_ON = 1
        AP_M_MAX_NUM_TRAJ_CTRL_POINTS: int = 20
        AP_C_PC_FAIL_MAX_LAT_ERROR_M: float = 0.1  # m
        AP_C_PC_FAIL_MAX_YAW_ERROR_RAD: float = 0.067  # rad
        AP_C_PC_FIRST_STEER_VEL_RADPS: float = 0.66  # rad/s
        AP_C_PC_MIN_STEER_VEL_RADPS: float = 0.04267  # rad/s
        AP_C_PC_FIRST_STEER_ACC_RADPS2: float = 2.20  # rad/s^2
        AP_V_STEER_RATIO_NU = 14.7  # No Unit
        AP_C_MANEUV_FINISHED_TIME_S: float = 0.1  # s
        AP_C_MANEUV_FINISHED_LIMIT_M: float = 0.15  # m
        AP_C_ACTIVE_CONTROL_MIN_TIME_S: float = 2  # s
        AP_C_MANEUV_FINISHED_HYST_M: float = 0.04  # m
        AP_C_COMP_TIRE_DEF_STEER_WHEEL_ANGLE_DEG: float = 5.0  # deg
        TRUE: bool = 1
        FALSE: bool = 0
        AL_SIG_STATE_OK: int = 1

        AP_C_KPI_PASS_MAX_LAT_ERROR_M: float = 0.03  # m
        AP_C_KPI_FAIL_MAX_LAT_ERROR_M: float = 0.05  # m
        AP_C_KPI_SUCCESS_RATE_MAX_LAT_ERROR_PASSED_PERCENT = 90  # percentage
        AP_C_KPI_SUCCESS_RATE_MAX_LAT_ERROR_ACCEPT_PERCENT = 95  # percentage

        AP_C_KPI_PASS_MAX_YAW_ERROR_DEG: float = 1  # deg
        AP_C_KPI_FAIL_MAX_YAW_ERROR_DEG: float = 2  # deg
        AP_C_KPI_SUCCESS_RATE_MAX_YAW_ERROR_PASSED_PERCENT = 90  # percentage
        AP_C_KPI_SUCCESS_RATE_MAX_YAW_ERROR_ACCEPT_PERCENT = 95  # percentage

        AP_C_KPI_SUCCESS_RATE_STANDSTILL_TIME_PERCENT = 95  # percentage
        AP_C_KPI_STANDSTILL_TIME_S: float = 3.0  # s

        AP_C_KPI_SUCCESS_RATE_TIRE_DEF_PERCENT = 95  # percentage

        AP_V_MAX_STEER_ANG_RAD = 0.595  # rad
        AP_C_PC_MAX_STEER_ACC_RADPS2 = 4.20  # rad/s^2
        AP_C_STEER_SATURATE_RATE_RADPS = 0.32  # rad/s
        AP_C_STEER_SATURATE_THRESH_RAD = 0.036  # rad
        AP_V_MAX_STEER_ANG_VEL_RADPS = 0.64  # rad/s


class ParkInEndSuccessRate:
    """Defining the constants used in park in success rate kpi"""

    class Par:
        """Defining the constants for parallel"""

        NB_STROKES = 4  # strokes
        TIME = 65  # seconds
        LAT_ERROR = (-0.1, 0.1)  # m
        LONG_ERROR = (-0.1, 0.1)  # m
        ORIENTATION_ERROR = (-1, 1)  # rad

    class PerpAng:
        """Defining the constants for perpendicular and angular"""

        TIME = 65  # seconds
        NB_STROKES = 4  # strokes
        LAT_ERROR = (-0.05, 0.05)  # m
        LONG_ERROR = (-0.1, 0.1)  # m
        ORIENTATION_ERROR = (-1, 1)  # rad


class SlotOffer:
    """Class containing predefined values related to slot offer KPI"""

    class CarCoordinates:
        """
        Class containing predefined coordinates for a car.

        All values are in meters.
        """

        REAR_RIGHT = [-1.1, -0.92]
        RIGHT_MIRROR_REAR_LEFT_CORNER = [2.05, -0.92]
        RIGHT_MIRROR_REAR_RIGHT_CORNER = [2.05, -1.05]
        RIGHT_MIRROR_FRONT_RIGHT_CORNER = [2.15, -1.05]
        RIGHT_MIRROR_FRONT_LEFT_CORNER = [2.15, -0.92]
        FRONT_RIGHT = [3.67, -0.92]
        FRONT_LEFT = [3.67, 0.92]
        LEFT_MIRROR_FRONT_RIGHT_CORNER = [2.15, 0.92]
        LEFT_MIRROR_FRONT_LEFT_CORNER = [2.15, 1.05]
        LEFT_MIRROR_REAR_LEFT_CORNER = [2.05, 1.05]
        LEFT_MIRROR_REAR_RIGHT_CORNER = [2.05, 0.92]
        REAR_LEFT = [-1.1, 0.92]

    class Thresholds:
        """Class containing predefined threshold values."""

        THRESHOLD_OVERLAP = 80  # %

    class AutoScale:
        """Class containing predefined auto-scaling percentage values."""

        PERCENTAGE_X_GT = 0.8  # percentage/100
        PERCENTAGE_Y_GT = 0.9  # percentage/100
        PERCENTAGE_X_SLOT = 0.6  # percentage/100
        PERCENTAGE_Y_SLOT = 0.4  # percentage/100


class ParkingUseCases:
    """Defining the constants regarding the usecase id in AUP kpi"""

    parking_usecase_id = {
        "AP_UC_001_01": "Parallel Parking Between Two Aligned Vehicles [Long Parking Slot]",
        "AP_UC_001_02": "Parallel Parking Between Two Aligned Vehicles [Short Parking Slot]",
        "AP_UC_002_001": "Parallel Parking Behind One Vehicle [Parking behind one Vehicle and next to a Curbstone or Wall]",
        "AP_UC_002_02": "Parallel Parking Behind One Vehicle [Parking between one Vehicle a small Obstacle]",
        "AP_UC_011": "Parallel Parking Between Two Misaligned Vehicles",
        "AP_UC_002_03": "Parallel Parking Behind One Vehicle [Parking in front of one Vehicle]",
        "AP_UC_003": "Parallel Parking Next to Curbstones",
        "AP_UC_004": "Parallel Parking Into Rectangular Curb Parking Bay",
        "AP_UC_005_01": "Parallel Parking Half on a Sidewalk [Enclosed by vehicles]",
        "AP_UC_005_02": "Parallel Parking Half on a Sidewalk [Indicated by parking slot markings]",
        "AP_UC_006_01": "Parallel Parking on Top of a Sidewalk [Enclosed by vehicles]",
        "AP_UC_006_02": "Parallel Parking on Top of a Sidewalk [Indicated by parking slot markings]",
        "AP_UC_007_01": "Parallel Parking Slots Enclosed by Parking Slot Markings [Parking based on Slot Markings only]",
        "AP_UC_007_02": "Parallel Parking Slots Enclosed by Parking Slot Markings [Parking Slot with Slot Markings and Curbs or Wall]",
        "AP_UC_008_01": "Parallel Parking Slots Enclosed by Parking Slot Markings and Obstacles [Parking Slot Enclosed by Parking Slot Markings and Obstacles]",
        "AP_UC_008_02": "Parallel Parking Slots Enclosed by Parking Slot Markings and Obstacles [Parking Slot with Slot Markings and Misaligned Vehicle at First Side Edge]",
        "AP_UC_008_03": "Parallel Parking Slots Enclosed by Parking Slot Markings and Obstacles [Parking Slot with Slot Markings and Misaligned Vehicle at Second Side Edge]",
        "AP_UC_008_04": "Parallel Parking Slots Enclosed by Parking Slot Markings and Obstacles [Parking Slot with only (dotted) longitudinal line and two Vehicles (no vertical lines)]",
        # Misaligned means:
        # Angle between vertical slot markings and target vehicle's yaw angle is NOT 90°
        # Target vehicle overlapping the slot marking (Nissan use case variant)
        "AP_UC_009": "Parallel Parking With Obstacles on Opposite Street Side",
        "AP_UC_010_01": "Parallel Parking With a Shifted Start Orientation of the Ego Vehicle [Orientation Shift after Passing the Parking Slot]",
        "AP_UC_010_02": "Parallel Parking With a Shifted Start Orientation of the Ego Vehicle [Orientation Shift while Passing the Parking Slot]",
        "AP_UC_012": "Parallel Parking in Convex Curves",
        "AP_UC_013": "Parallel Parking in Concave Curves",
        "AP_UC_014": "Parallel Parking with Manual Start",
        "AP_UC_015": "Parallel Parking with Immersion",
        "AP_UC_016_01": "Parallel Parking With Thin Obstacle and Vehicle as Parking Slot Limiters [Forward parking]",
        "AP_UC_016_02": "Parallel Parking With Thin Obstacle and Vehicle as Parking Slot Limiters [Backward Parking]",
        "AP_UC_017": "Parallel Parking Into Slanted Curb Parking Bay",
        # "Proposal AP_UC_xxx (003?)": "Parallel Parking Next to Curbstones or Walls",
        "AP_UC_018": "Backwards Perpendicular Parking Between Two Vehicles",
        "AP_UC_019": "Forwards Perpendicular Parking Between Two Vehicles",
        "AP_UC_020_01": "Backwards Perpendicular Parking With One Lateral Parking Slot Limiter ",
        "AP_UC_020_02": "Forwards Perpendicular Parking With One Lateral Parking Slot Limiter",
        "AP_UC_021_01": "Perpendicular Parking With a Curbstone or a Wall at the Curb Side Edge [Standard (No overhang)]",
        "AP_UC_021_02": "Perpendicular Parking With a Curbstone or a Wall at the Curb Side Edge [with Overhang]",
        "AP_UC_022_01": "Perpendicular Parking Next to a Curb or Wall [Parking Next to a Wall on One Lateral Edge]",
        "AP_UC_022_02": "Perpendicular Parking Next to a Curb or Wall [Parking Next to a Curbstone on One Lateral Edge]",
        "AP_UC_023_01": "Perpendicular Parking on Top of a Sidewalk [Enclosed by Vehicles]",
        "AP_UC_059_01": "Perpendicular Parking Half on a Sidewalk enclosed by Vehicles",
        "AP_UC_059_02": "Perpendicular Parking Half on a Sidewalk enclosed by Parking Slot Markings",
        "AP_UC_024_01": "Perpendicular Parking in Slots Enclosed by Parallel Parking Slot Markings Only",
        "AP_UC_024_02": "Perpendicular Parking Slots with Not Parallel Parking Slot Markings",
        "AP_UC_025": "Backwards Perpendicular Parking in Situations With Obstacles on the Opposite Side",
        "AP_UC_026": "Forwards Perpendicular Parking in Situations With Obstacles on the Opposite Side",
        "AP_UC_027_01": "Perpendicular Parking With Parking Slot Markings and Vehicles Within Lines",
        "AP_UC_027_02": "Perpendicular Parking With Parking Slot Markings and Vehicles out of Lines",
        "AP_UC_028_01": "Perpendicular Parking With a Shifted Start Orientation of the Ego Vehicle [Orientation Shift after Passing the Parking Slot]",
        "AP_UC_028_02": "Perpendicular Parking With a Shifted Start Orientation of the Ego Vehicle [Orientation Shift while Passing the Parking Slot]",
        "AP_UC_029_01": "Perpendicular Parking Between Two Misaligned Vehicles [No Parking Slot Limiter on the Curb Side Edge]",
        "AP_UC_029_02": "Perpendicular Parking Between Two Misaligned Vehicles [With Parking Slot Limiter on the Curb Side Edge]",
        "AP_UC_031_01 ": "Perpendicular Parking With Thin Obstacles as Parking Slot Limiters [Parking slot With Thin Obstacle on One Lateral Side]",
        "AP_UC_031_02": "Perpendicular Parking With Thin Obstacles as Parking Slot Limiters [Parking slot With Thin Obstacle Near the Door]",
        "AP_UC_031_03": "Perpendicular Parking With Thin Obstacles as Parking Slot Limiters [Parking slot With Thin Obstacle Inside]",
        "AP_UC_032": "Perpendicular Parking With Suddenly Appearing Obstacle",
        "AP_UC_033": "Perpendicular Parking in Convex Curves",
        "AP_UC_034": "Perpendicular Parking in Concave Curves",
        "AP_UC_035": "Perpendicular Parking with Manual Start",
        "AP_UC_036": "Perpendicular Parking with Immersion",
        "AP_UC_037": "Perpendicular Parking on Wheel Stoppers",
        "AP_UC_068": "Perpendicular Parking with traversable objects inside the parking slot",
        # "Proposal AP_UC_xxx (021?)": "Perpendicular Parking With a Curbstone or a Wall at the End (with and without overhang)",
        "AP_UC_069": "Perpendicular Parking on Wheel Lockers",
        "AP_UC_038": "Forwards Angular Parking Between Markers",
        "AP_UC_070": "Backwards Angular Parking Between Markers",
        "AP_UC_039_02": "Forwards Angular Parking Between Vehicles and Markers [Parking Slot with Slot Markings and one Vehicle]",  #######
        "AP_UC_71_02": "Backwards Angular Parking Between Vehicles and Markers [Parking Slot with Slot Markings and one Vehicle]",  ############
        "AP_UC_040_01": "Angular Parking Between Vehicles [Up- /Down- Hill Parallel to the Course of the Road]",  ####################
        "AP_UC_041": "Angular Parking Between Obstacles and Markers",
        "AP_UC_044": "Angular Parking Between Curbs",
        "AP_UC_060": "Angular Parking Between Two Misaligned Vehicles",
        "AP_UC_061": "Angular Parking Based on Wheel Stoppers",
        "AP_UC_100_01": "Parallel Parking Out - large slot or no vehicle in front (Driver-in-Vehicle and Remote)",  ######
        "AP_UC_100_02": "Parallel Parking Out - Only slot line markings (no target vehicle)",
        "AP_UC_101": "Perpendicular Parking Out Forward (Driver-in-Vehicle)",
        "AP_UC_102": "Perpendicular Parking Out Backward (Driver-in-Vehicle",
        "AP_UC_103": "Perpendicular Parking Out Forward (Remote)",
        "AP_UC_104": "Perpendicular Parking Out Backward (Remote)",
        "AP_UC_105": "Angular Parking Out Forward (Driver-in-Vehicle and Remote)",
        "AP_UC_106": "Angular Parking Out Backward (Driver-in-Vehicle and Remote)",
        "AP_UC_045": "Straight Forward and Backward Until Obstacle Reached",
        "AP_UC_046": "Alignment to Obstacles on Forward and Backward Driving",
        "AP_UC_047": "Parking with Interfering Pedestrians",
        "AP_UC_048": "Parking with Interfering Dynamic Objects (without Pedestrians)",
        "AP_UC_049": "Driver Intended Speed Increase/Reduction During Maneuver",
        "AP_UC_050": "Driver Intended Direction Change During Maneuver",
        "AP_UC_051": "Incorporate in Maneuver Appearing Static Obstacles (Dynamic Replanning)",
        "AP_UC_052": "Incorporate Static Obstacle From Previous Ignition Cycle",
        "AP_UC_053": "Park-out After Manual Park-in",
        "AP_UC_054_05": "Parking on Slopes [Up- /Down- Hill Parallel to the Course of the Road]",
        "AP_UC_054_06": "Parking on Slopes [Up- /Down- Hill Perpendicular to the Course of the Road]",
        "AP_UC_055": "Undo Maneuver",
        "AP_UC_056": "Handover to Driver on Park-out During Maneuver",
        "AP_UC_057": "Rear-axle Steering Support for Increased Performance",
        "AP_UC_058": "Driver Cancel Always Possible",
    }
