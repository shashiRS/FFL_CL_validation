"""Maneuvering to Terminate: Internal limitation"""

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

SIGNAL_DATA = "MAN_TO_TERM_INTERNAL_LIMITATION"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        CAR_A_TX = "Car_A_tx"
        CAR_B_TX = "Car_B_tx"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.CAR_A_TX: "CM.Traffic.P00.tx",
            self.Columns.CAR_B_TX: "CM.Traffic.P14.tx",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Mode transition, Internal limitation",
    description="Check system swithces from Maneuvering to Terminate mode.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupManToTermIntLimitCheck(TestStep):
    """AupManToTermIntLimitCheck Test Step."""

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
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()
        car_a_tx_sig = read_data["Car_A_tx"].tolist()
        car_b_tx_sig = read_data["Car_B_tx"].tolist()

        t_maneuvering_start_idx = None
        t_small_slot_idx = None

        car_a_target_x = 52.5  # Value is very specific for this evaluation script. Not used in any another script so not added to constants.py
        car_b_target_x = 55.5  # Value is very specific for this evaluation script. Not used in any another script so not added to constants.py

        """Evaluation part"""
        # Find man start and man end
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_maneuvering_start_idx = cnt
                break

        if t_maneuvering_start_idx is not None:

            # Find when car A and B move to way of ego vehicle
            for cnt in range(t_maneuvering_start_idx, len(time_signal)):
                if round(car_a_tx_sig[cnt], 1) == car_a_target_x and round(car_b_tx_sig[cnt], 1) == car_b_target_x:
                    t_small_slot_idx = cnt
                    break

            if t_small_slot_idx is not None:
                eval_cond = [True] * 1

                states_dict = HilClFuntions.States(state_on_hmi_sig, t_maneuvering_start_idx, len(state_on_hmi_sig), 1)

                counter = 0

                # Keys contains the idx
                # Check mode after Maneuvering mode
                for key in states_dict:
                    if counter == 1:
                        actual_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE.get(
                            states_dict[key]
                        )
                        actual_number = int(states_dict[key])

                        if key < t_small_slot_idx:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switches into {actual_value} ({actual_number})"
                                f" at {time_signal[key]} us before vehicle A nad vehicle B reached the target position to block the planed way of ego vehicle.".split()
                            )
                            eval_cond[0] = False
                            break

                        if states_dict[key] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, A nad vehicle B reached the target position to block the planed way of ego vehicle"
                                f"and signal switches into {actual_value} ({actual_number}) at {time_signal[key]} us.".split()
                            )
                            eval_cond[0] = False
                            break

                        else:
                            # Check reaction time
                            delta_t = time_signal[key] - time_signal[t_small_slot_idx]
                            delta_t = delta_t * 1e-6  # Convert to sec
                            delta_t = round(delta_t, 3)

                            if delta_t <= constants.HilCl.ApThreshold.TRESHOLD_TO_STANDSTILL:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED, system switched to PPC_PARKING_FAILED ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED}) at {time_signal[key]} us."
                                    f" Time gap between PPC_PARKING_FAILED and blocking event is {delta_t} sec. Predefined threshold in Test Case is {constants.HilCl.ApThreshold.TRESHOLD_TO_STANDSTILL} sec"
                                    " ".split()
                                )
                            else:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, system switched to PPC_PARKING_FAILED ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED}) at {time_signal[key]} us."
                                    f" Time gap between PPC_PARKING_FAILED and blocking event is {delta_t} sec and this value is greater than predefined threshold in Test Case is {constants.HilCl.ApThreshold.TRESHOLD_TO_STANDSTILL} sec".split()
                                )
                                eval_cond[0] = False
                                break

                    else:
                        counter += 1

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1

                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Car_A_tx']} signal and/or {signal_name['Car_B_tx']} signal is FAILED."
                    " Vehicle A and/or vehicle B never reached the target position to block the planed way of ego vehicle."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation."
                    f"<br>Required x position for vehicle A is: {car_a_target_x}"
                    f"<br>Required x position for vehicle B is: {car_b_target_x}".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to"
                f" PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})."
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

        signal_summary["Mode transition<br>Maneuvering to Terminate, Reason: Internal limitation"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=car_a_tx_sig, mode="lines", name=signal_name["Car_A_tx"]))
            fig.add_trace(go.Scatter(x=time_signal, y=car_b_tx_sig, mode="lines", name=signal_name["Car_B_tx"]))

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
    name="Maneuvering to Terminate, Internal limitation",
    description="The AP function shall transition from Maneuvering to Terminate mode,"
    " if function has an internal limitation that does not allow to continue the maneuver.",
)
class AupManToTermIntLimit(TestCase):
    """AupManToTermIntLimit Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupManToTermIntLimitCheck,
        ]
