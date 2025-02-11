"""Ego vehicle shall transit from RC Outside ParkOut to RC Maneuvering in case all preconditions are fulfilled."""

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

SIGNAL_DATA = "RCOUTPARK_TO_RCMAN_ACTREMDEV"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        IGNITION = "Ignition"
        REM_DEVICE_CONNECTED = "Rem_device_connected"
        REM_DEVICE_PAIRED = "Rem_device_paired"
        REM_USER_ACT = "Rem_user_act"
        FINGER_POS_X = "Finger_pos_x"
        FINGER_POS_Y = "Finger_pos_y"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
            self.Columns.REM_DEVICE_CONNECTED: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutBTDevConnected",
            self.Columns.REM_DEVICE_PAIRED: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutBTDevPaired",
            self.Columns.REM_USER_ACT: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionRem",
            self.Columns.FINGER_POS_X: "MTS.IO_CAN_AP_Private_CAN.APHMIOut2.APHMIOutRemFingerPosX",
            self.Columns.FINGER_POS_Y: "MTS.IO_CAN_AP_Private_CAN.APHMIOut2.APHMIOutRemFingerPosY",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="The driver is actuating a connected remote device",
    description="The driver is actuating a connected remote device when system is in state 'RC Outside Parking Out'.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class RCParkingOutToRCManActRemDevCheck(TestStep):
    """RCParkingOutToRCManActRemDevCheck Test Step."""

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
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()
        ignition_sig = read_data["Ignition"].tolist()
        rem_device_con_sig = read_data["Rem_device_connected"].tolist()
        rem_device_paired_sig = read_data["Rem_device_paired"].tolist()
        rem_ser_act_sig = read_data["Rem_user_act"].tolist()
        Finger_pos_X = read_data["Finger_pos_x"].tolist()
        Finger_pos_Y = read_data["Finger_pos_y"].tolist()

        ign_on_idx = None
        dev_connected_idx = None
        dev_paired_idx = None
        park_slot_sel_idx = None
        park_out_sel_idx = None
        dead_man_sw_idx = None

        eval_cond = [False] * 1
        evaluation1 = ""

        """Evaluation part"""
        # Find the moment when the ignition is turned on (Conti_Veh_CAN.VehInput05.IgnitionOn set to TRUE [1])
        for cnt in range(0, len(ignition_sig)):
            if ignition_sig[cnt] == constants.HilCl.CarMaker.IGNITION_ON:
                ign_on_idx = cnt
                break

        if ign_on_idx is not None:
            # Find the moment when device is connected (APHMIOutBTDevConnected set to TRUE [1])
            for cnt in range(ign_on_idx, len(rem_device_con_sig)):
                if rem_device_con_sig[cnt] == constants.HilCl.Hmi.BTDevConnected.TRUE:
                    dev_connected_idx = cnt
                    break

            if dev_connected_idx is not None:
                # Find the moment when device is paired (APHMIOutBTDevPaired set to TRUE [1])
                for cnt in range(dev_connected_idx, len(rem_device_paired_sig)):
                    if rem_device_paired_sig[cnt] == constants.HilCl.Hmi.BTDevPaired.TRUE:
                        dev_paired_idx = cnt
                        break

                if dev_paired_idx is not None:
                    for cnt in range(dev_paired_idx, len(rem_ser_act_sig)):
                        # Select the parking slot (AP_Private_CAN.APHMIOut1.APHMIOutUserActionREM set to REM_TAP_ON_PARKING_SPACE_1 [1])
                        if rem_ser_act_sig[cnt] == constants.HilCl.Hmi.RemCommand.REM_TAP_ON_PARKING_SPACE_1:
                            park_slot_sel_idx = cnt
                            break

                    if park_slot_sel_idx is not None:
                        for cnt in range(park_slot_sel_idx, len(rem_ser_act_sig)):
                            # Select park out (AP_Private_CAN.APHMIOut1.APHMIOutUserActionREM set to REM_TAP_ON_PARK_OUT [25])
                            if rem_ser_act_sig[cnt] == constants.HilCl.Hmi.RemCommand.REM_TAP_ON_PARK_OUT:
                                park_out_sel_idx = cnt
                                break

                        if park_out_sel_idx is not None:
                            # Tap on "dead man switch" on remote device (APHMIOutRemFingerPosX set to 1001 and APHMIOutRemFingerPosY set to 2001)
                            for cnt in range(park_out_sel_idx, len(Finger_pos_X)):
                                if (
                                    Finger_pos_X[cnt] == constants.HilCl.Hmi.RemFingerPosition.DM_FINGER_POS_X
                                    and Finger_pos_Y[cnt] == constants.HilCl.Hmi.RemFingerPosition.DM_FINGER_POS_Y
                                ):
                                    dead_man_sw_idx = cnt
                                    break

                            if dead_man_sw_idx is not None:
                                for cnt in range(dead_man_sw_idx, len(Finger_pos_X)):
                                    if (
                                        state_on_hmi_sig[cnt]
                                        == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING
                                    ):
                                        test_result = fc.PASS
                                        eval_cond = [True] * 1
                                        evaluation1 = " ".join(
                                            f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED,"
                                            " the parking maneuver started successfully.".split()
                                        )
                                    else:
                                        test_result = fc.FAIL
                                        eval_cond = [False] * 1
                                        evaluation1 = " ".join(
                                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                                            f" signal never switched to PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}).".split()
                                        )
                            else:
                                test_result = fc.FAIL
                                eval_cond = [False] * 1
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['Finger_pos_x']} and {signal_name['Finger_pos_y']} signals is FAILED,"
                                    f" ({signal_name['Finger_pos_x']} != {constants.HilCl.Hmi.RemFingerPosition.DM_FINGER_POS_X} and"
                                    f" {signal_name['Finger_pos_y']} != {constants.HilCl.Hmi.RemFingerPosition.DM_FINGER_POS_Y}).".split()
                                )
                        else:
                            test_result = fc.FAIL
                            eval_cond = [False] * 1
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Rem_user_act']} signal is FAILED,"
                                f" signal never switched to REM_TAP_ON_PARK_OUT ({constants.HilCl.Hmi.RemCommand.REM_TAP_ON_PARK_OUT}).".split()
                            )
                    else:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Rem_user_act']} signal is FAILED,"
                            f" signal never switched to REM_TAP_ON_PARKING_SPACE_1 ({constants.HilCl.Hmi.RemCommand.REM_TAP_ON_PARK_OUT}).".split()
                        )
                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Rem_device_paired']} signal is FAILED,"
                        f" signal never switched to TRUE ({constants.HilCl.Hmi.BTDevPaired.TRUE}).".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Rem_device_connected']} signal is FAILED,"
                    f" signal never switched to TRUE ({constants.HilCl.Hmi.BTDevConnected.TRUE}).".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Ignition']} signal is FAILED,"
                f" signal never switched to IGNITION_ON ({constants.HilCl.CarMaker.IGNITION_ON}).".split()
            )

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Check if driver is actuating a connected remote device"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=ignition_sig, mode="lines", name=signal_name["Ignition"]))
        fig.add_trace(
            go.Scatter(x=time_signal, y=rem_device_con_sig, mode="lines", name=signal_name["Rem_device_connected"])
        )
        fig.add_trace(
            go.Scatter(x=time_signal, y=rem_device_paired_sig, mode="lines", name=signal_name["Rem_device_paired"])
        )
        fig.add_trace(go.Scatter(x=time_signal, y=rem_ser_act_sig, mode="lines", name=signal_name["Rem_user_act"]))
        fig.add_trace(go.Scatter(x=time_signal, y=Finger_pos_X, mode="lines", name=signal_name["Finger_pos_x"]))
        fig.add_trace(go.Scatter(x=time_signal, y=Finger_pos_Y, mode="lines", name=signal_name["Finger_pos_y"]))
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
    name="RC OutsideParking to RC Maneuvering",
    description="The driver is actuating a connected remote device when system is in state 'RC Outside Parking Out'.",
)
class RCParkingOutToRCManActRemDev(TestCase):
    """RCParkingOutToRCManActRemDev Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            RCParkingOutToRCManActRemDevCheck,
        ]
