#!/usr/bin/env python3
"""Calculating the Absolute error for position of longitudinal and lateral w.r.to GT"""

import logging
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
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
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTeststepReport, rep
from pl_parking.PLP.MF.constants import PlotlyTemplate
from pl_parking.PLP.MF.VEDODO.constants import CarMakerUrl

from .common import calculate_odo_error

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


__author__ = "Anil A, uie64067"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.0.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

READER_NAME = "VedodoAbsoluateError"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        DRIVEN_DISTANCE = "driven_distance"
        YAWRATE_ESTIMATION = "yawrate_estimation"
        YAWRATE_GT = "yawrate_gt"
        CM_TIME = "cm_time"
        ODO_EST_X = "odoEstX"
        ODO_EST_Y = "odoEstY"
        ODO_CM_REF_X = "odoCmRefX"
        ODO_CM_REF_Y = "odoCmRefY"
        ODO_CM_REF_YAWANG_EGO_RA_CUR = "odoCmRefyawAngEgoRaCur"
        YAW_ANGLE = "yawAngle"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.YAWRATE_ESTIMATION: CarMakerUrl.yawrate_estimation,
            self.Columns.YAWRATE_GT: CarMakerUrl.yawrate_gt,
            self.Columns.ODO_CM_REF_X: CarMakerUrl.odoCmRefX,
            self.Columns.ODO_CM_REF_Y: CarMakerUrl.odoCmRefY,
            self.Columns.ODO_EST_X: CarMakerUrl.odoEstX,
            self.Columns.ODO_EST_Y: CarMakerUrl.odoEstY,
            self.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR: CarMakerUrl.odoCmRefyawAngEgoRaCur,
            self.Columns.YAW_ANGLE: CarMakerUrl.yawAngle,
        }


