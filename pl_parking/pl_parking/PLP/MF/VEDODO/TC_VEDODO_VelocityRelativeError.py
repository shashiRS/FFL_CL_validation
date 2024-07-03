#!/usr/bin/env python3
"""This is the test case to calculate the velocity relative error in both longitudinal and lateral positions"""

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
from pl_parking.common_ft_helper import MfCustomTeststepReport, convert_dict_to_pandas, get_color, rep
from pl_parking.PLP.MF.constants import PlotlyTemplate
from pl_parking.PLP.MF.VEDODO.constants import CarMakerUrl

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


__author__ = "Anil A, uie64067"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.0.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

READER_NAME = "VedodoVelocityRelativeError"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        EGO_VELOCITY_GT = "ego_velocity_gt"
        CM_VELOCITY_X = "cm_velocity_x"
        CM_AP_LONGI_VELOCITY = "cm_ap_longi_velocity"
        CM_TIME = "cm_time"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_VELOCITY_X: CarMakerUrl.velocityX,
            self.Columns.CM_AP_LONGI_VELOCITY: CarMakerUrl.longitudinalVelocity_mps,
            self.Columns.CM_TIME: CarMakerUrl.time,
        }


@teststep_definition(
    step_number=1,
    name="Relative velocity error when vehicle driving faster than 0.2 m/s",
    description="When the vehicle speed is faster than 0.2 m/s, the ESC Odometry shall provide the instantaneous "
    "vehicle speed with an relative error less than 1%",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVelocityRelativeError(TestStep):
    """Test case for vehicle velocity.

    Objective
    ---------

    Check the Relative error when vehicle driving faster than 0.2 m/s.

    Detail
    ------

    Check When the vehicle speed is faster than 0.2 m/s, the ESC Odometry shall provide the instantaneous vehicle
    speed with the relative error less than 1%.
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
        df: pd.DataFrame = self.readers[READER_NAME].signals

        ap_time = list(df[VedodoSignals.Columns.CM_TIME])
        cm_ego_velocity = list(df[VedodoSignals.Columns.CM_VELOCITY_X])
        cm_longi_velocity = list(df[VedodoSignals.Columns.CM_AP_LONGI_VELOCITY])

        # Init variables
        max_expected_relative_error: float = 0.01
        vehicle_speed_condition: float = 0.2
        signal_summary = dict()
        relative_error_list = list()

        for sp, lsp in zip(cm_ego_velocity, cm_longi_velocity):
            if sp > vehicle_speed_condition:
                relative_error = abs((lsp - sp) * 100 / sp)
            else:
                relative_error = 0

            relative_error_list.append(relative_error)

        max_relative_error = max(relative_error_list)
        if max_relative_error > max_expected_relative_error:
            evaluation = " ".join(
                f"Evaluation for Relative error when vehicle is faster than {vehicle_speed_condition} mps is FAILED "
                f"with maximum expected error < 1%, but vehicle velocity relative error got "
                f"{round(max_relative_error, 3)}% error".split()
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE
        else:
            evaluation = " ".join(
                f"Evaluation for Relative error when vehicle is faster than {vehicle_speed_condition} mps is PASSED "
                "with maximum expected error < 1% ".split()
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE

        signal_summary["Vehicle_Relative_Velocity_Error"] = evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=[
                    max_expected_relative_error * 100,
                ]
                * len(ap_time),
                mode="lines",
                name="Relative velocity error threshold",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=relative_error_list,
                mode="lines",
                name="velocity relative error",
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]", yaxis_title="Threshold[%]"
        )
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        fig.add_annotation(
            dict(
                font=dict(color="black", size=12),
                x=0,
                y=-0.12,
                showarrow=False,
                text="relative_velocity_error",
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
                y=cm_ego_velocity,
                mode="lines",
                name=CarMakerUrl.velocityX,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=cm_longi_velocity,
                mode="lines",
                name=CarMakerUrl.longitudinalVelocity_mps,
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
                text="Estimated VS GT velocity",
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


@verifies("ReqID_1386184")
@testcase_definition(
    name="Velocity Relative Error test case",
    description="VEDODO TestCase Velocity Relative Error",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_3z7qrzaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti."
    "de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configura"
    "tion=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleVelocityRelativeErrorTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVelocityRelativeError,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleVelocityRelativeErrorTestCase,
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
