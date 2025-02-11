"""Park Distance Warning - evaluation script"""

import logging
import os
import sys

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

__author__ = "Constantin Marius"

SIGNAL_DATA = "PDW_SOUND_RECOVER_GRAD"


class ValidationSignals(MDFSignalDefinition):
    """Example signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        TIMESTAMP = "mts_ts"
        PDW_CAN_STATE = "PDW_State"
        VEH_VELOCITY = "Vehicle_velocity"

        SECTOR_CRITICALITYFR = "SECTOR_CRITICALITYFR{}"
        SECTOR_CRITICALITYFR1 = "SECTOR_CRITICALITYFR1"
        SECTOR_CRITICALITYFR2 = "SECTOR_CRITICALITYFR2"
        SECTOR_CRITICALITYFR3 = "SECTOR_CRITICALITYFR3"
        SECTOR_CRITICALITYFR4 = "SECTOR_CRITICALITYFR4"

        TRAFFIC_PARTICIPANT0_VEL = "TRAFFIC_PARTICIPANT0_VEL"
        FRONT_SPEAKER = "FRONT_SPEAKER"
        FRONT_SPEAKER_VOLUME = "FRONT_SPEAKER_VOLUME"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.PDW_CAN_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.PDCInfo.PDCSystemState",
            self.Columns.VEH_VELOCITY: "MTS.ADAS_CAN.Conti_Veh_CAN.VehVelocity.VehVelocityExt",
            self.Columns.TRAFFIC_PARTICIPANT0_VEL: "CM.Traffic.T00.LongVel",
            self.Columns.FRONT_SPEAKER: "MTS.AP_Private_CAN.AP_Private_CAN.TONHInfo.FrontSpeakerOn",
            self.Columns.FRONT_SPEAKER_VOLUME: "MTS.AP_Private_CAN.AP_Private_CAN.TONHInfo.FrontSpeakerVolume",
        }

        front_sectors_criticality = {
            self.Columns.SECTOR_CRITICALITYFR.format(
                x
            ): f"MTS.AP_Private_CAN.AP_Private_CAN.PDCFrontAndLeft.PDCFront{x}CriticalLevel"
            for x in range(1, 5)
        }
        self._properties.update(front_sectors_criticality)


signals_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="PDW sound recover gradually if vehicle starts moving",
    description=(
        "The PDW function shall recover gradually the sound if the vehicle starts moving "
        "(with the obstacle still in range)."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwSoundRecoverGradEgoStartMovingTS(TestStep):
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
        pdw_state = signals[ValidationSignals.Columns.PDW_CAN_STATE].tolist()
        fr_crit1_lvl = signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR1].tolist()
        fr_crit2_lvl = signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR2].tolist()
        fr_crit3_lvl = signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR3].tolist()
        fr_crit4_lvl = signals[ValidationSignals.Columns.SECTOR_CRITICALITYFR4].tolist()
        obj_vel = signals[ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL].tolist()
        ego_vel = signals[ValidationSignals.Columns.VEH_VELOCITY].tolist()
        front_speaker_vol = signals[ValidationSignals.Columns.FRONT_SPEAKER_VOLUME].tolist()

        self.result.measured_result = None
        actv_btn_idx = 0
        yellow_crit_zn_idx = 0
        standstill_idx = 0
        no_sound_lvl_idx = 0
        ego_dynamic_idx = 0
        time_to_no_sound = 5500000  # us
        time_interval_sound_lvl_change = 550000  # us

        # check PDW activation precondition
        for idx in range(0, len(time)):
            if pdw_state[idx] == constants.HilCl.PDW.States.ACTIVATED_BY_BUTTON:
                actv_btn_idx = idx
                break

        # check if object reached the yellow critical zone
        if actv_btn_idx:
            for idx in range(actv_btn_idx, len(time)):
                if (
                    fr_crit1_lvl[idx] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE
                    or fr_crit2_lvl[idx] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE
                    or fr_crit3_lvl[idx] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE
                    or fr_crit4_lvl[idx] == constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE
                ):
                    yellow_crit_zn_idx = idx
                    break

        # check if ego vehicle is in standstill and object is static
        if yellow_crit_zn_idx:
            for idx in range(yellow_crit_zn_idx, len(time)):
                if obj_vel[idx] == 0 and ego_vel[idx] == 0:
                    standstill_idx = idx
                    break

        # check if this  status is maintained at least 5.5 seconds and that sound level is 0
        if standstill_idx:
            for idx in range(standstill_idx, len(time)):
                if time[idx] - time[standstill_idx] < time_to_no_sound:
                    if obj_vel[idx] != 0 or ego_vel[idx] != 0:
                        break
                else:
                    # if sound lvl is 0 continue
                    if front_speaker_vol[idx] == 0:
                        no_sound_lvl_idx = idx
                    # if sound lvl != 0 break, precondition is not fulfilled
                    else:
                        break

        # check if ego becomes dynamic
        if no_sound_lvl_idx:
            for idx in range(no_sound_lvl_idx, len(time)):
                if ego_vel[idx] != 0:
                    ego_dynamic_idx = idx
                    break

        # check if sound recovers gradually at every 0.55 seconds to 5
        sound_lvl_flag = [0, 0, 0, 0, 0]
        if ego_dynamic_idx:
            timer = 0
            for idx in range(ego_dynamic_idx, len(time)):
                if timer <= time_interval_sound_lvl_change:
                    timer = timer + time[idx]
                # check if sound increased when 0.55 seconds passed
                else:
                    if not sound_lvl_flag[0]:
                        if front_speaker_vol[idx] == 1:
                            sound_lvl_flag[0] = 1
                            timer = 0
                    else:
                        if not sound_lvl_flag[1]:
                            if front_speaker_vol[idx] == 2:
                                sound_lvl_flag[1] = 1
                                timer = 0
                        else:
                            if not sound_lvl_flag[2]:
                                if front_speaker_vol[idx] == 3:
                                    sound_lvl_flag[2] = 1
                                    timer = 0
                            else:
                                if not sound_lvl_flag[3]:
                                    if front_speaker_vol[idx] == 4:
                                        sound_lvl_flag[3] = 1
                                        timer = 0
                                else:
                                    if not sound_lvl_flag[4]:
                                        if front_speaker_vol[idx] == 5:
                                            sound_lvl_flag[4] = 1
                                            timer = 0
        if all(sound_lvl_flag):
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        if not actv_btn_idx:
            evaluation = " ".join(
                f"FAILED because signal: {signals_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} "
                f"did not change to {constants.HilCl.PDW.States.ACTIVATED_BY_BUTTON}.".split()
            )
            signal_summary["PDW sound recover gradually when ego starts moving"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not yellow_crit_zn_idx:
            evaluation = " ".join(
                f"FAILED because none of the following critical level signals: "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR1]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR2]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR3]}, "
                f"{signals_obj._properties[ValidationSignals.Columns.SECTOR_CRITICALITYFR4]} "
                f"changed to {constants.HilCl.PDW.CriticalLevel.YELLOW_ZONE}.".split()
            )
            signal_summary["PDW sound recover gradually when ego starts moving"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not standstill_idx:
            evaluation = " ".join(
                f"FAILED because ego velocity signal: {signals_obj._properties[ValidationSignals.Columns.VEH_VELOCITY]}"
                f" did not reached 0 km/h or object velocity signal: "
                f"{signals_obj._properties[ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL]} did not reached 0."
                f"km/h".split()
            )
            signal_summary["PDW sound recover gradually when ego starts moving"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not no_sound_lvl_idx:
            evaluation = " ".join(
                f"FAILED because ego velocity signal: {signals_obj._properties[ValidationSignals.Columns.VEH_VELOCITY]}"
                f" and object velocity signal:"
                f"{signals_obj._properties[ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL]} did not keep 0 km/h"
                f" for at least 5.5 seconds or "
                f"sound level signal {signals_obj._properties[ValidationSignals.Columns.FRONT_SPEAKER_VOLUME]} did not "
                f"reached 0.".split()
            )
            signal_summary["PDW sound recover gradually when ego starts moving"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not ego_dynamic_idx:
            evaluation = " ".join(
                f"FAILED because ego vehicle velocity signal "
                f"{signals_obj._properties[ValidationSignals.Columns.VEH_VELOCITY]} did not took a "
                f"value different of 0 after 5.5 seconds of standstill.".split()
            )
            signal_summary["PDW sound recover gradually when ego starts moving"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif self.result.measured_result == TRUE:
            evaluation = " ".join(
                f"PASSED because sound level signal "
                f"{signals_obj._properties[ValidationSignals.Columns.FRONT_SPEAKER_VOLUME]} "
                f"raised gradually to 5 after ego vehicle stated moving towards traffic participant after 5.5 "
                f"seconds of standstill.".split()
            )
            signal_summary["PDW sound recover gradually when ego starts moving"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
        elif self.result.measured_result == FALSE:
            evaluation = " ".join(
                f"FAILED because sound level signal "
                f"{signals_obj._properties[ValidationSignals.Columns.FRONT_SPEAKER_VOLUME]} "
                f"did not raised gradually to 5 after ego vehicle stated moving towards traffic participant after 5.5 "
                f"seconds of standstill.".split()
            )
            signal_summary["PDW sound recover gradually when ego starts moving"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )

        plot_signals = [
            ValidationSignals.Columns.PDW_CAN_STATE,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR1,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR2,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR3,
            ValidationSignals.Columns.SECTOR_CRITICALITYFR4,
            ValidationSignals.Columns.TRAFFIC_PARTICIPANT0_VEL,
            ValidationSignals.Columns.VEH_VELOCITY,
            ValidationSignals.Columns.FRONT_SPEAKER_VOLUME,
        ]
        fig_fr = plotter_helper(time, signals, plot_signals, signals_obj._properties)
        fig_fr.update_layout(title="Signals used in evaluation")
        self.result.details["Plots"].append(fig_fr.to_html(full_html=False, include_plotlyjs=False))


@verifies(
    requirement="2769069",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_21ySoISXEe-CF94Rr8dH8w?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
@testcase_definition(
    name="PDW sound recover gradually if vehicle starts moving towards object test case",
    description="The PDW function shall recover gradually the sound if the vehicle starts moving.",
)
class PdwSoundRecoverGradEgoStartMovingTestCase(TestCase):
    """PDW sound recover gradually when ego moves towards object test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PdwSoundRecoverGradEgoStartMovingTS,
        ]
