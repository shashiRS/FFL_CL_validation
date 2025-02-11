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

SIGNAL_DATA = "PDW_DEACTIVATION_BY_OPEN_LID"


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

        FRONT_SPEAKER = "FRONT_SPEAKER"
        FRONT_SPEAKER_VOLUME = "FRONT_SPEAKER_VOLUME"
        FRONT_SPEAKER_PITCH = "FRONT_SPEAKER_PITCH"

        REAR_SPEAKER = "REAR_SPEAKER"
        REAR_SPEAKER_VOLUME = "REAR_SPEAKER_VOLUME"
        REAR_SPEAKER_PITCH = "REAR_SPEAKER_PITCH"

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
            self.Columns.FRONT_SPEAKER: "MTS.AP_Private_CAN.AP_Private_CAN.TONHInfo.FrontSpeakerOn",
            self.Columns.FRONT_SPEAKER_VOLUME: "MTS.AP_Private_CAN.AP_Private_CAN.TONHInfo.FrontSpeakerVolume",
            self.Columns.FRONT_SPEAKER_PITCH: "MTS.AP_Private_CAN.AP_Private_CAN.TONHInfo.FrontSpeakerPitch",
            self.Columns.REAR_SPEAKER: "MTS.AP_Private_CAN.AP_Private_CAN.TONHInfo.RearSpeakerOn",
            self.Columns.REAR_SPEAKER_VOLUME: "MTS.AP_Private_CAN.AP_Private_CAN.TONHInfo.RearSpeakerVolume",
            self.Columns.REAR_SPEAKER_PITCH: "MTS.AP_Private_CAN.AP_Private_CAN.TONHInfo.RearSpeakerPitch",
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
    name="PDW deactivation by open lid",
    description="The PDW function shall deactivate the warning for the front side when the lid is open.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwDeactivationByOpenLid(TestStep):
    """Test step to evaluate if PDW function is deactivating when lid is open."""

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
                "front_speaker": signals[ValidationSignals.Columns.FRONT_SPEAKER],
                "front_speaker_vol": signals[ValidationSignals.Columns.FRONT_SPEAKER_VOLUME],
                "front_speaker_pitch": signals[ValidationSignals.Columns.FRONT_SPEAKER_PITCH],
                "rear_speaker": signals[ValidationSignals.Columns.REAR_SPEAKER],
                "rear_speaker_vol": signals[ValidationSignals.Columns.REAR_SPEAKER_VOLUME],
                "rear_speaker_pitch": signals[ValidationSignals.Columns.REAR_SPEAKER_PITCH],
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
                "open_lid": signals[ValidationSignals.Columns.OPEN_DOORS],
                "shifted_open_lid": signals[ValidationSignals.Columns.OPEN_DOORS].shift(-1),
            },
            index=time,
        )
        # filter for frames were we have an obj detected in front and other object detected in rear
        obj_dist_true = signal_df[
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
        if len(obj_dist_true):
            trigger0 = 1
            # search the last frame where open lid signal had value 0
            values_last_ts_closed_lid = signal_df[
                (signal_df["open_lid"] == constants.HilCl.DoorOpen.DOORS_CLOSED)
                & (signal_df["shifted_open_lid"] == constants.HilCl.DoorOpen.ENGINE_HOOD_OPEN)
            ]
            last_ts_closed_lid = values_last_ts_closed_lid.index[0]

            # filter for frames where we have an object detected by input signals and hood is opened
            open_lid_frames = obj_dist_true[obj_dist_true["open_lid"] == constants.HilCl.DoorOpen.ENGINE_HOOD_OPEN]
            if (
                (
                    values_last_ts_closed_lid["smallest_crit_fr_1"][last_ts_closed_lid] != 0
                    or values_last_ts_closed_lid["smallest_crit_fr_2"][last_ts_closed_lid] != 0
                    or values_last_ts_closed_lid["smallest_crit_fr_3"][last_ts_closed_lid] != 0
                    or values_last_ts_closed_lid["smallest_crit_fr_4"][last_ts_closed_lid] != 0
                    or values_last_ts_closed_lid["smallest_crit_le_1"][last_ts_closed_lid] != 0
                    or values_last_ts_closed_lid["smallest_crit_le_2"][last_ts_closed_lid] != 0
                    or values_last_ts_closed_lid["smallest_crit_ri_1"][last_ts_closed_lid] != 0
                    or values_last_ts_closed_lid["smallest_crit_ri_2"][last_ts_closed_lid] != 0
                )
                and (
                    values_last_ts_closed_lid["smallest_crit_re_1"][last_ts_closed_lid] != 0
                    or values_last_ts_closed_lid["smallest_crit_re_2"][last_ts_closed_lid] != 0
                    or values_last_ts_closed_lid["smallest_crit_re_3"][last_ts_closed_lid] != 0
                    or values_last_ts_closed_lid["smallest_crit_re_4"][last_ts_closed_lid] != 0
                    or values_last_ts_closed_lid["smallest_crit_le_3"][last_ts_closed_lid] != 0
                    or values_last_ts_closed_lid["smallest_crit_le_4"][last_ts_closed_lid] != 0
                    or values_last_ts_closed_lid["smallest_crit_ri_3"][last_ts_closed_lid] != 0
                    or values_last_ts_closed_lid["smallest_crit_ri_4"][last_ts_closed_lid] != 0
                )
                and (
                    values_last_ts_closed_lid["front_speaker"][last_ts_closed_lid] != 0
                    and values_last_ts_closed_lid["front_speaker_vol"][last_ts_closed_lid] != 0
                    and values_last_ts_closed_lid["front_speaker_pitch"][last_ts_closed_lid] != 0
                )
                and (
                    values_last_ts_closed_lid["rear_speaker"][last_ts_closed_lid] != 0
                    and values_last_ts_closed_lid["rear_speaker_vol"][last_ts_closed_lid] != 0
                    and values_last_ts_closed_lid["rear_speaker_pitch"][last_ts_closed_lid] != 0
                )
            ):
                trigger1 = True
                debounce_time_passed = 0
                for ts in open_lid_frames.index:
                    if trigger2 is None:
                        trigger2 = True
                        self.result.measured_result = TRUE
                    if debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                        debounce_time_passed = ts - open_lid_frames.index[0]
                    else:
                        if (
                            open_lid_frames["smallest_crit_fr_1"][ts] != 0
                            or open_lid_frames["smallest_crit_fr_2"][ts] != 0
                            or open_lid_frames["smallest_crit_fr_3"][ts] != 0
                            or open_lid_frames["smallest_crit_fr_4"][ts] != 0
                            or open_lid_frames["smallest_crit_le_1"][ts] != 0
                            or open_lid_frames["smallest_crit_le_2"][ts] != 0
                            or open_lid_frames["smallest_crit_ri_1"][ts] != 0
                            or open_lid_frames["smallest_crit_ri_2"][ts] != 0
                            or open_lid_frames["front_speaker"][ts] != 0
                            or open_lid_frames["front_speaker_vol"][ts] != 0
                            or open_lid_frames["front_speaker_pitch"][ts] != 0
                        ) or (
                            open_lid_frames["smallest_crit_re_1"][ts] == 0
                            and open_lid_frames["smallest_crit_re_2"][ts] == 0
                            and open_lid_frames["smallest_crit_re_3"][ts] == 0
                            and open_lid_frames["smallest_crit_re_4"][ts] == 0
                            and open_lid_frames["smallest_crit_le_3"][ts] == 0
                            and open_lid_frames["smallest_crit_le_4"][ts] == 0
                            and open_lid_frames["smallest_crit_ri_3"][ts] == 0
                            and open_lid_frames["smallest_crit_ri_4"][ts] == 0
                            and open_lid_frames["rear_speaker"][ts] == 0
                            and open_lid_frames["rear_speaker_vol"][ts] == 0
                            and open_lid_frames["rear_speaker_pitch"][ts] == 0
                        ):
                            self.result.measured_result = FALSE
        if trigger0 is None:
            evaluation = " ".join("Object was not detected in order to check PDW reaction when hood is opened.".split())
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
            self.result.measured_result = FALSE
        elif trigger1 is None:
            evaluation = " ".join("Warning signals did not work when lid was closed neither.".split())
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
            self.result.measured_result = FALSE
        elif trigger2 is None:
            evaluation = " ".join(
                f"{signals_obj._properties[ValidationSignals.Columns.OPEN_DOORS]} did not take "
                f"{constants.HilCl.DoorOpen.ENGINE_HOOD_OPEN} value in order to evaluate PDW reaction.".split()
            )
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
            self.result.measured_result = FALSE
        elif self.result.measured_result == FALSE:
            evaluation = " ".join(
                "FAILED because one of the following signals: "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR1]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR2]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR3]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR4]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE1]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE2]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI1]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI2]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.FRONT_SPEAKER]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.FRONT_SPEAKER_VOLUME]} , <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.FRONT_SPEAKER_PITCH]} is != 0, PDW detected front "
                f"objects with hood "
                f"opened ({signals_obj._properties[ValidationSignals.Columns.OPEN_DOORS]} took value "
                f"{constants.HilCl.DoorOpen.ENGINE_HOOD_OPEN}) OR detection stopped on a rear sector after "
                f"hood was opened.".split()
            )
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
        elif self.result.measured_result == TRUE:
            evaluation = " ".join(
                "PASSED because all the following signals: "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR1]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR2]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR3]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR4]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE1]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE2]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI1]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI2]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.FRONT_SPEAKER]}, <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.FRONT_SPEAKER_VOLUME]} , <br> "
                f"{signals_obj._properties[ValidationSignals.Columns.FRONT_SPEAKER_PITCH]} are == 0, PDW detected front"
                f" objects with hood "
                f"opened ({signals_obj._properties[ValidationSignals.Columns.OPEN_DOORS]} took value "
                f"{constants.HilCl.DoorOpen.ENGINE_HOOD_OPEN})".split()
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
            ValidationSignals.Columns.FRONT_SPEAKER,
            ValidationSignals.Columns.FRONT_SPEAKER_VOLUME,
            ValidationSignals.Columns.FRONT_SPEAKER_PITCH,
            ValidationSignals.Columns.OPEN_DOORS,
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
            ValidationSignals.Columns.FRONT_SPEAKER,
            ValidationSignals.Columns.FRONT_SPEAKER_VOLUME,
            ValidationSignals.Columns.FRONT_SPEAKER_PITCH,
            ValidationSignals.Columns.OPEN_DOORS,
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
    name="PDW deactivation by open lid",
    description="The PDW function shall deactivate the warning for the front side when the lid is open.",
)
class PDWDeactivationByOpenLidTestCase(TestCase):
    """PDW function deactivation by open lid test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PdwDeactivationByOpenLid,
        ]


@teststep_definition(
    step_number=1,
    name="PDW deactivation by open trunk",
    description="The PDW function shall deactivate the warnings for the rear side when the trunk is open.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwDeactivationByOpenTrunk(TestStep):
    """Test step to evaluate if PDW function is deactivating when trunk is open."""

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
        time = signals.index.tolist()
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
                "front_speaker": signals[ValidationSignals.Columns.FRONT_SPEAKER],
                "front_speaker_vol": signals[ValidationSignals.Columns.FRONT_SPEAKER_VOLUME],
                "front_speaker_pitch": signals[ValidationSignals.Columns.FRONT_SPEAKER_PITCH],
                "rear_speaker": signals[ValidationSignals.Columns.REAR_SPEAKER],
                "rear_speaker_vol": signals[ValidationSignals.Columns.REAR_SPEAKER_VOLUME],
                "rear_speaker_pitch": signals[ValidationSignals.Columns.REAR_SPEAKER_PITCH],
                "open_trunk": signals[ValidationSignals.Columns.OPEN_DOORS],
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
                "shifted_open_trunk": signals[ValidationSignals.Columns.OPEN_DOORS].shift(-1),
            },
            index=time,
        )
        # filter for frames were we have an obj detected
        obj_dist_true = signal_df[
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
        if len(obj_dist_true):
            trigger0 = 1
            # search the last frame where open trunk signal had value 0
            values_last_ts_closed_trunk = signal_df[
                (signal_df["open_trunk"] == constants.HilCl.DoorOpen.DOORS_CLOSED)
                & (signal_df["shifted_open_trunk"] == constants.HilCl.DoorOpen.TRUNK_OPEN)
            ]
            last_ts_closed_trunk = values_last_ts_closed_trunk.index[0]
            open_trunk_frames = obj_dist_true[obj_dist_true["open_trunk"] == constants.HilCl.DoorOpen.TRUNK_OPEN]
            if (
                (
                    values_last_ts_closed_trunk["smallest_crit_re_1"][last_ts_closed_trunk] != 0
                    or values_last_ts_closed_trunk["smallest_crit_re_2"][last_ts_closed_trunk] != 0
                    or values_last_ts_closed_trunk["smallest_crit_re_3"][last_ts_closed_trunk] != 0
                    or values_last_ts_closed_trunk["smallest_crit_re_4"][last_ts_closed_trunk] != 0
                    or values_last_ts_closed_trunk["smallest_crit_ri_3"][last_ts_closed_trunk] != 0
                    or values_last_ts_closed_trunk["smallest_crit_ri_4"][last_ts_closed_trunk] != 0
                    or values_last_ts_closed_trunk["smallest_crit_le_3"][last_ts_closed_trunk] != 0
                    or values_last_ts_closed_trunk["smallest_crit_le_4"][last_ts_closed_trunk] != 0
                )
                and (
                    values_last_ts_closed_trunk["smallest_crit_fr_1"][last_ts_closed_trunk] != 0
                    or values_last_ts_closed_trunk["smallest_crit_fr_2"][last_ts_closed_trunk] != 0
                    or values_last_ts_closed_trunk["smallest_crit_fr_3"][last_ts_closed_trunk] != 0
                    or values_last_ts_closed_trunk["smallest_crit_fr_4"][last_ts_closed_trunk] != 0
                    or values_last_ts_closed_trunk["smallest_crit_ri_1"][last_ts_closed_trunk] != 0
                    or values_last_ts_closed_trunk["smallest_crit_ri_2"][last_ts_closed_trunk] != 0
                    or values_last_ts_closed_trunk["smallest_crit_le_1"][last_ts_closed_trunk] != 0
                    or values_last_ts_closed_trunk["smallest_crit_le_2"][last_ts_closed_trunk] != 0
                )
                and (
                    values_last_ts_closed_trunk["rear_speaker"][last_ts_closed_trunk] != 0
                    and values_last_ts_closed_trunk["rear_speaker_vol"][last_ts_closed_trunk] != 0
                    and values_last_ts_closed_trunk["rear_speaker_pitch"][last_ts_closed_trunk] != 0
                )
                and (
                    values_last_ts_closed_trunk["front_speaker"][last_ts_closed_trunk] != 0
                    and values_last_ts_closed_trunk["front_speaker_vol"][last_ts_closed_trunk] != 0
                    and values_last_ts_closed_trunk["front_speaker_pitch"][last_ts_closed_trunk] != 0
                )
            ):
                trigger1 = True
                debounce_time_passed = 0
                for ts in open_trunk_frames.index:
                    if trigger2 is None:
                        trigger2 = True
                        self.result.measured_result = TRUE
                    if debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                        debounce_time_passed = ts - open_trunk_frames.index[0]
                    else:

                        if (
                            open_trunk_frames["smallest_crit_re_1"][ts] != 0
                            or open_trunk_frames["smallest_crit_re_2"][ts] != 0
                            or open_trunk_frames["smallest_crit_re_3"][ts] != 0
                            or open_trunk_frames["smallest_crit_re_4"][ts] != 0
                            or open_trunk_frames["smallest_crit_le_3"][ts] != 0
                            or open_trunk_frames["smallest_crit_le_4"][ts] != 0
                            or open_trunk_frames["smallest_crit_ri_3"][ts] != 0
                            or open_trunk_frames["smallest_crit_ri_4"][ts] != 0
                            or open_trunk_frames["rear_speaker"][ts] != 0
                            or open_trunk_frames["rear_speaker_vol"][ts] != 0
                            or open_trunk_frames["rear_speaker_pitch"][ts] != 0
                        ) or (
                            open_trunk_frames["smallest_crit_fr_1"][ts] == 0
                            and open_trunk_frames["smallest_crit_fr_2"][ts] == 0
                            and open_trunk_frames["smallest_crit_fr_3"][ts] == 0
                            and open_trunk_frames["smallest_crit_fr_4"][ts] == 0
                            and open_trunk_frames["smallest_crit_le_1"][ts] == 0
                            and open_trunk_frames["smallest_crit_le_2"][ts] == 0
                            and open_trunk_frames["smallest_crit_ri_1"][ts] == 0
                            and open_trunk_frames["smallest_crit_ri_2"][ts] == 0
                            and open_trunk_frames["front_speaker"][ts] == 0
                            and open_trunk_frames["front_speaker_vol"][ts] == 0
                            and open_trunk_frames["front_speaker_pitch"][ts] == 0
                        ):
                            self.result.measured_result = FALSE

        if trigger0 is None:
            evaluation = " ".join(
                "Object was not detected in order to check PDW reaction when trunk is opened.".split()
            )
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
            self.result.measured_result = FALSE
        elif trigger1 is None:
            evaluation = " ".join("Warning signals did not work when trunk was closed neither.".split())
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
            self.result.measured_result = FALSE
        elif trigger2 is None:
            evaluation = " ".join(
                f"{signals_obj._properties[ValidationSignals.Columns.OPEN_DOORS]} did not "
                f"take {constants.HilCl.DoorOpen.TRUNK_OPEN}"
                f"value in order to evaluate PDW reaction.".split()
            )
            signal_summary["PDW deactivation"] = evaluation
            self.result.details["Plots"].append(fh.convert_dict_to_pandas(signal_summary))
            self.result.measured_result = FALSE
        elif self.result.measured_result is False:
            evaluation = " ".join(
                "FAILED because one of the following signals: "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE1]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE2]}"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE3]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE4]}"
                f"{signals_obj._properties[ValidationSignals.Columns.REAR_SPEAKER]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.REAR_SPEAKER_VOLUME]}"
                f"{signals_obj._properties[ValidationSignals.Columns.REAR_SPEAKER_PITCH]} is != 0, PDW detected rear"
                f" objects with trunk "
                f"opened ({signals_obj._properties[ValidationSignals.Columns.OPEN_DOORS]} took value"
                f"{constants.HilCl.DoorOpen.TRUNK_OPEN}) OR detection stopped on a front sector after trunk was "
                f" opened.".split()
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
            ValidationSignals.Columns.FRONT_SPEAKER,
            ValidationSignals.Columns.FRONT_SPEAKER_VOLUME,
            ValidationSignals.Columns.FRONT_SPEAKER_PITCH,
            ValidationSignals.Columns.OPEN_DOORS,
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
            ValidationSignals.Columns.FRONT_SPEAKER,
            ValidationSignals.Columns.FRONT_SPEAKER_VOLUME,
            ValidationSignals.Columns.FRONT_SPEAKER_PITCH,
            ValidationSignals.Columns.OPEN_DOORS,
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
    name="PDW deactivation by open trunk",
    description="The PDW function shall deactivate the warnings for the rear side when the  trunk is open.",
)
class PDWDeactivationByOpenTrunkTestCase(TestCase):
    """PDW function deactivation by open trunk test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PdwDeactivationByOpenTrunk,
        ]
