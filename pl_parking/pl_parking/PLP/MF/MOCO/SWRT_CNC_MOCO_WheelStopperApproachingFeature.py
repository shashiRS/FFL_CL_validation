"""moco wheel stopper approaching feature"""

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
    calculate_distance_to_stop,
    check_phase_1_wheel_stopper_approaching_feature,
    check_phase_2_and_3_wheel_stopper_approaching_feature,
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

ALIAS = "SWRT_CNC_MOCO_WheelStopperApproachingFeature"

""" Steps required to create a new test case:
1. Define required signals in the Signals class
"""
signals_obj = MoCoSignals()


@teststep_definition(step_number=1, name="KPI", description=" ", expected_result=BooleanResult(TRUE))
@register_signals(ALIAS, MoCoSignals)
class Step1(TestStep):
    """moco wheel stopper approaching feature test setup"""

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

            "Verify that the component is in standstill"
            df["calculated_standstill"] = df.apply(
                lambda row: is_vehicle_in_standstill(
                    row["standstillHoldCur_nu"], row["standstillSecureCur_nu"], row["motionStatus_nu"]
                ),
                axis=1,
            )

            df["input_distanceToStopReq_m"] = df["distanceToStopReqInterExtrapolTraj_m"]
            loCtrlRequestType_param = constants.MoCo.LoCtrlRequestType.LOCTRL_BY_TRAJECTORY

            df = check_phase_1_wheel_stopper_approaching_feature(df, loCtrlRequestType_param)
            df = check_phase_2_and_3_wheel_stopper_approaching_feature(df)
            df = calculate_distance_to_stop(df, loCtrlRequestType_param)

            df["check_if_any_wheel_closer_to_stopper"] = df["check_if_any_wheel_closer_to_stopper"].map(
                {True: 1, False: 0}
            )
            df["intended_touched_wheel_stopper"] = df["intended_touched_wheel_stopper"].map({True: 1, False: 0})
            df["detect_touched_wheel_stopper"] = df["detect_touched_wheel_stopper"].map({True: 1, False: 0})
            df["check_phase1_conditions"] = df["check_phase1_conditions"].map({True: 1, False: 0})
            df["check_phase_2_Result"] = df["check_phase_2_Result"].map({True: 1, False: 0})

            ## Removed this for erg measurements as in erg files we don't have signal for this parameter so no use to consider this contact value for validation
            ## but need to consider this for rec measurements when required
            # df["feature_to_wait_for_contact"] = constants.MoCo.Parameter.AP_C_FEAT_WAIT_FOR_CONTACT_NU

            "TestStep"
            "Check and filter data by longitudinal control request"
            df_filtered = df[
                (df["activateLoCtrl"] == 1)
                & (df["loCtrlRequestType"] == constants.MoCo.LoCtrlRequestType.LOCTRL_BY_TRAJECTORY)
            ]

            passed = []
            if not df_filtered.empty:
                filtered_df = df_filtered[
                    (df_filtered["check_phase1_conditions"] == 1)
                    | (df_filtered["detect_touched_wheel_stopper"] == 1) & (df["isLastSegment_nu"] == 1)
                ]
                if not filtered_df.empty:
                    for _, car_pos_row in filtered_df.iterrows():
                        if (
                            (car_pos_row["check_phase1_conditions"] == 1)
                            and (car_pos_row["distanceToStopReq_m"] != car_pos_row["increase_distance_to_stop"])
                        ) and ((car_pos_row["check_phase_2_Result"] == 1) and car_pos_row["distanceToStopReq_m"] != 0):
                            passed.append(False)
                        else:
                            passed.append(True)
                else:
                    self.result.measured_result = NAN
                    test_result = fc.NOT_ASSESSED
                    eval_text = "Wheel Stopper Approaching phases are not met"

                if all(passed):
                    self.result.measured_result = TRUE
                    test_result = fc.PASS
                    eval_text = " ".join(
                        f"The component performed a wheel stopper approaching feature if configured via parameter AP_C_FEAT_WAIT_FOR_CONTACT_NU ({constants.MoCo.Parameter.AP_C_FEAT_WAIT_FOR_CONTACT_NU})"
                        f" for the last stroke of the maneuver (trajRequestPort.isLastSegment_nu == true).".split()
                    )
                else:
                    self.result.measured_result = FALSE
                    test_result = fc.FAIL
                    eval_text = " ".join(
                        f"The component has not performed a wheel stopper approaching feature if configured via parameter AP_C_FEAT_WAIT_FOR_CONTACT_NU ({constants.MoCo.Parameter.AP_C_FEAT_WAIT_FOR_CONTACT_NU})"
                        f" for the last stroke of the maneuver (trajRequestPort.isLastSegment_nu == true).".split()
                    )
                eval_0 = " ".join(
                    f"The component shall performed a wheel stopper approaching feature if configured via parameter AP_C_FEAT_WAIT_FOR_CONTACT_NU ({constants.MoCo.Parameter.AP_C_FEAT_WAIT_FOR_CONTACT_NU})"
                    f" for the last stroke of the maneuver (trajRequestPort.isLastSegment_nu == true).".split()
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
                eval_text = "Preconditions are not met"
                self.result.measured_result = NAN

                eval_0 = " ".join(
                    f"The component shall performed a wheel stopper approaching feature if configured via parameter AP_C_FEAT_WAIT_FOR_CONTACT_NU ({constants.MoCo.Parameter.AP_C_FEAT_WAIT_FOR_CONTACT_NU})"
                    f" for the last stroke of the maneuver (trajRequestPort.isLastSegment_nu == true).".split()
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
            y=df["isLastSegment_nu"].values.tolist(),
            mode="lines",
            name="isLastSegment_nu",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["check_if_any_wheel_closer_to_stopper"].values.tolist(),
            mode="lines",
            name="check_if_any_wheel_closer_to_stopper",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["intended_touched_wheel_stopper"].values.tolist(),
            mode="lines",
            name="intended_touched_wheel_stopper",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["detect_touched_wheel_stopper"].values.tolist(),
            mode="lines",
            name="detect_touched_wheel_stopper",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["distanceToStopReq_m"].values.tolist(),
            mode="lines",
            name="distanceToStopReq_m",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["newDistanceToStopReq_m"].values.tolist(),
            mode="lines",
            name="newDistanceToStopReq_m",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["distanceToStopReqInterExtrapolTraj_m"].values.tolist(),
            mode="lines",
            name="distanceToStopReqInterExtrapolTraj_m",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["newSegmentStarted_nu"].values.tolist(),
            mode="lines",
            name="newSegmentStarted_nu",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["drivingDirection_nu"].values.tolist(),
            mode="lines",
            name="drivingDirection_nu",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["previous_drivingDirectionValue_nu"].values.tolist(),
            mode="lines",
            name="previous_drivingDirectionValue_nu",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["shortest_distance_to_wheel_stopper"].values.tolist(),
            mode="lines",
            name="shortest_distance_to_wheel_stopper",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["calculated_driving_resistance_FL"].values.tolist(),
            mode="lines",
            name="calculated_driving_resistance_FL",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["calculated_driving_resistance_RL"].values.tolist(),
            mode="lines",
            name="calculated_driving_resistance_RL",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["calculated_driving_resistance_RR"].values.tolist(),
            mode="lines",
            name="calculated_driving_resistance_RR",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["calculated_driving_resistance_FR"].values.tolist(),
            mode="lines",
            name="calculated_driving_resistance_FR",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["drivingResistanceType_0"].values.tolist(),
            mode="lines",
            name="drivingResistanceType_0",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["drivingResistanceType_1"].values.tolist(),
            mode="lines",
            name="drivingResistanceType_1",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["drivingResistanceType_2"].values.tolist(),
            mode="lines",
            name="drivingResistanceType_2",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["drivingResistanceType_3"].values.tolist(),
            mode="lines",
            name="drivingResistanceType_3",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index.values.tolist(),
            y=df["passed_distance_of_current_stroke"].values.tolist(),
            mode="lines",
            name="passed_distance_of_current_stroke",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[df.index.values.min(), df.index.values.max()],
            y=[
                constants.MoCo.Parameter.AP_C_WFC_OVERSHOOT_LENGTH_M,
                constants.MoCo.Parameter.AP_C_WFC_OVERSHOOT_LENGTH_M,
            ],
            mode="lines",
            name="AP_C_WFC_OVERSHOOT_LENGTH_M",
            visible="legendonly",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[df.index.values.min(), df.index.values.max()],
            y=[
                constants.MoCo.Parameter.AP_C_WFC_OVERSHOOT_DIST_THRES_M,
                constants.MoCo.Parameter.AP_C_WFC_OVERSHOOT_DIST_THRES_M,
            ],
            mode="lines",
            name="AP_C_WFC_OVERSHOOT_DIST_THRES_M",
            visible="legendonly",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[df.index.values.min(), df.index.values.max()],
            y=[
                constants.MoCo.Parameter.AP_C_WFC_WS_VEL_LIMIT_MPS,
                constants.MoCo.Parameter.AP_C_WFC_WS_VEL_LIMIT_MPS,
            ],
            mode="lines",
            name="AP_C_WFC_WS_VEL_LIMIT_MPS",
            visible="legendonly",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[df.index.values.min(), df.index.values.max()],
            y=[
                constants.MoCo.Parameter.AP_C_WFC_VDY_DIST_THRES_M,
                constants.MoCo.Parameter.AP_C_WFC_VDY_DIST_THRES_M,
            ],
            mode="lines",
            name="AP_C_WFC_VDY_DIST_THRES_M",
            visible="legendonly",
        )
    )

    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="MTS.Package.Timestamp"
    )
    fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
    return fig


@tag("SWRT_CNC_MOCO_WheelStopperApproachingFeature")
@verifies("2605492")
@testcase_definition(
    name="MOCO Wheel Stopper Approaching Feature",
    description="The component shall perform a wheel stopper approaching feature if configured via parameter {AP_C_FEAT_WAIT_FOR_CONTACT_NU} "
    "for the last stroke of the maneuver (trajRequestPort.isLastSegment_nu == true).",
    group="Wheelstopper",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SWRT_CNC_MOCO_WheelStopperApproachingFeature(TestCase):
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
        SWRT_CNC_MOCO_WheelStopperApproachingFeature,
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
