"""
General utility for framework functionalities like signal definition,
function addition, and table overview customization.
"""

import logging
import os
import sys

import pandas as pd
import plotly.graph_objects as go
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
import pl_parking.PLP.LOC.MAP.constants as fh
from pl_parking.PLP.LOC.MAP.constants import DataOperationResult, StateChange

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))  # nopep8
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


class MAP_Signals(SignalDefinition):
    """PAR230 signals to read for component ."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        CYCLE_COUNTER = "uiCycleCounter"
        MAP_DATA_FILE_SYSTEM_DATA = "mapDataFileSystemStatus"
        MAP_RECORDING_STATUS = "mapRecordingStatus"
        MAP_ID = "MP_mapID"
        MAP_RESULT_ID = "MP_result_mapID"
        STORE_REQUEST = "storeRequest"
        SAVE_RESULT = "result"
        SAVE_MAP_ID = "PH_mapID"
        MAP_SIG_STATUS = "MAP_eSigStatus"
        MAP_SAVE_DATA_MAP_ID = "MAP_SAVE_Data_mapID"
        MAP_DATA_MAP_ID = "MAP_Data_mapID"
        MAP_NUMBER_OF_TILES = "numberOfTiles"
        MAP_NUMBER_OF_EDGES = "numberOfEdges"
        MAP_ORIGIN_HEADING = "mapOrigin.heading"
        MAP_ORIGIN_HEMISPHERE = "mapOrigin.hemisphere"
        MAP_ORIGIN_X = "mapOrigin.x"
        MAP_ORIGIN_Y = "mapOrigin.y"
        MAP_ORIGIN_ZONE = "mapOrigin.zone"
        TILE_ID = "tileId"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CYCLE_COUNTER: "SIM VFB.MapInstance.recordingResultPort.sSigHeader.uiCycleCounter",
            self.Columns.MAP_DATA_FILE_SYSTEM_DATA: "SIM VFB.MapInstance.recordingResultPort.mapDataFileSystemStatus",
            self.Columns.MAP_RECORDING_STATUS: "SIM VFB.MapInstance.recordingResultPort.mapRecordingStatus",
            self.Columns.MAP_ID: "SIM VFB.MP_ADAPTER_INSTANCE.recordingRequestPort.mapID",
            self.Columns.MAP_RESULT_ID: "SIM VFB.MapInstance.recordingResultPort.mapID",
            self.Columns.STORE_REQUEST: "SIM VFB.MP_ADAPTER_INSTANCE.recordingRequestPort.storeRequest",
            self.Columns.SAVE_RESULT: "SIM VFB.PH_ADAPTER_INSTANCE.saveMapDataResultMessage.result",
            self.Columns.SAVE_MAP_ID: "SIM VFB.PH_ADAPTER_INSTANCE.saveMapDataResultMessage.mapID",
            self.Columns.MAP_SIG_STATUS: "SIM VFB.MapInstance.recordingResultPort.sSigHeader.eSigStatus",
            self.Columns.MAP_SAVE_DATA_MAP_ID: "SIM VFB.MapInstance.saveMapDataRequestMessage.mapData.mapID",
            self.Columns.MAP_DATA_MAP_ID: "SIM VFB.MapInstance.saveMapDataRequestMessage.mapID",
            self.Columns.MAP_NUMBER_OF_TILES: "SIM VFB.MapInstance.saveMapDataRequestMessage.mapData.numberOfTiles",
            self.Columns.MAP_NUMBER_OF_EDGES: "SIM VFB.MapInstance.saveMapDataRequestMessage.mapData.numberOfEdges",
            self.Columns.MAP_ORIGIN_HEADING: "SIM VFB.MapInstance.saveMapDataRequestMessage.mapData.mapOrigin.heading",
            self.Columns.MAP_ORIGIN_HEMISPHERE: "SIM VFB.MapInstance.saveMapDataRequestMessage.mapData."
            "mapOrigin.hemisphere",
            self.Columns.MAP_ORIGIN_X: "SIM VFB.MapInstance.saveMapDataRequestMessage.mapData.mapOrigin.x",
            self.Columns.MAP_ORIGIN_Y: "SIM VFB.MapInstance.saveMapDataRequestMessage.mapData.mapOrigin.y",
            self.Columns.MAP_ORIGIN_ZONE: "SIM VFB.MapInstance.saveMapDataRequestMessage.mapData.mapOrigin.zone",
            self.Columns.TILE_ID: "SIM VFB.MapInstance.saveMapDataRequestMessage.mapData.tiles[%].tileId",
        }

    def get_complete_signal_name(self, column_name):
        """Fetch the complete signal name for a given column name."""
        return self._properties.get(column_name, "Unknown column")


class PLF_Signals(SignalDefinition):
    """PAR230 signals to read for component."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        PLF_POSITION_X = "plf_x_dir"
        PLF_POSITION_Y = "plf_y_dir"
        PLF_ORIENTATION = "plf_yaw_rad"
        VEDODO_POSITION_X = "vedodo_xPosition_m"
        VEDODO_POSITION_Y = "vedodo_yPosition_m"
        VEDODO_ORIENTATION = "vedodo_yawAngle_rad"
        PLF_STD_POSITION_X = "plf_std_x_m"
        PLF_STD_POSITION_Y = "plf_std_y_m"
        PLF_STD_ORIENTATION = "plf_std_heading_rad"
        PLF_CYCLE_COUNTER = "PLF_uiCycleCounter"
        LOAD_RESULT = "result"
        MAP_ID = "mapID"
        INITIAL_LOCALIZATION_REQUEST = "initialLocalizationRequest"
        NUM_VALID_REQUEST = "numValidRequests_nu"
        RELOCALIZATION_STATUS = "relocalizationStatus"
        MAP_DATA_FILE_SYSTEM_STATUS = "mapDataFileSystemStatus"
        NUM_VALID_RELOCALIZATION_MAP = "numValidRelocalizedMaps"
        PLF_SIG_STATUS = "PLF_eSigStatus"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.PLF_CYCLE_COUNTER: "SIM VFB.PLF_INSTANCE.relocalizationOutput.sSigHeader.uiCycleCounter",
            self.Columns.PLF_POSITION_X: "SIM VFB.PLF_INSTANCE.relocalizationOutput.relocalizationResultsPerID.currentEgoInMap.x_dir",
            self.Columns.PLF_POSITION_Y: "SIM VFB.PLF_INSTANCE.relocalizationOutput.relocalizationResultsPerID.currentEgoInMap.y_dir",
            self.Columns.PLF_ORIENTATION: "SIM VFB.PLF_INSTANCE.relocalizationOutput.relocalizationResultsPerID.currentEgoInMap.yaw_rad",
            self.Columns.VEDODO_POSITION_X: "MTA_ADC5.MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.xPosition_m",
            self.Columns.VEDODO_POSITION_Y: "MTA_ADC5.MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.yPosition_m",
            self.Columns.VEDODO_ORIENTATION: "MTA_ADC5.MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.yawAngle_rad",
            self.Columns.PLF_STD_POSITION_X: "SIM VFB.PLF_INSTANCE.relocalizationOutput.relocalizationResultsPerID.std_x_m",
            self.Columns.PLF_STD_POSITION_Y: "SIM VFB.PLF_INSTANCE.relocalizationOutput.relocalizationResultsPerID.std_y_m",
            self.Columns.PLF_STD_ORIENTATION: "SIM VFB.PLF_INSTANCE.relocalizationOutput.relocalizationResultsPerID.std_heading_rad",
            self.Columns.LOAD_RESULT: "SIM VFB.PH_ADAPTER_INSTANCE.loadMapDataResultMessage.result",
            self.Columns.MAP_ID: "SIM VFB.MP_ADAPTER_INSTANCE.relocalizationRequest.requestedRelocalizationSlots[0].mapID",
            self.Columns.INITIAL_LOCALIZATION_REQUEST: "SIM VFB.MP_ADAPTER_INSTANCE.relocalizationRequest.requestedRelocalizationSlots[0].initialLocalizationRequest",
            self.Columns.NUM_VALID_REQUEST: "SIM VFB.MP_ADAPTER_INSTANCE.relocalizationRequest.numValidRequests_nu",
            self.Columns.RELOCALIZATION_STATUS: "SIM VFB.PLF_INSTANCE.relocalizationOutput.relocalizationResultsPerID.relocalizationStatus",
            self.Columns.MAP_DATA_FILE_SYSTEM_STATUS: "SIM VFB.PLF_INSTANCE.relocalizationOutput.relocalizationResultsPerID.mapDataFileSystemStatus",
            self.Columns.NUM_VALID_RELOCALIZATION_MAP: "SIM VFB.PLF_INSTANCE.relocalizationOutput.numValidRelocalizedMaps",
            self.Columns.PLF_SIG_STATUS: "SIM VFB.PLF_INSTANCE.relocalizationOutput.sSigHeader.eSigStatus",
        }

    def get_complete_signal_name(self, column_name):
        """Fetch the complete signal name for a given column name."""
        return self._properties.get(column_name, "Unknown column")


