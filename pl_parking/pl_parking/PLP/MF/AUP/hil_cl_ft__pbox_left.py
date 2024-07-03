"""Check offered parking slot on driver's side."""

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
from pl_parking.PLP.MF.constants import PlotlyTemplate

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "PBOX_LEFT"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_tap = "HMI_tap"
        HMI_offered_slot = "HMI_offered_slot"
        SPEED = "Car_speed"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_tap: "CM.IO_CAN_AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.HMI_offered_slot: (
                "MTS.ADC5xx_Device.VD_DATA.IuHmiGeneralInputPort.parkingSpaces.left.scanned_nu[0]"
            ),
            self.Columns.SPEED: "MTS.ADC5xx_Device.EM_DATA.EmEgoMotionPort.vel_mps",
        }


example_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="Driver's side detection",
    description="Check offered parking slot on driver's side",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class DetectSlotOnDriversSideCheck(TestStep):
    """DetectSlotOnDriversSideCheck Test Step."""

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

        read_data = self.readers[SIGNAL_DATA].signals
        test_result = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        signal_summary = {}

        """Prepare sinals and variables"""
        time_signal = read_data["ts"].tolist()
        HMI_tap_signal = read_data["HMI_tap"].tolist()
        hmi_offered_signal = read_data["HMI_offered_slot"].tolist()
        car_speed_signal = read_data["Car_speed"].tolist()

        t1_idx = None
        t2_idx = None
        scanning_result = []

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['HMI_offered_slot']} is PASSED, signal contains available parking slot(s)".split()
        )

        """Evaluation part"""
        # Find beginig of scanning phase
        for item in HMI_tap_signal:
            if item == constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE:
                t1_idx = HMI_tap_signal.index(item)
                break
        # Find end of scanning phase
        for counter in range(t1_idx, len(car_speed_signal)):
            if car_speed_signal[counter] < constants.HilCl.CarMaker.ZERO_SPEED:
                t2_idx = counter
                break

        if t1_idx is not None and t2_idx is not None:
            eval_cond = [True] * 1

            # Collect detections between begining and end of scanning phase
            for cnt in range(t1_idx, t2_idx):
                scanning_result.append(hmi_offered_signal[cnt])

            detected_slots = max(scanning_result)

            # Check maximum value of detected slots
            if detected_slots == 0:
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['HMI_offered_slot']} is FAILED because                            "
                    " There is not offered parking slot on driver's side during scannig phase. Begining of scanning:"
                    f" {time_signal[t1_idx]} [us]. End of scanning {time_signal[t2_idx]} [us]".split()
                )
                eval_cond[0] = False

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                "Evaluation not possible, the required value for                            "
                f" {signal_name['Car_speed']} never found.".split()
            )

        signal_summary[signal_name["HMI_offered_slot"]] = evaluation1

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED or plot funtion is activated"""
        if test_result == fc.FAIL or bool(constants.GeneralConstants.ACTIVATE_PLOTS):
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=time_signal, y=hmi_offered_signal, mode="lines", name=signal_name["HMI_offered_slot"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=HMI_tap_signal, mode="lines", name=signal_name["HMI_tap"]))

            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
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
            "Detected slots": {"value": detected_slots, "color": fh.apply_color(detected_slots, 0, ">")},
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
    name="AUP parking box detection",
    description=(
        "The AP funtion shall offer a free parking slot, if it is located on the driver's side of the ego vehicle."
    ),
)
class FtCommon(TestCase):
    """DetectSlotOnDriversSide Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            DetectSlotOnDriversSideCheck,
        ]
