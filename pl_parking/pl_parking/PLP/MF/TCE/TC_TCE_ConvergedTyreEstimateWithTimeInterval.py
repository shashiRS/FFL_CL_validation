#!/usr/bin/env python3
"""This is the test case of Tyre Circumference Estimation module shall consider only the converged Tyre Circumference
Estimations. ie, Convergence means that it considers the stable estimations for which the noise variance is equal or
closer to epsilon value, Otherwise that the estimation value will be equal to the ground truth Tire Circumference value
 or closer within the +/- acceptable thresholds when the estimations are averaged for a specific
intervals (eg: 3 sec)
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

READER_NAME = "TceConvergedTyeEstimationWithTimeInterval"


class TceSignals(SignalDefinition):
    """Tce signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TIME"
        estTyreCircFR = "estTyreCircFR"
        estTyreCircFL = "estTyreCircFL"
        estTyreCircRR = "estTyreCircRR"
        estTyreCircRL = "estTyreCircRL"
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
            self.Columns.estTyreCircFL: CarMakerUrl.estTyreCircFL,
            self.Columns.estTyreCircFR: CarMakerUrl.estTyreCircFR,
            self.Columns.estTyreCircRL: CarMakerUrl.estTyreCircRL,
            self.Columns.estTyreCircRR: CarMakerUrl.estTyreCircRR,
            self.Columns.TIME: CarMakerUrl.time,
            self.Columns.ODO_CM_REF_X: vedodoCarMakerUrl.odoCmRefX,
            self.Columns.ODO_CM_REF_Y: vedodoCarMakerUrl.odoCmRefY,
            self.Columns.ODO_EST_X: vedodoCarMakerUrl.odoEstX,
            self.Columns.ODO_EST_Y: vedodoCarMakerUrl.odoEstY,
            self.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR: vedodoCarMakerUrl.odoCmRefyawAngEgoRaCur,
            self.Columns.YAW_ANGLE: vedodoCarMakerUrl.yawAngle,
        }


def check_tyre_circumference_for_driven_wheels(gt_tyre, algo_tyre, time_interval, time, threshold):
    """Evaluating the error rate with ground truth data with given time interval"""
    error_rate_list = list()
    counter = 0
    error_rate = 0
    converge_point = None
    for et in range(len(algo_tyre)):
        if algo_tyre[et] - threshold <= gt_tyre <= algo_tyre[et] + threshold:
            converge_point = et
            break
    if converge_point:
        for et, t in zip(algo_tyre[converge_point:], time[converge_point:]):
            if t % time_interval == 0:
                avg_error = error_rate / counter
                error_rate_list.append(abs(avg_error - gt_tyre))
                error_rate = et
                counter = 1
            else:
                counter += 1
                error_rate += et
                error_rate_list.append(0)

    return error_rate_list, converge_point


def evaluation_result(result, tyre, threshold, deviation, converged, time_sample):
    """Evaluate and validate the result to display the results in report"""
    if converged:
        if not result:
            evaluation = (
                f"Evaluation of Tire Circumference for the {tyre} axle wheel is {deviation}m deviated "
                f"with respect to the ground truth data in given sample interval time {time_sample}s, and max"
                f" threshold value is {threshold}, Hence test results is FAILED."
            )
            test_result = False
        else:
            evaluation = (
                f"Evaluation of Tire Circumference for the {tyre} axle wheel is within the "
                f"expected threshold {threshold} from the ground truth data with sample interval "
                f"time of {time_sample}s, Hence test results is PASSED."
            )
            test_result = True
    else:
        evaluation = (
            f"Evaluation of Tire Circumference for the {tyre} non-driven axle wheel is not converged"
            f"with respect to the ground truth data, Hence test results is FAILED."
        )
        test_result = False

    return test_result, evaluation


def get_test_result(expected_threshold, converged, tyre_error_list, max_deviation_threshold, sample_time, tyre):
    """This is the method to get the evaluation string and test results"""
    if not len(tyre_error_list):
        result = False
        max_deviation = None
        converged = False
    else:
        max_deviation = max(tyre_error_list)
        if max_deviation <= max_deviation_threshold and converged:
            result = True
        else:
            result = False
    test_result, evaluation = evaluation_result(result, tyre, expected_threshold, max_deviation, converged, sample_time)
    return evaluation, test_result


