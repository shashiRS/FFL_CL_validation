"""Ego vehicle shall terminate the parking maneuver in case the driver seat is reoccupied."""
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

SIGNAL_DATA = "TERMIN_DRIV_REOCC_SEAT"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USEER_ACTION_REM = "User_action"
        HMI_INFO = "State_on_HMI"
        SEAT_OCCUPANCY_STATE_DRIVER = "Seat_occupancy_state_driver"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USEER_ACTION_REM: "MTS.IO_CAN_AP_Private_CAN.APHMIOut1.APHMIOutUserActionRem",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.SEAT_OCCUPANCY_STATE_DRIVER: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput02.seatOccupancyStatus_frontLeft",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Terminate Maneuvering Check",
    description="Check if ego car terminate the parking maneuver if the driver seat is reoccupied.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class TerminateManDriverReoccCheck(TestStep):
    """TerminateManDriverReoccCheck Test Step."""

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
        user_act_rem = read_data["User_action"].tolist()
        HMI_Info = read_data["State_on_HMI"].tolist()
        seat_occupancy_state_driver = read_data["Seat_occupancy_state_driver"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None

        evaluation1 = " ".join(
            f"The evaluation of AVG State {signal_name['State_on_HMI']} signal is PASSED,"
            f" signal switches to a state diffetent than PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})"
            f" after the driver seat is reoccupied.".split()
        )

        """Evaluation part"""
        # Find the moment when AVG is in control ( ParkingProcedureCtrlState = PPC_PERFORM_PARKING)
        for cnt in range(0, len(HMI_Info)):
            if HMI_Info[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = cnt
                break

        if t1_idx is not None:
            eval_cond = [True] * 1

            # Find the moment when the driver seat is reoccupied
            for cnt in range(t1_idx, len(user_act_rem)):
                if seat_occupancy_state_driver[cnt] == constants.HilCl.Seat.DRIVERS_OCCUPIED:
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                # check between t1_idx and t2_idx if AVG have a constant PPC_PERFORM_PARKING state
                for i in range(t1_idx,t2_idx):
                    if HMI_Info[i] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                            " AVG not in PPC_PERFORM_PARKING state before driver reocc his seat.".split()
                        )
                        break
                # taking the timestamp of t2_idx in order to check the reaction 5s after
                t2_timestamp = time_signal[t2_idx]
                for cnt in range(t2_idx, len(HMI_Info)):
                    if abs(( float(t2_timestamp) - float(time_signal[cnt]) ) / 10**6) > (constants.DgpsConstants.THRESOLD_TIME_S * 10):
                        t3_idx = cnt
                        break
                # check if after 5s the AVG terminate the parking maneuver
                if t3_idx is not None:
                    if HMI_Info[t3_idx] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                            f" AVG didn't terminate the parking maneuver after max 5s from the moment when driver reoccupied"
                            f" the seat (state == {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})".split()
                        )
                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        "TC Failed because the scenario finished before the delay".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                    f" the driver didn't reoccupied the seat"
                    f" ({signal_name['seat_occupancy_state_driver']} != {constants.HilCl.Seat.DRIVERS_OCCUPIED}).".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                f" AVG didn't start the parking maneuver, state != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}.".split()
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
            "Check the reaction of the system while performing the RC parking if the driver seat is reoccupied"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=user_act_rem, mode="lines", name=signal_name["User_action"]))
        fig.add_trace(go.Scatter(x=time_signal, y=seat_occupancy_state_driver, mode="lines", name=signal_name["Seat_occupancy_state_driver"]))
        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
        fig.update_layout(PlotlyTemplate.lgt_tmplt)

        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

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
    name="Terminate Interrupted Maneuvering",
    description=f"In case the driver seat is reoccupied while RC parking is ON, the parking maneuver shall"
                f" terminate within a reasonable time of max 5s (AVG = {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_CANCELED})",
    doors_url="https://jazz.conti.de/rm4/resources/BI_BpGOEd09Ee62R7UY0u3jZg?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17892",
)
class TerminateManDriverReocc(TestCase):
    """TerminateManDriverReocc Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TerminateManDriverReoccCheck,
        ]
