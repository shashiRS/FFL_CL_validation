"""Constants file for SPP Test Scripts."""

from enum import Enum


class SensorSource:
    """Class to represent possible cameras source."""

    SPP_FC_DATA = "SPP_FC_DATA"
    SPP_LSC_DATA = "SPP_LSC_DATA"
    SPP_RC_DATA = "SPP_RC_DATA"
    SPP_RSC_DATA = "SPP_RSC_DATA"


class SppPolylines:
    """Class to represent an SPP Polyline."""

    SPP_MIN_NUMBER_PTS_POLYLINE = 2
    SPP_MAX_NUMBER_POLYLINES = 128
    SPP_MAX_NUMBER_VERTICES = 3072


class SppPolygon:
    """Class to represent an SPP Polygon."""

    SPP_MIN_NUMBER_PTS_POLYGON = 3
    FC_MAX_POLYGON = ((2, 0, 0.5), (7.77, 10, 0.5), (15, 10, 0.5), (15, -10, 0.5), (7.77, -10, 0.5), (2, 0, 0.5))
    LSC_MAX_POLYGON = ((1.5, 0, 0.5), (11, 10, 0.5), (-11, 10, 0.5), (1.5, 0, 0.5))
    RC_MAX_POLYGON = (
        (-0.5, 0, 0.5),
        (-6.27, 10, 0.5),
        (-15, 10, 0.5),
        (-15, -10, 0.5),
        (-6.27, -10, 0.5),
        (-0.5, 0, 0.5),
    )
    RSC_MAX_POLYGON = ((1.5, 0, 0.5), (11, -10, 0.5), (-11, -10, 0.5), (1.5, 0, 0.5))


class SppSemPoints:
    """Class to represent SPP SemPoints."""

    SPP_SEMPOINTS_MAX_NUMBER_VERTICES = 2000
    MIN_LATENCY_COMPENSATION_MODE = 0.02
    MAX_LATENCY_COMPENSATION_MODE = 0.07
    LATENCY_COMPENSATION_MODE_USED = 1
    LATENCY_COMPENSATION_MODE_NOT_USED = 0


class SppOperationalRange:
    """Class to represent SPP Operational Range."""

    SPP_OPERATIONAL_RANGE_LONGITUDINAL = 15
    SPP_OPERATIONAL_RANGE_LATERAL = 10


class SppSemantics(Enum):
    """Class to represent possible semantic of an SPP Polyline."""

    BACKGROUND = 0
    GROUND = 1
    DRIVABLE_AREA = 2
    STATIC_OBSTACLE = 3
    DYNAMIC_OBSTACLE = 4
    PARKING_MARKER = 5
    CURB = 6
    SEMANTICS_NO = 7


class SppSigStatus:
    """Class to represent possible states of SPP SigStatus."""

    AL_SIG_STATE_INIT = 0
    AL_SIG_STATE_OK = 1
    AL_SIG_STATE_INVALID = 2


class SppKPI(Enum):
    """Class to represent KPIs."""

    BUFFER_DISTANCE = 0.7  # [meter]
    MIN_TP_DETECTION = 70  # [percentage]
    MAX_FPA_STATIC = 30  # [percentage]
    MAX_FPA_CURB = 20  # [percentage]

    SPP_DETECTED_CURB_OBJECTS_TPR_PERC = 80
    SPP_DETECTED_STATIC_OBJECTS_TPR_PERC = 75

    TP_RATE_THRESHOLD_CURB = 85  # [percentage]
    TP_RATE_THRESHOLD_STATIC = 80  # [percentage]
    FP_RATE_THRESHOLD_CURB = 15  # [percentage]
    FP_RATE_THRESHOLD_STATIC = 20  # [percentage]
    FP_ACCURACY_THRESHOLD_CURB = 20  # [percentage]
    FP_ACCURACY_THRESHOLD_STATIC = 30  # [percentage]
    FN_RATE_THRESHOLD_CURB = 20  # [percentage]
    FN_RATE_THRESHOLD_STATIC = 25  # [percentage]

    UNCLASSIFIED = 0
    TRUE_POSITIVE = 1
    FALSE_POSITIVE = 2
    FALSE_POSITIVE_ACCURACY = 3
    FALSE_NEGATIVE = 4

    SPP_AVERAGE_POLYGON_AREA_COVERAGE = 80  # [percentage]
    SPP_POLYGON_AREA_COVERAGE_RATE = 75  # [percentage] TODO: add in Doors Next
    SPP_AVERAGE_MAXIMUM_EXTRALAP = 20  # [percentage]
    SPP_AVERAGE_MAXIMUM_UNDERLAP = 20  # [percentage]


