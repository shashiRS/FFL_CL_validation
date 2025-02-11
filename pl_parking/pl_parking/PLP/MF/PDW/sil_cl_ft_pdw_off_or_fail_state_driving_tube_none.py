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
ALIAS = "PDW_DRT_OFF"

gearPosition = constants.GearReqConstants
pdwState = constants.SilCl.PDWConstants.pdwState
pdwSysState = constants.SilCl.PDWConstants.pdwSystemState
pdw_hmi_interact = constants.SilCl.PDWConstants.pdwUserActionHeadUnit  # TAP_ON_PDC = 35
epbSwitch = constants.SilCl.PDWConstants.EPBSwitch
drvTubeDisplay = constants.SilCl.PDWConstants.DrivingTubeReq
apStateVal = constants.SilCl.PDWConstants.ApStates
ap_PDWFailure = constants.SilCl.PDWConstants.pdwFailure
wheel_direction = constants.SilCl.PDWConstants.WheelDirection
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


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="Driving tube display set to NONE",  # this would be shown as a test step name in html report
    description=(
        "This test step evaluates if the driving tube is not displayed if PDW is in off state or in failure state."
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class PDWDrivingTubeReq(TestStep):
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
        self.pdw_button = signals[Signals.Columns.TAP_ON_HMI]
        self.apStatus = signals[Signals.Columns.AP_STATE]
        self.pdwFailureState = signals[Signals.Columns.PDW_FAILURE]
        self.wheelfl = signals[Signals.Columns.WHEEL_FL]
        self.wheelfr = signals[Signals.Columns.WHEEL_FR]
        self.wheelrl = signals[Signals.Columns.WHEEL_RL]
        self.wheelrr = signals[Signals.Columns.WHEEL_RR]

        # pdw state mask
        state_pdw_init_mask = self.pdw_state == pdwState.PDW_INT_STATE_INIT
        state_deact_fail_mask = self.pdw_state == pdwState.PDW_INT_STATE_FAILURE

        pdw_state_mask = [
            x for x in self.pdw_state if x != pdwState.PDW_INT_STATE_INIT and x != pdwState.PDW_INT_STATE_DEACT_INIT
        ]

        deactivation_metod = "pdw error"
        pdwState_No_value = pdwState.PDW_INT_STATE_INIT
        pdwState_value = "PDW_INT_STATE_INIT"
        deact_validation = False
        if state_pdw_init_mask.any():
            if not pdw_state_mask:
                deactivation_metod = "deactivated after initialization"
                pdwState_No_value = pdwState.PDW_INT_STATE_DEACT_INIT
                pdwState_value = "PDW_INT_STATE_DEACT_INIT"

                self.result.measured_result = TRUE if deactivation_metod != "pdw error" else FALSE
                deact_validation = True if deactivation_metod != "pdw error" else False
                signal_summary["AP.drvWarnStatus.pdwState_nu"] = (
                    f" PDW function was {deactivation_metod} state with pdwState = {pdwState_No_value} ({pdwState_value})."
                )
                signal_summary["AP.pdcpDrivingTubePort.drvTubeDisplay_nu"] = (
                    f"Driving tube display PDC_DRV_TUBE_NONE = {int(self.dt_req.iat[-1])}"
                )
            elif state_deact_fail_mask.any():
                idx = -1
                for i, element in enumerate(self.pdw_state):
                    if element == pdwState.PDW_INT_STATE_FAILURE:
                        idx = i
                        break
                if (
                    self.pdwFailureState.iat[idx] == ap_PDWFailure.PDW_FAILURE_TRUE
                    and self.pdw_state.iat[idx] == pdwState.PDW_INT_STATE_FAILURE
                    and self.dt_req.iat[idx - delay] != drvTubeDisplay.PDC_DRV_TUBE_NONE
                ):  # validate if PDW is in failure
                    deactivation_metod = "deactivated by failure"
                    pdwState_No_value = pdwState.PDW_INT_STATE_FAILURE
                    pdwState_value = "PDW_INT_STATE_FAILURE"
                    signal_summary["AP.pdwFailure_nu"] = (
                        f"PDW failure present with value {int(self.pdwFailureState.iat[idx])} (0 for False and 1 for True )"
                    )
                    fail_deact = go.Scatter(
                        x=self.ap_time,
                        y=self.pdwFailureState,
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.PDW_FAILURE],
                    )
                deact_validation = True if deactivation_metod != "pdw error" else False
                signal_summary["AP.drvWarnStatus.pdwState_nu"] = (
                    f" PDW function is {deactivation_metod} state with pdwState = {pdwState_No_value} ({pdwState_value}) ."
                )

                if deact_validation:
                    dt_none = FALSE
                    if deactivation_metod == "deactivated after initialization":
                        signal_summary["AP.pdcpDrivingTubePort.drvTubeDisplay_nu"] = (
                            f"Driving tube display PDC_DRV_TUBE_NONE = {int(self.dt_req.iat[-1])}"
                        )
                        dt_none = (
                            TRUE
                            if self.dt_req.iat[-1] == self.dt_req.iat[1] == drvTubeDisplay.PDC_DRV_TUBE_NONE
                            else FALSE
                        )
                    elif deactivation_metod == "deactivated by failure":
                        signal_summary["AP.pdcpDrivingTubePort.drvTubeDisplay_nu"] = (
                            f"Driving tube display PDC_DRV_TUBE_NONE = {int(self.dt_req.iat[idx])}"
                        )

                        dt_none = TRUE if self.dt_req.iat[idx] == drvTubeDisplay.PDC_DRV_TUBE_NONE else FALSE

                    self.result.measured_result = dt_none
                    signal_summary["AP.drvWarnStatus.pdwState_nu"] = (
                        f" PDW function is {deactivation_metod} state with pdwState = {pdwState_No_value} ({pdwState_value})."
                    )

        remark = " ".join(
            "This test step verifies PDW activation/deactivation reason "
            "monitoring the signal (AP.drvWarnStatus.pdwState_nu) ".split()
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
                x=self.ap_time,
                y=self.gear_state,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.GEARBOX_STATE],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=self.ap_time, y=self.dt_req, mode="lines", name=signals_obj._properties[Signals.Columns.DRV_TUBE]
            )
        )
        if deactivation_metod == "deactivated by failure":
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
    name="No Driving Tube Display PDW OFF",
    description=(
        "PDW function shall set the Driving tube to None if it is deactivated after initialization or deactivated by failure"
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class PDWDrivingTubeNONE(TestCase):
    """Example test case."""  # required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # required docstring
        return [
            PDWDrivingTubeReq,
        ]  # in this list all the needed test steps are included
