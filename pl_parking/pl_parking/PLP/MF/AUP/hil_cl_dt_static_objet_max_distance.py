"""EnvironmentalModel shall detect static obstacles up to a maximum distance"""

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

SIGNAL_DATA = "L1D_STATIC_MAX_DIST"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        T00_SROAD = "T00_sroad"
        EGO_TX = "Ego_tx"
        STATIC_OBJECT_DETECTION_SIGNAL = "Static_obj_detection"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.T00_SROAD: "CM.Traffic.T00.sRoad",
            self.Columns.EGO_TX: "CM.Car.tx",
            self.Columns.STATIC_OBJECT_DETECTION_SIGNAL: "MTS.MTA_ADC5.CEM_EM_DATA.SGF_SgfOutput.staticObjectsOutput.numberOfObjects",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Static object detection range check",
    description="Check the distance between center point of the rear axle of the ego vehicle and rear site of static object when stattic object is detected by system.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class L1dStaticObjMaxDistCheck(TestStep):
    """L1dStaticObjMaxDistCheck Test Step."""

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
        t00_sroad_sig = read_data["T00_sroad"].tolist()
        ego_tx_sig = read_data["Ego_tx"].tolist()
        static_detection_sig = read_data["Static_obj_detection"].tolist()

        t00_location = 0
        delta_distance = 0

        t_detection_idx = None

        evaluation1 = " "

        """Evaluation part"""

        # Check detection
        if max(static_detection_sig) > 0:

            # Check distance when static object detected
            for cnt in range(0, len(static_detection_sig)):
                if static_detection_sig[cnt] > 0:
                    t_detection_idx = cnt
                    break

            # Calculate distance
            t00_location = max(t00_sroad_sig)
            ego_center = ego_tx_sig[t_detection_idx] + constants.HilCl.CarShape.CAR_R_AXLE_TO_HITCH
            delta_distance = t00_location - ego_center

            if delta_distance > constants.HilCl.L1D_Thresholds.MAX_STATICK_DETECTION_DISTANCE:
                test_result = fc.FAIL
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Static_obj_detection']} signal is FAILED, value of signal is {static_detection_sig[t_detection_idx]} at {time_signal[t_detection_idx]} us."
                    f" Distance between center point of the rear axle of the ego vehicle and rear site of static object is {delta_distance} m"
                    f" and this value is larger than {constants.HilCl.L1D_Thresholds.MAX_STATICK_DETECTION_DISTANCE} m".split()
                )
            else:
                test_result = fc.PASS
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Static_obj_detection']} signal is PASSED, value of signal is {static_detection_sig[t_detection_idx]} at {time_signal[t_detection_idx]} us."
                    f" Distance between center point of the rear axle of the ego vehicle and rear site of static object is {delta_distance} m"
                    f" and this value not more than {constants.HilCl.L1D_Thresholds.MAX_STATICK_DETECTION_DISTANCE} m".split()
                )

        else:
            test_result = fc.FAIL
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Static_obj_detection']} signal is FAILED, value of signal was {max(static_detection_sig)}."
                " There was a relevant static objec in the way of the ego vehcile but it was not detected."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Static object detection range"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=t00_sroad_sig, mode="lines", name=signal_name["T00_sroad"]))
            fig.add_trace(go.Scatter(x=time_signal, y=ego_tx_sig, mode="lines", name=signal_name["Ego_tx"]))
            fig.add_trace(
                go.Scatter(
                    x=time_signal, y=static_detection_sig, mode="lines", name=signal_name["Static_obj_detection"]
                )
            )

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
    name="Static object detection range",
    description=f"The EnvironmentalModel shall detect static obstacles up to an maximum distance 12 m"
    f" which are at least with a height of {constants.HilCl.HeightLimits.AP_G_MAX_HEIGHT_BODY_TRAVER_M}.",
)
class L1dStaticObjMaxDist(TestCase):
    """L1dStaticObjMaxDist Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            L1dStaticObjMaxDistCheck,
        ]
