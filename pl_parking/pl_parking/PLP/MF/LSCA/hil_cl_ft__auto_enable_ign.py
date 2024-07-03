"""LSCA automatic enable"""

import logging
import os
import sys

import plotly.graph_objects as go

from pl_parking.PLP.MF import constants

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

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import HilClFuntions, MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.constants import PlotlyTemplate

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "LSCA_AUTO_ENABLED"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        LSCA_STATE = "Lsca_state"
        CAR_IGNITION = "Car_ignition"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.LSCA_STATE: "MTS.ADC5xx_Device.EM_DATA.EmLscaStatusPort.lscaOverallMode_nu",
            self.Columns.CAR_IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Check LSCA automaticly enabled",
    description="Check LSCA automaticly enabled in all ignition cycles in TestRun.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class LscaEnableIgnCheck(TestStep):
    """LscaEnableIgnCheck Test Step."""

    custom_report = MfHilClCustomTeststepReport

    def __init__(self):
        """Init test."""
        super().__init__()

    def process(self, **kwargs):
        """
        This function processes the recorded signal from measurement file, set the result of the test,
        generate plots and additional results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        read_data = self.readers[SIGNAL_DATA]
        test_result = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        """Prepare sinals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        car_ignition_sig = read_data["Car_ignition"].tolist()
        lsca_state_sig = read_data["Lsca_state"].tolist()

        ignition_on_idx = []
        ignition_off_idx = []

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Lsca_state']} is PASSED, state of signal get enabled {constants.HilCl.Lsca.LSCA_ACTIVE} in all ignition cycles.".split()
        )

        # Collect all ignition ON and OFF events
        ignition_on_idx = HilClFuntions.RisingEdge(car_ignition_sig, 0)
        ignition_off_idx = HilClFuntions.FallingEdge(car_ignition_sig, 0)

        """Evaluation part"""
        # Required condition(s) for TestRun
        # 1 - There was at least one Ignition ON and OFF event
        # 2 - Number of Ignition ON and number of Ignition OFF equial

        if len(ignition_on_idx) > 0 and len(ignition_off_idx) > 0 and (len(ignition_on_idx) == len(ignition_off_idx)):
            eval_cond = [True] * 1

            # Check all ignition cycle
            for ign_cycle in range(0, len(ignition_on_idx)):
                # Check LSCA state in actual ignition cycle
                for cnt in range(
                    ignition_on_idx[ign_cycle] + 1, ignition_off_idx[ign_cycle]
                ):  # one sample is 100ms  #added +1 after ign_on
                    if lsca_state_sig[cnt] != constants.HilCl.Lsca.LSCA_ACTIVE:
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Lsca_state']} is FAILED, state of signal is NOT_ACTIVE {constants.HilCl.Lsca.LSCA_ACTIVE} at {time_signal[cnt]} [us] but"
                            f" ignition is ON(1).".split()
                        )
                        eval_cond[0] = False
                        break

                if not eval_cond[0]:
                    break

        elif len(ignition_on_idx) == 0:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Car_ignition']} is FAILED, there is no Ignition ON event (signal switch from 0 to 1) in TestRun.".split()
            )

        elif len(ignition_off_idx) == 0:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Car_ignition']} is FAILED, there is no Ignition OFF (0) event in TestRun.".split()
            )

        elif len(ignition_on_idx) != len(ignition_off_idx):
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Car_ignition']} is FAILED, Ignition ON(1) and Ignition OFF(0) events are not equal in TestRun.".split()
            )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join("The evaluation is FAILED, invalide TestRun".split())

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["LSCA automaticly enabled"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=lsca_state_sig, mode="lines", name=signal_name["Lsca_state"]))
            fig.add_trace(go.Scatter(x=time_signal, y=car_ignition_sig, mode="lines", name=signal_name["Car_ignition"]))
            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        """Calculate parameters to additional table"""
        sw_combatibility = (  # Remainder: Update if SW changed and script working well
            "swfw_apu_adc5-2.1.0-DR2-PLP-B1-PAR230"
        )

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            "Used SW version": {"value": sw_combatibility},
        }

        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="LSCA automaticly enabled",
    description="The LSCA function shall automatically get enabled after every ignition cycle.",
)
class LscaEnableIgn(TestCase):
    """LscaEnableIgn Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            LscaEnableIgnCheck,
        ]
