#!/usr/bin/env python3
"""This is the test case to validate different tyre's circumference standard deviate is in meter or not"""

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

READER_NAME = "TceTyreCircumferenceStandardDeviate"


class TceSignals(SignalDefinition):
    """Tce signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TIME"
        estTyreCircStdvFL = "estTyreCircStdvFL"
        estTyreCircStdvFR = "estTyreCircStdvFR"
        estTyreCircStdvRL = "estTyreCircStdvRL"
        estTyreCircStdvRR = "estTyreCircStdvRR"
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
            self.Columns.TIME: CarMakerUrl.time,
            self.Columns.estTyreCircStdvFL: CarMakerUrl.estTyreCircStdvFL,
            self.Columns.estTyreCircStdvFR: CarMakerUrl.estTyreCircStdvFR,
            self.Columns.estTyreCircStdvRL: CarMakerUrl.estTyreCircStdvRL,
            self.Columns.estTyreCircStdvRR: CarMakerUrl.estTyreCircStdvRR,
            self.Columns.ODO_CM_REF_X: vedodoCarMakerUrl.odoCmRefX,
            self.Columns.ODO_CM_REF_Y: vedodoCarMakerUrl.odoCmRefY,
            self.Columns.ODO_EST_X: vedodoCarMakerUrl.odoEstX,
            self.Columns.ODO_EST_Y: vedodoCarMakerUrl.odoEstY,
            self.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR: vedodoCarMakerUrl.odoCmRefyawAngEgoRaCur,
            self.Columns.YAW_ANGLE: vedodoCarMakerUrl.yawAngle,
            self.Columns.GT_Velocity: vedodoCarMakerUrl.velocityX,
        }


def check_tyre_circumference_stdv_in_meter(est_tyre, driven_distance):
    """Here to check the provided signals data format in meter format or not"""
    tyre_circumference_standard_deviate_in_meter = True
    distance = 0
    for estFl, dst in zip(est_tyre, driven_distance):
        distance += dst
        if distance < 2000:  # validating the results after 2 KM distance driven
            continue
        if not estFl:
            continue
        if not TceConstantValues.TCE_TYRE_STDV_RANGE[0] <= estFl <= TceConstantValues.TCE_TYRE_STDV_RANGE[1]:
            tyre_circumference_standard_deviate_in_meter = False
            break
    return tyre_circumference_standard_deviate_in_meter


def evaluation_string_results(tyre_circumference_standard_deviate_in_meter, result, tyre_part):
    """Evaluate and validate the result to display the results in report"""
    if not tyre_circumference_standard_deviate_in_meter:
        evaluation = (
            f"Evaluation of TCE {tyre_part} Tyre Circumference standard deviate not in meter, "
            f"Hence results is FAILED."
        )
        test_result = fc.FAIL
        result.measured_result = FALSE
    else:
        evaluation = (
            f"Evaluation of TCE {tyre_part} Tyre Circumference standard deviate is in meter, "
            f"Hence results is PASSED."
        )
        test_result = fc.PASS
        result.measured_result = TRUE
    return evaluation, test_result, result.measured_result


def plot_graphs(ap_time, est_tyre, fig, est_sig):
    """Method to plot graphs in report"""
    fig.add_trace(
        go.Scatter(
            x=ap_time,
            y=est_tyre,
            mode="lines",
            name=est_sig,
        )
    )

    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"),
        xaxis=dict(tickformat="14"),
        xaxis_title="Time[s]",
        yaxis_title="Tyre Circumference standard deviate[m]",
    )
    fig.update_layout(PlotlyTemplate.lgt_tmplt)
    fig.add_annotation(
        dict(
            font=dict(color="black", size=12),
            x=0,
            y=-0.12,
            showarrow=False,
            text="Estimated Tyre standard deviate",
            textangle=0,
            xanchor="left",
            xref="paper",
            yref="paper",
        )
    )
    return fig


@teststep_definition(
    step_number=1,
    name="The TCE shall provide the front left tyre circumference standard deviate in meter.",
    description="The TCE shall provide the front left tyre circumference standard deviate in meter.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, TceSignals)
class TceFlTyreCircumferenceStdv(TestStep):
    """Test case for TCE front left Tyre Circumference standard deviate.

    Objective
    ---------

    The TCE shall provide the front left tyre circumference standard deviate in meter.

    Detail
    ------

    The TCE shall provide the front left tyre circumference standard deviate in meter.
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
        est_tc_fl = list(df[TceSignals.Columns.estTyreCircStdvFL])

        gt_x = list(df[TceSignals.Columns.ODO_CM_REF_X])
        gt_y = list(df[TceSignals.Columns.ODO_CM_REF_Y])
        x_estimated = list(df[TceSignals.Columns.ODO_EST_X])
        y_estimated = list(df[TceSignals.Columns.ODO_EST_Y])
        psi_gt = list(df[TceSignals.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR])
        psi_estimated = list(df[TceSignals.Columns.YAW_ANGLE])
        # Init variables
        signal_summary = dict()

        _, _, driven_distance, _, _ = calculate_odo_error(gt_x, gt_y, psi_gt, psi_estimated, x_estimated, y_estimated)

        tyre_circumference_stdv_in_meter = check_tyre_circumference_stdv_in_meter(est_tc_fl, driven_distance)
        evaluation, test_result, self.result.measured_result = evaluation_string_results(
            tyre_circumference_stdv_in_meter, self.result, "Front Left"
        )

        signal_summary[f"{CarMakerUrl.estTyreCircStdvFL}"] = evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        plots.append(plot_graphs(ap_time, est_tc_fl, fig, CarMakerUrl.estTyreCircStdvFL))

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
            fc.REQ_ID: ["1675916"],
            fc.TESTCASE_ID: ["41324"],
            fc.TEST_RESULT: [test_result],
        }
        self.result.details["Additional_results"] = additional_results_dict


