"""Init mode. Release all active controll."""

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

SIGNAL_DATA = "INIT_RELEASE_ACTIVE_CTRL"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        LATERAL_CTRL_STATUS = "LaDMC_status"
        LONGITUDINAL_CTRL_REQUEST = "LoDMC_Ctrl_Request"
        USER_ACTION = "User_action"
        IGNITION = "Ignition"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.LATERAL_CTRL_STATUS: "MTS.ADAS_CAN.Conti_Veh_CAN.AP_DFLaDMCOutput01.LaDMC_Status__nu",
            self.Columns.LONGITUDINAL_CTRL_REQUEST: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCCtrlRequest",
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Active control state",
    description="Check system release all active controll in Init mode.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class InitRelActCtrlCheck(TestStep):
    """InitRelActCtrlCheck Test Step."""

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
        user_act_sig = read_data["User_action"].tolist()
        lo_ctrl_status_sig = read_data["LoDMC_Ctrl_Request"].tolist()
        la_ctrl_status_sig = read_data["LaDMC_status"].tolist()
        ignition_sig = read_data["Ignition"].tolist()

        t_maneuvering_start_idx = None
        t_maneuvering_end_idx = None
        t_user_deact_idx = None
        t_init_idx = None
        t_ign_off_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['LoDMC_Ctrl_Request']} signal and {signal_name['LaDMC_status']} signal is PASSED,"
            " system released all active control in Init mode.".split()
        )

        """Evaluation part"""
        # Find maneuver start
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_maneuvering_start_idx = cnt
                break

        if t_maneuvering_start_idx is not None:

            # Find maneuver end
            for cnt in range(t_maneuvering_start_idx, len(state_on_hmi_sig)):
                if state_on_hmi_sig[cnt] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                    t_maneuvering_end_idx = cnt
                    break

            if t_maneuvering_end_idx is not None:
                # Find when driver deactivate AP function
                for cnt in range(t_maneuvering_start_idx, t_maneuvering_end_idx):
                    if user_act_sig[cnt] == constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE:
                        t_user_deact_idx = cnt
                        break

                if t_user_deact_idx is not None:
                    # Find begining of Init mode
                    for cnt in range(t_user_deact_idx, len(state_on_hmi_sig)):
                        if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE:
                            t_init_idx = cnt
                            break

                    if t_init_idx is not None:
                        # Check La and Lo control
                        for cnt in range(t_init_idx, len(ignition_sig)):
                            if ignition_sig[cnt] == constants.HilCl.CarMaker.IGNITION_OFF:
                                t_ign_off_idx = cnt
                                break

                        if t_ign_off_idx is not None:

                            eval_cond = [True] * 1

                            # Check La and Lo control release
                            for cnt in range(t_init_idx, t_ign_off_idx):
                                if la_ctrl_status_sig[cnt] != 0 or lo_ctrl_status_sig[cnt] != 0:
                                    eval_cond[0] = False
                                    evaluation1 = " ".join(
                                        f"The evaluation of {signal_name['LoDMC_Ctrl_Request']} signal and {signal_name['LaDMC_status']} signal is FAILED,"
                                        f" {signal_name['LaDMC_status']} is {la_ctrl_status_sig[cnt]} at {time_signal[cnt]} us and"
                                        f" {signal_name['LoDMC_Ctrl_Request']} is {lo_ctrl_status_sig[cnt]} at {time_signal[cnt]} us."
                                        " It means, system not released all active control in Init mode.".split()
                                    )
                                    break

                        else:
                            test_result = fc.FAIL
                            eval_cond = [False] * 1
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Ignition']} signal is FAILED, signal never switched to"
                                f" IGNITION_OFF ({constants.HilCl.CarMaker.IGNITION_OFF})"
                                f" after {signal_name['State_on_HMI']} signal switched to PPC_INACTIVE ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE})."
                                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                            )

                    else:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to"
                            f" PPC_INACTIVE ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE})"
                            f" after PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})."
                            " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                        )
                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['User_action']} signal is FAILED, signal never switched to"
                        f" TOGGLE_AP_ACTIVE ({constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE})."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched out from"
                    f" PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}) mode."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to"
                f" PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}) mode."
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

        signal_summary["Init mode. The function shall release all active control in Init mode."] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
            fig.add_trace(go.Scatter(x=time_signal, y=ignition_sig, mode="lines", name=signal_name["Ignition"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=lo_ctrl_status_sig, mode="lines", name=signal_name["LoDMC_Ctrl_Request"])
            )
            fig.add_trace(
                go.Scatter(x=time_signal, y=la_ctrl_status_sig, mode="lines", name=signal_name["LaDMC_status"])
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
    name="Init mode. Release all active control",
    description="The function shall release all active control in Init mode.",
)
class InitRelActCtrl(TestCase):
    """InitRelActCtrl Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            InitRelActCtrlCheck,
        ]
