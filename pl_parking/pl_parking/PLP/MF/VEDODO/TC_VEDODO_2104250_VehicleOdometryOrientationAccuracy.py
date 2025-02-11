#!/usr/bin/env python3
"""This is the test case to check the Orientation Accuracy"""

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

READER_NAME = "VedodoVelocityOdometerOrientationAccuracy"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        CM_TIME = "cm_time"
        gt_yawAngle = "gt_yawAngle"
        yawAngle = "yawAngle"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.gt_yawAngle: CarMakerUrl.gt_yawAngle,
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.yawAngle: CarMakerUrl.yawAngle,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the Orientation Accuracy.",
    description="The ESC Odometry shall provide the Orientation Accuracy.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedOrientationAccuracy(TestStep):
    """The ESC Odometry shall provide the Orientation Accuracy.

    Objective
    ---------

    The ESC Odometry shall provide the Orientation Accuracy.

    Detail
    ------

    The ESC Odometry shall provide the Orientation Accuracy.
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
        odo_yaw_angle = list(df[VedodoSignals.Columns.yawAngle])
        gt_yaw_angle = list(df[VedodoSignals.Columns.gt_yawAngle])

        # Init variables
        signal_summary = dict()
        yaw_angle_deviate_list = list()
        max_expected_yaw_angle_error: float = 2

        for gy, ody in zip(gt_yaw_angle, odo_yaw_angle):
            yaw_angle_deviate_list.append(abs(gy - ody))

        max_yaw_angle_error = max(yaw_angle_deviate_list)
        if max_yaw_angle_error < max_expected_yaw_angle_error:
            evaluation_yaw = " ".join(
                f"Evaluation of estimated yaw angle, the deviation value w.r.t ground truth is "
                f"{round(max_yaw_angle_error, 3)}rad and the expected threshold is {max_expected_yaw_angle_error} rad,"
                f" the deviation value is below the threshold. Hence the result is PASSED.".split()
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            evaluation_yaw = " ".join(
                f"Evaluation of estimated yaw angle, the deviation value w.r.t ground truth is "
                f"{round(max_yaw_angle_error, 3)}rad and the expected threshold is {max_expected_yaw_angle_error} rad,"
                f" the deviation value is above the threshold. Hence the result is FAILED.".split()
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[CarMakerUrl.yawAngle] = evaluation_yaw

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        yaw_angle_threshold_fig = plot_graphs_threshold(
            ap_time,
            yaw_angle_deviate_list,
            "yaw Angle deviation error",
            max_expected_yaw_angle_error,
            "yaw Angle Threshold",
            "Time[s]",
            "Radiance[rad]",
        )
        yaw_angle_plot = plot_graphs(
            ap_time,
            odo_yaw_angle,
            CarMakerUrl.yawAngle,
            gt_yaw_angle,
            CarMakerUrl.gt_yawAngle,
            "Time[s]",
            "Radiance[rad]",
        )

        plots.append(yaw_angle_threshold_fig)
        plots.append(yaw_angle_plot)

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


@verifies("ReqID_2104250")
@testcase_definition(
    name="The ESC Odometry shall provide the Orientation Accuracy.",
    description="The ESC Odometry shall provide the Orientation Accuracy.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F"
    "%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_wJ5csACxEe-JmbR7EsJ0UA&componentURI=https%3A%2F%2Fjazz.cont"
    "i.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.conf"
    "iguration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedOrientationAccuracyTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedOrientationAccuracy,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedOrientationAccuracyTestCase,
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