def get_time_intervals_with_indices(cycle_counter, threshold=1):
    """
    Identify time intervals and their indices in non-continuous cycle counter data.

    :param cycle_counter: List of cycle counter values (assumed to be sorted).
    :param threshold: Difference threshold to identify gaps in the cycle counter.
    :return: List of time intervals, each represented as a dictionary with 'start', 'end', 'start_index', and 'end_index'.
    """
    if not cycle_counter:
        return []

    intervals = []
    start = cycle_counter[0]
    start_index = 0
    previous = cycle_counter[0]

    for i, current in enumerate(cycle_counter[1:], start=1):
        if current - previous > threshold:
            intervals.append({"start": start, "end": previous, "start_index": start_index, "end_index": i - 1})
            start = current
            start_index = i
        previous = current

    intervals.append({"start": start, "end": previous, "start_index": start_index, "end_index": len(cycle_counter) - 1})
    return intervals


def create_rects(time_intervals, final_df):
    """
    Returns:
    list of dict: List of rectangles represented as dictionaries with 'x_min', 'x_max', 'y_min', and 'y_max' keys.
    """
    rects = []

    # Check if 'storeRequest' and 'MP_mapID' exist in final_df
    if "storeRequest" in final_df.columns:
        y_min_signal = final_df["storeRequest"].min()
    else:
        # Use an alternative signal or default value if 'storeRequest' is not present
        y_min_signal = final_df["alternativeSignal"].min() if "alternativeSignal" in final_df.columns else 0

    if "MP_mapID" in final_df.columns:
        y_max_signal = final_df["MP_mapID"].max()
    else:
        # Use an alternative signal or default value if 'MP_mapID' is not present
        y_max_signal = final_df["mapDataFileSystemStatus"].max() if "mapRecordingStatus" in final_df.columns else 255

    for interval in time_intervals:
        rect = {
            "x_min": interval["start"],
            "x_max": interval["end"],
            "y_min": y_min_signal,
            "y_max": y_max_signal,
        }
        rects.append(rect)

    return rects


