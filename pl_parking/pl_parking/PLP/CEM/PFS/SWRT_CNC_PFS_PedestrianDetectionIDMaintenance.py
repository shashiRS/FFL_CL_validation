"""Pedestrian Crossing Detection ID Maintenance Test."""

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
from pl_parking.PLP.CEM.ft_ped_helper import FtPedHelper
from pl_parking.PLP.CEM.inputs.input_CemPedCrossReader import PedCrossReader
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import VedodoReader
from pl_parking.PLP.CEM.inputs.input_PmsdPedCrossReader import PMSDPedCrossCamera, PMSDPedCrossReader

SIGNAL_DATA = "PFS_Ped_ID_Maintenance"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS Ped Crossing Detection ID Maintenance",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPedMainID(TestStep):
    """Pedestrian Crossing Detection ID Maintenance Test."""

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

            Ped_data = PedCrossReader(reader).convert_to_class()
            psd_Ped_data = PMSDPedCrossReader(reader).convert_to_class()

            vedodo_buffer = VedodoReader(reader).convert_to_class()

            if any(reader.as_plain_df["Cem_numberOfPedCrossings"].values > 0):
                rows = []
                failed = 0

                for index, curTimeframe in enumerate(Ped_data):
                    if index == 0:
                        continue
                    prevTimeframe = Ped_data[index - 1]
                    relative_motion_output = vedodo_buffer.calc_relative_motion(
                        curTimeframe.timestamp, prevTimeframe.timestamp
                    )

                    transformed_prevSlots = [
                        FtPedHelper.transform_ped(self, ped, relative_motion_output)
                        for ped in prevTimeframe.pedestrian_crossing_detection
                    ]

                    psd_timeframe_index = [
                        FtPedHelper.get_PedCross_timeframe_index(
                            self, curTimeframe.timestamp, prevTimeframe.timestamp, psd_Ped_data[camera]
                        )
                        for camera in PMSDPedCrossCamera
                    ]

                    psd_timeframes = [
                        psd_Ped_data[camera][psd_timeframe_index[int(camera)]]
                        for camera in PMSDPedCrossCamera
                        if psd_timeframe_index[int(camera)] is not None
                    ]

                    updatedPeds = FtPedHelper.get_peds_with_associated_input(
                        self, transformed_prevSlots, psd_timeframes
                    )

                    associations = FtPedHelper.associate_ped_list(
                        self, curTimeframe.pedestrian_crossing_detection, updatedPeds
                    )

                    for prev_ixd, curr_index in associations.items():
                        if (
                            updatedPeds[prev_ixd].Ped_id
                            != curTimeframe.pedestrian_crossing_detection[curr_index].Ped_id
                        ):
                            failed += 1
                            values = [
                                [curTimeframe.timestamp],
                                [updatedPeds[prev_ixd].Ped_id],
                                [curTimeframe.pedestrian_crossing_detection[curr_index].Ped_id],
                            ]
                            rows.append(values)

                if failed:
                    test_result = fc.FAIL
                    values = list(zip(*rows))
                    fig = go.Figure(
                        data=[
                            go.Table(
                                header=dict(values=["Timestamp", "Prev Ped ID", "Curr Ped ID"]),
                                cells=dict(values=values),
                            )
                        ]
                    )
                    plot_titles.append("Test Fail report")
                    plots.append(fig)
                    remarks.append("")
                    evaluation = (
                        "Pedestrian detection is received in the current timeframe and can not be associated to a "
                        "parking pedestrian detection already received in previous time frames"
                    )
                    signal_summary["PedestrianCrossing_InsideFOV"] = evaluation
                else:
                    test_result = fc.PASS
                    evaluation = (
                        "Pedestrian detection is received in the current timeframe and can be associated to a "
                        "parking pedestrian detection already received in previous time frames"
                    )
                    signal_summary["PedestrianCrossing_InsideFOV"] = evaluation

            else:
                test_result = fc.INPUT_MISSING
                evaluation = "Required input is missing"
                signal_summary["PedestrianCrossing_InsideFOV"] = evaluation

        except KeyError as err:
            test_result = fc.FAIL
            evaluation = "Key Error " + str(err)

        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": "EnvironmentFusion maintains the identifier of each pedestrian if a Pedestrian detection is received in the current timeframe and can be associated to a "
                    "parking pedestrian detection already received in previous time frames",
                },
                "Result": {
                    "1": evaluation,
                },
                "Verdict": {
                    "1": "PASSED" if test_result == "passed" else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PFS Pedestrian Detection ID maintenance")
        self.result.details["Plots"].append(sig_sum)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2260073"],
            fc.TESTCASE_ID: ["69852"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                """This test checks that EnvironmentFusion maintains the identifier of each pedestrian if a pedestrian
                    detection is received in the current timeframe and can be associated to a parking pedestrian detection already
                    received in previous time frames"""
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


@verifies("2260073")
@testcase_definition(
    name="SWRT_CNC_PFS_PedestrianDetectionIDMaintenance",
    description="""This test checks that EnvironmentFusion maintains the identifier of each pedestrian if a pedestrian
        detection is received in the current timeframe and can be associated to a parking pedestrian detection already
        received in previous time frames.""",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_GuEOwQ1LEe-9Pf5VGwDpVA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
class FtPedMainID(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPedMainID]
