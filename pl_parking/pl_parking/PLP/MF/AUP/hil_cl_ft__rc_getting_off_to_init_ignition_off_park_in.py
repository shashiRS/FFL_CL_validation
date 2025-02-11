"""Mode transition, RC Getting Off to Init, Ignition off, Park in"""

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

SIGNAL_DATA = "RC_GET_OFF_TO_INIT_IGN_OFF"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        IGNITION = "Ignition"
        REM_USER_ACT = "Rem_user_act"
        HMI_INFO = "State_on_HMI"
        GENERAL_MESSAGE = "General_message"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
            self.Columns.REM_USER_ACT: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionRem",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Cancel via turning off ignition",
    description="Check RC function reaction if driver turning off ignition in RC Getting off state.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class CommonRcGetOffToInitCancelCheck(TestStep):
    """CommonRcGetOffToInitCancelCheck Test Step."""

    custom_report = MfHilClCustomTeststepReport

    def __init__(self):
        """Init test."""
        super().__init__()

    @fh.HilClFuntions.log_exceptions
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
        time_signal = read_data.index
        ignition_sig = read_data["Ignition"].tolist()
        rem_ser_act_sig = read_data["Rem_user_act"].tolist()
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()
        general_message_sig = read_data["General_message"].tolist()

        t_park_in_sel_idx = None
        t_ignition_off_idx = None

        eval_cond = []
        evaluation_steps = {}

        """Evaluation part"""
        # Find the moment when park in is selected
        for cnt in range(0, len(rem_ser_act_sig)):
            if rem_ser_act_sig[cnt] == constants.HilCl.Hmi.RemCommand.REM_TAP_ON_PARK_IN:
                t_park_in_sel_idx = cnt
                break

        if t_park_in_sel_idx is not None:
            # Find the moment when ignition is turned off
            for cnt in range(t_park_in_sel_idx, len(ignition_sig)):
                if ignition_sig[cnt] == constants.HilCl.CarMaker.IGNITION_OFF:
                    t_ignition_off_idx = cnt
                    break

            if t_ignition_off_idx is not None:

                general_message_states = HilClFuntions.States(
                    general_message_sig, t_park_in_sel_idx, t_ignition_off_idx, 1
                )

                lastGeneralMessageBeforeIgnOff = general_message_states[max(general_message_states.keys())]

                ppc_states = HilClFuntions.States(state_on_hmi_sig, t_park_in_sel_idx, t_ignition_off_idx, 1)

                lastPPCStateBeforeIgnOff = ppc_states[max(ppc_states.keys())]

                generalMessageIsCorrect = (
                    lastGeneralMessageBeforeIgnOff == constants.HilCl.Hmi.APHMIGeneralMessage.LEAVE_VEHICLE
                )

                ppcStateIsCorrect = (
                    lastPPCStateBeforeIgnOff != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_INACTIVE
                )

                if generalMessageIsCorrect:
                    eval_cond.append(True)
                    evaluation_steps[
                        f"LEAVE_VEHICLE value ({constants.HilCl.Hmi.APHMIGeneralMessage.LEAVE_VEHICLE}) should be present in the signal before ignition off"
                    ] = " ".join(f"The evaluation of {signal_name['General_message']} signal is PASSED".split())
                else:
                    eval_cond.append(False)
                    evaluation_steps[
                        f"LEAVE_VEHICLE value ({constants.HilCl.Hmi.APHMIGeneralMessage.LEAVE_VEHICLE}) should be present in the signal before ignition off"
                    ] = " ".join(
                        f"The evaluation of {signal_name['General_message']} signal is FAILED, value is {lastGeneralMessageBeforeIgnOff}".split()
                    )

                if ppcStateIsCorrect:
                    eval_cond.append(True)
                    evaluation_steps[
                        f"PPC_PARKING_INACTIVE value ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_INACTIVE}) should not be present in the signal before ignition off"
                    ] = " ".join(f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED".split())
                else:
                    eval_cond.append(False)
                    evaluation_steps[
                        f"PPC_PARKING_INACTIVE value ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_INACTIVE}) should not be present in the signal before ignition off"
                    ] = " ".join(
                        f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, value is {lastPPCStateBeforeIgnOff}".split()
                    )

                if generalMessageIsCorrect and ppcStateIsCorrect:

                    # Find the moment when system state related signal switched to PPC_PARKING_INACTIVE after ignition is turned off
                    for cnt in range(t_ignition_off_idx, len(state_on_hmi_sig)):
                        if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_INACTIVE:
                            eval_cond.append(True)
                            evaluation_steps[
                                f"PPC_PARKING_INACTIVE value ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_INACTIVE}) should be present in the signal"
                            ] = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED,"
                                " the parking maneuver stopped successfully.".split()
                            )
                            break
                    else:
                        eval_cond.append(False)
                        evaluation_steps[
                            f"PPC_PARKING_INACTIVE value ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_INACTIVE}) should be present in the signal"
                        ] = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                            f" signal never switched to PPC_PARKING_INACTIVE"
                            f" ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_INACTIVE}).".split()
                        )

            else:
                eval_cond.append(False)
                evaluation_steps["IGNITION_OFF should be present in the signal"] = " ".join(
                    f"The evaluation of {signal_name['Ignition']} signal is FAILED, signal never switched to IGNITION_OFF "
                    f" ({constants.HilCl.CarMaker.IGNITION_OFF}).".split()
                )
        else:
            eval_cond.append(False)
            evaluation_steps["REM_TAP_ON_PARK_IN should be present in the signal"] = " ".join(
                f"The evaluation of {signal_name['Rem_user_act']} signal is FAILED, signal never switched to REM_TAP_ON_PARK_IN "
                f" ({constants.HilCl.Hmi.RemCommand.REM_TAP_ON_PARK_IN}).".split()
            )

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(evaluation_steps)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=ignition_sig, mode="lines", name=signal_name["Ignition"]))
        fig.add_trace(go.Scatter(x=time_signal, y=rem_ser_act_sig, mode="lines", name=signal_name["Rem_user_act"]))
        fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))

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
    name="Mode transition, RC Getting Off to Init, Cancelled on ignition off",
    description="The function shall switch from RC Getting Off to Init mode, if the planned RC maneuver was cancelled by turning ignition off",
)
class CommonRcGetOffToInitCancel(TestCase):
    """CommonRcGetOffToInitCancel Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CommonRcGetOffToInitCancelCheck,
        ]
