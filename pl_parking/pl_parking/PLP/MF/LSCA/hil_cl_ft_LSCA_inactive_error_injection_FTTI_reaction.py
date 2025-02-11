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

__author__ = "uidn2788 - Liviu Macarie"

SIGNAL_DATA = "INPUT_FAILURE_LSCA_INACT_SS_FTTI"


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
        WHEEL_DIRECTION_FL = "Wheel_direction_FL"
        WHEEL_DIRECTION_FR = "Wheel_direction_FR"
        WHEEL_DIRECTION_RL = "Wheel_direction_RL"
        WHEEL_DIRECTION_RR = "Wheel_direction_RR"
        WHEEL_TICKS_FL = "Wheel_ticks_FL"
        WHEEL_TICKS_FR = "Wheel_ticks_FR"
        WHEEL_TICKS_RL = "Wheel_ticks_RL"
        WHEEL_TICKS_RR = "Wheel_ticks_RR"
        WHEEL_TICKS_QF_FL = "Wheel_ticks_QF_FL"
        WHEEL_TICKS_QF_FR = "Wheel_ticks_QF_FR"
        WHEEL_TICKS_QF_RL = "Wheel_ticks_QF_RL"
        WHEEL_TICKS_QF_RR = "Wheel_ticks_QF_RR"
        VEH_VELOCITY = "Vehicle_velocity"
        PED_BRAKE = "Pedal_brake"
        IGNITION = "Veh_ignition"
        USS0_dist = "USS0_dist_to_object"
        USS1_dist = "USS1_dist_to_object"
        USS2_dist = "USS2_dist_to_object"
        USS3_dist = "USS3_dist_to_object"
        USS4_dist = "USS4_dist_to_object"
        USS5_dist = "USS5_dist_to_object"
        USS6_dist = "USS6_dist_to_object"
        USS7_dist = "USS7_dist_to_object"
        USS8_dist = "USS8_dist_to_object"
        USS9_dist = "USS9_dist_to_object"
        USS10_dist = "USS10_dist_to_object"
        USS11_dist = "USS11_dist_to_object"
        ENG_STATE = "Engine_State"
        EPS_STATUS = "EPS_Status"
        FRONT_USS_DEACT = "Front_USS_Deact"
        REAR_USS_DEACT = "Rear_USS_Deact"
        VEH_LONG_ACCEL = "Vehicle_long_accel"
        SERVICE_BRAKE_STATE = "Service_Brake_State"
        GEARBOX_STATE = "Gearbox_State"
        VEH_VELOCITY = "Vehicle_velocity"
        PED_BRAKE = "Pedal_brake"
        IGNITION = "Veh_ignition"
        TP_VEL = "Traffic_velocity"
        AUP_STATE = "AUP_State"
        GEN_SCREEN = "General_screen"
        GEN_MESSAGE = "General_message"
        SECURE_REQ = "Secure_request"
        HOLD_REQ = "Hold_request"
        GEAR_SW_REQ = "Gear_switch_request"
        GEAR_REQ = "Gear_request"
        EMER_HOLD_REQ = "Emergency_hold_request"
        LAT_DMC_REQ = "Lateral_DMC_request"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.SPEED: "MTS.MTA_ADC5.EM_DATA.EmEgoMotionPort.vel_mps",
            self.Columns.PARK_BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.ParkBrake",
            self.Columns.PARK_BRAKE_STATE: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.StateParkBrake",
            self.Columns.GEAR_MAN: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActualGear",
            self.Columns.GEAR_AUT: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActGearPos",
            self.Columns.WHEEL_DIRECTION_FL: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput04.WheelDrivingDirectionFL",
            self.Columns.WHEEL_DIRECTION_FR: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput04.WheelDrivingDirectionFR",
            self.Columns.WHEEL_DIRECTION_RL: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput04.WheelDrivingDirectionRL",
            self.Columns.WHEEL_DIRECTION_RR: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput04.WheelDrivingDirectionRR",
            self.Columns.WHEEL_TICKS_FL: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput04.WheelTicksFL",
            self.Columns.WHEEL_TICKS_FR: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput04.WheelTicksFR",
            self.Columns.WHEEL_TICKS_RL: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput04.WheelTicksRL",
            self.Columns.WHEEL_TICKS_RR: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput04.WheelTicksRR",
            self.Columns.WHEEL_TICKS_QF_FL: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput04.WheelTicksQFFL",
            self.Columns.WHEEL_TICKS_QF_FR: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput04.WheelTicksQFFR",
            self.Columns.WHEEL_TICKS_QF_RL: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput04.WheelTicksQFRL",
            self.Columns.WHEEL_TICKS_QF_RR: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput04.WheelTicksQFRR",
            self.Columns.VEH_VELOCITY: "MTS.ADAS_CAN.Conti_Veh_CAN.VehVelocity.VehVelocityExt",
            self.Columns.PED_BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.DriverBraking",
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
            self.Columns.USS0_dist: "CM.Sensor.Object.USS00.relvTgt.NearPnt.ds_p",
            self.Columns.USS1_dist: "CM.Sensor.Object.USS01.relvTgt.NearPnt.ds_p",
            self.Columns.USS2_dist: "CM.Sensor.Object.USS02.relvTgt.NearPnt.ds_p",
            self.Columns.USS3_dist: "CM.Sensor.Object.USS03.relvTgt.NearPnt.ds_p",
            self.Columns.USS4_dist: "CM.Sensor.Object.USS04.relvTgt.NearPnt.ds_p",
            self.Columns.USS5_dist: "CM.Sensor.Object.USS05.relvTgt.NearPnt.ds_p",
            self.Columns.USS6_dist: "CM.Sensor.Object.USS06.relvTgt.NearPnt.ds_p",
            self.Columns.USS7_dist: "CM.Sensor.Object.USS07.relvTgt.NearPnt.ds_p",
            self.Columns.USS8_dist: "CM.Sensor.Object.USS08.relvTgt.NearPnt.ds_p",
            self.Columns.USS9_dist: "CM.Sensor.Object.USS09.relvTgt.NearPnt.ds_p",
            self.Columns.USS10_dist: "CM.Sensor.Object.USS10.relvTgt.NearPnt.ds_p",
            self.Columns.USS11_dist: "CM.Sensor.Object.USS11.relvTgt.NearPnt.ds_p",
            self.Columns.VEH_VELOCITY: "MTS.ADAS_CAN.Conti_Veh_CAN.VehVelocity.VehVelocityExt",
            self.Columns.ENG_STATE: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput03.EngineState",
            self.Columns.EPS_STATUS: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput01.EPS_Status",
            self.Columns.FRONT_USS_DEACT: "CM.vCUS.FTi.Bus[0].Disable",
            self.Columns.REAR_USS_DEACT: "CM.vCUS.FTi.Bus[1].Disable",
            self.Columns.VEH_LONG_ACCEL: "MTS.ADAS_CAN.Conti_Veh_CAN.VehLongAccel.VehLongAccelExt",
            self.Columns.SERVICE_BRAKE_STATE: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.StateBrakeActLevel",
            self.Columns.GEARBOX_STATE: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.State_ActGearPos",
            self.Columns.PED_BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.DriverBraking",
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
            self.Columns.TP_VEL: "CM.Traffic.T00.LongVel",
            self.Columns.AUP_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.GEN_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
            self.Columns.GEN_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
            self.Columns.HOLD_REQ: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCHoldReq",
            self.Columns.EMER_HOLD_REQ: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCEmergencyHoldRequest",
            self.Columns.GEAR_REQ: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCGearReq",
            self.Columns.GEAR_SW_REQ: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCGearSwitchRequest",
            self.Columns.SECURE_REQ: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCSecureRequest",
            self.Columns.LAT_DMC_REQ: "MTS.ADAS_CAN.Conti_Veh_CAN.AP_DFLaDMCOutput01.LaDMC_Status__nu",
        }