@teststep_definition(
    step_number=1,
    name="Verify the longitudinal deviate error w.r.to GT position",
    description="Verify the longitudinal deviation error w.r.to GT and the deviate threshold should not more than 0.2m",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoLongitudinalPosition(TestStep):
    """Test case for position of longitudinal w.r.to GT

    Objective
    ---------

    The position of longitudinal w.r.to GT position should not deviate more than the 0.2m threshold value.

    Detail
    ------

    The position of longitudinal w.r.to GT position should not deviate more than the 0.2m threshold value
    """

    custom_report = MfCustomTeststepReport

    def __init__(self):
        super().__init__()

    def process(self, **kwargs):
        """Evaluating test case"""
        _log.debug("Starting processing...")
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)
        df: pd.DataFrame = self.readers[READER_NAME].signals

        ap_time = list(df[VedodoSignals.Columns.CM_TIME])
        x_gt = list(df[VedodoSignals.Columns.ODO_CM_REF_X])
        x_estimated = list(df[VedodoSignals.Columns.ODO_EST_X])

        y_gt = list(df[VedodoSignals.Columns.ODO_CM_REF_Y])
        y_estimated = list(df[VedodoSignals.Columns.ODO_EST_Y])

        psi_gt = list(df[VedodoSignals.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR])
        psi_estimated = list(df[VedodoSignals.Columns.YAW_ANGLE])
        # Init variables
        max_expected_threshold_x: float = 0.2
        signal_summary = dict()

        x_deviate_list, _, _, _, _ = calculate_odo_error(x_gt, y_gt, psi_gt, psi_estimated, x_estimated, y_estimated)
        max_x_deviate = max(x_deviate_list)

        if max_expected_threshold_x > max_x_deviate:
            evaluation = " ".join(
                f"Evaluation of estimated longitudinal position is PASSED and within the expected deviate threshold "
                f"{max_expected_threshold_x}m from the GT longitudinal position".split()
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            evaluation = " ".join(
                f"Evaluation of estimated longitudinal position is FAILED and the expected deviate threshold "
                f"{max_expected_threshold_x}m is more than GT longitudinal position and {round(max_x_deviate, 3)}m"
                f" more from the given threshold".split()
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary["Longitudinal position"] = evaluation

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=[
                    max_expected_threshold_x,
                ]
                * len(ap_time),
                mode="lines",
                name="Longitudinal Error threshold",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=x_deviate_list,
                mode="lines",
                name="Longitudinal Deviation",
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]", yaxis_title="Distance[m]"
        )
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        fig.add_annotation(
            dict(
                font=dict(color="black", size=12),
                x=0,
                y=-0.12,
                showarrow=False,
                text="Longitudinal Deviation",
                textangle=0,
                xanchor="left",
                xref="paper",
                yref="paper",
            )
        )
        plot_titles.append(" ")
        plots.append(fig)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=x_estimated,
                mode="lines",
                name=CarMakerUrl.odoEstX,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=x_gt,
                mode="lines",
                name=CarMakerUrl.odoCmRefX,
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]", yaxis_title="Distance[m]"
        )
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        fig.add_annotation(
            dict(
                font=dict(color="black", size=12),
                x=0,
                y=-0.12,
                showarrow=False,
                text="Longitudinal Estimated VS GT",
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
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
        }
        self.result.details["Additional_results"] = additional_results_dict


@teststep_definition(
    step_number=2,
    name="Verify the lateral deviate error w.r.to GT position",
    description="Verify the lateral deviation error w.r.to GT and the deviate threshold should not more than 0.2m",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoLateralPosition(TestStep):
    """Test case for position of lateral w.r.to GT

    Objective
    ---------

    The position of lateral w.r.to GT position should not deviate more than the 0.2m threshold value.

    Detail
    ------

    The position of lateral w.r.to GT position should not deviate more than the 0.2m threshold value
    """

    custom_report = MfCustomTeststepReport

    def __init__(self):
        super().__init__()

    def process(self, **kwargs):
        """Evaluating test case"""
        _log.debug("Starting processing...")
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)
        df: pd.DataFrame = self.readers[READER_NAME].signals

        ap_time = list(df[VedodoSignals.Columns.CM_TIME])
        x_gt = list(df[VedodoSignals.Columns.ODO_CM_REF_X])
        x_estimated = list(df[VedodoSignals.Columns.ODO_EST_X])

        y_gt = list(df[VedodoSignals.Columns.ODO_CM_REF_Y])
        y_estimated = list(df[VedodoSignals.Columns.ODO_EST_Y])

        psi_gt = list(df[VedodoSignals.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR])
        psi_estimated = list(df[VedodoSignals.Columns.YAW_ANGLE])

        # Init variables
        max_expected_threshold_y: float = 0.2
        signal_summary = dict()

        _, y_deviate_list, _, _, _ = calculate_odo_error(x_gt, y_gt, psi_gt, psi_estimated, x_estimated, y_estimated)
        max_y_deviate = max(y_deviate_list)

        if max_expected_threshold_y > max_y_deviate:
            evaluation = " ".join(
                f"Evaluation of estimated lateral position is PASSED and within the expected deviate threshold "
                f"{max_expected_threshold_y}m is from the GT lateral position ".split()
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            evaluation = " ".join(
                f"Evaluation of estimated lateral position is FAILED and the expected deviate threshold "
                f"{max_expected_threshold_y}m is more from the GT lateral position and maximum deviate threshold"
                f"value is {round(max_y_deviate, 3)}m".split()
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary["Lateral position"] = evaluation
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=[
                    max_expected_threshold_y,
                ]
                * len(ap_time),
                mode="lines",
                name="Lateral Error threshold",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=y_deviate_list,
                mode="lines",
                name="Lateral Deviation",
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]", yaxis_title="Distance[m]"
        )
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        fig.add_annotation(
            dict(
                font=dict(color="black", size=12),
                x=0,
                y=-0.12,
                showarrow=False,
                text="Lateral Deviation",
                textangle=0,
                xanchor="left",
                xref="paper",
                yref="paper",
            )
        )
        plot_titles.append(" ")
        plots.append(fig)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=y_estimated,
                mode="lines",
                name=CarMakerUrl.odoEstY,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=y_gt,
                mode="lines",
                name=CarMakerUrl.odoCmRefY,
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]", yaxis_title="Distance[m]"
        )
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        fig.add_annotation(
            dict(
                font=dict(color="black", size=12),
                x=0,
                y=-0.12,
                showarrow=False,
                text="Lateral Estimated VS GT",
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
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
        }
        self.result.details["Additional_results"] = additional_results_dict


@verifies("ReqID_1386165")
@testcase_definition(
    name="Absolute Error test case",
    description="VEDODO TestCase Absolute Error",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_3z8RpzaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti.de%2"
    "Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configuration="
    "https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/Playground_2/TSF-Debug")
class VedodoAbsoluteTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoLongitudinalPosition,
            VedodoLateralPosition,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoAbsoluteTestCase,
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
