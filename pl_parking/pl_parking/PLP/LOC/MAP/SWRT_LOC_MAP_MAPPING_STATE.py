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
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, build_html_table, rep
from pl_parking.PLP.LOC.common_ft_helper import (
    MAP_Signals,
    MAPBuildSummary,
    MAPEventStateChecker,
    create_config,
    create_dataframes,
    create_plot,
    create_rects,
    get_time_intervals_with_indices,
    update_results,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "SIGNAL_DATA"
loc_signal = MAP_Signals()


@teststep_definition(
    step_number=1,
    name="LOC-MAP MAPPING State",
    description="This test step will confirm that it will realize an mapping state",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MAP_Signals)
class TestStepFtLOCOutputMAPPINGState(TestStep):
    """This test step confirms that it is in idle state"""

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
        data = pd.DataFrame()
        plot_titles, plots, remarks = rep([], 3)
        signal_details = {}
        passed_data, failed_data = rep([], 2)
        # Load signals
        reader = self.readers[SIGNAL_DATA]
        data = pd.DataFrame(reader)
        data.reset_index(drop=True, inplace=True)
        Required_signals = ["uiCycleCounter", "mapRecordingStatus", "mapDataFileSystemStatus"]

        """Evaluation part"""
        # check for state change
        checker = MAPEventStateChecker(data)
        for index in range(1, len(data) - 1):
            if not checker.isInMappingState(index):
                failed_data.append(data.iloc[index])
            else:
                passed_data.append(data.iloc[index])

        # Convert lists to DataFrames
        passed_df, failed_df = create_dataframes(passed_data, failed_data)

        # Determine test result
        if not passed_df.empty:
            test_result = fc.PASS
            current_state_result = fc.PASS
        else:
            test_result = fc.FAIL
            current_state_result = fc.FAIL
            if failed_df.empty:
                failed_df = data

        map_summary = MAPBuildSummary(loc_signal)

        signal_details = map_summary.build_signal_summary(
            event=None,
            current_state="mapping",
            next_state=None,
            event_result=None,
            current_state_result=current_state_result,
            next_state_result=None,
        )
        remark = []

        # Determine the result and corresponding remarks
        self.result.measured_result = TRUE if test_result == fc.PASS else FALSE
        remark_message = (
            "The transition state indicates that it realized an mapping state."
            if self.result.measured_result is TRUE
            else "The transition state indicates that it did not realize an mapping state."
        )
        remark.append(remark_message)

        # Build the signal summary
        signal_summary = build_html_table(signal_details, remark[0])
        plots = [signal_summary]
        plot_titles = [""]
        remarks = [remark[0]]

        # Choose DataFrame and annotation based on test result
        df_to_plot = passed_df if self.result.measured_result is TRUE else failed_df
        annotation_text = (
            "transition state" if self.result.measured_result is TRUE else "transition state failed"
        )

        # Create plots
        time_intervals = get_time_intervals_with_indices(df_to_plot["uiCycleCounter"].tolist(), threshold=1)
        rects = create_rects(time_intervals, df_to_plot)
        config = create_config(Required_signals[1:], rects=rects, annotation_text=annotation_text)
        plots = create_plot(data, plot_titles, plots, remarks, config, df_to_plot)
        update_results(self.result, test_result, plots, plot_titles, remarks)


@verifies(
    "75106",
    "https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_ufIY0DRKEe-YwuveGcgWRQ#action=com.ibm.rqm.planning.home."
    "actionDispatcher&subAction=viewTestCase&id=75106",
)
@testcase_definition(
    name="LOC-MAP MAPPING state",
    description="This test confirm that it will realize an mapping state.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI"
              "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_wa8L0FWUEe-WGbhflTJCAg&vvc.configuration"
              "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fcm%2Fchangeset%2F_te6KgT7VEe-moNw0sxuQRA&componentURI"
              "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F"
              "_wxtVgiowEe-t3Zp5B0W8XQ",
)
class FtLOCOutputMAPPINGState(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtLOCOutputMAPPINGState]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.
    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.
    This is only meant to jump start testcase debugging.
    """
    debug(
        FtLOCOutputMAPPINGState,
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
