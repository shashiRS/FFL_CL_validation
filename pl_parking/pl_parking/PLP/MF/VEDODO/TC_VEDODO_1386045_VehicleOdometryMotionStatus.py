#!/usr/bin/env python3
"""This is the test case to check the MotionStatus"""

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

READER_NAME = "VedodoVelocityOdometryMotionStatus"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        motionStatus = "motionStatus"
        CM_TIME = "cm_time"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.motionStatus: CarMakerUrl.motionStatus,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the MotionStatus.",
    description="The ESC Odometry shall provide the MotionStatus.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedMotionStatus(TestStep):
    """The ESC Odometry shall provide the MotionStatus.

    Objective
    ---------

    The ESC Odometry shall provide the MotionStatus.

    Detail
    ------

    The ESC Odometry shall provide the MotionStatus.
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
        odo_status = list(df[VedodoSignals.Columns.motionStatus])

        # Init variables
        signal_summary = dict()
        if not sum(odo_status):
            evaluation = "The MotionStatus signal values are zero, the vehicle is in StandStill state"
            test_result = fc.FAIL
            self.result.measured_result = FALSE
        else:
            evaluation = "The vehicle MotionStatus value is changed, and it's in No StandStill state"
            test_result = fc.PASS
            self.result.measured_result = TRUE

        signal_summary[CarMakerUrl.motionStatus] = evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        x_plot = plot_graphs_signgle_signal(
            ap_time, odo_status, CarMakerUrl.motionStatus, "Estimated motionStatus Signal", "Time[s]", "Status"
        )
        plots.append(x_plot)

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


@verifies("ReqID_1386045")
@testcase_definition(
    name="The ESC Odometry shall provide the MotionStatus.",
    description="The ESC Odometry shall provide the MotionStatus.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F"
    "%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z5OYjaaEe6mrdm2_agUYg&oslc_config.context=https%3A%2F%2Fjaz"
    "z.conti.de%2Fgc%2Fconfiguration%2F17099&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-project"
    "s%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedMotionStatusTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedMotionStatus,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedMotionStatusTestCase,
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
