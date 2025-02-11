#!/usr/bin/env python3
"""With every stroke (stop and go) an additional distance error is allowed to be added which is equal to wheel
encoder resolution in meters. This can be 2.5 cm
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
from pl_parking.PLP.MF.VEDODO.common import calculate_odo_error
from pl_parking.PLP.MF.VEDODO.constants import CarMakerUrl

from .common import plot_graphs

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


__author__ = "Anil A, Uie64067"
__copyright__ = "2012-2024, Continental AG"
__version__ = "0.0.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

READER_NAME = "VedodoDrivenDistanceErrorDueToStrokes"


class VedodoSignals(SignalDefinition):
    """Vedodo signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        DRIVEN_DISTANCE = "driven_distance"
        CM_TIME = "cm_time"
        ODO_CM_REF_X = "odoCmRefX"
        ODO_CM_REF_Y = "odoCmRefY"
        ODO_EST_X = "odoEstX"
        ODO_EST_Y = "odoEstY"
        ODO_CM_REF_YAWANG_EGO_RA_CUR = "odoCmRefyawAngEgoRaCur"
        YAW_ANGLE = "yawAngle"
        num_strokes = "num_strokes"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.DRIVEN_DISTANCE: CarMakerUrl.drivenDistance_m,
            self.Columns.CM_TIME: CarMakerUrl.time,
            self.Columns.ODO_CM_REF_X: CarMakerUrl.odoCmRefX,
            self.Columns.ODO_CM_REF_Y: CarMakerUrl.odoCmRefY,
            self.Columns.ODO_EST_X: CarMakerUrl.odoEstX,
            self.Columns.ODO_EST_Y: CarMakerUrl.odoEstY,
            self.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR: CarMakerUrl.odoCmRefyawAngEgoRaCur,
            self.Columns.YAW_ANGLE: CarMakerUrl.yawAngle,
            self.Columns.num_strokes: CarMakerUrl.num_strokes,
        }


