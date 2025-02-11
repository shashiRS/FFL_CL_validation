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
import pl_parking.PLP.MF.PDW.pdw_helper as pdwh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "PDW_DYNAMIC"

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

        SECTOR_CRITICALITYFR = "SECTOR_CRITICALITYFR{}"
        SECTOR_DISTANCEFR = "SECTOR_DISTANCEFR{}"
        SECTOR_CRITICALITYFR0 = "SECTOR_CRITICALITYFR0"
        SECTOR_DISTANCEFR0 = "SECTOR_DISTANCEFR0"
        SECTOR_CRITICALITYFR1 = "SECTOR_CRITICALITYFR1"
        SECTOR_DISTANCEFR1 = "SECTOR_DISTANCEFR1"
        SECTOR_CRITICALITYFR2 = "SECTOR_CRITICALITYFR2"
        SECTOR_DISTANCEFR2 = "SECTOR_DISTANCEFR2"
        SECTOR_CRITICALITYFR3 = "SECTOR_CRITICALITYFR3"
        SECTOR_DISTANCEFR3 = "SECTOR_DISTANCEFR3"

        OBSTACE_DISTANCE1 = "EvalShortDist1"

        SECTOR_CRITICALITYLE = "SECTOR_CRITICALITYLE{}"
        SECTOR_DISTANCELE = "SECTOR_DISTANCELE{}"
        SECTOR_CRITICALITYLE0 = "SECTOR_CRITICALITYLE0"
        SECTOR_DISTANCELE0 = "SECTOR_DISTANCELE0"
        SECTOR_CRITICALITYLE1 = "SECTOR_CRITICALITYLE1"
        SECTOR_DISTANCELE1 = "SECTOR_DISTANCELE1"
        SECTOR_CRITICALITYLE2 = "SECTOR_CRITICALITYLE2"
        SECTOR_DISTANCELE2 = "SECTOR_DISTANCELE2"
        SECTOR_CRITICALITYLE3 = "SECTOR_CRITICALITYLE3"
        SECTOR_DISTANCELE3 = "SECTOR_DISTANCELE3"

        SECTOR_CRITICALITYRE = "SECTOR_CRITICALITYRE{}"
        SECTOR_DISTANCERE = " SECTOR_DISTANCERE{}"
        SECTOR_CRITICALITYRE0 = "SECTOR_CRITICALITYRE0"
        SECTOR_DISTANCERE0 = " SECTOR_DISTANCERE0"
        SECTOR_CRITICALITYRE1 = "SECTOR_CRITICALITYRE1"
        SECTOR_DISTANCERE1 = " SECTOR_DISTANCERE1"
        SECTOR_CRITICALITYRE2 = "SECTOR_CRITICALITYRE2"
        SECTOR_DISTANCERE2 = " SECTOR_DISTANCERE2"
        SECTOR_CRITICALITYRE3 = "SECTOR_CRITICALITYRE3"
        SECTOR_DISTANCERE3 = " SECTOR_DISTANCERE3"

        SECTOR_CRITICALITYRI = "SECTOR_CRITICALITYRI{}"
        SECTOR_DISTANCERI = " SECTOR_DISTANCERI{}"
        SECTOR_CRITICALITYRI0 = "SECTOR_CRITICALITYRI0"
        SECTOR_DISTANCERI0 = " SECTOR_DISTANCERI0"
        SECTOR_CRITICALITYRI1 = "SECTOR_CRITICALITYRI1"
        SECTOR_DISTANCERI1 = " SECTOR_DISTANCERI1"
        SECTOR_CRITICALITYRI2 = "SECTOR_CRITICALITYRI2"
        SECTOR_DISTANCERI2 = " SECTOR_DISTANCERI2"
        SECTOR_CRITICALITYRI3 = "SECTOR_CRITICALITYRI3"
        SECTOR_DISTANCERI3 = " SECTOR_DISTANCERI3"

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
            self.Columns.OBSTACE_DISTANCE1: "AP.testEvaluation.shortestDistanceCM[1]",
        }

        front_sectors_criticality = {
            self.Columns.SECTOR_CRITICALITYFR.format(x): f"AP.pdcpSectorsPort.sectorsFront_{x}.criticalityLevel_nu"
            for x in range(4)
        }
        front_sectors_distance = {
            self.Columns.SECTOR_DISTANCEFR.format(x): f"AP.pdcpSectorsPort.sectorsFront_{x}.dynamicSmallestDistance_m"
            for x in range(4)
        }
        left_sectors_criticality = {
            self.Columns.SECTOR_CRITICALITYLE.format(x): f"AP.pdcpSectorsPort.sectorsLeft_{x}.criticalityLevel_nu"
            for x in range(4)
        }
        left_sectors_distance = {
            self.Columns.SECTOR_DISTANCELE.format(x): f"AP.pdcpSectorsPort.sectorsLeft_{x}.dynamicSmallestDistance_m"
            for x in range(4)
        }
        rear_sectors_criticality = {
            self.Columns.SECTOR_CRITICALITYRE.format(x): f"AP.pdcpSectorsPort.sectorsRear_{x}.criticalityLevel_nu"
            for x in range(4)
        }
        rear_sectors_distance = {
            self.Columns.SECTOR_DISTANCERE.format(x): f"AP.pdcpSectorsPort.sectorsRear_{x}.dynamicSmallestDistance_m"
            for x in range(4)
        }
        right_sectors_criticality = {
            self.Columns.SECTOR_CRITICALITYRI.format(x): f"AP.pdcpSectorsPort.sectorsRight_{x}.criticalityLevel_nu"
            for x in range(4)
        }
        right_sectors_distance = {
            self.Columns.SECTOR_DISTANCERI.format(x): f"AP.pdcpSectorsPort.sectorsRight_{x}.dynamicSmallestDistance_m"
            for x in range(4)
        }

        self._properties.update(front_sectors_criticality)
        self._properties.update(front_sectors_distance)
        self._properties.update(left_sectors_criticality)
        self._properties.update(left_sectors_distance)
        self._properties.update(rear_sectors_criticality)
        self._properties.update(rear_sectors_distance)
        self._properties.update(right_sectors_criticality)
        self._properties.update(right_sectors_distance)


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="PDW at initialization",  # this would be shown as a test step name in html report
    description=(
        "This test step evaluates PDW at init state and if any state changes occurs."
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

        self.smallest_dist_fr_0 = signals[Signals.Columns.SECTOR_DISTANCEFR0]
        self.smallest_dist_fr_1 = signals[Signals.Columns.SECTOR_DISTANCEFR1]
        self.smallest_dist_fr_2 = signals[Signals.Columns.SECTOR_DISTANCEFR2]
        self.smallest_dist_fr_3 = signals[Signals.Columns.SECTOR_DISTANCEFR3]

        self.smallest_dist_ri_0 = signals[Signals.Columns.SECTOR_DISTANCERI0]
        self.smallest_dist_ri_1 = signals[Signals.Columns.SECTOR_DISTANCERI1]
        self.smallest_dist_ri_2 = signals[Signals.Columns.SECTOR_DISTANCERI2]
        self.smallest_dist_ri_3 = signals[Signals.Columns.SECTOR_DISTANCERI3]

        self.smallest_dist_re_0 = signals[Signals.Columns.SECTOR_DISTANCERE0]
        self.smallest_dist_re_1 = signals[Signals.Columns.SECTOR_DISTANCERE1]
        self.smallest_dist_re_2 = signals[Signals.Columns.SECTOR_DISTANCERE2]
        self.smallest_dist_re_3 = signals[Signals.Columns.SECTOR_DISTANCERE3]

        self.smallest_dist_le_0 = signals[Signals.Columns.SECTOR_DISTANCELE0]
        self.smallest_dist_le_1 = signals[Signals.Columns.SECTOR_DISTANCELE1]
        self.smallest_dist_le_2 = signals[Signals.Columns.SECTOR_DISTANCELE2]
        self.smallest_dist_le_3 = signals[Signals.Columns.SECTOR_DISTANCELE3]

        self.smallest_crit_fr_0 = signals[Signals.Columns.SECTOR_CRITICALITYFR0]
        self.smallest_crit_fr_1 = signals[Signals.Columns.SECTOR_CRITICALITYFR1]
        self.smallest_crit_fr_2 = signals[Signals.Columns.SECTOR_CRITICALITYFR2]
        self.smallest_crit_fr_3 = signals[Signals.Columns.SECTOR_CRITICALITYFR3]

        self.smallest_crit_re_0 = signals[Signals.Columns.SECTOR_CRITICALITYRE0]
        self.smallest_crit_re_1 = signals[Signals.Columns.SECTOR_CRITICALITYRE1]
        self.smallest_crit_re_2 = signals[Signals.Columns.SECTOR_CRITICALITYRE2]
        self.smallest_crit_re_3 = signals[Signals.Columns.SECTOR_CRITICALITYRE3]

        self.smallest_crit_ri_0 = signals[Signals.Columns.SECTOR_CRITICALITYRI0]
        self.smallest_crit_ri_1 = signals[Signals.Columns.SECTOR_CRITICALITYRI1]
        self.smallest_crit_ri_2 = signals[Signals.Columns.SECTOR_CRITICALITYRI2]
        self.smallest_crit_ri_3 = signals[Signals.Columns.SECTOR_CRITICALITYRI3]

        self.smallest_crit_le_0 = signals[Signals.Columns.SECTOR_CRITICALITYLE0]
        self.smallest_crit_le_1 = signals[Signals.Columns.SECTOR_CRITICALITYLE1]
        self.smallest_crit_le_2 = signals[Signals.Columns.SECTOR_CRITICALITYLE2]
        self.smallest_crit_le_3 = signals[Signals.Columns.SECTOR_CRITICALITYLE3]

        self.short_dist_1 = signals[Signals.Columns.OBSTACE_DISTANCE1]

        act_btn_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_BTN
        act_auto_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_AUTO
        act_rg_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_R_GEAR

        activate_metod = "not activated"
        pdwState_No_value = pdwState.PDW_INT_STATE_INIT
        pdwState_value = "PDW_INT_STATE_INIT"
        pdwSysState_No_value = pdwSysState.PDW_INIT
        pdwSysState_value = "PDW_INIT"
        verdict_state = DATA_NOK
        if act_btn_mask.any():
            activate_metod = "activated by button"
            pdwState_No_value = pdwState.PDW_INT_STATE_ACT_BTN
            pdwState_value = "PDW_INT_STATE_ACT_BTN"
            pdwSysState_No_value = pdwSysState.PDW_ACTIVATED_BY_BUTTON
            pdwSysState_value = "PDW_ACTIVATED_BY_BUTTON"
            verdict_state = TRUE
        elif act_auto_mask.any():
            activate_metod = "automatically activated"
            pdwState_No_value = pdwState.PDW_INT_STATE_ACT_AUTO
            pdwState_value = "PDW_INT_STATE_ACT_AUTO"
            pdwSysState_No_value = pdwSysState.PDW_AUTOMATICALLY_ACTIVATED
            pdwSysState_value = "PDW_AUTOMATICALLY_ACTIVATED"
            verdict_state = TRUE
        elif act_rg_mask.any():
            activate_metod = "reverse gear"
            pdwState_No_value = pdwState.PDW_INT_STATE_ACT_R_GEAR
            pdwState_value = "PDW_INT_STATE_ACT_R_GEAR"
            pdwSysState_No_value = pdwSysState.PDW_ACTIVATED_BY_R_GEAR
            pdwSysState_value = "PDW_ACTIVATED_BY_R_GEAR"
            verdict_state = TRUE
        else:
            activate_metod = "not activated"
            pdwState_No_value = pdwState.PDW_INT_STATE_INIT
            pdwState_value = "PDW_INT_STATE_FAILURE"
            pdwSysState_No_value = pdwSysState.PDW_INIT
            pdwSysState_value = "PDW_PDW_FAILURE"
            verdict_state = FALSE

        self.result.measured_result = TRUE if verdict_state == TRUE else FALSE

        signal_summary["AP.drvWarnStatus.pdwState_nu"] = (
            f" PDW function is {activate_metod} state with pdwState = {pdwState_No_value} ({pdwState_value}) ."
        )

        signal_summary["AP.drvWarnStatus.pdwSystemState_nu"] = (
            f" PDW function is {activate_metod} state with pdwSystemState = {pdwSysState_No_value} ({pdwSysState_value})."
        )

        remark = " ".join("".split())
        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        # add the needed signals in the plot
        fig.add_trace(
            go.Scatter(
                x=self.ap_time, y=self.velocity, mode="lines", name=signals_obj._properties[Signals.Columns.VELOCITY]
            )
        )
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


@teststep_definition(
    step_number=2,
    name="Front sectors",  # this would be shown as a test step name in html report
    description=(
        "This test step evaluates the front sector signals for PDW function when a dynamic obstacle is present iside the sector."
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestPDWFront(TestStepPDW):
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
        super().process(**kwargs)
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
        ap_time = self.ap_time
        ap_time = self.ap_time
        act_btn_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_BTN
        act_auto_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_AUTO
        act_rg_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_R_GEAR
        activate_metod = "not activated"
        pdwState_No_value = pdwState.PDW_INT_STATE_INIT
        pdwState_value = "PDW_INT_STATE_INIT"
        pdwSysState_No_value = pdwSysState.PDW_INIT
        pdwSysState_value = "PDW_INIT"
        verdict_state = DATA_NOK
        if act_btn_mask.any():
            activate_metod = "activated by button"
            pdwState_No_value = pdwState.PDW_INT_STATE_ACT_BTN
            pdwState_value = "PDW_INT_STATE_ACT_BTN"
            pdwSysState_No_value = pdwSysState.PDW_ACTIVATED_BY_BUTTON
            pdwSysState_value = "PDW_ACTIVATED_BY_BUTTON"
            verdict_state = TRUE
        elif act_auto_mask.any():
            activate_metod = "automatically activated"
            pdwState_No_value = pdwState.PDW_INT_STATE_ACT_AUTO
            pdwState_value = "PDW_INT_STATE_ACT_AUTO"
            pdwSysState_No_value = pdwSysState.PDW_AUTOMATICALLY_ACTIVATED
            pdwSysState_value = "PDW_AUTOMATICALLY_ACTIVATED"
            verdict_state = TRUE
        elif act_rg_mask.any():
            activate_metod = "reverse gear"
            pdwState_No_value = pdwState.PDW_INT_STATE_ACT_R_GEAR
            pdwState_value = "PDW_INT_STATE_ACT_R_GEAR"
            pdwSysState_No_value = pdwSysState.PDW_ACTIVATED_BY_R_GEAR
            pdwSysState_value = "PDW_ACTIVATED_BY_R_GEAR"
            verdict_state = TRUE
        else:
            activate_metod = "not activated"
            pdwState_No_value = pdwState.PDW_INT_STATE_INIT
            pdwState_value = "PDW_INT_STATE_INIT"
            pdwSysState_No_value = pdwSysState.PDW_INIT
            pdwSysState_value = "PDW_INIT"
            verdict_state = FALSE

        sector_dist_check_list = [
            self.smallest_dist_ri_2,
            self.smallest_dist_ri_3,
            self.smallest_dist_re_0,
            self.smallest_dist_re_1,
            self.smallest_dist_re_2,
            self.smallest_dist_re_3,
            self.smallest_dist_le_2,
            self.smallest_dist_le_3,
        ]
        sector_crit_check_list = [
            self.smallest_crit_ri_2,
            self.smallest_crit_ri_3,
            self.smallest_crit_re_0,
            self.smallest_crit_re_1,
            self.smallest_crit_re_2,
            self.smallest_crit_re_3,
            self.smallest_crit_le_2,
            self.smallest_crit_le_3,
        ]
        dist_check_signal = [
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI3],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE1],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE3],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE3],
        ]
        smallest_dist_fr = [
            self.smallest_dist_ri_0,
            self.smallest_dist_le_0,
            self.smallest_dist_ri_1,
            self.smallest_dist_le_1,
            self.smallest_dist_fr_0,
            self.smallest_dist_fr_1,
            self.smallest_dist_fr_2,
            self.smallest_dist_fr_3,
        ]
        smallest_crit_fr = [
            self.smallest_crit_ri_0,
            self.smallest_crit_le_0,
            self.smallest_crit_ri_1,
            self.smallest_crit_le_1,
            self.smallest_crit_fr_0,
            self.smallest_crit_fr_1,
            self.smallest_crit_fr_2,
            self.smallest_crit_fr_3,
        ]
        front_dist_signal = [
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI1],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE1],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR1],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR3],
        ]

        signal_summary, verdict = pdwh.sector_evaluation(smallest_dist_fr, smallest_crit_fr, front_dist_signal)

        shortest_distance = min(self.short_dist_1)
        idx = -1
        for i, obj1_short_dist in enumerate(self.short_dist_1):
            if obj1_short_dist == shortest_distance:
                obj1_short_dist = round(obj1_short_dist, 3)
                idx = i
                break
        for j in range(4):
            crit_lvl = smallest_crit_fr[j + 4]
            if crit_lvl.iat[idx] != 0:
                summary_txt = f"The shortest evaluated distance between object and ego vehicle is {obj1_short_dist} m and criticality level = {crit_lvl.iat[idx]}"
            else:
                summary_txt = f"The object is detected in wrong sector at {obj1_short_dist} m"

        if any(verdict) and shortest_distance <= pdw_sector_length.PDW_SECTOR_LENGTH:
            signal_summary, verdict = pdwh.sector_evaluation(
                sector_dist_check_list, sector_crit_check_list, dist_check_signal
            )

            if any(verdict):
                self.result.measured_result = FALSE
                signal_summary, verdict = pdwh.sector_evaluation(
                    sector_dist_check_list, sector_crit_check_list, dist_check_signal
                )
                signal_summary["AP.testEvaluation.shortestDistanceCM[1]"] = summary_txt
            else:
                signal_summary, verdict = pdwh.sector_evaluation(smallest_dist_fr, smallest_crit_fr, front_dist_signal)
                self.result.measured_result = TRUE
                signal_summary["AP.testEvaluation.shortestDistanceCM[1]"] = summary_txt
        else:
            self.result.measured_result = FALSE
            signal_summary["AP.testEvaluation.shortestDistanceCM[1]"] = "No object detected"

        self.result.measured_result = TRUE if verdict_state == TRUE else FALSE
        signal_summary["AP.drvWarnStatus.pdwState_nu"] = (
            f" PDW function is {activate_metod} state with pdwState = {pdwState_No_value} ({pdwState_value}) ."
        )

        signal_summary["AP.drvWarnStatus.pdwSystemState_nu"] = (
            f" PDW function is {activate_metod} state with pdwSystemState = {pdwSysState_No_value} ({pdwSysState_value})."
        )

        # signal_summary = sector_evaluation(smallest_dist_le,smallest_crit_le,"Left")[0]
        remark = " ".join("Check if each segment of front sector had a PDW object detection.".split())
        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        # add the needed signals in the plot
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_crit_ri_0,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYRI0],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_dist_ri_0,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI0],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_crit_le_0,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYLE0],
            )
        )

        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_dist_le_0,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE0],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_crit_ri_1,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYRI1],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_dist_ri_1,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI1],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_crit_le_1,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYLE1],
            )
        )

        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_dist_le_1,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE1],
            )
        )
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=smallest_dist_fr[i + 4],
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR.format(i)],
                )
            )
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=smallest_crit_fr[i + 4],
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYFR.format(i)],
                )
            )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.short_dist_1,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.OBSTACE_DISTANCE1],
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
    name="PDW Dynamic_Front",
    description=("PDW shall detect all dynamic obstacles in the front side of the car."),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class PDWDynamicFront(TestCase):
    """Example test case."""  # required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # required docstring
        return [
            TestStepPDW,
            TestPDWFront,
        ]  # in this list all the needed test steps are included


