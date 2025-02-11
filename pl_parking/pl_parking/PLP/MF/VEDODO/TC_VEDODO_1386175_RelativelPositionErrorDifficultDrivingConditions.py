#!/usr/bin/env python3
"""This is the test case to validate the relative position error shall not exceed 0.2 m per driven meter during
difficult driving conditions
"""

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
from pl_parking.PLP.MF.VEDODO.common import (
    calculate_odo_error,
    get_relative_positional_error_per_meter,
    plot_graphs,
    plot_graphs_threshold,
)
from pl_parking.PLP.MF.VEDODO.constants import CarMakerUrl

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


__author__ = "Anil A, Uie64067"
__copyright__ = "2012-2024, Continental AG"
__version__ = "0.0.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

READER_NAME = "VedodoRelativePositionErrorInDifficultDrivingConditions"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        CM_TIME = "cm_time"
        ODO_CM_REF_X = "odoCmRefX"
        ODO_CM_REF_Y = "odoCmRefY"
        ODO_EST_X = "odoEstX"
        ODO_EST_Y = "odoEstY"
        ODO_CM_REF_YAWANG_EGO_RA_CUR = "odoCmRefyawAngEgoRaCur"
        YAW_ANGLE = "yawAngle"
        GT_Velocity = "gt_velocity"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.ODO_CM_REF_X: CarMakerUrl.odoCmRefX,
            self.Columns.ODO_CM_REF_Y: CarMakerUrl.odoCmRefY,
            self.Columns.ODO_EST_X: CarMakerUrl.odoEstX,
            self.Columns.ODO_EST_Y: CarMakerUrl.odoEstY,
            self.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR: CarMakerUrl.odoCmRefyawAngEgoRaCur,
            self.Columns.YAW_ANGLE: CarMakerUrl.yawAngle,
            self.Columns.GT_Velocity: CarMakerUrl.velocityX,
        }


