"""Check steering angle velocity while AVG is active."""

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

SIGNAL_DATA = "AVG_STEERING_ANG_VELOCITY"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        WH_ANG_VELOCITY = "Steering_ang_velocity"
        HMI_INFO = "State_on_HMI"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.WH_ANG_VELOCITY: "CM.Steer.WhlVel",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Steering angle velocity check",
    description="Check steering angle velocity while AVG is active",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupAvgWhAngVelCheck(TestStep):
    """AupAvgWhAngVelCheck Test Case."""

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
        wh_ang_vel_signal = read_data["Steering_ang_velocity"].tolist()
        ap_state_signal = read_data["State_on_HMI"].tolist()

        t1_idx = None
        t2_idx = None
        max_wh_ang_vel_avg = None
        evaluation1 = ""

        # Create limit marker for chart
        limit_marker = [constants.HilCl.ApThreshold.AP_V_MAX_STEER_ANG_VEL_RADPS] * len(time_signal)

        """Evaluation part"""
        # Find begining and end of AVG active
        for cnt in range(0, len(ap_state_signal)):
            if (
                ap_state_signal[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING
            ) and t1_idx is None:
                t1_idx = cnt
                continue
            if (
                ap_state_signal[cnt] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING
            ) and t1_idx is not None:
                t2_idx = cnt
                break

        if t1_idx is not None and t2_idx is not None:
            eval_cond = [True] * 1

            # Calculate maxsteering wheel angle velocitywhile AVG active
            tmp_wh_ang_vel = []
            for cnt in range(t1_idx, t2_idx):
                tmp_wh_ang_vel.append(wh_ang_vel_signal[cnt])
            max_wh_ang_vel_avg = round(max(tmp_wh_ang_vel), 5)

            # Check steering wheel angle velocitywhile AVG is active
            for cnt in range(t1_idx, t2_idx):
                if abs(wh_ang_vel_signal[cnt]) > constants.HilCl.ApThreshold.AP_V_MAX_STEER_ANG_VEL_RADPS:
                    eval_cond[0] = False
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Steering_ang_velocity']} signal is FAILED,"
                        f" steering wheel angle velocity is {wh_ang_vel_signal[cnt]} rad/s at {time_signal[cnt]} us"
                        f" during AVG and this is greather than {constants.HilCl.ApThreshold.AP_V_MAX_STEER_ANG_VEL_RADPS}"
                        f" rad/s.".split()
                    )
                    break

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} is FAILED, state of signal never switched to AVG active ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}).".split()
            )

        if all(eval_cond):
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Steering_ang_velocity']} signal is PASSED, "
                f" maximal steering wheel angle velocity is {max_wh_ang_vel_avg} rad/s during AVG and"
                f" this is less than {constants.HilCl.ApThreshold.AP_V_MAX_STEER_ANG_VEL_RADPS}"
                f" rad/s.".split()
            )
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Angle velocity of Steering wheel during AVG active"] = evaluation1

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
                    name="Limit marker for absolute steering angle velocity",
                )
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=wh_ang_vel_signal, mode="lines", name=signal_name["Steering_ang_velocity"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=ap_state_signal, mode="lines", name=signal_name["State_on_HMI"]))

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
            "Max steering wheel angle velocity AVG [rad/s]": {
                "value": max_wh_ang_vel_avg,
                "color": fh.apply_color(
                    max_wh_ang_vel_avg, constants.HilCl.ApThreshold.AP_V_MAX_STEER_ANG_VEL_RADPS, "<"
                ),
            },
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
    name="Angle velocity of steering wheel vehicle while AVG is active",
    description=f"While AVG is active the function shall control the ego-vehicle,"
    f" so that an absolute steering angle velocity at the wheel of"
    f" {constants.HilCl.ApThreshold.AP_V_MAX_STEER_ANG_VEL_RADPS} rad/s (tunable) is not exceeded.",
)
class AupAvgWhAngVel(TestCase):
    """AupAvgWhAngVelCheck Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupAvgWhAngVelCheck,
        ]
