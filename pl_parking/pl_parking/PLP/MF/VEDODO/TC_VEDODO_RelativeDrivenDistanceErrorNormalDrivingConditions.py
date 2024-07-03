#!/usr/bin/env python3
"""This is the test case to validate the driven distance position error in normal driving conditions"""

import logging
import math
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
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

READER_NAME = "VedodoRelativeDrivenDistancePositionErrorInNormalDrivingConditions"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        DRIVEN_DISTANCE = "driven_distance"
        CM_TIME = "cm_time"
        ODO_CM_REF_X = "odoCmRefX"
        ODO_CM_REF_Y = "odoCmRefY"
        ODO_EST_X = "odoEstX"
        ODO_EST_Y = "odoEstY"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.DRIVEN_DISTANCE: CarMakerUrl.drivenDistance_m,
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.ODO_CM_REF_X: CarMakerUrl.odoCmRefX,
            self.Columns.ODO_CM_REF_Y: CarMakerUrl.odoCmRefY,
            self.Columns.ODO_EST_X: CarMakerUrl.odoEstX,
            self.Columns.ODO_EST_Y: CarMakerUrl.odoEstY,
        }


@teststep_definition(
    step_number=1,
    name="The relative driven distance position error shall not exceed 0.6 m per driven meter in"
    " normal driving conditions",
    description="The relative driven distance position error shall not exceed 0.6 m per driven meter in"
    " normal driving conditions",
    expected_result=BooleanResult(TRUE),
    doors_url="https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_RiAxIJNHEe674_0gzoV9FQ?oslc.configuration=https%3A%"
    "2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099#action=com.ibm.rqm.planning.home.actionDispatcher&subAc"
    "tion=viewTestCase&id=38755",
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoRelativeDrivenDistancePositionErrorNormalgDrivingonditions(TestStep):
    """Test case for driven distance at normal driving conditions.

    Objective
    ---------

    The relative driven distance position error shall not exceed 0.6m per driven meter in
     normal driving conditions.

    Detail
    ------

    Check the driven distance relative position error should not exceed 0.6m per driven meter in
     normal driving conditions.
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
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)
        df: pd.DataFrame = self.readers[READER_NAME].signals
        position_error_per_driven_meter: list = list()
        current_driven_distance_vedodo: float = 0.0
        reference_driven_distance: float = 0.0
        max_expected_error: float = 0.06
        signal_summary = dict()
        driven_distance_gt_list = list()
        driven_distance = 0
        prev_x = 0
        prev_y = 0

        ap_time = list(df[VedodoSignals.Columns.CM_TIME])
        driven_distance_est = list(df[VedodoSignals.Columns.DRIVEN_DISTANCE])
        gt_x = list(df[VedodoSignals.Columns.ODO_CM_REF_X])
        gt_y = list(df[VedodoSignals.Columns.ODO_CM_REF_Y])

        # Extracting GT driven distance from GT X and GT Y
        for x, y in zip(gt_x, gt_y):
            disp_x = x - prev_x
            disp_y = y - prev_y
            disp_m = abs(math.sqrt(disp_x * disp_x + disp_y * disp_y))
            driven_distance += disp_m
            driven_distance_gt_list.append(driven_distance % 1000)
            prev_x = x
            prev_y = y

        for d_est, d_gt in zip(driven_distance_est, driven_distance_gt_list):
            if not np.isnan(d_est) and d_gt and d_est:
                current_driven_distance_vedodo += d_est
                reference_driven_distance += d_gt
                if current_driven_distance_vedodo >= 1:  # check for 1 meter chunks
                    diff_dist = abs(reference_driven_distance - current_driven_distance_vedodo)
                    # To avoid peeks
                    if diff_dist > 800:
                        diff_dist -= 1000
                    elif diff_dist < -800:
                        diff_dist += 1000
                    position_error_per_driven_meter.append(diff_dist)
                    current_driven_distance_vedodo = 0
                    reference_driven_distance = 0
            else:
                position_error_per_driven_meter.append(0)

        # check if all 1 meter chunks pass the criteria
        max_estimated_error = max(position_error_per_driven_meter)
        if max_estimated_error <= max_expected_error:
            evaluation = " ".join(
                f"Evaluation for Relative Driven Distance position error during normal driving conditions is PASSED "
                f"and the maximum expected threshold error is {max_expected_error}m for "
                f"every 1m chunk and the maximum estimated error is {max_estimated_error}m ".split()
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            evaluation = " ".join(
                f"Evaluation for Relative Driven Distance position error during normal driving conditions is FAILED "
                f"and the maximum expected threshold error is {max_expected_error}m for "
                f"every 1m chunk and the maximum estimated error is {max_estimated_error}m ".split()
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary["Relative Driven Distance Position Error During Normal Driving Conditions"] = evaluation

        self.sig_summary = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_summary)
        remarks.append("")

        # relative_position_error_normal_driving_conditions
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=[
                    max_expected_error,
                ]
                * len(ap_time),
                mode="lines",
                name="Threshold of Position Error per driven meter",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=position_error_per_driven_meter,
                mode="lines",
                name="Position Error driven per meter",
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
                text="relative_position_error_normal_driving_conditions",
                textangle=0,
                xanchor="left",
                xref="paper",
                yref="paper",
            )
        )
        plot_titles.append(" ")
        plots.append(fig)
        remarks.append("")

        # Driven Distance GT vs Estimate
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=driven_distance_gt_list,
                mode="lines",
                name="Driven Distance GT",
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]", yaxis_title="Distance[m]"
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=driven_distance_est,
                mode="lines",
                name=CarMakerUrl.drivenDistance_m,
            )
        )
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        fig.add_annotation(
            dict(
                font=dict(color="black", size=12),
                x=0,
                y=-0.12,
                showarrow=False,
                text="Driven Distance GT vs Estimate",
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
            "Driven Distance": {"value": max_expected_error, "color": get_color(test_result)},
        }
        self.result.details["Additional_results"] = additional_results_dict


@verifies("ReqId-1386174")
@testcase_definition(
    name="Check the driven distance position error in normal driving conditions",
    description="The driven distance position error shall not exceed 0.06 m per driven meter in normal "
    "driving conditions",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2"
    "Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z7qozaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti.de"
    "%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configurat"
    "ion=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class VedodoRelativeDrivenDistancePositionErrorNormalInConditionsTestCase(TestCase):
    """VedodoRelativeDrivenDistancePositionErrorNormalInConditionsTestCase test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoRelativeDrivenDistancePositionErrorNormalgDrivingonditions,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.

    """
    _, testrun_id, cp = debug(
        VedodoRelativeDrivenDistancePositionErrorNormalInConditionsTestCase,
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
