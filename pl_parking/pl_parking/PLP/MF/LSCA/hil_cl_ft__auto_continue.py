"""Cancel LSCA brake intervention, Auto continue mode"""

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

SIGNAL_DATA = "LSCA_AUTO_CONTINUE"


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
    name="Auto continue check",
    description="Check LSCA brake request cancel process in case of auto continue mode",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class LscaAutoContinueCheck(TestStep):
    """LscaAutoContinueCheck Test Step."""

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

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        acce_pedal_sig = read_data["Acce_pedal"].tolist()
        lsca_brake_req_sig = read_data["Lsca_brake"].tolist()
        car_speed_sig = read_data["Car_speed"].tolist()

        t1_idx = None  # LSCA brake req set active
        t2_idx = None  # Vehicle reach standstill
        t3_idx = None  # Car_ax = 0
        t4_idx = None  # Car_ax > 0.1
        debounce_time = 0

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Lsca_brake']} is PASSED, LSCA sent a brake request to avoid the collision and auto continue worked well.".split()
        )

        # Step 1: Find LSCA brake request
        for cnt in range(0, len(lsca_brake_req_sig)):
            if lsca_brake_req_sig[cnt] == constants.HilCl.Lsca.BRAKE_REQUEST:
                t1_idx = cnt
                break

        if t1_idx is None:
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Lsca_brake']} is FAILED, LSCA never sent a brake request.".split()
            )
        else:
            # Step 2: Find when ego reaches standstill
            for cnt in range(t1_idx, len(car_speed_sig)):
                if car_speed_sig[cnt] < constants.HilCl.CarMaker.ZERO_SPEED:
                    t2_idx = cnt
                    break

            if t2_idx is None:
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Car_speed']} is FAILED, ego vehicle never reached standstill after LSCA brake request.".split()
                )
            else:
                # Step 3: Find when driver releases gas pedal (gas pedal = 0)
                for cnt in range(t2_idx, len(acce_pedal_sig)):
                    if acce_pedal_sig[cnt] == 0:
                        t3_idx = cnt
                        break

                if t3_idx is None:
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Acce_pedal']} is FAILED, driver never released the gas pedal after reaching standstill.".split()
                    )
                else:
                    # Step 4: Find when driver presses gas pedal (gas pedal > 0.1)
                    for cnt in range(t3_idx, len(acce_pedal_sig)):
                        if acce_pedal_sig[cnt] > 0.1:
                            t4_idx = cnt
                            break

                    if t4_idx is None:
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Acce_pedal']} is FAILED, driver did not press gas pedal within the configurable waiting time.".split()
                        )
                    else:
                        for ts in range(t4_idx, len(acce_pedal_sig)):
                            if debounce_time < 0.5:
                                debounce_time = (time_signal[ts] - time_signal[t4_idx]) / 10**6
                            else:
                                t5_idx = ts
                                break

                        # Check LSCA reaction
                        if (
                            car_speed_sig[t5_idx] > 0.1
                            and lsca_brake_req_sig[t5_idx] != constants.HilCl.Lsca.BRAKE_REQUEST
                        ):
                            test_result = fc.PASS
                        elif car_speed_sig[t5_idx] < 0.1:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Car_speed']} is FAILED, car speed did not exceed the threshold after gas pedal was pressed.".split()
                            )
                        elif lsca_brake_req_sig[t5_idx] == constants.HilCl.Lsca.BRAKE_REQUEST:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Lsca_brake']} is FAILED, LSCA did not cancel brake request after gas pedal was pressed.".split()
                            )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["LSCA cancel brake request, Auto continue mode"] = evaluation1

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
    name="Cancel LSCA brake request",
    description="In case of auto continue mode being used, the LSCA function shall automatically cancel"
    " the active brake request when reaching a configurable waiting time after recognized standstill.",
)
class LscaAutoContinue(TestCase):
    """LscaAutoContinue Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            LscaAutoContinueCheck,
        ]
