"""Check Time Delay for LSM Braking Reaction after Obstacle Detection using USS2 and USS3 signals"""

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
from pl_parking.common_ft_helper import MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.constants import PlotlyTemplate

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "LSM_BRAKING_DELAY_CHECK"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USS2_DIST = "USS2_dist"
        USS3_DIST = "USS3_dist"
        LSCA_BRAKE_REQ = "Lsca_brake_req"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USS2_DIST: "CM.Sensor.Object.USS02.relvTgt.NearPnt.ds_p",
            self.Columns.LSCA_BRAKE_REQ: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCEmergencyHoldRequest",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="LSM braking reaction delay check",
    description="The system shall activate braking intervention within 600 ms after detecting a relevant obstacle using USS2 or USS3 signals.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class TimeDelayRelevantCheck(TestStep):
    """TimeDelayRelevantCheck Test Step."""

    custom_report = MfHilClCustomTeststepReport

    def _init_(self):
        """Init test."""
        super()._init_()

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
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        uss2_dist_sig = read_data["USS2_dist"].tolist()
        lsca_brake_req_sig = read_data["Lsca_brake_req"].tolist()

        t1_idx = None
        t2_idx = None
        detected_distance = 0
        time_difference = 0

        evaluation1 = " "

        # Step 1: Detect if a relevant obstacle is detected by USS2 (distance within threshold)
        for cnt in range(0, len(uss2_dist_sig)):
            if (
                constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION
                < uss2_dist_sig[cnt]
                <= constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION
            ):
                detected_distance = uss2_dist_sig[cnt]
                t1_idx = cnt
                break

        if t1_idx is None:
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['USS2_dist']} is FAILED, no relevant obstacle was detected by USS2 within"
                f"{constants.HilCl.PDW.Thresholds.MIN_DISTANCE_DETECTION} and {constants.HilCl.PDW.Thresholds.MAX_DISTANCE_DETECTION}".split()
            )
        else:
            # Step 2: Monitor braking intervention request and check for activation within 600 ms
            for cnt in range(t1_idx, len(lsca_brake_req_sig)):
                if lsca_brake_req_sig[cnt] == constants.HilCl.Lsca.BRAKE_REQUEST:
                    t2_idx = cnt
                    break

            if t2_idx is None:
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Lsca_brake_req']} is FAILED, braking intervention did not activate ({constants.HilCl.Lsca.BRAKE_REQUEST}), after obstacle detection.".split()
                )
            else:
                # Calculate the time difference between t1 and t2
                time_difference = (time_signal[t2_idx] - time_signal[t1_idx]) / 1000.0  # Convert to milliseconds
                if time_difference <= constants.HilCl.Lsca.REACTION_TIME_ON_OBSTACLES:
                    test_result = fc.PASS
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Lsca_brake_req']} is PASSED, the braking request from LSCA to brake the vehicle is within {constants.HilCl.Lsca.REACTION_TIME_ON_OBSTACLES} ms, distance between the vehicle and ego vehicle is {detected_distance} m at "
                        f"{time_signal[t1_idx]/1000} ms".split()
                    )
                else:
                    test_result = fc.FAIL
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Lsca_brake_req']} is FAILED, braking intervention took {time_difference:.2f} ms, which exceeds the {constants.HilCl.Lsca.REACTION_TIME_ON_OBSTACLES} ms limit.".split()
                    )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["LSM braking delay evaluation"] = evaluation1

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_header_left="Evaluation")
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        # Generate chart if test result FAILED
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=time_signal / constants.GeneralConstants.US_IN_MS,
                y=uss2_dist_sig,
                mode="lines",
                name=signal_name["USS2_dist"],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=time_signal / constants.GeneralConstants.US_IN_MS,
                y=lsca_brake_req_sig,
                mode="lines",
                name=signal_name["Lsca_brake_req"],
            )
        )
        fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [ms]")
        fig.update_layout(PlotlyTemplate.lgt_tmplt)
        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

        # Add the data in the table from Functional Test Filter Results
        additional_results_dict = {"Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)}}

        for plot in plots:
            if isinstance(plot, go.Figure):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="LSM Braking Reaction Delay Check",
    description="The system shall activate braking intervention within 600 ms after detecting a relevant obstacle using USS2 or USS3 signals.",
)
class LsmBrakingDelay(TestCase):
    """LsmBrakingDelay Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TimeDelayRelevantCheck,
        ]
