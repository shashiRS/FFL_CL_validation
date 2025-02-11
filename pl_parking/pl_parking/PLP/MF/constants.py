"""File used to store all constants used in kpis from MF directory"""

from collections import Counter
from enum import IntEnum

import numpy as np
import plotly.graph_objects as go


class GetVariableName:
    """Class used to get the name of the variable"""

    # Get the name of the variable and its value
    @classmethod
    def get_variable_name(cls, value):
        """Get the name of the variable and its value"""
        for name, val in cls.__dict__.items():
            if val == value:
                return f"{name} ({value})"
        return value


class DrawCarClassMethods:
    """Class to be inherited by the class that will draw the car"""

    _translated_coords = {}

    @classmethod
    def translate_and_rotate(cls, new_x, new_y, yaw):
        """
        Translates and rotates all coordinates based on the ego position and yaw angle.

        Parameters:
        - new_x: The new X origin coordinate
        - new_y: The new Y origin coordinate
        - yaw: Rotation angle in radians
        """
        # Create the rotation matrix
        rotation_matrix = np.array([[np.cos(yaw), -np.sin(yaw)], [np.sin(yaw), np.cos(yaw)]])

        # Apply translation and rotation to each point
        for attr, value in cls.__dict__.items():
            if isinstance(value, list):  # Only process the coordinates

                point = np.array(value)

                # First, apply the rotation to the point relative to origin (0,0)
                rotated_point = rotation_matrix @ point

                # Then, translate the rotated point to the new origin
                final_point = rotated_point + np.array([new_x, new_y])

                # Store the transformed coordinates
                cls._translated_coords[attr] = final_point.tolist()

    @classmethod
    def get_translated_coord(cls, point_name):
        """
        Returns the translated coordinates for a specific point.

        Parameters:
        - point_name: The name of the point (as string).

        Returns:
        - Translated coordinates as a list [x, y].
        """
        return cls._translated_coords.get(point_name)


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


class ConstantsAUPBodyDistFinalPose:
    """Defining the constants for minimal body distance in automated parking final pose"""

    AP_G_DIST_MIN_SSIDE_HIGH_OBST_M = 0.1
    AP_G_DIST_MIN_LSIDE_HIGH_OBST_PERP_M = 0.31
    AP_G_DIST_MIN_LSIDE_HIGH_OBST_PAR_M = 0.05
    AP_G_DIST_MIN_LSIDE_TRAV_PAR_M = 0.2  # [m]
    AP_G_DIST_MIN_LSIDE_TRAV_PAR_M = 0.2  # [m]


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
    US_IN_MS = 1000
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
    WHEEL_DIAMETER = 0.668  # [m]


class BodyTraversibleObjectTestConstants:
    """Default CM body traversible object dimensions"""

    OBSTACLE_WIDTH = 0.2  # [m]
    OBSTACLE_LENGTH = 4.28  # [m]
    OBSTACLE_HEIGHT = 0.15  # [m]


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

    class GpStates:
        """Defining the constants regarding Gp states"""

        GP_AVG_FINISHED = 7
        GP_INACTIVE = 0

    class RmStates:
        """Defining the constants regarding RM states"""

        RM_AVG_FINISHED = 4
        RM_INACTIVE = 0

    class RaStates:
        """Defining the constants regarding RA states"""

        RA_INACTIVE = 0
        RA_AVG_FINISHED = 4

    class MpStates:
        """Defining the constants regarding MP states"""

        MP_RECALL_FINISHED = 9
        MP_TRAIN_FINISHED = 5
        MP_INACTIVE = 0

    class ReachableStatus:
        """Defining the constants reachableStatus"""

        TP_NOT_VALID = 0
        TP_NOT_REACHABLE = 1
        TP_FULLY_REACHABLE = 2
        TP_SAFE_ZONE_REACHABLE = 3
        TP_MANUAL_FWD_REACHABLE = 4
        TP_MANUAL_BWD_REACHABLE = 5
        MAX_NUM_POSE_REACHABLE_STATUS = 6

    class ScenarioType:
        """Defining the constants for parking box scenario types"""

        PARALLEL_PARKING = 0
        PERPENDICULAR_PARKING = 1
        ANGLED_PARKING_OPENING_TOWARDS_BACK = 2
        ANGLED_PARKING_OPENING_TOWARDS_FRONT = 3
        GARAGE_PARKING = 4
        DIRECT_PARKING = 5
        EXTERNAL_TAPOS_PARALLEL = 6
        EXTERNAL_TAPOS_PERPENDICULAR = 7
        EXTERNAL_TAPOS_PARALLEL_OUT = 8
        EXTERNAL_TAPOS_PERPENDICULAR_OUT = 9
        MAX_NUM_PARKING_SCENARIO_TYPES = 10

    class PlannedTrajType:
        """Defining the constants trajType"""

        PERP_PARK_IN_TRAJ = 0
        PAR_PARK_IN_TRAJ = 1
        PERP_PARK_OUT_TRAJ = 2
        PAR_PARK_OUT_TRAJ = 3
        REMOTE_MAN_TRAJ = 4
        UNDO_TRAJ = 5
        MAX_NUM_PLANNED_TRAJ_TYPES = 6

    class PoseType:
        """Defining the constants pose types"""

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

    class Parameter:
        PARALLEL_PARK_MAX_TARGET_POSE = 1
        PERP_PARK_MAX_TARGET_POSE = 2
        PERP_PARK_FWD_MAX_TARGET_POSE = 1
        PERP_PARK_BWD_MAX_TARGET_POSE = 1
        ANGLED_PARK_MAX_TARGET_POSE = 1
        AP_P_MAX_NUM_POSES_IN_PATH_NU = 1000
        AP_P_MAX_NUM_SEGMENTS_IN_PATH_NU = 25
        AP_G_MAX_AVG_LAT_ACCEL_MPS2 = 1.0
        AP_G_MAX_AVG_V_MPS = 2.778
        AP_V_MIN_TURN_RADIUS_M = 4.1
        AP_P_MIN_RADIUS_ADD_CLOTHOID_M = 0.2

    ACT_NB_STROKES_GREATER_MAX_NB_STROKES_FALSE = 0
    NB_CRV_STEPS_FALSE = 0
    FAIL_REASON = 0
    PATH_FOUND = 1
    PATH_NOT_FOUND = 0
    TRAJ_VALID = 1
    TRAJ_INVALID = 0
    AP_INACTIVE = 0
    AP_SCAN_IN = 1
    AP_SCAN_OUT = 2
    AP_AVG_ACTIVE_IN = 3
    AP_AVG_ACTIVE_OUT = 4
    AP_AVG_PAUSE = 5
    AP_AVG_UNDO = 6
    AP_ACTIVE_HANDOVER_AVAILABLE = 7
    AP_AVG_FINISHED = 8


class ConstantsSI:
    """Defining the constants used in trajpla test"""

    AP_V_WIDTH_M = 1.832  # unit [m]
    AP_G_PERP_SLOT_MAX_OFFSET_W_PARK_M = 1.50  # unit [m] default value
    # AP_G_PERP_SLOT_MAX_OFFSET_W_PARK_M = 5.00 # unit [m] Max value
    AP_G_PERP_SLOT_MAX_OFFSET_L_SCAN_M = 1.8  # unit [m]
    AP_G_PERP_SLOT_MAX_OFFSET_L_PARK_M = 1.8  # unit [m]
    AP_G_PERP_SLOT_MIN_OFFSET_W_M = 0.60  # unit [m]
    AP_G_PERP_SLOT_MAX_OFFSET_W_SCAN_M = 1.50  # unit [m]
    AP_G_PERP_SLOT_MIN_OFFSET_L_M = 0.50  # unit [m]
    AP_V_LENGTH_M = 4.767  # unit [m]
    AP_G_PAR_SLOT_MIN_OFFSET_L_M = 0.80  # unit [m]
    AP_G_PAR_SLOT_MAX_OFFSET_L_PARK_M = 3.00  # unit [m]
    AP_SI_MAX_DIST_OPTIM_M = 10.0  # unit [m]
    AP_G_SCAN_OFFER_SLOTS_LO_DIST_M = 10.00  # unit [m]
    AP_G_MAX_HEIGHT_HANG_OBST_M = 1.6  # unit [m]
    # AP_G_PAR_SLOT_MAX_OFFSET_L_PARK_M = 3.0 # unit [m]
    AP_G_PAR_SLOT_MAX_OFFSET_L_SCAN_M = 3.00  # unit [m]
    AP_SI_NOMINAL_SLOT_LENGTH_DELTA_PARA_M = 1.5  # unit [m]
    AP_SI_NOMINAL_SLOT_WIDTH_DELTA_PERP_M = 1.0  # unit [m]
    AP_G_PER_MAX_ROAD_OVERHANG_M = 1.00  # unit [m]
    AP_G_PAR_MAX_ROAD_OVERHANG_M = 0.50  # unit [m]
    AP_SI_PAR_SLOT_MIN_OFFSET_DEPTH_SCAN_M = 0.11
    AP_SI_PAR_SLOT_MIN_OFFSET_DEPTH_PARK_M = 0.11
    ####
    """
    AP_G_PAR_SLOT_MAX_OFFSET_W_PARK_M in the requirements is currently set to 0.8, in our config it is set to 1.4,
    also we always add 0.5m of Roadside extension, so the current limit implemented would be vehicle width + 1.4 + 0.5
    """
    AP_G_PAR_SLOT_MAX_OFFSET_W_SCAN_M = 1.4  # unit [m] as communicated by dev team
    AP_G_PAR_SLOT_MAX_OFFSET_W_PARK_M = 1.4  # unit [m] as communicated by dev team
    ROADSIDE_EXTENSION = 0.5  # unit [m] as communicated by dev team
    AP_SI_NONPAR_SLOT_MIN_OFFSET_DEPTH_SCAN_M = 0.21
    AP_SI_NONPAR_SLOT_MIN_OFFSET_DEPTH_PARK_M = 0.21
    # MAX_DEPTH_PARALLEL_PARKING_BOX = AP_V_WIDTH_M + AP_G_PAR_SLOT_MAX_OFFSET_W_PARK_M + ROADSIDE_EXTENSION
    MAX_DEPTH_PARALLEL_PARKING_BOX_PARK = AP_V_WIDTH_M + AP_G_PAR_SLOT_MAX_OFFSET_W_PARK_M + ROADSIDE_EXTENSION
    MAX_DEPTH_PARALLEL_PARKING_BOX_SCAN = AP_V_WIDTH_M + AP_G_PAR_SLOT_MAX_OFFSET_W_SCAN_M + ROADSIDE_EXTENSION
    ####

    MAX_PERP_WDTH_PARK_IN = AP_V_WIDTH_M + AP_G_PERP_SLOT_MAX_OFFSET_W_PARK_M
    MAX_PERP_WDTH_SCAN_IN = AP_V_WIDTH_M + AP_G_PERP_SLOT_MAX_OFFSET_W_SCAN_M
    MIN_WDTH_PERP = AP_V_WIDTH_M + AP_G_PERP_SLOT_MIN_OFFSET_W_M

    MIN_LEN_PARALLEL = AP_V_LENGTH_M + AP_G_PAR_SLOT_MIN_OFFSET_L_M
    MAX_LEN_PARALLEL_SCAN_IN = AP_V_LENGTH_M + AP_G_PAR_SLOT_MAX_OFFSET_L_SCAN_M
    MAX_LEN_PARALLEL_PARK_IN = AP_V_LENGTH_M + AP_G_PAR_SLOT_MAX_OFFSET_L_PARK_M

    MIN_DEPTH_PARALLEL_SCAN_M = AP_V_WIDTH_M + AP_SI_PAR_SLOT_MIN_OFFSET_DEPTH_SCAN_M
    MIN_DEPT_PARALLEL_PARK_M = AP_V_WIDTH_M + AP_SI_PAR_SLOT_MIN_OFFSET_DEPTH_PARK_M

    MAX_DEPTH_PARALLEL_SCAN_M = AP_V_WIDTH_M + AP_G_PAR_SLOT_MAX_OFFSET_W_SCAN_M
    MAX_DEPTH_PARALLEL_PARK_M = AP_V_WIDTH_M + AP_G_PAR_SLOT_MAX_OFFSET_W_PARK_M

    MIN_DEPTH_PER_SCAN_M = AP_V_LENGTH_M + AP_SI_NONPAR_SLOT_MIN_OFFSET_DEPTH_SCAN_M
    MIN_DEPTH_PER_PARK_M = AP_V_LENGTH_M + AP_SI_NONPAR_SLOT_MIN_OFFSET_DEPTH_PARK_M

    DEGREE_OF_TOLERENCE_FOR_ORIENTATION = 10  # unit [degree]

    AP_G_PAR_MAX_ROAD_OVERHANG_M = 0.50  # unit [m]
    AP_G_PER_MAX_ROAD_OVERHANG_M = 1.00  # unit [m]

    AP_SI_PAR_SLOT_MIN_OFFSET_DEPTH_SCAN_M = 0.11  # unit [m]
    AP_SI_PAR_SLOT_MIN_OFFSET_DEPTH_PARK_M = 0.11  # unit [m]

    AP_SI_NONPAR_SLOT_MIN_OFFSET_DEPTH_SCAN_M = 0.21  # unit [m]
    AP_SI_NONPAR_SLOT_MIN_OFFSET_DEPTH_PARK_M = 0.21  # unit [m]

    AP_V_OVERHANG_REAR_M = 1.096  # unit [m]
    AP_G_PAR_MAX_ORI_ANGLE_RAD = 0.15  # unit [radian]
    VERTICES_PB_VEHICLE = [1.0, 0.0]  # unit [m]
    AP_SI_KPI_SLOT_CORNER_DEVIATION_M = 3  # unit [m] NEEDS TO BE DISCUSSED & UPDATED
    AP_G_PERP_MAX_ORI_ANGLE_RAD = 0.15  # unit [radian]
    AP_SI_CNN_ROAD_ALIGN_LIMIT_TO_ROAD_PARA_M = 0.50  # unit [m]
    ANGLE_DIFFERENCE_ALLOWED = 10  # unit [in degree]

    LIST_ZERO_DEGREE = [0.00, 90.00, 180.00, 360.00]
    AP_SI_CNN_ROAD_ALIGN_LIMIT_TO_CURB_PARA_M = 0  # unit [m]

    AP_SI_MAX_ROT_ANGLE_PERP_RAD = 2.356  # unit [rad]

    AP_G_V_SCANNING_THRESH_OFF_MPS = 11.250  # unit [m/s]

    vehicle_polygon = [
        (3.254, 0.916),
        (-0.356, 0.916),
        (-0.846, 0.77),
        (-0.976, 0.685),
        (-1.046, 0.5),
        (-1.096, 0.0),
        (-1.046, -0.5),
        (-0.976, -0.685),
        (-0.846, -0.77),
        (-0.356, -0.916),
        (3.254, -0.916),
        (3.404, -0.85),
        (3.671, -0.5),
        (3.671, 0.0),
        (3.671, 0.5),
        (3.404, 0.85),
    ]

    AP_G_SCAN_MAX_DIST_SLOT_M = 7.00  # unit [m]
    CAR_MIRROR_BACK_OFFSET = 0.5  # unit [m]



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
    REACHED = 1
    TOLERANCE_LONG_DIFF_OTP = 0.1  # m
    TOLERANCE_LAT_DIFF_OTP = 0.1  # m
    TOLERANCE_YAW_DIFF_OTP = 0.02  # rad

    class TargetSide:
        """Defining constants for targetSide"""

        TS_RIGHT_SIDE = 0
        TS_LEFT_SIDE = 1


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

    GEAR_N = 0
    GEAR_P = 9
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


class ParkCoreStatus(GetVariableName):
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


