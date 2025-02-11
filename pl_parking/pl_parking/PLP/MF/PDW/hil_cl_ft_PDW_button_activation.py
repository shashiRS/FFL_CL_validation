"""Park Distance Warning - evaluation script"""

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
from pl_parking.common_ft_helper import MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.constants import PlotlyTemplate

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "PDW_BUTTON_ACTIVATION"


class ValidationSignals(MDFSignalDefinition):
    """Example signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        TIMESTAMP = "mts_ts"
        SPEED = "Car_speed"
        ROAD = "Car_road"
        PARK_BRAKE = "Park_Brake"
        PARK_BRAKE_STATE = "Park_Brake_State"
        GEAR_MAN = "Gear_man"
        GEAR_AUT = "Gear_auto"
        PDW_CAN_STATE = "PDW_State"
        WHEEL_DIRECTION_FL = "Wheel_direction_FL"
        WHEEL_DIRECTION_RR = "Wheel_direction_RR"
        VEH_VELOCITY = "Vehicle_velocity"
        PED_BRAKE = "Pedal_brake"
        PDW_BUTTON = "PDW_Button"
        IGNITION = "Veh_ignition"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.SPEED: "MTS.MTA_ADC5.EM_DATA.EmEgoMotionPort.vel_mps",
            self.Columns.PARK_BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.ParkBrake",
            self.Columns.PARK_BRAKE_STATE: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.StateParkBrake",
            self.Columns.GEAR_MAN: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActualGear",
            self.Columns.GEAR_AUT: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActGearPos",
            self.Columns.PDW_CAN_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.PDCInfo.PDCSystemState",
            self.Columns.WHEEL_DIRECTION_FL: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput04.WheelDrivingDirectionFL",
            self.Columns.WHEEL_DIRECTION_RR: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput04.WheelDrivingDirectionRR",
            self.Columns.VEH_VELOCITY: "MTS.ADAS_CAN.Conti_Veh_CAN.VehVelocity.VehVelocityExt",
            self.Columns.PED_BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.DriverBraking",
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
            self.Columns.PDW_BUTTON: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
        }


example_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="PDW_button_activation_by_button",
    description="If the PDW button is pressed, the PDW function shall become active.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PDWButtonActivation(TestStep):
    """Example test step"""

    custom_report = MfHilClCustomTeststepReport

    def __init__(self):
        super().__init__()

    def process(self, **kwargs):
        """Process"""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        read_data = self.readers[SIGNAL_DATA]
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index.tolist()
        pdw_state = read_data["PDW_State"].tolist()
        pdw_button = read_data["PDW_Button"].tolist()
        veh_ignition = read_data["Veh_ignition"].tolist()

        # Variables used in the evaluation
        button_pressed = False
        eval_status_ok = None
        FTTI_time = 0
        start_waiting = 0

        evaluation1 = f"The evaluation of {signal_name['PDW_State']} is PASSED, PDW State switched to the desired state after preconditions were met"

        """Evaluation part"""

        # Go through each signal value based on the measurement's timestamp
        for frame in range(0, len(time_signal)):
            if not start_waiting:
                # Check if IG is ON and our function is not in failure state
                if veh_ignition[frame] and pdw_state[frame] != constants.HilCl.PDW.States.FAILURE:
                    # Check if PDW button is pressed
                    if pdw_button[frame] == constants.HilCl.PDW.Button.PDW_TAP_ON:
                        button_pressed = True
                        start_waiting = 1  # Start waiting after button is pressed

                    if button_pressed:
                        if not FTTI_time:  # Start waiting for FTTI time
                            start_waiting = 1
                        else:
                            # Check if PDW state has switched to ACTIVATED_BY_BUTTON
                            if pdw_state[frame] != constants.HilCl.PDW.States.ACTIVATED_BY_BUTTON:
                                eval_status_ok = False
                                break
                            else:
                                eval_status_ok = True
                                FTTI_time = 0
                else:
                    break
            else:
                # FTTI time delay
                FTTI_time += time_signal[frame] - time_signal[frame - 1]
                if FTTI_time >= 600000:  # 600ms - system FTTI
                    start_waiting = 0

        if eval_status_ok is None:
            eval_cond = [False]
            evaluation1 = f"The evaluation of {signal_name['PDW_State']} is FAILED, preconditions were not fulfilled"
        elif eval_status_ok is False:
            eval_cond = [False]
            evaluation1 = (
                f"The evaluation of {signal_name['PDW_State']} is FAILED, PDW State did not switch to the "
                f"desired state after preconditions were met"
            )
        else:
            eval_cond = [True]

        signal_summary["PDW state - reactivation if a certain condition was fulfilled"] = evaluation1

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if plot function is activated"""
        fig = go.Figure()
        # Graphic signals
        fig.add_trace(go.Scatter(x=time_signal, y=pdw_state, mode="lines", name=signal_name["PDW_State"]))
        fig.add_trace(go.Scatter(x=time_signal, y=pdw_button, mode="lines", name=signal_name["PDW_Button"]))
        fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[us]")
        fig.update_layout(PlotlyTemplate.lgt_tmplt)

        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

        """Calculate parameters for additional table"""
        sw_compatibility = "swfw_apu_adc5-2.1.0-DR2-PLP-B1-PAR230"

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            "Preconditions": {"value": evaluation1, "color": "grey"},
            "SW_used": {"value": sw_compatibility, "color": "grey"},
        }

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

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
    name="PDW_button_activation",
    description="If the PDW button is pressed, the PDW function shall become active.",
)
class PdwButtonActivation(TestCase):
    """Example test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PDWButtonActivation,
        ]
