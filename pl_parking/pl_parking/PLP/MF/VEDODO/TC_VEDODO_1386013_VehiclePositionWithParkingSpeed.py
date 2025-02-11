#!/usr/bin/env python3
"""This is the test case to continuously monitor the X and Y position during parking speed condition"""

import logging
import math
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
from pl_parking.common_ft_helper import MfCustomTeststepReport, convert_dict_to_pandas, get_color, rep
from pl_parking.PLP.MF.constants import PlotlyTemplate
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

READER_NAME = "VedodoVehiclePositionDuringParkingSpeed"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        CM_VELOCITY_X = "cm_velocity_x"
        time = "time"
        odoEstX = "odoEstX"
        odoEstY = "odoEstY"
        odoCmRefX = "odoCmRefX"
        odoCmRefY = "odoCmRefY"
        estVelocityX = "estVelocityX"
        estVelocityY = "estVelocityY"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_VELOCITY_X: CarMakerUrl.velocityX,
            self.Columns.time: CarMakerUrl.time,
            self.Columns.odoCmRefX: CarMakerUrl.odoCmRefX,
            self.Columns.odoCmRefY: CarMakerUrl.odoCmRefY,
            self.Columns.odoEstX: CarMakerUrl.odoEstX,
            self.Columns.odoEstY: CarMakerUrl.odoEstY,
            self.Columns.estVelocityX: CarMakerUrl.estVelocityX,
            self.Columns.estVelocityY: CarMakerUrl.estVelocityY,
        }


@teststep_definition(
    step_number=1,
    name="Test step to monitor position (x,y) signals continuously during parking speed",
    description="Test step to monitor position (x,y) signals continuously during parking speed and there should not be"
    " any jumps w.r.t previous data",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoMonitorVehiclePositionInParkingSpeed(TestStep):
    """Test case to monitor position (x,y) signals continuously during parking speed.

    Objective
    ---------

    Monitor position (x,y) signals continuously during parking speed.

    Detail
    ------

    Check and monitor position (x,y) signals continuously during parking speed.
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

        time = list(df[VedodoSignals.Columns.time])
        cm_ego_velocity = list(df[VedodoSignals.Columns.CM_VELOCITY_X])
        est_velocity_x = list(df[VedodoSignals.Columns.estVelocityX])
        est_velocity_y = list(df[VedodoSignals.Columns.estVelocityY])
        est_x = list(df[VedodoSignals.Columns.odoEstX])
        est_y = list(df[VedodoSignals.Columns.odoEstY])
        ref_x = list(df[VedodoSignals.Columns.odoCmRefX])
        ref_y = list(df[VedodoSignals.Columns.odoCmRefY])

        flag = True
        pre_x = 0
        pre_y = 0
        sum_x = 0
        sum_y = 0
        x_distance_list = list()
        y_distance_list = list()
        signal_summary = dict()

        for vx, vy, ex, t in zip(est_velocity_x, est_velocity_y, est_x, time):
            if t % 10 == 0:
                if vx > 10 and vy > 10:
                    # Vehicle speed should not be more than 10 mps
                    flag = False
                    break
                elif abs(sum_x - pre_x) > 100 or abs(sum_y - pre_y) > 100:
                    # The driven distance should not be more than 100m
                    # because here validating distance for every 10s time interval
                    flag = False
                    break
                else:
                    pre_x = sum_x
                    x_distance_list.append(sum_x)
                    sum_x = abs(ex)
                    y_distance_list.append(sum_y)
                    pre_y = sum_y
                    sum_y = math.sqrt(abs(((abs(vy) * t) ** 2) - (abs(ex) ** 2)))
                    y_distance_list.append(sum_y)
            else:
                sum_x += abs(ex)
                # calculating distance Y using Pythagorean theorem
                y_distance = math.sqrt(abs(((abs(vy) * t) ** 2) - (abs(ex) ** 2)))
                sum_y += y_distance

        if flag:
            evaluation = (
                "Evaluation for Vehicle position (x,y) with parking speed is PASSED and no huge jumps w.r.t "
                "previous position"
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            inx = x_distance_list.index(max(x_distance_list))
            iny = y_distance_list.index(max(y_distance_list))
            evaluation = (
                f"Evaluation for Vehicle position (x,y) with parking speed is FAILED and there are huge jumps"
                f"are noticed w.r.t previous position, "
                f"peek jump distance-x:{round(x_distance_list[inx] - x_distance_list[inx - 1], 3)} and "
                f"peek jump distance-y:{round(y_distance_list[iny] - y_distance_list[iny - 1], 3)}"
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary["VehiclePositionWithParkingSpeed"] = evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=time,
                y=est_x,
                mode="lines",
                name=CarMakerUrl.odoEstX,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=time,
                y=ref_x,
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
                text="Estimated VS GT Position-X",
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
                x=time,
                y=est_y,
                mode="lines",
                name=CarMakerUrl.odoEstY,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=time,
                y=ref_y,
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
                text="Estimated VS GT Position-Y",
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
                x=time,
                y=y_distance_list,
                mode="lines",
                name="Y Distance",
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
                text="Y Distance using Pythagorean theorem",
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
                x=time,
                y=est_velocity_x,
                mode="lines",
                name=CarMakerUrl.estVelocityX,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=time,
                y=cm_ego_velocity,
                mode="lines",
                name=CarMakerUrl.velocityX,
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]", yaxis_title="Velocity[mps]"
        )
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        fig.add_annotation(
            dict(
                font=dict(color="black", size=12),
                x=0,
                y=-0.12,
                showarrow=False,
                text="Estimated VS GT Velocity-X",
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
        }
        self.result.details["Additional_results"] = additional_results_dict


@verifies("ReqID_1386013")
@testcase_definition(
    name="Monitor position (x,y) signals continuously during parking speed",
    description="Test step to monitor position (x,y) signals continuously during parking speed and there should not be"
    " any jumps w.r.t previous data",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fja"
    "zz.conti.de%2Frm4%2Fresources%2FBI_3z4nUzaaEe6mrdm2_agUYg&oslc_config.context=https%3A%2F%2Fjazz.conti.d"
    "e%2Fgc%2Fconfiguration%2F17099&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtE"
    "eqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoMonitorVehiclePositionInParkingSpeedTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoMonitorVehiclePositionInParkingSpeed,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoMonitorVehiclePositionInParkingSpeedTestCase,
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
