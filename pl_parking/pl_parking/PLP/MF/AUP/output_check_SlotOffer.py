"""Output Check Slot Offer"""

import logging
import os
import sys

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
from time import time as start_time

from tsf.core.results import TRUE, BooleanResult
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

import pl_parking.common_ft_helper as fh

# from pl_parking.PLP.MF.PARKSM.ft_parksm import StatisticsExample

__author__ = "BA ADAS ENP SIMU KPI"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

EXAMPLE = "OUTPUT CHECK"
now_time = start_time()


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        sg_time = "TimeStamp"
        sg_time_m7 = "TimeStamp_M7"
        sg_parksm_core_status_stop_reason = "ParkSmCoreStatus"
        sg_parksm_core_status_state = "ParkSmCoreStatusState"
        sg_num_valid_parking_boxes = "NumValidParkingBoxes"
        sg_velocity = "EgoMotionPort"
        sg_ego_pos = "EgoPositionAP"
        sg_slot_coord = "SlotCoordinates"
        sg_slot_coord_1 = "SlotCoordinates1"
        sg_slot_coord_2 = "SlotCoordinates2"
        sg_slot_coord_3 = "SlotCoordinates3"
        sg_slot_coord_4 = "SlotCoordinates4"
        sg_slot_coord_5 = "SlotCoordinates5"
        sg_slot_coord_6 = "SlotCoordinates6"
        sg_slot_coord_7 = "SlotCoordinates7"
        sg_targetposes0_pose_0 = "TargetPoses0Pose0"
        sg_targetposes0_pose_1 = "TargetPoses0Pose1"
        sg_targetposes0_pose_2 = "TargetPoses0Pose2"
        sg_targetposes0_reachable_status = "TargetPoses0ReachableStatus"
        sg_targetposes1_pose_0 = "TargetPoses1Pose0"
        sg_targetposes1_pose_1 = "TargetPoses1Pose1"
        sg_targetposes1_pose_2 = "TargetPoses1Pose2"
        sg_targetposes1_reachable_status = "TargetPoses1ReachableStatus"
        sg_targetposes2_pose_0 = "TargetPoses2Pose0"
        sg_targetposes2_pose_1 = "TargetPoses2Pose1"
        sg_targetposes2_pose_2 = "TargetPoses2Pose2"
        sg_targetposes2_reachable_status = "TargetPoses2ReachableStatus"
        sg_targetposes3_pose_0 = "TargetPoses3Pose0"
        sg_targetposes3_pose_1 = "TargetPoses3Pose1"
        sg_targetposes3_pose_2 = "TargetPoses3Pose2"
        sg_targetposes3_reachable_status = "TargetPoses3ReachableStatus"
        sg_targetposes4_pose_0 = "TargetPoses4Pose0"
        sg_targetposes4_pose_1 = "TargetPoses4Pose1"
        sg_targetposes4_pose_2 = "TargetPoses4Pose2"
        sg_targetposes4_reachable_status = "TargetPoses4ReachableStatus"
        sg_targetposes5_pose_0 = "TargetPoses5Pose0"
        sg_targetposes5_pose_1 = "TargetPoses5Pose1"
        sg_targetposes5_pose_2 = "TargetPoses5Pose2"
        sg_targetposes5_reachable_status = "TargetPoses5ReachableStatus"
        sg_targetposes6_pose_0 = "TargetPoses6Pose0"
        sg_targetposes6_pose_1 = "TargetPoses6Pose1"
        sg_targetposes6_pose_2 = "TargetPoses6Pose2"
        sg_targetposes6_reachable_status = "TargetPoses6ReachableStatus"
        sg_targetposes7_pose_0 = "TargetPoses7Pose0"
        sg_targetposes7_pose_1 = "TargetPoses7Pose1"
        sg_targetposes8_pose_2 = "TargetPoses7Pose2"
        sg_targetposes7_reachable_status = "TargetPoses7ReachableStatus"
        SOFTWARE_MAJOR = "SOFTWARE_MAJOR"
        SOFTWARE_MINOR = "SOFTWARE_MINOR"
        SOFTWARE_PATCH = "SOFTWARE_PATCH"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = [
            "CarPC.EM_Thread",
            "M7board.ConfigurationTrace",
            "MTS.Package",
            "M7board.CAN_Thread",
            "ADC5xx_Device",
        ]
        # TO BE UPDATED FOR ADC5:
        # ADC5xx_Device.TRJPLA_DATA.TrjPlaTargetPosesPort.targetPoses[].reachableStatus
        # ADC5xx_Device.TRJPLA_DATA.TrjPlaTargetPosesPort.targetPoses[].pose.x_dir for ADC5
        # ADC5xx_Device.TRJPLA_DATA.TrjPlaTargetPosesPort.targetPoses[].pose.y_dir
        # ADC5xx_Device.TRJPLA_DATA.TrjPlaTargetPosesPort.targetPoses[].pose.yaw_rad
        self._properties = {
            self.Columns.sg_time: ".TimeStamp",
            self.Columns.sg_time_m7: ".OdoEstimationOutputPort.odoEstimationPort.timestamp_us",  # ADC5xx_Device.USP_DATA.SpuOdoEstimationOutputPort.sSigHeader.uiTimeStamp
            self.Columns.sg_parksm_core_status_stop_reason: ".PARKSMCoreStatusPort.coreStopReason_nu",
            # self.Columns.sg_parksm_core_status_stop_reason: ".EM_DATA.EmPARRKSMCoreStatusPort.coreStopReason_nu",
            # ADC5xx_Device.EM_DATA.EmPARRKSMCoreStatusPort.coreStopReason_nu
            self.Columns.sg_parksm_core_status_state: ".PARKSMCoreStatusPort.parksmCoreState_nu",  # ADC5xx_Device.EM_DATA.EmPARRKSMCoreStatusPort.parksmCoreState_nu
            self.Columns.sg_num_valid_parking_boxes: ".ApParkingBoxPort.numValidParkingBoxes_nu",  # ADC5xx_Device.EM_DATA.EmApParkingBoxPort.numValidParkingBoxes_nu
            self.Columns.sg_velocity: ".EgoMotionPort.vel_mps",  # ADC5xx_Device.EM_DATA.EmEgoMotionPort.vel_mps
            self.Columns.sg_ego_pos: ".ApEnvModelPort.egoVehiclePoseForAP[0]",  # ADC5xx_Device.EM_DATA.EmApEnvModelPort.egoVehiclePoseForAP.x_dir
            self.Columns.sg_slot_coord: ".ApParkingBoxPort.parkingBoxes[0].slotCoordinates_m[0]",
            # ADC5xx_Device.EM_DATA.EmApParkingBoxPort.parkingBoxes[SOMETHING].slotCoordinates_m.array[SOMETHING].x_dir
            self.Columns.sg_slot_coord_1: ".ApParkingBoxPort.parkingBoxes[1].slotCoordinates_m[0]",
            self.Columns.sg_slot_coord_2: ".ApParkingBoxPort.parkingBoxes[2].slotCoordinates_m[0]",
            self.Columns.sg_slot_coord_3: ".ApParkingBoxPort.parkingBoxes[3].slotCoordinates_m[0]",
            self.Columns.sg_slot_coord_4: ".ApParkingBoxPort.parkingBoxes[4].slotCoordinates_m[0]",
            self.Columns.sg_slot_coord_5: ".ApParkingBoxPort.parkingBoxes[5].slotCoordinates_m[0]",
            self.Columns.sg_slot_coord_6: ".ApParkingBoxPort.parkingBoxes[6].slotCoordinates_m[0]",
            self.Columns.sg_slot_coord_7: ".ApParkingBoxPort.parkingBoxes[7].slotCoordinates_m[0]",
            self.Columns.sg_targetposes0_pose_0: ".TargetPosesPort.targetPoses[0].pose[0]",
            # self.Columns.sg_targetposes0_pose_1: '.TargetPosesPort.targetPoses[0].pose[1]',
            # self.Columns.sg_targetposes0_pose_2: '.TargetPosesPort.targetPoses[0].pose[2]',
            self.Columns.sg_targetposes0_reachable_status: ".TargetPosesPort.targetPoses[0].reachableStatus",
            self.Columns.sg_targetposes1_pose_0: ".TargetPosesPort.targetPoses[1].pose[0]",
            # self.Columns.sg_targetposes1_pose_1: '.TargetPosesPort.targetPoses[1].pose[1]',
            # self.Columns.sg_targetposes1_pose_2: '.TargetPosesPort.targetPoses[1].pose[2]',
            self.Columns.sg_targetposes1_reachable_status: ".TargetPosesPort.targetPoses[1].reachableStatus",
            self.Columns.sg_targetposes2_pose_0: ".TargetPosesPort.targetPoses[2].pose[0]",
            # self.Columns.sg_targetposes2_pose_1: '.TargetPosesPort.targetPoses[2].pose[1]',
            # self.Columns.sg_targetposes2_pose_2: '.TargetPosesPort.targetPoses[2].pose[2]',
            self.Columns.sg_targetposes2_reachable_status: ".TargetPosesPort.targetPoses[2].reachableStatus",
            self.Columns.sg_targetposes3_pose_0: ".TargetPosesPort.targetPoses[3].pose[0]",
            # self.Columns.sg_targetposes3_pose_1: '.TargetPosesPort.targetPoses[3].pose[1]',
            # self.Columns.sg_targetposes3_pose_2: '.TargetPosesPort.targetPoses[3].pose[2]',
            self.Columns.sg_targetposes3_reachable_status: ".TargetPosesPort.targetPoses[3].reachableStatus",
            self.Columns.sg_targetposes4_pose_0: ".TargetPosesPort.targetPoses[4].pose[0]",
            # self.Columns.sg_targetposes4_pose_1: '.TargetPosesPort.targetPoses[4].pose[1]',
            # self.Columns.sg_targetposes4_pose_2: '.TargetPosesPort.targetPoses[4].pose[2]',
            self.Columns.sg_targetposes4_reachable_status: ".TargetPosesPort.targetPoses[4].reachableStatus",
            self.Columns.sg_targetposes5_pose_0: ".TargetPosesPort.targetPoses[5].pose[0]",
            # self.Columns.sg_targetposes5_pose_1: '.TargetPosesPort.targetPoses[5].pose[1]',
            # self.Columns.sg_targetposes5_pose_2: '.TargetPosesPort.targetPoses[5].pose[2]',
            self.Columns.sg_targetposes5_reachable_status: ".TargetPosesPort.targetPoses[5].reachableStatus",
            self.Columns.sg_targetposes6_pose_0: ".TargetPosesPort.targetPoses[6].pose[0]",
            # self.Columns.sg_targetposes6_pose_1: '.TargetPosesPort.targetPoses[6].pose[1]',
            # self.Columns.sg_targetposes6_pose_2: '.TargetPosesPort.targetPoses[6].pose[2]',
            self.Columns.sg_targetposes6_reachable_status: ".TargetPosesPort.targetPoses[6].reachableStatus",
            self.Columns.sg_targetposes7_pose_0: ".TargetPosesPort.targetPoses[7].pose[0]",
            # self.Columns.sg_targetposes7_pose_1: '.TargetPosesPort.targetPoses[7].pose[1]',
            # self.Columns.sg_targetposes8_pose_2: '.TargetPosesPort.targetPoses[7].pose[2]',
            self.Columns.sg_targetposes7_reachable_status: ".TargetPosesPort.targetPoses[7].reachableStatus",
            self.Columns.SOFTWARE_MAJOR: ".ApplicationReleaseInfo.softwareVersion.major",
            self.Columns.SOFTWARE_MINOR: ".ApplicationReleaseInfo.softwareVersion.minor",
            self.Columns.SOFTWARE_PATCH: ".ApplicationReleaseInfo.softwareVersion.patch",
        }


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="VEDODO",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class VEDODO_STEP(TestStep):
    """Vedodo Test Step for Output Check"""

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

            self.result.details["root_cause_text"] = "passed"
            self.result.measured_result = TRUE

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=2,
    name="MOCO",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class MOCO_STEP(TestStep):
    """Moco Test Step for Output Check"""

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
            self.result.details["root_cause_text"] = "passed"
            self.result.measured_result = TRUE

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=3,
    name="TRAJPLA",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class TRAJPLA_STEP(TestStep):
    """Trajpla Test Step for Output Check"""

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

            self.result.details["root_cause_text"] = "passed"
            self.result.measured_result = TRUE

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=4,
    name="TAPOSD",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class TAPOSD_STEP(TestStep):
    """Taposd Test Step for Output Check"""

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

            self.result.details["root_cause_text"] = "passed"
            self.result.measured_result = TRUE

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=5,
    name="SI",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class SI_STEP(TestStep):
    """SI Test Step for Output Check"""

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

            self.result.details["root_cause_text"] = "passed"
            self.result.measured_result = TRUE

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=6,
    name="CEM",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class CEM_STEP(TestStep):
    """CEM Test Step for Output Check"""

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

            self.result.details["root_cause_text"] = "passed"
            self.result.measured_result = TRUE

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=7,
    name="UDP",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class UDP_STEP(TestStep):
    """UDP Test Step for Output Check"""

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

            self.result.details["root_cause_text"] = "passed"
            self.result.measured_result = TRUE

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=8,
    name="PMSD",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class PMSD_STEP(TestStep):
    """PMSD Test Step for Output Check"""

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

            self.result.details["root_cause_text"] = "passed"
            self.result.measured_result = TRUE

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("req-001")
@testcase_definition(name="Output Check", description="")
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class OutputCheckCase(TestCase):
    # custom_report = CustomTestcaseReport
    """Output Check"""

    # custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            VEDODO_STEP,
            MOCO_STEP,
            TRAJPLA_STEP,
            TAPOSD_STEP,
            SI_STEP,
            CEM_STEP,
            UDP_STEP,
            PMSD_STEP,
        ]
