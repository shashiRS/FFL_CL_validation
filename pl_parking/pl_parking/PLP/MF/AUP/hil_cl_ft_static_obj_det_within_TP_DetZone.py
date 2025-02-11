"""The goal of this TC is to validate the detection of the static objects within the Traffic Participant detection zone."""
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

SIGNAL_DATA = "STATIC_OBJ_DET_TPDZ"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        USEER_ACTION = "User_action"
        STATIC_OBJ_DET_TPDZ = "Static_det_tpdz"


    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.USEER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.STATIC_OBJ_DET_TPDZ: "MTS.SI_DATA.m_environmentModelPort.m_environmentModelPort.numberOfStaticObjects_u8",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Static object detection within detection zone",
    description="The goal of this TC is to validate the detection of the static objects within the Traffic Participant detection zone.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class StaticObjDetWithinTPDZCheck(TestStep):
    """StaticObjDetWithinTPDZCheck Test Step."""

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
        user_act_sig = read_data["User_action"].tolist()
        staticDet_tpdz = read_data["Static_det_tpdz"]

        t1_idx = None

        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation of static object detection {signal_name['Static_det_tpdz']} signal is PASSED,"
            f" all targets are detected (SI_DATA.m_environmentModelPort.m_environmentModelPort.numberOfStaticObjects_u8 == 4).".split()
        )

        """Evaluation part"""
        # Find the moment when AP function is activated
        for cnt in range(0, len(HMI_Info)):
            if user_act_sig[cnt] == constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE:
                t1_idx = cnt
                break
        if t1_idx is not None:
            # taking the timestamp of t1_idx in order to check the reaction after [t_identification] sec
            t1_timestamp = time_signal[t1_idx]
            for cnt in range(t1_idx, len(HMI_Info)):
                if abs(( float(t1_timestamp) - float(time_signal[cnt]) ) / 10**6) > 0.4:
                    t2_idx = cnt
                    break
            if t2_idx is not None:
                # Check the total number of static objects detected with traffic participant detection zone
                if staticDet_tpdz[t1_idx] != 4:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Static_det_tpdz']} signal is FAILED,"
                    f" the system is not detecting the correct number of traffic objects within the traffic participant detection zone (m_environmentModelPort.numberOfStaticObjects_u8 != 4).".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    "TC Failed because the scenario finished before [t_identification] time.".split()
                )
        else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"TC Failed because driver didn't activate the AP function (APHMIOutUserActionHU != {constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE}).".split()
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
            "Check the reaction of the system related to the static object detection within detection zone."
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
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
    name="Static object detection within traffic participant detection zone",
    description="Check the detection of the static objects within the Traffic Participant detection zone",
    doors_url="https://jazz.conti.de/rm4/resources/BI_cbgO591kEe62R7UY0u3jZg?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
class StaticObjDetWithinTPDZ(TestCase):
    """StaticObjDetWithinTPDZ Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            StaticObjDetWithinTPDZCheck,
        ]
