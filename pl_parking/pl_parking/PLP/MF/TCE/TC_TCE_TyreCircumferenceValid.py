#!/usr/bin/env python3
"""This is the test case to validate different tyre's circumference is valid"""

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
from pl_parking.PLP.MF.TCE.constants import CarMakerUrl

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "Anil A, uie64067"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.0.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

READER_NAME = "TceTyreCircumferenceValid"


class TceSignals(SignalDefinition):
    """Tce signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TIME"
        estTyreCircFLValid = "estTyreCircFLValid"
        estTyreCircFRValid = "estTyreCircFRValid"
        estTyreCircRLValid = "estTyreCircRLValid"
        estTyreCircRRValid = "estTyreCircRRValid"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.TIME: CarMakerUrl.time,
            self.Columns.estTyreCircFLValid: CarMakerUrl.estTyreCircFLValid,
            self.Columns.estTyreCircFRValid: CarMakerUrl.estTyreCircFRValid,
            self.Columns.estTyreCircRLValid: CarMakerUrl.estTyreCircRLValid,
            self.Columns.estTyreCircRRValid: CarMakerUrl.estTyreCircRRValid,
        }


def check_tyre_circumference_is_valid(est_tyre):
    """Validate the tire circumference is valid or not"""
    if max(est_tyre) > 0:
        tyre_circumference_is_valid = True
    else:
        tyre_circumference_is_valid = False
    return tyre_circumference_is_valid


def evaluation_string_results(tyre_circumference_is_valid, result, tyre_part):
    """Evaluate and validate the result to display the results in report"""
    if not tyre_circumference_is_valid:
        evaluation = f"Evaluation of TCE {tyre_part} Tyre Circumference is not Valid, Hence results is FAILED."
        test_result = fc.FAIL
        result.measured_result = FALSE
    else:
        evaluation = f"Evaluation of TCE {tyre_part} Tyre Circumference is Valid, Hence results is PASSED."
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
        yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]", yaxis_title="Status"
    )
    fig.update_layout(PlotlyTemplate.lgt_tmplt)
    fig.add_annotation(
        dict(
            font=dict(color="black", size=12),
            x=0,
            y=-0.12,
            showarrow=False,
            text="Estimated Tyre Circumference Valid Signal Status",
            textangle=0,
            xanchor="left",
            xref="paper",
            yref="paper",
        )
    )
    return fig


@teststep_definition(
    step_number=1,
    name="The TCE shall provide the front left tyre circumference is Valid.",
    description="The TCE shall provide the front left tyre circumference is Valid.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, TceSignals)
class TceFlTyreCircumferenceValid(TestStep):
    """Test case for TCE front left Tyre Circumference is Valid.

    Objective
    ---------

    The TCE shall provide the front left tyre circumference is Valid.

    Detail
    ------

    The TCE shall provide the front left tyre circumference is Valid.
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
        est_tc_fl = list(df[TceSignals.Columns.estTyreCircFLValid])

        # Init variables
        signal_summary = dict()

        tyre_circumference_is_valid = check_tyre_circumference_is_valid(est_tc_fl)
        evaluation, test_result, self.result.measured_result = evaluation_string_results(
            tyre_circumference_is_valid, self.result, "Front Left"
        )

        signal_summary[f"{CarMakerUrl.estTyreCircFLValid}"] = evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        plots.append(plot_graphs(ap_time, est_tc_fl, fig, CarMakerUrl.estTyreCircFLValid))

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
            fc.REQ_ID: ["1675852"],
            fc.TESTCASE_ID: ["41336"],
            fc.TEST_RESULT: [test_result],
        }
        self.result.details["Additional_results"] = additional_results_dict


