#!/usr/bin/env python3
"""This is the test case to check the Driven Distance with forward and reverse directions"""

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

READER_NAME = "VedodoVelocityOdometryDrivenDistanceWithForwardAndReverseDirection"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        drivenDistance_m = "drivenDistance_m"
        estVelocityX = "estVelocityX"
        CM_TIME = "cm_time"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.drivenDistance_m: CarMakerUrl.drivenDistance_m,
            self.Columns.estVelocityX: CarMakerUrl.estVelocityX,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the Driven Distance With Forward And Reverse Direction.",
    description="The ESC Odometry shall provide the Driven Distance With Forward And Reverse Direction.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedDrivenDistanceWithForwardAndReverseDirection(TestStep):
    """The ESC Odometry shall provide the Driven Distance With Forward And Reverse Direction.

    Objective
    ---------

    The ESC Odometry shall provide the Driven Distance With Forward And Reverse Direction.

    Detail
    ------

    The ESC Odometry shall provide the Driven Distance With Forward And Reverse Direction.
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
        odo_v = list(df[VedodoSignals.Columns.estVelocityX])
        odo_driven_dist = list(df[VedodoSignals.Columns.drivenDistance_m])

        dd_flag = True
        evaluation = ""

        # Init variables
        signal_summary = dict()
        if not sum(odo_driven_dist):
            evaluation = (
                "The Driven distance signal values are zero, no data is available to evaluate,"
                "Hence test result is FAILED"
            )
            dd_flag = False

        if not sum(odo_v):
            evaluation = (
                "The sum of Vehicle velocity signal value is zero, no data is available to evaluate"
                "the driven distance signal, Hence test result is FAILED"
            )
            dd_flag = False

        for d, v in zip(odo_driven_dist, odo_v):
            if v:
                if d >= 1000:
                    dd_flag = False
                    evaluation = "The Driven Distance signal value is not reset at 1000m, Hence test result is FAILED"
                    break

        if dd_flag:
            evaluation = (
                "The Driven distance signal is resetting when the value is reached near to 1000m distance in"
                "Forward or Reverse direction of the Vehicle. Hence test result is PASSED"
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[CarMakerUrl.drivenDistance_m] = evaluation

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        dd_plot = plot_graphs_signgle_signal(
            ap_time,
            odo_driven_dist,
            CarMakerUrl.drivenDistance_m,
            "Estimated Driven Distance Signal",
            "Time[s]",
            "Distance[m]",
        )
        plots.append(dd_plot)

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


@verifies("ReqID_1386197")
@testcase_definition(
    name="The ESC Odometry shall provide the Driven Distance With Forward And Reverse Direction.",
    description="The ESC Odometry shall provide the Driven Distance With Forward And Reverse Direction.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2"
    "Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z8RqzaaEe6mrdm2_agUYg&oslc_config.context=https%3A%2F%2Fjazz.c"
    "onti.de%2Fgc%2Fconfiguration%2F17099&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_"
    "D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedDrivenDistanceWithForwardAndReverseDirectionTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedDrivenDistanceWithForwardAndReverseDirection,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedDrivenDistanceWithForwardAndReverseDirectionTestCase,
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
