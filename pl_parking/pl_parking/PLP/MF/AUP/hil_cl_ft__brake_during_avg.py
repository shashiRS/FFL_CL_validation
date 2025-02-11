"""Ego vehicle shall stop if brake pressure caused by brake pedal exceeds {AP_G_BRAKE_PRESS_THRESH_BAR} bar."""
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

SIGNAL_DATA = "BRK_DUR_AVG"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USEER_ACTION = "User_action"
        HMI_INFO = "State_on_HMI"
        DRIVING_DIR = "Driv_dir"
        GENERAL_MESSAGE = "General_message"
        CAR_SPEED = "Car_speed"
        BRAKE = "Brake"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USEER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
            self.Columns.CAR_SPEED: "MTS.ADAS_CAN.Conti_Veh_CAN.Tachometer.SpeedoSpeed",
            self.Columns.BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput06.BrakePressureDriver",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Brake Check",
    description="Check if ego car stop after brake pedal is pressed within AVG in control.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class BrakeDuringAVGCheck(TestStep):
    """BrakeDuringAVGCheck Test Step."""

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

        read_data = self.readers[SIGNAL_DATA].signals
        test_result = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        general_message_sig = read_data["General_message"].tolist()
        user_act_sig = read_data["User_action"].tolist()
        driving_dir_sig = read_data["Driv_dir"].tolist()
        brake_sig = read_data["Brake"].tolist()
        car_speed = read_data["Car_speed"].tolist()
        HMI_Info = read_data["State_on_HMI"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None

        evaluation1 = " ".join(
            f"The evaluation of driving direction {signal_name['Driv_dir']} signal is PASSED,"
            f" signal switches to STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL})"
            f" when the ego car stops.".split()
        )

        """Evaluation part"""
        # Find the moment when AVG start to control ( ParkingProcedureCtrlState = PPC_PERFORM_PARKING)
        for cnt in range(0, len(HMI_Info)):
            if HMI_Info[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = cnt
                break

        if t1_idx is not None:
            eval_cond = [True] * 1

            # Find the moment when driver start to press the brake pedal but lower than {AP_G_BRAKE_PRESS_THRESH_BAR}
            for cnt in range(t1_idx, len(brake_sig)):
                if ((brake_sig[cnt] * constants.HilCl.BrakePressure.brake_pressure_driver_factor) - constants.HilCl.BrakePressure.brake_pressure_driver_offset < constants.HilCl.ApThreshold.AP_G_BRAKE_PRESS_THRESH_BAR and
                    (brake_sig[cnt] * constants.HilCl.BrakePressure.brake_pressure_driver_factor) - constants.HilCl.BrakePressure.brake_pressure_driver_offset > 0 and
                    HMI_Info[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING):
                    t2_idx = cnt
                    #save the velocity from t2_idx in order to compare it with the value when t3_idx start
                    t2_idx_velocity = car_speed[t2_idx]
                    for i in range(t1_idx, t2_idx):
                        if HMI_Info[i] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                            eval_cond = [False] * 1
                            break
                    break
            if t2_idx is not None and False not in eval_cond:
                # Find the moment when BrakePressureDriver set to a value > {AP_G_BRAKE_PRESS_THRESH_BAR}
                for cnt in range(t2_idx, len(brake_sig)):
                    if ( brake_sig[cnt] * constants.HilCl.BrakePressure.brake_pressure_driver_factor ) - constants.HilCl.BrakePressure.brake_pressure_driver_offset > constants.HilCl.ApThreshold.AP_G_BRAKE_PRESS_THRESH_BAR and HMI_Info[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                        t3_idx = cnt
                        # Compare the ego vel at t3_idx to make sure it is less than t2_idx_velocity
                        t3_idx_velocity = car_speed[t3_idx]
                        if t3_idx_velocity < t2_idx_velocity:
                            for i in range(t2_idx, t3_idx):
                                if car_speed[i] < 0.1 or HMI_Info[i] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                                    eval_cond = [False] * 1
                                    break
                        else:
                            eval_cond = [False] * 1
                        break
                #Checking if after BrakePressure is > limit, car is stopping and APHMIGeneralDrivingDir signal set to STANDSTILL
                if t3_idx is not None and False not in eval_cond:
                    #taking the timestamp of t3_idx in order to check the reaction 500ms after
                    t3_timestamp = time_signal[t3_idx]
                    for cnt in range(t3_idx, len(car_speed)):
                        if (( t3_timestamp - time_signal[cnt] ) / 10**6) > constants.HilCl.ApThreshold.TRESHOLD_TO_STANDSTILL / 10:
                            if car_speed[cnt] > 0 or driving_dir_sig[cnt] != constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL:
                                eval_cond = [False] * 1
                                break
                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Driv_dir']} signal is FAILED,"
                        f" brake pedal does not exceeds {constants.HilCl.ApThreshold.AP_G_BRAKE_PRESS_THRESH_BAR} bar"
                        f" or ego vel at t3_idx >= t2_idx.".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Driv_dir']} signal is FAILED,"
                    f" brake pedal not within 0 and  {constants.HilCl.ApThreshold.AP_G_BRAKE_PRESS_THRESH_BAR} bar interval.".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Driv_dir']} signal is FAILED,"
                f" AVG never in control.".split()
            )

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary[
            "Check the reaction of the system during AVG ON with brake pedal"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(x=time_signal, y=general_message_sig, mode="lines", name=signal_name["General_message"])
        )
        fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
        fig.add_trace(go.Scatter(x=time_signal, y=brake_sig, mode="lines", name=signal_name["Brake"] + " [bar]"))
        fig.add_trace(go.Scatter(x=time_signal, y=driving_dir_sig, mode="lines", name=signal_name["Driv_dir"]))
        fig.add_trace(go.Scatter(x=time_signal, y=car_speed, mode="lines", name=signal_name["Car_speed"]))

        fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
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
            "Used SW version": {"value": sw_combatibility},
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
    name="Brake pedal pressed during AVG ON",
    description="In case that the driver actuates the brake pedal below {AP_G_BRAKE_PRESS_THRESH_BAR} bar (tunable) during AVG, the function shall reduce the velocity of the maneuver accordingl",
)
class BrakeDuringAVG(TestCase):
    """BrakeDuringAVG Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            BrakeDuringAVGCheck,
        ]
