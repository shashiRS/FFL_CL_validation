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

SIGNAL_DATA = "PDW_CRITICAL_SLICES"


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

        SECTOR_CRIT_SLICE_FR = "SECTOR_CRIT_SLICE_FR{}"
        SECTOR_CRIT_SLICE_FR1 = "SECTOR_CRIT_SLICE_FR1"
        SECTOR_CRIT_SLICE_FR2 = "SECTOR_CRIT_SLICE_FR2"
        SECTOR_CRIT_SLICE_FR3 = "SECTOR_CRIT_SLICE_FR3"
        SECTOR_CRIT_SLICE_FR4 = "SECTOR_CRIT_SLICE_FR4"

        SECTOR_CRIT_SLICE_LE = "SECTOR_CRIT_SLICE_LE{}"
        SECTOR_CRIT_SLICE_LE1 = "SECTOR_CRIT_SLICE_LE1"
        SECTOR_CRIT_SLICE_LE2 = "SECTOR_CRIT_SLICE_LE2"
        SECTOR_CRIT_SLICE_LE3 = "SECTOR_CRIT_SLICE_LE3"
        SECTOR_CRIT_SLICE_LE4 = "SECTOR_CRIT_SLICE_LE4"

        SECTOR_CRIT_SLICE_RE = "SECTOR_CRIT_SLICE_RE{}"
        SECTOR_CRIT_SLICE_RE1 = "SECTOR_CRIT_SLICE_RE1"
        SECTOR_CRIT_SLICE_RE2 = "SECTOR_CRIT_SLICE_RE2"
        SECTOR_CRIT_SLICE_RE3 = "SECTOR_CRIT_SLICE_RE3"
        SECTOR_CRIT_SLICE_RE4 = "SECTOR_CRIT_SLICE_RE4"

        SECTOR_CRIT_SLICE_RI = "SECTOR_CRIT_SLICE_RI{}"
        SECTOR_CRIT_SLICE_RI1 = "SECTOR_CRIT_SLICE_RI1"
        SECTOR_CRIT_SLICE_RI2 = "SECTOR_CRIT_SLICE_RI2"
        SECTOR_CRIT_SLICE_RI3 = "SECTOR_CRIT_SLICE_RI3"
        SECTOR_CRIT_SLICE_RI4 = "SECTOR_CRIT_SLICE_RI4"

        T0_uss2_dist = "T0_uss2_dist"
        T0_uss3_dist = "T0_uss3_dist"
        T0_uss0_dist = "T0_uss0_dist"
        T0_uss5_dist = "T0_uss5_dist"
        T1_uss6_dist = "T1_uss6_dist"
        T1_uss11_dist = "T1_uss11_dist"
        T1_uss1_dist = "T1_uss1_dist"
        T2_uss4_dist = "T2_uss4_dist"
        T0_uss8_dist = "T0_uss8_dist"
        T0_uss9_dist = "T0_uss9_dist"
        T1_uss7_dist = "T1_uss7_dist"
        T2_uss10_dist = "T2_uss10_dist"

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
            self.Columns.T0_uss5_dist: "CM.Sensor.Object.USS05.Obj.T00.NearPnt.ds_p",
            self.Columns.T1_uss6_dist: "CM.Sensor.Object.USS06.Obj.T00_1.NearPnt.ds_p",
            self.Columns.T0_uss0_dist: "CM.Sensor.Object.USS00.Obj.T00.NearPnt.ds_p",
            self.Columns.T1_uss11_dist: "CM.Sensor.Object.USS11.Obj.T00_1.NearPnt.ds_p",
            self.Columns.T0_uss2_dist: "CM.Sensor.Object.USS02.T00.NearPnt.ds_p",
            self.Columns.T0_uss3_dist: "CM.Sensor.Object.USS03.T00.NearPnt.ds_p",
            self.Columns.T1_uss1_dist: "CM.Sensor.Object.USS01.T00_1.NearPnt.ds_p",
            self.Columns.T2_uss4_dist: "CM.Sensor.Object.USS04.T00_2.NearPnt.ds_p",
            self.Columns.T0_uss8_dist: "CM.Sensor.Object.USS08.T00.NearPnt.ds_p",
            self.Columns.T0_uss9_dist: "CM.Sensor.Object.USS09.T00.NearPnt.ds_p",
            self.Columns.T1_uss7_dist: "CM.Sensor.Object.USS07.T00_2.NearPnt.ds_p",
            self.Columns.T2_uss10_dist: "CM.Sensor.Object.USS10.T00_1.NearPnt.ds_p",
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
        front_sectors_crit_slice = {
            self.Columns.SECTOR_CRIT_SLICE_FR.format(
                x
            ): f"MTS.AP_Private_CAN.AP_Private_CAN.PDCFrontAndLeft.PDCFront{x}Slice"
            for x in range(1, 5)
        }
        left_sectors_crit_slice = {
            self.Columns.SECTOR_CRIT_SLICE_LE.format(
                x
            ): f"MTS.AP_Private_CAN.AP_Private_CAN.PDCFrontAndLeft.PDCLeft{x}Slice"
            for x in range(1, 5)
        }
        rear_sectors_crit_slice = {
            self.Columns.SECTOR_CRIT_SLICE_RE.format(
                x
            ): f"MTS.AP_Private_CAN.AP_Private_CAN.PDCRearAndRight.PDCRear{x}Slice"
            for x in range(1, 5)
        }
        right_sectors_crit_slice = {
            self.Columns.SECTOR_CRIT_SLICE_RI.format(
                x
            ): f"MTS.AP_Private_CAN.AP_Private_CAN.PDCRearAndRight.PDCRight{x}Slice"
            for x in range(1, 5)
        }
        self._properties.update(front_sectors_criticality)
        self._properties.update(left_sectors_criticality)
        self._properties.update(rear_sectors_criticality)
        self._properties.update(right_sectors_criticality)
        self._properties.update(front_sectors_crit_slice)
        self._properties.update(left_sectors_crit_slice)
        self._properties.update(rear_sectors_crit_slice)
        self._properties.update(right_sectors_crit_slice)


signals_obj = ValidationSignals()


