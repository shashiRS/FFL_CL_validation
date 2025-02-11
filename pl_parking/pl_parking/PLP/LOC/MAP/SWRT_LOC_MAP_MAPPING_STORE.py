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

SIGNAL_DATA = "MAPPING_STORE"
loc_signal = MAP_Signals()


@teststep_definition(
    step_number=1,
    name="LOC-MAP MAPPING Store state",
    description="This test step confirms that in mapping state, after "
    "receiving Store event map is moved from mapping to saving state.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MAP_Signals)
class TestStepFtLOCOutputMAPPINGStore(TestStep):
    """Transitions from the MAPPING state,
    when store event received, map shall move from idle mapping to saving state
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
        data = pd.DataFrame(self.readers[SIGNAL_DATA])
        data.reset_index(drop=True, inplace=True)
        # Define variables
        # The result will be set to pass if the correct event is encountered (e.g., stop, continue, reinit, load).
        event_result = fc.FAIL
        # The current state will be marked as pass if the correct transition state is encountered before the event.
        current_state_result = fc.FAIL
        # The next state will be marked as pass if the system undergoes the correct transition after the event.
        next_state_result = fc.FAIL
        passed_data, failed_data = rep([], 2)
        Required_signals = [
            "uiCycleCounter",
            "MP_mapID",
            "storeRequest",
            "mapRecordingStatus",
            "mapDataFileSystemStatus",
        ]
        data = data[Required_signals]
        checker = MAPEventStateChecker(data)

        """Evaluation part"""
        # check for state change
        for index in range(1, len(data) - 1):
            previous_index = index - 1
            # Check for store event conditions
            if checker.isStoreEvent(index, previous_index):
                event_result = fc.PASS
                # Check for mapping state conditions
                if checker.isInMappingState(index):
                    current_state_result = fc.PASS
                    next_index = index + 1
                    next_conditions_wrong = not checker.isInSavingState(next_index)
                    # Check for nest transition conditions
                    if next_conditions_wrong:
                        failed_data.extend([data.iloc[index], data.iloc[next_index]])
                        next_state_result = fc.FAIL
                    else:
                        passed_data.extend([data.iloc[index], data.iloc[next_index]])
                        next_state_result = fc.PASS

        passed_df, failed_df = create_dataframes(passed_data, failed_data)

        # Determine test result
        if not passed_df.empty and failed_df.empty:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL
            if failed_df.empty:
                failed_df = data

        map_summary = MAPBuildSummary(loc_signal)

        signal_details = map_summary.build_signal_summary(
            event="store",
            current_state="mapping",
            next_state="saving",
            event_result=event_result,
            current_state_result=current_state_result,
            next_state_result=next_state_result,
        )
        remark = []

        # Determine the result and corresponding remarks
        self.result.measured_result = TRUE if test_result == fc.PASS else FALSE
        remark_message = (
            "The transition state change indicates that the state changed from mapping state to saving state."
            if self.result.measured_result is TRUE
            else "A store event occurred in an mapping state, yet the transition from the mapping state failed."
        )
        remark.append(remark_message)

        # Build the signal summary
        signal_summary = build_html_table(signal_details, remark[0])
        plots = [signal_summary]
        plot_titles = [""]
        remarks = [remark[0]]

        # Select DataFrame and annotation based on test result
        df_to_plot = passed_df if self.result.measured_result is TRUE else failed_df
        annotation_text = (
            "transition state change" if self.result.measured_result is TRUE else "transition state change failed"
        )

        # Create plots
        time_intervals = get_time_intervals_with_indices(df_to_plot["uiCycleCounter"].tolist(), threshold=1)
        rects = create_rects(time_intervals, df_to_plot)
        config = create_config(Required_signals[1:], rects=rects, annotation_text=annotation_text)
        plots = create_plot(data, plot_titles, plots, remarks, config, df_to_plot)
        update_results(self.result, test_result, plots, plot_titles, remarks)


@verifies(
    "71891",
    "https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_ufIY0DRKEe-YwuveGcgWRQ#action=com.ibm.rqm.planning.home."
    "actionDispatcher&subAction=viewTestCase&id=71891",
)
@testcase_definition(
    name="LOC-MAP MAPPING Store state",
    description="This test ensure that in Mapping state, after "
    "receiving Store event map shall move from mapping to saving state.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI="
    "https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_DguvgFYaEe-WGbhflTJCAg&vvc.configuration="
    "https%3A%2F%2Fjazz.conti.de%2Frm4%2Fcm%2Fchangeset%2F_te6KgT7VEe-moNw0sxuQRA&componentURI="
    "https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F"
    "_wxtVgiowEe-t3Zp5B0W8XQ",
)
class FtLOCOutputMAPPINGStore(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtLOCOutputMAPPINGStore]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.
    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.
    This is only meant to jump start testcase debugging.
    """
    debug(
        FtLOCOutputMAPPINGStore,
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
