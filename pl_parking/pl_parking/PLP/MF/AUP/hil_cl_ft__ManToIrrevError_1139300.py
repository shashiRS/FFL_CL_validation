"""AP function state related signal shall indicate irreversible error after USS Timeout injection."""

import logging
import os
import sys

import plotly.graph_objects as go
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.io.mdf import MDFSignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.PLP.MF.constants import PlotlyTemplate

__author__ = "jozsef.banyasz (uif89959)"

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)


TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        AP_state = "Parking procedure CTRL state"
        APHMIOutUserActionHU = "APHMIOutUserActionHU"
        FrameTimeout = "Frame timeout"
        EnableReq = "Enable Req"
        IgnitionOn = "Ignition On"

        ego_x = "Ego vehicle reference point x"
        ego_y = "Ego vehicle reference point y"
        ego_angle_rad = "Ego vehicle orientation"

        timestamps = "timestamps"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.AP_state: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.APHMIOutUserActionHU: "CM.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.FrameTimeout: "CM.vCUS.FTi.Sensor[1].Pdcm.E2E.FrameTimeout",
            self.Columns.EnableReq: "CM.vCUS.FTi.EnableReq",
            self.Columns.IgnitionOn: "CM.VehInput05.IgnitionOn",
            self.Columns.ego_x: "CM.Car.tx",
            self.Columns.ego_y: "CM.Car.ty",
            self.Columns.ego_angle_rad: "CM.Car.Yaw",
            self.Columns.timestamps: "timestamps",
        }


SIGNALS_OBJ = ValidationSignals()
REGISTER = "MAN_TO_IRREV_ERROR"


