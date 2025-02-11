#!/usr/bin/env python3
"""The ESC Odometry shall provide the vehicle speed consistent to the change of the position estimation"""

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

READER_NAME = "VedodoSpeedConsistentToTheChangeInPosition"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        odoEstX = "odoEstX"
        estVelocityX = "estVelocityX"
        CM_TIME = "cm_time"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.odoEstX: CarMakerUrl.odoEstX,
            self.Columns.estVelocityX: CarMakerUrl.estVelocityX,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the vehicle speed consistent to the change of the position estimation",
    description="The ESC Odometry shall provide the vehicle speed consistent to the change of the position estimation",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedPositionConsistentToSpeed(TestStep):
    """The ESC Odometry shall provide the vehicle speed consistent to the change of the position estimation

    Objective
    ---------

    The ESC Odometry shall provide the vehicle speed consistent to the change of the position estimation

    Detail
    ------

    The ESC Odometry shall provide the vehicle speed consistent to the change of the position estimation
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

        # skip first few frames
        ap_time = np.array(df[VedodoSignals.Columns.CM_TIME])[10:]
        odo_v = np.array(df[VedodoSignals.Columns.estVelocityX])[10:]
        odo_x = np.array(df[VedodoSignals.Columns.odoEstX])[10:]
        vx_diff_list = list()
        signal_summary = dict()
        max_error_threshold = 0.02

        velocity_x = np.diff(odo_x) / np.diff(ap_time)
        diff_sig_len = len(velocity_x)

        for i in range(diff_sig_len):
            d_vx = velocity_x[i]
            vx = odo_v[i]
            vx_diff_list.append(abs(abs(vx) - abs(d_vx)))

        max_vx_error = max(vx_diff_list)
        if max_error_threshold > max_vx_error:
            evaluation = (
                f"The Driven distance signal is consistent to the velocity signal, and the deviation "
                f"error {round(max_vx_error, 3)} is below the threshold {max_error_threshold},"
                f"Hence test result is PASSED"
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            evaluation = (
                f"The Driven distance signal is not consistent to the velocity signal, and the deviation "
                f"error {round(max_vx_error, 3)} is above the threshold {max_error_threshold},"
                f"Hence test result is FAILED"
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[f"{CarMakerUrl.odoEstX} vs {CarMakerUrl.estVelocityX}"] = evaluation

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        dvx_plot = plot_graphs_threshold(
            ap_time,
            vx_diff_list,
            "Differential Position-X Velocity",
            max_error_threshold,
            "Max Expected Position-X Velocity Threshold",
            "Time[s]",
            "Velocity[mps]",
        )
        plots.append(dvx_plot)

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


@verifies("ReqID_1386187")
@testcase_definition(
    name="The ESC Odometry shall provide the vehicle speed consistent to the change of the position estimation",
    description="The ESC Odometry shall provide the vehicle speed consistent to the change of the position estimation",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%"
    "2Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z8RoTaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti."
    "de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configu"
    "ration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedPositionConsistentToSpeedTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedPositionConsistentToSpeed,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedPositionConsistentToSpeedTestCase,
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
