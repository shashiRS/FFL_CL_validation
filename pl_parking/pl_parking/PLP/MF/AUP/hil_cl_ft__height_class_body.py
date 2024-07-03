"""Check body traversable object classification."""

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

SIGNAL_DATA = "HEIGHT_CLASSIFICATION_BODY_TRAV"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        CAR_ROAD = "Car_road"
        CAR_SPEED = "Car_speed"
        STATIC_OBJ = "Detected_static_obj"
        STATIC_OBJ_POS = "Static_obj_position"
        HEIGHT_CLASS = "Height_class"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.STATIC_OBJ: "MTS.ADC5xx_Device.EM_DATA.EmCollEnvModelPort.numberOfStaticObjects_u8",
            self.Columns.CAR_ROAD: "CM.Car.Road.sRoad",
            self.Columns.CAR_SPEED: "MTS.ADC5xx_Device.EM_DATA.EmEgoMotionPort.vel_mps",
            self.Columns.HEIGHT_CLASS: "MTS.ADC5xx_Device.EM_DATA.EmCollEnvModelPort.staticObjects[0].objHeightClass_nu",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Height classification",
    description="Check body traversable object classification",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class CommonBodyTravCheck(TestStep):
    """CommonBodyTravCheck Test Step."""

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
        time_sig = read_data["ts"].tolist()
        height_class_sig = read_data["Height_class"].tolist()
        detected_static_obj_sig = read_data["Detected_static_obj"].tolist()
        car_speed_sig = read_data["Car_speed"].tolist()

        detections_idx = []
        evaluation1 = ""

        """Evaluation part"""
        if max(detected_static_obj_sig) > 0:
            # Find when syytem detect a static object. Collect rising edges
            detections_idx = HilClFuntions.RisingEdge(detected_static_obj_sig, 0)

        if len(detections_idx) > 0:
            eval_cond = [True] * 1

            evaluation1 = " ".join(
                "The evaluation is PASSED, AP function considers obstacle as body traversable static object.".split()
            )

            # Check type of detected object
            for item in detections_idx:
                if height_class_sig[item] != constants.HilCl.HeightClases.BODY_TRAVERSABLE:
                    evaluation1 = " ".join(
                        f"The evaluation is FAILED, AP function does not consider"
                        f" static object as body traversable object at {time_sig[item]} us.".split()
                    )
                    eval_cond[0] = False
                    break
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join("The evaluation of is FAILED, AP function never detected any static object.".split())

        signal_summary["Height classification: Body traversable"] = evaluation1

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

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=time_sig, y=detected_static_obj_sig, mode="lines", name=signal_name["Detected_static_obj"])
            )
            fig.add_trace(go.Scatter(x=time_sig, y=height_class_sig, mode="lines", name=signal_name["Height_class"]))
            fig.add_trace(go.Scatter(x=time_sig, y=car_speed_sig, mode="lines", name=signal_name["Car_speed"]))

            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        """Calculate parameters to additional table"""
        sw_combatibility = (  # Remainder: Update if SW changed and script working well
            "swfw_apu_adc5-2.1.0-DR2-PLP-B1-PAR230"
        )

        # Calculate max detected static object
        max_detec_static_obj = max(detected_static_obj_sig)

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            "Detected static object(s)": {
                "value": max_detec_static_obj,
                "color": fh.apply_color(max_detec_static_obj, 0, ">"),
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
    name="Height classification: Body traversable",
    description=f"The AP Function shall consider static objects higher than {constants.HilCl.HeightLimits.AP_G_MAX_HEIGHT_WHEEL_TRAVER_M}"
    f" m but lower or equal than {constants.HilCl.HeightLimits.AP_G_MAX_HEIGHT_BODY_TRAVER_M} m as body traversable.",
)
class FtCommon(TestCase):
    """CommonBodyTrav Test Case."""

    custom_report = MfHilClCustomTestcaseReport
    # Important iformation:
    # Please use this script only with TestRun HIL_COMMON_HeightClassification_Body_ID1073781

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CommonBodyTravCheck,
        ]
