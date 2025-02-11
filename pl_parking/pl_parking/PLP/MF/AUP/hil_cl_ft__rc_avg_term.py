"""Remote Control, Inform driver about terminate on Remote Device. Lost connection with Remote Device"""

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

SIGNAL_DATA = "RC_MAN_TERM_LSOT_REM_DEV"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        REM_GENERAL_MESSAGE = "Rem_general_message"
        HMI_INFO = "State_on_HMI"
        DEVICE_CONNECTION = "Rem_connected"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.REM_GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral2.APHMIGeneralMessageRemote",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.DEVICE_CONNECTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutBTDevConnected",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="System reaction on lost connection with Remote Device",
    description="Check system reaction on lost connecteion with Remote Device during RC Maneuvering",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class CommonRcManTermCheck(TestStep):
    """CommonRcManTermCheck Test Step."""

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
        rem_message_sig = read_data["Rem_general_message"].tolist()
        device_connected_sig = read_data["Rem_connected"].tolist()

        t_maneuvering_idx = None
        t_lost_conn_idx = None

        evaluation1 = " "

        """Evaluation part"""
        # Find begining of Maneuvering
        for cnt, item in enumerate(state_on_hmi_sig):
            if item == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_maneuvering_idx = cnt
                break

        if t_maneuvering_idx is not None:

            # Find lost connection
            for cnt in range(t_maneuvering_idx, len(device_connected_sig)):
                if device_connected_sig[cnt] == constants.HilCl.Hmi.BTDevConnected.FALSE:
                    t_lost_conn_idx = cnt
                    break

            if t_lost_conn_idx is not None:

                # Check signal states
                eval_cond = [True] * 1
                counter = 0

                # Collect states of signal
                states_dict = HilClFuntions.States(rem_message_sig, t_maneuvering_idx, len(rem_message_sig), 1)

                # Keys contains the idx
                for key in states_dict:
                    if counter == 1:
                        actual_value = constants.HilCl.Hmi.APHMIGeneralMessageRemote.DICT_REM_MESSAGE.get(
                            states_dict[key]
                        )

                        if key < t_lost_conn_idx:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Rem_general_message']} signal is FAILED, signal switches to {actual_value} at {time_signal[key]} us"
                                f" before connection set to FALSE ({constants.HilCl.Hmi.BTDevConnected.FALSE}).".split()
                            )
                            eval_cond[0] = False
                            break

                        if states_dict[key] != constants.HilCl.Hmi.APHMIGeneralMessageRemote.PARKING_FAILED:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Rem_general_message']} signal is FAILED, state of signal is {actual_value} at {time_signal[key]} us"
                                f" PARKING_FAILED ({constants.HilCl.Hmi.APHMIGeneralMessageRemote.PARKING_FAILED}).".split()
                            )
                            eval_cond[0] = False
                            break

                        else:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Rem_general_message']} signal is PASSED, state of signal is {actual_value} at {time_signal[key]} us"
                                f" and requiered mode is PARKING_FAILED ({constants.HilCl.Hmi.APHMIGeneralMessageRemote.PARKING_FAILED}).".split()
                            )
                            break
                    else:
                        counter += 1

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Rem_connected']} signal is FAILED, signal never switched to FALSE ({constants.HilCl.Hmi.BTDevConnected.FALSE})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})."
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

        signal_summary["Required state change: RC Maneuvering to Terminate."] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=rem_message_sig, mode="lines", name=signal_name["Rem_general_message"])
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=device_connected_sig, mode="lines", name=signal_name["Rem_connected"])
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
    name="Inform the driver about terminated AVG",
    description="When the AVG is interrupted or terminated during a remote maneuver or remote control, the function shall inform the driver by a visual warning on Remote Device.",
)
class CommonRcManTerm(TestCase):
    """CommonRcManTerm Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CommonRcManTermCheck,
        ]
