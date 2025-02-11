"""The goal of this TC is to validate the system behavior related to the low beam before the maneuvering is started."""
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

__author__ = "VALERICA ATUDOSIEI"

SIGNAL_DATA = "LOW_BEAM_BEFORE_AVG_ON"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        LOW_BEAM = "Low_beam_state"
        USEER_ACTION = "User_action"


    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.LOW_BEAM: "MTS.IO_CAN_Conti_Veh_CAN.APReq01.LowBeamLightReq",
            self.Columns.USEER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
        }

example_obj = ValidationSignals()

@teststep_definition(
    name="Low Beam State at the beginning of the maneuvering state",
    description="The system shall activate the low beam signal before the maneuvering is started.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class LowBeamActivatedBeforeManCheck(TestStep):
    """LowBeamActivatedBeforeManCheck Test Step."""

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
        low_beam_state = read_data["Low_beam_state"]
        user_act_sig = read_data["User_action"].tolist()

        t1_idx = None
        t2_idx = None

        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation of AVG State {signal_name['State_on_HMI']} signal is PASSED,"
            f" signal switches to Init after the rear left door has been open".split()
        )

        """Evaluation part"""
        # Search for the moment when driver select the start park option from hmi
        for cnt in range(0, len(HMI_Info)):
            if user_act_sig[cnt] == constants.HilCl.Hmi.Command.TAP_ON_START_PARKING:
                t1_idx = cnt
                break
        if t1_idx is not None:
            # Check if the AVG ON
            for _ in range(t1_idx, len(HMI_Info)):
                if HMI_Info[_] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                    t2_idx = _
                    break
            if t2_idx is not None:
                # taking the timestamp of t1_idx in order to check the reaction after THRESOLD_TIME_S sec
                t1_timestamp = time_signal[t1_idx]
                for cnt in range(t1_idx, len(HMI_Info)):
                    if abs(( float(t1_timestamp) - float(time_signal[cnt]) ) / 10**6) > constants.DgpsConstants.THRESOLD_TIME_S:
                        t3_idx = cnt
                        break

                if t3_idx is not None:
                    # Check the reaction of the system
                    if not low_beam_state[t3_idx]:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Low_beam_state']} signal is FAILED,"
                        f" low beam not activated (LowBeamLightReq != 1).".split()
                    )
                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"TC Failed because the scenario finished before the added delay({constants.DgpsConstants.THRESOLD_TIME_S}s)".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Low_beam_state']} signal is FAILED,"
                            f" AVG not activated (APHMIParkingProcedureCtrlState != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}).".split()
                        )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Low_beam_state']} signal is FAILED,"
                            f" the driver didn't select the start parking option (APHMIOutUserActionHU != {constants.HilCl.Hmi.Command.TAP_ON_START_PARKING} ).".split()
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
            "Check the reaction of the low beam signal."
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=low_beam_state, mode="lines", name=signal_name["Low_beam_state"]))
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


@testcase_definition(
    name="Low Beam State before maneuvering state",
    description="The system shall activate the low beam before the maneuvering is started",
    doors_url="https://jazz.conti.de/rm4/resources/BI_TIGNAd1oEe62R7UY0u3jZg?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F26252",
)
class LowBeamActivatedBeforeMan(TestCase):
    """LowBeamActivatedBeforeMan Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            LowBeamActivatedBeforeManCheck,
        ]
