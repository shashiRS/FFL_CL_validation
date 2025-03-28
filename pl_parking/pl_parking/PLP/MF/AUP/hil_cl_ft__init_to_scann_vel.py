"""Mode Transition check, Init to Scanning: Driving forward with a velocity below limit"""

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

SIGNAL_DATA = "INIT_TO_SCANN_EGO_VELOCITY"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        CAR_SPEED = "Car_speed"
        HMI_INFO = "State_on_HMI"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CAR_SPEED: "MTS.ADAS_CAN.Conti_Veh_CAN.Tachometer.SpeedoSpeed",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Init to Scannning check",
    description="Check maximum velocity dependence of mode transition",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupInitScannVelCheck(TestStep):
    """AupInitScannVelCheck Test Step."""

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
        t3_idx = None
        evaluation1 = " ".join(
            f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED, signal switches to Scanning mode when speed of ego"
            f" vehicle above {constants.HilCl.ApThreshold.AP_G_V_SCANNING_THRESH_ON_MPS} m/s.".split()
        )

        """Evaluation part"""
        # Find when AP switches to Scanning first time
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN:
                t1_idx = cnt
                break

        if t1_idx is not None:
            # Find when AP switches to Init after Scanning
            for cnt in range(t1_idx, len(state_on_hmi_sig)):
                if (
                    state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE
                    or state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_INACTIVE
                    or state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE
                ):
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                # Find when speed of ego vehicle is lower or equal with limit after Init mode
                for cnt in range(t2_idx, len(car_speed_sig)):
                    if car_speed_sig[cnt] < 3.6 * constants.HilCl.ApThreshold.AP_G_V_SCANNING_THRESH_ON_MPS:
                        t3_idx = cnt
                        break

                if t3_idx is not None:
                    eval_cond = [True] * 1

                    states_dict = HilClFuntions.States(state_on_hmi_sig, t2_idx, len(state_on_hmi_sig), 1)

                    counter = 0
                    # counter == 0 : This is Scanning mode, because states are collected from the begining of Scanning.
                    # counter == 1: This has to be Scanning or Init mode in this case but shall not be Maneuvering.

                    # Keys contains the idx
                    # Check mode
                    for key in states_dict:
                        if counter == 1:
                            actual_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE.get(
                                states_dict[key]
                            )
                            actual_number = int(states_dict[key])

                            if key < t3_idx:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switches to {actual_value} ({actual_number}) at {time_signal[key]} us but speed of"
                                    f" ego vehicle is {car_speed_sig[key] / 3.6} m/s. This value is greather"
                                    f" than {constants.HilCl.ApThreshold.AP_G_V_SCANNING_THRESH_ON_MPS} m/s.".split()
                                )
                                eval_cond[0] = False
                                break

                            if states_dict[key] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switches to {actual_value} ({actual_number}) at {time_signal[key]} us not to Scanning mode"
                                    f" ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN}) but speed of ego vehicle is {car_speed_sig[key] / 3.6} m/s. This value is less"
                                    f" than {constants.HilCl.ApThreshold.AP_G_V_SCANNING_THRESH_ON_MPS} m/s. ".split()
                                )
                                eval_cond[0] = False
                                break
                            counter += 1
                        else:
                            counter += 1

                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Car_speed']} signal is FAILED, speed of ego vehicle never turned back to Scanning speed range."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to Init mode"
                    f" afte PPC_SCANNING_IN mode ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN}). "
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched"
                f" to PPC_SCANNING_IN mode ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN})."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Required AP state change: Init to Scanning. Reason: Velocity of ego vehicle"] = evaluation1

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
    name="Mode transition: Init to Scanning",
    description=f"The ego vehicle is driving forward with a velocity below {constants.HilCl.ApThreshold.AP_G_V_SCANNING_THRESH_ON_MPS} m/s.",
)
class AupInitScannVel(TestCase):
    """AupInitScannVel Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupInitScannVelCheck,
        ]