class LscaConstants(GetVariableName):
    """Defining the constants used in LSCA KPI"""

    DEACTIVATE = 0
    ACTIVATE = 1
    FALSE_POSITIVE = 255

    LSCA_B_BACKW_SPEED_MIN_ON_MPS = 0  # m/s
    LSCA_B_FORW_SPEED_MIN_ON_MPS = 0  # m/s
    LSCA_B_BACKW_SPEED_MAX_ON_MPS = 2.78  # m/s
    LSCA_B_FORW_SPEED_MAX_ON_MPS = 2.78  # m/s

    P_CM_STANDSTILL = 0.1  # m/s

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

        class RemFingerPosition:
            """Defining the constants regarding HMI finger position on remote device"""

            DM_FINGER_POS_X = 1001
            DM_FINGER_POS_Y = 2001

        class BTDevConnected:
            """Defining the constants regarding"""

            FALSE = 0
            TRUE = 1

        class BTDevPaired:
            """Defining the constants regarding BTDevPaired"""

            FALSE = 0
            TRUE = 1

        class LoDMCHoldReq:
            """Defining the constants regarding LoDMCHoldReq"""

            FALSE = 0
            TRUE = 1

        class GeneralScreenReactionTime:
            """Defining the reaction time constants for general screen."""

            VISUAL_INDICATOR_REACTION_TIME = 100000  # [us]

        class APHMIGeneralMessageRemote:
            """Defining the constants regarding APHMIGeneralMessageRemote"""

            PARKING_OUT_FINISHED_FALLBACK = 39
            PARKING_IN_FINISHED_FALLBACK = 38
            KEY_NOT_ALIVE = 37
            KEY_NOT_IN_RANGE = 36
            SLOW_DOWN = 35
            WAIT = 34
            LOW_ENERGY = 33
            UNDO_FINISHED = 32
            GARAGE_NOT_OPEN = 31
            PARKING_CANCELLED_STEER = 30
            PARKING_CANCELLED_THROTTLE = 29
            NO_REMOTE_DEVICE_CONNECTED = 28
            NO_REMOTE_DEVICE_PAIRED = 27
            SELECT_PARKING_VARIANT = 26
            SHIFT_TO_N = 25
            SHIFT_TO_P = 24
            NO_MESSAGE = 0
            VERY_CLOSE_TO_OBJECTS = 1
            START_PARKING_IN = 2
            PARKING_IN_FINISHED = 3
            PARKING_CANCELLED = 4
            PARKING_FAILED = 5
            SHIFT_TO_R = 6
            SHIFT_TO_D = 7
            SHIFT_TO_1 = 8
            RELEASE_BRAKE = 9
            START_PARKING_OUT = 10
            PARKING_OUT_FINISHED = 11
            START_REM_MAN = 12
            REM_MAN_OBSTACLE_STOP = 13
            REDUCE_DISTANCE_TO_VEHICLE = 14
            CLOSE_DOOR_OR_START_REMOTE = 15
            RELEASE_HANDBRAKE = 16
            LEAVE_VEHICLE = 17
            NO_DRIVER_DETECTED_ON_SEAT = 18
            INTERNAL_SYSTEM_ERROR = 19
            PARKING_OUT_HANDOVER = 20
            STEERING_ACTIVE = 21
            STOP = 22
            MAX_WAITING_TIME_EXCEEDED = 23

            DICT_REM_MESSAGE = {
                39: "PARKING_OUT_FINISHED_FALLBACK",
                38: "PARKING_IN_FINISHED_FALLBACK",
                37: "KEY_NOT_ALIVE",
                36: "KEY_NOT_IN_RANGE",
                35: "SLOW_DOWN",
                34: "WAIT",
                33: "LOW_ENERGY",
                32: "UNDO_FINISHED",
                31: "GARAGE_NOT_OPEN",
                30: "PARKING_CANCELLED_STEER",
                29: "PARKING_CANCELLED_THROTTLE",
                28: "NO_REMOTE_DEVICE_CONNECTED",
                27: "NO_REMOTE_DEVICE_PAIRED",
                26: "SELECT_PARKING_VARIANT",
                25: "SHIFT_TO_N",
                24: "SHIFT_TO_P",
                0: "NO_MESSAGE",
                1: "VERY_CLOSE_TO_OBJECTS",
                2: "START_PARKING_IN",
                3: "PARKING_IN_FINISHED",
                4: "PARKING_CANCELLED",
                5: "PARKING_FAILED",
                6: "SHIFT_TO_R",
                7: "SHIFT_TO_D",
                8: "SHIFT_TO_1",
                9: "RELEASE_BRAKE",
                10: "START_PARKING_OUT",
                11: "PARKING_OUT_FINISHED",
                12: "START_REM_MAN",
                13: "REM_MAN_OBSTACLE_STOP",
                14: "REDUCE_DISTANCE_TO_VEHICLE",
                15: "CLOSE_DOOR_OR_START_REMOTE",
                16: "RELEASE_HANDBRAKE",
                17: "LEAVE_VEHICLE",
                18: "NO_DRIVER_DETECTED_ON_SEAT",
                19: "INTERNAL_SYSTEM_ERROR",
                20: "PARKING_OUT_HANDOVER",
                21: "STEERING_ACTIVE",
                22: "STOP",
                23: "MAX_WAITING_TIME_EXCEEDED",
            }

        class APHMIGeneralScreenRemote:
            """Defining the constants regarding APHMIGeneralScreenRemote"""

            GP_MANEUVER_ACTIVE = 19
            GP_START = 18
            PDC_ACTIVE = 17
            KEY_CONTROL_ACTIVE = 16
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

            DICT_REM_SCREEN = {
                19: "GP_MANEUVER_ACTIVE",
                18: "GP_START",
                17: "PDC_ACTIVE",
                16: "KEY_CONTROL_ACTIVE",
                0: "SYSTEM_NOT_ACTIVE",
                1: "SCANNING_ACTIVE",
                2: "PARKING_SPACE_SELECTION",
                3: "REMOTE_APP_ACTIVE",
                4: "MANEUVER_ACTIVE",
                5: "MANEUVER_FINISHED",
                6: "MANEUVER_INTERRUPTED",
                7: "UNDO_MANEUVER_ACTIVE",
                8: "START_REMOTE_APP",
                9: "PARK_OUT_INIT",
                10: "PARK_OUT_SIDE",
                11: "MENU_REM",
                12: "MANEUVER_ACTIVE_LONG_MAN",
                13: "REM_SV",
                14: "REM_MAN",
                15: "REM_MAN_ACTIVE",
            }

        class RemCommand:
            """Defining the constants regarding RemCommand"""

            REM_TAP_ON_SWITCH_TO_HEAD_UNIT = 32
            REM_TAP_ON_GP = 31
            REM_TAP_ON_PREVIOUS_SCREEN = 30
            REM_TAP_ON_REM_BWD = 29
            REM_TAP_ON_REM_FWD = 28
            REM_TAP_ON_REM_SV = 27
            REM_TAP_ON_REM_MAN = 26
            REM_TAP_ON_PARK_OUT = 25
            REM_TAP_ON_PARK_IN = 24
            REM_TAP_ON_REDO = 23
            REM_TAP_ON_CANCEL = 22
            REM_TAP_ON_UNDO = 21
            REM_TAP_ON_CONTINUE = 20
            REM_TAP_ON_INTERRUPT = 19
            REM_TAP_ON_START_PARKING = 18
            REM_APP_CLOSED = 17
            REM_APP_STARTED = 16
            REM_TAP_ON_PARKING_SPACE_4 = 4
            REM_TAP_ON_PARKING_SPACE_3 = 3
            REM_TAP_ON_PARKING_SPACE_2 = 2
            REM_TAP_ON_PARKING_SPACE_1 = 1
            REM_NO_USER_ACTION = 0

        class Command:
            """Defining the constants regarding HmiCommands"""

            TAP_ON_LSCA = 65
            TAP_ON_LVMD = 64
            TAP_ON_USER_SLOT_DEFINE = 63
            TAP_ON_USER_SLOT_CLOSE = 62
            TAP_ON_USER_SLOT_REFINE = 61
            TAP_ON_MEMORY_SLOT_3 = 60
            TAP_ON_MEMORY_SLOT_2 = 59
            TAP_ON_MEMORY_SLOT_1 = 58
            TAP_ON_MEMORY_PARKING = 57
            TAP_ON_MUTE = 56
            TAP_ON_REVERSE_ASSIST = 55
            TAP_ON_EXPLICIT_SCANNING = 54
            TAP_ON_USER_SLOT_SAVE = 53
            TAP_ON_USER_SLOT_RESET = 52
            TAP_ON_USER_SLOT_ROT_CTRCLKWISE = 51
            TAP_ON_USER_SLOT_ROT_CLKWISE = 50
            TAP_ON_USER_SLOT_MOVE_RIGHT = 49
            TAP_ON_USER_SLOT_MOVE_LEFT = 48
            TAP_ON_USER_SLOT_MOVE_DOWN = 47
            TAP_ON_USER_SLOT_MOVE_UP = 46
            TAP_ON_USER_SLOT_RIGHT_PERP_FWD = 45
            TAP_ON_USER_SLOT_RIGHT_PERP_BWD = 44
            TAP_ON_USER_SLOT_RIGHT_PAR = 43
            TAP_ON_USER_SLOT_LEFT_PERP_FWD = 42
            TAP_ON_USER_SLOT_LEFT_PERP_BWD = 41
            TAP_ON_USER_SLOT_LEFT_PAR = 40
            TAP_ON_WHP = 39
            TAP_ON_SWITCH_TO_REMOTE_APP = 38
            TAP_ON_SWITCH_TO_REMOTE_KEY = 37
            TAP_ON_AP_PDC_TOGGLE_VIEW = 36
            TAP_ON_PDC = 35
            TAP_ON_RM = 34
            TAP_ON_GP = 33
            TAP_ON_START_REM_PARK_KEY = 32
            TAP_ON_SEMI_AUTOMATED_PARKING = 31
            TAP_ON_FULLY_AUTOMATED_PARKING = 30
            TAP_ON_LSCA_RELEASE_BRAKE = 29
            NO_USER_ACTION = 0
            TAP_ON_PARKING_SPACE_LEFT_1 = 1
            TAP_ON_PARKING_SPACE_LEFT_2 = 2
            TAP_ON_PARKING_SPACE_LEFT_3 = 3
            TAP_ON_PARKING_SPACE_LEFT_4 = 4
            TAP_ON_PARKING_SPACE_RIGHT_1 = 5
            TAP_ON_PARKING_SPACE_RIGHT_2 = 6
            TAP_ON_PARKING_SPACE_RIGHT_3 = 7
            TAP_ON_PARKING_SPACE_RIGHT_4 = 8
            TAP_ON_PARKING_SPACE_FRONT_1 = 9
            TAP_ON_PARKING_SPACE_FRONT_2 = 10
            TAP_ON_PARKING_SPACE_FRONT_3 = 11
            TAP_ON_PARKING_SPACE_FRONT_4 = 12
            TAP_ON_PARKING_SPACE_REAR_1 = 13
            TAP_ON_PARKING_SPACE_REAR_2 = 14
            TAP_ON_PARKING_SPACE_REAR_3 = 15
            TAP_ON_PARKING_SPACE_REAR_4 = 16
            TAP_ON_START_SELECTION = 17
            TAP_ON_START_PARKING = 18
            TAP_ON_INTERRUPT = 19
            TAP_ON_CONTINUE = 20
            TAP_ON_UNDO = 21
            TAP_ON_CANCEL = 22
            TAP_ON_REDO = 23
            TAP_ON_START_REM_PARK_PHONE = 24
            TAP_ON_SWITCH_DIRECTION = 25
            TAP_ON_SWITCH_ORIENTATION = 26
            TAP_ON_PREVIOUS_SCREEN = 27
            TOGGLE_AP_ACTIVE = 28

        class RemoteCommands:
            """Defining the constants regarding the Remote control device"""

            TAP_ON_PREVIOUS_SCREEN = 30
            TAP_ON_REM_BWD = 29
            TAP_ON_REM_FWD = 28
            TAP_ON_REM_SV = 27
            TAP_ON_REM_MAN = 26
            TAP_ON_PARK_OUT = 25
            TAP_ON_PARK_IN = 24
            TAP_ON_REDO = 23
            TAP_ON_CANCEL = 22
            TAP_ON_UNDO = 21
            TAP_ON_CONTINUE = 20
            TAP_ON_INTERRUPT = 19
            TAP_ON_START_PARKING = 18
            APP_CLOSED = 17
            APP_STARTED = 16
            TAP_ON_PARKING_SPACE_4 = 4
            TAP_ON_PARKING_SPACE_3 = 3
            TAP_ON_PARKING_SPACE_2 = 2
            TAP_ON_PARKING_SPACE_1 = 1
            NO_USER_ACTION = 0

            dict_head_unit = {
                30: "TAP_ON_PREVIOUS_SCREEN",
                29: "TAP_ON_REM_BWD",
                28: "TAP_ON_REM_FWD",
                27: "TAP_ON_REM_SV",
                26: "TAP_ON_REM_MAN",
                25: "TAP_ON_PARK_OUT",
                24: "TAP_ON_PARK_IN",
                23: "TAP_ON_REDO",
                22: "TAP_ON_CANCEL",
                21: "TAP_ON_UNDO",
                20: "TAP_ON_CONTINUE",
                19: "TAP_ON_INTERRUPT",
                18: "TAP_ON_START_PARKING",
                17: "APP_CLOSED",
                16: "APP_STARTED",
                4: "TAP_ON_PARKING_SPACE_4",
                3: "TAP_ON_PARKING_SPACE_3",
                2: "TAP_ON_PARKING_SPACE_2",
                1: "TAP_ON_PARKING_SPACE_1",
                0: "NO_USER_ACTION",
            }

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

            MEMORY_PARKING_REFINE = 58
            MEMORY_PARKING_FAILED = 57
            MEMORY_PARKING_CANCELLED = 56
            MEMORY_PARKING_FINISHED = 55
            DIAG_USS_12_NOT_RUNNING = 54
            DIAG_USS_11_NOT_RUNNING = 53
            DIAG_USS_10_NOT_RUNNING = 52
            DIAG_USS_9_NOT_RUNNING = 51
            DIAG_USS_8_NOT_RUNNING = 50
            DIAG_USS_7_NOT_RUNNING = 49
            DIAG_USS_6_NOT_RUNNING = 48
            DIAG_USS_5_NOT_RUNNING = 47
            DIAG_USS_4_NOT_RUNNING = 46
            DIAG_USS_3_NOT_RUNNING = 45
            DIAG_USS_2_NOT_RUNNING = 44
            DIAG_USS_1_NOT_RUNNING = 43
            REVERSE_ASSIST_FAILED = 42
            REVERSE_ASSIST_CANCELLED = 41
            REVERSE_ASSIST_FINISHED = 40
            PARKING_OUT_FINISHED_FALLBACK = 39
            PARKING_IN_FINISHED_FALLBACK = 38
            KEY_NOT_ALIVE = 37
            KEY_NOT_IN_RANGE = 36
            SLOW_DOWN = 35
            WAIT = 34
            LOW_ENERGY = 33
            UNDO_FINISHED = 32
            GARAGE_NOT_OPEN = 31
            PARKING_CANCELLED_STEER = 30
            PARKING_CANCELLED_THROTTLE = 29
            NO_REMOTE_DEVICE_CONNECTED = 28
            NO_REMOTE_DEVICE_PAIRED = 27
            SELECT_PARKING_VARIANT = 26
            SHIFT_TO_N = 25
            SHIFT_TO_P = 24
            NO_MESSAGE = 0
            VERY_CLOSE_TO_OBJECTS = 1
            START_PARKING_IN = 2
            PARKING_IN_FINISHED = 3
            PARKING_CANCELLED = 4
            PARKING_FAILED = 5
            SHIFT_TO_R = 6
            SHIFT_TO_D = 7
            SHIFT_TO_1 = 8
            RELEASE_BRAKE = 9
            START_PARKING_OUT = 10
            PARKING_OUT_FINISHED = 11
            START_REM_MAN = 12
            REM_MAN_OBSTACLE_STOP = 13
            REDUCE_DISTANCE_TO_VEHICLE = 14
            CLOSE_DOOR_OR_START_REMOTE = 15
            RELEASE_HANDBRAKE = 16
            LEAVE_VEHICLE = 17
            NO_DRIVER_DETECTED_ON_SEAT = 18
            INTERNAL_SYSTEM_ERROR = 19
            PARKING_OUT_HANDOVER = 20
            STEERING_ACTIVE = 21
            STOP = 22
            MAX_WAITING_TIME_EXCEEDED = 23
            PDW_UNRELIABLE = 80
            LSCA_UNRELIABLE = 81
            RA_UNRELIABLE = 82
            HV_UNRELIABLE = 83

            DICT_MESSAGE = {
                58: "MEMORY_PARKING_REFINE",
                57: "MEMORY_PARKING_FAILED",
                56: "MEMORY_PARKING_CANCELLED",
                55: "MEMORY_PARKING_FINISHED",
                54: "DIAG_USS_12_NOT_RUNNING",
                53: "DIAG_USS_11_NOT_RUNNING",
                52: "DIAG_USS_10_NOT_RUNNING",
                51: "DIAG_USS_9_NOT_RUNNING",
                50: "DIAG_USS_8_NOT_RUNNING",
                49: "DIAG_USS_7_NOT_RUNNING",
                48: "DIAG_USS_6_NOT_RUNNING",
                47: "DIAG_USS_5_NOT_RUNNING",
                46: "DIAG_USS_4_NOT_RUNNING",
                45: "DIAG_USS_3_NOT_RUNNING",
                44: "DIAG_USS_2_NOT_RUNNING",
                43: "DIAG_USS_1_NOT_RUNNING",
                42: "REVERSE_ASSIST_FAILED",
                41: "REVERSE_ASSIST_CANCELLED",
                40: "REVERSE_ASSIST_FINISHED",
                39: "PARKING_OUT_FINISHED_FALLBACK",
                38: "PARKING_IN_FINISHED_FALLBACK",
                37: "KEY_NOT_ALIVE",
                36: "KEY_NOT_IN_RANGE",
                35: "SLOW_DOWN",
                34: "WAIT",
                33: "LOW_ENERGY",
                32: "UNDO_FINISHED",
                31: "GARAGE_NOT_OPEN",
                30: "PARKING_CANCELLED_STEER",
                29: "PARKING_CANCELLED_THROTTLE",
                28: "NO_REMOTE_DEVICE_CONNECTED",
                27: "NO_REMOTE_DEVICE_PAIRED",
                26: "SELECT_PARKING_VARIANT",
                25: "SHIFT_TO_N",
                24: "SHIFT_TO_P",
                0: "NO_MESSAGE",
                1: "VERY_CLOSE_TO_OBJECTS",
                2: "START_PARKING_IN",
                3: "PARKING_IN_FINISHED",
                4: "PARKING_CANCELLED",
                5: "PARKING_FAILED",
                6: "SHIFT_TO_R",
                7: "SHIFT_TO_D",
                8: "SHIFT_TO_1",
                9: "RELEASE_BRAKE",
                10: "START_PARKING_OUT",
                11: "PARKING_OUT_FINISHED",
                12: "START_REM_MAN",
                13: "REM_MAN_OBSTACLE_STOP",
                14: "REDUCE_DISTANCE_TO_VEHICLE",
                15: "CLOSE_DOOR_OR_START_REMOTE",
                16: "RELEASE_HANDBRAKE",
                17: "LEAVE_VEHICLE",
                18: "NO_DRIVER_DETECTED_ON_SEAT",
                19: "INTERNAL_SYSTEM_ERROR",
                20: "PARKING_OUT_HANDOVER",
                21: "STEERING_ACTIVE",
                22: "STOP",
                23: "MAX_WAITING_TIME_EXCEEDED",
                80: "PDW_UNRELIABLE",
                81: "LSCA_UNRELIABLE",
                82: "RA_UNRELIABLE",
                83: "HV_UNRELIABLE",
            }

        class APHMIGeneralScreen:
            """Defining the constants regarding APHMIGeneralScreen states"""

            REVERSE_ASSIST = 24
            MP_WAITING_FOR_FINISH = 23
            MP_USER_ADJUSTMENTS = 22
            MP_SPACE_SELECTION = 21
            DIAG_ERROR = 20
            GP_MANEUVER_ACTIVE = 19
            GP_START = 18
            PDC_ACTIVE = 17
            KEY_CONTROL_ACTIVE = 16
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

            DICT_SCREEN = {
                24: "REVERSE_ASSIST",
                23: "MP_WAITING_FOR_FINISH",
                22: "MP_USER_ADJUSTMENTS",
                21: "MP_SPACE_SELECTION",
                20: "DIAG_ERROR",
                19: "GP_MANEUVER_ACTIVE",
                18: "GP_START",
                17: "PDC_ACTIVE",
                16: "KEY_CONTROL_ACTIVE",
                0: "SYSTEM_NOT_ACTIVE",
                1: "SCANNING_ACTIVE",
                2: "PARKING_SPACE_SELECTION",
                3: "REMOTE_APP_ACTIVE",
                4: "MANEUVER_ACTIVE",
                5: "MANEUVER_FINISHED",
                6: "MANEUVER_INTERRUPTED",
                7: "UNDO_MANEUVER_ACTIVE",
                8: "START_REMOTE_APP",
                9: "PARK_OUT_INIT",
                10: "PARK_OUT_SIDE",
                11: "MENU_REM",
                12: "MANEUVER_ACTIVE_LONG_MAN",
                13: "REM_SV",
                14: "REM_MAN",
                15: "REM_MAN_ACTIVE",
            }

        class APHMIGeneralDrivingDir:
            """Defining the constants regarding APHMIGeneralDrivingDir states"""

            DIRECTION_UNKNOWN = 0
            STANDSTILL = 1
            DRIVING_FORWARDS = 2
            DRIVING_BACKWARDS = 3

            DICT_DRIVDIR = {
                3: "DRIVING_BACKWARDS",
                0: "DIRECTION_UNKNOWN",
                1: "STANDSTILL",
                2: "DRIVING_FORWARDS",
            }

        class ParkingSlotPossOrientation:
            """Defining the constants regarding ParkingSlotPossOrientation states"""

            ONE_DIRECTION = 0
            BOTH_DIRECTION = 1

        class APHMIGeneralAVGType:
            """Defining the constants regarding APHMIGeneralAVGType states"""

            NO_AVG_TYPE = 0
            PARK_IN_PARALLEL_LEFT = 1
            PARK_IN_PARALLEL_RIGHT = 2
            PARK_IN_PERPENDICULAR_LEFT_FWD = 3
            PARK_IN_PERPENDICULAR_LEFT_BWD = 4
            PARK_IN_PERPENDICULAR_RIGHT_FWD = 5
            PARK_IN_PERPENDICULAR_RIGHT_BWD = 6
            PARK_OUT_PARALLEL_LEFT = 7
            PARK_OUT_PARALLEL_RIGHT = 8
            PARK_OUT_PERPENDICULAR_LEFT_FWD = 9
            PARK_OUT_PERPENDICULAR_LEFT_BWD = 10
            PARK_OUT_PERPENDICULAR_RIGHT_FWD = 11
            PARK_OUT_PERPENDICULAR_RIGHT_BWD = 12
            REM_MAN_FWD = 13
            REM_MAN_BWD = 14
            GP_GENERAL = 15

            DICT_MESSAGE = {
                0: "NO_AVG_TYPE",
                1: "PARK_IN_PARALLEL_LEFT",
                2: "PARK_IN_PARALLEL_RIGHT",
                3: "PARK_IN_PERPENDICULAR_LEFT_FWD",
                4: "PARK_IN_PERPENDICULAR_LEFT_BWD",
                5: "PARK_IN_PERPENDICULAR_RIGHT_FWD",
                6: "PARK_IN_PERPENDICULAR_RIGHT_BWD",
                7: "PARK_OUT_PARALLEL_LEFT",
                8: "PARK_OUT_PARALLEL_RIGHT",
                9: "PARK_OUT_PERPENDICULAR_LEFT_FWD",
                10: "PARK_OUT_PERPENDICULAR_LEFT_BWD",
                11: "PARK_OUT_PERPENDICULAR_RIGHT_FWD",
                12: "PARK_OUT_PERPENDICULAR_RIGHT_BWD",
                13: "REM_MAN_FWD",
                14: "REM_MAN_BWD",
                15: "GP_GENERAL",
            }

        class APHMIGeneralContinuePoss:
            """Defining the constants regarding APHMIGeneralContinuePoss"""

            FALSE = 0
            TRUE = 1

        class APHMIGeneralRevAssistPoss:
            """Defining the constants regarding APHMIGeneralRevAssistPoss"""

            FALSE = 0
            TRUE = 1

    class LoDMCHoldReq:
        """Defining the constants regarding LoDMCHoldReq"""

        FALSE = 0
        TRUE = 1

    class LoDMCEmergencyHoldRequest:
        """Defining the constants regarding LoDMCEmergencyHoldRequest"""

        FALSE = 0
        TRUE = 1

    class LoDMCCtrlRequestSource:
        """Defining the constants regarding LoDMCCtrlRequestSource"""

        NO_REQUESTER = 0
        AP_TRJCTL = 1
        LSCA = 2
        AP_SAFBAR = 3

        DICT_SOURCE = {
            3: "AP_SAFBAR",
            2: "LSCA",
            1: "AP_TRJCTL",
            0: "NO_REQUESTER",
        }

    class VehicleLights:
        """Defining the constants regarding lights of vehicle"""

        class HazardLights:
            HAZARD_WARNING_REQ = 1
            HAZARD_LIGHT_OFF = 0
            HAZARD_LIGHT_ON = 1
            HAZARD_LIGHT_INVALID = 3

            DICT_HAZARDLIGHTS = {
                0: "HAZARD_LIGHT_OFF",
                1: "HAZARD_LIGHT_ON",
                3: "HAZARD_LIGHT_INVALID",
            }

    class SotifTime:
        """Defining the constants regarding sotif req. time"""

        T_HAZARD = 3  # [sec]
        T_UPDATE_1 = 600  # ms
        T_UPDATE_2 = 200  # ms
        T_UPDATE_3 = 600  # ms
        T_UPDATE_4 = 200  # ms
        T_PRESS_DEAD_MAN_SWITCH = 100  # ms
        T_SECURE = 2  # [sec]

    class SotifParameters:
        """Defining the constants regarding parameters for SOTIF requirements"""

        REM_BATTERY_LIMIT_LOW = 20  # [%]
        T_MOVE_VEHICLE = 1  # [sec]
        T_MOVE_RC = 2  # [sec]
        P_DROP = 95  # [%]

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
        PERP_IN_F_D_4 = 3
        PERP_IN_F_D_5 = 0.6
        # Parallel parking in
        PAR_IN_D_1 = 6
        PAR_IN_D_2 = 0.3
        PAR_IN_D_3 = 3
        PAR_IN_D_4 = 3
        PAR_IN_D_5 = 0.6
        AP_G_MAN_AREA_PAR_IN_D7_M = 3
        # Parallel parking out
        PAR_OUT_D_1 = 4
        PAR_OUT_D_2 = 3
        PAR_OUT_D_3 = 3
        PAR_OUT_D_4 = 0.6

    class VehCanActualGear:
        """Defining the constants regarding ego vehicle gear in Conti_Veh_CAN.dbc"""

        POWER_FREE_ACTUALGEAR = 12
        PARK_ACTUALGEAR = 11
        REVERSE_ACTUALGEAR = 10
        NINTH_ACTUALGEAR = 9
        EIGHTH_ACTUALGEAR = 8
        SEVENTH_ACTUALGEAR = 7
        SIXTH_ACTUALGEAR = 6
        FIFTH_ACTUALGEAR = 5
        FOURTH_ACTUALGEAR = 4
        THIRD_ACTUALGEAR = 3
        SECOND_ACTUALGEAR = 2
        FIRST_ACTUALGEAR = 1
        NEUTRAL_ACTUALGEAR = 0
        INVALID_ACTUALGEAR = 15

        DICT_ACTUAL_GEAR = {
            12: "POWER_FREE_ACTUALGEAR",
            11: "PARK_ACTUALGEAR",
            10: "REVERSE_ACTUALGEAR",
            9: "NINTH_ACTUALGEAR",
            8: "EIGHTH_ACTUALGEAR",
            7: "SEVENTH_ACTUALGEAR",
            6: "SIXTH_ACTUALGEAR",
            5: "FIFTH_ACTUALGEAR",
            4: "FOURTH_ACTUALGEAR",
            3: "THIRD_ACTUALGEAR",
            2: "SECOND_ACTUALGEAR",
            1: "FIRST_ACTUALGEAR",
            0: "NEUTRAL_ACTUALGEAR",
            15: "INVALID_ACTUALGEAR",
        }

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
        ZERO_SPEED_KMH = 0.1
        ZORE_STEERING_SPEED = 0.007
        IGNITION_OFF = 0
        IGNITION_ON = 1
        LANE_WIDTH = 3.5  # [m]
        PARKING_SLOT_WIDTH = 6  # [m]
        OBSTACLE_OFFSET = 1.5  # [m]
        OBSTACLE_WIDTH = 0.2  # [m]
        REAR_WHEEL_TO_HITCH = 0.74  # [m]
        MIN_DIST_BODY_TRAVERSABLE_OBSTACLE = -0.1
        PEDESTRIAN_FEMALE_SENIOR_02_BABYSTROLLER_WIDTH = 0.6
        OverhangPassatB8 = 1.096  # [m]

        class UssError:
            """Defining the constants regarding UssError"""

            TIMEOUT_DISABLED = 0
            TIMEOUT_ENABLED = -1

        class TrafficObjectDimensions:
            """Defining the constant dimensions of various Traffic objects in Carmaker"""

            CYCLIST_ADULT_EURONCAP_2020_02_LENGTH = 1.9  # [m]
            CYCLIST_ADULT_EURONCAP_2020_02_WIDTH = 0.72  # [m]
            CYCLIST_ADULT_EURONCAP_2020_02_HEIGHT = 1.9  # [m]

            MB_CITARO0345_2005_LENGTH = 10.7  # [m]
            MB_CITARO0345_2005_WIDTH = 2.55  # [m]
            MB_CITARO0345_2005_HEIGHT = 2.65  # [m]

            AGRI_00_LENGTH = 5.68  # [m]
            AGRI_00_WIDTH = 2.58  # [m]
            AGRI_00_HEIGHT = 2.74  # [m]

            PEDESTRIAN_ADULT_EURONCAP_2018_ANIMATED_LENGTH = 0.8  # [m]
            PEDESTRIAN_ADULT_EURONCAP_2018_ANIMATED_WIDTH = 0.64  # [m]
            PEDESTRIAN_ADULT_EURONCAP_2018_ANIMATED_HEIGHT = 1.81  # [m]

    class TrailerConnection:
        """Defining the constants regarding Trailer state"""

        NO_DETECT_TRAILERCONNECTION = 0
        OK_TRAILERCONNECTION = 1
        INVALID_TRAILERCONNECTION = 3

    class Seat:
        """Defining the constants regarding seats"""

        DRIVERS_OCCUPIED = 3
        DRIVERS_FREE = 2

    class SeatBelt:
        """Defining the constants regarding seat belts"""

        DRIVERS_CLOSED = 3
        DRIVERS_OPEN = 2

    class Door:
        """Defining the constants regarding Door states"""

        DOORSTATE_TRUNK_OPEN = 32
        DOORSTATE_ENG_HOOD_OPEN = 16
        DOORSTATE_REAR_RIGHT_OPEN = 8
        DOORSTATE_REAR_LEFT_OPEN = 4
        DOORSTATE_FRONT_RIGHT_OPEN = 2
        DOORSTATE_FRONT_LEFT_OPEN = 1
        DOORSTATE_ALL_CLOSED = 0

        DICT_DOORS = {
            32: "DOORSTATE_TRUNK_OPEN",
            16: "DOORSTATE_ENG_HOOD_OPEN",
            8: "DOORSTATE_REAR_RIGHT_OPEN",
            4: "DOORSTATE_REAR_LEFT_OPEN",
            2: "DOORSTATE_FRONT_RIGHT_OPEN",
            1: "DOORSTATE_FRONT_LEFT_OPEN",
            0: "DOORSTATE_ALL_CLOSED",
        }

    class TunkCap:
        """Defining the constants regarding TunkCap states"""

        CLOSED = 0
        OPEN = 1

        DICT = {0: "CLOSED", 1: "OPEN"}

    class Brake:
        """Defining the constants regarding parking brake states"""

        PARK_BRAKE_SET = 1

    class BrakePressure:
        """Defining the factor and the offset for BrakePressureDriver signal"""

        brake_pressure_driver_offset = -30
        brake_pressure_driver_factor = 0.3

    class Lsca:
        """Defining the constants regarding LSCA values"""

        LSCA_NOT_ACTIVE = 0
        LSCA_ACTIVE = 1
        LSCA_B_FORW_SPEED_MIN_ON_MPS = 0.01
        LSCA_B_FORW_SPEED_MAX_ON_MPS = 2.78
        LSCA_B_BACKW_SPEED_MIN_ON_MPS = 0.01
        LSCA_B_BACKW_SPEED_MAX_ON_MPS = 2.78
        LSCA_B_STANDSTILL_TIME_S = 1  # [sec]
        LSCA_INIT_TIME = 1500  # [ms]
        LSCA_TOLERANCE_TIME = 100  # [ms]
        LSCA_B_OVERIDE_ACCELPEDAL_AFTERBRAKING_PERC = 0.25  # [25%]
        LSCA_B_OVERIDE_BRAKEPEDAL_AFTERBRAKING_PERC = 0.90  # [pressed 90%]
        BRAKE_REQUEST = 1
        REAR_WARNING_ACTIVE = 1
        REACTION_TIME_ON_OBSTACLES = 600  # [ms]
        REACTION_TIME_WITHOUT_OBSTACLES = 200  # [ms]
        T_REACTION_LSCA = 1000  # [ms]
        MAX_FRONT_DETECTION_ZONE = 6  # [m]
        LSCA_TIME_REMOTE_ALERT = 1000  # [ms]

    class WheelDrivingDirection:
        WHEEL_DIRECTION_FL = {0: "FORWARD", 1: "BACKWARD", 2: "INIT", 3: "INVALID"}

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
        RA_G_ACTIVATION_REQUEST_TIMEOUT = 30  # [sec]
        AP_G_MAX_WAIT_TIME_REM_S = 120  # [sec]
        AP_G_MAX_TIME_REM_DISCONNECT_S = 1  # [sec]
        AP_G_MAX_TIME_TO_PARK_IN_S = 180  # [sec]
        # Limit(s) for speed
        AP_G_MAX_AVG_V_MPS = 2.778
        AP_G_MAX_AVG_YAW_RATE_RADPS = 1
        AP_V_MAX_STEER_ANG_VEL_RADPS = 0.64
        AP_G_V_SCANNING_THRESH_ON_MPS = 2.77
        AP_G_V_SCANNING_THRESH_OFF_MPS = 11.250
        AP_G_MAX_AVG_CTRL_V_MPS = 1.6
        # Limit(s) for acceleration
        AP_G_MAX_AVG_LONG_ACCEL_MPS2 = 0.5
        AP_G_MAX_DECEL_COMFORTABLE_MPS2 = 0.5
        AP_G_MAX_DECEL_EMERGENCY_MPS2 = 10
        AP_G_MAX_AVG_LAT_ACCEL_MPS2 = 1
        AP_C_PC_MAX_STEER_ACC_RADPS2 = 4.2
        AP_C_PC_FIRST_STEER_ACC_RADPS2 = 2.2
        # Limit(s) for jerk
        AP_G_MAX_AVG_LON_JERK_COMF_MPS3 = 3
        # Limit(s) for distance
        AP_G_ROLLED_DIST_IN_THRESH_M = 1
        AP_G_MAX_DIST_WHEEL_STOPPER_M = 0.075  # [m]
        AP_G_MIN_LENGTH_STROKE_M = 0.1  # [m]
        # Limit(s) for %
        AP_G_THROTTLE_THRESH_PERC = 10
        AP_G_THROTTLE_TRESH_PERC = 5
        # Limit(s) for brake
        AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR = 15
        AP_G_BRAKE_PRESS_THRESH_BAR = 5
        # Limit for strokes
        AP_G_MAX_NUM_STROKES_PAR_NU = 13
        AP_G_MAX_NUM_STROKES_PERP_NU = 10
        AP_G_MAX_NUM_STROKES_ANG_NU = 6
        # Tester defined
        TRESHOLD_TO_STANDSTILL = 5  # [sec]
        THRESHOLD_MAX_DISTANCE = 1.9  # [m]
        THRESHOLD_MAX_TIME_UNTIL_CONTINUE = 4  # [s]
        AP_G_ROLLED_DIST_OUT_THRESH_M = 1  # [m]
        AP_S_STEERING_TORQUE_THRESH_NM = 4  # [Nm]
        AP_G_MAX_INTERRUPT_TIME_S_PAR230 = 15  # [s]
        THRESOLD_TO_TERMINATE = 10  # [s]
        AP_G_MAX_TIME_TO_PARK_OUT_S = 45  # [s]
        AP_G_MAX_LATENCY_REM_S = 0.25  # [s]
        RA_G_MAX_LAT_START_ERROR_M = 0.05 # [m]

    class TurnSignallLever:
        """Defining the constants regarding TurnSignallLever"""

        TURN_LEVER_OFF = 0
        TURN_LEVER_ENGAGED_LEFT = 1
        TURN_LEVER_ENGAGED_RIGHT = 2
        TURN_LEVER_INVALID = 3

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
        AP_G_MAX_HEIGHT_CURBSTONE_M = 0.17  # [m]

    class L1D_Thresholds:
        """Defining the constants regarding L1D limits"""

        MAX_STATICK_DETECTION_DISTANCE = 12  # [m] from origin point of ego vehicle

    class PDW:
        """Defining contants related to PDW functionality"""

        class Veh_modules:
            """Defining the other module states of our ego vehicle"""

            class ENGINE:
                """Class representing the different states of the engine"""

                VALID = 0
                INVALID = 1

            class EPS:
                """Class representing the different states of the EPS"""

                SYSTEM_AVAILABLE = 0
                SYSTEM_NOT_AVAILABLE = 1
                SYSTEM_ERROR = 2
                INVALID = 3

            class SERVICE_BRAKE:
                """Class representing the different states of the service brake"""

                VALID = 0
                INVALID = 1
                NOT_AVAILABLE = 3

            class USS_STATE:
                """Class representing the different states of the USS deactivation switch"""

                ACTIVE = 0
                INACTIVE = 1

            class GEARBOX:
                """Class representing the different states of the gearbox"""

                VALID = 0
                INVALID = 1
                NOT_AVAILABLE = 3

        # Function activation  speed thresholds
        class Thresholds:
            """Class that holds the thresholds for speed and distance detection."""

            MIN_SPEED_THRESHOLD_MPS = 0.01  # mps
            MAX_SPEED_THRESHOLD_MPS = 5.56
            MIN_DISTANCE_DETECTION = 0  # meters
            MAX_DISTANCE_DETECTION = 2.55
            CONT_TONE_RANGE = 0.3
            VEH_ACCEL_LOWER = -21  # m/s2
            VEH_ACCEL_UPPER = 21
            MIN_LSCA_DISTANCE = 0
            MAX_LSCA_DISTANCE = 1.25

        # Function states
        class States:
            """Class representing the different states of the parking system."""

            INIT = 0
            OFF = 1
            ACTIVATED_BY_R_GEAR = 2
            ACTIVATED_BY_BUTTON = 3
            AUTOMATICALLY_ACTIVATED = 4
            FAILURE = 5

        class Button:
            """A class representing constants for buttons."""

            PDW_AUTOACT_TAP_ON = 74
            WHP_TAP_ON = 39
            PDW_TAP_ON = 35  # decimal value
            AUP_TOGGLE_ACTIVE = 28
            START_PARKING = 18
            NO_USER_INTERACTION = 0

        class Gear:
            """A class representing different types of gears for a vehicle."""

            class Manual:
                """Class representing manual constants."""

                INVALID = 15
                NEUTRAL = 0
                REVERSE = 10
                PARK = 11
                FIRST = 1

            class Automatic:
                """Class representing automatic constants."""

                NEUTRAL = 0
                FORWARD = 1
                REVERSE = 3
                PARK = 2
                INVALID = 7

        # EPB state:
        class EPB_state:
            """A class representing the different states of the EPB."""

            VALID = 0
            INVALID = 1
            NotAvailable = 3

        class Veh_Motion:
            """A class representing the different states of the vehicle motion."""

            class Wheel_dir:
                """A class representing the different states of the wheel direction."""

                FORWARD = 0
                REVERSE = 1
                INIT = 2
                INVALID = 3

            class Wheel_ticks:
                """A class representing the different values of the wheel ticks."""

                VALID = 0
                INVALID = 1
                INIT = 991
                LOW_VOLTAGE = 1022
                ERROR = 1023

        class FTTI:
            """A class representing the different states of the FTTI."""

            SYSTEM = 599999
            SYSTEM_WO_OBJECTS = 199999
            SYSTEM_INIT = 1499999
            REDUCTION_CONT = 4999999
            REDUCTION_INTERM = 2999999
            REDUCTION_STEP = 499999
            SAFETY_SS = 699999
            SAFE_STANDSTILL = 1999999

        class DrivingTubeDisplay:
            """A class representing the different states of the driving tube display."""

            NONE = 0
            FRONT = 1
            REAR = 2
            BOTH = 3

        class Driver_braking:
            """A class representing the different states of the driver braking."""

            ACTIVE = 1
            INACTIVE = 0
            INVALID = 3

        class Distance_covered:
            """A class representing the different states of the distance covered."""

            ROLL_BACKWARDS_WITH_TP = 0.1
            ROLL_BACKWARDS_WO_TP = 0.5

        class CriticalLevel:
            """A class representing the different critical zones of PDW."""

            RED_ZONE = 3
            YELLOW_ZONE = 2
            GREEN_ZONE = 1
            NO_CRITICAL_ZONE = 0

        class CriticalSlice:
            """A class representing the different critical slices of PDW."""

            CLOSE_SLICE = 3
            MIDDLE_SLICE = 2
            FAR_SLICE = 1
            NO_SLICE = 0

        class SliceDistances:
            """A class representing critical slice distances."""

            GREEN_FAR_L = 2.26
            GREEN_FAR_H = 2.55
            GREEN_MID_L = 1.98
            GREEN_MID_H = 2.26
            GREEN_CLOSE_L = 1.7
            GREEN_CLOSE_H = 1.98
            YELLOW_FAR_L = 1.41
            YELLOW_FAR_H = 1.7
            YELLOW_MID_L = 1.13
            YELLOW_MID_H = 1.41
            YELLOW_CLOSE_L = 0.85
            YELLOW_CLOSE_H = 1.13
            RED_FAR_L = 0.56
            RED_FAR_H = 0.85
            RED_MID_L = 0.28
            RED_MID_H = 0.56
            RED_CLOSE_L = 0
            RED_CLOSE_H = 0.28

    class DoorOpen:
        """Defining the constants regarding door open states"""

        DOORS_CLOSED = 0
        LEFT_FRONT_DOOR_OPEN = 1
        RIGHT_FRONT_DOOR_OPEN = 2
        LEFT_BACK_DOOR_OPEN = 4
        RIGHT_BACK_DOOR_OPEN = 8
        TRUNK_OPEN = 16
        ENGINE_HOOD_OPEN = 32

    class TrailerHitchStatus:
        """Defining the constants regarding trailer hitch status"""

        NOT_FOLDED = 0
        FOLDED = 1
        NOT_INSTALLED = 2

    class WHP:
        """Defining the constants regarding Wheel Protection function"""

        class State:
            """Defining the constants regarding the state of Wheel Protection function"""

            INIT = 0
            INACTIVE = 1
            ACTIVE = 2
            FAILURE = 3

        class Warning_Lvl:
            """Defining the constants regarding the warning level of Wheel Protection function"""

            NOT_AVAILABLE = 0
            NO_WARNING = 1
            LOW_WARNING = 2
            HIGH_WARNING = 3

        class WhlDirection:
            """Defining the constants regarding direction of the wheels for Wheel Protection function"""

            LEFT = 0
            RIGHT = 1


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


