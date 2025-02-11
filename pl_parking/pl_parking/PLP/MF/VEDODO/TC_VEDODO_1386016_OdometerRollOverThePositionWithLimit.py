#!/usr/bin/env python3
"""This is the test case to check the Odometer is resetting to zero when the crossing positive or
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
from pl_parking.PLP.MF.VEDODO.common import plot_graphs
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

READER_NAME = "VedodoVehiclePositionResetWhenLimitCrossed"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        time = "time"
        odoEstX = "odoEstX"
        odoEstY = "odoEstY"
        odoCmRefX = "odoCmRefX"
        odoCmRefY = "odoCmRefY"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.time: CarMakerUrl.time,
            self.Columns.odoCmRefX: CarMakerUrl.odoCmRefX,
            self.Columns.odoCmRefY: CarMakerUrl.odoCmRefY,
            self.Columns.odoEstX: CarMakerUrl.odoEstX,
            self.Columns.odoEstY: CarMakerUrl.odoEstY,
        }


@teststep_definition(
    step_number=1,
    name="Test step to monitor position (x,y) signal values are reset with +-1000m reached.",
    description="Test step to monitor position (x,y) signal values are reset with +-1000m reached.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoMonitorVehiclePositionResetWithLimit(TestStep):
    """Test step to monitor position (x,y) signal values are reset with +-1000m reached.

    Objective
    ---------

    Test step to monitor position (x,y) signal values are reset with +-1000m reached.

    Detail
    ------

    Test step to monitor position (x,y) signal values are reset with +-1000m reached.
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
        est_x = list(df[VedodoSignals.Columns.odoEstX])
        est_y = list(df[VedodoSignals.Columns.odoEstY])
        ref_x = list(df[VedodoSignals.Columns.odoCmRefX])
        ref_y = list(df[VedodoSignals.Columns.odoCmRefY])

        signal_summary = dict()
        sum_x = 0
        sum_y = 0
        pre_x = 0
        pre_y = 0
        flag = True

        for ex, ey in zip(est_x, est_y):
            sum_x += ex
            sum_y += ey

            if pre_x or pre_y:
                if ex > 1000 or ey > 1000:
                    flag = False
                    break

            if 999 >= sum_x >= 1000:
                pre_x = sum_x
                sum_x = 0

            if 997 >= sum_y >= 1000:
                pre_y = sum_y
                sum_y = 0

        if flag:
            evaluation = (
                "Evaluation for Vehicle Odometer position (x,y) is roll overed successfully when reaching "
                "to 1000m, Hence test case is PASSED"
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            evaluation = (
                f"Evaluation for Vehicle Odometer position (x,y) is not roll overed when reaching "
                f"to 1000m, Hence test case is FAILED, max position-x is {max(est_x)}m and max position-y is "
                f"{max(est_y)}m."
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary["VehiclePositions(x,y)ResetAt1000mLimit"] = evaluation
        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig_x = plot_graphs(time, est_x, CarMakerUrl.odoEstX, ref_x, CarMakerUrl.odoCmRefX, "Time[s]", "Distance[m]")
        plot_titles.append(" ")
        plots.append(fig_x)
        remarks.append("")

        fig_y = plot_graphs(time, est_y, CarMakerUrl.odoEstY, ref_y, CarMakerUrl.odoCmRefY, "Time[s]", "Distance[m]")
        plot_titles.append(" ")
        plots.append(fig_y)
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


@verifies("ReqID_1386016")
@testcase_definition(
    name="Test step to monitor position (x,y) signal values are reset with +-1000m reached",
    description="Test step to monitor position (x,y) signal values are reset with +-1000m reached",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_3z4nVTaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti.de%2F"
    "rm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.configuration="
    "https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoMonitorVehiclePositionResetWithLimitTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoMonitorVehiclePositionResetWithLimit,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoMonitorVehiclePositionResetWithLimitTestCase,
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