def plot_est_vs_ref_grapgs(ap_time, est_tire, fig, gt_tire, est_signal_name, ref_signal_name, title):
    """This is the method to plot the graphs for estimate vs reference data"""
    fig.add_trace(
        go.Scatter(
            x=ap_time,
            y=est_tire,
            mode="lines",
            name=est_signal_name,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=ap_time,
            y=[
                gt_tire,
            ]
            * len(ap_time),
            mode="lines",
            name=ref_signal_name,
        )
    )
    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"),
        xaxis=dict(tickformat="14"),
        xaxis_title="Time[s]",
        yaxis_title="Distance[m]",
        showlegend=True,
    )
    fig.update_layout(PlotlyTemplate.lgt_tmplt)
    fig.add_annotation(
        dict(
            font=dict(color="black", size=12),
            x=0,
            y=-0.12,
            showarrow=False,
            text=title,
            textangle=0,
            xanchor="left",
            xref="paper",
            yref="paper",
        )
    )
    return fig


def plot_error_rate_vs_threshold(
    ap_time, fig, tyre_error_list, max_deviation_threshold, threshold_str, error_list_str, title
):
    """This is the method to plot the graphs for error rate vs threshold data"""
    fig.add_trace(
        go.Scatter(
            x=ap_time,
            y=[
                max_deviation_threshold,
            ]
            * len(ap_time),
            mode="lines",
            name=threshold_str,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=ap_time,
            y=tyre_error_list,
            mode="lines",
            name=error_list_str,
        )
    )
    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"),
        xaxis=dict(tickformat="14"),
        xaxis_title="Time[s]",
        yaxis_title="Distance[m]",
        showlegend=True,
    )
    fig.update_layout(PlotlyTemplate.lgt_tmplt)
    fig.add_annotation(
        dict(
            font=dict(color="black", size=12),
            x=0,
            y=-0.12,
            showarrow=False,
            text=title,
            textangle=0,
            xanchor="left",
            xref="paper",
            yref="paper",
        )
    )
    return fig


@teststep_definition(
    step_number=1,
    name="The TCE shall provide the Tire Circumference from tyre from the Convergence.",
    description="This is the test case of Tyre Circumference Estimation module shall consider only the converged"
    " Tyre Circumference Estimations. ie, Convergence means that it considers the stable estimations "
    "for which the noise variance is equal or closer to epsilon value, Otherwise that the estimation "
    "value will be equal to the ground truth Tire Circumference value or closer within the +/- acceptable"
    " thresholds when the estimations are averaged for a specific intervals (eg: 3 sec).",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, TceSignals)
