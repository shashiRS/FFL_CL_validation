"""moco lateral comfortable standstill steering"""

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
    calculate_comfortable_standstill_steering_duration,
    front_SteerAngle_Req_radsec,
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

ALIAS = "SWRT_CNC_MOCO_ComfortableStandstillSteering"

signals_obj = MoCoSignals()


@teststep_definition(step_number=1, name="KPI", description=" ", expected_result=BooleanResult(TRUE))
@register_signals(ALIAS, MoCoSignals)
class Step1(TestStep):
    """MoCo lateral comfortable standstill steering test step"""

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

            "Verify that the vehicle is in standstill"
            df["calculated_standstill"] = df.apply(
                lambda row: is_vehicle_in_standstill(
                    row["standstillHoldCur_nu"], row["standstillSecureCur_nu"], row["motionStatus_nu"]
                ),
                axis=1,
            )
            df["calculated_standstill"] = df["calculated_standstill"].map({True: 1, False: 0})

            # Check
            df["calculated_standstill_check"] = (
                df["calculated_standstill"] & (df["activateLaCtrl"] == 1) & (df["activateLoCtrl"] == 1)
            ).astype(bool)

            df["calculated_comfortable_standstill"] = False
            df.loc[
                (abs(df["frontSteerAngReq_rad"] - df["steerAngReqRaw_rad"]) > 0.001)
                & (df["calculated_standstill_check"].astype(int) == 1),
                "calculated_comfortable_standstill",
            ] = True

            df = calculate_comfortable_standstill_steering_duration(df)
            df["calculated_comfortable_standstill"] = df["calculated_comfortable_standstill"].map({True: 1, False: 0})

            "Calculating front steer angle request velocity"
            df = front_SteerAngle_Req_radsec(df)

            "Checking if laDMCCtrlRequest_nu is activated"
            laDMCCtrlRequest_nu_present = df[df["laDMCCtrlRequest_nu"] == 1]

            try:
                steeranglegrad = (
                    laDMCCtrlRequest_nu_present.iloc[0]["steerAngFrontAxle_rad"]
                    - laDMCCtrlRequest_nu_present.iloc[1]["frontSteerAngReq_rad"]
                )
            except Exception:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")

            "TestStep"
            "Filter data by lateral control request and lateral operation mode control by path"
            df_filtered = df[
                (df["activateLaCtrl"] == 1)
                & (df["laCtrlRequestType"] == constants.MoCo.LaCtrlRequestType.LACTRL_COMF_ANGLE_ADJUSTMENT)
            ]
            if not df_filtered.empty:
                """Verify if the component determines the front steer angle
                request within the limits for comfortable standstill steering"""
                assertion_dict = {}
                first_iteration = 1
                df_filtered["frontSteerAngReq_rad_sec2"] = 0
                for idx, ts_row in enumerate(df_filtered.iterrows()):
                    ts = ts_row[0]
                    row = ts_row[1]
                    if first_iteration == 1:
                        first_iteration = 0
                        df_filtered.at[ts, "frontSteerAngReq_rad_sec"] = steeranglegrad
                    """Calculating front steer angle request acceleration"""
                    df_filtered["frontSteerAngReq_rad_sec2"] = df_filtered["frontSteerAngReq_rad_sec"].diff() / (
                        df["sample_time"] / 1000000000
                    )
                    df_filtered["frontSteerAngReq_rad_sec2"].fillna(0, inplace=True)

                    df["frontSteerAngReq_rad_sec2"] = df_filtered["frontSteerAngReq_rad_sec2"]
                    df["frontSteerAngReq_rad_sec2"].fillna(0, inplace=True)

                    df["frontSteerAngReq_rad_sec"] = df_filtered["frontSteerAngReq_rad_sec"]
                    df["frontSteerAngReq_rad_sec"].fillna(0, inplace=True)

                    if (
                        not abs(row["frontSteerAngReq_rad_sec"])
                        <= constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_VEL_RADPS
                    ):
                        assertion_dict[ts] = abs(row["frontSteerAngReq_rad_sec"])
                    if row["frontSteerAngReq_rad_sec"] < constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_VEL_RADPS:
                        if (
                            not abs(row["frontSteerAngReq_rad_sec2"])
                            <= constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_ACC_RADPS2
                        ):
                            assertion_dict[ts] = abs(row["frontSteerAngReq_rad_sec2"])
                    if abs(row["frontSteerAngReq_rad_sec"]) > constants.MoCo.Parameter.AP_C_PC_MIN_STEER_VEL_RADPS:
                        if (
                            not abs(row["frontSteerAngReq_rad_sec2"])
                            <= constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_ACC_RADPS2
                        ):
                            assertion_dict[ts] = abs(row["frontSteerAngReq_rad_sec2"])

                    """Calculating if the input signal laCtrlRequestPort.steerAngReqFront_rad was
                    reached in laDMCCtrlRequestPort.frontSteerAngReq_rad, for the last iteration"""
                    if idx == len(df_filtered) - 1:
                        if not abs(row["frontSteerAngReq_rad"] - row["steerAngReqFront_rad"]) < 0.01:
                            assertion_dict[ts] = abs(row["frontSteerAngReq_rad"])

                if assertion_dict:
                    assert_summary = pd.DataFrame(
                        {
                            "ERROR": {
                                key: f"Timestamp: {key} with value: {value}" for key, value in assertion_dict.items()
                            }
                        }
                    )
                    assert_summary = fh.build_html_table(assert_summary)
                    plot_titles.append("")
                    plots.append(assert_summary)
                    remarks.append("")

                    self.result.measured_result = FALSE
                    test_result = fc.FAIL
                    eval_text = " ".join("Conditions not satisfied" f" {test_result}.".split())

                else:
                    self.result.measured_result = TRUE
                    test_result = fc.PASS
                    eval_text = " ".join("Conditions satisfied" f" {test_result}.".split())

                eval_0 = " ".join(
                    "Ensure that the component shall perform lateral control in operation mode "
                    "comfortable steer angle adjustment via comfortable standstill steering based on the "
                    "input signal laCtrlRequestPort.steerAngReqFront_rad to determine the front "
                    "steer angle request (laDMCCtrlRequestPort.frontSteerAngReq_rad).".split()
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
                        y=df["frontSteerAngReq_rad_sec2"].values.tolist(),
                        mode="lines",
                        name="frontSteerAngReq_rad_sec2",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["frontSteerAngReq_rad_sec"].values.tolist(),
                        mode="lines",
                        name="frontSteerAngReq_rad_sec",
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
                        y=df["calculated_comfortable_standstill"].values.tolist(),
                        mode="lines",
                        name="calculated_comfortable_standstill",
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=[df.index.values.min(), df.index.values.max()],
                        y=[
                            constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_VEL_RADPS,
                            constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_VEL_RADPS,
                        ],
                        mode="lines",
                        name="AP_C_PC_FIRST_STEER_VEL_RADPS",
                        visible="legendonly",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["laCtrlRequestType"].values.tolist(),
                        mode="lines",
                        name="laCtrlRequestType",
                        visible="legendonly",
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=[df.index.values.min(), df.index.values.max()],
                        y=[
                            -constants.MoCo.Parameter.AP_C_PC_MIN_STEER_VEL_RADPS,
                            -constants.MoCo.Parameter.AP_C_PC_MIN_STEER_VEL_RADPS,
                        ],
                        mode="lines",
                        name="-AP_C_PC_MIN_STEER_VEL_RADPS",
                        visible="legendonly",
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=[df.index.values.min(), df.index.values.max()],
                        y=[
                            constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_ACC_RADPS2,
                            constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_ACC_RADPS2,
                        ],
                        mode="lines",
                        name="AP_C_PC_FIRST_STEER_ACC_RADPS2",
                        visible="legendonly",
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["steerAngReqFront_rad"].values.tolist(),
                        mode="lines",
                        name="steerAngReqFront_rad",
                        visible="legendonly",
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["steerAngReqRaw_rad"].values.tolist(),
                        mode="lines",
                        name="steerAngReqRaw_rad",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["frontSteerAngReq_rad"].values.tolist(),
                        mode="lines",
                        name="frontSteerAngReq_rad",
                        visible="legendonly",
                    )
                )

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
                self.result.measured_result = NAN
                eval_text = "Precondition not satisfied"
                self.result.details["Step_result"] = test_result

                eval_0 = " ".join(
                    "Ensure that the component shall perform lateral control in operation mode "
                    "comfortable steer angle adjustment via comfortable standstill steering based on the "
                    "input signal laCtrlRequestPort.steerAngReqFront_rad to determine the front "
                    "steer angle request (laDMCCtrlRequestPort.frontSteerAngReq_rad).".split()
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
                fig = go.Figure()
                plot_titles.append("")
                plots.append(sig_sum)
                remarks.append("")
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
                        x=[df.index.values.min(), df.index.values.max()],
                        y=df["laCtrlRequestType"].values.tolist(),
                        mode="lines",
                        name="laCtrlRequestType",
                        visible="legendonly",
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["frontSteerAngReq_rad_sec"].values.tolist(),
                        mode="lines",
                        name="frontSteerAngReq_rad_sec",
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
                        y=df["calculated_comfortable_standstill"].values.tolist(),
                        mode="lines",
                        name="calculated_comfortable_standstill",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=[df.index.values.min(), df.index.values.max()],
                        y=[
                            constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_VEL_RADPS,
                            constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_VEL_RADPS,
                        ],
                        mode="lines",
                        name="AP_C_PC_FIRST_STEER_VEL_RADPS",
                        visible="legendonly",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=[df.index.values.min(), df.index.values.max()],
                        y=[
                            -constants.MoCo.Parameter.AP_C_PC_MIN_STEER_VEL_RADPS,
                            -constants.MoCo.Parameter.AP_C_PC_MIN_STEER_VEL_RADPS,
                        ],
                        mode="lines",
                        name="-AP_C_PC_MIN_STEER_VEL_RADPS",
                        visible="legendonly",
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=[df.index.values.min(), df.index.values.max()],
                        y=[
                            constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_ACC_RADPS2,
                            constants.MoCo.Parameter.AP_C_PC_FIRST_STEER_ACC_RADPS2,
                        ],
                        mode="lines",
                        name="AP_C_PC_FIRST_STEER_ACC_RADPS2",
                        visible="legendonly",
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["steerAngReqFront_rad"].values.tolist(),
                        mode="lines",
                        name="steerAngReqFront_rad",
                        visible="legendonly",
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["steerAngReqRaw_rad"].values.tolist(),
                        mode="lines",
                        name="steerAngReqRaw_rad",
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["frontSteerAngReq_rad"].values.tolist(),
                        mode="lines",
                        name="frontSteerAngReq_rad",
                        visible="legendonly",
                    )
                )
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


@tag("SWRT_CNC_MOCO_ComfortableStandstillSteering")
@verifies("1407039")
@testcase_definition(
    name="MoCo Lateral Comfortable Standstill Steering",
    group="standstill steering",
    description="Ensure that the component shall perform lateral control in operation mode comfortable "
    "steer angle adjustment via comfortable standstill steering based on "
    "the input signal laCtrlRequestPort.steerAngReqFront_rad to determine the"
    " front steer angle request (laDMCCtrlRequestPort.frontSteerAngReq_rad).",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SWRT_CNC_MOCO_ComfortableStandstillSteering(TestCase):
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
        SWRT_CNC_MOCO_ComfortableStandstillSteering,
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
