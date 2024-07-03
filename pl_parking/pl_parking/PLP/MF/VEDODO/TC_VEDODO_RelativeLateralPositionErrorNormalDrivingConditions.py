#!/usr/bin/env python3
"""This is the test case to validate the relative Lateral position error during normal driving conditions"""

import logging
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from tsf.core.results import (
    FALSE,
    TRUE,
    BooleanResult,
)
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
from pl_parking.PLP.MF.constants import PlotlyTemplate

from .common import calculate_odo_error, get_relative_positional_error_per_meter
from .constants import CarMakerUrl

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


__author__ = "Anil A, Uie64067"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.0.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

READER_NAME = "VedodoRelativeLateralPositionErrorInNormalDrivingConditions"


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
        }


@teststep_definition(
    step_number=1,
    name="The relative Lateral position error shall not exceed 0.03m per driven meter in normal driving conditions",
    description="The relative Lateral position error shall not exceed 0.03m per driven meter in normal "
    "driving conditions",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoRelativeLateralPositionErrorNormalDrivingConditions(TestStep):
    """Test case for driven distance at normal driving conditions.

    Objective
    ---------

    The relative Lateral position error shall not exceed 0.03m per driven meter during normal driving conditions.

    Detail
    ------

    Check the relative Lateral position error should not exceed 0.03m per driven meter during normal
    driving conditions.
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
        df: pd.DataFrame = self.readers[READER_NAME].signals
        max_expected_lat_relative_error: float = 0.03
        signal_summary = dict()
        test_result_list = list()

        ap_time = list(df[VedodoSignals.Columns.CM_TIME])
        gt_x = list(df[VedodoSignals.Columns.ODO_CM_REF_X])
        gt_y = list(df[VedodoSignals.Columns.ODO_CM_REF_Y])
        x_estimated = list(df[VedodoSignals.Columns.ODO_EST_X])
        y_estimated = list(df[VedodoSignals.Columns.ODO_EST_Y])
        psi_gt = list(df[VedodoSignals.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR])
        psi_estimated = list(df[VedodoSignals.Columns.YAW_ANGLE])

        relative_lat_per_meter_list = get_relative_positional_error_per_meter(gt_y, y_estimated)

        max_lat_error = max(relative_lat_per_meter_list)
        if max_lat_error > max_expected_lat_relative_error:
            evaluation_longi = " ".join(
                f"Evaluation for Lateral position error during normal driving conditions is FAILED and "
                f"the maximum expected error threshold is {max_expected_lat_relative_error}m is above the "
                f"threshold and maximum estimated relative error is {max_lat_error}m".split()
            )
            test_result_list.append(False)
        else:
            evaluation_longi = " ".join(
                f"Evaluation for Lateral position error during normal driving conditions is PASSED and "
                f"the maximum expected error threshold is {max_expected_lat_relative_error}m is within the "
                f"threshold and maximum estimated relative error is {max_lat_error}m".split()
            )
            test_result_list.append(True)

        signal_summary["Lateral Position Error"] = evaluation_longi

        _, _, _, _, relative_lat = calculate_odo_error(gt_x, gt_y, psi_gt, psi_estimated, x_estimated, y_estimated)

        max_relative_lat_error = max(relative_lat)
        if max_relative_lat_error > max_expected_lat_relative_error:
            evaluation_relative_longi = " ".join(
                f"Evaluation for Relative Lateral position error during normal driving conditions is FAILED and "
                f"the maximum expected relative error threshold is {max_expected_lat_relative_error}m is above the "
                f"threshold and maximum estimated relative error is {max_relative_lat_error}m".split()
            )
            test_result_list.append(False)
        else:
            evaluation_relative_longi = " ".join(
                f"Evaluation for Relative Lateral position error during normal driving conditions is PASSED and "
                f"the maximum expected relative error threshold is {max_expected_lat_relative_error}m is within the "
                f"threshold and maximum estimated relative error is {max_relative_lat_error}m".split()
            )
            test_result_list.append(True)

        if all(test_result_list):
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary["Lateral Relative Position Error"] = evaluation_relative_longi

        self.sig_summary = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_summary)
        remarks.append("")

        # Position error of Lateral w.r.to threshold
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=[
                    max_expected_lat_relative_error,
                ]
                * len(ap_time),
                mode="lines",
                name="Lateral position error threshold",
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]", yaxis_title="Distance[m]"
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=relative_lat_per_meter_list,
                mode="lines",
                name="Lateral position per meter",
            )
        )
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        fig.add_annotation(
            dict(
                font=dict(color="black", size=12),
                x=0,
                y=-0.12,
                showarrow=False,
                text="Lateral position Error vs Threshold",
                textangle=0,
                xanchor="left",
                xref="paper",
                yref="paper",
            )
        )
        plot_titles.append(" ")
        plots.append(fig)
        remarks.append("")

        # Relative Position error of Lateral w.r.to threshold
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=[
                    max_expected_lat_relative_error,
                ]
                * len(ap_time),
                mode="lines",
                name="Lateral relative error threshold",
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]", yaxis_title="Distance[m]"
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=relative_lat,
                mode="lines",
                name="Lateral relative error",
            )
        )
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        fig.add_annotation(
            dict(
                font=dict(color="black", size=12),
                x=0,
                y=-0.12,
                showarrow=False,
                text="Lateral relative error vs Threshold",
                textangle=0,
                xanchor="left",
                xref="paper",
                yref="paper",
            )
        )
        plot_titles.append(" ")
        plots.append(fig)
        remarks.append("")

        # Lateral position error of GT vs Estimate
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=gt_y,
                mode="lines",
                name=CarMakerUrl.odoCmRefY,
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]", yaxis_title="Distance[m]"
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=y_estimated,
                mode="lines",
                name=CarMakerUrl.odoEstY,
            )
        )
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        fig.add_annotation(
            dict(
                font=dict(color="black", size=12),
                x=0,
                y=-0.12,
                showarrow=False,
                text="Lateral GT vs Estimate",
                textangle=0,
                xanchor="left",
                xref="paper",
                yref="paper",
            )
        )
        plot_titles.append(" ")
        plots.append(fig)
        remarks.append("")

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
            "Driven Distance": {"value": max_lat_error, "color": get_color(test_result)},
        }
        self.result.details["Additional_results"] = additional_results_dict


@verifies("ReqId-2104439")
@testcase_definition(
    name="Check the lateral position error in normal driving conditions",
    description="The relative Lateral position error shall not exceed 0.03 m per driven meter during normal "
    "driving conditions",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_x7Zm0gDCEe-JmbR7EsJ0UA&componentURI=https%3A%2F%2Fjazz.conti.de%2"
    "Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configuration"
    "=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class VedodoRelativeLateralPositionErrorNormalDrivingConditionsTestCase(TestCase):
    """VedodoRelativeLateralPositionErrorNormalDrivingConditionsTestCase test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoRelativeLateralPositionErrorNormalDrivingConditions,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.

    """
    _, testrun_id, cp = debug(
        VedodoRelativeLateralPositionErrorNormalDrivingConditionsTestCase,
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
