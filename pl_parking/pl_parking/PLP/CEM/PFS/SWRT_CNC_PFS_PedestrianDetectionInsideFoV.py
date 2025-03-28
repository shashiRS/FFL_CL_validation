"""Pedestrian Crossing Detection Inside FOV Test."""

import logging

from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

TRC_ROOT = os.path.abspath(os.path.join(__file__, "", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


import pandas as pd
import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import ConstantsCem
from pl_parking.PLP.CEM.ft_ped_helper import FtPedHelper
from pl_parking.PLP.CEM.inputs.input_CemPedCrossReader import PedCrossReader

SIGNAL_DATA = "PFS_Ped_Field_of_View"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS Pedestrian Crossing Detection Field of View",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPedFieldOFView(TestStep):
    """Pedestrian Crossing Detection Inside FOV Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step"""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)
        signal_summary = {}
        evaluation = []

        reader = self.readers[SIGNAL_DATA]

        try:
            input_reader = PedCrossReader(reader)
            ped_data = input_reader.convert_to_class()

            if any(reader.as_plain_df["Cem_numberOfPedCrossings"].values > 0):
                rows = []
                failed = 0

                for time_frame in ped_data:
                    if not time_frame.pedestrian_crossing_detection:
                        for ped in time_frame.pedestrian_crossing_detection:
                            closes_point = FtPedHelper.get_closest_point(ped)
                            if (
                                abs(closes_point.x) > ConstantsCem.AP_G_DES_MAP_RANGE_M / 2
                                or abs(closes_point.y) > ConstantsCem.AP_G_DES_MAP_RANGE_M / 2
                            ):
                                failed += 1
                                values = [
                                    [time_frame.timestamp],
                                    [ped.Ped_id],
                                    [closes_point.x],
                                    [closes_point.y],
                                    [ConstantsCem.AP_G_DES_MAP_RANGE_M],
                                ]
                                rows.append(values)

                if failed:
                    test_result = fc.FAIL
                    values = list(zip(*rows))
                    fig = go.Figure(
                        data=[
                            go.Table(
                                header=dict(values=["Timestamp", "PEDID", "x", "y", "LIMIT_OUTPUT_FIELD_OF_VIEW"]),
                                cells=dict(values=values),
                            )
                        ]
                    )
                    plot_titles.append("Test Fail report")
                    plots.append(fig)
                    remarks.append("")
                    evaluation = f"""CEM output does not contains only PedCrossingsDetection inside the limited {ConstantsCem.AP_G_DES_MAP_RANGE_M} x {ConstantsCem.AP_G_DES_MAP_RANGE_M} field of view."""
                    signal_summary["PedestrianCrossing_InsideFOV"] = evaluation
                else:
                    test_result = fc.PASS
                    evaluation = f"""CEM output contains only PedCrossingsDetection inside the limited {ConstantsCem.AP_G_DES_MAP_RANGE_M} x {ConstantsCem.AP_G_DES_MAP_RANGE_M} field of view."""
                    signal_summary["PedestrianCrossing_InsideFOV"] = evaluation
            else:
                test_result = fc.INPUT_MISSING
                evaluation = "Required input is missing"
                signal_summary["PedestrianCrossing_InsideFOV"] = evaluation
        except KeyError as err:
            test_result = fc.FAIL
            evaluation = "Key Error " + str(err)
            signal_summary["PedestrianCrossing_InsideFOV"] = evaluation

        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": f"""EnvironmentFusion checks if CEM output contains only parking slots inside the limited {ConstantsCem.AP_G_DES_MAP_RANGE_M} x {ConstantsCem.AP_G_DES_MAP_RANGE_M} field of view.""",
                },
                "Result": {
                    "1": evaluation,
                },
                "Verdict": {
                    "1": "PASSED" if test_result == "passed" else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PFS Slot Detection ID maintenance")
        self.result.details["Plots"].append(sig_sum)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2260044"],
            fc.TESTCASE_ID: ["69849"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                f"""This test case checks if PFS output contains only pedestrian crossing inside the limited
                {ConstantsCem.AP_G_DES_MAP_RANGE_M} x {ConstantsCem.AP_G_DES_MAP_RANGE_M} field of view."""
            ],
            fc.TEST_RESULT: [test_result],
        }

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = result_df


@verifies("2260044")
@testcase_definition(
    name="SWRT_CNC_PFS_PedestrianDetectionInsideFoV",
    description=f"""This test case checks if CEM output contains only pedestrian crossing detection inside the limited
    {ConstantsCem.AP_G_DES_MAP_RANGE_M} x {ConstantsCem.AP_G_DES_MAP_RANGE_M} field of view.""",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_dXbIqQ1IEe-9Pf5VGwDpVA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
class FtPedFieldOFView(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPedFieldOFView]
