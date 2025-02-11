"""check if slot offered for parking and ego fully parked into slot"""

import logging
import os
import sys

import plotly.graph_objects as go
from shapely import Polygon, affinity, box, difference
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

        HMI_offered_slot = "HMI_offered_slot"

        AP_state = "Parking procedure CTRL state"

        ego_angle_rad = "Ego vehicle orientation"
        ego_x = "Ego vehicle reference point x"
        ego_y = "Ego vehicle reference point y"

        rp_0_x = "parking slot reference point 0 x"
        rp_0_y = "parking slot reference point 0 y"

        rp_1_x = "parking slot reference point 1 x"
        rp_1_y = "parking slot reference point 1 y"

        rp_2_x = "parking slot reference point 2 x"
        rp_2_y = "parking slot reference point 2 y"

        rp_3_x = "parking slot reference point 3 x"
        rp_3_y = "parking slot reference point 3 y"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_offered_slot: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInSituationLeft.ParkingSlotFreeLeft",
            self.Columns.AP_state: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.ego_angle_rad: "CM.Car.Yaw",
            self.Columns.ego_x: "CM.Car.tx",
            self.Columns.ego_y: "CM.Car.ty",
            self.Columns.rp_0_x: "CM.Traffic.rp_0.tx",
            self.Columns.rp_0_y: "CM.Traffic.rp_0.ty",
            self.Columns.rp_1_x: "CM.Traffic.rp_1.tx",
            self.Columns.rp_1_y: "CM.Traffic.rp_1.ty",
            self.Columns.rp_2_x: "CM.Traffic.rp_2.tx",
            self.Columns.rp_2_y: "CM.Traffic.rp_2.ty",
            self.Columns.rp_3_x: "CM.Traffic.rp_3.tx",
            self.Columns.rp_3_y: "CM.Traffic.rp_3.ty",
        }


SIGNALS_OBJ = ValidationSignals()
REGISTER = "SLOT_LEFT_PARK_IN_FULLY"


