"""Example functional test"""  # this is a required docstring

"""import libraries"""
import logging
import os
import sys

import pandas as pd
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
ALIAS = "PDW_STATIC_FTP"


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
            self.Columns.GEARBOX_STATE: "AP.odoInputPort.odoSigFcanPort.gearboxCtrlStatus.gearCur_nu",
            self.Columns.EPB_SWITCH: "DM.BrakePark",
            self.Columns.SECTOR_CRITICALITYFR0: "AP.pdcpSectorsPort.sectorsFront_0.criticalityLevel_nu",
            self.Columns.SECTOR_DISTANCEFR0: "AP.pdcpSectorsPort.sectorsFront_0.smallestDistance_m",
            self.Columns.SECTOR_CRITICALITYLE0: "AP.pdcpSectorsPort.sectorsLeft_0.criticalityLevel_nu",
            self.Columns.SECTOR_DISTANCELE0: "AP.pdcpSectorsPort.sectorsLeft_0.smallestDistance_m",
            self.Columns.SECTOR_CRITICALITYRE0: "AP.pdcpSectorsPort.sectorsRear_0.criticalityLevel_nu",
            self.Columns.SECTOR_DISTANCERE0: "AP.pdcpSectorsPort.sectorsRear_0.smallestDistance_m",
            self.Columns.SECTOR_CRITICALITYRI0: "AP.pdcpSectorsPort.sectorsRight_0.criticalityLevel_nu",
            self.Columns.SECTOR_DISTANCERI0: "AP.pdcpSectorsPort.sectorsRight_0.smallestDistance_m",
            self.Columns.SECTOR_CRITICALITYFR1: "AP.pdcpSectorsPort.sectorsFront_1.criticalityLevel_nu",
            self.Columns.SECTOR_DISTANCEFR1: "AP.pdcpSectorsPort.sectorsFront_1.smallestDistance_m",
            self.Columns.SECTOR_CRITICALITYLE1: "AP.pdcpSectorsPort.sectorsLeft_1.criticalityLevel_nu",
            self.Columns.SECTOR_DISTANCELE1: "AP.pdcpSectorsPort.sectorsLeft_1.smallestDistance_m",
            self.Columns.SECTOR_CRITICALITYRE1: "AP.pdcpSectorsPort.sectorsRear_1.criticalityLevel_nu",
            self.Columns.SECTOR_DISTANCERE1: "AP.pdcpSectorsPort.sectorsRear_1.smallestDistance_m",
            self.Columns.SECTOR_CRITICALITYRI1: "AP.pdcpSectorsPort.sectorsRight_1.criticalityLevel_nu",
            self.Columns.SECTOR_DISTANCERI1: "AP.pdcpSectorsPort.sectorsRight_1.smallestDistance_m",
            self.Columns.SECTOR_CRITICALITYFR2: "AP.pdcpSectorsPort.sectorsFront_2.criticalityLevel_nu",
            self.Columns.SECTOR_DISTANCEFR2: "AP.pdcpSectorsPort.sectorsFront_2.smallestDistance_m",
            self.Columns.SECTOR_CRITICALITYLE2: "AP.pdcpSectorsPort.sectorsLeft_2.criticalityLevel_nu",
            self.Columns.SECTOR_DISTANCELE2: "AP.pdcpSectorsPort.sectorsLeft_2.smallestDistance_m",
            self.Columns.SECTOR_CRITICALITYRE2: "AP.pdcpSectorsPort.sectorsRear_2.criticalityLevel_nu",
            self.Columns.SECTOR_DISTANCERE2: "AP.pdcpSectorsPort.sectorsRear_2.smallestDistance_m",
            self.Columns.SECTOR_CRITICALITYRI2: "AP.pdcpSectorsPort.sectorsRight_2.criticalityLevel_nu",
            self.Columns.SECTOR_DISTANCERI2: "AP.pdcpSectorsPort.sectorsRight_2.smallestDistance_m",
            self.Columns.SECTOR_CRITICALITYFR3: "AP.pdcpSectorsPort.sectorsFront_3.criticalityLevel_nu",
            self.Columns.SECTOR_DISTANCEFR3: "AP.pdcpSectorsPort.sectorsFront_3.smallestDistance_m",
            self.Columns.SECTOR_CRITICALITYLE3: "AP.pdcpSectorsPort.sectorsLeft_3.criticalityLevel_nu",
            self.Columns.SECTOR_DISTANCELE3: "AP.pdcpSectorsPort.sectorsLeft_3.smallestDistance_m",
            self.Columns.SECTOR_CRITICALITYRE3: "AP.pdcpSectorsPort.sectorsRear_3.criticalityLevel_nu",
            self.Columns.SECTOR_DISTANCERE3: "AP.pdcpSectorsPort.sectorsRear_3.smallestDistance_m",
            self.Columns.SECTOR_CRITICALITYRI3: "AP.pdcpSectorsPort.sectorsRight_3.criticalityLevel_nu",
            self.Columns.SECTOR_DISTANCERI3: "AP.pdcpSectorsPort.sectorsRight_3.smallestDistance_m",
        }


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="Initial evaluation",
    description=("This test step evaluates the activation conditions for pdw test case."),
    expected_result=BooleanResult(TRUE),
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

        class pdwState:
            PDW_INT_STATE_INIT = 0
            PDW_INT_STATE_ACT_BTN = 1  # activat de la buton
            PDW_INT_STATE_ACT_R_GEAR = 2  # activat de la reverse gear
            PDW_INT_STATE_ACT_AP = 3  # activat de la AutoPark
            PDW_INT_STATE_ACT_AUTO = 4  # activare automata cand depisteaza obiect critic
            PDW_INT_STATE_ACT_ROLLBACK = 5  # activare cand deplaseaza in spate fara viteza de la motor
            PDW_INT_STATE_ACT_RA = 6  # activare ...
            PDW_INT_STATE_DEACT_INIT = 7
            PDW_INT_STATE_DEACT_BTN = 8
            PDW_INT_STATE_DEACT_SPEED = 9
            PDW_INT_STATE_DEACT_P_GEAR = 10
            PDW_INT_STATE_DEACT_EPB = 11
            PDW_INT_STATE_DEACT_AP_FIN = 12
            PDW_INT_STATE_FAILURE = 13
            PDW_INT_NUM_STATES = 14

        class pdwSystemState:
            PDW_INIT = 0
            PDW_OFF = 1
            PDW_ACTIVATED_BY_R_GEAR = 2
            PDW_ACTIVATED_BY_BUTTON = 3
            PDW_AUTOMATICALLY_ACTIVATED = 4
            PDW_FAILURE = 5

        signal_summary = {}
        signals = self.readers[ALIAS]  # Make a dataframe(df) with all signals extracted from Signals class

        self.velocity = signals[Signals.Columns.VELOCITY]
        self.ap_time = signals[Signals.Columns.TIME]
        self.pdw_state = signals[Signals.Columns.PDW_STATE]
        self.pdw_sys_state = signals[Signals.Columns.PDW_SYSTEM_STATE]

        act_btn_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_BTN
        act_auto_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_AUTO
        act_rg_mask = self.pdw_state == pdwState.PDW_INT_STATE_ACT_R_GEAR

        activate_metod = "not activated"
        if act_btn_mask.any():
            activate_metod = "button"
        elif act_auto_mask.any():
            activate_metod = "automated"
        elif act_rg_mask.any():
            activate_metod = "reverse gear"

        self.result.measured_result = TRUE if activate_metod != "not activated" else FALSE

        signal_summary["Method of activation"] = f"The vehicle was activated by {activate_metod}."
        remark = " ".join("".split())
        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        # add the needed signals in the plot

        fig.add_trace(go.Scatter(x=self.ap_time, y=self.velocity, mode="lines", name=Signals.Columns.VELOCITY))
        fig.add_trace(go.Scatter(x=self.ap_time, y=self.pdw_state, mode="lines", name=Signals.Columns.PDW_STATE))
        fig.add_trace(
            go.Scatter(x=self.ap_time, y=self.pdw_sys_state, mode="lines", name=Signals.Columns.PDW_SYSTEM_STATE)
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
    name="Left sector",  # this would be shown as a test step name in html report
    description=(
        "This test step evaluate the left sector signals for PDW function"
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepPDWLeft(TestStep):
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
        signals = self.readers[ALIAS]

        signal_summary = {}
        ap_time = signals[Signals.Columns.TIME]
        self.smallest_dist_le_0 = signals[Signals.Columns.SECTOR_DISTANCELE0]
        self.smallest_dist_le_1 = signals[Signals.Columns.SECTOR_DISTANCELE1]
        self.smallest_dist_le_2 = signals[Signals.Columns.SECTOR_DISTANCELE2]
        self.smallest_dist_le_3 = signals[Signals.Columns.SECTOR_DISTANCELE3]

        self.smallest_crit_le_0 = signals[Signals.Columns.SECTOR_CRITICALITYLE0]
        self.smallest_crit_le_1 = signals[Signals.Columns.SECTOR_CRITICALITYLE1]
        self.smallest_crit_le_2 = signals[Signals.Columns.SECTOR_CRITICALITYLE2]
        self.smallest_crit_le_3 = signals[Signals.Columns.SECTOR_CRITICALITYLE3]

        smallest_dist_le = [
            self.smallest_dist_le_0,
            self.smallest_dist_le_1,
            self.smallest_dist_le_2,
            self.smallest_dist_le_3,
        ]
        smallest_crit_le = [
            self.smallest_crit_le_0,
            self.smallest_crit_le_1,
            self.smallest_crit_le_2,
            self.smallest_crit_le_3,
        ]

        signal_summary, verdict = sector_evaluation(smallest_dist_le, smallest_crit_le, "Left")

        if any(verdict):
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        # signal_summary = sector_evaluation(smallest_dist_le,smallest_crit_le,"Left")[0]
        remark = " ".join("Check if each segment of left sector had a PDW object detection.".split())
        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=ap_time, y=smallest_dist_le[i], mode="lines", name=Signals.Columns.SECTOR_DISTANCELE.format(i)
                )
            )
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=ap_time, y=smallest_crit_le[i], mode="lines", name=Signals.Columns.SECTOR_CRITICALITYLE.format(i)
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
    step_number=3,
    name="Rear sector",  # this would be shown as a test step name in html report
    description=(
        "This test step evaluate the rear sector signals for PDW function"
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepPDWRear(TestStep):
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
        signals = self.readers[ALIAS]
        ap_time = signals[Signals.Columns.TIME]
        self.smallest_dist_re_0 = signals[Signals.Columns.SECTOR_DISTANCERE0]
        self.smallest_dist_re_1 = signals[Signals.Columns.SECTOR_DISTANCERE1]
        self.smallest_dist_re_2 = signals[Signals.Columns.SECTOR_DISTANCERE2]
        self.smallest_dist_re_3 = signals[Signals.Columns.SECTOR_DISTANCERE3]
        self.smallest_crit_re_0 = signals[Signals.Columns.SECTOR_CRITICALITYRE0]
        self.smallest_crit_re_1 = signals[Signals.Columns.SECTOR_CRITICALITYRE1]
        self.smallest_crit_re_2 = signals[Signals.Columns.SECTOR_CRITICALITYRE2]
        self.smallest_crit_re_3 = signals[Signals.Columns.SECTOR_CRITICALITYRE3]

        smallest_dist_re = [
            self.smallest_dist_re_0,
            self.smallest_dist_re_1,
            self.smallest_dist_re_2,
            self.smallest_dist_re_3,
        ]
        smallest_crit_re = [
            self.smallest_crit_re_0,
            self.smallest_crit_re_1,
            self.smallest_crit_re_2,
            self.smallest_crit_re_3,
        ]

        signal_summary, verdict = sector_evaluation(smallest_dist_re, smallest_crit_re, "Rear")

        if any(verdict):
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        # signal_summary = sector_evaluation(smallest_dist_le,smallest_crit_le,"Left")[0]
        remark = " ".join("Check if each segment of rear sector had a PDW object detection.".split())
        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        # add the needed signals in the plot
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=ap_time, y=smallest_dist_re[i], mode="lines", name=Signals.Columns.SECTOR_DISTANCERE.format(i)
                )
            )
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=ap_time, y=smallest_crit_re[i], mode="lines", name=Signals.Columns.SECTOR_CRITICALITYRE.format(i)
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
    step_number=4,
    name="Front sector",
    description=("This test step evaluate the front sector signals for PDW function"),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class TestStepPDWFront(TestStep):
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
        signals = self.readers[ALIAS]

        signal_summary = {}
        ap_time = signals[Signals.Columns.TIME]
        self.smallest_dist_fr_0 = signals[Signals.Columns.SECTOR_DISTANCEFR0]
        self.smallest_dist_fr_1 = signals[Signals.Columns.SECTOR_DISTANCEFR1]
        self.smallest_dist_fr_2 = signals[Signals.Columns.SECTOR_DISTANCEFR2]
        self.smallest_dist_fr_3 = signals[Signals.Columns.SECTOR_DISTANCEFR3]
        self.smallest_crit_fr_0 = signals[Signals.Columns.SECTOR_CRITICALITYFR0]
        self.smallest_crit_fr_1 = signals[Signals.Columns.SECTOR_CRITICALITYFR1]
        self.smallest_crit_fr_2 = signals[Signals.Columns.SECTOR_CRITICALITYFR2]
        self.smallest_crit_fr_3 = signals[Signals.Columns.SECTOR_CRITICALITYFR3]

        smallest_dist_fr = [
            self.smallest_dist_fr_0,
            self.smallest_dist_fr_1,
            self.smallest_dist_fr_2,
            self.smallest_dist_fr_3,
        ]
        smallest_crit_fr = [
            self.smallest_crit_fr_0,
            self.smallest_crit_fr_1,
            self.smallest_crit_fr_2,
            self.smallest_crit_fr_3,
        ]

        signal_summary, verdict = sector_evaluation(smallest_dist_fr, smallest_crit_fr, "Front")

        if any(verdict):
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        # signal_summary = sector_evaluation(smallest_dist_le,smallest_crit_le,"Left")[0]
        remark = " ".join("Check if each segment of front sector had a PDW object detection.".split())
        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        # add the needed signals in the plot
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=ap_time, y=smallest_dist_fr[i], mode="lines", name=Signals.Columns.SECTOR_DISTANCEFR.format(i)
                )
            )
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=ap_time, y=smallest_crit_fr[i], mode="lines", name=Signals.Columns.SECTOR_CRITICALITYFR.format(i)
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
    step_number=5,
    name="Right sector",  # this would be shown as a test step name in html report
    description=(
        "This test step evaluate the right sector signals for PDW function"
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepPDWRight(TestStep):
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
        signals = self.readers[ALIAS]

        signal_summary = {}
        ap_time = signals[Signals.Columns.TIME]
        self.smallest_dist_ri_0 = signals[Signals.Columns.SECTOR_DISTANCERI0]
        self.smallest_dist_ri_1 = signals[Signals.Columns.SECTOR_DISTANCERI1]
        self.smallest_dist_ri_2 = signals[Signals.Columns.SECTOR_DISTANCERI2]
        self.smallest_dist_ri_3 = signals[Signals.Columns.SECTOR_DISTANCERI3]
        self.smallest_crit_ri_0 = signals[Signals.Columns.SECTOR_CRITICALITYRI0]
        self.smallest_crit_ri_1 = signals[Signals.Columns.SECTOR_CRITICALITYRI1]
        self.smallest_crit_ri_2 = signals[Signals.Columns.SECTOR_CRITICALITYRI2]
        self.smallest_crit_ri_3 = signals[Signals.Columns.SECTOR_CRITICALITYRI3]

        smallest_dist_ri = [
            self.smallest_dist_ri_0,
            self.smallest_dist_ri_1,
            self.smallest_dist_ri_2,
            self.smallest_dist_ri_3,
        ]
        smallest_crit_ri = [
            self.smallest_crit_ri_0,
            self.smallest_crit_ri_1,
            self.smallest_crit_ri_2,
            self.smallest_crit_ri_3,
        ]

        signal_summary, verdict = sector_evaluation(smallest_dist_ri, smallest_crit_ri, "Right")

        if any(verdict):
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        # signal_summary = sector_evaluation(smallest_dist_le,smallest_crit_le,"Left")[0]
        remark = " ".join("Check if each segment of right sector had a PDW object detection.".split())
        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        # add the needed signals in the plot
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=ap_time, y=smallest_dist_ri[i], mode="lines", name=Signals.Columns.SECTOR_DISTANCERI.format(i)
                )
            )
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=ap_time, y=smallest_crit_ri[i], mode="lines", name=Signals.Columns.SECTOR_CRITICALITYRI.format(i)
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


