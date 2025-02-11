"""The system shall provide status information (active/inactive) to the LSMF (Scene_3: Error deactivates LSCA --> active LSMF shall terminate and go to safe state)"""
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

SIGNAL_DATA = "STATUS_INFO_LSMF_SCENE_3"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        USEER_ACTION = "User_action"
        HOLD_REQ = "Hold_req"
        ENABLE_REQ = "Enable_req"
        FRAME_TIMEOUT = "Frame_timeout"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.USEER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.HOLD_REQ: "MTS.Conti_Veh_CAN.APReq01.LoDMCHoldReq",
            self.Columns.FRAME_TIMEOUT: "MTS.vCUS.FTi.Sensor[0].Pdcm.E2E.FrameTimeout",
            self.Columns.ENABLE_REQ: "MTS.vCUS.FTi.EnableReq",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Behavior check, Error after AVG ON",
    description="Check the behavior of the system if LSCA have an error after AVG ON.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class StatusInfoToLSMFScene3Check(TestStep):
    """StatusInfoToLSMFScene3Check Test Step."""

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
        hold_rq = read_data["Hold_req"].tolist()
        enable_req = read_data["Enable_req"].tolist()
        frame_timeout = read_data["Frame_timeout"].tolist()

        t1_ap_start_parking_maneuver = None
        t2_failure_inserted = None
        t3_after_delay_added = None
        trigger_state = True
        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation of AVG State {signal_name['State_on_HMI']} signal is PASSED,"
            f" signal switches to Failed - ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_IRREVERSIBLE_ERROR})".split()
        )

        """Evaluation part"""
        # Find the moment when AP function start the parking maneuver
        for cnt in range(0, len(HMI_Info)):
            if HMI_Info[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_ap_start_parking_maneuver = cnt
                break
        if t1_ap_start_parking_maneuver is not None:
            # Find the moment when error is inserted
            for i in range(t1_ap_start_parking_maneuver, len(HMI_Info)):
                if enable_req[i] == 1 and frame_timeout[i] == constants.HilCl.CarMaker.UssError.TIMEOUT_ENABLED:
                    t2_failure_inserted = i
                    break
            if t2_failure_inserted is not None:
                # Check if the system is in Perform Parking until failure inserted
                for _ in range(t1_ap_start_parking_maneuver, t2_failure_inserted):
                    if HMI_Info[cnt] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                        trigger_state = False
                        break
                if trigger_state:
                    # taking the timestamp of t2_failure_inserted in order to check the reaction 0.5s after
                    t2_timestamp = time_signal[t2_failure_inserted]
                    for y in range(t2_failure_inserted, len(HMI_Info)):
                        if abs(( float(t2_timestamp) - float(time_signal[y]) ) / 10**6) > constants.DgpsConstants.THRESOLD_TIME_S:
                            t3_after_delay_added = y
                            break
                    if t3_after_delay_added is not None:
                        # check the state of the system
                        if HMI_Info[t3_after_delay_added] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_IRREVERSIBLE_ERROR or hold_rq[t3_after_delay_added] != constants.HilCl.Hmi.LoDMCHoldReq.TRUE:
                            test_result = fc.FAIL
                            eval_cond = [False] * 1
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                                f" AVG not in Failed state (APHMIParkingProcedureCtrlState != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_IRREVERSIBLE_ERROR}) after LSCA turned ON"
                                f" or system not in hold state (LoDMCHoldReq != {constants.HilCl.Hmi.LoDMCHoldReq.TRUE})".split()
                            )
                    else:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"TC Failed because the scenario finished before the delay finished ({constants.DgpsConstants.THRESOLD_TIME_S})".split()
                        )
                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"TC Failed because the system don't have a constant Perform Parking state (APHMIParkingProcedureCtrlState != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                            f"TC Failed because the failure was not inserter into the system({signal_name['Enable_req']} == 1"
                            f" and {signal_name['Frame_timeout']} == -1).".split()
                            )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                "TC Failed because AP never in Perform Parking state,"
                f" ({signal_name['State_on_HMI']} != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}).".split()
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
            "Check the reaction of the system if LSCA in error after AVG ON"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=enable_req, mode="lines", name=signal_name["Enable_req"]))
        fig.add_trace(go.Scatter(x=time_signal, y=frame_timeout, mode="lines", name=signal_name["Frame_timeout"]))
        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
        fig.add_trace(go.Scatter(x=time_signal, y=hold_rq, mode="lines", name=signal_name["Hold_req"]))
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
    name="Behavior check, error LSCA Error after AVG ON.",
    description="Check the behavior of the system if the system have an error after AVG ON",
    doors_url="https://jazz.conti.de/rm4/resources/BI_Ob4AYN1mEe62R7UY0u3jZg?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
class StatusInfoToLSMFScene3(TestCase):
    """StatusInfoToLSMFScene3 Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            StatusInfoToLSMFScene3Check,
        ]
