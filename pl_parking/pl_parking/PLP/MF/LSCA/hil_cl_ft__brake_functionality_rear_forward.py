"""LSCA enable brake functionality in forward mode when trailer is attached"""

import logging
import os
import sys

import plotly.graph_objects as go

log = logging.getLogger(__name__)
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

SIGNAL_DATA = "LSCA_ENABLE_BRAKE_FORWARD"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        TRAILER_CONNECTION = "Trailer_connection"
        LSCA_BRAKE = "Lsca_brake"
        DRIVING_DIRECTION = "Driving_direction"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.TRAILER_CONNECTION: "MTS.ADAS_CAN.Conti_Veh_CAN.Trailer.TrailerConnection",
            self.Columns.LSCA_BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCEmergencyHoldRequest",
            self.Columns.DRIVING_DIRECTION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput04.WheelDrivingDirectionFL",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="LSCA enable brake functionality in forward mode",
    description="LSCA function is still active when a trailer is attached if the ego vehicle drives forward.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class LscaEnableBrakeForwardCheck(TestStep):
    """LscaEnableBrakeForwardCheck Test Step."""

    custom_report = MfHilClCustomTeststepReport

    def _init_(self):
        """Init test."""
        super().__init__()

    def process(self, **kwargs):
        """
        This function processes the recorded signal from measurement file, sets the result of the test,
        generates plots and additional results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        read_data = self.readers[SIGNAL_DATA]
        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        lsca_brake_sig = read_data["Lsca_brake"].tolist()
        trailer_conn_sig = read_data["Trailer_connection"].tolist()
        driving_direction_sig = read_data["Driving_direction"].tolist()

        trailer_attached = 0  # False
        brake_detected = 0  # False

        """Evaluation part"""
        # Check when trailer is attached and driving forward
        for cnt in range(len(trailer_conn_sig)):
            if trailer_conn_sig[cnt] == constants.HilCl.TrailerConnection.OK_TRAILERCONNECTION:
                trailer_attached = 1  # True
                break

        if trailer_attached:
            for cnt in range(len(lsca_brake_sig)):
                if (
                    lsca_brake_sig[cnt] == constants.HilCl.Lsca.BRAKE_REQUEST
                    and driving_direction_sig[cnt] == constants.HilCl.WheelDrivingDirection.WHEEL_DIRECTION_FL
                ):
                    brake_detected = 1  # True
                    break

            if brake_detected:
                test_result = fc.PASS
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Lsca_brake']} signal is PASSED. LSCA correctly activated brakes while driving forward with the trailer attached.".split()
                )
            else:
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Lsca_brake']} signal is FAILED. LSCA did not activate the brakes while driving forward with the trailer attached.".split()
                )
        else:
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Trailer_connection']} signal is FAILED. Trailer attachment was not detected.".split()
            )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["LSCA Enable Rear Brake Forward Mode"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("LSCA Trailer Brake Enable Evaluation (Forward Mode)")
        plots.append(self.sig_sum)
        remarks.append(evaluation1)

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=lsca_brake_sig, mode="lines", name=signal_name["Lsca_brake"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=trailer_conn_sig, mode="lines", name=signal_name["Trailer_connection"])
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=driving_direction_sig, mode="lines", name=signal_name["Driving_direction"])
            )

            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("LSCA Brake Activation Failure (Forward Mode)")
            plots.append(fig)
            remarks.append("")

        """Calculate parameters to additional table"""
        sw_combatibility = "swfw_apu_adc5-2.1.0-DR2-PLP-B1-PAR230"

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
    name="LSCA enable brake functionality in forward mode with trailer attached",
    description="LSCA function is still active when a trailer is attached if the ego vehicle drives forward.",
)
class LscaEnableBrakeForward(TestCase):
    """LscaEnableBrakeForward Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            LscaEnableBrakeForwardCheck,
        ]
