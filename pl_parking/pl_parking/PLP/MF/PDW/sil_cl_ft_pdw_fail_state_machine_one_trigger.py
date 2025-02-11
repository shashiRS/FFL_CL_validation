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
ALIAS = "PDW_F_STATE_ONE"

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
    name="PDW Fail State Machine one trigger",  # this would be shown as a test step name in html report
    description=(
        "This test step evaluates PDW at initialization state and checks if a failure is present."
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

        # pdw state mask
        state_pdw_init_mask = self.pdw_state == pdwState.PDW_INT_STATE_INIT

        pdw_state_mask = [
            x for x in self.pdw_state if x != pdwState.PDW_INT_STATE_INIT and x != pdwState.PDW_INT_STATE_DEACT_INIT
        ]
        pdw_sys_state_mask = [x for x in self.pdw_sys_state if x != pdwSysState.PDW_INIT and x != pdwSysState.PDW_OFF]

        activate_method1 = "not activated"
        deactivation_method1 = "PDW error"
        pdwState_No_value1 = pdwState.PDW_INT_STATE_INIT
        pdwState_value1 = "PDW_INT_STATE_INIT"
        pdwSysState_No_value1 = pdwSysState.PDW_INIT
        pdwSysState_value1 = "PDW_INIT"
        pdw_state_trigger1 = pdw_SysState_trigger1 = "No trigger for state transition"
        verdict = FALSE
        idx = -1
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
                            verdict = TRUE
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
                else:
                    verdict = DATA_NOK

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
        if activate_method1 == "deactivated by failure":
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
    name="PDW Fail State Machine One",
    description=("PDW shall enter in failure state if any failure occurs."),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class PDWFailStateMachineOne(TestCase):
    """Example test case."""  # required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # required docstring
        return [
            TestStepPDW,
        ]  # in this list all the needed test steps are included
