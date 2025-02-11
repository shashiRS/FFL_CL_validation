"""Reverse Assist, Automated reversing to terminate gear shifted to N, P or D"""

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

SIGNAL_DATA = "RA_AUT_TERM_GEAR"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        GENERAL_MESSAGE = "Gen_message"
        GENERAL_SCREEN = "Gen_screen"
        ACTUAL_GEAR = "Actual_gear"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
            self.Columns.GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
            self.Columns.ACTUAL_GEAR: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActualGear",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Sysrem reaction in case of shift to N, P or D",
    description="Check mode transition if gear is switched to N, p or D during automated reversing.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class RaAutToTermGearCheck(TestStep):
    """RaAutToTermGearCheck Test Step."""

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
        gen_screen_sig = read_data["Gen_screen"].tolist()
        act_gear_sig = read_data["Actual_gear"].tolist()

        t_ra_start_idx = None
        t_gear_n_idx = None
        t_gear_p_idx = None
        t_gear_d_idx = None
        t_shift_idx = None
        gear_number = None
        gear_text = None

        evaluation1 = ""

        """Evaluation part"""
        # Find begining of RA
        for cnt, item in enumerate(gen_screen_sig):
            if item == constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                t_ra_start_idx = cnt
                break

        if t_ra_start_idx is not None:

            # Calculate a time window according Test Case Design to avoid no needed gear shifts
            tmp = time_signal[t_ra_start_idx] + 2 * 1e6
            end_of_t_window = min(time_signal, key=lambda x: abs(x - tmp))
            end_of_t_window_idx = list(time_signal).index(end_of_t_window)

            # Find gear shift
            for cnt in range(t_ra_start_idx, end_of_t_window_idx + 1):
                if act_gear_sig[cnt] == constants.HilCl.VehCanActualGear.NEUTRAL_ACTUALGEAR:
                    t_gear_n_idx = cnt
                    break
                if act_gear_sig[cnt] == constants.HilCl.VehCanActualGear.PARK_ACTUALGEAR:
                    t_gear_p_idx = cnt
                    break
                if act_gear_sig[cnt] == constants.HilCl.VehCanActualGear.POWER_FREE_ACTUALGEAR:
                    t_gear_d_idx = cnt
                    break

            # Check which gear was reached
            if t_gear_n_idx is None and t_gear_p_idx is None and t_gear_d_idx is None:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Actual_gear']} signal is FAILED, signal didn't switch to"
                    f" NEUTRAL_ACTUALGEAR ({constants.HilCl.VehCanActualGear.NEUTRAL_ACTUALGEAR})"
                    f" or PARK_ACTUALGEAR ({constants.HilCl.VehCanActualGear.PARK_ACTUALGEAR})"
                    f" or POWER_FREE_ACTUALGEAR ({constants.HilCl.VehCanActualGear.POWER_FREE_ACTUALGEAR}) during Automated reversing mode."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )
            else:

                if t_gear_n_idx is not None:
                    t_shift_idx = t_gear_n_idx
                    gear_number = constants.HilCl.VehCanActualGear.NEUTRAL_ACTUALGEAR
                    gear_text = constants.HilCl.VehCanActualGear.DICT_ACTUAL_GEAR.get(
                        constants.HilCl.VehCanActualGear.NEUTRAL_ACTUALGEAR
                    )
                elif t_gear_p_idx is not None:
                    t_shift_idx = t_gear_p_idx
                    gear_number = constants.HilCl.VehCanActualGear.PARK_ACTUALGEAR
                    gear_text = constants.HilCl.VehCanActualGear.DICT_ACTUAL_GEAR.get(
                        constants.HilCl.VehCanActualGear.PARK_ACTUALGEAR
                    )
                elif t_gear_d_idx is not None:
                    t_shift_idx = t_gear_d_idx
                    gear_number = constants.HilCl.VehCanActualGear.POWER_FREE_ACTUALGEAR
                    gear_text = constants.HilCl.VehCanActualGear.DICT_ACTUAL_GEAR.get(
                        constants.HilCl.VehCanActualGear.POWER_FREE_ACTUALGEAR
                    )

                eval_cond = [True] * 1

                states_dict = HilClFuntions.States(gen_message_sig, t_ra_start_idx, len(gen_message_sig), 1)

                counter = 0

                # Keys contains the idx
                for key in states_dict:
                    if counter == 1:
                        actual_value = constants.HilCl.Hmi.APHMIGeneralMessage.DICT_MESSAGE.get(states_dict[key])

                        actual_number = int(states_dict[key])

                        if key < t_shift_idx:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Gen_message']} signal is FAILED, signal switches into {actual_value} ({actual_number}) at {time_signal[key]} us"
                                f" before gear shifted to {gear_text} ({gear_number}) at {time_signal[t_shift_idx]} us".split()
                            )
                            eval_cond[0] = False
                            break

                        if states_dict[key] != constants.HilCl.Hmi.APHMIGeneralMessage.REVERSE_ASSIST_FAILED:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Gen_message']} signal is FAILED, signal switches to {actual_value} ({actual_number}) state"
                                f" after driver shifted gear to {gear_text} ({gear_number}) at {time_signal[t_shift_idx]} us."
                                f" Required state is REVERSE_ASSIST_FAILED ({constants.HilCl.Hmi.APHMIGeneralMessage.REVERSE_ASSIST_FAILED})".split()
                            )
                            eval_cond[0] = False
                            break

                        else:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Gen_message']} signal is PASSED, signal switches to {actual_value} ({actual_number}) state"
                                f" after driver shifted gear to {gear_text} ({gear_number}) at {time_signal[t_shift_idx]} us.".split()
                            )
                            break

                    else:
                        counter += 1

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Gen_screen']} signal is FAILED, signal never switched to"
                f" REVERSE_ASSIST ({constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST})."
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

        signal_summary["RA Mode Transition, Automated reversing to Terminate.<br>Reason: Gear is shifted by drive"] = (
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
            fig.add_trace(go.Scatter(x=time_signal, y=gen_screen_sig, mode="lines", name=signal_name["Gen_screen"]))
            fig.add_trace(go.Scatter(x=time_signal, y=act_gear_sig, mode="lines", name=signal_name["Actual_gear"]))

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
    name="RA Mode transition, Automated reversing to Terminate, Gear is shifted by drive",
    description="The RA function shall transit from Automated Reversing to Terminate if the driver switches the gear to N, P or D",
)
class RaAutToTermGear(TestCase):
    """RaAutToTermGear Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            RaAutToTermGearCheck,
        ]
