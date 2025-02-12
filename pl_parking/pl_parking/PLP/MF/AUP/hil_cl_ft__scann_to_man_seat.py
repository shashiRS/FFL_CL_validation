"""Mode Transition check, Scanning to Maneuvering: Driver's seat"""

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

SIGNAL_DATA = "SCANNING_TO_MANEUVERING_DRIVERS_SEAT"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USEER_ACTION = "User_action"
        SEAT = "Drivers_seat_state"
        HMI_INFO = "State_on_HMI"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USEER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.SEAT: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput02.seatOccupancyStatus_frontLeft",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Scannning to Maneivering",
    description="Check driver's seat occupancy dependence of mode transition",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupScannToManDrivSeatCheck(TestStep):
    """AupScannToManDrivSeatCheck Test Step."""

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
        user_act_sig = read_data["User_action"].tolist()
        driver_seat_state_sig = read_data["Drivers_seat_state"].tolist()
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None

        evaluation1 = ""

        """Evaluation part"""

        # Find begining of scanning phase
        for cnt in range(0, len(state_on_hmi_sig)):
            # Begining of Scanning
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN:
                t1_idx = cnt
                break

        if t1_idx is not None:
            # Find when seat signal set to NOT occupied
            for cnt in range(t1_idx, len(driver_seat_state_sig)):
                if driver_seat_state_sig[cnt] == constants.HilCl.Seat.DRIVERS_FREE:
                    t2_idx = cnt
                    break

            # Find when user try to start parking in
            for cnt in range(t1_idx, len(user_act_sig)):
                if user_act_sig[cnt] == constants.HilCl.Hmi.Command.TAP_ON_START_PARKING:
                    t3_idx = cnt
                    break

            # Check this is a pozitive or a negative test
            # Positive - Driver is present on the driver's seat when driver taps on TAP_ON_START_PARKING
            # Negative - Driver is !NOT! present on the driver's seat  when driver taps on TAP_ON_START_PARKING
            if t3_idx is not None:

                if t2_idx is None:
                    # Positive check
                    eval_cond = [True] * 1

                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED, signal state switches to Maneuvering mode when an automated parking maneuver"
                        f" is initiated from inside the vehicle, the driver is present on the driver's seat. Driver's seat related signal: {signal_name['Drivers_seat_state']}".split()
                    )

                    states_dict = HilClFuntions.States(state_on_hmi_sig, t1_idx, len(state_on_hmi_sig), 1)

                    counter = 0
                    # counter == 0 : This is Scanning mode, because states are collected from the begining of Scanning.
                    # counter == 1: This has to be Maneuvering in this case

                    if len(states_dict) == 1:
                        local_key = list(states_dict.keys())[0]
                        local_actual_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE.get(
                            states_dict[local_key]
                        )
                        local_actual_number = int(states_dict[local_key])
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, "
                            f" siganl state stills in {local_actual_value} ({local_actual_number}) from {time_signal[t1_idx]} us until end of the measurement.".split()
                        )
                        eval_cond[0] = False

                    else:
                        # Keys contains the idx
                        # Check mode
                        for key in states_dict:
                            actual_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE.get(
                                states_dict[key]
                            )
                            actual_number = int(states_dict[key])

                            if counter == 0:
                                counter += 1
                                continue

                            if counter == 1:
                                if key < t3_idx:
                                    evaluation1 = " ".join(
                                        f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, "
                                        f" signal state switches into {actual_value} ({actual_number}) at {time_signal[key]} us before driver starts parking maneuver.".split()
                                    )
                                    eval_cond[0] = False
                                    break

                                if (
                                    states_dict[key]
                                    == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_INACTIVE
                                    or states_dict[key]
                                    == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PREPARE_PARKING
                                ):
                                    counter += 1
                                    continue

                                if (
                                    states_dict[key]
                                    != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING
                                ):
                                    evaluation1 = " ".join(
                                        f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, the driver is present on the driver's seat and driver starts parking"
                                        f" maneuver but signalstate switches into {actual_value} ({actual_number}) at {time_signal[key]} us.".split()
                                    )
                                    eval_cond[0] = False
                                    break
                                counter += 1

                            if counter == 2:
                                if (
                                    states_dict[key]
                                    == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PREPARE_PARKING
                                ):
                                    counter += 1
                                    continue

                                if (
                                    states_dict[key]
                                    != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING
                                ):
                                    evaluation1 = " ".join(
                                        f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, the driver is present on the driver's seat and driver starts parking"
                                        f" maneuver but signalstate switches into {actual_value} ({actual_number}) at {time_signal[key]} us.".split()
                                    )
                                    eval_cond[0] = False
                                    break
                                counter += 1

                            if counter == 3:
                                if (
                                    states_dict[key]
                                    != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING
                                ):
                                    evaluation1 = " ".join(
                                        f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, the driver is present on the driver's seat and driver starts parking"
                                        f" maneuver but signalstate switches into {actual_value} ({actual_number}) at {time_signal[key]} us.".split()
                                    )
                                    eval_cond[0] = False
                                    break
                                counter += 1

                    signal_summary[
                        "Required AP state change: Scanning to Maneuvering. Reason: Driver's seat occupied"
                    ] = evaluation1

                else:
                    # Negative check
                    eval_cond = [True] * 1

                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED, signal state does not switch to Maneuvering mode when an automated parking maneuver"
                        f" is initiated from inside the vehicle, the driver is NOT present on the driver's seat. Driver's seat related signal: {signal_name['Drivers_seat_state']}".split()
                    )

                    states_dict = HilClFuntions.States(state_on_hmi_sig, t1_idx, len(state_on_hmi_sig), 1)

                    counter = 0
                    # counter == 0 : This is Scanning mode, because states are collected from the begining of Scanning.
                    # counter == 1: This has to be Scanning or Init mode in this case but shall not be Maneuvering.

                    # Keys contains the idx
                    # Check mode
                    for key in states_dict:
                        actual_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE.get(
                            states_dict[key]
                        )
                        actual_number = int(states_dict[key])

                        if counter == 0:
                            counter += 1
                            continue

                        if counter == 1:
                            if key < t3_idx:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, "
                                    f" signal state switches into {actual_value} ({actual_number}) at {time_signal[key]} us before driver starts parking maneuver.".split()
                                )
                                eval_cond[0] = False
                                break

                            if (
                                states_dict[key] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_INACTIVE
                                or states_dict[key] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PREPARE_PARKING
                            ):
                                counter += 1
                                continue

                            if states_dict[key] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, the driver is NOT present on the driver's seat and driver starts parking"
                                    f" maneuver but signal state switches into {actual_value} ({actual_number}) at {time_signal[key]} us.".split()
                                )
                                eval_cond[0] = False
                                break
                            counter += 1

                        if counter == 2:
                            if states_dict[key] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PREPARE_PARKING:
                                counter += 1
                                continue

                            if states_dict[key] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, the driver is NOT present on the driver's seat and driver starts parking"
                                    f" maneuver but signal state switches into {actual_value} ({actual_number}) at {time_signal[key]} us.".split()
                                )
                                eval_cond[0] = False
                                break
                            counter += 1

                        if counter == 3:
                            if states_dict[key] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, the driver is NOT present on the driver's seat and driver starts parking"
                                    f" maneuver but signal state switches into {actual_value} ({actual_number}) at {time_signal[key]} us.".split()
                                )
                                eval_cond[0] = False
                                break
                            counter += 1

                    signal_summary[
                        "Required AP state change: Not switch to Maneuvering. Reason: Driver's seat not occupied"
                    ] = evaluation1

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['User_action']} signal is FAILED, driver never started parking maneuver. State of signal never switched to TAP_ON_START_PARKING ({constants.HilCl.Hmi.Command.TAP_ON_START_PARKING})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )
                signal_summary[
                    "Required AP state change: Not switch to Maneuvering. Reason: Driver's seat not occupied"
                ] = evaluation1
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal state never switched to PPC_SCANNING_IN ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN})."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )
            signal_summary[
                "Required AP state change: Not switch to Maneuvering. Reason: Driver's seat not occupied"
            ] = evaluation1

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=driver_seat_state_sig, mode="lines", name=signal_name["Drivers_seat_state"])
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
    name="Mode transition: Scanning to Maneuvering, Reaction on seat state",
    description="If an automated parking maneuver is initiated from inside the vehicle, the driver is present on the driver's seat.",
)
class AupScannToManDrivSeat(TestCase):
    """AupScannToManDrivSeat Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupScannToManDrivSeatCheck,
        ]
