#!/usr/bin/env python3
"""This is the test case shall provide the possibility to read ego-motion data up to 300ms to past."""

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

from .common import plot_graphs, plot_graphs_threshold
from .constants import CarMakerUrl

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


__author__ = "Anil A, Uie64067"
__copyright__ = "2012-2024, Continental AG"
__version__ = "0.0.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

READER_NAME = "VedodoPastPositionsAndOrientation"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        CM_TIME = "cm_time"
        ODO_CM_REF_X = "odoCmRefX"
        ODO_CM_REF_Y = "odoCmRefY"
        odo_xPositionPastBuffer30 = "odo_xPositionPastBuffer30"
        odo_yPositionPastBuffer30 = "odo_yPositionPastBuffer30"
        odo_yawAnglePastBuffer30 = "odo_yawAnglePastBuffer30"
        YAW_ANGLE = "yawAngle"
        GT_Velocity = "gt_velocity"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.ODO_CM_REF_X: CarMakerUrl.odoCmRefX,
            self.Columns.ODO_CM_REF_Y: CarMakerUrl.odoCmRefY,
            self.Columns.odo_xPositionPastBuffer30: CarMakerUrl.odo_xPositionPastBuffer30,
            self.Columns.odo_yPositionPastBuffer30: CarMakerUrl.odo_yPositionPastBuffer30,
            self.Columns.odo_yawAnglePastBuffer30: CarMakerUrl.odo_yawAnglePastBuffer30,
            self.Columns.YAW_ANGLE: CarMakerUrl.gt_yawAngle,
            self.Columns.GT_Velocity: CarMakerUrl.velocityX,
        }


