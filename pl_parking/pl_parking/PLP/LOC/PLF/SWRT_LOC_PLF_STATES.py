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
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    build_html_table,
    rep,
)
from pl_parking.PLP.LOC.common_ft_helper import (
    PLF_Signals,
    PLFBuildSummary,
    PLFEventStateChecker,
    create_config,
    create_plot,
    create_rects,
    get_time_intervals_with_indices,
    update_results,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "PLF_STATES"
loc_signal = PLF_Signals()


@teststep_definition(
    step_number=1,
    name="LOC-PLF States",
    description="This test step will confirm that PLF shall be always in one of the following "
    "states: idle, localization, waitmap, failed.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, PLF_Signals)
class TestStepFtLOCOutputStates(TestStep):
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

        # Load signals

        data = pd.DataFrame(self.readers[SIGNAL_DATA])
        Required_signals = [
            "PLF_uiCycleCounter",
            "relocalizationStatus",
            "mapDataFileSystemStatus",
            "numValidRelocalizedMaps",
        ]
        data = data[Required_signals]
        data.reset_index(drop=True, inplace=True)

        # Check if data has been provided to continue with the validation
        """Evaluation part"""
        # Define valid states
        checker = PLFEventStateChecker(data)

        not_valid = 0
        for index in data.index[1 : len(data) - 1]:
            valid_states = [
                checker.isInIdleState(index),
                checker.isInLocalizationState(index),
                checker.isInWaitmapState(index),
                checker.isInFailedState(index),
            ]
            if all(result is False for result in valid_states):  # Checks if all are False
                not_valid = 1

        test_result = fc.FAIL if not_valid else fc.PASS
        plf_summary = PLFBuildSummary(loc_signal)

        signal_details = plf_summary.build_signal_summary(
            event=None,
            current_state=None,
            next_state=None,
            event_result=None,
            current_state_result=test_result,
            next_state_result=None,
        )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
            remark = "Confirms PLF shall be always in any one states (idle, localization, waitmap, failed)."
        else:
            self.result.measured_result = FALSE
            remark = "Confirms PLF is not in any states (idle, localization, waitmap, failed)."
        signal_summary = build_html_table(signal_details, remark)
        plot_titles.append("")
        annotation_text = "PLF States" if self.result.measured_result is TRUE else "failed-PLF States"
        plots.append(signal_summary)
        remarks.append(remark)
        time_intervals = get_time_intervals_with_indices(data["PLF_uiCycleCounter"].tolist(), threshold=1)
        rects = create_rects(time_intervals, data)
        config = create_config(Required_signals[1:], rects=rects, annotation_text=annotation_text)
        plots = create_plot(data, plot_titles, plots, remarks, config, data)
        update_results(self.result, test_result, plots, plot_titles, remarks)


@verifies(
    "112918",
    "https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_KZRFUDhlEe-YwuveGcgWRQ#action=com.ibm.rqm.planning."
    "home.actionDispatcher&subAction=viewTestCase&id=112918",
)
@testcase_definition(
    name="LOC-PLF States",
    description="This test confirm PLF shall be always in one of the following "
    "states: idle, localization, waitmap, failed.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI"
              "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_mvlrQIfxEe-ZB7Q23GLe5g&oslc_config.context"
              "=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324&componentURI"
              "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F"
              "_wxtVgiowEe-t3Zp5B0W8XQ",
)
class FtLOCOutputStates(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtLOCOutputStates]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.
    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.
    This is only meant to jump start testcase debugging.
    """
    debug(
        FtLOCOutputStates,
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
