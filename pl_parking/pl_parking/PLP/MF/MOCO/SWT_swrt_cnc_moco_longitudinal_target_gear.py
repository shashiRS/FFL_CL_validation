"""moco longitudinal target gear"""

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

ALIAS = "SWT_swrt_cnc_moco_longitudinal_target_gear"

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
            try:
                df = self.readers[ALIAS].signals
            except Exception as e:
                print(str(e))
                df = self.readers[ALIAS]

            assertion_dict = {}
            df["calculated_standstill"] = df.apply(
                lambda row: is_vehicle_in_standstill(
                    row["standstillHoldCur_nu"], row["standstillSecureCur_nu"], row["motionStatus_nu"]
                ),
                axis=1,
            )

            df["calculated_target_gear"] = df.apply(evaluate_target_gear, axis=1)
            df["calculated_standstill"] = df["calculated_standstill"].map({True: 1, False: 0})

            "TestStep"
            "Filter data by longitudinal control request"
            df_filtered = df[(df["activateLoCtrl"] == 1)]

            "Check precondition for all target gears"
            if check_target_gear(df_filtered) and not df_filtered.empty:
                df_filtered["calculated_hold_req"] = (
                    df_filtered["calculated_target_gear"] != df_filtered["gearCur_nu"]
                ).astype(int)

                cycles_evaluated = df_filtered.loc[df_filtered["calculated_hold_req"] == 1]
                for _, hold_req_row in cycles_evaluated.iterrows():
                    if hold_req_row["calculated_hold_req"] != hold_req_row["holdReq_nu"]:
                        assertion_dict[_] = hold_req_row["holdReq_nu"]
                if assertion_dict:
                    self.result.measured_result = FALSE
                    test_result = fc.FAIL
                    eval_text = " ".join(
                        f"The component doesnt sends a request to stop and hold ('holdReq_nu')in standstill in case"
                        f" when the applied gear is not equal to the target gear"
                        f" Conditions: {test_result}.".split()
                    )

                else:
                    self.result.measured_result = TRUE
                    test_result = fc.PASS
                    eval_text = " ".join(
                        f"The component sends a request to stop and hold in standstill in case"
                        f" when the applied gear is not equal to the target gear"
                        f" Conditions: {test_result}.".split()
                    )

                eval_0 = " ".join(
                    " Ensure that the component sends a request to stop and hold in standstill in case"
                    " if the applied gear is not equal to the target gear.".split()
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

                fig = get_plot_signals(df_filtered)
                fig.add_trace(
                    go.Scatter(
                        x=df_filtered.index.values.tolist(),
                        y=df_filtered["calculated_hold_req"].values.tolist(),
                        mode="lines",
                        name="calculated_hold_req",
                    )
                )

                plot_titles.append("Graphical Overview")
                plots.append(fig)
                remarks.append("")

                additional_results_dict = {
                    "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)}
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
                eval_text = "Longitudinal control request not active"
                self.result.measured_result = NAN

                eval_0 = " ".join(
                    " Ensure that the component sends a request to stop and hold in standstill in case"
                    " if the applied gear is not equal to the target gear.".split()
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
            y=df["calculated_standstill"].values.tolist(),
            mode="lines",
            name="calculated_standstill",
        )
    )
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
            y=df["holdReq_nu"].values.tolist(),
            mode="lines",
            name="holdReq_nu",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["loCtrlRequestType"].values.tolist(),
            mode="lines",
            name="loCtrlRequestType",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["trajValid_nu"].values.tolist(),
            mode="lines",
            name="trajValid_nu",
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
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["secureInStandstill"].values.tolist(),
            mode="lines",
            name="secureInStandstill",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["comfortStopRequest"].values.tolist(),
            mode="lines",
            name="comfortStopRequest",
        )
    )

    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="MTS.Package.Timestamp"
    )
    fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
    return fig


@verifies("1407045")
@testcase_definition(
    name="MOCO Longitudinal Target Gear",
    description="Ensure that the component sends a request to stop and hold in standstill in case of "
    "the applied gear is not equal to the target gear",
    group="gearbox",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class SWT_swrt_cnc_moco_longitudinal_target_gear(TestCase):
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
        SWT_swrt_cnc_moco_longitudinal_target_gear,
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
