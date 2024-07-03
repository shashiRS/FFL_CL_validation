"""Functional Test Cases - CEM - EML component"""

import logging

from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import CemSignals, CustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import ConstantsCem

SIGNAL_DATA = "CEM-LSMO Al Signal State"

# TODO: VERIFY IF VEDODO DATA IS THE INPUT AND MOTION_DATA IS THE OUTPUT. TCs NOT VERIFIED YET, DATA IS NOT AVAILABLE


@teststep_definition(
    step_number=1,
    name="CEM-LSMO Al Signal State",
    description="This test case checks if LSMO only processes input signals if their signal state is AL_SIG_STATE_OK",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtLSMOAlSignalState(TestStep):
    """TestStep for evaluating LSMOAl signal states, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        data_df = reader.as_plain_df

        motion_data = data_df.filter(regex="EgoMotionPort_")
        vedodo_data = data_df[["vedodo_timestamp_us", "vedodo_signalState", "x", "y", "yaw"]]

        # Find ts where input signal state changes from 0 to 1
        first_section_end_ts = vedodo_data[
            vedodo_data["vedodo_signalState"].isin([fc.AL_SIG_STATE_OK])
        ].vedodo_timestamp_us.min()
        lsmo_closest_ts = motion_data.loc[
            motion_data.EgoMotionPort_uiTimeStamp > first_section_end_ts, "EgoMotionPort_uiTimeStamp"
        ].min()

        # Find ts where there must be data in the output
        processing_tolerance = ConstantsCem.CYCLE_PERIOD_TIME_MS * ConstantsCem.NUM_OF_CYCLES_FOR_OUTPUT * 1e3
        processing_end_ts = motion_data.loc[
            motion_data.EgoMotionPort_uiTimeStamp > first_section_end_ts + processing_tolerance,
            "EgoMotionPort_uiTimeStamp",
        ].min()

        failing_section = []
        expected_result = []
        result_provided = []
        section_range = []

        # Confirm there is no output at first section
        first_section = motion_data.loc[motion_data["EgoMotionPort_uiTimeStamp"] < lsmo_closest_ts]
        if (first_section["EgoMotionPort_frontWheelAngle_rad"] == 0).all():
            first_section_result = True
        else:
            first_section_result = False
            failing_section.append("First scenario")
            expected_result.append("frontWheelAngle_rad = 0")
            result_provided.append(
                [
                    first_section["EgoMotionPort_frontWheelAngle_rad"].min(),
                    first_section["EgoMotionPort_frontWheelAngle_rad"].max(),
                ]
            )
            section_range.append(f"0 - {lsmo_closest_ts}")

        # Confirm there is output at second section
        second_section = motion_data.loc[motion_data["EgoMotionPort_uiTimeStamp"] > processing_end_ts]
        if (second_section["EgoMotionPort_frontWheelAngle_rad"] != 0).all():
            second_section_result = True
        else:
            second_section_result = False
            failing_section.append("Second scenario")
            expected_result.append("frontWheelAngle_rad != 0")
            result_provided.append(
                [
                    second_section["EgoMotionPort_frontWheelAngle_rad"].min(),
                    second_section["EgoMotionPort_frontWheelAngle_rad"].max(),
                ]
            )
            section_range.append(f"{processing_end_ts} - end")

        if first_section_result and second_section_result:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL
            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(
                            values=["Failing section", "Expected output", "Min Max values", "Output section range"]
                        ),
                        cells=dict(values=[failing_section, expected_result, result_provided, section_range]),
                    )
                ]
            )
            plot_titles.append("Test Fail report")
            plots.append(fig)
            remarks.append("")

        # Plot data
        motion_data = motion_data.loc[(motion_data["EgoMotionPort_uiTimeStamp"] != 0)].drop_duplicates()
        vedodo_data = vedodo_data.loc[(vedodo_data["vedodo_timestamp_us"] != 0)].drop_duplicates()
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=motion_data["EgoMotionPort_uiTimeStamp"],
                y=motion_data["EgoMotionPort_frontWheelAngle_rad"],
                name="Output",
            )
        )
        fig.add_vrect(
            x0=motion_data["EgoMotionPort_uiTimeStamp"].iat[0], x1=lsmo_closest_ts, fillcolor="#BBDEFB", layer="below"
        )
        fig.add_vrect(
            x0=processing_end_ts,
            x1=motion_data["EgoMotionPort_uiTimeStamp"].iat[-1],
            fillcolor="#BBDEFB",
            layer="below",
        )
        fig.add_trace(
            go.Scatter(
                x=vedodo_data["vedodo_timestamp_us"], y=vedodo_data["vedodo_signalState"], name="IN signal state"
            )
        )
        plots.append(fig)
        plot_titles.append("Signal state EM data")
        remarks.append("")

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


@testcase_definition(
    name="CEM-LSMO Al Signal State",
    description="This test case checks if LSMO only processes input signals if their signal state is AL_SIG_STATE_OK",
)
class FtLSMOAlSignalState(TestCase):
    """CEM-LSMO Al Signal State Test Case"""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtLSMOAlSignalState]


@teststep_definition(
    step_number=1,
    name="CEM-LSMO Output reset",
    description="This test case checks if an Init request received, LSMO shall reset its outputs"
    "and its internal states to the default initialized values and states.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtLSMOReset(TestStep):
    """TestStep for resetting LSMO module, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        data_df = reader.as_plain_df

        motion_data = data_df.filter(regex="EgoMotionPort_")

        # Find ts where signal state changes from ok to init
        motion_data = motion_data.drop_duplicates()
        motion_data["EgoMotionPort_eSigStatus"] = motion_data["EgoMotionPort_eSigStatus"].astype(float)
        reset_ts = motion_data.loc[
            motion_data["EgoMotionPort_eSigStatus"].diff() == -1, "EgoMotionPort_uiTimeStamp"
        ].min()
        if np.isnan(reset_ts):
            _log.error("No reset foun in data")
            test_result = fc.NOT_ASSESSED

        else:
            # Verify if signal output is in state init after reset
            motion_data.set_index("EgoMotionPort_uiTimeStamp", inplace=True)
            reset_section = motion_data[motion_data.index == reset_ts]
            result_columns = (reset_section == 0).all()

            if result_columns.all():
                test_result = fc.PASS
            else:
                test_result = fc.FAIL
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=result_columns.index.str.split("_").str[1]),
                            cells=dict(values=result_columns.values.tolist()),
                        )
                    ]
                )
                plot_titles.append("Test Fail report Output Signal in Init state")
                plots.append(fig)
                remarks.append("")

            # Plot data
            motion_data = motion_data.loc[(motion_data.index != 0)].drop_duplicates()
            fig = px.line(motion_data, x=motion_data.index, y=motion_data.columns)
            fig.add_vrect(x0=reset_ts, x1=motion_data.index.max(), fillcolor="#F5F5F5", layer="below")
            plots.append(fig)
            plot_titles.append("Output signal values")
            remarks.append("")

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


