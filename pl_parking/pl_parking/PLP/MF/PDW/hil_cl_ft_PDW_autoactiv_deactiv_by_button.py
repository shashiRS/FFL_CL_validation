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

SIGNAL_DATA = "AUTOACTIV_DEACTIVATION_BT_BUTTON"


class ValidationSignals(MDFSignalDefinition):
    """Example signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        GEAR_MAN = "Gear_man"
        GEAR_AUT = "Gear_auto"
        PDW_CAN_STATE = "PDW_State"
        USER_ACTION = "USER_ACTION"
        PDW_STANDSTILL_AUTOACTIVATION = "PDW_STANDSTILL_AUTOACTIVATION"
        IGNITION = "Veh_ignition"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.GEAR_MAN: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActualGear",
            self.Columns.GEAR_AUT: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActGearPos",
            self.Columns.PDW_CAN_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.PDCInfo.PDCSystemState",
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.PDW_STANDSTILL_AUTOACTIVATION: "MTS.MTA_ADC5.CFG_DATA.MF_DWF_APP_Parameter.PDW_L_AUTOM_ACTIV_STANDSTILL_NU",
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
        }


signals_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="PDW deactivation by button after automatic activation.",
    description=(
        "PDW shall become disabled after PDW was activated by automatic activation and the pdw button " "is pressed."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwAutoactivDeactivationByButton(TestStep):
    """Pdw automatic activation to disabled by pdw button pressed test step."""

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
        self.result.measured_result = None
        ig_on_tr = 0
        autoactivation_tr = 0
        pdw_fr_button_pressed_tr = 0
        act_by_btn_tr = 0
        pdw_sc_button_pressed_tr = 0
        pdw_sc_button_released_tr = 0
        bool_second_debounce = 0

        signal_df = pd.DataFrame(
            data={
                "pdw_state": signals[ValidationSignals.Columns.PDW_CAN_STATE],
                "user_action": signals[ValidationSignals.Columns.USER_ACTION],
                "ignition": signals[ValidationSignals.Columns.IGNITION],
                "standstill_autoactivation": signals[ValidationSignals.Columns.PDW_STANDSTILL_AUTOACTIVATION],
            },
            index=time,
        )
        ignition_on = signal_df[(signal_df["ignition"] == 1) & (signal_df["standstill_autoactivation"] == 1)]

        if len(ignition_on):
            ig_on_tr = 1
            pdw_autoactivated = ignition_on[
                ignition_on["pdw_state"] == constants.HilCl.PDW.States.AUTOMATICALLY_ACTIVATED
            ]
            if len(pdw_autoactivated):
                autoactivation_tr = 1
                button_pressed = pdw_autoactivated[
                    (pdw_autoactivated["user_action"] == constants.HilCl.PDW.Button.PDW_TAP_ON)
                ]
                if len(button_pressed):
                    last_ts_button_pressed = button_pressed.index[-1]
                    last_idx_fr_button_pressed = time.index(last_ts_button_pressed)
                    pdw_fr_button_pressed_tr = 1
                    debounce_time_passed = 0
                    for ts in ignition_on.index[last_idx_fr_button_pressed:-1]:
                        if debounce_time_passed < 600000:  # 600ms - system FTTI
                            debounce_time_passed = ts - last_ts_button_pressed
                        else:
                            if not act_by_btn_tr:
                                if ignition_on["pdw_state"][ts] == constants.HilCl.PDW.States.ACTIVATED_BY_BUTTON:
                                    act_by_btn_tr = 1
                            else:
                                if not pdw_sc_button_pressed_tr:
                                    if ignition_on["user_action"][ts] == constants.HilCl.PDW.Button.PDW_TAP_ON:
                                        pdw_sc_button_pressed_tr = 1
                                if pdw_sc_button_pressed_tr and not pdw_sc_button_released_tr:
                                    if ignition_on["user_action"][ts] == constants.HilCl.PDW.Button.NO_USER_INTERACTION:
                                        pdw_sc_button_released_tr = 1
                                        last_ts_second_button_pressed = ts
                                        second_debounce_time_passed = 0
                                if pdw_sc_button_released_tr:
                                    if (
                                        second_debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM
                                    ):  # 600ms - system FTTI
                                        second_debounce_time_passed = ts - last_ts_second_button_pressed
                                        bool_second_debounce = 1
                                    else:
                                        if ignition_on["pdw_state"][ts] != constants.HilCl.PDW.States.OFF:
                                            self.result.measured_result = FALSE

        if bool_second_debounce and self.result.measured_result is None:
            self.result.measured_result = TRUE

        if not ig_on_tr:
            evaluation = " ".join(
                f"Ignition signal {signals_obj._properties[ValidationSignals.Columns.IGNITION]} did "
                f"not took value 1 or "
                f"{signals_obj._properties[ValidationSignals.Columns.PDW_STANDSTILL_AUTOACTIVATION]} did not took "
                f"value 1.".split()
            )
            signal_summary["PDW deactivation by button"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not autoactivation_tr:
            evaluation = " ".join(
                f"PDW state signal {signals_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} did not "
                f"went to {constants.HilCl.PDW.States.AUTOMATICALLY_ACTIVATED} state in order to be disabled by "
                f"pressing the button".split()
            )
            signal_summary["PDW deactivation by button"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not pdw_fr_button_pressed_tr:
            evaluation = " ".join(
                f"PDW button was not pressed. {signals_obj._properties[ValidationSignals.Columns.USER_ACTION]} "
                f"signal did not take value {constants.HilCl.PDW.Button.PDW_TAP_ON}".split()
            )
            signal_summary["PDW deactivation by button"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not act_by_btn_tr:
            evaluation = " ".join(
                f"PDW state signal {signals_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} did not change to"
                f"{constants.HilCl.PDW.States.ACTIVATED_BY_BUTTON} state after pdw button signal"
                f"{signals_obj._properties[ValidationSignals.Columns.USER_ACTION]} took value "
                f"{constants.HilCl.PDW.States.AUTOMATICALLY_ACTIVATED} first time.".split()
            )
            signal_summary["PDW deactivation by button"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not pdw_sc_button_pressed_tr:
            evaluation = " ".join(
                f"PDW button was not pressed.{signals_obj._properties[ValidationSignals.Columns.USER_ACTION]} "
                f"signal did not take value {constants.HilCl.PDW.Button.PDW_TAP_ON} for the second time".split()
            )
            signal_summary["PDW deactivation by button"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not pdw_sc_button_released_tr:
            evaluation = " ".join(
                f"PDW button was not pressed.{signals_obj._properties[ValidationSignals.Columns.USER_ACTION]} "
                f"signal did not take value {constants.HilCl.PDW.Button.NO_USER_INTERACTION} back after button "
                f"was pressed second time".split()
            )
            signal_summary["PDW deactivation by button"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not bool_second_debounce:
            evaluation = " ".join(
                f"Scenario ended before debounce time ({constants.HilCl.PDW.FTTI.SYSTEM}) passed after the second "
                f"button pressed ({signals_obj._properties[ValidationSignals.Columns.USER_ACTION]} singal took value"
                f" {constants.HilCl.PDW.Button.PDW_TAP_ON}) in order to check if PDW change changed state "
                f"to off.".split()
            )
            signal_summary["PDW deactivation by button"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif self.result.measured_result == FALSE:
            evaluation = " ".join(
                f"PDW state signal {signals_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} "
                f"did not changed to {constants.HilCl.PDW.States.OFF} after pdw button was pressed "
                f"({signals_obj._properties[ValidationSignals.Columns.USER_ACTION]} singal took value "
                f"{constants.HilCl.PDW.Button.PDW_TAP_ON}) second time.".split()
            )
            signal_summary["PDW deactivation by button"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
        elif self.result.measured_result == TRUE:
            evaluation = " ".join(
                f"PDW state signal {signals_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} "
                f"changed to {constants.HilCl.PDW.States.OFF} after pdw button was pressed "
                f"({signals_obj._properties[ValidationSignals.Columns.USER_ACTION]} singal took value "
                f"{constants.HilCl.PDW.Button.PDW_TAP_ON}) second time.".split()
            )
            signal_summary["PDW deactivation by button"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )

        columns_front = [
            ValidationSignals.Columns.PDW_CAN_STATE,
            ValidationSignals.Columns.USER_ACTION,
            ValidationSignals.Columns.IGNITION,
            ValidationSignals.Columns.PDW_STANDSTILL_AUTOACTIVATION,
        ]

        fig_fr = plotter_helper(time, signals, columns_front, signals_obj._properties)
        fig_fr.update_layout(title="Signals used in evaluation")
        self.result.details["Plots"].append(fig_fr.to_html(full_html=False, include_plotlyjs=False))


@testcase_definition(
    name="PDW deactivation by button after automatic activation",
    description="If PDW function is active and the reason for activation was automatic activation and activation by "
    "button parameter is true and the driver press the activation/deactivation button then the PDW shall "
    "become disabled.",
)
class PDWDeactivByButtonAfterAutoactivTestCase(TestCase):
    """PDW function should be enabled by default after ignition."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PdwAutoactivDeactivationByButton,
        ]
