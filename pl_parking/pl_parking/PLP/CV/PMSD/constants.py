#!/usr/bin/env python3
"""Defining constants testcases"""

from enum import Enum


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
    NUM_PED_CROSSING_MIN = 0
    NUM_PED_CROSSING_MAX = 16
    PARKING_LINES_END_POINTS_MIN = -15
    PARKING_LINES_END_POINTS_MAX = 15
    NUM_WHEELSTOPPER_MIN = 0
    NUM_WHEELSTOPPER_MAX = 64
    NUM_WHEELLOCKER_MIN = 0
    NUM_WHEELLOCKER_MAX = 32
    NUM_STOPLINE_MIN = 0
    NUM_STOPLINE_MAX = 16
    AP_G_DES_MIN_SLOT_LENGTH_M = 2.3
    AP_G_DES_MIN_SLOT_WIDTH_M = 1.4
    AP_G_PMSD_MIN_LENGTH_P_MARKING_SEG_M = 1.3
    AP_G_PMSD_MAXDIST_FAR_M = 12
    AP_G_PMSD_MINDIST_FAR_M = 5
    AP_G_PMSD_MAXDIST_CLOSE_M = 2
    AP_G_PMSD_ACCURACY_FAR_RANGE_M = 0.20
    AP_G_PMSD_ACCURACY_MID_RANGE_M = 0.04
    AP_G_PMSD_ACCURACY_CLOSE_RANGE_M = 0.04


class AssociationConstants:
    """Class containing association constants."""

    MAX_SLOT_DISTANCE_IN_M = 2.0
    THRESHOLD_SLOT_DISTANCE_IN_M = 1.5
    THRESHOLD_SLOT_TRUE_POSITIVE = 0.5
    THRESHOLD_SLOT_ANGLE_IN_DEG = 10
    THRESHOLD_SLOT_SCENARIO_TRUE_POSITIVE = 0.8
    THRESHOLD_SLOT_SCENARIO_FALSE_POSITIVE = 0.2
    PCL_ASSOCIATION_RADIUS = 0.4  # Value ok
    WS_ASSOCIATION_RADIUS = 0.2  # Value ok


class SlotScenario(Enum):
    """Enumeration for element slot scenario."""

    SLOT_SCENARIO_PERPENDICULAR = 1
    SLOT_SCENARIO_PARALLEL = 2
    SLOT_SCENARIO_ANGLED = 3
