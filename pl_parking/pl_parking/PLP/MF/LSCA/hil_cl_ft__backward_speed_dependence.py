"""Speed dependence."""

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
from pl_parking.common_ft_helper import HilClFuntions, MfCustomTestcaseReport, MfCustomTeststepReport
from pl_parking.PLP.MF.constants import GeneralConstants, PlotlyTemplate

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "LSCA_SPEED_BACKWARD"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""  #

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        SPEED = "Car_speed"
        LSCA_ACT = "Lsca_active"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.SPEED: "MTS.ADAS_CAN.Conti_Veh_CAN.Tachometer.SpeedoSpeed",
            self.Columns.LSCA_ACT: "MTS.ADC5xx_Device.EM_DATA.EmLscaStatusPort.lscaOverallMode_nu",
        }


example_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name=("LSCA active value check in backward mode"),
    description="Check LSCA active value if ego vehicle speed is over minimum speed , between minumum and maximum speed and below than maximum speed for backward motion.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class LscaActiveCheckbackward(TestStep):
    """LscaActiveCheckbackward Test Step."""

    custom_report = MfCustomTeststepReport

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

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        car_speed_signal = read_data["Car_speed"].tolist()
        lsca_act_signal = read_data["Lsca_active"].tolist()
        t1_idx = None
        t2_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Lsca_active']} signal is PASSED, state of signal get activated "
            f"{constants.HilCl.Lsca.LSCA_ACTIVE} because ego vehicle speed is greater than LSCA_B_BACKW_SPEED_MIN_ON_MPS : {constants.HilCl.Lsca.LSCA_B_BACKW_SPEED_MIN_ON_MPS} [m/s]"
            f" and lower than LSCA_B_BACKW_SPEED_MAX_ON_MPS : {constants.HilCl.Lsca.LSCA_B_BACKW_SPEED_MAX_ON_MPS} [m/s]".split()
        )
        """Evaluation part"""
        for speed in car_speed_signal:
            # First time, Car.v > min limit for backward speed
            if speed / 3.6 > abs(constants.HilCl.Lsca.LSCA_B_BACKW_SPEED_MIN_ON_MPS) and t1_idx is None:
                t1_idx = car_speed_signal.index(speed)
                continue
            # First time, Car.v < max limit for backward speed
            if (
                speed / 3.6 < abs(constants.HilCl.Lsca.LSCA_B_BACKW_SPEED_MAX_ON_MPS)
                and t2_idx is None
                and t1_idx is not None
            ):
                t2_idx = car_speed_signal.index(speed)
                continue

        if t1_idx is not None and t2_idx is not None:
            eval_cond = [True] * 1

            # Check LSCA_active when Car.v is between min speed and max speed for backward
            for cnt in range(t1_idx, t2_idx):
                if lsca_act_signal[cnt] != constants.HilCl.Lsca.LSCA_ACTIVE:
                    failed_t = time_signal[cnt]
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Lsca_active']} is FAILED because"
                        f" the value is [NOT_ACTIVE] at {failed_t} [us], but speed is between"
                        f" {(constants.HilCl.Lsca.LSCA_B_BACKW_SPEED_MIN_ON_MPS)} [m/s] and {(constants.HilCl.Lsca.LSCA_B_BACKW_SPEED_MAX_ON_MPS)} [m/s].".split()
                    )
                    eval_cond[0] = False
                    break
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"Evaluation not possible, the required value for" f" {signal_name['Lsca_active']} never found.".split()
            )

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        signal_summary["LSCA is active between the minimum and maximum speed in reverse mode of the vehicle"] = (
            evaluation1
        )

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED or plot funtion is activated"""
        if test_result == fc.FAIL or bool(GeneralConstants.ACTIVATE_PLOTS):
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=lsca_act_signal, mode="lines", name=signal_name["Lsca_active"]))
            fig.add_trace(go.Scatter(x=time_signal, y=car_speed_signal, mode="lines", name=signal_name["Car_speed"]))

            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(fig)
            remarks.append("TestStep 1")

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
class LscaActiveBackward(TestCase):
    """LscaActiveBackward test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            LscaActiveCheckbackward,
        ]
