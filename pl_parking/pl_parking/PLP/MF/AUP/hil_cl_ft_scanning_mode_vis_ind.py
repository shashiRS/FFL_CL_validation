"""Scanning mode visual indicator - evaluation script"""

import logging
import os
import sys

import pandas as pd

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import TestCase, TestStep, register_signals, testcase_definition, teststep_definition
from tsf.io.mdf import MDFSignalDefinition

import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.PDW.pdw_helper import plotter_helper

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "Constantin Marius"

SIGNAL_DATA = "SCANNING_MODE_VISUAL_INDICATOR"


class ValidationSignals(MDFSignalDefinition):
    """Example signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        TIMESTAMP = "mts_ts"
        PDW_CAN_STATE = "PDW_State"
        VEH_VELOCITY = "Vehicle_velocity"
        IGNITION = "Veh_ignition"
        USER_ACTION = "User_action"
        HMI_INFO = "State_on_HMI"
        GENERAL_SCREEN = "General_screen"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
        }


signals_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="Parking out scanning visual indicator",
    description=(
        "When the function is searching for free parking out situations to offer, it shall indicate this visually to "
        "the driver."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class ScanningOutVisualIndicator(TestStep):
    """Example test step"""

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

        scanning_phase_tr = None
        self.result.measured_resul = None
        db_time_passed_tr = None

        signal_df = pd.DataFrame(
            data={
                "hmi_info": signals[ValidationSignals.Columns.HMI_INFO],
                "general_screen": signals[ValidationSignals.Columns.GENERAL_SCREEN],
            },
            index=time,
        )

        scanning_frames_df = signal_df[
            signal_df["hmi_info"] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_OUT
        ]

        if len(scanning_frames_df):
            scanning_phase_tr = 1
            debounce_time_passed = 0
            for ts in scanning_frames_df.index:
                if debounce_time_passed < constants.HilCl.Hmi.GeneralScreenReactionTime.VISUAL_INDICATOR_REACTION_TIME:
                    debounce_time_passed = ts - scanning_frames_df.index[0]
                else:
                    db_time_passed_tr = 1
                    if scanning_frames_df["general_screen"][ts] != constants.HilCl.Hmi.APHMIGeneralScreen.PARK_OUT_SIDE:
                        self.result.measured_result = FALSE

            if self.result.measured_result is None and db_time_passed_tr:
                self.result.measured_result = TRUE

        if scanning_phase_tr is None:
            evaluation = " ".join(
                f"{signals_obj._properties[ValidationSignals.Columns.HMI_INFO]} did not took value "
                f"{constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_OUT}.".split()
            )
            signal_summary["Scanning out visual message"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
            self.result.measured_result = FALSE
        elif db_time_passed_tr is None:
            evaluation = " ".join(
                f"Debounce time "
                f"({constants.HilCl.Hmi.GeneralScreenReactionTime.VISUAL_INDICATOR_REACTION_TIME} "
                f"[us]) did not passed in order to evaluate.".split()
            )
            signal_summary["Scanning out visual message"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
            self.result.measured_result = FALSE
        elif self.result.measured_result == FALSE:
            evaluation = " ".join(
                f"{signals_obj._properties[ValidationSignals.Columns.GENERAL_SCREEN]} did not took value "
                f"{constants.HilCl.Hmi.APHMIGeneralScreen.PARK_OUT_SIDE} (PARK_OUT_SIDE) after a debounce time "
                f"({constants.HilCl.Hmi.GeneralScreenReactionTime.VISUAL_INDICATOR_REACTION_TIME} [us]) from the moment"
                f" {signals_obj._properties[ValidationSignals.Columns.HMI_INFO]} had value"
                f"{constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_OUT}.".split()
            )
            signal_summary["Scanning out visual message"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
        elif self.result.measured_result == TRUE:
            evaluation = " ".join(
                f"{signals_obj._properties[ValidationSignals.Columns.GENERAL_SCREEN]} took value "
                f"{constants.HilCl.Hmi.APHMIGeneralScreen.PARK_OUT_SIDE} "
                f"(PARK_OUT_SIDE) after a debounce time "
                f"({constants.HilCl.Hmi.GeneralScreenReactionTime.VISUAL_INDICATOR_REACTION_TIME} [us]) from the moment"
                f" {signals_obj._properties[ValidationSignals.Columns.HMI_INFO]} had value"
                f"{constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_OUT}.".split()
            )
            signal_summary["Scanning out visual message"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))

        columns_front = [
            ValidationSignals.Columns.GENERAL_SCREEN,
            ValidationSignals.Columns.HMI_INFO,
            ValidationSignals.Columns.USER_ACTION,
        ]

        fig_fr = plotter_helper(time, signals, columns_front, signals_obj._properties)
        self.result.details["Plots"].append(fig_fr.to_html(full_html=False, include_plotlyjs=False))


@testcase_definition(
    name="Scanning out visual indicator test case",
    description=(
        "When the function is searching for free parking out situations to offer, it shall indicate this visually "
        "to the driver."
    ),
)
class ScanningOutVisualIndicatorTestCase(TestCase):
    """Scanning out visual indicator test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            ScanningOutVisualIndicator,
        ]
