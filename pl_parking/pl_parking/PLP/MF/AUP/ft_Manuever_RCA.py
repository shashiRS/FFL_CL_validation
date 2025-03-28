#!/usr/bin/env python3
"""Root cause analysis for Manuever test."""
import json
import logging
import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
from time import time as start_time

from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants

# from pl_parking.PLP.MF.PARKSM.ft_parksm import StatisticsExample
from pl_parking.common_ft_helper import MfCustomTestcaseReport

__author__ = "BA ADAS ENP SIMU KPI"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

EXAMPLE = "ROOT_CAUSE_M"
now_time = start_time()


class StoreStepResults:
    """Initializes variables for multiple steps and provides a method
    to check their status and return corresponding results and color codes.
    """

    def __init__(self):
        """Initialize the test steps results"""
        self.step_1 = fc.INPUT_MISSING
        self.step_2 = fc.INPUT_MISSING
        self.step_3 = fc.INPUT_MISSING
        self.step_4 = fc.INPUT_MISSING
        self.step_5 = fc.INPUT_MISSING
        self.step_6 = fc.INPUT_MISSING
        self.step_7 = fc.INPUT_MISSING
        self.step_8 = fc.INPUT_MISSING

    def check_result(self):
        """
        The function `check_result` checks the status of multiple steps and returns a corresponding result and color code.
        :return: The `check_result` method is returning a tuple with two values. The first value is one of the constants
        `fc.PASS`, `fc.INPUT_MISSING`, `fc.NOT_ASSESSED`, or `fc.FAIL` based on the conditions checked in the method. The
        second value is a color code represented as a string.
        """
        if (
            self.step_1 == fc.PASS
            and self.step_2 == fc.PASS
            and self.step_3 == fc.PASS
            and self.step_4 == fc.PASS
            and self.step_5 == fc.PASS
            and self.step_6 == fc.PASS
            and self.step_7 == fc.PASS
            and self.step_8 == fc.PASS
        ):
            return fc.PASS, "#28a745"
        elif (
            self.step_1 == fc.INPUT_MISSING
            or self.step_2 == fc.INPUT_MISSING
            or self.step_3 == fc.INPUT_MISSING
            or self.step_4 == fc.INPUT_MISSING
            or self.step_5 == fc.INPUT_MISSING
            or self.step_6 == fc.INPUT_MISSING
            or self.step_7 == fc.INPUT_MISSING
            or self.step_8 == fc.INPUT_MISSING
        ):
            return fc.INPUT_MISSING, "rgb(33,39,43)"
        elif (
            self.step_1 == fc.NOT_ASSESSED
            or self.step_2 == fc.NOT_ASSESSED
            or self.step_3 == fc.NOT_ASSESSED
            or self.step_4 == fc.NOT_ASSESSED
            or self.step_5 == fc.NOT_ASSESSED
            or self.step_6 == fc.NOT_ASSESSED
            or self.step_7 == fc.NOT_ASSESSED
            or self.step_8 == fc.NOT_ASSESSED
        ):
            return fc.NOT_ASSESSED, "rgb(129, 133, 137)"
        else:
            # self.case_result == fc.FAIL
            return fc.FAIL, "#dc3545"


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        sg_time = "TimeStamp"
        NUMBER_OF_POINTS = "Number Of Points"
        NUMBER_OF_ECHOS = "Number Of Echos"
        NUMBER_OF_LINES_FC = "Number Of Lines FC"
        NUMBER_OF_LINES_LSC = "Number Of Lines LSC"
        NUMBER_OF_LINES_RC = "Number Of Lines RC"
        NUMBER_OF_LINES_RSC = "Number Of Lines RSC"

        NUMBER_OF_DELIMITERS = "Number Of Delimiters"
        NUMBER_OF_SLOTS = "Number Of Slots"
        NUMBER_OF_OBJECTS = "Number Of Objects"
        NUMBER_OF_PARKMARK = "Number Of Parking Marks"
        NUMBER_OF_STATOBJ = "Number Of Static Objects"
        NUMBER_OF_VALID_PB = "Number Of Valid Parking Boxes"
        NUMBER_OF_VALID_POSES = "Number Of Valid Poses"
        SELECTED_PB_ID = "SelectedPB-ID"
        SCREEN_NU = "Screen_nu"
        PARK_SPACES = "Park_spaces"
        VELOCITY = "Velocity"
        HMI_PS_RIGHT_0 = "parkingSpaces.right.scanned_0"
        HMI_PS_RIGHT_1 = "parkingSpaces.right.scanned_1"
        HMI_PS_RIGHT_2 = "parkingSpaces.right.scanned_2"
        HMI_PS_RIGHT_3 = "parkingSpaces.right.scanned_3"
        HMI_PS_LEFT_0 = "parkingSpaces.left.scanned_0"
        HMI_PS_LEFT_1 = "parkingSpaces.left.scanned_1"
        HMI_PS_LEFT_2 = "parkingSpaces.left.scanned_2"
        HMI_PS_LEFT_3 = "parkingSpaces.left.scanned_3"
        PATH_FOUND = "Any Path Found"
        FAIL_REASON = "Fail Reason"
        sg_time_m7 = "TimeStamp_M7"
        SOFTWARE_MAJOR = "SOFTWARE_MAJOR"
        SOFTWARE_MINOR = "SOFTWARE_MINOR"
        SOFTWARE_PATCH = "SOFTWARE_PATCH"
        CORE_STATE = "MTA_ADC5.MF_PARKSM_CORE_DATA.parksmCoreStatusPort.parksmCoreState_nu"
        CORE_STOP_REASON = "MTA_ADC5.MF_PARKSM_CORE_DATA.parksmCoreStatusPort.coreStopReason_nu"
        CORE_READY = "MTA_ADC5.MF_PARKSM_CORE_DATA.parksmCoreStatusPort.parkingReady_nu"
        CORE_EM_BRAKE_REQ = "MTA_ADC5.MF_PARKSM_CORE_DATA.trajCtrlRequestPort.emergencyBrakeRequest"
        TRJPLA_FAILREASON = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.failReason"
        TRJPLA_ANYPATH = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.anyPathFound"
        TRJPLA_NUM_VALID_POSES = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.numValidPoses"
        TRJPLA_POSEFAIL_REASON_0 = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[0].poseFailReason"
        TRJPLA_POSEFAIL_REASON_1 = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[1].poseFailReason"
        TRJPLA_POSEFAIL_REASON_2 = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[2].poseFailReason"
        TRJPLA_POSEFAIL_REASON_3 = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[3].poseFailReason"
        TRJPLA_POSEFAIL_REASON_4 = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[4].poseFailReason"
        TRJPLA_POSEFAIL_REASON_5 = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[5].poseFailReason"
        TRJPLA_POSEFAIL_REASON_6 = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[6].poseFailReason"
        TRJPLA_POSEFAIL_REASON_7 = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[7].poseFailReason"
        TRJPLA_POSE_REACHABLE_0 = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[0].reachableStatus"
        TRJPLA_POSE_REACHABLE_1 = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[1].reachableStatus"
        TRJPLA_POSE_REACHABLE_2 = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[2].reachableStatus"
        TRJPLA_POSE_REACHABLE_3 = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[3].reachableStatus"
        TRJPLA_POSE_REACHABLE_4 = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[4].reachableStatus"
        TRJPLA_POSE_REACHABLE_5 = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[5].reachableStatus"
        TRJPLA_POSE_REACHABLE_6 = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[6].reachableStatus"
        TRJPLA_POSE_REACHABLE_7 = "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[7].reachableStatus"
        TRJPLA_TRAJPLAN_STATE = "MTA_ADC5.MF_TRJPLA_DATA.trjplaDebugPort.mTrajPlanState"
        TRJPLA_NUM_OF_REPLAN_CALLS = "MTA_ADC5.MF_TRJPLA_DATA.trjplaDebugPort.mNumOfReplanCalls"
        TRJPLA_REPLAN_SUCCESSFUL = "MTA_ADC5.MF_TRJPLA_DATA.trjplaDebugPort.mReplanSuccessful_nu"
        PLANNED_TRAJ_TYPE = "MTA_ADC5.MF_TRJPLA_DATA.plannedTrajectory.trajType_nu"
        PLANNED_TRAJ_DRIVING_FORWARD_REQ = "MTA_ADC5.MF_TRJPLA_DATA.plannedTrajectory.drivingForwardReq_nu"
        PLANNED_TRAJ_VALID = "MTA_ADC5.MF_TRJPLA_DATA.plannedTrajectory.trajValid_nu"
        PLANNED_TRAJ_NEW_SEGMENT_STARTED = "MTA_ADC5.MF_TRJPLA_DATA.plannedTrajectory.newSegmentStarted_nu"
        PLANNED_TRAJ_IS_LAST_SEGMENT = "MTA_ADC5.MF_TRJPLA_DATA.plannedTrajectory.isLastSegment_nu"
        MOCO_LODMC_SECURE = "MTA_ADC5.MF_TRJCTL_DATA.LoDMCCtrlRequestPort.secureReq_nu"
        MOCO_LODMC_DRIVING_FORWARD_REQ = "MTA_ADC5.MF_TRJCTL_DATA.LoDMCCtrlRequestPort.drivingForwardReq_nu"
        MOCO_LODMC_TRAJECTORY_RESET = "MTA_ADC5.MF_TRJCTL_DATA.LoDMCCtrlRequestPort.trajectoryReset_nu"
        MOCO_LODMC_DIST2STOP = "MTA_ADC5.MF_TRJCTL_DATA.LoDMCCtrlRequestPort.distanceToStopReq_m"
        MOCO_LODMC_VELOCITY_LIMIT = "MTA_ADC5.MF_TRJCTL_DATA.LoDMCCtrlRequestPort.velocityLimitReq_mps"
        MOCO_LODMC_ACCELERATION = "MTA_ADC5.MF_TRJCTL_DATA.LoDMCCtrlRequestPort.accelerationReq_mps2"
        MOCO_LODMC_REQUEST_SOURCE = "MTA_ADC5.MF_TRJCTL_DATA.LoDMCCtrlRequestPort.loDMCCtrlRequestSource_nu"
        MOCO_LODMC_REQUEST_INTERFACE = "MTA_ADC5.MF_TRJCTL_DATA.LoDMCCtrlRequestPort.loDMCCtrlRequestInterface_nu"
        MOCO_LODMC_REQUEST = "MTA_ADC5.MF_TRJCTL_DATA.LoDMCCtrlRequestPort.loDMCCtrlRequest_nu"
        MOCO_LODMC_HOLD_REQ = "MTA_ADC5.MF_TRJCTL_DATA.LoDMCCtrlRequestPort.holdReq_nu"
        MOCO_LODMC_EMERGENCY_HOLD_REQ = "MTA_ADC5.MF_TRJCTL_DATA.LoDMCCtrlRequestPort.emergencyHoldReq_nu"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["ADC5xx_Device", "ADAS_CAN", "MTA_ADC5", "AP_Conti_CAN"]

        self._properties = {
            self.Columns.NUMBER_OF_POINTS: [
                ".USP_DATA.SpuUsProcessingPointListOutput.numberOfPoints",
                ".US_PROCESSING_DATA.UsProcessingPointListOutput.numberOfPoints",
            ],
            self.Columns.NUMBER_OF_ECHOS: [
                ".USP_DATA.SpuUsProcessingEchoOutput.numEchoes",
                ".US_PROCESSING_DATA.UsProcessingEchoOutput.numEchoes",
            ],
            self.Columns.NUMBER_OF_LINES_FC: [
                ".PMSD_FC_DATA.PmsdParkingLinesOutputFc.numberOfLines",
                ".PMSD_FC_DATA.ParkingLines.numberOfLines",
            ],
            self.Columns.NUMBER_OF_LINES_LSC: [
                ".PMSD_LSC_DATA.PmsdParkingLinesOutputLsc.numberOfLines",
                ".PMSD_LSC_DATA.ParkingLines.numberOfLines",
            ],
            self.Columns.NUMBER_OF_LINES_RC: [
                ".PMSD_RC_DATA.PmsdParkingLinesOutputRc.numberOfLines",
                ".PMSD_RC_DATA.ParkingLines.numberOfLines",
            ],
            self.Columns.NUMBER_OF_LINES_RSC: [
                ".PMSD_RSC_DATA.PmsdParkingLinesOutputRsc.numberOfLines",
                ".PMSD_RSC_DATA.ParkingLines.numberOfLines",
            ],
            self.Columns.NUMBER_OF_DELIMITERS: [
                ".CEM_EM_DATA.AUPDF_ParkingDelimiters.numberOfDelimiters",
                # ".CEM200_AUPDF_DATA.ParkingDelimiters.numberOfDelimiters",
                "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.numberOfDelimiters",
            ],
            self.Columns.NUMBER_OF_SLOTS: [
                ".CEM_EM_DATA.AUPDF_ParkingSlots.numberOfSlots",
                # ".CEM200_AUPDF_DATA.ParkingSlots.numberOfSlots",
                "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.numberOfSlots",
            ],
            self.Columns.NUMBER_OF_OBJECTS: [
                ".CEM_EM_DATA.AUPDF_DynamicObjects.numberOfObjects",
                # ".CEM200_AUPDF_DATA.DynamicObjects.numberOfObjects",
                "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.numberOfObjects",

            ],
            self.Columns.NUMBER_OF_PARKMARK: [
                ".EM_DATA.EmApEnvModelPort.numberOfParkMarkings_u8",
                ".SI_DATA.m_environmentModelPort.numberOfParkMarkings_u8",
            ],
            self.Columns.NUMBER_OF_STATOBJ: [
                ".EM_DATA.EmApEnvModelPort.numberOfStaticObjects_u8",
                ".SI_DATA.m_environmentModelPort.numberOfStaticObjects_u8",
            ],
            self.Columns.NUMBER_OF_VALID_PB: [
                ".EM_DATA.EmApParkingBoxPort.numValidParkingBoxes_nu",
                ".SI_DATA.m_parkingBoxesPort.numValidParkingBoxes_nu",
            ],
            self.Columns.NUMBER_OF_VALID_POSES: [
                ".TRJPLA_DATA.TrjPlaTargetPosesPort.numValidPoses",
                ".MF_TRJPLA_DATA.targetPoses.numValidPoses",
            ],
            self.Columns.SELECTED_PB_ID: [
                ".EM_DATA.EmSlotCtrlPort.selectedParkingBoxId_nu",
                ".MF_PARKSM_CORE_DATA.slotCtrlPort.selectedParkingBoxId_nu",
            ],
            self.Columns.SCREEN_NU: [
                ".EM_DATA.EmHeadUnitVisualizationPort.screen_nu",
                "MTA_ADC5.APPDEMO_HMIH_DATA.headUnitVisualizationPort.screen_nu",
            ],
            self.Columns.sg_time_m7: [
                ".USP_DATA.SpuOdoEstimationOutputPort.sSigHeader.uiTimeStamp",
                "MTA_ADC5.APPDEMO_HMIH_DATA.headUnitVisualizationPort.sSigHeader.uiTimeStamp",
            ],
            self.Columns.VELOCITY: [
                "Reference_RT3000_Ethernet.Hunter.VelocityVehicle.LongitudinalVelocity_kph",
                ".Conti_Veh_CAN.VehVelocity.VehVelocityExt",
                "AP_Conti_CAN.AP_Conti_CAN_1_0_10.VehVelocity.VehVelocityExt",
            ],
            self.Columns.HMI_PS_RIGHT_0: [
                ".EM_DATA.EmHMIGeneralInputPort.parkingSpaces.right.scanned_nu[0]",
                "MTA_ADC5.APPDEMO_HMIH_DATA.hmiInputPort.parkingSpaces.right.scanned_nu[0]",
            ],
            self.Columns.HMI_PS_RIGHT_1: [
                ".EM_DATA.EmHMIGeneralInputPort.parkingSpaces.right.scanned_nu[1]",
                "MTA_ADC5.APPDEMO_HMIH_DATA.hmiInputPort.parkingSpaces.right.scanned_nu[1]",
            ],
            self.Columns.HMI_PS_RIGHT_2: [
                ".EM_DATA.EmHMIGeneralInputPort.parkingSpaces.right.scanned_nu[2]",
                "MTA_ADC5.APPDEMO_HMIH_DATA.hmiInputPort.parkingSpaces.right.scanned_nu[2]",
            ],
            self.Columns.HMI_PS_RIGHT_3: [
                ".EM_DATA.EmHMIGeneralInputPort.parkingSpaces.right.scanned_nu[3]",
                "MTA_ADC5.APPDEMO_HMIH_DATA.hmiInputPort.parkingSpaces.right.scanned_nu[3]",
            ],
            self.Columns.HMI_PS_LEFT_0: [
                ".EM_DATA.EmHMIGeneralInputPort.parkingSpaces.left.scanned_nu[0]",
                "MTA_ADC5.APPDEMO_HMIH_DATA.hmiInputPort.parkingSpaces.left.scanned_nu[0]",
            ],
            self.Columns.HMI_PS_LEFT_1: [
                ".EM_DATA.EmHMIGeneralInputPort.parkingSpaces.left.scanned_nu[1]",
                "MTA_ADC5.APPDEMO_HMIH_DATA.hmiInputPort.parkingSpaces.left.scanned_nu[1]",
            ],
            self.Columns.HMI_PS_LEFT_2: [
                ".EM_DATA.EmHMIGeneralInputPort.parkingSpaces.left.scanned_nu[2]",
                "MTA_ADC5.APPDEMO_HMIH_DATA.hmiInputPort.parkingSpaces.left.scanned_nu[2]",
            ],
            self.Columns.HMI_PS_LEFT_3: [
                ".EM_DATA.EmHMIGeneralInputPort.parkingSpaces.left.scanned_nu[3]",
                "MTA_ADC5.APPDEMO_HMIH_DATA.hmiInputPort.parkingSpaces.left.scanned_nu[3]",
            ],
            self.Columns.PATH_FOUND: [
                ".TRJPLA_DATA.TrjPlaTargetPosesPort.anyPathFound",
                ".MF_TRJPLA_DATA.targetPoses.anyPathFound",
            ],
            self.Columns.FAIL_REASON: [
                ".TRJPLA_DATA.TrjPlaTargetPosesPort.failReason",
                ".MF_TRJPLA_DATA.targetPoses.failReason",
            ],
            self.Columns.CORE_STATE: "MTA_ADC5.MF_PARKSM_CORE_DATA.parksmCoreStatusPort.parksmCoreState_nu",
            self.Columns.CORE_STOP_REASON: "MTA_ADC5.MF_PARKSM_CORE_DATA.parksmCoreStatusPort.coreStopReason_nu",
            self.Columns.CORE_READY: "MTA_ADC5.MF_PARKSM_CORE_DATA.parksmCoreStatusPort.parkingReady_nu",
            self.Columns.CORE_EM_BRAKE_REQ: "MTA_ADC5.MF_PARKSM_CORE_DATA.trajCtrlRequestPort.emergencyBrakeRequest",
            self.Columns.TRJPLA_POSEFAIL_REASON_0: "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[0].poseFailReason",
            self.Columns.TRJPLA_POSEFAIL_REASON_1: "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[1].poseFailReason",
            self.Columns.TRJPLA_POSEFAIL_REASON_2: "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[2].poseFailReason",
            self.Columns.TRJPLA_POSEFAIL_REASON_3: "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[3].poseFailReason",
            self.Columns.TRJPLA_POSEFAIL_REASON_4: "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[4].poseFailReason",
            self.Columns.TRJPLA_POSEFAIL_REASON_5: "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[5].poseFailReason",
            self.Columns.TRJPLA_POSEFAIL_REASON_6: "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[6].poseFailReason",
            self.Columns.TRJPLA_POSEFAIL_REASON_7: "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[7].poseFailReason",
            self.Columns.TRJPLA_POSE_REACHABLE_0: "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[0].reachableStatus",
            self.Columns.TRJPLA_POSE_REACHABLE_1: "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[1].reachableStatus",
            self.Columns.TRJPLA_POSE_REACHABLE_2: "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[2].reachableStatus",
            self.Columns.TRJPLA_POSE_REACHABLE_3: "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[3].reachableStatus",
            self.Columns.TRJPLA_POSE_REACHABLE_4: "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[4].reachableStatus",
            self.Columns.TRJPLA_POSE_REACHABLE_5: "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[5].reachableStatus",
            self.Columns.TRJPLA_POSE_REACHABLE_6: "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[6].reachableStatus",
        }


