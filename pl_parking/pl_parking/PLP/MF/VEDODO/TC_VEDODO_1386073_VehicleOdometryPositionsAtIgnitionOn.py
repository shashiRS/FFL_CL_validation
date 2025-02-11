#!/usr/bin/env python3
"""This is the test case to check the initial values of Longitudinal, Lateral positions and Yaw Rate
when Ignition is ON
"""

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

READER_NAME = "VedodoOdometerPositionsYawWhenIgnitionOn"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        odoEstX = "odoEstX"
        odoEstY = "odoEstY"
        CM_TIME = "cm_time"
        yawrate_estimation = "yawrate_estimation"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.odoEstX: CarMakerUrl.odoEstX,
            self.Columns.odoEstY: CarMakerUrl.odoEstY,
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.yawrate_estimation: CarMakerUrl.yawrate_estimation,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the positions(x,y) and yaw rate when ignition is On.",
    description="The ESC Odometry shall provide the positions(x,y) and yaw rate when ignition is On.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedPositionsAndYawRateWhenIgnitionOn(TestStep):
    """The ESC Odometry shall provide the positions(x,y) and yaw rate when ignition is On.

    Objective
    ---------

    The ESC Odometry shall provide the positions(x,y) and yaw rate when ignition is On.

    Detail
    ------

    The ESC Odometry shall provide the positions(x,y) and yaw rate when ignition is On.
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
        odo_yaw = list(df[VedodoSignals.Columns.yawrate_estimation])

        # Init variables
        signal_summary = dict()
        result_list = list()

        if not odo_x[0]:
            evaluation_x = (
                "The evaluation for Position-X, the initial value at Ignition is Zero(0), "
                "Hence the test result is PASSED"
            )
            result_list.append(True)
        else:
            evaluation_x = (
                "The evaluation for Position-X, the initial value at Ignition is Non-Zero, "
                "Hence the test result is FAILED"
            )
            result_list.append(False)
        if not odo_y[0]:
            evaluation_y = (
                "The evaluation for Position-Y, the initial value at Ignition is Zero(0), "
                "Hence the test result is PASSED"
            )
            result_list.append(True)
        else:
            evaluation_y = (
                "The evaluation for Position-Y, the initial value at Ignition is Non-Zero, "
                "Hence the test result is FAILED"
            )
            result_list.append(False)
        if not odo_yaw[0]:
            evaluation_yaw = (
                "The evaluation for Yaw Rate, the initial value at Ignition is Zero(0), "
                "Hence the test result is PASSED"
            )
            result_list.append(True)
        else:
            evaluation_yaw = (
                "The evaluation for Yaw Rate, the initial value at Ignition is Non-Zero, "
                "Hence the test result is FAILED"
            )
            result_list.append(False)

        if all(result_list):
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[CarMakerUrl.odoEstX] = evaluation_x
        signal_summary[CarMakerUrl.odoEstY] = evaluation_y
        signal_summary[CarMakerUrl.yawrate_estimation] = evaluation_yaw

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
        yaw_plot = plot_graphs_signgle_signal(
            ap_time, odo_yaw, CarMakerUrl.yawrate_estimation, "Estimated YawRate Signal", "Time[s]", "Radiance[rad]"
        )

        plot_titles.append(" ")
        plots.append(x_plot)
        plots.append(y_plot)
        plots.append(yaw_plot)

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


@verifies("ReqID_1386073")
@testcase_definition(
    name="The ESC Odometry shall provide the positions(x,y) and yaw rate when ignition is On.",
    description="The ESC Odometry shall provide the positions(x,y) and yaw rate when ignition is On.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_3z51bzaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti.de%2"
    "Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configuration"
    "=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedPositionsAndYawRateWhenIgnitionOnTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedPositionsAndYawRateWhenIgnitionOn,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedPositionsAndYawRateWhenIgnitionOnTestCase,
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
