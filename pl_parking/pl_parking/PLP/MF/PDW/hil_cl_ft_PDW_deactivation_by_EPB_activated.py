"""Park Distance Warning - evaluation script"""

import logging
import os
import sys

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

SIGNAL_DATA = "PDW_DEACTIVATION_BY_EPB_ACT"


class ValidationSignals(MDFSignalDefinition):
    """Example signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        VEH_VELOCITY = "Vehicle_velocity"
        TIME = "Time"
        GEAR_MAN = "Gear_man"
        GEAR_AUT = "Gear_auto"
        PDW_CAN_STATE = "PDW_State"
        PARK_BRAKE = "Park_Brake"
        PARK_BRAKE_STATE = "Park_Brake_State"
        PDW_BUTTON = "PDW_Button"
        PDW_DEACTV_BY_EPB = "Deactv_by_EPB"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.TIME: "Time",
            self.Columns.VEH_VELOCITY: "MTS.ADAS_CAN.Conti_Veh_CAN.VehVelocity.VehVelocityExt",
            self.Columns.GEAR_MAN: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActualGear",
            self.Columns.GEAR_AUT: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActGearPos",
            self.Columns.PDW_CAN_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.PDCInfo.PDCSystemState",
            self.Columns.PARK_BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.ParkBrake",
            self.Columns.PARK_BRAKE_STATE: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.StateParkBrake",
            self.Columns.PDW_BUTTON: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.PDW_DEACTV_BY_EPB: "MTS.MTA_ADC5.CFG_DATA.MF_DWF_APP_Parameter.PDW_L_DEACTIV_BY_EPB_NU",
        }


signals_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="PDW disabled by EBP activation",
    description=(
        "If the PDW receives the information EPB activated and free of errors, the PDW function shall become disabled."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PDWDeactivationByEPBActivation(TestStep):
    """PDW disabled by EPB activated and free of errors."""

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
        trigger0 = 0
        trigger1 = 0
        trigger2 = 0

        data = pd.DataFrame(
            data={
                "man_gear": signals[ValidationSignals.Columns.GEAR_MAN],
                "aut_gear": signals[ValidationSignals.Columns.GEAR_AUT],
                "PDW_state": signals[ValidationSignals.Columns.PDW_CAN_STATE],
                "PDW_button": signals[ValidationSignals.Columns.PDW_BUTTON],
                "park_brake": signals[ValidationSignals.Columns.PARK_BRAKE],
                "park_brake_state": signals[ValidationSignals.Columns.PARK_BRAKE_STATE],
                "epb_param": signals[ValidationSignals.Columns.PDW_DEACTV_BY_EPB],
            },
            index=time,
        )

        epb_param_on_fr = data[data["epb_param"] == 1]
        if len(epb_param_on_fr):
            trigger0 = 1

        man_gear_r_frames = epb_param_on_fr[
            (epb_param_on_fr["man_gear"] == constants.HilCl.PDW.Gear.Manual.REVERSE)
            | (epb_param_on_fr["aut_gear"] == constants.HilCl.PDW.Gear.Automatic.REVERSE)
        ]
        if len(man_gear_r_frames):
            pdw_active_fr = man_gear_r_frames[
                man_gear_r_frames["PDW_state"] == constants.HilCl.PDW.States.ACTIVATED_BY_R_GEAR
            ]
            if len(pdw_active_fr):
                trigger1 = 1

        park_brake_frames = man_gear_r_frames[
            (man_gear_r_frames["park_brake_state"] == constants.HilCl.PDW.EPB_state.VALID)
            & (man_gear_r_frames["park_brake"] == 1)
        ]
        if len(park_brake_frames):
            trigger2 = 1

        debounce_time_passed = 0

        eval_st = None
        for ts in park_brake_frames.index:
            if debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                debounce_time_passed = ts - park_brake_frames.index[0]
            else:
                if park_brake_frames["PDW_state"][ts] != constants.HilCl.PDW.States.OFF:
                    eval_st = FALSE

        if eval_st is None and trigger0 and trigger1 and trigger2:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        if not trigger0:
            evaluation = " ".join(
                f"Deactivated by EPB was switched off: "
                f"{signals_obj._properties[ValidationSignals.Columns.PDW_DEACTV_BY_EPB]} != 1".split()
            )
            signal_summary["PDW button reactivation after deactivation by EPB"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
        if not trigger1:
            evaluation = " ".join(
                f"{signals_obj._properties[ValidationSignals.Columns.GEAR_MAN]} did not change state "
                f"to {constants.HilCl.PDW.Gear.Manual.REVERSE}"
                f" or {signals_obj._properties[ValidationSignals.Columns.GEAR_AUT]} did not change state "
                f"to {constants.HilCl.PDW.Gear.Automatic.REVERSE}"
                f"or {signals_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} did not change "
                f"state to {constants.HilCl.PDW.States.ACTIVATED_BY_R_GEAR}".split()
            )
            signal_summary["PDW button reactivation after deactivation by EPB"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
        elif not trigger2:
            evaluation = " ".join(
                f"Park brake signal: {signals_obj._properties[ValidationSignals.Columns.PARK_BRAKE]} did "
                f"not change value to 1"
                f" or Automatic gear signal: {signals_obj._properties[ValidationSignals.Columns.PARK_BRAKE_STATE]} did "
                f"not change state to {constants.HilCl.PDW.EPB_state.VALID}"
                f"after ".split()
            )
            signal_summary["PDW button reactivation after deactivation by EPB"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
        elif self.result.measured_result == FALSE:
            evaluation = " ".join(
                f"{signals_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} did not change state "
                f"to {constants.HilCl.PDW.States.OFF}"
                f"after EPB was activated".split()
            )
            signal_summary["PDW button reactivation after deactivation by EPB"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
        elif self.result.measured_result == TRUE:
            evaluation = " ".join(
                f"PASSED because PDW state signal: {signals_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} "
                f"hanged state to {constants.HilCl.PDW.States.OFF}"
                f"after EPB was activated".split()
            )
            signal_summary["PDW button reactivation after deactivation by EPB"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )

        columns = [
            ValidationSignals.Columns.GEAR_MAN,
            ValidationSignals.Columns.GEAR_AUT,
            ValidationSignals.Columns.PDW_BUTTON,
            ValidationSignals.Columns.PDW_CAN_STATE,
            ValidationSignals.Columns.PARK_BRAKE,
            ValidationSignals.Columns.PARK_BRAKE_STATE,
            ValidationSignals.Columns.PDW_DEACTV_BY_EPB,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Signals used in evaluation")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))


@testcase_definition(
    name="PDW disabled by EBP activation",
    description=(
        "If the PDW receives the information EPB activated and free of errors, the PDW function shall become disabled."
    ),
)
class PDWDeactivationByEPBActivationTC(TestCase):
    """PDW disabled by EPB activated and free of errors."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PDWDeactivationByEPBActivation,
        ]
