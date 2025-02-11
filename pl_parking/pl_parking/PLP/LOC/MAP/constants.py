"""Defining LOC constants"""

DEBUG_ROOT_FOLDER = "D:\\uie98244"
BSIG_PATH = r"PL_PARKING_BASE\pl_loc_bsig\D2024_11_05_PLF.bsig"


TRUE = 1
FALSE = 0
INVALID_MAP_ID = 255


class SigStatus:
    """Signal status"""

    AL_SIG_STATE_INIT = 0
    AL_SIG_STATE_OK = 1
    AL_SIG_STATE_INVALID = 2


class DataOperationResult:
    """signal values and its state"""

    DATA_OPERATION_SUCCESSFUL = 0
    DATA_OPERATION_FAILED = 1


class StateChange:
    """signal values and its state"""

    INACTIVE = 0
    ONGOING = 1
    FAILED = 2
    FINISHED = 3
    SUCCESS = 3
