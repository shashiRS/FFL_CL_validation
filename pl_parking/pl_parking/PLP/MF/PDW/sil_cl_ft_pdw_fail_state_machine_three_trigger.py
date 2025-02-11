"""Example functional test"""  # this is a required docstring

"""import libraries"""
import logging
import os
import sys

import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
"""imports from tsf core"""
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.io.signals import SignalDefinition

"""imports from current repo"""
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "PDW_F_STATE_THREE"

gearPosition = constants.GearReqConstants
pdwState = constants.SilCl.PDWConstants.pdwState
pdwSysState = constants.SilCl.PDWConstants.pdwSystemState
pdw_hmi_interact = constants.SilCl.PDWConstants.pdwUserActionHeadUnit  # TAP_ON_PDC = 35
epbSwitch = constants.SilCl.PDWConstants.EPBSwitch
drvTubeDisplay = constants.SilCl.PDWConstants.DrivingTubeReq
apStateVal = constants.SilCl.PDWConstants.ApStates
ap_PDWFailure = constants.SilCl.PDWConstants.pdwFailure
wheel_direction = constants.SilCl.PDWConstants.WheelDirection
speed_threshold = constants.SilCl.PDWConstants.PDWSpeedThreshold
pdw_sector_length = constants.SilCl.PDWConstants.PDWSectorLength
speed_converter = 3.6  # vehicle velocity convert factor unit [km/h]
overspeed_deact = 20  # km/h
tata_overspeed_deact = 13  # km/h
delay = constants.SilCl.PDWConstants.delay


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        PDW_SYSTEM_STATE = "PDWSystemState"
        PDW_STATE = "PDWSate"
        VELOCITY = "Velocity"
        STEERING_ANGLE = "SteeringAngle"
        TIME = "Time"
        GEARBOX_STATE = "GearBoxState"
        EPB_SWITCH = "EPBActivation"
        MUTE = "PDWMute"
        DRV_TUBE = "DrvTubeDisplay"
        TAP_ON_HMI = "UserActionHMI"
        AP_STATE = "APState"
        PDW_FAILURE = "apPDWFailure"
        WHEEL_FL = "WheelFrontLeft"
        WHEEL_FR = "WheelFrontRight"
        WHEEL_RL = "WheelRearLeft"
        WHEEL_RR = "WheelRearRight"

        SECTOR_STAT_DISTANCEFR = "SECTOR_STAT_DISTANCEFR{}"
        SECTOR_STAT_DISTANCEFR0 = "SECTOR_STAT_DISTANCEFR0"
        SECTOR_STAT_DISTANCEFR1 = "SECTOR_STAT_DISTANCEFR1"
        SECTOR_STAT_DISTANCEFR2 = "SECTOR_STAT_DISTANCEFR2"
        SECTOR_STAT_DISTANCEFR3 = "SECTOR_STAT_DISTANCEFR3"
        SECTOR_DYN_DISTANCEFR = "SECTOR_DYN_DISTANCEFR{}"
        SECTOR_DYN_DISTANCEFR0 = "SECTOR_DYN_DISTANCEFR0"
        SECTOR_DYN_DISTANCEFR1 = "SECTOR_DYN_DISTANCEFR1"
        SECTOR_DYN_DISTANCEFR2 = "SECTOR_DYN_DISTANCEFR2"
        SECTOR_DYN_DISTANCEFR3 = "SECTOR_DYN_DISTANCEFR3"

        SECTOR_STAT_DISTANCERI = "SECTOR_STAT_DISTANCERI{}"
        SECTOR_STAT_DISTANCERI0 = "SECTOR_STAT_DISTANCERI0"
        SECTOR_STAT_DISTANCERI1 = "SECTOR_STAT_DISTANCERI1"
        SECTOR_STAT_DISTANCERI2 = "SECTOR_STAT_DISTANCERI2"
        SECTOR_STAT_DISTANCERI3 = "SECTOR_STAT_DISTANCERI3"
        SECTOR_DYN_DISTANCERI = "SECTOR_DYN_DISTANCERI{}"
        SECTOR_DYN_DISTANCERI0 = "SECTOR_DYN_DISTANCERI0"
        SECTOR_DYN_DISTANCERI1 = "SECTOR_DYN_DISTANCERI1"
        SECTOR_DYN_DISTANCERI2 = "SECTOR_DYN_DISTANCERI2"
        SECTOR_DYN_DISTANCERI3 = "SECTOR_DYN_DISTANCERI3"

        SECTOR_STAT_DISTANCERE = "SECTOR_STAT_DISTANCERE{}"
        SECTOR_STAT_DISTANCERE0 = "SECTOR_STAT_DISTANCERE0"
        SECTOR_STAT_DISTANCERE1 = "SECTOR_STAT_DISTANCERE1"
        SECTOR_STAT_DISTANCERE2 = "SECTOR_STAT_DISTANCERE2"
        SECTOR_STAT_DISTANCERE3 = "SECTOR_STAT_DISTANCERE3"
        SECTOR_DYN_DISTANCERE = "SECTOR_DYN_DISTANCERE{}"
        SECTOR_DYN_DISTANCERE0 = "SECTOR_DYN_DISTANCERE0"
        SECTOR_DYN_DISTANCERE1 = "SECTOR_DYN_DISTANCERE1"
        SECTOR_DYN_DISTANCERE2 = "SECTOR_DYN_DISTANCERE2"
        SECTOR_DYN_DISTANCERE3 = "SECTOR_DYN_DISTANCERE3"

        SECTOR_STAT_DISTANCELE = "SECTOR_STAT_DISTANCELE{}"
        SECTOR_STAT_DISTANCELE0 = "SECTOR_STAT_DISTANCELE0"
        SECTOR_STAT_DISTANCELE1 = "SECTOR_STAT_DISTANCELE1"
        SECTOR_STAT_DISTANCELE2 = "SECTOR_STAT_DISTANCELE2"
        SECTOR_STAT_DISTANCELE3 = "SECTOR_STAT_DISTANCELE3"
        SECTOR_DYN_DISTANCELE = "SECTOR_DYN_DISTANCELE{}"
        SECTOR_DYN_DISTANCELE0 = "SECTOR_DYN_DISTANCELE0"
        SECTOR_DYN_DISTANCELE1 = "SECTOR_DYN_DISTANCELE1"
        SECTOR_DYN_DISTANCELE2 = "SECTOR_DYN_DISTANCELE2"
        SECTOR_DYN_DISTANCELE3 = "SECTOR_DYN_DISTANCELE3"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = [
            "PDW_Signals",
        ]

        self._properties = {
            self.Columns.PDW_SYSTEM_STATE: "AP.drvWarnStatus.pdwSystemState_nu",
            self.Columns.PDW_STATE: "AP.drvWarnStatus.pdwState_nu",
            self.Columns.VELOCITY: "Car.v",
            self.Columns.TIME: "Time",
            self.Columns.GEARBOX_STATE: "AP.odoInputPort.odoSigFcanPort.gearboxCtrlStatus.gearCur_nu",
            self.Columns.EPB_SWITCH: "DM.BrakePark",
            self.Columns.MUTE: "AP.drvWarnStatus.reduceToMuteSoundReq_nu",
            self.Columns.DRV_TUBE: "AP.pdcpDrivingTubePort.drvTubeDisplay_nu",
            self.Columns.TAP_ON_HMI: "AP.hmiOutputPort.userActionHeadUnit_nu",
            self.Columns.AP_STATE: "AP.planningCtrlPort.apStates",
            self.Columns.PDW_FAILURE: "AP.pdwFailure_nu",
            self.Columns.WHEEL_FL: "AP.odoInputPort.odoSigFcanPort.wheelMeasurements.wheelDrivingDirections.wheelDrivingDirection_FL_nu",
            self.Columns.WHEEL_FR: "AP.odoInputPort.odoSigFcanPort.wheelMeasurements.wheelDrivingDirections.wheelDrivingDirection_FR_nu",
            self.Columns.WHEEL_RL: "AP.odoInputPort.odoSigFcanPort.wheelMeasurements.wheelDrivingDirections.wheelDrivingDirection_RL_nu",
            self.Columns.WHEEL_RR: "AP.odoInputPort.odoSigFcanPort.wheelMeasurements.wheelDrivingDirections.wheelDrivingDirection_RR_nu",
        }

        front_stat_distance = {
            self.Columns.SECTOR_STAT_DISTANCEFR.format(x): f"AP.pdcpSectorsPort.sectorsFront_{x}.smallestDistance_m"
            for x in range(4)
        }
        front_dyn_distance = {
            self.Columns.SECTOR_DYN_DISTANCEFR.format(
                x
            ): f"AP.pdcpSectorsPort.sectorsFront_{x}.dynamicSmallestDistance_m"
            for x in range(4)
        }
        left_stat_distance = {
            self.Columns.SECTOR_STAT_DISTANCELE.format(x): f"AP.pdcpSectorsPort.sectorsLeft_{x}.smallestDistance_m"
            for x in range(4)
        }
        left_dyn_distance = {
            self.Columns.SECTOR_DYN_DISTANCELE.format(
                x
            ): f"AP.pdcpSectorsPort.sectorsLeft_{x}.dynamicSmallestDistance_m"
            for x in range(4)
        }
        rear_stat_distance = {
            self.Columns.SECTOR_STAT_DISTANCERE.format(x): f"AP.pdcpSectorsPort.sectorsRear_{x}.smallestDistance_m"
            for x in range(4)
        }
        rear_dyn_distance = {
            self.Columns.SECTOR_DYN_DISTANCERE.format(
                x
            ): f"AP.pdcpSectorsPort.sectorsRear_{x}.dynamicSmallestDistance_m"
            for x in range(4)
        }
        right_stat_distance = {
            self.Columns.SECTOR_STAT_DISTANCERI.format(x): f"AP.pdcpSectorsPort.sectorsRight_{x}.smallestDistance_m"
            for x in range(4)
        }
        right_dyn_distance = {
            self.Columns.SECTOR_DYN_DISTANCERI.format(
                x
            ): f"AP.pdcpSectorsPort.sectorsRight_{x}.dynamicSmallestDistance_m"
            for x in range(4)
        }

        self._properties.update(front_stat_distance)
        self._properties.update(front_dyn_distance)
        self._properties.update(left_stat_distance)
        self._properties.update(left_dyn_distance)
        self._properties.update(rear_stat_distance)
        self._properties.update(rear_dyn_distance)
        self._properties.update(right_stat_distance)
        self._properties.update(right_dyn_distance)


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="PDW Fail State Machine three triggers",  # this would be shown as a test step name in html report
    description=(
        "This test step evaluates PDW at initialization state and checks if a failure is present or if the necessary conditions are met PDW changes to an other state."
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepPDW(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
    """

    custom_report = MfCustomTeststepReport  # Specific overview

    def __init__(self):
        super().__init__()

    #
    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """  # required docstring
        _log.debug("Starting processing...")
        # Update the details from the results page with the needed information
        # All the information from self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # Make a constant with the reader for signals:
        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_summary = {}
        signals = self.readers[ALIAS]  # Make a dataframe(df) with all signals extracted from Signals class

        self.velocity = signals[Signals.Columns.VELOCITY]
        self.ap_time = signals[Signals.Columns.TIME]
        self.pdw_state = signals[Signals.Columns.PDW_STATE]
        self.pdw_sys_state = signals[Signals.Columns.PDW_SYSTEM_STATE]
        self.gear_state = signals[Signals.Columns.GEARBOX_STATE]
        self.epb_switch = signals[Signals.Columns.EPB_SWITCH]
        self.mute = signals[Signals.Columns.MUTE]
        self.dt_req = signals[Signals.Columns.DRV_TUBE]
        self.hmi_interract = signals[Signals.Columns.TAP_ON_HMI]
        self.apStatus = signals[Signals.Columns.AP_STATE]
        self.pdwFailureState = signals[Signals.Columns.PDW_FAILURE]
        self.wheelfl = signals[Signals.Columns.WHEEL_FL]
        self.wheelfr = signals[Signals.Columns.WHEEL_FR]
        self.wheelrl = signals[Signals.Columns.WHEEL_RL]
        self.wheelrr = signals[Signals.Columns.WHEEL_RR]

        self.stat_dist_fr_0 = signals[Signals.Columns.SECTOR_STAT_DISTANCEFR0]
        self.stat_dist_fr_1 = signals[Signals.Columns.SECTOR_STAT_DISTANCEFR1]
        self.stat_dist_fr_2 = signals[Signals.Columns.SECTOR_STAT_DISTANCEFR2]
        self.stat_dist_fr_3 = signals[Signals.Columns.SECTOR_STAT_DISTANCEFR3]
        self.dyn_dist_fr_0 = signals[Signals.Columns.SECTOR_DYN_DISTANCEFR0]
        self.dyn_dist_fr_1 = signals[Signals.Columns.SECTOR_DYN_DISTANCEFR1]
        self.dyn_dist_fr_2 = signals[Signals.Columns.SECTOR_DYN_DISTANCEFR2]
        self.dyn_dist_fr_3 = signals[Signals.Columns.SECTOR_DYN_DISTANCEFR3]

        self.stat_dist_ri_0 = signals[Signals.Columns.SECTOR_STAT_DISTANCERI0]
        self.stat_dist_ri_1 = signals[Signals.Columns.SECTOR_STAT_DISTANCERI1]
        self.stat_dist_ri_2 = signals[Signals.Columns.SECTOR_STAT_DISTANCERI2]
        self.stat_dist_ri_3 = signals[Signals.Columns.SECTOR_STAT_DISTANCERI3]
        self.dyn_dist_ri_0 = signals[Signals.Columns.SECTOR_DYN_DISTANCERI0]
        self.dyn_dist_ri_1 = signals[Signals.Columns.SECTOR_DYN_DISTANCERI1]
        self.dyn_dist_ri_2 = signals[Signals.Columns.SECTOR_DYN_DISTANCERI2]
        self.dyn_dist_ri_3 = signals[Signals.Columns.SECTOR_DYN_DISTANCERI3]

        self.stat_dist_re_0 = signals[Signals.Columns.SECTOR_STAT_DISTANCERE0]
        self.stat_dist_re_1 = signals[Signals.Columns.SECTOR_STAT_DISTANCERE1]
        self.stat_dist_re_2 = signals[Signals.Columns.SECTOR_STAT_DISTANCERE2]
        self.stat_dist_re_3 = signals[Signals.Columns.SECTOR_STAT_DISTANCERE3]
        self.dyn_dist_re_0 = signals[Signals.Columns.SECTOR_DYN_DISTANCERE0]
        self.dyn_dist_re_1 = signals[Signals.Columns.SECTOR_DYN_DISTANCERE1]
        self.dyn_dist_re_2 = signals[Signals.Columns.SECTOR_DYN_DISTANCERE2]
        self.dyn_dist_re_3 = signals[Signals.Columns.SECTOR_DYN_DISTANCERE3]

        self.stat_dist_le_0 = signals[Signals.Columns.SECTOR_STAT_DISTANCELE0]
        self.stat_dist_le_1 = signals[Signals.Columns.SECTOR_STAT_DISTANCELE1]
        self.stat_dist_le_2 = signals[Signals.Columns.SECTOR_STAT_DISTANCELE2]
        self.stat_dist_le_3 = signals[Signals.Columns.SECTOR_STAT_DISTANCELE3]
        self.dyn_dist_le_0 = signals[Signals.Columns.SECTOR_DYN_DISTANCELE0]
        self.dyn_dist_le_1 = signals[Signals.Columns.SECTOR_DYN_DISTANCELE1]
        self.dyn_dist_le_2 = signals[Signals.Columns.SECTOR_DYN_DISTANCELE2]
        self.dyn_dist_le_3 = signals[Signals.Columns.SECTOR_DYN_DISTANCELE3]

        global obj_dist_list

        obj_dist_list = [
            self.stat_dist_fr_0,
            self.stat_dist_fr_1,
            self.stat_dist_fr_2,
            self.stat_dist_fr_3,
            self.stat_dist_ri_0,
            self.stat_dist_ri_1,
            self.stat_dist_ri_2,
            self.stat_dist_ri_3,
            self.stat_dist_re_0,
            self.stat_dist_re_1,
            self.stat_dist_re_2,
            self.stat_dist_re_3,
            self.stat_dist_le_0,
            self.stat_dist_le_1,
            self.stat_dist_le_2,
            self.stat_dist_le_3,
            self.dyn_dist_fr_0,
            self.dyn_dist_fr_1,
            self.dyn_dist_fr_2,
            self.dyn_dist_fr_3,
            self.dyn_dist_ri_0,
            self.dyn_dist_ri_1,
            self.dyn_dist_ri_2,
            self.dyn_dist_ri_3,
            self.dyn_dist_re_0,
            self.dyn_dist_re_1,
            self.dyn_dist_re_2,
            self.dyn_dist_re_3,
            self.dyn_dist_le_0,
            self.dyn_dist_le_1,
            self.dyn_dist_le_2,
            self.dyn_dist_le_3,
        ]
        global obj_dist_signal_list

        obj_dist_signal_list = [
            signals_obj._properties[Signals.Columns.SECTOR_STAT_DISTANCEFR0],
            signals_obj._properties[Signals.Columns.SECTOR_STAT_DISTANCEFR1],
            signals_obj._properties[Signals.Columns.SECTOR_STAT_DISTANCEFR2],
            signals_obj._properties[Signals.Columns.SECTOR_STAT_DISTANCEFR3],
            signals_obj._properties[Signals.Columns.SECTOR_DYN_DISTANCEFR0],
            signals_obj._properties[Signals.Columns.SECTOR_DYN_DISTANCEFR1],
            signals_obj._properties[Signals.Columns.SECTOR_DYN_DISTANCEFR2],
            signals_obj._properties[Signals.Columns.SECTOR_DYN_DISTANCEFR3],
            signals_obj._properties[Signals.Columns.SECTOR_STAT_DISTANCERI0],
            signals_obj._properties[Signals.Columns.SECTOR_STAT_DISTANCERI1],
            signals_obj._properties[Signals.Columns.SECTOR_STAT_DISTANCERI2],
            signals_obj._properties[Signals.Columns.SECTOR_STAT_DISTANCERI3],
            signals_obj._properties[Signals.Columns.SECTOR_DYN_DISTANCERI0],
            signals_obj._properties[Signals.Columns.SECTOR_DYN_DISTANCERI1],
            signals_obj._properties[Signals.Columns.SECTOR_DYN_DISTANCERI2],
            signals_obj._properties[Signals.Columns.SECTOR_DYN_DISTANCERI3],
            signals_obj._properties[Signals.Columns.SECTOR_STAT_DISTANCERE0],
            signals_obj._properties[Signals.Columns.SECTOR_STAT_DISTANCERE1],
            signals_obj._properties[Signals.Columns.SECTOR_STAT_DISTANCERE2],
            signals_obj._properties[Signals.Columns.SECTOR_STAT_DISTANCERE3],
            signals_obj._properties[Signals.Columns.SECTOR_DYN_DISTANCERE0],
            signals_obj._properties[Signals.Columns.SECTOR_DYN_DISTANCERE1],
            signals_obj._properties[Signals.Columns.SECTOR_DYN_DISTANCERE2],
            signals_obj._properties[Signals.Columns.SECTOR_DYN_DISTANCERE3],
            signals_obj._properties[Signals.Columns.SECTOR_STAT_DISTANCELE0],
            signals_obj._properties[Signals.Columns.SECTOR_STAT_DISTANCELE1],
            signals_obj._properties[Signals.Columns.SECTOR_STAT_DISTANCELE2],
            signals_obj._properties[Signals.Columns.SECTOR_STAT_DISTANCELE3],
            signals_obj._properties[Signals.Columns.SECTOR_DYN_DISTANCELE0],
            signals_obj._properties[Signals.Columns.SECTOR_DYN_DISTANCELE1],
            signals_obj._properties[Signals.Columns.SECTOR_DYN_DISTANCELE2],
            signals_obj._properties[Signals.Columns.SECTOR_DYN_DISTANCELE3],
        ]

        # pdw state mask
        state_pdw_init_mask = self.pdw_state == pdwState.PDW_INT_STATE_INIT

        pdw_state_mask = [
            x for x in self.pdw_state if x != pdwState.PDW_INT_STATE_INIT and x != pdwState.PDW_INT_STATE_DEACT_INIT
        ]
        pdw_sys_state_mask = [x for x in self.pdw_sys_state if x != pdwSysState.PDW_INIT and x != pdwSysState.PDW_OFF]

        activate_method1 = activate_method2 = activate_method3 = "not activated"
        deactivation_method1 = "PDW error"
        pdwState_No_value1 = pdwState_No_value2 = pdwState_No_value3 = pdwState.PDW_INT_STATE_INIT
        pdwState_value1 = pdwState_value2 = pdwState_value3 = "PDW_INT_STATE_INIT"
        pdwSysState_No_value1 = pdwSysState_No_value2 = pdwSysState_No_value3 = pdwSysState.PDW_INIT
        pdwSysState_value1 = pdwSysState_value2 = pdwSysState_value3 = "PDW_INIT"
        pdw_state_trigger1 = pdw_SysState_trigger1 = pdw_state_trigger2 = pdw_SysState_trigger2 = pdw_state_trigger3 = (
            pdw_SysState_trigger3
        ) = "No trigger for state transition"
        verdict = FALSE
        idx = idx1 = idx2 = -1
        if state_pdw_init_mask.any():
            if not pdw_state_mask and not pdw_sys_state_mask:
                deactivation_method1 = "deactivated after initialization"
                pdwState_No_value1 = pdwState.PDW_INT_STATE_DEACT_INIT
                pdwState_value1 = "PDW_INT_STATE_DEACT_INIT"
                pdwSysState_No_value1 = pdwSysState.PDW_OFF
                verdict = DATA_NOK

                self.result.measured_result = FALSE
                signal_summary["AP.drvWarnStatus.pdwState_nu"] = (
                    f" PDW function was {deactivation_method1} state with pdwState = {pdwState_No_value1} ({pdwState_value1})."
                )
                signal_summary["AP.drvWarnStatus.pdwSystemState_nu"] = (
                    f" PDW function was {deactivation_method1} state with pdwSystemState = {pdwSysState_No_value1} ({pdwSysState_value1})."
                )
            else:

                state_act_btn_mask1 = pdw_state_mask[0] == pdwState.PDW_INT_STATE_ACT_BTN
                state_act_rgear_mask1 = pdw_state_mask[0] == pdwState.PDW_INT_STATE_ACT_R_GEAR
                state_act_ap_mask1 = pdw_state_mask[0] == pdwState.PDW_INT_STATE_ACT_AP
                state_act_auto_mask1 = pdw_state_mask[0] == pdwState.PDW_INT_STATE_ACT_AUTO
                state_act_rbk_mask1 = pdw_state_mask[0] == pdwState.PDW_INT_STATE_ACT_ROLLBACK
                state_deact_fail_mask1 = pdw_state_mask[0] == pdwState.PDW_INT_STATE_FAILURE

                if verdict == FALSE:
                    # First State change trigger
                    if state_deact_fail_mask1:
                        for i, element in enumerate(self.pdwFailureState):
                            if element == ap_PDWFailure.PDW_FAILURE_TRUE:
                                idx = i
                                break
                        if (
                            self.pdwFailureState.iat[idx] == ap_PDWFailure.PDW_FAILURE_TRUE
                            and self.pdwFailureState.iat[idx + delay] == ap_PDWFailure.PDW_FAILURE_TRUE
                            and self.pdw_state.iat[idx + delay] == pdwState.PDW_INT_STATE_FAILURE
                            and self.pdw_sys_state.iat[idx + delay] == pdwSysState.PDW_FAILURE
                        ):  # validate if PDW is in failure
                            activate_method1 = "deactivated by failure"
                            pdwState_No_value1 = pdwState.PDW_INT_STATE_FAILURE
                            pdwState_value1 = "PDW_INT_STATE_FAILURE"
                            pdwSysState_No_value1 = pdwSysState.PDW_FAILURE
                            pdwSysState_value1 = "PDW_FAILURE"
                            verdict = DATA_NOK
                            pdw_state_trigger1 = "First trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger1 = "First trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            signal_summary["AP.pdwFailure_nu"] = (
                                f"PDW failure present with value {int(self.pdwFailureState.iat[idx])} (0 for False and 1 for True )"
                            )
                            fail_deact = go.Scatter(
                                x=self.ap_time,
                                y=self.pdwFailureState,
                                mode="lines",
                                name=signals_obj._properties[Signals.Columns.PDW_FAILURE],
                            )
                    elif state_act_btn_mask1:
                        for i, element in enumerate(self.hmi_interract):
                            if element == pdw_hmi_interact.TAP_ON_PDC:
                                idx = i
                                break
                        if (
                            self.hmi_interract.iat[idx] == pdw_hmi_interact.TAP_ON_PDC
                            and self.pdw_state.iat[idx + delay] == pdwState.PDW_INT_STATE_ACT_BTN
                            and self.pdw_sys_state.iat[idx + delay] == pdwSysState.PDW_ACTIVATED_BY_BUTTON
                        ):  # validate if pdw button is pressed
                            activate_method1 = "activated by button"
                            pdwState_No_value1 = pdwState.PDW_INT_STATE_ACT_BTN
                            pdwState_value1 = "PDW_INT_STATE_ACT_BTN"
                            pdwSysState_No_value1 = pdwSysState.PDW_ACTIVATED_BY_BUTTON
                            pdwSysState_value1 = "PDW_ACTIVATED_BY_BUTTON"
                            verdict = TRUE
                            pdw_state_trigger1 = "First trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger1 = "First trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            signal_summary["First trigger for signal: AP.hmiOutputPort.userActionHeadUnit_nu"] = (
                                f"PDW button pressed with value TAP_ON_PDC = {int(self.hmi_interract.iat[idx])}"
                            )
                            button_press = go.Scatter(
                                x=self.ap_time,
                                y=self.hmi_interract,
                                mode="lines",
                                name=signals_obj._properties[Signals.Columns.TAP_ON_HMI],
                            )
                    elif state_act_ap_mask1:
                        for i, element in enumerate(self.apStatus):
                            if element == apStateVal.AP_AVG_ACTIVE_IN:
                                idx = i
                                break
                        if (
                            self.pdw_state.iat[idx] == pdwState.PDW_INT_STATE_ACT_AP
                            and self.apStatus.iat[idx] == apStateVal.AP_AVG_ACTIVE_IN
                            and self.pdw_sys_state.iat[idx] == pdwSysState.PDW_ACTIVATED_BY_BUTTON
                            and self.hmi_interract.iat[idx] == pdw_hmi_interact.TAP_ON_START_PARKING
                        ):  # validate if automated parking button was pressed
                            activate_method1 = "activated by automated parking"
                            pdwState_value1 = "PDW_INT_STATE_ACT_AP"
                            pdwState_No_value1 = pdwState.PDW_INT_STATE_ACT_AP
                            pdwSysState_No_value1 = pdwSysState.PDW_ACTIVATED_BY_BUTTON
                            pdwSysState_value1 = "PDW_ACTIVATED_BY_BUTTON"
                            pdw_state_trigger1 = "First trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger1 = "First trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            verdict = TRUE
                            signal_summary["AP.hmiOutputPort.userActionHeadUnit_nu"] = (
                                f"Automated parking started with value TAP_ON_SART_PARKING = {int(self.hmi_interract.iat[idx])}"
                            )
                            signal_summary["AP.planningCtrlPort.apStates"] = (
                                f"Automated parking stade apStates = {int(self.apStatus.iat[idx])} (AP_AVG_ACTIVE_IN)"
                            )
                            apState_figure = go.Scatter(
                                x=self.ap_time,
                                y=self.apStatus,
                                mode="lines",
                                name=signals_obj._properties[Signals.Columns.AP_STATE],
                            )
                    elif state_act_rgear_mask1:
                        for i, element in enumerate(self.gear_state):
                            if element == gearPosition.GEAR_R:
                                idx = i
                                break
                        if (
                            self.gear_state.iat[idx] == gearPosition.GEAR_R
                            and self.pdw_state.iat[idx + delay] == pdwState.PDW_INT_STATE_ACT_R_GEAR
                            and self.pdw_sys_state.iat[idx + delay] == pdwSysState.PDW_ACTIVATED_BY_R_GEAR
                        ):  # validate if Reverse gear was engaged
                            activate_method1 = "activated by reverse gear"
                            pdwState_No_value1 = pdwState.PDW_INT_STATE_ACT_R_GEAR
                            pdwState_value1 = "PDW_INT_STATE_ACT_R_GEAR"
                            pdwSysState_No_value1 = pdwSysState.PDW_ACTIVATED_BY_R_GEAR
                            pdwSysState_value1 = "PDW_ACTIVATED_BY_R_GEAR"
                            pdw_state_trigger1 = "First trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger1 = "First trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            verdict = TRUE
                            signal_summary["AP.odoInputPort.odoSigFcanPort.gearboxCtrlStatus.gearCur_n"] = (
                                f"Gear in reverse with value GEAR_R = {int(self.gear_state.iat[idx])}"
                            )
                            rg_trace = go.Scatter(
                                x=self.ap_time,
                                y=self.gear_state,
                                mode="lines",
                                name=signals_obj._properties[Signals.Columns.GEARBOX_STATE],
                            )
                    elif state_act_rbk_mask1:
                        for i, element in enumerate(self.pdw_state):
                            if element == pdwState.PDW_INT_STATE_ACT_ROLLBACK:
                                idx = i
                                break
                        if (
                            self.dt_req.iat[idx] == drvTubeDisplay.PDC_DRV_TUBE_REAR
                            and self.pdw_state.iat[idx] == pdwState.PDW_INT_STATE_ACT_ROLLBACK
                            and self.pdw_sys_state.iat[idx] == pdwSysState.PDW_AUTOMATICALLY_ACTIVATED
                            and self.velocity.iat[idx] >= speed_threshold.SPEED_THRESHOLD_LO
                            and self.wheelfl.iat[idx]
                            == self.wheelfr.iat[idx]
                            == self.wheelrl.iat[idx]
                            == self.wheelrr.iat[idx]
                            == wheel_direction.WHEEL_DIRECTION_REVERSE
                        ):  # validate if vehicle rolls backward with driving tube display in rear
                            activate_method1 = "activated by rollback"
                            pdwState_No_value1 = pdwState.PDW_INT_STATE_ACT_ROLLBACK
                            pdwState_value1 = "PDW_INT_STATE_ACT_ROLLBACK"
                            pdwSysState_No_value1 = pdwSysState.PDW_AUTOMATICALLY_ACTIVATED
                            pdwSysState_value1 = "PDW_AUTOMATICALLY_ACTIVATED"
                            pdw_state_trigger1 = "First trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger1 = "First trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            verdict = TRUE
                            signal_summary["Car.v"] = (
                                f"Ego vehicle speed while rolling backward {round(self.velocity.iat[idx], 3)} m/s"
                            )
                            signal_summary["AP.pdcpDrivingTubePort.drvTubeDisplay_nu"] = (
                                f"Driving tube display PDC_DRV_TUBE_REAR = {int(self.dt_req.iat[idx])}"
                            )
                    elif state_act_auto_mask1:
                        for i, element in enumerate(self.pdw_state):
                            if element == pdwState.PDW_INT_STATE_ACT_AUTO:
                                idx = i
                                break

                        for i in range(
                            len(obj_dist_list)
                        ):  # check if an obstacle is present in any of the sectors around the car
                            if (
                                obj_dist_list[i].iat[idx] < pdw_sector_length.PDW_SECTOR_LENGTH
                                and self.pdw_state.iat[idx] == pdwState.PDW_INT_STATE_ACT_AUTO
                                and self.pdw_sys_state.iat[idx] == pdwSysState.PDW_AUTOMATICALLY_ACTIVATED
                            ):
                                activate_method1 = "automatically activated"
                                pdwState_No_value1 = pdwState.PDW_INT_STATE_ACT_AUTO
                                pdwState_value1 = "PDW_INT_STATE_ACT_AUTO"
                                pdwSysState_No_value1 = pdwSysState.PDW_AUTOMATICALLY_ACTIVATED
                                pdwSysState_value1 = "PDW_AUTOMATICALLY_ACTIVATED"
                                pdw_state_trigger1 = "First trigger for signal: AP.drvWarnStatus.pdwState_nu"
                                pdw_SysState_trigger1 = "First trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                                verdict = TRUE
                                signal_summary[f"{obj_dist_signal_list[i]}"] = (
                                    f"Smallest distance detected towards object = {round(obj_dist_list[i].iat[idx], 3)} m"
                                )
                                auto_obj_dist = go.Scatter(
                                    x=self.ap_time, y=obj_dist_list[i], mode="lines", name=obj_dist_signal_list[i]
                                )

                if verdict == TRUE:
                    verdict = FALSE
                    # check for PDW State transition Second trigger
                    for i, element in enumerate(self.pdw_state):
                        if i > (idx + delay) and element != self.pdw_state.iat[idx + delay]:
                            idx1 = i
                            break
                    if int(self.pdw_state.iat[idx1]) == pdwState.PDW_INT_STATE_FAILURE:
                        for i, element in enumerate(self.pdwFailureState):
                            if element == ap_PDWFailure.PDW_FAILURE_TRUE:
                                idx = i
                                break
                        if (
                            self.pdwFailureState.iat[idx1] == ap_PDWFailure.PDW_FAILURE_TRUE
                            and self.pdwFailureState.iat[idx1 + delay] == ap_PDWFailure.PDW_FAILURE_TRUE
                            and self.pdw_state.iat[idx1 + delay] == pdwState.PDW_INT_STATE_FAILURE
                            and self.pdw_sys_state.iat[idx1 + delay] == pdwSysState.PDW_FAILURE
                        ):  # validate if PDW is in failure
                            activate_method2 = "deactivated by failure"
                            pdwState_No_value2 = pdwState.PDW_INT_STATE_FAILURE
                            pdwState_value2 = "PDW_INT_STATE_FAILURE"
                            pdwSysState_No_value2 = pdwSysState.PDW_FAILURE
                            pdwSysState_value2 = "PDW_FAILURE"
                            verdict = TRUE
                            pdw_state_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            signal_summary["AP.pdwFailure_nu"] = (
                                f"PDW failure present with value {int(self.pdwFailureState.iat[idx1])} (0 for False and 1 for True )"
                            )
                            fail_deact = go.Scatter(
                                x=self.ap_time,
                                y=self.pdwFailureState,
                                mode="lines",
                                name=signals_obj._properties[Signals.Columns.PDW_FAILURE],
                            )
                    elif (
                        int(self.pdw_state.iat[idx1]) == pdwState.PDW_INT_STATE_DEACT_SPEED
                        and self.velocity.iat[idx1] >= (tata_overspeed_deact / speed_converter)
                        and self.velocity.iat[idx1] <= speed_threshold.SPEED_THRESHOLD_HI
                    ):
                        for i, element in enumerate(self.velocity):
                            if i > (idx + delay) and element >= (tata_overspeed_deact / speed_converter):
                                idx1 = i
                                break
                        if (
                            (self.velocity.iat[idx1]) >= overspeed_deact / speed_converter
                            and self.pdw_state.iat[idx1 + delay] == pdwState.PDW_INT_STATE_DEACT_SPEED
                            and self.pdw_sys_state.iat[idx1 + delay] == pdwSysState.PDW_OFF
                        ):  # validate if vehicle speed is greater than speed threshold
                            activate_method2 = "deactivated by speed"
                            pdwState_No_value2 = pdwState.PDW_INT_STATE_DEACT_SPEED
                            pdwState_value2 = "PDW_INT_STATE_DEACT_SPEED"
                            pdwSysState_No_value2 = pdwSysState.PDW_OFF
                            pdwSysState_value2 = "PDW_OFF"
                            pdw_state_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            verdict = TRUE
                            signal_summary["Car.v"] = f"Ego vehicle sped {round(self.velocity.iat[idx1], 3)} m/s"
                        # in case of deactivation by speed over 20 km/h
                    elif (
                        int(self.pdw_state.iat[idx1]) == pdwState.PDW_INT_STATE_DEACT_SPEED
                        and self.velocity.iat[idx1] >= speed_threshold.SPEED_THRESHOLD_HI
                    ):
                        for i, element in enumerate(self.velocity):
                            if i > (idx + delay) and element >= speed_threshold.SPEED_THRESHOLD_HI:
                                idx1 = i
                                break
                        if (
                            (self.velocity.iat[idx1]) >= overspeed_deact / speed_converter
                            and self.pdw_state.iat[idx1 + delay] == pdwState.PDW_INT_STATE_DEACT_SPEED
                            and self.pdw_sys_state.iat[idx1 + delay] == pdwSysState.PDW_OFF
                        ):  # validate if vehicle speed is greater than speed threshold
                            activate_method2 = "deactivated by speed"
                            pdwState_No_value2 = pdwState.PDW_INT_STATE_DEACT_SPEED
                            pdwState_value2 = "PDW_INT_STATE_DEACT_SPEED"
                            pdwSysState_No_value2 = pdwSysState.PDW_OFF
                            pdwSysState_value2 = "PDW_OFF"
                            pdw_state_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            verdict = TRUE
                            signal_summary["Car.v"] = f"Ego vehicle sped {round(self.velocity.iat[idx1], 3)} m/s"
                    elif int(self.pdw_state.iat[idx1]) == pdwState.PDW_INT_STATE_DEACT_P_GEAR:
                        for i, element in enumerate(self.gear_state):
                            if i > (idx + delay) and element == gearPosition.GEAR_P:
                                idx1 = i
                                break
                        if (
                            self.gear_state.iat[idx1] == gearPosition.GEAR_P
                            and self.pdw_state.iat[idx1 + delay] == pdwState.PDW_INT_STATE_DEACT_P_GEAR
                            and self.pdw_sys_state.iat[idx1 + delay] == pdwSysState.PDW_OFF
                        ):  # validate if parking gear was engaged
                            activate_method2 = "deactivated by parking gear"
                            pdwState_No_value2 = pdwState.PDW_INT_STATE_DEACT_P_GEAR
                            pdwState_value2 = "PDW_INT_STATE_DEACT_P_GEAR"
                            pdwSysState_No_value2 = pdwSysState.PDW_OFF
                            pdwSysState_value2 = "PDW_OFF"
                            pdw_state_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            verdict = TRUE
                            signal_summary["AP.odoInputPort.odoSigFcanPort.gearboxCtrlStatus.gearCur_n"] = (
                                f"Gear in reverse with value GEAR_P = {int(self.gear_state.iat[idx1])}"
                            )
                    elif int(self.pdw_state.iat[idx1]) == pdwState.PDW_INT_STATE_DEACT_EPB:
                        for i, element in enumerate(self.epb_switch):
                            if i > (idx + delay) and element == epbSwitch.EPB_ON:
                                idx1 = i
                                break
                        if (
                            self.epb_switch.iat[idx1] == epbSwitch.EPB_ON
                            and self.pdw_state.iat[idx1 + delay] == pdwState.PDW_INT_STATE_DEACT_EPB
                            and self.pdw_sys_state.iat[idx1 + delay] == pdwSysState.PDW_OFF
                        ):  # validate if electronic parking brake was engaged
                            activate_method2 = "deactivated by EPB"
                            pdwState_No_value2 = pdwState.PDW_INT_STATE_DEACT_EPB
                            pdwState_value2 = "PDW_INT_STATE_DEACT_EPB"
                            pdwSysState_No_value2 = pdwSysState.PDW_OFF
                            pdwSysState_value2 = "PDW_OFF"
                            pdw_state_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            verdict = TRUE
                            signal_summary["DM.BrakePark"] = (
                                f"Electornic parking brake active with value EPB_ON = {int(self.epb_switch.iat[idx1])}"
                            )
                    elif int(self.pdw_state.iat[idx1]) == pdwState.PDW_INT_STATE_DEACT_AP_FIN:
                        for i, element in enumerate(self.apStatus):
                            if i > (idx + delay) and element == apStateVal.AP_AVG_FINISHED:
                                idx1 = i
                                break
                        if (
                            self.apStatus.iat[idx1] == apStateVal.AP_AVG_FINISHED
                            and self.pdw_state.iat[idx1 + delay] == pdwState.PDW_INT_STATE_DEACT_AP_FIN
                            and self.pdw_sys_state.iat[idx1 + delay] == pdwSysState.PDW_OFF
                        ):  # validate if automated parking finished
                            activate_method2 = "deactivated by automated parking finish"
                            pdwState_No_value2 = pdwState.PDW_INT_STATE_DEACT_AP_FIN
                            pdwState_value2 = "PDW_INT_STATE_DEACT_AP_FIN"
                            pdwSysState_No_value2 = pdwSysState.PDW_OFF
                            pdwSysState_value2 = "PDW_OFF"
                            pdw_state_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            verdict = TRUE
                            signal_summary["AP.planningCtrlPort.apStates"] = (
                                f"Automated parking finished apStates = {int(self.apStatus.iat[idx1])} (AP_AVG_FINISHED)"
                            )
                            apState_figure = go.Scatter(
                                x=self.ap_time,
                                y=self.apStatus,
                                mode="lines",
                                name=signals_obj._properties[Signals.Columns.AP_STATE],
                            )
                    elif int(self.pdw_state.iat[idx1]) == pdwState.PDW_INT_STATE_DEACT_BTN:
                        for i, element in enumerate(self.hmi_interract):
                            if i > (idx + delay) and element == pdw_hmi_interact.TAP_ON_PDC:
                                idx1 = i
                                break
                        if (
                            self.hmi_interract.iat[idx1] == pdw_hmi_interact.TAP_ON_PDC
                            and self.pdw_state.iat[idx1 + delay] == pdwState.PDW_INT_STATE_DEACT_BTN
                            and self.pdw_sys_state.iat[idx1 + delay] == pdwSysState.PDW_OFF
                        ):  # validate if pdw button is pressed
                            activate_method2 = "deactivated by button"
                            pdwState_No_value2 = pdwState.PDW_INT_STATE_DEACT_BTN
                            pdwState_value2 = "PDW_INT_STATE_DEACT_BTN"
                            pdwSysState_No_value2 = pdwSysState.PDW_OFF
                            pdwSysState_value2 = "PDW_OFF"
                            pdw_state_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            verdict = TRUE

                            signal_summary["AP.hmiOutputPort.userActionHeadUnit_nu"] = (
                                f"PDW button pressed with value TAP_ON_PDC = {int(self.hmi_interract.iat[idx1])}"
                            )
                            button_press = go.Scatter(
                                x=self.ap_time,
                                y=self.hmi_interract,
                                mode="lines",
                                name=signals_obj._properties[Signals.Columns.TAP_ON_HMI],
                            )
                    elif int(self.pdw_state.iat[idx1]) == pdwState.PDW_INT_STATE_ACT_BTN:
                        for i, element in enumerate(self.hmi_interract):
                            if i > (idx + delay) and element == pdw_hmi_interact.TAP_ON_PDC:
                                idx1 = i
                                break
                        if (
                            self.hmi_interract.iat[idx1] == pdw_hmi_interact.TAP_ON_PDC
                            and self.pdw_state.iat[idx1 + delay] == pdwState.PDW_INT_STATE_ACT_BTN
                            and self.pdw_sys_state.iat[idx1 + delay] == pdwSysState.PDW_ACTIVATED_BY_BUTTON
                        ):  # validate if pdw button is pressed
                            activate_method2 = "activated by button"
                            pdwState_No_value2 = pdwState.PDW_INT_STATE_ACT_BTN
                            pdwState_value2 = "PDW_INT_STATE_ACT_BTN"
                            pdwSysState_No_value2 = pdwSysState.PDW_ACTIVATED_BY_BUTTON
                            pdwSysState_value2 = "PDW_ACTIVATED_BY_BUTTON"
                            pdw_state_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            verdict = TRUE
                            signal_summary["Second trigger for signal: AP.hmiOutputPort.userActionHeadUnit_nu"] = (
                                f"PDW button pressed with value TAP_ON_PDC = {int(self.hmi_interract.iat[idx1])}"
                            )
                            button_press = go.Scatter(
                                x=self.ap_time,
                                y=self.hmi_interract,
                                mode="lines",
                                name=signals_obj._properties[Signals.Columns.TAP_ON_HMI],
                            )
                    elif int(self.pdw_state.iat[idx1]) == pdwState.PDW_INT_STATE_ACT_AUTO:
                        for i, element in enumerate(self.pdw_state):
                            if i > (idx + delay) and element == pdwState.PDW_INT_STATE_ACT_AUTO:
                                idx1 = i
                                break

                        for i in range(
                            len(obj_dist_list)
                        ):  # check if an obstacle is present in any of the sectors around the car
                            if (
                                obj_dist_list[i].iat[idx1] < pdw_sector_length.PDW_SECTOR_LENGTH
                                and self.pdw_state.iat[idx1] == pdwState.PDW_INT_STATE_ACT_AUTO
                                and self.pdw_sys_state.iat[idx1] == pdwSysState.PDW_AUTOMATICALLY_ACTIVATED
                            ):
                                activate_method2 = "automatically activated"
                                pdwState_No_value2 = pdwState.PDW_INT_STATE_ACT_AUTO
                                pdwState_value2 = "PDW_INT_STATE_ACT_AUTO"
                                pdwSysState_No_value2 = pdwSysState.PDW_AUTOMATICALLY_ACTIVATED
                                pdwSysState_value2 = "PDW_AUTOMATICALLY_ACTIVATED"
                                pdw_state_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwState_nu"
                                pdw_SysState_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                                verdict = TRUE
                                signal_summary[f"{obj_dist_signal_list[i]}"] = (
                                    f"Smallest distance detected towards object = {round(obj_dist_list[i].iat[idx1], 3)} m"
                                )
                                auto_obj_dist = go.Scatter(
                                    x=self.ap_time, y=obj_dist_list[i], mode="lines", name=obj_dist_signal_list[i]
                                )
                    elif int(self.pdw_state.iat[idx1]) == pdwState.PDW_INT_STATE_ACT_R_GEAR:
                        for i, element in enumerate(self.gear_state):
                            if i > (idx + delay) and element == gearPosition.GEAR_R:
                                idx1 = i
                                break
                        if (
                            self.gear_state.iat[idx1] == gearPosition.GEAR_R
                            and self.pdw_state.iat[idx1 + delay] == pdwState.PDW_INT_STATE_ACT_R_GEAR
                            and self.pdw_sys_state.iat[idx1 + delay] == pdwSysState.PDW_ACTIVATED_BY_R_GEAR
                        ):  # validate if Reverse gear was engaged
                            activate_method2 = "activated by reverse gear"
                            pdwState_No_value2 = pdwState.PDW_INT_STATE_ACT_R_GEAR
                            pdwState_value2 = "PDW_INT_STATE_ACT_R_GEAR"
                            pdwSysState_No_value2 = pdwSysState.PDW_ACTIVATED_BY_R_GEAR
                            pdwSysState_value2 = "PDW_ACTIVATED_BY_R_GEAR"
                            pdw_state_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            verdict = TRUE
                            signal_summary["AP.odoInputPort.odoSigFcanPort.gearboxCtrlStatus.gearCur_n"] = (
                                f"Gear in reverse with value GEAR_R = {int(self.gear_state.iat[idx1])}"
                            )
                            rg_trace = go.Scatter(
                                x=self.ap_time,
                                y=self.gear_state,
                                mode="lines",
                                name=signals_obj._properties[Signals.Columns.GEARBOX_STATE],
                            )
                    elif int(self.pdw_state.iat[idx1]) == pdwState.PDW_INT_STATE_ACT_AP:
                        for i, element in enumerate(self.apStatus):
                            if i > (idx + delay) and element == apStateVal.AP_AVG_ACTIVE_IN:
                                idx1 = i
                                break
                        if (
                            self.pdw_state.iat[idx1] == pdwState.PDW_INT_STATE_ACT_AP
                            and self.apStatus.iat[idx1] == apStateVal.AP_AVG_ACTIVE_IN
                            and self.pdw_sys_state.iat[idx1] == pdwSysState.PDW_ACTIVATED_BY_BUTTON
                            and self.hmi_interract.iat[idx1] == pdw_hmi_interact.TAP_ON_START_PARKING
                        ):  # validate if automated parking button was pressed
                            activate_method2 = "activated by automated parking"
                            pdwState_value2 = "PDW_INT_STATE_ACT_AP"
                            pdwState_No_value2 = pdwState.PDW_INT_STATE_ACT_AP
                            pdwSysState_No_value2 = pdwSysState.PDW_ACTIVATED_BY_BUTTON
                            pdwSysState_value2 = "PDW_ACTIVATED_BY_BUTTON"
                            pdw_state_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            verdict = TRUE
                            signal_summary["AP.hmiOutputPort.userActionHeadUnit_nu"] = (
                                f"Automated parking started with value TAP_ON_SART_PARKING = {int(self.hmi_interract.iat[idx1])}"
                            )
                            signal_summary["AP.planningCtrlPort.apStates"] = (
                                f"Automated parking stade apStates = {int(self.apStatus.iat[idx1])} (AP_AVG_ACTIVE_IN)"
                            )
                            apState_figure = go.Scatter(
                                x=self.ap_time,
                                y=self.apStatus,
                                mode="lines",
                                name=signals_obj._properties[Signals.Columns.AP_STATE],
                            )
                    elif int(self.pdw_state.iat[idx1]) == pdwState.PDW_INT_STATE_ACT_ROLLBACK:
                        for i, element in enumerate(self.pdw_state):
                            if i > (idx + delay) and element == pdwState.PDW_INT_STATE_ACT_ROLLBACK:
                                idx1 = i
                                break
                        if (
                            self.dt_req.iat[idx1] == drvTubeDisplay.PDC_DRV_TUBE_REAR
                            and self.pdw_state.iat[idx1] == pdwState.PDW_INT_STATE_ACT_ROLLBACK
                            and self.pdw_sys_state.iat[idx1] == pdwSysState.PDW_AUTOMATICALLY_ACTIVATED
                            and self.velocity.iat[idx1] >= speed_threshold.SPEED_THRESHOLD_LO
                            and self.wheelfl.iat[idx1]
                            == self.wheelfr.iat[idx1]
                            == self.wheelrl.iat[idx1]
                            == self.wheelrr.iat[idx1]
                            == wheel_direction.WHEEL_DIRECTION_REVERSE
                        ):  # validate if vehicle rolls backward with driving tube display in rear
                            activate_method2 = "activated by rollback"
                            pdwState_No_value2 = pdwState.PDW_INT_STATE_ACT_ROLLBACK
                            pdwState_value2 = "PDW_INT_STATE_ACT_ROLLBACK"
                            pdwSysState_No_value2 = pdwSysState.PDW_AUTOMATICALLY_ACTIVATED
                            pdwSysState_value2 = "PDW_AUTOMATICALLY_ACTIVATED"
                            pdw_state_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger2 = "Second trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            verdict = TRUE
                            signal_summary["Car.v"] = (
                                f"Ego vehicle speed while rolling backward {round(self.velocity.iat[idx1], 3)} m/s"
                            )
                            signal_summary["AP.pdcpDrivingTubePort.drvTubeDisplay_nu"] = (
                                f"Driving tube display PDC_DRV_TUBE_REAR = {int(self.dt_req.iat[idx1])}"
                            )

                if verdict == TRUE:
                    verdict = FALSE
                    # Check for Third PDW State transition trigger
                    for i, element in enumerate(self.pdw_state):
                        if i > (idx1 + delay) and element != self.pdw_state.iat[idx1 + delay]:
                            idx2 = i
                            break
                    if int(self.pdw_state.iat[idx2]) == pdwState.PDW_INT_STATE_FAILURE:
                        for i, element in enumerate(self.pdwFailureState):
                            if i > (idx1 + delay) and element == ap_PDWFailure.PDW_FAILURE_TRUE:
                                idx2 = i
                                break
                        if (
                            self.pdwFailureState.iat[idx2 + delay] == ap_PDWFailure.PDW_FAILURE_TRUE
                            and self.pdw_state.iat[idx2 + delay] == pdwState.PDW_INT_STATE_FAILURE
                            and self.pdw_sys_state.iat[idx2 + delay] == pdwSysState.PDW_FAILURE
                        ):  # validate if PDW is in failure
                            activate_method3 = "deactivated by failure"
                            pdwState_No_value3 = pdwState.PDW_INT_STATE_FAILURE
                            pdwState_value3 = "PDW_INT_STATE_FAILURE"
                            pdwSysState_No_value3 = pdwSysState.PDW_FAILURE
                            pdwSysState_value3 = "PDW_FAILURE"
                            verdict = TRUE
                            pdw_state_trigger3 = "Third trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger3 = "Third trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            signal_summary["AP.pdwFailure_nu"] = (
                                f"PDW failure present with value {int(self.pdwFailureState.iat[idx2])} (0 for False and 1 for True )"
                            )
                            fail_deact = go.Scatter(
                                x=self.ap_time,
                                y=self.pdwFailureState,
                                mode="lines",
                                name=signals_obj._properties[Signals.Columns.PDW_FAILURE],
                            )
                    elif int(self.pdw_state.iat[idx2]) == pdwState.PDW_INT_STATE_DEACT_INIT:
                        for i, element in enumerate(self.pdw_state):
                            if i > (idx1 + delay) and element == pdwState.PDW_INT_STATE_DEACT_INIT:
                                idx2 = i
                                break
                        if (
                            self.pdwFailureState.iat[idx2] == ap_PDWFailure.PDW_FAILURE_FALSE
                            and self.pdw_state.iat[idx2 + delay] == pdwState.PDW_INT_STATE_DEACT_INIT
                            and self.pdw_sys_state.iat[idx2 + delay] == pdwSysState.PDW_OFF
                        ):  # validate if PDW is in failure
                            activate_method3 = "deactivated by failure"
                            pdwState_No_value3 = pdwState.PDW_INT_STATE_DEACT_INIT
                            pdwState_value3 = "PDW_INT_STATE_DEACT_INIT"
                            pdwSysState_No_value3 = pdwSysState.PDW_OFF
                            pdwSysState_value3 = "PDW_OFF"
                            verdict = TRUE
                            pdw_state_trigger3 = "Third trigger for signal: AP.drvWarnStatus.pdwState_nu"
                            pdw_SysState_trigger3 = "Third trigger for signal: AP.drvWarnStatus.pdwSystemState_nu"
                            signal_summary["AP.pdwFailure_nu"] = (
                                f"PDW failure present with value {int(self.pdwFailureState.iat[idx2])} (0 for False and 1 for True )"
                            )
                            fail_deact = go.Scatter(
                                x=self.ap_time,
                                y=self.pdwFailureState,
                                mode="lines",
                                name=signals_obj._properties[Signals.Columns.PDW_FAILURE],
                            )

                if verdict == DATA_NOK:
                    self.result.measured_result = FALSE
                else:
                    self.result.measured_result = TRUE if verdict == TRUE else FALSE

                signal_summary[pdw_state_trigger1] = (
                    f" PDW function is {activate_method1} state with pdwState = {pdwState_No_value1} ({pdwState_value1}) ."
                )
                signal_summary[pdw_SysState_trigger1] = (
                    f" PDW function is {activate_method1} state with pdwSystemState = {pdwSysState_No_value1} ({pdwSysState_value1})."
                )
                signal_summary[pdw_state_trigger2] = (
                    f" PDW function is {activate_method2} state with pdwState = {pdwState_No_value2} ({pdwState_value2}) ."
                )
                signal_summary[pdw_SysState_trigger2] = (
                    f" PDW function is {activate_method2} state with pdwSystemState = {pdwSysState_No_value2} ({pdwSysState_value2})."
                )
                signal_summary[pdw_state_trigger3] = (
                    f" PDW function is {activate_method3} state with pdwState = {pdwState_No_value3} ({pdwState_value3}) ."
                )
                signal_summary[pdw_SysState_trigger3] = (
                    f" PDW function is {activate_method3} state with pdwSystemState = {pdwSysState_No_value3} ({pdwSysState_value3})."
                )

        remark = " ".join(
            "This test step verifies PDW activation/deactivation reason "
            'monitoring the signal "AP.drvWarnStatus.pdwSystemState_nu".'.split()
        )
        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        # add the needed signals in the plot

        fig.add_trace(
            go.Scatter(
                x=self.ap_time, y=self.pdw_state, mode="lines", name=signals_obj._properties[Signals.Columns.PDW_STATE]
            )
        )

        fig.add_trace(
            go.Scatter(
                x=self.ap_time,
                y=self.pdw_sys_state,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.PDW_SYSTEM_STATE],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=self.ap_time, y=self.velocity, mode="lines", name=signals_obj._properties[Signals.Columns.VELOCITY]
            )
        )
        fig.add_trace(
            go.Scatter(
                x=self.ap_time,
                y=self.gear_state,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.GEARBOX_STATE],
            )
        )
        fig.add_trace(
            go.Scatter(x=self.ap_time, y=self.mute, mode="lines", name=signals_obj._properties[Signals.Columns.MUTE])
        )
        fig.add_trace(
            go.Scatter(
                x=self.ap_time, y=self.dt_req, mode="lines", name=signals_obj._properties[Signals.Columns.DRV_TUBE]
            )
        )
        if (
            activate_method1 == "automatically activated"
            or activate_method2 == "automatically activated"
            or activate_method3 == "automatically activated"
        ):
            fig.add_trace(auto_obj_dist)
        if (
            activate_method1 == "activated by button"
            or activate_method2 == "deactivated by button"
            or activate_method3 == "activated by button"
        ):
            fig.add_trace(button_press)
        if (
            activate_method1 == "activated by automated parking"
            or activate_method2 == "activated by automated parking"
            or activate_method3 == "activated by automated parking"
        ):
            fig.add_trace(apState_figure)
        if (
            activate_method1 == "activated by reverse gear"
            or activate_method2 == "activated by reverse gear"
            or activate_method3 == "activated by reverse gear"
        ):
            fig.add_trace(rg_trace)
        if (
            activate_method1 == "deactivated by failure"
            or activate_method2 == "deactivated by failure"
            or activate_method3 == "deactivated by failure"
        ):
            fig.add_trace(fail_deact)

        fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
        fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@testcase_definition(
    name="PDW State Machine Failure Three",
    description=("This test case verifies if PDW goes to fail state if a failure is present."),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class PDWFailStateMachineThree(TestCase):
    """Example test case."""  # required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # required docstring
        return [
            TestStepPDW,
        ]  # in this list all the needed test steps are included