@teststep_definition(
    step_number=3,
    name="Right sectors",  # this would be shown as a test step name in html report
    description=(
        "This test step evaluates the right sector signals for PDW function when a dynamic obstacle is present iside the sector."
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestPDWRight(TestStepPDW):
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
        super().process(**kwargs)
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
        ap_time = self.ap_time
        ap_time = self.ap_time
        act_btn_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_BTN
        act_auto_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_AUTO
        act_rg_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_R_GEAR
        activate_metod = "not activated"
        pdwState_No_value = pdwState.PDW_INT_STATE_INIT
        pdwState_value = "PDW_INT_STATE_INIT"
        pdwSysState_No_value = pdwSysState.PDW_INIT
        pdwSysState_value = "PDW_INIT"
        verdict_state = DATA_NOK
        if act_btn_mask.any():
            activate_metod = "activated by button"
            pdwState_No_value = pdwState.PDW_INT_STATE_ACT_BTN
            pdwState_value = "PDW_INT_STATE_ACT_BTN"
            pdwSysState_No_value = pdwSysState.PDW_ACTIVATED_BY_BUTTON
            pdwSysState_value = "PDW_ACTIVATED_BY_BUTTON"
            verdict_state = TRUE
        elif act_auto_mask.any():
            activate_metod = "automatically activated"
            pdwState_No_value = pdwState.PDW_INT_STATE_ACT_AUTO
            pdwState_value = "PDW_INT_STATE_ACT_AUTO"
            pdwSysState_No_value = pdwSysState.PDW_AUTOMATICALLY_ACTIVATED
            pdwSysState_value = "PDW_AUTOMATICALLY_ACTIVATED"
            verdict_state = TRUE
        elif act_rg_mask.any():
            activate_metod = "reverse gear"
            pdwState_No_value = pdwState.PDW_INT_STATE_ACT_R_GEAR
            pdwState_value = "PDW_INT_STATE_ACT_R_GEAR"
            pdwSysState_No_value = pdwSysState.PDW_ACTIVATED_BY_R_GEAR
            pdwSysState_value = "PDW_ACTIVATED_BY_R_GEAR"
            verdict_state = TRUE
        else:
            activate_metod = "not activated"
            pdwState_No_value = pdwState.PDW_INT_STATE_INIT
            pdwState_value = "PDW_INT_STATE_INIT"
            pdwSysState_No_value = pdwSysState.PDW_INIT
            pdwSysState_value = "PDW_INIT"
            verdict_state = FALSE

        sector_dist_check_list = [
            self.smallest_dist_re_0,
            self.smallest_dist_re_1,
            self.smallest_dist_fr_0,
            self.smallest_dist_fr_1,
            self.smallest_dist_le_0,
            self.smallest_dist_le_1,
            self.smallest_dist_le_2,
            self.smallest_dist_le_3,
        ]
        sector_crit_check_list = [
            self.smallest_crit_re_0,
            self.smallest_crit_re_1,
            self.smallest_crit_fr_0,
            self.smallest_crit_fr_1,
            self.smallest_crit_le_0,
            self.smallest_crit_le_1,
            self.smallest_crit_le_2,
            self.smallest_crit_le_3,
        ]
        dist_check_signal = [
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE1],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR1],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE1],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE3],
        ]
        smallest_dist_ri = [
            self.smallest_dist_fr_3,
            self.smallest_dist_fr_2,
            self.smallest_dist_re_3,
            self.smallest_dist_re_2,
            self.smallest_dist_ri_0,
            self.smallest_dist_ri_1,
            self.smallest_dist_ri_2,
            self.smallest_dist_ri_3,
        ]
        smallest_crit_ri = [
            self.smallest_crit_fr_3,
            self.smallest_crit_fr_2,
            self.smallest_crit_re_3,
            self.smallest_crit_re_2,
            self.smallest_crit_ri_0,
            self.smallest_crit_ri_1,
            self.smallest_crit_ri_2,
            self.smallest_crit_ri_3,
        ]
        right_dist_signal = [
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR3],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE3],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI1],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI3],
        ]

        signal_summary, verdict = pdwh.sector_evaluation(smallest_dist_ri, smallest_crit_ri, right_dist_signal)

        shortest_distance = min(self.short_dist_1)
        idx = -1
        for i, obj1_short_dist in enumerate(self.short_dist_1):
            if obj1_short_dist == shortest_distance:
                obj1_short_dist = round(obj1_short_dist, 3)
                idx = i
                break
        for j in range(4):
            crit_lvl = smallest_crit_ri[j + 4]
            if crit_lvl.iat[idx] != 0:
                summary_txt = f"The shortest evaluated distance between object and ego vehicle is {obj1_short_dist} m and criticality level = {crit_lvl.iat[idx]}"
            else:
                summary_txt = f"The object is detected in wrong sector at {obj1_short_dist} m"

        if any(verdict) and shortest_distance <= pdw_sector_length.PDW_SECTOR_LENGTH:
            signal_summary, verdict = pdwh.sector_evaluation(
                sector_dist_check_list, sector_crit_check_list, dist_check_signal
            )

            if any(verdict):
                self.result.measured_result = FALSE
                signal_summary, verdict = pdwh.sector_evaluation(
                    sector_dist_check_list, sector_crit_check_list, dist_check_signal
                )
                signal_summary["AP.testEvaluation.shortestDistanceCM[1]"] = summary_txt
            else:
                signal_summary, verdict = pdwh.sector_evaluation(smallest_dist_ri, smallest_crit_ri, right_dist_signal)
                self.result.measured_result = TRUE
                signal_summary["AP.testEvaluation.shortestDistanceCM[1]"] = summary_txt
        else:
            self.result.measured_result = FALSE
            signal_summary["AP.testEvaluation.shortestDistanceCM[1]"] = "No object detected"

        self.result.measured_result = TRUE if verdict_state == TRUE else FALSE
        signal_summary["AP.drvWarnStatus.pdwState_nu"] = (
            f" PDW function is {activate_metod} state with pdwState = {pdwState_No_value} ({pdwState_value}) ."
        )

        signal_summary["AP.drvWarnStatus.pdwSystemState_nu"] = (
            f" PDW function is {activate_metod} state with pdwSystemState = {pdwSysState_No_value} ({pdwSysState_value})."
        )

        # signal_summary = sector_evaluation(smallest_dist_le,smallest_crit_le,"Left")[0]
        remark = " ".join("Check if each segment of front sector had a PDW object detection.".split())
        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        # add the needed signals in the plot
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_crit_fr_3,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYFR3],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_dist_fr_3,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR3],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_crit_re_3,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYRE3],
            )
        )

        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_dist_re_3,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE3],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_crit_fr_2,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYFR2],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_dist_fr_2,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR2],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_crit_re_2,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYRE2],
            )
        )

        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_dist_re_2,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE2],
            )
        )
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=smallest_dist_ri[i + 4],
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI.format(i)],
                )
            )
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=smallest_crit_ri[i + 4],
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYRI.format(i)],
                )
            )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.short_dist_1,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.OBSTACE_DISTANCE1],
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
    name="PDW Dynamic_Right",
    description=("PDW shall detect all dynamic obstacles in the right side of the car."),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class PDWDynamicRight(TestCase):
    """Example test case."""  # required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # required docstring
        return [
            TestStepPDW,
            TestPDWRight,
        ]  # in this list all the needed test steps are included


