#!/usr/bin/env python3
"""This is the test case to check the Longitudinal and Lateral Acceleration w.r.t Ground Truth"""

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
from pl_parking.PLP.MF.VEDODO.common import plot_graphs_signgle_signal, plot_graphs_threshold
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

READER_NAME = "VedodoAccelerationOdometryLongitudinalLateralAccelerationWithGt"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        longitudinalAcceleration = "longitudinalAcceleration"
        motionStatus = "motionStatus"
        ax = "ax"
        lateralAcceleration = "lateralAcceleration"
        ay = "ay"
        CM_TIME = "cm_time"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.longitudinalAcceleration: CarMakerUrl.longiAcceleration,
            self.Columns.ax: CarMakerUrl.ax,
            self.Columns.lateralAcceleration: CarMakerUrl.lateralAcceleration,
            self.Columns.ay: CarMakerUrl.ay,
            self.Columns.motionStatus: CarMakerUrl.motionStatus,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the Longitudinal and Lateral Acceleration w.r.t Ground Truth.",
    description="The ESC Odometry shall provide the Longitudinal and Lateral Acceleration w.r.t Ground Truth.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedLongitudinalLateralAccelerationWithGt(TestStep):
    """The ESC Odometry shall provide the Longitudinal and Lateral Acceleration w.r.t Ground Truth.

    Objective
    ---------

    The ESC Odometry shall provide the Longitudinal and Lateral Acceleration w.r.t Ground Truth.

    Detail
    ------

    The ESC Odometry shall provide the Longitudinal and Lateral Acceleration w.r.t Ground Truth.
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
        odo_ax = list(df[VedodoSignals.Columns.longitudinalAcceleration])
        ref_ax = list(df[VedodoSignals.Columns.ax])
        odo_ay = list(df[VedodoSignals.Columns.lateralAcceleration])
        ref_ay = list(df[VedodoSignals.Columns.ay])
        motion_status = list(df[VedodoSignals.Columns.motionStatus])
        ax_flag = True
        ay_flag = True
        evaluation_x = ""
        evaluation_y = ""
        acceleration_x_dff_list = list()
        acceleration_y_dff_list = list()
        max_expected_threshold_error: float = 0.2
        result = list()
        # Init variables
        signal_summary = dict()
        if not sum(odo_ax):
            evaluation_x = "The LongitudinalAcceleration signal values are zero, no data is available " "to evaluate"
            ax_flag = False
        for x in odo_ax:
            if pd.isna(x) and ax_flag:
                evaluation_x = "The Longitudinal Acceleration signal data having NAN values"
                ax_flag = False
                break

        if not sum(odo_ay):
            evaluation_y = "The Lateral Acceleration signal values are zero, no data is available to evaluate"
            ay_flag = False

        for y in odo_ay:
            if pd.isna(y) and ay_flag:
                evaluation_y = "The Lateral Acceleration signal data having NAN values"
                ay_flag = False
                break

        for gxv, oxv, gyv, oyv, m in zip(ref_ax, odo_ax, ref_ay, odo_ay, motion_status):
            if m:
                error_diff_x = abs(gxv) - abs(oxv)
                error_diff_y = abs(gyv) - abs(oyv)
            else:
                error_diff_x = 0
                error_diff_y = 0
            acceleration_x_dff_list.append(error_diff_x)
            acceleration_y_dff_list.append(error_diff_y)

        max_error_x = max(acceleration_x_dff_list)
        max_error_y = max(acceleration_y_dff_list)

        if max_error_x > max_expected_threshold_error and not ax_flag:
            evaluation_error_x = " ".join(
                f"Evaluation for Longitudinal Acceleration is FAILED and the allowed expected difference"
                f" error is 1%,but vehicle acceleration difference error between Estimate and Reference is "
                f"{round(max_error_x, 3)}mps2".split()
            )
            result.append(False)
        else:
            evaluation_x = "The Longitudinal Acceleration signal data is having valid data"
            evaluation_error_x = " ".join(
                f"Evaluation for Longitudinal Acceleration is PASSED and the allowed expected difference"
                " error is 1%, vehicle acceleration difference error between Estimate and Reference is "
                f"{round(max_error_x, 3)}mps2".split()
            )
            result.append(True)

        if max_error_y > max_expected_threshold_error and not ay_flag:
            evaluation_error_y = " ".join(
                f"Evaluation for Lateral Acceleration is FAILED and the allowed expected difference"
                f" error is 1%,but vehicle acceleration difference error between Estimate and Reference is "
                f"{round(max_error_y, 3)}mps2".split()
            )
            result.append(False)
        else:
            evaluation_y = "The Lateral Acceleration signal data is having valid data"
            evaluation_error_y = " ".join(
                f"Evaluation for Lateral Acceleration is PASSED and the allowed expected difference"
                " error is 1%, vehicle acceleration difference error between Estimate and Reference is "
                f"{round(max_error_y, 3)}mps2".split()
            )
            result.append(True)

        if all(result):
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[CarMakerUrl.longiAcceleration] = evaluation_x
        signal_summary[CarMakerUrl.lateralAcceleration] = evaluation_y
        signal_summary[f"{CarMakerUrl.longiAcceleration} vs " f"{CarMakerUrl.ax}"] = evaluation_error_x
        signal_summary[f"{CarMakerUrl.lateralAcceleration} vs " f"{CarMakerUrl.ay}"] = evaluation_error_y

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        vx_plot = plot_graphs_signgle_signal(
            ap_time,
            odo_ax,
            CarMakerUrl.longiAcceleration,
            "Estimated Longitudinal Acceleration Signal",
            "Time[s]",
            "Acceleration[mps2]",
        )
        plots.append(vx_plot)
        plot_titles.append("")

        vx_plot_threshold = plot_graphs_threshold(
            ap_time,
            acceleration_x_dff_list,
            "Difference between Estimate and Ground Truth",
            max_expected_threshold_error,
            "Maximum Expected Longitudinal Acceleration Threshold",
            "Time[s]",
            "Acceleration[mps2]",
        )
        plots.append(vx_plot_threshold)
        plot_titles.append("")

        vy_plot = plot_graphs_signgle_signal(
            ap_time,
            odo_ay,
            CarMakerUrl.lateralAcceleration,
            "Estimated Lateral Acceleration Signal",
            "Time[s]",
            "Acceleration[mps2]",
        )
        plots.append(vy_plot)
        plot_titles.append("")

        vy_plot_threshold = plot_graphs_threshold(
            ap_time,
            acceleration_y_dff_list,
            "Difference between Estimate and Ground Truth",
            max_expected_threshold_error,
            "Maximum Expected Lateral Acceleration Threshold",
            "Time[s]",
            "Acceleration[mps2]",
        )
        plots.append(vy_plot_threshold)
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


@verifies("ReqID_2106782")
@testcase_definition(
    name="The ESC Odometry shall provide the Longitudinal and Lateral Acceleration w.r.t Ground Truth.",
    description="The ESC Odometry shall provide the Longitudinal and Lateral Acceleration w.r.t Ground Truth.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_5vjxgAGEEe-JmbR7EsJ0UA&componentURI=https%3A%2F%2Fjazz.conti.de%2"
    "Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configuration"
    "=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedLongitudinalLateralAccelerationWithGtTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedLongitudinalLateralAccelerationWithGt,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedLongitudinalLateralAccelerationWithGtTestCase,
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
