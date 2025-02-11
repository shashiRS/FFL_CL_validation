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

SIGNAL_DATA = "PDW_ACTIVATION_BY_AUP"


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
        AUP_STATE = "AUP_State"
        PDW_STANDSTILL_AUTOACTIVATION = "PDW_standstill_autoactivation"
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
            self.Columns.AUP_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.PDW_STANDSTILL_AUTOACTIVATION: "MTS.MTA_ADC5.CFG_DATA.MF_DWF_APP_Parameter.PDW_L_AUTOM_ACTIV_STANDSTILL_NU",
            self.Columns.PDW_BUTTON: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
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
        }


example_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="PDW activation by AUP",
    description=(
        "This step is checking if PDW is activated after a certain condition was fulfilled (AUP gets activated)."
        "Initial state of PDW is 'OFF'."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PDW_activation_by_AUP(TestStep):
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
        # pdw_standstill_autoact = read_data["PDW_standstill_autoactivation"].tolist()
        ap_state = read_data["AUP_State"].tolist()
        # uss0 = read_data["USS0_dist_to_object"].tolist()
        # uss1 = read_data["USS1_dist_to_object"].tolist()
        # uss2 = read_data["USS2_dist_to_object"].tolist()
        # uss3 = read_data["USS3_dist_to_object"].tolist()
        # uss4 = read_data["USS4_dist_to_object"].tolist()
        # uss5 = read_data["USS5_dist_to_object"].tolist()
        # uss6 = read_data["USS6_dist_to_object"].tolist()
        # uss7 = read_data["USS7_dist_to_object"].tolist()
        # uss8 = read_data["USS8_dist_to_object"].tolist()
        # uss9 = read_data["USS9_dist_to_object"].tolist()
        # uss10 = read_data["USS10_dist_to_object"].tolist()
        # uss11 = read_data["USS11_dist_to_object"].tolist()

        # Variables used in the evaluation
        trigger1 = None
        trigger2 = None
        trigger3 = None
        eval_status_ok = None
        FTTI_time = 0
        start_waiting = 0

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['PDW_State']} is PASSED, PDW State switched to 'activated by button' ({constants.HilCl.PDW.States.ACTIVATED_BY_BUTTON}) state"
            f" after the following activation condition was fulfilled ({signal_name['AUP_State']}"
            f"  switched to 'ACTIVE' ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})".split()
        )

        """Evaluation part"""

        # Function defined to see whether we have at least one object around the ego considered by PDW
        # def ObjectDetection(frame):
        #     if (
        #         (
        #             uss0[frame] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
        #             and uss0[frame] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
        #         )
        #         or (
        #             uss1[frame] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
        #             and uss1[frame] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
        #         )
        #         or (
        #             uss2[frame] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
        #             and uss2[frame] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
        #         )
        #         or (
        #             uss3[frame] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
        #             and uss3[frame] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
        #         )
        #         or (
        #             uss4[frame] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
        #             and uss4[frame] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
        #         )
        #         or (
        #             uss5[frame] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
        #             and uss5[frame] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
        #         )
        #         or (
        #             uss6[frame] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
        #             and uss6[frame] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
        #         )
        #         or (
        #             uss7[frame] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
        #             and uss7[frame] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
        #         )
        #         or (
        #             uss8[frame] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
        #             and uss8[frame] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
        #         )
        #         or (
        #             uss9[frame] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
        #             and uss9[frame] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
        #         )
        #         or (
        #             uss10[frame] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
        #             and uss10[frame] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
        #         )
        #         or (
        #             uss11[frame] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
        #             and uss11[frame] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
        #         )
        #     ):
        #         return True
        #     else:
        #         return False

        # Go through each signal value based on the measurement's timestamp
        for frame in range(0, len(time_signal)):
            if not start_waiting:
                # Check if our function is not in failure state
                if pdw_state[frame] != constants.HilCl.PDW.States.FAILURE:
                    trigger1 = True
                    # check PDW state to be 'OFF' until AUP gets activated
                    if ap_state[frame] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                        if pdw_state[frame] != constants.HilCl.PDW.States.OFF:
                            trigger2 = False
                            break
                    # check if AUP was activated
                    if ap_state[frame] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                        trigger3 = True
                        if not FTTI_time:  # Wait FTTI time for functionality to change its own state as it should
                            start_waiting = 1
                        else:
                            # Check if PDW switched to 'activated by button' state
                            if pdw_state[frame] == constants.HilCl.PDW.States.ACTIVATED_BY_BUTTON:
                                eval_status_ok = True
                                break
                            else:
                                eval_status_ok = False
                                break
                else:
                    trigger1 = False
                    break
            else:
                # FTTI time delay
                FTTI_time += time_signal[frame] - time_signal[frame - 1]
                if FTTI_time >= constants.HilCl.PDW.FTTI.SYSTEM_WO_OBJECTS:  # 200ms - system FTTI
                    start_waiting = 0
        """Check if preconditions were ok"""
        if trigger1 is False:
            preconditions = f"Check trigger1! PDW state({signal_name['PDW_State']}) set to Failure ({constants.HilCl.PDW.States.FAILURE})."
        elif trigger2 is False:
            preconditions = f"Check trigger2! PDW state {signal_name['PDW_State']} not switched to 'OFF'({constants.HilCl.PDW.States.OFF}) within {constants.HilCl.PDW.FTTI.SYSTEM}us."
        elif trigger3 is None:
            preconditions = f"Check trigger3! AUP did not get activated. ({signal_name['AUP_State']} not switched to ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})."
        else:
            preconditions = "Preconditions were fulfilled. Check test result!"

        if eval_status_ok is None:
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['PDW_State']} is FAILED, preconditions were not fulfilled. "
                f"       {preconditions}".split()
            )
        elif eval_status_ok is False:
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['PDW_State']} is FAILED, PDW State did not switch to 'activated by button'state({constants.HilCl.PDW.States.ACTIVATED_BY_BUTTON})"
                f" after the following activation condition was fulfilled ({signal_name['AUP_State']}"
                f"  switched to 'ACTIVE' ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})".split()
            )
        else:
            eval_cond = [True] * 1

        signal_summary["PDW state -activation if a certain condition was fulfilled."] = evaluation1

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
        # fig.add_trace(
        #     go.Scatter(
        #         x=time_signal, y=pdw_standstill_autoact, mode="lines", name=signal_name["PDW_standstill_autoactivation"]
        #     )
        # )
        fig.add_trace(go.Scatter(x=time_signal, y=ap_state, mode="lines", name=signal_name["AUP_State"]))
        fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[us]")
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        # Second plot
        # fig1 = go.Figure()
        # Graphic signals
        # fig1.add_trace(go.Scatter(x=time_signal, y=uss0, mode="lines", name=signal_name["USS0_dist_to_object"]))
        # fig1.add_trace(go.Scatter(x=time_signal, y=uss1, mode="lines", name=signal_name["USS1_dist_to_object"]))
        # fig1.add_trace(go.Scatter(x=time_signal, y=uss2, mode="lines", name=signal_name["USS2_dist_to_object"]))
        # fig1.add_trace(go.Scatter(x=time_signal, y=uss3, mode="lines", name=signal_name["USS3_dist_to_object"]))
        # fig1.add_trace(go.Scatter(x=time_signal, y=uss4, mode="lines", name=signal_name["USS4_dist_to_object"]))
        # fig1.add_trace(go.Scatter(x=time_signal, y=uss5, mode="lines", name=signal_name["USS5_dist_to_object"]))
        # fig1.add_trace(go.Scatter(x=time_signal, y=uss6, mode="lines", name=signal_name["USS6_dist_to_object"]))
        # fig1.add_trace(go.Scatter(x=time_signal, y=uss7, mode="lines", name=signal_name["USS7_dist_to_object"]))
        # fig1.add_trace(go.Scatter(x=time_signal, y=uss8, mode="lines", name=signal_name["USS8_dist_to_object"]))
        # fig1.add_trace(go.Scatter(x=time_signal, y=uss9, mode="lines", name=signal_name["USS9_dist_to_object"]))
        # fig1.add_trace(go.Scatter(x=time_signal, y=uss10, mode="lines", name=signal_name["USS10_dist_to_object"]))
        # fig1.add_trace(go.Scatter(x=time_signal, y=uss11, mode="lines", name=signal_name["USS11_dist_to_object"]))
        # fig1.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[us]")
        # fig1.update_layout(PlotlyTemplate.lgt_tmplt)

        plot_titles.append("")
        plots.append(fig)
        # plots.append(fig1)
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
    name="PDW activation by AUP",
    description="Check if PDW is activated whenever AUP is activated.",
)
class PdwHil(TestCase):
    """Example test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PDW_activation_by_AUP,
        ]
