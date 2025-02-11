"""In case of an interruption of the AVG the AP function will secure the VUT in a standstill and prevent collision."""
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

SIGNAL_DATA = "PREVENT_COLLISION_DURING_INTERR"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        DRIVING_DIR = "Driv_dir"
        BRAKE_REQUEST_EMERGENCY = "Brake_rq_emergency"
        CAR_HITCH_Y = "Car_Hitch_ty"
        PEDESTRIAN_Y = "traffic_t00_ty"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
            self.Columns.BRAKE_REQUEST_EMERGENCY: "MTS.IO_CAN_Conti_Veh_CAN.APReq01.LoDMCEmergencyHoldRequest",
            self.Columns.CAR_HITCH_Y: "CM.Car.Hitch.ty",
            self.Columns.PEDESTRIAN_Y: "CM.Traffic.T00.ty",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Brake during interrupt state.",
    description="The system shall prevent the collision during interrupt state while the ego car is still braking.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PreventCollisionDuringInterrCheck(TestStep):
    """PreventCollisionDuringInterrCheck Test Step."""

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
        driving_dir_sig = read_data["Driv_dir"].tolist()
        break_req_emergency = read_data["Brake_rq_emergency"].tolist()
        car_hitch_Y = read_data["Car_Hitch_ty"].tolist()
        pedestrian_Y = read_data["traffic_t00_ty"].tolist()

        t1_idx = None
        t2_idx = None
        trigger_emergency_brake = False
        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation of AVG State {signal_name['State_on_HMI']} signal is PASSED,"
            f" signal switches to Parking state within {constants.HilCl.ApThreshold.AP_G_MAX_LATENCY_REM_S}s".split()
        )

        """Evaluation part"""
        # Find the moment when AP started the interrupt state
        for cnt in range(0, len(HMI_Info)):
            if HMI_Info[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_PAUSE:
                t1_idx = cnt
                break
        if t1_idx is not None:
            # Check if we have a deceleration smaller than constants.HilCl.ApThreshold.AP_G_MAX_DECEL_COMFORTABLE_MPS2
            if break_req_emergency[t1_idx] == 0:
                # Search for the moment when ego vehicle is in standstill
                for _ in range(t1_idx, len(HMI_Info)):
                    if driving_dir_sig[_] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL:
                        t2_idx = _
                        break

                if t2_idx is not None:
                    # Check if we exceeded the max comfort deceleration durring interrupt state
                    for i in range(t1_idx, t2_idx):
                        if break_req_emergency[i] == 1:
                            trigger_emergency_brake = True
                            break

                    if trigger_emergency_brake is True:
                        # Check is the system avoided the colision
                        if car_hitch_Y[t2_idx] - pedestrian_Y[t2_idx] < 0 :
                            test_result = fc.FAIL
                            eval_cond = [False] * 1
                            evaluation1 = " ".join(
                            "TC Failed, the system didn't avoid the colision.".split()
                        )
                    else:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                        "TC Failed, deceleration didn't exceed the max confortable value ({constants.HilCl.ApThreshold.AP_G_MAX_DECEL_COMFORTABLE_MPS2}) .".split()
                        )

                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"TC Failed, ego car not in standstill (APHMIGeneralDrivingDir != {constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL}).".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Brake_rq']} signal is FAILED,"
                            f" comfort deceleration > {constants.HilCl.Hmi.ParkingProcedureCtrlState} before interrupt state.".split()
                        )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"TC Failed, the AP not in Interrupt state (ParkingProcedureCtrlState != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_PAUSE})".split()
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
            "Check the reaction of the system in case of interrupt state while a dynamic obj is coming closer to the ego veh."
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=driving_dir_sig, mode="lines", name=signal_name["Driv_dir"]))
        fig.add_trace(go.Scatter(x=time_signal, y=break_req_emergency, mode="lines", name=signal_name["Brake_rq_emergency"]))
        fig.add_trace(go.Scatter(x=time_signal, y=car_hitch_Y, mode="lines", name=signal_name["Car_Hitch_ty"]))
        fig.add_trace(go.Scatter(x=time_signal, y=pedestrian_Y, mode="lines", name=signal_name["traffic_t00_ty"]))
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
    name="Brake during interrupt state.",
    description="The system shall prevent the collision during interrupt state while the ego car is still braking.",
    doors_url="https://jazz.conti.de/rm4/resources/BI_Xq04x_V2Ee26y5qu8i0o0w?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
class PreventCollisionDuringInterr(TestCase):
    """PreventCollisionDuringInterr Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PreventCollisionDuringInterrCheck,
        ]
