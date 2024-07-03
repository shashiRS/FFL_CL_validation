#!/usr/bin/env python3
"""Max ego yaw rate TestCase."""

import logging
import os
import sys

import pandas as pd
import plotly.graph_objects as go

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", "..", ".."))  # nopep8
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)  # nopep8
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
import pl_parking.PLP.MF.constants as constants  # nopep8
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

SIGNAL_DATA = "EGO_YAW_RATE"
signal_obj = fh.MfSignals()


@teststep_definition(
    step_number=1,
    name="Max Ego Yaw rate",
    description=(
        "Absolute yaw rate of the ego vehicle during parking manoeuver must be <"
        f" {constants.ConstantsMaxEgoYawRate.THRESHOLD} rad/s."
    ),
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
        sg_ego_yaw_rate = "yawRate_radps"
        sg_parksm_cor_status = "ParkSmCoreStatus"

        df = self.readers[SIGNAL_DATA].signals
        signal_name = signal_obj._properties
        eval_cond = [False] * 2

        parking_mask = None
        yaw_rate = None
        self.test_result = fc.INPUT_MISSING
        verdict_color = "rgb(33,39,43)"  # fc.InputMissing
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        time = df[fh.MfSignals.Columns.TIME]

        park_state = df[sg_parksm_cor_status]
        yaw_rate = df[sg_ego_yaw_rate]
        parking_mask = park_state == constants.ParkSmCoreStatus.PERFORM_PARKING

        yaw_rate_filtered = yaw_rate * parking_mask

        max_yaw_rate_radps = yaw_rate_filtered.abs().max()

        if parking_mask.any():
            eval_cond[0] = True
        if max_yaw_rate_radps < constants.ConstantsMaxEgoYawRate.THRESHOLD:
            eval_cond[1] = True

        if all(eval_cond):
            self.test_result = fc.PASS
            verdict_color = "#28a745"
            self.result.measured_result = TRUE
        else:
            self.test_result = fc.FAIL
            verdict_color = "#dc3545"
            self.result.measured_result = FALSE
        # self.result.measured_result = Result(max_yaw_rate_radps, unit='radps')

        # Set condition strings
        cond_0 = " ".join(
            f"The signal {signal_name[sg_parksm_cor_status]} should contain values of PERFORM_PARKING           "
            f" ({constants.ParkSmCoreStatus.PERFORM_PARKING}).".split()
        )

        cond_1 = " ".join(
            f"Maximum value for signal {signal_name[sg_ego_yaw_rate]} during parking             should be <"
            f" {constants.ConstantsMaxEgoYawRate.THRESHOLD} rad/s.".split()
        )

        # # Set table dataframe
        signal_summary = pd.DataFrame(
            {
                "Condition": {
                    "0": cond_0,
                    "1": cond_1,
                },
                "Result": {
                    "0": (
                        " ".join(
                            f"Parking status was set to PERFORM_PARKING({constants.ParkSmCoreStatus.PERFORM_PARKING}).".split()
                        )
                        if eval_cond[0]
                        else " ".join(
                            "Parking status was not set to                    "
                            f" PERFORM_PARKING({constants.ParkSmCoreStatus.PERFORM_PARKING}).".split()
                        )
                    ),
                    "1": " ".join(f"Maximum value was = {max_yaw_rate_radps:.2f}  rad/s.".split()),
                },
                "Verdict": {
                    "0": "PASSED" if eval_cond[0] else "FAILED",
                    "1": "PASSED" if eval_cond[1] else "FAILED",
                },
            }
        )
        # Set table dataframe
        sig_sum = fh.build_html_table(signal_summary, table_remark="TEXT")

        plot_titles.append("Condition Evaluation")
        self.result.details["Plots"].append(sig_sum)
        # plots.append(sig_sum)
        remarks.append("")

        if self.test_result == fc.FAIL or bool(constants.GeneralConstants.ACTIVATE_PLOTS):
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=time.tolist(),
                    y=df[sg_parksm_cor_status].values.tolist(),
                    mode="lines",
                    name=signal_name[sg_parksm_cor_status],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time.tolist(),
                    y=df[sg_ego_yaw_rate].abs().values.tolist(),
                    mode="lines",
                    name=f"{signal_name[sg_ego_yaw_rate]} absolute values",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time.tolist(),
                    y=df[sg_ego_yaw_rate].values.tolist(),
                    mode="lines",
                    name=f"{signal_name[sg_ego_yaw_rate]}",
                )
            )

            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            plot_titles.append("Graphical overview")
            # plots.append(fig)
            self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))
            remarks.append("Max Ego Yaw Rate")

        # for plot in plots:
        #     self.result.details["Plots"].append(
        #         plot.to_html(full_html=False, include_plotlyjs=False))
        # self.result.details["Plots"].append(s)
        # plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        additional_results_dict = {
            "Verdict": {"value": self.test_result.title(), "color": verdict_color},
            "Expected [rad/s]": {"value": f"< {constants.ConstantsMaxEgoYawRate.THRESHOLD}"},
            "Measured [rad/s]": {"value": f"{max_yaw_rate_radps:.2f}"},
        }
        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="MF MAXIMUM EGO YAW RATE",
    description=(
        "Absolute yaw rate of the ego vehicle during parking manoeuver must be <"
        f" {constants.ConstantsMaxEgoYawRate.THRESHOLD} rad/s."
    ),
)
class MaxEgoYawRate(TestCase):
    """Max Ego Yaw Rate test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step1,
        ]