# TODO: update it when recordings are available
TEST_CASE_MAP = {
    "SWRT_CNC_SPP_Polylines-DetectionOfStaticObjects": {
        "SPP_FC_DATA": {
            "Recording Name": "2024.05.13_at_11.46.45_radar-mi_827",
            "Start Timestamp": 4777770924,
            "End Timestamp": 4778304264,
        },
        "SPP_LSC_DATA": {
            "Recording Name": "2024.04.08_at_08.34.35_camera-mi_128",
            "Start Timestamp": 1,
            "End Timestamp": 100,
        },
        "SPP_RC_DATA": {
            "Recording Name": "2024.05.13_at_09.33.26_radar-mi_827",
            "Start Timestamp": 101,
            "End Timestamp": 200,
        },
        "SPP_RSC_DATA": {
            "Recording Name": "2024.04.08_at_08.34.35_camera-mi_128",
            "Start Timestamp": 201,
            "End Timestamp": 300,
        },
    },
    "SWRT_CNC_SPP_Polylines-DetectionOfCurbObjects": {
        "SPP_FC_DATA": {
            "Recording Name": "2024.05.13_at_09.33.26_radar-mi_827",
            "Start Timestamp": 4777770924,
            "End Timestamp": 4778304264,
        },
        "SPP_LSC_DATA": {
            "Recording Name": "2024.04.08_at_08.34.35_camera-mi_128",
            "Start Timestamp": 1,
            "End Timestamp": 100,
        },
        "SPP_RC_DATA": {
            "Recording Name": "2024.05.13_at_09.33.26_radar-mi_827",
            "Start Timestamp": 101,
            "End Timestamp": 200,
        },
        "SPP_RSC_DATA": {
            "Recording Name": "2024.04.08_at_08.34.35_camera-mi_128",
            "Start Timestamp": 201,
            "End Timestamp": 300,
        },
    },
    "SWRT_CNC_SPP_General-IdentifcationOfFreeAndDrivableAreaOnCobblestone": {
        "SPP_FC_DATA": {
            "Recording Name": "2024.05.13_at_09.33.26_radar-mi_827",
            "Start Timestamp": 4777770924,
            "End Timestamp": 4778304264,
        },
        "SPP_LSC_DATA": {
            "Recording Name": "2024.04.08_at_08.34.35_camera-mi_128",
            "Start Timestamp": 1,
            "End Timestamp": 100,
        },
        "SPP_RC_DATA": {
            "Recording Name": "2024.05.13_at_09.33.26_radar-mi_827",
            "Start Timestamp": 101,
            "End Timestamp": 200,
        },
        "SPP_RSC_DATA": {
            "Recording Name": "2024.04.08_at_08.34.35_camera-mi_128",
            "Start Timestamp": 201,
            "End Timestamp": 300,
        },
    },
    "SWRT_CNC_SPP_General-IdentifcationOfFreeAndDrivableAreaOnOffroad": {
        "SPP_FC_DATA": {
            "Recording Name": "2024.05.13_at_09.33.26_radar-mi_827",
            "Start Timestamp": 4777770924,
            "End Timestamp": 4778304264,
        },
        "SPP_LSC_DATA": {
            "Recording Name": "2024.04.08_at_08.34.35_camera-mi_128",
            "Start Timestamp": 1,
            "End Timestamp": 100,
        },
        "SPP_RC_DATA": {
            "Recording Name": "2024.05.13_at_09.33.26_radar-mi_827",
            "Start Timestamp": 101,
            "End Timestamp": 200,
        },
        "SPP_RSC_DATA": {
            "Recording Name": "2024.04.08_at_08.34.35_camera-mi_128",
            "Start Timestamp": 201,
            "End Timestamp": 300,
        },
    },
}
