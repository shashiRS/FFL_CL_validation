"""React on brake interrupt. System shall stay in standstill"""

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

SIGNAL_DATA = "REACT_ON_INTERRUPT_OBJ"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        DRIVING_DIR = "Driv_dir"
        PARK_BREAK = "Park_Break"
        PARKING_CORE_STATE = "Parking_Core_State"
        BRAKE = "Brake"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
            self.Columns.PARK_BREAK: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.ParkBrake",
            self.Columns.PARKING_CORE_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput06.BrakePressureDriver",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="React on interruption of manuever",
    description="The goal of this test case is to verify, that in case of an interruption of the AVG the AP function brakes the ego vehicle to standstill and holds the ego vehicle in standstill.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class CommonInterruptBrakeOnCheck(TestStep):
    """CommonInterruptBrakeOnCheck Test Step."""

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
        driv_dir_sig = read_data["Driv_dir"].tolist()
        park_break_sig = read_data["Park_Break"].tolist()
        parking_core_state_sig = read_data["Parking_Core_State"].tolist()
        brake_sig = read_data["Brake"].tolist()

        t_man_idx = None
        t_interrupt_idx = None
        t_standstill_idx = None

        eval_cond = [False] * 1
        evaluation1 = ""

        """Evaluation part"""
        # Find when AP switches to Maneuvering mode
        for cnt in range(0, len(parking_core_state_sig)):
            if parking_core_state_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_man_idx = cnt
                break

        if t_man_idx is not None:
            # Find break interrupt request
            for cnt in range(t_man_idx, len(brake_sig)):
                if brake_sig[cnt] >= constants.HilCl.ApThreshold.AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR:
                    t_interrupt_idx = cnt
                    break

            if t_interrupt_idx is not None:
                # Find when ego vehicle is in standstill
                for cnt in range(t_interrupt_idx, len(driv_dir_sig)):
                    if (
                        driv_dir_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL
                        and park_break_sig[cnt] == constants.HilCl.Brake.PARK_BRAKE_SET
                    ):
                        t_standstill_idx = cnt
                        break

                if t_standstill_idx is not None:
                    eval_cond = [True] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Driv_dir']} signal is PASSED, signal switched to STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL})."
                        f"The evaluation of {signal_name['Park_Break']} signal is PASSED, signal switched to PARK_BREAK_SET ({constants.HilCl.Brake.PARK_BRAKE_SET}).".split()
                    )
                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Driv_dir']} signal is FAILED, signal never switched to STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL})."
                        f"The evaluation of {signal_name['Park_Break']} signal is FAILED, signal never switched to PARK_BREAK_SET ({constants.HilCl.Brake.PARK_BRAKE_SET}).".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Brake']} signal is FAILED, signal never reached AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR ({constants.HilCl.ApThreshold.AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Parking_Core_State']} signal is FAILED, signal never switched to PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}). AP funtion was never activated."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["React on brake interrupt."] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=driv_dir_sig, mode="lines", name=signal_name["Driv_dir"]))
            fig.add_trace(go.Scatter(x=time_signal, y=park_break_sig, mode="lines", name=signal_name["Park_Break"]))
            fig.add_trace(go.Scatter(x=time_signal, y=brake_sig, mode="lines", name=signal_name["Brake"]))
            fig.add_trace(
                go.Scatter(
                    x=time_signal, y=parking_core_state_sig, mode="lines", name=signal_name["Parking_Core_State"]
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
    name="React on interruption of manuever",
    description="The goal of this test case is to verify, that in case of an interruption of the AVG the AP function brakes the ego vehicle to standstill and holds the ego vehicle in standstill.",
)
class CommonInterruptBrakeOn(TestCase):
    """CommonInterruptBrakeOn Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CommonInterruptBrakeOnCheck,
        ]
