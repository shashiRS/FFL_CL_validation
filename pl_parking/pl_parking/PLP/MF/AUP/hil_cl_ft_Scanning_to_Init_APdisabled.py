"""Check the transition from Scanning to Init."""

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

SIGNAL_DATA = "SCANNING_TO_INIT_AP_DISABLED"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USER_ACTION = "User_action"
        HMI_INFO = "State_on_HMI"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
        }


example_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="Transition from Scanning state to Init",
    description="Check the behavior of the system in case AP function is disabled in Scanning state",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class ScanningToInitAPdisabledCheck(TestStep):
    """ScanningToInitAPdisabledCheck Test Step."""

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
        user_act_sig = read_data["User_action"].tolist()
        HMI_Info = read_data["State_on_HMI"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None

        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation of AP State transition is PASSED signal switch to Terminate ({signal_name['State_on_HMI']} =="
            f" {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE}).".split()
        )

        """Evaluation part"""
        # Find when the AP function is in SCANNING state
        for idx, value in enumerate(HMI_Info):
            if value == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN and user_act_sig[idx] == constants.HilCl.Hmi.Command.NO_USER_ACTION:
                t1_idx = idx
                break

        # If AP not in scanning state, TC Failed
        if t1_idx is not None:
            for cnt in range(t1_idx, len(HMI_Info)):
                if user_act_sig[cnt] == constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE:
                    t2_idx = cnt
                    break
            if t2_idx is not None:
                # check between t1_idx and t2_idx if AVG have a constant PPC_SCANNING_IN state
                for i in range(t1_idx,t2_idx):
                    if HMI_Info[i] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                            f" AVG not in Scanning state ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN}) before disabling the function.".split()
                        )
                        break
                # taking the timestamp of t2_idx in order to check the reaction 0.5s after
                t2_timestamp = time_signal[t2_idx]
                for cnt in range(t2_idx, len(HMI_Info)):
                    if abs(( float(t2_timestamp) - float(time_signal[cnt]) ) / 10**6) > constants.DgpsConstants.THRESOLD_TIME_S:
                        t3_idx = cnt
                        break
                # check if after 0.5s the AVG switch to Init state
                if t3_idx is not None:
                    if HMI_Info[t3_idx] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE:
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                        f"The transition of the AP state ({signal_name['State_on_HMI']}) is Failed, the state didn't switch to Init "
                        f"({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE}) within 500ms".split()
                        )
                else:
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                    f"TC Failed because the scenario finished before the added delay ({constants.HilCl.ApThreshold.AP_G_ROLLED_DIST_OUT_THRESH_M}).".split()
                    )
            else:
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                f"TC Failed because the AP function was not disabled ({signal_name['User_action']} != {constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE}).".split()
                )
        else:
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                    f"TC Failed because AP never in Scanning state ( {signal_name['State_on_HMI']} !="
                    f" {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN}).".split()
                )

        signal_summary["Check the reaction of the system in case a function is disabled during Scanning In state"] = evaluation1

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

        fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
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
    name="AP state transition Scanning to Init",
    description="The AP funtion shall switch to Init from Scanning after function is disabled",
    doors_url="https://jazz.conti.de/rm4/resources/BI_J5u0sEfmEe68PtCWeWkWbA?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324"
)
class ScanningToInitAPdisabled(TestCase):
    """ScanningToInitAPdisabled Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    # Important information:
    # This script check the behavior of the system in case a snow/sand/soil pile is present in front of the ego vehicle while driving

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            ScanningToInitAPdisabledCheck,
        ]
