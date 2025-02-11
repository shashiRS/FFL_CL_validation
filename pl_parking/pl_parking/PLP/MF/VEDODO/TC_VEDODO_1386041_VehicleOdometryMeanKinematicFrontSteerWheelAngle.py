#!/usr/bin/env python3
"""This is the test case to provide the mean kinematic front steer angle"""

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

READER_NAME = "VedodoVelocityOdometerMeanKinematicFrontSteerWheelAngle"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        SteerAngleFL = "SteerAngleFL"
        SteerAngleFR = "SteerAngleFR"
        CM_TIME = "cm_time"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.SteerAngleFL: CarMakerUrl.SteerAngleFL,
            self.Columns.SteerAngleFR: CarMakerUrl.SteerAngleFR,
            self.Columns.CM_TIME: CarMakerUrl.time,
        }


def calculate_mean_steer_angle(steer_angle_left, steer_angle_right):
    """
    Calculate the mean kinematic front steer angle of a car.

    Parameters:
    steer_angle_left (float): The steering angle of the left front wheel in radiance.
    steer_angle_right (float): The steering angle of the right front wheel in radiance.

    Returns:
    float: The mean kinematic front steer angle in radiance.
    """
    # Calculate the mean steer angle
    mean_steer_angle = (steer_angle_left + steer_angle_right) / 2

    return mean_steer_angle


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the mean kinematic front steer angle.",
    description="The ESC Odometry shall provide the mean kinematic front steer angle.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoOdometryMeanKinematicFrontSteerWheelAngle(TestStep):
    """The ESC Odometry shall provide the mean kinematic front steer angle.

    Objective
    ---------

    The ESC Odometry shall provide the mean kinematic front steer angle.

    Detail
    ------

    The ESC Odometry shall provide the mean kinematic front steer angle.
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
        odo_fl = list(df[VedodoSignals.Columns.SteerAngleFL])
        odo_fr = list(df[VedodoSignals.Columns.SteerAngleFR])

        # Init variables
        signal_summary = dict()
        fl_len = len(odo_fl)
        fr_len = len(odo_fr)
        fl_flag = True
        fr_flag = True
        evaluation_fl = ""
        evaluation_fr = ""
        mean_kinematic_steer_angle_list = list()

        if fl_len != fr_len:
            evaluation = (
                f"The FrontWheelSteerAngles signals data are having different length, WheelSteerAngleFL: {fl_len} and "
                f"WheelSteerAngleFR: {fr_len} length"
            )
        else:
            evaluation = (
                f"The FrontWheelSteerAngles signals data are having equal length, WheelSteerAngleFL: {fl_len} and "
                f"WheelSteerAngleFR: {fr_len} length"
            )
        if not sum(odo_fr):
            evaluation_fl = "The WheelSteerAngleFL signal values are zero, no estimation data is available"
            fl_flag = False
        if not sum(odo_fr):
            evaluation_fr = "The WheelSteerAngleFR signal values are zero, no estimation data is available"
            fr_flag = False

        for x, y in zip(odo_fl[10:], odo_fr[10:]):  # ignoring first few frames
            if pd.isna(x) and fl_flag:
                evaluation_fl = "The WheelSteerAngleFL signal data having NAN values"
                fl_flag = False
            if pd.isna(y) and fr_flag:
                evaluation_fr = "The WheelSteerAngleFR signal data having NAN values"
                fr_flag = False

        if fl_flag:
            evaluation_fl = "The WheelSteerAngleFL signal data is having valid data"

        if fr_flag:
            evaluation_fr = "The WheelSteerAngleFR signal data is having valid data"

        if fl_flag and fr_flag:
            for fl, fr in zip(odo_fl, odo_fr):
                mean_kinematic_steer_angle_list.append(calculate_mean_steer_angle(fl, fr))
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary["Estimated FrontSteerWheelAngles"] = evaluation
        signal_summary[CarMakerUrl.SteerAngleFL] = evaluation_fl
        signal_summary[CarMakerUrl.SteerAngleFR] = evaluation_fr

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fl_plot = plot_graphs_signgle_signal(
            ap_time, odo_fl, CarMakerUrl.SteerAngleFL, "Estimated SteerAngleFL Signal", "Time[s]", "Radiance[rad]"
        )
        fr_plot = plot_graphs_signgle_signal(
            ap_time, odo_fr, CarMakerUrl.SteerAngleFR, "Estimated SteerAngleFR Signal", "Time[s]", "Radiance[rad]"
        )

        plot_mean = plot_graphs_signgle_signal(
            ap_time,
            mean_kinematic_steer_angle_list,
            "Front Steer Wheel Angles",
            "Mean Kinematic Front Steer Wheel Angles",
            "Time[s]",
            "Radiance[rad]",
        )
        plots.append(plot_mean)
        plot_titles.append(" ")
        plots.append(fl_plot)
        plot_titles.append(" ")
        plots.append(fr_plot)
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


@verifies("ReqID_1386041")
@testcase_definition(
    name="The ESC Odometry shall provide the mean kinematic front steer angle.",
    description="The ESC Odometry shall provide the mean kinematic front steer angle.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%"
    "2Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z5OXTaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti."
    "de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configu"
    "ration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoOdometryMeanKinematicFrontSteerWheelAngleTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoOdometryMeanKinematicFrontSteerWheelAngle,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoOdometryMeanKinematicFrontSteerWheelAngleTestCase,
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
