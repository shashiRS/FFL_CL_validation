#!/usr/bin/env python3
"""This is the test case to check and monitor the MotionState From No Standstill To Standstill with Wheel Pulses"""

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
from pl_parking.PLP.MF.VEDODO.common import plot_graphs, plot_graphs_signgle_signal
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

READER_NAME = "VedodoVelocityOdometryMotionStateFromNoStandstillToStandstillWithWheelPulses"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        motionStatus = "motionStatus"
        CM_TIME = "cm_time"
        wheelPulsesFL_nu = "wheelPulsesFL_nu"
        wheelPulsesFR_nu = "wheelPulsesFR_nu"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.motionStatus: CarMakerUrl.motionStatus,
            self.Columns.wheelPulsesFL_nu: CarMakerUrl.wheelPulsesFL_nu,
            self.Columns.wheelPulsesFR_nu: CarMakerUrl.wheelPulsesFR_nu,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide and monitor the MotionState From No Standstill To Standstill with "
    "Wheel Pulses.",
    description="The ESC Odometry shall provide and monitor the MotionState From Standstill To "
    "NoStandstill with Wheel Pulses.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedMotionStateFromNoStandstillToStandstillWithWheelPulses(TestStep):
    """The ESC Odometry shall provide and monitor the MotionState From No Standstill To Standstill with Wheel Pulses.

    Objective
    ---------

    The ESC Odometry shall provide and monitor the MotionState From No Standstill To Standstill with Wheel Pulses.

    Detail
    ------

    The ESC Odometry shall provide and monitor the MotionState From No Standstill To Standstill with Wheel Pulses.
    """

    custom_report = MfCustomTeststepReport

    def __init__(self):
        super().__init__()
        self.sig_sum = None

    def process(self):
        """Evaluating test case"""
        _log.debug("Starting processing...")
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)
        df: pd.DataFrame = self.readers[READER_NAME]

        ap_time = list(df[VedodoSignals.Columns.CM_TIME])
        odo_status = list(df[VedodoSignals.Columns.motionStatus])
        wheel_fl = list(df[VedodoSignals.Columns.wheelPulsesFL_nu])
        wheel_fr = list(df[VedodoSignals.Columns.wheelPulsesFR_nu])

        # Init variables
        signal_summary = dict()
        # Actual wait time is 100ms, each time stamp gives 10ms for every instance, due to mentioned wait time as 30
        wait_time = 30
        time_counter = 0
        fl_wheel_ticks = []
        fr_wheel_ticks = []
        motion_flag = False
        signal_len = len(odo_status)

        for i in range(1, signal_len):
            current_odo = odo_status[i]
            previous_odo = odo_status[i - 1]

            if (previous_odo == 1 or motion_flag) and current_odo == 0 and time_counter < wait_time:
                motion_flag = True
                time_counter += 1
                fl_wheel_ticks.append(wheel_fl[i])
                fr_wheel_ticks.append(wheel_fr[i])
            elif previous_odo == 0 and current_odo == 1:
                motion_flag = False
                time_counter = 0
                fl_wheel_ticks.append(0)
                fr_wheel_ticks.append(0)
            else:
                fl_wheel_ticks.append(0)
                fr_wheel_ticks.append(0)

        max_fr_wheel = max(fr_wheel_ticks)
        max_fl_wheel = max(fl_wheel_ticks)
        if max_fr_wheel < 990 or max_fl_wheel < 990:
            evaluation = (
                f"The evaluation for motion state is changed from 1 to 0 and during this time the front "
                f"wheel ticks are not resetting at 1000m, and wheel pulses occurred {max_fr_wheel}"
                f" times, Hence the test result is PASSED"
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            evaluation = (
                f"The evaluation for motion state is not changed from 1 to 0, even though the front "
                f"wheel ticks are resetting at 1000m, and wheel pulses occurred {max_fr_wheel} times, "
                f"Hence the test result is FAILED"
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[CarMakerUrl.motionStatus] = evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        plot_fl = plot_graphs(
            ap_time,
            wheel_fl,
            CarMakerUrl.wheelPulsesFL_nu,
            odo_status,
            CarMakerUrl.motionStatus,
            "Time[s]",
            "MotionState and Wheel Pulse Ticks",
        )

        plot_fr = plot_graphs(
            ap_time,
            wheel_fr,
            CarMakerUrl.wheelPulsesFR_nu,
            odo_status,
            CarMakerUrl.motionStatus,
            "Time[s]",
            "MotionState and Wheel Pulse Ticks",
        )
        plot_s = plot_graphs_signgle_signal(
            ap_time, odo_status, CarMakerUrl.motionStatus, "Odometry Motion Status", "Time[s]", "Status"
        )
        plots.append(plot_fl)
        plot_titles.append("")
        plots.append(plot_fr)
        plot_titles.append("")
        plots.append(plot_s)
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


@verifies("ReqID_1386051")
@testcase_definition(
    name="The ESC Odometry shall provide and monitor the MotionState From No Standstill To Standstill "
    "with Wheel Pulses.",
    description="The ESC Odometry shall provide and monitor the MotionState From No Standstill To Standstill "
    "with Wheel Pulses.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F"
    "%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z5OZDaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti"
    ".de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.config"
    "uration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedMotionStateFromNoStandstillToStandstillWithWheelPulsesTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedMotionStateFromNoStandstillToStandstillWithWheelPulses,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedMotionStateFromNoStandstillToStandstillWithWheelPulsesTestCase,
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
