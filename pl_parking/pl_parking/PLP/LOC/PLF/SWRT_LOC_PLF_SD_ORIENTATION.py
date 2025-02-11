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
from pl_parking.PLP.LOC.common_ft_helper import PLF_Signals, create_config, create_plot, update_plots, update_results

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "PLF_SD_ORIENTATION"
loc_signal = PLF_Signals()


def build_signal_summary(result):
    """Will build signal summary"""
    return pd.DataFrame(
        {
            "Signal_Evaluation": {
                "1": f"{loc_signal.get_complete_signal_name(PLF_Signals.Columns.PLF_STD_ORIENTATION)},  ",
            },
            "Result": {
                "1": f"values of below signal should not be zero    " f"{PLF_Signals.Columns.PLF_STD_ORIENTATION}  "
            },
            "Verdict": {"1": f"{result}"},
        }
    )


@teststep_definition(
    step_number=1,
    name="LOC-PLF SD ORIENTATION",
    description="This test step will confirm that MappingAndLocalizationLowSpeed shall provide the estimate of the "
    "standard deviation of the ego vehicle orientation [sigmaPsi]rad.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, PLF_Signals)
class TestStepFtLOCOutputSDORIENTATION(TestStep):
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
        df = pd.DataFrame()
        plot_titles, plots, remarks = rep([], 3)
        signal_details = {}

        # Load signals

        df = pd.DataFrame(self.readers[SIGNAL_DATA])
        df.reset_index(drop=True, inplace=True)
        Required_signals = [
            "PLF_uiCycleCounter",
            "plf_std_heading_rad",
        ]
        df = df[Required_signals]

        # Check if data has been provided to continue with the validation
        # check if any value is zero
        plf_sd_orientation_missing = (df["plf_std_heading_rad"] == 0).any()
        test_result = fc.FAIL if plf_sd_orientation_missing else fc.PASS
        # Determine if the test passed or failed
        is_passed = test_result == fc.PASS

        # Set the measured result
        self.result.measured_result = TRUE if is_passed else FALSE

        # Build signal summary and remarks based on test result
        signal_details = build_signal_summary(test_result)
        if is_passed:
            remark = "State confirms that ego vehicle orientation [sigmaPsi]rad estimated correctly"
        else:
            remark = "Since test is failed, ego vehicle orientation [sigmaPsi]rad was not estimated correctly."

        # Create the HTML table for the signal summary
        signal_summary = build_html_table(signal_details, remark)
        plot_titles.append("")
        plots.append(signal_summary)

        # Create configuration and update plots accordingly
        config = create_config(Required_signals, annotation_text=" sd_orientation [sigmaPsi]rad")
        plots = (
            create_plot(df, plot_titles, plots, remarks, config)
            if is_passed
            else update_plots(df, plot_titles, plots, remarks, Required_signals[1:])
        )

        update_results(self.result, test_result, plots, plot_titles, remarks)


@verifies(
    "91007",
    "https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_ufIY0DRKEe-YwuveGcgWRQ#action=com.ibm.rqm.planning.home."
    "actionDispatcher&subAction=viewTestCase&id=91007",
)
@testcase_definition(
    name="LOC-PLF SD ORIENTATION",
    description="This test confirm that MappingAndLocalizationLowSpeed shall provide the estimate of the "
    "standard deviation of the ego vehicle orientation [sigmaPsi]rad.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI"
    "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_aJPgFDLREe-Om-dBJsz4EQ&vvc.configuration"
    "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fcm%2Fchangeset%2F_te6KgT7VEe-moNw0sxuQRA&componentURI"
    "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F"
    "_wxtVgiowEe-t3Zp5B0W8XQ",
)
class FtLOCOutputSDORIENTATION(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtLOCOutputSDORIENTATION]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.
    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.
    This is only meant to jump start testcase debugging.
    """
    debug(
        FtLOCOutputSDORIENTATION,
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
