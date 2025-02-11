"""Check if vehicle secured after reversible error occure"""

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

SIGNAL_DATA = "REV_ERR_ABS"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        ABS_STATE = "ABS_state"
        PARKING_CORE_STATE = "Parking_core_state"
        GEAR = "Gear_state"
        PARK_BRAKE_STATE = "Park_brake_state"
        DRIVING_DIR = "Driving_direction"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.ABS_STATE: "MTS.ADAS_CAN.Conti_Veh_CAN.FunctionStates01.ABS_ActiveState",
            self.Columns.PARKING_CORE_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.GEAR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralCurrentGear",
            self.Columns.PARK_BRAKE_STATE: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.StateParkBrake",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Check if vehicle secured",
    description=("Check that the vehicle is secured when entering into inactive mode after a reversible error."),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupRAInactiveVehSecured(TestStep):
    """AupRAInactiveVehSecured Test Step."""

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
        abs_state_sig = read_data["ABS_state"].tolist()
        state_on_hmi_sig = read_data["Parking_core_state"].tolist()
        gear_state = read_data["Gear_state"].tolist()
        park_brake_sig = read_data["Park_brake_state"].tolist()
        veh_state_sig = read_data["Driving_direction"].tolist()

        t1_idx = None
        t_secured_idx = None
        t_standstill_idx = None
        evaluation1 = " "

        """Evaluation part"""
        # Find where ABS get active
        act_idx = HilClFuntions.RisingEdge(abs_state_sig, 0)
        if len(act_idx) == 0:
            act_idx.append(0)
        # Find when parking core switches to Init mode
        for cnt in range(act_idx[0], len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE:
                t1_idx = cnt
                break

        # Find when the vehicle is secured
        for cnt in range(t1_idx or 0, len(state_on_hmi_sig)):
            if (
                park_brake_sig[cnt] == constants.HilCl.Brake.PARK_BRAKE_SET
                and gear_state[cnt == constants.HilCl.Gear.GEAR_P]
            ):
                t_secured_idx = cnt
                break

        # Find when the vehicle is standstill
        for cnt in range(t1_idx or 0, len(veh_state_sig)):
            if veh_state_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL:
                t_standstill_idx = cnt
                break

        # Check conditions of TestRun
        # There was ABS activation
        # The system correctly transitioned to Inactive mode
        # The vehicle was secured and standstill
        if len(act_idx) != 0 and t1_idx is not None and t_secured_idx is not None and t_standstill_idx is not None:
            test_result = fc.PASS
            evaluation1 = " ".join(
                "The evaluation is Passed, there was a correct state transition to Inactive, and after that the vehicle was secured and standstill.".split()
            )

        else:
            test_result = fc.FAIL
            evaluation1 = " ".join("The evaluation is FAILED".split())

        if len(act_idx) == 0:
            evaluation1 = " ".join("Testrun incorrect. There was no ABS activation".split())
        if t1_idx is None:
            evaluation1 = " ".join("The system did not transition to Inactive state".split())
        if t_secured_idx is None:
            evaluation1 = " ".join("The vehicle was not secured after entering Inactive state".split())
        if t_standstill_idx is None:
            evaluation1 = " ".join("The vehicle was not braked to a standstill.".split())

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Vehicle secured"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["Parking_core_state"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=abs_state_sig, mode="lines", name=signal_name["ABS_state"]))
            fig.add_trace(go.Scatter(x=time_signal, y=gear_state, mode="lines", name=signal_name["Gear_state"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=park_brake_sig, mode="lines", name=signal_name["Park_brake_state"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=veh_state_sig, mode="lines", name=signal_name["Driving_direction"]))
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
    name="Check if vehicle secured",
    description=("Check that the vehicle is secured when entering into inactive mode after a reversible error."),
)
class AupRAInactiveVehSec(TestCase):
    """AupRAInactiveVehSec Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupRAInactiveVehSecured,
        ]
