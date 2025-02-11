#!/usr/bin/env python3
"""This is the test case to continuously monitor the X and Y position during different speed conditions"""

import logging
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
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
from pl_parking.PLP.MF.VEDODO.common import plot_graphs_threshold
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

READER_NAME = "VelocitySignalConsistentToPositionSignal"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        CM_VELOCITY_X = "cm_velocity_x"
        time = "time"
        odoEstX = "odoEstX"
        odoEstY = "odoEstY"
        estVelocityX = "estVelocityX"
        estVelocityY = "estVelocityY"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_VELOCITY_X: CarMakerUrl.velocityX,
            self.Columns.time: CarMakerUrl.time,
            self.Columns.odoEstX: CarMakerUrl.odoEstX,
            self.Columns.odoEstY: CarMakerUrl.odoEstY,
            self.Columns.estVelocityX: CarMakerUrl.estVelocityX,
            self.Columns.estVelocityY: CarMakerUrl.estVelocityY,
        }


@teststep_definition(
    step_number=1,
    name="Test step to monitor the velocity signal shall be consistent to the position signal",
    description="Test step to monitor the velocity signal shall be consistent to the position signal "
    "and there should not be any jumps w.r.t previous data",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VelocitySignalConsistentToPositionSignal(TestStep):
    """Test case to monitor the velocity signal shall be consistent to the position signal.

    Objective
    ---------

    monitor the velocity signal shall be consistent to the position signal.

    Detail
    ------

    Check and monitor the velocity signal shall be consistent to the position signal.
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

        time = list(df[VedodoSignals.Columns.time])[10:]
        est_velocity_x = list(df[VedodoSignals.Columns.estVelocityX])[10:]
        est_velocity_y = list(df[VedodoSignals.Columns.estVelocityY])[10:]
        est_x = list(df[VedodoSignals.Columns.odoEstX])[10:]
        est_y = list(df[VedodoSignals.Columns.odoEstY])[10:]
        signal_summary = dict()
        est_x_array = np.array(est_x)
        est_y_array = np.array(est_y)

        diff_x = np.diff(est_x_array)
        diff_y = np.diff(est_y_array)
        diff_t = np.diff(time)
        len_diff_sig = len(diff_x)
        vx_diff_list = list()
        vy_diff_list = list()
        max_deviation_threshold = 0.02

        for i in range(len_diff_sig):
            d_vx = diff_x[i] / diff_t[i]
            vx = est_velocity_x[i]
            vx_diff_list.append(abs(abs(vx) - abs(d_vx)))
            d_vy = diff_y[i] / diff_t[i]
            vy = est_velocity_y[i]
            vy_diff_list.append(abs(abs(vy) - abs(d_vy)))

        vx_deviation_error = max(vx_diff_list)
        vy_deviation_error = max(vy_diff_list)

        if max_deviation_threshold > vx_deviation_error and max_deviation_threshold > vy_deviation_error:
            evaluation = (
                "Evaluation for Vehicle position (x,y) with different speed conditions is PASSED and no huge "
                "jumps w.r.t previous position."
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            evaluation = (
                f"Evaluation for Vehicle Velocity with position (x,y), the velocity w.r.t Position-X has"
                f"{round(vx_deviation_error, 3)} deviation and velocity w.r.t Position-Y has"
                f" {round(vy_deviation_error, 3)} deviation w.r.t the previous position, which are above the given "
                f"threshold {max_deviation_threshold}, Hence result is FAILED."
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary["VehiclePositionWithDifferentSpeedConditions"] = evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        dvx_plot = plot_graphs_threshold(
            time,
            vx_diff_list,
            "Differential Position-X Velocity",
            max_deviation_threshold,
            "Max Expected Position-X Velocity Threshold",
            "Time[s]",
            "Velocity[mps]",
        )
        dvy_plot = plot_graphs_threshold(
            time,
            vy_diff_list,
            "Differential Position-Y Velocity",
            max_deviation_threshold,
            "Max Expected Position-Y Velocity Threshold",
            "Time[s]",
            "Velocity[mps]",
        )
        plot_titles.append(" ")
        plots.append(dvx_plot)
        plot_titles.append(" ")
        plots.append(dvy_plot)

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


@verifies("ReqID_1386029")
@testcase_definition(
    name="The velocity signal shall be consistent to the position signal",
    description="Test step to monitor The velocity signal shall be consistent to the position signal",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2"
    "Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z5OUDaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti.de"
    "%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configurat"
    "ion=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VelocitySignalConsistentToPositionSignalTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VelocitySignalConsistentToPositionSignal,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VelocitySignalConsistentToPositionSignalTestCase,
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
