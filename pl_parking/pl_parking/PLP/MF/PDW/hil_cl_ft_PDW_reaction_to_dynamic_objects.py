"""Park Distance Warning - evaluation script"""

import logging
import os
import sys

import pandas as pd
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import TestCase, TestStep, register_signals, testcase_definition, teststep_definition, verifies
from tsf.io.mdf import MDFSignalDefinition

import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.PDW.pdw_helper import plotter_helper

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))

if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)


TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "PDW_REACTION_DYNAMIC_OBJECTS"


class ValidationSignals(MDFSignalDefinition):
    """Example signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        VEH_VELOCITY = "Vehicle_velocity"
        TIME = "Time"
        GEAR_MAN = "Gear_man"
        GEAR_AUT = "Gear_auto"
        PDW_CAN_STATE = "PDW_State"
        TRAFFIC_PARTICIPANT0_VEL = "TRAFFIC_PARTICIPANT0_VEL"
        TRAFFIC_PARTICIPANT1_VEL = "TRAFFIC_PARTICIPANT1_VEL"
        TRAFFIC_PARTICIPANT2_VEL = "TRAFFIC_PARTICIPANT2_VEL"

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

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = [
            "PDW_Signals",
        ]

        self._properties = {
            self.Columns.TIME: "Time",
            self.Columns.VEH_VELOCITY: "MTS.ADAS_CAN.Conti_Veh_CAN.VehVelocity.VehVelocityExt",
            self.Columns.GEAR_MAN: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActualGear",
            self.Columns.GEAR_AUT: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActGearPos",
            self.Columns.TRAFFIC_PARTICIPANT0_VEL: "CM.Traffic.T00.LongVel",
            self.Columns.TRAFFIC_PARTICIPANT1_VEL: "CM.Traffic.T00_1.LongVel",
            self.Columns.TRAFFIC_PARTICIPANT2_VEL: "CM.Traffic.T00_2.LongVel",
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
        front_sectors_criticality = {
            self.Columns.SECTOR_CRITICALITYFR.format(
                x
            ): f"MTS.AP_Private_CAN.AP_Private_CAN.PDCFrontAndLeft.PDCFront{x}CriticalLevel"
            for x in range(1, 5)
        }
        left_sectors_criticality = {
            self.Columns.SECTOR_CRITICALITYLE.format(
                x
            ): f"MTS.AP_Private_CAN.AP_Private_CAN.PDCFrontAndLeft.PDCLeft{x}CriticalLevel"
            for x in range(1, 5)
        }
        rear_sectors_criticality = {
            self.Columns.SECTOR_CRITICALITYRE.format(
                x
            ): f"MTS.AP_Private_CAN.AP_Private_CAN.PDCRearAndRight.PDCRear{x}CriticalLevel"
            for x in range(1, 5)
        }
        right_sectors_criticality = {
            self.Columns.SECTOR_CRITICALITYRI.format(
                x
            ): f"MTS.AP_Private_CAN.AP_Private_CAN.PDCRearAndRight.PDCRight{x}CriticalLevel"
            for x in range(1, 5)
        }

        self._properties.update(front_sectors_criticality)
        self._properties.update(left_sectors_criticality)
        self._properties.update(rear_sectors_criticality)
        self._properties.update(right_sectors_criticality)


signals_obj = ValidationSignals()


def uss_detect_left_sectors(signals, ts):
    """Check if uss signals detect any object in left sectors at a given timestamp."""
    uss5 = signals[ValidationSignals.Columns.USS5_dist]
    uss6 = signals[ValidationSignals.Columns.USS6_dist]
    if (constants.HilCl.PDW.SliceDistances.RED_CLOSE_L < uss5[ts] < 0.25) or (
        constants.HilCl.PDW.SliceDistances.RED_CLOSE_L < uss6[ts] < 0.25
    ):
        return 1
    else:
        return 0


def uss_detect_right_sectors(signals, ts):
    """Check if uss signals detect any object in right sectors at a given timestamp."""
    uss0 = signals[ValidationSignals.Columns.USS0_dist]
    uss11 = signals[ValidationSignals.Columns.USS11_dist]
    if (constants.HilCl.PDW.SliceDistances.RED_CLOSE_L < uss0[ts] < 0.25) or (
        constants.HilCl.PDW.SliceDistances.RED_CLOSE_L < uss11[ts] < 0.25
    ):
        return 1
    else:
        return 0


def uss_detect_front_sectors(signals, ts):
    """Check if uss signals detect any object in front sectors at a given timestamp."""
    uss1 = signals[ValidationSignals.Columns.USS1_dist]
    uss2 = signals[ValidationSignals.Columns.USS2_dist]
    uss3 = signals[ValidationSignals.Columns.USS3_dist]
    uss4 = signals[ValidationSignals.Columns.USS4_dist]

    if (
        (constants.HilCl.PDW.SliceDistances.RED_CLOSE_L < uss1[ts] < constants.HilCl.PDW.SliceDistances.GREEN_FAR_H)
        or (constants.HilCl.PDW.SliceDistances.RED_CLOSE_L < uss2[ts] < constants.HilCl.PDW.SliceDistances.GREEN_FAR_H)
        or (constants.HilCl.PDW.SliceDistances.RED_CLOSE_L < uss3[ts] < constants.HilCl.PDW.SliceDistances.GREEN_FAR_H)
        or (constants.HilCl.PDW.SliceDistances.RED_CLOSE_L < uss4[ts] < constants.HilCl.PDW.SliceDistances.GREEN_FAR_H)
    ):
        return 1
    else:
        return 0


def uss_detect_rear_sectors(signals, ts):
    """Check if uss signals detect any object in rear sectors at a given timestamp."""
    uss7 = signals[ValidationSignals.Columns.USS7_dist]
    uss8 = signals[ValidationSignals.Columns.USS8_dist]
    uss9 = signals[ValidationSignals.Columns.USS9_dist]
    uss10 = signals[ValidationSignals.Columns.USS10_dist]

    if (
        (constants.HilCl.PDW.SliceDistances.RED_CLOSE_L < uss7[ts] < constants.HilCl.PDW.SliceDistances.GREEN_FAR_H)
        or (constants.HilCl.PDW.SliceDistances.RED_CLOSE_L < uss8[ts] < constants.HilCl.PDW.SliceDistances.GREEN_FAR_H)
        or (constants.HilCl.PDW.SliceDistances.RED_CLOSE_L < uss9[ts] < constants.HilCl.PDW.SliceDistances.GREEN_FAR_H)
        or (constants.HilCl.PDW.SliceDistances.RED_CLOSE_L < uss10[ts] < constants.HilCl.PDW.SliceDistances.GREEN_FAR_H)
    ):
        return 1
    else:
        return 0


@teststep_definition(
    step_number=1,
    name="Front sectors test step",
    description=(
        "Test step is checking if PDW function is reacting on front sectors to any dynamic object as defined in "
        "req 990450 (vehicle, bicycle, pedestrian)."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwReactionToDynamicObjectsFrontSector(TestStep):
    """Test step to evaluate PDW function reaction to dynamic objects."""

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
        reverse_gear_trigger = 0
        objects_are_dynamic = 0
        object_detected = 0
        self.result.measured_result = None
        data = pd.DataFrame(
            data={
                "smallest_crit_fr_1": signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR1],
                "smallest_crit_fr_2": signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR2],
                "smallest_crit_fr_3": signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR3],
                "smallest_crit_fr_4": signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR4],
                "man_gear": signals[ValidationSignals.Columns.GEAR_MAN],
                "aut_gear": signals[ValidationSignals.Columns.GEAR_AUT],
                "traffic_participant_0_vel": signals[ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL],
            },
            index=time,
        )
        reverse_frames = data[
            (data["man_gear"] == constants.HilCl.PDW.Gear.Manual.REVERSE)
            | (data["aut_gear"] == constants.HilCl.PDW.Gear.Automatic.REVERSE)
        ]
        if len(reverse_frames):
            reverse_gear_trigger = 1
        debounce_time_passed = 0
        second_debounce_time_passed = 0
        first_ts_obj_det = 0
        for ts in reverse_frames.index:
            if debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                debounce_time_passed = ts - reverse_frames.index[0]
            else:
                if uss_detect_front_sectors(signals, ts):
                    object_detected = 1
                    if reverse_frames["traffic_participant_0_vel"][ts] != 0:
                        objects_are_dynamic = 1
                        if first_ts_obj_det == 0:
                            first_ts_obj_det = ts
                        if second_debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                            second_debounce_time_passed = ts - first_ts_obj_det
                        else:
                            if (
                                reverse_frames["smallest_crit_fr_1"][ts]
                                == constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE
                                or reverse_frames["smallest_crit_fr_2"][ts]
                                == constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE
                                or reverse_frames["smallest_crit_fr_3"][ts]
                                == constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE
                                or reverse_frames["smallest_crit_fr_4"][ts]
                                == constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE
                            ):
                                self.result.measured_result = FALSE

        if (
            reverse_gear_trigger
            and debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM
            and self.result.measured_result is None
        ):
            self.result.measured_result = TRUE

        if not reverse_gear_trigger:

            evaluation = " ".join(
                f"R gear was not engaged. The evaluation was failed because manual gear signal: "
                f"{signals_obj._properties[ValidationSignals.Columns.GEAR_MAN]} did not take "
                f"value {constants.HilCl.PDW.Gear.Manual.REVERSE} or automatic gear signal: "
                f"{signals_obj._properties[ValidationSignals.Columns.GEAR_AUT]} "
                f"did not take value {constants.HilCl.PDW.Gear.Automatic.REVERSE}. ".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not object_detected:
            evaluation = " ".join(
                f"No objects detected in critical range. All of the following signals:"
                f"{signals_obj._properties[ValidationSignals.Columns.USS1_dist]} <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.USS2_dist]} <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.USS3_dist]} <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.USS4_dist]} <br>"
                f"have values of {constants.HilCl.PDW.SliceDistances.RED_CLOSE_L} or bigger "
                f"than {constants.HilCl.PDW.SliceDistances.GREEN_FAR_H}".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not objects_are_dynamic:
            evaluation = " ".join(
                f"Objects are not dynamic. Traffic participant velocity signal "
                f"{signals_obj._properties[ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL]}"
                f"had value 0".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif self.result.measured_result == FALSE:
            evaluation = " ".join(
                "All critical signals used in evaluation:"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR1]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR2]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR3]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR4]}, <br>"
                f"stayed on value {constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE}.".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
        elif self.result.measured_result == TRUE:
            evaluation = " ".join(
                "All critical signals used in evaluation:"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR1]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR2]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR3]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR4]}, <br>"
                f"took values != {constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE}.".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )

        # generate plots
        columns = [
            ValidationSignals.Columns.SECTOR_CRITICALITYFR1,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR2,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR3,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR4,
            ValidationSignals.Columns.GEAR_MAN,
            ValidationSignals.Columns.GEAR_AUT,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Critical right signals and Gear signals")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))

        columns = [
            ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Traffic participants velocity")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))

        columns = [
            ValidationSignals.Columns.USS1_dist,
            ValidationSignals.Columns.USS2_dist,
            ValidationSignals.Columns.USS3_dist,
            ValidationSignals.Columns.USS4_dist,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Distance to object signals [m]")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))


@teststep_definition(
    step_number=1,
    name="Rear sectors test step",
    description=(
        "Test step is checking if PDW function is reacting on rear sectors to any dynamic object as defined in "
        "req 990450 (vehicle, bicycle, pedestrian)."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwReactionToDynamicObjectsRearSector(TestStep):
    """Test step to evaluate PDW function reaction to dynamic objects."""

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
        reverse_gear_trigger = 0
        objects_are_dynamic = 0
        object_detected = 0
        self.result.measured_result = None
        data = pd.DataFrame(
            data={
                "smallest_crit_re_1": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRE1],
                "smallest_crit_re_2": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRE2],
                "smallest_crit_re_3": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRE3],
                "smallest_crit_re_4": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRE4],
                "man_gear": signals[ValidationSignals.Columns.GEAR_MAN],
                "aut_gear": signals[ValidationSignals.Columns.GEAR_AUT],
                "traffic_participant_0_vel": signals[ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL],
            },
            index=time,
        )

        reverse_frames = data[
            (data["man_gear"] == constants.HilCl.PDW.Gear.Manual.REVERSE)
            | (data["aut_gear"] == constants.HilCl.PDW.Gear.Automatic.REVERSE)
        ]
        if len(reverse_frames):
            reverse_gear_trigger = 1
        debounce_time_passed = 0
        second_debounce_time_passed = 0
        first_ts_obj_det = 0
        for ts in reverse_frames.index:
            if debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                debounce_time_passed = ts - reverse_frames.index[0]
            else:
                if uss_detect_rear_sectors(signals, ts):
                    object_detected = 1
                    if reverse_frames["traffic_participant_0_vel"][ts] != 0:
                        objects_are_dynamic = 1
                        if first_ts_obj_det == 0:
                            first_ts_obj_det = ts
                        if second_debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                            second_debounce_time_passed = ts - first_ts_obj_det
                        else:
                            if (
                                reverse_frames["smallest_crit_re_1"][ts]
                                == constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE
                                or reverse_frames["smallest_crit_re_2"][ts]
                                == constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE
                                or reverse_frames["smallest_crit_re_3"][ts]
                                == constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE
                                or reverse_frames["smallest_crit_re_4"][ts]
                                == constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE
                            ):
                                self.result.measured_result = FALSE

        if (
            reverse_gear_trigger
            and debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM
            and self.result.measured_result is None
        ):
            self.result.measured_result = TRUE

        if not reverse_gear_trigger:
            evaluation = " ".join(
                f"R gear was not engaged. The evaluation was failed because manual gear signal: "
                f"{signals_obj._properties[ValidationSignals.Columns.GEAR_MAN]} did not take "
                f"value {constants.HilCl.PDW.Gear.Manual.REVERSE} or automatic gear signal: "
                f"{signals_obj._properties[ValidationSignals.Columns.GEAR_AUT]} "
                f"did not take value {constants.HilCl.PDW.Gear.Automatic.REVERSE}. ".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not object_detected:
            evaluation = " ".join(
                f"No objects detected in critical range. All of the following signals:"
                f"{signals_obj._properties[ValidationSignals.Columns.USS7_dist]} <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.USS8_dist]} <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.USS9_dist]} <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.USS10_dist]} <br>"
                f"have values of {constants.HilCl.PDW.SliceDistances.RED_CLOSE_L} or bigger "
                f"than {constants.HilCl.PDW.SliceDistances.GREEN_FAR_H}".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not objects_are_dynamic:
            evaluation = " ".join(
                f"Objects are not dynamic. Traffic participant velocity signal "
                f"{signals_obj._properties[ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL]}"
                f"had value 0".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif self.result.measured_result == FALSE:
            evaluation = " ".join(
                "All critical signals used in evaluation:"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE1]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE2]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE3]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE4]}, <br>"
                f"stayed on value {constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE}.".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
        elif self.result.measured_result == TRUE:
            evaluation = " ".join(
                "All critical signals used in evaluation:"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE1]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE2]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE3]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE4]}, <br>"
                f"took values != {constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE}.".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )

        # generate plots
        columns = [
            ValidationSignals.Columns.SECTOR_CRITICALITYRE1,
            ValidationSignals.Columns.SECTOR_CRITICALITYRE2,
            ValidationSignals.Columns.SECTOR_CRITICALITYRE3,
            ValidationSignals.Columns.SECTOR_CRITICALITYRE4,
            ValidationSignals.Columns.GEAR_MAN,
            ValidationSignals.Columns.GEAR_AUT,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Critical right signals and Gear signals")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))

        columns = [
            ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Traffic participants velocity")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))

        columns = [
            ValidationSignals.Columns.USS7_dist,
            ValidationSignals.Columns.USS8_dist,
            ValidationSignals.Columns.USS9_dist,
            ValidationSignals.Columns.USS10_dist,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Distance to object signals [m]")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))


@teststep_definition(
    step_number=1,
    name="Left sectors test step",
    description=(
        "Test step is checking if PDW function is reacting on left sectors to any dynamic object as defined in "
        "req 990450 (vehicle, bicycle, pedestrian)."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwReactionToDynamicObjectsLeftSector(TestStep):
    """Test step to evaluate PDW function reaction to dynamic objects."""

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
        reverse_gear_trigger = 0
        objects_are_dynamic = 0
        object_detected = 0
        self.result.measured_result = None
        data = pd.DataFrame(
            data={
                "smallest_crit_le_1": signals[ValidationSignals.Columns.SECTOR_CRITICALITYLE1],
                "smallest_crit_le_2": signals[ValidationSignals.Columns.SECTOR_CRITICALITYLE2],
                "smallest_crit_le_3": signals[ValidationSignals.Columns.SECTOR_CRITICALITYLE3],
                "smallest_crit_le_4": signals[ValidationSignals.Columns.SECTOR_CRITICALITYLE4],
                "man_gear": signals[ValidationSignals.Columns.GEAR_MAN],
                "aut_gear": signals[ValidationSignals.Columns.GEAR_AUT],
                "traffic_participant_0_vel": signals[ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL],
            },
            index=time,
        )

        reverse_frames = data[
            (data["man_gear"] == constants.HilCl.PDW.Gear.Manual.REVERSE)
            | (data["aut_gear"] == constants.HilCl.PDW.Gear.Automatic.REVERSE)
        ]
        if len(reverse_frames):
            reverse_gear_trigger = 1

        debounce_time_passed = 0
        second_debounce_time_passed = 0
        first_ts_obj_det = 0
        for ts in reverse_frames.index:
            if debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                debounce_time_passed = ts - reverse_frames.index[0]
            else:
                if uss_detect_left_sectors(signals, ts):
                    object_detected = 1
                    if reverse_frames["traffic_participant_0_vel"][ts] != 0:
                        objects_are_dynamic = 1
                        if first_ts_obj_det == 0:
                            first_ts_obj_det = ts
                        if second_debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                            second_debounce_time_passed = ts - first_ts_obj_det
                        else:
                            if (
                                reverse_frames["smallest_crit_le_1"][ts]
                                == constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE
                                or reverse_frames["smallest_crit_le_2"][ts]
                                == constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE
                                or reverse_frames["smallest_crit_le_3"][ts]
                                == constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE
                                or reverse_frames["smallest_crit_le_4"][ts]
                                == constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE
                            ):
                                self.result.measured_result = FALSE

        if (
            reverse_gear_trigger
            and debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM
            and self.result.measured_result is None
        ):
            self.result.measured_result = TRUE

        if not reverse_gear_trigger:
            evaluation = " ".join(
                f"R gear was not engaged. The evaluation was failed because manual gear signal: "
                f"{signals_obj._properties[ValidationSignals.Columns.GEAR_MAN]} did not take "
                f"value {constants.HilCl.PDW.Gear.Manual.REVERSE} or automatic gear signal: "
                f"{signals_obj._properties[ValidationSignals.Columns.GEAR_AUT]} "
                f"did not take value {constants.HilCl.PDW.Gear.Automatic.REVERSE}. ".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not object_detected:
            evaluation = " ".join(
                f"No objects detected in critical range. All of the following signals:"
                f"{signals_obj._properties[ValidationSignals.Columns.USS5_dist]}<br>"
                f"{signals_obj._properties[ValidationSignals.Columns.USS6_dist]}<br>"
                f"have values of {constants.HilCl.PDW.SliceDistances.RED_CLOSE_L} or bigger "
                f"than {constants.HilCl.PDW.SliceDistances.GREEN_FAR_H}".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not objects_are_dynamic:
            evaluation = " ".join(
                f"Objects are not dynamic. Traffic participant velocity signal "
                f"{signals_obj._properties[ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL]}"
                f"had value 0".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif self.result.measured_result == FALSE:
            evaluation = " ".join(
                "All critical signals used in evaluation:"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE1]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE2]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE3]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE4]}, <br>"
                f"stayed on value {constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE}.".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
        elif self.result.measured_result == TRUE:
            evaluation = " ".join(
                "All critical signals used in evaluation:"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE1]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE2]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE3]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE4]}, <br>"
                f"took values != {constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE}.".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )

        # generate plots
        columns = [
            ValidationSignals.Columns.SECTOR_CRITICALITYLE1,
            ValidationSignals.Columns.SECTOR_CRITICALITYLE2,
            ValidationSignals.Columns.SECTOR_CRITICALITYLE3,
            ValidationSignals.Columns.SECTOR_CRITICALITYLE4,
            ValidationSignals.Columns.GEAR_MAN,
            ValidationSignals.Columns.GEAR_AUT,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Critical right signals and Gear signals")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))

        columns = [
            ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Traffic participants velocity")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))

        columns = [
            ValidationSignals.Columns.USS5_dist,
            ValidationSignals.Columns.USS6_dist,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Distance to object signals [m]")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))


@teststep_definition(
    step_number=1,
    name="Right sectors test step",
    description=(
        "Test step is checking if PDW function is reacting on right sectors to any dynamic object as defined in "
        "req 990450 (vehicle, bicycle, pedestrian)."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwReactionToDynamicObjectsRightSector(TestStep):
    """Test step to evaluate PDW function reaction to dynamic objects."""

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
        reverse_gear_trigger = 0
        objects_are_dynamic = 0
        object_detected = 0
        self.result.measured_result = None
        data = pd.DataFrame(
            data={
                "smallest_crit_ri_1": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRI1],
                "smallest_crit_ri_2": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRI2],
                "smallest_crit_ri_3": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRI3],
                "smallest_crit_ri_4": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRI4],
                "man_gear": signals[ValidationSignals.Columns.GEAR_MAN],
                "aut_gear": signals[ValidationSignals.Columns.GEAR_AUT],
                "traffic_participant_0_vel": signals[ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL],
            },
            index=time,
        )

        reverse_frames = data[
            (data["man_gear"] == constants.HilCl.PDW.Gear.Manual.REVERSE)
            | (data["aut_gear"] == constants.HilCl.PDW.Gear.Automatic.REVERSE)
        ]
        if len(reverse_frames):
            reverse_gear_trigger = 1

        debounce_time_passed = 0
        second_debounce_time_passed = 0
        first_ts_obj_det = 0
        for ts in reverse_frames.index:
            if debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                debounce_time_passed = ts - reverse_frames.index[0]
            else:
                if uss_detect_right_sectors(signals, ts):
                    object_detected = 1
                    if reverse_frames["traffic_participant_0_vel"][ts] != 0:
                        objects_are_dynamic = 1
                        if first_ts_obj_det == 0:
                            first_ts_obj_det = ts
                        if second_debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                            second_debounce_time_passed = ts - first_ts_obj_det
                        else:
                            if (
                                reverse_frames["smallest_crit_ri_1"][ts]
                                == constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE
                                or reverse_frames["smallest_crit_ri_2"][ts]
                                == constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE
                                or reverse_frames["smallest_crit_ri_3"][ts]
                                == constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE
                                or reverse_frames["smallest_crit_ri_4"][ts]
                                == constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE
                            ):
                                self.result.measured_result = FALSE

        if (
            reverse_gear_trigger
            and debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM
            and self.result.measured_result is None
        ):
            self.result.measured_result = TRUE

        if not reverse_gear_trigger:
            evaluation = " ".join(
                f"R gear was not engaged. The evaluation was failed because manual gear signal: "
                f"{signals_obj._properties[ValidationSignals.Columns.GEAR_MAN]} did not take "
                f"value {constants.HilCl.PDW.Gear.Manual.REVERSE} or automatic gear signal: "
                f"{signals_obj._properties[ValidationSignals.Columns.GEAR_AUT]} "
                f"did not take value {constants.HilCl.PDW.Gear.Automatic.REVERSE}. ".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not object_detected:
            evaluation = " ".join(
                f"No objects detected in critical range. All of the following signals:"
                f"{signals_obj._properties[ValidationSignals.Columns.USS0_dist]} <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.USS11_dist]} <br>"
                f"have values of {constants.HilCl.PDW.SliceDistances.RED_CLOSE_L} or bigger "
                f"than {constants.HilCl.PDW.SliceDistances.GREEN_FAR_H}".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not objects_are_dynamic:
            evaluation = " ".join(
                f"Objects are not dynamic. Traffic participant velocity signal "
                f"{signals_obj._properties[ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL]}"
                f"had value 0".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif self.result.measured_result == FALSE:
            evaluation = " ".join(
                "All critical signals used in evaluation:"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI1]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI2]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI3]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI4]}, <br>"
                f"stayed on value {constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE}.".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
        elif self.result.measured_result == TRUE:
            evaluation = " ".join(
                "All critical signals used in evaluation:"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI1]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI2]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI3]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI4]}, <br>"
                f"took values != {constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE}.".split()
            )
            signal_summary["PDW react to dynamic object"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )

        # generate plots
        columns = [
            ValidationSignals.Columns.SECTOR_CRITICALITYRI1,
            ValidationSignals.Columns.SECTOR_CRITICALITYRI2,
            ValidationSignals.Columns.SECTOR_CRITICALITYRI3,
            ValidationSignals.Columns.SECTOR_CRITICALITYRI4,
            ValidationSignals.Columns.GEAR_MAN,
            ValidationSignals.Columns.GEAR_AUT,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Critical right signals and Gear signals")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))

        columns = [
            ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Traffic participants velocity")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))

        columns = [
            ValidationSignals.Columns.USS0_dist,
            ValidationSignals.Columns.USS11_dist,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Distance to object signals [m]")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))


@verifies(
    requirement="1818115",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_KoRT4LEcEe65AZJQ7uUF6w?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@testcase_definition(
    name="PDW reaction to dynamic objects on left sector Test Case",
    description=(
        "Test is checking if PDW function is reacting on left sectors to any dynamic object as defined in req 990450, "
        "if its classified as one of the following: vehicle, bicycle, pedestrian"
    ),
)
class PDWReactionToDynamicObjectsLeftSectorTestCase(TestCase):
    """PDW function reaction to dynamic objects test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PdwReactionToDynamicObjectsLeftSector,
        ]


