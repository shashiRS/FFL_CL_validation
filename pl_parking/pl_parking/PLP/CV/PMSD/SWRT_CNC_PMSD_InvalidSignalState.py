"""Parking Marker Indie ROI Test."""

import logging

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

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

import pandas as pd

TRC_ROOT = os.path.abspath(os.path.join(__file__, "", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import ConstantsCem
from pl_parking.PLP.MF.constants import PlotlyTemplate

SIGNAL_DATA = "PMSD_INVALID_STATE"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD Invalid Signal State",
    description="PMSD shall set INVALID state on its output if any of its input signal's state is AL_SIG_STATE_INVALID.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPMSDInvalidSigStateOk(TestStep):
    """TestStep for PMSD signal state, utilizing a custom report."""

    custom_report = MfCustomTeststepReport

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
        df = reader.as_plain_df

        # Input df
        pmsd_input_data = df[
            [
                "Mecal_CameraExtrinsics_FC_EsigStatus",
                "Mecal_CameraExtrinsics_RC_EsigStatus",
                "Mecal_CameraExtrinsics_LSC_EsigStatus",
                "Mecal_CameraExtrinsics_RSC_EsigStatus",
                "Grappa_FC_DetectionResults_EsigStatus",
                "Grappa_RC_DetectionResults_EsigStatus",
                "Grappa_LSC_DetectionResults_EsigStatus",
                "Grappa_RSC_DetectionResults_EsigStatus",
                "Grappa_FC_Semseg_EsigStatus",
                "Grappa_RC_Semseg_EsigStatus",
                "Grappa_LSC_Semseg_EsigStatus",
                "Grappa_RSC_Semseg_EsigStatus",
                "ParameterHandler_FC_EsigStatus",
                "ParameterHandler_RC_EsigStatus",
                "ParameterHandler_LSC_EsigStatus",
                "ParameterHandler_RSC_EsigStatus",
            ]
        ]
        pmsd_input_data.reset_index(inplace=True, drop=True)

        # Output df
        output_df = df[
            [
                "PMDCamera_Front_eSigStatus",
                "PMDCamera_Rear_eSigStatus",
                "PMDCamera_Left_eSigStatus",
                "PMDCamera_Right_eSigStatus",
                "PMDWs_Front_eSigStatus",
                "PMDWs_Rear_eSigStatus",
                "PMDWs_Left_eSigStatus",
                "PMDWs_Right_eSigStatus",
                "PmsdSlot_Front_eSigStatus",
                "PmsdSlot_Rear_eSigStatus",
                "PmsdSlot_Left_eSigStatus",
                "PmsdSlot_Right_eSigStatus",
                "PMDWl_Front_eSigStatus",
                "PMDWl_Rear_eSigStatus",
                "PMDWl_Left_eSigStatus",
                "PMDWl_Right_eSigStatus",
                "PMDSl_Front_eSigStatus",
                "PMDSl_Rear_eSigStatus",
                "PMDSl_Left_eSigStatus",
                "PMDSl_Right_eSigStatus",
                "PMDPEDCROS_Front_eSigStatus",
                "PMDPEDCROS_Rear_eSigStatus",
                "PMDPEDCROS_Left_eSigStatus",
                "PMDPEDCROS_Right_eSigStatus",
            ]
        ]
        output_df.reset_index(inplace=True, drop=True)

        result_list = []
        fail_dict = {}
        data_not_ok_list = []
        for column_name in pmsd_input_data:
            index = 0
            if pmsd_input_data[column_name].isin([ConstantsCem.AL_SIG_STATE_INIT, ConstantsCem.AL_SIG_STATE_OK]).all():
                data_not_ok_list.append("DATA_NOK")
            for esig_value in pmsd_input_data[column_name]:
                if esig_value == ConstantsCem.AL_SIG_STATE_INVALID:
                    index = index + 1
                    for column_name in output_df:
                        if output_df[column_name][index] == ConstantsCem.AL_SIG_STATE_INVALID:
                            result_list.append(1)
                        else:
                            result_list.append(0)
                            fail_dict[column_name] = "fail"
                else:
                    index = index + 1

        if len(data_not_ok_list) == 16:
            evaluation = "None of the input signals has AL_SIG_STATE_INVALID"
        else:
            if fail_dict:
                evaluation = (
                    "PMSD output signal state is not Invalid even if the input signal state is "
                    "AL_SIG_STATE_INVALID for these "
                    "signals ",
                    fail_dict.keys(),
                )
            else:
                evaluation = (
                    "PMSD sets INVALID state on its output if any of its input signal's state is "
                    "AL_SIG_STATE_INVALID.."
                )

        test_result = fc.PASS if all(result_list) else fc.FAIL

        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": "< PMSD shall set INVALID state on its output if any of its input signal's state is "
                    "AL_SIG_STATE_INVALID.",
                },
                "Result": {
                    "1": evaluation,
                },
                "Verdict": {
                    "1": "PASSED" if all(result_list) else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PFS Invalid Input State")
        self.result.details["Plots"].append(sig_sum)

        # Plot input esignal status dataframe
        if len(pmsd_input_data) != 0:
            for col_name, _ in pmsd_input_data.items():
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(pmsd_input_data[col_name]))),
                        y=pmsd_input_data[col_name].values.tolist(),
                        mode="lines",
                        showlegend=True,
                        name=f"{col_name}",
                        line=dict(color="darkblue"),
                    )
                )
                fig.layout = go.Layout(
                    yaxis=dict(tickformat="14"),
                    xaxis=dict(tickformat="14"),
                    xaxis_title="Frames",
                    yaxis_title=f"{col_name}",
                )
                fig.update_layout(PlotlyTemplate.lgt_tmplt)
                fig.add_annotation(
                    dict(
                        font=dict(color="black", size=12),
                        x=0,
                        y=-0.12,
                        showarrow=False,
                        text=f"{col_name}",
                        textangle=0,
                        xanchor="left",
                        xref="paper",
                        yref="paper",
                    )
                )
                plot_titles.append("")
                plots.append(fig)
                remarks.append("")

        # Plot output esignal status dataframe
        if len(output_df) != 0:
            for col_name, _ in output_df.items():
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(output_df[col_name]))),
                        y=output_df[col_name].values.tolist(),
                        mode="lines",
                        showlegend=True,
                        name=f"{col_name}",
                        line=dict(color="darkblue"),
                    )
                )
                fig.layout = go.Layout(
                    yaxis=dict(tickformat="14"),
                    xaxis=dict(tickformat="14"),
                    xaxis_title="Frames",
                    yaxis_title=f"{col_name}",
                )
                fig.update_layout(PlotlyTemplate.lgt_tmplt)
                fig.add_annotation(
                    dict(
                        font=dict(color="black", size=12),
                        x=0,
                        y=-0.12,
                        showarrow=False,
                        text=f"{col_name}",
                        textangle=0,
                        xanchor="left",
                        xref="paper",
                        yref="paper",
                    )
                )
                plot_titles.append("")
                plots.append(fig)
                remarks.append("")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2049496"],
            fc.TESTCASE_ID: ["86652"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "<PMSD> shall set INVALID state on its output if any of its input signal's state is "
                "AL_SIG_STATE_INVALID."
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


@verifies("2049496")
@testcase_definition(
    name="SWRT_CNC_PMSD_InvalidSignalState",
    description="<PMSD> shall set INVALID state on its output if any of its input signal's state is "
    "AL_SIG_STATE_INVALID.",
    doors_url="",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class FtPMSDInvalidSigStateOk(TestCase):
    """Invalid Signal State test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPMSDInvalidSigStateOk]
