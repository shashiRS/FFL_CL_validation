"""List of constants used in TPP Test Cases."""


class Thresholds:
    """Thresholds used in KPIs."""

    DISTANCE_TH = 10  # [m]
    ERROR_TH = 0.22  # [m]


TPP_DETECTION_RANGE = 20.0  # [m]
TPP_MAX_NUMBER_OF_DETECTIONS = 64

# TODO: Update class types and sizes after GRAPPA interface changes
# Release 1.3.1
CuboidClassTypes = {"UNKNOWN": 0, "CAR": 1, "VAN": 2, "TRUCK": 3}
BoxClassTypes = {"UNKNOWN": 0, "PEDESTRIAN": 1, "TWOWHEELER": 2, "SHOPPINGCART": 3, "ANIMAL": 4}
TppCuboids = ["CAR", "VAN", "TRUCK"]
TppBoxes = [
    "PEDESTRIAN",
    "TWOWHEELER",
    "SHOPPINGCART",
    "ANIMAL",
]
# Release 1.3.1 R3
ClassTypesR3 = {"CLASS_UNKNOWN": 0, "PEDESTRIAN": 1, "BIKE": 2, "MOTOR": 3, "CAR": 4, "TRUCK": 5}
TppCuboidsR3 = ["CAR", "TRUCK"]
TppBoxesR3 = [
    "PEDESTRIAN",
    "BIKE",
    "MOTOR",
    "RIDER",
]


GrappaClassTypes = {"PEDESTRIAN": 0, "BIKE": 1, "MOTOR": 2, "RIDER": 3, "CAR": 4, "TRUCK": 5, "WS": 20, "PS": 21}
GrappaCuboids = [GrappaClassTypes["CAR"], GrappaClassTypes["TRUCK"]]
GrappaBoxes = [
    GrappaClassTypes["PEDESTRIAN"],
    GrappaClassTypes["BIKE"],
    GrappaClassTypes["MOTOR"],
    GrappaClassTypes["RIDER"],
]

# Sizes measured in meters [m] for the latest release
ObjectSizes = {
    "UNKNOWN": {
        "width": {"min": 0, "max": 0, "default": 0},
        "height": {"min": 0, "max": 0, "default": 0},
        "length": {"min": 0, "max": 0, "default": 0},
    },
    "PEDESTRIAN": {
        "width": {"min": 0.3, "max": 2.0, "default": 0.5},
        "height": {"min": 0.8, "max": 2.2, "default": 1.75},
    },
    "TWOWHEELER": {
        "width": {"min": 0.3, "max": 2.0, "default": 1.6},
        "height": {"min": 0.6, "max": 1.8, "default": 1.5},
    },
    "SHOPPINGCART": {
        "width": {"min": 1.8, "max": 3.0, "default": 2.6},
        "height": {"min": 1.5, "max": 3.0, "default": 2.6},
    },
    "ANIMAL": {
        "width": {"min": 1.8, "max": 3.0, "default": 2.6},
        "height": {"min": 1.5, "max": 3.0, "default": 2.6},
    },
    "CAR": {
        "width": {"min": 1.6, "max": 2.4, "default": 1.8},
        "height": {"min": 1.2, "max": 2.0, "default": 3.0},
        "length": {"min": 3.0, "max": 6.0, "default": 4.0},
    },
    "VAN": {
        "width": {"min": 1.5, "max": 2.5, "default": 2.0},
        "height": {"min": 1.5, "max": 2.6, "default": 2.2},
        "length": {"min": 4.0, "max": 8.0, "default": 6.0},
    },
    "TRUCK": {
        "width": {"min": 1.8, "max": 3.0, "default": 2.6},
        "height": {"min": 1.5, "max": 3.0, "default": 2.6},
        "length": {"min": 5.0, "max": 15.0, "default": 8.0},
    },
}

# Constants for the signal state
AL_SIG_STATE_INIT = 0
AL_SIG_STATE_OK = 1
AL_SIG_STATE_INVALID = 2

# range for extrinsic parameters
POS_MIN_VALUE = -5000
POS_MAX_VALUE = 5000
ROT_MIN_VALUE = -3.14159
ROT_MAX_VALUE = 3.14159

IMG_WIDTH = 832
IMG_HEIGHT = 650
