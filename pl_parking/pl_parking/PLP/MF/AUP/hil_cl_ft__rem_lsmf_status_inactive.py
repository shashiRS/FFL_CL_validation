"""The remote controller HMI shall display remote controlled LSMF status information to the driver: inactive"""

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

SIGNAL_DATA = "LSMF_REM_INFO_INACTIVE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        REM_DEVICE_CONNECTED = "Rem_device_connected"
        REM_DEVICE_PAIRED = "Rem_device_paired"
        REM_GENERAL_SCREEN = "Rem_general_screen"
        IGNITION = "Ignition"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.REM_DEVICE_CONNECTED: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutBTDevConnected",
            self.Columns.REM_DEVICE_PAIRED: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutBTDevPaired",
            self.Columns.REM_GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral2.APHMIGeneralScreenRemote",
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Information about actual remote controlled LSMF state (inactive) on remmote HMI",
    description="Check information on remote HMI about actual state of remote controlled LSMF.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class RemLsmfStatInactiveCheck(TestStep):
    """RemLsmfStatInactiveCheck Test Step."""

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
        ignition_sig = read_data["Ignition"].tolist()

        t_ignition_on_idx = None
        t_device_ready_idx = None
        t_ignition_off_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Rem_general_screen']} signal is PASSED, signal shows SYSTEM_NOT_ACTIVE"
            f" ({constants.HilCl.Hmi.APHMIGeneralScreenRemote.SYSTEM_NOT_ACTIVE}) when system is not activated by driver.".split()
        )

        """Evaluation part"""
        # Find the ignition on
        for cnt in range(0, len(ignition_sig)):
            if ignition_sig[cnt] == constants.HilCl.CarMaker.IGNITION_ON:
                t_ignition_on_idx = cnt
                break

        if t_ignition_on_idx is not None:
            # find ignition off
            for cnt in range(t_ignition_on_idx, len(ignition_sig)):
                if ignition_sig[cnt] == constants.HilCl.CarMaker.IGNITION_OFF:
                    t_ignition_off_idx = cnt
                    break

            if t_ignition_off_idx is not None:
                # Find when device is connected and paired
                for cnt in range(0, len(rem_device_con_sig)):
                    if (
                        rem_device_con_sig[cnt] == constants.HilCl.Hmi.BTDevConnected.TRUE
                        and rem_device_paired_sig[cnt] == constants.HilCl.Hmi.BTDevPaired.TRUE
                    ):
                        t_device_ready_idx = cnt
                        break

                if t_device_ready_idx is not None:
                    eval_cond = [True] * 1

                    # Check info from remote device HMI
                    for cnt in range(t_device_ready_idx, t_ignition_off_idx + 1):
                        if rem_gen_screen_sig[cnt] != constants.HilCl.Hmi.APHMIGeneralScreenRemote.SYSTEM_NOT_ACTIVE:
                            actual_value = constants.HilCl.Hmi.APHMIGeneralScreenRemote.DICT_REM_SCREEN.get(
                                rem_gen_screen_sig[cnt]
                            )
                            actual_number = rem_gen_screen_sig[cnt]

                            eval_cond[0] = False
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Rem_general_screen']} signal is FAILED, state of signal is {actual_value} ({actual_number}) at {time_signal[cnt]} us"
                                f" but requiered mode is SYSTEM_NOT_ACTIVE ({constants.HilCl.Hmi.APHMIGeneralScreenRemote.SYSTEM_NOT_ACTIVE}).".split()
                            )

                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Rem_device_connected']} signal and {signal_name['Rem_device_paired']} signal is FAILED."
                        f" There was no time point when {signal_name['Rem_device_connected']} and {signal_name['Rem_device_paired']} where TRUE"
                        f" ({constants.HilCl.Hmi.BTDevPaired.TRUE}) in the same time."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Ignition']} signal is FAILED."
                    f" Signal never switched to IGNITION_OFF ({constants.HilCl.CarMaker.IGNITION_OFF})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Ignition']} signal is FAILED."
                f" Signal never switched to IGNITION_ON ({constants.HilCl.CarMaker.IGNITION_ON})."
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

        signal_summary["Remote HMI shall show inactive state of LSMF"] = evaluation1

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
            fig.add_trace(go.Scatter(x=time_signal, y=ignition_sig, mode="lines", name=signal_name["Ignition"]))

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
    name="Remote controlled LSMF status state on remoted HMI, Inactive",
    description="The remote controller HMI shall display remote controlled LSMF status information to the driver: inactive",
)
class RemLsmfStatInactive(TestCase):
    """RemLsmfStatInactive Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            RemLsmfStatInactiveCheck,
        ]
