"""Park Distance Warning - evaluation script"""

import logging
import os
import sys

import numpy as np
import pandas as pd

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
)
from tsf.io.mdf import MDFSignalDefinition

from pl_parking.common_ft_helper import MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.PDW.pdw_helper import plotter_helper

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "PDW_ACTIVATION_BY_R_GEAR"


class ValidationSignals(MDFSignalDefinition):
    """Example signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        VEH_VELOCITY = "Vehicle_velocity"
        TIME = "Time"
        GEAR_MAN = "Gear_man"
        GEAR_AUT = "Gear_auto"
        PDW_CAN_STATE = "PDW_State"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.TIME: "Time",
            self.Columns.VEH_VELOCITY: "MTS.ADAS_CAN.Conti_Veh_CAN.VehVelocity.VehVelocityExt",
            self.Columns.GEAR_MAN: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActualGear",
            self.Columns.GEAR_AUT: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActGearPos",
            self.Columns.PDW_CAN_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.PDCInfo.PDCSystemState",
        }


signals_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="PDW activation by R gear, manual transmission",
    description=(
        "If the R-gear is engaged in case of manual transmission and a debounce time has passed, the PDW function"
        " shall become active."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwActivationbyRGearManualTransmission(TestStep):
    """Test step to evaluate if PDW function is activated by R gear."""

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

        data = pd.DataFrame(
            data={
                "man_gear": signals[ValidationSignals.Columns.GEAR_MAN],
                "PDW_state": signals[ValidationSignals.Columns.PDW_CAN_STATE],
            },
            index=time,
        )

        man_gear_r_frames = data[data["man_gear"] == constants.HilCl.PDW.Gear.Manual.REVERSE]
        debounce_time_passed = 0

        if len(man_gear_r_frames):
            self.result.measured_result = TRUE

        for ts in man_gear_r_frames.index:
            if debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                debounce_time_passed = ts - man_gear_r_frames.index[0]
            else:
                if man_gear_r_frames["PDW_state"][ts] != constants.HilCl.PDW.States.ACTIVATED_BY_R_GEAR:
                    self.result.measured_result = FALSE

        if self.result.measured_result == TRUE:
            evaluation = " ".join(
                f"PASSED because PDW state signal: {signals_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} "
                f"changed his state to activated"
                f"by R gear({constants.HilCl.PDW.States.ACTIVATED_BY_R_GEAR}) after "
                f"{signals_obj._properties[ValidationSignals.Columns.GEAR_MAN]} changed to"
                f" {constants.HilCl.PDW.Gear.Manual.REVERSE} and debounce time has passed.".split()
            )
            signal_summary["PDW activation by R gear automatic"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
        if self.result.measured_result is FALSE:
            evaluation = " ".join(
                f"FAILED because PDW state signal: {signals_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} "
                f"did not change his state to activated by R gear"
                f"({signals_obj._properties[constants.HilCl.PDW.States.ACTIVATED_BY_R_GEAR]}) after reverse was "
                f"engaged and debounce time has passed.".split()
            )
            signal_summary["PDW activation by R gear manual"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
        elif self.result.measured_result is None:
            evaluation = " ".join(
                f"FAILED because Automatic gear signal: {signals_obj._properties[ValidationSignals.Columns.GEAR_MAN]} "
                f"did not change his state to {constants.HilCl.PDW.Gear.Manual.REVERSE}".split()
            )
            signal_summary["PDW activation by R gear automatic"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE

        columns = [
            ValidationSignals.Columns.GEAR_MAN,
            ValidationSignals.Columns.PDW_CAN_STATE,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Signals used in evaluation")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))


@testcase_definition(
    name="PDW activation by R gear in case of manual transmission",
    description=(
        "If the R-gear is engaged in case of manual transmission and a debounce time has passed, the PDW function "
        "shall become active."
    ),
)
class PDWActivationByRGearManualTestCase(TestCase):
    """PDW function activation by R gear test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PdwActivationbyRGearManualTransmission,
        ]


@teststep_definition(
    step_number=1,
    name="PDW activation by R gear, automatic transmission",
    description=(
        "If the R-gear is engaged in case of automatic transmission and a debounce time has passed, the PDW function"
        " shall become active."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwActivationByRGearAutomaticTransmission(TestStep):
    """Test step to evaluate if PDW function is activated by R gear."""

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

        data = pd.DataFrame(
            data={
                "aut_gear": signals[ValidationSignals.Columns.GEAR_AUT],
                "PDW_state": signals[ValidationSignals.Columns.PDW_CAN_STATE],
                "Frame": np.array(range(len(time)), dtype=int),
            },
            index=time,
        )

        aut_gear_r_frames = data[data["aut_gear"] == constants.HilCl.PDW.Gear.Automatic.REVERSE]
        debounce_time_passed = 0

        if len(aut_gear_r_frames):
            self.result.measured_result = TRUE

        for ts in aut_gear_r_frames.index:
            if debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                debounce_time_passed = ts - aut_gear_r_frames.index[0]
            else:
                if aut_gear_r_frames["PDW_state"][ts] != constants.HilCl.PDW.States.ACTIVATED_BY_R_GEAR:
                    self.result.measured_result = FALSE

        if self.result.measured_result == TRUE:
            evaluation = " ".join(
                f"PASSED because PDW state signal: {signals_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} "
                f"changed his state to activated"
                f"by R gear({constants.HilCl.PDW.States.ACTIVATED_BY_R_GEAR}) after "
                f"{signals_obj._properties[ValidationSignals.Columns.GEAR_AUT]} changed to"
                f" {constants.HilCl.PDW.Gear.Automatic.REVERSE} and debounce time has passed.".split()
            )
            signal_summary["PDW activation by R gear automatic"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
        elif self.result.measured_result == FALSE:
            evaluation = " ".join(
                f"FAILED because PDW state signal: {signals_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} "
                f"did not change his state to activated"
                f"by R gear({constants.HilCl.PDW.States.ACTIVATED_BY_R_GEAR}) after reverse was engaged and "
                f"debounce time has passed.".split()
            )
            signal_summary["PDW activation by R gear automatic"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
        elif self.result.measured_result is None:
            evaluation = " ".join(
                f"FAILED because Automatic gear signal: {signals_obj._properties[ValidationSignals.Columns.GEAR_AUT]} "
                f"did not change his state to "
                f"{constants.HilCl.PDW.Gear.Automatic.REVERSE}".split()
            )
            signal_summary["PDW activation by R gear automatic"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
            self.result.measured_result = FALSE

        columns = [
            ValidationSignals.Columns.GEAR_AUT,
            ValidationSignals.Columns.PDW_CAN_STATE,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Signals used in evaluation")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))


@testcase_definition(
    name="PDW activation by R gear in case of automatic transmission",
    description=(
        "If the R-gear is engaged in case of automatic transmission and a debounce time has passed, the PDW function "
        "shall become active."
    ),
)
class PDWActivationByRGearAutomaticTestCase(TestCase):
    """PDW function activation by R gear test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PdwActivationByRGearAutomaticTransmission,
        ]
