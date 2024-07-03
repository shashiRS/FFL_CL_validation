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

SIGNAL_DATA = "PDW_DEACTIVATION_BY_EPB"


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
        PDW_STANDSTILL_AUTOACTIVATION = "PDW_standstill_autoactivation"
        PDW_DEACTV_BY_EPB = "Deactv_by_EPB"
        FRONT1_CRITICAL_LEVEL = "Front1_Critical_Level"
        FRONT2_CRITICAL_LEVEL = "Front2_Critical_Level"
        FRONT3_CRITICAL_LEVEL = "Front3_Critical_Level"
        FRONT4_CRITICAL_LEVEL = "Front4_Critical_Level"
        LEFT1_CRITICAL_LEVEL = "Left1_Critical_Level"
        LEFT2_CRITICAL_LEVEL = "Left2_Critical_Level"
        LEFT3_CRITICAL_LEVEL = "Left3_Critical_Level"
        LEFT4_CRITICAL_LEVEL = "Left4_Critical_Level"
        REAR1_CRITICAL_LEVEL = "Rear1_Critical_Level"
        REAR2_CRITICAL_LEVEL = "Rear2_Critical_Level"
        REAR3_CRITICAL_LEVEL = "Rear3_Critical_Level"
        REAR4_CRITICAL_LEVEL = "Rear4_Critical_Level"
        RIGHT1_CRITICAL_LEVEL = "Right1_Critical_Level"
        RIGHT2_CRITICAL_LEVEL = "Right2_Critical_Level"
        RIGHT3_CRITICAL_LEVEL = "Right3_Critical_Level"
        RIGHT4_CRITICAL_LEVEL = "Right4_Critical_Level"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.SPEED: "MTS.ADC5xx_Device.EM_DATA.EmEgoMotionPort.vel_mps",
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
            self.Columns.PDW_STANDSTILL_AUTOACTIVATION: "MTS.ADC5xx_Device.CFG_DATA.MF_DWF_APP_Parameter.PDW_L_AUTOM_ACTIV_STANDSTILL_NU",
            self.Columns.PDW_DEACTV_BY_EPB: "MTS.ADC5xx_Device.CFG_DATA.MF_DWF_APP_Parameter.PDW_L_DEACTIV_BY_EPB_NU",
            self.Columns.PDW_BUTTON: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.FRONT1_CRITICAL_LEVEL: "MTS.AP_Private_CAN.AP_Private_CAN.PDCFrontAndLeft.PDCFront1CriticalLevel",
            self.Columns.FRONT2_CRITICAL_LEVEL: "MTS.AP_Private_CAN.AP_Private_CAN.PDCFrontAndLeft.PDCFront2CriticalLevel",
            self.Columns.FRONT3_CRITICAL_LEVEL: "MTS.AP_Private_CAN.AP_Private_CAN.PDCFrontAndLeft.PDCFront3CriticalLevel",
            self.Columns.FRONT4_CRITICAL_LEVEL: "MTS.AP_Private_CAN.AP_Private_CAN.PDCFrontAndLeft.PDCFront4CriticalLevel",
            self.Columns.LEFT1_CRITICAL_LEVEL: "MTS.AP_Private_CAN.AP_Private_CAN.PDCFrontAndLeft.PDCLeft1CriticalLevel",
            self.Columns.LEFT2_CRITICAL_LEVEL: "MTS.AP_Private_CAN.AP_Private_CAN.PDCFrontAndLeft.PDCLeft2CriticalLevel",
            self.Columns.LEFT3_CRITICAL_LEVEL: "MTS.AP_Private_CAN.AP_Private_CAN.PDCFrontAndLeft.PDCLeft3CriticalLevel",
            self.Columns.LEFT4_CRITICAL_LEVEL: "MTS.AP_Private_CAN.AP_Private_CAN.PDCFrontAndLeft.PDCLeft4CriticalLevel",
            self.Columns.REAR1_CRITICAL_LEVEL: "MTS.AP_Private_CAN.AP_Private_CAN.PDCRearAndRight.PDCRear1CriticalLevel",
            self.Columns.REAR2_CRITICAL_LEVEL: "MTS.AP_Private_CAN.AP_Private_CAN.PDCRearAndRight.PDCRear2CriticalLevel",
            self.Columns.REAR3_CRITICAL_LEVEL: "MTS.AP_Private_CAN.AP_Private_CAN.PDCRearAndRight.PDCRear3CriticalLevel",
            self.Columns.REAR4_CRITICAL_LEVEL: "MTS.AP_Private_CAN.AP_Private_CAN.PDCRearAndRight.PDCRear4CriticalLevel",
            self.Columns.RIGHT1_CRITICAL_LEVEL: "MTS.AP_Private_CAN.AP_Private_CAN.PDCRearAndRight.PDCRight1CriticalLevel",
            self.Columns.RIGHT2_CRITICAL_LEVEL: "MTS.AP_Private_CAN.AP_Private_CAN.PDCRearAndRight.PDCRight2CriticalLevel",
            self.Columns.RIGHT3_CRITICAL_LEVEL: "MTS.AP_Private_CAN.AP_Private_CAN.PDCRearAndRight.PDCRight3CriticalLevel",
            self.Columns.RIGHT4_CRITICAL_LEVEL: "MTS.AP_Private_CAN.AP_Private_CAN.PDCRearAndRight.PDCRight4CriticalLevel",
        }


