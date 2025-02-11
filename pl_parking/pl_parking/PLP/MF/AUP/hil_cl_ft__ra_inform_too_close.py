"""Driver interaction with the vehicle during RA, Inform about interruption"""

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

SIGNAL_DATA = "RA_INT_INFO"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        GENERAL_SCREEN = "General_screen"
        GENERAL_MESSAGE = "General_message"
        TONE_INFO_REAR_PITCH = "Tone_info_rear_pitch"
        TONE_INFO_REAR_VOLUME = "Tone_info_rear_volume"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
            self.Columns.TONE_INFO_REAR_PITCH: "MTS.AP_Private_CAN.AP_Private_CAN.TONHInfo.RearSpeakerPitch",
            self.Columns.TONE_INFO_REAR_VOLUME: "MTS.AP_Private_CAN.AP_Private_CAN.TONHInfo.RearSpeakerVolume",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Provide information check",
    description="Check provided information about interruption by system",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class CommonRaIntInformCheck(TestStep):
    """CommonRaIntInformCheck Test Step."""

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
        general_scrren_sig = read_data["General_screen"].tolist()
        general_message_sig = read_data["General_message"].tolist()
        tone_rear_pitch_sig = read_data["Tone_info_rear_pitch"].tolist()
        tone_rear_volume_sig = read_data["Tone_info_rear_volume"].tolist()

        t1_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['General_message']} and {signal_name['Tone_info_rear_pitch']} signals are PASSED, HMI sent acoustically and visually information."
            f" {signal_name['General_message']} signal switches VERY_CLOSE_TO_OBJECTS ({constants.HilCl.Hmi.APHMIGeneralMessage.VERY_CLOSE_TO_OBJECTS}),"
            f" value of {signal_name['Tone_info_rear_pitch']} and {signal_name['Tone_info_rear_volume']} signals are greater than 0 in the same time. ".split()
        )

        """Evaluation part"""

        # Find when RA active
        for cnt in range(0, len(general_scrren_sig)):
            if general_scrren_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                t1_idx = cnt
                break

        if t1_idx is not None:
            eval_cond = [True] * 1

            visually_info = False
            acoustically_info = False

            # Check warning infos

            # visually_info
            for cnt in range(t1_idx, len(general_message_sig)):
                if general_message_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralMessage.VERY_CLOSE_TO_OBJECTS:
                    visually_info = True
                    break

            # acoustically_info
            for cnt in range(t1_idx, len(tone_rear_pitch_sig)):
                if tone_rear_pitch_sig[cnt] > 0 and tone_rear_volume_sig[cnt] > 0:
                    acoustically_info = True
                    break

            if visually_info is not True and acoustically_info is True:
                eval_cond[0] = False
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['General_message']} signal is FAILED,"
                    f" signal never switched to VERY_CLOSE_TO_OBJECTS ({constants.HilCl.Hmi.APHMIGeneralMessage.VERY_CLOSE_TO_OBJECTS})."
                    f" Visually information not presented to driver.".split()
                )

            if visually_info is True and acoustically_info is not True:
                eval_cond[0] = False
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Tone_info_rear_pitch']} and {signal_name['Tone_info_rear_volume']} signals are FAILED,"
                    f" value of signals never greater than 0 in the same time."
                    f" Acoustically information not presented to driver.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['General_screen']} signal is FAILED,"
                f" signal never switched to REVERSE_ASSIST ({constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST})."
                f" It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
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
            "In case of interruption, function shall inform driver about the reason for the interruption on HMI acoustically and visually"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=time_signal, y=general_scrren_sig, mode="lines", name=signal_name["General_screen"])
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=general_message_sig, mode="lines", name=signal_name["General_message"])
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=tone_rear_pitch_sig, mode="lines", name=signal_name["Tone_info_rear_pitch"])
            )
            fig.add_trace(
                go.Scatter(
                    x=time_signal, y=tone_rear_volume_sig, mode="lines", name=signal_name["Tone_info_rear_volume"]
                )
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
    name="Driver interaction with the vehicle during RA, Inform about interruption",
    description="In case the function brakes the ego vehicle to a standstill due to the interruption of the AVG,"
    " a warning shall be provided to the driver about the reason for the interruption on HMI acoustically and visually.",
)
class CommonRaIntInform(TestCase):
    """CommonRaIntInform Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CommonRaIntInformCheck,
        ]
