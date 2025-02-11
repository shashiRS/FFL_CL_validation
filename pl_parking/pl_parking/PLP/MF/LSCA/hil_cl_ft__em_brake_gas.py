"""LSCA Driver Override During Emergency Braking"""

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

SIGNAL_DATA = "LSCA_BRAKING_OVERRIDE_GAS"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        ACCELERATION_PEDAL = "Acce_pedal"
        LSCA_BRAKE_REQ = "Lsca_brake"
        CAR_SPEED = "Car_speed"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.ACCELERATION_PEDAL: "MTS.ADAS_CAN.Conti_Veh_CAN.GasPedal.GasPedalPos",
            self.Columns.LSCA_BRAKE_REQ: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCEmergencyHoldRequest",
            self.Columns.CAR_SPEED: "MTS.ADAS_CAN.Conti_Veh_CAN.Tachometer.SpeedoSpeed",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Driver Override During LSCA Emergency Braking",
    description="Check if driver can override LSCA brake request by pressing the accelerator pedal above the required threshold.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class EmergencyGasCheck(TestStep):
    """EmergencyGasCheck Test Step."""

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
        acce_pedal_sig = read_data["Acce_pedal"].tolist()
        lsca_brake_req_sig = read_data["Lsca_brake"].tolist()
        car_speed_sig = read_data["Car_speed"].tolist()

        t1_idx = None  # LSCA brake request active
        t2_idx = None  # Accelerator pedal pressed above threshold
        t3_idx = None  # Car continue moving after override

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Lsca_brake']} is PASSED, driver successfully overrode LSCA braking by pressing the accelerator pedal and the car keeps moving.".split()
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
            # Step 2: Find when driver presses the accelerator pedal above the threshold
            for cnt in range(t1_idx, len(acce_pedal_sig)):
                if acce_pedal_sig[cnt] > constants.HilCl.Lsca.LSCA_B_OVERIDE_ACCELPEDAL_AFTERBRAKING_PERC:
                    t2_idx = cnt
                    break

            if t2_idx is None:
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Acce_pedal']} is FAILED, driver never pressed the accelerator pedal above the threshold to override LSCA braking.".split()
                )
                test_result = fc.FAIL
            else:
                # Step 3: Check if car keeps moving after override
                for cnt in range(t2_idx, len(car_speed_sig)):
                    if car_speed_sig[cnt] > constants.HilCl.CarMaker.ZERO_SPEED:
                        t3_idx = cnt
                        break

                if t3_idx is None:
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Car_speed']} is FAILED, the car did not keep moving after the driver overrode the LSCA braking.".split()
                    )
                    test_result = fc.FAIL
                else:
                    test_result = fc.PASS

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["LSCA brake request during emergency braking"] = evaluation1

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=lsca_brake_req_sig, mode="lines", name=signal_name["Lsca_brake"]))
            fig.add_trace(go.Scatter(x=time_signal, y=acce_pedal_sig, mode="lines", name=signal_name["Acce_pedal"]))
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
    name="LSCA Brake Override During Emergency Braking by pressing the gas pedal",
    description="The LSCA function shall allow the driver to take over control by pressing the accelerator pedal above a specific threshold during emergency braking, and the car should start moving.",
)
class LscaBrakingOverride(TestCase):
    """LscaBrakingOverride Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            EmergencyGasCheck,
        ]
