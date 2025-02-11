"""LOC MAP Test Cases"""

import logging
import os
import tempfile
from pathlib import Path

import pandas as pd
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import TestCase, TestStep, register_signals, testcase_definition, teststep_definition, verifies
from tsf.core.utilities import debug

import pl_parking.common_constants as fc
import pl_parking.PLP.LOC.MAP.constants as fh
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    build_html_table,
    rep,
)
from pl_parking.PLP.LOC.common_ft_helper import (
    MAP_Signals,
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

SIGNAL_DATA = "SIGNAL_DATA"
loc_signal = MAP_Signals()


def build_signal_summary(pre_condition_result, test_result):
    """Will build signal summary"""
    return pd.DataFrame(
        {
            "Signal_Evaluation": {
                "1": f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.MAP_DATA_FILE_SYSTEM_DATA)} ,"
                f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.MAP_RECORDING_STATUS)} ",
                "2": f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.MAP_ID)} ,"
                f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.MAP_DATA_MAP_ID)} "
                f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.SAVE_RESULT)} ",
            },
            "Result": {
                "1": f"and {MAP_Signals.Columns.MAP_RECORDING_STATUS} == {StateChange.ONGOING}(ongoing) "
                f"and {MAP_Signals.Columns.MAP_DATA_FILE_SYSTEM_DATA} == {StateChange.ONGOING}(ongoing)"
                f"which indicate map is in saving state.",
                "2": f"{MAP_Signals.Columns.MAP_ID}(before saving) == {MAP_Signals.Columns.MAP_DATA_MAP_ID}(after saving)"
                f" and  {MAP_Signals.Columns.SAVE_RESULT} == 1  "
                f"   provided an acknowledgement if all the metadata and data from the in memory map "
                f"was saved successfully.",
            },
            "Verdict": {"1": f"{pre_condition_result}", "2": f"{test_result}"},
        }
    )


@teststep_definition(
    step_number=1,
    name="LOC_MAP_SAVING_MapSavedSuccess ",
    description="This test step confirms that component shall wait for an acknowledgement if all the "
    "metadata and data from the in memory map was saved successfully.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MAP_Signals)
class TestStepFtLOCOutputSAVINGMapSavedSuccess(TestStep):
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
        pre_condition_result = fc.NOT_ASSESSED
        data = pd.DataFrame()
        plot_titles, plots, remarks = rep([], 3)
        signal_details = {}

        # Load signals

        data = pd.DataFrame(self.readers[SIGNAL_DATA])
        data.reset_index(drop=True, inplace=True)
        Required_signals = [
            "uiCycleCounter",
            "MP_mapID",
            "mapRecordingStatus",
            "mapDataFileSystemStatus",
            "MAP_Data_mapID",
            "result",
        ]
        data = data[Required_signals]
        matching_indices = []
        # Check if data has been provided to continue with the validation
        result_data = []
        checker = MAPEventStateChecker(data)
        """Evaluation part"""
        # which indicate map is in saving state
        for index in range(len(data) - 1):
            next_index = index + 1
            if checker.isInMappingState(index) and checker.isInSavingState(next_index):
                # If all conditions are met, store the index
                matching_indices.append(index)
                pre_condition_result = fc.PASS

        pre_condition_result = fc.PASS if pre_condition_result == fc.PASS else fc.FAIL

        for index in matching_indices:
            if index < len(data):
                if (
                    any(data.at[index + i, "MP_mapID"] == data.at[index + i, "MAP_Data_mapID"] for i in range(1, 3))
                    and data.at[index + 1, "result"] == fh.TRUE
                ):
                    result_data.extend(data.iloc[index + 1 : index + 3])

        final_df = pd.DataFrame(result_data)
        test_result = fc.FAIL if final_df.empty else fc.PASS

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
            remark = "provided an acknowledgement if all the metadata and data from the in memory map was saved successfully."
        else:
            self.result.measured_result = FALSE
            final_df = data
            remark = "Not received an acknowledgement if all the metadata and data from the in memory map was saved successfully."
        signal_details = build_signal_summary(pre_condition_result, test_result)
        signal_summary = build_html_table(signal_details, remark)
        plot_titles.append("")
        annotation_text = "map saved success" if self.result.measured_result is TRUE else "failed-map saving"
        plots.append(signal_summary)
        remarks.append(remark)
        time_intervals = get_time_intervals_with_indices(final_df["uiCycleCounter"].tolist(), threshold=1)
        rects = create_rects(time_intervals, final_df)
        config = create_config(Required_signals, rects=rects, annotation_text=annotation_text)
        plots = create_plot(data, plot_titles, plots, remarks, config, final_df)
        update_results(self.result, test_result, plots, plot_titles, remarks)


@verifies(
    "83244",
    "https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_ufIY0DRKEe-YwuveGcgWRQ#action=com.ibm.rqm.planning.home."
    "actionDispatcher&subAction=viewTestCase&id=83244",
)
@testcase_definition(
    name="LOC_MAP_SAVING_MapSavedSuccess ",
    description="This test ensure component shall wait for an acknowledgement if all the metadata "
    "and data from the in memory map was saved successfully.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI"
    "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_FjoDRipHEe-t3Zp5B0W8XQ&vvc.configuration"
    "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fcm%2Fchangeset%2F_te6KgT7VEe-moNw0sxuQRA&componentURI"
    "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F"
    "_wxtVgiowEe-t3Zp5B0W8XQ",
)
class FtLOCOutputSAVINGMapSavedSuccess(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtLOCOutputSAVINGMapSavedSuccess]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.
    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.
    This is only meant to jump start testcase debugging.
    """
    debug(
        FtLOCOutputSAVINGMapSavedSuccess,
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