class SENSOR_MODE:
    """Sensor mode constants"""

    SENSOR_NFD_MODE = 2
    SENSOR_FFD_MODE = 3
    SENSOR_SWITCH_MODE = 4


class ENTRY_HIL_CONSTANTS:
    """Defining the constants regarding entry HIL tests"""

    NUMBER_OF_ECHOES = 720
    NUMBER_OF_OBJECTS = 32
    NUMBER_OF_SENSORS = 12
    NUMBER_OF_POINTS = 255


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

    class LaDMC_Status_nu:
        """Defining the constants for the lateral DMC status"""

        OFF: int = 0
        ON_STEERING: int = 1
        DRIVER_SUPPORT_STEERING: int = 2
        DRIVER_COUNTERSTEERING: int = 3
        PERM_DISABLED: int = 4
        TEMP_DISABLED: int = 5
        ON_BRAKE: int = 6
        ON_COMBINED: int = 7

    class RequestedDrivingDir:
        """Defining the constants for requested driving directions"""

        NOT_RELEVANT: int = 0
        FORWARD: int = 1
        BACKWARD: int = 2

    class MFMDrivingResistanceType:
        """Defining the constant for driving resistance type"""

        MFM_NONE: int = 0
        MFM_WHEEL_STOPPER: int = 7

    class Parameter:
        """
        :param AP_C_PC_FIRST_STEER_ACCUR_RAD: The accuracy threshold for considering angle as 'close'
        :param AP_C_PC_MIN_STEER_VEL_RADPS: Minimum steer angle velocity for ramping steer angle to desired value for first
         steering (at wheels)
        :param AP_M_MAX_NUM_TRAJ_CTRL_POINTS: The number of trajectory control points in the planned path.
        :param AP_C_PC_FAIL_MAX_LAT_ERROR_M:  Maximum allowed absolute deviation from calculated trajectory
        :param AP_C_PC_FAIL_MAX_YAW_ERROR_RAD: Maximum allowed absolute yaw angle (orientation) error from calculated trajectory.
        :param AP_C_PC_FIRST_STEER_VEL_RADPS: Maximum steer angle velocity for ramping steer angle to desired value for
            first steering (at wheels).
        :param AP_C_PC_FIRST_STEER_ACC_RADPS2: Maximum steer angle acceleration for ramping steer angle to desired value
            for first steering (at wheels)
        :param AP_C_KPI_PASS_MAX_LAT_ERROR_M: Maximum allowed absolute lateral deviation from calculated trajectory to pass the KPI
        :param AP_C_KPI_FAIL_MAX_LAT_ERROR_M: Maximum allowed absolute lateral deviation from calculated trajectory to not fail/accept the KPI
        :param AP_C_KPI_SUCCESS_RATE_MAX_LAT_ERROR_PASSED_PERCENT: Success rate for absolute lateral error KPI for passed threshold
        :param AP_C_KPI_SUCCESS_RATE_MAX_LAT_ERROR_ACCEPT_PERCENT: Success rate for absolute lateral error KPI for acceptable threshold

        """

        AP_C_PC_FIRST_STEER_ACCUR_RAD: float = 0.1746  # radians
        AP_C_PC_MIN_STEER_VEL_RADPS: float = 0.04267  # rad/s

        LOCTRL_EMERGENCY_STOP: int = 7
        LODMC_HOLD_REQ_ON = 1
        AP_M_MAX_NUM_TRAJ_CTRL_POINTS: int = 20
        AP_C_PC_FAIL_MAX_LAT_ERROR_M: float = 0.1  # m
        AP_C_PC_FAIL_MAX_YAW_ERROR_RAD: float = 0.067  # rad
        AP_C_PC_FIRST_STEER_VEL_RADPS: float = 0.66  # rad/s
        AP_C_PC_FIRST_STEER_ACC_RADPS2: float = 2.20  # rad/s^2
        AP_V_STEER_RATIO_NU = 14.7  # No Unit
        AP_C_MANEUV_FINISHED_TIME_S: float = 0.1  # s
        AP_C_MANEUV_FINISHED_LIMIT_M: float = 0.15  # m
        AP_C_ACTIVE_CONTROL_MIN_TIME_S: float = 2  # s
        AP_C_MANEUV_FINISHED_HYST_M: float = 0.04  # m
        AP_C_COMP_TIRE_DEF_STEER_WHEEL_ANGLE_DEG: float = 5.0  # deg
        AP_C_COMP_TIRE_DEF_FACTOR_NU = 0.05  # No Unit
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
        AP_C_KPI_STANDSTILL_TIME_S: float = 4.5  # s

        AP_C_KPI_SUCCESS_RATE_TIRE_DEF_PERCENT = 95  # percentage

        AP_V_MAX_STEER_ANG_RAD = 0.595  # rad
        AP_C_PC_MAX_STEER_ACC_RADPS2 = 4.20  # rad/s^2
        AP_C_STEER_SATURATE_RATE_RADPS = 0.32  # rad/s
        AP_C_STEER_SATURATE_THRESH_RAD = 0.036  # rad
        AP_V_MAX_STEER_ANG_VEL_RADPS = 0.64  # rad/s
        floatingPointThreshold = 0.00001  # no unit

        AP_C_LEAVING_PATH_BEHIND_M = 0.15  # m
        AP_C_LEAVING_PATH_BEFORE_M = 0.15  # m
        AP_C_VL_RAMP_UP_DIST_NU = 1  # No Unit
        AP_C_VL_RAMP_UP_VEL_NU = 1  # No Unit
        AP_C_PC_VELO_PREVIEW_TIME_S = 0.50  # s
        AP_C_MIN_PARKING_VEL_MPS = 0.20  # m/s
        AP_C_VL_VEL_RAMP_LIMIT_MPS2 = 0.30  # m/s2
        AP_V_WHEELBASE_M = 2.786  # m
        AP_C_WFC_WS_VEL_DIST_THRESH_M = 1  # m
        AP_C_FEAT_WS_VEL_REDUCED_NU = 1  # No Unit
        AP_C_WFC_WS_VEL_LIMIT_MPS = 0.201  # m/s
        AP_C_FEAT_WAIT_FOR_CONTACT_NU = 1  # No Unit
        AP_C_WFC_OVERSHOOT_LENGTH_M = 0.175  # m
        AP_C_WFC_OVERSHOOT_DIST_THRES_M = 2  # m
        AP_C_WFC_VDY_DIST_THRES_M = 0.30  # m
        AP_C_WFC_VDY_DRIVE_OFF_THRES_M = 0.20  # m
        AP_C_MAX_DIST_TO_STOP_M = 32.765  # m
        AP_G_MAX_AVG_LAT_ACCEL_MPS2 = 1  # m/s2
        AP_G_MAX_AVG_YAW_RATE_RADPS = 1  # rad/s

