"""LSCA active value driver's seat dependence check in forward mode"""

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
from pl_parking.common_ft_helper import MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.constants import GeneralConstants, PlotlyTemplate

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "LSCA_DRIVERS_SEAT"


class ValidationSignals(MDFSignalDefinition):
    """Example signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        LSCA_ACT = "Lsca_active"
        DRIVERS_SEAT = "Drievers_seat"
        SPEED = "Car_speed"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.DRIVERS_SEAT: (
                "MTS.ADC5xx_Device.VD_DATA.vehicleOccupancyStatusPort.seatOccupancyStatus.driver_nu"
            ),
            self.Columns.LSCA_ACT: "MTS.ADC5xx_Device.EM_DATA.EmLscaStatusPort.lscaOverallMode_nu",
            self.Columns.SPEED: "MTS.ADC5xx_Device.EM_DATA.EmEgoMotionPort.vel_mps",
        }


example_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="LSCA active value driver's seat dependence check in forward mode",
    description=(
        "Check LSCA active value if driver's seat is FREE and if it is OCCUPED. Ego vehicle speed is in accepted speed"
        " range."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class LscaSeatCheck(TestStep):
    """Example test step."""

    custom_report = MfHilClCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        read_data = self.readers[SIGNAL_DATA].signals
        test_result = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        """Prepare sinals and variables"""
        signal_summary = {}
        time_signal = read_data["ts"].tolist()
        drivers_seat_signal = read_data["Drievers_seat"].tolist()
        lsca_act_signal = read_data["Lsca_active"].tolist()
        car_speed_signal = read_data["Car_speed"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Lsca_active']} is PASSED, signal is NOT_ACTIVE when"
            f" {signal_name['Drievers_seat']} is NOT_OCCUPIED".split()
        )

        """Evaluation part"""
        # Find t1_idx when speed > min and LSCA shall active
        for speed in car_speed_signal:
            if speed > constants.HilCl.Lsca.LSCA_B_FORW_SPEED_MIN_ON_MPS:
                t1_idx = car_speed_signal.index(speed)
                break

        for state in drivers_seat_signal:
            # Find t2_idx when seat set to FREE
            if state == constants.HilCl.Seat.DRIVERS_FREE and t1_idx is not None and t2_idx is None:
                t2_idx = drivers_seat_signal.index(state)
                continue
            # Find t3_idx when seat set to OCCUPED again
            if state == constants.HilCl.Seat.DRIVERS_OCCUPIED and t2_idx is not None and t3_idx is None:
                t3_idx = drivers_seat_signal.index(state)
                break

        if t1_idx is not None and t2_idx is not None and t3_idx is not None:
            eval_cond = [True] * 2

            # Check LSCA active during OCCUPED driver's seat
            for cnt in range(t1_idx, t2_idx):
                if lsca_act_signal[cnt] != constants.HilCl.Lsca.LSCA_ACTIVE:
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Lsca_active']} is FAILED because                            "
                        f" the value is NOT_ACTIVE between {time_signal[t1_idx]} [us] and {time_signal[t2_idx]} [us]"
                        " but driver's seat is OCCUPED.".split()
                    )
                    eval_cond[0] = False
                    break
            # Check LSCA active during FREE driver's seat
            for cnt in range(t1_idx, t2_idx):
                if lsca_act_signal[cnt] == constants.HilCl.Lsca.LSCA_ACTIVE:
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Lsca_active']} is FAILED because                            "
                        f" the value is ACTIVE between {time_signal[t1_idx]} [us] and {time_signal[t2_idx]} [us] but"
                        " driver's seat is FREE.".split()
                    )
                    eval_cond[1] = False
                    break

            if not any(eval_cond):
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Lsca_active']} is FAILED because the value is NOT_ACTIVE between"
                    f" {time_signal[t1_idx]} [us] and {time_signal[t2_idx]} [us] but driver's seat is OCCUPED. The"
                    f" signal is ACTIVE between {time_signal[t2_idx]} [us] and {time_signal[t3_idx]} [us] but driver's"
                    " seat is FREE".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                "Evaluation not possible, the required value for                            "
                f" {signal_name['Drievers_seat']} never found.".split()
            )

        signal_summary["Driver's seat check"] = evaluation1

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        """Generate chart if test result FAILED or plot funtion is activated"""
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if test_result == fc.FAIL or bool(GeneralConstants.ACTIVATE_PLOTS):
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=time_signal, y=drivers_seat_signal, mode="lines", name=signal_name["Drievers_seat"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=lsca_act_signal, mode="lines", name=signal_name["Lsca_active"]))
            fig.add_trace(go.Scatter(x=time_signal, y=car_speed_signal, mode="lines", name=signal_name["Car_speed"]))

            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[us]")
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

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

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


@testcase_definition(name="LSCA active check", description="LSCA active value check.")
class FtLSCA(TestCase):
    """Example test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            LscaSeatCheck,
        ]