signals_obj = Signals()
verdict_obj = StoreStepResults()


@teststep_definition(
    step_number=1,
    name="VEDODO",
    description="Verify that vehicle velocity[km/h] has values greater than 0 in manuever phase.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class VEDODO_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_1 = fc.INPUT_MISSING

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}

            df = self.readers[EXAMPLE]  # for rrec
            try:
                df[Signals.Columns.TIMESTAMP] = df.index
            except Exception as err:
                print(str(err))

            # Converting microseconds to seconds
            df[Signals.Columns.TIMESTAMP] = df[Signals.Columns.TIMESTAMP] / constants.GeneralConstants.US_IN_S
            # Converting epoch time to seconds passed
            df[Signals.Columns.TIMESTAMP] = df[Signals.Columns.TIMESTAMP] - df[Signals.Columns.TIMESTAMP].iat[0]
            global time
            time = df[Signals.Columns.TIMESTAMP]

            velocity = df[Signals.Columns.VELOCITY]
            screen_nu = df[Signals.Columns.SCREEN_NU]

            evaluation1 = " ".join(
                f"The evaluation of {Signals.Columns.VELOCITY} is FAILED because has only values"
                f"  <= {0} during manuever phase.".split()
            )
            for idx, val in enumerate(df[Signals.Columns.SCREEN_NU]):
                if val != constants.RootCauseAnalysis.MANEUVER_FINISHED:
                    t2 = idx
                    break
            if t2 is not None:
                eval_cond = [False]

                for idx in range(t2, len(df[Signals.Columns.SCREEN_NU])):
                    if df[Signals.Columns.SCREEN_NU].iloc[idx] == constants.RootCauseAnalysis.MANEUVER_ACTIVE:
                        if df[Signals.Columns.VELOCITY].iloc[idx] > 0:
                            evaluation1 = " ".join(
                                f"The evaluation of {Signals.Columns.VELOCITY} is PASSED with values > than"
                                f" {0} during manuever phase .".split()
                            )
                            eval_cond[0] = True

                    if all(eval_cond):
                        self.result.measured_result = TRUE
                        verdict_obj.step_1 = fc.PASS
                        self.result.details["root_cause_text"] = "passed"
                    else:
                        self.result.measured_result = FALSE
                        verdict_obj.step_1 = fc.FAIL
                        self.result.details["root_cause_text"] = "failed"
            else:
                evaluation1 = "Trigger not found!"
                self.result.measured_result = DATA_NOK
                verdict_obj.step_1 = fc.NOT_ASSESSED

            signal_summary["Vehicle velocity [kph]"] = evaluation1
            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")

            df["status"] = screen_nu.apply(lambda x: fh.get_status_label(x, constants.RootCauseAnalysis))

            self.fig = go.Figure()
            self.fig.add_trace(go.Scatter(x=time, y=velocity, mode="lines", name=Signals.Columns.VELOCITY))
            self.fig.add_trace(
                go.Scatter(
                    x=time,
                    y=screen_nu,
                    mode="lines",
                    name=Signals.Columns.SCREEN_NU,
                    visible="legendonly",
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=df["status"],
                )
            )

            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.SCANNING_ACTIVE, time, "LightSalmon", " "
            )

            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.MANEUVER_ACTIVE, time, "RoyalBlue", " "
            )

            self.fig.update_layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=2,
    name="US",
    description="Verify that number of points and echos detected by ultrasonic sensor has values greater than 0 until manuever finished.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class US_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:
            script_directory = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(script_directory, "UseCases.json")
            usecases_file = open(json_path)
            usecases_data = json.load(usecases_file)

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_2 = fc.INPUT_MISSING

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}
            usecase_const = True
            # try to find if measurement name contain use case
            for _, data in enumerate(usecases_data):
                if self.result.details["file_name"].find(data["Use_Case"]) != -1:
                    if not data["USS"].isalnum():
                        usecase_const = False

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            num_of_point = df[Signals.Columns.NUMBER_OF_POINTS]
            num_of_echos = df[Signals.Columns.NUMBER_OF_ECHOS]
            screen_nu = df[Signals.Columns.SCREEN_NU]

            evaluation1 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_POINTS} is FAILED because the values"
                f" are <= 0 until manuever finished.".split()
            )
            evaluation2 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_ECHOS} is FAILED because the values"
                f" are <= 0 until manuever finished.".split()
            )

            for idx, val in enumerate(df[Signals.Columns.SCREEN_NU]):
                if val != 5:
                    t2 = idx
                    break
            if t2 is not None:
                eval_cond = [False] * 2

                for idx in range(t2, len(df[Signals.Columns.SCREEN_NU])):
                    if df[Signals.Columns.SCREEN_NU].iloc[idx] != constants.RootCauseAnalysis.MANEUVER_FINISHED:
                        if df[Signals.Columns.NUMBER_OF_POINTS].iloc[idx] > 0:
                            evaluation1 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_POINTS} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[0] = True

                        if df[Signals.Columns.NUMBER_OF_ECHOS].iloc[idx] > 0:

                            evaluation2 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_ECHOS} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[1] = True
                    if usecase_const:
                        if all(eval_cond):
                            self.result.measured_result = TRUE
                            verdict_obj.step_2 = fc.PASS
                            self.result.details["root_cause_text"] = "passed"
                        else:
                            self.result.measured_result = FALSE
                            verdict_obj.step_2 = fc.FAIL
                            self.result.details["root_cause_text"] = "failed"
                    else:
                        evaluation1 = evaluation2 = "USS component is not evaluated for this measurement"
            else:
                evaluation1 = evaluation2 = "Trigger not found!"
                self.result.measured_result = DATA_NOK
                verdict_obj.step_2 = fc.NOT_ASSESSED
                self.result.details["root_cause_text"] = "not assessed"

            signal_summary["Number of points detected by ultrasonic sensors"] = evaluation1
            signal_summary["Number of echoes detected by ultrasonic sensors"] = evaluation2
            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")
            df["status"] = screen_nu.apply(lambda x: fh.get_status_label(x, constants.RootCauseAnalysis))

            self.fig = go.Figure()
            self.fig.add_trace(go.Scatter(x=time, y=num_of_point, mode="lines", name=Signals.Columns.NUMBER_OF_POINTS))
            self.fig.add_trace(go.Scatter(x=time, y=num_of_echos, mode="lines", name=Signals.Columns.NUMBER_OF_ECHOS))
            self.fig.add_trace(
                go.Scatter(
                    x=time,
                    y=screen_nu,
                    mode="lines",
                    name=Signals.Columns.SCREEN_NU,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    visible="legendonly",
                    text=df["status"],
                )
            )

            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.SCANNING_ACTIVE, time, "LightSalmon", " "
            )
            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.MANEUVER_ACTIVE, time, "RoyalBlue", " "
            )

            self.fig.update_layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=3,
    name="PMSD",
    description="Verify that number of parking lines detected by cameras has values greater than 0 until manuever finished.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class PMSD_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:
            script_directory = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(script_directory, "UseCases.json")
            usecases_file = open(json_path)
            usecases_data = json.load(usecases_file)
            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_3 = fc.INPUT_MISSING

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}
            usecase_const = True
            # try to find if measurement name contain use case
            for _, data in enumerate(usecases_data):
                if self.result.details["file_name"].find(data["Use_Case"]) != -1:
                    if not data["PMSD"].isalnum():
                        usecase_const = False

            usecases_file.close()

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            lines_fc = df[Signals.Columns.NUMBER_OF_LINES_FC]
            lines_lsc = df[Signals.Columns.NUMBER_OF_LINES_LSC]
            lines_rc = df[Signals.Columns.NUMBER_OF_LINES_RC]
            lines_rsc = df[Signals.Columns.NUMBER_OF_LINES_RSC]
            screen_nu = df[Signals.Columns.SCREEN_NU]

            evaluation1 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_LINES_FC} is FAILED because the values"
                f" are <= 0 until manuever finished.".split()
            )

            evaluation2 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_LINES_LSC} is FAILED because the values"
                f" are <= 0 until manuever finished.".split()
            )

            evaluation3 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_LINES_RC} is FAILED because the values"
                f" are <= 0 until manuever finished.".split()
            )

            evaluation4 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_LINES_RSC} is FAILED because the values"
                f" are <= 0 until manuever finished.".split()
            )

            for idx, val in enumerate(df[Signals.Columns.SCREEN_NU]):
                if val != constants.RootCauseAnalysis.MANEUVER_FINISHED:
                    t2 = idx
                    break
            if t2 is not None:
                eval_cond = [False] * 4

                for idx in range(t2, len(df[Signals.Columns.SCREEN_NU])):
                    if df[Signals.Columns.SCREEN_NU].iloc[idx] != constants.RootCauseAnalysis.MANEUVER_FINISHED:
                        if df[Signals.Columns.NUMBER_OF_LINES_FC].iloc[idx] > 0:
                            evaluation1 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_LINES_FC} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[0] = True

                        if df[Signals.Columns.NUMBER_OF_LINES_LSC].iloc[idx] > 0:
                            evaluation2 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_LINES_LSC} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[1] = True
                        if df[Signals.Columns.NUMBER_OF_LINES_RC].iloc[idx] > 0:
                            evaluation3 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_LINES_RC} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[2] = True

                        if df[Signals.Columns.NUMBER_OF_LINES_RSC].iloc[idx] > 0:
                            evaluation4 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_LINES_RSC} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[3] = True
                    if usecase_const:
                        if all(eval_cond):
                            self.result.measured_result = TRUE
                            verdict_obj.step_3 = fc.PASS
                            self.result.details["root_cause_text"] = "passed"
                        else:
                            self.result.measured_result = FALSE
                            verdict_obj.step_3 = fc.FAIL
                            self.result.details["root_cause_text"] = "failed"
                    else:
                        evaluation1 = evaluation2 = evaluation3 = evaluation4 = (
                            "PMSD component is not evaluated for this measurement."
                        )
            else:
                evaluation1 = evaluation2 = evaluation3 = evaluation4 = "Trigger not found!"
                self.result.measured_result = DATA_NOK
                verdict_obj.step_3 = fc.NOT_ASSESSED
                self.result.details["root_cause_text"] = "not assessed"

            signal_summary["Number of parking lines detected by front camera"] = evaluation1
            signal_summary["Number of parking lines detected by left camera"] = evaluation2
            signal_summary["Number of parking lines detected by rear camera"] = evaluation3
            signal_summary["Number of parking lines detected by right camera"] = evaluation4
            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")
            df["status"] = screen_nu.apply(lambda x: fh.get_status_label(x, constants.RootCauseAnalysis))

            self.fig = go.Figure()
            self.fig.add_trace(go.Scatter(x=time, y=lines_fc, mode="lines", name=Signals.Columns.NUMBER_OF_LINES_FC))
            self.fig.add_trace(go.Scatter(x=time, y=lines_lsc, mode="lines", name=Signals.Columns.NUMBER_OF_LINES_LSC))
            self.fig.add_trace(go.Scatter(x=time, y=lines_rc, mode="lines", name=Signals.Columns.NUMBER_OF_LINES_RC))
            self.fig.add_trace(go.Scatter(x=time, y=lines_rsc, mode="lines", name=Signals.Columns.NUMBER_OF_LINES_RSC))
            self.fig.add_trace(
                go.Scatter(
                    x=time,
                    y=screen_nu,
                    mode="lines",
                    name=Signals.Columns.SCREEN_NU,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    visible="legendonly",
                    text=df["status"],
                )
            )

            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.SCANNING_ACTIVE, time, "LightSalmon", " "
            )
            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.MANEUVER_ACTIVE, time, "RoyalBlue", " "
            )

            self.fig.update_layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=4,
    name="CEM",
    description="Verify that number of parking slot delimiters and of fusion objects has values greater than 0 until manuever finished.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class CEM_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_4 = fc.INPUT_MISSING

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            num_delim = df[Signals.Columns.NUMBER_OF_DELIMITERS]
            num_obj = df[Signals.Columns.NUMBER_OF_OBJECTS]
            screen_nu = df[Signals.Columns.SCREEN_NU]

            evaluation1 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_DELIMITERS} is FAILED because the values"
                f" are <= 0 until manuever finished.".split()
            )

            evaluation2 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_OBJECTS} is FAILED because the values"
                f" are <= 0 until manuever finished.".split()
            )

            for idx, val in enumerate(df[Signals.Columns.SCREEN_NU]):
                if val != constants.RootCauseAnalysis.MANEUVER_FINISHED:
                    t2 = idx
                    break
            if t2 is not None:
                eval_cond = [False] * 2

                for idx in range(t2, len(df[Signals.Columns.SCREEN_NU])):
                    if df[Signals.Columns.SCREEN_NU].iloc[idx] != constants.RootCauseAnalysis.MANEUVER_FINISHED:
                        if num_delim.iloc[idx] > 0:
                            evaluation1 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_DELIMITERS} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[0] = True

                        if num_obj.iloc[idx] > 0:
                            evaluation2 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_OBJECTS} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[1] = True

                    if all(eval_cond):
                        self.result.measured_result = TRUE
                        verdict_obj.step_4 = fc.PASS
                        self.result.details["root_cause_text"] = "passed"
                    else:
                        self.result.measured_result = FALSE
                        verdict_obj.step_4 = fc.FAIL
                        self.result.details["root_cause_text"] = "failed"
            else:
                evaluation1 = evaluation2 = "Trigger not found!"
                self.result.measured_result = DATA_NOK
                verdict_obj.step_4 = fc.NOT_ASSESSED
                self.result.details["root_cause_text"] = "not assessed"

            signal_summary["Number of parking slot delimeters"] = evaluation1
            signal_summary["Number of fusion objects"] = evaluation2
            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")
            df["status"] = screen_nu.apply(lambda x: fh.get_status_label(x, constants.RootCauseAnalysis))

            self.fig = go.Figure()
            self.fig.add_trace(go.Scatter(x=time, y=num_delim, mode="lines", name=Signals.Columns.NUMBER_OF_DELIMITERS))
            self.fig.add_trace(go.Scatter(x=time, y=num_obj, mode="lines", name=Signals.Columns.NUMBER_OF_OBJECTS))
            # self.fig.add_trace(
            #     go.Scatter(
            #         x=time,
            #         y=screen_nu,
            #         mode="lines",
            #         hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
            #         name=Signals.Columns.SCREEN_NU,
            #     ),
            #     text=df["status"],
            # )
            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.SCANNING_ACTIVE, time, "LightSalmon", "SCANNING_ACTIVE"
            )
            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.MANEUVER_ACTIVE, time, "RoyalBlue", " "
            )
            self.fig.update_layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=constants.RootCauseAnalysis.MANEUVER_FINISHED,
    name="SI",
    description="Verify that number of parking markings, of static objects and of valid parking boxes has values greater than 0 until manuever finished.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class SI_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:
            script_directory = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(script_directory, "UseCases.json")
            usecases_file = open(json_path)
            usecases_data = json.load(usecases_file)
            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_5 = fc.INPUT_MISSING

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}
            usecase_const_uss = True
            usecase_const_pmsd = True

            # try to find if measurement name contain use case
            for _, data in enumerate(usecases_data):
                if self.result.details["file_name"].find(data["Use_Case"]) != -1:
                    if not data["USS"].isalnum():
                        usecase_const_uss = False
                    if not data["PMSD"].isalnum():
                        usecase_const_pmsd = False

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            num_of_parkmark = df[Signals.Columns.NUMBER_OF_PARKMARK]
            num_of_statobj = df[Signals.Columns.NUMBER_OF_STATOBJ]
            num_of_validpb = df[Signals.Columns.NUMBER_OF_VALID_PB]
            screen_nu = df[Signals.Columns.SCREEN_NU]
            eval_cond = [False] * 3

            if usecase_const_pmsd:
                evaluation1 = " ".join(
                    f"The evaluation of {Signals.Columns.NUMBER_OF_PARKMARK} is FAILED because the values"
                    f" are <= 0 until manuever finished.".split()
                )
            else:
                evaluation1 = "PMSD component is not evaluated for this measurement."
                eval_cond[0] = [True]

            if usecase_const_uss:
                evaluation2 = " ".join(
                    f"The evaluation of {Signals.Columns.NUMBER_OF_STATOBJ} is FAILED because the values"
                    f" are <= 0 until manuever finished.".split()
                )
            else:
                evaluation2 = "USS component is not evaluated for this measurement."
                eval_cond[1] = [True]

            evaluation3 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_VALID_PB} is FAILED because the values"
                f" are <= 0 until manuever finished.".split()
            )

            for idx, val in enumerate(df[Signals.Columns.SCREEN_NU]):
                if val != constants.RootCauseAnalysis.MANEUVER_FINISHED:
                    t2 = idx
                    break
            if t2 is not None:

                for idx in range(t2, len(df[Signals.Columns.SCREEN_NU])):
                    if df[Signals.Columns.SCREEN_NU].iloc[idx] != constants.RootCauseAnalysis.MANEUVER_FINISHED:
                        if usecase_const_pmsd:
                            if df[Signals.Columns.NUMBER_OF_PARKMARK].iloc[idx] > 0:
                                evaluation1 = " ".join(
                                    f"The evaluation of {Signals.Columns.NUMBER_OF_PARKMARK} is PASSED with values > than"
                                    f" {0} .".split()
                                )
                                eval_cond[0] = True

                        if usecase_const_uss:
                            if df[Signals.Columns.NUMBER_OF_STATOBJ].iloc[idx] > 0:
                                evaluation2 = " ".join(
                                    f"The evaluation of {Signals.Columns.NUMBER_OF_STATOBJ} is PASSED with values > than"
                                    f" {0} .".split()
                                )
                                eval_cond[1] = True

                        if df[Signals.Columns.NUMBER_OF_VALID_PB].iloc[idx] > 0:
                            evaluation3 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_VALID_PB} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[2] = True
                    if all(eval_cond):
                        self.result.measured_result = TRUE
                        verdict_obj.step_5 = fc.PASS
                        self.result.details["root_cause_text"] = "passed"
                    else:
                        self.result.measured_result = FALSE
                        verdict_obj.step_5 = fc.FAIL
                        self.result.details["root_cause_text"] = "failed"
            else:
                evaluation1 = evaluation2 = evaluation3 = "Trigger not found!"
                self.result.measured_result = DATA_NOK
                verdict_obj.step_5 = fc.NOT_ASSESSED
                self.result.details["root_cause_text"] = "not assessed"

            signal_summary["Number of parking markings"] = evaluation1
            signal_summary["Number of static objects"] = evaluation2
            signal_summary["Number of valid parking boxes"] = evaluation3

            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")
            df["status"] = screen_nu.apply(lambda x: fh.get_status_label(x, constants.RootCauseAnalysis))

            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(x=time, y=num_of_parkmark, mode="lines", name=Signals.Columns.NUMBER_OF_PARKMARK)
            )
            self.fig.add_trace(
                go.Scatter(x=time, y=num_of_statobj, mode="lines", name=Signals.Columns.NUMBER_OF_STATOBJ)
            )
            self.fig.add_trace(
                go.Scatter(x=time, y=num_of_validpb, mode="lines", name=Signals.Columns.NUMBER_OF_VALID_PB)
            )
            self.fig.add_trace(
                go.Scatter(
                    x=time,
                    y=screen_nu,
                    mode="lines",
                    name=Signals.Columns.SCREEN_NU,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    visible="legendonly",
                    text=df["status"],
                )
            )

            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.SCANNING_ACTIVE, time, "LightSalmon", " "
            )
            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.MANEUVER_ACTIVE, time, "RoyalBlue", " "
            )
            self.fig.update_layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=6,
    name="TRJPLA",
    description="Verify that trajectory was successfully planned.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class TRJPLA_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_6 = fc.INPUT_MISSING

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            screen_nu = df[Signals.Columns.SCREEN_NU]
            path_found = df[Signals.Columns.PATH_FOUND]
            fail_reason = df[Signals.Columns.FAIL_REASON]
            core_state = df[Signals.Columns.CORE_STATE]
            TRJPLA_POSEFAIL_REASON = [
                Signals.Columns.TRJPLA_POSEFAIL_REASON_0,
                Signals.Columns.TRJPLA_POSEFAIL_REASON_1,
                Signals.Columns.TRJPLA_POSEFAIL_REASON_2,
                Signals.Columns.TRJPLA_POSEFAIL_REASON_3,
                Signals.Columns.TRJPLA_POSEFAIL_REASON_4,
                Signals.Columns.TRJPLA_POSEFAIL_REASON_5,
                Signals.Columns.TRJPLA_POSEFAIL_REASON_6,
                Signals.Columns.TRJPLA_POSEFAIL_REASON_7,
            ]
            # TRJPLA_POSE_REACHABLE = [
            #     Signals.Columns.TRJPLA_POSE_REACHABLE_0,
            #     Signals.Columns.TRJPLA_POSE_REACHABLE_1,
            #     Signals.Columns.TRJPLA_POSE_REACHABLE_2,
            #     Signals.Columns.TRJPLA_POSE_REACHABLE_3,
            #     Signals.Columns.TRJPLA_POSE_REACHABLE_4,
            #     Signals.Columns.TRJPLA_POSE_REACHABLE_5,
            #     Signals.Columns.TRJPLA_POSE_REACHABLE_6,
            #     Signals.Columns.TRJPLA_POSE_REACHABLE_7,
            # ]
            maneuvere_mask = screen_nu == constants.RootCauseAnalysis.MANEUVER_ACTIVE
            TRJPLA_POSEFAIL_REASON_mask = [
                (df[Signals.Columns.TRJPLA_POSEFAIL_REASON_0] != constants.ConstantsTrajpla.FAIL_REASON)
                & maneuvere_mask,
                (df[Signals.Columns.TRJPLA_POSEFAIL_REASON_1] != constants.ConstantsTrajpla.FAIL_REASON)
                & maneuvere_mask,
                (df[Signals.Columns.TRJPLA_POSEFAIL_REASON_2] != constants.ConstantsTrajpla.FAIL_REASON)
                & maneuvere_mask,
                (df[Signals.Columns.TRJPLA_POSEFAIL_REASON_3] != constants.ConstantsTrajpla.FAIL_REASON)
                & maneuvere_mask,
                (df[Signals.Columns.TRJPLA_POSEFAIL_REASON_4] != constants.ConstantsTrajpla.FAIL_REASON)
                & maneuvere_mask,
                (df[Signals.Columns.TRJPLA_POSEFAIL_REASON_5] != constants.ConstantsTrajpla.FAIL_REASON)
                & maneuvere_mask,
                (df[Signals.Columns.TRJPLA_POSEFAIL_REASON_6] != constants.ConstantsTrajpla.FAIL_REASON)
                & maneuvere_mask,
                (df[Signals.Columns.TRJPLA_POSEFAIL_REASON_7] != constants.ConstantsTrajpla.FAIL_REASON)
                & maneuvere_mask,
            ]

            evaluation1 = " ".join(
                f"The evaluation of {Signals.Columns.PATH_FOUND} is FAILED because the values"
                f" are != 1 until manuever finished.".split()
            )

            evaluation2 = " ".join(
                f"The evaluation of {Signals.Columns.FAIL_REASON} is PASSED with values =="
                f" {constants.ConstantsTrajpla.FAIL_REASON} until manuever finished.".split()
            )
            evaluation = ["" for _ in range(8)]
            for i in range(8):
                evaluation[i] = " ".join(
                    f"The evaluation of {TRJPLA_POSEFAIL_REASON[i]} is PASSED with values == "
                    f"{constants.ConstantsTrajpla.FAIL_REASON} until manuever finished.".split()
                )

            # for idx, val in enumerate(df[Signals.Columns.SCREEN_NU]):
            #     if val != constants.RootCauseAnalysis.MANEUVER_FINISHED:
            #         t2 = idx
            #         break
            # if t2 is not None:
            #     eval_cond = [False] * 2
            #     eval_cond[1] = True
            for idx, val in enumerate(df[Signals.Columns.CORE_STATE]):
                if val != constants.ParkCoreStatus.CORE_PARKING:
                    t2 = idx
                    break
            if t2 is not None:
                eval_cond = [False] * 10
                eval_cond[1:] = [True] * 9

                for idx in range(t2, len(df[Signals.Columns.SCREEN_NU])):
                    if df[Signals.Columns.SCREEN_NU].iloc[idx] != constants.RootCauseAnalysis.MANEUVER_FINISHED:
                        if df[Signals.Columns.PATH_FOUND].iloc[idx] == constants.ConstantsTrajpla.PATH_FOUND:
                            evaluation1 = " ".join(
                                f"The evaluation of {Signals.Columns.PATH_FOUND} is PASSED with values == "
                                f" {constants.ConstantsTrajpla.PATH_FOUND} .".split()
                            )
                            eval_cond[0] = True
                        if (
                            df[Signals.Columns.FAIL_REASON].iloc[idx] != constants.ConstantsTrajpla.FAIL_REASON
                            and eval_cond[1]
                        ):
                            evaluation2 = " ".join(
                                f"The evaluation of {Signals.Columns.FAIL_REASON} is FAILED because the values"
                                f" are != 0 until manuever finished.".split()
                            )
                            eval_cond[1] = False
                for i in range(8):
                    if TRJPLA_POSEFAIL_REASON_mask[i].any():
                        evaluation[i] = " ".join(
                            f"The evaluation of {TRJPLA_POSEFAIL_REASON[i]} is FAILED because the values"
                            " are != 0 until manuever finished.".split()
                        )
                        eval_cond[i + 2] = False

                    if all(eval_cond):
                        self.result.measured_result = TRUE
                        verdict_obj.step_6 = fc.PASS
                        self.result.details["root_cause_text"] = "passed"
                    else:
                        self.result.measured_result = FALSE
                        verdict_obj.step_6 = fc.FAIL
                        self.result.details["root_cause_text"] = "failed"
            else:
                evaluation1 = "Trigger not found!"
                self.result.measured_result = DATA_NOK
                verdict_obj.step_6 = fc.NOT_ASSESSED
                self.result.details["root_cause_text"] = "not assessed"

            signal_summary["Trajectory successfully planned"] = evaluation1
            signal_summary["Fail "] = evaluation2
            for i in range(8):
                signal_summary[f"Target Pose {i} fail"] = evaluation[i]
            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")
            df["status"] = screen_nu.apply(lambda x: fh.get_status_label(x, constants.RootCauseAnalysis))

            self.fig = go.Figure()
            self.fig.add_trace(go.Scatter(x=time, y=path_found, mode="lines", name=Signals.Columns.PATH_FOUND))
            self.fig.add_trace(go.Scatter(x=time, y=fail_reason, mode="lines", name=Signals.Columns.FAIL_REASON))
            self.fig.add_trace(go.Scatter(x=time, y=core_state, mode="lines", name=Signals.Columns.CORE_STATE))

            self.fig.add_trace(
                go.Scatter(
                    x=time,
                    y=screen_nu,
                    mode="lines",
                    name=Signals.Columns.SCREEN_NU,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    visible="legendonly",
                    text=df["status"],
                )
            )

            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.SCANNING_ACTIVE, time, "LightSalmon", " "
            )
            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.MANEUVER_ACTIVE, time, "RoyalBlue", " "
            )
            # fh.highlight_segments(
            #     self.fig, core_state, constants.ParkCoreStatus.CORE_PARKING, time, "RoyalBlue", "CORE_PARKING"
            # )
            self.fig.update_layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

            self.fig = go.Figure()
            for i in range(8):
                self.fig.add_trace(
                    go.Scatter(
                        x=time,
                        y=df[TRJPLA_POSEFAIL_REASON[i]],
                        mode="lines",
                        name=TRJPLA_POSEFAIL_REASON[i],
                    )
                )
            self.fig.update_layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

            # self.fig = go.Figure()
            # for i in range(8):
            #     self.fig.add_trace(
            #         go.Scatter(
            #             x=time,
            #             y=df[TRJPLA_POSE_REACHABLE[i]],
            #             mode="lines",
            #             name=TRJPLA_POSE_REACHABLE[i],
            #         )
            #     )
            # self.fig.update_layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            # self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            # plot_titles.append("")
            # plots.append(self.fig)
            # remarks.append("")

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=7,
    name="TAPOSD",
    description="Verify that parking box ID selected by the driver has a value different of 255(No slot is selected by the driver) until manuever finished.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class TAPOSD_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_7 = fc.INPUT_MISSING

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            pb_id = df[Signals.Columns.SELECTED_PB_ID]
            screen_nu = df[Signals.Columns.SCREEN_NU]

            evaluation1 = " ".join(
                f"The evaluation of {Signals.Columns.SELECTED_PB_ID} is FAILED because the values"
                f" are == {constants.RootCauseAnalysis.NO_SLOT_SELECT} until MANUEVER FINISHED.".split()
            )

            for idx, val in enumerate(df[Signals.Columns.SCREEN_NU]):
                if val != constants.RootCauseAnalysis.MANEUVER_FINISHED:
                    t2 = idx
                    break
            if t2 is not None:
                eval_cond = [False]

                for idx in range(t2, len(df[Signals.Columns.SCREEN_NU])):
                    if screen_nu.iloc[idx] != constants.RootCauseAnalysis.MANEUVER_FINISHED:
                        if df[Signals.Columns.SELECTED_PB_ID].iloc[idx] != constants.RootCauseAnalysis.NO_SLOT_SELECT:
                            evaluation1 = " ".join(
                                f"The evaluation of {Signals.Columns.SELECTED_PB_ID} is PASSED with values different than"
                                f" {constants.RootCauseAnalysis.NO_SLOT_SELECT} .".split()
                            )
                            eval_cond[0] = True

                    if all(eval_cond):
                        self.result.measured_result = TRUE
                        verdict_obj.step_7 = fc.PASS
                        self.result.details["root_cause_text"] = "passed"
                    else:
                        self.result.measured_result = FALSE
                        verdict_obj.step_7 = fc.FAIL
                        self.result.details["root_cause_text"] = "failed"
            else:
                evaluation1 = "Trigger not found!"
                self.result.measured_result = DATA_NOK
                verdict_obj.step_7 = fc.NOT_ASSESSED
                self.result.details["root_cause_text"] = "not assessed"

            signal_summary["Parking box ID selected by the driver"] = evaluation1
            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")
            df["status"] = screen_nu.apply(lambda x: fh.get_status_label(x, constants.RootCauseAnalysis))

            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(
                    x=time,
                    y=screen_nu,
                    mode="lines",
                    name=Signals.Columns.SCREEN_NU,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    visible="legendonly",
                    text=df["status"],
                )
            )
            self.fig.add_trace(go.Scatter(x=time, y=pb_id, mode="lines", name=Signals.Columns.SELECTED_PB_ID))
            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.SCANNING_ACTIVE, time, "LightSalmon", "SCANNING_ACTIVE"
            )
            self.fig.update_layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=8,
    name="HMI",
    description="Verify that in the signal SCREEN.NU from HMI is present the value 5(MANUEVER_FINISHED) which means that parking succeded.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class HMI_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_8 = fc.INPUT_MISSING

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            screen_nu = df[Signals.Columns.SCREEN_NU]

            evaluation1 = " ".join(
                f"The evaluation of {Signals.Columns.SCREEN_NU} is FAILED because"
                f"values of screen_nu == {constants.RootCauseAnalysis.MANEUVER_FINISHED}  does not exist.".split()
            )

            for idx, val in enumerate(df[Signals.Columns.SCREEN_NU]):
                if val != 5:
                    t2 = idx
                    break
            if t2 is not None:
                eval_cond = [False]

                for idx in range(t2, len(df[Signals.Columns.SCREEN_NU])):
                    if df[Signals.Columns.SCREEN_NU].iloc[idx] == constants.RootCauseAnalysis.MANEUVER_FINISHED:
                        evaluation1 = " ".join(
                            f"The evaluation of {Signals.Columns.SCREEN_NU} is PASSED with  values =={constants.RootCauseAnalysis.MANEUVER_FINISHED}.".split()
                        )
                        eval_cond[0] = True

                if all(eval_cond):
                    self.result.measured_result = TRUE
                    verdict_obj.step_8 = fc.PASS
                    self.result.details["root_cause_text"] = "passed"
                else:
                    self.result.measured_result = FALSE
                    verdict_obj.step_8 = fc.FAIL
                    self.result.details["root_cause_text"] = "failed"
            else:
                evaluation1 = "Trigger not found!"
                self.result.measured_result = DATA_NOK
                verdict_obj.step_1 = fc.NOT_ASSESSED
                self.result.details["root_cause_text"] = "not assessed"

            signal_summary["Parking succeeded message on HMI"] = evaluation1
            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")
            df["status"] = screen_nu.apply(lambda x: fh.get_status_label(x, constants.RootCauseAnalysis))

            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(
                    x=time,
                    y=screen_nu,
                    mode="lines",
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    name=Signals.Columns.SCREEN_NU,
                    text=df["status"],
                )
            )
            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.SCANNING_ACTIVE, time, "LightSalmon", "SCANNING_ACTIVE"
            )
            self.fig.update_layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)

            verdict, color = verdict_obj.check_result()

            additional_results_dict = {
                "Verdict": {"value": verdict.title(), "color": color},
            }
            self.result.details["Additional_results"] = additional_results_dict

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=9,
    name="PARKSM",
    description="Verify that parking process succeeded without errors.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class PARKSM_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_8 = fc.INPUT_MISSING

            plot_titles, plots, remarks = fh.rep([], 3)
            signal_summary = {}
            eval_cond = [False] * 3

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            core_ready = df[Signals.Columns.CORE_READY]
            core_state = df[Signals.Columns.CORE_STATE]
            core_stop_reason = df[Signals.Columns.CORE_STOP_REASON]

            core_ready_mask = (
                core_ready != 1
            )  # mask for core_ready values equal with 1(parking state machine is working properly)
            core_state_mask = (
                core_state == 3
            )  # mask for core_state values equal with 3(parking is successfully finished)
            core_stop_reason_mask = (
                core_stop_reason == 3
            )  # mask for core_stop_reason values equal with 3(parking is successfully finished)
            core_stop_reason_mask_0 = (
                core_stop_reason != 0
            )  # mask for core_stop_reason values different than 0(error during parking)
            core_stop_reason_mask_3 = (
                core_stop_reason != 3
            )  # mask for core_stop_reason values different than 3(error during parking)
            # core_stop_reason_error_mask = (core_stop_reason == 0) and core_stop_reason_mask # mask for core_stop_reason values different than 0 and 3(error during parking)
            core_ready_mask_np = np.array(core_ready_mask)
            first_true_index_1 = np.argmax(core_ready_mask_np)

            if not core_ready_mask_np.any():
                evaluation1 = " ".join(
                    f"The evaluation of {Signals.Columns.CORE_READY} is FAILED because"
                    f"during the whole measurement were not found values equals with 1, meaning parking system machine is not working properly."
                    f" ".split()
                )
                eval_cond[0] = False
            elif core_ready_mask.any():
                evaluation1 = " ".join(
                    f"The evaluation of {Signals.Columns.CORE_READY} is FAILED at timestamp {time.iloc[first_true_index_1]} because"
                    f" during the whole measurement were found values different than 1, meaning parking system machine is not working properly."
                    f" ".split()
                )
                eval_cond[0] = False
            else:
                evaluation1 = " ".join(
                    f"The evaluation of {Signals.Columns.CORE_READY} is PASSED with values == 1 during the whole measurement,"
                    f" meaning parking system machine is working properly.".split()
                )
                eval_cond[0] = True

            if core_state_mask.any() and core_stop_reason_mask.any():
                evaluation2 = " ".join(
                    f"The evaluation of {Signals.Columns.CORE_STATE} and {Signals.Columns.CORE_STOP_REASON} is PASSED with values == 3,"
                    f" meaning parking is successfully finished.".split()
                )
                eval_cond[1] = True
            else:
                evaluation2 = " ".join(
                    f"The evaluation of {Signals.Columns.CORE_STATE} and {Signals.Columns.CORE_STOP_REASON} is FAILED because"
                    f" values of CORE STATE == 3 or CORE STOP REASON == 3 were not found.".split()
                )
                eval_cond[1] = False
            if core_stop_reason_mask_0.any() and core_stop_reason_mask_3.any():
                evaluation3 = " ".join(
                    f"The evaluation of {Signals.Columns.CORE_STOP_REASON} is FAILED because"
                    f" values different than 0 or 3 exist, which means an error during parking occured.".split()
                )
                eval_cond[2] = False
            else:
                evaluation3 = " ".join(
                    f"The evaluation of {Signals.Columns.CORE_STOP_REASON} is PASSED without any errors during parking, meaning only values of 3 and/or 0 were found.".split()
                )
                eval_cond[2] = True

            if all(eval_cond):
                self.result.measured_result = TRUE
                self.result.details["root_cause_text"] = "passed"
            else:
                self.result.measured_result = FALSE
                self.result.details["root_cause_text"] = "failed"

            signal_summary["CORE READY "] = evaluation1
            signal_summary["CORE STATE & CORE STOP REASON "] = evaluation2
            signal_summary["CORE STOP REASON "] = evaluation3
            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")

            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(
                    x=time,
                    y=core_state,
                    mode="lines",
                    name=Signals.Columns.CORE_STATE,
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=time,
                    y=core_ready,
                    mode="lines",
                    name=Signals.Columns.CORE_READY,
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=time,
                    y=core_stop_reason,
                    mode="lines",
                    name=Signals.Columns.CORE_STOP_REASON,
                )
            )

            fh.highlight_segments(
                self.fig, core_state, constants.ParkCoreStatus.CORE_PAUSE, time, "LightSalmon", "PARKING FINISHED"
            )
            self.fig.update_layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)

            verdict, color = verdict_obj.check_result()

            additional_results_dict = {
                "Verdict": {"value": verdict.title(), "color": color},
            }
            self.result.details["Additional_results"] = additional_results_dict

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=10,
    name="MOCO",
    description="Show relevant plots for MOCO component.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class MOCO_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_8 = fc.INPUT_MISSING

            plot_titles, plots, remarks = fh.rep([], 3)

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            screen_nu = df[Signals.Columns.SCREEN_NU]
            moco_lodmc_acceleration = (
                df[Signals.Columns.MOCO_LODMC_ACCELERATION]
                if Signals.Columns.MOCO_LODMC_ACCELERATION in df.columns
                else None
            )
            moco_lodmc_dist2stop = (
                df[Signals.Columns.MOCO_LODMC_DIST2STOP] if Signals.Columns.MOCO_LODMC_DIST2STOP in df.columns else None
            )
            moco_lodmc_driving_forward_req = (
                df[Signals.Columns.MOCO_LODMC_DRIVING_FORWARD_REQ]
                if Signals.Columns.MOCO_LODMC_DRIVING_FORWARD_REQ in df.columns
                else None
            )
            moco_lodmc_emergency_hold_req = (
                df[Signals.Columns.MOCO_LODMC_EMERGENCY_HOLD_REQ]
                if Signals.Columns.MOCO_LODMC_EMERGENCY_HOLD_REQ in df.columns
                else None
            )
            moco_lodmc_hold_req = (
                df[Signals.Columns.MOCO_LODMC_HOLD_REQ] if Signals.Columns.MOCO_LODMC_HOLD_REQ in df.columns else None
            )
            moco_lodmc_request = (
                df[Signals.Columns.MOCO_LODMC_REQUEST] if Signals.Columns.MOCO_LODMC_REQUEST in df.columns else None
            )
            moco_lodmc_request_interface = (
                df[Signals.Columns.MOCO_LODMC_REQUEST_INTERFACE]
                if Signals.Columns.MOCO_LODMC_REQUEST_INTERFACE in df.columns
                else None
            )
            moco_lodmc_request_source = (
                df[Signals.Columns.MOCO_LODMC_REQUEST_SOURCE]
                if Signals.Columns.MOCO_LODMC_REQUEST_SOURCE in df.columns
                else None
            )
            moco_lodmc_secure = (
                df[Signals.Columns.MOCO_LODMC_SECURE] if Signals.Columns.MOCO_LODMC_SECURE in df.columns else None
            )
            moco_lodmc_trajectory_reset = (
                df[Signals.Columns.MOCO_LODMC_TRAJECTORY_RESET]
                if Signals.Columns.MOCO_LODMC_TRAJECTORY_RESET in df.columns
                else None
            )
            moco_lodmc_velocity_limit = (
                df[Signals.Columns.MOCO_LODMC_VELOCITY_LIMIT]
                if Signals.Columns.MOCO_LODMC_VELOCITY_LIMIT in df.columns
                else None
            )

            df["status"] = screen_nu.apply(lambda x: fh.get_status_label(x, constants.RootCauseAnalysis))

            self.fig = go.Figure()

            if moco_lodmc_acceleration is not None:
                self.fig.add_trace(
                    go.Scatter(
                        x=time, y=moco_lodmc_acceleration, mode="lines", name=Signals.Columns.MOCO_LODMC_ACCELERATION
                    )
                )

            if moco_lodmc_dist2stop is not None:
                self.fig.add_trace(
                    go.Scatter(x=time, y=moco_lodmc_dist2stop, mode="lines", name=Signals.Columns.MOCO_LODMC_DIST2STOP)
                )

            if moco_lodmc_driving_forward_req is not None:
                self.fig.add_trace(
                    go.Scatter(
                        x=time,
                        y=moco_lodmc_driving_forward_req,
                        mode="lines",
                        name=Signals.Columns.MOCO_LODMC_DRIVING_FORWARD_REQ,
                    )
                )

            if moco_lodmc_emergency_hold_req is not None:
                self.fig.add_trace(
                    go.Scatter(
                        x=time,
                        y=moco_lodmc_emergency_hold_req,
                        mode="lines",
                        name=Signals.Columns.MOCO_LODMC_EMERGENCY_HOLD_REQ,
                    )
                )

            if moco_lodmc_hold_req is not None:
                self.fig.add_trace(
                    go.Scatter(x=time, y=moco_lodmc_hold_req, mode="lines", name=Signals.Columns.MOCO_LODMC_HOLD_REQ)
                )

            if moco_lodmc_request is not None:
                self.fig.add_trace(
                    go.Scatter(x=time, y=moco_lodmc_request, mode="lines", name=Signals.Columns.MOCO_LODMC_REQUEST)
                )

            if moco_lodmc_request_interface is not None:
                self.fig.add_trace(
                    go.Scatter(
                        x=time,
                        y=moco_lodmc_request_interface,
                        mode="lines",
                        name=Signals.Columns.MOCO_LODMC_REQUEST_INTERFACE,
                    )
                )

            if moco_lodmc_request_source is not None:
                self.fig.add_trace(
                    go.Scatter(
                        x=time,
                        y=moco_lodmc_request_source,
                        mode="lines",
                        name=Signals.Columns.MOCO_LODMC_REQUEST_SOURCE,
                    )
                )

            if moco_lodmc_secure is not None:
                self.fig.add_trace(
                    go.Scatter(x=time, y=moco_lodmc_secure, mode="lines", name=Signals.Columns.MOCO_LODMC_SECURE)
                )

            if moco_lodmc_trajectory_reset is not None:
                self.fig.add_trace(
                    go.Scatter(
                        x=time,
                        y=moco_lodmc_trajectory_reset,
                        mode="lines",
                        name=Signals.Columns.MOCO_LODMC_TRAJECTORY_RESET,
                    )
                )

            if moco_lodmc_velocity_limit is not None:
                self.fig.add_trace(
                    go.Scatter(
                        x=time,
                        y=moco_lodmc_velocity_limit,
                        mode="lines",
                        name=Signals.Columns.MOCO_LODMC_VELOCITY_LIMIT,
                    )
                )
            self.fig.add_trace(go.Scatter(x=time, y=screen_nu, mode="lines", name=Signals.Columns.SCREEN_NU))

            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.MANEUVER_ACTIVE, time, "LightSalmon", "MANEUVER ACTIVE"
            )
            self.fig.update_layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)

            verdict, color = verdict_obj.check_result()

            additional_results_dict = {
                "Verdict": {"value": verdict.title(), "color": color},
            }
            self.result.details["Additional_results"] = additional_results_dict

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("req-001")
@testcase_definition(
    name="Manuever Root Cause Analysis",
    description="Verify the output checks of components for manuever(to be ignored if slot offering checks failed for the measurement).",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class ManueverRootCause(TestCase):
    # custom_report = CustomTestcaseReport
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            # PreAnalysisSTEP,
            VEDODO_STEP,
            US_STEP,
            PMSD_STEP,
            CEM_STEP,
            SI_STEP,
            TRJPLA_STEP,
            TAPOSD_STEP,
            HMI_STEP,
            PARKSM_STEP,
            MOCO_STEP,
        ]


def convert_dict_to_pandas(signal_summary: dict, table_remark="", table_title=""):
    """Converts a dictionary to a Pandas DataFrame and creates an HTML table."""
    evaluation_summary = pd.DataFrame(
        {
            "Evaluation": {key: key for key, val in signal_summary.items()},
            "Results": {key: val for key, val in signal_summary.items()},
        }
    )
    return fh.build_html_table(
        evaluation_summary,
        table_remark,
        table_title,
    )
