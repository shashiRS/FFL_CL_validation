"""SOTIF, Re-evaluate parking slot"""

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

SIGNAL_DATA = "SOTIF_RE_EVAL_SLOT"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        HOL_REQUEST = "Hold_req"
        T00_TX = "T00_tx"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.HOL_REQUEST: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCHoldReq",
            self.Columns.T00_TX: "CM.Traffic.T00.tx",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Send hold request after re-evaluation is slot is not safe",
    description="Check system send hold request is slot is not anymore according re-evaluation",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class SotifNotSafeSlotCheck(TestStep):
    """SotifNotSafeSlotCheck Test Step."""

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
        hold_req_sig = read_data["Hold_req"].tolist()
        t00_tx_sig = read_data["T00_tx"].tolist()

        t_start_man_idx = None
        t_obs_in_way_idx = None
        t_hold_req_idx = None

        treshold_ms = constants.HilCl.SotifTime.T_UPDATE_3 + constants.HilCl.SotifTime.T_UPDATE_4

        t00_target_x = 54  # Value is very specific for this evaluation script. Not used in any another script so not added to constants.py

        """Evaluation part"""
        # Find begining of maneuvering
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_start_man_idx = cnt
                break

        if t_start_man_idx is not None:
            # Find when obstacle teleport in the slot
            for cnt in range(t_start_man_idx, len(t00_tx_sig)):
                if t00_tx_sig[cnt] == t00_target_x:
                    t_obs_in_way_idx = cnt
                    break

            if t_obs_in_way_idx is not None:
                # Find when sysytem sent out hold requ
                for cnt in range(t_obs_in_way_idx, len(hold_req_sig)):
                    if hold_req_sig[cnt] == constants.HilCl.LoDMCHoldReq.TRUE:
                        t_hold_req_idx = cnt
                        break

                if t_hold_req_idx is not None:

                    # Calculate reaction time
                    reation_t = time_signal[t_hold_req_idx] - time_signal[t_obs_in_way_idx]
                    reation_t = reation_t * 1e-3  # Conver to ms from us

                    if reation_t > treshold_ms:
                        test_result = fc.FAIL
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Hold_req']} signal is FAILED, value of the signal switched to TRUE ({constants.HilCl.LoDMCHoldReq.TRUE}) at {time_signal[t_hold_req_idx]} us"
                            f" but reaction time of the system was {reation_t} ms. Limit for reaction is {treshold_ms} ms.".split()
                        )
                    else:
                        test_result = fc.PASS
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Hold_req']} signal is PASSED, value of the signal switched to TRUE ({constants.HilCl.LoDMCHoldReq.TRUE}) at {time_signal[t_hold_req_idx]} us"
                            f" and reaction time of the system was {reation_t} ms. Limit for reaction is {treshold_ms} ms.".split()
                        )

                else:
                    test_result = fc.FAIL
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Hold_req']} signal is FAILED, value of the signal never switched to TRUE ({constants.HilCl.LoDMCHoldReq.TRUE})."
                        " There was no hold request from AP after obstacle teleported into the slot."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )

            else:
                test_result = fc.FAIL
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['T00_tx']} signal is FAILED, value of the signal never switched to {t00_target_x}. Obstacle never telepoted into the slot."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )
        else:
            test_result = fc.FAIL
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to PPC_PERFORM_PARKING {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}"
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary[
            f"System shall execute following action in range {treshold_ms} ms after traffic object appeared."
            "<br>Conti_Veh_CAN.APReq01.LoDMCHoldReq shall switch to TRUE [1]"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=hold_req_sig, mode="lines", name=signal_name["Hold_req"]))
            fig.add_trace(go.Scatter(x=time_signal, y=t00_tx_sig, mode="lines", name=signal_name["T00_tx"]))

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
    name="Target slot is not safe anymore",
    description=f"System shall send a hold request in {constants.HilCl.SotifTime.T_UPDATE_3} ms + {constants.HilCl.SotifTime.T_UPDATE_4} ms"
    " if slot is not save anymore according re-evaluation.",
)
class SotifNotSafeSlot(TestCase):
    """SotifNotSafeSlot Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SotifNotSafeSlotCheck,
        ]