@teststep_definition(
    step_number=1,
    name="MAN_TO_IRREV_ERROR",
    description="AP function state related signal shall indicate irreversible error after USS Timeout injection",
    expected_result=BooleanResult(TRUE),
)
@register_signals(REGISTER, ValidationSignals)
class CheckManToIrrevError(TestStep):
    """CheckManToIrrevError Test Step."""

    custom_report = fh.MfHilClCustomTeststepReport

    def __init__(self):
        """Init test."""
        super().__init__()

    @fh.HilClFuntions.log_exceptions
    def process(self, **kwargs):
        """
        This function processes the recorded signal from measurement file, set the result of the test,
        generate plots and additional results.
        """
        self.result.details.update({"Plots": [], "file_name": os.path.basename(self.artifacts[0].file_path)})
        reader_data = self.readers[REGISTER]
        support = fh.HilClFuntions

        signal_aliases = SIGNALS_OBJ.Columns
        signal_names: dict = SIGNALS_OBJ._properties
        evaluation_steps = {}

        # read signals
        time_signal_in_ms = reader_data[signal_aliases.timestamps]
        time_signal_in_sec = round(time_signal_in_ms / 10**6, 3).tolist()
        ap_state_signal = reader_data[signal_aliases.AP_state].tolist()
        APHMIOutUserActionHU_signal = reader_data[signal_aliases.APHMIOutUserActionHU].tolist()
        frame_timeout_signal = reader_data[signal_aliases.FrameTimeout].tolist()
        enable_req_signal = reader_data[signal_aliases.EnableReq].tolist()
        ignition_on_signal = reader_data[signal_aliases.IgnitionOn].tolist()

        ego_x_signal = reader_data[signal_aliases.ego_x].tolist()
        ego_y_signal = reader_data[signal_aliases.ego_y].tolist()

        irreversible_error_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_IRREVERSIBLE_ERROR
        parking_in_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING

        # ===== Prepare evaluation - END =====

        # ===== Creating plots - START =====

        # create plot of relevant signals
        signals_plot = go.Figure()

        for name, values in (
            (signal_names.get(signal_aliases.ego_x), ego_x_signal),
            (signal_names.get(signal_aliases.ego_y), ego_y_signal),
            (signal_names.get(signal_aliases.AP_state), ap_state_signal),
            (signal_names.get(signal_aliases.APHMIOutUserActionHU), APHMIOutUserActionHU_signal),
            (signal_names.get(signal_aliases.IgnitionOn), ignition_on_signal),
            (signal_names.get(signal_aliases.FrameTimeout), frame_timeout_signal),
            (signal_names.get(signal_aliases.EnableReq), enable_req_signal),
        ):
            signals_plot.add_trace(go.Scatter(x=time_signal_in_sec, y=values, mode="lines", name=name))

        signals_plot.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14", title="Time [s]"))
        signals_plot.update_layout(PlotlyTemplate.lgt_tmplt)
        signals_plot.update_layout(title=dict(text="<b>Relevant signals</b>", font=dict(size=30), x=0), margin_b=200)
        # ===== Creating plots - END =====

        # ===== Evaluation - START =====
        def _strip_str(input_str: str):
            """Removes extra-whitespaces, unnecessary escape chars, etc"""
            return " ".join(input_str.split())

        def get_highliting_rectangle(start_date, end_date, fillcolor="blue", opacity=0.15):
            return dict(
                type="rect",
                xref="x",
                yref="paper",
                x0=start_date,
                y0=0,
                x1=end_date,
                y1=1,
                fillcolor=fillcolor,
                opacity=opacity,
                layer="below",
                line_width=0,
            )

        result_aggregator = []  # summary of each individual test steps
        step_key = _strip_str("'Parking in' phase shall be observable within the measurement")
        parking_in_starts_subwindow = support.signal_equals(ap_state_signal, parking_in_value)

        irreversible_error_detected_time = None
        error_injection_starts_time = None

        if not parking_in_starts_subwindow:
            evaluation_steps[step_key] = _strip_str("Failed; 'Parking in' phase not registered during the measurement")
            result_aggregator.append(False)
        else:

            parking_in_starts_idx = parking_in_starts_subwindow[0]
            highlight_eval_area_start = time_signal_in_sec[parking_in_starts_idx]
            highlight_eval_area_end = time_signal_in_sec[-1]

            highlighter = [get_highliting_rectangle(highlight_eval_area_start, highlight_eval_area_end)]
            signals_plot.update_layout(shapes=highlighter)

            evaluation_steps[step_key] = _strip_str(
                f"'Parking in' phase detected starting from {highlight_eval_area_start}[sec]<br/>(highlighted in summary plot)"
            )
            step_key = _strip_str(
                f"Time between error injection time and irreversible error registering time shall be below 10[sec].<br/>"
                f"Error injection time: where {signal_names.get(signal_aliases.FrameTimeout)} is set to -1.<br/>"
                f"irreversible error registering time: where {signal_names.get(signal_aliases.AP_state)} is set to {irreversible_error_value}."
            )
            # --- CHECK FOR ERROR INJECTION SEGMENT WITHIN PARKING OK SUBWINDOW---

            error_injection_subwindow = support.signal_equals(frame_timeout_signal, -1)
            irreversible_error_detected_subwindow = support.signal_equals(ap_state_signal, irreversible_error_value)

            if not error_injection_subwindow:
                evaluation_steps[step_key] = _strip_str(
                    "Failed; Error injection start time not registered during the measurement"
                )
                result_aggregator.append(False)
            else:
                error_injection_starts_time = time_signal_in_sec[error_injection_subwindow[0]]

            if not irreversible_error_detected_subwindow:
                evaluation_steps[step_key] = _strip_str(
                    "Failed; Irreversible error not registered during the measurement"
                )
                result_aggregator.append(False)
            else:
                irreversible_error_detected_time = time_signal_in_sec[irreversible_error_detected_subwindow[0]]

            if error_injection_subwindow and irreversible_error_detected_subwindow:
                irreversible_error_registering_time = irreversible_error_detected_time - error_injection_starts_time
                irreversible_error_within_time_limit = irreversible_error_registering_time < 10  # [sec]

                # --- CHECK FOR EXPECTED RESULT---
                if not irreversible_error_within_time_limit:
                    evaluation_steps[step_key] = _strip_str(
                        f"Failed; measured time: {irreversible_error_registering_time}[sec]"
                    )
                    result_aggregator.append(False)
                else:
                    result_aggregator.append(True)
                    evaluation_steps[step_key] = _strip_str(
                        f"Passed; measured time: {irreversible_error_registering_time}[sec]"
                    )

        # ===== Evaluation - END =====

        if not all(result_aggregator):
            test_result = fc.FAIL
            self.result.measured_result = FALSE
        else:
            test_result = fc.PASS
            self.result.measured_result = TRUE

        eval_table_plot = support.hil_convert_dict_to_pandas(evaluation_steps)

        for plot in [eval_table_plot, signals_plot]:
            if isinstance(plot, go.Figure):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)

        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
        }

        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="MAN_TO_IRREV_ERROR",
    description=("AP function state related signal shall indicate irreversible error after Timeout injection."),
)
class ManToIrrevError(TestCase):
    """ManToIrrevError Test Case."""

    custom_report = fh.MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CheckManToIrrevError,
        ]
