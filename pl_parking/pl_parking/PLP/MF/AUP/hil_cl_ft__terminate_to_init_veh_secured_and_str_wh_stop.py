"""Mode Transition check, Maneuvering to Terminate: Brake pressure eventt"""

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

SIGNAL_DATA = "MANEUVERING_TO_TERMINATE_BRAKE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        WH_ANG_VELOCITY = "Steering_ang_velocity"
        PARKING_CORE_STATE = "Parking_core_state"
        GEAR_STATE = "Gear_state"
        PARK_BRAKE_STATE = "Park_brake_state"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.WH_ANG_VELOCITY: "CM.Steer.WhlVel",
            self.Columns.PARKING_CORE_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.GEAR_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralCurrentGear",
            self.Columns.PARK_BRAKE_STATE: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.StateParkBrake",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Mode transition: Terminate to Init, steering stopped and parked",
    description="The vehicle shall transit from Terminate to Inint mode, when both of the condition"
    " is fullfilled \n:"
    "1. The vehicle is secured (Parking brake is on and the vehicle is in Parking gear.\n"
    "2. The steering wheel is stopped moving.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupTermInitVehSecuredCheck(TestStep):
    """AupTermInitVehSecuredCheck Test Step."""

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

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        str_whl_vel = read_data["Steering_ang_velocity"].tolist()
        gear_state = read_data["Gear_state"].tolist()
        park_brake_sig = read_data["Park_brake_state"].tolist()
        state_on_hmi_sig = read_data["Parking_core_state"].tolist()

        t_terminate_idx = None
        t_init_idx = None
        t_secured_idx = None
        t_str_wheel_idx = None
        str_wh_stopped = True
        eval_conditions = [False]

        evaluation1 = ""

        """Evaluation part"""
        # Find when parking core switches to terminate mode
        for cnt in range(0, len(state_on_hmi_sig)):
            if (
                state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS
                or state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED
            ):
                t_terminate_idx = cnt
                break

        # Find when parking core switches to Init mode
        for cnt in range(t_terminate_idx or 0, len(time_signal)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE:
                t_init_idx = cnt
                break

        for cnt in range(t_terminate_idx or 0, len(time_signal)):
            if (
                park_brake_sig[cnt] == constants.HilCl.Brake.PARK_BRAKE_SET
                and gear_state[cnt == constants.HilCl.Gear.GEAR_P]
            ):
                t_secured_idx = cnt
                break

        for cnt in range(t_terminate_idx or 0, len(time_signal)):
            if abs(str_whl_vel[cnt]) <= 0.01:
                t_str_wheel_idx = cnt
                break
        for cnt in range(t_str_wheel_idx or 0, t_init_idx or len(time_signal)):
            if abs(str_whl_vel[cnt] > 0.01):
                str_wh_stopped = False

        if t_terminate_idx and t_init_idx and t_secured_idx and t_str_wheel_idx and str_wh_stopped:
            eval_conditions = [
                t_secured_idx < t_init_idx,
                t_str_wheel_idx < t_init_idx,
            ]
        if all(eval_conditions):
            test_result = fc.PASS
            evaluation1 = " ".join("The test for checking Mode transition from Terminate to Init is PASSED. ".split())
        else:
            test_result = fc.FAIL
            evaluation1 = " ".join("The test for checking Mode transition from Terminate to Init is FAILED. ".split())
            if t_secured_idx is not None and t_init_idx is not None and t_secured_idx > t_init_idx:
                evaluation1 += " ".join(
                    f"The system transitioned to Init mode ({signal_name['Parking_core_state']} is {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE}), before the Parking "
                    "brake was on and it was shifted into Parking gear. ".split()
                )

            if t_str_wheel_idx is not None and t_init_idx is not None and t_str_wheel_idx >= t_init_idx:
                evaluation1 += " ".join(
                    "The system transitioned to Init mode ({signal_name['Parking_core_state']} is {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE}), before the steering "
                    "wheel movement was stopped".split()
                )
        if t_terminate_idx is None:
            evaluation1 += " ".join(
                f"The system did not transition to Terminate mode, the signal {signal_name['Parking_core_state']} is not reeached either {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS} or {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED}. ".split()
            )
        if t_init_idx is None:
            evaluation1 += " ".join(
                f"The system did not transition to Init mode, the signal {signal_name['Parking_core_state']} is not {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE} at the end. ".split()
            )
        if t_str_wheel_idx is None:
            evaluation1 += " ".join(
                f"The steering wheel did not stop turning, the signal {signal_name['Steering_ang_velocity']} is never below 0.01. ".split()
            )
        if t_secured_idx is None:
            evaluation1 += " ".join(
                f"The vehicle was not secured, the signal {signal_name['Gear_state']} is not {constants.HilCl.Gear.GEAR_P} and signal {signal_name['Park_brake_state']} is not {constants.HilCl.Brake.PARK_BRAKE_SET} at the same time. ".split()
            )
        if not str_wh_stopped:
            evaluation1 += " ".join(
                "The steering wheel started to move again before the system transitioned to init.".split()
            )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary[
            "Required AP state change: Terminate to Init when the steering wheel stopped "
            "moving, and the vehicle was secured."
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("Visualizing the measured signals in function of time")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["Parking_core_state"])
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=park_brake_sig, mode="lines", name=signal_name["Park_brake_state"])
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=str_whl_vel, mode="lines", name=signal_name["Steering_ang_velocity"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=gear_state, mode="lines", name=signal_name["Gear_state"]))

            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("Visualizing the measured signals in function of time")
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
    name="Mode transition: Terminate to Init, steering stopped and parked",
    description="The vehicle shall transit from Terminate to Inint mode, when both of the condition"
    " is fullfilled \n:"
    "1. The vehicle is secured: Parking brake is on and the vehicle is in Parking gear.\n"
    "2. The steering wheel is stopped moving.",
)
class AupTermInitVehSecured(TestCase):
    """AupTermInitVehSecured Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupTermInitVehSecuredCheck,
        ]
