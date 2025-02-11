"""Remote Control, Inform driver about interruption on Remote Device. Dead Man's Switch released"""

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

SIGNAL_DATA = "RC_INFORM_DRIVER_ON_REM_DEV_DMS_RELEASED"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        ABS_STATE = "ABS_state"
        FINGER_POS_X = "Finger_x"
        FINGER_POS_Y = "Finger_y"
        REM_GENERAL_SCREEN = "Rem_screen"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.FINGER_POS_X: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutRemFingerPosX",
            self.Columns.FINGER_POS_Y: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutRemFingerPosY",
            self.Columns.REM_GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral2.APHMIGeneralScreenRemote",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Inform the driver about interrupted RC maneuver via Remote Device. AVG interrupted because Dead Man's Switch is released. ",
    description="Check information on Remote Device ",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class CommonRcAvgIntCheck(TestStep):
    """CommonRcAvgIntCheck Test Step."""

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
        finger_x_sig = read_data["Finger_x"].tolist()
        finger_y_sig = read_data["Finger_y"].tolist()
        rem_screem_sig = read_data["Rem_screen"].tolist()

        t_begining_rc_idx = None
        t_dm_released_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Rem_screen']} signal is PASSED, state of signal is MANEUVER_INTERRUPTED ({constants.HilCl.Hmi.APHMIGeneralScreenRemote.MANEUVER_INTERRUPTED}) after Dead Man's Switch set to released.".split()
        )

        """Evaluation part"""
        # Find begining of RC maneuver
        for cnt, item in enumerate(state_on_hmi_sig):
            if item == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_begining_rc_idx = cnt
                break

        if t_begining_rc_idx is not None:

            # Find when Dead Man's Switch set to released
            for cnt in range(t_begining_rc_idx, len(finger_x_sig)):
                if finger_x_sig[cnt] == 0 and finger_y_sig[cnt] == 0:
                    t_dm_released_idx = cnt
                    break

            if t_dm_released_idx is not None:
                # Check message on remote device
                eval_cond = [True] * 1
                counter = 0

                # Collect states of remote device screen after event
                states_dict = HilClFuntions.States(rem_screem_sig, t_begining_rc_idx, len(rem_screem_sig), 1)

                # Keys contains the idx
                for key in states_dict:
                    if counter == 1:
                        actual_value = constants.HilCl.Hmi.APHMIGeneralScreenRemote.DICT_REM_SCREEN.get(
                            states_dict[key]
                        )
                        actual_number = int(states_dict[key])

                        if key < t_dm_released_idx:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Rem_screen']} signal is FAILED, signal switches to {actual_value} ({actual_number}) at {time_signal[key]} us"
                                f" before Dead Man' Switch set to released ({time_signal[t_dm_released_idx]} us).".split()
                            )
                            eval_cond[0] = False
                            break

                        if states_dict[key] != constants.HilCl.Hmi.APHMIGeneralScreenRemote.MANEUVER_INTERRUPTED:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Rem_screen']} signal is FAILED, state of signal is {actual_value} ({actual_number}) at {time_signal[key]} us"
                                f" but requiered mode is MANEUVER_INTERRUPTED ({constants.HilCl.Hmi.APHMIGeneralScreenRemote.MANEUVER_INTERRUPTED})".split()
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
                    f"The evaluation of {signal_name['Finger_x']} and {signal_name['Finger_y']} signals is FAILED, signals never switched to 0 after begining of RC maneuvering ({time_signal[t_begining_rc_idx]} us)."
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

        signal_summary["Required state change: RC Outside Parking Out to Init. Reason: Interrupt"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=finger_x_sig, mode="lines", name=signal_name["Finger_x"]))
            fig.add_trace(go.Scatter(x=time_signal, y=finger_x_sig, mode="lines", name=signal_name["Finger_y"]))
            fig.add_trace(go.Scatter(x=time_signal, y=rem_screem_sig, mode="lines", name=signal_name["Rem_screen"]))

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
    name="Inform the driver about interrupted AVG",
    description="When the AVG is interrupted or terminated during a remote maneuver or remote control, the function shall inform the driver by a visual warning on Remote Device.",
)
class CommonRcAvgInt(TestCase):
    """CommonRcAvgInt Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CommonRcAvgIntCheck,
        ]
