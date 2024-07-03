"""Mode Transition check, Scanning to Init: Velocity of ego vehicle"""

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

SIGNAL_DATA = "AUP_SCANN_TO_INIT_VELOCITY"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        CAR_ROAD = "Car_road"
        CAR_SPEED = "Car_speed"
        USEER_ACTION = "User_action"
        HMI_INFO = "State_on_HMI"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CAR_ROAD: "CM.Car.sRoad",
            self.Columns.CAR_SPEED: "MTS.ADAS_CAN.Conti_Veh_CAN.Tachometer.SpeedoSpeed",
            self.Columns.USEER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Scanning to Init check",
    description="Check minimum velocity dependence of mode transition",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupScanToInitVelCheck(TestStep):
    """AupScanToInitVelCheck Test Step."""

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
        signal_summary = {}
        time_signal = read_data.index
        car_speed_sig = read_data["Car_speed"].tolist()
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()

        t1_idx = None
        t2_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED, signal switches to Init mode while speed of ego"
            f" vehicle was lower than {constants.HilCl.ApThreshold.AP_G_V_SCANNING_THRESH_OFF_MPS} m/s. Ego vehicle speed related siganl: {signal_name['Car_speed']}".split()
        )

        """Evaluation part"""
        # Find when AP switches to Scanning
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN:
                t1_idx = cnt
                break

        if t1_idx is not None:
            # Find when speed of ego vehicle is above OFF limit
            for cnt in range(t1_idx, len(car_speed_sig)):
                if car_speed_sig[cnt] < 3.6 * constants.HilCl.ApThreshold.AP_G_V_SCANNING_THRESH_OFF_MPS:
                    t2_idx = cnt
                    break
            if t2_idx is not None:
                eval_cond = [True] * 1

                states_dict = HilClFuntions.States(state_on_hmi_sig, t1_idx, len(state_on_hmi_sig), 1)

                counter = 0
                # counter == 0 : This is Scanning mode, because states are collected from the begining of Scanning.
                # counter == 1: This has to be Init mode in this case. System has to switch from Scanning to Init

                # Keys contains the idx
                # Check mode after Scanning mode
                for key in states_dict:
                    if counter == 1:
                        actual_valule = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE.get(
                            states_dict[key]
                        )

                        if key < t2_idx:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switches into {actual_valule} at {time_signal[key]} us but speed of ego vehicle"
                                f" above {constants.HilCl.ApThreshold.AP_G_V_SCANNING_THRESH_OFF_MPS}.".split()
                            )
                            eval_cond[0] = False
                            break

                        if states_dict[key] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, speed of ego vehicle is {car_speed_sig[key] / 3.6} m/s. This value is above"
                                f" {constants.HilCl.ApThreshold.AP_G_V_SCANNING_THRESH_OFF_MPS} m/s and"
                                f" State of signal switches into {actual_valule} at {time_signal[key]} us.".split()
                            )
                            eval_cond[0] = False
                            break

                    else:
                        counter += 1
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Car_speed']} signal is FAILED, speed of ego vehicle never aboive"
                    f" {constants.HilCl.ApThreshold.AP_G_V_SCANNING_THRESH_OFF_MPS} m/s.".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to Snanning.".split()
            )

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Required AP state change: Scanning to Init. Reason: Velocity of ego vehicle"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=car_speed_sig, mode="lines", name=signal_name["Car_speed"] + " [km/h]")
            )

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
    name="Mode transition: Scanning to Init",
    description=f"The velocity of the ego vehicle is above {constants.HilCl.ApThreshold.AP_G_V_SCANNING_THRESH_OFF_MPS}.",
)
class FtCommon(TestCase):
    """AupScanToInitVel Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupScanToInitVelCheck,
        ]
