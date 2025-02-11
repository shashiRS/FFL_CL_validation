"""Check Dead Man Switch Reaction Timing for Safe State Transition"""

import logging
import os
import sys

import plotly.graph_objects as go

log = logging.getLogger(__name__)
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
from pl_parking.common_ft_helper import MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.constants import PlotlyTemplate

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "Serban Marius"

SIGNAL_DATA = "MANEUVERING_STATE_SAFE_CHECK"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        REM_FINGER_X = "Rem_finger_x"
        REM_FINGER_Y = "Rem_finger_y"
        HOLD_REQUEST = "Hold_request"
        STATE_ON_HMI = "State_on_HMI"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.REM_FINGER_X: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutRemFingerPosX",
            self.Columns.REM_FINGER_Y: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutRemFingerPosY",
            self.Columns.HOLD_REQUEST: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCHoldReq",
            self.Columns.STATE_ON_HMI: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Maneuvering State Dead Man Switch Check",
    description="The system shall enter a safe state if the dead man switch is not pressed within 100ms after being released during maneuvering.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class ManeuveringStateSafeCheck(TestStep):
    """ManeuveringStateSafeCheck Test Step."""

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
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        rem_finger_x_sig = read_data["Rem_finger_x"].tolist()
        rem_finger_y_sig = read_data["Rem_finger_y"].tolist()
        hold_request_sig = read_data["Hold_request"].tolist()
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None
        evaluation1 = " "

        # Step 1: Detect when the system enters maneuvering state
        for cnt, state in enumerate(state_on_hmi_sig):
            if state == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = time_signal[cnt]
                break

        if t1_idx is None:
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} is FAILED, the system never switched to the maneuvering state {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}.".split()
            )
            test_result = fc.FAIL
        else:
            # Step 2: Detect when dead man's switch is released
            for cnt in range(len(time_signal)):
                if time_signal[cnt] >= t1_idx:
                    rem_finger_x = rem_finger_x_sig[cnt]
                    rem_finger_y = rem_finger_y_sig[cnt]

                    if (
                        rem_finger_x != constants.HilCl.Hmi.RemFingerPosition.DM_FINGER_POS_X
                        or rem_finger_y != constants.HilCl.Hmi.RemFingerPosition.DM_FINGER_POS_Y
                    ):
                        t2_idx = cnt
                        break

            if t2_idx is None:
                test_result = fc.FAIL
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Rem_finger_x']} and {signal_name['Rem_finger_y']} is FAILED, the dead man's switch was never released during the maneuvering state.".split()
                )
            else:
                # Step 3: Detect when hold request is triggered
                for cnt in range(t1_idx, len(time_signal)):
                    if hold_request_sig[cnt] == constants.HilCl.LoDMCHoldReq.TRUE:
                        t3_idx = cnt
                        break

                if t3_idx is None:
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Hold_request']} is FAILED, the system did not trigger a hold request [{constants.HilCl.LoDMCHoldReq.TRUE}] after the dead man's switch was released.".split()
                    )
                    test_result = fc.FAIL
                else:
                    # Step 4: Compare time difference between t_dead_man_release and t_hold_request
                    time_difference = (time_signal[t3_idx] - time_signal[t2_idx]) / constants.GeneralConstants.US_IN_MS
                    if time_difference < constants.HilCl.SotifTime.T_PRESS_DEAD_MAN_SWITCH:  # tPRESS = 100ms
                        test_result = fc.FAIL
                        evaluation1 = " ".join(
                            f"The evaluation is FAILED, the system transitioned to a safe state too early. It did not wait for the required {constants.HilCl.SotifTime.T_PRESS_DEAD_MAN_SWITCH} [ms] "
                            f"of the dead man's switch being unpressed. Time difference {time_difference} [ms]".split()
                        )
                    else:
                        test_result = fc.PASS
                        evaluation1 = " ".join(
                            f"The evaluation is PASSED, the system correctly went to a safe state after {constants.HilCl.SotifTime.T_PRESS_DEAD_MAN_SWITCH} [ms] of the dead man's switch being unpressed. Time difference: {time_difference} [ms].".split()
                        )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Dead man switch safe state timing evaluation"] = evaluation1

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_header_left="Evaluation")
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        # Generate chart if test result FAILED
        if test_result == fc.FAIL:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=time_signal, y=rem_finger_x_sig, mode="lines", name=signal_name["Rem_finger_x"]))
            fig.add_trace(go.Scatter(x=time_signal, y=rem_finger_y_sig, mode="lines", name=signal_name["Rem_finger_y"]))
            fig.add_trace(go.Scatter(x=time_signal, y=hold_request_sig, mode="lines", name=signal_name["Hold_request"]))
            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        # Add the data in the table from Functional Test Filter Results
        additional_results_dict = {"Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)}}

        for plot in plots:
            if isinstance(plot, go.Figure):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="Maneuvering State Dead Man Switch Safe State Check",
    description="The system shall go to a safe state if the dead man switch is not pressed for a period longer than [tpress] after entering the maneuvering state.",
)
class ManeuveringStateSafeTest(TestCase):
    """ManeuveringStateSafeTest Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            ManeuveringStateSafeCheck,
        ]
