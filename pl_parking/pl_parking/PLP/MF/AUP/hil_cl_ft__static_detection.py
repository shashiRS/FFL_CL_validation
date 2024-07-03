"""Detect static objects."""

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

SIGNAL_DATA = "STATIC_DETECT"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        SPEED = "Car_speed"
        ROAD = "Car_road"
        STATIC_OBJ = "Static_obj_number"
        STATIC_OBJ_POS = "Static_obj_position"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.SPEED: "MTS.MTA_ADC5.SI_DATA.m_egoMotionPort.vel_mps",
            self.Columns.ROAD: "CM.Car.Road.sRoad",
            self.Columns.STATIC_OBJ: "MTS.MTA_ADC5.SI_DATA.m_collisionEnvironmentModelPort.numberOfStaticObjects_u8",
            self.Columns.STATIC_OBJ_POS: "CM.Traffic.T00.sRoad",
        }


example_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="AP statick object detection",
    description="Check AP considers static object",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class CommonStaticObjCheck(TestStep):
    """CommonStaticObjCheck Test Step."""

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

        """Prepare sinals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        car_speed_signal = read_data["Car_speed"].tolist()
        car_road_signal = read_data["Car_road"].tolist()
        static_obj_pos_signal = read_data["Static_obj_position"].tolist()
        detected_static_obj_signal = read_data["Static_obj_number"].tolist()

        t1_idx = None
        max_obj = 0
        static_obj_pos = None
        position_of_detection = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Static_obj_number']} is PASSED, signal contains"
            f" {max(detected_static_obj_signal)} static object(s)".split()
        )

        """Evaluation part"""
        # Find the first time point when static object is detected by vehicle
        for item in detected_static_obj_signal:
            if item > 0:
                t1_idx = detected_static_obj_signal.index(item)
                break
        # If there was no detected object, test failed
        if t1_idx is None:
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Static_obj_number']} is FAILED, there is no detected object".split()
            )
        else:
            eval_cond = [True] * 1
            max_obj = max(detected_static_obj_signal)
            static_obj_pos = round(max(static_obj_pos_signal), 2)
            position_of_detection = round(car_road_signal[t1_idx], 2)

        signal_summary["Static object detection"] = evaluation1

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
                go.Scatter(
                    x=time_signal, y=detected_static_obj_signal, mode="lines", name=signal_name["Static_obj_number"]
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time_signal, y=static_obj_pos_signal, mode="lines", name=signal_name["Static_obj_position"]
                )
            )
            fig.add_trace(go.Scatter(x=time_signal, y=car_road_signal, mode="lines", name=signal_name["Car_road"]))
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
            "Detected static objects": {"value": max_obj, "color": fh.apply_color(max_obj, 0, ">")},
            "Position of object [m]": {"value": static_obj_pos},
            "Ego position at detection [m]": {"value": position_of_detection},
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
    name="AP statick object detection",
    description="The AP funtion shall consider obstacles with an absulte velocity value bellow"
    f" {constants.HilCl.StaticDynamic.LIMIT_OF_STAICK_SPEED} m/s as static object. There is only one statick"
    " obstacle in the used simulation.",
)
class FtCommon(TestCase):
    """CommonStaticObj Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    # Important information:
    # This script check number of static objects is greater than 0 but check of exact number of static objects during the measure is not implemented yet!

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CommonStaticObjCheck,
        ]
