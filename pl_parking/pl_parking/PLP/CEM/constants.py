#!/usr/bin/env python3
"""Defining constants testcases"""
from enum import Enum

# Should be equla to :
# doors://rbgs854a:40000/?version=2&prodID=0&view=00000015&urn=urn:telelogic::1-503e822e5ec3651e-M-00065413


class ConstantsCem:
    """Class containing constant values for CEM module."""

    PCL_MAX_NUM_MARKERS = 40  # Not defined in requirements
    PSD_MAX_NUM_MARKERS = 64  # Not defined in requirements
    SGF_MAX_NUM_OBJECTS = 64  # Not used (changed to real length)
    AP_E_DYN_OBJ_MAX_NUM_NU = 100  # Value ok
    MAX_CYCLE_NUM = 20  # TODO: Confirm Value
    AP_G_DES_MAP_RANGE_M = 20  # Value ok
    AP_E_SLOT_ID_REUSE_LIMIT_NU = 10  # Value ok
    AP_E_MAX_NUM_POLY_VERTEX_NU = 16  # Value ok
    MAX_NUM_TOTAL_VERTICES = 512  # Not used
    AP_STATIC_OBJ_ROI = 21.12  # Not defined in requirement (1729081 AP_E_STA_OBJ_MAX_DIST_M)
    TPF_RECALL_RATE = 97.0  # Value ok
    TPF_PRECISION_RATE = 97.0  # Value ok
    PCL_PRECISION_RATE = 97.0  # Value ok
    AP_E_DYN_OBJ_MIN_TRACKING_TIME_S = 0  # [s]  Value ok
    AP_E_DYN_OBJ_MAX_TRACKING_TIME_S = 1  # [s]  Value ok
    AP_E_DYN_OBJ_ID_REUSE_TIME_S = 1  # [s]  Value ok
    AP_E_DYN_OBJ_VELOCITY_ACCURACY_20_5_MPS = 0.5  # [m/s]  Not used
    AP_E_DYN_OBJ_VELOCITY_ACCURACY_5_1_MPS = 0.25  # [m/s]  Not used
    AP_E_DYN_OBJ_VELOCITY_ACCURACY_1_MPS = 0.1  # [m/s]  Not used
    AP_E_STA_OBJ_ID_REUSE_TIME_S = 3600  # [s]  Value ok
    AP_E_STA_OBJ_ELEV_CONF_MIN_NU = 20  # Value ok
    AP_E_TIME_BEFORE_CURRENT_T_CONTRIBUTION_MS = 60  # ms  Value ok (tpf helper)
    AP_E_DYN_OBJ_ACC_EQUAL_RATE_NU = 90  # Value ok
    AP_E_DYN_OBJ_ACC_MAX_RATE_NU = 95  # Value ok
    AP_E_HEIGHT_WHEEL_TRAVER_MIN_M = 0.04  # Value ok
    AP_E_HEIGHT_HANGING_MAX_M = 4  # [m]  Value ok
    CYCLE_PERIOD_TIME_MS = 33  # ms - estimatedCycletimeUs
    SYNC_INPUT_OUTPUT_CYCLES = 20  # TODO: Confirm Value == MAX_CYCLE_NUM
    NUM_OF_CYCLES_FOR_OUTPUT = 15  # TODO: Confirm Value
    THRESHOLD_FOR_LATENCY = 5  # ms  Not used

    @staticmethod
    def AP_E_DYN_OBJ_ACC_M(dist: float) -> float:
        """Calculate the acceleration in meters for dynamic objects based on distance."""
        return 0.1 + 0.05 * dist  # Value ok

    @staticmethod
    def AP_E_DYN_OBJ_ACC_MAX_M(dist: float) -> float:
        """Calculate the maximum acceleration in meters for dynamic objects based on distance."""
        return 0.2 + 0.1 * dist  # Value ok

    @staticmethod
    def AP_E_DYN_OBJ_ACC_Y_M(dist: float) -> float:
        """Calculate the lateral acceleration in meters for dynamic objects based on distance."""
        return 0.1 + 0.05 * dist  # Value ok

    @staticmethod
    def AP_E_DYN_OBJ_ACC_MAX_Y_M(dist: float) -> float:
        """Calculate the maximum lateral acceleration in meters for dynamic objects based on distance."""
        return 0.2 + 0.1 * dist  # Value ok


class ConstantsCemInput:
    """Class containing input constants for CEM module."""

    PCLEnum = 1  # Value ok
    WSEnum = 7  # Value ok
    WLEnum = 7  # This value needs to be reconfirmed once WL output is available.
    SLEnum = 7  # This value needs to be reconfirmed once SL output is available.


class GroundTruthCem:
    """Class containing ground truth data for CEM."""

    kml_files = [
        r"config\cem_ground_truth\mring_parking_markers.kml",
        r"config\cem_ground_truth\mring_parking_slots.kml",
    ]
    relevent_distance = 100


class GroundTruthTpf:
    """Class containing ground truth data for TPF."""

    tpf_gt_file = [
        r"config\\tpf_ground_truth_2023.05.05_at_08.45.59_svu-mi5_401.h5",
    ]
    relevent_distance = 10


class GroundTruthCarMaker:
    """Class containing ground truth data for CarMaker."""

    CAR_WIDTH = 1.799
    CAR_LENGTH = 4.562
    REAR_BUMPER_TO_REAR_AXIS_DIST = 1.096
    REAR_AXIS_TO_FRONT_DIST = 4.767 - REAR_BUMPER_TO_REAR_AXIS_DIST


class AssociationConstants:
    """Class containing association constants."""

    MAX_SLOT_DISTANCE = 0.5  # Value ok
    PCL_ASSOCIATION_RADIUS = 0.4  # Value ok
    WS_ASSOCIATION_RADIUS = 0.2  # Value ok
    WL_ASSOCIATION_RADIUS = 0.2  # This values need to be re confirmed once WL output is available.
    SL_ASSOCIATION_RADIUS = 0.2  # This values need to be re confirmed once SL output is available.


# https://github-am.geo.conti.de/ADAS/cem_lsm_types/blob/96249cb00d0f140bb37ea6ba9bb29100312a63ab/interface/types/aupdf/sef_output_interface_types.plantuml#L7-L16
# TODO: Check that the enum values are correct. Do they need to be contiguous like below or powers of 2
# like in the plantuml?
class ElementClassification(Enum):
    """Enumeration for element classification."""

    AGP_CLASS_UNKNOWN = 0  # Value ok
    AGP_CLASS_PARKING_CAR = 1  # Not used correct
    AGP_CLASS_GUARDRAIL = 2  # Not used correct
    AGP_CLASS_CURBSTONE = 3  # Not used incorrect
    AGP_CLASS_VEHICLE = 4  # Not used incorrect
    AGP_CLASS_ANIMAL = 5  # Not used incorrect
    AGP_CLASS_VULNERABLEROADUSER = 6  # Not used incorrect
    AGP_CLASS_OTHER_MOVING = 7  # Not used incorrect
    AGP_CLASS_2D_NO_ENTRY_ZONE = 8  # Not used incorrect
    AGP_CLASS_2D_PED_CROSSING = 9  # Not used incorrect
    AGP_CLASS_2D_DIRECTIONAL_ARROW = 10  # Not used incorrect
    AGP_CLASS_2D_TEXT = 11  # Not used incorrect


class TpfFovConstatns:
    """Class containing constants for TPF field of view."""

    DISTANCE_RANGE = 7.0  # Not in reqs