class TceTyreConvergedTyreEstimateWithSampleTime(TestStep):
    """The TCE shall provide the Tire Circumference from tyre from the Convergence.

    Objective
    ---------

    The TCE shall provide the Tire Circumference from tyre from the Convergence.

    Detail
    ------

    The TCE shall provide the Tire Circumference from tyre from the Convergence.
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
        est_tire_fr = list(df[TceSignals.Columns.estTyreCircFR])
        est_tire_fl = list(df[TceSignals.Columns.estTyreCircFL])
        est_tire_rr = list(df[TceSignals.Columns.estTyreCircRR])
        est_tire_rl = list(df[TceSignals.Columns.estTyreCircRL])
        gt_tire_front = TceConstantValues.TCE_TYRE_CIRCUMFERENCE_FR_M
        gt_tire_rear = TceConstantValues.TCE_TYRE_CIRCUMFERENCE_RE_M
        gt_x = list(df[TceSignals.Columns.ODO_CM_REF_X])
        gt_y = list(df[TceSignals.Columns.ODO_CM_REF_Y])
        x_estimated = list(df[TceSignals.Columns.ODO_EST_X])
        y_estimated = list(df[TceSignals.Columns.ODO_EST_Y])
        psi_gt = list(df[TceSignals.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR])
        psi_estimated = list(df[TceSignals.Columns.YAW_ANGLE])

        # Init variables
        signal_summary = dict()
        expected_threshold = "0.5%"
        max_deviation_threshold_rear = 0.005 * gt_tire_rear
        max_deviation_threshold_front = 0.005 * gt_tire_front
        sample_time = 3

        _, _, driven_distance, _, _ = calculate_odo_error(gt_x, gt_y, psi_gt, psi_estimated, x_estimated, y_estimated)

        fl_tyre_error_list, fl_converged = check_tyre_circumference_for_driven_wheels(
            gt_tire_front, est_tire_fl, sample_time, ap_time, max_deviation_threshold_front
        )
        fl_evaluation, fl_test_result = get_test_result(
            expected_threshold,
            fl_converged,
            fl_tyre_error_list,
            max_deviation_threshold_front,
            sample_time,
            "front left",
        )

        fr_tyre_error_list, fr_converged = check_tyre_circumference_for_driven_wheels(
            gt_tire_front, est_tire_fr, sample_time, ap_time, max_deviation_threshold_front
        )
        fr_evaluation, fr_test_result = get_test_result(
            expected_threshold,
            fr_converged,
            fr_tyre_error_list,
            max_deviation_threshold_front,
            sample_time,
            "front right",
        )

        rl_tyre_error_list, rl_converged = check_tyre_circumference_for_driven_wheels(
            gt_tire_rear, est_tire_rl, sample_time, ap_time, max_deviation_threshold_rear
        )
        rl_evaluation, rl_test_result = get_test_result(
            expected_threshold, rl_converged, rl_tyre_error_list, max_deviation_threshold_rear, sample_time, "rear left"
        )

        rr_tyre_error_list, rr_converged = check_tyre_circumference_for_driven_wheels(
            gt_tire_rear, est_tire_rr, sample_time, ap_time, max_deviation_threshold_rear
        )
        rr_evaluation, rr_test_result = get_test_result(
            expected_threshold,
            rr_converged,
            rr_tyre_error_list,
            max_deviation_threshold_rear,
            sample_time,
            "rear right",
        )

        if fl_test_result and fr_test_result and rl_test_result and rr_test_result:
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[f"{CarMakerUrl.estTyreCircFR}"] = fr_evaluation
        signal_summary[f"{CarMakerUrl.estTyreCircFL}"] = fl_evaluation
        signal_summary[f"{CarMakerUrl.estTyreCircRR}"] = rr_evaluation
        signal_summary[f"{CarMakerUrl.estTyreCircRL}"] = rl_evaluation

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plots.append(self.sig_sum)
        remarks.append("")

        # #################### Front wheels graph plots ##################################

        plots.append(
            plot_est_vs_ref_grapgs(
                ap_time,
                est_tire_fl,
                go.Figure(),
                gt_tire_front,
                CarMakerUrl.estTyreCircFL,
                "Ground Truth Front Left Tyre Circumference",
                "Estimated VS GT Front Left Tyre Circumference",
            )
        )
        plots.append(
            plot_est_vs_ref_grapgs(
                ap_time,
                est_tire_fr,
                go.Figure(),
                gt_tire_front,
                CarMakerUrl.estTyreCircFR,
                "Ground Truth Front Right Tyre Circumference",
                "Estimated VS GT Front Right Tyre Circumference",
            )
        )

        plots.append(
            plot_error_rate_vs_threshold(
                ap_time,
                go.Figure(),
                fl_tyre_error_list,
                max_deviation_threshold_front,
                "Max Expected deviation threshold",
                "Front left tyre error",
                "Front left tyre circumference error VS Threshold",
            )
        )
        plots.append(
            plot_error_rate_vs_threshold(
                ap_time,
                go.Figure(),
                fr_tyre_error_list,
                max_deviation_threshold_front,
                "Max Expected deviation threshold",
                "Front right tyre error",
                "Front right tyre circumference error VS Threshold",
            )
        )

        # #################### Front wheels graph plots ##################################

        plots.append(
            plot_est_vs_ref_grapgs(
                ap_time,
                est_tire_rl,
                go.Figure(),
                gt_tire_rear,
                CarMakerUrl.estTyreCircRL,
                "Ground Truth Rear Left Tyre Circumference",
                "Estimated VS GT Rear Left Tyre Circumference",
            )
        )
        plots.append(
            plot_est_vs_ref_grapgs(
                ap_time,
                est_tire_rr,
                go.Figure(),
                gt_tire_rear,
                CarMakerUrl.estTyreCircRR,
                "Ground Truth Rear Right Tyre Circumference",
                "Estimated VS GT Rear Right Tyre Circumference",
            )
        )

        plots.append(
            plot_error_rate_vs_threshold(
                ap_time,
                go.Figure(),
                rl_tyre_error_list,
                max_deviation_threshold_rear,
                "Max Expected deviation threshold",
                "Rear left tyre error",
                "Rear left tyre circumference error VS Threshold",
            )
        )
        plots.append(
            plot_error_rate_vs_threshold(
                ap_time,
                go.Figure(),
                rr_tyre_error_list,
                max_deviation_threshold_rear,
                "Max Expected deviation threshold",
                "Rear right tyre error",
                "Rear right tyre circumference error VS Threshold",
            )
        )

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
            fc.REQ_ID: ["1675987"],
            fc.TEST_RESULT: [test_result],
        }
        self.result.details["Additional_results"] = additional_results_dict


@verifies("ReqID_1675987")
@testcase_definition(
    name="The TCE shall provide the Tire Circumference from tyre from the Convergence.",
    description="The TCE shall provide the Tire Circumference from tyre from the Convergence.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_yDU1p3pAEe6n7Ow9oWyCxw&oslc_config.context=https%3A%2F%2Fjazz.con"
    "ti.de%2Fgc%2Fconfiguration%2F30013&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K2"
    "8PvtEeqIqKySVwTVNQ%2Fcomponents%2F__9Yt9nfVEe6n7Ow9oWyCxw",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TceTyreConvergedTyreEstimateWithSampleTimeTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TceTyreConvergedTyreEstimateWithSampleTime,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        TceTyreConvergedTyreEstimateWithSampleTimeTestCase,
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