class ParkInEndSuccessRate:
    """Defining the constants used in park in success rate kpi"""

    class Par:
        """Defining the constants for parallel"""

        NB_STROKES = 4  # strokes
        TIME = 65  # seconds
        LAT_ERROR = (-0.1, 0.1)  # m
        LONG_ERROR = (-0.1, 0.1)  # m
        ORIENTATION_ERROR = (-1, 1)  # degrees

    class PerpAng:
        """Defining the constants for perpendicular and angular"""

        TIME = 65  # seconds
        NB_STROKES = 4  # strokes
        LAT_ERROR = (-0.05, 0.05)  # m
        LONG_ERROR = (-0.1, 0.1)  # m
        ORIENTATION_ERROR = (-1, 1)  # degrees


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

        THRESHOLD_OVERLAP = 60  # % [https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_Z8FBEJtjEe6Zoo0NnU8erA&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_lWHOEPvsEeqIqKySVwTVNQ%2Fcomponents%2F_u4eQYMlKEe2iKqc0KPO99Q]
        THRESHOLD_ORIENTATION = 15  # degrees [https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_rdg3gJtjEe6Zoo0NnU8erA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_lWHOEPvsEeqIqKySVwTVNQ%2Fcomponents%2F_u4eQYMlKEe2iKqc0KPO99Q&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324]
        THRESHOLD_CENTER_DISTANCE_SHORT_SIDE = 0.8  # meters [https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_0DjgQJtjEe6Zoo0NnU8erA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_lWHOEPvsEeqIqKySVwTVNQ%2Fcomponents%2F_u4eQYMlKEe2iKqc0KPO99Q&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324]
        THRESHOLD_CENTER_DISTANCE_LONG_SIDE = 1.6  # meters [https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_BI9QQJtkEe6Zoo0NnU8erA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_lWHOEPvsEeqIqKySVwTVNQ%2Fcomponents%2F_u4eQYMlKEe2iKqc0KPO99Q&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324]

        THRESHOLD_TPR = 85  # % [https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI__Y1CwLqZEe6Sn6sUDJb62g&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_lWHOEPvsEeqIqKySVwTVNQ%2Fcomponents%2F_u4eQYMlKEe2iKqc0KPO99Q]
        THRESHOLD_FPR = 25  # % [https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_VUnIILqbEe6Sn6sUDJb62g&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_lWHOEPvsEeqIqKySVwTVNQ%2Fcomponents%2F_u4eQYMlKEe2iKqc0KPO99Q&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324]
        THRESHOLD_FNR = 15  # % [https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_LHFkMLqbEe6Sn6sUDJb62g&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_lWHOEPvsEeqIqKySVwTVNQ%2Fcomponents%2F_u4eQYMlKEe2iKqc0KPO99Q&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324]

    class AutoScale:
        """Class containing predefined auto-scaling percentage values."""

        PERCENTAGE_X_GT = 0.8  # percentage/100
        PERCENTAGE_Y_GT = 0.9  # percentage/100
        PERCENTAGE_X_SLOT = 1.8  # percentage/100
        PERCENTAGE_Y_SLOT = 0.4  # percentage/100

    class VehicleDimensions:
        """Class containing predefined vehicle dimensions."""

        VEHICLE_LENGTH = 4.767  # meters
        VEHICLE_WIDTH = 1.832  # meters

    class ImageSize:
        """
        A class used to represent the size of an image.
        Attributes:
            IMG_WIDTH (int): The width of the image in pixels.
            IMG_HEIGHT (int): The height of the image in pixels.
            SCALE_FACTOR (float): The factor by which the image is scaled.
        """

        IMG_WIDTH = 1150
        IMG_HEIGHT = 900
        SCALE_FACTOR = 0.5

    class ParkingBoxesSignalIterator:
        """
        A class used to iterate over parking boxes signals.
        Attributes
        ----------
        MAX_NUM_PARKING_BOXES : int
            The maximum number of parking boxes.
        MAX_NUM_VERTICES_PER_BOX : int
            The maximum number of vertices per parking box.
        """

        MAX_NUM_PARKING_BOXES = 8
        MAX_NUM_VERTICES_PER_BOX = 4


