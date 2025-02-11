"""SOTIF, Safe state if the selected parking slot is not longer safe for more than {T_UPDATE_2}"""

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

SIGNAL_DATA = "SOTIF_SLOT_NOT_SAFE_MORE_THAN"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        FREE_SLOT_RIGHT = "Free_slot_right"
        HOL_REQUEST = "Hold_req"
        T00_TX = "T00_tx"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.FREE_SLOT_RIGHT: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInSituationRight.ParkingSlotFreeRight",
            self.Columns.HOL_REQUEST: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCHoldReq",
            self.Columns.T00_TX: "CM.Traffic.T00.tx",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Send hold request and remove slot from offered list",
    description="Check system send hold request and remove slot from offered list in time",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class SotifNotSafeTrajCheck(TestStep):
    """SotifNotSafeTrajCheck Test Step."""

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
        free_slot_sig = read_data["Free_slot_right"].tolist()
        hold_req_sig = read_data["Hold_req"].tolist()
        t00_tx_sig = read_data["T00_tx"].tolist()

        t_slot_detection_idx = None
        t_obs_in_way_idx = None
        t_hold_req_idx = None
        t_slot_dropped_idx = None

        treshold_ms = constants.HilCl.SotifTime.T_UPDATE_1 + constants.HilCl.SotifTime.T_UPDATE_2

        t00_target_x = 53  # Value is very specific for this evaluation script. Not used in any another script so not added to constants.py

        """Evaluation part"""
        # Check slot detection
        for cnt in range(0, len(free_slot_sig)):
            if free_slot_sig[cnt] > 0:
                t_slot_detection_idx = cnt
                break

        if t_slot_detection_idx is not None:

            # Find when obstacel teleport in the area
            for cnt in range(t_slot_detection_idx, len(t00_tx_sig)):
                if t00_tx_sig[cnt] == t00_target_x:
                    t_obs_in_way_idx = cnt
                    break

            if t_obs_in_way_idx is not None:
                # Find when system send HolReq and remove slot from list

                for cnt in range(t_obs_in_way_idx, len(time_signal)):
                    if hold_req_sig[cnt] == constants.HilCl.LoDMCHoldReq.TRUE and t_hold_req_idx is None:
                        t_hold_req_idx = cnt

                    # Compare actual number of free slots with number befor obstacle appeared
                    if free_slot_sig[cnt] < free_slot_sig[t_obs_in_way_idx - 1] and t_slot_dropped_idx is None:
                        t_slot_dropped_idx = cnt

                    if t_hold_req_idx is not None and t_slot_dropped_idx is not None:
                        break

                if t_hold_req_idx is not None and t_slot_dropped_idx is not None:
                    # Calculate reaction time
                    reaction_t_slot = time_signal[t_slot_dropped_idx] - time_signal[t_obs_in_way_idx]
                    reaction_t_slot = reaction_t_slot * 1e-3  # Conver to ms from us

                    reaction_t_hold = time_signal[t_hold_req_idx] - time_signal[t_obs_in_way_idx]
                    reaction_t_hold = reaction_t_hold * 1e-3  # Conver to ms from us

                    if reaction_t_slot > treshold_ms and reaction_t_hold > treshold_ms:
                        test_result = fc.FAIL
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Free_slot_right']} signal and {signal_name['Hold_req']} is FAILED."
                            f" Reaction time of system was more than {treshold_ms} ms. System didn't send hold request in time and didn't remove parking slot from the offered list in time."
                            f"<br> Reaction time of {signal_name['Free_slot_right']}: {reaction_t_slot} ms"
                            f"<br> Reaction time of {signal_name['Hold_req']}: {reaction_t_hold} ms".split()
                        )
                    elif reaction_t_hold > treshold_ms:
                        test_result = fc.FAIL

                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Hold_req']} is FAILED, reaction time of the signal was {reaction_t_hold} ms but limit is {treshold_ms} ms."
                            " System didn't send hold request in time.".split()
                        )
                    elif reaction_t_slot > treshold_ms:
                        test_result = fc.FAIL

                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Free_slot_right']} is FAILED, reaction time of the signal was {reaction_t_slot} ms but limit is {treshold_ms} ms."
                            " System didn't remove parking slot from the offered list in time.".split()
                        )
                    else:
                        test_result = fc.PASS
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Free_slot_right']} signal and {signal_name['Hold_req']} is PASSED."
                            f" System sent brake request and removed slot from the offered list in time. Limit for execution is {treshold_ms} ms"
                            f"<br> Reaction time of {signal_name['Free_slot_right']}: {reaction_t_slot} ms"
                            f"<br> Reaction time of {signal_name['Hold_req']}: {reaction_t_hold} ms".split()
                        )

                elif t_hold_req_idx is None and t_slot_dropped_idx is not None:
                    test_result = fc.FAIL
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Hold_req']} signal is FAILED, signal never switched to TRUE after obstacle appeared in the area of ego vehicle."
                        f" Obstacle appeared at {time_signal[t_obs_in_way_idx]} us."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )

                elif t_hold_req_idx is not None and t_slot_dropped_idx is None:
                    test_result = fc.FAIL
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Free_slot_right']} signal is FAILED, value of the signal did not reduced after obstacle appeared in the way of ego vehicle."
                        f" Obstacle appeared at {time_signal[t_obs_in_way_idx]} us."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )

            else:
                test_result = fc.FAIL
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['T00_tx']} signal is FAILED, signal value never set to"
                    f" {t00_target_x}. Obstacle never moved in the area of the ego vehicle."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL

            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Free_slot_right']} signal is FAILED, value of signal never more than 0. There was no slot detection."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary[
            f"System shall execute following actions in range {treshold_ms} ms after traffic object appeared."
            "<br>Remove the parking slot from offered list"
            "<br>Conti_Veh_CAN.APReq01.LoDMCHoldReq shall switch to TRUE [1]"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=free_slot_sig, mode="lines", name=signal_name["Free_slot_right"]))
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
    name="Calculated trajectory is not safe anymore",
    description=f"System shall go to safe state and remove slor from offered list in range {constants.HilCl.SotifTime.T_UPDATE_1} ms + {constants.HilCl.SotifTime.T_UPDATE_2} ms",
)
class SotifNotSafeTraj(TestCase):
    """SotifNotSafeTraj Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SotifNotSafeTrajCheck,
        ]