example_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="PDW -no transition from OFF state",
    description=(
        "This step is checking if PDW state remains OFF when trying to switch to an active state with a certain feature is enabled."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PDW_deactivation_by_EPB_standstill(TestStep):
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
        test_result = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index.tolist()
        park_brake = read_data["Park_Brake"].tolist()
        park_brake_state = read_data["Park_Brake_State"].tolist()
        gear_manual = read_data["Gear_man"].tolist()
        gear_automatic = read_data["Gear_auto"].tolist()
        pdw_state = read_data["PDW_State"].tolist()
        fl_wheel_direction = read_data["Wheel_direction_FL"].tolist()
        rr_wheel_direction = read_data["Wheel_direction_RR"].tolist()
        veh_velocity = read_data["Vehicle_velocity"].tolist()
        pedal_brake = read_data["Pedal_brake"].tolist()
        pdw_button = read_data["PDW_Button"].tolist()
        veh_ignition = read_data["Veh_ignition"].tolist()
        pdw_deactv_by_epb = read_data["Deactv_by_EPB"].tolist()
        # pdw_standstill_autoact = read_data["PDW_standstill_autoactivation"].tolist()
        # front1 = read_data["Front1_Critical_Level"].tolist()
        # front2 = read_data["Front2_Critical_Level"].tolist()
        # front3 = read_data["Front3_Critical_Level"].tolist()
        # front4 = read_data["Front4_Critical_Level"].tolist()
        # left1 = read_data["Left1_Critical_Level"].tolist()
        # left2 = read_data["Left2_Critical_Level"].tolist()
        # left3 = read_data["Left3_Critical_Level"].tolist()
        # left4 = read_data["Left4_Critical_Level"].tolist()
        # rear1 = read_data["Rear1_Critical_Level"].tolist()
        # rear2 = read_data["Rear2_Critical_Level"].tolist()
        # rear3 = read_data["Rear3_Critical_Level"].tolist()
        # rear4 = read_data["Rear4_Critical_Level"].tolist()
        # right1 = read_data["Right1_Critical_Level"].tolist()
        # right2 = read_data["Right2_Critical_Level"].tolist()
        # right3 = read_data["Right3_Critical_Level"].tolist()
        # right4 = read_data["Right4_Critical_Level"].tolist()
        # Variables used in the evaluation
        trigger1 = None
        trigger2 = None
        trigger3 = None
        trigger4 = None
        trigger5 = None
        trigger6 = None
        eval_status_ok = None
        FTTI_time = 0
        start_waiting = 0

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['PDW_State']} is PASSED. "
            f" PDW state remained OFF after trying to switch to an active state with EPB engaged('Deactivation by EPB(electronic park brake)' feature enabled)".split()
        )

        """Evaluation part"""

        # Function to see whether we have at least one object around the ego considered by PDW
        # def ObjectDetection(frame):
        #     if (
        #         front1[frame] > 0
        #         or front2[frame] > 0
        #         or front3[frame] > 0
        #         or front4[frame] > 0
        #         or left1[frame] > 0
        #         or left2[frame] > 0
        #         or left3[frame] > 0
        #         or left4[frame] > 0
        #         or rear1[frame] > 0
        #         or rear2[frame] > 0
        #         or rear3[frame] > 0
        #         or rear4[frame] > 0
        #         or right1[frame] > 0
        #         or right2[frame] > 0
        #         or right3[frame] > 0
        #         or right4[frame] > 0
        #     ):
        #         return True
        #     else:
        #         return False
        # Go through each signal value based on the measurement's timestamp
        for frame in range(0, len(time_signal)):
            # delay used only when necessary
            if not start_waiting:
                # Check if IG is ON and our function is not in failure state
                if veh_ignition[frame] and pdw_state[frame] != constants.HilCl.PDW.States.FAILURE:
                    trigger1 = True
                    # Check 'deactivation by EPB(electronic parking brake)' parameter is True
                    if pdw_deactv_by_epb[frame]:
                        trigger2 = True
                        # Check if the vehicle is standstill
                        if veh_velocity[frame] < abs(constants.HilCl.PDW.Thresholds.MIN_SPEED_THRESHOLD_MPS):
                            trigger3 = True
                            if (
                                (
                                    # gear not in reverse gear
                                    gear_manual[frame] != constants.HilCl.PDW.Gear.Manual.REVERSE
                                    or gear_automatic[frame] != constants.HilCl.PDW.Gear.Automatic.REVERSE
                                )
                                and (
                                    # gear not in parking gear
                                    gear_manual[frame] != constants.HilCl.PDW.Gear.Manual.PARK
                                    or gear_automatic[frame] != constants.HilCl.PDW.Gear.Automatic.PARK
                                )
                                and (
                                    # gear not invalid
                                    gear_manual[frame] != constants.HilCl.PDW.Gear.Manual.INVALID
                                    or gear_automatic[frame] != constants.HilCl.PDW.Gear.Automatic.INVALID
                                )
                                # EPB engaged and status is valid
                                and park_brake[frame]
                                and park_brake_state[frame] == constants.HilCl.PDW.EPB_state.VALID
                            ):
                                trigger4 = True
                                if not FTTI_time and trigger5 is None:
                                    start_waiting = 1
                                else:
                                    if pdw_state[frame] != constants.HilCl.PDW.States.OFF:  # PDW state shall be OFF
                                        trigger5 = False
                                        break
                                    else:
                                        trigger5 = True
                                        FTTI_time = 0
                            elif (
                                (
                                    # gear in reverse gear
                                    gear_manual[frame] == constants.HilCl.PDW.Gear.Manual.REVERSE
                                    or gear_automatic[frame] == constants.HilCl.PDW.Gear.Automatic.REVERSE
                                )
                                and park_brake[frame]
                                and park_brake_state[frame] == constants.HilCl.PDW.EPB_state.VALID
                                and trigger5
                            ):
                                trigger6 = True
                                if not FTTI_time and eval_status_ok is None:
                                    start_waiting = 1
                                else:
                                    if pdw_state[frame] != constants.HilCl.PDW.States.OFF:  # PDW state shall reactivate
                                        eval_status_ok = False
                                        break
                                    else:
                                        eval_status_ok = True
                            else:
                                trigger6 = False
                                continue
                        else:
                            trigger3 = False
                            continue
                    else:
                        trigger2 = False
                        continue
                else:
                    trigger1 = False
                    break
            else:
                # FTTI time delay
                FTTI_time += time_signal[frame] - time_signal[frame - 1]
                if FTTI_time >= constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                    start_waiting = 0
        """Check if preconditions were ok"""
        if trigger1 is False:
            preconditions = "Check trigger1! PDW state set to Failure."
        elif trigger2 is False:
            preconditions = "Check trigger2! 'Deactivation by EPB(electronic park Brake)' not enabled."
        elif trigger3 is False:
            preconditions = "Check trigger3! Vehicle not in standstill."
        elif trigger4 is None:
            preconditions = "Check trigger4! Gear not switched to NEUTRAL."
        elif trigger5 is False:
            preconditions = "Check trigger5! PDW did not switch to OFF"
        elif trigger6 is False:
            preconditions = "Check trigger6! PDW did not remain in OFF state"
        else:
            preconditions = "Test ended before evaluation!"

        if eval_status_ok is None:
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['PDW_State']} is FAILED, preconditions were not fulfilled. "
                f"       {preconditions}".split()
            )
        elif eval_status_ok is False:
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['PDW_State']} is FAILED, PDW state did not remained in OFF state "
                f" after trying to switch to an active state with EPB (electronic park brake) engaged ('Deactivation by EPB' feature enabled).".split()
            )
        else:
            eval_cond = [True] * 1

        signal_summary["PDW state -deactivation by EPB active case."] = evaluation1

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        self.sig_sum = fh.HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if plot function is activated"""
        fig = go.Figure()
        # Graphic signals
        fig.add_trace(go.Scatter(x=time_signal, y=veh_velocity, mode="lines", name=signal_name["Vehicle_velocity"]))
        fig.add_trace(go.Scatter(x=time_signal, y=pdw_state, mode="lines", name=signal_name["PDW_State"]))
        fig.add_trace(go.Scatter(x=time_signal, y=park_brake, mode="lines", name=signal_name["Park_Brake"]))
        fig.add_trace(go.Scatter(x=time_signal, y=park_brake_state, mode="lines", name=signal_name["Park_Brake_State"]))
        fig.add_trace(go.Scatter(x=time_signal, y=gear_manual, mode="lines", name=signal_name["Gear_man"]))
        fig.add_trace(go.Scatter(x=time_signal, y=gear_automatic, mode="lines", name=signal_name["Gear_auto"]))
        fig.add_trace(
            go.Scatter(x=time_signal, y=fl_wheel_direction, mode="lines", name=signal_name["Wheel_direction_FL"])
        )
        fig.add_trace(
            go.Scatter(x=time_signal, y=rr_wheel_direction, mode="lines", name=signal_name["Wheel_direction_RR"])
        )
        fig.add_trace(go.Scatter(x=time_signal, y=pedal_brake, mode="lines", name=signal_name["Pedal_brake"]))
        fig.add_trace(go.Scatter(x=time_signal, y=pdw_button, mode="lines", name=signal_name["PDW_Button"]))
        fig.add_trace(go.Scatter(x=time_signal, y=veh_ignition, mode="lines", name=signal_name["Veh_ignition"]))
        fig.add_trace(go.Scatter(x=time_signal, y=pdw_deactv_by_epb, mode="lines", name=signal_name["Deactv_by_EPB"]))
        fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[us]")
        fig.update_layout(PlotlyTemplate.lgt_tmplt)

        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

        """Calculate parameters to additional table"""
        sw_combatibility = (  # Remainder: Update if SW changed and script working well
            "swfw_apu_adc5-2.1.0-DR2-PLP-B1-PAR230"
        )

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            "Preconditions": {"value": preconditions, "color": "grey"},
            "SW_used": {"value": sw_combatibility, "color": "grey"},
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
    name="PDW - 'deactivation by_EPB(electronic parking brake)' feature active.",
    description="PDW transition from active state to OFF state when a certain feature is active while our vehicle is standstill. ",
)
class PdwHil(TestCase):
    """Example test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PDW_deactivation_by_EPB_standstill,
        ]