class DrawCarLayer:
    """Class containing predefined values used to draw the car layer."""

    def draw_car(new_origin_x, new_origin_y, new_yaw):
        """Draw the car layer with the given origin coordinates."""
        figures = []
        DrawCarLayer.CarCoordinates.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        car_fix_coordinates = [
            DrawCarLayer.CarCoordinates.get_translated_coord(key)
            for key in vars(DrawCarLayer.CarCoordinates).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.CarCoordinates, key), list)
        ]
        car_fix_coordinates.append(car_fix_coordinates[0])
        car_x = [list[0] for list in car_fix_coordinates]
        car_y = [list[1] for list in car_fix_coordinates]

        figures.append(
            go.Scatter(
                x=car_x,
                y=car_y,
                fill="toself",  # Fill the shape with color
                line=dict(color="black", width=0.1),  # Set the color of the exterior lines
                fillcolor="orange",  # Set the fill color
                mode="lines",
                name="Car",
                text=f"Rear axle coords:<br>" f"X: {new_origin_x}<br>" f"Y: {new_origin_y}",
                legendgroup="Car",
            )
        )
        DrawCarLayer.HoodTrim.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        back_windshield = [
            DrawCarLayer.HoodTrim.get_translated_coord(key)
            for key in vars(DrawCarLayer.HoodTrim).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.HoodTrim, key), list)
        ]
        back_windshield.append(back_windshield[0])
        back_windshield_x = [list[0] for list in back_windshield]
        back_windshield_y = [list[1] for list in back_windshield]
        figures.append(
            go.Scatter(
                x=back_windshield_x,
                y=back_windshield_y,
                # fill="toself",  # Fill the shape with color
                line=dict(color="#D18700"),  # Set the color of the exterior lines
                # fillcolor="black",  # Set the fill color
                mode="lines",
                hoverinfo="skip",
                legendgroup="Car",
                showlegend=False,
                name="Vehicle - Passat B8 Variant",
            )
        )
        DrawCarLayer.Windows.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        windshield = [
            DrawCarLayer.Windows.get_translated_coord(key)
            for key in vars(DrawCarLayer.Windows).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.Windows, key), list)
        ]
        windshield.append(windshield[0])
        windshield_x = [list[0] for list in windshield]
        windshield_y = [list[1] for list in windshield]
        figures.append(
            go.Scatter(
                x=windshield_x,
                y=windshield_y,
                fill="toself",  # Fill the shape with color
                line=dict(color="black"),  # Set the color of the exterior lines
                fillcolor="black",  # Set the fill color
                mode="lines",
                hoverinfo="skip",
                legendgroup="Car",
                showlegend=False,
                name="Vehicle - Passat B8 Variant",
            )
        )
        DrawCarLayer.BackWindow.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        back_windshield = [
            DrawCarLayer.BackWindow.get_translated_coord(key)
            for key in vars(DrawCarLayer.BackWindow).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.BackWindow, key), list)
        ]
        back_windshield.append(back_windshield[0])
        back_windshield_x = [list[0] for list in back_windshield]
        back_windshield_y = [list[1] for list in back_windshield]
        figures.append(
            go.Scatter(
                x=back_windshield_x,
                y=back_windshield_y,
                fill="toself",  # Fill the shape with color
                line=dict(color="black"),  # Set the color of the exterior lines
                fillcolor="black",  # Set the fill color
                mode="lines",
                hoverinfo="skip",
                legendgroup="Car",
                showlegend=False,
                name="Vehicle - Passat B8 Variant",
            )
        )

        DrawCarLayer.LeftWindows.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        back_windshield = [
            DrawCarLayer.LeftWindows.get_translated_coord(key)
            for key in vars(DrawCarLayer.LeftWindows).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.LeftWindows, key), list)
        ]
        back_windshield.append(back_windshield[0])
        back_windshield_x = [list[0] for list in back_windshield]
        back_windshield_y = [list[1] for list in back_windshield]
        figures.append(
            go.Scatter(
                x=back_windshield_x,
                y=back_windshield_y,
                fill="toself",  # Fill the shape with color
                line=dict(color="black"),  # Set the color of the exterior lines
                fillcolor="black",  # Set the fill color
                mode="lines",
                legendgroup="Car",
                hoverinfo="skip",
                showlegend=False,
                name="Vehicle - Passat B8 Variant",
            )
        )

        DrawCarLayer.RightWindows.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        back_windshield = [
            DrawCarLayer.RightWindows.get_translated_coord(key)
            for key in vars(DrawCarLayer.RightWindows).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.RightWindows, key), list)
        ]
        back_windshield.append(back_windshield[0])
        back_windshield_x = [list[0] for list in back_windshield]
        back_windshield_y = [list[1] for list in back_windshield]
        figures.append(
            go.Scatter(
                x=back_windshield_x,
                y=back_windshield_y,
                fill="toself",  # Fill the shape with color
                line=dict(color="black"),  # Set the color of the exterior lines
                fillcolor="black",  # Set the fill color
                mode="lines",
                legendgroup="Car",
                hoverinfo="skip",
                showlegend=False,
                name="Vehicle - Passat B8 Variant",
            )
        )
        DrawCarLayer.BackLateralLeftTrim.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        back_windshield = [
            DrawCarLayer.BackLateralLeftTrim.get_translated_coord(key)
            for key in vars(DrawCarLayer.BackLateralLeftTrim).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.BackLateralLeftTrim, key), list)
        ]
        back_windshield.append(back_windshield[0])
        back_windshield_x = [list[0] for list in back_windshield]
        back_windshield_y = [list[1] for list in back_windshield]
        figures.append(
            go.Scatter(
                x=back_windshield_x,
                y=back_windshield_y,
                fill="toself",  # Fill the shape with color
                line=dict(color="orange"),  # Set the color of the exterior lines
                fillcolor="black",  # Set the fill color
                mode="lines",
                legendgroup="Car",
                hoverinfo="skip",
                showlegend=False,
                name="Vehicle - Passat B8 Variant",
            )
        )
        DrawCarLayer.BackLateralRightTrim.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        back_windshield = [
            DrawCarLayer.BackLateralRightTrim.get_translated_coord(key)
            for key in vars(DrawCarLayer.BackLateralRightTrim).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.BackLateralRightTrim, key), list)
        ]
        back_windshield.append(back_windshield[0])
        back_windshield_x = [list[0] for list in back_windshield]
        back_windshield_y = [list[1] for list in back_windshield]
        figures.append(
            go.Scatter(
                x=back_windshield_x,
                y=back_windshield_y,
                fill="toself",  # Fill the shape with color
                line=dict(color="orange"),  # Set the color of the exterior lines
                fillcolor="black",  # Set the fill color
                mode="lines",
                legendgroup="Car",
                hoverinfo="skip",
                showlegend=False,
                name="Vehicle - Passat B8 Variant",
            )
        )
        DrawCarLayer.FrontLeft1Trim.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        back_windshield = [
            DrawCarLayer.FrontLeft1Trim.get_translated_coord(key)
            for key in vars(DrawCarLayer.FrontLeft1Trim).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.FrontLeft1Trim, key), list)
        ]
        back_windshield.append(back_windshield[0])
        back_windshield_x = [list[0] for list in back_windshield]
        back_windshield_y = [list[1] for list in back_windshield]
        figures.append(
            go.Scatter(
                x=back_windshield_x,
                y=back_windshield_y,
                fill="toself",  # Fill the shape with color
                line=dict(color="orange"),  # Set the color of the exterior lines
                fillcolor="black",  # Set the fill color
                mode="lines",
                legendgroup="Car",
                hoverinfo="skip",
                showlegend=False,
                name="Vehicle - Passat B8 Variant",
            )
        )
        DrawCarLayer.FrontLeft2Trim.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        back_windshield = [
            DrawCarLayer.FrontLeft2Trim.get_translated_coord(key)
            for key in vars(DrawCarLayer.FrontLeft2Trim).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.FrontLeft2Trim, key), list)
        ]
        back_windshield.append(back_windshield[0])
        back_windshield_x = [list[0] for list in back_windshield]
        back_windshield_y = [list[1] for list in back_windshield]
        figures.append(
            go.Scatter(
                x=back_windshield_x,
                y=back_windshield_y,
                fill="toself",  # Fill the shape with color
                line=dict(color="orange"),  # Set the color of the exterior lines
                fillcolor="black",  # Set the fill color
                mode="lines",
                legendgroup="Car",
                hoverinfo="skip",
                showlegend=False,
                name="Vehicle - Passat B8 Variant",
            )
        )
        DrawCarLayer.FrontRight1Trim.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        back_windshield = [
            DrawCarLayer.FrontRight1Trim.get_translated_coord(key)
            for key in vars(DrawCarLayer.FrontRight1Trim).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.FrontRight1Trim, key), list)
        ]
        back_windshield.append(back_windshield[0])
        back_windshield_x = [list[0] for list in back_windshield]
        back_windshield_y = [list[1] for list in back_windshield]
        figures.append(
            go.Scatter(
                x=back_windshield_x,
                y=back_windshield_y,
                fill="toself",  # Fill the shape with color
                line=dict(color="orange"),  # Set the color of the exterior lines
                fillcolor="black",  # Set the fill color
                mode="lines",
                legendgroup="Car",
                hoverinfo="skip",
                showlegend=False,
                name="Vehicle - Passat B8 Variant",
            )
        )
        DrawCarLayer.FrontRight2Trim.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        back_windshield = [
            DrawCarLayer.FrontRight2Trim.get_translated_coord(key)
            for key in vars(DrawCarLayer.FrontRight2Trim).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.FrontRight2Trim, key), list)
        ]
        back_windshield.append(back_windshield[0])
        back_windshield_x = [list[0] for list in back_windshield]
        back_windshield_y = [list[1] for list in back_windshield]
        figures.append(
            go.Scatter(
                x=back_windshield_x,
                y=back_windshield_y,
                fill="toself",  # Fill the shape with color
                line=dict(color="orange"),  # Set the color of the exterior lines
                fillcolor="black",  # Set the fill color
                mode="lines",
                legendgroup="Car",
                hoverinfo="skip",
                showlegend=False,
                name="Vehicle - Passat B8 Variant",
            )
        )

        DrawCarLayer.FinalTrim.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        back_windshield = [
            DrawCarLayer.FinalTrim.get_translated_coord(key)
            for key in vars(DrawCarLayer.FinalTrim).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.FinalTrim, key), list)
        ]
        back_windshield.append(back_windshield[0])
        back_windshield_x = [list[0] for list in back_windshield]
        back_windshield_y = [list[1] for list in back_windshield]
        figures.append(
            go.Scatter(
                x=back_windshield_x,
                y=back_windshield_y,
                # fill="toself",  # Fill the shape with color
                line=dict(color="black"),  # Set the color of the exterior lines
                # fillcolor="black",  # Set the fill color
                mode="lines",
                hoverinfo="skip",
                legendgroup="Car",
                showlegend=False,
                name="Vehicle - Passat B8 Variant",
            )
        )
        DrawCarLayer.HeadLightsRight.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        back_windshield = [
            DrawCarLayer.HeadLightsRight.get_translated_coord(key)
            for key in vars(DrawCarLayer.HeadLightsRight).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.HeadLightsRight, key), list)
        ]
        back_windshield.append(back_windshield[0])
        back_windshield_x = [list[0] for list in back_windshield]
        back_windshield_y = [list[1] for list in back_windshield]
        figures.append(
            go.Scatter(
                x=back_windshield_x,
                y=back_windshield_y,
                fill="toself",  # Fill the shape with color
                line=dict(color="black", width=0.1),  # Set the color of the exterior lines
                fillcolor="#FFFD55",  # Set the fill color
                mode="lines",
                legendgroup="Car",
                hoverinfo="skip",
                showlegend=False,
                name="Vehicle - Passat B8 Variant",
            )
        )
        DrawCarLayer.HeadLights.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        back_windshield = [
            DrawCarLayer.HeadLights.get_translated_coord(key)
            for key in vars(DrawCarLayer.HeadLights).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.HeadLights, key), list)
        ]
        back_windshield.append(back_windshield[0])
        back_windshield_x = [list[0] for list in back_windshield]
        back_windshield_y = [list[1] for list in back_windshield]
        figures.append(
            go.Scatter(
                x=back_windshield_x,
                y=back_windshield_y,
                fill="toself",  # Fill the shape with color
                line=dict(color="black", width=0.1),  # Set the color of the exterior lines
                fillcolor="#FFFD55",  # Set the fill color
                mode="lines",
                legendgroup="Car",
                hoverinfo="skip",
                showlegend=False,
                name="Vehicle - Passat B8 Variant",
            )
        )
        DrawCarLayer.RearLightsRight.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        back_windshield = [
            DrawCarLayer.RearLightsRight.get_translated_coord(key)
            for key in vars(DrawCarLayer.RearLightsRight).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.RearLightsRight, key), list)
        ]
        back_windshield.append(back_windshield[0])
        back_windshield_x = [list[0] for list in back_windshield]
        back_windshield_y = [list[1] for list in back_windshield]
        figures.append(
            go.Scatter(
                x=back_windshield_x,
                y=back_windshield_y,
                fill="toself",  # Fill the shape with color
                line=dict(color="black", width=0.1),  # Set the color of the exterior lines
                fillcolor="red",  # Set the fill color
                mode="lines",
                legendgroup="Car",
                hoverinfo="skip",
                showlegend=False,
                name="Vehicle - Passat B8 Variant",
            )
        )
        DrawCarLayer.RearLightsLeft.translate_and_rotate(new_origin_x, new_origin_y, new_yaw)
        back_windshield = [
            DrawCarLayer.RearLightsLeft.get_translated_coord(key)
            for key in vars(DrawCarLayer.RearLightsLeft).keys()
            if not key.startswith("__") and isinstance(getattr(DrawCarLayer.RearLightsLeft, key), list)
        ]
        back_windshield.append(back_windshield[0])
        back_windshield_x = [list[0] for list in back_windshield]
        back_windshield_y = [list[1] for list in back_windshield]
        figures.append(
            go.Scatter(
                x=back_windshield_x,
                y=back_windshield_y,
                fill="toself",  # Fill the shape with color
                line=dict(color="black", width=0.1),  # Set the color of the exterior lines
                fillcolor="red",  # Set the fill color
                mode="lines",
                hoverinfo="skip",
                legendgroup="Car",
                showlegend=False,
                name="Vehicle - Passat B8 Variant",
            )
        )

        return [
            [
                car_x,
                car_y,
            ],  # for global x and y
            figures,
        ]

    class CarCoordinates(DrawCarClassMethods):
        """
        Class containing predefined coordinates for a car.

        All values are in meters.
        """

        sensor_front_side_left = [3.145, 0.895]
        sensor_front_side_left_1 = [3.31, 0.84]
        sensor_front_outer_left = [3.446, 0.730]
        sensor_front_outer_left_2 = [3.61, 0.49]
        sensor_front_inner_left = [3.654, 0.295]
        sensor_front_inner_left_1 = [3.66, 0.27]
        sensor_front_inner_left_2 = [3.67, 0.20]
        sensor_front_inner_left_3 = [3.67, 0.12]
        sensor_front_inner_left_4 = [3.67, -0.12]
        sensor_front_inner_left_5 = [3.67, -0.20]
        sensor_front_inner_left_6 = [3.66, -0.27]
        sensor_front_inner_right = [3.654, -0.295]
        sensor_front_inner_right_2 = [3.61, -0.49]
        sensor_front_outer_right = [3.446, -0.730]
        sensor_front_outer_right_2 = [3.31, -0.84]
        sensor_front_side_right = [3.145, -0.895]

        RIGHT_MIRROR_FRONT_LEFT_CORNER_1 = [2.15, -0.90]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_2 = [2.14, -0.92]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_3 = [2.13, -0.94]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_4 = [2.12, -0.96]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_5 = [2.11, -0.97]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_6 = [2.10, -0.99]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_7 = [2.09, -1.00]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_8 = [2.08, -1.00]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_9 = [2.07, -1.01]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_10 = [2.06, -1.02]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_11 = [2.05, -1.03]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_12 = [2.04, -1.03]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_13 = [2.03, -1.04]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_14 = [2.02, -1.04]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_15 = [2.01, -1.04]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_16 = [2.00, -1.04]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_17 = [1.98, -1.04]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_18 = [1.97, -1.03]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_19 = [1.96, -1.03]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_20 = [1.96, -1.02]
        RIGHT_MIRROR_FRONT_LEFT_CORNER_21 = [1.97, -1.01]
        RIGHT_MIRROR_REAR_LEFT_CORNER = [2.01, -0.90]

        sensor_rear_side_right = [-0.364, -0.888]
        sensor_rear_side_right_1 = [-0.74, -0.81]
        sensor_rear_side_right_2 = [-0.85, -0.77]
        sensor_rear_side_right_3 = [-0.88, -0.74]

        sensor_rear_outer_right = [-0.955, -0.682]
        sensor_rear_outer_righ_1 = [-1.05, -0.51]
        sensor_rear_outer_right_2 = [-1.07, -0.44]

        sensor_rear_inner_right = [-1.09, -0.284]

        sensor_rear_inner_left = [-1.09, 0.284]
        sensor_rear_outer_left_1 = [-1.07, 0.44]
        sensor_rear_outer_left_2 = [-1.05, 0.51]
        sensor_rear_outer_left = [-0.955, 0.682]
        sensor_rear_side_left_1 = [-0.88, 0.74]
        sensor_rear_side_left_2 = [-0.85, 0.77]
        sensor_rear_side_left_3 = [-0.74, 0.81]
        sensor_rear_side_left = [-0.364, 0.888]

        LEFT_MIRROR_REAR_LEFT_CORNER = [2.01, 0.90]
        LEFT_MIRROR_FRONT_LEFT_CORNER_20 = [1.97, 1.01]
        LEFT_MIRROR_FRONT_LEFT_CORNER_19 = [1.96, 1.02]
        LEFT_MIRROR_FRONT_LEFT_CORNER_18 = [1.96, 1.03]
        LEFT_MIRROR_FRONT_LEFT_CORNER_17 = [1.97, 1.03]
        LEFT_MIRROR_FRONT_LEFT_CORNER_16 = [1.98, 1.04]
        LEFT_MIRROR_FRONT_LEFT_CORNER_15 = [2.00, 1.04]
        LEFT_MIRROR_FRONT_LEFT_CORNER_14 = [2.01, 1.04]
        LEFT_MIRROR_FRONT_LEFT_CORNER_13 = [2.02, 1.04]
        LEFT_MIRROR_FRONT_LEFT_CORNER_12 = [2.03, 1.04]
        LEFT_MIRROR_FRONT_LEFT_CORNER_11 = [2.04, 1.03]
        LEFT_MIRROR_FRONT_LEFT_CORNER_10 = [2.05, 1.03]
        LEFT_MIRROR_FRONT_LEFT_CORNER_9 = [2.06, 1.02]
        LEFT_MIRROR_FRONT_LEFT_CORNER_8 = [2.07, 1.01]
        LEFT_MIRROR_FRONT_LEFT_CORNER_7 = [2.08, 1.00]
        LEFT_MIRROR_FRONT_LEFT_CORNER_6 = [2.09, 1.00]
        LEFT_MIRROR_FRONT_LEFT_CORNER_5 = [2.10, 0.99]
        LEFT_MIRROR_FRONT_LEFT_CORNER_4 = [2.11, 0.97]
        LEFT_MIRROR_FRONT_LEFT_CORNER_3 = [2.12, 0.96]
        LEFT_MIRROR_FRONT_LEFT_CORNER_2 = [2.13, 0.94]
        LEFT_MIRROR_FRONT_LEFT_CORNER_1 = [2.14, 0.92]
        LEFT_MIRROR_FRONT_RIGHT_CORNER = [2.15, 0.90]

        _translated_coords = {}

    class Windows(DrawCarClassMethods):
        """Defining the constants for windows"""

        point_a_0 = [1.69, 0.58]
        point_a_0_0 = [2.39, 0.71]
        point_a_1 = [2.410, 0.680]
        point_a_2 = [2.422, 0.609]
        point_a_3 = [2.433, 0.539]
        point_a_4 = [2.442, 0.468]
        point_a_5 = [2.450, 0.397]
        point_a_6 = [2.457, 0.326]
        point_a_7 = [2.462, 0.255]
        point_a_8 = [2.466, 0.184]
        point_a_9 = [2.469, 0.112]
        point_a_9 = [2.469, 0.112]
        point_a_9 = [2.469, 0.112]
        point_a_10 = [2.470, 0.041]
        point_a_11 = [2.470, -0.031]
        point_a_12 = [2.469, -0.102]
        point_a_13 = [2.466, -0.174]
        point_a_14 = [2.462, -0.246]
        point_a_15 = [2.457, -0.318]
        point_a_16 = [2.450, -0.390]
        point_a_17 = [2.442, -0.463]
        point_a_18 = [2.433, -0.535]
        point_a_19 = [2.422, -0.607]
        point_a_20 = [2.410, -0.680]
        a_16 = [2.39, -0.71]
        a_17 = [1.69, -0.58]
        point_b_1 = [1.690, -0.580]
        point_b_2 = [1.695, -0.519]
        point_b_3 = [1.699, -0.458]
        point_b_4 = [1.703, -0.397]
        point_b_5 = [1.707, -0.336]
        point_b_6 = [1.709, -0.275]
        point_b_7 = [1.712, -0.214]
        point_b_8 = [1.713, -0.153]
        point_b_9 = [1.714, -0.092]
        point_b_10 = [1.715, -0.031]
        point_b_11 = [1.715, 0.031]
        point_b_12 = [1.714, 0.092]
        point_b_13 = [1.713, 0.153]
        point_b_14 = [1.712, 0.214]
        point_b_15 = [1.709, 0.275]
        point_b_16 = [1.707, 0.336]
        point_b_17 = [1.703, 0.397]
        point_b_18 = [1.699, 0.458]
        point_b_19 = [1.695, 0.519]
        point_b_20 = [1.690, 0.580]
        # a_18 = [1.74,0.0]
        _translated_coords = {}

    class BackWindow(DrawCarClassMethods):
        """Defining the constants for windows"""

        up_right = [-0.6, 0.54]
        point_bbb_1 = [-0.600, 0.540]
        point_bbb_2 = [-0.605, 0.483]
        point_bbb_3 = [-0.609, 0.426]
        point_bbb_4 = [-0.613, 0.369]
        point_bbb_5 = [-0.617, 0.313]
        point_bbb_6 = [-0.619, 0.256]
        point_bbb_7 = [-0.622, 0.199]
        point_bbb_8 = [-0.623, 0.142]
        point_bbb_9 = [-0.624, 0.085]
        point_bbb_10 = [-0.625, 0.028]
        point_bbb_11 = [-0.625, -0.028]
        point_bbb_12 = [-0.624, -0.085]
        point_bbb_13 = [-0.623, -0.142]
        point_bbb_14 = [-0.622, -0.199]
        point_bbb_15 = [-0.619, -0.256]
        point_bbb_16 = [-0.617, -0.313]
        point_bbb_17 = [-0.613, -0.369]
        point_bbb_18 = [-0.609, -0.426]
        point_bbb_19 = [-0.605, -0.483]
        point_bbb_20 = [-0.600, -0.540]
        down_right = [-0.6, -0.54]

        down_left = [-0.81, -0.65]
        point_bb_1 = [-0.810, -0.650]
        point_bb_2 = [-0.824, -0.582]
        point_bb_3 = [-0.836, -0.513]
        point_bb_4 = [-0.847, -0.445]
        point_bb_5 = [-0.857, -0.376]
        point_bb_6 = [-0.864, -0.308]
        point_bb_7 = [-0.870, -0.239]
        point_bb_8 = [-0.875, -0.171]
        point_bb_9 = [-0.878, -0.103]
        point_bb_10 = [-0.880, -0.034]
        point_bb_11 = [-0.880, 0.034]
        point_bb_12 = [-0.878, 0.103]
        point_bb_13 = [-0.875, 0.171]
        point_bb_14 = [-0.870, 0.239]
        point_bb_15 = [-0.864, 0.308]
        point_bb_16 = [-0.857, 0.376]
        point_bb_17 = [-0.847, 0.445]
        point_bb_18 = [-0.836, 0.513]
        point_bb_19 = [-0.824, 0.582]
        point_bb_20 = [-0.810, 0.650]
        up_left = [-0.81, 0.65]

        _translated_coords = {}

    class LeftWindows(DrawCarClassMethods):
        """Defining the constants for windows"""

        a1 = [2.21, 0.79]
        a2 = [1.42, 0.63]
        a3 = [-0.29, 0.61]
        a4 = [-0.45, 0.71]
        a5 = [-0.30, 0.75]
        a6 = [1.12, 0.80]
        _translated_coords = {}

    class RightWindows(DrawCarClassMethods):
        """Defining the constants for windows"""

        a1 = [2.21, -0.79]
        a2 = [1.42, -0.63]
        a3 = [-0.29, -0.61]
        a4 = [-0.45, -0.71]
        a5 = [-0.30, -0.75]
        a6 = [1.12, -0.80]
        _translated_coords = {}

    class BackLateralLeftTrim(DrawCarClassMethods):
        """Defining the constants for windows"""

        a = [0.23, 0.61]
        a1 = [0.15, 0.78]
        a2 = [0.39, 0.78]
        a3 = [0.35, 0.61]
        _translated_coords = {}

    class BackLateralRightTrim(DrawCarClassMethods):
        """Defining the constants for windows"""

        a4 = [0.23, -0.61]
        a5 = [0.15, -0.78]
        a6 = [0.39, -0.78]
        a7 = [0.35, -0.61]
        _translated_coords = {}

    class FrontLeft1Trim(DrawCarClassMethods):
        """Defining the constants for windows"""

        a = [1.14, 0.625]
        a1 = [1.23, 0.80]
        a34 = [1.15, 0.80]
        aa = [1.08, 0.625]

        _translated_coords = {}

    class FrontLeft2Trim(DrawCarClassMethods):
        """Defining the constants for windows"""

        a = [1.07, 0.625]
        a1 = [1.13, 0.80]

        a2 = [1.07, 0.80]
        a3 = [1.02, 0.625]
        _translated_coords = {}

    class FrontRight1Trim(DrawCarClassMethods):
        """Defining the constants for windows"""

        a = [1.14, -0.625]
        a1 = [1.23, -0.80]
        a34 = [1.15, -0.80]
        aa = [1.08, -0.625]

        _translated_coords = {}

    class FrontRight2Trim(DrawCarClassMethods):
        """Defining the constants for windows"""

        a = [1.07, -0.625]
        a1 = [1.13, -0.80]

        a2 = [1.07, -0.80]
        a3 = [1.02, -0.625]

        _translated_coords = {}

    class HoodTrim(DrawCarClassMethods):
        """Defining the constants for windows"""

        az = [2.39, 0.71]
        sensor_front_outer_left_2 = [3.61, 0.49]
        sensor_front_inner_left = [3.654, 0.295]
        sensor_front_inner_left_1 = [3.66, 0.27]
        sensor_front_inner_left_2 = [3.67, 0.20]
        sensor_front_inner_left_3 = [3.67, 0.12]
        sensor_front_inner_left_4 = [3.67, -0.12]
        sensor_front_inner_left_5 = [3.67, -0.20]
        sensor_front_inner_left_6 = [3.66, -0.27]

        sensor_front_inner_right = [3.654, -0.295]
        sensor_front_inner_right_2 = [3.61, -0.49]

        azz = [2.39, -0.71]

        _translated_coords = {}

        @classmethod
        def translate_and_rotate(cls, new_x, new_y, yaw):
            """
            Translates and rotates all coordinates based on the ego position and yaw angle.

            Parameters:
            - new_x: The new X origin coordinate
            - new_y: The new Y origin coordinate
            - yaw: Rotation angle in radians
            """
            # Create the rotation matrix
            rotation_matrix = np.array([[np.cos(yaw), -np.sin(yaw)], [np.sin(yaw), np.cos(yaw)]])

            # Apply translation and rotation to each point
            for attr, value in cls.__dict__.items():
                if isinstance(value, list):  # Only process the coordinates
                    ##########TODO
                    # THIS ROTATES THE POINTS, but the measurement looks bad
                    point = np.array(value)

                    # First, apply the rotation to the point relative to origin (0,0)
                    rotated_point = rotation_matrix @ point

                    # Then, translate the rotated point to the new origin
                    final_point = rotated_point + np.array([new_x, new_y])

                    # Store the transformed coordinates
                    cls._translated_coords[attr] = final_point.tolist()

        @classmethod
        def get_translated_coord(cls, point_name):
            """
            Returns the translated and rotated coordinates for a specific point.

            Parameters:
            - point_name: The name of the point (as string).

            Returns:
            - Transformed coordinates as a list [x, y].
            """
            return cls._translated_coords.get(point_name)

    class HeadLights(DrawCarClassMethods):
        """Defining the constants for windows"""

        sensor_front_outer_left = [3.43, 0.730]
        sensor_front_outer_left_2 = [3.60, 0.50]
        sensor_front_outer_left_3 = [3.56, 0.50]
        sensor_front_outer_left45 = [3.342, 0.730]
        _translated_coords = {}

    class HeadLightsRight(DrawCarClassMethods):
        """Defining the constants for windows"""

        sensor_front_outer_left = [3.43, -0.730]
        sensor_front_outer_left_2 = [3.60, -0.50]
        sensor_front_outer_left_3 = [3.56, -0.50]
        sensor_front_outer_left45 = [3.342, -0.730]
        _translated_coords = {}

    class RearLightsRight(DrawCarClassMethods):
        """Defining the constants for windows"""

        point_1 = [-0.68, -0.78]
        # point_mid_1_2 = [-0.85,-0.76]
        point_2 = [-0.80, -0.76]
        point_3 = [-0.94, -0.60]
        point_4 = [-0.90, -0.60]
        point_5 = [-0.83, -0.69]
        point_6 = [-0.72, -0.74]
        _translated_coords = {}

    class RearLightsLeft(DrawCarClassMethods):
        """Defining the constants for windows"""

        point_1 = [-0.68, 0.78]
        point_2 = [-0.80, 0.76]
        point_3 = [-0.94, 0.60]
        point_4 = [-0.90, 0.60]
        point_5 = [-0.83, 0.69]
        point_6 = [-0.72, 0.74]
        _translated_coords = {}

    class FinalTrim(DrawCarClassMethods):
        """Defining the constants for windows"""

        up_right = [-0.6, 0.54]
        windshield_top_left = [1.69, 0.58]
        center_windshield = [1.88, 0.0]
        windshield_down_left = [1.69, -0.58]
        down_right = [-0.6, -0.54]
        center_right = [-0.70, 0.0]
        _translated_coords = {}


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