@teststep_definition(
    step_number=1,
    name="The relative position error shall not exceed 0.2 m per driven meter during difficult driving conditions.",
    description="The relative position error shall not exceed 0.2 m per driven meter during "
    "difficult driving conditions.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoRelativePositionErrorDifficultDrivingConditions(TestStep):
    """The relative position error shall not exceed 0.2 m per driven meter during "difficult driving conditions".

    Objective
    ---------

    The relative position error shall not exceed 0.2 m per driven meter during "difficult driving conditions".

    Detail
    ------

    The relative position error shall not exceed 0.2 m per driven meter during "difficult driving conditions".
    """

    custom_report = MfCustomTeststepReport

    def __init__(self):
        super().__init__()
        self.sig_summary = None

    def process(self, **kwargs):
        """Evaluating test case"""
        _log.debug("Starting processing...")
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)
        df: pd.DataFrame = self.readers[READER_NAME]
        max_expected_relative_error: float = 0.2
        signal_summary = dict()
        test_result_list = list()
        # Ignoring first few frames to settle the algorithm
        ap_time = list(df[VedodoSignals.Columns.CM_TIME])[3:]
        gt_x = list(df[VedodoSignals.Columns.ODO_CM_REF_X])[3:]
        gt_y = list(df[VedodoSignals.Columns.ODO_CM_REF_Y])[3:]
        x_estimated = list(df[VedodoSignals.Columns.ODO_EST_X])[3:]
        y_estimated = list(df[VedodoSignals.Columns.ODO_EST_Y])[3:]
        psi_gt = list(df[VedodoSignals.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR])[3:]
        psi_estimated = list(df[VedodoSignals.Columns.YAW_ANGLE])[3:]

        _, _, _, relative_long, relative_lat = calculate_odo_error(
            gt_x, gt_y, psi_gt, psi_estimated, x_estimated, y_estimated
        )
        relative_long_per_meter = get_relative_positional_error_per_meter(gt_x, x_estimated, ap_time)
        relative_lat_per_meter = get_relative_positional_error_per_meter(gt_y, y_estimated, ap_time)

        max_relative_longi_error = max(relative_long_per_meter["error"])
        if max_relative_longi_error > max_expected_relative_error:
            evaluation_relative_long = (
                f"Evaluation for Relative Longitudinal position error during difficult driving conditions, the max "
                f"relative longitudinal error is {round(max_relative_longi_error, 3)}m and which is above the threshold"
                f" of {max_expected_relative_error}m. Hence the test result is FAILED."
            )
            test_result_list.append(False)
        else:
            evaluation_relative_long = (
                f"Evaluation for Relative Longitudinal position error during difficult driving conditions, the max "
                f"relative longitudinal error is {round(max_relative_longi_error, 3)}m and which is within the "
                f"threshold of {max_expected_relative_error}m. Hence the test result is PASSED."
            )
            test_result_list.append(True)

        max_relative_lat_error = max(relative_lat_per_meter["error"])
        if max_relative_lat_error > max_expected_relative_error:
            evaluation_relative_lat = (
                f"Evaluation for Relative Lateral position error during difficult driving conditions, the max "
                f"relative lateral error is {round(max_relative_lat_error, 3)}m and which is above the threshold "
                f"of {max_expected_relative_error}m. Hence the test result is FAILED."
            )
            test_result_list.append(False)
        else:
            evaluation_relative_lat = (
                f"Evaluation for Relative Lateral position error during difficult driving conditions, the max "
                f"relative lateral error is {round(max_relative_lat_error, 3)}m and which is above the threshold "
                f"of {max_expected_relative_error}m. Hence the test result is PASSED."
            )
            test_result_list.append(True)

        if all(test_result_list):
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[CarMakerUrl.odoEstX] = evaluation_relative_long
        signal_summary[CarMakerUrl.odoEstY] = evaluation_relative_lat

        self.sig_summary = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_summary)
        remarks.append("")

        x_plot = plot_graphs(
            ap_time, x_estimated, CarMakerUrl.odoEstX, gt_x, CarMakerUrl.odoCmRefX, "Time[s]", "Distance[m]"
        )
        y_plot = plot_graphs(
            ap_time, y_estimated, CarMakerUrl.odoEstY, gt_y, CarMakerUrl.odoCmRefY, "Time[s]", "Distance[m]"
        )
        x_plot_th = plot_graphs_threshold(
            relative_long_per_meter["time"],
            relative_long_per_meter["error"],
            "Relative Longitudinal Position Deviation",
            max_expected_relative_error,
            "Max Relative Positional Error Threshold",
            "Time[s]",
            "Distance[m]",
        )
        y_plot_th = plot_graphs_threshold(
            relative_lat_per_meter["time"],
            relative_lat_per_meter["error"],
            "Relative Lateral Position Deviation",
            max_expected_relative_error,
            "Max Relative Positional Error Threshold",
            "Time[s]",
            "Distance[m]",
        )

        plots.append(x_plot)
        plot_titles.append(" ")
        plots.append(y_plot)
        plot_titles.append(" ")
        plots.append(x_plot_th)
        plot_titles.append(" ")
        plots.append(y_plot_th)
        plot_titles.append(" ")

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


@verifies("ReqId-1386175")
@testcase_definition(
    name="The relative position error shall not exceed 0.2 m per driven meter during 'difficult driving conditions'",
    description="The relative position error shall not exceed 0.2 m per driven meter during difficult "
    "driving conditions",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%"
    "2Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z7qpTaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti."
    "de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configu"
    "ration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoRelativePositionErrorDifficultDrivingConditionsTestCase(TestCase):
    """VedodoRelativeLongitudinalPositionErrorNormalDrivingConditionsTestCase test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoRelativePositionErrorDifficultDrivingConditions,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.

    """
    _, testrun_id, cp = debug(
        VedodoRelativePositionErrorDifficultDrivingConditionsTestCase,
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