def check_crit_slice_dist(uss, level, cr_slice):
    """Check if critically level and slices are set correctly."""
    if level == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
        if cr_slice == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
            if constants.HilCl.PDW.SliceDistances.GREEN_FAR_L < uss <= constants.HilCl.PDW.SliceDistances.GREEN_FAR_H:
                return 1
            else:
                return 0
        elif cr_slice == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
            if constants.HilCl.PDW.SliceDistances.GREEN_MID_L < uss <= constants.HilCl.PDW.SliceDistances.GREEN_MID_H:
                return 1
            else:
                return 0
        elif cr_slice == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
            if (
                constants.HilCl.PDW.SliceDistances.GREEN_CLOSE_L
                < uss
                <= constants.HilCl.PDW.SliceDistances.GREEN_CLOSE_H
            ):
                return 1
            else:
                return 0
        else:
            raise Exception("Wrong slice parameter")
    elif level == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
        if cr_slice == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
            if constants.HilCl.PDW.SliceDistances.YELLOW_FAR_L < uss <= constants.HilCl.PDW.SliceDistances.YELLOW_FAR_H:
                return 1
            else:
                return 0
        elif cr_slice == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
            if constants.HilCl.PDW.SliceDistances.YELLOW_MID_L < uss <= constants.HilCl.PDW.SliceDistances.YELLOW_MID_H:
                return 1
            else:
                return 0
        elif cr_slice == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
            if (
                constants.HilCl.PDW.SliceDistances.YELLOW_CLOSE_L
                < uss
                <= constants.HilCl.PDW.SliceDistances.YELLOW_CLOSE_H
            ):
                return 1
            else:
                return 0
        else:
            raise Exception("Wrong slice parameter")
    elif level == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
        if cr_slice == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
            if constants.HilCl.PDW.SliceDistances.RED_FAR_L < uss <= constants.HilCl.PDW.SliceDistances.RED_FAR_H:
                return 1
            else:
                return 0
        elif cr_slice == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
            if constants.HilCl.PDW.SliceDistances.RED_MID_L < uss <= constants.HilCl.PDW.SliceDistances.RED_MID_H:
                return 1
            else:
                return 0
        elif cr_slice == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
            if constants.HilCl.PDW.SliceDistances.RED_CLOSE_L < uss <= constants.HilCl.PDW.SliceDistances.RED_CLOSE_H:
                return 1
            else:
                return 0
        else:
            raise Exception("Wrong slice parameter")
    else:
        raise Exception("Wrong level parameter")


