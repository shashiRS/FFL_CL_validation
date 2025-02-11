"""Maneuvering time in case of parking in"""

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

SIGNAL_DATA = "MAN_TIME_PARK_IN"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        USER_ACTION = "User_action"
        AVG_TYPE = "AVG_type"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.AVG_TYPE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralAVGType",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Maneuvering time in case of parking in.",
    description=f"Check system capable to finish park in maneuver in {constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S} sec."
    " The time while the maneuver is interrupted shall not be considered for the maneuvering time",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupManTimeCheck(TestStep):
    """AupManTimeCheck Test Step."""

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

        hmi_state_sig = read_data["State_on_HMI"].tolist()
        user_act_sig = read_data["User_action"].tolist()
        avg_type_sig = read_data["AVG_type"].tolist()

        t_start_maneuver_idx = None
        t_end_maneuver_idx = None
        t_interruption = None
        avg_type = None

        number_of_interruption = 0
        calculated_man_time = 0
        calculated_man_time_wo_interrupt = 0
        calculated_interruption_time = 0

        interruption_time_list = []

        evaluation1 = ""

        """Evaluation part"""
        # Find begining  and end of maneuvering
        for cnt, item in enumerate(hmi_state_sig):
            if (
                item == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING
                and t_start_maneuver_idx is None
            ):
                t_start_maneuver_idx = cnt
                continue
            if (
                item == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS
                or item == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED
            ) and t_start_maneuver_idx is not None:
                t_end_maneuver_idx = cnt
                break

        if t_start_maneuver_idx is not None and t_end_maneuver_idx is not None:
            eval_cond = [True] * 1

            # Check AVG type
            avg_type = constants.HilCl.Hmi.APHMIGeneralAVGType.DICT_MESSAGE.get(
                avg_type_sig[t_start_maneuver_idx + 1]
            )  # Wait one sample for exacty AVG type

            # Get actual state
            actual_value_on_hmi = hmi_state_sig[t_end_maneuver_idx]
            actual_state_on_hmi = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE.get(actual_value_on_hmi)

            # Collect number of interruption(s)
            user_act_states = HilClFuntions.States(user_act_sig, 0, len(user_act_sig), 1)

            for key in user_act_states:
                if user_act_states[key] == constants.HilCl.Hmi.Command.TAP_ON_INTERRUPT:
                    number_of_interruption += 1

            # Decide which way is used to evaluate the measurement
            if number_of_interruption > 0:
                # There was at least one interruption

                # Collect states
                states_dict = HilClFuntions.States(hmi_state_sig, t_start_maneuver_idx, t_end_maneuver_idx + 1, 1)
                # Find begining and end of interruptions.
                # Calculate and collect interruptions
                for idx in states_dict:
                    if states_dict[idx] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_PAUSE:
                        t_interruption = time_signal[idx]
                        continue
                    if (
                        states_dict[idx] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING
                        and t_interruption is not None
                    ):
                        delta_t = time_signal[idx] - t_interruption
                        interruption_time_list.append(delta_t)
                        t_interruption = None
                # Calculate the whole interruption time
                calculated_interruption_time = sum(interruption_time_list)

                # Calculate maneuvering time with interruption
                calculated_man_time = time_signal[t_end_maneuver_idx] - time_signal[t_start_maneuver_idx]
                calculated_man_time = calculated_man_time * 1e-6  # convert to s from us
                calculated_man_time = round(calculated_man_time, 3)

                # Calculate maneuvering time without interruption
                calculated_interruption_time = calculated_interruption_time * 1e-6  # convert to s from us
                calculated_interruption_time = round(calculated_interruption_time, 3)
                calculated_man_time_wo_interrupt = calculated_man_time - calculated_interruption_time

                # Compare maneuvering time with limit
                if (
                    calculated_man_time_wo_interrupt > constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S
                    and hmi_state_sig[t_end_maneuver_idx]
                    != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED
                ):
                    eval_cond[0] = False
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['State_on_HMI']} is FAILED, maneuvering time without interruption time is {calculated_man_time_wo_interrupt} sec"
                        f" and this value is larger than {constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S} sec. "
                        f" Number of interruption(s) in TestRun: {number_of_interruption}."
                        f" Whole maneuvering time is {calculated_man_time} sec"
                        f" and whole time of interruption is {calculated_interruption_time} sec."
                        f" Actual state of signal at end of maneuver is {actual_state_on_hmi} ({actual_value_on_hmi})"
                        f" but required state is PPC_PARKING_FAILED ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED})."
                        f" <br>AVG type: {avg_type}.".split()
                    )

                elif (
                    calculated_man_time_wo_interrupt <= constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S
                    and hmi_state_sig[t_end_maneuver_idx] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS
                ):
                    eval_cond[0] = False
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['State_on_HMI']} is FAILED, maneuvering time without interruption time is {calculated_man_time_wo_interrupt} sec"
                        f" and this value is not larger than {constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S} sec."
                        f" Number of interruption(s) in TestRun: {number_of_interruption}."
                        f" Whole maneuvering time is {calculated_man_time} sec"
                        f" and whole time of interruption is {calculated_interruption_time} sec."
                        f" Actual state of signal at end of maneuver is {actual_state_on_hmi} ({actual_value_on_hmi})"
                        f" but required state is PPC_SUCCESS ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS})."
                        f" <br>AVG type: {avg_type}.".split()
                    )
                elif (
                    calculated_man_time_wo_interrupt > constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S
                    and hmi_state_sig[t_end_maneuver_idx]
                    == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED
                ):
                    eval_cond[0] = True
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['State_on_HMI']} is PASSED, maneuvering time without interruption time is {calculated_man_time_wo_interrupt} sec"
                        f" and this value is larger than {constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S} sec. "
                        f" Number of interruption(s) in TestRun: {number_of_interruption}."
                        f" Whole maneuvering time is {calculated_man_time} sec"
                        f" and whole time of interruption is {calculated_interruption_time} sec."
                        f" Actual state of signal at end of maneuver is {actual_state_on_hmi} ({actual_value_on_hmi})"
                        f" and required state is PPC_PARKING_FAILED ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED})."
                        f" <br>AVG type: {avg_type}.".split()
                    )

                else:
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['State_on_HMI']} is PASSED, maneuvering time without interruption time is {calculated_man_time_wo_interrupt} sec"
                        f" and this value is not larger than {constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S} sec."
                        f" Number of interruption(s) in TestRun: {number_of_interruption}."
                        f" Whole maneuvering time is {calculated_man_time} sec"
                        f" and whole time of interruption is {calculated_interruption_time} sec."
                        f" Actual state of signal at end of maneuver is {actual_state_on_hmi} ({actual_value_on_hmi})"
                        f" and required state is PPC_SUCCESS ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS})."
                        f" <br>AVG type:  {avg_type}.".split()
                    )

            else:
                # Number of interruption(s)
                calculated_man_time = time_signal[t_end_maneuver_idx] - time_signal[t_start_maneuver_idx]
                calculated_man_time = calculated_man_time * 1e-6  # convert to s from us
                calculated_man_time = round(calculated_man_time, 3)

                # Compare maneuvering time with limit
                if (
                    calculated_man_time > constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S
                    and hmi_state_sig[t_end_maneuver_idx]
                    != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED
                ):
                    eval_cond[0] = False
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['State_on_HMI']} is FAILED, maneuvering time is {calculated_man_time} sec"
                        f" and this value is larger than {constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S} sec."
                        f" Actual state of signal at end of maneuver is {actual_state_on_hmi} ({actual_value_on_hmi})"
                        f" but required state is PPC_PARKING_FAILED ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED})."
                        f" There is no interruption in TestRun."
                        f" <br>AVG type was {avg_type}.".split()
                    )

                elif (
                    calculated_man_time <= constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S
                    and hmi_state_sig[t_end_maneuver_idx] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS
                ):
                    eval_cond[0] = False
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['State_on_HMI']} is FAILED, maneuvering time is {calculated_man_time} sec"
                        f" and this value is not larger than {constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S} sec."
                        f" Actual state of signal at end of maneuver is {actual_state_on_hmi} ({actual_value_on_hmi})"
                        f" but required state is PPC_SUCCESS ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS})."
                        f" There is no interruption in TestRun."
                        f" <br>AVG type was {avg_type}.".split()
                    )
                elif (
                    calculated_man_time > constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S
                    and hmi_state_sig[t_end_maneuver_idx]
                    == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED
                ):
                    eval_cond[0] = True
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['State_on_HMI']} is FAILED, maneuvering time is {calculated_man_time} sec"
                        f" and this value is larger than {constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S} sec."
                        f" Actual state of signal at end of maneuver is {actual_state_on_hmi} ({actual_value_on_hmi})"
                        f" and required state is PPC_PARKING_FAILED ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED})."
                        f" There is no interruption in TestRun."
                        f" <br>AVG type was {avg_type}.".split()
                    )
                else:
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['State_on_HMI']} is PASSED, maneuvering time is {calculated_man_time} sec"
                        f" and this value is not larger than {constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S} sec."
                        f" Actual state of signal at end of maneuver is {actual_state_on_hmi} ({actual_value_on_hmi})"
                        f" and required state is PPC_SUCCESS ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS})."
                        f" There is no interruption in TestRun."
                        f" <br>AVG type was {avg_type}.".split()
                    )

        elif t_start_maneuver_idx is None:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to"
                f" PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}). Parking maneuver never started."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        elif t_end_maneuver_idx is None:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to"
                f" PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}) "
                f"or to PPC_PARKING_FAILED ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED}). Parking maneuver never finished."
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
            f"The AP function shall be capable of executing a parking in maneuver so that"
            f" the maximum maneuvering time of {constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S} s (tunable) is not exceeded."
            "<br>The time while the maneuver is interrupted shall not be considered for the maneuvering time."
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=time_signal, y=hmi_state_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
            fig.add_trace(go.Scatter(x=time_signal, y=avg_type_sig, mode="lines", name=signal_name["AVG_type"]))

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
    name="Maneuvering time check in case of AP",
    description=f"The AP function shall be capable of executing a parking in maneuver so that"
    f" the maximum maneuvering time of {constants.HilCl.ApThreshold.AP_G_MAX_TIME_TO_PARK_IN_S} s (tunable) is not exceeded."
    " The time while the maneuver is interrupted shall not be considered for the maneuvering time.",
)
class AupManTime(TestCase):
    """AupManTime Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupManTimeCheck,
        ]
