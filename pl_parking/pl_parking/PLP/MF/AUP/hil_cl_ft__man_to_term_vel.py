"""Mode Transition check, Maneuvering to Terminate: Velocity exeeds the limit"""

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

SIGNAL_DATA = "MAN_TO_TERM_VEL"


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
    name="Maneuvering to Terminate",
    description="Check AP system reaction if velocity of ego vehicle exeeds the limit.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupManToTermVelCheck(TestStep):
    """AupManToTermVelCheck Test Step."""

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
            f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED,"
            f" signal switches to Terminate mode when s velocity of"
            f" the ego vehicle exceeds {constants.HilCl.ApThreshold.AP_G_MAX_AVG_V_MPS} m/s.".split()
        )

        """Evaluation part"""
        # Find when AP switches to Maneuvering
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = cnt
                break

        if (
            t1_idx is not None
        ):  # Feedback for review: This part is useful because there was no PPC_SUCCESS, test automatically failed.
            # Find when AP switches to Terminate after Maneuvering
            for cnt in range(t1_idx, len(state_on_hmi_sig)):
                if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS:
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                # Find when speed of ego vehicle exeeds the limit after Maneuvering mode
                for cnt in range(t1_idx, len(car_speed_sig)):
                    if car_speed_sig[cnt] > 3.6 * constants.HilCl.ApThreshold.AP_G_MAX_AVG_V_MPS:
                        t3_idx = cnt
                        break

                if t3_idx is not None:
                    eval_cond = [True] * 1

                    states_dict = HilClFuntions.States(state_on_hmi_sig, t1_idx, len(state_on_hmi_sig), 1)

                    counter = 0
                    # counter == 0 : This is Maneuvering mode, because states are collected from the begining of Maneuvering.
                    # counter == 1: This has to be Terminate mode in this case but shall not be Maneuvering.

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
                                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switches to {actual_value} ({actual_number}) at {time_signal[key]} us but velocity of"
                                    f" ego vehicle is {car_speed_sig[key] / 3.6} m/s. This value is less"
                                    f" than {constants.HilCl.ApThreshold.AP_G_MAX_AVG_V_MPS} m/s.".split()
                                )
                                eval_cond[0] = False
                                break

                            if states_dict[key] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switches to {actual_value} ({actual_number}) at {time_signal[key]} us not to Terminate mode"
                                    f" but velocity of ego vehicle is {car_speed_sig[key] / 3.6} m/s. This value is more"
                                    f" than {constants.HilCl.ApThreshold.AP_G_MAX_AVG_V_MPS} m/s. ".split()
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
                        f"The evaluation of {signal_name['Car_speed']} signal is FAILED, velocity of ego vehicle never exeeded {constants.HilCl.ApThreshold.AP_G_MAX_AVG_V_MPS} m/s."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to Terminate mode ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to PPC_PERFORM_PARKING mode ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})."
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

        signal_summary["Required AP state change: Maneuvering to Terminate. Reason: Velocity of ego vehicle"] = (
            evaluation1
        )

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
    name="Mode transition: Maneuvering to Teminate",
    description=f"The AP function shall transition from Maneuvering to Terminate mode if"
    f" The velocity of the ego vehicle exceeds {constants.HilCl.ApThreshold.AP_G_MAX_AVG_V_MPS} m/s.",
)
class AupManToTermVel(TestCase):
    """AupManToTermVel Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupManToTermVelCheck,
        ]
