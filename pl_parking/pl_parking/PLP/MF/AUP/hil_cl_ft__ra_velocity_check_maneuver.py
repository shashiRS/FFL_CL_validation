"""Check velocity while Reverse Assist is maneuvering."""

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

SIGNAL_DATA = "RA_VEH_LONG_SPEED"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        CAR_SPEED = "Car_speed"
        GENERAL_SCREEN = "General_screen"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CAR_SPEED: "MTS.ADAS_CAN.Conti_Veh_CAN.Tachometer.SpeedoSpeed",
            self.Columns.GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Velocity check",
    description="Check velocity while Reverse assist is maneuvering ",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class RASpeedCheck(TestStep):
    """RASpeedCheck Test Step."""

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
        ap_state_signal = read_data["General_screen"].tolist()

        t1_idx = None
        t2_idx = None
        max_speed_avg = None
        evaluation1 = ""

        # Create limit marker for chart
        limit_marker = [constants.HilCl.ApThreshold.AP_G_MAX_AVG_CTRL_V_MPS] * len(time_signal)

        """Evaluation part"""
        # Find begining and end of Reverse Assist is maneuvering
        for cnt in range(0, len(ap_state_signal)):
            if (ap_state_signal[cnt] == constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST) and t1_idx is None:
                t1_idx = cnt
                continue
            if (ap_state_signal[cnt] != constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST) and t1_idx is not None:
                t2_idx = cnt
                break

        if t1_idx is not None and t2_idx is not None:
            eval_cond = [True] * 1

            # Check vehicle speed while Reverse Assist is maneuvering
            for cnt in range(t1_idx, t2_idx):
                if abs(car_speed_signal[cnt]) > constants.HilCl.ApThreshold.AP_G_MAX_AVG_CTRL_V_MPS * 3.6:
                    eval_cond[0] = False
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Car_speed']} signal"
                        f" is FAILED, velocity is {car_speed_signal[cnt] / 3.6} m/s at {time_signal[cnt]} us"
                        f" during Reverse Assist is maneuvering and this is greater than {constants.HilCl.ApThreshold.AP_G_MAX_AVG_CTRL_V_MPS}"
                        f" m/s.".split()
                    )
                    break

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['General_screen']} is FAILED, state of signal never switched to REVERSE_ASSIST ({constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST})."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        if all(eval_cond):
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Car_speed']} signal is PASSED,"
                f" maxmial velocity is {max_speed_avg} m/s during Reverse Assist is maneuvering and this is less than"
                f" {constants.HilCl.ApThreshold.AP_G_MAX_AVG_CTRL_V_MPS} m/s.".split()
            )
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Ego vehicle velocity  during Reverse Assist is maneuvering"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=time_signal,
                    y=limit_marker,
                    mode="lines",
                    line=go.scatter.Line(color="purple"),
                    name="Limit marker for absolute longitudinal velocity of ego vehicle",
                )
            )
            fig.add_trace(go.Scatter(x=time_signal, y=car_speed_signal, mode="lines", name=signal_name["Car_speed"]))
            fig.add_trace(go.Scatter(x=time_signal, y=ap_state_signal, mode="lines", name=signal_name["General_screen"]))

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
    name="Velocity of ego vehicle while Reverse Assist is maneuvering",
    description=f"While Reverse Assist is maneuvering the function shall control the ego vehicle in a"
    f" way that the absolute longitudinal velocity of"
    f" {constants.HilCl.ApThreshold.AP_G_MAX_AVG_CTRL_V_MPS} m/s is not exceeded.",
)
class RASpeed(TestCase):
    """RASpeed Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            RASpeedCheck,
        ]
