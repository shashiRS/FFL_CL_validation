"""moco lateral path control status port"""

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
from pl_parking.PLP.MF.MOCO.helpers import is_vehicle_in_standstill

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.1"
__status__ = "Development"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ALIAS = "SWRT_CNC_MOCO_LateralPathControlStatusPort"

signals_obj = MoCoSignals


@teststep_definition(step_number=1, name="KPI", description=" ", expected_result=BooleanResult(TRUE))
@register_signals(ALIAS, MoCoSignals)
class Step1(TestStep):
    """moco lateral path control status port test setup"""

    custom_report = fh.MOCOCustomTeststepReport

    def __init__(self):
        """Initialize the test step"""
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
            "Verify that the vehicle is in standstill"
            df["calculated_standstill"] = df.apply(
                lambda row: is_vehicle_in_standstill(
                    row["standstillHoldCur_nu"], row["standstillSecureCur_nu"], row["motionStatus_nu"]
                ),
                axis=1,
            )

            "Filter data by lateral control request and lateral operation mode control by path"
            df_filtered = df[
                (df["activateLaCtrl"] == 1)
                & (df["laCtrlRequestType"] == constants.MoCo.LaCtrlRequestType.LACTRL_BY_TRAJECTORY)
                & df["calculated_standstill"]
            ]

            df["calculated_standstill"] = df["calculated_standstill"].map({True: 1, False: 0})

            passed = []
            if not df_filtered.empty:
                "TestStep"
                "Evaluate lateral path control status"

                for _, car_pos_row in df_filtered.iterrows():
                    lateral_deviation = car_pos_row["currentDeviation_m"]
                    if (abs(lateral_deviation) > constants.MoCo.Parameter.AP_C_PC_FAIL_MAX_LAT_ERROR_M
                           and (car_pos_row["lateralPathControlFailed_nu"] == 0)):

                        passed.append(False)
                    else:
                        passed.append(True)
                if all(passed):
                    self.result.measured_result = TRUE
                    test_result = fc.PASS
                    eval_text = " ".join(
                        f" Lateral request control and "
                        f"absolute lateral deviation is active. "
                        f"The component output is satisfied."
                        f"Conditions: {test_result}.".split()
                    )
                else:
                    self.result.measured_result = FALSE
                    test_result = fc.FAIL
                    eval_text = " ".join(
                        f"Lateral request control is active and "
                        f"absolute lateral deviation from path is larger than AP_C_PC_FAIL_MAX_LAT_ERROR_M ({constants.MoCo.Parameter.AP_C_PC_FAIL_MAX_LAT_ERROR_M}) and the component output is (mfControlStatusPort.lateralPathControlFailed_nu=False))"
                        f"Conditions: {test_result}.".split()
                    )

                eval_0 = " ".join(
                    f"Lateral control request sent and if absolute lateral deviation from path is larger than AP_C_PC_FAIL_MAX_LAT_ERROR_M ({constants.MoCo.Parameter.AP_C_PC_FAIL_MAX_LAT_ERROR_M})the component shall output (mfControlStatusPort.lateralPathControlFailed_nu=True).".split()
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
                eval_text = "Lateral control request not activated"
                    #"Lateral control request not active"
                self.result.measured_result = NAN
                eval_0 = " ".join(
                    f"Lateral control request sent and if absolute lateral deviation from path is larger than AP_C_PC_FAIL_MAX_LAT_ERROR_M ({constants.MoCo.Parameter.AP_C_PC_FAIL_MAX_LAT_ERROR_M})the component shall output (mfControlStatusPort.lateralPathControlFailed_nu=true).".split()
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
            y=df["laCtrlRequestType"].values.tolist(),
            mode="lines",
            name="laCtrlRequestType",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["activateLaCtrl"].values.tolist(),
            mode="lines",
            name="activateLaCtrl",
        )
    )

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
            y=(abs(df["currentDeviation_m"]).values.tolist()),
            mode="lines",
            name="abs(currentDeviation_m)",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[df.index.values.min(), df.index.values.max()],
            y=[
                constants.MoCo.Parameter.AP_C_PC_FAIL_MAX_LAT_ERROR_M,
                constants.MoCo.Parameter.AP_C_PC_FAIL_MAX_LAT_ERROR_M,
            ],
            mode="lines",
            name="AP_C_PC_FAIL_MAX_LAT_ERROR_M",
            visible="legendonly",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["lateralPathControlFailed_nu"].values.tolist(),
            mode="lines",
            name="lateralPathControlFailed_nu",
        )
    )

    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="MTS.Package.Timestamp"
    )
    fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
    return fig

@tag("SWRT_CNC_MOCO_LateralPathControlStatusPort")
@verifies("1407027")
@testcase_definition(
    name="MOCO Lateral path control status port",
    group="Lateral Path Control",
    description="Ensure that if vehicle in standstill and the absolute lateral deviation from path is larger than {AP_C_PC_FAIL_MAX_LAT_ERROR_M} the component shall output mfControlStatusPort.lateralPathControlFailed_nu=true",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SWRT_CNC_MOCO_LateralPathControlStatusPort(TestCase):
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
        SWRT_CNC_MOCO_LateralPathControlStatusPort,
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
