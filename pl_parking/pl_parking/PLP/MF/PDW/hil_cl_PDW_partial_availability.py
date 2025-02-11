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

SIGNAL_DATA = "PDW_PARTIAL_AVAILABILITY"


class ValidationSignals(MDFSignalDefinition):
    """Example signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        VEH_VELOCITY = "Vehicle_velocity"
        GEAR_MAN = "Gear_man"
        GEAR_AUT = "Gear_auto"
        PDW_CAN_STATE = "PDW_State"
        OPEN_DOORS = "Open_doors"
        SECTOR_CRITICALITYFR = "SECTOR_CRITICALITYFR{}"
        SECTOR_CRITICALITYFR1 = "SECTOR_CRITICALITYFR1"
        SECTOR_CRITICALITYFR2 = "SECTOR_CRITICALITYFR2"
        SECTOR_CRITICALITYFR3 = "SECTOR_CRITICALITYFR3"
        SECTOR_CRITICALITYFR4 = "SECTOR_CRITICALITYFR4"

        SECTOR_CRITICALITYLE = "SECTOR_CRITICALITYLE{}"
        SECTOR_CRITICALITYLE1 = "SECTOR_CRITICALITYLE1"
        SECTOR_CRITICALITYLE2 = "SECTOR_CRITICALITYLE2"
        SECTOR_CRITICALITYLE3 = "SECTOR_CRITICALITYLE3"
        SECTOR_CRITICALITYLE4 = "SECTOR_CRITICALITYLE4"

        SECTOR_CRITICALITYRE = "SECTOR_CRITICALITYRE{}"
        SECTOR_CRITICALITYRE1 = "SECTOR_CRITICALITYRE1"
        SECTOR_CRITICALITYRE2 = "SECTOR_CRITICALITYRE2"
        SECTOR_CRITICALITYRE3 = "SECTOR_CRITICALITYRE3"
        SECTOR_CRITICALITYRE4 = "SECTOR_CRITICALITYRE4"

        SECTOR_CRITICALITYRI = "SECTOR_CRITICALITYRI{}"
        SECTOR_CRITICALITYRI1 = "SECTOR_CRITICALITYRI1"
        SECTOR_CRITICALITYRI2 = "SECTOR_CRITICALITYRI2"
        SECTOR_CRITICALITYRI3 = "SECTOR_CRITICALITYRI3"
        SECTOR_CRITICALITYRI4 = "SECTOR_CRITICALITYRI4"

        DRIVING_TUBE_DISPLAY = "DRIVING_TUBE_DISPLAY"

        USS0_dist = "USS0_dist"
        USS1_dist = "USS1_dist"
        USS2_dist = "USS2_dist"
        USS3_dist = "USS3_dist"
        USS4_dist = "USS4_dist"
        USS5_dist = "USS5_dist"
        USS6_dist = "USS6_dist"
        USS7_dist = "USS7_dist"
        USS8_dist = "USS8_dist"
        USS9_dist = "USS9_dist"
        USS10_dist = "USS10_dist"
        USS11_dist = "USS11_dist"

        FRONT_BUS_DISABLE = "FRONT_BUS_DISABLE"
        REAR_BUS_DISABLE = "REAR_BUS_DISABLE"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        front_sectors_criticality = {
            self.Columns.SECTOR_CRITICALITYFR.format(
                x
            ): f"MTS.AP_Private_CAN.AP_Private_CAN.PDCFrontAndLeft.PDCFront{x}CriticalLevel"
            for x in range(1, 5)
        }
        rear_sectors_criticality = {
            self.Columns.SECTOR_CRITICALITYRE.format(
                x
            ): f"MTS.AP_Private_CAN.AP_Private_CAN.PDCRearAndRight.PDCRear{x}CriticalLevel"
            for x in range(1, 5)
        }
        left_sectors_criticality = {
            self.Columns.SECTOR_CRITICALITYLE.format(
                x
            ): f"MTS.AP_Private_CAN.AP_Private_CAN.PDCFrontAndLeft.PDCLeft{x}CriticalLevel"
            for x in range(1, 5)
        }
        right_sectors_criticality = {
            self.Columns.SECTOR_CRITICALITYRI.format(
                x
            ): f"MTS.AP_Private_CAN.AP_Private_CAN.PDCRearAndRight.PDCRight{x}CriticalLevel"
            for x in range(1, 5)
        }
        self._properties = {
            self.Columns.VEH_VELOCITY: "MTS.ADAS_CAN.Conti_Veh_CAN.VehVelocity.VehVelocityExt",
            self.Columns.GEAR_MAN: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActualGear",
            self.Columns.GEAR_AUT: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActGearPos",
            self.Columns.PDW_CAN_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.PDCInfo.PDCSystemState",
            self.Columns.OPEN_DOORS: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput01.DoorOpen",
            self.Columns.DRIVING_TUBE_DISPLAY: "MTS.AP_Private_CAN.AP_Private_CAN.PDCInfo.DrivingTubeDisplay",
            self.Columns.FRONT_BUS_DISABLE: "CM.vCUS.FTi.Bus[0].Disable",
            self.Columns.REAR_BUS_DISABLE: "CM.vCUS.FTi.Bus[1].Disable",
            self.Columns.USS0_dist: "CM.Sensor.Object.USS00.relvTgt.NearPnt.ds_p",
            self.Columns.USS1_dist: "CM.Sensor.Object.USS01.relvTgt.NearPnt.ds_p",
            self.Columns.USS2_dist: "CM.Sensor.Object.USS02.relvTgt.NearPnt.ds_p",
            self.Columns.USS3_dist: "CM.Sensor.Object.USS03.relvTgt.NearPnt.ds_p",
            self.Columns.USS4_dist: "CM.Sensor.Object.USS04.relvTgt.NearPnt.ds_p",
            self.Columns.USS5_dist: "CM.Sensor.Object.USS05.relvTgt.NearPnt.ds_p",
            self.Columns.USS6_dist: "CM.Sensor.Object.USS06.relvTgt.NearPnt.ds_p",
            self.Columns.USS7_dist: "CM.Sensor.Object.USS07.relvTgt.NearPnt.ds_p",
            self.Columns.USS8_dist: "CM.Sensor.Object.USS08.relvTgt.NearPnt.ds_p",
            self.Columns.USS9_dist: "CM.Sensor.Object.USS09.relvTgt.NearPnt.ds_p",
            self.Columns.USS10_dist: "CM.Sensor.Object.USS10.relvTgt.NearPnt.ds_p",
            self.Columns.USS11_dist: "CM.Sensor.Object.USS11.relvTgt.NearPnt.ds_p",
        }

        self._properties.update(front_sectors_criticality)
        self._properties.update(rear_sectors_criticality)
        self._properties.update(left_sectors_criticality)
        self._properties.update(right_sectors_criticality)


signals_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="PDW partial availability, disabled front",
    description=(
        "In case of partial availability, the PDW function shall display The driving tube and the sectors that are "
        "not affected."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwPartialAvailabilityFrontDisabled(TestStep):
    """Test step to evaluate if PDW partial availability."""

    custom_report = MfHilClCustomTeststepReport

    def __init__(self):
        super().__init__()

    def process(self, **kwargs):
        """Process"""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        signal_summary = {}
        signals = self.readers[SIGNAL_DATA].signals
        time = signals[ValidationSignals.Columns.TIMESTAMP]
        trigger0 = None
        trigger1 = None
        trigger2 = None
        signal_df = pd.DataFrame(
            data={
                "smallest_crit_fr_1": signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR1],
                "smallest_crit_fr_2": signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR2],
                "smallest_crit_fr_3": signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR3],
                "smallest_crit_fr_4": signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR4],
                "smallest_crit_ri_1": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRI1],
                "smallest_crit_ri_2": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRI2],
                "smallest_crit_ri_3": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRI3],
                "smallest_crit_ri_4": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRI4],
                "smallest_crit_le_1": signals[ValidationSignals.Columns.SECTOR_CRITICALITYLE1],
                "smallest_crit_le_2": signals[ValidationSignals.Columns.SECTOR_CRITICALITYLE2],
                "smallest_crit_le_3": signals[ValidationSignals.Columns.SECTOR_CRITICALITYLE3],
                "smallest_crit_le_4": signals[ValidationSignals.Columns.SECTOR_CRITICALITYLE4],
                "smallest_crit_re_1": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRE1],
                "smallest_crit_re_2": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRE2],
                "smallest_crit_re_3": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRE3],
                "smallest_crit_re_4": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRE4],
                "gear_man": signals[ValidationSignals.Columns.GEAR_MAN],
                "gear_aut": signals[ValidationSignals.Columns.GEAR_AUT],
                "dist_to_obj_uss0": signals[ValidationSignals.Columns.USS0_dist],
                "dist_to_obj_uss1": signals[ValidationSignals.Columns.USS1_dist],
                "dist_to_obj_uss2": signals[ValidationSignals.Columns.USS2_dist],
                "dist_to_obj_uss3": signals[ValidationSignals.Columns.USS3_dist],
                "dist_to_obj_uss4": signals[ValidationSignals.Columns.USS4_dist],
                "dist_to_obj_uss5": signals[ValidationSignals.Columns.USS5_dist],
                "dist_to_obj_uss6": signals[ValidationSignals.Columns.USS6_dist],
                "dist_to_obj_uss7": signals[ValidationSignals.Columns.USS7_dist],
                "dist_to_obj_uss8": signals[ValidationSignals.Columns.USS8_dist],
                "dist_to_obj_uss9": signals[ValidationSignals.Columns.USS9_dist],
                "dist_to_obj_uss10": signals[ValidationSignals.Columns.USS10_dist],
                "dist_to_obj_uss11": signals[ValidationSignals.Columns.USS11_dist],
                "driving_tube_display": signals[ValidationSignals.Columns.DRIVING_TUBE_DISPLAY],
                "front_bus_disable": signals[ValidationSignals.Columns.FRONT_BUS_DISABLE],
                "shifted_front_bus_disable": signals[ValidationSignals.Columns.FRONT_BUS_DISABLE].shift(-1),
            },
            index=time,
        )

        reverse_gear_frames = signal_df[
            (
                (signal_df["gear_man"] == constants.HilCl.PDW.Gear.Manual.REVERSE)
                | (signal_df["gear_aut"] == constants.HilCl.PDW.Gear.Automatic.REVERSE)
            )
            & (
                (
                    (signal_df["dist_to_obj_uss0"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss0"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss1"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss1"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss2"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss2"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss3"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss3"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss4"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss4"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss5"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss5"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
            )
            & (
                (
                    (signal_df["dist_to_obj_uss6"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss6"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss7"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss7"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss8"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss8"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss9"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss9"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss10"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss10"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss11"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss11"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
            )
        ]
        if len(reverse_gear_frames):

            values_last_ts_before_disabling_front = signal_df[
                (signal_df["front_bus_disable"] == 0) & (signal_df["shifted_front_bus_disable"] == -1)
            ]
            last_ts_before_disabling = values_last_ts_before_disabling_front.index[0]
            front_disabled_frames = reverse_gear_frames[reverse_gear_frames["front_bus_disable"] == -1]
            if (
                (
                    values_last_ts_before_disabling_front["smallest_crit_fr_1"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_front["smallest_crit_fr_2"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_front["smallest_crit_fr_3"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_front["smallest_crit_fr_4"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_front["smallest_crit_le_1"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_front["smallest_crit_le_2"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_front["smallest_crit_ri_1"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_front["smallest_crit_ri_2"][last_ts_before_disabling] != 0
                )
                and (
                    values_last_ts_before_disabling_front["smallest_crit_re_1"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_front["smallest_crit_re_2"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_front["smallest_crit_re_3"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_front["smallest_crit_re_4"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_front["smallest_crit_le_3"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_front["smallest_crit_le_4"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_front["smallest_crit_ri_3"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_front["smallest_crit_ri_4"][last_ts_before_disabling] != 0
                )
                and (
                    values_last_ts_before_disabling_front["driving_tube_display"][last_ts_before_disabling]
                    == constants.HilCl.PDW.DrivingTubeDisplay.BOTH
                )
            ):
                trigger1 = True
                debounce_time_passed = 0
                for ts in front_disabled_frames.index:
                    if trigger2 is None:
                        trigger2 = True
                        self.result.measured_result = TRUE
                    if debounce_time_passed < 600000:  # 600ms - system FTTI
                        debounce_time_passed = ts - front_disabled_frames.index[0]
                    else:
                        if (
                            (
                                front_disabled_frames["smallest_crit_fr_1"][ts] != 0
                                or front_disabled_frames["smallest_crit_fr_2"][ts] != 0
                                or front_disabled_frames["smallest_crit_fr_3"][ts] != 0
                                or front_disabled_frames["smallest_crit_fr_4"][ts] != 0
                                or front_disabled_frames["smallest_crit_le_1"][ts] != 0
                                or front_disabled_frames["smallest_crit_le_2"][ts] != 0
                                or front_disabled_frames["smallest_crit_ri_1"][ts] != 0
                                or front_disabled_frames["smallest_crit_ri_2"][ts] != 0
                            )
                            or (
                                front_disabled_frames["driving_tube_display"][ts]
                                != constants.HilCl.PDW.DrivingTubeDisplay.REAR
                            )
                            or (
                                front_disabled_frames["smallest_crit_re_1"][ts] == 0
                                and front_disabled_frames["smallest_crit_re_2"][ts] == 0
                                and front_disabled_frames["smallest_crit_re_3"][ts] == 0
                                and front_disabled_frames["smallest_crit_re_4"][ts] == 0
                                and front_disabled_frames["smallest_crit_le_3"][ts] == 0
                                and front_disabled_frames["smallest_crit_le_4"][ts] == 0
                                and front_disabled_frames["smallest_crit_ri_3"][ts] == 0
                                and front_disabled_frames["smallest_crit_ri_4"][ts] == 0
                            )
                        ):
                            self.result.measured_result = FALSE

        if trigger0 is None:
            evaluation = " ".join(
                f"R gear was not engaged or uss signals stayed on 0. The evaluation was failed because manual "
                f"gear signal: {signals_obj._properties[ValidationSignals.Columns.GEAR_MAN]} did not take "
                f"value {constants.HilCl.PDW.Gear.Manual.REVERSE} or automatic gear signal: "
                f"{signals_obj._properties[ValidationSignals.Columns.GEAR_AUT]} "
                f"did not take value {constants.HilCl.PDW.Gear.Automatic.REVERSE}. ".split()
            )
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
            self.result.measured_result = FALSE
        elif trigger1 is None:
            evaluation = " ".join(
                "PDW front or rear critical signals were on 0 before front sector was disabled.".split()
            )
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
            self.result.measured_result = FALSE
        elif trigger2 is None:
            evaluation = " ".join(
                f"{signals_obj._properties[ValidationSignals.Columns.FRONT_BUS_DISABLE]} did not take {-1}"
                f"value in order to evaluate PDW reaction.".split()
            )
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
            self.result.measured_result = FALSE
        elif self.result.measured_result == FALSE:
            evaluation = " ".join(
                "FAILED because one of the following signals: "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE1]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE2]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE3]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE4]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE3]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE4]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI3]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI4]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.DRIVING_TUBE_DISPLAY]} == 0, PDW did not "
                f"display sectors that were "
                "not affected in case of partial availability OR it continued to display values for "
                "affected front sector.".split()
            )
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
        elif self.result.measured_result == TRUE:
            evaluation = " ".join(
                "Passed because all the following signals: "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE1]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE2]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE3]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE4]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE3]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE4]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI3]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI4]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.DRIVING_TUBE_DISPLAY]} != 0, PDW "
                f"displayed sectors that were "
                "not affected in case of partial availability".split()
            )
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))

        columns_front = [
            ValidationSignals.Columns.SECTOR_CRITICALITYFR1,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR2,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR3,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR4,
            ValidationSignals.Columns.SECTOR_CRITICALITYLE1,
            ValidationSignals.Columns.SECTOR_CRITICALITYLE2,
            ValidationSignals.Columns.SECTOR_CRITICALITYRI1,
            ValidationSignals.Columns.SECTOR_CRITICALITYRI2,
            ValidationSignals.Columns.DRIVING_TUBE_DISPLAY,
            ValidationSignals.Columns.FRONT_BUS_DISABLE,
        ]

        fig_fr = plotter_helper(time, signals, columns_front, signals_obj._properties)
        self.result.details["Plots"].append(fig_fr.to_html(full_html=False, include_plotlyjs=False))

        columns_rear = [
            ValidationSignals.Columns.SECTOR_CRITICALITYFR1,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR2,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR3,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR4,
            ValidationSignals.Columns.SECTOR_CRITICALITYLE1,
            ValidationSignals.Columns.SECTOR_CRITICALITYLE2,
            ValidationSignals.Columns.SECTOR_CRITICALITYRI1,
            ValidationSignals.Columns.SECTOR_CRITICALITYRI2,
            ValidationSignals.Columns.DRIVING_TUBE_DISPLAY,
            ValidationSignals.Columns.FRONT_BUS_DISABLE,
        ]

        fig_re = plotter_helper(time, signals, columns_rear, signals_obj._properties)
        self.result.details["Plots"].append(fig_re.to_html(full_html=False, include_plotlyjs=False))

        columns_plot_dist = [
            ValidationSignals.Columns.USS0_dist,
            ValidationSignals.Columns.USS1_dist,
            ValidationSignals.Columns.USS2_dist,
            ValidationSignals.Columns.USS3_dist,
            ValidationSignals.Columns.USS4_dist,
            ValidationSignals.Columns.USS5_dist,
            ValidationSignals.Columns.USS6_dist,
            ValidationSignals.Columns.USS7_dist,
            ValidationSignals.Columns.USS8_dist,
            ValidationSignals.Columns.USS9_dist,
            ValidationSignals.Columns.USS10_dist,
            ValidationSignals.Columns.USS11_dist,
        ]
        fig_dist = plotter_helper(time, signals, columns_plot_dist, signals_obj._properties)
        self.result.details["Plots"].append(fig_dist.to_html(full_html=False, include_plotlyjs=False))


@teststep_definition(
    step_number=2,
    name="PDW partial availability, disabled rear",
    description=(
        "In case of partial availability, the PDW function shall display The driving tube and the sectors that are "
        "not affected."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwPartialAvailabilityRearDisabled(TestStep):
    """Test step to evaluate if PDW partial availability."""

    custom_report = MfHilClCustomTeststepReport

    def __init__(self):
        super().__init__()

    def process(self, **kwargs):
        """Process"""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        signal_summary = {}
        signals = self.readers[SIGNAL_DATA].signals
        time = signals[ValidationSignals.Columns.TIMESTAMP]
        trigger0 = None
        trigger1 = None
        trigger2 = None
        signal_df = pd.DataFrame(
            data={
                "smallest_crit_fr_1": signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR1],
                "smallest_crit_fr_2": signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR2],
                "smallest_crit_fr_3": signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR3],
                "smallest_crit_fr_4": signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR4],
                "smallest_crit_ri_1": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRI1],
                "smallest_crit_ri_2": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRI2],
                "smallest_crit_ri_3": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRI3],
                "smallest_crit_ri_4": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRI4],
                "smallest_crit_le_1": signals[ValidationSignals.Columns.SECTOR_CRITICALITYLE1],
                "smallest_crit_le_2": signals[ValidationSignals.Columns.SECTOR_CRITICALITYLE2],
                "smallest_crit_le_3": signals[ValidationSignals.Columns.SECTOR_CRITICALITYLE3],
                "smallest_crit_le_4": signals[ValidationSignals.Columns.SECTOR_CRITICALITYLE4],
                "smallest_crit_re_1": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRE1],
                "smallest_crit_re_2": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRE2],
                "smallest_crit_re_3": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRE3],
                "smallest_crit_re_4": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRE4],
                "gear_man": signals[ValidationSignals.Columns.GEAR_MAN],
                "gear_aut": signals[ValidationSignals.Columns.GEAR_AUT],
                "dist_to_obj_uss0": signals[ValidationSignals.Columns.USS0_dist],
                "dist_to_obj_uss1": signals[ValidationSignals.Columns.USS1_dist],
                "dist_to_obj_uss2": signals[ValidationSignals.Columns.USS2_dist],
                "dist_to_obj_uss3": signals[ValidationSignals.Columns.USS3_dist],
                "dist_to_obj_uss4": signals[ValidationSignals.Columns.USS4_dist],
                "dist_to_obj_uss5": signals[ValidationSignals.Columns.USS5_dist],
                "dist_to_obj_uss6": signals[ValidationSignals.Columns.USS6_dist],
                "dist_to_obj_uss7": signals[ValidationSignals.Columns.USS7_dist],
                "dist_to_obj_uss8": signals[ValidationSignals.Columns.USS8_dist],
                "dist_to_obj_uss9": signals[ValidationSignals.Columns.USS9_dist],
                "dist_to_obj_uss10": signals[ValidationSignals.Columns.USS10_dist],
                "dist_to_obj_uss11": signals[ValidationSignals.Columns.USS11_dist],
                "driving_tube_display": signals[ValidationSignals.Columns.DRIVING_TUBE_DISPLAY],
                "rear_bus_disable": signals[ValidationSignals.Columns.REAR_BUS_DISABLE],
                "shifted_rear_bus_disable": signals[ValidationSignals.Columns.REAR_BUS_DISABLE].shift(-1),
            },
            index=time,
        )

        reverse_gear_frames = signal_df[
            (
                (signal_df["gear_man"] == constants.HilCl.PDW.Gear.Manual.REVERSE)
                | (signal_df["gear_aut"] == constants.HilCl.PDW.Gear.Automatic.REVERSE)
            )
            & (
                (
                    (signal_df["dist_to_obj_uss0"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss0"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss1"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss1"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss2"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss2"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss3"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss3"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss4"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss4"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss5"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss5"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
            )
            & (
                (
                    (signal_df["dist_to_obj_uss6"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss6"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss7"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss7"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss8"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss8"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss9"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss9"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss10"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss10"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
                | (
                    (signal_df["dist_to_obj_uss11"] > constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION)
                    & (signal_df["dist_to_obj_uss11"] < constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION)
                )
            )
        ]
        if len(reverse_gear_frames):
            trigger0 = 1
            values_last_ts_before_disabling_rear = signal_df[
                (signal_df["rear_bus_disable"] == 0) & (signal_df["shifted_rear_bus_disable"] == -1)
            ]
            last_ts_before_disabling = values_last_ts_before_disabling_rear.index[0]
            rear_disabled_frames = reverse_gear_frames[reverse_gear_frames["rear_bus_disable"] == -1]
            if (
                (
                    values_last_ts_before_disabling_rear["smallest_crit_re_1"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_rear["smallest_crit_re_2"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_rear["smallest_crit_re_3"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_rear["smallest_crit_re_4"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_rear["smallest_crit_le_3"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_rear["smallest_crit_le_4"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_rear["smallest_crit_ri_3"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_rear["smallest_crit_ri_4"][last_ts_before_disabling] != 0
                )
                and (
                    values_last_ts_before_disabling_rear["smallest_crit_fr_1"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_rear["smallest_crit_fr_2"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_rear["smallest_crit_fr_3"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_rear["smallest_crit_fr_4"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_rear["smallest_crit_le_1"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_rear["smallest_crit_le_2"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_rear["smallest_crit_ri_1"][last_ts_before_disabling] != 0
                    or values_last_ts_before_disabling_rear["smallest_crit_ri_2"][last_ts_before_disabling] != 0
                )
                and (
                    values_last_ts_before_disabling_rear["driving_tube_display"][last_ts_before_disabling]
                    == constants.HilCl.PDW.DrivingTubeDisplay.BOTH
                )
            ):
                trigger1 = True
                debounce_time_passed = 0
                for ts in rear_disabled_frames.index:
                    if trigger2 is None:
                        trigger2 = True
                        self.result.measured_result = TRUE
                    if debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                        debounce_time_passed = ts - rear_disabled_frames.index[0]
                    else:
                        if (
                            (
                                rear_disabled_frames["smallest_crit_re_1"][ts] != 0
                                or rear_disabled_frames["smallest_crit_re_2"][ts] != 0
                                or rear_disabled_frames["smallest_crit_re_3"][ts] != 0
                                or rear_disabled_frames["smallest_crit_re_4"][ts] != 0
                                or rear_disabled_frames["smallest_crit_le_3"][ts] != 0
                                or rear_disabled_frames["smallest_crit_le_4"][ts] != 0
                                or rear_disabled_frames["smallest_crit_ri_3"][ts] != 0
                                or rear_disabled_frames["smallest_crit_ri_4"][ts] != 0
                            )
                            or (
                                rear_disabled_frames["driving_tube_display"][ts]
                                == constants.HilCl.PDW.DrivingTubeDisplay.FRONT
                            )
                            or (
                                rear_disabled_frames["smallest_crit_fr_1"][ts] == 0
                                and rear_disabled_frames["smallest_crit_fr_2"][ts] == 0
                                and rear_disabled_frames["smallest_crit_fr_3"][ts] == 0
                                and rear_disabled_frames["smallest_crit_fr_4"][ts] == 0
                                and rear_disabled_frames["smallest_crit_le_1"][ts] == 0
                                and rear_disabled_frames["smallest_crit_le_2"][ts] == 0
                                and rear_disabled_frames["smallest_crit_ri_1"][ts] == 0
                                and rear_disabled_frames["smallest_crit_ri_2"][ts] == 0
                            )
                        ):
                            self.result.measured_result = FALSE

        if trigger0 is None:
            evaluation = " ".join(
                f"R gear was not engaged or uss signals stayed on 0. The evaluation was failed because manual "
                f"gear signal: {signals_obj._properties[ValidationSignals.Columns.GEAR_MAN]} did not take "
                f"value {constants.HilCl.PDW.Gear.Manual.REVERSE} or automatic gear signal: "
                f"{signals_obj._properties[ValidationSignals.Columns.GEAR_AUT]} "
                f"did not take value {constants.HilCl.PDW.Gear.Automatic.REVERSE}. ".split()
            )
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
            self.result.measured_result = FALSE
        elif trigger1 is None:
            evaluation = " ".join(
                "PDW front or rear critical signals were on 0 before rear sector was disabled.".split()
            )
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
            self.result.measured_result = FALSE
        elif trigger2 is None:
            evaluation = " ".join(
                f"{signals_obj._properties[ValidationSignals.Columns.REAR_BUS_DISABLE]} did not take {-1}"
                f"value in order to evaluate PDW reaction.".split()
            )
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
        elif self.result.measured_result == FALSE:
            evaluation = " ".join(
                "Failed because of one of the following signals: "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR1]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR2]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR3]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR4]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE1]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE2]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI1]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI2]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.DRIVING_TUBE_DISPLAY]} == 0, PDW did not "
                f"display sectors that were "
                "not affected in case of partial availability OR it continued to display values for "
                "affected rear sector.".split()
            )
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
        elif self.result.measured_result == TRUE:
            evaluation = " ".join(
                "Passed because all the following signals: "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR1]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR2]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR3]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR4]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE1]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE2]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI1]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI2]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.DRIVING_TUBE_DISPLAY]} != 0, PDW "
                f"displayed sectors that were not affected in case of partial availability".split()
            )
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))

        columns_front = [
            ValidationSignals.Columns.SECTOR_CRITICALITYFR1,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR2,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR3,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR4,
            ValidationSignals.Columns.SECTOR_CRITICALITYLE1,
            ValidationSignals.Columns.SECTOR_CRITICALITYLE2,
            ValidationSignals.Columns.SECTOR_CRITICALITYRI1,
            ValidationSignals.Columns.SECTOR_CRITICALITYRI2,
            ValidationSignals.Columns.DRIVING_TUBE_DISPLAY,
            ValidationSignals.Columns.REAR_BUS_DISABLE,
        ]

        fig_fr = plotter_helper(time, signals, columns_front, signals_obj._properties)
        self.result.details["Plots"].append(fig_fr.to_html(full_html=False, include_plotlyjs=False))

        columns_rear = [
            ValidationSignals.Columns.SECTOR_CRITICALITYFR1,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR2,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR3,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR4,
            ValidationSignals.Columns.SECTOR_CRITICALITYLE1,
            ValidationSignals.Columns.SECTOR_CRITICALITYLE2,
            ValidationSignals.Columns.SECTOR_CRITICALITYRI1,
            ValidationSignals.Columns.SECTOR_CRITICALITYRI2,
            ValidationSignals.Columns.DRIVING_TUBE_DISPLAY,
            ValidationSignals.Columns.REAR_BUS_DISABLE,
        ]

        fig_re = plotter_helper(time, signals, columns_rear, signals_obj._properties)
        self.result.details["Plots"].append(fig_re.to_html(full_html=False, include_plotlyjs=False))

        columns_plot_dist = [
            ValidationSignals.Columns.USS0_dist,
            ValidationSignals.Columns.USS1_dist,
            ValidationSignals.Columns.USS2_dist,
            ValidationSignals.Columns.USS3_dist,
            ValidationSignals.Columns.USS4_dist,
            ValidationSignals.Columns.USS5_dist,
            ValidationSignals.Columns.USS6_dist,
            ValidationSignals.Columns.USS7_dist,
            ValidationSignals.Columns.USS8_dist,
            ValidationSignals.Columns.USS9_dist,
            ValidationSignals.Columns.USS10_dist,
            ValidationSignals.Columns.USS11_dist,
        ]
        fig_dist = plotter_helper(time, signals, columns_plot_dist, signals_obj._properties)
        self.result.details["Plots"].append(fig_dist.to_html(full_html=False, include_plotlyjs=False))


@testcase_definition(
    name="PDW partial availability",
    description=(
        "In case of partial availability, the PDW function shall display The driving tube and the sectors that are "
        "not affected."
    ),
)
class PDWPartialAvailabilityTestCase(TestCase):
    """PDW partial availability test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [PdwPartialAvailabilityFrontDisabled, PdwPartialAvailabilityRearDisabled]
