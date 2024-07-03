"""List of constants used in TPP Test Cases."""


class Thresholds:
    """Thresholds used in KPIs."""

    DISTANCE_TH = 10  # [m]
    ERROR_TH = 0.22  # [m]


TPP_DETECTION_RANGE = 20.0  # [m]

# TODO: Update class types and sizes after GRAPPA interface changes
# Release 1.3.1
ClassTypes = {"CLASS_UNKNOWN": 0, "PEDESTRIAN": 1, "BIKE": 2, "MOTOR": 3, "RIDER": 4, "CAR": 5, "TRUCK": 6}
TppCuboids = ["CAR", "TRUCK"]
TppBoxes = [
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

# Sizes measured in meters [m]
ObjectSizes = {
    "PEDESTRIAN": {
        "width": {"min": 0.3, "max": 2.0, "default": 0.5},
        "height": {"min": 0.8, "max": 2.2, "default": 1.75},
    },
    "TWOWHEELER": {
        "width": {"min": 0.3, "max": 2.0, "default": 1.6},
        "height": {"min": 0.6, "max": 1.8, "default": 1.5},
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
