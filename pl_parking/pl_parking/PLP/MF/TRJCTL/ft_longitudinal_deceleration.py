#!/usr/bin/env python3
"""Max longitudinal deceleration TestCase."""

import logging
import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", "..", ".."))  # nopep8
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
from tsf.core.results import FALSE, TRUE, BooleanResult  # nopep8
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, calc_table_height

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


SIGNAL_DATA = "LONGITUDINAL_DECCELERATION"
signal_obj = fh.MfSignals()


@teststep_definition(
    step_number=1,
    name="Longitudinal Deceleration",
    description="Check if during PARK_IN or PARK_OUT manuever longitudinal acceleration does not go above 1.5m/s^2.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, fh.MfSignals)
class Step1(TestStep):
    """Test Step definition."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self, **kwargs):
        """Process the test result."""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        sg_longi_acceleration = "longitudinalAcceleration_mps2"
        sg_emergency_brake = "EbaActive"
        sg_parksm_cor_status = "ParkSmCoreStatus"
        df = self.readers[SIGNAL_DATA].signals
        signal_name = signal_obj._properties
        eval_cond = [False] * 3

        self.test_result = fc.INPUT_MISSING
        verdict_color = "rgb(33,39,43)"  # fc.InputMissing
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        eval_cond = [False] * 4

        perform_parking_mask = None
        deceleration_mask = None
        emergency_break_mask = None

        time = df[fh.MfSignals.Columns.TIME]

        longitudinal_acceleration = df[fh.MfSignals.Columns.LONGITUDINALACCELERATION_MPS2]
        emergency_break = df[fh.MfSignals.Columns.EBAACTIVE]

        parking_mode = df[fh.MfSignals.Columns.PARKSMCORESTATUS]
        perform_parking_mask = parking_mode == constants.ParkCoreStatus.CORE_PARKING

        deceleration_mask = longitudinal_acceleration >= constants.ConstantsMaxLongiDeceleration.THRESHOLD_MAX_LONG_ACC
        emergency_break_mask = emergency_break == 0

        emergency_filtered = perform_parking_mask & emergency_break_mask

        if emergency_filtered.any():
            eval_cond[0] = True
            eval_cond[2] = True
            if not deceleration_mask.any():
                eval_cond[1] = True
                self.test_result = fc.PASS
                verdict_color = "#28a745"
                self.result.measured_result = TRUE
            else:
                self.test_result = fc.FAIL
                verdict_color = "#dc3545"
                self.result.measured_result = FALSE
        else:
            self.test_result = fc.INPUT_MISSING
            self.result.measured_result = FALSE

        # Set condition strings
        cond_0 = " ".join(
            f"The values for signal {signal_name[sg_parksm_cor_status]} should be set to            "
            f" CORE_PARKING({constants.ParkCoreStatus.CORE_PARKING}).".split()
        )
        cond_1 = " ".join(
            "Longitudinal acceleration should be < threshold           "
            f" ({constants.ConstantsMaxLongiDeceleration.THRESHOLD_MAX_LONG_ACC} mps2) in signal            "
            f" {signal_name[sg_longi_acceleration]} while the state is set to CORE_PARKING(2).".split()
        )
        cond_2 = " ".join(
            f"{signal_name[sg_emergency_brake]} should not be active during the state of CORE_PARKING(2) ".split()
        )

        # Set table dataframe
        signal_summary = pd.DataFrame(
            {
                "Condition": {
                    "0": cond_0,
                    "1": cond_1,
                    "2": cond_2,
                },
                "Result": {
                    "0": (
                        " ".join(f"The status CORE_PARKING({constants.ParkCoreStatus.CORE_PARKING}) was found.".split())
                        if eval_cond[0]
                        else " ".join(
                            f"The status                     CORE_PARKING({constants.ParkCoreStatus.CORE_PARKING}) was"
                            " not found.".split()
                        )
                    ),
                    "1": " ".join(
                        "The maximum value of acceleration =                        "
                        f" {np.max(longitudinal_acceleration):.2f} mps2.".split()
                    ),
                    "2": (
                        " ".join(
                            "The values for Emergency brake while status was set to CORE_PARKING are != 0.".split()
                        )
                        if eval_cond[2]
                        else " ".join(
                            "There were no emergency brakes while the status was set to CORE_PARKING                   "
                            "      (values were = 0)".split()
                        )
                    ),
                },
                "Verdict": {
                    "0": "PASSED" if eval_cond[0] else "ACCEPTABLE",
                    "1": "PASSED" if eval_cond[1] else "FAIL",
                    "2": "PASSED" if eval_cond[2] else "ACCEPTABLE",
                },
            }
        )

        # Create table with eval conditions from the summary dict
        sig_sum = go.Figure(
            data=[
                go.Table(
                    columnwidth=[5, 2],
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
        sig_sum.update_layout(
            constants.PlotlyTemplate.lgt_tmplt, height=calc_table_height(signal_summary["Condition"].to_dict())
        )
        plot_titles.append("Condition Evaluation")
        plots.append(sig_sum)
        remarks.append("")

        if self.test_result == fc.FAIL or bool(constants.GeneralConstants.ACTIVATE_PLOTS):
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=time.tolist(),
                    y=df[sg_emergency_brake].values.tolist(),
                    mode="lines",
                    name=signal_name[sg_emergency_brake],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time.tolist(),
                    y=df[sg_longi_acceleration].values.tolist(),
                    mode="lines",
                    name=f"{signal_name[sg_longi_acceleration]}",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time.tolist(),
                    y=df[sg_parksm_cor_status].values.tolist(),
                    mode="lines",
                    name=f"{signal_name[sg_parksm_cor_status]}",
                )
            )

            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            plot_titles.append("Graphical overview")
            plots.append(fig)
            remarks.append("")

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)
        additional_results_dict = {}
        if emergency_filtered.any():
            additional_results_dict = {
                "Verdict": {"value": self.test_result.title(), "color": verdict_color},
                "Expected [mps2]": {"value": "< 1.5"},
                "Measured [mps2]": {"value": f"{np.max(longitudinal_acceleration):.2f}"},
            }
        else:
            additional_results_dict = {
                "Verdict": {"value": self.test_result.title(), "color": verdict_color},
                "Expected [mps2]": {"value": "< 1.5"},
                "Measured [mps2]": {"value": "Could not be calculated. There was no occurrence of an emergency brake."},
            }
        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="MF LONGITUDINAL DECELERATION",
    description="Check if during PARK_IN or PARK_OUT manuever longitudinal acceleration does not go above 1.5m/s^2.",
)
class LongitudinalDeceleration(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step1,
        ]
