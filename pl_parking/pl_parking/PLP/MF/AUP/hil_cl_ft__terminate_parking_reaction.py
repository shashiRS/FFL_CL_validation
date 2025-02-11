"""evaluation script"""

import logging
import os
import sys

import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants

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
    verifies,
)
from tsf.io.mdf import MDFSignalDefinition

from pl_parking.common_ft_helper import MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.PDW.pdw_helper import plotter_helper

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "TERMINATE_PARKING_REACTION"

__author__ = "Constantin Marius"


class ValidationSignals(MDFSignalDefinition):
    """Example signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        GEAR_AUT = "Gear_auto"
        STATE_ON_HMI = "State_on_HMI"
        PARK_BREAK = "Park_Break"
        DRIVING_DIR = "Driv_dir"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.GEAR_AUT: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActGearPos",
            self.Columns.PARK_BREAK: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.ParkBrake",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
            self.Columns.STATE_ON_HMI: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


signals_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="Terminate parking reaction",
    description=(
        "The AP function shall request braking the ego vehicle to standstill and afterwards request securing "
        "it from rolling away in terminate mode."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class TerminateParkingReaction(TestStep):
    """Terminate parking reaction test step."""

    custom_report = MfHilClCustomTeststepReport

    def __init__(self):
        super().__init__()

    def process(self, **kwargs):
        """Process"""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        signal_summary = {}
        signals = self.readers[SIGNAL_DATA]
        time = signals.index.tolist()
        state_on_hmi = signals[ValidationSignals.Columns.STATE_ON_HMI].tolist()
        aut_gear = signals[ValidationSignals.Columns.GEAR_AUT].tolist()
        parking_break = signals[ValidationSignals.Columns.PARK_BREAK].tolist()
        driving_dir = signals[ValidationSignals.Columns.DRIVING_DIR].tolist()

        self.result.measured_result = None
        time_for_terminate_reaction = 10000000   # 10s
        perform_parking_idx = 0
        parking_finished_idx = 0
        gearbox_cond = 0
        park_brake_cond = 0
        standstill_cond = 0

        for fr in range(0, len(time)):
            if state_on_hmi[fr] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                perform_parking_idx = fr

            if perform_parking_idx:
                if state_on_hmi[fr] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS:
                    parking_finished_idx = fr

                if parking_finished_idx:
                    if time[parking_finished_idx] - time[fr] < time_for_terminate_reaction:
                        if aut_gear[fr] == constants.HilCl.Gear.GEAR_P:
                            gearbox_cond = 1
                        if parking_break[fr] == constants.HilCl.Brake.PARK_BRAKE_SET:
                            park_brake_cond = 1
                        if driving_dir[fr] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL:
                            standstill_cond = 1
                    else:
                        break

        if gearbox_cond and park_brake_cond and standstill_cond:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        if not perform_parking_idx:
            evaluation = " ".join(
                f"Failed because state signal {signals_obj._properties[ValidationSignals.Columns.STATE_ON_HMI]} did "
                f"not took the value perform parking "
                f"({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})".split()
            )
            signal_summary["Terminate parking reaction"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not parking_finished_idx:
            evaluation = " ".join(
                f"Failed because state signal {signals_obj._properties[ValidationSignals.Columns.STATE_ON_HMI]} did "
                f"not took the value parking success "
                f"({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS})".split()
            )
            signal_summary["Terminate parking reaction"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif self.result.measured_result == FALSE:
            evaluation = " ".join(
                f"Failed because {signals_obj._properties[ValidationSignals.Columns.GEAR_AUT]} did not took"
                f"value {constants.HilCl.Gear.GEAR_P} OR "
                f"{signals_obj._properties[ValidationSignals.Columns.PARK_BREAK]} did not took value"
                f"{constants.HilCl.Brake.PARK_BRAKE_SET} OR"
                f"{signals_obj._properties[ValidationSignals.Columns.DRIVING_DIR]} did not took value"
                f"{constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL} in maximum 10 seconds after"
                f"{signals_obj._properties[ValidationSignals.Columns.STATE_ON_HMI]} took value "
                f"{constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS}".split()
            )
            signal_summary["Terminate parking reaction"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
        elif self.result.measured_result == TRUE:
            evaluation = " ".join(
                f"Passed because {signals_obj._properties[ValidationSignals.Columns.GEAR_AUT]} took"
                f"value {constants.HilCl.Gear.GEAR_P} AND "
                f"{signals_obj._properties[ValidationSignals.Columns.PARK_BREAK]} took value"
                f"{constants.HilCl.Brake.PARK_BRAKE_SET} AND"
                f"{signals_obj._properties[ValidationSignals.Columns.DRIVING_DIR]} took value"
                f"{constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL} in maximum 10 seconds after"
                f"{signals_obj._properties[ValidationSignals.Columns.STATE_ON_HMI]} took value "
                f"{constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS}".split()
            )
            signal_summary["Terminate parking reaction"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )

        plot_signals = [
            ValidationSignals.Columns.STATE_ON_HMI,
            ValidationSignals.Columns.GEAR_AUT,
            ValidationSignals.Columns.PARK_BREAK,
            ValidationSignals.Columns.DRIVING_DIR,
        ]
        fig_fr = plotter_helper(time, signals, plot_signals, signals_obj._properties)
        fig_fr.update_layout(title="Used signals")
        self.result.details["Plots"].append(fig_fr.to_html(full_html=False, include_plotlyjs=False))


@verifies(
    requirement="965593",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_Pepor8lcEe2iKqc0KPO99Q?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
@testcase_definition(
    name="Terminate parking reaction TC",
    description="The AP function shall request braking the ego vehicle to standstill and afterwards request securing "
    "it from rolling away in terminate mode.",
)
class TerminateParkingReactionTestCase(TestCase):
    """Terminate parking reaction test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            TerminateParkingReaction,
        ]
