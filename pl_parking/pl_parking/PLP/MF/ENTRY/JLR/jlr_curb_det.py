"""KPI for curb detection."""

import logging
import operator
import os
import sys

import pandas as pd
from tsf.core.results import DATA_NOK, Result
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.io.signals import SignalDefinition

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "HIL_curb_generic"


class StoreStepVerdicts:
    """Store the verdicts of the first step to use in the additional table in the 2nd step."""

    step_1 = fc.NOT_ASSESSED


class ValidationSignals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        distdir_tuples = "distdir_tuples"
        dista_dir = "dista_dir"
        velocity = "Velocity"
        number_of_objects = "numberOfStaticObjects_u8"
        TIMESTAMP = "Timestamp"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["M7board", "SIM VFB"]

        self._properties = {
            self.Columns.velocity: [
                ".EM_Thread.EgoMotionPort.vel_mps",
                # ".SiCoreGeneric.m_egoMotionPort.vel_mps"
            ],
            self.Columns.number_of_objects: [
                ".EM_Thread.CollEnvModelPort.numberOfStaticObjects_u8",
                # ".SiCoreGeneric.m_collisionEnvironmentModelPort.numberOfStaticObjects_u8",
            ],
            self.Columns.distdir_tuples: [
                ".EM_Thread.UsProcessingDistanceList.distdir_m[0]",
                ".Usp1.distListOutput.distdir_m[0]",
                ".Usp1.distListOutput.distdir_m",
            ],
        }


signals_obj = ValidationSignals()
verdict_obj = StoreStepVerdicts()


def highlight_segments(fig, signal, direction, time, fillcolor):
    """
    Highlight continuous segments where the vehicle is moving in a specified direction on a Plotly figure.

    Parameters:
    fig (plotly.graph_objects.Figure): The Plotly figure to which the vertical rectangles will be added.
    signal (list): The signal indicating the velocity of the vehicle.
    direction (str): The direction of movement to highlight ("Forwards" or "Backwards").
    time (list): The time signal corresponding to the velocity values.
    fillcolor (str): The color to fill the rectangles.

    Returns:
    None
    """
    ops = {
        "Forwards": operator.gt,
        "Backwards": operator.lt,
    }
    scanning = []
    start_scan = None
    for idx in range(len(signal)):
        if ops[direction](signal[idx], 0):
            if start_scan is None:
                start_scan = time[idx]
            end = time[idx]
        else:
            if start_scan is not None:
                scanning.append([start_scan, end])
                start_scan = None
    if start_scan is not None:
        scanning.append([start_scan, end])

    for segment in scanning:
        fig.add_vrect(
            x0=segment[0],
            x1=segment[1],
            fillcolor=fillcolor,
            line_width=0,
            opacity=0.4,
            # annotation_text=annotation_text,
            layer="below",
        )
    fig.add_annotation(
        dict(
            font=dict(color="black", size=12),
            x=0,
            y=-0.12,
            showarrow=False,
            text=f"Highlited area represent the time when the car moves {direction.lower()}",
            textangle=0,
            xanchor="left",
            xref="paper",
            yref="paper",
        )
    )


def max_and_idx(a, b):
    """Return the maximum value and the index of the maximum value."""
    if a > b:
        return a, 0
    else:
        return b, 1


def ordinal(n):
    """Handling the exceptions for 11th, 12th, and 13th"""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        # Mapping last digits to appropriate suffixes
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

    return str(n) + suffix