@teststep_definition(
    step_number=2,
    name="The TCE shall provide the front right  tyre circumference standard deviate in meter.",
    description="The TCE shall provide the front right tyre circumference standard deviate in meter.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, TceSignals)
class TceFrTyreCircumferenceStdv(TestStep):
    """Test case for TCE front right Tyre Circumference standard deviate .

    Objective
    ---------

    The TCE shall provide the front right tyre circumference standard deviate in meter.

    Detail
    ------

    The TCE shall provide the front right tyre circumference standard deviate in meter.
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
        est_tc_fr = list(df[TceSignals.Columns.estTyreCircStdvFR])

        gt_x = list(df[TceSignals.Columns.ODO_CM_REF_X])
        gt_y = list(df[TceSignals.Columns.ODO_CM_REF_Y])
        x_estimated = list(df[TceSignals.Columns.ODO_EST_X])
        y_estimated = list(df[TceSignals.Columns.ODO_EST_Y])
        psi_gt = list(df[TceSignals.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR])
        psi_estimated = list(df[TceSignals.Columns.YAW_ANGLE])
        # Init variables
        signal_summary = dict()

        _, _, driven_distance, _, _ = calculate_odo_error(gt_x, gt_y, psi_gt, psi_estimated, x_estimated, y_estimated)

        tyre_circumference_in_meter = check_tyre_circumference_stdv_in_meter(est_tc_fr, driven_distance)
        evaluation, test_result, self.result.measured_result = evaluation_string_results(
            tyre_circumference_in_meter, self.result, "Front Right"
        )

        signal_summary[f"{CarMakerUrl.estTyreCircStdvFR}"] = evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        plots.append(plot_graphs(ap_time, est_tc_fr, fig, CarMakerUrl.estTyreCircStdvFR))

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
            fc.REQ_ID: ["1675951"],
            fc.TESTCASE_ID: ["41328"],
            fc.TEST_RESULT: [test_result],
        }
        self.result.details["Additional_results"] = additional_results_dict


@teststep_definition(
    step_number=3,
    name="The TCE shall provide the rear left tyre circumference standard deviate in meter.",
    description="The TCE shall provide the rear left tyre circumference standard deviate in meter.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, TceSignals)
class TceRlTyreCircumferenceStdv(TestStep):
    """Test case for TCE rear left Tyre Circumference standard deviate .

    Objective
    ---------

    The TCE shall provide the rear left tyre circumference standard deviate in meter.

    Detail
    ------

    The TCE shall provide the rear left tyre circumference standard deviate in meter.
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
        est_tc_rl = list(df[TceSignals.Columns.estTyreCircStdvRL])

        gt_x = list(df[TceSignals.Columns.ODO_CM_REF_X])
        gt_y = list(df[TceSignals.Columns.ODO_CM_REF_Y])
        x_estimated = list(df[TceSignals.Columns.ODO_EST_X])
        y_estimated = list(df[TceSignals.Columns.ODO_EST_Y])
        psi_gt = list(df[TceSignals.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR])
        psi_estimated = list(df[TceSignals.Columns.YAW_ANGLE])
        # Init variables
        signal_summary = dict()

        _, _, driven_distance, _, _ = calculate_odo_error(gt_x, gt_y, psi_gt, psi_estimated, x_estimated, y_estimated)
        tyre_circumference_in_meter = check_tyre_circumference_stdv_in_meter(est_tc_rl, driven_distance)
        evaluation, test_result, self.result.measured_result = evaluation_string_results(
            tyre_circumference_in_meter, self.result, "Rear Left"
        )

        signal_summary[f"{CarMakerUrl.estTyreCircStdvRL}"] = evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        plots.append(plot_graphs(ap_time, est_tc_rl, fig, CarMakerUrl.estTyreCircStdvRL))

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
            fc.REQ_ID: ["1675857"],
            fc.TESTCASE_ID: ["41330"],
            fc.TEST_RESULT: [test_result],
        }
        self.result.details["Additional_results"] = additional_results_dict


