"""RC Getting Off to RC Maneuvering, Actuating a connected remote device"""

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

SIGNAL_DATA = "RC_GET_OFF_TO_MAN_DEAD"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        GENERAL_MESSAGE = "General_message"
        USER_ACTION = "User_action"
        HMI_INFO = "State_on_HMI"
        REM_FINGER_X = "Rem_finger_x"
        REM_FINGER_Y = "Rem_finger_y"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.REM_FINGER_X: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutRemFingerPosX",
            self.Columns.REM_FINGER_Y: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutRemFingerPosY",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Mode transition, RC Getting Off to RC Maneuvering",
    description="Check RC funtion state change if dead man's switch is pressed",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class CommonRcGetOffToRcManDeadCheck(TestStep):
    """CommonRcGetOffToRcManDeadCheck Test Step."""

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
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()
        rem_finger_x = read_data["Rem_finger_x"].tolist()
        rem_finger_y = read_data["Rem_finger_y"].tolist()

        t1_idx = None
        t2_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED, signal switches to"
            f" PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})"
            " when driver pressed Dead Man's Switch on Remote Device.".split()
        )

        """Evaluation part"""
        # Find when LEAVE_VEHICLE message appeares in APHMIGeneralMessage
        for idx, item in enumerate(general_message_sig):
            if item == constants.HilCl.Hmi.APHMIGeneralMessage.LEAVE_VEHICLE:
                t1_idx = idx
                break

        if t1_idx is not None:

            # Find when dead man's switche is pressed
            for cnt in range(0, len(time_signal)):
                if (
                    rem_finger_x[cnt] == constants.HilCl.Hmi.RemFingerPosition.DM_FINGER_POS_X
                    and rem_finger_y[cnt] == constants.HilCl.Hmi.RemFingerPosition.DM_FINGER_POS_Y
                ):
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                eval_cond = [True] * 1

                states_dict = HilClFuntions.States(state_on_hmi_sig, t1_idx, len(state_on_hmi_sig), 1)

                counter = 0
                # Keys contains the idx
                # Check mode
                for key in states_dict:
                    if counter == 1:
                        actual_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE.get(
                            states_dict[key]
                        )

                        if key < t2_idx:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switces into {actual_value} at {time_signal[key]} us"
                                f" but dead man's switch is not pressed just at {round(time_signal[t2_idx], 4)} us.".split()
                            )
                            eval_cond[0] = False
                            break

                        if states_dict[key] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switches into {actual_value} at {time_signal[key]} us"
                                f" but requiered sate is PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}).".split()
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
                    f"The evaluation of {signal_name['Rem_finger_x']} and {signal_name['Rem_finger_y']} signals are FAILED. Dead Man's Switch never pressed."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['General_message']} signal is FAILED, signal never"
                f" switched to LEAVE_VEHICLE ({constants.HilCl.Hmi.APHMIGeneralMessage.LEAVE_VEHICLE})."
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
            "Required state change: RC Getting Off to RC Maneuvering. Reason: Actuating a connected remote device (Dead man's switch)"
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
            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=rem_finger_x, mode="lines", name=signal_name["Rem_finger_x"]))
            fig.add_trace(go.Scatter(x=time_signal, y=rem_finger_y, mode="lines", name=signal_name["Rem_finger_y"]))

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
    name="Mode transition, RC Getting Off to RC Maneuvering, Actuating a connected remote device (Dead man's switch)",
    description="The function shall switch from RC Getting Off to RC Maneuvering mode,"
    " if the driver is actuating a connected remote device",
)
class CommonRcGetOffToRcManDead(TestCase):
    """CommonRcGetOffToRcManDead Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CommonRcGetOffToRcManDeadCheck,
        ]