class BaseStep(TestStep):
    """Teststep that contains all generic functions that can be used by other test steps"""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        try:
            self.result.details.update(
                {
                    "Plots": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )

            df = self.readers[SIGNAL_DATA]
            self.test_result = fc.NOT_ASSESSED  # Result
            self.result.measured_result = DATA_NOK

            plots = []

            sig_name_idx = 0

            distances2 = []
            distances3 = []
            eval_cond = []
            eval_strings = []
            signal_used = []
            signal_summary = {"Signals": {}, "Evaluation": {}, "Result": {}}

            df[signals_obj.Columns.velocity] *= constants.GeneralConstants.MPS_TO_KMPH
            df[signals_obj.Columns.TIMESTAMP] = df.index
            df[signals_obj.Columns.TIMESTAMP] -= df[signals_obj.Columns.TIMESTAMP].iat[0]
            df[signals_obj.Columns.TIMESTAMP] /= constants.GeneralConstants.US_IN_S

            if kwargs["direction"] == "Forwards":
                mask_velocity = df[signals_obj.Columns.velocity] > 0
            else:
                mask_velocity = df[signals_obj.Columns.velocity] < 0

            number_of_obj = df[signals_obj.Columns.number_of_objects].tolist()

            time_signal = df[signals_obj.Columns.TIMESTAMP].tolist()
            velocity = df[signals_obj.Columns.velocity].apply(lambda x: round(x, 3)).values.tolist()

            # Combine all collumns into one that contains the distdir_m[0] to distdir_m[3] as a list and drop the original columns
            combined_list = [
                (signals_obj.Columns.distdir_tuples, i) for i in range(constants.ENTRY_HIL_CONSTANTS.NUMBER_OF_SENSORS)
            ]
            df[signals_obj.Columns.dista_dir] = df[combined_list].apply(lambda row: row.values.tolist(), axis=1)
            df = df.drop(columns=combined_list)

            distances2 = df[signals_obj.Columns.dista_dir].apply(lambda x: x[kwargs["idx"][0]]).values.tolist()
            distances3 = df[signals_obj.Columns.dista_dir].apply(lambda x: x[kwargs["idx"][1]]).values.tolist()

            # Divide by 2 because the values come from ultrasonic sensors and are doubled
            distances2fig = [round((distances2[i] / 2), 3) for i in range(len(distances2))]
            distances3fig = [round(distances3[i] / 2, 3) for i in range(len(distances3))]

            mask_obj_detected = (
                df[signals_obj.Columns.number_of_objects].rolling(2).apply(lambda x: x[0] < x[1], raw=True)
            )
            timestamp_obj_detected = [row for row, val in mask_obj_detected.items() if val == 1]
            idx_to_iterate = [list(df.index).index(timestamp) for timestamp in timestamp_obj_detected]

            for i in idx_to_iterate:
                if mask_velocity.iat[i]:
                    max_n, idx_n = max_and_idx(distances3fig[i], distances2fig[i])
                    signal_used.append(
                        f"Check the {ordinal(number_of_obj[i])} object detection (when \
                            {signals_obj._properties[signals_obj.Columns.number_of_objects][sig_name_idx]} is {number_of_obj[i]})."
                    )
                    if max_n >= constants.CurbDetectionKpi.THRESHOLD:

                        eval_cond.append(fc.PASS)
                        eval_strings.append(
                            " ".join(
                                f"An object was detected by\
                                {signals_obj._properties[signals_obj.Columns.distdir_tuples][sig_name_idx].replace('0', str(kwargs['idx'][idx_n]))} \
                                at timestamp {round(time_signal[i],3)} [s], at the distance of \
                                {max_n} [m] when the velocity was {abs(velocity[i])} [km/h].".split()
                            )
                        )
                    else:

                        eval_cond.append(fc.FAIL)
                        if max_n == 0:
                            eval_strings.append(
                                " ".join(
                                    f"No object was detected by UDP ({signals_obj._properties[signals_obj.Columns.distdir_tuples][sig_name_idx].replace('0', str(kwargs['idx'][0]))} = 0 AND {signals_obj._properties[signals_obj.Columns.distdir_tuples][sig_name_idx].replace('0', str(kwargs['idx'][1]))} = 0) at timestamp {round(time_signal[i],3)} [s] (no object detected).".split()
                                )
                            )
                        else:
                            eval_strings.append(
                                " ".join(
                                    f"An object was detected by\
                                {signals_obj._properties[signals_obj.Columns.distdir_tuples][sig_name_idx].replace('0', str(kwargs['idx'][idx_n]))} \
                                at timestamp {round(time_signal[i],3)} [s], when the velocity was {abs(velocity[i])} [km/h] at the distance of \
                                {max_n} [m], <b>which is below threshold ({constants.CurbDetectionKpi.THRESHOLD} [m])</b>.".split()
                                )
                            )

            if len(eval_cond) == 0:
                eval_strings.append(
                    f"Evaluation not possible, no objects detected in {signals_obj._properties[signals_obj.Columns.number_of_objects][sig_name_idx]}."
                )
                eval_cond.append(fc.NOT_ASSESSED)
                signal_used.append("Because no object was detected, data from UDP detections is not evaluated.")
                self.test_result = fc.NOT_ASSESSED
                self.result.measured_result = DATA_NOK
            elif all(eval != fc.FAIL for eval in eval_cond) and len(eval_cond) > 0:
                self.test_result = fc.PASS
                self.result.measured_result = Result(100, unit="%")
            else:
                self.result.measured_result = Result(0, unit="%")
                self.test_result = fc.FAIL

            for idx, string in enumerate(eval_strings):
                signal_summary["Evaluation"].setdefault(idx, string)
                signal_summary["Result"].setdefault(idx, eval_cond[idx].upper())
                signal_summary["Signals"].setdefault(idx, signal_used[idx])
            signal_summary = pd.DataFrame(signal_summary)

            remark = f"Evaluation of UDP ({signals_obj._properties[signals_obj.Columns.distdir_tuples][sig_name_idx].replace('0', str(kwargs['idx'][0]))}, {signals_obj._properties[signals_obj.Columns.distdir_tuples][sig_name_idx].replace('0', str(kwargs['idx'][1]))}) using static objects from {signals_obj._properties[signals_obj.Columns.number_of_objects][sig_name_idx]}."
            self.sig_sum = fh.build_html_table(signal_summary, remark)
            plots.append(self.sig_sum)
            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(
                    x=time_signal,
                    y=distances2fig,
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.distdir_tuples][sig_name_idx].replace(
                        "0", str(kwargs["idx"][0])
                    ),
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=time_signal,
                    y=distances3fig,
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.distdir_tuples][sig_name_idx].replace(
                        "0", str(kwargs["idx"][1])
                    ),
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=time_signal,
                    y=velocity,
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.velocity][sig_name_idx],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=time_signal,
                    y=number_of_obj,
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.number_of_objects][sig_name_idx],
                )
            )
            self.fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
            )
            highlight_segments(self.fig, velocity, kwargs["direction"], time_signal, "LightSalmon")
            # Horizontal rectangle for highlighting the threshold region
            self.fig.add_hrect(
                y0=constants.CurbDetectionKpi.THRESHOLD,  # The bottom of the rectangle
                y1=(constants.CurbDetectionKpi.THRESHOLD + 0.05),  # The top of the rectangle
                line_width=0,  # No border
                fillcolor="green",  # Fill color
                opacity=1.0,  # Transparency level
            )
            # Add an annotation for tooltip explanation
            self.fig.add_annotation(
                xref="paper",  # Use paper coordinates
                yref="y",  # Use y-axis coordinates
                x=1.15,  # Position the tooltip on the right side
                y=(constants.CurbDetectionKpi.THRESHOLD + 0.1),  # Centered vertically
                text=f"Horizontal green line represents the threshold <b>{constants.CurbDetectionKpi.THRESHOLD}<b> [m]",  # Tooltip text
                showarrow=True,  # Show arrow pointing to the rectangle
                arrowhead=2,  # Style of the arrow
                ax=20,  # X offset for the arrow
                ay=0,  # Y offset for the arrow
                bgcolor="rgba(255, 255, 255, 0.7)",  # Background color of the tooltip
                bordercolor="black",  # Border color of the tooltip
                borderwidth=1,  # Border width of the tooltip
                borderpad=4,  # Padding around the tooltip text
            )

            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            plots.append(self.fig)

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=1,
    name="Forward direction",
    description="Only scenarios where the vehicle is moving forwards are considered.",
    expected_result="> 90 %",
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class StepForwards(BaseStep):
    """Test step class"""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        super().process(idx=constants.CurbDetectionKpi.FORWARD_SENSOR_LIST, direction="Forwards")

        verdict_obj.step1 = self.test_result


