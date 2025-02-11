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
            self.Columns.FrameTimeout: "CM.vCUS.FTi.Sensor[1].Pdcm.E2E.FrameTimeout",
            self.Columns.EnableReq: "CM.vCUS.FTi.EnableReq",
            self.Columns.IgnitionOn: "CM.VehInput05.IgnitionOn",
            self.Columns.ego_x: "CM.Car.tx",
            self.Columns.ego_y: "CM.Car.ty",
            self.Columns.ego_angle_rad: "CM.Car.Yaw",
            self.Columns.timestamps: "timestamps",
        }


SIGNALS_OBJ = ValidationSignals()
REGISTER = "INIT_TO_IRREV_ERROR"


@teststep_definition(
    step_number=1,
    name="INIT_TO_IRREV_ERROR",
    description="AP function state related signal shall indicate irreversible error after USS Timeout injection",
    expected_result=BooleanResult(TRUE),
)
@register_signals(REGISTER, ValidationSignals)
class CheckInitToIrrevError(TestStep):
    """CheckInitToIrrevError Test Step."""

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
        frame_timeout_signal = reader_data[signal_aliases.FrameTimeout].tolist()
        enable_req_signal = reader_data[signal_aliases.EnableReq].tolist()
        ignition_on_signal = reader_data[signal_aliases.IgnitionOn].tolist()

        ego_x_signal = reader_data[signal_aliases.ego_x].tolist()
        ego_y_signal = reader_data[signal_aliases.ego_y].tolist()

        irreversible_error_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_IRREVERSIBLE_ERROR

        # ===== Prepare evaluation - END =====

        # ===== Creating plots - START =====

        # create plot of relevant signals
        signals_plot = go.Figure()

        for name, values in (
            (signal_names.get(signal_aliases.ego_x), ego_x_signal),
            (signal_names.get(signal_aliases.ego_y), ego_y_signal),
            (signal_names.get(signal_aliases.AP_state), ap_state_signal),
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

        result_aggregator = []  # summary of each individual test steps
        step_key = _strip_str(
            f"Time between error injection time and irreversible error registering time shall be below 10[sec].<br/>"
            f"Error injection time: where {signal_names.get(signal_aliases.FrameTimeout)} is set to -1.<br/>"
            f"irreversible error registering time: where {signal_names.get(signal_aliases.AP_state)} is set to {irreversible_error_value}."
        )
        error_injection_subwindow = support.signal_equals(frame_timeout_signal, -1)
        irreversible_error_detected_subwindow = support.signal_equals(ap_state_signal, irreversible_error_value)

        irreversible_error_detected_time = None
        error_injection_starts_time = None

        if not error_injection_subwindow:
            evaluation_steps[step_key] = _strip_str(
                "Failed; Error injection start time not registered during the measurement"
            )
            result_aggregator.append(False)
        else:
            error_injection_starts_time = time_signal_in_sec[error_injection_subwindow[0]]

        if not irreversible_error_detected_subwindow:
            evaluation_steps[step_key] = _strip_str("Failed; Irreversible error not registered during the measurement")
            result_aggregator.append(False)
        else:
            irreversible_error_detected_time = time_signal_in_sec[irreversible_error_detected_subwindow[0]]

        if error_injection_subwindow and irreversible_error_detected_subwindow:
            irreversible_error_registering_time = irreversible_error_detected_time - error_injection_starts_time
            irreversible_error_within_time_limit = irreversible_error_registering_time < 10  # [sec]

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
    name="INIT_TO_IRREV_ERROR",
    description=("AP function state related signal shall indicate irreversible error after Timeout injection."),
)
class InitToIrrevError(TestCase):
    """InitToIrrevError Test Case."""

    custom_report = fh.MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CheckInitToIrrevError,
        ]
