"""Output Latency Compensation Test."""

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
from tsf.io.signals import SignalDefinition

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
from pl_parking.PLP.CEM.inputs.input_CemTpfReader import TPFReader
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import VedodoReader

LSMO_DATA = "LSMO_DATA"


class LsmoSignals(SignalDefinition):
    """Custom signal definition for LSMO"""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TPF_TIMESTAMP = "tpf_timestamp"
        LSMO_TIMESTAMP = "vedodo_timestamp_us"
        LSMO_SIGSTATUS = "vedodo_signalState"
        X = "x"
        Y = "y"
        YAW = "yaw"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["cem_outpus_sub.dynamic_objects", "CarPC.EM_Thread.CemInDynamicEnvironment"]

        self._properties = [
            (
                self.Columns.TPF_TIMESTAMP,
                [
                    "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.LSMO_TIMESTAMP,
                [
                    # "cem_outpus_sub.ego_motion_at_cem_time.vehicle_pose_est_at_cem_time.timestamp_us",
                    # "CarPC.EM_Thread.OdoEstimationPortAtCem.timestamp_us",
                    # "egoMotionAtCemOutput.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.CEM200_LSMO_DATA.m_EgoMotionOutput.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.LSMO_SIGSTATUS,
                [
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.motionStatus_nu",
                    "CarPC.EM_Thread.OdoEstimationPortAtCemtate_nu",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.sSigHeader.eSigStatus",
                    "MTA_ADC5.CEM200_LSMO_DATA.m_EgoMotionOutput.sSigHeader.eSigStatus",
                ],
            ),
            (
                self.Columns.X,
                [
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.xPosition_m",
                    "cem_outpus_sub.ego_motion_at_cem_time.vehicle_pose_est_at_cem_time.x_position_m",
                    "CarPC.EM_Thread.OdoEstimationPortAtCem.xPosition_m",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.odoEstimationAtCemTime.xPosition_m",
                    "MTA_ADC5.CEM200_LSMO_DATA.m_EgoMotionOutput.odoEstimationAtCemTime.xPosition_m",
                ],
            ),
            (
                self.Columns.Y,
                [
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.yPosition_m",
                    "cem_outpus_sub.ego_motion_at_cem_time.vehicle_pose_est_at_cem_time.y_position_m",
                    "CarPC.EM_Thread.OdoEstimationPortAtCem.yPosition_m",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.odoEstimationAtCemTime.yPosition_m",
                    "MTA_ADC5.CEM200_LSMO_DATA.m_EgoMotionOutput.odoEstimationAtCemTime.yPosition_m",
                ],
            ),
            (
                self.Columns.YAW,
                [
                    "egoMotionAtCemOutput.odoEstimationAtCemTime.yawAngle_rad",
                    "cem_outpus_sub.ego_motion_at_cem_time.vehicle_pose_est_at_cem_time.yaw_angle_rad",
                    "CarPC.EM_Thread.OdoEstimationPortAtCem.yawAngle_rad",
                    "MTA_ADC5.CEM200_AUPDF_DATA.EgoMotionOutput.odoEstimationAtCemTime.yawAngle_rad",
                    "MTA_ADC5.CEM200_LSMO_DATA.m_EgoMotionOutput.odoEstimationAtCemTime.yawAngle_rad",
                ],
            ),
        ]


example_obj = CemSignals()
lsmo_obj = LsmoSignals()


@teststep_definition(
    step_number=1,
    name="CEM-TPF Latency Compensation",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(LSMO_DATA, LsmoSignals)
class TestStepFtTPFOutputAtT7(TestStep):
    """Output Latency Compensation Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step"""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarsk based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)
        data = pd.DataFrame()

        reader = self.readers[LSMO_DATA]
        reader = reader[5:]  # drop the first frames because they might not be initialized
        input_reader = TPFReader(reader)
        data["timestamp"] = input_reader.data["tpf_timestamp"]
        lsmo_buffer = VedodoReader(reader).convert_to_class()

        # Check if data has been provided to continue with the validation
        if len(data.timestamp) or len(lsmo_buffer.buffer):
            tpf_df = data.reset_index()
            t7_df = pd.DataFrame(lsmo_buffer.buffer)
            # Check that every timestamp that is present in the TPF output is matching the one provided by T7.
            if tpf_df.timestamp.equals(t7_df.timestamp):
                test_result = fc.PASS
            # Otherwise test will fail
            else:
                # Create a detailed table to show timeframe failing and the corresponding values
                test_result = fc.FAIL
                matching_data = pd.DataFrame(tpf_df.timestamp == t7_df.timestamp)
                failed_cycles = matching_data.loc[~matching_data.timestamp].index
                tpf_failing = tpf_df.filter(items=failed_cycles, axis=0).timestamp
                t7_failing = t7_df.filter(items=failed_cycles, axis=0).timestamp
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Cycle count", "TPF timestamp", "T7 timestamp"]),
                            cells=dict(values=[failed_cycles, tpf_failing, t7_failing]),
                        )
                    ]
                )
                plot_titles.append("Test Fail report for not matching timestamps")
                plots.append(fig)
                remarks.append("")

            # Add a summary plot with signals behaviour along the rrec
            fig = go.Figure(
                data=[
                    go.Scatter(
                        x=tpf_df.index, y=(tpf_df.timestamp - t7_df.timestamp) / 1e3, mode="lines", name="Offset"
                    )
                ]
            )

            plot_titles.append("TPF timestamp offset ms")
            plots.append(fig)
            remarks.append("")

        else:
            test_result = fc.INPUT_MISSING

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["TBD"],
            fc.TESTCASE_ID: ["TBD"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                """This test case checks if TPF provides its signals in the Vehicle coordinate system at T7"""
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


@verifies("TBD")
@testcase_definition(
    name="SWRT_CNC_TPF_OutputLatencyCompensation",
    description="This test case checks if TPF provides its signals in the Vehicle coordinate system at T7",
)
class FtTPFOutputAtT7(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtTPFOutputAtT7]
