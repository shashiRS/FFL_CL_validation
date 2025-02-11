"""Check transition from Maneuvering to Terminate when parking out pose is reached."""

import logging
import os
import sys

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

import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.PDW.pdw_helper import plotter_helper

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "MAN_TO_TER_PARKING_OUT_POSE"

__author__ = "Constantin Marius"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        GENERAL_MESSAGE = "General_message"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.GENERAL_MESSAGE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralMessage",
        }


signals_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="Maneuvering to terminate when parking out pose is reached",
    description="The function shall transition from Maneuvering to Terminate mode when the following condition is "
    "fulfilled: the parking out maneuver reached the parking out pose",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class ManeuveringToTerminateParkingOutPose(TestStep):
    """ManeuveringToTerminateParkingOutPose Test Step."""

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

        signal_summary = {}
        signals = self.readers[SIGNAL_DATA]
        time = signals.index.tolist()
        hmi_info = signals[ValidationSignals.Columns.HMI_INFO]
        general_message = signals[ValidationSignals.Columns.GENERAL_MESSAGE]

        perform_parking_tr = 0
        parking_pose_tr = 0
        self.result.measured_result = None

        for ts in time:

            if not perform_parking_tr:
                if hmi_info[ts] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                    perform_parking_tr = 1
            else:
                # check if parking out pose is reached
                if not parking_pose_tr:
                    if general_message[ts] == constants.HilCl.Hmi.APHMIGeneralMessage.PARKING_OUT_FINISHED:
                        parking_pose_tr = 1
                else:
                    if hmi_info[ts] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS:
                        self.result.measured_result = TRUE
                        break
                    else:
                        self.result.measured_result = FALSE
                        break

        if not perform_parking_tr:
            evaluation = " ".join(
                f"FAILED because signal: {signals_obj._properties[ValidationSignals.Columns.HMI_INFO]} "
                f"did not change his state to PPC_PERFORM_PARKING"
                f"({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})".split()
            )
            signal_summary["Maneuvering to terminate when parking out pose is reached"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not parking_pose_tr:
            evaluation = " ".join(
                f"FAILED because signal: {signals_obj._properties[ValidationSignals.Columns.GENERAL_MESSAGE]} "
                f"did not change his state to PARKING_OUT_FINISHED "
                f"({constants.HilCl.Hmi.APHMIGeneralMessage.PARKING_OUT_FINISHED})".split()
            )
            signal_summary["Maneuvering to terminate when parking out pose is reached"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif self.result.measured_result == TRUE:
            evaluation = " ".join(
                f"PASSED because signal: {signals_obj._properties[ValidationSignals.Columns.HMI_INFO]} "
                f"changed his state to PPC_SUCCESS "
                f"({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS})".split()
            )
            signal_summary["Maneuvering to terminate when parking out pose is reached"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
        elif self.result.measured_result == FALSE:
            evaluation = " ".join(
                f"FAILED because signal: {signals_obj._properties[ValidationSignals.Columns.HMI_INFO]} "
                f"did not changed his state to PPC_SUCCESS "
                f"({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS})".split()
            )
            signal_summary["Maneuvering to terminate when parking out pose is reached"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )

        columns = [
            ValidationSignals.Columns.HMI_INFO,
            ValidationSignals.Columns.GENERAL_MESSAGE,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Signals used in evaluation")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))


@testcase_definition(
    name="Maneuvering to terminate when parking out pose is reached test case",
    description="The function shall transition from Maneuvering to Terminate mode when the following condition is "
    "fulfilled: the parking out maneuver reached the parking out pose",
)
class ManeuveringToTerminateParkingOutPoseTestCase(TestCase):
    """Maneuvering to terminate when parking out pose is reached TC."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            ManeuveringToTerminateParkingOutPose,
        ]
