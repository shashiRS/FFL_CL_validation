"""Mode Transition check, Init to Scanning: No vehicle deactivation event"""

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

SIGNAL_DATA = "INIT_TO_SCANN_NO_VEH_DEACT"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        TARILER_CONNECTION = "Trailer_connection"
        DOOR_STATE = "Door_state"
        FUEL_CAP_STATE = "Fuel_cap_state"
        DRIVER_SEAT_OCCUPANCY = "Driver_in_seat"
        IGNITION = "Ignition"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.TARILER_CONNECTION: "MTS.ADAS_CAN.Conti_Veh_CAN.Trailer.TrailerConnection",
            self.Columns.DOOR_STATE: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput01.DoorOpen",
            self.Columns.FUEL_CAP_STATE: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.TankCapOpen",
            self.Columns.DRIVER_SEAT_OCCUPANCY: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput02.seatOccupancyStatus_frontLeft",
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Init to Scannning, No vehicle deactivation state",
    description="Check system reaction if there is no vehicle deactivation state event",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupInitScannVehDeactCheck(TestStep):
    """AupInitScannVehDeactCheck Test Step."""

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
        ignition_sig = read_data["Ignition"].tolist()
        trailer_conn_sig = read_data["Trailer_connection"].tolist()
        door_sig = read_data["Door_state"].tolist()
        fuel_cap_sig = read_data["Fuel_cap_state"].tolist()
        drv_seat_sig = read_data["Driver_in_seat"].tolist()

        t_ign_on_idx = None
        t_scanning_idx = None
        t_ign_off_idx = None

        vehicle_deact_events = [False] * 4

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED, signal swtiches to PPC_SCANNING_IN ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN}) if there is no vehicle deactiovation state.".split()
        )

        """Evaluation part"""
        # Find AP active user action on HMI
        for cnt in range(0, len(ignition_sig)):
            if ignition_sig[cnt] == constants.HilCl.CarMaker.IGNITION_ON:
                t_ign_on_idx = cnt
                break
        if t_ign_on_idx is not None:

            # Find when system scitches to Scanning
            for cnt in range(t_ign_on_idx, len(state_on_hmi_sig)):
                if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN:
                    t_scanning_idx = cnt
                    break

            # Find ignition off event
            for cnt in range(t_ign_on_idx, len(ignition_sig)):
                if ignition_sig[cnt] == constants.HilCl.CarMaker.IGNITION_OFF:
                    t_ign_off_idx = cnt
                    break

            if t_ign_off_idx is not None:
                eval_cond = [True] * 1

                if t_scanning_idx is not None:
                    # Check vehicle deactivation state when system switches to scanning
                    if (
                        trailer_conn_sig[t_scanning_idx]
                        != constants.HilCl.TrailerConnection.NO_DETECT_TRAILERCONNECTION
                        or door_sig[t_scanning_idx] != constants.HilCl.DoorOpen.DOORS_CLOSED
                        or fuel_cap_sig[t_scanning_idx] != constants.HilCl.TunkCap.CLOSED
                        or drv_seat_sig[t_scanning_idx] != constants.HilCl.Seat.DRIVERS_OCCUPIED
                    ):
                        eval_cond[0] = False
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switched to"
                            f" PPC_SCANNING_IN ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN})"
                            " but there was a vehicle deaction state related event.".split()
                        )

                    else:
                        # Test PASSED
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED, signal swtiches to PPC_SCANNING_IN ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN}) if there is no vehicle deactiovation state.".split()
                        )
                else:
                    # Check whole ignitnon cycle for vehicle deactivation event if there was no scanning in TestRun
                    for cnt in range(t_ign_on_idx, t_ign_off_idx):
                        if trailer_conn_sig[cnt] != constants.HilCl.TrailerConnection.NO_DETECT_TRAILERCONNECTION:
                            vehicle_deact_events[0] = True

                        if door_sig[cnt] != constants.HilCl.DoorOpen.DOORS_CLOSED:
                            vehicle_deact_events[1] = True

                        if fuel_cap_sig[cnt] != constants.HilCl.TunkCap.CLOSED:
                            vehicle_deact_events[2] = True

                        if drv_seat_sig[cnt] != constants.HilCl.Seat.DRIVERS_OCCUPIED:
                            vehicle_deact_events[3] = True

                    if any(vehicle_deact_events):
                        eval_cond[0] = False
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal does not switch to"
                            f" PPC_SCANNING_IN ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN}) because there is a vehicle deactiovation state."
                            " TestRun was not valid to Test Case.".split()
                        )
                    else:
                        eval_cond[0] = False
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal does not switch to"
                            f" PPC_SCANNING_IN ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN})"
                            " but there was no vehicle deaction state related event.".split()
                        )

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Ignition']} signal is FAILED, signal never set to FALSE ({constants.HilCl.CarMaker.IGNITION_OFF}) after Ignition On event."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Ignition']} signal is FAILED, signal never set to TRUE ({constants.HilCl.CarMaker.IGNITION_ON})."
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

        signal_summary[
            "Required AP state change: Init to Scanning. Reason: No vehivle deactivation"
            "<br> Vehicle deactivation happens if ANY of following conditions is fullfiled:"
            f"<br> - Value of {signal_name['Trailer_connection']} != {constants.HilCl.TrailerConnection.NO_DETECT_TRAILERCONNECTION}"
            f"<br> - Value of {signal_name['Door_state']} != {constants.HilCl.DoorOpen.DOORS_CLOSED}"
            f"<br> - Value of {signal_name['Fuel_cap_state']} != {constants.HilCl.TunkCap.CLOSED}"
            f"<br> - Value of {signal_name['Driver_in_seat']} != {constants.HilCl.Seat.DRIVERS_OCCUPIED}"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=ignition_sig, mode="lines", name=signal_name["Ignition"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=trailer_conn_sig, mode="lines", name=signal_name["Trailer_connection"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=door_sig, mode="lines", name=signal_name["Door_state"]))
            fig.add_trace(go.Scatter(x=time_signal, y=fuel_cap_sig, mode="lines", name=signal_name["Fuel_cap_state"]))
            fig.add_trace(go.Scatter(x=time_signal, y=drv_seat_sig, mode="lines", name=signal_name["Driver_in_seat"]))

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
    name="Mode transition: Init to Scanning, Vehicle deaction",
    description="The AP function shall transition from Init to Scanning mode if vehicle state deactivation is NOT triggered",
)
class AupInitScannVehDeact(TestCase):
    """AupInitScannVehDeact Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupInitScannVehDeactCheck,
        ]
