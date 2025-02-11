#!/usr/bin/env python3
"""This is the test case to check the Roll Over the Orientation."""

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
from pl_parking.PLP.MF.VEDODO.common import plot_graphs_two_threshold
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

READER_NAME = "VedodoVelocityOdometerRollOverOrientation"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        CM_TIME = "cm_time"
        rollAngle_estimation = "rollAngle_estimation"
        pitchAngle_estimation = "pitchAngle_estimation"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.rollAngle_estimation: CarMakerUrl.rollAngle_estimation,
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.pitchAngle_estimation: CarMakerUrl.pitchAngle_estimation,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the Roll Over the Orientation.",
    description="The ESC Odometry shall provide the Roll Over the Orientation.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoOdometryRollOverTheOrientation(TestStep):
    """The ESC Odometry shall provide the Roll Over the Orientation.

    Objective
    ---------

    The ESC Odometry shall provide the Roll Over the Orientation.

    Detail
    ------

    The ESC Odometry shall provide the Roll Over the Orientation.
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
        odo_pitch = list(df[VedodoSignals.Columns.pitchAngle_estimation])
        odo_roll = list(df[VedodoSignals.Columns.rollAngle_estimation])

        # Init variables
        signal_summary = dict()
        max_pos_orientation = 3.1398
        max_neg_orientation = -3.1398

        max_roll_angle = max(odo_roll)
        min_roll_angle = min(odo_roll)
        max_pitch_angle = max(odo_pitch)
        min_pitch_angle = min(odo_pitch)

        if max_neg_orientation <= min_roll_angle <= max_roll_angle < max_pos_orientation:
            evaluation_roll = (
                f"Evaluation of estimated Roll Angle is within the range of {max_neg_orientation}rad to "
                f"{max_pos_orientation}rad and min Roll Angle is {round(min_roll_angle, 3)}rad and max Roll Angle "
                f"is {max_roll_angle}rad, Hence the test result is PASSED"
            )

            test_result_roll = True
        else:
            evaluation_roll = (
                f"Evaluation of estimated Roll Angle is outside the range of {max_neg_orientation}rad"
                f" to {max_pos_orientation}rad and min Roll Angle is {round(min_roll_angle, 3)}rad and max Roll"
                f" Angle is {max_roll_angle}rad, Hence the test result is FAILED"
            )
            test_result_roll = False

        if max_neg_orientation <= min_pitch_angle <= max_pitch_angle <= max_pos_orientation:
            evaluation_pitch = (
                f"Evaluation of estimated Pitch Angle is within the range of {max_neg_orientation}rad"
                f" to {max_pos_orientation}rad and min Pitch Angle is {round(min_pitch_angle, 3)}rad and max Pitch"
                f" Angle is {max_roll_angle}rad, Hence the test result is PASSED"
            )

            test_result_pitch = True
        else:
            evaluation_pitch = (
                f"Evaluation of estimated Pitch Angle is outside the range of {max_neg_orientation}"
                f"rad to {max_pos_orientation}rad and min Pitch Angle is {round(min_pitch_angle, 3)}rad and max"
                f" Pitch Angle is {max_roll_angle}rad, Hence the test result is FAILED"
            )
            test_result_pitch = False

        if test_result_roll and test_result_pitch:
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[CarMakerUrl.rollAngle_estimation] = evaluation_roll
        signal_summary[CarMakerUrl.pitchAngle_estimation] = evaluation_pitch

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        roll_threshold_fig = plot_graphs_two_threshold(
            ap_time,
            odo_roll,
            CarMakerUrl.rollAngle_estimation,
            min_roll_angle,
            "Roll Angle Min Range Threshold",
            max_roll_angle,
            "Roll Angle Max Range Threshold",
            "Roll Over the Roll Angle With Threshold Range Limit",
            "Time[s]",
            "Radiance[rad]",
        )
        pitch_threshold_fig = plot_graphs_two_threshold(
            ap_time,
            odo_pitch,
            CarMakerUrl.pitchAngle_estimation,
            min_pitch_angle,
            "Pitch Angle Min Range Threshold",
            max_pitch_angle,
            "Pitch Angle Max Range Threshold",
            "Roll Over the Pitch Angle With Threshold Range Limit",
            "Time[s]",
            "Radiance[rad]",
        )

        plots.append(roll_threshold_fig)
        plot_titles.append("")
        plots.append(pitch_threshold_fig)
        plot_titles.append("")

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


@verifies("ReqID_1386021")
@testcase_definition(
    name="The ESC Odometry shall provide the Roll Over the Orientation.",
    description="The ESC Odometry shall provide the Roll Over the Orientation.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2"
    "F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z4nWjaaEe6mrdm2_agUYg&oslc_config.context=https%3A%2F%2F"
    "jazz.conti.de%2Fgc%2Fconfiguration%2F30013&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-pro"
    "jects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleOdometryRollOverTheOrientationTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoOdometryRollOverTheOrientation,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleOdometryRollOverTheOrientationTestCase,
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
