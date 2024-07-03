#!/usr/bin/env python3
"""Testcase example"""
import logging
import os
import sys

import pandas as pd
import plotly.graph_objects as go
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.1"
__status__ = "Development"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ALIAS = "Test_example"

""" Steps required to create a new test case:

1. Define required signals in the Signals class


"""


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        # Here you define your signals column name. It will be used to access the required data from the dataframe
        xTrajRAReq_m = "xTrajRAReq_m"
        xTrajRAReq_ = "xTrajRAReq_{}"
        VELOCITY = "Velocity"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()
        # You can split your signals to have a base string and a 'tail' string
        # If you do not define correctly the signals here, the reader will not add them to the dataframe
        # Due to the current situation where we can not read .csv files, we will use a .rrec file and define some
        # signals in order for the evaluation to start
        # After that, we will manually read the .csv file where the data is. In the future erg files will be used, so this is just temporary

        self._root = [
            "ADC5xx_Device",
        ]

        self._properties = {
            # self.Columns.xTrajRAReq_m: "ADC5xx_Device.VD_DATA.IuTrajRequestPort.plannedTraj[0].xTrajRAReq_m",
            self.Columns.VELOCITY: ".EM_DATA.EmEgoMotionPort.vel_mps",
        }


signals_obj = Signals()


@teststep_definition(step_number=1, name="KPI", description=" ", expected_result=BooleanResult(TRUE))
@register_signals(ALIAS, Signals)
class Step1(TestStep):
    """general signal status test step"""

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

            # try:
            #     df = self.readers[ALIAS].signals
            # except Exception as e:
            #     print(str(e))
            #     df = self.readers[ALIAS]

            # TODO temporary solution for extracting data from csf
            # future implementation will use ERG files
            df_from_csv = pd.read_csv(
                r"D:\MOCO\mf_trjctl\tests\algotest\functional_testcases\data\observed\exported_file__D2023_10_31_T08_10_22.csv"
            )

            activateLaCtrl = "ADC5xx_Device.VD_DATA.IuLaCtrlRequestPort.activateLaCtrl"
            laDMCCtrlRequest_nu = "ADC5xx_Device.VD_DATA.IuLaDMCCtrlRequestPort.laDMCCtrlRequest_nu"

            df_from_csv["match"] = (df_from_csv[activateLaCtrl] == 1) & (df_from_csv[laDMCCtrlRequest_nu] == 1)

            total = df_from_csv[(df_from_csv[activateLaCtrl] == 1) | (df_from_csv[laDMCCtrlRequest_nu] == 1)].shape[0]
            match = df_from_csv["match"].sum()
            percent_match = (match / total) * 100 if total > 0 else 0

            if percent_match == 100:
                observed_la_dmc_ctrl_request_nu = TRUE
                test_result = fc.PASS
            else:
                observed_la_dmc_ctrl_request_nu = FALSE
                test_result = fc.FAIL

            self.result.measured_result = observed_la_dmc_ctrl_request_nu
            eval_0 = " ".join(
                f"Signal activations for  {activateLaCtrl} and {laDMCCtrlRequest_nu} should match 100%.".split()
            )

            # Set table dataframe
            signal_summary = pd.DataFrame(
                {
                    "Evaluation": {
                        "1": eval_0,
                    },
                    "Result": {
                        "1": f"Signals matched in proportion of {percent_match} %",
                    },
                }
            )

            sig_sum = fh.build_html_table(signal_summary)
            fig = go.Figure()
            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append("")

            fig.add_trace(
                go.Scatter(
                    x=df_from_csv.index.values.tolist(),
                    y=df_from_csv[activateLaCtrl].values.tolist(),
                    mode="lines",
                    name=activateLaCtrl,
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df_from_csv.index.values.tolist(),
                    y=df_from_csv[laDMCCtrlRequest_nu].values.tolist(),
                    mode="lines",
                    name=laDMCCtrlRequest_nu,
                )
            )

            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="MTS.Package.Timestamp"
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plot_titles.append("Graphical Overview")
            plots.append(fig)
            remarks.append("")

            additional_results_dict = {
                "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                "Percent match [%]": {"value": percent_match},
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


@verifies("1406994")
@testcase_definition(
    name="MOCO Lateral active control",
    description="Ensure that the component activates lateral control when the request input is set to true.",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class SWT_swrt_cnc_moco_lateral_active_control(TestCase):
    """Example test case."""

    custom_report = fh.MOCOCustomTestCase

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            Step1,
        ]
