"""Functional test for lateral error"""

import logging
import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, calc_table_height
from pl_parking.PLP.MF.constants import GeneralConstants, LateralErrorConstants, ParkingModes, PlotlyTemplate

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


SIGNAL_DATA = "MF_LATERAL_ERROR"
signal_obj = fh.MfSignals()


class StoreStepResults:
    """Initializes variables for multiple steps and provides a method
    to check their status and return corresponding results and color codes.
    """

    def __init__(self):
        """Initialize object attributes."""
        self.step_1 = fc.INPUT_MISSING
        self.step_2 = fc.INPUT_MISSING
        self.step_3 = fc.INPUT_MISSING

    def check_result(self):
        """
        The function `check_result` checks the status of multiple steps and returns a corresponding result and color code.
        :return: The `check_result` method is returning a tuple with two values. The first value is one of the constants
        `fc.PASS`, `fc.INPUT_MISSING`, `fc.NOT_ASSESSED`, or `fc.FAIL` based on the conditions checked in the method. The
        second value is a color code represented as a string.
        """
        if self.step_1 == fc.PASS and self.step_2 == fc.PASS and self.step_3 == fc.PASS:
            return fc.PASS, "#28a745"
        elif self.step_1 == fc.INPUT_MISSING or self.step_2 == fc.INPUT_MISSING or self.step_3 == fc.INPUT_MISSING:
            return fc.INPUT_MISSING, "rgb(33,39,43)"
        else:
            return fc.FAIL, "#dc3545"


verdict_obj = StoreStepResults()


@teststep_definition(
    step_number=1,
    name="Lateral Error",
    description=(
        "Check if the maximum absolute value was found for the signal        "
        " M7board.CAN_Thread.trajCtrlDebugPort.currentDeviation_m during the PARK_IN(1) or PARK_OUT(2) maneuver."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, fh.MfSignals)
class Step1(TestStep):
    """Test step class"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        df = self.readers[SIGNAL_DATA].signals
        signal_name = signal_obj._properties
        eval_cond = [False] * 3
        prk_mode_list = []
        self.test_result = fc.INPUT_MISSING
        verdict_color = "rgb(33,39,43)"  # fc.InputMissing
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        sg_lateral_error = "LateralError"
        sg_ppc_parking_mode = "ppcParkingMode"

        time = df[fh.MfSignals.Columns.TIME]

        ppc_parking_mode = df[fh.MfSignals.Columns.PPCPARKINGMODE]
        lat_error_m = df[fh.MfSignals.Columns.LATERALERROR].to_numpy()

        parking_mode_in_mask = ppc_parking_mode == ParkingModes.PARK_IN
        parking_mode_out_mask = ppc_parking_mode == ParkingModes.PARK_OUT
        parking_in_out_mask = parking_mode_in_mask | parking_mode_out_mask
        lat_error_filtered = lat_error_m[parking_in_out_mask]

        if len(lat_error_filtered) == 0:
            max_lat_error_cm = 0
        else:
            max_lat_error_m = np.abs(lat_error_filtered).max()
            max_lat_error_cm = max_lat_error_m * LateralErrorConstants.M_TO_CM_COEF

        if any(ppc_parking_mode == ParkingModes.PARK_IN):
            prk_mode_list.append(f"PARK_IN({ParkingModes.PARK_IN})")
        if any(ppc_parking_mode == ParkingModes.PARK_OUT):
            prk_mode_list.append(f"PARK_OUT({ParkingModes.PARK_OUT})")

        prk_mode_list = " and ".join(prk_mode_list)

        cond_0 = " ".join(
            f"The mode PARK_IN({ParkingModes.PARK_IN}) or                 PARK_OUT({ParkingModes.PARK_OUT}) should be"
            f" found at least once in signal                 {signal_name[sg_ppc_parking_mode]}.".split()
        )

        cond_2 = " ".join(
            f"The values from signal {signal_name[sg_lateral_error]} should not             exceed the"
            f" threshold({LateralErrorConstants.THRESHOLD} cm).".split()
        )

        if parking_in_out_mask.any():
            eval_cond[0] = True

        if max_lat_error_cm < LateralErrorConstants.THRESHOLD:
            eval_cond[2] = True
            self.test_result = fc.PASS
            verdict_color = "#28a745"
            self.result.measured_result = TRUE

        else:
            self.test_result = fc.FAIL
            verdict_color = "#dc3545"
            self.result.measured_result = FALSE

        # Set table dataframe
        signal_summary = pd.DataFrame(
            {
                "Condition": {
                    "0": cond_0,
                    "1": cond_2,
                },
                "Result": {
                    "0": (
                        " ".join(f"Parking modes found: {prk_mode_list}.".split())
                        if eval_cond[0]
                        else " ".join("No parking mode was found.".split())
                    ),
                    "1": (
                        " ".join("Values did not exceed the threshold.".split())
                        if eval_cond[2]
                        else " ".join(
                            f"The threshold was exceeded with value: {round(max_lat_error_cm,3)}                           "
                            "      cm.".split()
                        )
                    ),  # to add also the timestamp
                },
                "Verdict": {
                    "0": "PASSED" if eval_cond[0] else "ACCEPTABLE",
                    "1": "PASSED" if eval_cond[2] else "FAILED",
                },
            }
        )

        # Create table with eval conditions from the summary dict
        sig_sum = go.Figure(
            data=[
                go.Table(
                    columnwidth=[50, 20, 7],
                    header=dict(
                        values=list(signal_summary.columns),
                        fill_color="rgb(255,165,0)",
                        font=dict(size=12, family="Arial", color="rgb(0,0,0)"),
                        align="center",
                    ),
                    cells=dict(
                        values=[signal_summary[col] for col in signal_summary.columns],
                        height=40,
                        align="center",
                        font=dict(size=12),
                    ),
                )
            ]
        )
        sig_sum.update_layout(PlotlyTemplate.lgt_tmplt, height=calc_table_height(signal_summary["Condition"].to_dict()))
        plot_titles.append("Condition Evaluation")
        plots.append(sig_sum)
        remarks.append("")

        if self.test_result == fc.FAIL or bool(GeneralConstants.ACTIVATE_PLOTS):
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=time.tolist(),
                    y=df[fh.MfSignals.Columns.LATERALERROR].values.tolist(),
                    mode="lines",
                    name=f"AP{signal_obj._properties[fh.MfSignals.Columns.LATERALERROR]}",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=time.tolist(),
                    y=df[fh.MfSignals.Columns.PPCPARKINGMODE].values.tolist(),
                    mode="lines",
                    name=f"AP{signal_obj._properties[fh.MfSignals.Columns.PPCPARKINGMODE]}",
                )
            )

            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("Graphical overview")
            plots.append(fig)
            remarks.append("Lateral Error")

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        additional_results_dict = {
            "Verdict": {"value": self.test_result.title(), "color": verdict_color},
            "Expected [cm]": {"value": f"< {LateralErrorConstants.THRESHOLD:.1f}"},  # , "color": 'rgba(0,0,0,0)'},
            "Measured [cm]": {"value": f"{max_lat_error_cm:.2f}"},  # , "color": 'rgba(0,0,0,0)'},
        }
        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="MF LATERAL ERROR",
    description=(
        "Check if the maximum absolute value was found for the signal        "
        " M7board.CAN_Thread.trajCtrlDebugPort.currentDeviation_m during the PARK_IN(1) or PARK_OUT(2) maneuver."
    ),
)
class LateralErrorMf(TestCase):
    """Test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            Step1,
        ]