@teststep_definition(
    step_number=4,
    name="The TCE shall provide the rear right  tyre circumference standard deviate in meter.",
    description="The TCE shall provide the rear right tyre circumference standard deviate in meter.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, TceSignals)
class TceRrTyreCircumferenceStdv(TestStep):
    """Test case for TCE rear right Tyre Circumference standard deviate .

    Objective
    ---------

    The TCE shall provide the rear right tyre circumference standard deviate in meter.

    Detail
    ------

    The TCE shall provide the rear right tyre circumference standard deviate in meter.
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
        est_tc_rr = list(df[TceSignals.Columns.estTyreCircStdvRR])

        gt_x = list(df[TceSignals.Columns.ODO_CM_REF_X])
        gt_y = list(df[TceSignals.Columns.ODO_CM_REF_Y])
        x_estimated = list(df[TceSignals.Columns.ODO_EST_X])
        y_estimated = list(df[TceSignals.Columns.ODO_EST_Y])
        psi_gt = list(df[TceSignals.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR])
        psi_estimated = list(df[TceSignals.Columns.YAW_ANGLE])

        # Init variables
        signal_summary = dict()

        _, _, driven_distance, _, _ = calculate_odo_error(gt_x, gt_y, psi_gt, psi_estimated, x_estimated, y_estimated)
        tyre_circumference_in_meter = check_tyre_circumference_stdv_in_meter(est_tc_rr, driven_distance)
        evaluation, test_result, self.result.measured_result = evaluation_string_results(
            tyre_circumference_in_meter, self.result, "Rear Right"
        )

        signal_summary[f"{CarMakerUrl.estTyreCircStdvRR}"] = evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        plots.append(plot_graphs(ap_time, est_tc_rr, fig, CarMakerUrl.estTyreCircStdvRR))

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
            fc.REQ_ID: {"Req_ID": ["1676133"]},
            fc.TESTCASE_ID: ["41331"],
            fc.TEST_RESULT: [test_result],
        }
        self.result.details["Additional_results"] = additional_results_dict


@verifies("ReqID: 1675916, 1675951, 1675857, 1676133")
@testcase_definition(
    name="TCE Tire Circumference standard deviate in meters.",
    description="TCE Tire Circumference standard deviate in meters test case.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fja"
    "zz.conti.de%2Frm4%2Fresources%2FMD_yDPWCXpAEe6n7Ow9oWyCxw&artifactInModule=https%3A%2F%2Fjazz.conti.de%2"
    "Frm4%2Fresources%2FBI_yDTnmXpAEe6n7Ow9oWyCxw&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-project"
    "s%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F__9Yt9nfVEe6n7Ow9oWyCxw&oslc.configuration=https%3A%2F%2Fjazz"
    ".conti.de%2Fgc%2Fconfiguration%2F30013&changeSet=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fcm%2Fchangeset%2F_J"
    "7SNMR2oEe-SquMaddCl2A",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class TceTyreCircumferenceStdvTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TceFlTyreCircumferenceStdv,
            TceFrTyreCircumferenceStdv,
            TceRlTyreCircumferenceStdv,
            TceRrTyreCircumferenceStdv,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        TceTyreCircumferenceStdvTestCase,
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
