#!/usr/bin/env python3
"""The ESC Odometry shall be applicable for all wheel driven vehicles."""

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

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "Anil A, uie64067"
__copyright__ = "2012-2024, Continental AG"
__version__ = "0.0.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

READER_NAME = "VedodoVelocityOdometerAllWheels"


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
        longitudinalAcceleration = "longitudinalAcceleration"
        motionStatus = "motionStatus"
        ax = "ax"
        lateralAcceleration = "lateralAcceleration"
        ay = "ay"

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
            self.Columns.longitudinalAcceleration: CarMakerUrl.longiAcceleration,
            self.Columns.ax: CarMakerUrl.ax,
            self.Columns.lateralAcceleration: CarMakerUrl.lateralAcceleration,
            self.Columns.ay: CarMakerUrl.ay,
            self.Columns.motionStatus: CarMakerUrl.motionStatus,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall be applicable for all wheel driven vehicles",
    description="The ESC Odometry shall be applicable for all wheel driven vehicles",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleOdometryForAllWheels(TestStep):
    """The ESC Odometry shall be applicable for all wheel driven vehicles

    Objective
    ---------

    The ESC Odometry shall be applicable for all wheel driven vehicles

    Detail
    ------

    The ESC Odometry shall be applicable for all wheel driven vehicles
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
        # skip first few frames
        ap_time = list(df[VedodoSignals.Columns.CM_TIME])[10:]
        odo_x = list(df[VedodoSignals.Columns.odoEstX])[10:]
        odo_y = list(df[VedodoSignals.Columns.odoEstY])[10:]
        gt_x = list(df[VedodoSignals.Columns.odoCmRefX])[10:]
        gt_y = list(df[VedodoSignals.Columns.odoCmRefY])[10:]
        gt_yaw = list(df[VedodoSignals.Columns.gt_yawAngle])[10:]
        odo_yaw = list(df[VedodoSignals.Columns.yawAngle_est])[10:]
        odo_ax = list(df[VedodoSignals.Columns.longitudinalAcceleration])[10:]
        ref_ax = list(df[VedodoSignals.Columns.ax])[10:]
        odo_ay = list(df[VedodoSignals.Columns.lateralAcceleration])[10:]
        ref_ay = list(df[VedodoSignals.Columns.ay])[10:]
        motion_status = list(df[VedodoSignals.Columns.motionStatus])[10:]
        acceleration_x_dff_list = list()
        acceleration_y_dff_list = list()
        signal_summary = dict()
        yaw_angle_deviate_list = list()
        x_deviate_list = list()
        y_deviate_list = list()
        result = list()
        max_expected_threshold_error: float = 0.2
        max_expected_deviate_yawangle: float = 0.00174533
        max_expected_x_error: float = 0.06
        max_expected_y_error: float = 0.03
        signal_len = len(odo_x)

        for i in range(signal_len):
            yaw_angle_deviate_list.append(abs(gt_yaw[i] - odo_yaw[i]))
            x_deviate_list.append(abs(gt_x[i] - odo_x[i]))
            y_deviate_list.append(abs(gt_y[i] - odo_y[i]))

        for gxv, oxv, gyv, oyv, m in zip(ref_ax, odo_ax, ref_ay, odo_ay, motion_status):
            if m:
                error_diff_x = abs(gxv) - abs(oxv)
                error_diff_y = abs(gyv) - abs(oyv)
            else:
                error_diff_x = 0
                error_diff_y = 0
            acceleration_x_dff_list.append(error_diff_x)
            acceleration_y_dff_list.append(error_diff_y)

        max_yaw_angle_deviate = max(yaw_angle_deviate_list)
        if max_yaw_angle_deviate < max_expected_deviate_yawangle:
            evaluation_yaw = " ".join(
                f"Evaluation of estimated yaw angle, The deviation between the GroundTruth and estimated is "
                f"{round(max_yaw_angle_deviate, 3)}rad and the threshold value is {max_expected_deviate_yawangle} rad"
                f"The deviation is below the threshold. Hence the result is PASSED".split()
            )
            result.append(True)
        else:
            evaluation_yaw = " ".join(
                f"Evaluation of estimated yaw angle, The deviation between the GroundTruth and estimated is "
                f"{round(max_yaw_angle_deviate, 3)}rad and the threshold value is {max_expected_deviate_yawangle} rad"
                f"The deviation is above the threshold. Hence the result is FAILED".split()
            )
            result.append(False)

        max_x_error = max(x_deviate_list)
        if max_x_error < max_expected_x_error:
            evaluation_x = " ".join(
                f"Evaluation of estimated Position-X, The deviation between the GroundTruth and estimated is "
                f"{round(max_x_error, 3)}m and the threshold value is {max_expected_x_error}m"
                f"The deviation is below the threshold. Hence the result is PASSED".split()
            )
            result.append(True)
        else:
            evaluation_x = " ".join(
                f"Evaluation of estimated Position-X, The deviation between the GroundTruth and estimated is "
                f"{round(max_x_error, 3)}m and the threshold value is {max_expected_x_error}m"
                f"The deviation is above the threshold. Hence the result is FAILED".split()
            )
            result.append(False)

        max_y_error = max(y_deviate_list)
        if max_y_error < max_expected_y_error:
            evaluation_y = " ".join(
                f"Evaluation of estimated Position-Y, The deviation between the GroundTruth and estimated is "
                f"{round(max_y_error, 3)}m and the threshold value is {max_expected_y_error}m"
                f"The deviation is below the threshold. Hence the result is PASSED".split()
            )
            result.append(True)
        else:
            evaluation_y = " ".join(
                f"Evaluation of estimated Position-Y, The deviation between the GroundTruth and estimated is "
                f"{round(max_y_error, 3)}m and the threshold value is {max_expected_y_error}m"
                f"The deviation is above the threshold. Hence the result is FAILED".split()
            )

            result.append(False)

        max_error_ax = max(acceleration_x_dff_list)
        if max_error_ax > max_expected_threshold_error:
            evaluation_ax = " ".join(
                f"Evaluation for Longitudinal Acceleration, the allowed expected threshold is 1% and vehicle"
                f" acceleration deviation between the Estimate and Reference is {round(max_error_ax, 3)}mps2. The "
                f"error deviation is above the given threshold. Hence result is FAILED.".split()
            )
            result.append(False)
        else:
            evaluation_ax = " ".join(
                f"Evaluation for Longitudinal Acceleration, the allowed expected threshold is 1% and vehicle"
                f" acceleration deviation between the Estimate and Reference is {round(max_error_ax, 3)}mps2. The "
                f"error deviation is above the given threshold. Hence result is FAILED.".split()
            )
            result.append(True)

        max_error_ay = max(acceleration_y_dff_list)
        if max_error_ay > max_expected_threshold_error:
            evaluation_ay = " ".join(
                f"Evaluation for Lateral Acceleration, the allowed expected threshold is 1% and vehicle"
                f" acceleration deviation between the Estimate and Reference is {round(max_error_ay, 3)}mps2. The "
                f"error deviation is above the given threshold. Hence result is FAILED.".split()
            )
            result.append(False)
        else:
            evaluation_ay = " ".join(
                f"Evaluation for Lateral Acceleration, the allowed expected threshold is 1% and vehicle"
                f" acceleration deviation between the Estimate and Reference is {round(max_error_ay, 3)}mps2. The "
                f"error deviation is above the given threshold. Hence result is FAILED.".split()
            )
            result.append(True)

        if all(result):
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[CarMakerUrl.odoEstX] = evaluation_x
        signal_summary[CarMakerUrl.odoEstY] = evaluation_y
        signal_summary[CarMakerUrl.yawAngle] = evaluation_yaw
        signal_summary[CarMakerUrl.longiAcceleration] = evaluation_ax
        signal_summary[CarMakerUrl.lateralAcceleration] = evaluation_ay
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        x_threshold_fig = plot_graphs_threshold(
            ap_time,
            x_deviate_list,
            "Position-X deviation error",
            max_expected_x_error,
            "Position-X Threshold",
            "Time[s]",
            "Meter[m]",
        )
        y_threshold_fig = plot_graphs_threshold(
            ap_time,
            y_deviate_list,
            "Position-Y deviation error",
            max_expected_y_error,
            "Position-Y Threshold",
            "Time[s]",
            "Meter[m]",
        )
        yaw_threshold_fig = plot_graphs_threshold(
            ap_time,
            yaw_angle_deviate_list,
            "Yaw Angle Deviation Error",
            max_expected_deviate_yawangle,
            "Yaw Angle Threshold",
            "Time[s]",
            "Radiance[rad]",
        )
        x_plot = plot_graphs(ap_time, odo_x, CarMakerUrl.odoEstX, gt_x, CarMakerUrl.odoCmRefX, "Time[s]", "Distance[m]")
        y_plot = plot_graphs(ap_time, odo_y, CarMakerUrl.odoEstY, gt_y, CarMakerUrl.odoCmRefY, "Time[s]", "Distance[m]")
        yaw_plot = plot_graphs(
            ap_time,
            odo_yaw,
            CarMakerUrl.yawAngle,
            gt_yaw,
            CarMakerUrl.gt_yawAngle,
            "Time[s]",
            "Radiance[rad]",
        )
        plots.append(x_threshold_fig)
        plots.append(x_plot)
        plots.append(y_threshold_fig)
        plots.append(y_plot)
        plots.append(yaw_threshold_fig)
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


@verifies("ReqID_1386122")
@testcase_definition(
    name="The ESC Odometry shall be applicable for all wheel driven vehicles.",
    description="The ESC Odometry shall be applicable for all wheel driven vehicles.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2"
    "Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z7DgTaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti.de"
    "%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configurat"
    "ion=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleOdometryForAllWheelsTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleOdometryForAllWheels,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleOdometryForAllWheelsTestCase,
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
