#!/usr/bin/env python3
"""This is the test case to check the Positions (x,y) and Yaw Rate with different Loads"""

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
from pl_parking.PLP.MF.VEDODO.common import calculate_odo_error, plot_graphs, plot_graphs_threshold
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

READER_NAME = "VedodoVelocityOdometerPositionsAndYawRateWithLoad"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        yawrate_estimation = "yawrate_estimation"
        odoEstX = "odoEstX"
        odoEstY = "odoEstY"
        CM_TIME = "cm_time"
        yawrate_gt = "yawrate_gt"
        odoCmRefX = "odoCmRefX"
        odoCmRefY = "odoCmRefY"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.odoEstX: CarMakerUrl.odoEstX,
            self.Columns.odoEstY: CarMakerUrl.odoEstY,
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.yawrate_gt: CarMakerUrl.yawrate_gt,
            self.Columns.yawrate_estimation: CarMakerUrl.yawrate_estimation,
            self.Columns.odoCmRefX: CarMakerUrl.odoCmRefX,
            self.Columns.odoCmRefY: CarMakerUrl.odoCmRefY,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the position in (x,y) and Yaw Rate with different Loads.",
    description="The ESC Odometry shall provide the position in (x,y) and Yaw Rate with different Loads.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedPositionsAndYawRateWithLoad(TestStep):
    """The ESC Odometry shall provide the position in (x,y) and Yaw Rate with different Loads.

    Objective
    ---------

    The ESC Odometry shall provide the position in (x,y) and Yaw Rate with different Loads.

    Detail
    ------

    The ESC Odometry shall provide the position in (x,y) and Yaw Rate with different Loads.
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
        odo_x = list(df[VedodoSignals.Columns.odoEstX])
        odo_y = list(df[VedodoSignals.Columns.odoEstY])
        gt_x = list(df[VedodoSignals.Columns.odoCmRefX])
        gt_y = list(df[VedodoSignals.Columns.odoCmRefY])
        gt_yaw = list(df[VedodoSignals.Columns.yawrate_gt])
        odo_yaw = list(df[VedodoSignals.Columns.yawrate_estimation])

        # Init variables
        signal_summary = dict()
        yaw_rate_deviate_list = list()
        x_deviate_list = list()
        y_deviate_list = list()
        total_dist = 0
        max_expected_deviate_yawrate: float = 0.0035
        max_expected_x_error: float = 0.06
        max_expected_y_error: float = 0.03
        _, _, driven_dist, _, _ = calculate_odo_error(gt_x, gt_y, gt_yaw, odo_yaw, odo_x, odo_y)

        for yw_gt, yw_od, xgt, xod, ygt, yod, d in zip(gt_yaw, odo_yaw, gt_x, odo_x, gt_y, odo_y, driven_dist):
            total_dist += d
            if total_dist >= 2000:
                yaw_rate_deviate_list.append(abs(yw_gt - yw_od))
                x_deviate_list.append(abs(xgt - xod))
                y_deviate_list.append(abs(ygt - yod))

        max_yaw_rate_deviate = max(yaw_rate_deviate_list)
        if max_yaw_rate_deviate < max_expected_deviate_yawrate:
            evaluation_yaw = " ".join(
                f"Evaluation of estimated yaw rate, the deviation w.r.t Ground truth is "
                f"{round(max_yaw_rate_deviate, 3)}rad/s and the expected threshold is {max_expected_deviate_yawrate}"
                f" rad/s, the deviation value is below the threshold. Hence the result is PASSED.".split()
            )
            test_result_yaw = True
        else:
            evaluation_yaw = " ".join(
                f"Evaluation of estimated yaw rate, the deviation w.r.t Ground truth is "
                f"{round(max_yaw_rate_deviate, 3)}rad/s and the expected threshold is {max_expected_deviate_yawrate}"
                f" rad/s, the deviation value is above the threshold. Hence the result is FAILED.".split()
            )
            test_result_yaw = False

        max_x_error = max(x_deviate_list)
        if max_x_error < max_expected_x_error:
            evaluation_x = " ".join(
                f"Evaluation of estimated Position-X, the deviation w.r.t ground truth is {round(max_x_error, 3)}m"
                f" and the expected threshold is {max_expected_x_error}m, the deviation value is below  "
                f"the threshold. Hence the result is PASSED.".split()
            )
            test_result_x = True
        else:
            evaluation_x = " ".join(
                f"Evaluation of estimated Position-X, the deviation w.r.t ground truth is {round(max_x_error, 3)}m"
                f" and the expected threshold is {max_expected_x_error}m, the deviation value is above  "
                f"the threshold. Hence the result is FAILED.".split()
            )
            test_result_x = False

        max_y_error = max(y_deviate_list)
        if max_y_error < max_expected_y_error:
            evaluation_y = " ".join(
                f"Evaluation of estimated Position-Y, the deviation w.r.t ground truth is {round(max_y_error, 3)}m"
                f" and the expected threshold is {max_expected_y_error}m, the deviation value is below  "
                f"the threshold. Hence the result is PASSED.".split()
            )
            test_result_y = True
        else:
            evaluation_y = " ".join(
                f"Evaluation of estimated Position-Y, the deviation w.r.t ground truth is {round(max_y_error, 3)}m"
                f" and the expected threshold is {max_expected_y_error}m, the deviation value is above  "
                f"the threshold. Hence the result is FAILED.".split()
            )
            test_result_y = False

        if test_result_yaw and test_result_x and test_result_y:
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[CarMakerUrl.odoEstX] = evaluation_x
        signal_summary[CarMakerUrl.odoEstY] = evaluation_y
        signal_summary[CarMakerUrl.yawrate_estimation] = evaluation_yaw

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        x_threshold_fig = plot_graphs_threshold(
            ap_time,
            x_deviate_list,
            "Position-X deviation error",
            max_expected_x_error,
            "Position-X Threshold",
            "Time[s]",
            "Meter[m]",
        )
        y_threshold_fig = plot_graphs_threshold(
            ap_time,
            y_deviate_list,
            "Position-Y deviation error",
            max_expected_y_error,
            "Position-Y Threshold",
            "Time[s]",
            "Meter[m]",
        )
        yaw_threshold_fig = plot_graphs_threshold(
            ap_time,
            yaw_rate_deviate_list,
            "YawRate deviation error",
            max_expected_deviate_yawrate,
            "Yaw Rate Threshold",
            "Time[s]",
            "Radiance[rad/s]",
        )
        x_plot = plot_graphs(ap_time, odo_x, CarMakerUrl.odoEstX, gt_x, CarMakerUrl.odoCmRefX, "Time[s]", "Distance[m]")
        y_plot = plot_graphs(ap_time, odo_y, CarMakerUrl.odoEstY, gt_y, CarMakerUrl.odoCmRefY, "Time[s]", "Distance[m]")
        yaw_plot = plot_graphs(
            ap_time,
            odo_yaw,
            CarMakerUrl.yawrate_estimation,
            gt_yaw,
            CarMakerUrl.yawrate_gt,
            "Time[s]",
            "Radiance[rad/s]",
        )
        plots.append(x_threshold_fig)
        plots.append(x_plot)
        plots.append(y_threshold_fig)
        plots.append(y_plot)
        plots.append(yaw_threshold_fig)
        plots.append(yaw_plot)

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


@verifies("ReqID_1386129")
@testcase_definition(
    name="The ESC Odometry shall provide the position in (x,y) and Yaw Rate with different Loads.",
    description="The ESC Odometry shall provide the position in (x,y) and Yaw Rate with different Loads.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%"
    "2Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z7DhjaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti."
    "de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configu"
    "ration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedPositionsAndYawRateWithLoadTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedPositionsAndYawRateWithLoad,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedPositionsAndYawRateWithLoadTestCase,
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
