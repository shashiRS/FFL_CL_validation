"""Init as default mode"""

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

SIGNAL_DATA = "IINIT_AS_DEFAULT"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        IGNITION = "Ignition"
        USER_ACT = "User_action"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
            self.Columns.USER_ACT: "CM.IO_CAN_AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name=" System state between ignition on and AP activation ",
    description=" Check System state between ignition on and AP activation",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupInitDefaultCheck(TestStep):
    """AupInitDefaultCheck Test Step."""

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
        ignition_sig = read_data["Ignition"].tolist()
        user_act_sig = read_data["User_action"].tolist()

        t_ign_on_idx = None
        t_tap_on_ap_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED, state of signal is PPC_INACTIVE ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE})"
            f" between Ignition On and TOGGLE_AP_ACTIVE events.".split()
        )

        """Evaluation part"""
        # Find ignition on
        for cnt, item in enumerate(ignition_sig):
            if item == constants.HilCl.CarMaker.IGNITION_ON:
                t_ign_on_idx = cnt
                break

        if t_ign_on_idx is not None:

            # Find TOGGLE_AP_ACTIVE
            for cnt in range(t_ign_on_idx, len(user_act_sig)):
                if user_act_sig[cnt] == constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE:
                    t_tap_on_ap_idx = cnt
                    break
            if t_tap_on_ap_idx is not None:
                test_result = fc.PASS
                self.result.measured_result = TRUE

                # Check state between IGNITION_ON and TOGGLE_AP_ACTIVE
                for cnt in range(t_ign_on_idx, t_tap_on_ap_idx + 1):
                    if state_on_hmi_sig[cnt] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE:

                        actual_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE.get(
                            state_on_hmi_sig[cnt]
                        )
                        test_result = fc.FAIL
                        self.result.measured_result = FALSE
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, state of signal is {actual_value} at {time_signal[cnt]} us"
                            f" but requiered mode is PPC_INACTIVE ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE}).".split()
                        )
                        break

            else:
                test_result = fc.FAIL
                self.result.measured_result = FALSE
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['User_action']} signal is FAILED, signal never switched to TOGGLE_AP_ACTIVE ({constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Ignition']} signal is FAILED, signal never switched to IGNITION_ON ({constants.HilCl.CarMaker.IGNITION_ON})."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        signal_summary["The function shall go into Init mode as the default mode during startup"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED"""
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
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
    name="Init as default mode",
    description="The function shall go into Init mode as the default mode during startup.",
)
class AupInitDefault(TestCase):
    """AupInitDefault Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupInitDefaultCheck,
        ]
