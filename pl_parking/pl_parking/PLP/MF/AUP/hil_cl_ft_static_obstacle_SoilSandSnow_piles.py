"""Detect static objects snow, soil, sand pile."""

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

SIGNAL_DATA = "STATIC_DETECT"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        CAR_HITCH_X = "Car_hitch_x"
        DRIVING_DIR = "Driv_dir"
        USER_ACTION = "User_action"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.CAR_HITCH_X: "CM.Car.Hitch.tx",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
        }


example_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="AP static object detection soil sand snow",
    description="Check AP considers sand/soil/snow as static object",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class StaticObstacleSSSPileCheck(TestStep):
    """StaticObstacleSSSPileCheck Test Step."""

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
        car_hitch_x = read_data["Car_hitch_x"].tolist()
        user_act_sig = read_data["User_action"].tolist()
        driv_dir_sig = read_data["Driv_dir"].tolist()

        # the actual position of the pile from CM
        pile_pos = 27
        t1_idx = None
        t2_idx = None

        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation of signal {signal_name['Driv_dir']} is PASSED, ego veh stops before the obstacle.".split()
        )

        """Evaluation part"""
        # Find when user activate the AP function
        for idx, item in enumerate(user_act_sig):
            if item == constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE:
                t1_idx = idx
                break

        # If AP not active, TC Failed
        if t1_idx is not None:
            for cnt in range(t1_idx, len(driv_dir_sig)):
                if driv_dir_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL:
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                if car_hitch_x[t2_idx] + constants.ConstantsSlotDetection.CAR_LENGTH >= pile_pos:
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                    f"The evaluation for position of ego veh is Failed, ({signal_name['Car_hitch_x']} + {constants.ConstantsSlotDetection.CAR_LENGTH}) is >= pos of the pile, ego veh not stopping in time.".split()
                    )
            else:
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                f"The evaluation of {signal_name['Driv_dir']} is Failed, ego veh didn't stop.".split()
                )

        else:
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of the signal {signal_name['User_action']} is Failed, AP never active (signal value != {constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE}).".split()
            )

        signal_summary["Check the reaction of the system in case a sand/soil/snow pile is present on ego lane"] = evaluation1

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=driv_dir_sig, mode="lines", name=signal_name["Driv_dir"]))
        fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
        fig.add_trace(go.Scatter(x=time_signal, y=car_hitch_x, mode="lines", name=signal_name["Car_hitch_x"]))
        fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[us]")
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
    name="AP static object detection soil sand snow",
    description="The AP funtion shall consider sand/soil/snow pile as static obstacle",
    doors_url="https://jazz.conti.de/rm4/resources/BI_XqxOVfV2Ee26y5qu8i0o0w?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099"
)
class StaticObstacleSSSPile(TestCase):
    """StaticObstacleSSSPile Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    # Important information:
    # This script check the behavior of the system in case a snow/sand/soil pile is present in front of the ego vehicle while driving

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            StaticObstacleSSSPileCheck,
        ]
