"""LSCA initialization after ignition on"""

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

SIGNAL_DATA = "LSCA_INITIALIZATION_CHECK"


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
            self.Columns.LSCA_STATE: "MTS.MTA_ADC5.MF_LSCA_DATA.statusPort.lscaOverallMode_nu",
            self.Columns.CAR_IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Check LSCA initialized within 1.5s after ignition on.",
    description="The LSCA function shall be initialized after ignition ON (time until initial detection of objects has passed) in less than 1.5s",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class LscaIgnitionConditionCheck(TestStep):
    """LscaIgnitionConditionCheck Test Step."""

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

        t1_idx = None
        t2_idx = None
        time_difference = 0

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Lsca_state']} signal is PASSED, state signal switches to active "
            f"{constants.HilCl.Lsca.LSCA_ACTIVE} within 1.5s (+100 ms tolerance) after {signal_name['Car_ignition']} event.".split()
        )

        """Evaluation part"""

        # Find when ignition is turned ON

        for cnt in range(len(car_ignition_sig)):
            if car_ignition_sig[cnt] == constants.HilCl.CarMaker.IGNITION_ON:
                t1_idx = cnt
                break

        if t1_idx is not None:
            # Find when LSCA becomes active
            for cnt in range(t1_idx, len(lsca_state_sig)):
                if lsca_state_sig[cnt] == constants.HilCl.Lsca.LSCA_ACTIVE:
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                # Calculate the time difference
                time_difference = time_signal[t2_idx] - time_signal[t1_idx]

                if (
                    time_difference < constants.HilCl.Lsca.LSCA_INIT_TIME + constants.HilCl.Lsca.LSCA_TOLERANCE_TIME
                ):  # 1.5 seconds + 100 ms tolerance
                    test_result = fc.PASS
                else:
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Lsca_state']} signal is FAILED, state signal switches to active "
                        f"{constants.HilCl.Lsca.LSCA_ACTIVE} but took longer than 1.6s (1.5s + 100ms tolerance) after {signal_name['Car_ignition']} event happening. "
                        f"Time difference: {time_difference} ms.".split()
                    )
            else:
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Lsca_state']} signal is FAILED, state signal does not switches to active "
                    f"within the observed period after {signal_name['Car_ignition']} event happening.".split()
                )
        else:
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Car_ignition']} is FAILED, Ignition ON event not happened.".split()
            )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["LSCA Initialization Check"] = evaluation1

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
    name="Check LSCA initialized within 1.5s after ignition on.",
    description="The LSCA function shall be initialized after ignition ON (time until initial detection of objects has passed) in less than 1.5s",
)
class LscaIgnitionCondition(TestCase):
    """LscaIgnitionCondition Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            LscaIgnitionConditionCheck,
        ]