# Define the test case definition. This will include the name of the test case and a description of the test.
@testcase_definition(
    name="PDW static",
    description=(
        "PDW shall detect all obstacles around the car, each obstacle situated inside each sector at a distance"
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class PDWStaticTestCase(TestCase):
    """Example test case."""  # required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # required docstring
        return [
            TestStepPDW,
            TestStepPDWLeft,
            TestStepPDWRight,
            TestStepPDWFront,
            TestStepPDWRear,
        ]  # in this list all the needed test steps are included


def sector_evaluation(smallest_dist_f: list, critical_level_f: list, type_of_sector: str):
    """
    This function evaluate_signals takes smallest_dist_f (an array with 4 signals of smallest_distance for each front)
    and critical_level_f (an array with 4 signals of critical for each front) as parameters. It then iterates over each front,
    checks if the critical level (a mask that checks if an object was detected) is non-zero, and evaluates accordingly.
    Finally, it returns a dictionary signal_summary where each segment of front is associated with its evaluation string.
    """
    signal_summary = {}
    verdict = []

    for idx, (smallest_dist, critical_level) in enumerate(zip(smallest_dist_f, critical_level_f)):
        critical_level_mask = any(critical_level)  # Checking if any value in the array is non-zero
        if critical_level_mask:
            verdict.append(True)
            smallest_dist_front = round(min(smallest_dist), 3)
            evaluation = f"The criticality level = {critical_level_f[idx].iat[-1]} with distance towards object {smallest_dist_front}."
        else:
            verdict.append(False)
            evaluation = "No object detected."

        signal_summary[f"{type_of_sector} sector {idx}"] = evaluation
    return signal_summary, verdict


def convert_dict_to_pandas(signal_summary: dict, table_remark="", table_title=""):
    """Function to personalize singal summary table"""
    evaluation_summary = pd.DataFrame(
        {
            "Evaluation": {key: key for key, val in signal_summary.items()},
            "Results": {key: val for key, val in signal_summary.items()},
        }
    )
    return fh.build_html_table(
        evaluation_summary,
        table_remark,
        table_title,
    )
