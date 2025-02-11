#!/usr/bin/env python3
"""This is the test case to validate that the maximum lateral error during the parking manoeuvres which are defined
in the scenario catalog shall not exceed 0.20 m.
"""

import logging
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
from tsf.core.results import (
    FALSE,
    TRUE,
    BooleanResult,
)
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.core.utilities import debug
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import MfCustomTeststepReport, convert_dict_to_pandas, get_color, rep
from pl_parking.PLP.MF.VEDODO.common import plot_graphs, plot_graphs_threshold
from pl_parking.PLP.MF.VEDODO.constants import CarMakerUrl

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "Anil A, uie64067"
__copyright__ = "2012-2024, Continental AG"
__version__ = "0.0.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

READER_NAME = "VehicleOdometryMaximumLateralError"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        CM_TIME = "cm_time"
        odoEstY = "odoEstY"
        odoCmRefY = "odoCmRefY"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.odoEstY: CarMakerUrl.odoEstY,
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.odoCmRefY: CarMakerUrl.odoCmRefY,
        }


@teststep_definition(
    step_number=1,
    name="The maximum lateral error during the parking manoeuvres which are defined in the scenario catalog shall "
    "not exceed 0.20 m.",
    description="The maximum lateral error during the parking manoeuvres which are defined in the scenario catalog"
    " shall not exceed 0.20 m.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoMaximulateralerror(TestStep):
    """The maximum lateral error during the parking manoeuvres which are defined in the scenario catalog shall
    not exceed 0.20 m".

    Objective
    ---------

    The maximum lateral error during the parking manoeuvres which are defined in the scenario catalog
    shall not exceed 0.20 m".

    Detail
    ------

    The maximum lateral error during the parking manoeuvres which are defined in the scenario catalog
    shall not exceed 0.20 m".
    """

    custom_report = MfCustomTeststepReport

    def __init__(self):
        super().__init__()
        self.sig_summary = None

    def process(self, **kwargs):
        """Evaluating test case"""
        _log.debug("Starting processing...")
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)

        df: pd.DataFrame = self.readers[READER_NAME]
        # Ignoring first few frames to settle the algorithm
        ap_time = list(df[VedodoSignals.Columns.CM_TIME])[2:]
        gt_y = list(df[VedodoSignals.Columns.odoCmRefY])[2:]
        y_estimated = list(df[VedodoSignals.Columns.odoEstY])[2:]

        # Init variables
        max_expected_lateral_error: float = 0.20
        signal_summary = dict()
        lateral_deviate_list = list()

        for gy, ody in zip(gt_y, y_estimated):
            lateral_deviate_list.append(abs(gy - ody))
        max_lateral_error = max(lateral_deviate_list)

        if max_lateral_error > max_expected_lateral_error:
            evaluation_max_error_lat = (
                f"Evaluation for lateral error during the parking manoeuvres which are defined in the scenario "
                f"catalog, max the lateral error is {round(max_lateral_error, 3)}m and which is above the threshold "
                f"of {max_expected_lateral_error}m. Hence the test result is FAILED."
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE
        else:
            evaluation_max_error_lat = (
                f"Evaluation for lateral error during the parking manoeuvres which are defined in the scenario "
                f"catalog, max the lateral error is {round(max_lateral_error, 3)}m and which is within the threshold "
                f"of {max_expected_lateral_error}m. Hence the test result is PASSED."
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE

        signal_summary[CarMakerUrl.odoEstY] = evaluation_max_error_lat

        self.sig_summary = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_summary)
        remarks.append("")

        lateral_plot = plot_graphs(
            ap_time, y_estimated, CarMakerUrl.odoEstY, gt_y, CarMakerUrl.odoCmRefY, "Time[s]", "Distance[m]"
        )
        lateral_threshold_fig = plot_graphs_threshold(
            ap_time,
            lateral_deviate_list,
            "Lateral Position Deviation",
            max_expected_lateral_error,
            "Max Positional Error Threshold",
            "Time[s]",
            "Distance[m]",
        )

        plots.append(lateral_plot)
        plot_titles.append(" ")
        plots.append(lateral_threshold_fig)
        plot_titles.append(" ")

        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": get_color(test_result)},
        }
        self.result.details["Additional_results"] = additional_results_dict


@verifies("ReqId-2104248")
@testcase_definition(
    name="The maximum lateral error during the parking manoeuvres which are defined in the scenario catalog shall "
    "not exceed 0.20 m",
    description="The maximum lateral error during the parking manoeuvres which are defined in the scenario catalog "
    "shall not exceed 0.20 m",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2"
    "Fjazz.conti.de%2Frm4%2Fresources%2FBI_cn5csACxEe-JmbR7EsJ0UA&componentURI=https%3A%2F%2Fjazz.conti.de"
    "%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configurat"
    "ion=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class VedodoMaximulateralerrorTestcase(TestCase):
    """VedodoMaximulateralerror_Testcase test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoMaximulateralerror,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.

    """
    # Define your directory path to your measurements for debugging purposes
    _, testrun_id, cp = debug(
        VedodoMaximulateralerrorTestcase,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
        kpi_report=False,
        dev_report=True,
    )
    return testrun_id, cp


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"
    out_folder = working_directory / "out"

    main(temp_dir=out_folder, open_explorer=True)
