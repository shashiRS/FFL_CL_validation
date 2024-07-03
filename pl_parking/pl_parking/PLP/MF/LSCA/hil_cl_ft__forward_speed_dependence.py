"""LSCA availability in defined speed range, Forward"""

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

SIGNAL_DATA = "LSCA_SPEED_FORWARD"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        CAR_SPEED = "Car_speed"
        LSCA_STATE = "Lsca_state"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CAR_SPEED: "MTS.ADAS_CAN.Conti_Veh_CAN.Tachometer.SpeedoSpeed",
            self.Columns.LSCA_STATE: "MTS.ADC5xx_Device.EM_DATA.EmLscaStatusPort.lscaOverallMode_nu",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="LSCA forward speed check",
    description="Check speed dependence of LSCA in forward mode.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class LscaSpeedForwardCheck(TestStep):
    """LscaSpeedForwardCheck Test Step."""

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
        car_speed_sig = read_data["Car_speed"].tolist()
        lsca_state_sig = read_data["Lsca_state"].tolist()

        t1_idx = None
        t2_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Lsca_state']} signal is PASSED, state of signal get activated "
            f"{constants.HilCl.Lsca.LSCA_ACTIVE} because ego vehicle speed is greater than LSCA_B_FORW_SPEED_MIN_ON_MPS : {constants.HilCl.Lsca.LSCA_B_FORW_SPEED_MIN_ON_MPS} [m/s]"
            f" and lower than LSCA_B_FORW_SPEED_MAX_ON_MPS : {constants.HilCl.Lsca.LSCA_B_FORW_SPEED_MAX_ON_MPS} [m/s]".split()
        )

        """Evaluation part"""
        # Find when speed of ego vehicle enters to range and leaves the range
        for cnt in range(0, len(car_speed_sig)):
            if car_speed_sig[cnt] / 3.6 > constants.HilCl.Lsca.LSCA_B_FORW_SPEED_MIN_ON_MPS:
                t1_idx = cnt
                continue
            if car_speed_sig[cnt] / 3.6 < constants.HilCl.Lsca.LSCA_B_FORW_SPEED_MAX_ON_MPS and t1_idx is not None:
                t2_idx = cnt
                break

        if t1_idx is not None and t2_idx is not None:
            eval_cond = [True] * 1

            # Check LSCA state in speed range
            for cnt in range(t1_idx, t2_idx):
                if lsca_state_sig[cnt] != constants.HilCl.Lsca.LSCA_ACTIVE:
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Lsca_state']} signal is FAILED, state of signal is not active {constants.HilCl.Lsca.LSCA_ACTIVE} at {time_signal[cnt]} [us] but"
                        f" speed of ego vehicle is {car_speed_sig[cnt] / 3.6} [m/s]. This value is in range."
                        f" Minimum limit: {constants.HilCl.Lsca.LSCA_B_FORW_SPEED_MIN_ON_MPS} [m/s]"
                        f" Maximum limit: {constants.HilCl.Lsca.LSCA_B_FORW_SPEED_MAX_ON_MPS} [m/s]".split()
                    )
                    eval_cond[0] = False
                    break
        elif t1_idx is None and t2_idx is not None:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation {signal_name['Car_speed']} is FAILED, ego vehicle never entered into speed range "
                f"minimum limit : {constants.HilCl.Lsca.LSCA_B_FORW_SPEED_MIN_ON_MPS} [m/s] and maximum limit : {constants.HilCl.Lsca.LSCA_B_FORW_SPEED_MAX_ON_MPS} [m/s] .".split()
            )

        elif t1_idx is not None and t2_idx is None:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation {signal_name['Car_speed']} is FAILED, ego vehicle never left speed range."
                f" Maximum limit : {constants.HilCl.Lsca.LSCA_B_FORW_SPEED_MAX_ON_MPS} [m/s]".split()
            )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join("The evaluation is FAILED, invalid TestRun".split())

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["LSCA is active between the minimum and maximum speed in forward mode of the vehicle"] = (
            evaluation1
        )

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=lsca_state_sig, mode="lines", name=signal_name["Lsca_state"]))
            fig.add_trace(go.Scatter(x=time_signal, y=car_speed_sig, mode="lines", name=signal_name["Car_speed"]))

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
    name="LSCA speed dependence, Forward mode",
    description="The LSCA function shall get activated if ego vehicle speed is greater than"
    f" LSCA_B_FORW_SPEED_MIN_ON_MPS: {constants.HilCl.Lsca.LSCA_B_FORW_SPEED_MIN_ON_MPS} m/s and"
    f" LSCA_B_BACKW_SPEED_MIN_ON_MPS: {constants.HilCl.Lsca.LSCA_B_BACKW_SPEED_MIN_ON_MPS} m/s.",
)
class LscaSpeedForward(TestCase):
    """LscaSpeedForward Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            LscaSpeedForwardCheck,
        ]
