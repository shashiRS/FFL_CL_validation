"""moco gearbox ctrl request port"""

#!/usr/bin/env python3

import logging
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from tsf.core.results import FALSE, NAN, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    tag,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.core.utilities import debug

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MoCoSignals
from pl_parking.PLP.MF.MOCO.helpers import (
    check_target_gear,
    evaluate_target_gear,
    is_vehicle_in_standstill,
)

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.1"
__status__ = "Development"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ALIAS = "SWRT_CNC_MOCO_GearboxCtrlRequestPortGearReqNu"

""" Steps required to create a new test case:

1. Define required signals in the Signals class


"""


signals_obj = MoCoSignals()


@teststep_definition(step_number=1, name="KPI", description=" ", expected_result=BooleanResult(TRUE))
@register_signals(ALIAS, MoCoSignals)
class Step1(TestStep):
    """moco longitudinal target gear test setup"""

    custom_report = fh.MOCOCustomTeststepReport

    def __init__(self):
        """Initialsie the test step"""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")

        try:
            self.result.details.update(
                {
                    "Plots": [],
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            plot_titles, plots, remarks = fh.rep([], 3)
            test_result = fc.INPUT_MISSING
            self.result.measured_result = NAN
            df = self.readers[ALIAS]

            df["calculated_standstill"] = df.apply(
                lambda row: is_vehicle_in_standstill(
                    row["standstillHoldCur_nu"], row["standstillSecureCur_nu"], row["motionStatus_nu"]
                ),
                axis=1,
            )
            df["calculated_target_gear"] = df.apply(evaluate_target_gear, axis=1)
            "TestStep"
            "Filter data by longitudinal control request"
            df_filtered = df[(df["activateLoCtrl"] == 1)]
            if not df_filtered.empty:
                # for _, row in df.iterrows():
                #     ego_position = get_ego_position(row)
                #     orthogonal_projection_point = get_orthogonal_projection_point(ego_position, planned_path)
                #     calculated_lateral_deviation = calculate_lateral_deviation(ego_position, orthogonal_projection_point)
                #     calculate_lateral_deviation_list.append(calculated_lateral_deviation)
                #
                # df['calculated_lateral_deviation'] = calculate_lateral_deviation_list
                # are_equal = df['calculated_lateral_deviation'].equals(df['currentDeviation_m'])
                # if not are_equal:
                #     self.result.measured_result = FALSE

                "TestStep"
                "Check if front steer angle is within +/_ AP_V_MAX_STEER_ANG_RAD"

                passed = []

                for _, _ in df_filtered.iterrows():
                    df_filtered["targetGear_equal_appliedGear"] = check_target_gear(df_filtered)
                    if (df_filtered["targetGear_equal_appliedGear"]).bool:
                        if (df_filtered["gearCur_nu"] == df_filtered["gearboxCtrlRequest_nu"]).bool:
                            passed.append(True)
                        else:
                            passed.append(False)
                    else:
                        passed.append(False)
                if all(passed):
                    self.result.measured_result = TRUE
                    test_result = fc.PASS
                    eval_text = " ".join(
                        f"The component sets the gear request equal to target gear. "
                        f"Conditions: {test_result}.".split()
                    )
                else:
                    self.result.measured_result = FALSE
                    test_result = fc.FAIL
                    eval_text = " ".join(
                        f"The component doesnt set the gear request equal to target gear. "
                        f"Conditions: {test_result}.".split()
                    )

                eval_0 = " ".join(
                    " If the component input loCtrlRequestPort.activateLoCtrl is set true then "
                    "the component sets the gear request equal to target gear".split()
                )

                # Set table dataframe
                signal_summary = pd.DataFrame(
                    {
                        "Evaluation": {
                            "1": eval_0,
                        },
                        "Result": {
                            "1": eval_text,
                        },
                    }
                )

                sig_sum = fh.build_html_table(signal_summary)
                plot_titles.append("")
                plots.append(sig_sum)
                remarks.append("")
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=df_filtered.index.values.tolist(),
                        y=df_filtered["calculated_target_gear"].values.tolist(),
                        mode="lines",
                        name="calculated_target_gear",
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=df_filtered.index.values.tolist(),
                        y=df_filtered["activateLoCtrl"].values.tolist(),
                        mode="lines",
                        name="activateLoCtrl",
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["gearCur_nu"].values.tolist(),
                        mode="lines",
                        name="gearCur_nu",
                    )
                )

                # fig = get_plot_signals(df)
                fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
                plot_titles.append("Graphical Overview")
                plots.append(fig)
                remarks.append("")

                additional_results_dict = {
                    "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                }

                for plot in plots:
                    if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                        self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                    else:
                        self.result.details["Plots"].append(plot)
                for plot_title in plot_titles:
                    self.result.details["Plot_titles"].append(plot_title)
                for remark in remarks:
                    self.result.details["Remarks"].append(remark)

                self.result.details["Additional_results"] = additional_results_dict
            else:
                test_result = fc.NOT_ASSESSED
                eval_text = "Target gear condition not satisfied"
                self.result.measured_result = NAN

                eval_0 = " ".join(
                    " If the component input loCtrlRequestPort.activateLoCtrl is set true then "
                    "the component sets the gear request equal to target gear".split()
                )
                # Set table dataframe
                signal_summary = pd.DataFrame(
                    {
                        "Evaluation": {
                            "1": eval_0,
                        },
                        "Result": {
                            "1": eval_text,
                        },
                    }
                )
                sig_sum = fh.build_html_table(signal_summary)

                plot_titles.append("")
                plots.append(sig_sum)
                remarks.append("")

                self.result.details["Step_result"] = test_result
                plot_titles.append("")
                remarks.append("")
                fig = get_plot_signals(df)
                plot_titles.append("Graphical Overview")
                plots.append(fig)
                remarks.append("")
                additional_results_dict = {
                    "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                    "Percent match [%]": {"value": "n/a"},
                }
                for plot in plots:
                    if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                        self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                    else:
                        self.result.details["Plots"].append(plot)
                for plot_title in plot_titles:
                    self.result.details["Plot_titles"].append(plot_title)
                for remark in remarks:
                    self.result.details["Remarks"].append(remark)
                self.result.details["Additional_results"] = additional_results_dict

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


def get_plot_signals(df):
    """Plotting Signals"""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["calculated_target_gear"].values.tolist(),
            mode="lines",
            name="calculated_target_gear",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["gearCur_nu"].values.tolist(),
            mode="lines",
            name="gearCur_nu",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["activateLoCtrl"].values.tolist(),
            mode="lines",
            name="activateLoCtrl",
        )
    )

    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="MTS.Package.Timestamp"
    )
    fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
    return fig


@tag("SWRT_CNC_MOCO_GearboxCtrlRequestPortGearReqNu")
@verifies("1407044")
@testcase_definition(
    name="MOCO Gearbox Ctrl Request Port",
    description="If the component input loCtrlRequestPort.activateLoCtrl is set true,ensure that "
    "the component shall set the gear request (gearboxCtrlRequestPort.gearReq_nu) equal to target gear.",
    group="gearbox",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SWRT_CNC_MOCO_GearboxCtrlRequestPortGearReqNu(TestCase):
    """Example test case."""

    custom_report = fh.MOCOCustomTestCase

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            Step1,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.
    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.
    This is only meant to jump start testcase debugging.
    """
    # Define your directory path to your measurements for debugging purposes
    test_bsigs = [r".\absolute_directory_path_to_your_measurement\file.erg"]
    debug(
        SWRT_CNC_MOCO_GearboxCtrlRequestPortGearReqNu,
        *test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
        kpi_report=False,
        dev_report=True,
    )
    _log.debug("All done.")


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"
    out_folder = working_directory / "out"

    main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)