def update_results(result, test_result, plots, plot_titles, remarks):
    """Update result details with test results, plots, plot titles, and remarks."""
    result_df = {
        fc.TEST_RESULT: [test_result],
    }
    result.details["Additional_results"] = result_df
    for plot in plots:
        if "plotly.graph_objs._figure.Figure" in str(type(plot)):
            result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        else:
            result.details["Plots"].append(plot)
    for plot_title in plot_titles:
        result.details["Plot_titles"].append(plot_title)
    for remark in remarks:
        result.details["Remarks"].append(remark)


def create_dataframes(passed_data, failed_data):
    """Create dataframe"""
    return pd.DataFrame(passed_data), pd.DataFrame(failed_data)


class PLFEventStateChecker:
    """define different state and different event"""

    def __init__(self, data: pd.DataFrame):
        self.data = data

    # Method to check if the row is in the 'idle' state
    def isInIdleState(self, index):
        """Check if the row at 'index' is in the 'idle' state."""
        return (
            self.data.at[index, "relocalizationStatus"] == StateChange.INACTIVE
            and self.data.at[index, "mapDataFileSystemStatus"] == StateChange.INACTIVE
            and self.data.at[index, "numValidRelocalizedMaps"] == 0
        )

    # Method to check if the row is in the 'failed' state
    def isInFailedState(self, index: int) -> bool:
        """Check if the row at 'index' is in the 'failed' state."""
        return (
            self.data.at[index, "relocalizationStatus"] == StateChange.FAILED
            and self.data.at[index, "mapDataFileSystemStatus"] == StateChange.FAILED
            and self.data.at[index, "numValidRelocalizedMaps"] == 0
        )

    # Method to check if the row is in the 'waitmap' state
    def isInWaitmapState(self, index):
        """Check if the row at 'index' is in the 'waitmap' state."""
        return (
            self.data.at[index, "relocalizationStatus"] == StateChange.INACTIVE
            and self.data.at[index, "mapDataFileSystemStatus"] == StateChange.ONGOING
            and self.data.at[index, "numValidRelocalizedMaps"] == 0
        )

    # Method to check if the row is in the 'localization' state
    def isInLocalizationState(self, index):
        """Check if the row at 'index' is in the 'localization' state."""
        return (
            self.data.at[index, "relocalizationStatus"] == StateChange.ONGOING
            and self.data.at[index, "mapDataFileSystemStatus"] == StateChange.INACTIVE
            and self.data.at[index, "numValidRelocalizedMaps"] == 1
        )

    # Example method to check if the event is a 'load' event
    def isLoadEvent(self, index, previous_row):
        """Check if the row at 'index' matches the 'load' event conditions."""
        return (
            self.data.at[index, "numValidRequests_nu"] == 1
            and self.data.at[index, "mapID"] != self.data.at[previous_row, "mapID"]
        )

    def isStopEvent(self, index):
        """Check if the row at 'index' matches the 'stop' event conditions."""
        return self.data.at[index, "numValidRequests_nu"] == 0

    def isReinitEvent(self, index, previous_row):
        """Check if the row at 'index' matches the 'reinit' event conditions."""
        return (
            self.data.at[index, "numValidRequests_nu"] == 1
            and self.data.at[index, "mapID"] == self.data.at[previous_row, "mapID"]
            and self.data.at[index, "initialLocalizationRequest"] == fh.TRUE
        )

    def isContinueEvent(self, index, previous_row):
        """Check if the row at 'index' matches the 'continue' event conditions."""
        return (
            self.data.at[index, "numValidRequests_nu"] == 1
            and self.data.at[index, "mapID"] == self.data.at[previous_row, "mapID"]
            and self.data.at[index, "initialLocalizationRequest"] == fh.FALSE
        )

    def isLoadResultSuccess(self, index):
        """Check if the row at 'index' matches the 'load_result' event conditions."""
        return self.data.at[index, "result"] == DataOperationResult.DATA_OPERATION_SUCCESSFUL

    def isLoadResultError(self, index):
        """Check if the row at 'index' matches the 'load_result' event conditions."""
        return self.data.at[index, "result"] == DataOperationResult.DATA_OPERATION_FAILED

    def isLoadResultNone(self, index):
        """Check if the row at 'index' matches the 'load_result' event conditions."""
        return (
            self.data.at[index, "result"] != DataOperationResult.DATA_OPERATION_FAILED
            and self.data.at[index, "result"] != DataOperationResult.DATA_OPERATION_SUCCESSFUL
        )