@teststep_definition(
    step_number=1,
    name="The relative driven distance position error shall not exceed 0.06 m per driven meter in"
    " normal driving conditions.",
    description="The relative driven distance position error shall not exceed 0.06 m per driven meter in"
    " normal driving conditions.",
    expected_result=BooleanResult(TRUE),
    doors_url="https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_RiAxIJNHEe674_0gzoV9FQ?oslc.configuration=https%3A%"
    "2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099#action=com.ibm.rqm.planning.home.actionDispatcher&subAc"
    "tion=viewTestCase&id=38755",
)
@register_signals(READER_NAME, VedodoSignals)
class VedodoRelativeDrivenDistanceErrorDueToStrokes(TestStep):
    """
    With every stroke (stop and go) an additional distance error is allowed to be added which is equal to wheel
    encoder resolution in meters. This can be 2.5 cm

    Objective
    ---------

    With every stroke (stop and go) an additional distance error is allowed to be added which is equal to wheel
    encoder resolution in meters. This can be 2.5 cm

    Detail
    ------

    With every stroke (stop and go) an additional distance error is allowed to be added which is equal to wheel
    encoder resolution in meters. This can be 2.5 cm
    """

    custom_report = MfCustomTeststepReport

    def __init__(self):
        super().__init__()
        self.sig_summary = None

    def process(self, **kwargs):
        """Evaluating test case"""
        _log.debug("Starting processing...")
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)
        df: pd.DataFrame = self.readers[READER_NAME]

        max_expected_error: float = 0.06
        error_allowed_per_stroke = 0.025
        signal_summary = dict()

        ap_time = list(df[VedodoSignals.Columns.CM_TIME])
        gt_x = list(df[VedodoSignals.Columns.ODO_CM_REF_X])
        gt_y = list(df[VedodoSignals.Columns.ODO_CM_REF_Y])
        x_estimated = list(df[VedodoSignals.Columns.ODO_EST_X])
        y_estimated = list(df[VedodoSignals.Columns.ODO_EST_Y])
        psi_gt = list(df[VedodoSignals.Columns.ODO_CM_REF_YAWANG_EGO_RA_CUR])
        psi_estimated = list(df[VedodoSignals.Columns.YAW_ANGLE])
        est_driven_dist = list(df[VedodoSignals.Columns.DRIVEN_DISTANCE])
        num_strokes = list(df[VedodoSignals.Columns.num_strokes])

        max_strokes = max(num_strokes)
        _, _, gt_driven_dist, _, _ = calculate_odo_error(gt_x, gt_y, psi_gt, psi_estimated, x_estimated, y_estimated)

        for i in range(len(num_strokes) - 1):
            if num_strokes[i] != num_strokes[i + 1]:
                est_driven_dist[i] += error_allowed_per_stroke

        sum_gt_driven_dist = sum(gt_driven_dist)
        sum_est_driven_dist = sum(est_driven_dist)
        deviation_error = abs(sum_est_driven_dist - sum_gt_driven_dist)

        if not max_strokes:
            evaluation = (
                f"The Evaluation for Driven Distance during multiple strokes is not possible, because the "
                f"number of occurred strokes in entire parking manoeuvre is {max_strokes}. Hence result is"
                f"FAILED"
            )
            test_result = fc.FAIL
            self.result.measured_result = FALSE
        else:
            if deviation_error <= max_expected_error:
                evaluation = " ".join(
                    f"Evaluation for Driven Distance during multiple strokes, number of strokes occurred in entire "
                    f"parking manoeuvre is {max_strokes}. The deviation error is {round(deviation_error, 3)}m"
                    f" and the max expected threshold value is {max_expected_error}m."
                    f" The deviation error is below the threshold. Hence the result is PASSED".split()
                )
                test_result = fc.PASS
                self.result.measured_result = TRUE
            else:
                evaluation = " ".join(
                    f"Evaluation for Driven Distance during multiple strokes, number of strokes occurred in entire "
                    f"parking manoeuvre is {max_strokes}. The deviation error is {round(deviation_error, 3)}m"
                    f" and the max expected threshold value is {max_expected_error}m."
                    f"The deviation error is above the threshold. Hence the result is FAILED".split()
                )
                test_result = fc.FAIL
                self.result.measured_result = FALSE

        signal_summary[CarMakerUrl.drivenDistance_m] = evaluation
        self.sig_summary = convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_summary)
        remarks.append("")

        plot_dist = plot_graphs(
            ap_time,
            est_driven_dist,
            CarMakerUrl.drivenDistance_m,
            gt_driven_dist,
            "GT Driven Distance",
            "Time[s]",
            "Distance[m]",
        )
        plots.append(plot_dist)

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
            "Driven Distance": {"value": max_expected_error, "color": get_color(test_result)},
        }
        self.result.details["Additional_results"] = additional_results_dict


@verifies("ReqId-1386176")
@testcase_definition(
    name="With every stroke (stop and go) an additional distance error is allowed to be added which is equal to "
    "wheel encoder resolution in meters. This can be 2.5 cm",
    description="With every stroke (stop and go) an additional distance error is allowed to be added which is equal "
    "to wheel encoder resolution in meters. This can be 2.5 cm",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%"
    "2Fjazz.conti.de%2Frm4%2Fresources%2FBI_3z7qpjaaEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti"
    ".de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_2ewE0DK_Ee6mrdm2_agUYg&oslc.conf"
    "iguration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F30013",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class VedodoRelativeDrivenDistanceErrorDueToStrokesTestCase(TestCase):
    """VedodoRelativeDrivenDistancePositionErrorNormalInConditionsTestCase test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VedodoRelativeDrivenDistanceErrorDueToStrokes,
        ]


def main(temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.

    """
    _, testrun_id, cp = debug(
        VedodoRelativeDrivenDistanceErrorDueToStrokesTestCase,
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
