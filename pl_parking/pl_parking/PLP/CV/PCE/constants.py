"""Defining PCE constants"""


class SigStatus:
    """Signal status"""

    AL_SIG_STATE_INIT = 0
    AL_SIG_STATE_OK = 1
    AL_SIG_STATE_INVALID = 2


class BaseCtrl:
    """Base control"""

    GS_BASE_OM_IDLE = 0
    GS_BASE_OM_RESET = 1
    GS_BASE_OM_MAX_RUNTIME = 2
    GS_BASE_OM_DEMO = 3
    GS_BASE_OM_RUN = 4
    GS_BASE_OM_RUN_ODD = 5
    GS_BASE_OM_RUN_EVEN = 6


class grappa_constants:
    """Grappa constants"""

    GRAPPA_MAX_NUMBER_OF_SPECIFIC_DETECTIONS = 64


class CompCtrl:
    """Base control"""

    GS_COMP_STATE_SUCCESS = 4


class SemSegLabel:
    """SemSegLabel"""

    GRAPPA_SEMSEG_LABEL_BACKGROUND = 0
    GRAPPA_SEMSEG_LABEL_GROUND = 1
    GRAPPA_SEMSEG_LABEL_DRIVABLE_AREA = 2
    GRAPPA_SEMSEG_LABEL_STATIC_OBJECT = 3
    GRAPPA_SEMSEG_LABEL_DYNAMIC_OBJECT = 4
    GRAPPA_SEMSEG_LABEL_PARKING_MARKER = 5
    GRAPPA_SEMSEG_LABEL_CURB_SIDE = 6
    GRAPPA_SEMSEG_LABEL_CURB_TOP = 7
    GRAPPA_SEMSEG_LABEL_STOPLINE_MARKER = 8
    GRAPPA_SEMSEG_LABEL_PED_CROSSING_MARKER = 9
    GRAPPA_SEMSEG_LABEL_CANDIDATE_HOUSE = 10
    GRAPPA_SEMSEG_LABEL_ROAD_SIGN = 11


class SensorSource:
    """Class to represent possible cameras source."""

    SPP_FC_DATA = "FC"
    SPP_LSC_DATA = "LSC"
    SPP_RC_DATA = "RC"
    SPP_RSC_DATA = "RSC"


class PlotlyTemplate:
    """Defining the constants used in plotly graphs"""

    lgt_tmplt = {"margin": dict(r=0, l=0, t=50, b=0)}
