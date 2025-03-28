#!/usr/bin/env python3
"""The estimated yaw rate shall consider possible changes in orientation during steering while the car being
stationary
"""

import logging
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
from tsf.io.signals import SignalDefinition

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

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

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTeststepReport, convert_dict_to_pandas, rep
from pl_parking.PLP.MF.constants import PlotlyTemplate

from .constants import CarMakerUrl

__author__ = "Anil A, uie64067"
__copyright__ = "2012-2024, Continental AG"
__version__ = "0.0.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

READER_NAME = "VedodoYawRateAtStationary"


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
        motionStatus = "motionStatus"

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
            self.Columns.motionStatus: CarMakerUrl.motionStatus,
        }


@teststep_definition(
    step_number=1,
    name="The estimated yaw rate shall consider possible changes in orientation during steering while the car "
    "being stationary",
    description="The estimated yaw rate shall consider possible changes in orientation during steering while the car "
    "being stationary",
    expected_result=BooleanResult(TRUE),
    doors_url="https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_RiAxIJNHEe674_0gzoV9FQ?oslc.configuration=https%3A%2"
    "F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099#action=com.ibm.rqm.planning.home.actionDispatcher&subActi"
    "on=viewTestCase&id=38987",
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoYawRateAtStationary(TestStep):
    """The estimated yaw rate shall consider possible changes in orientation during steering while the
    car being stationary.

    Objective
    ---------

    The estimated yaw rate shall consider possible changes in orientation during steering while the car being
    stationary.

    Detail
    ------

    The estimated yaw rate shall consider possible changes in orientation during steering while the car being
    stationary
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
        df: pd.DataFrame = self.readers[READER_NAME]

        ap_time = list(df[VedodoSignals.Columns.CM_TIME])
        yaw_rate_gt = list(df[VedodoSignals.Columns.YAWRATE_GT])
        yaw_rate_estimated = list(df[VedodoSignals.Columns.YAWRATE_ESTIMATION])
        motion_status = list(df[VedodoSignals.Columns.motionStatus])

        # Init variables
        max_expected_deviate_yaw_rate: float = 0
        yaw_rate_deviate_list = list()
        signal_summary = dict()

        for ygt, yst, m in zip(yaw_rate_gt, yaw_rate_estimated, motion_status):
            if not m:
                yaw_error = abs(abs(ygt) - abs(yst))
            else:
                yaw_error = 0
            yaw_rate_deviate_list.append(yaw_error)

        max_yawrate_deviate = max(yaw_rate_deviate_list)
        if max_yawrate_deviate < max_expected_deviate_yaw_rate:
            evaluation = " ".join(
                f"Evaluation of estimated yaw rate, the deviation value w.r.t ground truth is "
                f"{round(max_yawrate_deviate, 3)}rad/s and the expected threshold is {max_expected_deviate_yaw_rate} "
                f"rad/s, the deviation value is below the threshold. Hence the result is PASSED.".split()
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            evaluation = " ".join(
                f"Evaluation of estimated yaw rate, the deviation value w.r.t ground truth is "
                f"{round(max_yawrate_deviate, 3)}rad/s and the expected threshold is {max_expected_deviate_yaw_rate} "
                f"rad/s, the deviation value is above the threshold. Hence the result is FAILED.".split()
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[f"{CarMakerUrl.yawrate_estimation} vs {CarMakerUrl.yawrate_gt}"] = evaluation

        self.sig_summary = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_summary)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=[
                    max_expected_deviate_yaw_rate,
                ]
                * len(ap_time),
                mode="lines",
                name="YawRate threshold",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=yaw_rate_deviate_list,
                mode="lines",
                name="YawRate Deviate",
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"),
            xaxis=dict(tickformat="14"),
            xaxis_title="Time[s]",
            yaxis_title="YawRate deviate[rad/p]",
        )
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        fig.add_annotation(
            dict(
                font=dict(color="black", size=12),
                x=0,
                y=-0.12,
                showarrow=False,
                text="YawRate Deviation",
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
                y=yaw_rate_estimated,
                mode="lines",
                name=CarMakerUrl.yawrate_estimation,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=yaw_rate_gt,
                mode="lines",
                name=CarMakerUrl.yawrate_gt,
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"),
            xaxis=dict(tickformat="14"),
            xaxis_title="Time[s]",
            yaxis_title="YawRate[rad/s]",
        )
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        fig.add_annotation(
            dict(
                font=dict(color="black", size=12),
                x=0,
                y=-0.12,
                showarrow=False,
                text="Estimated VS GT YawRate",
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


@verifies("ReqID_2106504")
@testcase_definition(
    name="The estimated yaw rate shall consider possible changes in orientation during steering while the car "
    "being stationary",
    description="The estimated yaw rate shall consider possible changes in orientation during steering while the car "
    "being stationary",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F"
    "%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_H4940QFcEe-JmbR7EsJ0UA&componentURI=https%3A%2F%2Fjazz.cont"
    "i.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.conf"
    "iguration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoYawRateAtStationaryTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoYawRateAtStationary,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoYawRateAtStationaryTestCase,
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

    main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)
