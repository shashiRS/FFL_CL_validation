#!/usr/bin/env python3
"""The vehicle longitudinal acceleration shall be consistent to the vehicle velocity signal. The longitudinal
acceleration shall be the time derivative of the velocity
"""

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

READER_NAME = "VedodoAccelerationOdometryLongitudinalAccelerationWithTimeDerivativeOfTheVelocity"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        longitudinalAcceleration = "longitudinalAcceleration"
        motionStatus = "motionStatus"
        CM_TIME = "cm_time"
        estVelocityX = "estVelocityX"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.longitudinalAcceleration: CarMakerUrl.longiAcceleration,
            self.Columns.motionStatus: CarMakerUrl.motionStatus,
            self.Columns.estVelocityX: CarMakerUrl.estVelocityX,
        }


@teststep_definition(
    step_number=1,
    name="The vehicle longitudinal acceleration shall be consistent to the vehicle velocity signal. The longitudinal"
    "acceleration shall be the time derivative of the velocity",
    description="The vehicle longitudinal acceleration shall be consistent to the vehicle velocity signal. The "
    "longitudinal acceleration shall be the time derivative of the velocity",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedLongitudinalAccelerationWithWithTimeDerivativeOfTheVelocity(TestStep):
    """The vehicle longitudinal acceleration shall be consistent to the vehicle velocity signal. The longitudinal
        acceleration shall be the time derivative of the velocity"

    Objective
    ---------

    The vehicle longitudinal acceleration shall be consistent to the vehicle velocity signal. The longitudinal
    acceleration shall be the time derivative of the velocity"

    Detail
    ------

    The vehicle longitudinal acceleration shall be consistent to the vehicle velocity signal. The longitudinal
    acceleration shall be the time derivative of the velocity
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
        odo_a = list(df[VedodoSignals.Columns.longitudinalAcceleration])
        est_velocity_x = df[VedodoSignals.Columns.estVelocityX]
        est_vx_array = np.array(est_velocity_x)
        diff_vx = np.diff(est_vx_array)
        diff_t = np.diff(ap_time)
        a_flag = True
        evaluation = ""
        max_expected_threshold_error: float = 2
        len_diff_sig = len(diff_vx)
        ax_diff_list = list()
        signal_summary = dict()

        if not sum(odo_a):
            evaluation = "The Longitudinal Acceleration signal values are zero, no data is available to evaluate"
            a_flag = False

        for a in odo_a:
            if pd.isna(a) and a_flag:
                evaluation = "The Longitudinal Acceleration signal data having NAN values"
                a_flag = False
                break

        for i in range(len_diff_sig):
            d_vx = diff_vx[i] / diff_t[i]
            vx = odo_a[i]
            ax_diff_list.append(abs(abs(vx) - abs(d_vx)))

        max_error = max(ax_diff_list)
        if max_error > max_expected_threshold_error and not a_flag:
            evaluation_error = " ".join(
                f"Evaluation for Longitudinal Acceleration, the deviation error between the previous position is"
                f"{round(max_error, 3)}% and the expected threshold is 2%. The deviation error is above the given "
                f"threshold. Hence the result is FAILED.".split()
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE
        else:
            evaluation = "The Longitudinal Acceleration signal data is having valid data"
            evaluation_error = " ".join(
                f"Evaluation for Longitudinal Acceleration, the deviation error between the previous position is"
                f"{round(max_error, 3)}% and the expected threshold is 2%. The deviation error is below the given "
                f"threshold. Hence the result is PASSED.".split()
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE

        signal_summary[CarMakerUrl.longiAcceleration] = evaluation
        signal_summary[f"{CarMakerUrl.longiAcceleration} vs " f"{CarMakerUrl.ax}"] = evaluation_error

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        v_plot = plot_graphs_signgle_signal(
            ap_time,
            odo_a,
            CarMakerUrl.longiAcceleration,
            "Estimated Longitudinal Acceleration Signal",
            "Time[s]",
            "Acceleration[mps2]",
        )
        plots.append(v_plot)
        plot_titles.append("")

        v_plot_threshold = plot_graphs_threshold(
            ap_time,
            ax_diff_list,
            "Difference between Estimate and Ground Truth",
            max_expected_threshold_error,
            "Maximum Expected Acceleration Threshold",
            "Time[s]",
            "Acceleration[mps2]",
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


@verifies("ReqID_2354695")
@testcase_definition(
    name="The vehicle longitudinal acceleration shall be consistent to the vehicle velocity signal. The longitudinal "
    "acceleration shall be the time derivative of the velocity",
    description="The vehicle longitudinal acceleration shall be consistent to the vehicle velocity signal. The "
    "longitudinal acceleration shall be the time derivative of the velocity",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%"
    "2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_YCQ7YiP9Ee-SquMaddCl2A&componentURI=https%3A%2F%2Fjazz."
    "conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc."
    "configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedLongitudinalAccelerationWithWithTimeDerivativeOfTheVelocityTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedLongitudinalAccelerationWithWithTimeDerivativeOfTheVelocity,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedLongitudinalAccelerationWithWithTimeDerivativeOfTheVelocityTestCase,
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
