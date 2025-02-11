#!/usr/bin/env python3
"""This is the test case to check the Positions (x,y) and Orientation"""

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
from pl_parking.PLP.MF.VEDODO.common import calculate_odo_error, plot_graphs, plot_graphs_threshold
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

READER_NAME = "VedodoVelocityOdometerPositionsAndOrientationWithBreak"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        yawAngle_est = "yawAngle_est"
        odoEstX = "odoEstX"
        odoEstY = "odoEstY"
        CM_TIME = "cm_time"
        gt_yawAngle = "gt_yawAngle"
        odoCmRefX = "odoCmRefX"
        odoCmRefY = "odoCmRefY"
        breakctrlstatusport = "breakctrlstatusport"
        motionStatus = "motionStatus"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.odoEstX: CarMakerUrl.odoEstX,
            self.Columns.odoEstY: CarMakerUrl.odoEstY,
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.gt_yawAngle: CarMakerUrl.gt_yawAngle,
            self.Columns.yawAngle_est: CarMakerUrl.yawAngle,
            self.Columns.odoCmRefX: CarMakerUrl.odoCmRefX,
            self.Columns.odoCmRefY: CarMakerUrl.odoCmRefY,
            self.Columns.breakctrlstatusport: CarMakerUrl.breakctrlstatusport,
            self.Columns.motionStatus: CarMakerUrl.motionStatus,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the position in (x,y) and Orientation when the car is braked with "
    "maximum deceleration.",
    description="The ESC Odometry shall provide the position in (x,y) and Orientation when the car is braked with "
    "maximum deceleration.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedPositionsWhenDecelerationBreak(TestStep):
    """The ESC Odometry shall provide the position in (x,y) and Orientation when the car is braked with
    maximum deceleration.

    Objective
    ---------

    The ESC Odometry shall provide the position in (x,y) and Orientation when the car is braked with
    maximum deceleration.

    Detail
    ------

    The ESC Odometry shall provide the position in (x,y) and Orientation when the car is braked with
    maximum deceleration.
    """

    custom_report = MfCustomTeststepReport

    def __init__(self):
        super().__init__()
        self.sig_sum = None

    def process(self):
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
        gt_x = list(df[VedodoSignals.Columns.odoCmRefX])
        gt_y = list(df[VedodoSignals.Columns.odoCmRefY])
        gt_yaw = list(df[VedodoSignals.Columns.gt_yawAngle])
        odo_yaw = list(df[VedodoSignals.Columns.yawAngle_est])
        odo_break = list(df[VedodoSignals.Columns.breakctrlstatusport])
        motion_status = list(df[VedodoSignals.Columns.motionStatus])

        # Init variables
        signal_summary = dict()
        odo_total_dist = 0
        gt_total_dist = 0
        gt_dist_list = list()
        odo_dist_list = list()
        deviation_error_dict = {"error": [], "time": []}
        distance_error_threshold = 10
        break_flag = False

        _, _, driven_dist, _, _ = calculate_odo_error(gt_x, gt_y, gt_yaw, odo_yaw, odo_x, odo_y)

        for xgt, br, ms, d, t in zip(gt_x, odo_break, motion_status, driven_dist, ap_time):
            if not ms and br:
                break_flag = True
                odo_total_dist += d
                gt_total_dist += xgt
            elif ms and not br and break_flag:
                break_flag = False
                gt_dist_list.append(gt_total_dist)
                odo_dist_list.append(odo_total_dist)
                deviation_error_dict["error"].append(100 - (odo_total_dist * 100 / gt_total_dist))
                deviation_error_dict["time"].append(t)
                odo_total_dist = 0
                gt_total_dist = 0

        max_error_rate = max(deviation_error_dict["error"])
        if max_error_rate <= distance_error_threshold:
            evaluation = (
                f"The evaluation for position error when the car is braked with maximum deceleration"
                f", the allowed threshold is {distance_error_threshold}%, the max relative error"
                f"w.r.t ground is {round(max_error_rate, 3)}%. The deviation is below the threshold."
                f"Hence the test result is PASSED."
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            evaluation = (
                f"The evaluation for position error when the car is braked with maximum deceleration"
                f", the allowed threshold is {distance_error_threshold}%, the max relative error"
                f"w.r.t ground is {round(max_error_rate, 3)}%. The deviation is above the threshold."
                f"Hence the test result is FAILED."
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[CarMakerUrl.odoEstX] = evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        x_threshold_fig = plot_graphs_threshold(
            deviation_error_dict["time"],
            deviation_error_dict["error"],
            "Position deviation error",
            distance_error_threshold,
            "Position Threshold",
            "Time[s]",
            "Meter[m]",
        )
        x_plot = plot_graphs(ap_time, odo_x, CarMakerUrl.odoEstX, gt_x, CarMakerUrl.odoCmRefX, "Time[s]", "Distance[m]")
        plots.append(x_threshold_fig)
        plots.append(x_plot)

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


@verifies("ReqID_1386200")
@testcase_definition(
    name="The ESC Odometry shall provide the position in (x,y) and Orientation when the car is braked with "
    "maximum deceleration.",
    description="The ESC Odometry shall provide the position in (x,y) and Orientation when the car is braked "
    "with maximum deceleration..",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2"
    "Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z8RrjaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti.de"
    "%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configurat"
    "ion=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedPositionsWhenDecelerationBreakTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedPositionsWhenDecelerationBreak,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedPositionsWhenDecelerationBreakTestCase,
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
