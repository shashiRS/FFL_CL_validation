"""AUP override"""

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

SIGNAL_DATA = "AUP_TO_LSCA_OVERRIDE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        LSCA_BRAKE = "Lsca_brake"
        USER_ACTION = "User_action"
        ROAD_POSITION = "Vhcl_sRoad"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.LSCA_BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCEmergencyHoldRequest",
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.ROAD_POSITION: "CM.Car.Road.sRoad",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="AUP to LSCA Override Check",
    description="Check if AUP triggers an override after LSCA intervention, allowing to drive a specified distance before reactivating LSCA.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupLscaOverrideCheck(TestStep):
    """AupLscaOverrideCheck Test Step."""

    custom_report = MfHilClCustomTeststepReport

    def __init__(self):
        """Initialize the test."""
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
        test_result = fc.INPUT_MISSING  # Initial result state
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        # Prepare signals
        time_signal = read_data.index
        hmi_state_sig = read_data["State_on_HMI"].tolist()
        lsca_brake_sig = read_data["Lsca_brake"].tolist()
        user_action_sig = read_data["User_action"].tolist()
        s_road_sig = read_data["Vhcl_sRoad"].tolist()

        t1_idx = None  # Maneuvering State (T1)
        t2_idx = None  # LSCA Brake ON (T2)
        t3_idx = None  # AUP Continue Button (T3)
        t4_idx = None  # AUP in Maneuvering State Again (T4)
        t5_idx = None  # Vehicle has moved 10 cm (T5)

        # T1: Find when AUP enters Maneuvering state
        for cnt, state in enumerate(hmi_state_sig):
            if state == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = cnt
                break

        if t1_idx is None:
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} is FAILED, AUP never entered the Maneuvering state {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}.".split()
            )
            test_result = fc.FAIL

        else:
            # T2: Find when LSCA brake is activated
            for cnt in range(t1_idx, len(lsca_brake_sig)):
                if lsca_brake_sig[cnt] == constants.HilCl.Lsca.BRAKE_REQUEST:
                    t2_idx = cnt
                    break

            if t2_idx is None:
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Lsca_brake']} is FAILED, LSCA brake request was never activated after AUP entered Maneuvering.".split()
                )
                test_result = fc.FAIL

            else:
                # T3: Find when driver taps the continue button
                for cnt in range(t2_idx, len(user_action_sig)):
                    if user_action_sig[cnt] == constants.HilCl.Hmi.Command.TAP_ON_CONTINUE:
                        t3_idx = cnt
                        break

                if t3_idx is None:
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['User_action']} is FAILED, driver did not tap the continue button on the HMI.".split()
                    )
                    test_result = fc.FAIL

                else:
                    # T4: Find when AUP re-enters Maneuvering state (after T3)
                    for cnt in range(t3_idx, len(hmi_state_sig)):
                        if hmi_state_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                            t4_idx = cnt
                            s_road_continue = s_road_sig[t4_idx]  # Save current road position
                            break

                    if t4_idx is None:
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} is FAILED, AUP did not re-enter Maneuvering state after continue button press."
                        )
                        test_result = fc.FAIL

                    else:
                        # T5: Monitor vehicle's road position and check when it exceeds the 10 cm threshold
                        for cnt in range(t4_idx, len(s_road_sig)):
                            if s_road_sig[cnt] >= (s_road_continue + 0.10):  # 10 cm
                                t5_idx = cnt
                                break

                        if t5_idx is None:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Vhcl_sRoad']} is FAILED, vehicle did not travel the required 10 cm distance.".split()
                            )
                            test_result = fc.FAIL

                        else:
                            # T6: Check the LSCA state at 0.01 seconds before T5 (T5 - 0.01s)
                            t6_idx = max(
                                0, t5_idx - int(0.01 * (time_signal[1] - time_signal[0]) * 1e6)
                            )  # Adjusted index for 0.01s before
                            if lsca_brake_sig[t6_idx] == constants.HilCl.Lsca.BRAKE_REQUEST:
                                test_result = fc.PASS
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['Lsca_brake']} is PASSED, LSCA braking functionality was reactivated correctly after 10 cm distance.".split()
                                )

                            else:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['Lsca_brake']} is FAILED, LSCA did not reactivate braking after the 10 cm distance.".split()
                                )
                                test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary = {"AUP to LSCA Override Evaluation": evaluation1}
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_header_left="Evaluation")
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if test_result == fc.FAIL:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=time_signal, y=hmi_state_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=lsca_brake_sig, mode="lines", name="Lsca_Brake"))
            fig.add_trace(go.Scatter(x=time_signal, y=s_road_sig, mode="lines", name="Vhcl_sRoad"))
            fig.add_trace(go.Scatter(x=time_signal, y=user_action_sig, mode="lines", name="User_action"))
            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

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
    name="AUP to LSCA Override",
    description="Check if AUP triggers an override after LSCA intervention and handles driving distance correctly.",
)
class AupLscaOverride(TestCase):
    """AupLscaOverride Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupLscaOverrideCheck,
        ]