@teststep_definition(
    step_number=2,
    name="The TCE shall provide the front right  tyre circumference is Valid.",
    description="The TCE shall provide the front right tyre circumference is Valid.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, TceSignals)
class TceFrTyreCircumferenceValid(TestStep):
    """Test case for TCE front right Tyre Circumference is Valid.

    Objective
    ---------

    The TCE shall provide the front right tyre circumference is Valid.

    Detail
    ------

    The TCE shall provide the front right tyre circumference is Valid.
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
        est_tc_fr = list(df[TceSignals.Columns.estTyreCircFRValid])

        # Init variables
        signal_summary = dict()

        tyre_circumference_is_valid = check_tyre_circumference_is_valid(est_tc_fr)
        evaluation, test_result, self.result.measured_result = evaluation_string_results(
            tyre_circumference_is_valid, self.result, "Front Right"
        )

        signal_summary[f"{CarMakerUrl.estTyreCircFRValid}"] = evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        plots.append(plot_graphs(ap_time, est_tc_fr, fig, CarMakerUrl.estTyreCircFRValid))

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
            fc.REQ_ID: ["1676089"],
            fc.TESTCASE_ID: ["41337"],
            fc.TEST_RESULT: [test_result],
        }
        self.result.details["Additional_results"] = additional_results_dict


# @verifies("TestCase:41194")
@teststep_definition(
    step_number=3,
    name="The TCE shall provide the rear left tyre circumference is Valid",
    description="The TCE shall provide the rear left tyre circumference is Valid.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, TceSignals)
class TceRlTyreCircumferenceValid(TestStep):
    """Test case for TCE rear left Tyre Circumference is Valid.

    Objective
    ---------

    The TCE shall provide the rear left tyre circumference is Valid.

    Detail
    ------

    The TCE shall provide the rear left tyre circumference is Valid.
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
        est_tc_rl = list(df[TceSignals.Columns.estTyreCircRLValid])

        # Init variables
        signal_summary = dict()

        tyre_circumference_is_valid = check_tyre_circumference_is_valid(est_tc_rl)
        evaluation, test_result, self.result.measured_result = evaluation_string_results(
            tyre_circumference_is_valid, self.result, "Rear Left"
        )

        signal_summary[f"{CarMakerUrl.estTyreCircRLValid}"] = evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        plots.append(plot_graphs(ap_time, est_tc_rl, fig, CarMakerUrl.estTyreCircRLValid))

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
            fc.REQ_ID: ["1676083"],
            fc.TESTCASE_ID: ["41338"],
            fc.TEST_RESULT: [test_result],
        }
        self.result.details["Additional_results"] = additional_results_dict


@teststep_definition(
    step_number=4,
    name="The TCE shall provide the rear right  tyre circumference is Valid.",
    description="The TCE shall provide the rear right tyre circumference is Valid.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, TceSignals)
class TceRrTyreCircumferenceValid(TestStep):
    """Test case for TCE rear right Tyre Circumference is valid.

    Objective
    ---------

    The TCE shall provide the rear right tyre circumference is Valid.

    Detail
    ------

    The TCE shall provide the rear right tyre circumference is Valid.
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
        est_tc_rr = list(df[TceSignals.Columns.estTyreCircRRValid])

        # Init variables
        signal_summary = dict()

        tyre_circumference_is_valid = check_tyre_circumference_is_valid(est_tc_rr)
        evaluation, test_result, self.result.measured_result = evaluation_string_results(
            tyre_circumference_is_valid, self.result, "Rear Right"
        )

        signal_summary[f"{CarMakerUrl.estTyreCircRRValid}"] = evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        plots.append(plot_graphs(ap_time, est_tc_rr, fig, CarMakerUrl.estTyreCircRRValid))

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
            fc.REQ_ID: {"Req_ID": ["1676149"]},
            fc.TESTCASE_ID: ["41339"],
            fc.TEST_RESULT: [test_result],
        }
        self.result.details["Additional_results"] = additional_results_dict


@verifies("ReqID: 1675852, 1676089, 1676083, 1676149")
@testcase_definition(
    name="TCE Tire Circumference is Valid.",
    description="TCE Tire Circumference is Valid test case.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fja"
    "zz.conti.de%2Frm4%2Fresources%2FMD_yDPWCXpAEe6n7Ow9oWyCxw&artifactInModule=https%3A%2F%2Fjazz.conti.de%2"
    "Frm4%2Fresources%2FBI_yDTnmXpAEe6n7Ow9oWyCxw&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-project"
    "s%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F__9Yt9nfVEe6n7Ow9oWyCxw&oslc.configuration=https%3A%2F%2Fjazz"
    ".conti.de%2Fgc%2Fconfiguration%2F30013&changeSet=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fcm%2Fchangeset%2F_J"
    "7SNMR2oEe-SquMaddCl2A",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TceTyreCircumferenceValidTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TceFlTyreCircumferenceValid,
            TceFrTyreCircumferenceValid,
            TceRlTyreCircumferenceValid,
            TceRrTyreCircumferenceValid,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        TceTyreCircumferenceValidTestCase,
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