class SilCl:
    """SiL CL related constants"""

    class PDWConstants:
        """SiL CL PDW related constants"""

        REACTION_TOLERANCE = 3  # s
        VEH_STANDSTILL = 0.001  # m/s
        delay = 60  # 600ms
        delay_wait = 10  # 100ms

        class PDWResetCondition:
            """Defining constants for PDW reset conditions in case of auto-activation"""

            RESET_CONDITION_FALSE = 0
            RESET_CONDITION_TRUE = 1

        class pdwState:
            """Defining constants for PDW state"""

            PDW_INT_STATE_INIT = 0
            PDW_INT_STATE_ACT_BTN = 1
            PDW_INT_STATE_ACT_R_GEAR = 2
            PDW_INT_STATE_ACT_AP = 3
            PDW_INT_STATE_ACT_AUTO = 4
            PDW_INT_STATE_ACT_ROLLBACK = 5
            PDW_INT_STATE_ACT_RA = 6
            PDW_INT_STATE_DEACT_INIT = 7
            PDW_INT_STATE_DEACT_BTN = 8
            PDW_INT_STATE_DEACT_SPEED = 9
            PDW_INT_STATE_DEACT_P_GEAR = 10
            PDW_INT_STATE_DEACT_EPB = 11
            PDW_INT_STATE_DEACT_AP_FIN = 12
            PDW_INT_STATE_FAILURE = 13
            PDW_INT_NUM_STATES = 14

        class pdwSystemState:
            """Defining constants for PDW system state"""

            PDW_INIT = 0
            PDW_OFF = 1
            PDW_ACTIVATED_BY_R_GEAR = 2
            PDW_ACTIVATED_BY_BUTTON = 3
            PDW_AUTOMATICALLY_ACTIVATED = 4
            PDW_FAILURE = 5

        class pdwUserActionHeadUnit:
            """Defining constants for HMI button related to PDW"""

            TAP_ON_START_SELECTION = 17
            TAP_ON_START_PARKING = 18
            TAP_ON_PDC = 35

        class EPBSwitch:
            """Defining constants for Electornic Parking Brake"""

            EPB_ON = 1
            EPB_OFF = 0

        class DrivingTubeReq:
            """Defining constants for Driving Tube"""

            PDC_DRV_TUBE_NONE = 0
            PDC_DRV_TUBE_FRONT = 1
            PDC_DRV_TUBE_REAR = 2

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

        class pdwFailure:
            """Defining constants for PDW Failure"""

            PDW_FAILURE_TRUE = 1
            PDW_FAILURE_FALSE = 0

        class WheelDirection:
            """Defining constants for wheel directions"""

            WHEEL_DIRECTION_NONE = 0
            WHEEL_DIRECTION_FORWARD = 1
            WHEEL_DIRECTION_REVERSE = -1

        class PDWSpeedThreshold:
            """Defining speed threshold for PDW"""

            SPEED_THRESHOLD_LO = 0.1  # m/s
            SPEED_THRESHOLD_HI = 20 / 3.6  # m/s

        class PDWSectorLength:
            """Defining PDW sector Length"""

            PDW_SECTOR_LENGTH = 2.55  # m
            PDW_GREEN_ZONE = (1.7, 2.55)  # m
            PDW_YELLOW_ZONE = (0.85, 1.7)  # m
            PDW_RED_ZONE = 0.85  # m
            SLICE_LENGTH = 2.55 / 9  # m

        class IntersectsDrvTube:
            """Defining the values of intersectsDrvTube"""

            INTERSECTS = 1
            NOT_INTERSECTS = 0

        class ReduceToMute:
            """Defining the reduce to mute signals"""

            MUTE_STEP = 1
            CONTINUOUS_TIME = 500  # ms
            INTERMITTENT_TIME = 300  # ms
            STEP_TIME = 50  # ms
            PDW_REDUCE_NONE = 0
            PDW_REDUCE_LVL1 = 1
            PDW_REDUCE_LVL2 = 2
            PDW_REDUCE_LVL3 = 3
            PDW_REDUCE_LVL4 = 4


