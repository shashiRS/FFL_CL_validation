"""Check the behavior of the system after the remote controller is used by the driver outside the car and ignition successfully turned ON."""
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

SIGNAL_DATA = "RCOUTSIDEWAKEUP_TO_INIT_IGN_OK"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        ENGINE_STATE = "Engine_state"
        SEAT_OCCUPANCY_STATE_DRIVER = "Seat_occupancy_state_driver"
        BT_DEV_CONNECTION = "BT_dev_connection"
        BT_DEV_PAIRED = "BT_dev_paired"
        IGNITION = "Ignition"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.SEAT_OCCUPANCY_STATE_DRIVER: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput02.seatOccupancyStatus_frontLeft",
            self.Columns.BT_DEV_CONNECTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutBTDevConnected",
            self.Columns.BT_DEV_PAIRED: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutBTDevPaired",
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
            self.Columns.ENGINE_STATE: "MTS.IO_CAN_Conti_Veh_CAN.VehInput03.EngineState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Transition mode check - RC Outside WakeUp to RC Outside Parking Out",
    description="Check the transition from RC Outside WakeUp to RC Outside Parking Out, Ignition successfully turned ON.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class RCOutsideWakeUpToRCOutsideParkingOutCheck(TestStep):
    """RCOutsideWakeUpToRCOutsideParkingOutCheck Test Step."""

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
        seat_occupancy_state_driver = read_data["Seat_occupancy_state_driver"].tolist()
        bt_dev_connection = read_data["BT_dev_connection"].tolist()
        bt_dev_paired = read_data["BT_dev_paired"].tolist()
        ignition = read_data["Ignition"].tolist()
        engine_state = read_data["Engine_state"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None

        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation of AVG State {signal_name['State_on_HMI']} signal is PASSED,"
            f" signal switches to RC Outside Parking Out state - ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_OUT})".split()
        )

        """Evaluation part"""
        # Find the moment when AP is in RC Outside Wake Up state
        for cnt in range(0, len(HMI_Info)):
            if HMI_Info[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE:
                t1_idx = cnt
                break

        if t1_idx is not None:

            # Find the moment when Engine is turned ON
            for i in range(t1_idx, len(HMI_Info)):
                if engine_state[i] == 1:
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                # Check the state of the system between t1_idx and t2_idx in order to see if we have a constant state
                for y in range (t1_idx, t2_idx):
                    if HMI_Info[y] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE:
                        eval_cond = [False] * 1
                        break

                if eval_cond[0] is not False:
                    # taking the timestamp of t2_idx in order to check the reaction 0.5s after
                    t2_timestamp = time_signal[t2_idx]
                    for y in range(t2_idx, len(HMI_Info)):
                        if abs(( float(t2_timestamp) - float(time_signal[y]) ) / 10**6) > constants.DgpsConstants.THRESOLD_TIME_S:
                            t3_idx = y
                            break
                    if t3_idx is not None:
                        # check the state of the system after ignition has been turned OFF
                        if HMI_Info[t3_idx] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_OUT:
                            test_result = fc.FAIL
                            eval_cond = [False] * 1
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                                f" AVG not in RC Outside ParkingOut state after Ignition has been turned ON( != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_OUT}).".split()
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
                                f" AVG didn't had a constant WakeUp state before turning the Ignition ON (!={constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE}).".split()
                            )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"TC Failed because the Engine has not been turned ON ({signal_name['Engine_state']} != 1) after WakeUp state(AP[{constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE}])".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                "TC Failed because the WakeUp state has not been reached"
                f" ({signal_name['State_on_HMI']} != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE}).".split()
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
            "Check the reaction of the system during WakeUp state if the Ignition successfully turned ON"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=seat_occupancy_state_driver, mode="lines", name=signal_name["Seat_occupancy_state_driver"]))
        fig.add_trace(go.Scatter(x=time_signal, y=bt_dev_connection, mode="lines", name=signal_name["BT_dev_connection"]))
        fig.add_trace(go.Scatter(x=time_signal, y=bt_dev_paired, mode="lines", name=signal_name["BT_dev_paired"]))
        fig.add_trace(go.Scatter(x=time_signal, y=ignition, mode="lines", name=signal_name["Ignition"]))
        fig.add_trace(go.Scatter(x=time_signal, y=engine_state, mode="lines", name=signal_name["Engine_state"]))
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
    name="RC Outside WakeUp to RC Outside Parking Out transition.",
    description="The function shall switch from RC Outside Wake Up to RC Outside Parking Out mode if ignition was succesfuly turned on.",
    doors_url="https://jazz.conti.de/rm4/resources/BI_E1rzZDHqEe6mrdm2_agUYg?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F26252",
)
class RCOutsideWakeUpToRCOutsideParkingOut(TestCase):
    """RCOutsideWakeUpToRCOutsideParkingOut Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            RCOutsideWakeUpToRCOutsideParkingOutCheck,
        ]
