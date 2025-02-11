"""LSCA Driver Override with Brake Pedal During Emergency Braking"""

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

SIGNAL_DATA = "LSCA_BRAKING_OVERRIDE_BRAKE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        BRAKE_PEDAL = "Brake_pedal"
        LSCA_BRAKE_REQ = "Lsca_brake"
        CAR_AX = "Car_ax"  # Vehicle acceleration/deceleration
        CAR_SPEED = "Car_speed"  # Vehicle speed signal to detect standstill

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.BRAKE_PEDAL: "DM.Brake",
            self.Columns.LSCA_BRAKE_REQ: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCEmergencyHoldRequest",
            self.Columns.CAR_AX: "CM.Car.ax",
            self.Columns.CAR_SPEED: "MTS.ADAS_CAN.Conti_Veh_CAN.Tachometer.SpeedoSpeed",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Driver Override with Brake Pedal During LSCA Emergency Braking",
    description="Check if driver can override LSCA brake request by pressing the brake pedal above the required threshold and check if deceleration exceeds comfort limit between brake press and standstill.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class EmergencyBrakeCheck(TestStep):
    """EmergencyBrakeCheck Test Step."""

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
        brake_pedal_sig = read_data["Brake_pedal"].tolist()
        lsca_brake_req_sig = read_data["Lsca_brake"].tolist()
        car_ax_sig = read_data["Car_ax"].tolist()
        car_speed_sig = read_data["Car_speed"].tolist()

        t1_idx = None  # LSCA brake request active (t1)
        t2_idx = None  # Vehicle reaches standstill (t2)
        t3_idx = None  # Driver presses brake pedal above threshold (t3)
        decel_exceeded = False

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Lsca_brake']} is PASSED, driver successfully overrode LSCA braking by pressing the brake pedal, and deceleration exceeded comfort limit.".split()
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
            # Step 2: Find when vehicle reaches standstill
            for cnt in range(t1_idx, len(car_speed_sig)):
                if car_speed_sig[cnt] < constants.HilCl.CarMaker.ZERO_SPEED:
                    t2_idx = cnt
                    break

            if t2_idx is None:
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Car_speed']} is FAILED, vehicle never reached standstill.".split()
                )
                test_result = fc.FAIL
            else:
                # Step 3: Find when driver presses the brake pedal above the threshold (t3)
                for cnt in range(t1_idx, t2_idx):
                    if brake_pedal_sig[cnt] > constants.HilCl.Lsca.LSCA_B_OVERIDE_BRAKEPEDAL_AFTERBRAKING_PERC:
                        t3_idx = cnt
                        break

                if t3_idx is None:
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Brake_pedal']} is FAILED, driver never pressed the brake pedal above the threshold to override LSCA braking.".split()
                    )
                    test_result = fc.FAIL
                else:
                    # Step 4: Check deceleration
                    for cnt in range(t3_idx, t2_idx):
                        if car_ax_sig[cnt] > constants.HilCl.ApThreshold.AP_G_MAX_DECEL_COMFORTABLE_MPS2:
                            decel_exceeded = True
                            break

                    if decel_exceeded:
                        test_result = fc.PASS
                    else:
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Car_ax']} is FAILED, deceleration did not exceed the comfort limit.".split()
                        )
                        test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["LSCA brake request during emergency braking"] = evaluation1

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_header_left="Evaluation")
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=lsca_brake_req_sig, mode="lines", name=signal_name["Lsca_brake"]))
            fig.add_trace(go.Scatter(x=time_signal, y=brake_pedal_sig, mode="lines", name=signal_name["Brake_pedal"]))
            fig.add_trace(go.Scatter(x=time_signal, y=car_ax_sig, mode="lines", name=signal_name["Car_ax"]))
            fig.add_trace(go.Scatter(x=time_signal, y=car_speed_sig, mode="lines", name=signal_name["Car_speed"]))
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
    name="LSCA Brake Override During Emergency Braking by pressing the brake pedal",
    description="The LSCA function shall allow the driver to take over control by pressing the brake pedal above a specific threshold during emergency braking, and ensure that the deceleration is within a comfortable limit.",
)
class LscaBrakeOverride(TestCase):
    """LscaBrakeOverride Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            EmergencyBrakeCheck,
        ]
