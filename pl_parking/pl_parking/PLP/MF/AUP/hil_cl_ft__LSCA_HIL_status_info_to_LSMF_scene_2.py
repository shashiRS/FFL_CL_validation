"""The system shall provide status information (active/inactive) to the LSMF (Scene_2: Inactive LSMF shall not activate)"""
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
    verifies,
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

__author__ = "VALERICA ATUDOSIEI"

SIGNAL_DATA = "STATUS_INFO_LSMF_SCENE_2"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        USEER_ACTION = "User_action"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.USEER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Behavior check, LSCA deactivation before AVG ON",
    description="Check the behavior of the system if the LSCA is deactivated before AVG ON.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class StatusInfoToLSMFScene2Check(TestStep):
    """StatusInfoToLSMFScene2Check Test Step."""

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
        HMI_Info = read_data["State_on_HMI"].tolist()
        user_act_sig = read_data["User_action"].tolist()

        t1_lsca_selected = None
        t2_hmi_start_parking = None
        t3_start_parking_man = None
        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation of AVG State {signal_name['State_on_HMI']} signal is PASSED,"
            f" signal switches to Init - ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE})".split()
        )

        """Evaluation part"""
        # Find the moment when LSCA is selected via HMI
        for cnt in range(0, len(HMI_Info)):
            if user_act_sig[cnt] == constants.HilCl.Hmi.Command.TAP_ON_LSCA:
                t1_lsca_selected = cnt
                break
        if t1_lsca_selected is not None:
            # Find the moment when the driver select the starting of parking maneuver
            for i in range(t1_lsca_selected, len(HMI_Info)):
                if user_act_sig[i] == constants.HilCl.Hmi.Command.TAP_ON_START_PARKING:
                    t2_hmi_start_parking = i
                    break
            if t2_hmi_start_parking is not None:
                # check the system state until the end of the scenario
                for y in range(t2_hmi_start_parking, len(HMI_Info)):
                    if HMI_Info[y] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                        t3_start_parking_man = y
                        break
                if t3_start_parking_man is not None:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                        f" AVG ON (APHMIParkingProcedureCtrlStat == {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})after LSCA deactivated.".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"TC Failed driver didn't select the start parking maneuver from HMI (APHMIOutUserActionHU != {constants.HilCl.Hmi.Command.TAP_ON_START_PARKING})".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                        f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                        f" LSCA not selected by the driver (APHMIOutUserActionHU != {constants.HilCl.Hmi.Command.TAP_ON_LSCA}).".split()
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
            "Check the reaction of the system if LSCA is deactivated and try to start the parking maneuver"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
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

@verifies(
    requirement="1993818",
)
@testcase_definition(
    name="Check the system behavior in case LSCA deactivated before AVG ON",
    description="Check the behavior of the system if the LSCA is deactivated before AVG ON.",
    doors_url="https://jazz.conti.de/rm4/resources/BI_Ob4AYN1mEe62R7UY0u3jZg?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
class StatusInfoToLSMFScene2(TestCase):
    """StatusInfoToLSMFScene2 Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            StatusInfoToLSMFScene2Check,
        ]