class PLFBuildSummary:
    """defined build summary"""

    def __init__(self, plf_signals: PLF_Signals):
        """Initialize with a PLF_Signals instance."""
        self.plf_signals = plf_signals

    def get_signal_names(self):
        """Fetch state and event signals in dictionary format."""
        # Define state and event signals here
        state_signals = {
            self.plf_signals.get_complete_signal_name(self.plf_signals.Columns.RELOCALIZATION_STATUS),
            self.plf_signals.get_complete_signal_name(self.plf_signals.Columns.MAP_DATA_FILE_SYSTEM_STATUS),
            self.plf_signals.get_complete_signal_name(self.plf_signals.Columns.NUM_VALID_RELOCALIZATION_MAP),
        }
        event_signals = {
            self.plf_signals.get_complete_signal_name(self.plf_signals.Columns.NUM_VALID_REQUEST),
            self.plf_signals.get_complete_signal_name(self.plf_signals.Columns.MAP_ID),
            self.plf_signals.get_complete_signal_name(self.plf_signals.Columns.INITIAL_LOCALIZATION_REQUEST),
        }
        return state_signals, event_signals

    def check_state(self, state_type: str):
        """Check if the row at 'index' matches the given state conditions."""
        if state_type == "idle":
            return (
                f"{self.plf_signals.Columns.RELOCALIZATION_STATUS} = {StateChange.INACTIVE} ",
                f"{self.plf_signals.Columns.MAP_DATA_FILE_SYSTEM_STATUS} = {StateChange.INACTIVE} ",
                f"{self.plf_signals.Columns.NUM_VALID_RELOCALIZATION_MAP} = 0 ",
            )
        elif state_type == "failed":
            return (
                f"{self.plf_signals.Columns.RELOCALIZATION_STATUS} = {StateChange.FAILED} ",
                f"{self.plf_signals.Columns.MAP_DATA_FILE_SYSTEM_STATUS} = {StateChange.FAILED} ",
                f"{self.plf_signals.Columns.NUM_VALID_RELOCALIZATION_MAP} = 0",
            )
        elif state_type == "waitmap":
            return (
                f"{self.plf_signals.Columns.RELOCALIZATION_STATUS} = {StateChange.INACTIVE} ",
                f"{self.plf_signals.Columns.MAP_DATA_FILE_SYSTEM_STATUS} = {StateChange.ONGOING} ",
                f"{self.plf_signals.Columns.NUM_VALID_RELOCALIZATION_MAP} = 0",
            )
        elif state_type == "localization":
            return (
                f"{self.plf_signals.Columns.RELOCALIZATION_STATUS} = {StateChange.ONGOING} ",
                f"{self.plf_signals.Columns.MAP_DATA_FILE_SYSTEM_STATUS} = {StateChange.INACTIVE} ",
                f"{self.plf_signals.Columns.NUM_VALID_RELOCALIZATION_MAP} = 1",
            )
        else:
            raise ValueError(f"Unknown state type: {state_type}")

    def check_event(self, event_type: str):
        """Check if the row at 'index' matches the given event conditions."""
        if event_type == "load":
            return (
                f"{self.plf_signals.Columns.NUM_VALID_REQUEST} = 1 ",
                f"{self.plf_signals.Columns.MAP_ID} != previous_mapID ",
            )

        elif event_type == "stop":
            return f"{self.plf_signals.Columns.NUM_VALID_REQUEST} = 0 "

        elif event_type == "reinit":
            return (
                f"{self.plf_signals.Columns.NUM_VALID_REQUEST} = 1 ",
                f"{self.plf_signals.Columns.MAP_ID} = previous_mapID ",
                f"{self.plf_signals.Columns.INITIAL_LOCALIZATION_REQUEST} = 0 ",
            )

        elif event_type == "continue":
            return (
                f"{self.plf_signals.Columns.NUM_VALID_REQUEST} = 1 ",
                f"{self.plf_signals.Columns.MAP_ID} == previous_mapID ",
                f"{self.plf_signals.Columns.INITIAL_LOCALIZATION_REQUEST} = 1 ",
            )
        elif event_type == "continue_success":
            return (
                f"{self.plf_signals.Columns.NUM_VALID_REQUEST} = 1 ",
                f"{self.plf_signals.Columns.MAP_ID} == previous_mapID ",
                f"{self.plf_signals.Columns.INITIAL_LOCALIZATION_REQUEST} = 1 ",
                f"{self.plf_signals.Columns.LOAD_RESULT} = 1 ",
            )
        elif event_type == "continue_error":
            return (
                f"{self.plf_signals.Columns.NUM_VALID_REQUEST} = 1 ",
                f"{self.plf_signals.Columns.MAP_ID} == previous_mapID ",
                f"{self.plf_signals.Columns.INITIAL_LOCALIZATION_REQUEST} = 1 ",
                f"{self.plf_signals.Columns.LOAD_RESULT} = 0 ",
            )
        else:
            # Raise an error if the event_type is unknown
            raise ValueError(f"Unknown event type: {event_type}")

    def build_signal_summary(
        self, event, current_state, next_state, event_result, current_state_result, next_state_result
    ):
        """Builds a signal summary, handling both current state only or the original full summary."""
        # Check if event is None and only current state is provided
        if event is None and current_state is not None and next_state is None:
            state_signals, _ = self.get_signal_names()  # We don't need event_signals here
            return pd.DataFrame(
                {
                    "Signal_Evaluation": {
                        "1": state_signals,
                    },
                    "Result": {
                        "1": self.check_state(current_state),
                    },
                    "State": {
                        "1": f"{current_state} = {current_state_result}",
                    },
                }
            )

        if event is None and current_state is None and next_state is None:
            state_signals, _ = self.get_signal_names()  # We don't need event_signals here
            return pd.DataFrame(
                {
                    "Signal_Evaluation": {
                        "1": state_signals,
                    },
                    "Result": {
                        "1": "In any one state of the following states (Idle, Localization, Waitmap, Failed), "
                        "if it matches, the state is considered valid.)"
                    },
                    "State": {
                        "1": current_state_result,
                    },
                }
            )

        # Default behavior (original code)
        state_signals, event_signals = self.get_signal_names()

        return pd.DataFrame(
            {
                "Signal_Evaluation": {
                    "1": event_signals,
                    "2": state_signals,
                    "3": state_signals,
                },
                "Result": {
                    "1": self.check_event(event),
                    "2": self.check_state(current_state),
                    "3": self.check_state(next_state),
                },
                "Event": {"1": f"{event} = {event_result}", "2": "NA", "3": "NA"},
                "Current_state": {"1": "NA", "2": f"{current_state} = {current_state_result}", "3": "NA"},
                "Next_state": {"1": "NA", "2": "NA", "3": f"{next_state} = {next_state_result}"},
            }
        )


