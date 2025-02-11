"""Driver interaction with the vehicle during RA, Provide a visual message requesting driver to release the brake pedal to start"""

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

SIGNAL_DATA = "RA_RELEASE_BRAKE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USEER_ACTION = "User_action"
        GENERAL_MESSAGE = "General_message"
        BRAKE = "Brake"
        DRIVING_DIR = "Driv_dir"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USEER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
            self.Columns.BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput06.BrakePressureDriver",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="RA reaction for not released brake",
    description="Check RA reaction if driver does not release the brake pedal after RA activation.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class CommonRaRelBrakeCheck(TestStep):
    """CommonRaRelBrakeCheck Test Step."""

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
        general_message_sig = read_data["General_message"].tolist()
        user_act_sig = read_data["User_action"].tolist()
        brake_sig = read_data["Brake"].tolist()
        driving_dir_sig = read_data["Driv_dir"].tolist()

        t1_idx = None
        t2_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['General_message']} signal is PASSED,"
            f" signal swithes to RELEASE_BRAKE ({constants.HilCl.Hmi.APHMIGeneralMessage.RELEASE_BRAKE})"
            f" after successful function activation by driver and driver is pressing brake pedal.".split()
        )

        """Evaluation part"""

        # Find when driver taps on start RA
        for cnt in range(0, len(user_act_sig)):
            if user_act_sig[cnt] == constants.HilCl.Hmi.Command.TAP_ON_REVERSE_ASSIST:
                t1_idx = cnt
                break

        if t1_idx is not None:
            # Find when vehicle start in backward mode
            for cnt in range(t1_idx, len(driving_dir_sig)):
                if driving_dir_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.DRIVING_BACKWARDS:
                    t2_idx = cnt
                    break

            if t2_idx is not None:

                eval_cond = [True] * 1
                message_available = False

                for cnt in range(t1_idx, t2_idx):
                    if general_message_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralMessage.RELEASE_BRAKE:
                        message_available = True
                        break

                if message_available is not True:
                    eval_cond[0] = False
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['General_message']} signal is FAILED,"
                        f" signal does not switch to RELEASE_BRAKE ({constants.HilCl.Hmi.APHMIGeneralMessage.RELEASE_BRAKE})"
                        " after successful function activation by driver and driver is pressing brake pedal.".split()
                    )

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Driv_dir']} signal is FAILED,"
                    f" signal never switched to DRIVING_BACKWARDS ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.DRIVING_BACKWARDS})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['User_action']} signal is FAILED,"
                f" signal never switched to TAP_ON_REVERSE_ASSIST ({constants.HilCl.Hmi.Command.TAP_ON_REVERSE_ASSIST})."
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
            "Required RA state change: Precondition Mode to Automated Reversinge. Reason: Ego vehicle is in standstill"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=time_signal, y=general_message_sig, mode="lines", name=signal_name["General_message"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
            fig.add_trace(go.Scatter(x=time_signal, y=brake_sig, mode="lines", name=signal_name["Brake"] + " [bar]"))
            fig.add_trace(go.Scatter(x=time_signal, y=driving_dir_sig, mode="lines", name=signal_name["Driv_dir"]))

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
    name="Driver interaction with the vehicle during RA, Provide a visual message requesting driver to release the brake pedal to start",
    description="After successful function activation by driver and driver is pressing brake pedal, the function shall provide a visual message requesting driver to release the brake pedal to start automated maneuver.",
)
class CommonRaRelBrake(TestCase):
    """CommonRaRelBrake Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CommonRaRelBrakeCheck,
        ]
