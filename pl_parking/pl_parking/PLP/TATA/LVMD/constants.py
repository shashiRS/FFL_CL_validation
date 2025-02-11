"""File used to store all LVMD constants """

from collections import Counter
from enum import IntEnum

import numpy as np

class SystemStatus:
    """Defining constants for LVMD System States"""

    LVMD_Status_OFF = 0
    LVMD_Status_IDLE = 1
    LVMD_Status_INACTIVE = 2
    LVMD_Status_ACTIVE = 3
    LVMD_Status_FAILURE = 4

class WarningTrigger:
    "Defining Constants for Warning Trigger."

    LVMD_Trigger_NONE = 0
    LVMD_Trigger_VISUAL = 1
    LVMD_Trigger_VISUAL_AUDIO = 2


class WarningStatus:
    """Defining constants for LVMD Warning Status."""
    LVMD_Warning_NONE = 0
    LVMD_Warning_EGO_VEH_NOT_STANDSTILL = 1
    LVMD_Warning_LEAD_VEHICLE_NOT_SELECTED = 2
    LVMD_Warning_LEAD_VEH_NOT_MOVED_AWAY = 3
    LVMD_Warning_LEAD_VEH_NOT_IN_RANGE = 4
    LVMD_Warning_EGO_VEH_GEAR_POSITION_IN_REVERSE = 5
    LVMD_Warning_LEAD_VEH_CUTOUT = 6
    LVMD_Warning_VRU_In_ROI = 7
    LVMD_Warning_VEHICLE_APPEARED_FRONT_OF_EGO_VEHICLE = 8
    LVMD_Warning_LEAD_VEHICLE_MOVEMENT_DETECTION_SYSTEM_FAULT = 9

class UserInteraction:
    """Defining constants for LVMD User Interaction."""
    LVMD_NO_USER_ACTION = 0
    LVMD_TAP_ON_ACT_DEACT_BTN = 1
    LVMD_TAP_ON_MUTE_BTN = 2


class ConstantsLVMD:
    """Defining constants for LVMD test."""

    LVMD_Min_Forward_Selection_Distance_nu = 0.3
    LVMD_Max_Forward_Selection_Distance_nu = 5.0
    LVMD_Min_Forward_Alert_Distance_nu = 1.0
    LVMD_Max_DetectionRange_nu = 10.0
    LVMD_Alert_Min_DriveoffDistance_nu = 3.0
    LVMD_Min_EgoStandstill_nu = 5.0,
    LVMD_Min_LeadStandstill_nu = 10.0
    LVMD_VisualWarningTime_nu = 5.0
    LVMD_AudioWarningTime_nu = 2.0,
    LVMD_Alert_Min_LeadVelocity_nu = 2.0
    LVMD_Alert_Max_LeadVelocity_nu = 5.0

class DynObjClass():
    """Defining constants for LVMD Dynamic Object Class."""

    DYN_OBJ_CAR = 1
    DYN_OBJ_PEDESTRIAN = 2
    DYN_OBJ_TWOWHEELER = 3
    DYN_OBJ_VAN = 4
    DYN_OBJ_TRUCK = 5
    DYN_OBJ_SHOPPINGCART = 6
    DYN_OBJ_ANIMAL = 7

class Gear():
    """Defining constants for LVMD Ego Vehicle Gear information"""

    GEAR_N = 0
    GEAR_1 = 1
    GEAR_2 = 2
    GEAR_3 = 3
    GEAR_4 = 4
    GEAR_5 = 5
    GEAR_6 = 6
    GEAR_7 = 7
    GEAR_8 = 8
    GEAR_P = 9
    GEAR_S = 10
    GEAR_D = 11
    GEAR_INTERMEDIATE_POS = 12
    GEAR_R = 13
    GEAR_NOT_DEFINED = 14
    GEAR_ERROR = 15



    