class MAPEventStateChecker:
    """define different state and different event"""

    def __init__(self, data: pd.DataFrame):
        self.data = data

    # Method to check if the row is in the 'idle' state
    def isInIdleState(self, index):
        """Check if the row at 'index' is in the 'idle' state."""
        return (
            self.data.at[index, "mapRecordingStatus"] == StateChange.INACTIVE
            and self.data.at[index, "mapDataFileSystemStatus"] == StateChange.INACTIVE
        )

    # Method to check if the row is in the 'error' state
    def isInErrorState(self, index: int) -> bool:
        """Check if the row at 'index' is in the 'error' state."""
        return (
            self.data.at[index, "mapRecordingStatus"] == StateChange.FAILED
            and self.data.at[index, "mapDataFileSystemStatus"] == StateChange.FAILED
        )

    # Method to check if the row is in the 'mapping' state
    def isInMappingState(self, index):
        """Check if the row at 'index' is in the 'mapping' state."""
        return (
            self.data.at[index, "mapRecordingStatus"] == StateChange.ONGOING
            and self.data.at[index, "mapDataFileSystemStatus"] == StateChange.INACTIVE
        )

    # Method to check if the row is in the 'finished' state
    def isInFinishedState(self, index):
        """Check if the row at 'index' is in the 'finished' state."""
        return (
            self.data.at[index, "mapRecordingStatus"] == StateChange.FINISHED
            and self.data.at[index, "mapDataFileSystemStatus"] == StateChange.SUCCESS
        )

    # Method to check if the row is in the 'saving' state
    def isInSavingState(self, index):
        """Check if the row at 'index' is in the 'saving' state."""
        return (
            self.data.at[index, "mapRecordingStatus"] == StateChange.ONGOING
            and self.data.at[index, "mapDataFileSystemStatus"] == StateChange.ONGOING
        )

    def isParameterHandlerSuccessful(self, index, previous_index):
        """Check if the row at 'index' matches the 'isParameterHandler_Successful' event conditions."""
        return (
            self.data.at[index, "result"] == DataOperationResult.DATA_OPERATION_SUCCESSFUL
            and self.data.at[index, "MP_mapID"] == self.data.at[previous_index, "MP_mapID"]
        )

    def isParameterHandlerFailed(self, index, previous_index):
        """Check if the row at 'index' matches the 'ParameterHandler_Failed' event conditions."""
        return (
            self.data.at[index, "MP_mapID"] == self.data.at[previous_index, "MP_mapID"]
            and self.data.at[index, "result"] == DataOperationResult.DATA_OPERATION_FAILED
        )

    def isParameterHandlerWorking(self, index):
        """Check if the row at 'index' matches the 'ParameterHandler_Working' event conditions."""
        return (
            self.data.at[index, "result"] == DataOperationResult.DATA_OPERATION_SUCCESSFUL
            and self.data.at[index, "MP_mapID"] == fh.INVALID_MAP_ID
        )

    def isStartEvent(self, index, previous_index):
        """Check if the row at 'index' matches the 'start' event conditions."""
        return (
            self.data.at[index, "storeRequest"] == fh.FALSE
            and self.data.at[index, "MP_mapID"] != self.data.at[previous_index, "MP_mapID"]
        )

    def isStopEvent(self, index):
        """Check if the row at 'index' matches the 'stop' event conditions."""
        return self.data.at[index, "MP_mapID"] == fh.INVALID_MAP_ID

    def isStoreEvent(self, index, previous_index):
        """Check if the row at 'index' matches the 'store' event conditions."""
        return (
            self.data.at[index, "storeRequest"] == fh.TRUE
            and self.data.at[index, "MP_mapID"] == self.data.at[previous_index, "MP_mapID"]
        )

    def isContinueEvent(self, index, previous_index):
        """Check if the row at 'index' matches the 'continue' event conditions."""
        return (
            self.data.at[index, "storeRequest"] == fh.FALSE
            and self.data.at[index, "MP_mapID"] == self.data.at[previous_index, "MP_mapID"]
        )


