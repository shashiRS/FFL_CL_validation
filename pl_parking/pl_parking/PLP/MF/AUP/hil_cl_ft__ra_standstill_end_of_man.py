"""Check standtill at end of RA maneuver"""

import logging
import os
import sys

import plotly.graph_objects as go

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
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import HilClFuntions, MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.constants import PlotlyTemplate

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "RA_STANDSTILL_END_OF_MAN"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        SPEED = "Car_speed"
        DRIVING_DIR = "Driving_dir"
        GENERAL_MESSAGE = "General_message"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.SPEED: "MTS.ADAS_CAN.Conti_Veh_CAN.Tachometer.SpeedoSpeed",
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Standstill check at end of RA maneuver",
    description="Check standstill at end of Reverse Assist maneuvering ",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class RaStandstillCheck(TestStep):
    """RaStandstillCheck Test Step."""

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
        car_speed_signal = read_data["Car_speed"].tolist()
        driving_dir_sig = read_data["Driving_dir"].tolist()
        message_sig = read_data["General_message"].tolist()

        t_finished_idx = None
        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Car_speed']} signal is PASSED, ego vehicle reached Standstill at end of RA maneuver.".split()
        )

        """Evaluation part"""
        # Find when general message switches to REVERSE_ASSIST_FINISHED
        for idx, item in enumerate(message_sig):
            if item == constants.HilCl.Hmi.APHMIGeneralMessage.REVERSE_ASSIST_FINISHED:
                t_finished_idx = idx
                break

        if t_finished_idx is not None:
            eval_cond = [True] * 1

            # Check speed of car at end of RA maneuver
            if abs(car_speed_signal[t_finished_idx]) > constants.HilCl.CarMaker.ZERO_SPEED_KMH:
                eval_cond[0] = False

                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Car_speed']} signal is FAILED, absolute velocity of ego vehicle is {abs(car_speed_signal[t_finished_idx])} km/h at end of RA maneuver."
                    " Ego vehicle is not in standstill at end of RA maneuver."
                    f" State of {signal_name['Driving_dir']} is {driving_dir_sig[t_finished_idx]}.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['General_message']} signal is FAILED, signal never switched to REVERSE_ASSIST_FINISHED ({constants.HilCl.Hmi.APHMIGeneralMessage.REVERSE_ASSIST_FINISHED})."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Standstill check at end of RA maneuver"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=time_signal, y=car_speed_signal, mode="lines", name=signal_name["Car_speed"] + " [km/h]")
            )
            fig.add_trace(go.Scatter(x=time_signal, y=driving_dir_sig, mode="lines", name=signal_name["Driving_dir"]))
            fig.add_trace(go.Scatter(x=time_signal, y=message_sig, mode="lines", name=signal_name["General_message"]))

            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        """Calculate parameters to additional table"""

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
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
    name="Standstill at end of Reverse Assist",
    description="The RA function shall brake the ego vehicle to standstill at the end of the maneuver.",
)
class RaStandstill(TestCase):
    """RaStandstill Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            RaStandstillCheck,
        ]
