"""Mode Transition check, Init to Scanning: Ego vehicle traveled a minimum distance"""

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

SIGNAL_DATA = "INIT_TO_SCANN_EGO_TRAVELED"


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
            self.Columns.CAR_ROAD: "CM.Car.Road.sRoad",
            self.Columns.CAR_SPEED: "MTS.ADAS_CAN.Conti_Veh_CAN.Tachometer.SpeedoSpeed",
            self.Columns.USEER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Init to Scannning check",
    description="Check minimum distance dependence of mode transition",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupInitScannTravCheck(TestStep):
    """AupInitScannTravCheck Test Step."""

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

        """Prepare sinals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        car_road_sig = read_data["Car_road"].tolist()
        user_action_sig = read_data["User_action"].tolist()
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()

        t1_idx = None
        t2_idx = None
        evaluation1 = " ".join(
            f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED, signal swtiches to Scanning mode after ego vehicle"
            f" traveled more than {constants.HilCl.ApThreshold.AP_G_ROLLED_DIST_IN_THRESH_M} m.".split()
        )

        """Evaluation part"""
        # Find AP active user action on HMI
        for cnt in range(0, len(user_action_sig)):
            if user_action_sig[cnt] == constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE:
                t1_idx = cnt
                break

        if t1_idx is not None:
            # Find when road of ego vehcile is more than limit
            for cnt in range(t1_idx, len(car_road_sig)):
                delta_road = car_road_sig[cnt] - car_road_sig[0]

                if delta_road >= constants.HilCl.ApThreshold.AP_G_ROLLED_DIST_IN_THRESH_M:
                    t2_idx = cnt
                    break
            if t2_idx is not None:
                eval_cond = [True] * 1

                states_dict = HilClFuntions.States(state_on_hmi_sig, t1_idx, len(state_on_hmi_sig), 1)

                counter = 0
                # counter == 0 : This is Scanning mode, because states are collected from the begining of Init.
                # counter == 1: This has to be Scanning mode in this case. System has to switch from Init to Scanning

                # Keys contains the idx
                # Check mode after Init mode
                for key in states_dict:
                    if counter == 1:
                        actual_state = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE.get(
                            states_dict[key]
                        )

                        if key < t2_idx:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switches into {actual_state} at {time_signal[key]} us"
                                f" before ego vehicle has traveled a minimum distance:"
                                f" {constants.HilCl.ApThreshold.AP_G_ROLLED_DIST_IN_THRESH_M} m.".split()
                            )
                            eval_cond[0] = False
                            break

                        if states_dict[key] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal state is {actual_state}"
                                f" at {time_signal[key]} us but ego vehicle traveled more than"
                                f" {constants.HilCl.ApThreshold.AP_G_ROLLED_DIST_IN_THRESH_M} m.".split()
                            )
                            eval_cond[0] = False
                            break

                    else:
                        counter += 1
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Car_road']} is FAILED, road of ego vehicle never reached"
                    f" {constants.HilCl.ApThreshold.AP_G_ROLLED_DIST_IN_THRESH_M} m.".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never set to TOGGLE_AP_ACTIVE (Value: {constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE}).".split()
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
            "Required AP state change: Init to Scanning. Reason: Ego vehicle traveled more than the minimum distance"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=car_road_sig, mode="lines", name=signal_name["Car_road"]))
            fig.add_trace(go.Scatter(x=time_signal, y=user_action_sig, mode="lines", name=signal_name["User_action"]))

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
    name="Mode transition: Init to Scanning",
    description=f"Since the last ignition start, the ego vehicle has traveled a minimum distance of"
    f" {constants.HilCl.ApThreshold.AP_G_ROLLED_DIST_IN_THRESH_M} m.",
)
class AupInitScannTrav(TestCase):
    """AupInitScannTrav Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupInitScannTravCheck,
        ]