class CurbDetectionKpi:
    """Defining the constants regarding the Curb Detection KPI"""

    THRESHOLD = 1.92
    FORWARD_SENSOR_LIST = [2, 3]
    BACKWARD_SENSOR_LIST = [8, 9]


class ActiveManeuveringFunction(GetVariableName):
    """Constants for Active Maneuvering Function"""

    FUNCTION_NONE = 0
    FUNCTION_COLLISION_WARNING = 1
    FUNCTION_LSCA = 2
    FUNCTION_AUTOMATED_PARKING = 3
    FUNCTION_TRAILER_HITCH_ASSIST = 4
    FUNCTION_TRAILER_REVERSE_ASSIST = 5
    FUNCTION_TRAINED_PARKING = 6
    FUNCTION_AVGA = 7
    MAX_NUM_MANEUVERING_FUNCTIONS = 8


class AUPConstants:
    """Defining the constants regarding the AUP tests"""

    AP_G_MAX_INTERRUPT_TIME_S = 60  # s
    AP_G_V_SCANNING_THRESH_ON_MPS = 10.60  # m/s
    AP_G_V_SCANNING_THRESH_OFF_MPS = 11.250  # m/s
    AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR = 15  # bar
    AP_G_THROTTLE_THRESH_PERC = 10  # %
    AP_G_MAX_TIME_REM_DISCONNECT_S = 1  # s
    AP_G_TCS_TIME_THRESH_S = 0.5  # s
    AP_G_ESC_TIME_THRESH_S = 0.5  # s
    AP_G_ABS_TIME_THRESH_S = 0.5  # s
    AP_G_EBD_TIME_THRESH_S = 0.5  # s

    class LODMC_SYSTEM_STATE:
        """Defining the constants regarding the guidance request
        SignalManipulation.loDMCStatusPort_loDMCSystemState_nu
        """

        LODMC_NOT_AVAILABLE = 0
        LODMC_INITIALISATION = 1
        LODMC_AVAILABLE = 2
        LODMC_CTRL_ACTIVE = 3
        LODMC_CANCEL_BY_DRIVER = 4
        LODMC_ERROR = 7

    class LADMC_SYSTEM_STATE:
        """Defining the constants regarding the guidance request
        SignalManipulation.laDMCStatusPort_laDMCSystemState_nu
        """

        LADMC_NOT_AVAILABLE = 0
        LADMC_INITIALISATION = 1
        LADMC_AVAILABLE = 2
        LADMC_CTRL_ACTIVE = 3
        LADMC_CANCEL_BY_DRIVER = 4
        LADMC_ERROR = 7

    class GUIDANCE_REQUEST:
        """Defining the constants regarding the guidance request
        AP.avgaGuidanceRequestPort.automatedVehicleGuidanceRequest
        """

        AVGA_NONE = 0
        AVGA_BRAKING_SUPERVISION = 1
        AVGA_BRAKING_VISUAL_SUPERVISION = 2
        AVGA_BRAKING_AUDIO_VISUAL_SUPERVISION = 3

    class FINISH_TYPE:
        """Defining the constants regarding the finish type
        AP.apUserInformationPort.finishType_nu:
        """

        AP_NOT_FINISHED = 0
        AP_SUCCESS = 1
        AP_SUCCESS_FALLBACK = 2
        AP_CANCELED = 3

    class PLANNING_SPECIFICATION:
        """Defining the constants regarding the planning specification
        AP.planningCtrlPort.apPlanningSpecification:
        """

        APPS_INVALID = 0
        APPS_NONE = 1
        APPS_PARK_IN_FULL_MANEUVERING_AREA = 2
        APPS_PARK_IN_RESTRICTED_MANEUVERING_AREA = 3
        APPS_PARK_OUT_UNTIL_CRITICAL_POINT_REACHED = 4
        APPS_PARK_OUT_TO_TARGET_POSE = 5

    class SCREEN_NU:
        """Defining the constants regarding head unit visu port screen signal:
        AP.headUnitVisualizationPort.screen_nu
        """

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

    class STD_REQUEST:
        """Defining the constants regarding the std request
        AP.CtrlCommandPort.stdRequest_nu:
        """

        STD_REQ_NO_REQUEST = 0
        STD_REQ_INIT = 1
        STD_REQ_SCAN = 2
        STD_REQ_PREPARE = 3
        STD_REQ_DEGRADE = 4
        STD_REQ_START = 5
        STD_REQ_PAUSE = 6
        STD_REQ_SECURE = 7
        STD_REQ_FINISH = 8
        STD_REQ_ERROR = 9

    class RM_STATE:
        """Defining the constants regarding the RM state
        AP.planningCtrlPort.rmState:
        """

        RM_INACTIVE = 0
        RM_SCANNING = 1
        RM_AVG_ACTIVE = 2
        RM_AVG_PAUSED = 3
        RM_AVG_FINISHED = 4

    class PARKING_MODE:
        """Defining the constants regarding the PPC parking modes
        AP.CtrlCommandPort.ppcParkingMode_nu:
        """

        PARKING_MODE_NOT_VALID = 0
        PARK_IN = 1
        PARK_OUT = 2
        GARAGE_PARKING_IN = 3
        GARAGE_PARKING_OUT = 4
        TRAINED_PARKING_TRAIN = 5
        TRAINED_PARKING_EXEC = 6
        REMOTE_MANEUVERING = 7
        MEMORY_PARKING_TRAIN = 8
        MEMORY_PARKING_EXEC = 9
        UNDO_MANEUVER = 10
        REVERSE_ASSIST_ACTIVE = 11

    class REMOTE_DEVICE:
        """Defining the constants regarding user action remote device:
        AP.remoteHMIOutputPort.userActionRemoteDeviceCMQuant_nu
        """

        REM_NO_USER_ACTION = 0
        REM_TAP_ON_PARKING_SPACE_1 = 1
        REM_TAP_ON_PARKING_SPACE_2 = 2
        REM_TAP_ON_PARKING_SPACE_3 = 3
        REM_TAP_ON_PARKING_SPACE_4 = 4
        REM_APP_STARTED = 16
        REM_APP_CLOSED = 17
        REM_TAP_ON_START_PARKING = 18
        REM_TAP_ON_INTERRUPT = 19
        REM_TAP_ON_CONTINUE = 20
        REM_TAP_ON_UNDO = 21
        REM_TAP_ON_CANCEL = 22
        REM_TAP_ON_REDO = 23
        REM_TAP_ON_PARK_IN = 24
        REM_TAP_ON_PARK_OUT = 25
        REM_TAP_ON_REM_MAN = 26
        REM_TAP_ON_REM_SV = 27
        REM_TAP_ON_REM_FWD = 28
        REM_TAP_ON_REM_BWD = 29
        REM_TAP_ON_PREVIOUS_SCREEN = 30
        REM_TAP_ON_GP = 31
        REM_TAP_ON_SWITCH_TO_HEAD_UNIT = 32

    class CORE_STATUS:
        """
        Defining the constants regarding the core status
        AP.PARKSMCoreStatusPort.parksmCoreState_nu:
        """

        CORE_INIT = 0
        CORE_SCANNING = 1
        CORE_PARKING = 2
        CORE_PAUSE = 3
        CORE_FINISH = 4
        CORE_ERROR = 5

    class ACC_STATUS:
        """
        Defining the constants regarding the ACC status
        SignalManipulation.accInformationPort_accStatus_nu:
        """

        ACC_OFF = 0
        ACC_INIT = 1
        ACC_STANDBY = 2
        ACC_ACTIVE = 3
        ACC_OVERRIDE = 4
        ACC_TURN_OFF = 5
        ACC_ERROR_REVERSIBLE = 6
        ACC_ERROR_IRREVERSIBLE = 7

    class TCS_STATE:
        """
        Defining the constants regarding the TCS state
        SignalManipulation.escInformationPort_tcsState_nu:
        """

        TCS_INACTIVE = 0
        TCS_ACTIVE = 1
        TCS_ERROR = 2

    class ESC_STATE:
        """
        Defining the constants regarding the ESC state
        SignalManipulation.escInformationPort_ecsState_nu:
        """

        ESC_INACTIVE = 0
        ESC_ACTIVE = 1
        ESC_ERROR = 2

    class ABS_STATE:
        """
        Defining the constants regarding the ABS state
        SignalManipulation.escInformationPort_absState_nu:
        """

        ABS_INACTIVE = 0
        ABS_ACTIVE = 1
        ABS_ERROR = 2

    class EBD_STATE:
        """
        Defining the constants regarding the EBD state
        SignalManipulation.escInformationPort_ebdState_nu:
        """

        EBD_INACTIVE = 0
        EBD_ACTIVE = 1
        EBD_ERROR = 2

    class REACHED_STATUS:
        """
        Defining the constants regarding the position reached status
        AP.targetPosesPort.selectedPoseData.reachedStatus:
        """

        NO_TP_REACHED_STATUS = 0
        TP_REACHED = 1
        TP_REACHED_FALLBACK = 2
        TP_NOT_REACHED = 3
        MAX_NUM_POSE_REACHED_STATUS_TYPES = 4

    class DRIVING_MODE:
        """
        Defining the constants regarding the driving mode
        AP.trajCtrlRequestPort.drivingModeReq_nu:
        """

        NO_INTERVENTION = 0
        FOLLOW_TRAJ = 1
        MAKE_PAUSE = 2
        MAKE_SECURE = 3
        MAKE_SECURE_AND_ADJUST_ANGLE = 4

    class ESM_STATE:
        """
        Defining the constants regarding the ESM state
        AP.psmDebugPort.stateVarESM_nu:
        """

        ESM_INACTIVE = 0
        ESM_NO_ERROR = 1
        ESM_REVERSIBLE_ERROR = 2
        ESM_IRREVERSIBLE_ERROR = 3

    class PPC_STATE:
        """
        Defining the constants regarding the PPC state
        AP.psmDebugPort.stateVarPPC_nu:
        """

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

    class USER_ACTION(GetVariableName):
        """
        Defining the constants regarding the user action
        AP.hmiOutputPort.userActionHeadUnit_nu
        """

        NO_USER_ACTION = 0
        TAP_ON_PARKING_SPACE_LEFT_1 = 1
        TAP_ON_PARKING_SPACE_LEFT_2 = 2
        TAP_ON_PARKING_SPACE_LEFT_3 = 3
        TAP_ON_PARKING_SPACE_LEFT_4 = 4
        TAP_ON_PARKING_SPACE_RIGHT_1 = 5
        TAP_ON_PARKING_SPACE_RIGHT_2 = 6
        TAP_ON_PARKING_SPACE_RIGHT_3 = 7
        TAP_ON_PARKING_SPACE_RIGHT_4 = 8
        TAP_ON_PARKING_SPACE_FRONT_1 = 9
        TAP_ON_PARKING_SPACE_FRONT_2 = 10
        TAP_ON_PARKING_SPACE_FRONT_3 = 11
        TAP_ON_PARKING_SPACE_FRONT_4 = 12
        TAP_ON_PARKING_SPACE_REAR_1 = 13
        TAP_ON_PARKING_SPACE_REAR_2 = 14
        TAP_ON_PARKING_SPACE_REAR_3 = 15
        TAP_ON_PARKING_SPACE_REAR_4 = 16
        TAP_ON_START_SELECTION = 17
        TAP_ON_START_PARKING = 18
        TAP_ON_INTERRUPT = 19
        TAP_ON_CONTINUE = 20
        TAP_ON_UNDO = 21
        TAP_ON_CANCEL = 22
        TAP_ON_REDO = 23
        TAP_ON_START_REMOTE_PARKING = 24
        TAP_ON_SWITCH_DIRECTION = 25
        TAP_ON_SWITCH_ORIENTATION = 26
        TAP_ON_PREVIOUS_SCREEN = 27
        TOGGLE_AP_ACTIVE = 28
        TAP_ON_FULLY_AUTOMATED_PARKING = 30
        TAP_ON_SEMI_AUTOMATED_PARKING = 31
        TAP_ON_START_KEY_PARKING = 32
        TAP_ON_GP = 33
        TAP_ON_RM = 34
        TAP_ON_PDC = 35
        TAP_ON_AP_PDC_TOGGLE_VIEW = 36
        TAP_ON_SWITCH_TO_REMOTE_KEY = 37
        TAP_ON_SWITCH_TO_REMOTE_APP = 38
        TAP_ON_WHP = 39
        TAP_ON_USER_SLOT_LEFT_PAR = 40
        TAP_ON_USER_SLOT_LEFT_PERP_BWD = 41
        TAP_ON_USER_SLOT_LEFT_PERP_FWD = 42
        TAP_ON_USER_SLOT_RIGHT_PAR = 43
        TAP_ON_USER_SLOT_RIGHT_PERP_BWD = 44
        TAP_ON_USER_SLOT_RIGHT_PERP_FWD = 45
        TAP_ON_USER_SLOT_MOVE_UP = 46
        TAP_ON_USER_SLOT_MOVE_DOWN = 47
        TAP_ON_USER_SLOT_MOVE_LEFT = 48
        TAP_ON_USER_SLOT_MOVE_RIGHT = 49
        TAP_ON_USER_SLOT_ROT_CLKWISE = 50
        TAP_ON_USER_SLOT_ROT_CTRCLKWISE = 51
        TAP_ON_USER_SLOT_RESET = 52
        TAP_ON_USER_SLOT_SAVE = 53
        TAP_ON_EXPLICIT_SCANNING = 54
        TAP_ON_REVERSE_ASSIST = 55
        TAP_ON_MUTE = 56
        TAP_ON_MEMORY_PARKING = 57
        TAP_ON_MEMORY_SLOT_1 = 58
        TAP_ON_MEMORY_SLOT_2 = 59
        TAP_ON_MEMORY_SLOT_3 = 60

    class AP_STATES:
        """
        Defining the constants regarding the AP states
        AP.planningCtrlPort.apStates
        """

        AP_INACTIVE = 0
        AP_SCAN_IN = 1
        AP_SCAN_OUT = 2
        AP_AVG_ACTIVE_IN = 3
        AP_AVG_ACTIVE_OUT = 4
        AP_AVG_PAUSE = 5
        AP_AVG_UNDO = 6
        AP_ACTIVE_HANDOVER_AVAILABLE = 7
        AP_AVG_FINISHED = 8

    class SEAT_OCCUPANCY:
        """
        Defining the constants regarding the seat occupancy
        SignalManipulation.vehicleOccupancyStatusPort_seatOccupancyStatus_driver_nu
        """

        OCC_STATUS_NOT_INSTALLED = 0
        OCC_STATUS_NOT_AVAILABLE = 1
        OCC_STATUS_FREE = 2
        OCC_STATUS_OCCUPIED = 3

    class HMI_MESSAGE:
        """
        Defining the constants regarding the user information
        AP.apUserInformationPort.generalUserInformation_nu:
        """

        NO_MESSAGE = 0
        VERY_CLOSE_TO_OBJECTS = 1
        START_PARKING_IN = 2
        PARKING_IN_FINISHED = 3
        PARKING_CANCELLED = 4
        PARKING_FAILED = 5
        SHIFT_TO_R = 6
        SHIFT_TO_D = 7
        SHIFT_TO_1 = 8
        RELEASE_BRAKE = 9
        START_PARKING_OUT = 10
        PARKING_OUT_FINISHED = 11
        START_REM_MAN = 12
        REM_MAN_OBSTACLE_STOP = 13
        REDUCE_DISTANCE_TO_VEHICLE = 14
        CLOSE_DOOR_OR_START_REMOTE = 15
        RELEASE_HANDBRAKE = 16
        LEAVE_VEHICLE = 17
        NO_DRIVER_DETECTED_ON_SEAT = 18
        INTERNAL_SYSTEM_ERROR = 19
        PARKING_OUT_HANDOVER = 20
        STEERING_ACTIVE = 21
        STOP = 22
        MAX_WAITING_TIME_EXCEEDED = 23
        SHIFT_TO_P = 24
        SHIFT_TO_N = 25
        SELECT_PARKING_VARIANT = 26
        NO_REMOTE_DEVICE_PAIRED = 27
        NO_REMOTE_DEVICE_CONNECTED = 28
        PARKING_CANCELLED_THROTTLE = 29
        PARKING_CANCELLED_STEER = 30
        GARAGE_NOT_OPEN = 31
        UNDO_FINISHED = 32
        LOW_ENERGY = 33
        WAIT = 34
        SLOW_DOWN = 35
        KEY_NOT_IN_RANGE = 36
        KEY_NOT_ALIVE = 37
        PARKING_IN_FINISHED_FALLBACK = 38
        PARKING_OUT_FINISHED_FALLBACK = 39
        REVERSE_ASSIST_FINISHED = 40
        REVERSE_ASSIST_CANCELLED = 41
        REVERSE_ASSIST_FAILED = 42
        FRONT_CAM_VISION_UNRELIABLE = 43
        REAR_CAM_VISION_UNRELIABLE = 44
        LEFT_CAM_VISION_UNRELIABLE = 45
        RIGHT_CAM_VISION_UNRELIABLE = 46
        FRONT_CAM_PRE_PROC_UNRELIABLE = 47
        REAR_CAM_PRE_PROC_UNRELIABLE = 48
        LEFT_CAM_PRE_PROC_UNRELIABLE = 49
        RIGHT_CAM_PRE_PROC_UNRELIABLE = 50
        FRONT_ULTRASONICS_UNRELIABLE = 51
        REAR_ULTRASONICS_UNREALIBLE = 52
        HOST_TEMPERATURE_WARNING = 53
        VEHICLE_COMMUNICATION_ERROR = 54
        MEMORY_PARKING_FINISHED = 55
        MEMORY_PARKING_CANCELLED = 56
        MEMORY_PARKING_FAILED = 57
        MEMORY_PARKING_REFINE = 58
        PARKING_SLOT_FOUND = 59
        DRIVER_IN_OUT_SELECTION = 60
        PARKING_RESUMED = 61
        PARKING_TIMER_EXCEEDED = 62
        DMS_TIMER_EXCEEDED = 63
        PARK_BRAKE_ENGAGED = 64
        REFERENCE_VEHICLE_MOVED = 65
        PRESS_BRAKE_PEDAL = 66
        STEEP_ROAD = 67
        POOR_LIGHTING = 68
        NO_VISIBILTY = 69
        AVG_SPPED_HIGH = 70
        SPACE_CONSTRAINT = 71
        SYSTEM_FAILURE = 72
        ORVM_MANUAL_HANDLING = 73
        ONLY_SAFETY_CORE_AVAILABLE = 74
        ODOMETRY_UNRELIABLE = 75
        ENV_MODEL_STATIC_OBJS_UNRELIABLE = 76
        ENV_MODEL_TRAFFIC_PARTICIPANTS_UNRELIABLE = 77
        ENV_MODEL_PARKING_FEATURES_UNRELIABLE = 78
        LOCALIZATION_UNRELIABLE = 79
        PDW_UNRELIABLE = 80
        LSCA_UNRELIABLE = 81
        RA_UNRELIABLE = 82
        HV_UNRELIABLE = 83
        AVGA_FAILED = 84
        MF_MANAGER_FAILED = 85
        MOCO_FAILED = 86
        FRONT_CAM_BLOCKAGE = 87
        REAR_CAM_BLOCKAGE = 88
        LEFT_CAM_BLOCKAGE = 89
        RIGHT_CAM_BLOCKAGE = 90
        HMI_COMMUNICATION_ERROR = 91
        PARKING_ABORT_ESP_EPAS = 92
        PARKING_ABORT_UNESSENTIAL_GEAR = 93
        PARKING_ABORT_UNESSENTIAL_INDICATOR = 94
        PARKING_STROKES_EXCEEDED = 95
        PARKINGIN_MANUALLY = 96
        AVGA_INTERVENTION = 97
        DRIVER_NOT_STRAPPED = 98
        PASSENGER_NOT_STRAPPED = 99

    class DOOR_DRIVER:
        """
        Defining the constants regarding the driver door status
        AP.doorStatusPort.status.driver_nu
        """

        DOOR_STATUS_INIT = 0
        DOOR_STATUS_OPEN = 1
        DOOR_STATUS_CLOSED = 2
        DOOR_STATUS_LOCKED = 3
        DOOR_STATUS_ERROR = 4

    class BELT_DRIVER:
        """
        Defining the constants regarding the driver belt status
        AP.vehicleOccupancyStatusPort.beltBuckleStatus.driver_nu
        """

        BELT_STATUS_NOT_INSTALLED = 0
        BELT_STATUS_NOT_AVAILABLE = 1
        BELT_STATUS_OPEN = 2
        BELT_STATUS_LOCKED = 3

    class STATE_VAR_DM:
        """
        Defining the constants regarding the state variable DM
        AP.psmDebugPort.stateVarDM_nu
        """

        DM_INACTIVE = 0
        DM_DRIVER_MANEUVERING = 1
        DM_DRIVER_ASSISTS_AP_MANEUVER = 2
        DM_DRIVER_NOT_MANEUVERING = 3
        DM_PASSENGER_IN_VEHICLE = 4
        DM_NOONE_IN_VEHICLE = 5

    #  AP.PARKSMCoreStatusPort.parksmCoreState_nu:
    CORE_INIT = 0
    CORE_SCANNING = 1
    CORE_PARKING = 2
    CORE_PAUSE = 3
    CORE_FINISH = 4
    CORE_ERROR = 5

    #  AP.trajCtrlRequestPort.drivingModeReq_nu:
    NO_INTERVENTION = 0
    FOLLOW_TRAJ = 1
    MAKE_PAUSE = 2
    MAKE_SECURE = 3
    MAKE_SECURE_AND_ADJUST_ANGLE = 4

    # AP.hmiOutputPort.userActionHeadUnit_nu

    TAP_ON_CANCEL = 20
    TAP_ON_START_PARKING = 18
    NO_USER_ACTION = 0

    # AP.planningCtrlPort.apStates
    AP_INACTIVE = (0,)
    AP_SCAN_IN = (1,)
    AP_SCAN_OUT = (2,)
    AP_AVG_ACTIVE_IN = (3,)
    AP_AVG_ACTIVE_OUT = (4,)
    AP_AVG_PAUSE = (5,)
    AP_AVG_UNDO = (6,)
    AP_ACTIVE_HANDOVER_AVAILABLE = (7,)
    AP_AVG_FINISHED = 8

    DOOR_STATUS_INIT = 0
    DOOR_STATUS_OPEN = 1
    DOOR_STATUS_CLOSED = 2
    DOOR_STATUS_LOCKED = 3
    DOOR_STATUS_ERROR = 4


