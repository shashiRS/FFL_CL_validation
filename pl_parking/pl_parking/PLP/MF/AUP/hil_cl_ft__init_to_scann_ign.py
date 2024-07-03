"""Mode Transition check, Init to Scanning: Ego vehicle has ignition on"""

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

SIGNAL_DATA = "INIT_TO_SCANN_IGNITION"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        IGNITION = "Car_ignition"
        CAR_SPEED = "Car_speed"
        GEAR_STATE = "Gear_state"
        PARKING_CORE_STATE = "Parking_core_state"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.IGNITION: "MTS.ADC5xx_Device.VD_DATA.IuAdditionalBCMStatusPort.ignition.ignitionOn_nu",
            self.Columns.CAR_SPEED: "CM.Car.v",
            self.Columns.GEAR_STATE: "MTS.ADC5xx_Device.EM_DATA.EmHMIGeneralInputPort.general.currentGear_nu",
            self.Columns.PARKING_CORE_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Init to Scannning check",
    description="Check the transition is correctly happening based on the ignition condition",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupInitScannIgnCheck(TestStep):
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
        ignition_sig = read_data["Car_ignition"].tolist()
        car_speed_sig = read_data["Car_speed"].tolist()
        gear_state_sig = read_data["Gear_state"].tolist()
        p_core_state_sig = read_data["Parking_core_state"].tolist()

        t0_idx = None
        t1_idx = None
        t2_idx = None
        t3_idx = None
        t4_idx = None
        evaluation1 = " "

        """Evaluation part"""
        # Find when the AP is in INIT
        for cnt in range(0, len(p_core_state_sig)):
            if (
                p_core_state_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE
                or p_core_state_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_INACTIVE
                or p_core_state_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE
            ):
                t0_idx = cnt
                break
        # Find when the AP transition to scanning
        for cnt in range(0, len(p_core_state_sig)):
            if p_core_state_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN:
                t1_idx = cnt
                break
        # Find when ignition turned on
        for cnt in range(0, len(ignition_sig)):
            if ignition_sig[cnt] == constants.HilCl.CarMaker.IGNITION_ON:  # create ignition class
                t2_idx = cnt
                break
        # Find when turned to DRIVE gear
        for cnt in range(0, len(gear_state_sig)):
            if gear_state_sig[cnt] == constants.GearReqConstants.GEAR_D:
                t3_idx = cnt
                break

        for cnt in range(t1_idx - 1, t1_idx + 1):
            if car_speed_sig[cnt] >= constants.HilCl.ApThreshold.AP_G_V_SCANNING_THRESH_ON_MPS:
                t4_idx = cnt
                break

        if t1_idx is not None and t2_idx is not None and t3_idx is not None:
            eval_cond = [True] * 1

            states_dict = HilClFuntions.States(p_core_state_sig, t1_idx, len(p_core_state_sig), None)
            counter = 0
            # counter == 0 : This is Init mode, because states are collected from the beginning of Init.
            # counter == 1: This has to be Scanning mode in this case. System has to switch from Init to Scanning

            # Keys contains the idx
            # Check mode after Init mode
            for key in states_dict:
                actual_state = constants.HilCl.Hmi.HeadUnit.dict_head_unit.get(states_dict[key])
                if (
                    actual_state == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE
                    or actual_state == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_INACTIVE
                    or actual_state == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE
                ):
                    counter = 1
                    continue
                if states_dict[key] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN:
                    if counter == 1:
                        if key < t2_idx:
                            evaluation1 = " ".join(
                                f"The evaluation is FAILED, AP switches into {actual_state}"
                                f" before ego vehicle has IGNITION on".split()
                            )
                            eval_cond[0] = False
                            break
                        if key < t3_idx:
                            evaluation1 = " ".join(
                                "The evaluation is FAILED, since "
                                "the gear condition was met after the ignition".split()
                            )
                            eval_cond[0] = False
                            break
                        if t4_idx is not None:
                            evaluation1 = " ".join(
                                "The evaluation is FAILED, since "
                                f"the vehicle was travelling faster than the AP_G_V_SCANNING_THRESH_ON_MPS"
                                f" ({constants.HilCl.ApThreshold.AP_G_V_SCANNING_THRESH_ON_MPS} mps).".split()
                            )
                            eval_cond[0] = False
                            break
                    else:
                        evaluation1 = " ".join(
                            "The evaluation is FAILED, AP switches into SCANNING" " before being in INIT state".split()
                        )
                        if t0_idx is None:
                            evaluation1.join("Invalid TestRun, there were no INIT state during the recording.")
                        eval_cond[0] = False
                        break
        elif t1_idx is None:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join("The evaluation is FAILED, AP function never turned to SCANNING.".split())
        elif t2_idx is None:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                "The evaluation is FAILED, Invalid TestRun, the ignition was never turned on in the ego vehicle "
                "during the recording.".split()
            )
        elif t3_idx is None:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                "The evaluation is FAILED, Invalid TestRun, the ego vehicle was never turned to drive gear "
                "during the recording.".split()
            )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join("The evaluation is FAILED, Invalid TestRun.".split())
        if all(eval_cond):
            test_result = fc.PASS
            evaluation1 = " ".join(
                "The evaluation is PASSED, AP function swtiches to Scanning mode after ignition turned on.".split()
            )
        else:
            test_result = fc.FAIL
        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Init to Scanning, Ignition on"] = evaluation1

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=ignition_sig, mode="lines", name=signal_name["Car_ignition"]))
            fig.add_trace(go.Scatter(x=time_signal, y=car_speed_sig, mode="lines", name=signal_name["Car_speed"]))
            fig.add_trace(go.Scatter(x=time_signal, y=gear_state_sig, mode="lines", name=signal_name["Gear_state"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=p_core_state_sig, mode="lines", name=signal_name["Parking_core_state"])
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
    name="Mode transition: Init to Scanning",
    description="After turning on the ignition (given that there is no irreversible error, and the vehicle speed is "
    "below the threshold), the AP switches from INIT to SCANNING after ignition is turned on.",
)
class FtCommon(TestCase):
    """AupInitScannTrav Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupInitScannIgnCheck,
        ]
