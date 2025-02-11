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

        DRIVER_SEAT = "Drivers_seat_state"
        DRIVING_DIR = "Driving_direction"
        PARKING_CORE_STATE = "Parking_core_state"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.DRIVER_SEAT: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput02.seatOccupancyStatus_frontLeft",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
            self.Columns.PARKING_CORE_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Vehicle state deactivation",
    description="Check driver's seat occupancy dependence of vehicle state deactivation",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupVehStateDeactDrivSeatCheck(TestStep):
    """AupVehStateDeactDrivSeatCheck Test Step."""

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
        driver_seat_state_sig = read_data["Drivers_seat_state"].tolist()
        veh_state_sig = read_data["Driving_direction"].tolist()
        state_on_hmi_sig = read_data["Parking_core_state"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None

        evaluation1 = ""

        """Evaluation part"""

        # Find begining of maneuvering phase
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = cnt
                break

        # Find when seat signal set to NOT occupied
        for cnt in range(t1_idx or 0, len(driver_seat_state_sig)):
            if driver_seat_state_sig[cnt] == constants.HilCl.Seat.DRIVERS_FREE:
                t2_idx = cnt
                break

        for cnt in range(t2_idx or 0, len(veh_state_sig)):
            if veh_state_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL:
                t3_idx = cnt
                break

        if t1_idx is not None and t2_idx is not None and t3_idx is not None:
            test_result = fc.PASS
            evaluation1 = " ".join("The test completed successfully and PASSED.".split())
        else:
            test_result = fc.FAIL
            evaluation1 = " ".join("The test FAILED.".split())

        if t1_idx is None:
            evaluation1 = " ".join("The vehicle did not step into maneuvering state.".split())

        if t2_idx is None:
            evaluation1 = " ".join(
                "The driver seat signal did not turned to NOT OCCUPIED state while maneuvering.".split()
            )

        if t3_idx is None:
            evaluation1 = " ".join(
                "The vehicle did not have a state deactivation after the driver seat was NOT OCCUPIED.".split()
            )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Scanning to Maneuvering, Driver's seat"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=veh_state_sig, mode="lines", name=signal_name["Parking_core_state"]))
            fig.add_trace(go.Scatter(x=time_signal, y=veh_state_sig, mode="lines", name=signal_name["Driving_direction"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=driver_seat_state_sig, mode="lines", name=signal_name["Drivers_seat_state"])
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
    name="Vehicle state deactivation",
    description="Testing if AP system correctly deactivate vehicle state while performing automated maneuver if the driver is not present.",
)
class AupVehStateDeactDrivSeat(TestCase):
    """AupVehStateDeactDrivSeat Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupVehStateDeactDrivSeatCheck,
        ]