class LSCAState(GetVariableName):
    """Defining the constants regarding the LSCA state"""

    LSCA_STATE_DEACTIVATED = 0
    LSCA_STATE_ACTIVATED = 1
    LSCA_STATE_INTERVENTION = 2
    LSCA_STATE_ERROR = 3


class UiManager:
    """Defining the constants regarding the user interface manager"""

    PDW_DEFAULT_MINIMUM_DISTANCE = 2.55  # m

    class HmiScreen(GetVariableName):
        """Defining the constants regarding the HMI screen"""

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
        PDC_ACTIVE = 17
        GP_START = 18
        GP_MANEUVER_ACTIVE = 19
        DIAG_ERROR = 20

    class HmiMessage(GetVariableName):
        """Defining the constants regarding the HMI message"""

        NO_MESSAGE = 0
        VERY_CLOSE_TO_OBJECTS = 1
        START_PARKING_IN = 2
        PARKING_IN_FINISHED = 3
        PARKING_CANCELLED = 4
        PARKING_FAILED = 5
        SHIFT_TO_R = 6
        SHIFT_TO_D = 7
        SHIFT_TO_1 = 8
        RELEASE_BRAKE = 9
        START_PARKING_OUT = 10
        PARKING_OUT_FINISHED = 11
        START_REM_MAN = 12
        REM_MAN_OBSTACLE_STOP = 13
        REDUCE_DISTANCE_TO_VEHICLE = 14
        CLOSE_DOOR_OR_START_REMOTE = 15
        RELEASE_HANDBRAKE = 16
        LEAVE_VEHICLE = 17
        NO_DRIVER_DETECTED_ON_SEAT = 18
        INTERNAL_SYSTEM_ERROR = 19
        PARKING_OUT_HANDOVER = 20
        STEERING_ACTIVE = 21
        STOP = 22
        MAX_WAITING_TIME_EXCEEDED = 23
        SHIFT_TO_P = 24
        SHIFT_TO_N = 25
        SELECT_PARKING_VARIANT = 26
        NO_REMOTE_DEVICE_PAIRED = 27
        NO_REMOTE_DEVICE_CONNECTED = 28
        PARKING_CANCELLED_THROTTLE = 29
        PARKING_CANCELLED_STEER = 30
        GARAGE_NOT_OPEN = 31
        UNDO_FINISHED = 32
        LOW_ENERGY = 33
        WAIT = 34
        SLOW_DOWN = 35
        KEY_NOT_IN_RANGE = 36
        KEY_NOT_ALIVE = 37
        PARKING_IN_FINISHED_FALLBACK = 38
        PARKING_OUT_FINISHED_FALLBACK = 39
        REVERSE_ASSIST_FINISHED = 40
        REVERSE_ASSIST_CANCELLED = 41
        REVERSE_ASSIST_FAILED = 42
        DIAG_USS_1_NOT_RUNNING = 43
        DIAG_USS_2_NOT_RUNNING = 44
        DIAG_USS_3_NOT_RUNNING = 45
        DIAG_USS_4_NOT_RUNNING = 46
        DIAG_USS_5_NOT_RUNNING = 47
        DIAG_USS_6_NOT_RUNNING = 48
        DIAG_USS_7_NOT_RUNNING = 49
        DIAG_USS_8_NOT_RUNNING = 50
        DIAG_USS_9_NOT_RUNNING = 51
        DIAG_USS_10_NOT_RUNNING = 52
        DIAG_USS_11_NOT_RUNNING = 53
        DIAG_USS_12_NOT_RUNNING = 54
        MEMORY_PARKING_FINISHED = 55
        MEMORY_PARKING_CANCELLED = 56
        MEMORY_PARKING_FAILED = 57

    class PDCUserActionHeadUnit(GetVariableName):
        """Defining the constants regarding the PDC user action head unit"""

        PDC_NO_USER_ACTION = 0
        PDC_TAP_ON_ACT_DEACT_BTN = 1
        PDC_TAP_ON_MUTE_BTN = 2

    class UserAction(GetVariableName):
        """Defining the constants regarding HmiCommands"""

        TAP_ON_HIDE_PDW = 100
        TAP_ON_LSCA = 65
        TAP_ON_LVMD = 64
        TAP_ON_USER_SLOT_DEFINE = 63
        TAP_ON_USER_SLOT_CLOSE = 62
        TAP_ON_USER_SLOT_REFINE = 61
        TAP_ON_MEMORY_SLOT_3 = 60
        TAP_ON_MEMORY_SLOT_2 = 59
        TAP_ON_MEMORY_SLOT_1 = 58
        TAP_ON_MEMORY_PARKING = 57
        TAP_ON_MUTE = 56
        TAP_ON_REVERSE_ASSIST = 55
        TAP_ON_EXPLICIT_SCANNING = 54
        TAP_ON_USER_SLOT_SAVE = 53
        TAP_ON_USER_SLOT_RESET = 52
        TAP_ON_USER_SLOT_ROT_CTRCLKWISE = 51
        TAP_ON_USER_SLOT_ROT_CLKWISE = 50
        TAP_ON_USER_SLOT_MOVE_RIGHT = 49
        TAP_ON_USER_SLOT_MOVE_LEFT = 48
        TAP_ON_USER_SLOT_MOVE_DOWN = 47
        TAP_ON_USER_SLOT_MOVE_UP = 46
        TAP_ON_USER_SLOT_RIGHT_PERP_FWD = 45
        TAP_ON_USER_SLOT_RIGHT_PERP_BWD = 44
        TAP_ON_USER_SLOT_RIGHT_PAR = 43
        TAP_ON_USER_SLOT_LEFT_PERP_FWD = 42
        TAP_ON_USER_SLOT_LEFT_PERP_BWD = 41
        TAP_ON_USER_SLOT_LEFT_PAR = 40
        TAP_ON_WHP = 39
        TAP_ON_SWITCH_TO_REMOTE_APP = 38
        TAP_ON_SWITCH_TO_REMOTE_KEY = 37
        TAP_ON_AP_PDC_TOGGLE_VIEW = 36
        TAP_ON_PDC = 35
        TAP_ON_RM = 34
        TAP_ON_GP = 33
        TAP_ON_START_REM_PARK_KEY = 32
        TAP_ON_SEMI_AUTOMATED_PARKING = 31
        TAP_ON_FULLY_AUTOMATED_PARKING = 30
        TAP_ON_LSCA_RELEASE_BRAKE = 29
        NO_USER_ACTION = 0
        TAP_ON_PARKING_SPACE_LEFT_1 = 1
        TAP_ON_PARKING_SPACE_LEFT_2 = 2
        TAP_ON_PARKING_SPACE_LEFT_3 = 3
        TAP_ON_PARKING_SPACE_LEFT_4 = 4
        TAP_ON_PARKING_SPACE_RIGHT_1 = 5
        TAP_ON_PARKING_SPACE_RIGHT_2 = 6
        TAP_ON_PARKING_SPACE_RIGHT_3 = 7
        TAP_ON_PARKING_SPACE_RIGHT_4 = 8
        TAP_ON_PARKING_SPACE_FRONT_1 = 9
        TAP_ON_PARKING_SPACE_FRONT_2 = 10
        TAP_ON_PARKING_SPACE_FRONT_3 = 11
        TAP_ON_PARKING_SPACE_FRONT_4 = 12
        TAP_ON_PARKING_SPACE_REAR_1 = 13
        TAP_ON_PARKING_SPACE_REAR_2 = 14
        TAP_ON_PARKING_SPACE_REAR_3 = 15
        TAP_ON_PARKING_SPACE_REAR_4 = 16
        TAP_ON_START_SELECTION = 17
        TAP_ON_START_PARKING = 18
        TAP_ON_INTERRUPT = 19
        TAP_ON_CONTINUE = 20
        TAP_ON_UNDO = 21
        TAP_ON_CANCEL = 22
        TAP_ON_REDO = 23
        TAP_ON_START_REM_PARK_PHONE = 24
        TAP_ON_SWITCH_DIRECTION = 25
        TAP_ON_SWITCH_ORIENTATION = 26
        TAP_ON_PREVIOUS_SCREEN = 27
        TOGGLE_AP_ACTIVE = 28

    class DrivingTubeDisplay(GetVariableName):
        """A class representing the different states of the driving tube display."""

        NONE = 0
        FRONT = 1
        REAR = 2
        BOTH = 3

    class pdwSystemState(GetVariableName):
        """Defining constants for PDW system state"""

        PDW_INIT = 0
        PDW_OFF = 1
        PDW_ACTIVATED_BY_R_GEAR = 2
        PDW_ACTIVATED_BY_BUTTON = 3
        PDW_AUTOMATICALLY_ACTIVATED = 4
        PDW_FAILURE = 5

    class ReduceToMute(GetVariableName):
        """Defining the reduce to mute signals"""

        PDW_REDUCE_NONE = 0
        PDW_REDUCE_LVL1 = 1
        PDW_REDUCE_LVL2 = 2
        PDW_REDUCE_LVL3 = 3
        PDW_REDUCE_LVL4 = 4

    class TONHUserActionHeadUnit(GetVariableName):
        """Defining the constants for TONH user action head unit
        AP.TONHUserInteractionPort.tonhUserActionHeadUnit_nu
        """

        TONH_NO_USER_ACTION = 0
        TONH_TAP_ON_MUTE = 1

    class PdwAutoActivate_nu(GetVariableName):
        """Defining the constants for PDC user interaction port"""

        PDW_AUTO_ACTIVATE_OFF = 0
        PDW_AUTO_ACTIVATE_ON = 1

    class LscaCore(GetVariableName):
        """Defining the constants for LSCA core state"""

        LSCA_DISABLED = 0
        LSCA_ENABLED = 1

    class DoorStatus(GetVariableName):
        """Defining the constants for door status"""

        DOOR_STATUS_INIT = 0
        DOOR_STATUS_OPEN = 1
        DOOR_STATUS_CLOSED = 2
        DOOR_STATUS_LOCKED = 3
        DOOR_STATUS_ERROR = 4


class LaCtrlRequestType(GetVariableName):
    """Defining the constants for LA control request type"""

    LACTRL_OFF = 0
    LACTRL_BY_TRAJECTORY = 1
    LACTRL_BY_ANGLE_FRONT = 2
    LACTRL_BY_ANGLE_REAR = 3
    LACTRL_BY_ANGLE_FRONT_REAR = 4
    LACTRL_BY_TORQUE = 5
    LACTRL_BY_CURVATURE = 6
    LACTRL_COMF_ANGLE_ADJUSTMENT = 7
    MAX_NUM_LA_REQUEST_TYPES = 8


class LoCtrlRequestType(GetVariableName):
    """Defining the constants for LO control request type"""

    LOCTRL_OFF = 0
    LOCTRL_BY_TRAJECTORY = 1
    LOCTRL_BY_DISTANCE = 2
    LOCTRL_BY_VELOCITY = 3
    LOCTRL_BY_DISTANCE_VELOCITY = 4
    LOCTRL_BY_ACCELERATION = 5
    LOCTRL_VELOCITY_LIMITATION = 6
    LOCTRL_EMERGENCY_STOP = 7
    MAX_NUM_LO_REQUEST_TYPES = 8


class LSCABrakePortRequestMode(GetVariableName):
    """Defining the constants for LSCA brake port request mode"""

    BRAKE_MODE_NONE = 0
    BRAKE_MODE_COMFORT = 1
    BRAKE_MODE_EMERGENCY = 2


class AVGStateAUP:
    """Constants for Automated Vehicle Guidance State for AUP"""

    AVGA_UNAVAILABLE = 0
    AVGA_AVAILABLE = 1
    AVGA_USED = 2
    AVGA_GRANTED = 3
    AVGA_OVERRULED = 4


class LoCtrlRequestSource_nu(GetVariableName):
    """Defining the constants for LO control request source"""

    LODMC_REQ_SRC_NO_REQEUESTER = 0
    LODMC_REQ_SRC_AUP = 1
    LODMC_REQ_SRC_LSCA = 2
    LODMC_REQ_SRC_REMOTE = 3
    LODMC_REQ_SRC_MSP = 4
    LODMC_REQ_SRC_SAFBAR = 5


class LaCtrlRequestSource_nu(GetVariableName):
    """Defining the constants for LA control request source"""

    LADMC_REQ_SRC_NO_REQEUESTER = 0
    LADMC_REQ_SRC_AUP = 1
    LADMC_REQ_SRC_LSCA = 2
    LADMC_REQ_SRC_REMOTE = 3
    LADMC_REQ_SRC_MSP = 4
    LADMC_REQ_SRC_SAFBAR = 5


class TrajCtrlActive_nu(GetVariableName):
    """Defining the constants for Trajectory Control Active AP.trajCtrlRequestPort.trajCtrlActive_nu"""

    NO_INTERVENTION = 0
    FOLLOW_TRAJ = 1