example_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="System input failure, LSCA active",
    description=(
        "This step is checking if the system is reacting within FTTI time once there is an input failure (check ETM testcase description for the specific error)."
    ),
    expected_result=BooleanResult(TRUE),
    doors_url="https://jazz.conti.de/rm4/resources/BI_b4MMAYqaEe62BpLgEHoMZA?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324 , https://jazz.conti.de/rm4/resources/BI_6vPYsIqaEe62BpLgEHoMZA?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class System_safe_state_error_injected_LSCA_inactive_SS(TestStep):
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
        fl_wheel_direction = read_data["Wheel_direction_FL"].tolist()
        fr_wheel_direction = read_data["Wheel_direction_FR"].tolist()
        rl_wheel_direction = read_data["Wheel_direction_RL"].tolist()
        rr_wheel_direction = read_data["Wheel_direction_RR"].tolist()
        fl_wheel_ticks = read_data["Wheel_ticks_FL"].tolist()
        fr_wheel_ticks = read_data["Wheel_ticks_FR"].tolist()
        rl_wheel_ticks = read_data["Wheel_ticks_RL"].tolist()
        rr_wheel_ticks = read_data["Wheel_ticks_RR"].tolist()
        fl_wheel_qf_ticks = read_data["Wheel_ticks_QF_FL"].tolist()
        fr_wheel_qf_ticks = read_data["Wheel_ticks_QF_FR"].tolist()
        rl_wheel_qf_ticks = read_data["Wheel_ticks_QF_RL"].tolist()
        rr_wheel_qf_ticks = read_data["Wheel_ticks_QF_RR"].tolist()
        veh_velocity = read_data["Vehicle_velocity"].tolist()
        pedal_brake = read_data["Pedal_brake"].tolist()
        veh_ignition = read_data["Veh_ignition"].tolist()
        uss0 = read_data["USS0_dist_to_object"].tolist()
        uss1 = read_data["USS1_dist_to_object"].tolist()
        uss2 = read_data["USS2_dist_to_object"].tolist()
        uss3 = read_data["USS3_dist_to_object"].tolist()
        uss4 = read_data["USS4_dist_to_object"].tolist()
        uss5 = read_data["USS5_dist_to_object"].tolist()
        uss6 = read_data["USS6_dist_to_object"].tolist()
        uss7 = read_data["USS7_dist_to_object"].tolist()
        uss8 = read_data["USS8_dist_to_object"].tolist()
        uss9 = read_data["USS9_dist_to_object"].tolist()
        uss10 = read_data["USS10_dist_to_object"].tolist()
        uss11 = read_data["USS11_dist_to_object"].tolist()
        engine_state = read_data["Engine_State"].tolist()
        eps_status = read_data["EPS_Status"].tolist()
        front_uss_deact = read_data["Front_USS_Deact"].tolist()
        rear_uss_deact = read_data["Rear_USS_Deact"].tolist()
        veh_long_acc = read_data["Vehicle_long_accel"].tolist()
        service_brake_state = read_data["Service_Brake_State"].tolist()
        gearbox_state = read_data["Gearbox_State"].tolist()
        veh_velocity = read_data["Vehicle_velocity"].tolist()
        pedal_brake = read_data["Pedal_brake"].tolist()
        veh_ignition = read_data["Veh_ignition"].tolist()
        tp_velocity = read_data["Traffic_velocity"].tolist()
        aup_state = read_data["AUP_State"].tolist()
        general_message = read_data["General_message"].tolist()
        general_screen = read_data["General_screen"].tolist()
        hold_req_AUP = read_data["Hold_request"].tolist()
        emer_hold_req_LSCA = read_data["Emergency_hold_request"].tolist()
        gear_req = read_data["Gear_request"].tolist()
        gear_sw_req = read_data["Gear_switch_request"].tolist()
        secure_req = read_data["Secure_request"].tolist()
        lat_DMC_req = read_data["Lateral_DMC_request"].tolist()
        # Variables used in the evaluation
        trigger1 = None
        trigger2 = None
        trigger3 = None
        trigger4 = None
        eval_status_ok = None
        FTTI_T1 = 0
        t1_idx = None
        t2_idx = None
        val_list = [None] * 4
        init_time = 0

        evaluation1 = " ".join(
            f"The evaluation is PASSED, the system switched to safe state within {constants.HilCl.PDW.FTTI.SAFETY_SS}us after an input error was injected. "
            "<br>The following conditions were met: "
            f"<br>{signal_name['Emergency_hold_request']} remained set to True. "
            f"<br>{signal_name['General_screen']} was set to Diag Error ({constants.HilCl.Hmi.APHMIGeneralScreen.DIAG_ERROR})."
            f"<br>{signal_name['Lateral_DMC_request']} was set to permanent disabled ({constants.MoCo.LaDMC_Status_nu.PERM_DISABLED})."
            f"<br>{signal_name['General_message']} was set to LSCA Unreliable ({constants.HilCl.Hmi.APHMIGeneralMessage.LSCA_UNRELIABLE}).".split()
        )

        """Evaluation part"""

        def eval_check(frame, val_list):
            if general_screen[frame] == constants.HilCl.Hmi.APHMIGeneralScreen.DIAG_ERROR:
                val_list[0] = True
            if general_message[frame] == constants.HilCl.Hmi.APHMIGeneralMessage.LSCA_UNRELIABLE:
                val_list[1] = True
            if lat_DMC_req[frame] == constants.MoCo.LaDMC_Status_nu.PERM_DISABLED:
                val_list[2] = True
            if emer_hold_req_LSCA[frame]:
                val_list[3] = True
            return val_list

        def error_injection_check(frame):
            if (
                fl_wheel_direction[frame] == constants.HilCl.PDW.Veh_Motion.Wheel_dir.INVALID
                or fr_wheel_direction[frame] == constants.HilCl.PDW.Veh_Motion.Wheel_dir.INVALID
                or rl_wheel_direction[frame] == constants.HilCl.PDW.Veh_Motion.Wheel_dir.INVALID
                or rr_wheel_direction[frame] == constants.HilCl.PDW.Veh_Motion.Wheel_dir.INVALID
                or fl_wheel_qf_ticks[frame] == constants.HilCl.PDW.Veh_Motion.Wheel_ticks.INVALID
                or fr_wheel_qf_ticks[frame] == constants.HilCl.PDW.Veh_Motion.Wheel_ticks.INVALID
                or rl_wheel_qf_ticks[frame] == constants.HilCl.PDW.Veh_Motion.Wheel_ticks.INVALID
                or rr_wheel_qf_ticks[frame] == constants.HilCl.PDW.Veh_Motion.Wheel_ticks.INVALID
                or fl_wheel_ticks[frame] == constants.HilCl.PDW.Veh_Motion.Wheel_ticks.ERROR
                or fr_wheel_ticks[frame] == constants.HilCl.PDW.Veh_Motion.Wheel_ticks.ERROR
                or rl_wheel_ticks[frame] == constants.HilCl.PDW.Veh_Motion.Wheel_ticks.ERROR
                or rr_wheel_ticks[frame] == constants.HilCl.PDW.Veh_Motion.Wheel_ticks.ERROR
                or engine_state[frame] == constants.HilCl.PDW.Veh_modules.ENGINE.INVALID
                or eps_status[frame] == constants.HilCl.PDW.Veh_modules.EPS.SYSTEM_ERROR
                or park_brake_state[frame] == constants.HilCl.PDW.EPB_state.INVALID
                or service_brake_state[frame] == constants.HilCl.PDW.Veh_modules.SERVICE_BRAKE.INVALID
                or gearbox_state[frame] == constants.HilCl.PDW.Veh_modules.GEARBOX.INVALID
                or front_uss_deact[frame] == constants.HilCl.PDW.Veh_modules.USS_STATE.INACTIVE
                or rear_uss_deact[frame] == constants.HilCl.PDW.Veh_modules.USS_STATE.INACTIVE
                or veh_long_acc[frame] == constants.HilCl.PDW.Thresholds.VEH_ACCEL_LOWER
                or veh_long_acc[frame] == constants.HilCl.PDW.Thresholds.VEH_ACCEL_UPPER
                or front_uss_deact[frame] == constants.HilCl.PDW.Veh_modules.USS_STATE.INACTIVE
                or rear_uss_deact[frame] == constants.HilCl.PDW.Veh_modules.USS_STATE.INACTIVE
            ):
                return True
            else:
                return False

            # Go through each signal value based on the measurement's timestamp

        for frame in range(0, len(time_signal)):
            # Check the system Ignition
            if veh_ignition[frame] and trigger1 is None:
                # Wait for system initialization time
                if init_time >= constants.HilCl.PDW.FTTI.SYSTEM_INIT:
                    # Check transmission to be in NEUTRAL gear was engaged and there is no obstacle in the rear side of the ego to trigger the LSCA activation.
                    if (
                        (
                            gear_automatic[frame] == constants.HilCl.PDW.Gear.Automatic.NEUTRAL
                            or gear_manual[frame] == constants.HilCl.PDW.Gear.Manual.NEUTRAL
                        )
                        and (
                            uss8[frame] == constants.HilCl.PDW.Thresholds.MIN_LSCA_DISTANCE
                            and uss9[frame] == constants.HilCl.PDW.Thresholds.MIN_LSCA_DISTANCE
                        )
                        and fl_wheel_direction[frame] == constants.HilCl.PDW.Veh_Motion.Wheel_dir.INVALID
                    ):
                        trigger1 = True
                        t1_idx = frame
                        break
        if t1_idx:
            for frame in range(t1_idx, len(time_signal)):
                # Check the error injection part. No error should be injected into the system at this point
                if error_injection_check(frame) is False:
                    trigger2 = True
                    # Save only the list
                    precond_list = eval_check(frame, val_list)[0:3]
                    # Check the preconditions before the error were injected into the system
                    # Only emergency brake should be already trigger as LSCA is active when error is being injected into the system
                    if precond_list.count(None) == len(precond_list) and eval_check(frame, val_list)[3]:
                        t2_idx = frame
                        trigger3 = True
                        break
                    else:
                        trigger3 = False
                        break
                else:
                    trigger2 = False
                    break
        if t2_idx:
            for frame in range(t2_idx, len(time_signal)):
                # Search for the moment when the error was injected into the system while vehicle should still be moving
                if (
                    error_injection_check(frame)
                    and (
                        gear_automatic[frame] == constants.HilCl.PDW.Gear.Automatic.REVERSE
                        or gear_manual[frame] == constants.HilCl.PDW.Gear.Manual.REVERSE
                    )
                    and veh_velocity[frame] > constants.HilCl.PDW.Thresholds.MIN_SPEED_THRESHOLD_MPS
                    and trigger4 is None
                ):
                    trigger4 = True
                    FTTI_T1 = time_signal[frame]
                if FTTI_T1:
                    # Evaluate all conditions after the error was injected within a specific time
                    if time_signal[frame] <= (FTTI_T1 + constants.HilCl.PDW.FTTI.SAFETY_SS):
                        # Check that at least once all conditions were fulfilled
                        if (eval_check(frame, val_list))[0:2]:
                            eval_status_ok = True
                            break
                        else:
                            eval_status_ok = False

        """Check if preconditions were ok"""
        if trigger1 is None:
            preconditions = (
                "<br>Evaluation stopped!"
                "<br>Condition 1 violated - Gear switched to REVERSE:"
                f"<br>{signal_name['Gear_auto']} not different than {constants.HilCl.PDW.Gear.Automatic.REVERSE}"
                f"<br>or {signal_name['Gear_auto']} not different than {constants.HilCl.PDW.Gear.Manual.REVERSE} "
                "<br>or Condition 2 violated- Objects reported by rear USS within LSCA activation range:"
                f"<br>{signal_name['USS8_dist_to_object']} not equal to {constants.HilCl.PDW.Thresholds.MIN_LSCA_DISTANCE}"
                f"<br> or {signal_name['USS9_dist_to_object']} not equal to {constants.HilCl.PDW.Thresholds.MIN_LSCA_DISTANCE}"
                "<br>or Condition 3 violated- Vehicle moving:"
                f"<br>{signal_name['Wheel_direction_FL']} not equal to {constants.HilCl.PDW.Veh_Motion.Wheel_dir.INVALID}"
            )
        elif trigger2 is False:
            preconditions = "<br>Evaluation stopped!" "<br>The error was injected too early into the system!"
        elif trigger3 is False:
            preconditions = (
                "<br>Evaluation stopped!"
                "At least one of the following situations happened before error injection: "
                f"<br>{signal_name['Emergency_hold_request']} not True. "
                f"<br>{signal_name['General_screen']} was equal to Diag Error ({constants.HilCl.Hmi.APHMIGeneralScreen.DIAG_ERROR})."
                f"<br>{signal_name['Lateral_DMC_request']} was equal to permanent disabled ({constants.MoCo.LaDMC_Status_nu.PERM_DISABLED})."
                f"<br>{signal_name['General_message']} was equal to LSCA Unreliable ({constants.HilCl.Hmi.APHMIGeneralMessage.LSCA_UNRELIABLE})."
            )
        elif trigger4 is None:
            preconditions = "<br>Evaluation stopped!" "<br>There is no error injected into the system!"
        else:
            preconditions = "Preconditions were fulfilled. Check test result!"

        if eval_status_ok is None:
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation is FAILED, preconditions were not fulfilled. " f"       {preconditions}".split()
            )
        elif eval_status_ok is False:
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation is FAILED, the system did not switch to safe state within {constants.HilCl.PDW.FTTI.SAFETY_SS}us after an input error was injected. "
                "<br>At least one of the following situations happened:"
                f"<br>{signal_name['Emergency_hold_request']} not True. "
                f"<br>{signal_name['General_screen']} not set to error ({constants.HilCl.Hmi.APHMIGeneralScreen.DIAG_ERROR})."
                f"<br>{signal_name['Lateral_DMC_request']} not set to permanent disabled ({constants.MoCo.LaDMC_Status_nu.PERM_DISABLED})."
                f"<br>{signal_name['General_message']} not set to LSCA Unreliable {constants.HilCl.Hmi.APHMIGeneralMessage.LSCA_UNRELIABLE}.".split()
            )
        else:
            eval_cond = [True] * 1

        signal_summary["Safe State Transition."] = evaluation1

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        self.sig_sum = fh.HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if plot function is activated"""
        # First plot
        fig = go.Figure()
        # Graphic signals
        fig.add_trace(go.Scatter(x=time_signal, y=veh_ignition, mode="lines", name=signal_name["Veh_ignition"]))
        fig.add_trace(go.Scatter(x=time_signal, y=veh_velocity, mode="lines", name=signal_name["Vehicle_velocity"]))
        fig.add_trace(go.Scatter(x=time_signal, y=tp_velocity, mode="lines", name=signal_name["Traffic_velocity"]))
        fig.add_trace(go.Scatter(x=time_signal, y=pedal_brake, mode="lines", name=signal_name["Pedal_brake"]))
        fig.add_trace(go.Scatter(x=time_signal, y=park_brake, mode="lines", name=signal_name["Park_Brake"]))
        fig.add_trace(go.Scatter(x=time_signal, y=park_brake_state, mode="lines", name=signal_name["Park_Brake_State"]))
        fig.add_trace(go.Scatter(x=time_signal, y=gear_manual, mode="lines", name=signal_name["Gear_man"]))
        fig.add_trace(go.Scatter(x=time_signal, y=gear_automatic, mode="lines", name=signal_name["Gear_auto"]))
        fig.add_trace(
            go.Scatter(x=time_signal, y=fl_wheel_direction, mode="lines", name=signal_name["Wheel_direction_FL"])
        )
        fig.add_trace(
            go.Scatter(x=time_signal, y=fr_wheel_direction, mode="lines", name=signal_name["Wheel_direction_FR"])
        )
        fig.add_trace(
            go.Scatter(x=time_signal, y=rl_wheel_direction, mode="lines", name=signal_name["Wheel_direction_RL"])
        )
        fig.add_trace(
            go.Scatter(x=time_signal, y=rr_wheel_direction, mode="lines", name=signal_name["Wheel_direction_RR"])
        )
        fig.add_trace(go.Scatter(x=time_signal, y=fl_wheel_ticks, mode="lines", name=signal_name["Wheel_ticks_FL"]))
        fig.add_trace(go.Scatter(x=time_signal, y=fr_wheel_ticks, mode="lines", name=signal_name["Wheel_ticks_FR"]))
        fig.add_trace(go.Scatter(x=time_signal, y=rl_wheel_ticks, mode="lines", name=signal_name["Wheel_ticks_RL"]))
        fig.add_trace(go.Scatter(x=time_signal, y=rr_wheel_ticks, mode="lines", name=signal_name["Wheel_ticks_RR"]))
        fig.add_trace(
            go.Scatter(x=time_signal, y=fl_wheel_qf_ticks, mode="lines", name=signal_name["Wheel_ticks_QF_FL"])
        )
        fig.add_trace(
            go.Scatter(x=time_signal, y=fr_wheel_qf_ticks, mode="lines", name=signal_name["Wheel_ticks_QF_FR"])
        )
        fig.add_trace(
            go.Scatter(x=time_signal, y=rl_wheel_qf_ticks, mode="lines", name=signal_name["Wheel_ticks_QF_RL"])
        )
        fig.add_trace(
            go.Scatter(x=time_signal, y=rr_wheel_qf_ticks, mode="lines", name=signal_name["Wheel_ticks_QF_RR"])
        )
        fig.add_trace(go.Scatter(x=time_signal, y=engine_state, mode="lines", name=signal_name["Engine_State"]))
        fig.add_trace(go.Scatter(x=time_signal, y=eps_status, mode="lines", name=signal_name["EPS_Status"]))
        fig.add_trace(
            go.Scatter(x=time_signal, y=service_brake_state, mode="lines", name=signal_name["Service_Brake_State"])
        )
        fig.add_trace(go.Scatter(x=time_signal, y=front_uss_deact, mode="lines", name=signal_name["Front_USS_Deact"]))
        fig.add_trace(go.Scatter(x=time_signal, y=rear_uss_deact, mode="lines", name=signal_name["Rear_USS_Deact"]))
        fig.add_trace(go.Scatter(x=time_signal, y=gearbox_state, mode="lines", name=signal_name["Gearbox_State"]))
        fig.add_trace(go.Scatter(x=time_signal, y=veh_long_acc, mode="lines", name=signal_name["Vehicle_long_accel"]))
        fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[us]")
        fig.update_layout(title="System input signals")
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        # Second plot
        fig1 = go.Figure()
        # Graphic signals
        fig1.add_trace(go.Scatter(x=time_signal, y=aup_state, mode="lines", name=signal_name["AUP_State"]))
        fig1.add_trace(go.Scatter(x=time_signal, y=general_message, mode="lines", name=signal_name["General_message"]))
        fig1.add_trace(go.Scatter(x=time_signal, y=general_screen, mode="lines", name=signal_name["General_screen"]))
        fig1.add_trace(go.Scatter(x=time_signal, y=gear_req, mode="lines", name=signal_name["Gear_request"]))
        fig1.add_trace(go.Scatter(x=time_signal, y=gear_sw_req, mode="lines", name=signal_name["Gear_switch_request"]))
        fig1.add_trace(go.Scatter(x=time_signal, y=secure_req, mode="lines", name=signal_name["Secure_request"]))
        fig1.add_trace(go.Scatter(x=time_signal, y=hold_req_AUP, mode="lines", name=signal_name["Hold_request"]))
        fig1.add_trace(
            go.Scatter(x=time_signal, y=emer_hold_req_LSCA, mode="lines", name=signal_name["Emergency_hold_request"])
        )
        fig1.add_trace(go.Scatter(x=time_signal, y=lat_DMC_req, mode="lines", name=signal_name["Lateral_DMC_request"]))
        fig1.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[us]")
        fig1.update_layout(title="System output signals")
        fig1.update_layout(PlotlyTemplate.lgt_tmplt)

        # Third plot
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=time_signal, y=uss0, mode="lines", name=signal_name["USS0_dist_to_object"]))
        fig2.add_trace(go.Scatter(x=time_signal, y=uss1, mode="lines", name=signal_name["USS1_dist_to_object"]))
        fig2.add_trace(go.Scatter(x=time_signal, y=uss2, mode="lines", name=signal_name["USS2_dist_to_object"]))
        fig2.add_trace(go.Scatter(x=time_signal, y=uss3, mode="lines", name=signal_name["USS3_dist_to_object"]))
        fig2.add_trace(go.Scatter(x=time_signal, y=uss4, mode="lines", name=signal_name["USS4_dist_to_object"]))
        fig2.add_trace(go.Scatter(x=time_signal, y=uss5, mode="lines", name=signal_name["USS5_dist_to_object"]))
        fig2.add_trace(go.Scatter(x=time_signal, y=uss6, mode="lines", name=signal_name["USS6_dist_to_object"]))
        fig2.add_trace(go.Scatter(x=time_signal, y=uss7, mode="lines", name=signal_name["USS7_dist_to_object"]))
        fig2.add_trace(go.Scatter(x=time_signal, y=uss8, mode="lines", name=signal_name["USS8_dist_to_object"]))
        fig2.add_trace(go.Scatter(x=time_signal, y=uss9, mode="lines", name=signal_name["USS9_dist_to_object"]))
        fig2.add_trace(go.Scatter(x=time_signal, y=uss10, mode="lines", name=signal_name["USS10_dist_to_object"]))
        fig2.add_trace(go.Scatter(x=time_signal, y=uss11, mode="lines", name=signal_name["USS11_dist_to_object"]))
        fig2.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[us]")
        fig2.update_layout(title="Distance to objects reported by CarMaker USS")
        fig2.update_layout(PlotlyTemplate.lgt_tmplt)

        plot_titles.append("")
        plots.append(fig)
        plots.append(fig1)
        plots.append(fig2)
        remarks.append("")

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            "Preconditions": {"value": preconditions, "color": "grey"},
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
    name="System transition to Safe State mode (within 700 miliseconds) while LSCA was inactive",
    description="Check if the system goes to safe state once there is a failure injected.",
)
class SafeStateHil(TestCase):
    """Example test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            System_safe_state_error_injected_LSCA_inactive_SS,
        ]
