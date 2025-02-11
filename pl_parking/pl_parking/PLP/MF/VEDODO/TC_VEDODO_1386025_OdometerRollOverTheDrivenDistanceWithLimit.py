#!/usr/bin/env python3
"""This is the test case to check the Odometer of Driven Distance is resetting to zero when the crossing positive or
negative side to 1000m
"""

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
from pl_parking.PLP.MF.VEDODO.common import plot_graphs_threshold
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

READER_NAME = "VedodoVehicleDrivenDistanceResetWhenLimitCrossed"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        time = "time"
        drivenDistance_m = "drivenDistance_m"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.time: CarMakerUrl.time,
            self.Columns.drivenDistance_m: CarMakerUrl.drivenDistance_m,
        }


@teststep_definition(
    step_number=1,
    name="Test step to monitor DrivenDistance signal values are reset with +-1000m reached",
    description="This is the test case to check the Odometer is resetting to zero when the crossing positive or "
    "negative side limit 1000m",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoMonitorVehicleDrivenDistanceResetWithLimit(TestStep):
    """Test step to monitor DrivenDistance signal values are reset with +-1000m reached.

    Objective
    ---------

    Test step to monitor DrivenDistance signal values are reset with +-1000m reached.

    Detail
    ------

    Test step to monitor DrivenDistance signal values are reset with +-1000m reached.
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
        driven_dist = list(df[VedodoSignals.Columns.drivenDistance_m])
        max_driven_distance = max(driven_dist)
        signal_summary = dict()

        if max_driven_distance < 1000:
            evaluation = (
                f"Evaluation for Vehicle Odometer Driven Distance is roll overed successfully at 1000m and "
                f"max Driven Distance is {max_driven_distance}m. Hence test case is PASSED."
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            evaluation = (
                f"Evaluation for Vehicle Odometer Driven Distance is failed to roll over at 1000m and "
                f"max Driven Distance is {max_driven_distance}m. Hence test case is FAILED."
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary["VehicleDrivenDistanceResetWith1000mLimit"] = evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        driven_dist_plot = plot_graphs_threshold(
            time,
            driven_dist,
            CarMakerUrl.drivenDistance_m,
            1000,
            "DrivenDistance Roll Over with 1000m Limit",
            "Time[s]",
            "Distance[m]",
        )
        plots.append(driven_dist_plot)

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


@verifies("ReqID_1386025")
@testcase_definition(
    name="Test step to monitor DrivenDistance signal values are reset with +-1000m reached",
    description="Test step to monitor DrivenDistance signal values are reset with +-1000m reached",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%"
    "2Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z4nXTaaEe6mrdm2_agUYg&oslc_config.context=https%3A%2F%2Fjazz"
    ".conti.de%2Fgc%2Fconfiguration%2F17099&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2"
    "F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoMonitorVehicleDrivenDistanceResetWithLimitTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoMonitorVehicleDrivenDistanceResetWithLimit,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoMonitorVehicleDrivenDistanceResetWithLimitTestCase,
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
