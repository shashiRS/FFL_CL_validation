"""Functional test for number of planned strokes"""

import logging

from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

import pandas as pd
import plotly.graph_objects as go

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

SIGNAL_DATA = "MF_NUMBER_OF_PLANNED_STROKES"

example_obj = EntrySignals()


@teststep_definition(
    step_number=1,
    name="NUMBER OF PLANNED STROKES",
    description=(
        "Computes the number of planned strokes for the parking manoeuvre. This is achieved by checking when the"
        " parking mode is PPC_SCANNING_IN and PPC_PERFORM_PARKING (in signal"
        " M7board.EM_Thread.PSMDebugPort.stateVarPPC_nu), then computing the number of valid segments. For each"
        " segment, a driving direction signal is appended. The planned number of strokes is the number of times the"
        " driving direction changes from one index to the next one."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ExampleSignals)
class TestStepFtParkingNbPlannedStrokes(TestStep):
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
        result_final = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)

        # Defining signal variables for signal handling
        sg_valid_segments = "NumValidSegments"
        sg_time = "TimeStamp"
        sg_parking_mode = "PSMDebugPort"
        sg_drv_dir = "DrvDir"  # Basename for all DrVDir signals

        signal_summary = {}
        eval_cond = [False] * 5
        direction = []
        number_of_strokes = 0
        number_valid_segments = 0
        found_valid_segment = False
        signal_name = example_obj._properties

        try:
            # Converting microseconds to seconds
            df[sg_time] = df[sg_time] / constants.GeneralConstants.US_IN_S
            # Converting epoch time to seconds passed
            df[sg_time] = df[sg_time] - df[sg_time].iat[0]

            scanning_in = df[sg_parking_mode] == constants.ParkingMachineStates.PPC_SCANNING_IN
            performing_parking = df[sg_parking_mode] == constants.ParkingMachineStates.PPC_PERFORM_PARKING

            for i, _value in enumerate(df[sg_parking_mode]):
                if scanning_in.values[: i + 1].any() and performing_parking.values[i + 1]:
                    number_valid_segments = max(
                        min(
                            df[sg_valid_segments].values[i + 1], constants.ConstantsNbPlannedStrokes.MAX_VALID_SEGMENTS
                        ),
                        0,
                    )
                    for segment in range(number_valid_segments):
                        direction.append(df[f"{sg_drv_dir}{segment}"].values[i + 1])

                    found_valid_segment = True
                    break

            for i, _value in enumerate(direction[:-1]):
                if direction[i] != direction[i + 1]:
                    number_of_strokes += 1

            # Set condition strings
            cond_0 = " ".join(
                "Parking state should be set to PPC_SCANNING_IN                "
                f" ({constants.ParkingMachineStates.PPC_SCANNING_IN}) in signal {signal_name[sg_parking_mode]}.".split()
            )
            cond_1 = " ".join(
                "Parking state should be set to PPC_PERFORM_PARKING                "
                f" ({constants.ParkingMachineStates.PPC_PERFORM_PARKING}) in signal                "
                f" {signal_name[sg_parking_mode]}.".split()
            )
            cond_2 = " ".join("Scanning and parking should occur one after the other.".split())
            cond_3 = " ".join(
                f"At least one valid segment should be available in signal {signal_name[sg_valid_segments]}.".split()
            )
            cond_4 = " ".join(
                "Number of planned strokes should be <=                "
                f" {constants.ConstantsNbPlannedStrokes.THRESHOLD_STROKES}.".split()
            )

            if scanning_in.any():
                eval_cond[0] = True
            if performing_parking.any():
                eval_cond[1] = True
            if found_valid_segment:
                eval_cond[2] = True
            if number_valid_segments > 0:
                eval_cond[3] = True
            if number_of_strokes <= constants.ConstantsNbPlannedStrokes.THRESHOLD_STROKES:
                eval_cond[4] = True

            if eval_cond[4] is True:
                result_final = fc.PASS
            else:
                result_final = fc.FAIL

            # Set table dataframe
            signal_summary = pd.DataFrame(
                {
                    "Conditions": {
                        "0": cond_0,
                        "1": cond_1,
                        "2": cond_2,
                        "3": cond_3,
                        "4": cond_4,
                    },
                    "Result": {
                        "0": (
                            " ".join(
                                f"Parking state PPC_SCANNING_IN ({constants.ParkingMachineStates.PPC_SCANNING_IN})     "
                                "               was found.".split()
                            )
                            if eval_cond[0]
                            else " ".join(
                                "Parking state PPC_SCANNING_IN                    "
                                f" ({constants.ParkingMachineStates.PPC_SCANNING_IN}) was not found.".split()
                            )
                        ),
                        "1": (
                            " ".join(
                                "Parking state PPC_PERFORM_PARKING"
                                f" ({constants.ParkingMachineStates.PPC_PERFORM_PARKING})                    was found.".split()
                            )
                            if eval_cond[1]
                            else " ".join(
                                "Parking state PPC_PERFORM_PARKING                    "
                                f" ({constants.ParkingMachineStates.PPC_PERFORM_PARKING}) was not found.".split()
                            )
                        ),
                        "2": (
                            "Scanning and parking should occur one after the other."
                            if eval_cond[2]
                            else "Scanning and parking did not occur one after the other."
                        ),
                        "3": (
                            "At least one valid segment is available."
                            if eval_cond[3]
                            else "No valid segment was found."
                        ),
                        "4": (
                            " ".join(f'"Number of planned strokes is {number_of_strokes}.'.split())
                            if eval_cond[4]
                            else " ".join(
                                f"Number of planned strokes is {number_of_strokes} (instead of  <=                    "
                                f" {constants.ConstantsNbPlannedStrokes.THRESHOLD_STROKES}).".split()
                            )
                        ),
                    },
                    "Verdict": {
                        "0": "PASSED" if eval_cond[0] else "ACCEPTABLE",
                        "1": "PASSED" if eval_cond[1] else "ACCEPTABLE",
                        "2": "PASSED" if eval_cond[2] else "ACCEPTABLE",
                        "3": "PASSED" if eval_cond[3] else "ACCEPTABLE",
                        "4": "PASSED" if eval_cond[4] else "FAILED",
                    },
                }
            )

            # Create table with eval conditions from the summary dataframe
            sig_sum = go.Figure(
                data=[
                    go.Table(
                        columnwidth=[50, 30, 10],
                        header=dict(
                            values=list(signal_summary.columns),
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
            sig_sum.update_layout(
                constants.PlotlyTemplate.lgt_tmplt, height=fh.calc_table_height(signal_summary["Conditions"].to_dict())
            )

            plot_titles.append("Condition Evaluation")
            plots.append(sig_sum)
            remarks.append("")

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df[sg_time].values.tolist(),
                    y=df[sg_parking_mode].values.tolist(),
                    mode="lines",
                    name=signal_name[sg_parking_mode],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df[sg_time].values.tolist(),
                    y=df[sg_valid_segments].values.tolist(),
                    mode="lines",
                    name=signal_name[sg_valid_segments],
                )
            )

            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plot_titles.append("Graphical Overview")
            plots.append(fig)
            remarks.append("")

            additional_results_dict = {
                "Verdict": {"value": result_final.title(), "color": fh.get_color(result_final)},
                "Name": {"value": "HIL Number of strokes"},
                "Expected result [strokes]": {"value": f"<= {constants.ConstantsNbPlannedStrokes.THRESHOLD_STROKES}"},
                "Measured result [strokes]": {"value": number_of_strokes},
            }
        except Exception as err:
            result_final = fc.INPUT_MISSING
            print(str(err))
            # write_log_message(f"Test failed, the following signal is missing:{str(err)}", "error", LOGGER)
            additional_results_dict = {
                "Verdict": {"value": result_final.title(), "color": fh.get_color(result_final)},
                "Name": {"value": f"Signal missing: { str(err)}"},
                "Expected result [strokes]": {"value": ""},
                "Measured result [strokes]": {"value": ""},
            }
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")

        if result_final == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="MF NUMBER OF PLANNED STROKES",
    description=(
        "Computes the number of planned strokes for the parking manoeuvre. This is achieved by checking when the"
        " parking mode is PPC_SCANNING_IN and PPC_PERFORM_PARKING (in signal"
        " M7board.EM_Thread.PSMDebugPort.stateVarPPC_nu), then computing the number of valid segments. For each"
        " segment, a driving direction signal is appended. The planned number of strokes is the number of times the"
        " driving direction changes from one index to the next one."
    ),
)
class FtParkingNbPlannedStrokes(TestCase):
    """Test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtParkingNbPlannedStrokes]
