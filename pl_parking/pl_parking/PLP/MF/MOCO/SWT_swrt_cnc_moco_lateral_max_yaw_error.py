"""moco lateral max yaw error"""

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

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.1"
__status__ = "Development"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ALIAS = "SWT_swrt_cnc_moco_lateral_max_yaw_error"

signals_obj = MoCoSignals()


@teststep_definition(step_number=1, name="KPI", description=" ", expected_result=BooleanResult(TRUE))
@register_signals(ALIAS, MoCoSignals)
class Step1(TestStep):
    """moco lateral max yaw error status test step"""

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

            "TestStep"
            "Filter data by lateral control request and lateral operation mode control by path"
            df_filtered = df[
                (df["activateLaCtrl"] == 1)
                & (df["laCtrlRequestType"] == constants.MoCo.LaCtrlRequestType.LACTRL_BY_TRAJECTORY)
            ]

            "TestStep"
            "Filter data by longitudinal control request"
            df_filtered = df_filtered[df["activateLoCtrl"] == 1]

            # planned_path = get_planned_path(df)
            # calculate_orientation_deviation_list = []

            df_filtered = df_filtered.loc[
                abs(df["orientationError_rad"]) > constants.MoCo.Parameter.AP_C_PC_FAIL_MAX_YAW_ERROR_RAD
            ]
            if not df_filtered.empty:
                # for _, row in df.iterrows():
                #     ego_yaw_angle = row['yawAngle_rad']
                #     ego_position = get_ego_position(row)
                #     orthogonal_projection_point = get_orthogonal_projection_point(ego_position, planned_path)
                #     orientation_deviation_from_path = calculate_orientation_deviation_from_path(ego_yaw_angle, planned_path,
                #                                                                                 orthogonal_projection_point)
                #     calculate_orientation_deviation_list.append(orientation_deviation_from_path)
                #
                # df['calculated_orientation_deviation'] = calculate_orientation_deviation_list
                # are_equal = df['calculated_orientation_deviation'].equals(df['orientationError_rad'])
                # if not are_equal:
                #     self.result.measured_result = FALSE
                "TestStep"
                (
                    "Check if the absolute orientation deviation from planned path is greater than {AP_C_PC_FAIL_MAX_YAW_ERROR_RAD} and  "
                    "calculated_hold_req_nu = LoDMCHoldRequestType.LODMC_HOLD_REQ_OFF"
                )
                calculated_hold_req_nu = constants.MoCo.LoDMCHoldRequestType.LODMC_HOLD_REQ_OFF

                for _, car_pos_row in df_filtered.iterrows():

                    orientation_deviation_from_path = car_pos_row["orientationError_rad"]

                    if abs(orientation_deviation_from_path) > constants.MoCo.Parameter.AP_C_PC_FAIL_MAX_YAW_ERROR_RAD:
                        calculated_hold_req_nu = constants.MoCo.LoDMCHoldRequestType.LODMC_HOLD_REQ_ON
                        if car_pos_row["holdReq_nu"] != calculated_hold_req_nu:
                            assertion_dict[_] = car_pos_row["holdReq_nu"]

                if assertion_dict:
                    # assert_summary = pd.DataFrame({"The component didn't correctly request to stop and hold the vehicle in standstill, holdReq_nu for row":{key: f'Timestamp: {key} with value: {value}' for key,value in assertion_dict.items()}})
                    # assert_summary = fh.build_html_table(assert_summary)
                    # plot_titles.append("")
                    # plots.append(assert_summary)
                    # remarks.append("")
                    self.result.measured_result = FALSE
                    test_result = fc.FAIL
                    eval_text = " ".join(
                        f"absolute orientation deviation from planned path <= AP_C_FAIL_MAX_YAW_ERROR_RAD({constants.MoCo.Parameter.AP_C_PC_FAIL_MAX_YAW_ERROR_RAD}) "
                        f"and loDMCCtrlRequestPort.holdReq_nu = 1".split()
                    )
                    eval_0 = " ".join(
                        f" The absolute orientation deviation from planned path is greater "
                        f"than {constants.MoCo.Parameter.AP_C_PC_FAIL_MAX_YAW_ERROR_RAD}.".split()
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
                    self.result.measured_result = TRUE
                    test_result = fc.PASS
                    eval_text = " ".join(
                        f"absolute orientation deviation from planned path <= AP_C_FAIL_MAX_YAW_ERROR_RAD({constants.MoCo.Parameter.AP_C_PC_FAIL_MAX_YAW_ERROR_RAD}) "
                        f"and loDMCCtrlRequestPort.holdReq_nu = 0".split()
                    )
                    eval_0 = " ".join(
                        f" The absolute orientation deviation from planned path is greater "
                        f"than {constants.MoCo.Parameter.AP_C_PC_FAIL_MAX_YAW_ERROR_RAD}.".split()
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
                eval_text = f"The absolute orientation deviation from planned path is not greater than {constants.MoCo.Parameter.AP_C_PC_FAIL_MAX_YAW_ERROR_RAD}"
                self.result.measured_result = NAN

                eval_0 = " ".join(
                    f" The absolute orientation deviation from planned path is greater "
                    f"than {constants.MoCo.Parameter.AP_C_PC_FAIL_MAX_YAW_ERROR_RAD}.".split()
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
                additional_results_dict = {
                    "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                    "Percent match [%]": {"value": "n/a"},
                }
                fig = get_plot_signals(df)
                plot_titles.append("Graphical Overview")
                plots.append(fig)
                remarks.append("")
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
            y=df["loDMCCtrlRequest_nu"].values.tolist(),
            mode="lines",
            name="loDMCCtrlRequest_nu",
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
            y=df["holdReq_nu"].values.tolist(),
            mode="lines",
            name="holdReq_nu",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["orientationError_rad"].values.tolist(),
            mode="lines",
            name="orientationError_rad",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[df.index.values.min(), df.index.values.max()],
            y=[
                constants.MoCo.Parameter.AP_C_PC_FAIL_MAX_YAW_ERROR_RAD,
                constants.MoCo.Parameter.AP_C_PC_FAIL_MAX_YAW_ERROR_RAD,
            ],
            mode="lines",
            name="AP_C_PC_FAIL_MAX_YAW_ERROR_RAD",
            visible="legendonly",
        )
    )

    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="MTS.Package.Timestamp"
    )
    fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
    return fig


@verifies("1407126")
@testcase_definition(
    name="MOCO Lateral max yaw error",
    group="yaw error",
    description="Ensure that the component sends a request to stop and hold in standstill in case of absolute \
        orientation deviation from planned path is larger than maximum yaw error allowed.",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class SWT_swrt_cnc_moco_lateral_max_yaw_error(TestCase):
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
        SWT_swrt_cnc_moco_lateral_max_yaw_error,
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
