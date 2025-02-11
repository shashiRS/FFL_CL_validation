"""LOC MAP Test Cases"""

import logging
import os
import tempfile
from pathlib import Path

import pandas as pd
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
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
    create_config,
    create_plot,
    create_rects,
    get_time_intervals_with_indices,
    update_results,
)
from pl_parking.PLP.LOC.MAP.constants import SigStatus

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "SIGNAL_DATA"
loc_signal = MAP_Signals()


def build_signal_summary(result):
    """Will build signal summary"""
    return pd.DataFrame(
        {
            "Signal_Evaluation": {
                "1": f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.MAP_SIG_STATUS)}  ,"
                f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.MAP_RECORDING_STATUS)}  , "
                f"{loc_signal.get_complete_signal_name(MAP_Signals.Columns.MAP_DATA_FILE_SYSTEM_DATA)}"
            },
            "Result": {
                "1": f"{MAP_Signals.Columns.MAP_SIG_STATUS} == {SigStatus.AL_SIG_STATE_OK} , "
                f"{MAP_Signals.Columns.MAP_RECORDING_STATUS} >= 0 and "
                f"{MAP_Signals.Columns.MAP_DATA_FILE_SYSTEM_DATA} >= 0 "
                f" which indicate all input signals are processed.",
            },
            "Verdict": {"1": f"{result}"},
        }
    )


@teststep_definition(
    step_number=1,
    name="LOC-MAP SIG State",
    description="This test step will confirm that MAP shall only process "
    "input signals if their signal state is AL_SIG_STATE_OK.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MAP_Signals)
class TestStepFtLOCOutputSIGState(TestStep):
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
        data = pd.DataFrame(self.readers[SIGNAL_DATA])
        Required_signals = ["uiCycleCounter", "mapRecordingStatus", "mapDataFileSystemStatus", "MAP_eSigStatus"]
        data = data[Required_signals]
        # Split the DataFrame based on the first occurrence of eSigStatus transitioning from 0 to 1
        map_before_sig_state_ok = data[data["MAP_eSigStatus"] == 0]
        map_after_sig_state_ok = data[data["MAP_eSigStatus"] == 1]

        # Extract the first index values for mapRecordingStatus and mapDataFileSystemStatus where esig state is init(0)
        first_mapRecordingStatus = map_before_sig_state_ok.iloc[0]["mapRecordingStatus"]
        first_mapDataFileSystemStatus = map_before_sig_state_ok.iloc[0]["mapDataFileSystemStatus"]

        # Check for the values remains same across the DataFrame
        map_sig_state_init = (
            (map_before_sig_state_ok["mapRecordingStatus"] == first_mapRecordingStatus)
            & (map_before_sig_state_ok["mapDataFileSystemStatus"] == first_mapDataFileSystemStatus)
        ).all()
        # Condition Check After Transition: eSigStatus is 1, other signals
        # INACTIVE = 0
        # ONGOING = 1
        # FAILED = 2
        # SUCCESS = 3
        map_sig_state_ok = (
            (map_after_sig_state_ok["MAP_eSigStatus"] == 1)
            & (map_after_sig_state_ok["mapDataFileSystemStatus"] >= 0)
            & (map_after_sig_state_ok["mapDataFileSystemStatus"] <= 3)
            & (map_after_sig_state_ok["mapRecordingStatus"] >= 0)
            & (map_after_sig_state_ok["mapRecordingStatus"] <= 3)
        ).all()

        test_result = fc.PASS if map_sig_state_ok and map_sig_state_init else fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
            remark = "MAP processed input signals as signal state is AL_SIG_STATE_OK."
        else:
            self.result.measured_result = FALSE
            remark = "MAP did not processed input signals as signal state was not AL_SIG_STATE_OK."
        signal_details = build_signal_summary(test_result)
        signal_summary = build_html_table(signal_details, remark)
        plot_titles.append("")
        annotation_text = (
            "eSigstate state ok" if self.result.measured_result is TRUE else "eSigstate state  not ok"
        )
        plots.append(signal_summary)
        remarks.append(remark)
        time_intervals = get_time_intervals_with_indices(data["uiCycleCounter"].tolist(), threshold=1)
        rects = create_rects(time_intervals, data)
        config = create_config(Required_signals, rects=rects, annotation_text=annotation_text)
        plots = create_plot(data, plot_titles, plots, remarks, config, data)
        update_results(self.result, test_result, plots, plot_titles, remarks)


@verifies(
    "77432",
    "https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_ufIY0DRKEe-YwuveGcgWRQ#action=com.ibm.rqm.planning.home."
    "actionDispatcher&subAction=viewTestCase&id=77432",
)
@testcase_definition(
    name="LOC-MAP SIG state",
    description="This test confirm that MAP shall only process input signals if their signal state is AL_SIG_STATE_OK.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI"
              "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_KdTqoFYbEe-WGbhflTJCAg&vvc.configuration"
              "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fcm%2Fchangeset%2F_te6KgT7VEe-moNw0sxuQRA&componentURI"
              "=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F"
              "_wxtVgiowEe-t3Zp5B0W8XQ",
)
class FtLOCOutputSIGState(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtLOCOutputSIGState]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.
    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.
    This is only meant to jump start testcase debugging.
    """
    debug(
        FtLOCOutputSIGState,
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