@verifies(
    requirement="1818115",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_KoRT4LEcEe65AZJQ7uUF6w?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@testcase_definition(
    name="PDW reaction to dynamic objects on right sector Test Case",
    description=(
        "Test is checking if PDW function is reacting on right sectors to any dynamic object as defined in req 990450, "
        "if its classified as one of the following: vehicle, bicycle, pedestrian"
    ),
)
class PDWReactionToDynamicObjectsRightSectorTestCase(TestCase):
    """PDW function reaction to dynamic objects test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PdwReactionToDynamicObjectsRightSector,
        ]


@verifies(
    requirement="1818115",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_KoRT4LEcEe65AZJQ7uUF6w?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@testcase_definition(
    name="PDW reaction to dynamic objects on front sector Test Case",
    description=(
        "Test is checking if PDW function is reacting on front sectors to any dynamic object as defined in req 990450, "
        "if its classified as one of the following: vehicle, bicycle, pedestrian"
    ),
)
class PDWReactionToDynamicObjectsFrontSectorTestCase(TestCase):
    """PDW function reaction to dynamic objects test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PdwReactionToDynamicObjectsFrontSector,
        ]


@verifies(
    requirement="1818115",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_KoRT4LEcEe65AZJQ7uUF6w?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@testcase_definition(
    name="PDW reaction to dynamic objects on rear sector Test Case",
    description=(
        "Test is checking if PDW function is reacting on rear sectors to any dynamic object as defined in req 990450, "
        "if its classified as one of the following: vehicle, bicycle, pedestrian"
    ),
)
class PDWReactionToDynamicObjectsRearSectorTestCase(TestCase):
    """PDW function reaction to dynamic objects test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PdwReactionToDynamicObjectsRearSector,
        ]
