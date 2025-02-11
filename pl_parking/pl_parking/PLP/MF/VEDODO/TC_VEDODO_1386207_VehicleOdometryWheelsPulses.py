#!/usr/bin/env python3
"""This is the test case to check the WheelPulses"""

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

READER_NAME = "VedodoVelocityOdometerWheelPulses"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        CM_TIME = "cm_time"
        wheelPulsesFL_nu = "wheelPulsesFL_nu"
        wheelPulsesFR_nu = "wheelPulsesFR_nu"
        wheelPulsesRL_nu = "wheelPulsesRL_nu"
        wheelPulsesRR_nu = "wheelPulsesRR_nu"
        longitudinalVelocity_mps = "longitudinalVelocity_mps"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.wheelPulsesFL_nu: CarMakerUrl.wheelPulsesFL_nu,
            self.Columns.wheelPulsesFR_nu: CarMakerUrl.wheelPulsesFR_nu,
            self.Columns.wheelPulsesRL_nu: CarMakerUrl.wheelPulsesRL_nu,
            self.Columns.wheelPulsesRR_nu: CarMakerUrl.wheelPulsesRR_nu,
            self.Columns.longitudinalVelocity_mps: CarMakerUrl.longitudinalVelocity_mps,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the WheelPulses.",
    description="The ESC Odometry shall provide the WheelPulses.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedWheelPulses(TestStep):
    """The ESC Odometry shall provide the WheelPulses.

    Objective
    ---------

    The ESC Odometry shall provide the WheelPulses.

    Detail
    ------

    The ESC Odometry shall provide the WheelPulses.
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
        wheel_fl = list(df[VedodoSignals.Columns.wheelPulsesFL_nu])
        wheel_fr = list(df[VedodoSignals.Columns.wheelPulsesFR_nu])
        wheel_rl = list(df[VedodoSignals.Columns.wheelPulsesRL_nu])
        wheel_rr = list(df[VedodoSignals.Columns.wheelPulsesRR_nu])
        odo_velocity = list(df[VedodoSignals.Columns.longitudinalVelocity_mps])

        # Init variables
        signal_summary = dict()
        fl_flag = True
        fr_flag = True
        rl_flag = True
        rr_flag = True
        v_flag = True
        evaluation_fl = ""
        evaluation_fr = ""
        evaluation_rl = ""
        evaluation_rr = ""

        if sum(odo_velocity):
            evaluation_velocity = "The longitudinal velocity signal data is having valid data."
            for fl, fr, rl, rr in zip(wheel_fl, wheel_fr, wheel_rl, wheel_rr):
                if fl_flag and (fl < 0 or fl > 1000):
                    fl_flag = False
                    evaluation_fl = (
                        "The Evaluation of Front Left Wheel Pulse data is outside the given range "
                        "(0, 1000), Hence test result is FAILED."
                    )
                if fr_flag and (fr < 0 or fr > 1000):
                    fr_flag = False
                    evaluation_fr = (
                        "The Evaluation of Front Right Wheel Pulse data is outside the given range "
                        "(0, 1000), Hence test result is FAILED."
                    )
                if rl_flag and (rl < 0 or rl > 1000):
                    rl_flag = False
                    evaluation_rl = (
                        "The Evaluation of Rear Left Wheel Pulse data is outside the given range "
                        "(0, 1000), Hence test result is FAILED."
                    )
                if rr_flag and (rr < 0 or rr > 1000):
                    rr_flag = False
                    evaluation_rr = (
                        "The Evaluation of Rear Right Wheel Pulse data is outside the given range "
                        "(0, 1000), Hence test result is FAILED."
                    )
        else:
            v_flag = False
            evaluation_velocity = "The longitudinal velocity signal values are zero, no data is available to evaluate"
            evaluation_fl = (
                "The longitudinal velocity signal values are zero, Hence Front Left Wheel Pulse Evaluation"
                " is not Possible, Hence test result is FAILED."
            )
            evaluation_fr = (
                "The longitudinal velocity signal values are zero, Hence Front Right Wheel Pulse "
                "Evaluation is not Possible, Hence test result is FAILED."
            )
            evaluation_rl = (
                "The longitudinal velocity signal values are zero, Hence Rear Left Wheel Pulse Evaluation"
                " is not Possible, Hence test result is FAILED."
            )
            evaluation_rr = (
                "The longitudinal velocity signal values are zero, Hence Rear Right Wheel Pulse Evaluation"
                " is not Possible, Hence test result is FAILED."
            )

        if fl_flag:
            evaluation_fl = (
                "The Evaluation of Front Left Wheel Pulse data is within the given range (0, 1000), "
                "Hence test result is PASSED."
            )
        if fr_flag:
            evaluation_fr = (
                "The Evaluation of Front Right Wheel Pulse data is within the given range (0, 1000), "
                "Hence test result is PASSED."
            )
        if rl_flag:
            evaluation_rl = (
                "The Evaluation of Rear Left Wheel Pulse data is within the given range (0, 1000), "
                "Hence test result is PASSED."
            )
        if rr_flag:
            evaluation_rr = (
                "The Evaluation of Rear Right Wheel Pulse data is within the given range (0, 1000), "
                "Hence test result is PASSED."
            )

        if v_flag and fl_flag and fr_flag and rl_flag and rr_flag:
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[CarMakerUrl.longitudinalVelocity_mps] = evaluation_velocity
        signal_summary[CarMakerUrl.wheelPulsesFL_nu] = evaluation_fl
        signal_summary[CarMakerUrl.wheelPulsesFR_nu] = evaluation_fr
        signal_summary[CarMakerUrl.wheelPulsesRL_nu] = evaluation_rl
        signal_summary[CarMakerUrl.wheelPulsesRR_nu] = evaluation_rr

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        plot_fl = plot_graphs_signgle_signal(
            ap_time, wheel_fl, CarMakerUrl.wheelPulsesFL_nu, "Front Left Wheel Pulse", "Time[s]", "WheelPulse"
        )
        plot_fr = plot_graphs_signgle_signal(
            ap_time, wheel_fr, CarMakerUrl.wheelPulsesFR_nu, "Front Right Wheel Pulse", "Time[s]", "WheelPulse"
        )
        plot_rl = plot_graphs_signgle_signal(
            ap_time, wheel_rl, CarMakerUrl.wheelPulsesRL_nu, "Rear Left Wheel Pulse", "Time[s]", "WheelPulse"
        )
        plot_rr = plot_graphs_signgle_signal(
            ap_time, wheel_rr, CarMakerUrl.wheelPulsesRR_nu, "Rear Right Wheel Pulse", "Time[s]", "WheelPulse"
        )
        plot_v = plot_graphs_signgle_signal(
            ap_time,
            odo_velocity,
            CarMakerUrl.longitudinalVelocity_mps,
            "Longitudinal Velocity",
            "Time[s]",
            "Velocity[mps]",
        )

        plots.append(plot_fl)
        plots.append(plot_fr)
        plots.append(plot_rl)
        plots.append(plot_rr)
        plots.append(plot_v)

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


@verifies("ReqID_1386207")
@testcase_definition(
    name="The ESC Odometry shall provide the WheelPulses.",
    description="When the vehicle moves on, the ESC Odometry shall detect the correct driving direction (forward,"
    " reverse) latest after the second wheel pulse occured at any of the four wheels.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F"
    "%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z8RtzaaEe6mrdm2_agUYg&oslc_config.context=https%3A%2F%2Fja"
    "zz.conti.de%2Fgc%2Fconfiguration%2F17099&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-project"
    "s%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedWheelPulsesTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedWheelPulses,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedWheelPulsesTestCase,
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
