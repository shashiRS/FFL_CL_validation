#!/usr/bin/env python3
"""This is the test case to check the Orientation error per meter"""

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
from pl_parking.PLP.MF.VEDODO.common import plot_graphs, plot_graphs_threshold
from pl_parking.PLP.MF.VEDODO.constants import CarMakerUrl

from .common import calculate_odo_error

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "Anil A, uie64067"
__copyright__ = "2012-2024, Continental AG"
__version__ = "0.0.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

READER_NAME = "VedodoVelocityOdometryOrientationErrorPerMeter"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        yawAngle = "yawAngle"
        CM_TIME = "cm_time"
        ODO_CM_REF_X = "odoCmRefX"
        ODO_CM_REF_Y = "odoCmRefY"
        ODO_EST_X = "odoEstX"
        ODO_EST_Y = "odoEstY"
        ODO_CM_REF_YAWANG_EGO_RA_CUR = "odoCmRefyawAngEgoRaCur"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.yawAngle: CarMakerUrl.yawAngle,
            self.Columns.ODO_CM_REF_X: CarMakerUrl.odoCmRefX,
            self.Columns.ODO_CM_REF_Y: CarMakerUrl.odoCmRefY,
            self.Columns.ODO_EST_X: CarMakerUrl.odoEstX,
            self.Columns.ODO_EST_Y: CarMakerUrl.odoEstY,
            self.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR: CarMakerUrl.odoCmRefyawAngEgoRaCur,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the Orientation error per driven meter.",
    description="The ESC Odometry shall provide the Orientation error per driven meter.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedOrientationErrorPerDrivenMeter(TestStep):
    """The ESC Odometry shall provide the Orientation error per driven meter.

    Objective
    ---------

    The ESC Odometry shall provide the Orientation error per driven meter.

    Detail
    ------

    The ESC Odometry shall provide the Orientation error per driven meter.
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
        est_yaw_angle = list(df[VedodoSignals.Columns.yawAngle])
        yaw_angle_flag = True
        max_threshold_per_meter = 0.2
        evaluation = ""

        gt_x = list(df[VedodoSignals.Columns.ODO_CM_REF_X])
        gt_y = list(df[VedodoSignals.Columns.ODO_CM_REF_Y])
        x_estimated = list(df[VedodoSignals.Columns.ODO_EST_X])
        y_estimated = list(df[VedodoSignals.Columns.ODO_EST_Y])
        psi_gt = list(df[VedodoSignals.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR])
        psi_estimated = list(df[VedodoSignals.Columns.yawAngle])

        signal_summary = dict()
        if not sum(est_yaw_angle):
            evaluation = "The Orientation signal values are zero, no data is available to evaluate"
            yaw_angle_flag = False

        for y in est_yaw_angle:
            if pd.isna(y) and yaw_angle_flag:
                evaluation = "The Orientation signal data having NAN values"
                yaw_angle_flag = False
                break

        _, _, driven_dist, _, _ = calculate_odo_error(gt_x, gt_y, psi_gt, psi_estimated, x_estimated, y_estimated)

        total_dist = 0
        total_gt_angle = 0
        total_ref_angle = 0
        diff_orientation = {"error": [], "time": []}
        for d, gy, oy, t in zip(driven_dist, psi_gt, psi_estimated, ap_time):
            if total_dist >= 1:
                diff_orientation["error"].append(abs(total_gt_angle - total_ref_angle))
                diff_orientation["time"].append(t)
                total_dist = 0
            else:
                total_gt_angle += abs(gy)
                total_ref_angle += abs(oy)
                total_dist += d

        if yaw_angle_flag:
            evaluation = "The Orientation signal data is having valid data"

        max_error = max(diff_orientation["error"])
        if max_error <= max_threshold_per_meter:
            evaluation_orientation = " ".join(
                f"Evaluation for Orientation error per driven meter is {round(max_error, 3)}rad and which is "
                f"below the max expected threshold {max_threshold_per_meter}rad, Hence the test result "
                f"is PASSED.".split()
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            evaluation_orientation = " ".join(
                f"Evaluation for Orientation error per driven meter is {round(max_error, 3)}rad and which is "
                f"above the max expected threshold {max_threshold_per_meter}rad, Hence the test result is "
                f"FAILED.".split()
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[CarMakerUrl.yawAngle] = evaluation
        signal_summary[f"{CarMakerUrl.yawAngle} vs {CarMakerUrl.odoCmRefyawAngEgoRaCur}"] = evaluation_orientation

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        angle_per_meter_plot = plot_graphs_threshold(
            diff_orientation["time"],
            diff_orientation["error"],
            "Orientation error per driven meter",
            max_threshold_per_meter,
            "Max expected Error Per Meter",
            "Time[s]",
            "Radian[rad]",
        )
        plot_titles.append("")
        plots.append(angle_per_meter_plot)
        remarks.append("")

        angle_gt_ref = plot_graphs(
            ap_time,
            psi_gt,
            CarMakerUrl.odoCmRefyawAngEgoRaCur,
            psi_estimated,
            CarMakerUrl.yawAngle,
            "Time[s]",
            "Radian[rad]",
        )
        plot_titles.append("")
        plots.append(angle_gt_ref)
        remarks.append("")

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


@verifies("ReqID_1386177")
@testcase_definition(
    name="The ESC Odometry shall provide the Orientation error per driven meter.",
    description="The relative orientation error shall not exceed 0.2 deg per driven meter during parking manoeuvres "
    "which are defined in the scenario catalog.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2"
    "Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z7qpzaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti.de"
    "%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configurat"
    "ion=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedOrientationErrorPerDrivenMeterTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedOrientationErrorPerDrivenMeter,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedOrientationErrorPerDrivenMeterTestCase,
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
