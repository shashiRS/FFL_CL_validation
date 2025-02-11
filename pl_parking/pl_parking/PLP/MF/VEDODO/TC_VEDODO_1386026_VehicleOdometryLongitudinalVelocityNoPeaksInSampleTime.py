#!/usr/bin/env python3
"""This is the test case to check the longitudinal velocity has peaks at given sample time of 10ms"""

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

READER_NAME = "VedodoVelocityOdometryLongitudinalVelocityWithSampleTime"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        longitudinalVelocity_mps = "longitudinalVelocity_mps"
        CM_TIME = "cm_time"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.longitudinalVelocity_mps: CarMakerUrl.longitudinalVelocity_mps,
        }


@teststep_definition(
    step_number=1,
    name="When the vehicle speed is faster than 0.2 m/s, the velocity signal shall be a continuous signal "
    "without peaks.",
    description="When the vehicle speed is faster than 0.2 m/s, the velocity signal shall be a continuous signal "
    "without peaks. There shall be no jumps on the outputs which are not caused by the vehicle motion. "
    "Signal jumps can be deviations from the actual velocity for one or a few data samples. That means "
    "between two call cycles (sample time is 10 ms), the vehicle velocity shall not change for more "
    "then 0.1 m/s.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoVehicleEstimatedLongitudinalVelocityNoPeaks(TestStep):
    """When the vehicle speed is faster than 0.2 m/s, the velocity signal shall be a continuous signal without peaks.
    There shall be no jumps on the outputs which are not caused by the vehicle motion. Signal jumps can be deviations
    from the actual velocity for one or a few data samples. That means between two call cycles (sample time is 10 ms),
    the vehicle velocity shall not change for more than 0.1 m/sT.

    Objective
    ---------

    The ESC Odometry shall provide the longitudinal velocity.

    Detail
    ------

    The ESC Odometry shall provide the longitudinal velocity.
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
        v_flag = True
        pre_v = 0
        velocity_speed = 2
        first_instance = True
        max_velocity_deviation_threshold = 0.1
        velocity_deviation_list = list()
        velocity_deviation = 0
        sample_time = 1
        evaluation = ""

        # Init variables
        signal_summary = dict()
        if not sum(odo_v):
            evaluation = "The longitudinal velocity signal values are zero, no data is available to evaluate."
            v_flag = False

        for v in odo_v:
            if pd.isna(v) and v_flag:
                evaluation = "The longitudinal velocity signal data having NAN values."
                v_flag = False
                break

        if v_flag:
            for t, v in zip(ap_time, odo_v):
                if velocity_speed >= v and t % sample_time == 0:
                    abs_v = abs(v)
                    if first_instance:
                        pre_v = abs_v
                        first_instance = False
                    else:
                        velocity_deviation = abs(pre_v - abs_v)
                        pre_v = abs_v
                else:
                    velocity_deviation = 0
                velocity_deviation_list.append(velocity_deviation)

            max_velocity_deviation = max(velocity_deviation_list)
            if max_velocity_deviation_threshold >= max_velocity_deviation:
                evaluation = (
                    f"The velocity signal has no peak values at given sample time cycle of "
                    f"{sample_time * 10}s and max peak value is {max_velocity_deviation}mps, "
                    f"Hence the test result is PASSED"
                )
                test_result = fc.PASS
                self.result.measured_result = TRUE
            else:
                evaluation = (
                    f"The velocity signal has peak values at given sample time cycle of "
                    f"{sample_time * 10}s and max peak value is {max_velocity_deviation}mps, "
                    f"Hence the test result is FAILED"
                )
                test_result = fc.FAIL
                self.result.measured_result = FALSE
        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE

        signal_summary[CarMakerUrl.longitudinalVelocity_mps] = evaluation

        self.sig_sum = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        v_plot = plot_graphs_signgle_signal(
            ap_time,
            odo_v,
            CarMakerUrl.longitudinalVelocity_mps,
            "Estimated Longitudinal Velocity Signal",
            "Time[s]",
            "Velocity[mps]",
        )
        plots.append(v_plot)

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


@verifies("ReqID_1386026")
@testcase_definition(
    name=(
        "When the vehicle speed is faster than 0.2 m/s, the velocity signal shall be a continuous signal without peaks."
    ),
    description=(
        "When the vehicle speed is faster than 0.2 m/s, the velocity signal shall be a continuous signal without "
        "peaks. There shall be no jumps on the outputs which are not caused by the vehicle motion. Signal jumps "
        "can be deviations from the actual velocity for one or a few data samples. That means between two call "
        "cycles (sample time is 10 ms), the vehicle velocity shall not change for more then 0.1 m/s."
    ),
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2"
    "F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z4nXzaaEe6mrdm2_agUYg&oslc_config.context=https%3A%2F%2F"
    "jazz.conti.de%2Fgc%2Fconfiguration%2F17099&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-pr"
    "ojects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoVehicleEstimatedLongitudinalVelocityTestCase(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoVehicleEstimatedLongitudinalVelocityNoPeaks,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG/erg file) and report the result.
    """
    _, testrun_id, cp = debug(
        VedodoVehicleEstimatedLongitudinalVelocityTestCase,
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
