#!/usr/bin/env python3
"""This is the test case to check the longitudinal and lateral positions"""

import logging
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
from tsf.core.results import FALSE, TRUE, BooleanResult
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
from pl_parking.PLP.MF.VEDODO.common import plot_graphs_signgle_signal
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

READER_NAME = "VedodoVelocityOdometerPositions"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        odoEstX = "odoEstX"
        odoEstY = "odoEstY"
        CM_TIME = "cm_time"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.odoEstX: CarMakerUrl.odoEstX,
            self.Columns.odoEstY: CarMakerUrl.odoEstY,
            self.Columns.CM_TIME: CarMakerUrl.time,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the position in (x,y).",
    description="The ESC Odometry shall provide the position in (x,y).",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedPositions(TestStep):
    """The ESC Odometry shall provide the position in (x,y).

    Objective
    ---------

    The ESC Odometry shall provide the position in (x,y).

    Detail
    ------

    The ESC Odometry shall provide the position in (x,y).
    """

    custom_report = MfCustomTeststepReport

    def __init__(self):
        super().__init__()
        self.sig_sum = None

    def process(self, **kwargs):
        """Evaluating test case"""
        _log.debug("Starting processing...")
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)
        df: pd.DataFrame = self.readers[READER_NAME]

        ap_time = list(df[VedodoSignals.Columns.CM_TIME])
        odo_x = list(df[VedodoSignals.Columns.odoEstX])
        odo_y = list(df[VedodoSignals.Columns.odoEstY])

        # Init variables
        signal_summary = dict()
        x_len = len(odo_x)
        y_len = len(odo_y)
        x_flag = True
        y_flag = True
        evaluation_x = ""
        evaluation_y = ""

        if x_len != y_len:
            evaluation = (
                f"The positions(x, y) signals data are having different length, position-x: {x_len} and "
                f"position-y: {y_len} length"
            )
        else:
            evaluation = (
                f"The positions(x, y) signals data are having equal length, position-x: {x_len} and "
                f"position-y: {y_len} length"
            )
        if not sum(odo_x):
            evaluation_x = "The position-x signal values are zero, no estimation data is available"
            x_flag = False
        if not sum(odo_y):
            evaluation_y = "The position-y signal values are zero, no estimation data is available"
            y_flag = False

        for x, y in zip(odo_x[10:], odo_y[10:]):  # ignoring first few frames
            if pd.isna(x) and x_flag:
                evaluation_x = "The position-x signal data having NAN values"
                x_flag = False
            if pd.isna(y) and y_flag:
                evaluation_y = "The position-y signal data having NAN values"
                y_flag = False

        if x_flag:
            evaluation_x = "The position-x signal data is having valid data"

        if y_flag:
            evaluation_y = "The position-y signal data is having valid data"

        if x_flag and y_flag:
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary["Estimated Position(x,y)"] = evaluation
        signal_summary[CarMakerUrl.odoEstX] = evaluation_x
        signal_summary[CarMakerUrl.odoEstY] = evaluation_y

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        x_plot = plot_graphs_signgle_signal(
            ap_time, odo_x, CarMakerUrl.odoEstX, "Estimated Position-X Signal", "Time[s]", "Distance[m]"
        )
        y_plot = plot_graphs_signgle_signal(
            ap_time, odo_y, CarMakerUrl.odoEstY, "Estimated Position-Y Signal", "Time[s]", "Distance[m]"
        )

        plot_titles.append(" ")
        plots.append(x_plot)
        plots.append(y_plot)

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


@verifies("ReqID_1386008")
@testcase_definition(
    name="The ESC Odometry shall provide the position in (x,y).",
    description="The ESC Odometry shall provide the position in (x,y).",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_3z4nUDaaEe6mrdm2_agUYg&oslc_config.context=https%3A%2F%2Fjazz.con"
    "ti.de%2Fgc%2Fconfiguration%2F17099&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K"
    "28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedPositionsTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedPositions,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedPositionsTestCase,
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