class MAPBuildSummary:
    """defined build summary"""

    def __init__(self, map_signals: MAP_Signals):
        """Initialize with a PLF_Signals instance."""
        self.map_signals = map_signals

    def get_signal_names(self):
        """Fetch state and event signals in dictionary format."""
        # Define state and event signals here
        state_signals = {
            self.map_signals.get_complete_signal_name(self.map_signals.Columns.MAP_RECORDING_STATUS),
            self.map_signals.get_complete_signal_name(self.map_signals.Columns.MAP_DATA_FILE_SYSTEM_DATA),
        }
        event_signals = {
            self.map_signals.get_complete_signal_name(self.map_signals.Columns.STORE_REQUEST),
            self.map_signals.get_complete_signal_name(self.map_signals.Columns.MAP_ID),
            self.map_signals.get_complete_signal_name(self.map_signals.Columns.SAVE_RESULT),
        }
        return state_signals, event_signals

    def check_state(self, state_type: str):
        """Check if the row at 'index' matches the given state conditions."""
        if state_type == "idle":
            return (
                f"{self.map_signals.Columns.MAP_RECORDING_STATUS} = {StateChange.INACTIVE} ",
                f"{self.map_signals.Columns.MAP_DATA_FILE_SYSTEM_DATA} = {StateChange.INACTIVE} ",
            )
        elif state_type == "error":
            return (
                f"{self.map_signals.Columns.MAP_RECORDING_STATUS} = {StateChange.FAILED} ",
                f"{self.map_signals.Columns.MAP_DATA_FILE_SYSTEM_DATA} = {StateChange.FAILED} ",
            )
        elif state_type == "saving":
            return (
                f"{self.map_signals.Columns.MAP_RECORDING_STATUS} = {StateChange.ONGOING} ",
                f"{self.map_signals.Columns.MAP_DATA_FILE_SYSTEM_DATA} = {StateChange.ONGOING} ",
            )
        elif state_type == "mapping":
            return (
                f"{self.map_signals.Columns.MAP_RECORDING_STATUS} = {StateChange.ONGOING} ",
                f"{self.map_signals.Columns.MAP_DATA_FILE_SYSTEM_DATA} = {StateChange.INACTIVE} ",
            )
        elif state_type == "finished":
            return (
                f"{self.map_signals.Columns.MAP_RECORDING_STATUS} = {StateChange.FINISHED} ",
                f"{self.map_signals.Columns.MAP_DATA_FILE_SYSTEM_DATA} = {StateChange.SUCCESS} ",
            )
        else:
            raise ValueError(f"Unknown state type: {state_type}")

    def check_event(self, event_type: str):
        """Check if the row at 'index' matches the given event conditions."""
        if event_type == "start":
            return (
                f"{self.map_signals.Columns.STORE_REQUEST} = {fh.FALSE} ",
                f"{self.map_signals.Columns.MAP_ID} != previous_mapID ",
            )

        elif event_type == "stop":
            return f"{self.map_signals.Columns.MAP_ID} = {fh.INVALID_MAP_ID} "

        elif event_type == "store":
            return (
                f"{self.map_signals.Columns.STORE_REQUEST} = {fh.TRUE} ",
                f"{self.map_signals.Columns.MAP_ID} = previous_mapID ",
            )

        elif event_type == "continue":
            return (
                f"{self.map_signals.Columns.STORE_REQUEST} = {fh.FALSE} ",
                f"{self.map_signals.Columns.MAP_ID} = previous_mapID ",
            )
        elif event_type == "store_error":
            return (
                f"{self.map_signals.Columns.SAVE_RESULT} = {DataOperationResult.DATA_OPERATION_FAILED}",
                f"{self.map_signals.Columns.MAP_ID} = previous_mapID ",
            )

        elif event_type == "store_success":
            return (
                f"{self.map_signals.Columns.SAVE_RESULT} = {DataOperationResult.DATA_OPERATION_SUCCESSFUL}",
                f"{self.map_signals.Columns.MAP_ID} = previous_mapID ",
            )

        elif event_type == "store_start":
            return (
                f"{self.map_signals.Columns.SAVE_RESULT} != {DataOperationResult.DATA_OPERATION_SUCCESSFUL}",
                f"{self.map_signals.Columns.SAVE_RESULT} != {DataOperationResult.DATA_OPERATION_FAILED}",
                f"{self.map_signals.Columns.MAP_ID} = {fh.INVALID_MAP_ID} ",
            )
        else:
            # Raise an error if the event_type is unknown
            raise ValueError(f"Unknown event type: {event_type}")

    def build_signal_summary(
        self, event, current_state, next_state, event_result, current_state_result, next_state_result
    ):
        """Builds a signal summary, handling both current state only or the original full summary."""
        # Check if event is None and only current state is provided
        if event is None and current_state is not None and next_state is None:
            state_signals, _ = self.get_signal_names()  # We don't need event_signals here
            return pd.DataFrame(
                {
                    "Signal_Evaluation": {
                        "1": state_signals,
                    },
                    "Result": {
                        "1": self.check_state(current_state),
                    },
                    "State": {
                        "1": f"{current_state} = {current_state_result}",
                    },
                }
            )
        if event is None and current_state is None and next_state is None:
            state_signals, _ = self.get_signal_names()  # We don't need event_signals here
            return pd.DataFrame(
                {
                    "Signal_Evaluation": {
                        "1": state_signals,
                    },
                    "Result": {
                        "1": "In any one state of the following states (Idle, mapping, saving, finished, error) "
                        "if it matches, the state is considered valid.)"
                    },
                    "State": {
                        "1": current_state_result,
                    },
                }
            )

        # Default behavior (original code)
        state_signals, event_signals = self.get_signal_names()

        return pd.DataFrame(
            {
                "Signal_Evaluation": {
                    "1": event_signals,
                    "2": state_signals,
                    "3": state_signals,
                },
                "Result": {
                    "1": self.check_event(event),
                    "2": self.check_state(current_state),
                    "3": self.check_state(next_state),
                },
                "Event": {"1": f"{event} = {event_result}", "2": "NA", "3": "NA"},
                "Current_state": {"1": "NA", "2": f"{current_state} = {current_state_result}", "3": "NA"},
                "Next_state": {"1": "NA", "2": "NA", "3": f"{next_state} = {next_state_result}"},
            }
        )


