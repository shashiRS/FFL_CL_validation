"""Parallel parking In, AP function shall not maneuver the vehicle out more than d_7 = {AP_G_MAN_AREA_PAR_IN_D7_M} relative to the final parking pose"""

import logging
import os
import sys

import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
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
from pl_parking.common_ft_helper import HilClFuntions, MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.constants import PlotlyTemplate

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "PAR_PARK_IN_MAN_FIRST_STROKE"

__author__ = "uig14850"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        CAR_TX = "Car_tx"
        CAR_TY = "Car_ty"
        CAR_GEAR = "Gear"
        HEADING_ANGLE = "Heading_angle"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.CAR_TX: "CM.Car.tx",
            self.Columns.CAR_TY: "CM.Car.ty",
            self.Columns.CAR_GEAR: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActualGear",
            self.Columns.HEADING_ANGLE: "CM.Car.Yaw",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Distance from final parking pose after first reverse stroke",
    description="Check ego vehicle leaves allowd area or not",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupParInFirstRevAreaCheck(TestStep):
    """AupParInFirstRevAreaCheck Test Step."""

    custom_report = MfHilClCustomTeststepReport

    def __init__(self):
        """Init test."""
        super().__init__()

    def process(self, **kwargs):
        """
        This function processes the recorded signal from measurement file, set the result of the test,
        generate plots and additional results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        read_data = self.readers[SIGNAL_DATA]
        test_result = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        """Prepare sinals and variables"""
        time_signal = read_data.index
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()
        car_tx_sig = read_data["Car_tx"].tolist()
        car_ty_sig = read_data["Car_ty"].tolist()
        car_gear_sig = read_data["Gear"].tolist()
        car_yaw_sig = read_data["Heading_angle"].tolist()

        t_maneuvering_idx = None
        t_reverse_gear_idx = None
        t_end_of_first_stroke = None
        t_parking_finished = None

        enable_slider_graph = False

        evaluation_steps = {}

        """Evaluation part"""

        # Find when ego starts maneuvering
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_maneuvering_idx = cnt
                break

        # Find reverse in maneuvering
        for cnt in range(t_maneuvering_idx or 0, len(car_gear_sig)):
            if car_gear_sig[cnt] == constants.HilCl.VehCanActualGear.REVERSE_ACTUALGEAR:
                t_reverse_gear_idx = cnt
                break

        # Find end of first stroke
        for cnt in range(t_reverse_gear_idx or 0, len(car_gear_sig)):
            if car_gear_sig[cnt] != constants.HilCl.VehCanActualGear.REVERSE_ACTUALGEAR:
                t_end_of_first_stroke = cnt
                break

        # Find end of maneuvering
        for cnt in range(t_maneuvering_idx or 0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS:
                t_parking_finished = cnt
                break

        if t_maneuvering_idx and t_reverse_gear_idx and t_end_of_first_stroke and t_parking_finished:
            enable_slider_graph = True

            # Calculate and check area
            eval_cond, maneuver_area, ego = HilClFuntions.maneuver_area_check(
                positions_x=car_tx_sig[t_end_of_first_stroke:t_parking_finished],
                positions_y=car_ty_sig[t_end_of_first_stroke:t_parking_finished],
                heading_angle=car_yaw_sig[t_end_of_first_stroke:t_parking_finished],
                ego_length=constants.SlotOffer.VehicleDimensions.VEHICLE_LENGTH,
                ego_width=constants.SlotOffer.VehicleDimensions.VEHICLE_WIDTH,
                left_d=constants.HilCl.ManeuveringArea.AP_G_MAN_AREA_PAR_IN_D7_M,
                rear_d=5,
                right_d=5,
                front_d=5,
                parking_pos_x=car_tx_sig[t_parking_finished],
                parking_pos_y=car_ty_sig[t_parking_finished],
            )
            step_key = " ".join("System shall execute parking maneuver in defined area".split())

            if all(eval_cond):
                test_result = fc.PASS
                evaluation_steps[step_key] = " ".join(
                    "The evaluation is PASSED, ego vehicle does not leave the designated maneuvering area.".split()
                )
            else:
                test_result = fc.FAIL
                evaluation_steps[step_key] = " ".join(
                    "The evaluation is FAILED, ego vehicle leaves the designated maneuvering area.".split()
                )

        # Handle issues
        if t_maneuvering_idx is None:
            test_result = fc.FAIL

            step_key = " ".join(
                f"System shall start maneuvering: {signal_name['State_on_HMI']}"
                f" shall switch to PPC_PERFORM_PARKING"
                f" ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})".split()
            )
            evaluation_steps[step_key] = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal state never switched to PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}))."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        if t_reverse_gear_idx is None:
            test_result = fc.FAIL

            step_key = " ".join(
                "System shall switch gear to R after begining of Maneuvering:"
                f" {signal_name['Gear']} signal shall switch to REVERSE_ACTUALGEAR"
                f" ({constants.HilCl.VehCanActualGear.REVERSE_ACTUALGEAR})".split()
            )

            evaluation_steps[step_key] = " ".join(
                f"The evaluation of {signal_name['Gear']} signal is FAILED, signal state never switched to REVERSE_ACTUALGEAR ({constants.HilCl.VehCanActualGear.REVERSE_ACTUALGEAR})."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )
        if t_end_of_first_stroke is None:
            test_result = fc.FAIL

            step_key = " ".join(
                "System shall finish first stroke:"
                f" {signal_name['Gear']} signal shall switch out from REVERSE_ACTUALGEAR"
                f" ({constants.HilCl.VehCanActualGear.REVERSE_ACTUALGEAR})".split()
            )

            evaluation_steps[step_key] = " ".join(
                f"The evaluation of {signal_name['Gear']} signal is FAILED, signal state never switched out from REVERSE_ACTUALGEAR ({constants.HilCl.VehCanActualGear.REVERSE_ACTUALGEAR})."
                " Ego vehicle never finished first stroke."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )
        if t_parking_finished is None:
            test_result = fc.FAIL
            step_key = " ".join(
                "System shall finish parking maneuver:"
                f" {signal_name['State_on_HMI']} signal shall switch out from PPC_SUCCESS"
                f" ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS})".split()
            )

            evaluation_steps[step_key] = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal state never switched to PPC_SUCCESS ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS})."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(evaluation_steps)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        fig = go.Figure()

        if enable_slider_graph:
            shapes_plot = fh.HilClFuntions.create_slider_graph(
                target_boxes=ego, wz_polygons=maneuver_area, timestamps=time_signal
            )

            shapes_plot.update_layout(
                title=dict(text="<b>parking slot and ego vehicle positions in time</b>", font=dict(size=30), x=0),
                yaxis=dict(scaleanchor="x"),
                margin_b=200,
            )

        fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=car_gear_sig, mode="lines", name=signal_name["Gear"]))

        fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
        fig.update_layout(PlotlyTemplate.lgt_tmplt, title="Measured signals")

        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

        """Calculate parameters to additional table"""

        """Add the data in the table from Functional Test Filter Results"""
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


@testcase_definition(
    name="Maneuvering after first reverse stroke",
    description="After the first reverse stroke into the parallel parking slot has been completed,"
    f" the AP function shall not maneuver the vehicle out more than"
    f" d_7 = {constants.HilCl.ManeuveringArea.AP_G_MAN_AREA_PAR_IN_D7_M} relative to the final parking pose",
)
class AupParInFirstRevArea(TestCase):
    """AupParInFirstRevArea Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupParInFirstRevAreaCheck,
        ]
