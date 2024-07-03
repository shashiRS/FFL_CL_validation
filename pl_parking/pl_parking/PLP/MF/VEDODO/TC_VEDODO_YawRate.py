#!/usr/bin/env python3
"""
This the test case checking the deviate Yaw Rate with given threshold value
Calculating the deviate YawRate Limit with given time or frequency
"""

import logging
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
from tsf.io.signals import SignalDefinition

from pl_parking.PLP.MF.VEDODO.constants import CarMakerUrl

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
from pl_parking.common_ft_helper import MfCustomTeststepReport, rep
from pl_parking.PLP.MF.constants import PlotlyTemplate

__author__ = "Anil A, uie64067"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.0.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

READER_NAME = "VedodoYawRate"


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
        }


@teststep_definition(
    step_number=1,
    name="The Yaw rate should not deviate from the actual yaw rate by more than 0.0035 rad/s",
    description="The estimated yaw rate should not deviate from the actual yaw rate by more than "
    "0.0035 rad/s (0.2 deg/s)",
    expected_result=BooleanResult(TRUE),
    doors_url="https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_RiAxIJNHEe674_0gzoV9FQ?oslc.configuration=https%3A%2"
    "F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099#action=com.ibm.rqm.planning.home.actionDispatcher&subActi"
    "on=viewTestCase&id=38987",
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoYawRateThreshold(TestStep):
    """Test case for Vedodo YawRate Threshold.

    Objective
    ---------

    The Yaw rate should not deviate from the actual yaw rate by more than 0.0035 rad/s.

    Detail
    ------

    The estimated yaw rate should not deviate from the actual yaw rate by more than 0.0035 rad/s (0.2 deg/s)
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
        yawRate_gt = list(df[VedodoSignals.Columns.YAWRATE_GT])
        yawRate_estimated = list(df[VedodoSignals.Columns.YAWRATE_ESTIMATION])

        # Init variables
        max_expected_deviate_yawrate: float = 0.0035
        yarate_deviate_list = list()
        signal_summary = dict()

        for ygt, yst in zip(yawRate_gt, yawRate_estimated):
            yarate_deviate_list.append(abs(ygt - yst))

        max_yawrate_deviate = max(yarate_deviate_list)
        if max_yawrate_deviate < max_expected_deviate_yawrate:
            evaluation = " ".join(
                f"Evaluation of estimated yaw rate is PASSED and within the expected deviate threshould "
                f"{max_expected_deviate_yawrate} rad/s (0.2 deg/s) from the actual yaw rate".split()
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            evaluation = " ".join(
                f"Evaluation of estimated yaw rate is FAILED and the expected deviate threshould "
                f"{max_expected_deviate_yawrate} rad/s (0.2 deg/s) is more from the actual yaw rate, "
                f"max deviate value is {max_yawrate_deviate} rad/s".split()
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary["Yaw Rate Deviate"] = evaluation

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=[
                    max_expected_deviate_yawrate,
                ]
                * len(ap_time),
                mode="lines",
                name="YawRate threshold",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=yarate_deviate_list,
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
                y=yawRate_estimated,
                mode="lines",
                name=CarMakerUrl.yawrate_estimation,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=yawRate_gt,
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


@teststep_definition(
    step_number=2,
    name="The Yaw rate should not deviate from the actual yaw rate by more than 0.007 rad/s for less than 350 ms",
    description="The estimated yaw rate might deviate from actual yaw rate by more than 0.007 rad/s (0.4 deg/s) for"
    " less than 350 ms",
    expected_result=BooleanResult(TRUE),
    doors_url="https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_RiAxIJNHEe674_0gzoV9FQ?oslc.configuration=https%3A%2"
    "F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099#action=com.ibm.rqm.planning.home.actionDispatcher&subActi"
    "on=viewTestCase&id=38988",
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoYawRateLimit(TestStep):
    """Test case for Vedodo YawRate Limit.

    Objective
    ---------

    The Yaw rate should not deviate from the actual yaw rate by more than 0.007 rad/s for less than 350 ms.

    Detail
    ------

    The estimated yaw rate might deviate from actual yaw rate by more than 0.007 rad/s (0.4 deg/s) for less than 350 ms
    """

    custom_report = MfCustomTeststepReport

    def __init__(self):
        super().__init__()

    def process(self, **kwargs):
        """Evaluating test case"""
        _log.debug("Starting processing... for VedodoYawRateLimit")
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)
        df: pd.DataFrame = self.readers[READER_NAME].signals

        ap_time = list(df[VedodoSignals.Columns.CM_TIME])
        yawRate_gt = list(df[VedodoSignals.Columns.YAWRATE_GT])
        yawRate_estimated = list(df[VedodoSignals.Columns.YAWRATE_ESTIMATION])

        # Init variables
        max_expected_deviate_yawrate_limit: float = 0.007
        limit_time = 350 / 1000
        yawrate_deviate_list = list()
        signal_summary = dict()
        t_limit = 1

        for ygt, yst, t in zip(yawRate_gt, yawRate_estimated, ap_time):
            if t < limit_time:
                t_limit += 1
            yawrate_deviate = abs(ygt - yst)
            yawrate_deviate_list.append(yawrate_deviate)

        max_yawrate_deviate = max(yawrate_deviate_list[:t_limit])
        if max_yawrate_deviate < max_expected_deviate_yawrate_limit:
            evaluation = " ".join(
                f"Evaluation of estimated yaw rate is PASSED and within the expected deviate threshold "
                f"{max_expected_deviate_yawrate_limit} rad/s from the actual yaw rate within 350ms".split()
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            evaluation = " ".join(
                f"Evaluation of estimated yaw rate is FAILED and the expected deviate threshold "
                f"{max_expected_deviate_yawrate_limit} rad/s is more from the actual yaw rate, "
                f"the max deviate value is {max_yawrate_deviate} rad/s within 350ms".split()
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary["Yaw Rate Deviate Limit"] = evaluation

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=[
                    max_expected_deviate_yawrate_limit,
                ]
                * len(yawrate_deviate_list),
                mode="lines",
                name="YawRateLimit Error threshold",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=yawrate_deviate_list,
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
                y=yawRate_estimated,
                mode="lines",
                name=CarMakerUrl.yawrate_estimation,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=yawRate_gt,
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


@verifies("ReqID_1386193")
@testcase_definition(
    name="YawRate test case",
    description="VEDODO TestCase YawRate",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_3z8RpzaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti.de%2"
    "Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configuration="
    "https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class VedodoYawRateTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoYawRateThreshold,
            VedodoYawRateLimit,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoYawRateTestCase,
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
