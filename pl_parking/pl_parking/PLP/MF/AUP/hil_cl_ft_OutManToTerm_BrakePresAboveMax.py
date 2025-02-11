"""Check the behavior of the system in case the brake pressure goes above max during parking out maneuver."""
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

SIGNAL_DATA = "OUTMANEUVERING_TO_TERMINATE_BRAKE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        BRAKE = "Brake_pressure"


    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput06.BrakePressureDriver",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Transition mode check - Out Maneuvering to Terminate, brake pressure above max",
    description="Check the transition from Out Maneuvering to Terminate in case the brake pressure goes above AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class OutManToTermBrakeAboveMaxCheck(TestStep):
    """OutManToTermBrakeAboveMaxCheck Test Step."""

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
        brake_pressure = read_data["Brake_pressure"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None

        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation of AVG State {signal_name['State_on_HMI']} signal is PASSED,"
            f" signal switches to Terminate - ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED})".split()
        )

        """Evaluation part"""
        # Find the moment when AP is in maneuvering state
        for cnt in range(0, len(HMI_Info)):
            if HMI_Info[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = cnt
                break

        if t1_idx is not None:

            # Find the moment when brake pressure is > than AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR
            for i in range(t1_idx, len(HMI_Info)):
                if brake_pressure[i] > constants.HilCl.ApThreshold.AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR:
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                # Check the state of the system between t1_idx and t2_idx in order to see if we have a constant state
                for y in range (t1_idx, t2_idx):
                    if HMI_Info[y] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                        eval_cond = [False] * 1
                        break

                if eval_cond[0] is not False:
                    # taking the timestamp of t2_idx in order to check the reaction 10s after
                    t2_timestamp = time_signal[t2_idx]
                    for y in range(t2_idx, len(HMI_Info)):
                        if abs(( float(t2_timestamp) - float(time_signal[y]) ) / 10**6) > constants.HilCl.ApThreshold.THRESOLD_TO_TERMINATE:
                            t3_idx = y
                            break
                    if t3_idx is not None:
                        # check the state of the system after the brake pressure goes above AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR
                        if HMI_Info[t3_idx] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED:
                            test_result = fc.FAIL
                            eval_cond = [False] * 1
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                                f" AVG not in Terminate state after the brake pressure goes above the threshold(AVG != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_FAILED}).".split()
                            )
                    else:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"TC Failed because the scenario finished before the delay finished ({constants.DgpsConstants.THRESOLD_TIME_S})".split()
                        )
                else:
                    evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                                f" AVG didn't had a constant PPC_PERFORM_PARKING state before the brake pressure goes above max (AVG !={constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}).".split()
                            )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"TC Failed because the brake pressure didn't had the value above max threshold({signal_name['Brake_pressure']} > {constants.HilCl.ApThreshold.AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR}bar).".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                "TC Failed because AVG never active"
                f" ({signal_name['State_on_HMI']} != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}).".split()
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
            "Check the reaction of the system during PPC_PERFORM_PARKING Out maneuver in case the brake pressure goes above AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=brake_pressure, mode="lines", name=signal_name["Brake_pressure"]))
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
    name="Out Maneuvering to Terminate transition, brake pressure above max",
    description="The function shall switch from Out Maneuvering to Terminate state if the brake pressure is higher than AP_G_BRAKE_PRESS_TERMINATE_THRESH_BAR.",
    doors_url="https://jazz.conti.de/rm4/resources/BI_ShGGoM_vEe6xJ6AFScj__Q?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
class OutManToTermBrakeAboveMax(TestCase):
    """OutManToTermBrakeAboveMax Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            OutManToTermBrakeAboveMaxCheck,
        ]
