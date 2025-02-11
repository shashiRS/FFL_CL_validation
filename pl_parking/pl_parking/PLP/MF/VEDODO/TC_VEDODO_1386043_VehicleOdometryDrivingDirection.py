#!/usr/bin/env python3
"""This is the test case to check the Driving Direction (Forward or Reverse)."""

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
from pl_parking.PLP.MF.VEDODO.common import plot_graphs_time
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

READER_NAME = "VedodoVelocityOdometryDrivingDirections"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        longitudinalVelocity_mps = "longitudinalVelocity_mps"
        odoEstX = "odoEstX"
        CM_TIME = "cm_time"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.odoEstX: CarMakerUrl.odoEstX,
            self.Columns.longitudinalVelocity_mps: CarMakerUrl.longitudinalVelocity_mps,
        }


@teststep_definition(
    step_number=1,
    name="The ESC Odometry shall provide the Driving Direction (Forward or Reverse).",
    description="The ESC Odometry shall provide the Driving Direction (Forward or Reverse).",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleDrivingDirections(TestStep):
    """The ESC Odometry shall provide the Driving Direction (Forward or Reverse).

    Objective
    ---------

    The ESC Odometry shall provide the Driving Direction (Forward or Reverse).

    Detail
    ------

    The ESC Odometry shall provide the Driving Direction (Forward or Reverse).
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
        odo_v = list(df[VedodoSignals.Columns.longitudinalVelocity_mps])
        odo_x = list(df[VedodoSignals.Columns.odoEstX])
        signal_summary = dict()
        x_p_flag = True
        x_n_flag = True
        stand_still_velocity = 0.001
        pre_x = odo_x[0]
        direction_dict = {
            "forward_x": [],
            "reverse_x": [],
            "stand_still_x": [],
            "forward_v": [],
            "reverse_v": [],
            "stand_still_v": [],
        }

        for x, v, t in zip(odo_x[1:], odo_v[1:], ap_time[1:]):
            if v > stand_still_velocity:  # Moving forward
                if pre_x < x:
                    pre_x = x
                else:
                    x_p_flag = False
                direction_dict["forward_x"].append((x, t))
                direction_dict["forward_v"].append((v, t))
            elif v < -stand_still_velocity:  # Moving reverse
                if pre_x > x:
                    pre_x = x
                else:
                    x_n_flag = False
                direction_dict["reverse_x"].append((x, t))
                direction_dict["reverse_v"].append((v, t))
            if -stand_still_velocity < v < stand_still_velocity:  # Standstill
                pre_x = x
                direction_dict["stand_still_x"].append((x, t))
                direction_dict["stand_still_v"].append((v, t))

        # Determine the evaluation result
        if x_p_flag and x_n_flag:
            evaluation = (
                "The Vehicle driving directions are direct propositions to the vehicle velocity,"
                "Hence test result is PASSED"
            )
            test_result = fc.PASS
            self.result.measured_result = TRUE
        else:
            evaluation = (
                "The Vehicle driving directions are not direct propositions to the vehicle velocity, "
                "Hence test result is FAILED"
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[CarMakerUrl.odoEstX] = evaluation

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fd, fdt = zip(*direction_dict["forward_x"])
        fv, fvt = zip(*direction_dict["forward_v"])
        rd, rdt = zip(*direction_dict["reverse_x"])
        rv, rvt = zip(*direction_dict["reverse_v"])
        sd, sdt = zip(*direction_dict["stand_still_x"])
        sv, svt = zip(*direction_dict["stand_still_v"])

        fvd_plot = plot_graphs_time(
            fvt,
            fv,
            "Forward Velocity w.r.t Position-X",
            fdt,
            fd,
            "Forward direction w.r.t Position-X",
            "Time[s]",
            "Distance[m]",
        )
        plots.append(fvd_plot)
        plot_titles.append("")

        rvd_plot = plot_graphs_time(
            rvt,
            rv,
            "Reverse Velocity w.r.t Position-X",
            rdt,
            rd,
            "Reverse direction w.r.t Position-X",
            "Time[s]",
            "Distance[m]",
        )
        plots.append(rvd_plot)
        plot_titles.append("")

        svd_plot = plot_graphs_time(
            svt,
            sv,
            "StandStill Velocity w.r.t Position-X",
            sdt,
            sd,
            "StandStill direction w.r.t Position-X",
            "Time[s]",
            "Distance[m]",
        )
        plots.append(svd_plot)
        plot_titles.append("")

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


@verifies("ReqID_1386043")
@testcase_definition(
    name="The ESC Odometry shall provide the Driving Direction (Forward or Reverse).",
    description="The ESC Odometry shall provide the Driving Direction (Forward or Reverse).",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%"
    "2Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z5OYTaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti."
    "de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.config"
    "uration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleDrivingDirectionsTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleDrivingDirections,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleDrivingDirectionsTestCase,
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
