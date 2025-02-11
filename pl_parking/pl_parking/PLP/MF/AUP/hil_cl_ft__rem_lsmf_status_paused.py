"""The remote controller HMI shall display remote controlled LSMF status information to the driver: active (paused)"""

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

SIGNAL_DATA = "LSMF_REM_INFO_PAUSED"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        REM_DEVICE_CONNECTED = "Rem_device_connected"
        REM_DEVICE_PAIRED = "Rem_device_paired"
        REM_GENERAL_SCREEN = "Rem_general_screen"
        REM_USER_ACT = "Rem_user_action"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.REM_DEVICE_CONNECTED: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutBTDevConnected",
            self.Columns.REM_DEVICE_PAIRED: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutBTDevPaired",
            self.Columns.REM_GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral2.APHMIGeneralScreenRemote",
            self.Columns.REM_USER_ACT: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionRem",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Information about actual remote controlled LSMF state (paused) on remmote HMI",
    description="Check information on remote HMI about actual state of remote controlled LSMF.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class RemLsmfStatPausedCheck(TestStep):
    """RemLsmfStatPausedCheck Test Step."""

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
        rem_device_con_sig = read_data["Rem_device_connected"].tolist()
        rem_device_paired_sig = read_data["Rem_device_paired"].tolist()
        rem_gen_screen_sig = read_data["Rem_general_screen"].tolist()
        rem_user_act_sig = read_data["Rem_user_action"].tolist()

        t_device_ready_idx = None
        t_maneuvering_idx = None
        t_interrupt_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Rem_general_screen']} signal is PASSED, signal shows MANEUVER_INTERRUPTED"
            f" ({constants.HilCl.Hmi.APHMIGeneralScreenRemote.MANEUVER_INTERRUPTED}) after driver sent TAP_ON_INTERRUPT"
            f" ({constants.HilCl.Hmi.RemoteCommands.TAP_ON_INTERRUPT}).".split()
        )

        """Evaluation part"""
        # Find when device is connected and paired
        for cnt in range(0, len(rem_device_con_sig)):
            if (
                rem_device_con_sig[cnt] == constants.HilCl.Hmi.BTDevConnected.TRUE
                and rem_device_paired_sig[cnt] == constants.HilCl.Hmi.BTDevPaired.TRUE
            ):
                t_device_ready_idx = cnt
                break
        if t_device_ready_idx is not None:
            # Find begining of maneuvering
            for cnt in range(t_device_ready_idx, len(rem_gen_screen_sig)):
                if rem_gen_screen_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralScreenRemote.MANEUVER_ACTIVE:
                    t_maneuvering_idx = cnt
                    break

            if t_maneuvering_idx is not None:

                # Find interrupt command from driver
                for cnt in range(t_maneuvering_idx, len(rem_user_act_sig)):
                    if rem_user_act_sig[cnt] == constants.HilCl.Hmi.RemoteCommands.TAP_ON_INTERRUPT:
                        t_interrupt_idx = cnt
                        break

                if t_interrupt_idx is not None:

                    # Check signal states
                    eval_cond = [True] * 1
                    counter = 0

                    # Collect states of AP after switch to Maneuvering event
                    states_dict = HilClFuntions.States(
                        rem_gen_screen_sig, t_maneuvering_idx, len(rem_gen_screen_sig), 1
                    )

                    # Keys contains the idx
                    for key in states_dict:
                        if counter == 1:
                            actual_value = constants.HilCl.Hmi.APHMIGeneralScreenRemote.DICT_REM_SCREEN.get(
                                states_dict[key]
                            )
                            actual_number = int(states_dict[key])

                            if key < t_interrupt_idx:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['Rem_general_screen']} signal is FAILED, signal switches to {actual_value} ({actual_number}) at {time_signal[key]} us"
                                    f" before TAP_ON_INTERRUPT ({constants.HilCl.Hmi.RemoteCommands.TAP_ON_INTERRUPT}) sent via remote device event.".split()
                                )
                                eval_cond[0] = False
                                break

                            if states_dict[key] != constants.HilCl.Hmi.APHMIGeneralScreenRemote.MANEUVER_INTERRUPTED:
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['Rem_general_screen']} signal is FAILED, state of signal is {actual_value} ({actual_number}) at {time_signal[key]} us"
                                    f" but requiered mode is MANEUVER_INTERRUPTED ({constants.HilCl.Hmi.APHMIGeneralScreenRemote.MANEUVER_INTERRUPTED}).".split()
                                )
                                eval_cond[0] = False
                                break
                            counter += 1

                        else:
                            counter += 1

                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Rem_user_action']} signal is FAILED."
                        f" Signal never switched to TAP_ON_INTERRUPT ({constants.HilCl.Hmi.RemoteCommands.TAP_ON_INTERRUPT})."
                        " Maneuver was never interrupted by driver via remote device."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Rem_general_screen']} signal is FAILED."
                    f" Signal never switched to MANEUVER_ACTIVE ({constants.HilCl.Hmi.APHMIGeneralScreenRemote.MANEUVER_ACTIVE})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Rem_device_connected']} signal and {signal_name['Rem_device_paired']} signal is FAILED."
                f" There was no time point when {signal_name['Rem_device_connected']} and {signal_name['Rem_device_paired']} when TRUE"
                f" ({constants.HilCl.Hmi.BTDevPaired.TRUE}) in the same time."
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

        signal_summary["Remote HMI shall show paused state of LSMF"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(x=time_signal, y=rem_device_con_sig, mode="lines", name=signal_name["Rem_device_connected"])
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=rem_device_paired_sig, mode="lines", name=signal_name["Rem_device_paired"])
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=rem_gen_screen_sig, mode="lines", name=signal_name["Rem_general_screen"])
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=rem_user_act_sig, mode="lines", name=signal_name["Rem_user_action"])
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
    name="Remote controlled LSMF status state on remoted HMI, Paused",
    description="The remote controller HMI shall display remote controlled LSMF status information to the driver: active (paused)",
)
class RemLsmfStatPaused(TestCase):
    """RemLsmfStatPaused Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            RemLsmfStatPausedCheck,
        ]
