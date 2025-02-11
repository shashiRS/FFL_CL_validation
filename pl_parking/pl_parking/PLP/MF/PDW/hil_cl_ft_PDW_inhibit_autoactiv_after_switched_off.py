"""Park Distance Warning - evaluation script"""

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
from tsf.core.testcase import TestCase, TestStep, register_signals, testcase_definition, teststep_definition, verifies
from tsf.io.mdf import MDFSignalDefinition

import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.PDW.pdw_helper import plotter_helper

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "PDW_INHIBIT_AUTOACTIVATION"


class ValidationSignals(MDFSignalDefinition):
    """Example signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        TIMESTAMP = "mts_ts"
        GEAR_MAN = "Gear_man"
        GEAR_AUT = "Gear_auto"
        PDW_CAN_STATE = "PDW_State"
        VEH_VELOCITY = "Vehicle_velocity"
        USER_ACTION = "USER_ACTION"
        IGNITION = "Veh_ignition"
        USS0_dist = "USS0_dist"
        USS1_dist = "USS1_dist"
        USS2_dist = "USS2_dist"
        USS3_dist = "USS3_dist"
        USS4_dist = "USS4_dist"
        USS5_dist = "USS5_dist"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.GEAR_MAN: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActualGear",
            self.Columns.GEAR_AUT: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActGearPos",
            self.Columns.PDW_CAN_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.PDCInfo.PDCSystemState",
            self.Columns.VEH_VELOCITY: "MTS.ADAS_CAN.Conti_Veh_CAN.VehVelocity.VehVelocityExt",
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.USS0_dist: "CM.Sensor.Object.USS00.relvTgt.NearPnt.ds_p",
            self.Columns.USS1_dist: "CM.Sensor.Object.USS01.relvTgt.NearPnt.ds_p",
            self.Columns.USS2_dist: "CM.Sensor.Object.USS02.relvTgt.NearPnt.ds_p",
            self.Columns.USS3_dist: "CM.Sensor.Object.USS03.relvTgt.NearPnt.ds_p",
            self.Columns.USS4_dist: "CM.Sensor.Object.USS04.relvTgt.NearPnt.ds_p",
            self.Columns.USS5_dist: "CM.Sensor.Object.USS05.relvTgt.NearPnt.ds_p",
        }


example_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="PDW inhibit auto-activation after it was switched off by the driver",
    description=(
        "If automatic activation is switched off by the driver via infotainment setting screen"
        " (by removing a check mark), the PDW function shall inhibit automatic activation."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwInhibitAutoactivAfterSwitchedOff(TestStep):
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
        ig_on_tr = 0
        driver_deactivation_st = 0
        driver_deactivation_end = 0
        det_trigger = 0
        autoactiv_true_vf_deactiv = 0
        self.result.measured_result = None
        signal_df = pd.DataFrame(
            data={
                "pdw_state": signals[ValidationSignals.Columns.PDW_CAN_STATE],
                "user_action": signals[ValidationSignals.Columns.USER_ACTION],
                "ignition": signals[ValidationSignals.Columns.IGNITION],
                "dist_to_obj_uss0": signals[ValidationSignals.Columns.USS0_dist],
                "dist_to_obj_uss1": signals[ValidationSignals.Columns.USS1_dist],
                "dist_to_obj_uss2": signals[ValidationSignals.Columns.USS2_dist],
                "dist_to_obj_uss3": signals[ValidationSignals.Columns.USS3_dist],
                "dist_to_obj_uss4": signals[ValidationSignals.Columns.USS4_dist],
                "dist_to_obj_uss5": signals[ValidationSignals.Columns.USS5_dist],
            },
            index=time,
        )

        ignition_on = signal_df[signal_df["ignition"] == constants.HilCl.CarMaker.IGNITION_ON]
        driver_deactivation_end_ts = None
        debounce_time_passed = 0
        if len(ignition_on):
            ig_on_tr = 1
            for ts in ignition_on.index:
                if not autoactiv_true_vf_deactiv:
                    if (
                        (
                            (
                                ignition_on["dist_to_obj_uss0"][ts]
                                > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
                            )
                            & (
                                ignition_on["dist_to_obj_uss0"][ts]
                                < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
                            )
                        )
                        | (
                            (
                                ignition_on["dist_to_obj_uss1"][ts]
                                > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
                            )
                            & (
                                ignition_on["dist_to_obj_uss1"][ts]
                                < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
                            )
                        )
                        | (
                            (
                                ignition_on["dist_to_obj_uss2"][ts]
                                > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
                            )
                            & (
                                ignition_on["dist_to_obj_uss2"][ts]
                                < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
                            )
                        )
                        | (
                            (
                                ignition_on["dist_to_obj_uss3"][ts]
                                > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
                            )
                            & (
                                ignition_on["dist_to_obj_uss3"][ts]
                                < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
                            )
                        )
                        | (
                            (
                                ignition_on["dist_to_obj_uss4"][ts]
                                > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
                            )
                            & (
                                ignition_on["dist_to_obj_uss4"][ts]
                                < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
                            )
                        )
                        | (
                            (
                                ignition_on["dist_to_obj_uss5"][ts]
                                > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
                            )
                            & (
                                ignition_on["dist_to_obj_uss5"][ts]
                                < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
                            )
                        )
                    ):
                        if ignition_on["pdw_state"][ts] == constants.HilCl.PDW.States.AUTOMATICALLY_ACTIVATED:
                            autoactiv_true_vf_deactiv = 1
                else:
                    if (
                        ignition_on["user_action"][ts] == constants.HilCl.PDW.Button.PDW_AUTOACT_TAP_ON
                        and driver_deactivation_st == 0
                    ):
                        driver_deactivation_st = 1

                    if driver_deactivation_st:
                        if ignition_on["user_action"][ts] == 0 and driver_deactivation_end == 0:
                            driver_deactivation_end = 1
                            driver_deactivation_end_ts = ts

                    if driver_deactivation_end:

                        if debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                            debounce_time_passed = ts - driver_deactivation_end_ts

                        else:
                            if (
                                (
                                    (
                                        ignition_on["dist_to_obj_uss0"][ts]
                                        > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
                                    )
                                    & (
                                        ignition_on["dist_to_obj_uss0"][ts]
                                        < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
                                    )
                                )
                                | (
                                    (
                                        ignition_on["dist_to_obj_uss1"][ts]
                                        > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
                                    )
                                    & (
                                        ignition_on["dist_to_obj_uss1"][ts]
                                        < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
                                    )
                                )
                                | (
                                    (
                                        ignition_on["dist_to_obj_uss2"][ts]
                                        > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
                                    )
                                    & (
                                        ignition_on["dist_to_obj_uss2"][ts]
                                        < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
                                    )
                                )
                                | (
                                    (
                                        ignition_on["dist_to_obj_uss3"][ts]
                                        > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
                                    )
                                    & (
                                        ignition_on["dist_to_obj_uss3"][ts]
                                        < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
                                    )
                                )
                                | (
                                    (
                                        ignition_on["dist_to_obj_uss4"][ts]
                                        > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
                                    )
                                    & (
                                        ignition_on["dist_to_obj_uss4"][ts]
                                        < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
                                    )
                                )
                                | (
                                    (
                                        ignition_on["dist_to_obj_uss5"][ts]
                                        > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
                                    )
                                    & (
                                        ignition_on["dist_to_obj_uss5"][ts]
                                        < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
                                    )
                                )
                            ):
                                det_trigger = 1
                                if ignition_on["pdw_state"][ts] == constants.HilCl.PDW.States.AUTOMATICALLY_ACTIVATED:
                                    self.result.measured_result = FALSE

        if det_trigger and self.result.measured_result is None:
            self.result.measured_result = TRUE

        if ig_on_tr == 0:
            evaluation = " ".join(
                f"{example_obj._properties[ValidationSignals.Columns.IGNITION]} did not take "
                f"value of {constants.HilCl.CarMaker.IGNITION_ON}.".split()
            )
            signal_summary["PDW inhibit autoactivation"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif autoactiv_true_vf_deactiv == 0:
            evaluation = " ".join(
                "Auto-activation did not worked before driver disabled auto-activation."
                f"{example_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} did not change his state to "
                f"{constants.HilCl.PDW.States.AUTOMATICALLY_ACTIVATED} before auto-activation was switched off".split()
            )
            signal_summary["PDW inhibit autoactivation"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif driver_deactivation_st == 0:
            evaluation = " ".join(
                "Driver did not pressed the button to disable autoactivation."
                f"{example_obj._properties[ValidationSignals.Columns.USER_ACTION]} did not take "
                f"value {constants.HilCl.PDW.Button.PDW_AUTOACT_TAP_ON}".split()
            )
            signal_summary["PDW inhibit autoactivation"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif driver_deactivation_end == 0:
            evaluation = " ".join(
                "Driver did not released the button to disable autoactivation."
                f"{example_obj._properties[ValidationSignals.Columns.USER_ACTION]} did not went back to "
                f"value {constants.HilCl.CarMaker.IGNITION_OFF}".split()
            )
            signal_summary["PDW inhibit autoactivation"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif self.result.measured_result == FALSE:
            evaluation = " ".join(
                f"{example_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} went to auto-activated state "
                f"{constants.HilCl.PDW.States.AUTOMATICALLY_ACTIVATED}".split()
            )
            signal_summary["PDW inhibit autoactivation"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
        elif self.result.measured_result == TRUE:
            evaluation = " ".join(
                "PDW did not auto-activated."
                f"{example_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} did not change his state to "
                f"{constants.HilCl.PDW.States.AUTOMATICALLY_ACTIVATED} after auto-activation was switched off".split()
            )
            signal_summary["PDW inhibit autoactivation"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )

        plot_signals = [
            ValidationSignals.Columns.PDW_CAN_STATE,
            ValidationSignals.Columns.USER_ACTION,
            ValidationSignals.Columns.IGNITION,
        ]

        fig_fr = plotter_helper(time, signals, plot_signals, example_obj._properties)
        fig_fr.update_layout(title="State and user action signals")
        self.result.details["Plot_titles"].append("State and user action signals")
        self.result.details["Plots"].append(fig_fr.to_html(full_html=False, include_plotlyjs=False))

        columns_plot_dist = [
            ValidationSignals.Columns.USS0_dist,
            ValidationSignals.Columns.USS1_dist,
            ValidationSignals.Columns.USS2_dist,
            ValidationSignals.Columns.USS3_dist,
            ValidationSignals.Columns.USS4_dist,
            ValidationSignals.Columns.USS5_dist,
        ]
        fig_dist = plotter_helper(time, signals, columns_plot_dist, example_obj._properties)
        fig_dist.update_layout(title="Distance to object signals [m]")
        self.result.details["Plot_titles"].append("Distance to object signals")
        self.result.details["Plots"].append(fig_dist.to_html(full_html=False, include_plotlyjs=False))


@verifies(
    requirement="1902588",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_5ajNEcsZEe6xJ6AFScj__Q?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@testcase_definition(
    name="PDW inhibit auto-activation after it was switched off by the driver",
    description="If automatic activation is switched off by the driver via infotainment setting screen"
    " (by removing a check mark), the PDW function shall inhibit automatic activation.",
)
class PDWInhibitAutoactivAfterSwitchedOffTestCase(TestCase):
    """PDW function deactivation by open trunk test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PdwInhibitAutoactivAfterSwitchedOff,
        ]
