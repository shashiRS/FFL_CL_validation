"""LOC PLF Test Cases"""

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
    PLF_Signals,
    PLFBuildSummary,
    PLFEventStateChecker,
    create_config,
    create_dataframes,
    create_plot,
    create_rects,
    get_time_intervals_with_indices,
    update_results,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "IDLE_STOP"
loc_signal = PLF_Signals()


@teststep_definition(
    step_number=1,
    name="LOC-PLF IDLE Stop state",
    description="This test step confirms that in idle state, after "
    "receiving stop event LOC shall remain in the idle state.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, PLF_Signals)
class TestStepFtLOCOutputIDLEStop(TestStep):
    """Transitions from the IDLE state,
    when stop event received, LOC shall remains in same state.
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
        data = pd.DataFrame()
        plot_titles, plots, remarks, remark = rep([], 4)
        signal_details = {}
        # Load signals

        reader = self.readers[SIGNAL_DATA]
        data = pd.DataFrame(reader)
        data.reset_index(drop=True, inplace=True)
        Required_signals = [
            "PLF_uiCycleCounter",
            "numValidRequests_nu",
            "relocalizationStatus",
            "mapDataFileSystemStatus",
            "numValidRelocalizedMaps",
        ]
        data = data[Required_signals]

        # Check if data has been provided to continue with the validation
        passed_data, failed_data = rep([], 2)
        # The result will be set to pass if the correct event is encountered (e.g., stop, continue, reinit, load).
        event_result = fc.FAIL
        # The current state will be marked as pass if the correct transition state is encountered before the event.
        current_state_result = fc.FAIL
        # The next state will be marked as pass if the system undergoes the correct transition after the event.
        next_state_result = fc.FAIL
        passed_data, failed_data = rep([], 2)
        checker = PLFEventStateChecker(data)

        # Evaluation part
        for index in range(1, len(data) - 1):
            # Check for stop event conditions
            if checker.isStopEvent(index):
                event_result = fc.PASS
                # Check for failed state conditions
                if checker.isInIdleState(index):
                    current_state_result = fc.PASS
                    next_index = index + 1  # Continue event detected
                    next_conditions_wrong = not checker.isInIdleState(next_index)
                    # Check for continue event conditions
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

        # Data pairs for plotting
        plf_summary = PLFBuildSummary(loc_signal)

        signal_details = plf_summary.build_signal_summary(
            event="stop",
            current_state="idle",
            next_state="idle",
            event_result=event_result,
            current_state_result=current_state_result,
            next_state_result=next_state_result,
        )
        remark = []

        # Determine the result and corresponding remarks
        # Determine the result and corresponding remarks
        self.result.measured_result = TRUE if test_result == fc.PASS else FALSE
        remark_message = (
            "The transition state change indicates that the state remains in an idle state when a stop event arrives."
            if self.result.measured_result is TRUE
            else "A stop event occurred in an idle state, yet it failed to stay in the idle state."
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
            "transition state change" if self.result.measured_result is TRUE else "transition state change failed"
        )

        # Create plots
        time_intervals = get_time_intervals_with_indices(df_to_plot["PLF_uiCycleCounter"].tolist(), threshold=1)
        rects = create_rects(time_intervals, df_to_plot)
        config = create_config(Required_signals[1:], rects=rects, annotation_text=annotation_text)
        plots = create_plot(data, plot_titles, plots, remarks, config, df_to_plot)
        update_results(self.result, test_result, plots, plot_titles, remarks)


@verifies(
    "93837",
    "https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_ufIY0DRKEe-YwuveGcgWRQ#action=com.ibm.rqm.planning.home."
    "actionDispatcher&subAction=viewTestCase&id=93837",
)
@testcase_definition(
    name="LOC-PLF IDLE Stop state",
    description="This test ensure that in idle state, after receiving stop event LOC shall remain in the idle state.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI"
    "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_vcU_oIf2Ee-ZB7Q23GLe5g&vvc.configuration"
    "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fcm%2Fchangeset%2F_Q5BlUIb5Ee-ZB7Q23GLe5g&componentURI"
    "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F"
    "_wxtVgiowEe-t3Zp5B0W8XQ",
)
class FtLOCOutputIDLEStop(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtLOCOutputIDLEStop]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.
    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.
    This is only meant to jump start testcase debugging.
    """
    debug(
        FtLOCOutputIDLEStop,
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
