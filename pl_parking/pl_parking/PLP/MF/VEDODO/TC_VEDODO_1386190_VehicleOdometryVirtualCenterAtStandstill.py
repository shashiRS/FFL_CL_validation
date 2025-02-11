#!/usr/bin/env python3
"""The ESC Odometry shall provide the virtual center front wheel angle during standstill"""

import logging
import os
import sys
import tempfile
from math import tan
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
from pl_parking.PLP.MF.VEDODO.constants import CarMakerUrl, OtherConstants

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "Anil A, uie64067"
__copyright__ = "2012-2024, Continental AG"
__version__ = "0.0.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

READER_NAME = "VedodoVelocityOdometryVirtualCenterDuringStandstill"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        odosteerAngFrontAxle = "odosteerAngFrontAxle"
        motionStatus = "motionStatus"
        CM_TIME = "cm_time"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.odosteerAngFrontAxle: CarMakerUrl.odosteerAngFrontAxle,
            self.Columns.motionStatus: CarMakerUrl.motionStatus,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the virtual center front wheel angle during standstill",
    description="The ESC Odometry shall provide the virtual center front wheel angle during standstill",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleVirtualCenterStandStill(TestStep):
    """The ESC Odometry shall provide the virtual center front wheel angle during standstill.

    Objective
    ---------

    The ESC Odometry shall provide the virtual center front wheel angle during standstill.

    Detail
    ------

    The ESC Odometry shall provide the virtual center front wheel angle during standstill.
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
        est_steer = list(df[VedodoSignals.Columns.odosteerAngFrontAxle])
        est_motion_status = list(df[VedodoSignals.Columns.motionStatus])
        steer_flag = True
        max_radius_deviation_threshold = 10
        evaluation = ""
        # WHEELBASE_M in meters and converted to centimeters
        wheel_base = OtherConstants.WHEELBASE_M * 100
        signal_summary = dict()
        deviate_radius_list = list()

        if not sum(est_steer):
            evaluation = "The SteerAngFrontAxle signal contains all zeros"
            steer_flag = False
        else:
            for x in est_steer:
                if pd.isna(x):
                    evaluation = "The SteerAngFrontAxle signal data has NAN values"
                    steer_flag = False
                    break

        # Process data if valid
        if steer_flag:
            evaluation = "The SteerAngFrontAxle signal data has valid data"

            for s, m in zip(est_steer, est_motion_status):
                if not m and s:
                    radius = wheel_base / tan(s)
                else:
                    radius = 0
                deviate_radius_list.append(radius)

            max_radius_deviation = max(deviate_radius_list)
            if max_radius_deviation <= max_radius_deviation_threshold:
                evaluation_error = " ".join(
                    f"Evaluation for virtual center front steer wheel angle during standstill radius deviation error "
                    f"{round(max_radius_deviation, 3)}cm is below the expected threshold "
                    f"{max_radius_deviation_threshold}cm. Hence the test result is PASSED".split()
                )
                test_result = fc.PASS
                self.result.measured_result = TRUE
            else:
                evaluation_error = " ".join(
                    f"Evaluation for virtual center front steer wheel angle during standstill radius deviation error "
                    f"{round(max_radius_deviation, 3)}cm is above the expected threshold "
                    f"{max_radius_deviation_threshold}cm. Hence the test result is FAILED".split()
                )
                test_result = fc.FAIL
                self.result.measured_result = FALSE
        else:
            evaluation_error = (
                "Evaluation for virtual center front steer wheel angle radius is not possible with invalid data,"
                " Hence the test result is FAILED"
            )
            test_result = fc.FAIL
            self.result.measured_result = False

        signal_summary[CarMakerUrl.odosteerAngFrontAxle] = evaluation
        signal_summary[f"{CarMakerUrl.odosteerAngFrontAxle} Radius"] = evaluation_error
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        steer_plot = plot_graphs_signgle_signal(
            ap_time,
            est_steer,
            CarMakerUrl.odosteerAngFrontAxle,
            "Estimated SteerAngFrontAxle Signal",
            "Time[s]",
            "Steer Angle[rad]",
        )
        plots.append(steer_plot)
        plot_titles.append("")

        steer_threshold_plot = plot_graphs_threshold(
            ap_time,
            deviate_radius_list,
            "Radius Deviation Error",
            max_radius_deviation_threshold,
            "Radius Threshold",
            "Time[s]",
            "Radius[cm]",
        )
        plots.append(steer_threshold_plot)
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


@verifies("ReqID_1386190")
@testcase_definition(
    name="The ESC Odometry shall provide the virtual center front wheel angle during standstill.",
    description="The ESC Odometry shall provide the virtual center front wheel angle during standstill.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%"
    "2Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z8RpDaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti."
    r"\de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.config"
    "uration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleVirtualCenterStandStillTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleVirtualCenterStandStill,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleVirtualCenterStandStillTestCase,
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
