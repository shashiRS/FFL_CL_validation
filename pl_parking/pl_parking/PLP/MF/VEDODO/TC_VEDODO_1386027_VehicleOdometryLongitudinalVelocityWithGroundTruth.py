#!/usr/bin/env python3
"""This is the test case to check the longitudinal velocity w.r.t Ground Truth"""

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

READER_NAME = "VedodoVelocityOdometryLongitudinalVelocityWithGt"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        longitudinalVelocity_mps = "longitudinalVelocity_mps"
        velocityX = "velocityX"
        CM_TIME = "cm_time"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.velocityX: CarMakerUrl.velocityX,
            self.Columns.longitudinalVelocity_mps: CarMakerUrl.longitudinalVelocity_mps,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the longitudinal velocity w.r.t Ground Truth.",
    description="The ESC Odometry shall provide the longitudinal velocity w.r.t Ground Truth.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedLongitudinalVelocityWithGt(TestStep):
    """The ESC Odometry shall provide the longitudinal velocity w.r.t Ground Truth.

    Objective
    ---------

    The ESC Odometry shall provide the longitudinal velocity w.r.t Ground Truth.

    Detail
    ------

    The ESC Odometry shall provide the longitudinal velocity w.r.t Ground Truth.
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
        odo_v = list(df[VedodoSignals.Columns.longitudinalVelocity_mps])
        ref_v = list(df[VedodoSignals.Columns.velocityX])
        v_flag = True
        evaluation = ""
        velocity_dff_list = list()
        max_expected_relative_error: float = 0.01
        vehicle_speed_condition: float = 0.2

        # Init variables
        signal_summary = dict()
        if not sum(odo_v):
            evaluation = "The longitudinal velocity signal values are zero, no data is available to evaluate"
            v_flag = False

        for x in odo_v:
            if pd.isna(x) and v_flag:
                evaluation = "The longitudinal velocity signal data having NAN values"
                v_flag = False
                break

        for gv, ov in zip(ref_v, odo_v):
            if abs(ov) >= vehicle_speed_condition:
                error_diff = abs(gv) - abs(ov)
            else:
                error_diff = 0
            velocity_dff_list.append(error_diff)

        max_error = max(velocity_dff_list)

        if max_error > max_expected_relative_error and v_flag:
            evaluation = "The longitudinal velocity signal data is having valid data"
            evaluation_error = " ".join(
                f"Evaluation for Longitudinal velocity the maximum expected threshold is 0.01ms. The deviation "
                f"between estimate and reference vehicle velocity is {round(max_error, 3)}mps. The deviation is "
                f"above the threshold. Hence the result is FAILED".split()
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE
        else:
            evaluation_error = " ".join(
                f"Evaluation for Longitudinal velocity the maximum expected threshold is 0.01ms. The deviation "
                f"between estimate and reference vehicle velocity is {round(max_error, 3)}mps. The deviation is "
                f"below the threshold. Hence the result is PASSED".split()
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE

        signal_summary[CarMakerUrl.longitudinalVelocity_mps] = evaluation
        signal_summary[f"{CarMakerUrl.longitudinalVelocity_mps} vs " f"{CarMakerUrl.velocityX}"] = evaluation_error

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        v_plot = plot_graphs_signgle_signal(
            ap_time,
            odo_v,
            CarMakerUrl.longitudinalVelocity_mps,
            "Estimated Longitudinal Velocity Signal",
            "Time[s]",
            "Velocity[mps]",
        )
        plots.append(v_plot)
        plot_titles.append("")

        v_plot_threshold = plot_graphs_threshold(
            ap_time,
            velocity_dff_list,
            "Difference between Estimate and Ground Truth",
            max_expected_relative_error,
            "Maximum Expected Velocity Threshold",
            "Time[s]",
            "Velocity[mps]",
        )
        plots.append(v_plot_threshold)
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


@verifies("ReqID_1386027")
@testcase_definition(
    name="The ESC Odometry shall provide the longitudinal velocity w.r.t Ground Truth.",
    description="The ESC Odometry shall provide the longitudinal velocity w.r.t Ground Truth.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_3z5OUTaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti.de%2"
    "Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configuration"
    "=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedLongitudinalVelocityWithGtTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedLongitudinalVelocityWithGt,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedLongitudinalVelocityWithGtTestCase,
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