@teststep_definition(
    step_number=1,
    name="Driver's side detection and parking check",
    description="check if slot offered for parking and ego fully parked into slot",
    expected_result=BooleanResult(TRUE),
)
@register_signals(REGISTER, ValidationSignals)
class DetectSlotOnDriversSideParkInFullyCheck(TestStep):
    """DetectSlotOnDriversSideParkInFullyCheck Test Step."""

    custom_report = fh.MfHilClCustomTeststepReport

    def __init__(self):
        """Init test."""
        super().__init__()

    def process(self, **kwargs):
        """
        This function processes the recorded signal from measurement file, set the result of the test,
        generate plots and additional results.
        """
        self.result.details.update({"Plots": [], "file_name": os.path.basename(self.artifacts[0].file_path)})

        reader_data = self.readers[REGISTER]

        signal_aliases = SIGNALS_OBJ.Columns
        signal_names: dict = SIGNALS_OBJ._properties

        evaluation_steps = {}

        # ===== Prepare evaluation - START =====
        # read signals
        time_signal = reader_data.index
        hmi_offered_signal = reader_data[signal_aliases.HMI_offered_slot].tolist()

        ap_state_signal = reader_data[signal_aliases.AP_state].tolist()

        ego_angle_signal = reader_data[signal_aliases.ego_angle_rad].tolist()
        ego_x_signal = reader_data[signal_aliases.ego_x].tolist()
        ego_y_signal = reader_data[signal_aliases.ego_y].tolist()

        rp_0_x_signal = reader_data[signal_aliases.rp_0_x].tolist()
        rp_0_y_signal = reader_data[signal_aliases.rp_0_y].tolist()
        rp_1_x_signal = reader_data[signal_aliases.rp_1_x].tolist()
        rp_1_y_signal = reader_data[signal_aliases.rp_1_y].tolist()
        rp_2_x_signal = reader_data[signal_aliases.rp_2_x].tolist()
        rp_2_y_signal = reader_data[signal_aliases.rp_2_y].tolist()
        rp_3_x_signal = reader_data[signal_aliases.rp_3_x].tolist()
        rp_3_y_signal = reader_data[signal_aliases.rp_3_y].tolist()

        # create shapes of ego and slot
        ego_shape_list, slot_shape_list = [], []
        ego_exterior_list, slot_exterior_list = [], []
        ego_width = constants.SlotOffer.VehicleDimensions.VEHICLE_WIDTH
        ego_length = constants.SlotOffer.VehicleDimensions.VEHICLE_LENGTH
        for idx, ego_angle in enumerate(ego_angle_signal):
            ego_x = ego_x_signal[idx]
            ego_y = ego_y_signal[idx]

            ego_shape = box(ego_x, ego_y - ego_width / 2.0, ego_x + ego_length, ego_y + ego_width / 2.0)

            ego_shape_list.append(
                ego_shape := affinity.rotate(ego_shape, ego_angle, origin=(ego_x, ego_y), use_radians=True)
            )

            ego_x_ext, ego_y_ext = ego_shape.exterior.xy
            ego_exterior_list.append((list(ego_x_ext), list(ego_y_ext)))

            slot_shape_list.append(
                slot_shape := Polygon(
                    [
                        (rp_0_x_signal[idx], rp_0_y_signal[idx]),
                        (rp_1_x_signal[idx], rp_1_y_signal[idx]),
                        (rp_2_x_signal[idx], rp_2_y_signal[idx]),
                        (rp_3_x_signal[idx], rp_3_y_signal[idx]),
                    ]
                ).minimum_rotated_rectangle
            )  # rectangle needed because RPs might not come in polygon-compatible order

            slot_x_ext, slot_y_ext = slot_shape.exterior.xy
            slot_exterior_list.append((list(slot_x_ext), list(slot_y_ext)))

        # find scanning phase
        ap_state_value_dict = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE
        scan_in_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN
        parking_in_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING

        scanning_starts = next((i_ for i_, v_ in enumerate(ap_state_signal) if v_ == scan_in_value), None)
        scanning_ends = next((i_ for i_, v_ in enumerate(ap_state_signal[::-1]) if v_ == scan_in_value), None)

        if scanning_ends is not None:
            scanning_ends = len(ap_state_signal) - scanning_ends

        # get number of detected slots
        # signal should be greater than zero during scanning phase
        detected_slots = max(hmi_offered_signal[scanning_starts:scanning_ends])

        # find end of parking phase
        parking_in_ends = next((i_ for i_, v_ in enumerate(ap_state_signal[::-1]) if v_ == parking_in_value), None)

        if parking_in_ends is not None:
            parking_in_ends = len(ap_state_signal) - parking_in_ends

        if parking_in_ends:
            final_shape_ego = ego_shape_list[parking_in_ends]
            final_shape_slot = slot_shape_list[parking_in_ends]
        else:
            final_shape_ego = ego_shape_list[-1]
            final_shape_slot = slot_shape_list[-1]

        fully_parked = difference(final_shape_ego, final_shape_slot).area == 0
        # ===== Prepare evaluation - END =====

        # ===== Creating plots - START =====
        # create plot of ego and slot shapes in time
        shapes_plot = fh.HilClFuntions.create_slider_graph(
            target_boxes=ego_exterior_list, wz_polygons=slot_exterior_list, timestamps=time_signal
        )

        shapes_plot.update_layout(
            title=dict(text="<b>parking slot and ego vehicle positions in time</b>", font=dict(size=30), x=0),
            yaxis=dict(scaleanchor="x"),
            margin_b=200,
        )

        # create plot of relevant signals
        signals_plot = go.Figure()

        for name, values in (
            (signal_names.get(signal_aliases.AP_state), ap_state_signal),
            (signal_names.get(signal_aliases.HMI_offered_slot), hmi_offered_signal),
        ):
            signals_plot.add_trace(go.Scatter(x=time_signal, y=values, mode="lines", name=name))

        signals_plot.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14",  title="Time [s]"))
        signals_plot.update_layout(PlotlyTemplate.lgt_tmplt)
        signals_plot.update_layout(
            title=dict(text="<b>relevant CAN signals</b>", font=dict(size=30), x=0), margin_b=200
        )
        # ===== Creating plots - END =====

        # ===== Evaluation - START =====
        def _strip_str(input: str):
            return " ".join(input.split())

        failed = False

        step_key = _strip_str(
            f"scanning phase shall be present in measurement: "
            f"value {ap_state_value_dict.get(scan_in_value)} ( {scan_in_value} ) "
            f"should be present in {signal_names.get(signal_aliases.AP_state)}"
        )

        if not scanning_starts:  # stop evaluation
            unique_values = ", ".join([f"{ap_state_value_dict.get(v_)} ( {v_} )" for v_ in set(ap_state_signal)])

            evaluation_steps[step_key] = _strip_str(
                f"{ap_state_value_dict.get(scan_in_value)} is NOT present, unique values: {unique_values}"
            )

            failed = True
        else:  # continue evaluation
            evaluation_steps[step_key] = _strip_str(f"{ap_state_value_dict.get(scan_in_value)} is present")

            step_key = _strip_str(
                "number of detected parking slots shall be greater than 0 at some point during scanning phase"
            )
            evaluation_steps[step_key] = _strip_str(f"number of slots: {detected_slots}")

            if not detected_slots:  # stop evaluation
                failed = True
            else:  # continue evaluation
                step_key = _strip_str("ego shall be fully parked inside offered parking slot")
                evaluation_steps[step_key] = _strip_str(f"ego is fully parked: {fully_parked}")

                if not fully_parked:
                    failed = True
        # ===== Evaluation - END =====

        if failed:
            test_result = fc.FAIL
            self.result.measured_result = FALSE
        else:
            test_result = fc.PASS
            self.result.measured_result = TRUE

        eval_table_plot = fh.HilClFuntions.hil_convert_dict_to_pandas(evaluation_steps)

        for plot in [eval_table_plot, signals_plot, shapes_plot]:
            if isinstance(plot, go.Figure):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)

        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
        }

        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="Driver's side detection and parking",
    description=(
        "The AP function shall offer a free parking slot, if it is located on the driver's side of the ego vehicle. "
        "Ego shall fully park in inside the slot."
    ),
)
class DetectSlotOnDriversSideParkInFully(TestCase):
    """DetectSlotOnDriversSide Test Case."""

    custom_report = fh.MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            DetectSlotOnDriversSideParkInFullyCheck,
        ]