@teststep_definition(
    step_number=2,
    name="Backward direction",
    description="Only scenarios where the vehicle is moving backwards are considered.",
    expected_result="> 90 %",
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class StepBackwards(BaseStep):
    """Test step class"""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        super().process(idx=constants.CurbDetectionKpi.BACKWARD_SENSOR_LIST, direction="Backwards")

        final_verdict = fc.NOT_ASSESSED
        if verdict_obj.step1 == fc.FAIL or self.test_result == fc.FAIL:
            final_verdict = fc.FAIL
        elif verdict_obj.step1 == fc.NOT_ASSESSED and self.test_result == fc.NOT_ASSESSED:
            final_verdict = fc.NOT_ASSESSED
        else:
            final_verdict = fc.PASS
        additional_results_dict = {
            "Forwards": {"value": verdict_obj.step1.title(), "color": fh.get_color(verdict_obj.step1)},
            "Backwards": {"value": self.test_result.title(), "color": fh.get_color(self.test_result)},
            "Verdict": {"value": final_verdict.title(), "color": fh.get_color(final_verdict)},
        }

        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="Approching curb KPI",
    description=f"Check if the curb is detected. A pass verdict is givben if the curb is detected at {constants.CurbDetectionKpi.THRESHOLD} or more meters.",
)
@register_inputs("/parking-M7")
class CurbDetectionKpi(TestCase):
    """Example test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [StepForwards, StepBackwards]
