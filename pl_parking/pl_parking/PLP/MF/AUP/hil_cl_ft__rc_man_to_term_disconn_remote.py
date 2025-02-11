"""RC Maneuvering to Terminate, Disconnected remote device"""

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

SIGNAL_DATA = "RC_MAN_TO_TERM_DISC_REM_DEVICE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        REM_DEVICE_CONNECTED = "Rem_device_connected"
        REM_GENERAL_MESSAGE = "Rem_general_message"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.REM_DEVICE_CONNECTED: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutBTDevConnected",
            self.Columns.REM_GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral2.APHMIGeneralMessageRemote",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="System reaction on lost connection with remote device in case of maneuvering mode",
    description="Check system reaction if connection between remote device and ego vehicle lost during active parking maneuver",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class CommonRcManTermDisconnCheck(TestStep):
    """CommonRcManTermDisconnCheck Test Step."""

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
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()
        rem_device_con_sig = read_data["Rem_device_connected"].tolist()
        rem_gen_message_sig = read_data["Rem_general_message"].tolist()

        t_maneuvering_start_idx = None
        t_device_connected_idx = None
        t_device_disconnected_idx = None
        t_failed_msg_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Rem_general_message']} signal is PASSED, signal switches to PARKING_FAILED ({constants.HilCl.Hmi.APHMIGeneralMessageRemote.PARKING_FAILED}) if the remote device"
            f" is disconnected from the ego vehicle for longer than {constants.HilCl.ApThreshold.AP_G_MAX_TIME_REM_DISCONNECT_S} second(s).".split()
        )

        """Evaluation part"""
        # Find when remote device set to connected
        for cnt, item in enumerate(rem_device_con_sig):
            if item == constants.HilCl.Hmi.BTDevConnected.TRUE:
                t_device_connected_idx = cnt
                break

        if t_device_connected_idx is not None:

            # Find  Maneuvering
            for cnt in range(t_device_connected_idx, len(state_on_hmi_sig)):
                if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                    t_maneuvering_start_idx = cnt
                    break

            if t_maneuvering_start_idx is not None:
                # Find disconnect event
                for cnt in range(t_maneuvering_start_idx, len(rem_device_con_sig)):
                    if rem_device_con_sig[cnt] == constants.HilCl.Hmi.BTDevConnected.FALSE:
                        t_device_disconnected_idx = cnt
                        break

                if t_device_disconnected_idx is not None:
                    # Find when rem hmi shows PARKING_FAILED
                    for cnt in range(t_device_disconnected_idx, len(rem_gen_message_sig)):
                        if rem_gen_message_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralMessageRemote.PARKING_FAILED:
                            t_failed_msg_idx = cnt
                            break

                    if t_failed_msg_idx is not None:

                        eval_cond = [True] * 1

                        delta = time_signal[t_failed_msg_idx] - time_signal[t_device_disconnected_idx]  # [us]

                        if delta < constants.HilCl.ApThreshold.AP_G_MAX_TIME_REM_DISCONNECT_S * 1e6:
                            eval_cond[0] = False
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Rem_general_message']} signal is FAILED, signal switched"
                                f" to PARKING_FAILED ({constants.HilCl.Hmi.APHMIGeneralMessageRemote.PARKING_FAILED}) at {time_signal[t_failed_msg_idx]} us after remote device disconnected event ({time_signal[t_device_disconnected_idx]} us)."
                                f" Time gap between error mesage and issue injection is {round(delta * 1e-6, 4)} secnod(s) but system shall switch from RC Maneuvering to Terminate if the remote device"
                                f" is disconnected from the ego vehicle for longer than {constants.HilCl.ApThreshold.AP_G_MAX_TIME_REM_DISCONNECT_S} second(s)".split()
                            )

                    else:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Rem_general_message']} signal is FAILED, signal never switched"
                            f" to PARKING_FAILED ({constants.HilCl.Hmi.APHMIGeneralMessageRemote.PARKING_FAILED}) after remote device disconnected event.".split()
                        )

                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Rem_device_connected']} signal is FAILED, signal never switched to FALSE ({constants.HilCl.Hmi.BTDevConnected.FALSE}) after PPC_PERFORM_PARKING event."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Rem_device_connected']} signal is FAILED, signal never switched to TRUE ({constants.HilCl.Hmi.BTDevConnected.TRUE})."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
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
            f"Required state change: RC Maneuvering to Terminate, Reason: Disconnected remote device for longer than {constants.HilCl.ApThreshold.AP_G_MAX_TIME_REM_DISCONNECT_S} second(s)"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=rem_device_con_sig, mode="lines", name=signal_name["Rem_device_connected"])
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=rem_gen_message_sig, mode="lines", name=signal_name["Rem_general_message"])
            )

            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        """Calculate parameters to additional table"""

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
    name="RC Maneuvering to Terminate, Disconnected remote device",
    description=f"The system shall switch from RC Maneuvering to Terminate if the remote device"
    f" is disconnected from the ego vehicle for longer than {constants.HilCl.ApThreshold.AP_G_MAX_TIME_REM_DISCONNECT_S} second(s).",
)
class CommonRcManTermDisconn(TestCase):
    """SotifStanstillTime Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CommonRcManTermDisconnCheck,
        ]
