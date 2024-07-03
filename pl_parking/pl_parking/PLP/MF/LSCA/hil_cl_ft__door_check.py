"""LSCA door state check"""

import logging
import os
import sys

import plotly.graph_objects as go

from pl_parking.PLP.MF import constants

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
from pl_parking.common_ft_helper import HilClFuntions, MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.constants import PlotlyTemplate

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "LSCA_DOOR_STATE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        LSCA_STATE = "Lsca_state"
        CAR_DOOR = "Car_door"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.LSCA_STATE: "MTS.ADC5xx_Device.EM_DATA.EmLscaStatusPort.lscaOverallMode_nu",
            self.Columns.CAR_DOOR: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput01.DoorOpen",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="LSCA door dependence check",
    description="Check LSCA state in case of opened door. Doors are opened and closed one-by-one.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class LscaDoorCheck(TestStep):
    """LscaDoorCheck Test Step."""

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
        lsca_state_sig = read_data["Lsca_state"].tolist()
        car_door_sig = read_data["Car_door"].tolist()

        t1_idx = None
        door_open_idx = []
        door_close_idx = []

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Lsca_state']} is PASSED, LSCA function get only be enabled if no door is opened.".split()
        )

        """Evaluation part"""

        # Collect door open and door close events
        door_open_idx = HilClFuntions.RisingEdge(car_door_sig, 0)
        door_close_idx = HilClFuntions.FallingEdge(car_door_sig, 0)
        # Required condition(s) for TestRun
        # 1 - There is at least one door open event
        # 2 - Number of Door Open and number of Door Close equal

        for cnt in range(0, len(lsca_state_sig)):
            if lsca_state_sig[cnt] == constants.HilCl.Lsca.LSCA_ACTIVE:
                t1_idx = cnt
                break

        # Check LSCA was active before first door open
        if t1_idx < door_open_idx[0]:

            if len(door_open_idx) > 0 and len(door_close_idx) == len(door_open_idx):
                eval_cond = [True] * 1

                # Check all door open-close event
                for door_cycle in range(0, len(door_open_idx)):
                    # Start index for the current door cycle
                    start_idx = door_open_idx[door_cycle]

                    # End index for the current door cycle
                    end_idx = door_close_idx[door_cycle]

                    # Check which door is open
                    actual_door_state = constants.HilCl.CarMaker.Door.DICT_DOORS[car_door_sig[start_idx]]
                    actual_door_value = car_door_sig[start_idx]

                    # Check LSCA state in the range from door open to door close
                    for cnt in range(start_idx, end_idx):
                        if lsca_state_sig[cnt] == constants.HilCl.Lsca.LSCA_ACTIVE:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Lsca_state']} signal is FAILED, state of signal is ENABLED ({constants.HilCl.Lsca.LSCA_ACTIVE})"
                                f" at {time_signal[cnt]} us but actual door state is {actual_door_state} ({actual_door_value}).".split()
                            )
                            eval_cond[0] = False
                            break

                    if not eval_cond[0]:
                        break

            elif len(door_open_idx) == 0:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Lsca_state']} is FAILED, state of signal still ({constants.HilCl.CarMaker.Door.ALL_CLOSED})"
                    " during measurement. There is no Door Open event in TestRun.".split()
                )

            elif len(door_close_idx) == 0:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Lsca_state']} is FAILED, there is no Door Close event in TestRun.".split()
                )

            elif len(door_open_idx) != len(door_close_idx):
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Lsca_state']} is FAILED, Door Open and Door Close events are not equal in TestRun.".split()
                )

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join("The evaluation is FAILED, invalide TestRun".split())
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Lsca_state']} is FAILED, state of signal was not active"
                f" ({constants.HilCl.Lsca.LSCA_NOT_ACTIVE}) before the first door open event.".split()
            )

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["LSCA reaction for opened door"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=car_door_sig, mode="lines", name=signal_name["Car_door"]))
            fig.add_trace(go.Scatter(x=time_signal, y=lsca_state_sig, mode="lines", name=signal_name["Lsca_state"]))

            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        """Calculate parameters to additional table"""
        sw_combatibility = (  # Remainder: Update if SW changed and script working well
            "swfw_apu_adc5-2.1.0-DR2-PLP-B1-PAR230"
        )

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
    name="LSCA door dependence",
    description="The LSCA function shall only be enabled if no door is opened.",
)
class LscaDoor(TestCase):
    """LscaDoor Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            LscaDoorCheck,
        ]