@teststep_definition(
    step_number=1,
    name="Front sectors critical levels test step",
    description=(
        "Based on the evaluated distances from ego vehicle front side car contour to the closest point of all the "
        "objects intersecting the current sector, the PDW function shall send to the driver the slice "
        "criticality level."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwCriticalLevelsFrontSector(TestStep):
    """Test step to evaluate PDW critical levels."""

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
        uss1 = signals[ValidationSignals.Columns.T1_uss1_dist]
        uss2 = signals[ValidationSignals.Columns.T0_uss3_dist]
        uss3 = signals[ValidationSignals.Columns.T0_uss3_dist]
        uss4 = signals[ValidationSignals.Columns.T2_uss4_dist]

        reverse_gear_trigger = 0
        self.result.measured_result = None
        fr1_crit_slice = 1
        fr2_crit_slice = 1
        fr3_crit_slice = 1
        fr4_crit_slice = 1
        crit_sector1 = 0
        crit_sector1_l = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        crit_sector2 = 0
        crit_sector2_l = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        crit_sector3 = 0
        crit_sector3_l = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        crit_sector4 = 0
        crit_sector4_l = [0, 0, 0, 0, 0, 0, 0, 0, 0]

        data = pd.DataFrame(
            data={
                "smallest_crit_fr_1": signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR1],
                "smallest_crit_fr_2": signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR2],
                "smallest_crit_fr_3": signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR3],
                "smallest_crit_fr_4": signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR4],
                "crit_slice_fr_1": signals[ValidationSignals.Columns.SECTOR_CRIT_SLICE_FR1],
                "crit_slice_fr_2": signals[ValidationSignals.Columns.SECTOR_CRIT_SLICE_FR2],
                "crit_slice_fr_3": signals[ValidationSignals.Columns.SECTOR_CRIT_SLICE_FR3],
                "crit_slice_fr_4": signals[ValidationSignals.Columns.SECTOR_CRIT_SLICE_FR4],
                "man_gear": signals[ValidationSignals.Columns.GEAR_MAN],
                "aut_gear": signals[ValidationSignals.Columns.GEAR_AUT],
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

        for ts in reverse_frames.index:
            if debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                debounce_time_passed = ts - reverse_frames.index[0]
                self.result.measured_result = TRUE
            else:
                # fr1
                if reverse_frames["smallest_crit_fr_1"][ts] != constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE:
                    crit_sector1 = 1
                    fr1_ts_status = 1
                    if reverse_frames["smallest_crit_fr_1"][ts] == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
                        if reverse_frames["crit_slice_fr_1"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[0] = 1
                            fr1_ts_status = check_crit_slice_dist(
                                uss4[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_1"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[1] = 1
                            fr1_ts_status = check_crit_slice_dist(
                                uss4[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_1"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[2] = 1
                            fr1_ts_status = check_crit_slice_dist(
                                uss4[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_fr_1"][ts] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
                        if reverse_frames["crit_slice_fr_1"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[3] = 1
                            fr1_ts_status = check_crit_slice_dist(
                                uss4[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_1"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[4] = 1
                            fr1_ts_status = check_crit_slice_dist(
                                uss4[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_1"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[5] = 1
                            fr1_ts_status = check_crit_slice_dist(
                                uss4[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_fr_1"][ts] == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
                        if reverse_frames["crit_slice_fr_1"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[6] = 1
                            fr1_ts_status = check_crit_slice_dist(
                                uss4[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_1"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[7] = 1
                            fr1_ts_status = check_crit_slice_dist(
                                uss4[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_1"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[8] = 1
                            fr1_ts_status = check_crit_slice_dist(
                                uss4[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    if not fr1_ts_status:
                        fr1_crit_slice = 0
                # fr2
                if reverse_frames["smallest_crit_fr_2"][ts] != constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE:
                    crit_sector2 = 1
                    fr2_ts_status = 1
                    if reverse_frames["smallest_crit_fr_2"][ts] == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
                        if reverse_frames["crit_slice_fr_2"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[0] = 1
                            fr2_ts_status = check_crit_slice_dist(
                                uss3[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_2"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[1] = 1
                            fr2_ts_status = check_crit_slice_dist(
                                uss3[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_2"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[2] = 1
                            fr2_ts_status = check_crit_slice_dist(
                                uss3[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_fr_2"][ts] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
                        if reverse_frames["crit_slice_fr_2"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[3] = 1
                            fr2_ts_status = check_crit_slice_dist(
                                uss3[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_2"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[4] = 1
                            fr2_ts_status = check_crit_slice_dist(
                                uss3[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_2"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[5] = 1
                            fr2_ts_status = check_crit_slice_dist(
                                uss3[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_fr_2"][ts] == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
                        if reverse_frames["crit_slice_fr_2"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[6] = 1
                            fr2_ts_status = check_crit_slice_dist(
                                uss3[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_2"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[7] = 1
                            fr2_ts_status = check_crit_slice_dist(
                                uss3[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_2"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[8] = 1
                            fr2_ts_status = check_crit_slice_dist(
                                uss3[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    if not fr2_ts_status:
                        fr2_crit_slice = 0
                # fr3
                if reverse_frames["smallest_crit_fr_3"][ts] != constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE:
                    crit_sector3 = 1
                    fr3_ts_status = 1
                    if reverse_frames["smallest_crit_fr_3"][ts] == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
                        if reverse_frames["crit_slice_fr_3"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[0] = 1
                            fr3_ts_status = check_crit_slice_dist(
                                uss2[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_3"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[1] = 1
                            fr3_ts_status = check_crit_slice_dist(
                                uss2[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_3"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[2] = 1
                            fr3_ts_status = check_crit_slice_dist(
                                uss2[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_fr_3"][ts] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
                        if reverse_frames["crit_slice_fr_3"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[3] = 1
                            fr3_ts_status = check_crit_slice_dist(
                                uss2[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_3"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[4] = 1
                            fr3_ts_status = check_crit_slice_dist(
                                uss2[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_3"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[5] = 1
                            fr3_ts_status = check_crit_slice_dist(
                                uss2[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_fr_3"][ts] == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
                        if reverse_frames["crit_slice_fr_3"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[6] = 1
                            fr3_ts_status = check_crit_slice_dist(
                                uss2[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_3"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[7] = 1
                            fr3_ts_status = check_crit_slice_dist(
                                uss2[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_3"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[8] = 1
                            fr3_ts_status = check_crit_slice_dist(
                                uss2[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    if not fr3_ts_status:
                        fr3_crit_slice = 0
                # fr4
                if reverse_frames["smallest_crit_fr_4"][ts] != constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE:
                    crit_sector4 = 1
                    fr4_ts_status = 1
                    if reverse_frames["smallest_crit_fr_4"][ts] == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
                        if reverse_frames["crit_slice_fr_4"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[0] = 1
                            fr4_ts_status = check_crit_slice_dist(
                                uss1[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_4"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[1] = 1
                            fr4_ts_status = check_crit_slice_dist(
                                uss1[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_4"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[2] = 1
                            fr4_ts_status = check_crit_slice_dist(
                                uss1[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_fr_4"][ts] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
                        if reverse_frames["crit_slice_fr_4"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[3] = 1
                            fr4_ts_status = check_crit_slice_dist(
                                uss1[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_4"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[4] = 1
                            fr4_ts_status = check_crit_slice_dist(
                                uss1[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_4"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[5] = 1
                            fr4_ts_status = check_crit_slice_dist(
                                uss1[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_fr_4"][ts] == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
                        if reverse_frames["crit_slice_fr_4"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[6] = 1
                            fr4_ts_status = check_crit_slice_dist(
                                uss1[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_4"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[7] = 1
                            fr4_ts_status = check_crit_slice_dist(
                                uss1[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_fr_4"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[8] = 1
                            fr4_ts_status = check_crit_slice_dist(
                                uss1[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    if not fr4_ts_status:
                        fr4_crit_slice = 0

        if not reverse_gear_trigger:
            evaluation = " ".join(
                f"The evaluation was FAILED, because the signal"
                f" {signals_obj._properties[ValidationSignals.Columns.GEAR_MAN]}"
                f" did not take value {constants.HilCl.PDW.Gear.Manual.REVERSE} or"
                f" {signals_obj._properties[ValidationSignals.Columns.GEAR_AUT]} did not take "
                f"value {constants.HilCl.PDW.Gear.Automatic.REVERSE}.".split()
            )
            signal_summary["PDW critical levels"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not crit_sector1 or not crit_sector2 or not crit_sector3 or not crit_sector4:
            evaluation = " ".join(
                "At least one of critically signals:"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR1]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR2]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR3]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR4]} "
                f" stayed on 0.".split()
            )
            signal_summary["PDW critical levels"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif (
            not crit_sector1_l.count(1) == len(crit_sector1_l)
            or not crit_sector2_l.count(1) == len(crit_sector2_l)
            or not crit_sector3_l.count(1) == len(crit_sector3_l)
            or not crit_sector4_l.count(1) == len(crit_sector4_l)
        ):
            evaluation = " ".join("Not all critically slices were evaluated.".split())
            signal_summary["PDW critical levels"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        else:
            if not fr1_crit_slice:
                evaluation = " ".join("Front sector 1 critically slice computed wrong.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )
                self.result.measured_result = FALSE
            if not fr2_crit_slice:
                evaluation = " ".join("Front sector 2 critically slice computed wrong.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )
                self.result.measured_result = FALSE
            if not fr3_crit_slice:
                evaluation = " ".join("Front sector 3 critically slice computed wrong.".split())
                signal_summary["PPDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )
                self.result.measured_result = FALSE
            if not fr4_crit_slice:
                evaluation = " ".join("Front sector 4 critically slice computed wrong.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )
                self.result.measured_result = FALSE
            if (
                self.result.measured_result == TRUE
                and fr1_crit_slice
                and fr2_crit_slice
                and fr3_crit_slice
                and fr4_crit_slice
            ):
                evaluation = " ".join("Critical slices were computed right.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )

        # generate plots
        columns = [
            ValidationSignals.Columns.SECTOR_CRITICALITYFR1,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR2,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR3,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR4,
            ValidationSignals.Columns.SECTOR_CRIT_SLICE_FR1,
            ValidationSignals.Columns.SECTOR_CRIT_SLICE_FR2,
            ValidationSignals.Columns.SECTOR_CRIT_SLICE_FR3,
            ValidationSignals.Columns.SECTOR_CRIT_SLICE_FR4,
            ValidationSignals.Columns.GEAR_MAN,
            ValidationSignals.Columns.GEAR_AUT,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Critical front signals and Gear signals")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))

        columns = [
            ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Traffic participants velocity")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))

        columns = [
            ValidationSignals.Columns.T0_uss2_dist,
            ValidationSignals.Columns.T0_uss3_dist,
            ValidationSignals.Columns.T1_uss1_dist,
            ValidationSignals.Columns.T2_uss4_dist,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Distance to traffic participants(T0,T1,T2) signals [m]")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))


@teststep_definition(
    step_number=1,
    name="Rear sectors critical levels test step",
    description=(
        "Based on the evaluated distances from ego vehicle rear side car contour to the closest point of all the "
        "objects intersecting the current sector, the PDW function shall send to the driver the "
        "slice criticality level."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwCriticalLevelsRearSector(TestStep):
    """Test step to evaluate PDW critical levels."""

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
        uss7 = signals[ValidationSignals.Columns.T1_uss7_dist]
        uss8 = signals[ValidationSignals.Columns.T0_uss8_dist]
        uss9 = signals[ValidationSignals.Columns.T0_uss9_dist]
        uss10 = signals[ValidationSignals.Columns.T2_uss10_dist]
        time = signals.index.tolist()
        reverse_gear_trigger = 0
        self.result.measured_result = None
        re1_crit_slice = 1
        re2_crit_slice = 1
        re3_crit_slice = 1
        re4_crit_slice = 1
        crit_sector1 = 0
        crit_sector1_l = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        crit_sector2 = 0
        crit_sector2_l = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        crit_sector3 = 0
        crit_sector3_l = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        crit_sector4 = 0
        crit_sector4_l = [0, 0, 0, 0, 0, 0, 0, 0, 0]

        data = pd.DataFrame(
            data={
                "smallest_crit_re_1": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRE1],
                "smallest_crit_re_2": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRE2],
                "smallest_crit_re_3": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRE3],
                "smallest_crit_re_4": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRE4],
                "crit_slice_re_1": signals[ValidationSignals.Columns.SECTOR_CRIT_SLICE_RE1],
                "crit_slice_re_2": signals[ValidationSignals.Columns.SECTOR_CRIT_SLICE_RE2],
                "crit_slice_re_3": signals[ValidationSignals.Columns.SECTOR_CRIT_SLICE_RE3],
                "crit_slice_re_4": signals[ValidationSignals.Columns.SECTOR_CRIT_SLICE_RE4],
                "man_gear": signals[ValidationSignals.Columns.GEAR_MAN],
                "aut_gear": signals[ValidationSignals.Columns.GEAR_AUT],
            },
            index=time,
        )

        reverse_frames = data[
            (data["man_gear"] == constants.HilCl.PDW.Gear.Manual.REVERSE)
            | (data["man_gear"] == constants.HilCl.PDW.Gear.Automatic.REVERSE)
        ]
        if len(reverse_frames):
            reverse_gear_trigger = 1

        debounce_time_passed = 0
        for ts in reverse_frames.index:
            if debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                debounce_time_passed = ts - reverse_frames.index[0]
                self.result.measured_result = TRUE
            else:
                # re1
                if reverse_frames["smallest_crit_re_1"][ts] != constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE:
                    re1_ts_status = 1
                    crit_sector1 = 1
                    if reverse_frames["smallest_crit_re_1"][ts] == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
                        if reverse_frames["crit_slice_re_1"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[0] = 1
                            re1_ts_status = check_crit_slice_dist(
                                uss10[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_1"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[1] = 1
                            re1_ts_status = check_crit_slice_dist(
                                uss10[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_1"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[2] = 1
                            re1_ts_status = check_crit_slice_dist(
                                uss10[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_re_1"][ts] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
                        if reverse_frames["crit_slice_re_1"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[3] = 1
                            re1_ts_status = check_crit_slice_dist(
                                uss10[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_1"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[4] = 1
                            re1_ts_status = check_crit_slice_dist(
                                uss10[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_1"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[5] = 1
                            re1_ts_status = check_crit_slice_dist(
                                uss10[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_re_1"][ts] == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
                        if reverse_frames["crit_slice_re_1"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[6] = 1
                            re1_ts_status = check_crit_slice_dist(
                                uss10[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_1"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[7] = 1
                            re1_ts_status = check_crit_slice_dist(
                                uss10[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_1"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[8] = 1
                            re1_ts_status = check_crit_slice_dist(
                                uss10[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    if not re1_ts_status:
                        re1_crit_slice = 0

                # re2
                if reverse_frames["smallest_crit_re_2"][ts] != constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE:
                    crit_sector2 = 1
                    re2_ts_status = 1
                    if reverse_frames["smallest_crit_re_2"][ts] == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
                        if reverse_frames["crit_slice_re_2"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[0] = 1
                            re2_ts_status = check_crit_slice_dist(
                                uss9[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_2"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[1] = 1
                            re2_ts_status = check_crit_slice_dist(
                                uss9[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_2"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[2] = 1
                            re2_ts_status = check_crit_slice_dist(
                                uss9[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_re_2"][ts] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
                        if reverse_frames["crit_slice_re_2"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[3] = 1
                            re2_ts_status = check_crit_slice_dist(
                                uss9[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_2"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[4] = 1
                            re2_ts_status = check_crit_slice_dist(
                                uss9[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_2"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[5] = 1
                            re2_ts_status = check_crit_slice_dist(
                                uss9[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_re_2"][ts] == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
                        if reverse_frames["crit_slice_re_2"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[6] = 1
                            re2_ts_status = check_crit_slice_dist(
                                uss9[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_2"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[7] = 1
                            re2_ts_status = check_crit_slice_dist(
                                uss9[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_2"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[8] = 1
                            re2_ts_status = check_crit_slice_dist(
                                uss9[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    if not re2_ts_status:
                        re2_crit_slice = 0

                # re3
                if reverse_frames["smallest_crit_re_3"][ts] != constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE:
                    crit_sector3 = 1
                    re3_ts_status = 1
                    if reverse_frames["smallest_crit_re_3"][ts] == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
                        if reverse_frames["crit_slice_re_3"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[0] = 1
                            re3_ts_status = check_crit_slice_dist(
                                uss8[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_3"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[1] = 1
                            re3_ts_status = check_crit_slice_dist(
                                uss8[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_3"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[2] = 1
                            re3_ts_status = check_crit_slice_dist(
                                uss8[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_re_3"][ts] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
                        if reverse_frames["crit_slice_re_3"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[3] = 1
                            re3_ts_status = check_crit_slice_dist(
                                uss8[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_3"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[4] = 1
                            re3_ts_status = check_crit_slice_dist(
                                uss8[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_3"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[5] = 1
                            re3_ts_status = check_crit_slice_dist(
                                uss8[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_re_3"][ts] == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
                        if reverse_frames["crit_slice_re_3"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[6] = 1
                            re3_ts_status = check_crit_slice_dist(
                                uss8[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_3"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[7] = 1
                            re3_ts_status = check_crit_slice_dist(
                                uss8[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_3"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[8] = 1
                            re3_ts_status = check_crit_slice_dist(
                                uss8[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    if not re3_ts_status:
                        re3_crit_slice = 0

                # re4
                if reverse_frames["smallest_crit_re_4"][ts] != constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE:
                    crit_sector4 = 1
                    re4_ts_status = 1
                    if reverse_frames["smallest_crit_re_4"][ts] == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
                        if reverse_frames["crit_slice_re_4"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[0] = 1
                            re4_ts_status = check_crit_slice_dist(
                                uss7[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_4"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[1] = 1
                            re4_ts_status = check_crit_slice_dist(
                                uss7[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_4"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[2] = 1
                            re4_ts_status = check_crit_slice_dist(
                                uss7[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_re_4"][ts] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
                        if reverse_frames["crit_slice_re_4"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[3] = 1
                            re4_ts_status = check_crit_slice_dist(
                                uss7[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_4"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[4] = 1
                            re4_ts_status = check_crit_slice_dist(
                                uss7[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_4"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[5] = 1
                            re4_ts_status = check_crit_slice_dist(
                                uss7[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_re_4"][ts] == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
                        if reverse_frames["crit_slice_re_4"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[6] = 1
                            re4_ts_status = check_crit_slice_dist(
                                uss7[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_4"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[7] = 1
                            re4_ts_status = check_crit_slice_dist(
                                uss7[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_re_4"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[8] = 1
                            re4_ts_status = check_crit_slice_dist(
                                uss7[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    if not re4_ts_status:
                        re4_crit_slice = 0

        if not reverse_gear_trigger:
            evaluation = " ".join(
                f"The evaluation was FAILED, because the signal"
                f" {signals_obj._properties[ValidationSignals.Columns.GEAR_MAN]}"
                f" did not take value {constants.HilCl.PDW.Gear.Manual.REVERSE} or"
                f" {signals_obj._properties[ValidationSignals.Columns.GEAR_AUT]} did not take "
                f"value {constants.HilCl.PDW.Gear.Automatic.REVERSE}.".split()
            )
            signal_summary["PDW critical levels"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not crit_sector1 or not crit_sector2 or not crit_sector3 or not crit_sector4:
            evaluation = " ".join(
                "At least one of critically signals:"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE1]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE2]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE3]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRE4]} "
                f" stayed on 0.".split()
            )
            signal_summary["PDW critical levels"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif (
            not crit_sector1_l.count(1) == len(crit_sector1_l)
            or not crit_sector2_l.count(1) == len(crit_sector2_l)
            or not crit_sector3_l.count(1) == len(crit_sector3_l)
            or not crit_sector4_l.count(1) == len(crit_sector4_l)
        ):
            evaluation = " ".join("Not all critically slices were evaluated.".split())
            signal_summary["PDW critical levels"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        else:
            if not re1_crit_slice:
                evaluation = " ".join("Rear sector 1 critically slice computed wrong.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )
                self.result.measured_result = FALSE
            if not re2_crit_slice:
                evaluation = " ".join("Rear sector 2 critically slice computed wrong.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )
                self.result.measured_result = FALSE
            if not re3_crit_slice:
                evaluation = " ".join("Rear sector 3 critically slice computed wrong.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )
                self.result.measured_result = FALSE
            if not re4_crit_slice:
                evaluation = " ".join("Rear sector 4 critically slice computed wrong.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )
                self.result.measured_result = FALSE
            if (
                self.result.measured_result == TRUE
                and re1_crit_slice
                and re2_crit_slice
                and re3_crit_slice
                and re4_crit_slice
            ):
                evaluation = " ".join("Critical slices were computed right.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )

        # generate plots
        columns = [
            ValidationSignals.Columns.SECTOR_CRITICALITYRE1,
            ValidationSignals.Columns.SECTOR_CRITICALITYRE2,
            ValidationSignals.Columns.SECTOR_CRITICALITYRE3,
            ValidationSignals.Columns.SECTOR_CRITICALITYRE4,
            ValidationSignals.Columns.SECTOR_CRIT_SLICE_RE1,
            ValidationSignals.Columns.SECTOR_CRIT_SLICE_RE2,
            ValidationSignals.Columns.SECTOR_CRIT_SLICE_RE3,
            ValidationSignals.Columns.SECTOR_CRIT_SLICE_RE4,
            ValidationSignals.Columns.GEAR_MAN,
            ValidationSignals.Columns.GEAR_AUT,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Critical rear signals and Gear signals")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))

        columns = [
            ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Traffic participants velocity")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))

        columns = [
            ValidationSignals.Columns.T0_uss8_dist,
            ValidationSignals.Columns.T0_uss9_dist,
            ValidationSignals.Columns.T1_uss7_dist,
            ValidationSignals.Columns.T2_uss10_dist,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Distance to traffic participants(T0,T1,T2) signals [m]")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))


@teststep_definition(
    step_number=1,
    name="Left sectors critical levels test step",
    description=(
        "Based on the evaluated distances from ego vehicle left side car contour to the closest point of all the "
        "objects intersecting the current sector, the PDW function shall send to the driver the slice "
        "criticality level."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwCriticalLevelsLeftSector(TestStep):
    """Test step to evaluate PDW critical levels."""

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
        self.result.measured_result = None
        uss5 = signals[ValidationSignals.Columns.T0_uss5_dist]
        uss6 = signals[ValidationSignals.Columns.T1_uss6_dist]
        le1_crit_slice = 1
        le2_crit_slice = 1
        le3_crit_slice = 1
        le4_crit_slice = 1
        crit_sector1 = 0
        crit_sector1_l = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        crit_sector2 = 0
        crit_sector2_l = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        crit_sector3 = 0
        crit_sector3_l = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        crit_sector4 = 0
        crit_sector4_l = [0, 0, 0, 0, 0, 0, 0, 0, 0]

        data = pd.DataFrame(
            data={
                "smallest_crit_le_1": signals[ValidationSignals.Columns.SECTOR_CRITICALITYLE1],
                "smallest_crit_le_2": signals[ValidationSignals.Columns.SECTOR_CRITICALITYLE2],
                "smallest_crit_le_3": signals[ValidationSignals.Columns.SECTOR_CRITICALITYLE3],
                "smallest_crit_le_4": signals[ValidationSignals.Columns.SECTOR_CRITICALITYLE4],
                "crit_slice_le_1": signals[ValidationSignals.Columns.SECTOR_CRIT_SLICE_LE1],
                "crit_slice_le_2": signals[ValidationSignals.Columns.SECTOR_CRIT_SLICE_LE2],
                "crit_slice_le_3": signals[ValidationSignals.Columns.SECTOR_CRIT_SLICE_LE3],
                "crit_slice_le_4": signals[ValidationSignals.Columns.SECTOR_CRIT_SLICE_LE4],
                "man_gear": signals[ValidationSignals.Columns.GEAR_MAN],
                "aut_gear": signals[ValidationSignals.Columns.GEAR_AUT],
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

        for ts in reverse_frames.index:
            if debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                debounce_time_passed = ts - reverse_frames.index[0]
                self.result.measured_result = TRUE
            else:
                # le1
                if reverse_frames["smallest_crit_le_1"][ts] != constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE:
                    crit_sector1 = 1
                    le1_ts_status = 1
                    if reverse_frames["smallest_crit_le_1"][ts] == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
                        if reverse_frames["crit_slice_le_1"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[0] = 1
                            le1_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_1"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[1] = 1
                            le1_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_1"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[2] = 1
                            le1_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_le_1"][ts] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
                        if reverse_frames["crit_slice_le_1"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[3] = 1
                            le1_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_1"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[4] = 1
                            le1_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_1"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[5] = 1
                            le1_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_le_1"][ts] == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
                        if reverse_frames["crit_slice_le_1"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[6] = 1
                            le1_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_1"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[7] = 1
                            le1_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_1"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[8] = 1
                            le1_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    if not le1_ts_status:
                        le1_crit_slice = 0

                # le2
                if reverse_frames["smallest_crit_le_2"][ts] != constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE:
                    crit_sector2 = 1
                    le2_ts_status = 1
                    if reverse_frames["smallest_crit_le_2"][ts] == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
                        if reverse_frames["crit_slice_le_2"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[0] = 1
                            le2_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_2"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[1] = 1
                            le2_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_2"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[2] = 1
                            le2_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_le_2"][ts] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
                        if reverse_frames["crit_slice_le_2"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[3] = 1
                            le2_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_2"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[4] = 1
                            le2_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_2"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[5] = 1
                            le2_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_le_2"][ts] == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
                        if reverse_frames["crit_slice_le_2"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[6] = 1
                            le2_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_2"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[7] = 1
                            le2_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_2"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[8] = 1
                            le2_ts_status = check_crit_slice_dist(
                                uss6[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    if not le2_ts_status:
                        le2_crit_slice = 0

                # le3
                if reverse_frames["smallest_crit_le_3"][ts] != constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE:
                    crit_sector3 = 1
                    le3_ts_status = 1
                    if reverse_frames["smallest_crit_le_3"][ts] == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
                        if reverse_frames["crit_slice_le_3"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[0] = 1
                            le3_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_3"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[1] = 1
                            le3_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_3"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[2] = 1
                            le3_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_le_3"][ts] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
                        if reverse_frames["crit_slice_le_3"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[3] = 1
                            le3_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_3"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[4] = 1
                            le3_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_3"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[5] = 1
                            le3_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_le_3"][ts] == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
                        if reverse_frames["crit_slice_le_3"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[6] = 1
                            le3_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_3"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[7] = 1
                            le3_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_3"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[8] = 1
                            le3_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    if not le3_ts_status:
                        le3_crit_slice = 0

                # le4
                if reverse_frames["smallest_crit_le_4"][ts] != constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE:
                    crit_sector4 = 1
                    le4_ts_status = 1
                    if reverse_frames["smallest_crit_le_4"][ts] == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
                        if reverse_frames["crit_slice_le_4"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[0] = 1
                            le4_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_4"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[1] = 1
                            le4_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_4"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[2] = 1
                            le4_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_le_4"][ts] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
                        if reverse_frames["crit_slice_le_4"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[3] = 1
                            le4_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_4"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[4] = 1
                            le4_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_4"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[5] = 1
                            le4_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_le_4"][ts] == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
                        if reverse_frames["crit_slice_le_4"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[6] = 1
                            le4_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_4"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[7] = 1
                            le4_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_le_4"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[8] = 1
                            le4_ts_status = check_crit_slice_dist(
                                uss5[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    if not le4_ts_status:
                        le4_crit_slice = 0

        if not reverse_gear_trigger:
            evaluation = " ".join(
                f"The evaluation was FAILED, because the signal"
                f" {signals_obj._properties[ValidationSignals.Columns.GEAR_MAN]}"
                f" did not take value {constants.HilCl.PDW.Gear.Manual.REVERSE} or"
                f" {signals_obj._properties[ValidationSignals.Columns.GEAR_AUT]} did not take "
                f"value {constants.HilCl.PDW.Gear.Automatic.REVERSE}.".split()
            )
            signal_summary["PDW critical levels"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not crit_sector1 or not crit_sector2 or not crit_sector3 or not crit_sector4:
            evaluation = " ".join(
                "At least one of critically signals:"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE1]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE2]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE3]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYLE4]} "
                f" stayed on 0.".split()
            )
            signal_summary["PDW critical levels"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif (
            not crit_sector1_l.count(1) == len(crit_sector1_l)
            or not crit_sector2_l.count(1) == len(crit_sector2_l)
            or not crit_sector3_l.count(1) == len(crit_sector3_l)
            or not crit_sector4_l.count(1) == len(crit_sector4_l)
        ):
            evaluation = " ".join("Not all critically slices were evaluated.".split())
            signal_summary["PDW critical levels"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        else:
            if not le1_crit_slice:
                evaluation = " ".join("Left sector 1 critically slice computed wrong.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )
                self.result.measured_result = FALSE
            if not le2_crit_slice:
                evaluation = " ".join("Left sector 2 critically slice computed wrong.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )
                self.result.measured_result = FALSE
            if not le3_crit_slice:
                evaluation = " ".join("Left sector 3 critically slice computed wrong.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )
                self.result.measured_result = FALSE
            if not le4_crit_slice:
                evaluation = " ".join("Left sector 4 critically slice computed wrong.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )
                self.result.measured_result = FALSE
            if (
                self.result.measured_result == TRUE
                and le1_crit_slice
                and le2_crit_slice
                and le3_crit_slice
                and le4_crit_slice
            ):
                evaluation = " ".join("Critical slices were computed right.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )

        # generate plots
        columns = [
            ValidationSignals.Columns.SECTOR_CRITICALITYLE1,
            ValidationSignals.Columns.SECTOR_CRITICALITYLE2,
            ValidationSignals.Columns.SECTOR_CRITICALITYLE3,
            ValidationSignals.Columns.SECTOR_CRITICALITYLE4,
            ValidationSignals.Columns.SECTOR_CRIT_SLICE_LE1,
            ValidationSignals.Columns.SECTOR_CRIT_SLICE_LE2,
            ValidationSignals.Columns.SECTOR_CRIT_SLICE_LE3,
            ValidationSignals.Columns.SECTOR_CRIT_SLICE_LE4,
            ValidationSignals.Columns.GEAR_MAN,
            ValidationSignals.Columns.GEAR_AUT,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Critical left signals and Gear signals")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))

        columns = [
            ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Traffic participants velocity")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))

        columns = [
            ValidationSignals.Columns.T0_uss5_dist,
            ValidationSignals.Columns.T1_uss6_dist,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Distance to traffic participants (T0,T1 signals) [m]")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))


@teststep_definition(
    step_number=1,
    name="Right sectors critical levels test step",
    description=(
        "Based on the evaluated distances from ego vehicle right side car contour to the closest point of all the "
        "objects intersecting the current sector, the PDW function shall send to the driver the slice "
        "criticality level."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwCriticalLevelsRightSector(TestStep):
    """Test step to evaluate PDW critical levels."""

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
        self.result.measured_result = None
        uss0 = signals[ValidationSignals.Columns.T0_uss0_dist]
        uss11 = signals[ValidationSignals.Columns.T1_uss11_dist]
        ri1_crit_slice = 1
        ri2_crit_slice = 1
        ri3_crit_slice = 1
        ri4_crit_slice = 1
        crit_sector1 = 0
        crit_sector1_l = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        crit_sector2 = 0
        crit_sector2_l = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        crit_sector3 = 0
        crit_sector3_l = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        crit_sector4 = 0
        crit_sector4_l = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        data = pd.DataFrame(
            data={
                "smallest_crit_ri_1": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRI1],
                "smallest_crit_ri_2": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRI2],
                "smallest_crit_ri_3": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRI3],
                "smallest_crit_ri_4": signals[ValidationSignals.Columns.SECTOR_CRITICALITYRI4],
                "crit_slice_le_1": signals[ValidationSignals.Columns.SECTOR_CRIT_SLICE_RI1],
                "crit_slice_le_2": signals[ValidationSignals.Columns.SECTOR_CRIT_SLICE_RI2],
                "crit_slice_le_3": signals[ValidationSignals.Columns.SECTOR_CRIT_SLICE_RI3],
                "crit_slice_le_4": signals[ValidationSignals.Columns.SECTOR_CRIT_SLICE_RI4],
                "man_gear": signals[ValidationSignals.Columns.GEAR_MAN],
                "aut_gear": signals[ValidationSignals.Columns.GEAR_AUT],
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

        for ts in reverse_frames.index:
            if debounce_time_passed < constants.HilCl.PDW.FTTI.SYSTEM:  # 600ms - system FTTI
                debounce_time_passed = ts - reverse_frames.index[0]
                self.result.measured_result = TRUE
            else:
                # ri1
                if reverse_frames["smallest_crit_ri_1"][ts] != constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE:
                    crit_sector1 = 1
                    ri1_ts_status = 1
                    if reverse_frames["smallest_crit_ri_1"][ts] == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
                        if reverse_frames["crit_slice_ri_1"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[0] = 1
                            ri1_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_1"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[1] = 1
                            ri1_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_1"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[2] = 1
                            ri1_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_ri_1"][ts] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
                        if reverse_frames["crit_slice_ri_1"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[3] = 1
                            ri1_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_1"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[4] = 1
                            ri1_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_1"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[5] = 1
                            ri1_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_ri_1"][ts] == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
                        if reverse_frames["crit_slice_ri_1"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[6] = 1
                            ri1_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_1"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[7] = 1
                            ri1_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_1"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[8] = 1
                            ri1_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    if not ri1_ts_status:
                        ri1_crit_slice = 0

                # ri2
                if reverse_frames["smallest_crit_ri_2"][ts] != constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE:
                    crit_sector2 = 1
                    ri2_ts_status = 1
                    if reverse_frames["smallest_crit_ri_2"][ts] == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
                        if reverse_frames["crit_slice_ri_2"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[0] = 1
                            ri2_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_2"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[1] = 1
                            ri2_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_2"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[2] = 1
                            ri2_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_ri_2"][ts] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
                        if reverse_frames["crit_slice_ri_2"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[3] = 1
                            ri2_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_2"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[4] = 1
                            ri2_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_2"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[5] = 1
                            ri2_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_ri_2"][ts] == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
                        if reverse_frames["crit_slice_ri_2"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[6] = 1
                            ri2_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_2"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[7] = 1
                            ri2_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_2"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[8] = 1
                            ri2_ts_status = check_crit_slice_dist(
                                uss0[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    if not ri2_ts_status:
                        ri2_crit_slice = 0

                # ri3
                if reverse_frames["smallest_crit_ri_3"][ts] != constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE:
                    crit_sector3 = 1
                    ri3_ts_status = 1
                    if reverse_frames["smallest_crit_ri_3"][ts] == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
                        if reverse_frames["crit_slice_ri_3"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[0] = 1
                            ri3_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_3"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[1] = 1
                            ri3_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_3"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[2] = 1
                            ri3_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_ri_3"][ts] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
                        if reverse_frames["crit_slice_ri_3"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[3] = 1
                            ri3_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_3"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[4] = 1
                            ri3_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_3"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[5] = 1
                            ri3_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_ri_3"][ts] == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
                        if reverse_frames["crit_slice_ri_3"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[6] = 1
                            ri3_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_3"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[7] = 1
                            ri3_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_3"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[8] = 1
                            ri3_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    if not ri3_ts_status:
                        ri3_crit_slice = 0

                # ri4
                if reverse_frames["smallest_crit_ri_4"][ts] != constants.HilCl.PDW.CriticalLevel.NO_CRITICAL_ZONE:
                    crit_sector4 = 1
                    ri4_ts_status = 1
                    if reverse_frames["smallest_crit_ri_4"][ts] == constants.HilCl.PDW.CriticalLevel.GREEN_ZONE:
                        if reverse_frames["crit_slice_ri_4"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[0] = 1
                            ri4_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_4"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[1] = 1
                            ri4_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_4"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[2] = 1
                            ri4_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.GREEN_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_ri_4"][ts] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE:
                        if reverse_frames["crit_slice_ri_4"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[3] = 1
                            ri4_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_4"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[4] = 1
                            ri4_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_4"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[5] = 1
                            ri4_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    elif reverse_frames["smallest_crit_ri_4"][ts] == constants.HilCl.PDW.CriticalLevel.RED_ZONE:
                        if reverse_frames["crit_slice_ri_4"][ts] == constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE:
                            crit_sector1_l[6] = 1
                            ri4_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.CLOSE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_4"][ts] == constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE:
                            crit_sector1_l[7] = 1
                            ri4_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.MIDDLE_SLICE,
                            )
                        elif reverse_frames["crit_slice_ri_4"][ts] == constants.HilCl.PDW.CriticalSlice.FAR_SLICE:
                            crit_sector1_l[8] = 1
                            ri4_ts_status = check_crit_slice_dist(
                                uss11[ts],
                                constants.HilCl.PDW.CriticalLevel.RED_ZONE,
                                constants.HilCl.PDW.CriticalSlice.FAR_SLICE,
                            )
                    if not ri4_ts_status:
                        ri4_crit_slice = 0

        if not reverse_gear_trigger:
            evaluation = " ".join(
                f"The evaluation was FAILED, because the signal"
                f" {signals_obj._properties[ValidationSignals.Columns.GEAR_MAN]}"
                f" did not take value {constants.HilCl.PDW.Gear.Manual.REVERSE} or"
                f" {signals_obj._properties[ValidationSignals.Columns.GEAR_AUT]} did not take "
                f"value {constants.HilCl.PDW.Gear.Automatic.REVERSE}.".split()
            )
            signal_summary["PDW critical levels"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not crit_sector1 or not crit_sector2 or not crit_sector3 or not crit_sector4:
            evaluation = " ".join(
                "At least one of critically signals:"
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI1]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI2]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI3]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYRI4]} "
                f" stayed on 0.".split()
            )
            signal_summary["PDW critical levels"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif (
            not crit_sector1_l.count(1) == len(crit_sector1_l)
            or not crit_sector2_l.count(1) == len(crit_sector2_l)
            or not crit_sector3_l.count(1) == len(crit_sector3_l)
            or not crit_sector4_l.count(1) == len(crit_sector4_l)
        ):
            evaluation = " ".join("Not all critically slices were evaluated.".split())
            signal_summary["PDW critical levels"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        else:
            if not ri1_crit_slice:
                evaluation = " ".join("Right sector 1 critically slice computed wrong.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )
                self.result.measured_result = FALSE
            if not ri2_crit_slice:
                evaluation = " ".join("Right sector 2 critically slice computed wrong.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )
                self.result.measured_result = FALSE
            if not ri3_crit_slice:
                evaluation = " ".join("Right sector 3 critically slice computed wrong.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )
                self.result.measured_result = FALSE
            if not ri4_crit_slice:
                evaluation = " ".join("Right sector 4 critically slice computed wrong.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )
                self.result.measured_result = FALSE
            if (
                self.result.measured_result == TRUE
                and ri1_crit_slice
                and ri2_crit_slice
                and ri3_crit_slice
                and ri4_crit_slice
            ):
                evaluation = " ".join("Critical slices were computed right.".split())
                signal_summary["PDW critical levels"] = evaluation
                self.result.details["Plots"].append(
                    fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
                )

        # generate plots
        columns = [
            ValidationSignals.Columns.SECTOR_CRITICALITYRI1,
            ValidationSignals.Columns.SECTOR_CRITICALITYRI2,
            ValidationSignals.Columns.SECTOR_CRITICALITYRI3,
            ValidationSignals.Columns.SECTOR_CRITICALITYRI4,
            ValidationSignals.Columns.SECTOR_CRIT_SLICE_RI1,
            ValidationSignals.Columns.SECTOR_CRIT_SLICE_RI2,
            ValidationSignals.Columns.SECTOR_CRIT_SLICE_RI3,
            ValidationSignals.Columns.SECTOR_CRIT_SLICE_RI4,
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
            ValidationSignals.Columns.T0_uss0_dist,
            ValidationSignals.Columns.T1_uss11_dist,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Distance to traffic participants(T0,T1 signals) [m]")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))


@verifies(
    requirement="990467",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_j0KOGtIAEe2iKqc0KPO99Q?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@verifies(
    requirement="990471",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_j0KOHdIAEe2iKqc0KPO99Q?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@testcase_definition(
    name="PDW critical levels on front sector Test Case",
    description=("Test is checking if PDW function is reacting with the correct critical level."),
)
class PDWCriticalLevelsFrontSectorTestCase(TestCase):
    """PDW critical levels front sectors test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PdwCriticalLevelsFrontSector,
        ]


@verifies(
    requirement="990467",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_j0KOGtIAEe2iKqc0KPO99Q?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@verifies(
    requirement="990471",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_j0KOHdIAEe2iKqc0KPO99Q?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@testcase_definition(
    name="PDW critical levels on rear sector Test Case",
    description=("Test is checking if PDW function is reacting with the correct critical level."),
)
class PDWCriticalLevelsRearSectorTestCase(TestCase):
    """PDW critical levels rear sectors test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PdwCriticalLevelsRearSector,
        ]


@verifies(
    requirement="990467",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_j0KOGtIAEe2iKqc0KPO99Q?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@verifies(
    requirement="990471",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_j0KOHdIAEe2iKqc0KPO99Q?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@testcase_definition(
    name="PDW critical levels on right sector Test Case",
    description=("Test is checking if PDW function is reacting with the correct critical level."),
)
class PDWCriticalLevelsRightSectorTestCase(TestCase):
    """PDW critical levels right sectors test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PdwCriticalLevelsRightSector,
        ]


@verifies(
    requirement="990467",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_j0KOGtIAEe2iKqc0KPO99Q?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@verifies(
    requirement="990471",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_j0KOHdIAEe2iKqc0KPO99Q?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@testcase_definition(
    name="PDW critical levels on left sector Test Case",
    description=("Test is checking if PDW function is reacting with the correct critical level."),
)
class PDWCriticalLevelsLeftSectorTestCase(TestCase):
    """PDW critical levels left sectors test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PdwCriticalLevelsLeftSector,
        ]
