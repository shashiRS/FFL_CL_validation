#!/usr/bin/env python3
"""This is the test case to check the Side Slip Angle w.r.t Ground Truth"""

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

READER_NAME = "VedodoVelocityOdometrySideSlipAngleWithGt"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        est_side_slip_angle = "est_side_slip_angle"
        gt_side_slip_angle = "gt_side_slip_angle"
        CM_TIME = "cm_time"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.gt_side_slip_angle: CarMakerUrl.gt_side_slip_angle,
            self.Columns.est_side_slip_angle: CarMakerUrl.est_side_slip_angle,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the Side Slip Angle w.r.t Ground Truth.",
    description="The ESC Odometry shall provide the Side Alip Angle w.r.t Ground Truth.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedSideSlipAngleWithGt(TestStep):
    """The ESC Odometry shall provide the Side Slip Angle w.r.t Ground Truth.

    Objective
    ---------

    The ESC Odometry shall provide the Side Slip Angle w.r.t Ground Truth.

    Detail
    ------

    The ESC Odometry shall provide the Side Slip Angle w.r.t Ground Truth.
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
        odo_s = list(df[VedodoSignals.Columns.est_side_slip_angle])
        ref_s = list(df[VedodoSignals.Columns.gt_side_slip_angle])
        s_flag = True
        evaluation = ""
        side_slip_angle_dff = {"error": [], "time": []}
        max_expected_error: float = 0.01

        # Init variables
        signal_summary = dict()
        if not sum(odo_s):
            evaluation = "The Side Slip Angle signal values are zero, no data is available to evaluate"
            s_flag = False

        for s in odo_s:
            if pd.isna(s) and s_flag:
                evaluation = "The Side Slip Angle signal data having NAN values"
                s_flag = False
                break

        for gt_angle, odo_angle, t in zip(ref_s, odo_s, ap_time):
            if odo_angle and gt_angle:
                side_slip_angle_dff["error"].append(abs(abs(gt_angle) - abs(odo_angle)))
                side_slip_angle_dff["time"].append(t)

        max_error = max(side_slip_angle_dff["error"])

        if s_flag:
            evaluation = "The Side Slip Angle signal is having valid data"

        if max_error > max_expected_error:
            evaluation_error = " ".join(
                f"Evaluation for Side Slip Angle, "
                f"The deviation between estimate and reference vehicle Side Slip Angle is"
                f" {round(max_error, 3)}rad and the error is above the threshold {max_expected_error}rad. Hence"
                f"the test result is FAILED".split()
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE
        else:
            evaluation_error = " ".join(
                f"Evaluation for Side Slip Angle, "
                f"The deviation between estimate and reference vehicle Side Slip Angle is"
                f" {round(max_error, 3)}rad and the error is below the threshold {max_expected_error}rad. Hence"
                f"the test result is PASSED".split()
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE

        signal_summary[CarMakerUrl.est_side_slip_angle] = evaluation
        signal_summary[f"{CarMakerUrl.est_side_slip_angle} vs " f"{CarMakerUrl.gt_side_slip_angle}"] = evaluation_error

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        side_slip_plot = plot_graphs(
            ap_time,
            odo_s,
            CarMakerUrl.est_side_slip_angle,
            ref_s,
            CarMakerUrl.gt_side_slip_angle,
            "Time[s]",
            "Radiance[rad]",
        )
        plots.append(side_slip_plot)
        plot_titles.append("")

        side_slip_plot_threshold = plot_graphs_threshold(
            side_slip_angle_dff["time"],
            side_slip_angle_dff["error"],
            "Difference between Estimate and Ground Truth",
            max_expected_error,
            "Maximum Expected Side Slip Angle Threshold",
            "Time[s]",
            "Radiance[rad]",
        )
        plots.append(side_slip_plot_threshold)
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


@verifies("ReqID_1386033")
@testcase_definition(
    name="The ESC Odometry shall provide the Side Slip Angle w.r.t Ground Truth.",
    description="The ESC Odometry shall provide the Side Slip Angle w.r.t Ground Truth.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%"
    "2Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z5OVjaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti."
    "de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configu"
    "ration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedSideSlipAngleWithGtTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedSideSlipAngleWithGt,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedSideSlipAngleWithGtTestCase,
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
