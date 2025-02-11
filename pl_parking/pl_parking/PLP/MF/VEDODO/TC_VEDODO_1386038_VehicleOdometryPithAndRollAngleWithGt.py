#!/usr/bin/env python3
"""This is the test case to check the Pitch Angle and Roll Angle with Gt"""

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

READER_NAME = "VedodoVelocityOdometerPitchAndRollAngleWithGt"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        CM_TIME = "cm_time"
        gt_pitchAngle = "gt_pitchAngle"
        gt_rollAngle = "gt_rollAngle"
        rollAngle_estimation = "rollAngle_estimation"
        pitchAngle_estimation = "pitchAngle_estimation"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.gt_pitchAngle: CarMakerUrl.gt_pitchAngle,
            self.Columns.rollAngle_estimation: CarMakerUrl.rollAngle_estimation,
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.gt_rollAngle: CarMakerUrl.gt_rollAngle,
            self.Columns.pitchAngle_estimation: CarMakerUrl.pitchAngle_estimation,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the Pitch Angle and Roll Angle with Gt.",
    description="The ESC Odometry shall provide the Pitch Angle and Roll Angle with Gt.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedPitchAndRollAngle(TestStep):
    """The ESC Odometry shall provide the Pitch Angle and Roll Angle with Gt.

    Objective
    ---------

    The ESC Odometry shall provide the Pitch Angle and Roll Angle with Gt.

    Detail
    ------

    The ESC Odometry shall provide the Pitch Angle and Roll Angle with Gt.
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
        gt_pitch = list(df[VedodoSignals.Columns.gt_pitchAngle])
        gt_roll = list(df[VedodoSignals.Columns.gt_rollAngle])

        # Init variables
        signal_summary = dict()
        roll_deviate_list = list()
        pitch_deviate_list = list()
        max_expected_pith_angle_error: float = 0.035
        max_expected_roll_angle_error: float = 0.035

        for gr, odr, gp, odp in zip(gt_roll, odo_roll, gt_pitch, odo_pitch):
            roll_deviate_list.append(abs(gr - odr))
            pitch_deviate_list.append(abs(gp - odp))

        max_roll_error = max(roll_deviate_list)
        if max_roll_error < max_expected_roll_angle_error:
            evaluation_roll = " ".join(
                f"Evaluation of estimated Roll Angle with Gt is PASSED. The max deviation of Roll Angle "
                f"{max_roll_error}rad is below the given threshold {round(max_expected_roll_angle_error, 3)}rad".split()
            )
            test_result_roll = True
        else:
            evaluation_roll = " ".join(
                f"Evaluation of estimated Roll Angle with Gt is FAILED. The max deviation of Roll Angle "
                f"{max_roll_error}rad is above the given threshold {round(max_expected_roll_angle_error, 3)}rad".split()
            )
            test_result_roll = False

        max_pitch_error = max(pitch_deviate_list)
        if max_pitch_error < max_expected_pith_angle_error:
            evaluation_pitch = " ".join(
                f"Evaluation of estimated Pitch Angle with Gt is PASSED. The max deviation of Pitch Angle "
                f"{max_pitch_error}rad is within the given threshold {round(max_expected_pith_angle_error, 3)}rad"
                f"".split()
            )
            test_result_pitch = True
        else:
            evaluation_pitch = " ".join(
                f"Evaluation of estimated Pitch Angle with Gt is FAILED. The max deviation of Pitch Angle "
                f"{max_pitch_error}rad is above the given threshold {round(max_expected_pith_angle_error, 3)}rad"
                f"".split()
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

        roll_threshold_fig = plot_graphs_threshold(
            ap_time,
            roll_deviate_list,
            "Roll Angle deviation error",
            max_expected_roll_angle_error,
            "Roll Angle Threshold",
            "Time[s]",
            "Radiance[rad]",
        )
        pitch_threshold_fig = plot_graphs_threshold(
            ap_time,
            pitch_deviate_list,
            "Pitch Angle deviation error",
            max_expected_pith_angle_error,
            "Pitch Angle Threshold",
            "Time[s]",
            "Radiance[rad]",
        )
        roll_plot = plot_graphs(
            ap_time,
            odo_roll,
            CarMakerUrl.rollAngle_estimation,
            gt_roll,
            CarMakerUrl.gt_rollAngle,
            "Time[s]",
            "Radiance[rad]",
        )
        pitch_plot = plot_graphs(
            ap_time,
            odo_pitch,
            CarMakerUrl.pitchAngle_estimation,
            gt_pitch,
            CarMakerUrl.gt_pitchAngle,
            "Time[s]",
            "Radiance[rad]",
        )

        plots.append(roll_threshold_fig)
        plots.append(roll_plot)
        plots.append(pitch_threshold_fig)
        plots.append(pitch_plot)

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


@verifies("ReqID_1386038")
@testcase_definition(
    name="The ESC Odometry shall provide the Pitch Angle and Roll Angle with Gt.",
    description="The ESC Odometry shall provide the Pitch Angle and Roll Angle with Gt.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2"
    "Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z5OXDaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti.de"
    "%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configurat"
    "ion=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedPitchAndRollAngleTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedPitchAndRollAngle,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedPitchAndRollAngleTestCase,
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
