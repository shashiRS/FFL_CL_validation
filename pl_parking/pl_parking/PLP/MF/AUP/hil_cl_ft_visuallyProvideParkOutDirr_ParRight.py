"""Check the HMI notification during parkingOut state."""

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

SIGNAL_DATA = "DIRRECTION_PARALLE_RIGHT"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        AVG_TYPE = "AVG_Type"
        USER_ACTION = "User_action"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.AVG_TYPE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralAVGType",
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
        }


example_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="Parallel Right Indicator during Scanning State",
    description="Check the behavior of the system after the driver select the right dirrection from HMI in case ego veh is on a parallel parking slot in Scanning Out state.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class ParkOutDirrParallelRightCheck(TestStep):
    """ParkOutDirrParallelRightCheck Test Step."""

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
        avg_type = read_data["AVG_Type"].tolist()
        user_act_sig = read_data["User_action"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None

        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation the Right dirrection indicator signal is True, the system is providyng a constant visualisation to the intended parkingOut dirrection ({signal_name['AVG_Type']} =="
            f" {constants.HilCl.Hmi.APHMIGeneralAVGType.PARK_OUT_PARALLEL_RIGHT}).".split()
        )

        """Evaluation part"""
        # Find the moment when AP in Scanning Out state
        for idx, item in enumerate(HMI_Info):
            if item == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_OUT:
                t1_idx = idx
                break

        # If AP not in ScanninOut state, TC Failed
        if t1_idx is not None:
            # Find the moment when the driver select the wanted parking out dirrection
            for i in range(t1_idx,len(HMI_Info)):
                if user_act_sig[i] ==  constants.HilCl.Hmi.Command.TAP_ON_PARKING_SPACE_RIGHT_1:
                    t2_idx = i
                    break

            if t2_idx is not None:
                # taking the timestamp of t2_idx in order to check the reaction 0.5s after
                t2_timestamp = time_signal[t2_idx]
                for cnt in range(t2_idx, len(HMI_Info)):
                    if abs(( float(t2_timestamp) - float(time_signal[cnt]) ) / 10**6) > constants.DgpsConstants.THRESOLD_TIME_S:
                        t3_idx = cnt
                        break

                if t3_idx is not None:
                    # Check the system behavior after driver selected the wanted dirrection
                    for y in range(t3_idx,len(HMI_Info)):
                        if avg_type[y] != constants.HilCl.Hmi.APHMIGeneralAVGType.PARK_OUT_PARALLEL_RIGHT:
                            test_result = fc.FAIL
                            eval_cond = [False] * 1
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['AVG_Type']} signal is FAILED,"
                                f" the system didn't provide a constant visualisation of the Right dirrection indicator ( != {constants.HilCl.Hmi.APHMIGeneralAVGType.PARK_OUT_PARALLEL_RIGHT})."
                                f" First failed moment, {time_signal[y]}".split()
                            )
                            break
                else:
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                    f"TC Failed because the scenario finished before the added delay ({constants.DgpsConstants.THRESOLD_TIME_S})".split()
                    )
            else:
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                f"TC Failed because the driver didn't select the parkOut dirrection ({signal_name['User_action']} != {constants.HilCl.Hmi.Command.TAP_ON_PARKING_SPACE_RIGHT_1})".split()
                )
        else:
            eval_cond = [False] * 1
            evaluation1 = " ".join(
            f"TC Failed because AP never in Scanning state ({signal_name['State_on_HMI']} !="
            f" {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_OUT}).".split()
            )

        signal_summary["Check the reaction of the system related to the dirrection indicator during ParkingOut state - parallel right."] = evaluation1

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

        fig.add_trace(go.Scatter(x=time_signal, y=avg_type, mode="lines", name=signal_name["AVG_Type"]))
        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
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
    name="Dirrection Indicator in which the system shall start the parking out maneuver during scanning state - parallel right",
    description="The AP funtion shall continuously show the Right Dirrection Indicator in which the system shall start the parking out maneuver during scanning state",
    doors_url="https://jazz.conti.de/rm4/resources/BI_Xq2G7_V2Ee26y5qu8i0o0w?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F26252, \
               https://jazz.conti.de/rm4/resources/BI_Xq2G8PV2Ee26y5qu8i0o0w?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F26252"
)
class ParkOutDirrParallelRight(TestCase):
    """ParkOutDirrParallelRightTest Case."""

    custom_report = MfHilClCustomTestcaseReport

    # Important information:
    # This script check the behavior of the system in case AVG ON related to the dirrection indicator

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            ParkOutDirrParallelRightCheck,
        ]