@testcase_definition(
    name="CEM-LSMO Output reset",
    description="This test case checks if an Init request received, LSMO shall reset its outputs"
    "and its internal states to the default initialized values and states.",
)
class FtLSMOReset(TestCase):
    """CEM-LSMO Output reset Test Case"""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtLSMOReset]


@teststep_definition(
    step_number=1,
    name="CEM-LSMO Latency Compensation",
    description="LSMO shall provide its signals in the Vehicle coordinate system at T7",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtLSMOOutputAtT7(TestStep):
    """TestStep for LSMO output at T7, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        data_df = reader.as_plain_df

        motion_data = data_df[["EgoMotionPort_uiTimeStamp"]]
        motion_data = motion_data.rename(columns={"EgoMotionPort_uiTimeStamp": "timestamp"})

        t7_data = data_df[["vedodo_timestamp_us"]]

        # Compute the estimated time at T7
        t7_data["timestamp"] = t7_data["vedodo_timestamp_us"] + (ConstantsCem.CYCLE_PERIOD_TIME_MS * 1e3)

        # Check if data has been provided to continue with the validation
        if len(motion_data.timestamp) or len(t7_data.timestamp):

            # Check that every timestamp that is present in the TPF output is matching the one provided by T7.
            if motion_data.timestamp.equals(t7_data.timestamp):
                test_result = fc.PASS
            # Otherwise test will fail
            else:
                # Create a detailed table to show timeframe failing and the corresponding values
                test_result = fc.FAIL
                matching_data = pd.DataFrame(motion_data.timestamp == t7_data.timestamp)
                failed_cycles = matching_data.loc[~matching_data.timestamp].index
                lsmo_failing = motion_data.filter(items=failed_cycles, axis=0).timestamp
                t7_failing = t7_data.filter(items=failed_cycles, axis=0).timestamp
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Cycle count", "LSMO output", "T7 timestamp"]),
                            cells=dict(values=[failed_cycles, lsmo_failing, t7_failing]),
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
                        x=motion_data.index,
                        y=(motion_data.timestamp - t7_data.timestamp) / 1e3,
                        mode="lines",
                        name="Offset",
                    )
                ]
            )

            plot_titles.append("LSMO timestamp offset ms")
            plots.append(fig)
            remarks.append("")

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


@testcase_definition(
    name="CEM-LSMO Latency Compensation",
    description="LSMO shall provide its signals in the Vehicle coordinate system at T7",
)
class FtLSMOOutputAtT7(TestCase):
    """CEM-LSMO Latency Compensation Test Case"""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtLSMOOutputAtT7]
