#!/usr/bin/env python3
"""Defining constants testcases"""


class Platforms:
    """Functional tests platform"""

    VEHICLE = "Vehicle"
    SIM = "Sim"
    GT = "GT"
    ANY = "Any"


class PlotlyTemplate:
    """Defining the constants used in plotly graphs"""

    lgt_tmplt = {"margin": dict(r=0, l=0, t=50, b=0)}


class ConstantsPmsd:
    """PMSD constants"""

    LINE_CONFIDENCE_MIN = 0
    LINE_CONFIDENCE_MAX = 1
    CONVERT_MM_TO_M = 0.001
    NUM_PARKING_LINES_MIN = 0
    NUM_PARKING_LINES_MAX = 300
    NUM_PARKING_SLOTS_MIN = 0
    NUM_PARKING_SLOTS_MAX = 32
    PARKING_LINES_END_POINTS_MIN = -15
    PARKING_LINES_END_POINTS_MAX = 15
    NUM_WHEELSTOPPER_MIN = 0
    NUM_WHEELSTOPPER_MAX = 64
    NUM_WHEELLOCKER_MIN = 0
    NUM_WHEELLOCKER_MAX = 32
    NUM_STOPLINE_MIN = 0
    NUM_STOPLINE_MAX = 16


class AssociationConstants:
    """Class containing association constants."""

    MAX_SLOT_DISTANCE_IN_M = 2.0
    THRESHOLD_SLOT_DISTANCE_IN_M = 1.5
    THRESHOLD_SLOT_TRUE_POSITIVE = 0.5
    THRESHOLD_SLOT_ANGLE_IN_DEG = 10
    PCL_ASSOCIATION_RADIUS = 0.4  # Value ok
    WS_ASSOCIATION_RADIUS = 0.2  # Value ok
