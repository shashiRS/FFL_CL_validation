#!/usr/bin/env python3
"""This is the test case to check the TCE provide the Estimated  Tire Circumference for the non-driven axle wheels,
ie In a Typical Front axle non-Driven vehicle rear axle right wheel, front axle left wheel
"""

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
from pl_parking.PLP.MF.TCE.constants import CarMakerUrl, TceConstantValues
from pl_parking.PLP.MF.VEDODO.common import calculate_odo_error
from pl_parking.PLP.MF.VEDODO.constants import CarMakerUrl as vedodoCarMakerUrl

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


__author__ = "Anil A, uie64067"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.0.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

READER_NAME = "TceTyreCircumferenceForNonDrivenRearAxleWheels"


class TceSignals(SignalDefinition):
    """Tce signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TIME"
        estTyreCircRR = "estTyreCircRR"
        estTyreCircRL = "estTyreCircRL"
        ODO_CM_REF_X = "odoCmRefX"
        ODO_CM_REF_Y = "odoCmRefY"
        ODO_EST_X = "odoEstX"
        ODO_EST_Y = "odoEstY"
        positionDOP = "positionDOP"
        ODO_CM_REF_YAWANG_EGO_RA_CUR = "odoCmRefyawAngEgoRaCur"
        YAW_ANGLE = "yawAngle"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.estTyreCircRL: CarMakerUrl.estTyreCircRL,
            self.Columns.estTyreCircRR: CarMakerUrl.estTyreCircRR,
            self.Columns.TIME: CarMakerUrl.time,
            self.Columns.ODO_CM_REF_X: vedodoCarMakerUrl.odoCmRefX,
            self.Columns.ODO_CM_REF_Y: vedodoCarMakerUrl.odoCmRefY,
            self.Columns.ODO_EST_X: vedodoCarMakerUrl.odoEstX,
            self.Columns.ODO_EST_Y: vedodoCarMakerUrl.odoEstY,
            self.Columns.positionDOP: CarMakerUrl.positionDOP,
            self.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR: vedodoCarMakerUrl.odoCmRefyawAngEgoRaCur,
            self.Columns.YAW_ANGLE: vedodoCarMakerUrl.yawAngle,
        }


def check_tyre_circumference_for_non_driven_wheels(gt_tyre, algo_tyre, driven_distance):
    """Evaluating the error rate with ground truth data"""
    distance = 0
    error_rate_list = list()
    for et, d in zip(algo_tyre, driven_distance):
        distance += d
        if distance >= 8000:
            error_rate_list.append(abs(et - gt_tyre))
        else:
            error_rate_list.append(0)
    return error_rate_list


def evaluation_result(result, tyre, threshold, deviation):
    """Evaluate and validate the result to display the results in report"""
    if not result:
        evaluation = (
            f"Evaluation of Tire Circumference for the {tyre} non-driven axle wheel is {deviation}m deviated "
            f"with respect to the ground truth data, and max threshold value {threshold} w.r.to the ,"
            f"ground truth, Hence test results is FAILED."
        )
        test_result = False
    else:
        evaluation = (
            f"Evaluation of Tire Circumference for the {tyre} non-driven axle wheel is within the "
            f"expected threshold from  the ground truth and max threshold value {threshold} w.r.to the ,"
            f"ground truth, Hence test results is FAILED."
        )
        test_result = True
    return test_result, evaluation


@teststep_definition(
    step_number=1,
    name="The TCE shall provide the Tire Circumference for the non-driven axle wheels.",
    description="The TCE provide the Estimated  Tire Circumference for the non-driven axle wheels, "
    "ie In a Typical Rear axle non-Driven vehicle Rear axle right wheel, Rear axle left wheel.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, TceSignals)
class TceTyreCircumferenceForNonDrivenAxleWheels(TestStep):
    """Test case for TCE Tire Circumference for the non-driven axle wheels.

    Objective
    ---------

    The TCE shall provide the Tire Circumference for the non-driven axle wheels.

    Detail
    ------

    The TCE shall provide the Tire Circumference for the non-driven axle wheels.
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
        ap_time = list(df[TceSignals.Columns.TIME])
        est_tire_fr = list(df[TceSignals.Columns.estTyreCircRR])
        est_tire_fl = list(df[TceSignals.Columns.estTyreCircRL])
        gt_tire_rear = TceConstantValues.TCE_TYRE_CIRCUMFERENCE_RE_M
        position_dop = list(df[TceSignals.Columns.positionDOP])
        gt_x = list(df[TceSignals.Columns.ODO_CM_REF_X])
        gt_y = list(df[TceSignals.Columns.ODO_CM_REF_Y])
        x_estimated = list(df[TceSignals.Columns.ODO_EST_X])
        y_estimated = list(df[TceSignals.Columns.ODO_EST_Y])
        psi_gt = list(df[TceSignals.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR])
        psi_estimated = list(df[TceSignals.Columns.YAW_ANGLE])

        # Init variables
        signal_summary = dict()
        expected_threshold = "0.5%"
        max_deviation_threshold = 0.005 * gt_tire_rear
        max_gps_precision_error = 2.5

        _, _, driven_distance, _, _ = calculate_odo_error(gt_x, gt_y, psi_gt, psi_estimated, x_estimated, y_estimated)
        fl_tyre_error_list = check_tyre_circumference_for_non_driven_wheels(gt_tire_rear, est_tire_fl, driven_distance)
        fl_max_deviation = max(fl_tyre_error_list)
        max_position_dop = max(position_dop)
        if fl_max_deviation <= max_deviation_threshold and max_position_dop <= max_gps_precision_error:
            fl_result = True
        else:
            fl_result = False
        fl_test_result, fl_evaluation = evaluation_result(fl_result, "rear left", expected_threshold, fl_max_deviation)

        fr_tyre_error_list = check_tyre_circumference_for_non_driven_wheels(gt_tire_rear, est_tire_fr, driven_distance)
        fr_max_deviation = max(fr_tyre_error_list)
        if fr_max_deviation <= max_deviation_threshold and max_position_dop <= max_gps_precision_error:
            fr_result = True
        else:
            fr_result = False
        fr_test_result, fr_evaluation = evaluation_result(fr_result, "rear right", expected_threshold, fr_max_deviation)

        if fl_test_result and fr_test_result:
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[f"{CarMakerUrl.estTyreCircRR}"] = fr_evaluation
        signal_summary[f"{CarMakerUrl.estTyreCircRL}"] = fl_evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=est_tire_fl,
                mode="lines",
                name=CarMakerUrl.estTyreCircRL,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=[
                    gt_tire_rear,
                ]
                * len(ap_time),
                mode="lines",
                name="Ground Truth Rear Left Tyre Circumference",
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
                text="Estimated VS GT Rear Left Tyre Circumference",
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
                y=est_tire_fr,
                mode="lines",
                name=CarMakerUrl.estTyreCircRR,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=[
                    gt_tire_rear,
                ]
                * len(ap_time),
                mode="lines",
                name="Ground Truth Rear Right Tyre Circumference",
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
                text="Estimated VS GT Rear Right Tyre Circumference",
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
                y=[
                    max_deviation_threshold,
                ]
                * len(ap_time),
                mode="lines",
                name="Max Expected deviation threshold",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=fl_tyre_error_list,
                mode="lines",
                name="Rear left tyre error",
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
                text="Rear left tyre circumference error VS Threshold",
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
                y=[
                    max_deviation_threshold,
                ]
                * len(ap_time),
                mode="lines",
                name="Max Expected deviation threshold",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=fr_tyre_error_list,
                mode="lines",
                name="Rear right tyre error",
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
                text="Rear right tyre circumference error VS Threshold",
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
                y=[
                    max_gps_precision_error,
                ]
                * len(ap_time),
                mode="lines",
                name="Max Expected Position GPS threshold",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=position_dop,
                mode="lines",
                name="GPS Port Position DOP",
            )
        )
        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]", yaxis_title="GPS"
        )
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        fig.add_annotation(
            dict(
                font=dict(color="black", size=12),
                x=0,
                y=-0.12,
                showarrow=False,
                text="GPS Port Position DOP VS Threshold",
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
            fc.REQ_ID: ["1675922"],
            fc.TESTCASE_ID: ["41446"],
            fc.TEST_RESULT: [test_result],
        }
        self.result.details["Additional_results"] = additional_results_dict


@verifies("ReqID_1675922")
@testcase_definition(
    name="TCE Tire Circumference for the non-driven axle wheels.",
    description="TCE Tire Circumference for the non-driven axle wheels.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fj"
    "azz.conti.de%2Frm4%2Fresources%2FBI_yDU1n3pAEe6n7Ow9oWyCxw&oslc_config.context=https%3A%2F%2Fjazz.conti"
    ".de%2Fgc%2Fconfiguration%2F17099&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28"
    "PvtEeqIqKySVwTVNQ%2Fcomponents%2F__9Yt9nfVEe6n7Ow9oWyCxw",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TceTyreCircumferenceForNonDrivenAxleWheelsTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TceTyreCircumferenceForNonDrivenAxleWheels,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        TceTyreCircumferenceForNonDrivenAxleWheelsTestCase,
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