def create_config(data_pairs, annotation_text, rects=None):
    """Returns: dict: Configuration dictionary."""
    if rects is None:
        rects = []  # Default to an empty list if no rectangles are provided

    # We assume data_pairs is a list of strings (column names) to be used in plotting
    config = {
        "data_pairs": data_pairs,  # Just using the list of column names
        "rects": rects,
        "annotation": {
            "text": annotation_text,
            "font_size": 15,
            "font_color": "Black",
        },
        "layout": {
            "xaxis_title": "uiCycleCounter",
            "yaxis_title": "State transition",
        },
    }
    return config


def create_plot(data, plot_titles, plots, remarks, config, final_data=None):
    """
    Create a plot using the provided data and optional configuration.

    Parameters:
        - data: DataFrame containing the main data to plot.
        - plot_titles: List to append plot titles.
        - plots: List to append plot figures.
        - remarks: List to append remarks.
        - config: Configuration dictionary containing the data_pairs, rects, annotation, and layout.
        - final_data: Optional DataFrame for final data to plot; if not provided, only main data will be plotted.
    """

    def add_trace(fig, x, y, name, marker_color=None):
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines+markers",
                line_shape="hv",
                name=name,
                marker=dict(color=marker_color) if marker_color else None,
            )
        )

    # Add initial elements to plot_titles, plots, and remarks
    plot_titles.append("")
    plots.append("")
    remarks.append("")

    fig = go.Figure()

    # Here, data_pairs is a list of strings (column names), so we need to treat it differently
    for col_name in config["data_pairs"]:
        # Assuming that each pair in the data_pairs list is a column name to be plotted against the index or other column
        x = data.index  # Typically, you plot against the index or another column like 'uiCycleCounter'
        y = data[col_name]  # Use the column name for y
        add_trace(fig, x, y, col_name)  # Add trace using column name as 'name'

        # If final_data is provided, we also plot it
        if final_data is not None:
            add_trace(fig, final_data.index, final_data[col_name], f"{col_name}_state_change", "green")

    # Determine rectangles and annotations positions based on config
    rects = config["rects"]
    annotation = config["annotation"]
    layout = config["layout"]

    # Add rectangles
    for rect in rects:
        fig.add_shape(
            type="rect",
            x0=rect["x_min"],
            y0=rect["y_min"],
            x1=rect["x_max"],
            y1=rect["y_max"],
            line=dict(color="RoyalBlue"),
            fillcolor="red" if "failed" in annotation["text"] else "green",
            opacity=0.3,
        )

    # Add annotations to each rectangle
    for rect in rects:
        fig.add_annotation(
            x=(rect["x_min"] + rect["x_max"]) / 2,
            y=(rect["y_min"] + rect["y_max"]) / 2,
            text=annotation["text"],
            showarrow=False,
            font=dict(size=annotation["font_size"], color=annotation["font_color"]),
            align="center",
        )

    # Update layout
    fig.update_layout(xaxis_title=layout["xaxis_title"], yaxis_title=layout["yaxis_title"])

    # Append figure to plots
    plots.append(fig)
    return plots


def update_plots(data, plot_titles, plots, remarks, data_pairs):
    """Updates plot titles, plots, and remarks based on the provided data pairs."""

    def add_trace(fig, x, y, name, marker_color=None):
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines+markers",
                line_shape="hv",
                name=name,
                marker=dict(color=marker_color) if marker_color else None,
            )
        )

    # Add initial elements to plot_titles, plots, and remarks
    plot_titles.append("")
    plots.append("")
    remarks.append("")

    fig = go.Figure()

    for col_name in data_pairs:
        # Assuming you are plotting against the index for each column in data_pairs
        x = data.index  # Typically, you plot against the index or another column
        y = data[col_name]  # Use the column name as y
        add_trace(fig, x, y, col_name)  # Add trace using the column name as the trace name

    plots.append(fig)
    return plots
