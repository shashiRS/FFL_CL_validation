"""The vehicle shall secure within Tsecure time(2sec): when maneuver terminated"""

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

"__author__ = Rakesh Kyathsandra Jayaramu"

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "SECURE_VEHICLE_WITHIN_TSECURE_MAN_TO_TERMINATE_BRAKE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        DRIVING_DIR = "Driv_dir"
        PARK_BREAK = "Park_Break"
        PARKING_CORE_STATE = "Parking_Core_State"
        BRAKE = "Brake"
        ACTUAL_GEAR = "Actual_Gear"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
            self.Columns.PARK_BREAK: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.ParkBrake",
            self.Columns.PARKING_CORE_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput06.BrakePressureDriver",
            self.Columns.ACTUAL_GEAR: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActualGear",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Secure the vehicle",
    description="The goal of this test case is to verify, that in case of an maneuver termination"
    " the vehicle shall secure within T_secure(2sec).",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class VehicleSecureBrakeOnCheck(TestStep):
    """VehicleSecureBrakeOnCheck Test Step."""

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
        time_signal = read_data.index
        driv_dir_sig = read_data["Driv_dir"].tolist()
        park_break_sig = read_data["Park_Break"].tolist()
        parking_core_state_sig = read_data["Parking_Core_State"].tolist()
        brake_sig = read_data["Brake"].tolist()
        actual_gear = read_data["Actual_Gear"].tolist()
        t_man_idx = None
        t_interrupt_idx = None
        t_standstill_idx = None
        t_parking_break_idx = None
        t_actual_gear_idx = None

        eval_cond = []
        evaluation1 = {}

        """Evaluation part"""
        # Find when AP switches to Maneuvering mode
        for cnt in range(0, len(parking_core_state_sig)):
            if parking_core_state_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_man_idx = cnt
                break

        if t_man_idx is not None:
            # Find break interrupt request
            for cnt in range(t_man_idx, len(brake_sig)):
                if parking_core_state_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_CANCELED:
                    t_interrupt_idx = cnt
                    break

            if t_interrupt_idx is not None:
                # taking the timestamp of t_interrupt_idx in order to check the reaction after maneuver termination(PPC_PARKING_CANCELED)
                for idx in range(t_interrupt_idx, len(parking_core_state_sig)):
                    if driv_dir_sig[idx] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL:
                        t_standstill_idx = idx
                        break
                for idx in range(t_interrupt_idx, len(parking_core_state_sig)):
                    if park_break_sig[idx] == constants.HilCl.Brake.PARK_BRAKE_SET:
                        t_parking_break_idx = idx
                        break
                for idx in range(t_interrupt_idx, len(parking_core_state_sig)):
                    if actual_gear[idx] == constants.HilCl.VehCanActualGear.PARK_ACTUALGEAR:
                        t_actual_gear_idx = idx
                        break

                if t_standstill_idx is not None:
                    t1_timestamp = time_signal[t_interrupt_idx]
                    t2_timestamp = time_signal[t_standstill_idx]
                    actual_time = (float(t2_timestamp) - float(t1_timestamp)) / 10**6
                    # checking if the vehicle goes to standstill in 2 sec
                    if actual_time <= constants.HilCl.SotifTime.T_SECURE:
                        eval_cond.append(True)
                        evaluation1["Check the STANDSTILL state within T secure after maneuver termination."] = (
                            " ".join(
                                f"The evaluation of {signal_name['Driv_dir']} signal is PASSED, signal switched to STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL}) within T_secure(2sec) and actual time taken is {actual_time} sec.<br>".split()
                            )
                        )
                    else:
                        eval_cond.append(False)
                        evaluation1["Check the STANDSTILL state within T secure after maneuver termination."] = (
                            " ".join(
                                f"The evaluation of {signal_name['Driv_dir']} signal is FAILED, signal  switched to STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL}) after T_secure(2sec)) and actual time taken is {actual_time} sec.<br>".split()
                            )
                        )
                else:
                    eval_cond.append(False)
                    evaluation1["Check the STANDSTILL state within T secure after maneuver termination."] = " ".join(
                        f"The evaluation of {signal_name['Driv_dir']} signal is FAILED, signal never switched to STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL}).<br>".split()
                    )

                if t_parking_break_idx is not None:
                    t1_timestamp = time_signal[t_interrupt_idx]
                    t2_timestamp = time_signal[t_parking_break_idx]
                    actual_time = (float(t2_timestamp) - float(t1_timestamp)) / 10**6
                    # checking if the vehicle parking break is set(1) in 2 sec
                    if actual_time <= constants.HilCl.SotifTime.T_SECURE:
                        eval_cond.append(True)
                        evaluation1["Check the PARK_BREAK_SET state within T secure after maneuver termination."] = (
                            " ".join(
                                f"The evaluation of {signal_name['Park_Break']} signal is PASSED, signal switched to PARK_BREAK_SET ({constants.HilCl.Brake.PARK_BRAKE_SET}) within T_secure(2sec) and actual time taken is {actual_time} sec.<br>".split()
                            )
                        )
                    else:
                        eval_cond.append(False)
                        evaluation1["Check the PARK_BREAK_SET state within T secure after maneuver termination."] = (
                            " ".join(
                                f"The evaluation of {signal_name['Park_Break']} signal is FAILED, signal  switched to PARK_BREAK_SET ({constants.HilCl.Brake.PARK_BRAKE_SET}) after T_secure(2sec) and actual time taken is {actual_time} sec.<br>".split()
                            )
                        )
                else:
                    eval_cond.append(False)
                    evaluation1["Check the PARK_BREAK_SET state within T secure after maneuver termination."] = (
                        " ".join(
                            f"The evaluation of {signal_name['Park_Break']} signal is FAILED, signal never switched to PARK_BREAK_SET ({constants.HilCl.Brake.PARK_BRAKE_SET}).<br>".split()
                        )
                    )

                if t_actual_gear_idx is not None:
                    t1_timestamp = time_signal[t_interrupt_idx]
                    t2_timestamp = time_signal[t_actual_gear_idx]
                    # checking if the vehicle actual gear is set to (11) in 2 sec
                    actual_time = (float(t2_timestamp) - float(t1_timestamp)) / 10**6
                    if actual_time <= constants.HilCl.SotifTime.T_SECURE:
                        eval_cond.append(True)
                        evaluation1["Check the ACTUAL_GEAR state within T secure after maneuver termination."] = (
                            " ".join(
                                f"The evaluation of {signal_name['Actual_Gear']} signal is PASSED, signal switched to ACTUAL_GEAR ({constants.HilCl.VehCanActualGear.PARK_ACTUALGEAR}) within T_secure(2sec) and actual time taken is {actual_time} sec.<br>".split()
                            )
                        )
                    else:
                        eval_cond.append(False)
                        evaluation1["Check the ACTUAL_GEAR state within T secure after maneuver termination."] = (
                            " ".join(
                                f"The evaluation of {signal_name['Actual_Gear']} signal is FAILED, signal  switched to ACTUAL_GEAR ({constants.HilCl.VehCanActualGear.PARK_ACTUALGEAR}) after T_secure(2sec)) and actual time taken is {actual_time} sec.<br>".split()
                            )
                        )
                else:
                    eval_cond.append(False)
                    evaluation1["Check the ACTUAL_GEAR state within T secure after maneuver termination."] = " ".join(
                        f"The evaluation of {signal_name['Actual_Gear']} signal is FAILED, signal never switched to ACTUAL_GEAR ({constants.HilCl.VehCanActualGear.PARK_ACTUALGEAR}).<br>".split()
                    )
            else:
                eval_cond.append(False)
                evaluation1["Check the vehicle secure state within T secure after maneuver termination."] = " ".join(
                    f"The evaluation of {signal_name['Brake']} signal is FAILED, signal never reached AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR ({constants.HilCl.ApThreshold.AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR}).<br>"
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )
        else:
            eval_cond.append(False)
            evaluation1["Check the vehicle secure state within T secure after maneuver termination."] = " ".join(
                f"The evaluation of {signal_name['Parking_Core_State']} signal is FAILED, signal never switched to PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}). AP funtion was never activated.<br>"
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

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(evaluation1)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart"""

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=driv_dir_sig, mode="lines", name=signal_name["Driv_dir"]))
        fig.add_trace(go.Scatter(x=time_signal, y=park_break_sig, mode="lines", name=signal_name["Park_Break"]))
        fig.add_trace(go.Scatter(x=time_signal, y=brake_sig, mode="lines", name=signal_name["Brake"]))
        fig.add_trace(go.Scatter(x=time_signal, y=actual_gear, mode="lines", name=signal_name["Actual_Gear"]))
        fig.add_trace(
            go.Scatter(x=time_signal, y=parking_core_state_sig, mode="lines", name=signal_name["Parking_Core_State"])
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
    name="Secure the vehicle.",
    description="The goal of this test case is to verify, that in case of an maneuver termination the vehicle shall secure within T_secure(2sec).",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_2-G8I91qEe62R7UY0u3jZg&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_lWHOEPvsEeqIqKySVwTVNQ%2Fcomponents%2F_u4eQYMlKEe2iKqc0KPO99Q&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
class VehicleSecureBrakeOn(TestCase):
    """VehicleSecureBrakeOn Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VehicleSecureBrakeOnCheck,
        ]
