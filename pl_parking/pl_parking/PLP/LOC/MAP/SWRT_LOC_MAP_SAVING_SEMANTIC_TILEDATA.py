"""LOC MAP Test Cases"""

import logging
import os
import tempfile
from pathlib import Path

import pandas as pd
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import TestCase, TestStep, register_signals, testcase_definition, teststep_definition, verifies
from tsf.core.utilities import debug
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
import pl_parking.PLP.LOC.MAP.constants as fh
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    build_html_table,
    rep,
)
from pl_parking.PLP.LOC.common_ft_helper import (
    MAPEventStateChecker,
    create_config,
    create_plot,
    create_rects,
    get_time_intervals_with_indices,
    update_results,
)
from pl_parking.PLP.LOC.MAP.constants import StateChange

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class MAP_Signals(SignalDefinition):
    """PAR230 signals to read for component ."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        CYCLE_COUNTER = "uiCycleCounter"
        MAP_DATA_FILE_SYSTEM_DATA = "mapDataFileSystemStatus"
        MAP_RECORDING_STATUS = "mapRecordingStatus"
        NEW_GRID = "grid_{}_{}"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CYCLE_COUNTER: "SIM VFB.MapInstance.recordingResultPort.sSigHeader.uiCycleCounter",
            self.Columns.MAP_DATA_FILE_SYSTEM_DATA: "SIM VFB.MapInstance.recordingResultPort.mapDataFileSystemStatus",
            self.Columns.MAP_RECORDING_STATUS: "SIM VFB.MapInstance.recordingResultPort.mapRecordingStatus",
        }
        # grid has multiple array signals, iterating to extract multiple array values.
        # signal is in the form of SIM VFB.MapInstance.saveMapDataRequestMessage.mapData.tiles[n].layers[n].grid[n]
        grid_list = []

        for tiles in range(9):
            for layers in range(5):
                grid_list.append((tiles, layers))
        # grid_array will store the grid multiple array signal and its values.
        grid_array = {
            self.Columns.NEW_GRID.format(x[0], x[1]): [
                f"SIM VFB.MapInstance.saveMapDataRequestMessage." f"mapData.tiles[{x[0]}].layers[{x[1]}].grid"
            ]
            for x in grid_list
        }
        self._properties.update(grid_array)

    def get_complete_signal_name(self, column_name):
        """Fetch the complete signal name for a given column name."""
        return self._properties.get(column_name, "Unknown column")


def convert_tileid_array_multiple_to_single(reader, signal_defintion):
    """Convert to single array"""
    data = pd.DataFrame(reader)
    uiCycleCounter_list = []
    mapRecordingStatus_list = []
    mapDataFileSystemStatus_list = []
    # This will store all grid values in one array
    grid_list = []

    # Loop through the range
    for tiles in range(9):
        for layers in range(5):
            for grid in range(255):
                # Extend lists with data from the DataFrame
                uiCycleCounter_list.extend(data["uiCycleCounter"])
                mapRecordingStatus_list.extend(data["mapRecordingStatus"])
                mapDataFileSystemStatus_list.extend(data["mapDataFileSystemStatus"])

                # Access the grid value using the formatted key with two indices
                grid_key = MAP_Signals.Columns.NEW_GRID.format(tiles, layers)
                # grid signal has multiple array so grid_list will convert multiple array to single array
                # SIM VFB.MapInstance.saveMapDataRequestMessage.mapData.tiles[n].layers[n].grid[n] will be converted to
                #  SIM VFB.MapInstance.saveMapDataRequestMessage.mapData.tiles.layers.grid
                grid_list.append(data[grid_key, grid])

    # Create new DataFrame
    new_df = pd.DataFrame(
        {
            "uiCycleCounter": uiCycleCounter_list,
            "mapRecordingStatus": mapRecordingStatus_list,
            "mapDataFileSystemStatus": mapDataFileSystemStatus_list,
            "grid": grid_list,  # Only grid values are included
        }
    )
    # final_df will have valid data, if the values are repeated it will drop duplicate and retain valid values
    final_df = new_df.drop_duplicates()
    return final_df


loc_signal = MAP_Signals()
SIGNAL_DATA = "SIGNAL_DATA"


def build_signal_summary(pre_condition_result, test_result):
    """Will build signal summary"""
    return pd.DataFrame(
        {
            "Signal_Evaluation": {
                "1": f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.MAP_DATA_FILE_SYSTEM_DATA)} ,"
                f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.MAP_RECORDING_STATUS)} ",
                "2": f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.NEW_GRID)} ,",
            },
            "Result": {
                "1": f"and {MAP_Signals.Columns.MAP_RECORDING_STATUS} == {StateChange.ONGOING}(ongoing) "
                f"and {MAP_Signals.Columns.MAP_DATA_FILE_SYSTEM_DATA} == {StateChange.ONGOING}(ongoing)"
                f"which indicate map is in saving state.",
                "2": f"{MAP_Signals.Columns.NEW_GRID} Should be greater than 1"
                f"   list of Semantic TileData on its output port is updated.",
            },
            "Verdict": {"1": f"{pre_condition_result}", "2": f"{test_result}"},
        }
    )


@teststep_definition(
    step_number=1,
    name="LOC_MAP_SAVING_ResultSemanticTileData ",
    description="This test step confirms that component shall provide a list of SemanticTileData on its output port.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MAP_Signals, start_timestamp=897832287, end_timestamp=897832387)
class TestStepFtLOCOutputSAVINGResultSemanticTileData(TestStep):
    """Transitions from the ERROR state,
    when continue event received, map shall move from error state to error state
    """

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # Define variables
        test_result = fc.NOT_ASSESSED
        test_fail_message = None
        pre_condition_result = fc.NOT_ASSESSED
        data = pd.DataFrame()
        plot_titles, plots, remarks = rep([], 3)
        signal_details = {}

        # Load signals
        reader = self.readers[SIGNAL_DATA]
        data = convert_tileid_array_multiple_to_single(reader, loc_signal)
        data.reset_index(drop=True, inplace=True)

        matching_indices = []
        # Check if data has been provided to continue with the validation
        test_fail_message = None
        result_data = []
        checker = MAPEventStateChecker(data)
        # which indicate map is in saving state
        for index in range(len(data) - 1):
            next_index = index + 1
            if checker.isInMappingState(index) and checker.isInSavingState(next_index):
                # If all conditions are met, store the index
                matching_indices.append(index + 1)
                pre_condition_result = fc.PASS
        pre_condition_result = fc.PASS if pre_condition_result == fc.PASS else fc.FAIL
        # TODO later to check weather grid have correct values
        # checking weather gird has some valid value other than 0
        # SIM VFB.MapInstance.saveMapDataRequestMessage.mapData.tiles[n].layers[n].grid[n] is the signal to be checked
        # weather it has some valid values
        for index in matching_indices:
            if index < len(data):
                if data.at[index + 1, "grid"] > 0:
                    result_data.append(data.iloc[index])
                    result_data.append(data.iloc[index + 1])
                    result_data.append(data.iloc[index + 2])

        final_df = pd.DataFrame(result_data)
        test_result = fc.FAIL if final_df.empty else fc.PASS

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
            signal_details = build_signal_summary(pre_condition_result, test_result)
            remark = "provided a list of Semantic TileData on its output port"
            signal_summary = build_html_table(signal_details, remark)
            plot_titles.append("")
            plots.append(signal_summary)
            remarks.append("")
            time_intervals = get_time_intervals_with_indices(final_df["uiCycleCounter"].tolist(), threshold=1)
            rects = create_rects(time_intervals, final_df)
            data_pairs = [
                ("uiCycleCounter", "mapRecordingStatus", "MAP_RECORDING_STATUS", None),
                ("uiCycleCounter", "mapDataFileSystemStatus", "MAP_DATA_FILE_SYSTEM_DATA", None),
                ("uiCycleCounter", "grid", "GRID", None),
            ]
            config = create_config(data_pairs, rects=rects, annotation_text="Semantic TileData")
            plots = create_plot(data, plot_titles, plots, remarks, config, final_df)

        else:
            self.result.measured_result = FALSE
            test_fail_message = "Failed hence list of Semantic TileData on its output port is not updated."
            remarks.append(test_fail_message)
            signal_details = build_signal_summary(pre_condition_result, test_result)
            remark = "Since test is failed Semantic TileData on its output port is not updated."
            signal_summary = build_html_table(signal_details, remark)
            plot_titles.append("")
            plots.append(signal_summary)

        update_results(self.result, test_result, plots, plot_titles, remarks)


@verifies(
    "83251",
    "https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_ufIY0DRKEe-YwuveGcgWRQ#action=com.ibm.rqm.planning.home."
    "actionDispatcher&subAction=viewTestCase&id=83251",
)
@testcase_definition(
    name="LOC_MAP_SAVING_ResultSemanticTileData ",
    description="This test ensure that  component shall provide a list of SemanticTileData on its output port.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI"
    "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_FjncMSpHEe-t3Zp5B0W8XQ&vvc.configuration"
    "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fcm%2Fchangeset%2F_te6KgT7VEe-moNw0sxuQRA&componentURI"
    "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F"
    "_wxtVgiowEe-t3Zp5B0W8XQ",
)
class FtLOCOutputSAVINGResultSemanticTileData(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtLOCOutputSAVINGResultSemanticTileData]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.
    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.
    This is only meant to jump start testcase debugging.
    """
    debug(
        FtLOCOutputSAVINGResultSemanticTileData,
        os.path.join(fh.DEBUG_ROOT_FOLDER, fh.BSIG_PATH),
        temp_dir=temp_dir,
        open_explorer=open_explorer,
        kpi_report=False,
        dev_report=True,
        project_name="PAR230",
    )
    _log.debug("All done.")


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_loc"))

    data_folder = working_directory / "data"
    out_folder = working_directory / "out"

    main(temp_dir=out_folder, open_explorer=True)
