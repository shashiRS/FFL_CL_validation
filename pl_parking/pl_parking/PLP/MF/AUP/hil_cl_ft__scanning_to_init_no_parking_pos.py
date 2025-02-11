"""Check the reaction of the system in case the selected parking slot is not available anymore during scanning phase."""

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

SIGNAL_DATA = "SCANNING_TO_INIT_NO_PARKING_POSSIBLE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USER_ACTION = "User_action"
        HMI_INFO = "State_on_HMI"
        TARGET_POS = "Target_pos"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.TARGET_POS: "CM.Traffic.Park00.tx",
        }


example_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="Scanning to Init, no parking possible",
    description="Check the behavior of the system in case the length of the selected parking slot is not sufficient anymore.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class ScanningToInitNoParkingPossibleCheck(TestStep):
    """ScanningToInitNoParkingPossibleCheck Test Step."""

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
        target_pos = read_data["Target_pos"].tolist()
        user_act_sig = read_data["User_action"].tolist()
        target_length = 4.67

        t1_idx = None
        t2_idx = None
        t3_idx = None

        # Take the rear botton point of the right target vehicle
        # starting_point_parking_slot = 56
        end_point_parking_slot = 62.5

        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation of ParkingProcedureCtrlState PASSED signal switch to PPC_BEHAVIOR_INACTIVE ({signal_name['State_on_HMI']} =="
            f" {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE}).".split()
        )

        """Evaluation part"""
        # Find the moment when the driver select the parking slot ( APHMIOutUserActionHU = TAP_ON_PARKING_SPACE_RIGHT_4 )
        for cnt in range(0, len(user_act_sig)):
            if (
                user_act_sig[cnt] == constants.HilCl.Hmi.Command.TAP_ON_PARKING_SPACE_RIGHT_4 and
                end_point_parking_slot - (target_pos[cnt] + target_length) >= constants.ConstantsSI.AP_V_LENGTH_M + constants.ConstantsSI.AP_G_PAR_SLOT_MIN_OFFSET_L_M
            ):
                t1_idx = cnt
                break

        # If driver didn't select a free slot, TC Failed
        if t1_idx is not None:
            # Find the moment when target vehicle moves to the selected parking slot so the length is not sufficient anymore
            for y in range(t1_idx, len(HMI_Info)):
                if end_point_parking_slot - (target_pos[y] + target_length) < constants.ConstantsSI.AP_V_LENGTH_M + constants.ConstantsSI.AP_G_PAR_SLOT_MIN_OFFSET_L_M:
                    t2_idx = y
                    break
            if t2_idx is not None:
                # Check if we have a constant AVG state = 3
                for _ in range(t1_idx, t2_idx):
                    if HMI_Info[_] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN:
                        eval_cond = [False] * 1
                        break
                if eval_cond[0] is not False:
                    # taking the timestamp of t2_idx in order to check the reaction of the system 0.5s after
                    t2_timestamp = time_signal[t2_idx]
                    for x in range(t2_idx, len(HMI_Info)):
                        if abs(( float(t2_timestamp) - float(time_signal[x]) ) / 10**6) > constants.DgpsConstants.THRESOLD_TIME_S:
                            t3_idx = x
                            break
                    if t3_idx is not None:
                        # check the reaction of the system 0.5s
                        if HMI_Info[cnt] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE:
                            eval_cond = [False] * 1
                            evaluation1 = " ".join(
                            "The system didn't change the state to Terminate after the length of the selected parking slot is smaller than minimum "
                            f"({signal_name['State_on_HMI']} != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE}) within 500ms.".split()
                            )
                    else:
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                        f"TC Failed because the scenario finished before the added delay ({constants.HilCl.ApThreshold.AP_G_ROLLED_DIST_OUT_THRESH_M}).".split()
                        )
                else:
                    evaluation1 = " ".join(
                            f"TC Failed because AVG ({signal_name['State_on_HMI']}) don't have a constant scanning state (!= {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN} before precondition met).".split()
                            )
            else:
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                "TC Failed because reference vehicle didn't moved to the selected parking slot.".split()
                )
        else:
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                    f"TC Failed because AVG never in scanning state( {signal_name['State_on_HMI']} !="
                    f" {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN}).".split()
                )

        signal_summary["Check the reaction of the system in case AVG in scanning state and minimum length is not sufficient anymore."] = evaluation1

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

        fig.add_trace(go.Scatter(x=time_signal, y=target_pos, mode="lines", name=signal_name["Target_pos"]))
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
    name="Scanning to Init No Parking Possible",
    description=f"The system shall switch from Scanning({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_IN}) to Init({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE}) after reference vehicle start the movement.",
    doors_url="https://jazz.conti.de/rm4/resources/BI_it4U0OeJEe6f_fKhM-zv_g?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F26252"
)
class ScanningToInitNoParkingPossible(TestCase):
    """ScanningToInitNoParkingPossible Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    # Important information:
    # This script check the behavior of the system in case a snow/sand/soil pile is present in front of the ego vehicle while driving

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            ScanningToInitNoParkingPossibleCheck,
        ]
