"""Check the latency between sending remote parking commands from the Remote Device until the intended effect is observed in the vehicle."""
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

__author__ = "VALERICA ATUDOSIEI"

SIGNAL_DATA = "RP_LATENCY_INTERRUPT"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        FINGER_POS_X = "Finger_pos_x"
        FINGER_POS_Y = "Finger_pos_y"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.FINGER_POS_X: "MTS.IO_CAN_AP_Private_CAN.APHMIOut2.APHMIOutRemFingerPosX",
            self.Columns.FINGER_POS_Y: "MTS.IO_CAN_AP_Private_CAN.APHMIOut2.APHMIOutRemFingerPosY",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Latency observed in the car, interrupt RP.",
    description="The observed latency shall be less than {AP_G_MAX_LATENCY_REM_S} between the moment when RC is used and the reaction saw in the car.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class RPLatencyInterruptCheck(TestStep):
    """RPLatencyInterruptCheck Test Step."""

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
        Finger_pos_X = read_data["Finger_pos_x"].tolist()
        Finger_pos_Y = read_data["Finger_pos_y"].tolist()

        t1_idx = None
        t2_idx = None
        trigger_AP_within_range = False

        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation of AVG State {signal_name['State_on_HMI']} signal is PASSED,"
            f" signal switches to PAUSE state [{constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_PAUSE}] within {constants.HilCl.ApThreshold.AP_G_MAX_LATENCY_REM_S}s".split()
        )

        """Evaluation part"""
        # Find the moment when AP function is activated
        for cnt in range(0, len(HMI_Info)):
            if HMI_Info[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = cnt
                break
        if t1_idx is not None:
            # Search for the moment when the parking maneuver is interrupted
            for _ in range(t1_idx, len(HMI_Info)):
                if Finger_pos_X[cnt] != constants.HilCl.Hmi.RemFingerPosition.DM_FINGER_POS_X or Finger_pos_Y[cnt] != constants.HilCl.Hmi.RemFingerPosition.DM_FINGER_POS_Y:
                    t2_idx = _
                    break

            if t2_idx is not None:
                # taking the timestamp of t1_idx in order to check the reaction after {AP_G_MAX_LATENCY_REM_S}s
                t2_timestamp = time_signal[t2_idx]
                for y in range(t1_idx, len(HMI_Info)):
                    if abs(( float(t2_timestamp) - float(time_signal[y]) ) / 10**6) > constants.HilCl.ApThreshold.AP_G_MAX_LATENCY_REM_S:
                        t3_idx = y
                        break

                if t3_idx is not None:
                    # Check if the system interrupt the maneuver within {AP_G_MAX_LATENCY_REM_S}s
                    for i in range(t2_idx, t3_idx):
                        if HMI_Info[i] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_PAUSE:
                            trigger_AP_within_range = True
                            break

                    if trigger_AP_within_range is not True:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                            f" AP function not interrupted within {constants.HilCl.ApThreshold.AP_G_MAX_LATENCY_REM_S}s ( != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_PAUSE}).".split()
                        )
                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"TC Failed because the scenario finished before {constants.HilCl.ApThreshold.AP_G_MAX_LATENCY_REM_S}s after the driver used the remote controller".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                            f" driver didn't interrupt the maneuver, preconditions are not met.".split()
                        )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"TC Failed, AP function never activated (APHMIParkingProcedureCtrlState != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})".split()
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
            "Check the reaction of the system during Parking In phase in case the maneuver is interrupted via remote controller."
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=Finger_pos_X, mode="lines", name=signal_name["Finger_pos_x"]))
        fig.add_trace(go.Scatter(x=time_signal, y=Finger_pos_Y, mode="lines", name=signal_name["Finger_pos_y"]))
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
    name="Latency observed in the car - interrupt RP.",
    description="The observed latency in the car shall be less than {AP_G_MAX_LATENCY_REM_S}s in case of interrupt via RC.",
    doors_url="https://jazz.conti.de/rm4/resources/BI_PfDRTMlcEe2iKqc0KPO99Q?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
class RPLatencyInterrupt(TestCase):
    """RPLatencyInterrupt Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            RPLatencyInterruptCheck,
        ]
