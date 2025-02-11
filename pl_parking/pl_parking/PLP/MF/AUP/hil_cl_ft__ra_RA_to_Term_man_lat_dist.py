"""The driver has terminated the RA maneuver via lateral distance greater then {RA_G_MAX_LAT_START_ERROR_M}."""
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
    verifies,
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

__author__ = "VALERICA ATUDOSIEI"

SIGNAL_DATA = "RA_TO_TERMINATE_LAT_DIST"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        PATH_DEVDIST = "Path_DevDist"
        GENERAL_SCREEN = "General_screen"
        GENERAL_MESSAGE = "General_message"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.PATH_DEVDIST: "MTS.Car.Road.Path.DevDist",
            self.Columns.GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Transition mode check - RA Reverse to Terminate, lat dist above max threshold",
    description="Check the transition from RA Reverse to Terminate if lat dist above max threshold",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class RAReverseToTerminateLatDistCheck(TestStep):
    """RAReverseToTerminateLatDistCheck Test Step."""

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

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        HMI_Info = read_data["State_on_HMI"].tolist()
        road_dev_dist = read_data["Path_DevDist"].tolist()
        general_message = read_data["General_message"].tolist()
        state_on_hmi_sig = read_data["General_screen"].tolist()

        t1_RA_active_idx = None
        t2_lat_dist_greater_than_max = None
        t3_system_reaction_after_lat_dist_exceeded = None

        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation of RA State {signal_name['General_message']} signal is PASSED,"
            f" signal switches to Terminate ({constants.HilCl.Hmi.APHMIGeneralMessage.REVERSE_ASSIST_CANCELLED}) after lat dist is greater than RA_G_MAX_LAT_START_ERROR_M".split()
        )

        """Evaluation part"""
         # Find when parking core switches to automated reverse mode
        for cnt in range(0, len(HMI_Info)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                t1_RA_active_idx = cnt
                init_lat_dist = abs(road_dev_dist[cnt])
                break
        if t1_RA_active_idx is not None:
            # Find the moment when laterat dist is > {RA_G_MAX_LAT_START_ERROR_M}
            for i in range(t1_RA_active_idx, len(HMI_Info)):
                if abs(road_dev_dist[i]) > init_lat_dist + constants.HilCl.ApThreshold.RA_G_MAX_LAT_START_ERROR_M:
                    t2_lat_dist_greater_than_max = i
                    break
            if t2_lat_dist_greater_than_max is not None:
                # taking the timestamp of t2_lat_dist_greater_than_max in order to check the reaction 0.5s after
                t2_timestamp = time_signal[t2_lat_dist_greater_than_max]
                for y in range(t2_lat_dist_greater_than_max, len(HMI_Info)):
                    if abs(( float(t2_timestamp) - float(time_signal[y]) ) / 10**6) > constants.DgpsConstants.THRESOLD_TIME_S:
                        t3_system_reaction_after_lat_dist_exceeded = y
                        break
                if t3_system_reaction_after_lat_dist_exceeded is not None:
                    # Check the reaction of the system after THRESOLD_TIME_S s
                    if general_message[t3_system_reaction_after_lat_dist_exceeded] != constants.HilCl.Hmi.APHMIGeneralMessage.REVERSE_ASSIST_CANCELLED:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['General_message']} signal is FAILED,"
                            f" RA not deactivated(APHMIGeneralMessage != {constants.HilCl.Hmi.APHMIGeneralMessage.REVERSE_ASSIST_CANCELLED}).".split()
                        )
                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"TC Failed because the scenario finished before the delay finished ({constants.DgpsConstants.THRESOLD_TIME_S})".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Path_DevDist']} signal is FAILED,"
                            f" laterat dist(PathDevDist) is not > {constants.HilCl.ApThreshold.RA_G_MAX_LAT_START_ERROR_M}m during RA activex(initial value {init_lat_dist}).".split()
                        )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"TC Failed, RA maneuver not started ({signal_name['General_screen']} != {constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST}).".split()
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
            "Check the reaction of the system during Reverse state in case lat dist is above max threshold"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=road_dev_dist, mode="lines", name=signal_name["Path_DevDist"]))
        fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["General_screen"]))
        fig.add_trace(go.Scatter(x=time_signal, y=general_message, mode="lines", name=signal_name["General_message"]))
        fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
        fig.update_layout(PlotlyTemplate.lgt_tmplt)

        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

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

@verifies(
    requirement="1948418",
)
@testcase_definition(
    name="Transition mode check - RA Reverse to Terminate, lat dist above max thresh.",
    description="Check the transition from RA Reverse to Terminate if lat dist above max thresh.",
    doors_url="https://jazz.conti.de/rm4/resources/BI_yfGbgdI4Ee6vvdVFvzgyYA?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
class RAReverseToTerminateLatDist(TestCase):
    """RAReverseToTerminateLatDist Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            RAReverseToTerminateLatDistCheck,
        ]
