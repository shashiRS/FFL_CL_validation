"""The system shall be able to consider free parking slots if the color of the markings is while/yellow."""
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

SIGNAL_DATA = "CONS_LANE_MARKING"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        PARK_SLOT_FREE_RIGHT = "Park_slot_free_right"
        HMI_INFO = "State_on_HMI"
        CAR_SPEED = "Car_speed"
        DRIVING_DIR = "Driv_dir"
        USER_ACTION = "User_action"
        GEAR = "Gear_pos"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.PARK_SLOT_FREE_RIGHT: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInSituationRight.ParkingSlotFreeRight",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.GEAR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralCurrentGear",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Consider white/yellow lane markings",
    description="Check if the system is able to detect free parking slots if the color of the markings is white/yellow.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class ConsLaneMarkingsCheck(TestStep):
    """ConsLaneMarkingsCheck Test Step."""

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

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        park_slot_free_right = read_data["Park_slot_free_right"].tolist()
        HMI_Info = read_data["State_on_HMI"].tolist()
        driv_dir_sig = read_data["Driv_dir"].tolist()
        user_act_sig = read_data["User_action"].tolist()
        gear_pos = read_data["Gear_pos"].tolist()

        t1_idx = None
        t2_idx = None

        evaluation1 = " ".join(
            f"The evaluation for the detection of free parking slots ({signal_name['Park_slot_free_right']}) is PASSED,"
            f" the system consider white/yellow as valid markings and provide a positive number of free parking slots".split()
        )

        """Evaluation part"""
        # Find when user activate the AP function
        for idx, item in enumerate(user_act_sig):
            if item == constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE:
                t1_idx = idx
                break

        # If AP not active, TC Failed
        if t1_idx is not None:
            eval_cond = [True] * 1
            for cnt in range(t1_idx, len(driv_dir_sig)):
                if driv_dir_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL and gear_pos[cnt] == constants.HilCl.Gear.GEAR_P:
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                if park_slot_free_right[t2_idx] < 1:
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                    f"The evaluation for the detection of free parking slots ({signal_name['Park_slot_free_right']}) is  False (<1, the system is not detecting any slot available in the parking area)".split()
                    )
            else:
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                f"The evaluation of {signal_name['Driv_dir']} is False, ego veh didn't stop or gear pos != Parking".split()
                )

        else:
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['User_action']} is False, AP never active".split()
            )

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary[
            "Check the reaction of the system in case the color of the parking markings is white/yellow."
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=park_slot_free_right, mode="lines", name=signal_name["Park_slot_free_right"]))
        fig.add_trace(go.Scatter(x=time_signal, y=driv_dir_sig, mode="lines", name=signal_name["Driv_dir"]))
        fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=gear_pos, mode="lines", name=signal_name["Gear_pos"]))
        fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
        fig.update_layout(PlotlyTemplate.lgt_tmplt)

        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

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
    name="Consider white/yellow lane markings",
    description="In case the parking markings color is white/yellow, the system shall be able to detect free slots and"
                " provide this info to the driver(APHMIInSituationRight.ParkingSlotFreeRight >= 1)",
    doors_url="https://jazz.conti.de/rm4/resources/BI_P1CmIJUBEe688_FkznaDhw?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
class ConsLaneMarkings(TestCase):
    """ConsLaneMarkings Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            ConsLaneMarkingsCheck,
        ]
