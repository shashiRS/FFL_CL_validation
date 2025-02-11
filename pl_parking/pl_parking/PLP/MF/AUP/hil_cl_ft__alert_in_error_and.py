"""The HMI shall provide a visual and sound alert to the driver in case of error mode"""

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

SIGNAL_DATA = "LSMF_SOUND_VISUAL_ALERT_AND"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        GENERAL_MESSAGE = "Gen_message"
        ISSUE_INDICATOR = "Issue_indicator"
        FRONT_SPEAKER_PITCH = "Front_pitch"
        FRONT_SPEAKER_VOLUME = "Front_Volume"
        REAR_SPEAKER_PITCH = "Rear_pitch"
        REAR_SPEAKER_VOLUME = "Rear_Volume"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
            self.Columns.ISSUE_INDICATOR: "CM.vCUS.FTi.Sensor[1].Pdcm.E2E.FrameTimeout",
            self.Columns.FRONT_SPEAKER_PITCH: "MTS.AP_Private_CAN.AP_Private_CAN.TONHInfo.FrontSpeakerPitch",
            self.Columns.FRONT_SPEAKER_VOLUME: "MTS.AP_Private_CAN.AP_Private_CAN.TONHInfo.FrontSpeakerVolume",
            self.Columns.REAR_SPEAKER_PITCH: "MTS.AP_Private_CAN.AP_Private_CAN.TONHInfo.RearSpeakerPitch",
            self.Columns.REAR_SPEAKER_VOLUME: "MTS.AP_Private_CAN.AP_Private_CAN.TONHInfo.RearSpeakerVolume",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Provided alert(s) in case of error. Relation between alert(s): AND",
    description="Check provided alert(s) when error appears.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class SotifDrivAlertAndCheck(TestStep):
    """SotifDrivAlertAndCheck Test Step."""

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

        gen_message_sig = read_data["Gen_message"].tolist()
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()
        issue_state_sig = read_data["Issue_indicator"].tolist()
        front_pitch_sig = read_data["Front_pitch"].tolist()
        front_volume_sig = read_data["Front_Volume"].tolist()
        rear_pitch_sig = read_data["Rear_pitch"].tolist()
        rear_volume_sig = read_data["Rear_Volume"].tolist()

        t_maneuvering_idx = None
        t_issue_injection_idx = None
        t_issue_remove_idx = None

        visual_alert_detected = False
        sound_alert_detected = False

        evaluation1 = ""

        """Evaluation part"""
        # Find begining of maneuvering
        for cnt, item in enumerate(state_on_hmi_sig):
            if item == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_maneuvering_idx = cnt
                break

        if t_maneuvering_idx is not None:

            # Find issue injection
            for cnt in range(t_maneuvering_idx, len(issue_state_sig)):
                if issue_state_sig[cnt] == constants.HilCl.CarMaker.UssError.TIMEOUT_ENABLED:
                    t_issue_injection_idx = cnt
                    break

            if t_issue_injection_idx is not None:

                # Find when issue is removed
                for cnt in range(t_issue_injection_idx, len(issue_state_sig)):
                    if issue_state_sig[cnt] == constants.HilCl.CarMaker.UssError.TIMEOUT_DISABLED:
                        t_issue_remove_idx = cnt
                        break

                if t_issue_remove_idx is not None:

                    # Visual alert check
                    for cnt in range(t_issue_injection_idx, t_issue_remove_idx + 1):
                        if gen_message_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralMessage.INTERNAL_SYSTEM_ERROR:
                            visual_alert_detected = True
                            break

                    # Sound alert
                    for cnt in range(t_issue_injection_idx, t_issue_remove_idx + 1):
                        if (front_pitch_sig[cnt] > 0 and front_volume_sig[cnt] > 0) and (
                            rear_pitch_sig[cnt] > 0 and rear_volume_sig[cnt] > 0
                        ):
                            sound_alert_detected = True
                            break

                    if visual_alert_detected and sound_alert_detected:
                        eval_cond = [True] * 1

                        evaluation1 += " ".join(
                            "The evaluation is PASSED. HMI provides a visual and sound alert to the driver in case of error mode".split()
                        )

                    else:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            "The evaluation is FAILED. HMI don't provide a visual or sound alert to the driver in case of error mode".split()
                        )

                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Issue_indicator']} signal is FAILED, signal didn't switch to"
                        f" TIMEOUT_DISABLED ({constants.HilCl.CarMaker.UssError.TIMEOUT_DISABLED}) after TIMEOUT_ENABLED event ({time_signal[t_issue_injection_idx]} us)."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Issue_indicator']} signal is FAILED, signal never switched to"
                    f" TIMEOUT_ENABLED ({constants.HilCl.CarMaker.UssError.TIMEOUT_ENABLED})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to"
                f" PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})."
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

        signal_summary["The HMI shall provide a visual and sound alert to the driver in case of error mode"] = (
            evaluation1
        )

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=time_signal, y=gen_message_sig, mode="lines", name=signal_name["Gen_message"]))
            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=issue_state_sig, mode="lines", name=signal_name["Issue_indicator"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=front_pitch_sig, mode="lines", name=signal_name["Front_pitch"]))
            fig.add_trace(go.Scatter(x=time_signal, y=front_volume_sig, mode="lines", name=signal_name["Front_Volume"]))
            fig.add_trace(go.Scatter(x=time_signal, y=rear_pitch_sig, mode="lines", name=signal_name["Rear_pitch"]))
            fig.add_trace(go.Scatter(x=time_signal, y=rear_volume_sig, mode="lines", name=signal_name["Rear_Volume"]))

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
    name="Driver alert in case or error. Relation between alert(s): AND",
    description="The HMI shall provide a visual and sound alert to the driver in case of error mode",
)
class SotifDrivAlertAnd(TestCase):
    """SotifDrivAlertAnd Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SotifDrivAlertAndCheck,
        ]
