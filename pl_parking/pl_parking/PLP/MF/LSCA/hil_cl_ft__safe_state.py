"""Check Safe State when LSCA is deactivated"""

import logging
import os
import sys

import plotly.graph_objects as go

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", ".."))
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
from pl_parking.common_ft_helper import MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.constants import PlotlyTemplate

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "SAFE_STATE_LSCA_INACTIVE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        DRIVING_DIR = "Driving_direction"
        GEAR_POSITION = "Gear_position"
        PARKING_BRAKE = "Parking_brake"
        USER_ACTION = "User_action"  # Signal for HMI button press
        HMI_INFO = "State_on_HMI"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
            self.Columns.GEAR_POSITION: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActualGear",
            self.Columns.PARKING_BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.ParkBrake",
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Safe state check when LSCA is deactivated.",
    description="The system shall enter a safe state if the driver deactivates LSCA using the HMI button.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class SafeStateCheck(TestStep):
    """SafeStateCheck Test Step."""

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
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        hmi_state_sig = read_data["State_on_HMI"].tolist()
        driv_dir_sig = read_data["Driving_direction"].tolist()
        gear_position_sig = read_data["Gear_position"].tolist()
        parking_brake_sig = read_data["Parking_brake"].tolist()
        user_action_sig = read_data["User_action"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Driving_direction']}; {signal_name['Gear_position']}; {signal_name['Parking_brake']} is PASSED, the system goes in safe state meaning "
            f"vehicle is in standstill position, gear set to 'P' and parking brakes set to active, after AUP maneuver starts ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}) "
            f"and LSCA it's deactivated via HMI ({constants.HilCl.Hmi.Command.TAP_ON_LSCA}).".split()
        )

        # Step 1: Detect if the HMI button to deactivate LSCA (TAP_ON_LSCA = 65) was pressed
        for cnt in range(0, len(user_action_sig)):
            if user_action_sig[cnt] == constants.HilCl.Hmi.Command.TAP_ON_LSCA:
                t1_idx = cnt
                break

        if t1_idx is None:
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['User_action']} is FAILED, LSCA deactivation via HMI button was not detected.".split()
            )
        else:
            # Step 2: Check for safe state (standstill, gear in P, and parking brake engaged)
            for cnt in range(t1_idx, len(driv_dir_sig)):
                if (
                    driv_dir_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL
                    and gear_position_sig[cnt] == constants.HilCl.VehCanActualGear.PARK_ACTUALGEAR
                    and parking_brake_sig[cnt] == constants.HilCl.Brake.PARK_BRAKE_SET
                ):
                    t2_idx = cnt
                    break

            if t2_idx is None:
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Driving_direction']}; {signal_name['Gear_position']}; {signal_name['Parking_brake']} is FAILED. The vehicle did not enter in safe state, meaning the vehicle isn't in standstill ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL}) OR "
                    f"the gear is NOT set to 'P' ({constants.HilCl.VehCanActualGear.PARK_ACTUALGEAR}) OR parking brakes are inactive ({constants.HilCl.Brake.PARK_BRAKE_SET}).".split()
                )
            else:
                # Step 3: Detect when driver starts the parking maneuver
                for cnt in range(t2_idx, len(hmi_state_sig)):
                    if hmi_state_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                        t3_idx = cnt
                        break

                if t3_idx is None:
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['State_on_HMI']} is FAILED, driver did not start the parking maneuver.".split()
                    )
                elif t2_idx < t3_idx:
                    test_result = fc.FAIL
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Driving_direction']},{signal_name['Gear_position']} and {signal_name['Parking_brake']} is FAILED, safe state occurred before driver started the parking maneuver.".split()
                    )
                else:
                    test_result = fc.PASS

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Safe state evaluation after LSCA deactivated via HMI"] = evaluation1

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_header_left="Evaluation")
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        # Generate chart if test result FAILED
        if test_result == fc.FAIL:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(x=time_signal, y=driv_dir_sig, mode="lines", name=signal_name["Driving_direction"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=hmi_state_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=gear_position_sig, mode="lines", name=signal_name["Gear_position"])
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=parking_brake_sig, mode="lines", name=signal_name["Parking_brake"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=user_action_sig, mode="lines", name=signal_name["User_action"]))
            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        # Add the data in the table from Functional Test Filter Results
        additional_results_dict = {"Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)}}

        for plot in plots:
            if isinstance(plot, go.Figure):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="Safe State when LSCA is deactivated.",
    description="The system shall enter a safe state (standstill, gear to P, parking brake engaged) after LSCA is deactivated via HMI button and AUP maneuver starts.",
)
class SafeStateLscaInactive(TestCase):
    """SafeStateLscaInactive Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SafeStateCheck,
        ]
