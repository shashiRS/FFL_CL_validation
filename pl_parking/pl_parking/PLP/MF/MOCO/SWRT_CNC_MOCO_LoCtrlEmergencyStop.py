"""moco longitudinal control emergency stop"""

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

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.1"
__status__ = "Development"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ALIAS = "SWRT_CNC_MOCO_LoCtrlEmergencyStop"

""" Steps required to create a new test case:

1. Define required signals in the Signals class


"""


signals_obj = MoCoSignals()


@teststep_definition(step_number=1, name="KPI", description=" ", expected_result=BooleanResult(TRUE))
@register_signals(ALIAS, MoCoSignals)
class Step1(TestStep):
    """moco longitudinal control emergency stop test setup"""

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

            "TestStep"
            "Filter data by longitudinal control request and emergency stop request"
            df_filtered = df[
                (df["activateLoCtrl"] == 1)
                & (df["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_EMERGENCY_STOP)
            ]
            passed = []
            "Checking for emergency hold request at the request port"
            if not df_filtered.empty:
                for _, _ in df_filtered.iterrows():
                    if df_filtered["emergencyHoldReq_nu"].bool:
                        passed.append(True)
                    else:
                        passed.append(False)
                if all(passed):
                    self.result.measured_result = TRUE
                    test_result = fc.PASS
                    eval_text = " ".join(
                        f"Component input loCtrlRequestPort.loCtrlRequestType is set to LOCTRL_EMERGENCY_STOP({constants.MoCo.LoCtrlRequestType.LOCTRL_EMERGENCY_STOP}) ,ensure "
                        f"that the component shall perform operation mode emergency stop and output an emergency stop request by setting loDMCCtrlRequestPort.emergencyHoldReq_nu= true"
                        f" Conditions: {test_result}.".split()
                    )

                else:
                    self.result.measured_result = FALSE
                    test_result = fc.FAIL
                    eval_text = " ".join(
                        f"Component input loCtrlRequestPort.loCtrlRequestType is set to LOCTRL_EMERGENCY_STOP({constants.MoCo.LoCtrlRequestType.LOCTRL_EMERGENCY_STOP}),emergency stop request is not set"
                        f" Conditions: {test_result}.".split()
                    )

                eval_0 = " ".join(
                    f" If component input loCtrlRequestPort.loCtrlRequestType is set to LOCTRL_EMERGENCY_STOP({constants.MoCo.LoCtrlRequestType.LOCTRL_EMERGENCY_STOP}) ,ensure "
                    f"that the component shall perform operation mode emergency stop and output an"
                    f" emergency stop request by setting loDMCCtrlRequestPort.emergencyHoldReq_nu= true.".split()
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

                fig = get_plot_signals(df)
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
                eval_text = "No emergency stop request"
                self.result.measured_result = NAN

                eval_0 = " ".join(
                    f" If component input loCtrlRequestPort.loCtrlRequestType is set to LOCTRL_EMERGENCY_STOP({constants.MoCo.LoCtrlRequestType.LOCTRL_EMERGENCY_STOP}) ,ensure "
                    f"that the component shall perform operation mode emergency stop and output an"
                    f" emergency stop request by setting loDMCCtrlRequestPort.emergencyHoldReq_nu= true.".split()
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
            y=df["activateLoCtrl"].values.tolist(),
            mode="lines",
            name="activateLoCtrl",
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
            y=df["emergencyHoldReq_nu"].values.tolist(),
            mode="lines",
            name="emergencyHoldReq_nu",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[df.index.values.min(), df.index.values.max()],
            y=[
                constants.MoCo.LoCtrlRequestType.LOCTRL_EMERGENCY_STOP,
                constants.MoCo.LoCtrlRequestType.LOCTRL_EMERGENCY_STOP,
            ],
            mode="lines",
            name="LOCTRL_EMERGENCY_STOP",
            visible="legendonly",
        )
    )

    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="MTS.Package.Timestamp"
    )
    fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
    return fig


@tag("SWRT_CNC_MOCO_LoCtrlEmergencyStop")
@verifies("1407122")
@testcase_definition(
    name="MOCO LoCtrlEmergencyStop",
    description="If the component input loCtrlRequestPort.loCtrlRequestType is set to LOCTRL_EMERGENCY_STOP (7) ,ensure that the component "
    "shall perform operation mode emergency stop and output an emergency stop request by setting "
    "loDMCCtrlRequestPort.emergencyHoldReq_nu= true.",
    group="emergency stop",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SWRT_CNC_MOCO_LoCtrlEmergencyStop(TestCase):
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
        SWRT_CNC_MOCO_LoCtrlEmergencyStop,
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
