"""Functional test for velocity"""

import logging
import os
import sys

import pandas as pd
import plotly.graph_objects as go
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import (
    EntrySignals,
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    rep,
)
from pl_parking.PLP.MF.ft_helper import ExampleSignals

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)


SIGNAL_DATA = "MF_VELOCITY"

example_obj = EntrySignals()


@teststep_definition(
    step_number=1,
    name="VELOCITY",
    description=(
        "Computes the maximum velocity of the ego vehicle during PARKING_MODE = PPC_SCANNING_IN                 (in"
        " signal M7board.EM_Thread.PSMDebugPort.stateVarPPC_nu)"
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ExampleSignals)
class TestStepFtParkingVelocity(TestStep):
    """Test step class"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        try:
            df = self.readers[SIGNAL_DATA].signals
        except Exception:
            df = self.readers[SIGNAL_DATA]
            df[EntrySignals.Columns.TIMESTAMP] = df.index
        test_result = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)

        sg_time = "TimeStamp"
        sg_velocity = "EgoMotionPort"
        sg_parking_mode = "PSMDebugPort"
        max_speed = 0
        min_speed_overall = 0
        min_speed_scanning = 0
        idx0, idx1, idx2 = 0, 0, 0
        min_spd_all_found, min_spd_scan_found, max_speed_exceeded = 0, 0, 0
        prk_state_found = True
        all_speed_positive = True
        scanned_speed_positive = True
        max_in_limits = True
        signal_name = example_obj._properties

        try:
            # Converting mps to kmh
            df[sg_velocity] = df[sg_velocity] * constants.GeneralConstants.MPS_TO_KMPH
            # Converting microseconds to seconds
            df[sg_time] = df[sg_time] / constants.GeneralConstants.US_IN_S
            # Converting epoch time to seconds passed
            df[sg_time] = df[sg_time] - df[sg_time].iat[0]

            # Creating a new dataframe when PPC_SCANNING_IN is active
            mask_velocity = df[sg_parking_mode] == constants.ParkingMachineStates.PPC_SCANNING_IN
            df_filtered = df[sg_velocity] * mask_velocity

            # Check if overall velocity is positive
            min_speed_overall = df[sg_velocity].min()

            if min_speed_overall < 0:
                all_speed_positive = False
                idx0 = df[sg_velocity].index[df[sg_velocity] < 0]
                min_spd_all_found = df[sg_velocity][idx0[0]]

            # Check if parking state machine is set to PPC_SCANNING_IN
            if not mask_velocity.any():
                prk_state_found = False
                scanned_speed_positive = False
                max_in_limits = False
            else:
                # Get speed readings
                min_speed_scanning = df_filtered.min()
                max_speed = df_filtered.max()

                # Check min speed during scanning
                if min_speed_scanning < 0:
                    scanned_speed_positive = False
                    idx1 = df_filtered.index[df_filtered < 0]
                    min_spd_scan_found = df[sg_velocity][idx1[0]]

                # Check if max velocity during scanning is < than threshold
                if max_speed > constants.ConstantsVelocity.MAX_SPEED_THRESHOLD:
                    max_in_limits = False
                    idx2 = df_filtered.index[df_filtered > constants.ConstantsVelocity.MAX_SPEED_THRESHOLD]
                    max_speed_exceeded = df[sg_velocity][idx2[0]]

            if prk_state_found and max_in_limits:
                test_result = fc.PASS
            else:
                test_result = fc.FAIL

            # Set condition strings
            cond_0 = " ".join(
                "Vehicle speed should be >= 0 km/h. The speed is checked in signal               "
                f" {signal_name[sg_velocity]}.".split()
            )
            cond_1 = " ".join(
                "Parking state should be PPC_SCANNING_IN               "
                f" ({constants.ParkingMachineStates.PPC_SCANNING_IN}) in signal {signal_name[sg_parking_mode]}.".split()
            )
            cond_2 = " ".join("Vehicle speed during scanning should be >= 0 km/h.".split())
            cond_3 = " ".join(
                "Vehicle speed during scanning should                 be <"
                f" {constants.ConstantsVelocity.MAX_SPEED_THRESHOLD} km/h.".split()
            )

            # Set table dataframe
            signal_summary = pd.DataFrame(
                {
                    "Condition": {"0": cond_0, "1": cond_1, "2": cond_2, "3": cond_3},
                    # Logic for Results:
                    # string_1 IF condition(True) ELSE string_2
                    # string_1 IF condition(True) ELSE (string_2 IF condition_2(TRUE) else string_3)
                    # the above logic is applied when the PPC_SCANNING_IN is not found
                    "Result": {
                        "0": (
                            "Overall vehicle speed is positive."
                            if all_speed_positive
                            else (
                                f"Value {min_spd_all_found:.2f} km/h found at timestamp:"
                                f" {df[sg_time][idx0[0]]:.2f} seconds."
                            )
                        ),
                        "1": (
                            f"Parking state PPC_SCANNING_IN({constants.ParkingMachineStates.PPC_SCANNING_IN}) was found."
                            if prk_state_found
                            else (
                                "Parking state PPC_SCANNING_IN                   "
                                f" ({constants.ParkingMachineStates.PPC_SCANNING_IN}) was not found."
                            )
                        ),
                        "2": (
                            "Speed during scanning is positive."
                            if scanned_speed_positive
                            else (
                                f"Value {min_spd_scan_found:.2f} km/h found                     at"
                                f" timestamp:{df[sg_time][idx1[0]]:.2f} seconds."
                                if prk_state_found
                                else (
                                    "Scanning did not occur, parking state PPC_SCANNING_IN                   "
                                    f" ({constants.ParkingMachineStates.PPC_SCANNING_IN}) was not found."
                                )
                            )
                        ),
                        "3": (
                            f"Maximum speed: {max_speed:.2f} km/h."
                            if max_in_limits
                            else (
                                f"Maximum speed exceeded with the value of {max_speed_exceeded:.2f} km/h               "
                                f"      at timestamp: {df[sg_time][idx2[0]]:.2f} seconds."
                                if prk_state_found
                                else (
                                    "Scanning did not occur, parking state PPC_SCANNING_IN                    "
                                    f" ({constants.ParkingMachineStates.PPC_SCANNING_IN}) was not found."
                                )
                            )
                        ),
                    },
                    "Verdict": {
                        "0": "PASSED" if all_speed_positive else "ACCEPTABLE",
                        "1": "PASSED" if prk_state_found else "FAILED",
                        "2": "PASSED" if scanned_speed_positive else "ACCEPTABLE" if prk_state_found else "FAILED",
                        "3": "PASSED" if max_in_limits else "FAILED",
                    },
                }
            )

            # Create table with eval conditions from the summary dict
            fig = go.Figure(
                data=[
                    go.Table(
                        columnwidth=[50, 25],
                        header=dict(
                            values=list(signal_summary.columns),
                            fill_color="rgb(255,165,0)",
                            font=dict(size=12, family="Arial", color="rgb(0,0,0)"),
                            align="center",
                        ),
                        cells=dict(
                            values=[signal_summary[col] for col in signal_summary.columns],
                            height=40,
                            align="center",
                            font=dict(size=12),
                        ),
                    )
                ]
            )
            fig.update_layout(
                constants.PlotlyTemplate.lgt_tmplt, height=fh.calc_table_height(signal_summary["Result"].to_dict())
            )
            plot_titles.append("Condition Evaluation")
            plots.append(fig)
            remarks.append("")

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df[sg_time].values.tolist(),
                    y=df[sg_velocity].values.tolist(),
                    mode="lines",
                    name=f"{signal_name[sg_velocity]} * 3.6 [km/h]",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df[sg_time].values.tolist(),
                    y=df[sg_parking_mode].values.tolist(),
                    mode="lines",
                    name=signal_name[sg_parking_mode],
                )
            )
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            plot_titles.append("Overall vehicle velocity [km/h]  ")
            plots.append(fig)
            remarks.append("")

            max_speed = f"{max_speed:.2f}" if prk_state_found else "N/A"
            if test_result == fc.PASS:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE
            additional_results_dict = {
                "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                "Name": {"value": "Checks for maximum velocity violation"},
                "Expected result [km/h]": {"value": f"< {constants.ConstantsVelocity.MAX_SPEED_THRESHOLD}"},
                "Velocity speed during scanning [km/h]": {"value": max_speed},
            }
            for plot in plots:
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)

        except Exception as err:
            test_result = fc.INPUT_MISSING
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")
            print(str(err))
            additional_results_dict = {
                "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                "Name": {"value": f"Signal missing: { str(err)}"},
                "Expected result [km/h]": {"value": ""},
                "Velocity speed during scanning [km/h]": {"value": ""},
            }

            self.result.details["Additional_results"] = additional_results_dict
            # 1/0


@testcase_definition(
    name="MF VELOCITY",
    description=(
        " Computes the maximum velocity of the ego vehicle during PARKING_MODE = PPC_SCANNING_IN (in signal"
        " M7board.EM_Thread.PSMDebugPort.stateVarPPC_nu)"
    ),
)
class FtParkingVelocity(TestCase):
    """Test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtParkingVelocity]
