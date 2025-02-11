"""moco reduce tire deformation"""

import logging
import math
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from tsf.core.results import NAN
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
from tsf.db.results import Result

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

ALIAS = "SWKPI_CNC_MOCO_ReduceTireDeformation"

signals_obj = MoCoSignals


@teststep_definition(
    step_number=1,
    name="KPI",
    description=" ",
    expected_result=f">= {constants.MoCo.Parameter.AP_C_KPI_SUCCESS_RATE_TIRE_DEF_PERCENT} %",
)
@register_signals(ALIAS, MoCoSignals)
class Step1(TestStep):
    """moco reduce tire deformation KPI test setup"""

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

            df["steerAngFrontAxle_deg"] = df["steerAngFrontAxle_rad"].astype(float).apply(math.degrees)
            df['isStatusChanged'] = df['activateLaCtrl'].diff()
            df_filtered = df[df['isStatusChanged'] == -1]

            if not df_filtered.empty:
                # filter cases where the lateral control request was deactivated
                filtered_df = df[df["activateLaCtrl"] == 0]

                # calculate the steering wheel angle at the front axle and check against the threshold
                filtered_df["steer_wheel_angle_deformation_deg"] =(
                    filtered_df["steerAngFrontAxle_deg"] * constants.MoCo.Parameter.AP_V_STEER_RATIO_NU
                )
                filtered_df["is_below_threshold"] = (
                    filtered_df["steer_wheel_angle_deformation_deg"]
                    < constants.MoCo.Parameter.AP_C_COMP_TIRE_DEF_STEER_WHEEL_ANGLE_DEG
                )

                passed = filtered_df["is_below_threshold"].sum()
                assertion = filtered_df["is_below_threshold"].count() - passed
                if assertion > 0:
                    self.result.measured_result = Result(numerator=0, denominator=1, unit="= 0 %")
                    test_result = fc.FAIL
                    eval_text = " ".join(
                        f"When active lateral control is deactivated,steering wheel angle deformation at the front axle > "
                        f"AP_C_COMP_TIRE_DEF_STEER_WHEEL_ANGLE_DEG({constants.MoCo.Parameter.AP_C_COMP_TIRE_DEF_STEER_WHEEL_ANGLE_DEG})"
                        f"Conditions: {test_result}.".split()
                    )
                    eval_0 = " ".join(
                        "MFControl shall execute a requested comfortable standstill steering in a way that the deformation of the tire contact area is reduced.".split()
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
                else:
                    self.result.measured_result = Result(numerator=100, denominator=1, unit="= 100 %")
                    test_result = fc.PASS
                    eval_text = " ".join(
                        f"When active lateral control is deactivated,steering wheel angle deformation at the front axle <= "
                        f"AP_C_COMP_TIRE_DEF_STEER_WHEEL_ANGLE_DEG({constants.MoCo.Parameter.AP_C_COMP_TIRE_DEF_STEER_WHEEL_ANGLE_DEG})"
                        f"Conditions: {test_result}.".split()
                    )

                    eval_0 = " ".join(
                        "MFControl shall execute a requested comfortable standstill steering in a way that the deformation of the tire contact area is reduced.".split()
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

                # this line is for plot purposes only.
                df["steer_wheel_angle_deformation_deg"] = (
                    df["steerAngFrontAxle_deg"] * constants.MoCo.Parameter.AP_V_STEER_RATIO_NU
                )

                fig = get_plot_signals(df)
                plot_titles.append("Graphical Overview")
                plots.append(fig)
                remarks.append("")

                additional_results_dict = {
                    "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                    "Total Cycles": {"value": df.shape[0]},
                    "Passed Cycles": {"value": passed},
                    "Failed Cycles": {"value": assertion},
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
                eval_text = "Lateral control request is not deactivated"
                self.result.measured_result = NAN

                eval_0 = " ".join(
                    "MFControl shall execute a requested comfortable standstill steering in a way that the deformation of the tire contact area is reduced.".split()
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
                        x=df.index.values.tolist(),
                        y=df["activateLaCtrl"].values.tolist(),
                        mode="lines",
                        name="activateLaCtrl",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["steerAngFrontAxle_deg"].values.tolist(),
                        mode="lines",
                        name="steerAngFrontAxle_deg",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=[df.index.values.min(), df.index.values.max()],
                        y=[
                            constants.MoCo.Parameter.AP_C_COMP_TIRE_DEF_STEER_WHEEL_ANGLE_DEG,
                            constants.MoCo.Parameter.AP_C_COMP_TIRE_DEF_STEER_WHEEL_ANGLE_DEG,
                        ],
                        mode="lines",
                        name="AP_C_COMP_TIRE_DEF_STEER_WHEEL_ANGLE_DEG",
                        visible="legendonly",
                    )
                )
                fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
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
            y=df["activateLaCtrl"].values.tolist(),
            mode="lines",
            name="activateLaCtrl",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["steer_wheel_angle_deformation_deg"].values.tolist(),
            mode="lines",
            name="steer_wheel_angle_deformation_deg",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["steerAngFrontAxle_deg"].values.tolist(),
            mode="lines",
            name="steerAngFrontAxle_deg",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[df.index.values.min(), df.index.values.max()],
            y=[
                constants.MoCo.Parameter.AP_C_COMP_TIRE_DEF_STEER_WHEEL_ANGLE_DEG,
                constants.MoCo.Parameter.AP_C_COMP_TIRE_DEF_STEER_WHEEL_ANGLE_DEG,
            ],
            mode="lines",
            name="AP_C_COMP_TIRE_DEF_STEER_WHEEL_ANGLE_DEG",
            visible="legendonly",
        )
    )

    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="MTS.Package.Timestamp"
    )
    fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
    return fig

@tag("SWKPI_CNC_MOCO_ReduceTireDeformation")
@verifies("1735580")
@testcase_definition(
    name="MOCO reduce tire deformation KPI",
    group="deformation kpi",
    description="MFControl shall execute a requested comfortable standstill steering in a way that the deformation of the tire contact area is reduced.",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SWKPI_CNC_MOCO_ReduceTireDeformation(TestCase):
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
    test_bsigs =[r".\absolute_directory_path_to_your_measurement\file.erg"]

    debug(
        SWKPI_CNC_MOCO_ReduceTireDeformation,
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
