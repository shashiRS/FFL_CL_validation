"""Minimum lenght of strokes during active maneuver"""

import logging
import os
import sys

import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
from math import sqrt

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

SIGNAL_DATA = "MIN_LENGHT_OF_STROKES"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        CAR_TX = "Car_tx"
        CAR_TY = "Car_ty"
        ACTUAL_GEAR = "Actual_gear"
        HMI_INFO = "State_on_HMI"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CAR_TX: "CM.Car.tx",
            self.Columns.CAR_TY: "CM.Car.ty",
            self.Columns.ACTUAL_GEAR: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActualGear",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Minimumlenght of a signle stroke",
    description="Check lenght of all stroke and compare distance of stroke with minimum lenght of stroke",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupMinLenStrokeCheck(TestStep):
    """AupMinLenStrokeCheck Test Step."""

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
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()
        car_tx_sig = read_data["Car_tx"].tolist()
        car_ty_sig = read_data["Car_ty"].tolist()
        actual_gear_sig = read_data["Actual_gear"].tolist()

        t_start_man_idx = None
        t_end_man_idx = None

        distance = None
        distance_list = []

        old_tx = None
        old_ty = None

        evaluation1 = ""

        """Evaluation part"""
        # Find AP active user action on HMI
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_start_man_idx = cnt
                break

        if t_start_man_idx is not None:

            # Find end of maneuvering
            for cnt in range(t_start_man_idx, len(state_on_hmi_sig)):
                if state_on_hmi_sig[cnt] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                    t_end_man_idx = cnt
                    break

            if t_end_man_idx is not None:

                eval_cond = [True] * 1

                gears_dict = HilClFuntions.States(actual_gear_sig, t_start_man_idx, t_end_man_idx + 1, 1)
                counter = 0

                for key in gears_dict:
                    if counter == 0:  # Skip because tester set gear to N before start parking
                        counter += 1
                        continue

                    if counter == 1:  # Skip because system switch grear to required gear at first time
                        old_tx = car_tx_sig[key]
                        old_ty = car_ty_sig[key]
                        counter += 1
                        continue

                    else:
                        distance = sqrt((car_tx_sig[key] - old_tx) ** 2 + (car_ty_sig[key] - old_ty) ** 2)
                        distance_list.append(distance)

                        if distance < constants.HilCl.ApThreshold.AP_G_MIN_LENGTH_STROKE_M:
                            eval_cond[0] = False
                            test_result = fc.FAIL
                            evaluation1 = " ".join(
                                f"The evaluation is FAILED, distance of actual store is {distance} m"
                                f" but required minimum distance is {constants.HilCl.ApThreshold.AP_G_MIN_LENGTH_STROKE_M} m.".split()
                            )
                            break

                        old_tx = car_tx_sig[key]
                        old_ty = car_ty_sig[key]

                        counter += 1

                if all(eval_cond):
                    test_result = fc.PASS
                    evaluation1 = " ".join(
                        f"The evaluation is PASSED, the shortest traveled distance was {min(distance_list)} m in a signle stroke and"
                        f" required minimum distance is {constants.HilCl.ApThreshold.AP_G_MIN_LENGTH_STROKE_M} m.".split()
                    )
            else:
                test_result = fc.FAIL
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched out from PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never set to PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["A single stroke shall have a minimum travelled distance"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=car_tx_sig, mode="lines", name=signal_name["Car_tx"]))
            fig.add_trace(go.Scatter(x=time_signal, y=car_ty_sig, mode="lines", name=signal_name["Car_ty"]))
            fig.add_trace(go.Scatter(x=time_signal, y=actual_gear_sig, mode="lines", name=signal_name["Actual_gear"]))

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
    name="A single stroke shall have a minimum travelled distance",
    description=f"The AP function shall maneuver the ego vehicle in a manner that"
    f" a single stroke shall have a minimum travelled distance of {constants.HilCl.ApThreshold.AP_G_MIN_LENGTH_STROKE_M} m.",
)
class AupMinLenStroke(TestCase):
    """AupMinLenStroke Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupMinLenStrokeCheck,
        ]