@teststep_definition(
    step_number=4,
    name="Rear sectors",  # this would be shown as a test step name in html report
    description=(
        "This test step evaluates the rear sector signals for PDW function when a dynamic obstacle is present iside the sector."
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestPDWRear(TestStepPDW):
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
        super().process(**kwargs)
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
        ap_time = self.ap_time
        activate_metod = "not activated"
        pdwState_No_value = pdwState.PDW_INT_STATE_INIT
        pdwState_value = "PDW_INT_STATE_INIT"
        pdwSysState_No_value = pdwSysState.PDW_INIT
        pdwSysState_value = "PDW_INIT"
        verdict_state = DATA_NOK
        ap_time = self.ap_time
        act_btn_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_BTN
        act_auto_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_AUTO
        act_rg_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_R_GEAR
        if act_btn_mask.any():
            activate_metod = "activated by button"
            pdwState_No_value = pdwState.PDW_INT_STATE_ACT_BTN
            pdwState_value = "PDW_INT_STATE_ACT_BTN"
            pdwSysState_No_value = pdwSysState.PDW_ACTIVATED_BY_BUTTON
            pdwSysState_value = "PDW_ACTIVATED_BY_BUTTON"
            verdict_state = TRUE
        elif act_auto_mask.any():
            activate_metod = "automatically activated"
            pdwState_No_value = pdwState.PDW_INT_STATE_ACT_AUTO
            pdwState_value = "PDW_INT_STATE_ACT_AUTO"
            pdwSysState_No_value = pdwSysState.PDW_AUTOMATICALLY_ACTIVATED
            pdwSysState_value = "PDW_AUTOMATICALLY_ACTIVATED"
            verdict_state = TRUE
        elif act_rg_mask.any():
            activate_metod = "reverse gear"
            pdwState_No_value = pdwState.PDW_INT_STATE_ACT_R_GEAR
            pdwState_value = "PDW_INT_STATE_ACT_R_GEAR"
            pdwSysState_No_value = pdwSysState.PDW_ACTIVATED_BY_R_GEAR
            pdwSysState_value = "PDW_ACTIVATED_BY_R_GEAR"
            verdict_state = TRUE
        else:
            activate_metod = "not activated"
            pdwState_No_value = pdwState.PDW_INT_STATE_INIT
            pdwState_value = "PDW_INT_STATE_INIT"
            pdwSysState_No_value = pdwSysState.PDW_INIT
            pdwSysState_value = "PDW_INIT"
            verdict_state = FALSE

        sector_dist_check_list = [
            self.smallest_dist_ri_0,
            self.smallest_dist_ri_1,
            self.smallest_dist_fr_0,
            self.smallest_dist_fr_1,
            self.smallest_dist_fr_2,
            self.smallest_dist_fr_3,
            self.smallest_dist_le_0,
            self.smallest_dist_le_1,
        ]
        sector_crit_check_list = [
            self.smallest_crit_ri_0,
            self.smallest_crit_ri_1,
            self.smallest_crit_fr_0,
            self.smallest_crit_fr_1,
            self.smallest_crit_fr_2,
            self.smallest_crit_fr_3,
            self.smallest_crit_le_0,
            self.smallest_crit_le_1,
        ]
        dist_check_signal = [
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI1],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR1],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR3],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE1],
        ]
        smallest_dist_re = [
            self.smallest_dist_ri_3,
            self.smallest_dist_le_3,
            self.smallest_dist_ri_2,
            self.smallest_dist_le_2,
            self.smallest_dist_re_0,
            self.smallest_dist_re_1,
            self.smallest_dist_re_2,
            self.smallest_dist_re_3,
        ]
        smallest_crit_re = [
            self.smallest_crit_ri_3,
            self.smallest_crit_le_3,
            self.smallest_crit_ri_2,
            self.smallest_crit_le_2,
            self.smallest_crit_re_0,
            self.smallest_crit_re_1,
            self.smallest_crit_re_2,
            self.smallest_crit_re_3,
        ]
        rear_dist_signal = [
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI3],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE3],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE1],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE3],
        ]

        signal_summary, verdict = pdwh.sector_evaluation(smallest_dist_re, smallest_crit_re, rear_dist_signal)

        shortest_distance = min(self.short_dist_1)
        idx = -1
        for i, obj1_short_dist in enumerate(self.short_dist_1):
            if obj1_short_dist == shortest_distance:
                obj1_short_dist = round(obj1_short_dist, 3)
                idx = i
                break
        for j in range(4):
            crit_lvl = smallest_crit_re[j + 4]
            if crit_lvl.iat[idx] != 0:
                summary_txt = f"The shortest evaluated distance between object and ego vehicle is {obj1_short_dist} m and criticality level = {crit_lvl.iat[idx]}"
            else:
                summary_txt = f"The object is detected in wrong sector at {obj1_short_dist} m"

        if any(verdict) and shortest_distance <= pdw_sector_length.PDW_SECTOR_LENGTH:
            signal_summary, verdict = pdwh.sector_evaluation(
                sector_dist_check_list, sector_crit_check_list, dist_check_signal
            )

            if any(verdict):
                self.result.measured_result = FALSE
                signal_summary, verdict = pdwh.sector_evaluation(
                    sector_dist_check_list, sector_crit_check_list, dist_check_signal
                )
                signal_summary["AP.testEvaluation.shortestDistanceCM[1]"] = summary_txt
            else:
                signal_summary, verdict = pdwh.sector_evaluation(smallest_dist_re, smallest_crit_re, rear_dist_signal)
                self.result.measured_result = TRUE
                signal_summary["AP.testEvaluation.shortestDistanceCM[1]"] = summary_txt
        else:
            self.result.measured_result = FALSE
            signal_summary["AP.testEvaluation.shortestDistanceCM[1]"] = "No object detected"

        self.result.measured_result = TRUE if verdict_state == TRUE else FALSE
        signal_summary["AP.drvWarnStatus.pdwState_nu"] = (
            f" PDW function is {activate_metod} state with pdwState = {pdwState_No_value} ({pdwState_value}) ."
        )

        signal_summary["AP.drvWarnStatus.pdwSystemState_nu"] = (
            f" PDW function is {activate_metod} state with pdwSystemState = {pdwSysState_No_value} ({pdwSysState_value})."
        )

        # signal_summary = sector_evaluation(smallest_dist_le,smallest_crit_le,"Left")[0]
        remark = " ".join("Check if each segment of front sector had a PDW object detection.".split())
        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        # add the needed signals in the plot
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_crit_ri_3,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYRI3],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_dist_ri_3,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI3],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_crit_le_3,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYLE3],
            )
        )

        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_dist_le_3,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE3],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_crit_ri_2,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYRI2],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_dist_ri_2,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI2],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_crit_le_2,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYLE2],
            )
        )

        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_dist_le_2,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE2],
            )
        )
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=smallest_dist_re[i + 4],
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE.format(i)],
                )
            )
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=smallest_crit_re[i + 4],
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYRE.format(i)],
                )
            )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.short_dist_1,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.OBSTACE_DISTANCE1],
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
    name="PDW Dynamic_Rear",
    description=("PDW shall detect all dynamic obstacles in the rear side of the car."),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class PDWDynamicRear(TestCase):
    """Example test case."""  # required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # required docstring
        return [
            TestStepPDW,
            TestPDWRear,
        ]  # in this list all the needed test steps are included


