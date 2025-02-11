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
ALIAS = "PDW_REACH_CONT"

gearPosition = constants.GearReqConstants
pdwState = constants.SilCl.PDWConstants.pdwState
pdwSysState = constants.SilCl.PDWConstants.pdwSystemState
reduceToMute = constants.SilCl.PDWConstants.ReduceToMute
pdw_sector_length = constants.SilCl.PDWConstants.PDWSectorLength
wheel_direction = constants.SilCl.PDWConstants.WheelDirection
speed_converter = 3.6  # vehicle velocity convert factor unit [km/h]
overspeed_deact = 20  # km/h
delay = constants.SilCl.PDWConstants.delay_wait
tolerance = constants.SilCl.PDWConstants.REACTION_TOLERANCE
standstill = constants.SilCl.PDWConstants.VEH_STANDSTILL


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
        OBSTACE_DISTANCE1 = "EvalShortDist1"
        REDUCE_TO_MUTE = "PDWVolume"
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
            self.Columns.REDUCE_TO_MUTE: "AP.drvWarnStatus.reduceToMuteSoundReq_nu",
            self.Columns.OBSTACE_DISTANCE1: "AP.testEvaluation.shortestDistanceCM[1]",
            self.Columns.WHEEL_FL: "AP.odoInputPort.odoSigFcanPort.wheelMeasurements.wheelDrivingDirections.wheelDrivingDirection_FL_nu",
            self.Columns.WHEEL_FR: "AP.odoInputPort.odoSigFcanPort.wheelMeasurements.wheelDrivingDirections.wheelDrivingDirection_FR_nu",
            self.Columns.WHEEL_RL: "AP.odoInputPort.odoSigFcanPort.wheelMeasurements.wheelDrivingDirections.wheelDrivingDirection_RL_nu",
            self.Columns.WHEEL_RR: "AP.odoInputPort.odoSigFcanPort.wheelMeasurements.wheelDrivingDirections.wheelDrivingDirection_RR_nu",
        }


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="Reduce to mute continuous zone",  # this would be shown as a test step name in html report
    description=(
        "This test step evaluates if PDW function linearly reduces the tone tone."
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class ReduceToMute(TestStep):
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
        self.mute_req = signals[Signals.Columns.REDUCE_TO_MUTE]
        self.short_dist_1 = signals[Signals.Columns.OBSTACE_DISTANCE1]
        self.wheelfl = signals[Signals.Columns.WHEEL_FL]
        self.wheelfr = signals[Signals.Columns.WHEEL_FR]
        self.wheelrl = signals[Signals.Columns.WHEEL_RL]
        self.wheelrr = signals[Signals.Columns.WHEEL_RR]
        # velocity_reversed = self.velocity.iloc[::-1]

        idx = idx1 = idx_0 = idx_m = -1
        car_speed = -1
        act_rgear = False
        verdict = False
        small_dist = round(min(self.short_dist_1), 3)
        # Check for standstill

        # if small_dist >= pdw_sector_length.SLICE_LENGTH and small_dist <= pdw_sector_length.PDW_SECTOR_LENGTH and car_speed <=0.1:
        # Check if PDW activates by R gear
        for i, element in enumerate(self.gear_state):
            if element == gearPosition.GEAR_R:
                idx = i
                if (
                    self.gear_state.iat[idx] == gearPosition.GEAR_R
                    and self.pdw_state.iat[idx] == pdwState.PDW_INT_STATE_ACT_R_GEAR
                    and self.pdw_sys_state.iat[idx] == pdwSysState.PDW_ACTIVATED_BY_R_GEAR
                ):
                    act_rgear = True
                    idx1 = i
                    break
        # check ego vehicle moving
        for i, element in enumerate(self.velocity):
            if element > standstill and i > idx1:
                idx_m = i
                break

        # check ego vehicle stand still
        for i, element in enumerate(self.velocity):
            if (
                element < standstill
                and i > idx_m
                and self.wheelfl.iat[i]
                == self.wheelfr.iat[i]
                == self.wheelrl.iat[i]
                == self.wheelrr.iat[i]
                == wheel_direction.WHEEL_DIRECTION_NONE
            ):
                idx_0 = i
                break
        car_speed = self.velocity.iat[idx_0]
        idx_mute = idx_0
        idx_step = idx_step1 = idx_step2 = idx_step3 = -1
        reduce = 0
        volume_lvl = int(self.mute_req.iat[idx_mute])
        volume_lvl1 = volume_lvl2 = volume_lvl3 = volume_lvl4 = -1
        if act_rgear and car_speed <= standstill and small_dist < pdw_sector_length.SLICE_LENGTH:
            signal_summary["AP.drvWarnStatus.pdwSystemState_nu"] = (
                f" PDW function is Activated by Reverse gear with volume tone reduced to {self.mute_req.iat[idx1]}."
            )
            # Get the timestamp when the volume is reduced by 1 step
            for i, element in enumerate(self.mute_req):
                if element == reduceToMute.PDW_REDUCE_LVL1:
                    idx_step = i
                    break
            reduce = idx_step - idx_mute
            volume_lvl1 = int(self.mute_req.iat[idx_step])
        if (
            volume_lvl == reduceToMute.PDW_REDUCE_NONE
            and reduce <= (reduceToMute.CONTINUOUS_TIME + delay)
            and reduce >= (reduceToMute.CONTINUOUS_TIME - delay)
        ):
            if (
                int(self.mute_req.iat[idx_step - tolerance]) == reduceToMute.PDW_REDUCE_NONE
                and int(self.mute_req.iat[idx_step + tolerance]) == reduceToMute.PDW_REDUCE_LVL1
            ):
                idx_step1 = idx_step + reduceToMute.STEP_TIME
                volume_lvl2 = int(self.mute_req.iat[idx_step1])
                verdict = True
            else:
                verdict = False
            if verdict:
                verdict = False
                if (
                    int(self.mute_req.iat[idx_step1 - tolerance]) == reduceToMute.PDW_REDUCE_LVL1
                    and int(self.mute_req.iat[idx_step1 + tolerance]) == reduceToMute.PDW_REDUCE_LVL2
                ):
                    idx_step2 = idx_step1 + reduceToMute.STEP_TIME
                    volume_lvl3 = int(self.mute_req.iat[idx_step2])
                    if (
                        int(self.mute_req.iat[idx_step2 - tolerance]) == reduceToMute.PDW_REDUCE_LVL2
                        and int(self.mute_req.iat[idx_step2 + tolerance]) == reduceToMute.PDW_REDUCE_LVL3
                    ):
                        idx_step3 = idx_step2 + reduceToMute.STEP_TIME
                        volume_lvl4 = int(self.mute_req.iat[idx_step3])
                        if (
                            int(self.mute_req.iat[idx_step3 - tolerance]) == reduceToMute.PDW_REDUCE_LVL3
                            and int(self.mute_req.iat[idx_step3 + tolerance]) == reduceToMute.PDW_REDUCE_LVL4
                        ):
                            verdict = True

                            signal_summary["AP.testEvaluation.shortestDistanceCM[1]"] = (
                                f"Obstacle placed at distance: {small_dist}m"
                            )
                            signal_summary["AP.drvWarnStatus.reduceToMuteSoundReq_nu"] = "".join(
                                f"Reduced volume at start {int(self.mute_req.iat[idx_mute])}. "
                                f"Volume after standstill wait time {int(self.mute_req.iat[idx_step])}. "
                                f"Volume levels after every {(reduceToMute.STEP_TIME / 100)}s in standstill PDW_REDUCE_LVL values: {volume_lvl1}, {volume_lvl2}, {volume_lvl3}, {volume_lvl4}"
                            )
                            signal_summary["TIME"] = "".join(
                                f"Standstill time with obstacle in continuous zone: {round(self.ap_time.iat[reduce], 3)}s. "
                                f"Each time frame for each PDW_REDUCE_LVL when volume is reduced value: {round(self.ap_time.iat[idx_step], 3)}s, {round(self.ap_time.iat[idx_step1], 3)}s, {round(self.ap_time.iat[idx_step2], 3)}s, {round(self.ap_time.iat[idx_step3], 3)}s"
                            )
        else:
            signal_summary["AP.testEvaluation.shortestDistanceCM[1]"] = f"Obstacle placed at distance {small_dist}"
            signal_summary["AP.drvWarnStatus.reduceToMuteSoundReq_nu"] = (
                f"PDW Volume reduced to: {int(self.mute_req.iat[-1])}"
            )
            signal_summary["Time"] = f"Start reduce to mute time is: {reduce/100}s."
            verdict = False
        if not act_rgear:
            self.result.measured_result = FALSE
            signal_summary["AP.drvWarnStatus.pdwState_nu"] = " PDW function internal state is deactivated."
            signal_summary["AP.drvWarnStatus.pdwSystemState_nu"] = " PDW function system state is OFF."
        elif small_dist > pdw_sector_length.SLICE_LENGTH:
            self.result.measured_result = FALSE
            signal_summary["AP.testEvaluation.shortestDistanceCM[1]"] = (
                f"Obstacle not in continuous tone zone {small_dist}m"
            )
        else:
            self.result.measured_result = TRUE if verdict else FALSE

        remark = " ".join(
            "Reduce Volume lvl to mute: From 0 (for maximum volume) to 4 (volume muted)".split(),
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
                x=self.ap_time,
                y=self.mute_req,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.REDUCE_TO_MUTE],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=self.ap_time,
                y=self.velocity,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.VELOCITY],
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
    name="Continuous zone reduce to mute reach standstill",
    description=(
        "After the time in standstill of the ego vehicle has passed when an obstacle is in continuous zone to reduce the tone to muted linearly."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class ReduceToMuteReachContinuous(TestCase):
    """Example test case."""  # required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # required docstring
        return [
            ReduceToMute,
        ]  # in this list all the needed test steps are included
