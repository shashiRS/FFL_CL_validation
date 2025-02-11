"""executing a parking in maneuver so that the ego vehicle reaches the final parking in pose with a maximum amount of strokes, Angular"""

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

__author__ = "uig14850"
SIGNAL_DATA = "PARK_OT_MAX_MAN_TERM_NUM_OF_STROKES_ANG"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        ACTUAL_GEAR = "Actual_gear"
        HMI_INFO = "State_on_HMI"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.ACTUAL_GEAR: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActualGear",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Maximum number of strokes in case of Angular parking",
    description="Check state chanh if number of strokes exeeds the limit",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class NumOfStokresAngularCheck(TestStep):
    """NumOfStokresAngularCheck Test Step."""

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
        time_signal = read_data.index
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()
        actual_gear_sig = read_data["Actual_gear"].tolist()

        t_start_man_idx = None
        t_end_man_idx = None

        previous_state = None
        number_of_strokes = 0

        evaluation_steps = {}

        """Evaluation part"""
        # Find start of maneuvering
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_start_man_idx = cnt
                break

        # Find end of maneuvering
        for cnt in range(t_start_man_idx or 0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_end_man_idx = cnt
                break

        if t_start_man_idx and t_end_man_idx:
            # Collect geat states durin maneuvering
            gears_states = HilClFuntions.States(actual_gear_sig, t_start_man_idx, t_end_man_idx, 1)

            # Collect R-D and D-R switches. This transition presents a stroke
            for key in gears_states:
                if (
                    gears_states[key] == constants.HilCl.VehCanActualGear.PARK_ACTUALGEAR
                    or gears_states[key] == constants.HilCl.VehCanActualGear.NEUTRAL_ACTUALGEAR
                ):
                    continue
                if previous_state is None:
                    previous_state = gears_states[key]
                    continue
                else:
                    if (
                        previous_state == constants.HilCl.VehCanActualGear.FIRST_ACTUALGEAR
                        and gears_states[key] == constants.HilCl.VehCanActualGear.REVERSE_ACTUALGEAR
                    ):
                        number_of_strokes += 1
                        previous_state = gears_states[key]

                    if (
                        previous_state == constants.HilCl.VehCanActualGear.REVERSE_ACTUALGEAR
                        and gears_states[key] == constants.HilCl.VehCanActualGear.FIRST_ACTUALGEAR
                    ):
                        number_of_strokes += 1
                        previous_state = gears_states[key]
            # Check number of strokes and state at end of maneuver
            if number_of_strokes > constants.HilCl.ApThreshold.AP_G_MAX_NUM_STROKES_ANG_NU:

                if state_on_hmi_sig[t_end_man_idx] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS:
                    test_result = fc.FAIL

                    step_key = " ".join(
                        f"System executed parking with {number_of_strokes} stroke(s),"
                        f" Limit: {constants.HilCl.ApThreshold.AP_G_MAX_NUM_STROKES_ANG_NU}".split()
                    )
                    evaluation_steps[step_key] = " ".join(
                        f"The evaluation is FAILED."
                        f" Number of strokes is {number_of_strokes} at end of maneuver,"
                        f" this values is greater than AP_G_MAX_NUM_STROKES_ANG_NU ({constants.HilCl.ApThreshold.AP_G_MAX_NUM_STROKES_ANG_NU}) and"
                        f" {signal_name['State_on_HMI']} signal is PPC_SUCCESS ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS})"
                        f" at end of active maneuver ({time_signal[t_end_man_idx]} us).".split()
                    )

            else:
                if state_on_hmi_sig[t_end_man_idx] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS:
                    # PASSED
                    test_result = fc.PASS
                    step_key = " ".join(
                        f"System executed parking with {number_of_strokes} stroke(s),"
                        f" Limit: {constants.HilCl.ApThreshold.AP_G_MAX_NUM_STROKES_ANG_NU}".split()
                    )
                    evaluation_steps[step_key] = " ".join(
                        f"The evaluation is PASSED."
                        f" Number of strokes is {number_of_strokes} at end of maneuver,"
                        f" this values is not greater than AP_G_MAX_NUM_STROKES_ANG_NU ({constants.HilCl.ApThreshold.AP_G_MAX_NUM_STROKES_ANG_NU}) and"
                        f" {signal_name['State_on_HMI']} signal is PPC_SUCCESS ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS})"
                        f" at end of active maneuver ({time_signal[t_end_man_idx]} us)".split()
                    )

        if t_start_man_idx is None:
            test_result = fc.FAIL
            step_key = " ".join(
                f"System shall start Maneuvering mode:"
                f" {signal_name['State_on_HMI']} switches to"
                f" PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})".split()
            )
            evaluation_steps[step_key] = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched out from PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        if t_end_man_idx is None:
            test_result = fc.FAIL
            step_key = " ".join(
                f"System shall finish Maneuvering mode:"
                f" {signal_name['State_on_HMI']} switches our from"
                f" PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})".split()
            )
            evaluation_steps[step_key] = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switch out from PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(evaluation_steps)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=actual_gear_sig, mode="lines", name=signal_name["Actual_gear"]))

        fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
        fig.update_layout(PlotlyTemplate.lgt_tmplt, title="Measured signals")

        if t_start_man_idx is not None:
            fig.add_vline(
                x=time_signal[t_start_man_idx],
                line_width=1,
                line_dash="dash",
                line_color="darkslategray",
                annotation_text="T1",
            )

        if t_end_man_idx is not None:
            fig.add_vline(
                x=time_signal[t_end_man_idx],
                line_width=1,
                line_dash="dash",
                line_color="darkslategray",
                annotation_text="T2",
            )

        if t_start_man_idx is not None and t_end_man_idx is not None:

            fig.add_vrect(
                x0=time_signal[t_start_man_idx],
                x1=time_signal[t_end_man_idx],
                fillcolor="LimeGreen",
                line_width=0,
                opacity=0.3,
                annotation_text="Active maneuvering",
                layer="below",
            )

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
    name="Parking Out: Maneuvering to Terminate, Number of strokes exeeds, Angular parking ",
    description=f"The function shall switch from Maneuvering to Terminate mode when number of strokes exeeds the limit."
    f"<br>Maximum number of strokes:"
    f"<br>Angular parking: {constants.HilCl.ApThreshold.AP_G_MAX_NUM_STROKES_ANG_NU}",
)
class NumOfStokresAngular(TestCase):
    """NumOfStokresAngular Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            NumOfStokresAngularCheck,
        ]