@teststep_definition(
    step_number=5,
    name="Left sectors",  # this would be shown as a test step name in html report
    description=(
        "This test step evaluates the left sector signals for PDW function when a dynamic obstacle is present iside the sector."
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestPDWLeft(TestStepPDW):
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
        super().process(**kwargs)
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
        ap_time = self.ap_time
        activate_metod = "not activated"
        pdwState_No_value = pdwState.PDW_INT_STATE_INIT
        pdwState_value = "PDW_INT_STATE_INIT"
        pdwSysState_No_value = pdwSysState.PDW_INIT
        pdwSysState_value = "PDW_INIT"
        verdict_state = DATA_NOK
        ap_time = self.ap_time
        act_btn_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_BTN
        act_auto_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_AUTO
        act_rg_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_R_GEAR
        if act_btn_mask.any():
            activate_metod = "activated by button"
            pdwState_No_value = pdwState.PDW_INT_STATE_ACT_BTN
            pdwState_value = "PDW_INT_STATE_ACT_BTN"
            pdwSysState_No_value = pdwSysState.PDW_ACTIVATED_BY_BUTTON
            pdwSysState_value = "PDW_ACTIVATED_BY_BUTTON"
            verdict_state = TRUE
        elif act_auto_mask.any():
            activate_metod = "automatically activated"
            pdwState_No_value = pdwState.PDW_INT_STATE_ACT_AUTO
            pdwState_value = "PDW_INT_STATE_ACT_AUTO"
            pdwSysState_No_value = pdwSysState.PDW_AUTOMATICALLY_ACTIVATED
            pdwSysState_value = "PDW_AUTOMATICALLY_ACTIVATED"
            verdict_state = TRUE
        elif act_rg_mask.any():
            activate_metod = "reverse gear"
            pdwState_No_value = pdwState.PDW_INT_STATE_ACT_R_GEAR
            pdwState_value = "PDW_INT_STATE_ACT_R_GEAR"
            pdwSysState_No_value = pdwSysState.PDW_ACTIVATED_BY_R_GEAR
            pdwSysState_value = "PDW_ACTIVATED_BY_R_GEAR"
            verdict_state = TRUE
        else:
            activate_metod = "not activated"
            pdwState_No_value = pdwState.PDW_INT_STATE_INIT
            pdwState_value = "PDW_INT_STATE_INIT"
            pdwSysState_No_value = pdwSysState.PDW_INIT
            pdwSysState_value = "PDW_INIT"
            verdict_state = FALSE

        sector_dist_check_list = [
            self.smallest_dist_re_2,
            self.smallest_dist_re_3,
            self.smallest_dist_fr_2,
            self.smallest_dist_fr_3,
            self.smallest_dist_ri_0,
            self.smallest_dist_ri_1,
            self.smallest_dist_ri_2,
            self.smallest_dist_ri_3,
        ]
        sector_crit_check_list = [
            self.smallest_crit_re_2,
            self.smallest_crit_re_3,
            self.smallest_crit_fr_2,
            self.smallest_crit_fr_3,
            self.smallest_crit_ri_0,
            self.smallest_crit_ri_1,
            self.smallest_crit_ri_2,
            self.smallest_crit_ri_3,
        ]
        dist_check_signal = [
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE3],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR3],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI1],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERI3],
        ]
        smallest_dist_le = [
            self.smallest_dist_fr_0,
            self.smallest_dist_re_0,
            self.smallest_dist_fr_1,
            self.smallest_dist_re_1,
            self.smallest_dist_le_0,
            self.smallest_dist_le_1,
            self.smallest_dist_le_2,
            self.smallest_dist_le_3,
        ]
        smallest_crit_le = [
            self.smallest_crit_fr_0,
            self.smallest_crit_re_0,
            self.smallest_crit_fr_1,
            self.smallest_crit_re_1,
            self.smallest_crit_le_0,
            self.smallest_crit_le_1,
            self.smallest_crit_le_2,
            self.smallest_crit_le_3,
        ]
        left_dist_signal = [
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR1],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE1],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE1],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE3],
        ]

        signal_summary, verdict = pdwh.sector_evaluation(smallest_dist_le, smallest_crit_le, left_dist_signal)

        shortest_distance = min(self.short_dist_1)
        idx = -1
        for i, obj1_short_dist in enumerate(self.short_dist_1):
            if obj1_short_dist == shortest_distance:
                obj1_short_dist = round(obj1_short_dist, 3)
                idx = i
                break
        for j in range(4):
            crit_lvl = smallest_crit_le[j + 4]
            if crit_lvl.iat[idx] != 0:
                summary_txt = f"The shortest evaluated distance between object and ego vehicle is {obj1_short_dist} m and criticality level = {crit_lvl.iat[idx]}"
            else:
                summary_txt = f"The object is detected in wrong sector at {obj1_short_dist} m"

        if any(verdict) and shortest_distance <= pdw_sector_length.PDW_SECTOR_LENGTH:
            signal_summary, verdict = pdwh.sector_evaluation(
                sector_dist_check_list, sector_crit_check_list, dist_check_signal
            )

            if any(verdict):
                self.result.measured_result = FALSE
                signal_summary, verdict = pdwh.sector_evaluation(
                    sector_dist_check_list, sector_crit_check_list, dist_check_signal
                )
                signal_summary["AP.testEvaluation.shortestDistanceCM[1]"] = summary_txt
            else:
                signal_summary, verdict = pdwh.sector_evaluation(smallest_dist_le, smallest_crit_le, left_dist_signal)
                self.result.measured_result = TRUE
                signal_summary["AP.testEvaluation.shortestDistanceCM[1]"] = summary_txt
        else:
            self.result.measured_result = FALSE
            signal_summary["AP.testEvaluation.shortestDistanceCM[1]"] = "No object detected"

        self.result.measured_result = TRUE if verdict_state == TRUE else FALSE
        signal_summary["AP.drvWarnStatus.pdwState_nu"] = (
            f" PDW function is {activate_metod} state with pdwState = {pdwState_No_value} ({pdwState_value}) ."
        )

        signal_summary["AP.drvWarnStatus.pdwSystemState_nu"] = (
            f" PDW function is {activate_metod} state with pdwSystemState = {pdwSysState_No_value} ({pdwSysState_value})."
        )

        # signal_summary = sector_evaluation(smallest_dist_le,smallest_crit_le,"Left")[0]
        remark = " ".join("Check if each segment of front sector had a PDW object detection.".split())
        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        # add the needed signals in the plot
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_crit_fr_0,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYFR0],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_dist_fr_0,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR0],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_crit_re_0,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYRE0],
            )
        )

        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_dist_re_0,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE0],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_crit_fr_1,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYFR1],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_dist_fr_1,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR1],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_crit_re_1,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYRE1],
            )
        )

        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.smallest_dist_re_1,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCERE1],
            )
        )
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=smallest_dist_le[i + 4],
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCELE.format(i)],
                )
            )
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=smallest_crit_le[i + 4],
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITYLE.format(i)],
                )
            )
        fig.add_trace(
            go.Scatter(
                x=ap_time,
                y=self.short_dist_1,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.OBSTACE_DISTANCE1],
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
    name="PDW Dynamic_Left",
    description=("PDW shall detect all dynamic obstacles in the left side of the car."),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class PDWDynamicLeft(TestCase):
    """Example test case."""  # required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # required docstring
        return [
            TestStepPDW,
            TestPDWLeft,
        ]  # in this list all the needed test steps are included
