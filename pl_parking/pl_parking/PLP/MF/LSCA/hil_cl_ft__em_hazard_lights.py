"""Hazard Light Activation During LSCA or Maneuver Emergency Braking"""

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

SIGNAL_DATA = "LSCA_HAZARD_ACTIVATION"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        LSCA_BRAKE_REQ = "Lsca_brake"
        HAZARD_WARNING_REQ = "Hazard_warning_req"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.LSCA_BRAKE_REQ: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCEmergencyHoldRequest",
            self.Columns.HAZARD_WARNING_REQ: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.HazardWarningReq",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Hazard Light Activation During Emergency Braking",
    description="Check that LSCA or Maneuver emergency braking triggers a hazard light request and ensures that the hazard lights remain active for 3 seconds after the braking request.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class EmergencyHazardLightCheck(TestStep):
    """EmergencyHazardLightCheck Test Step."""

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
        test_result = fc.INPUT_MISSING  # Initial result assumption
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        lsca_brake_req_sig = read_data["Lsca_brake"].tolist()
        hazard_warning_req_sig = read_data["Hazard_warning_req"].tolist()

        t1_idx = None
        hazard_light_activated = False
        hazard_light_duration_valid = False

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Hazard_warning_req']} is PASSED, hazard lights were activated during LSCA emergency braking and remained active for the required duration.".split()
        )

        # Step 1: Find LSCA brake request activation
        for cnt in range(0, len(lsca_brake_req_sig)):
            if lsca_brake_req_sig[cnt] == constants.HilCl.Lsca.BRAKE_REQUEST:
                t1_idx = cnt
                break

        if t1_idx is None:
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Lsca_brake']} is FAILED, LSCA never initiated a brake request.".split()
            )
            test_result = fc.FAIL
        else:
            # Step 2: Find when hazard light request is sent after brake request
            for cnt in range(t1_idx, len(hazard_warning_req_sig)):
                if hazard_warning_req_sig[cnt] == constants.HilCl.VehicleLights.HazardLights.HAZARD_WARNING_REQ:
                    hazard_light_activated = True

                    # Check if hazard light request remains active for T_HAZARD seconds (3s)
                    start_time = time_signal[cnt]  # Start time of hazard warning request
                    for t in range(cnt, len(hazard_warning_req_sig)):
                        if hazard_warning_req_sig[t] != constants.HilCl.VehicleLights.HazardLights.HAZARD_WARNING_REQ:
                            break  # Hazard warning is no longer active
                        elapsed_time = round(time_signal[t] - start_time)  # check the conversion
                        if elapsed_time >= constants.HilCl.SotifTime.T_HAZARD:
                            hazard_light_duration_valid = True
                            break
                    break

            if not hazard_light_activated:
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Hazard_warning_req']} is FAILED, hazard light request was not activated during LSCA emergency braking.".split()
                )
                test_result = fc.FAIL
            elif not hazard_light_duration_valid:
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Hazard_warning_req']} is FAILED, hazard lights did not remain active for {constants.HilCl.SotifTime.T_HAZARD} seconds.".split()
                )
                test_result = fc.FAIL
            else:
                test_result = fc.PASS

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Hazard light activation during LSCA braking"] = evaluation1

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_header_left="Evaluation")
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=lsca_brake_req_sig, mode="lines", name=signal_name["Lsca_brake"]))
            fig.add_trace(
                go.Scatter(
                    x=time_signal, y=hazard_warning_req_sig, mode="lines", name=signal_name["Hazard_warning_req"]
                )
            )
            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {"Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)}}

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
    name="Hazard Light Activation During LSCA Braking",
    description="Ensure that during LSCA braking, hazard light request is sent to BCM and lights remain active for 3 seconds.",
)
class LscaHazardLightActivation(TestCase):
    """LscaHazardLightActivation Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            EmergencyHazardLightCheck,
        ]
