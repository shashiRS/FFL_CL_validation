"""Check the dirrection indicator during AVG ON."""

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

SIGNAL_DATA = "DIRRECTION_INDICATOR_AVG_RIGHT"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        TURN_SIG_LEVER = "Turn_sig_lever"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.TURN_SIG_LEVER: "MTS.Conti_Veh_CAN.Conti_Veh_CAN.VehInput06.TurnSignallLever",
        }


example_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="Right dirrection Indicator during AVG ON",
    description="Check the behavior of the system related to dirrection indicator while performing the automated parking",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class DirrIndicatorDuringAVGonCheck(TestStep):
    """DirrIndicatorDuringAVGonCheck Test Step."""

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
        HMI_Info = read_data["State_on_HMI"].tolist()
        turn_sig_lever = read_data["Turn_sig_lever"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None

        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation the right turn indicator signal is True, the system is providyng a constant visualisation to the expected final pose ({signal_name['Turn_sig_lever']} =="
            " 2).".split()
        )

        """Evaluation part"""
        # Find whthe moment when AP start to control the ego vehicle
        for idx, item in enumerate(HMI_Info):
            if item == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = idx
                break

        # If AP not active, TC Failed
        if t1_idx is not None:
            # taking the timestamp of t1_idx in order to check the reaction 0.5s after
            t1_timestamp = time_signal[t1_idx]
            for cnt in range(t1_idx, len(HMI_Info)):
                if abs(( float(t1_timestamp) - float(time_signal[cnt]) ) / 10**6) > constants.DgpsConstants.THRESOLD_TIME_S:
                    t2_idx = cnt
                    break
            if t2_idx is not None:
                # Find the moment when AVG stop the maneuvering mode
                for i in range(t2_idx,len(HMI_Info)):
                    if HMI_Info[i] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                        t3_idx = i
                if t3_idx is not None:
                    for i in range(t2_idx,t3_idx):
                        if turn_sig_lever[i] != constants.HilCl.TurnSignallLever.TURN_LEVER_ENGAGED_RIGHT:
                            test_result = fc.FAIL
                            eval_cond = [False] * 1
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Turn_sig_lever']} signal is FAILED,"
                                " the system didn't provide a constant visualisation of the right turn indicator(2).".split()
                            )
                            break
                else:
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                    f"TC Failed because the AP function not finishing the parking maneuver({signal_name['State_on_HMI']} != "
                    f"{constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}).".split()
                    )
            else:
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                f"TC Failed because the scenario finished before the added delay ({constants.HilCl.ApThreshold.AP_G_ROLLED_DIST_OUT_THRESH_M})".split()
                )
        else:
            eval_cond = [False] * 1
            evaluation1 = " ".join(
            f"TC Failed because AP never in Maneuvering state ({signal_name['State_on_HMI']} !="
            f" {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}).".split()
            )

        signal_summary["Check the reaction of the system related to the dirrection indicator during maneuvering mode."] = evaluation1

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

        fig.add_trace(go.Scatter(x=time_signal, y=turn_sig_lever, mode="lines", name=signal_name["Turn_sig_lever"]))
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
    name="Right Dirrection Indicator during AVG ON",
    description="The AP funtion shall continuously show the right dirrection indicator in the direction of the intended final pose",
    doors_url="https://jazz.conti.de/rm4/resources/BI_6X7gUET0Ee-vpsGuug6K4Q?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F26252"
)
class DirrIndicatorDuringAVGon(TestCase):
    """DirrIndicatorDuringAVGon Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    # Important information:
    # This script check the behavior of the system in case AVG ON related to the dirrection indicator

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            DirrIndicatorDuringAVGonCheck,
        ]