@teststep_definition(
    step_number=1,
    name="This is the test case shall provide the possibility to read ego-motion data up to 300ms to past.",
    description="This is the test case shall provide the possibility to read ego-motion data up to 300ms to past.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoProvidePastPositionAndOrientation(TestStep):
    """This is the test case shall provide the possibility to read ego-motion data up to 300ms to past.

    Objective
    ---------

    This is the test case shall provide the possibility to read ego-motion data up to 300ms to past.

    Detail
    ------

    This is the test case shall provide the possibility to read ego-motion data up to 300ms to past.
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
        plot_titles, plots, remarks = rep([], 3)
        df: pd.DataFrame = self.readers[READER_NAME]
        max_expected_y_position_error: float = 0.03
        max_expected_x_position_error: float = 0.06
        max_expected_orientation_error: float = 0.035
        buffer_delay = 30  # 300ms buffer time

        signal_summary = dict()
        test_result_list = list()
        # Ignoring first few frames to settle the algorithm
        ap_time = list(df[VedodoSignals.Columns.CM_TIME])[3:-buffer_delay]
        gt_x = list(df[VedodoSignals.Columns.ODO_CM_REF_X])[3:-buffer_delay]
        gt_y = list(df[VedodoSignals.Columns.ODO_CM_REF_Y])[3:-buffer_delay]
        x_estimated = list(df[VedodoSignals.Columns.odo_xPositionPastBuffer30])[3 + buffer_delay :]
        y_estimated = list(df[VedodoSignals.Columns.odo_yPositionPastBuffer30])[3 + buffer_delay :]
        orientation_estimated = list(df[VedodoSignals.Columns.odo_yawAnglePastBuffer30])[3 + buffer_delay :]
        gt_orientation = list(df[VedodoSignals.Columns.YAW_ANGLE])[3:-buffer_delay]
        deviation_dict = {"x": list(), "y": list(), "orientation": list()}

        for gx, gy, go, px, py, po in zip(gt_x, gt_y, gt_orientation, x_estimated, y_estimated, orientation_estimated):
            deviation_dict["x"].append(abs(abs(gx) - abs(px)))
            deviation_dict["y"].append(abs(abs(gy) - abs(py)))
            deviation_dict["orientation"].append(abs(abs(go) - abs(po)))

        max_longi_error = max(deviation_dict["x"])
        if max_longi_error > max_expected_x_position_error:
            evaluation_long = (
                f"Evaluation for Longitudinal position up to 300ms to the past, the max "
                f"longitudinal deviation error is {round(max_longi_error, 3)}m and which is above the threshold "
                f"{max_expected_x_position_error}m. Hence the test result is FAILED."
            )
            test_result_list.append(False)
        else:
            evaluation_long = (
                f"Evaluation for Longitudinal position up to 300ms to the past, the max "
                f"longitudinal deviation error is {round(max_longi_error, 3)}m and which is within the threshold "
                f"{max_expected_x_position_error}m. Hence the test result is PASSED."
            )
            test_result_list.append(True)

        max_lat_error = max(deviation_dict["y"])
        if max_lat_error > max_expected_y_position_error:
            evaluation_lat = (
                f"Evaluation for Lateral position up to 300ms to the past, the max "
                f"longitudinal deviation error is {round(max_lat_error, 3)}m and which is above the threshold "
                f"{max_expected_y_position_error}m. Hence the test result is FAILED."
            )
            test_result_list.append(False)
        else:
            evaluation_lat = (
                f"Evaluation for Lateral position up to 300ms to the past, the max "
                f"longitudinal deviation error is {round(max_lat_error, 3)}m and which is within the threshold "
                f"{max_expected_y_position_error}m. Hence the test result is PASSED."
            )
            test_result_list.append(True)

        max_orientation_error = max(deviation_dict["orientation"])
        if max_orientation_error > max_expected_orientation_error:
            evaluation_orient = (
                f"Evaluation for Orientation up to 300ms to the past, the max "
                f"longitudinal deviation error is {round(max_orientation_error, 3)}rad and which is above the "
                f"threshold {max_expected_orientation_error}rad. Hence the test result is FAILED."
            )
            test_result_list.append(False)
        else:
            evaluation_orient = (
                f"Evaluation for Orientation up to 300ms to the past, the max "
                f"longitudinal deviation error is {round(max_orientation_error, 3)}rad and which is within the "
                f"threshold {max_expected_orientation_error}rad. Hence the test result is PASSED."
            )
            test_result_list.append(True)

        if all(test_result_list):
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[f"{CarMakerUrl.odo_xPositionPastBuffer30} vs {CarMakerUrl.odoCmRefX}"] = evaluation_long
        signal_summary[f"{CarMakerUrl.odo_yPositionPastBuffer30} vs {CarMakerUrl.odoCmRefY}"] = evaluation_lat
        signal_summary[f"{CarMakerUrl.odo_yawAnglePastBuffer30} vs {CarMakerUrl.gt_yawAngle}"] = evaluation_orient
        self.sig_summary = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_summary)
        remarks.append("")

        x_plot = plot_graphs(
            ap_time,
            x_estimated,
            CarMakerUrl.odo_xPositionPastBuffer30,
            gt_x,
            CarMakerUrl.odoCmRefX,
            "Time[s]",
            "Distance[m]",
        )
        y_plot = plot_graphs(
            ap_time,
            y_estimated,
            CarMakerUrl.odo_yPositionPastBuffer30,
            gt_y,
            CarMakerUrl.odoCmRefY,
            "Time[s]",
            "Distance[m]",
        )
        orientation_plot = plot_graphs(
            ap_time,
            y_estimated,
            CarMakerUrl.odo_yawAnglePastBuffer30,
            gt_y,
            CarMakerUrl.gt_yawAngle,
            "Time[s]",
            "Radiance[rad]",
        )
        x_plot_th = plot_graphs_threshold(
            ap_time,
            deviation_dict["x"],
            "Longitudinal Position Deviation",
            max_expected_x_position_error,
            "Max Positional Error Threshold",
            "Time[s]",
            "Distance[m]",
        )
        y_plot_th = plot_graphs_threshold(
            ap_time,
            deviation_dict["y"],
            "Lateral Position Deviation",
            max_expected_y_position_error,
            "Max Positional Error Threshold",
            "Time[s]",
            "Distance[m]",
        )
        orientation_plot_th = plot_graphs_threshold(
            ap_time,
            deviation_dict["orientation"],
            "Orientation Deviation",
            max_expected_orientation_error,
            "Max Orientation Error Threshold",
            "Time[s]",
            "Radiance[rad]",
        )

        plots.append(x_plot)
        plot_titles.append(" ")
        plots.append(y_plot)
        plot_titles.append(" ")
        plots.append(orientation_plot)
        plot_titles.append(" ")
        plots.append(x_plot_th)
        plot_titles.append(" ")
        plots.append(y_plot_th)
        plot_titles.append(" ")
        plots.append(orientation_plot_th)
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


@verifies("ReqId-1386050")
@testcase_definition(
    name="This is the test case shall provide the possibility to read ego-motion data up to 300ms to past.",
    description="This is the test case shall provide the possibility to read ego-motion data up to 300ms to past.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_3z5OZjaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti.de%2"
    "Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configuration"
    "=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoProvidePastPositionAndOrientationTestCase(TestCase):
    """VedodoRelativeLongitudinalPositionErrorNormalDrivingConditionsTestCase test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoProvidePastPositionAndOrientation,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.

    """
    _, testrun_id, cp = debug(
        VedodoProvidePastPositionAndOrientationTestCase,
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
