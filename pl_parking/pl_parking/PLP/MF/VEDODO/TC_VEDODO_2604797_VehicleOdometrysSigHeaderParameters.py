#!/usr/bin/env python3
"""This is the test case to check the sSigHeader Parameters"""

import logging
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
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
from pl_parking.PLP.MF.VEDODO.common import plot_graphs_signgle_signal
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

READER_NAME = "VedodoVelocityOdometrysSigHeaderParameters"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        eSigStatus = "eSigStatus"
        timeMicroSec = "timeMicroSec"
        uiCycleCounter = "uiCycleCounter"
        uiMeasurementCounter = "uiMeasurementCounter"
        CM_TIME = "cm_time"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.eSigStatus: CarMakerUrl.eSigStatus,
            self.Columns.timeMicroSec: CarMakerUrl.timeMicroSec,
            self.Columns.uiCycleCounter: CarMakerUrl.uiCycleCounter,
            self.Columns.uiMeasurementCounter: CarMakerUrl.uiMeasurementCounter,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the sSigHeader Parameters.",
    description="The ESC Odometry shall provide the sSigHeader Parameters.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedsSigHeaderParameters(TestStep):
    """The ESC Odometry shall provide the sSigHeader Parameters.

    Objective
    ---------

    The ESC Odometry shall provide the sSigHeader Parameters.

    Detail
    ------

    The ESC Odometry shall provide the sSigHeader Parameters.
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

        ap_time = list(df[VedodoSignals.Columns.CM_TIME])
        est_e_sig_status = list(df[VedodoSignals.Columns.eSigStatus])
        est_time_micro_sec = list(df[VedodoSignals.Columns.timeMicroSec])
        est_ui_cycle_counter = list(df[VedodoSignals.Columns.uiCycleCounter])
        est_ui_measurement_counter = list(df[VedodoSignals.Columns.uiMeasurementCounter])
        e_sig_status_flag = True
        time_micro_sec_flag = True
        ui_cycle_counter_flag = True
        ui_measurement_counter_flag = True
        evaluation_e_sig_status = ""
        evaluation_time_micro_sec = ""
        evaluation_ui_cycle_counter = ""
        evaluation_ui_measurement_counter = ""
        test_result_list = list()

        signal_summary = dict()
        if not sum(est_e_sig_status):
            evaluation_e_sig_status = "The eSigStatus signal values are zero, no data is available to evaluate"
            e_sig_status_flag = False
        if not sum(est_time_micro_sec):
            evaluation_time_micro_sec = "The timeMicroSec signal values are zero, no data is available to evaluate"
            time_micro_sec_flag = False
        if not sum(est_ui_cycle_counter):
            evaluation_ui_cycle_counter = "The uiCycleCounter signal values are zero, no data is available to evaluate"
            ui_cycle_counter_flag = False
        if sum(est_ui_measurement_counter):
            evaluation_ui_measurement_counter = "The uiMeasurementCounter signal values bust be zero"
            ui_measurement_counter_flag = False

        for s, t, uc, um in zip(est_e_sig_status, est_time_micro_sec, est_ui_cycle_counter, est_ui_measurement_counter):
            if pd.isna(s) and e_sig_status_flag:
                evaluation_e_sig_status = "The eSigStatus signal data having NAN values"
                e_sig_status_flag = False
            if pd.isna(t) and time_micro_sec_flag:
                evaluation_time_micro_sec = "The timeMicroSec signal data having NAN values"
                time_micro_sec_flag = False
            if pd.isna(uc) and ui_cycle_counter_flag:
                evaluation_ui_cycle_counter = "The uiCycleCounter signal data having NAN values"
                ui_cycle_counter_flag = False
            if pd.isna(um) and ui_measurement_counter_flag:
                evaluation_ui_measurement_counter = "The uiMeasurementCounter signal data having NAN values"
                ui_measurement_counter_flag = False

        if e_sig_status_flag:
            evaluation_e_sig_status = "The sSigHeader signal data is having valid data"
            test_result_list.append(True)
        else:
            test_result_list.append(False)
        if time_micro_sec_flag:
            evaluation_time_micro_sec = "The timeMicroSec signal data is having valid data"
            test_result_list.append(True)
        else:
            test_result_list.append(False)
        if ui_cycle_counter_flag:
            evaluation_ui_cycle_counter = "The uiCycleCounter signal data is having valid data"
            test_result_list.append(True)
        else:
            test_result_list.append(False)
        if ui_measurement_counter_flag:
            evaluation_ui_measurement_counter = "The uiMeasurementCounter signal data is having valid data"
            test_result_list.append(True)
        else:
            test_result_list.append(False)

        if all(test_result_list):
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[CarMakerUrl.eSigStatus] = evaluation_e_sig_status
        signal_summary[CarMakerUrl.timeMicroSec] = evaluation_time_micro_sec
        signal_summary[CarMakerUrl.uiCycleCounter] = evaluation_ui_cycle_counter
        signal_summary[CarMakerUrl.uiMeasurementCounter] = evaluation_ui_measurement_counter

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        s_plot = plot_graphs_signgle_signal(
            ap_time, est_e_sig_status, CarMakerUrl.eSigStatus, "Estimated eSigStatus Signal", "Time[s]", ""
        )
        plots.append(s_plot)
        t_plot = plot_graphs_signgle_signal(
            ap_time, est_time_micro_sec, CarMakerUrl.timeMicroSec, "Estimated timeMicroSec Signal", "Time[s]", ""
        )
        plots.append(t_plot)
        uc_plot = plot_graphs_signgle_signal(
            ap_time, est_ui_cycle_counter, CarMakerUrl.uiCycleCounter, "Estimated uiCycleCounter Signal", "Time[s]", ""
        )
        plots.append(uc_plot)
        um_plot = plot_graphs_signgle_signal(
            ap_time,
            est_ui_measurement_counter,
            CarMakerUrl.uiMeasurementCounter,
            "Estimated uiMeasurementCounter Signal",
            "Time[s]",
            "",
        )
        plots.append(um_plot)

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


@verifies("ReqID_2604797")
@testcase_definition(
    name="The ESC Odometry shall provide the sSigHeader Parameters.",
    description="The ESC Odometry shall provide the sSigHeader Parameters.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%"
    "2Fjazz.conti.de%2Frm4%2Fresources%2FBI_8-PY8GFIEe-KEpz7IkVhAA&componentURI=https%3A%2F%2Fjazz.conti."
    "de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configu"
    "ration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedsSigHeaderParametersTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedsSigHeaderParameters,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedsSigHeaderParametersTestCase,
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
