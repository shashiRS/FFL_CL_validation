"""Ego vehicle rear wheel must not intersect with the obstacle moved to the designated parking slot."""

import logging
import os
import sys
from math import sqrt

import plotly.graph_objects as go
from shapely import affinity, box, intersects
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

        ego_x = "Ego vehicle reference point x"
        ego_y = "Ego vehicle reference point y"
        ego_angle_rad = "Ego vehicle orientation"

        obstacle_x = "Origin x coordinate of the placed traffic obstacle"
        obstacle_y = "Origin y coordinate of the placed traffic obstacle"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.AP_state: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.ego_x: "CM.Car.tx",
            self.Columns.ego_y: "CM.Car.ty",
            self.Columns.ego_angle_rad: "CM.Car.Yaw",
            self.Columns.obstacle_x: "CM.Traffic.obstacle.tx",
            self.Columns.obstacle_y: "CM.Traffic.obstacle.ty",
        }


SIGNALS_OBJ = ValidationSignals()
REGISTER = "PREVENT_COLLISION_W_BODY_TRAV_OBJ"


@teststep_definition(
    step_number=1,
    name="PREVENT_COLLISION_W_BODY_TRAV_OBJ",
    description="Prevent collision of tires against a body traversible object placed in the designated parking slot",
    expected_result=BooleanResult(TRUE),
)
@register_signals(REGISTER, ValidationSignals)
class CheckPreventCollisionWBodyTraversibleObject(TestStep):
    """CheckPreventCollisionWBodyTraversibleObject Test Step."""

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
        support = fh.HilClFuntions

        signal_aliases = SIGNALS_OBJ.Columns
        signal_names: dict = SIGNALS_OBJ._properties
        evaluation_steps = {}

        # read signals
        time_signal = reader_data.index
        ap_state_signal = reader_data[signal_aliases.AP_state].tolist()

        ego_x_signal = reader_data[signal_aliases.ego_x].tolist()
        ego_y_signal = reader_data[signal_aliases.ego_y].tolist()
        ego_angle_signal = reader_data[signal_aliases.ego_angle_rad].tolist()

        obstacle_x_signal = reader_data[signal_aliases.obstacle_x].tolist()
        obstacle_y_signal = reader_data[signal_aliases.obstacle_y].tolist()

        # create shapes
        ego_shape_list, obstacle_shape_list = [], []
        ego_exterior_list, obstacle_exterior_list = [], []

        WHEEL_DIAMETER_RADIUS_MODIFIER = 0.01  # [m]
        ego_wheel_diameter = constants.ConstantsSlotDetection.WHEEL_DIAMETER
        ego_width = constants.SlotOffer.VehicleDimensions.VEHICLE_WIDTH
        ego_length = constants.SlotOffer.VehicleDimensions.VEHICLE_LENGTH
        ego_rear_axle_modifier = constants.HilCl.CarShape.CAR_R_AXLE_TO_HITCH
        ego_front_axle_modifier = constants.HilCl.CarShape.CAR_F_AXLE_TO_FRONT
        obstacle_length = constants.BodyTraversibleObjectTestConstants.OBSTACLE_LENGTH
        obstacle_height = constants.BodyTraversibleObjectTestConstants.OBSTACLE_HEIGHT
        obstacle_width = constants.BodyTraversibleObjectTestConstants.OBSTACLE_WIDTH

        # eq of a circle is:
        #   x^2 + y^2 = r^2
        # by substituting knows items (with wheel radius compensated with an additional +1cm due to TC design decisions):
        #   x^2 + obstacle_height^2 = (wheel_diameter/2)^2
        #   x^2 + 0.15^2 = 0.334^2
        # after some math:
        #   x = +-sqrt(0.334^2-0.15^2)
        #   x = 0.2984 [m] (the x axis distance from the center of the wheel (== axle) to the contact point in case of a 0.15m tall object)
        wheel_contact_modifier = sqrt(
            (ego_wheel_diameter / 2 + WHEEL_DIAMETER_RADIUS_MODIFIER) ** 2 - obstacle_height**2
        )

        for idx, ego_angle in enumerate(ego_angle_signal):
            ego_x = ego_x_signal[idx]
            ego_y = ego_y_signal[idx]

            obstacle_x = obstacle_x_signal[idx]
            obstacle_y = obstacle_y_signal[idx]

            # NOTE: ego shape in this case is not "veh rear to veh front", but "contact point of rear wheel to contact point of front wheel"
            ego_shape = box(
                ego_x + ego_rear_axle_modifier - wheel_contact_modifier,
                ego_y - ego_width / 2.0,
                ego_x + ego_length - ego_front_axle_modifier + wheel_contact_modifier,
                ego_y + ego_width / 2.0,
            )
            obstacle_shape = box(
                obstacle_x,
                obstacle_y - obstacle_width / 2.0,
                obstacle_x + obstacle_length,
                obstacle_y + obstacle_width / 2.0,
            )

            ego_shape_list.append(
                ego_shape := affinity.rotate(ego_shape, ego_angle, origin=(ego_x, ego_y), use_radians=True)
            )

            obstacle_shape_list.append(
                obstacle_shape := affinity.rotate(
                    obstacle_shape, angle=0, origin=(obstacle_x, obstacle_y), use_radians=True
                )
            )
            ego_x_ext, ego_y_ext = ego_shape.exterior.xy
            obstacle_x_ext, obstacle_y_ext = obstacle_shape.exterior.xy

            ego_exterior_list.append((list(ego_x_ext), list(ego_y_ext)))
            obstacle_exterior_list.append((list(obstacle_x_ext), list(obstacle_y_ext)))

        ap_state_value_dict = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE
        parking_in_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING
        parking_failed_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED

        # valuable measurement idx subwindow
        parking_in_starts_idx = support.signal_equals(ap_state_signal, parking_in_value)[0]
        end_of_test_idx = len(time_signal) - 1

        # check if parking has failed within the valuable subwindow
        active_parking_subwindow = ap_state_signal[parking_in_starts_idx:end_of_test_idx]
        parking_failed_exists = parking_failed_value in active_parking_subwindow
        # ===== Prepare evaluation - END =====

        # ===== Creating plots - START =====
        # create plot of shapes

        shapes_plot = support.create_slider_graph(
            target_boxes=ego_exterior_list, wz_polygons=obstacle_exterior_list, timestamps=time_signal
        )

        shapes_plot.update_layout(
            title=dict(
                text="<b>Obstacle and ego vehicle relevant wheel contact point positions in time</b>",
                font=dict(size=30),
                x=0,
            ),
            yaxis=dict(scaleanchor="x"),
            margin_b=200,
        )

        # create plot of relevant CAN signals
        signals_plot = go.Figure()

        for name, values in (
            (signal_names.get(signal_aliases.AP_state), ap_state_signal),
            (signal_names.get(signal_aliases.ego_x), ego_x_signal),
            (signal_names.get(signal_aliases.ego_y), ego_y_signal),
            (signal_names.get(signal_aliases.ego_angle_rad), ego_angle_signal),
        ):
            signals_plot.add_trace(go.Scatter(x=time_signal, y=values, mode="lines", name=name))

        signals_plot.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14", title="Time [s]"))
        signals_plot.update_layout(PlotlyTemplate.lgt_tmplt)
        signals_plot.update_layout(
            title=dict(text="<b>relevant CAN signals</b>", font=dict(size=30), x=0), margin_b=200
        )
        # ===== Creating plots - END =====

        # ===== Evaluation - START =====
        def _strip_str(input_str: str):
            """Removes extra-whitespaces, unnecessary escape chars, etc"""
            return " ".join(input_str.split())

        step_key = _strip_str(
            f"Start of parking shall be present in measurement: "
            f"value {ap_state_value_dict.get(parking_in_value)} ( {parking_in_value} ) "
            f"should be present in {signal_names.get(signal_aliases.AP_state)}"
        )

        result_aggregator = []  # summary of each individual test steps
        if not parking_in_starts_idx:
            evaluation_steps[step_key] = _strip_str(f"{ap_state_value_dict.get(parking_in_value)} is NOT observable")
            result_aggregator.append(False)
        else:
            result_aggregator.append(True)
            evaluation_steps[step_key] = _strip_str(f"{ap_state_value_dict.get(parking_in_value)} is observable")

            step_key = _strip_str(
                f"Once parking is in progress, until the end of the measurement file: "
                f"value {ap_state_value_dict.get(parking_failed_value)} ( {parking_failed_value} ) "
                f"should be present in {signal_names.get(signal_aliases.AP_state)}"
            )
            if not parking_failed_exists:
                evaluation_steps[step_key] = _strip_str(
                    f"{ap_state_value_dict.get(parking_failed_value)} is NOT observable"
                )
                result_aggregator.append(False)  # failed
            else:
                result_aggregator.append(True)
                evaluation_steps[step_key] = _strip_str(
                    f"{ap_state_value_dict.get(parking_failed_value)} is observable"
                )

            no_intersect_detected = True not in intersects(ego_shape_list, obstacle_shape_list)
            result_aggregator.append(no_intersect_detected)

            step_key = _strip_str(
                "Ego vehicle rear wheel must not intersect with the obstacle moved to the designated parking slot (see below plot for obstacle vs. ego vehicle positions in time)"
            )
            evaluation_steps[step_key] = _strip_str(f"{no_intersect_detected}")

        # ===== Evaluation - END =====

        if not all(result_aggregator):
            test_result = fc.FAIL
            self.result.measured_result = FALSE
        else:
            test_result = fc.PASS
            self.result.measured_result = TRUE

        eval_table_plot = support.hil_convert_dict_to_pandas(evaluation_steps)

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
class PreventCollisionWBodyTraversibleObject(TestCase):
    """DetectSlotOnDriversSide Test Case."""

    custom_report = fh.MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CheckPreventCollisionWBodyTraversibleObject,
        ]
