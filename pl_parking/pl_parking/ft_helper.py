"""helper module for pl_parking"""

import os
import sys

sys_path = os.path.abspath(os.path.join(__file__, ".."))
if sys_path not in sys.path:
    sys.path.append(sys_path)
from typing import Any, Union

from tsf.io.signals import SignalDefinition

from pl_parking.PLP.MF.constants import Platforms


class Parking:
    """Class representing parking-related functionalities."""

    # Stores sensor data calculated in TRC coordinate system if the memory threshold_yellow is satisfied
    data_dict = {Platforms.SIM: {}, Platforms.VEHICLE: {}}

    @staticmethod
    def calc_table_height(data_dict, base=80, height_per_row=40, char_limit=115, height_padding=10):
        """
        This function calculates the total height required to display a table based on
        the provided data dictionary. The height is determined by the number of rows in
        the table and the length of the values in each row.
        """
        total_height = base

        if isinstance(data_dict, dict):
            total_height += height_per_row * len(data_dict.keys())
            for value in data_dict.values():
                if len(str(value)) > char_limit:
                    total_height += height_padding
        else:
            raise ValueError("Invalid input type. Expected a dictionary.")

        return total_height

    @staticmethod
    def apply_color(result, threshold_check, operator_pass, threshold_color, operator_color):
        """
        Evaluates the given 'result' against a 'threshold_color' using the specified 'operator_color' and
        returns a color code.

        Args:
            result: The value to be compared.
            threshold_check: The value for pass.
            operator_pass: The operator to be used for the comparison for pass situations.
            threshold_color: The value for the acceptable(yellow).
            operator_color: The operator to be used for comparing acceptance values.

        Returns:
            A color code representing the result of the comparison:
            - '#28a745' (green) for a passed comparison.
            - '#dc3545' (red) for a failed comparison.
            - '#ffc107' (yellow) for threshold_pass value.
            - '#000000' (black) for a TypeError during the comparison.
        """
        comparison_operators = {
            "==": lambda value, threshold: value == threshold,
            "!=": lambda value, threshold: value != threshold,
            ">": lambda value, threshold: value > threshold,
            ">=": lambda value, threshold: value >= threshold,
            "<": lambda value, threshold: value < threshold,
            "<=": lambda value, threshold: value <= threshold,
            "><": lambda value, threshold: value > threshold[0] and value < threshold[1],
            ">=<=": lambda value, threshold: value >= threshold[0] and value <= threshold[1],
        }
        color_operators = {
            "None": lambda result, val1, val2: 1 == 3,  # dummy to return false
            "><": lambda result, val1, val2: result > val2 and result < val1 or result > val1 and result < val2,
            ">=<=": lambda result, val1, val2: result >= val2[0] and result <= val2[1],
            ">=<": lambda result, val1, val2: result >= val2[0] and result < val2[1],
            "><=": lambda result, val1, val2: result > val2[0] and result <= val2[1],
            "==": lambda result, val1, val2: result == val2,
            "!=": lambda result, val1, val2: result != val2,
            "<": lambda result, val1, val2: result < val2,
            "<=": lambda result, val1, val2: result <= val2,
            ">": lambda result, val1, val2: result > val2,
            ">=": lambda result, val1, val2: result >= val2,
        }
        try:
            if isinstance(result, tuple):
                result = result[0]
            if comparison_operators[operator_pass](result, threshold_check):
                color = "#28a745"  # Green color for PASSED
                if color_operators[operator_color](result, threshold_check, threshold_color):
                    color = "#ffc107"  # yellow color for PASSED
            else:
                color = ("#dc3545",)  # Red color for FAILED
        except TypeError:
            color = "rgb(33,39,43)"  # Black color for N/A

        return color

    @staticmethod
    # @typechecked
    # @runtime_decorator(min_level=3)
    def get_base_string(reader: Any, platform: str) -> Union[None, str]:
        """
        Get string for reading the correct signal
        :param reader: contains all signals from measurement
        :param platform: SIM or VEHICLE
        """
        basestring = None

        # Check what kind of platform is used and get basestring accordingly
        if platform == Platforms.SIM:
            if "AP.headUnitVisualizationPort.screen_nu" or "AP.evaluationPort.useCase_nu" in reader:
                basestring = "AP."
            # other checks for NEXT will be necessary to be added

            # if basestring is None:
            #     write_log_message("Error while reading mf_sil base string", "error", LOGGER)
            # else:
            #     write_log_message("mf_sil string found", "success", LOGGER)

        if platform == Platforms.VEHICLE:
            basestring = []
            if "MTS.Package.TimeStamp" in reader:
                basestring.append("MTS.Package.")
            if "M7board.EM_Thread.PSMDebugPort.stateVarPPC_nu" in reader:
                basestring.append("M7board.EM_Thread.")
            if "Reference_CAN.RT-Range_2017_02_28_SystemC.RangeHunterPosLocal.RangeHunterPosLocalX" in reader:
                basestring.append("Reference_CAN.RT-Range_2017_02_28_SystemC.")
            if "Reference_CAN.NAVconfig_AP_Passat_154_28-02-2017.HeadingPitchRoll.AngleHeading" in reader:
                basestring.append("Reference_CAN.NAVconfig_AP_Passat_154_28-02-2017.")
            if "M7board.CAN_Thread.OdoEstimationPort.yPosition_m" in reader:
                basestring.append("M7board.CAN_Thread.")

            # message output
            # if basestring is None:
            #     write_log_message("Error while reading M7 base string", "error", LOGGER)
            # else:
            #     write_log_message("M7 string found", "success", LOGGER)

        return basestring

    @staticmethod
    # @typechecked
    def data_mapping_EgoVehicle(base_string):
        """
        Return a tuple containing a dictionary and a bool element
        :param base_string : the basestring based on which is decided the dictionary
        :return :
                - a dictionary

        """
        # different handling for the signals which do not need a "base string" to be added
        if base_string == "AP.":
            return {
                "Car_vx": {"string": "Car.vx", "type": float},
                "CarYawRate": {"string": "Car.YawRate", "type": float},
                "LatSlope": {"string": "Car.Road.Route.LatSlope", "type": float},
                "CollisionCount": {"string": "Sensor.Collision.Vhcl.Fr1.Count", "type": float},
                "LongSlope": {"string": "Car.Road.Route.LongSlope", "type": float},
                "time": {"string": "Time", "type": float},
                "Car_ax": {"string": "Car.ax", "type": float},
                "Car_ay": {"string": "Car.ay", "type": float},
                "Vhcl_v": {"string": "Vhcl.v", "type": float},
                "VhclYawRate": {"string": "Vhcl.YawRate", "type": float},
                "VehicleRoad": {"string": "SI.trafficObject.Vehicle.sRoad", "type": float},
                "ParkingLaneMarking": {"string": "SI.trafficObject.parkingLaneMarking.sRoad", "type": float},
                "furthestObject_sRoad": {"string": "SI.trafficObject.furthestObject.sRoad", "type": float},
                "furthestObject_yaw": {"string": "SI.trafficObject.furthestObject.yaw", "type": float},
                "OdoRoad": {"string": "Traffic.Odo.sRoad", "type": float},
                "lscaRequestMode": {"string": "LSCA.brakePort.requestMode", "type": int},
                "brakeModeState": {"string": "LSCA.statusPort.brakingModuleState_nu", "type": int},
                "Car_v": {"string": "Car.v", "type": int},
                "sceneInterpretationActive_nu": {"string": "AP.sceneInterpretationActive_nu", "type": int},
                # keep in sync with trc/evaluation/functional_test_cases/PLP/MF/constants.py
                # (ConstantsSlotDetection.EXPORTED_SLOTS_NUMBER):
                "parkingBox0_slotCoordinates0_x": {
                    "string": "AP.parkingBoxPortCMOrigin.parkingBoxes_0.slotCoordinates_FrontLeft_x",
                    "type": float,
                },
                "parkingBox0_slotCoordinates0_y": {
                    "string": "AP.parkingBoxPortCMOrigin.parkingBoxes_0.slotCoordinates_FrontLeft_y",
                    "type": float,
                },
                "parkingBox0_slotCoordinates1_x": {
                    "string": "AP.parkingBoxPortCMOrigin.parkingBoxes_0.slotCoordinates_RearLeft_x",
                    "type": float,
                },
                "parkingBox0_slotCoordinates1_y": {
                    "string": "AP.parkingBoxPortCMOrigin.parkingBoxes_0.slotCoordinates_RearLeft_y",
                    "type": float,
                },
                "parkingBox0_slotCoordinates2_x": {
                    "string": "AP.parkingBoxPortCMOrigin.parkingBoxes_0.slotCoordinates_RearRight_x",
                    "type": float,
                },
                "parkingBox0_slotCoordinates2_y": {
                    "string": "AP.parkingBoxPortCMOrigin.parkingBoxes_0.slotCoordinates_RearRight_y",
                    "type": float,
                },
                "parkingBox0_slotCoordinates3_x": {
                    "string": "AP.parkingBoxPortCMOrigin.parkingBoxes_0.slotCoordinates_FrontRight_x",
                    "type": float,
                },
                "parkingBox0_slotCoordinates3_y": {
                    "string": "AP.parkingBoxPortCMOrigin.parkingBoxes_0.slotCoordinates_FrontRight_y",
                    "type": float,
                },
                "parkingBox1_slotCoordinates0_x": {
                    "string": "AP.parkingBoxPortCMOrigin.parkingBoxes_1.slotCoordinates_FrontLeft_x",
                    "type": float,
                },
                "parkingBox1_slotCoordinates0_y": {
                    "string": "AP.parkingBoxPortCMOrigin.parkingBoxes_1.slotCoordinates_FrontLeft_y",
                    "type": float,
                },
                "parkingBox1_slotCoordinates1_x": {
                    "string": "AP.parkingBoxPortCMOrigin.parkingBoxes_1.slotCoordinates_RearLeft_x",
                    "type": float,
                },
                "parkingBox1_slotCoordinates1_y": {
                    "string": "AP.parkingBoxPortCMOrigin.parkingBoxes_1.slotCoordinates_RearLeft_y",
                    "type": float,
                },
                "parkingBox1_slotCoordinates2_x": {
                    "string": "AP.parkingBoxPortCMOrigin.parkingBoxes_1.slotCoordinates_RearRight_x",
                    "type": float,
                },
                "parkingBox1_slotCoordinates2_y": {
                    "string": "AP.parkingBoxPortCMOrigin.parkingBoxes_1.slotCoordinates_RearRight_y",
                    "type": float,
                },
                "parkingBox1_slotCoordinates3_x": {
                    "string": "AP.parkingBoxPortCMOrigin.parkingBoxes_1.slotCoordinates_FrontRight_x",
                    "type": float,
                },
                "parkingBox1_slotCoordinates3_y": {
                    "string": "AP.parkingBoxPortCMOrigin.parkingBoxes_1.slotCoordinates_FrontRight_y",
                    "type": float,
                },
            }
        # Check if base_string is from any other data and return accordingly
        else:
            return {
                "Car_vx": {"string": base_string + "EgoMotionPort.vel_mps", "type": float},
                "CarYawRate": {"string": base_string + "EgoMotionPort.yawRate_radps", "type": float},
                "LatSlope": {"string": "Car.Road.Route.LatSlope", "type": float},
                "LongSlope": {"string": "Car.Road.Route.LongSlope", "type": float},
            }

    @staticmethod
    # @typechecked
    def data_mapping(base_string):
        """Defines the mapping of data fields."""
        return {
            "ApOdoCmRefXPosM": {"string": ("odoDebugPort.odoCmRefxPosition_m",), "type": float},
            "ApOdoCmRefYPosM": {"string": ("odoDebugPort.odoCmRefyPosition_m",), "type": float},
            "ApOdoCmRefYawAngRad": {"string": ("odoDebugPort.odoCmRefyawAngEgoRaCur_rad",), "type": float},
            "ApOdoEstimYawAngRad": {"string": ("odoEstimationPort.yawAngle_rad",), "type": float},
            "ApOdoEstimXPosM": {"string": ("odoEstimationPort.xPosition_m",), "type": float},
            "ApOdoEstimYPosM": {"string": ("odoEstimationPort.yPosition_m",), "type": float},
            "ApOdoEstimYawRateRadps": {"string": ("odoEstimationPort.yawRate_radps",), "type": float},
            "longiVelocity": {"string": ("odoEstimationPort.longiVelocity_mps",), "type": float},
            "steerAngFrontAxle_rad": {"string": ("odoEstimationPortCM.steerAngFrontAxle_rad",), "type": float},
            "motionStatus_nu": {"string": ("odoEstimationPort.motionStatus_nu",), "type": float},
            "steeringWheelAngle_rad": {
                "string": ("odoInputPort.odoSigFcanPort.steerCtrlStatus.steeringWheelAngle_rad",),
                "type": float,
            },
            "steeringWheelAngleVelocity_radps": {
                "string": ("odoInputPort.odoSigFcanPort.steerCtrlStatus.steeringWheelAngleVelocity_radps",),
                "type": float,
            },
            "lateralAcceleration_mps2": {
                "string": ("odoInputPort.odoSigFcanPort.vehDynamics.lateralAcceleration_mps2",),
                "type": float,
            },
            "longitudinalAcceleration_mps2": {
                "string": ("odoInputPort.odoSigFcanPort.vehDynamics.longitudinalAcceleration_mps2",),
                "type": float,
            },
            "yawRate_radps": {"string": ("odoEstimationPort.yawRate_radps",), "type": float},
            "pitchAngle_rad": {"string": ("odoEstimationPort.pitchAngle_rad",), "type": float},
            "headUnitVisu_screen_nu": {"string": ("headUnitVisualizationPort.screen_nu",), "type": float},
            "ApState": {"string": ("planningCtrlPort.apStates",), "type": float},
            "OrientationError": {"string": ("trajCtrlDebugPort.orientationError_rad",), "type": float},
            "LateralError": {"string": ("trajCtrlDebugPort.currentDeviation_m",), "type": float},
            "ApDistToStopReqInterExtrapolTraj": {
                "string": ("evaluationPort.distanceToStopReqInterExtrapolTraj_m",),
                "type": float,
            },
            "ApTrajCtrlActive": {"string": ("trajCtrlRequestPort.trajCtrlActive_nu",), "type": float},
            "ApDrivingModeReq": {"string": ("trajCtrlRequestPort.drivingModeReq_nu",), "type": float},
            "ApUsecase": {"string": ("evaluationPort.useCase_nu",), "type": float},
            "NbCrevSteps": {"string": ("evaluationPort.TRJPLA_numberOfCrvSteps",), "type": float},
            "ActNbStrokesGreaterMaxNbStrokes": {
                "string": ("currentNrOfStrokesGreaterThanMaxNrOfSrokes_bool",),
                "type": float,
            },
            "latDiffOptimalTP_FinalEgoPose": {
                "string": ("testEvaluation.latDiffOptimalTP_FinalEgoPose_m",),
                "type": float,
            },
            "longDiffOptimalTP_FinalEgoPose": {
                "string": ("testEvaluation.longDiffOptimalTP_FinalEgoPose_m",),
                "type": float,
            },
            "yawDiffOptimalTP_FinalEgoPose": {
                "string": ("testEvaluation.yawDiffOptimalTP_FinalEgoPose_deg",),
                "type": float,
            },
            "steerAngReq_rad": {"string": ("steerCtrlRequestPort.steerAngReq_rad",), "type": float},
            "userActionHeadUnit_nu": {"string": ("hmiOutputPort.userActionHeadUnit_nu",), "type": float},
            "allowedManeuveringSpaceExceed_bool": {"string": ("allowedManeuveringSpaceExceed_bool",), "type": float},
            "headUnitVisu_message_nu": {"string": ("headUnitVisualizationPort.message_nu",), "type": float},
            "t_sim_max_s": {"string": ("evaluationPort.t_sim_max_s",), "type": float},
            "n_strokes_max_nu": {"string": ("evaluationPort.n_strokes_max_nu",), "type": float},
            "maxCycleTimeOfAUPStep_ms": {"string": ("maxCycleTimeOfAUPStep_ms",), "type": float},
            "ReachedStatus": {"string": ("targetPosesPort.selectedPoseData.reachedStatus",), "type": float},
            "LatDistToTarget": {
                "string": ("evaluationPort.egoPoseTargetPoseDeviation.latDistToTarget_m",),
                "type": float,
            },
            "LongDistToTarget": {
                "string": ("evaluationPort.egoPoseTargetPoseDeviation.longDistToTarget_m",),
                "type": float,
            },
            "YawDiffToTarget": {
                "string": ("evaluationPort.egoPoseTargetPoseDeviation.yawDiffToTarget_rad",),
                "type": float,
            },
            "LatMaxDeviation": {"string": ("evaluationPort.latMaxDeviation_m",), "type": float},
            "LongMaxDeviation": {"string": ("evaluationPort.longMaxDeviation_m",), "type": float},
            "YawMaxDeviation": {"string": ("evaluationPort.yawMaxDeviation_rad",), "type": float},
            "numValidParkingBoxes_nu": {"string": ("parkingBoxPort.numValidParkingBoxes_nu",), "type": float},
            "parkingBox0": {"string": ("parkingBoxPort.parkingBoxes_0.parkingBoxID_nu",), "type": float},
            "NumberOfStrokes": {"string": ("numberOfStrokes",), "type": int},
            "trajCtrlRequestPort": {"string": ("trajCtrlRequestPort.remoteReq_nu",), "type": float},
            "wheelAngleAcceleration": {"string": ("steeringWheelAngleAcceleration",), "type": float},
            "longDiffOptimalTP_TargetPose": {
                "string": ("testEvaluation.longDiffOptimalTP_TargetPose_m",),
                "type": float,
            },
            "latDiffOptimalTP_TargetPose": {"string": ("testEvaluation.latDiffOptimalTP_TargetPose_m",), "type": float},
            "yawDiffOptimalTP_TargetPose": {
                "string": ("testEvaluation.yawDiffOptimalTP_TargetPose_deg",),
                "type": float,
            },
            "stateVarPPC": {"string": ("psmDebugPort.stateVarPPC_nu",), "type": int},
            "stateVarESM": {"string": ("psmDebugPort.stateVarESM_nu",), "type": int},
            "stateVarVSM": {"string": ("psmDebugPort.stateVarVSM_nu",), "type": int},
            "stateVarDM": {"string": ("psmDebugPort.stateVarDM_nu",), "type": int},
            "stateVarRDM": {"string": ("psmDebugPort.stateVarRDM_nu",), "type": int},
            "car_outside_PB": {"string": ("evaluationPort.car_outside_PB",), "type": int},
            "staticStructColidesTarget_Pose_0": {
                "string": ("evaluationPort.staticStructColidesTarget_Pose_0",),
                "type": int,
            },
            "staticStructColidesTarget_Pose_1": {
                "string": ("evaluationPort.staticStructColidesTarget_Pose_1",),
                "type": int,
            },
            "staticStructColidesTarget_Pose_2": {
                "string": ("evaluationPort.staticStructColidesTarget_Pose_2",),
                "type": int,
            },
            "staticStructColidesTarget_Pose_3": {
                "string": ("evaluationPort.staticStructColidesTarget_Pose_3",),
                "type": int,
            },
            "staticStructColidesTarget_Pose_4": {
                "string": ("evaluationPort.staticStructColidesTarget_Pose_4",),
                "type": int,
            },
            "staticStructColidesTarget_Pose_5": {
                "string": ("evaluationPort.staticStructColidesTarget_Pose_5",),
                "type": int,
            },
            "staticStructColidesTarget_Pose_6": {
                "string": ("evaluationPort.staticStructColidesTarget_Pose_6",),
                "type": int,
            },
            "staticStructColidesTarget_Pose_7": {
                "string": ("evaluationPort.staticStructColidesTarget_Pose_7",),
                "type": int,
            },
            "lscaDisabled": {"string": ("lscaDisabled_nu",), "type": int},
            # ENTRY
            "TimeStamp": {"string": ("TimeStamp",), "type": float},
            "EgoMotionPort": {"string": ("EgoMotionPort.vel_mps",), "type": float},
            "PSMDebugPort": {"string": ("PSMDebugPort.stateVarPPC_nu",), "type": float},
            "ppcParkingMode": {"string": ("CtrlCommandPort.ppcParkingMode_nu",), "type": float},
            "ParkingScenario": {"string": ("ApParkingBoxPort.parkingBoxes[0].parkingScenario_nu",), "type": float},
            "NumberOfValidParkingBoxes": {"string": ("ApParkingBoxPort.numValidParkingBoxes_nu",), "type": float},
            "NumberOfKmDriven": {"string": ("EgoMotionPort.drivenDistance_m",), "type": float},
            "NumValidSegments": {"string": ("TrajPlanVisuPort.numValidSegments",), "type": float},
            #
            "DrvDir0": {"string": ("TrajPlanVisuPort.plannedGeometricPath[0].drvDir",), "type": float},
            "DrvDir1": {"string": ("TrajPlanVisuPort.plannedGeometricPath[1].drvDir",), "type": float},
            "DrvDir2": {"string": ("TrajPlanVisuPort.plannedGeometricPath[2].drvDir",), "type": float},
            "DrvDir3": {"string": ("TrajPlanVisuPort.plannedGeometricPath[3].drvDir",), "type": float},
            "DrvDir4": {"string": ("TrajPlanVisuPort.plannedGeometricPath[4].drvDir",), "type": float},
            "DrvDir5": {"string": ("TrajPlanVisuPort.plannedGeometricPath[5].drvDir",), "type": float},
            "DrvDir6": {"string": ("TrajPlanVisuPort.plannedGeometricPath[6].drvDir",), "type": float},
            "DrvDir7": {"string": ("TrajPlanVisuPort.plannedGeometricPath[7].drvDir",), "type": float},
            "DrvDir8": {"string": ("TrajPlanVisuPort.plannedGeometricPath[8].drvDir",), "type": float},
            "DrvDir9": {"string": ("TrajPlanVisuPort.plannedGeometricPath[9].drvDir",), "type": float},
            "DrvDir10": {"string": ("TrajPlanVisuPort.plannedGeometricPath[10].drvDir",), "type": float},
            "DrvDir11": {"string": ("TrajPlanVisuPort.plannedGeometricPath[11].drvDir",), "type": float},
            "DrvDir12": {"string": ("TrajPlanVisuPort.plannedGeometricPath[12].drvDir",), "type": float},
            "DrvDir13": {"string": ("TrajPlanVisuPort.plannedGeometricPath[13].drvDir",), "type": float},
            "DrvDir14": {"string": ("TrajPlanVisuPort.plannedGeometricPath[14].drvDir",), "type": float},
            "DrvDir15": {"string": ("TrajPlanVisuPort.plannedGeometricPath[15].drvDir",), "type": float},
            "DrvDir16": {"string": ("TrajPlanVisuPort.plannedGeometricPath[16].drvDir",), "type": float},
            "DrvDir17": {"string": ("TrajPlanVisuPort.plannedGeometricPath[17].drvDir",), "type": float},
            "DrvDir18": {"string": ("TrajPlanVisuPort.plannedGeometricPath[18].drvDir",), "type": float},
            "DrvDir19": {"string": ("TrajPlanVisuPort.plannedGeometricPath[19].drvDir",), "type": float},
            "DrvDir20": {"string": ("TrajPlanVisuPort.plannedGeometricPath[20].drvDir",), "type": float},
            "DrvDir21": {"string": ("TrajPlanVisuPort.plannedGeometricPath[21].drvDir",), "type": float},
            "DrvDir22": {"string": ("TrajPlanVisuPort.plannedGeometricPath[22].drvDir",), "type": float},
            "DrvDir23": {"string": ("TrajPlanVisuPort.plannedGeometricPath[23].drvDir",), "type": float},
            "DrvDir24": {"string": ("TrajPlanVisuPort.plannedGeometricPath[24].drvDir",), "type": float},
            "NumberValidStaticObjects": {"string": ("CollEnvModelPort.numberOfStaticObjects_u8",), "type": float},
            "SlotCoordinates": {"string": ("ApParkingBoxPort.parkingBoxes[0].slotCoordinates_m",), "type": float},
            "SlotCoordinates1": {"string": ("ApParkingBoxPort.parkingBoxes[1].slotCoordinates_m",), "type": float},
            "SlotCoordinates2": {"string": ("ApParkingBoxPort.parkingBoxes[2].slotCoordinates_m",), "type": float},
            "EgoPositionAP": {"string": ("ApEnvModelPort.egoVehiclePoseForAP",), "type": float},
            "TransfToOdom": {"string": ("ApEnvModelPort.transformationToOdometry",), "type": float},
            "StaticObjectShape0": {"string": ("CollEnvModelPort.staticObjects[0].objShape_m",), "type": float},
            "StaticObjectShape1": {"string": ("CollEnvModelPort.staticObjects[1].objShape_m",), "type": float},
            "StaticObjectShape2": {"string": ("CollEnvModelPort.staticObjects[2].objShape_m",), "type": float},
            "StaticObjectShape3": {"string": ("CollEnvModelPort.staticObjects[3].objShape_m",), "type": float},
            "StaticObjectShape4": {"string": ("CollEnvModelPort.staticObjects[4].objShape_m",), "type": float},
            "StaticObjectShape5": {"string": ("CollEnvModelPort.staticObjects[5].objShape_m",), "type": float},
            "StaticObjectShape6": {"string": ("CollEnvModelPort.staticObjects[6].objShape_m",), "type": float},
            "StaticObjectShape7": {"string": ("CollEnvModelPort.staticObjects[7].objShape_m",), "type": float},
            "StaticObjectShape8": {"string": ("CollEnvModelPort.staticObjects[8].objShape_m",), "type": float},
            "StaticObjectShape9": {"string": ("CollEnvModelPort.staticObjects[9].objShape_m",), "type": float},
            "StaticObjectShape10": {"string": ("CollEnvModelPort.staticObjects[10].objShape_m",), "type": float},
            "StaticObjectShape11": {"string": ("CollEnvModelPort.staticObjects[11].objShape_m",), "type": float},
            "StaticObjectShape12": {"string": ("CollEnvModelPort.staticObjects[12].objShape_m",), "type": float},
            "StaticObjectShape13": {"string": ("CollEnvModelPort.staticObjects[13].objShape_m",), "type": float},
            "StaticObjectShape14": {"string": ("CollEnvModelPort.staticObjects[14].objShape_m",), "type": float},
            "StaticObjectShape15": {"string": ("CollEnvModelPort.staticObjects[15].objShape_m",), "type": float},
            "StaticObjectShape16": {"string": ("CollEnvModelPort.staticObjects[16].objShape_m",), "type": float},
            "StaticObjectShape17": {"string": ("CollEnvModelPort.staticObjects[17].objShape_m",), "type": float},
            "StaticObjectShape18": {"string": ("CollEnvModelPort.staticObjects[18].objShape_m",), "type": float},
            "StaticObjectShape19": {"string": ("CollEnvModelPort.staticObjects[19].objShape_m",), "type": float},
            "StaticObjectShape20": {"string": ("CollEnvModelPort.staticObjects[20].objShape_m",), "type": float},
            "StaticObjectShape21": {"string": ("CollEnvModelPort.staticObjects[21].objShape_m",), "type": float},
            "StaticObjectShape22": {"string": ("CollEnvModelPort.staticObjects[22].objShape_m",), "type": float},
            "StaticObjectShape23": {"string": ("CollEnvModelPort.staticObjects[23].objShape_m",), "type": float},
            "StaticObjectShape24": {"string": ("CollEnvModelPort.staticObjects[24].objShape_m",), "type": float},
            "StaticObjectShape25": {"string": ("CollEnvModelPort.staticObjects[25].objShape_m",), "type": float},
            "StaticObjectShape26": {"string": ("CollEnvModelPort.staticObjects[26].objShape_m",), "type": float},
            "StaticObjectShape27": {"string": ("CollEnvModelPort.staticObjects[27].objShape_m",), "type": float},
            "StaticObjectShape28": {"string": ("CollEnvModelPort.staticObjects[28].objShape_m",), "type": float},
            "StaticObjectShape29": {"string": ("CollEnvModelPort.staticObjects[29].objShape_m",), "type": float},
            "StaticObjectShape30": {"string": ("CollEnvModelPort.staticObjects[30].objShape_m",), "type": float},
            "StaticObjectShape31": {"string": ("CollEnvModelPort.staticObjects[31].objShape_m",), "type": float},
            "DgpsHunterX": {"string": ("RangeHunterPosLocal.RangeHunterPosLocalX",), "type": float},
            "DgpsHunterY": {"string": ("RangeHunterPosLocal.RangeHunterPosLocalY",), "type": float},
            "DgpsTargetX": {"string": ("RangeTargetPosLocal.RangeTargetPosLocalX",), "type": float},
            "DgpsTargetY": {"string": ("RangeTargetPosLocal.RangeTargetPosLocalY",), "type": float},
            "DgpsTarget2X": {"string": ("Range2TargetPosLocal.Range2TargetPosLocalX",), "type": float},
            "DgpsTarget2Y": {"string": ("Range2TargetPosLocal.Range2TargetPosLocalY",), "type": float},
            "DgpsTarget3X": {"string": ("Range3TargetPosLocal.Range3TargetPosLocalX",), "type": float},
            "DgpsTarget3Y": {"string": ("Range3TargetPosLocal.Range3TargetPosLocalY",), "type": float},
            "DgpsTarget4X": {"string": ("Range4TargetPosLocal.Range4TargetPosLocalX",), "type": float},
            "DgpsTarget4Y": {"string": ("Range4TargetPosLocal.Range4TargetPosLocalY",), "type": float},
            "DgpsEgoYaw": {"string": ("HeadingPitchRoll.AngleHeading",), "type": float},
            "OdoEstimX": {"string": ("OdoEstimationPort.xPosition_m",), "type": float},
            "OdoEstimY": {"string": ("OdoEstimationPort.yPosition_m",), "type": float},
            "RtaRefTsUs": {"string": ("RTA_BUFFER_0.u_RefTs_us",), "type": float},
            "RtaMaxEventIndex": {"string": ("RTA_BUFFER_0.u_MaxEventIndex",), "type": float},
        }


class ExampleSignals(SignalDefinition):
    """Example signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        APODOCMREFXPOSM = "ApOdoCmRefXPosM"
        APODOCMREFYPOSM = "ApOdoCmRefYPosM"
        APODOCMREFYAWANGRAD = "ApOdoCmRefYawAngRad"
        APODOESTIMYAWANGRAD = "ApOdoEstimYawAngRad"
        APODOESTIMXPOSM = "ApOdoEstimXPosM"
        APODOESTIMYPOSM = "ApOdoEstimYPosM"
        APODOESTIMYAWRATERADPS = "ApOdoEstimYawRateRadps"
        LONGIVELOCITY = "longiVelocity"
        STEERANGFRONTAXLE_RAD = "steerAngFrontAxle_rad"
        MOTIONSTATUS_NU = "motionStatus_nu"
        STEERINGWHEELANGLE_RAD = "steeringWheelAngle_rad"
        STEERINGWHEELANGLEVELOCITY_RADPS = "steeringWheelAngleVelocity_radps"
        LATERALACCELERATION_MPS2 = "lateralAcceleration_mps2"
        LONGITUDINALACCELERATION_MPS2 = "longitudinalAcceleration_mps2"
        YAWRATE_RADPS = "yawRate_radps"
        PITCHANGLE_RAD = "pitchAngle_rad"
        HEADUNITVISU_SCREEN_NU = "headUnitVisu_screen_nu"
        APSTATE = "ApState"
        ORIENTATIONERROR = "OrientationError"
        LATERALERROR = "LateralError"
        APDISTTOSTOPREQINTEREXTRAPOLTRAJ = "ApDistToStopReqInterExtrapolTraj"
        APTRAJCTRLACTIVE = "ApTrajCtrlActive"
        APDRIVINGMODEREQ = "ApDrivingModeReq"
        APUSECASE = "ApUsecase"
        NBCREVSTEPS = "NbCrevSteps"
        ACTNBSTROKESGREATERMAXNBSTROKES = "ActNbStrokesGreaterMaxNbStrokes"
        LATDIFFOPTIMALTP_FINALEGOPOSE = "latDiffOptimalTP_FinalEgoPose"
        LONGDIFFOPTIMALTP_FINALEGOPOSE = "longDiffOptimalTP_FinalEgoPose"
        YAWDIFFOPTIMALTP_FINALEGOPOSE = "yawDiffOptimalTP_FinalEgoPose"
        STEERANGREQ_RAD = "steerAngReq_rad"
        USERACTIONHEADUNIT_NU = "userActionHeadUnit_nu"
        ALLOWEDMANEUVERINGSPACEEXCEED_BOOL = "allowedManeuveringSpaceExceed_bool"
        HEADUNITVISU_MESSAGE_NU = "headUnitVisu_message_nu"
        T_SIM_MAX_S = "t_sim_max_s"
        N_STROKES_MAX_NU = "n_strokes_max_nu"
        MAXCYCLETIMEOFAUPSTEP_MS = "maxCycleTimeOfAUPStep_ms"
        REACHEDSTATUS = "ReachedStatus"
        LATDISTTOTARGET = "LatDistToTarget"
        LONGDISTTOTARGET = "LongDistToTarget"
        YAWDIFFTOTARGET = "YawDiffToTarget"
        LATMAXDEVIATION = "LatMaxDeviation"
        LONGMAXDEVIATION = "LongMaxDeviation"
        YAWMAXDEVIATION = "YawMaxDeviation"
        NUMVALIDPARKINGBOXES_NU = "numValidParkingBoxes_nu"
        PARKINGBOX0 = "parkingBox0"
        NUMBEROFSTROKES = "NumberOfStrokes"
        TRAJCTRLREQUESTPORT = "trajCtrlRequestPort"
        WHEELANGLEACCELERATION = "wheelAngleAcceleration"
        LONGDIFFOPTIMALTP_TARGETPOSE = "longDiffOptimalTP_TargetPose"
        LATDIFFOPTIMALTP_TARGETPOSE = "latDiffOptimalTP_TargetPose"
        YAWDIFFOPTIMALTP_TARGETPOSE = "yawDiffOptimalTP_TargetPose"
        STATEVARPPC = "stateVarPPC"
        STATEVARESM = "stateVarESM"
        STATEVARVSM = "stateVarVSM"
        STATEVARDM = "stateVarDM"
        STATEVARRDM = "stateVarRDM"
        CAR_OUTSIDE_PB = "car_outside_PB"
        STATICSTRUCTCOLIDESTARGET_POSE_0 = "staticStructColidesTarget_Pose_0"
        STATICSTRUCTCOLIDESTARGET_POSE_1 = "staticStructColidesTarget_Pose_1"
        STATICSTRUCTCOLIDESTARGET_POSE_2 = "staticStructColidesTarget_Pose_2"
        STATICSTRUCTCOLIDESTARGET_POSE_3 = "staticStructColidesTarget_Pose_3"
        STATICSTRUCTCOLIDESTARGET_POSE_4 = "staticStructColidesTarget_Pose_4"
        STATICSTRUCTCOLIDESTARGET_POSE_5 = "staticStructColidesTarget_Pose_5"
        STATICSTRUCTCOLIDESTARGET_POSE_6 = "staticStructColidesTarget_Pose_6"
        STATICSTRUCTCOLIDESTARGET_POSE_7 = "staticStructColidesTarget_Pose_7"
        LSCADISABLED = "lscaDisabled"
        TIMESTAMP = "TimeStamp"
        EGOMOTIONPORT = "EgoMotionPort"
        PSMDEBUGPORT = "PSMDebugPort"
        PPCPARKINGMODE = "ppcParkingMode"
        PARKINGSCENARIO = "ParkingScenario"
        NUMBEROFVALIDPARKINGBOXES = "NumberOfValidParkingBoxes"
        NUMBEROFKMDRIVEN = "NumberOfKmDriven"
        NUMVALIDSEGMENTS = "NumValidSegments"
        DRVDIR0 = "DrvDir0"
        DRVDIR1 = "DrvDir1"
        DRVDIR2 = "DrvDir2"
        DRVDIR3 = "DrvDir3"
        DRVDIR4 = "DrvDir4"
        DRVDIR5 = "DrvDir5"
        DRVDIR6 = "DrvDir6"
        DRVDIR7 = "DrvDir7"
        DRVDIR8 = "DrvDir8"
        DRVDIR9 = "DrvDir9"
        DRVDIR10 = "DrvDir10"
        DRVDIR11 = "DrvDir11"
        DRVDIR12 = "DrvDir12"
        DRVDIR13 = "DrvDir13"
        DRVDIR14 = "DrvDir14"
        DRVDIR15 = "DrvDir15"
        DRVDIR16 = "DrvDir16"
        DRVDIR17 = "DrvDir17"
        DRVDIR18 = "DrvDir18"
        DRVDIR19 = "DrvDir19"
        DRVDIR20 = "DrvDir20"
        DRVDIR21 = "DrvDir21"
        DRVDIR22 = "DrvDir22"
        DRVDIR23 = "DrvDir23"
        DRVDIR24 = "DrvDir24"
        NUMBERVALIDSTATICOBJECTS = "NumberValidStaticObjects"
        SLOTCOORDINATES = "SlotCoordinates"
        SLOTCOORDINATES1 = "SlotCoordinates1"
        SLOTCOORDINATES2 = "SlotCoordinates2"
        EGOPOSITIONAP = "EgoPositionAP"
        TRANSFTOODOM = "TransfToOdom"
        STATICOBJECTSHAPE0 = "StaticObjectShape0"
        STATICOBJECTSHAPE1 = "StaticObjectShape1"
        STATICOBJECTSHAPE2 = "StaticObjectShape2"
        STATICOBJECTSHAPE3 = "StaticObjectShape3"
        STATICOBJECTSHAPE4 = "StaticObjectShape4"
        STATICOBJECTSHAPE5 = "StaticObjectShape5"
        STATICOBJECTSHAPE6 = "StaticObjectShape6"
        STATICOBJECTSHAPE7 = "StaticObjectShape7"
        STATICOBJECTSHAPE8 = "StaticObjectShape8"
        STATICOBJECTSHAPE9 = "StaticObjectShape9"
        STATICOBJECTSHAPE10 = "StaticObjectShape10"
        STATICOBJECTSHAPE11 = "StaticObjectShape11"
        STATICOBJECTSHAPE12 = "StaticObjectShape12"
        STATICOBJECTSHAPE13 = "StaticObjectShape13"
        STATICOBJECTSHAPE14 = "StaticObjectShape14"
        STATICOBJECTSHAPE15 = "StaticObjectShape15"
        STATICOBJECTSHAPE16 = "StaticObjectShape16"
        STATICOBJECTSHAPE17 = "StaticObjectShape17"
        STATICOBJECTSHAPE18 = "StaticObjectShape18"
        STATICOBJECTSHAPE19 = "StaticObjectShape19"
        STATICOBJECTSHAPE20 = "StaticObjectShape20"
        STATICOBJECTSHAPE21 = "StaticObjectShape21"
        STATICOBJECTSHAPE22 = "StaticObjectShape22"
        STATICOBJECTSHAPE23 = "StaticObjectShape23"
        STATICOBJECTSHAPE24 = "StaticObjectShape24"
        STATICOBJECTSHAPE25 = "StaticObjectShape25"
        STATICOBJECTSHAPE26 = "StaticObjectShape26"
        STATICOBJECTSHAPE27 = "StaticObjectShape27"
        STATICOBJECTSHAPE28 = "StaticObjectShape28"
        STATICOBJECTSHAPE29 = "StaticObjectShape29"
        STATICOBJECTSHAPE30 = "StaticObjectShape30"
        STATICOBJECTSHAPE31 = "StaticObjectShape31"
        DGPSHUNTERX = "DgpsHunterX"
        DGPSHUNTERY = "DgpsHunterY"
        DGPSTARGETX = "DgpsTargetX"
        DGPSTARGETY = "DgpsTargetY"
        DGPSTARGET2X = "DgpsTarget2X"
        DGPSTARGET2Y = "DgpsTarget2Y"
        DGPSTARGET3X = "DgpsTarget3X"
        DGPSTARGET3Y = "DgpsTarget3Y"
        DGPSTARGET4X = "DgpsTarget4X"
        DGPSTARGET4Y = "DgpsTarget4Y"
        DGPSEGOYAW = "DgpsEgoYaw"
        ODOESTIMX = "OdoEstimX"
        ODOESTIMY = "OdoEstimY"
        RTAREFTSUS = "RtaRefTsUs"
        RTAMAXEVENTINDEX = "RtaMaxEventIndex"
        CAR_VX = "Car_vx"
        CARYAWRATE = "CarYawRate"
        LATSLOPE = "LatSlope"
        COLLISIONCOUNT = "CollisionCount"
        LONGSLOPE = "LongSlope"
        TIME = "time"
        CAR_AX = "Car_ax"
        CAR_AY = "Car_ay"
        VHCL_V = "Vhcl_v"
        VHCLYAWRATE = "VhclYawRate"
        VEHICLEROAD = "VehicleRoad"
        PARKINGLANEMARKING = "ParkingLaneMarking"
        ODOROAD = "OdoRoad"
        LSCAREQUESTMODE = "lscaRequestMode"
        BRAKEMODESTATE = "brakeModeState"
        CAR_V = "Car_v"
        CAR_VX = "Car_vx"
        CARYAWRATE = "CarYawRate"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = [
            "AP",
            "MTS.Package",
            "M7board.EM_Thread",
            "Reference_CAN.RT-Range_2017_02_28_SystemC",
            "Reference_CAN.NAVconfig_AP_Passat_154_28-02-2017",
            "M7board.CAN_Thread",
        ]

        self._properties = {
            self.Columns.APODOCMREFXPOSM: ".odoDebugPort.odoCmRefxPosition_m",
            self.Columns.APODOCMREFYPOSM: ".odoDebugPort.odoCmRefyPosition_m",
            self.Columns.APODOCMREFYAWANGRAD: ".odoDebugPort.odoCmRefyawAngEgoRaCur_rad",
            self.Columns.APODOESTIMYAWANGRAD: ".odoEstimationPort.yawAngle_rad",
            self.Columns.APODOESTIMXPOSM: ".odoEstimationPort.xPosition_m",
            self.Columns.APODOESTIMYPOSM: ".odoEstimationPort.yPosition_m",
            self.Columns.APODOESTIMYAWRATERADPS: ".odoEstimationPort.yawRate_radps",
            self.Columns.LONGIVELOCITY: ".odoEstimationPort.longiVelocity_mps",
            self.Columns.STEERANGFRONTAXLE_RAD: ".odoEstimationPortCM.steerAngFrontAxle_rad",
            self.Columns.MOTIONSTATUS_NU: ".odoEstimationPort.motionStatus_nu",
            self.Columns.STEERINGWHEELANGLE_RAD: ".odoInputPort.odoSigFcanPort.steerCtrlStatus.steeringWheelAngle_rad",
            self.Columns.STEERINGWHEELANGLEVELOCITY_RADPS: ".odoInputPort.odoSigFcanPort.steerCtrlStatus.steeringWheelAngleVelocity_radps",
            self.Columns.LATERALACCELERATION_MPS2: ".odoInputPort.odoSigFcanPort.vehDynamics.lateralAcceleration_mps2",
            self.Columns.LONGITUDINALACCELERATION_MPS2: ".odoInputPort.odoSigFcanPort.vehDynamics.longitudinalAcceleration_mps2",
            self.Columns.YAWRATE_RADPS: ".odoEstimationPort.yawRate_radps",
            self.Columns.PITCHANGLE_RAD: ".odoEstimationPort.pitchAngle_rad",
            self.Columns.HEADUNITVISU_SCREEN_NU: ".headUnitVisualizationPort.screen_nu",
            self.Columns.APSTATE: ".planningCtrlPort.apStates",
            self.Columns.ORIENTATIONERROR: ".trajCtrlDebugPort.orientationError_rad",
            self.Columns.LATERALERROR: ".trajCtrlDebugPort.currentDeviation_m",
            self.Columns.APDISTTOSTOPREQINTEREXTRAPOLTRAJ: ".evaluationPort.distanceToStopReqInterExtrapolTraj_m",
            self.Columns.APTRAJCTRLACTIVE: ".trajCtrlRequestPort.trajCtrlActive_nu",
            self.Columns.APDRIVINGMODEREQ: ".trajCtrlRequestPort.drivingModeReq_nu",
            self.Columns.APUSECASE: ".evaluationPort.useCase_nu",
            self.Columns.NBCREVSTEPS: ".evaluationPort.TRJPLA_numberOfCrvSteps",
            self.Columns.ACTNBSTROKESGREATERMAXNBSTROKES: ".currentNrOfStrokesGreaterThanMaxNrOfSrokes_bool",
            self.Columns.LATDIFFOPTIMALTP_FINALEGOPOSE: ".testEvaluation.latDiffOptimalTP_FinalEgoPose_m",
            self.Columns.LONGDIFFOPTIMALTP_FINALEGOPOSE: ".testEvaluation.longDiffOptimalTP_FinalEgoPose_m",
            self.Columns.YAWDIFFOPTIMALTP_FINALEGOPOSE: ".testEvaluation.yawDiffOptimalTP_FinalEgoPose_deg",
            self.Columns.STEERANGREQ_RAD: ".steerCtrlRequestPort.steerAngReq_rad",
            self.Columns.USERACTIONHEADUNIT_NU: ".hmiOutputPort.userActionHeadUnit_nu",
            self.Columns.ALLOWEDMANEUVERINGSPACEEXCEED_BOOL: ".allowedManeuveringSpaceExceed_bool",
            self.Columns.HEADUNITVISU_MESSAGE_NU: ".headUnitVisualizationPort.message_nu",
            self.Columns.T_SIM_MAX_S: ".evaluationPort.t_sim_max_s",
            self.Columns.N_STROKES_MAX_NU: ".evaluationPort.n_strokes_max_nu",
            self.Columns.MAXCYCLETIMEOFAUPSTEP_MS: ".maxCycleTimeOfAUPStep_ms",
            self.Columns.REACHEDSTATUS: ".targetPosesPort.selectedPoseData.reachedStatus",
            self.Columns.LATDISTTOTARGET: ".evaluationPort.egoPoseTargetPoseDeviation.latDistToTarget_m",
            self.Columns.LONGDISTTOTARGET: ".evaluationPort.egoPoseTargetPoseDeviation.longDistToTarget_m",
            self.Columns.YAWDIFFTOTARGET: ".evaluationPort.egoPoseTargetPoseDeviation.yawDiffToTarget_rad",
            self.Columns.LATMAXDEVIATION: ".evaluationPort.latMaxDeviation_m",
            self.Columns.LONGMAXDEVIATION: ".evaluationPort.longMaxDeviation_m",
            self.Columns.YAWMAXDEVIATION: ".evaluationPort.yawMaxDeviation_rad",
            self.Columns.NUMVALIDPARKINGBOXES_NU: ".parkingBoxPort.numValidParkingBoxes_nu",
            self.Columns.PARKINGBOX0: ".parkingBoxPort.parkingBoxes_0.parkingBoxID_nu",
            self.Columns.NUMBEROFSTROKES: ".numberOfStrokes",
            self.Columns.TRAJCTRLREQUESTPORT: ".trajCtrlRequestPort.remoteReq_nu",
            self.Columns.WHEELANGLEACCELERATION: ".steeringWheelAngleAcceleration",
            self.Columns.LONGDIFFOPTIMALTP_TARGETPOSE: ".testEvaluation.longDiffOptimalTP_TargetPose_m",
            self.Columns.LATDIFFOPTIMALTP_TARGETPOSE: ".testEvaluation.latDiffOptimalTP_TargetPose_m",
            self.Columns.YAWDIFFOPTIMALTP_TARGETPOSE: ".testEvaluation.yawDiffOptimalTP_TargetPose_deg",
            self.Columns.STATEVARPPC: ".psmDebugPort.stateVarPPC_nu",
            self.Columns.STATEVARESM: ".psmDebugPort.stateVarESM_nu",
            self.Columns.STATEVARVSM: ".psmDebugPort.stateVarVSM_nu",
            self.Columns.STATEVARDM: ".psmDebugPort.stateVarDM_nu",
            self.Columns.STATEVARRDM: ".psmDebugPort.stateVarRDM_nu",
            self.Columns.CAR_OUTSIDE_PB: ".evaluationPort.car_outside_PB",
            self.Columns.STATICSTRUCTCOLIDESTARGET_POSE_0: ".evaluationPort.staticStructColidesTarget_Pose_0",
            self.Columns.STATICSTRUCTCOLIDESTARGET_POSE_1: ".evaluationPort.staticStructColidesTarget_Pose_1",
            self.Columns.STATICSTRUCTCOLIDESTARGET_POSE_2: ".evaluationPort.staticStructColidesTarget_Pose_2",
            self.Columns.STATICSTRUCTCOLIDESTARGET_POSE_3: ".evaluationPort.staticStructColidesTarget_Pose_3",
            self.Columns.STATICSTRUCTCOLIDESTARGET_POSE_4: ".evaluationPort.staticStructColidesTarget_Pose_4",
            self.Columns.STATICSTRUCTCOLIDESTARGET_POSE_5: ".evaluationPort.staticStructColidesTarget_Pose_5",
            self.Columns.STATICSTRUCTCOLIDESTARGET_POSE_6: ".evaluationPort.staticStructColidesTarget_Pose_6",
            self.Columns.STATICSTRUCTCOLIDESTARGET_POSE_7: ".evaluationPort.staticStructColidesTarget_Pose_7",
            self.Columns.LSCADISABLED: ".lscaDisabled_nu",
            self.Columns.TIMESTAMP: ".TimeStamp",
            self.Columns.EGOMOTIONPORT: ".EgoMotionPort.vel_mps",
            self.Columns.PSMDEBUGPORT: ".PSMDebugPort.stateVarPPC_nu",
            self.Columns.PPCPARKINGMODE: ".CtrlCommandPort.ppcParkingMode_nu",
            self.Columns.PARKINGSCENARIO: ".ApParkingBoxPort.parkingBoxes[0].parkingScenario_nu",
            self.Columns.NUMBEROFVALIDPARKINGBOXES: ".ApParkingBoxPort.numValidParkingBoxes_nu",
            self.Columns.NUMBEROFKMDRIVEN: ".EgoMotionPort.drivenDistance_m",
            self.Columns.NUMVALIDSEGMENTS: ".TrajPlanVisuPort.numValidSegments",
            self.Columns.DRVDIR0: ".TrajPlanVisuPort.plannedGeometricPath[0].drvDir",
            self.Columns.DRVDIR1: ".TrajPlanVisuPort.plannedGeometricPath[1].drvDir",
            self.Columns.DRVDIR2: ".TrajPlanVisuPort.plannedGeometricPath[2].drvDir",
            self.Columns.DRVDIR3: ".TrajPlanVisuPort.plannedGeometricPath[3].drvDir",
            self.Columns.DRVDIR4: ".TrajPlanVisuPort.plannedGeometricPath[4].drvDir",
            self.Columns.DRVDIR5: ".TrajPlanVisuPort.plannedGeometricPath[5].drvDir",
            self.Columns.DRVDIR6: ".TrajPlanVisuPort.plannedGeometricPath[6].drvDir",
            self.Columns.DRVDIR7: ".TrajPlanVisuPort.plannedGeometricPath[7].drvDir",
            self.Columns.DRVDIR8: ".TrajPlanVisuPort.plannedGeometricPath[8].drvDir",
            self.Columns.DRVDIR9: ".TrajPlanVisuPort.plannedGeometricPath[9].drvDir",
            self.Columns.DRVDIR10: ".TrajPlanVisuPort.plannedGeometricPath[10].drvDir",
            self.Columns.DRVDIR11: ".TrajPlanVisuPort.plannedGeometricPath[11].drvDir",
            self.Columns.DRVDIR12: ".TrajPlanVisuPort.plannedGeometricPath[12].drvDir",
            self.Columns.DRVDIR13: ".TrajPlanVisuPort.plannedGeometricPath[13].drvDir",
            self.Columns.DRVDIR14: ".TrajPlanVisuPort.plannedGeometricPath[14].drvDir",
            self.Columns.DRVDIR15: ".TrajPlanVisuPort.plannedGeometricPath[15].drvDir",
            self.Columns.DRVDIR16: ".TrajPlanVisuPort.plannedGeometricPath[16].drvDir",
            self.Columns.DRVDIR17: ".TrajPlanVisuPort.plannedGeometricPath[17].drvDir",
            self.Columns.DRVDIR18: ".TrajPlanVisuPort.plannedGeometricPath[18].drvDir",
            self.Columns.DRVDIR19: ".TrajPlanVisuPort.plannedGeometricPath[19].drvDir",
            self.Columns.DRVDIR20: ".TrajPlanVisuPort.plannedGeometricPath[20].drvDir",
            self.Columns.DRVDIR21: ".TrajPlanVisuPort.plannedGeometricPath[21].drvDir",
            self.Columns.DRVDIR22: ".TrajPlanVisuPort.plannedGeometricPath[22].drvDir",
            self.Columns.DRVDIR23: ".TrajPlanVisuPort.plannedGeometricPath[23].drvDir",
            self.Columns.DRVDIR24: ".TrajPlanVisuPort.plannedGeometricPath[24].drvDir",
            self.Columns.NUMBERVALIDSTATICOBJECTS: ".CollEnvModelPort.numberOfStaticObjects_u8",
            self.Columns.SLOTCOORDINATES: ".ApParkingBoxPort.parkingBoxes[0].slotCoordinates_m",
            self.Columns.SLOTCOORDINATES1: ".ApParkingBoxPort.parkingBoxes[1].slotCoordinates_m",
            self.Columns.SLOTCOORDINATES2: ".ApParkingBoxPort.parkingBoxes[2].slotCoordinates_m",
            self.Columns.EGOPOSITIONAP: ".ApEnvModelPort.egoVehiclePoseForAP",
            self.Columns.TRANSFTOODOM: ".ApEnvModelPort.transformationToOdometry",
            self.Columns.STATICOBJECTSHAPE0: ".CollEnvModelPort.staticObjects[0].objShape_m",
            self.Columns.STATICOBJECTSHAPE1: ".CollEnvModelPort.staticObjects[1].objShape_m",
            self.Columns.STATICOBJECTSHAPE2: ".CollEnvModelPort.staticObjects[2].objShape_m",
            self.Columns.STATICOBJECTSHAPE3: ".CollEnvModelPort.staticObjects[3].objShape_m",
            self.Columns.STATICOBJECTSHAPE4: ".CollEnvModelPort.staticObjects[4].objShape_m",
            self.Columns.STATICOBJECTSHAPE5: ".CollEnvModelPort.staticObjects[5].objShape_m",
            self.Columns.STATICOBJECTSHAPE6: ".CollEnvModelPort.staticObjects[6].objShape_m",
            self.Columns.STATICOBJECTSHAPE7: ".CollEnvModelPort.staticObjects[7].objShape_m",
            self.Columns.STATICOBJECTSHAPE8: ".CollEnvModelPort.staticObjects[8].objShape_m",
            self.Columns.STATICOBJECTSHAPE9: ".CollEnvModelPort.staticObjects[9].objShape_m",
            self.Columns.STATICOBJECTSHAPE10: ".CollEnvModelPort.staticObjects[10].objShape_m",
            self.Columns.STATICOBJECTSHAPE11: ".CollEnvModelPort.staticObjects[11].objShape_m",
            self.Columns.STATICOBJECTSHAPE12: ".CollEnvModelPort.staticObjects[12].objShape_m",
            self.Columns.STATICOBJECTSHAPE13: ".CollEnvModelPort.staticObjects[13].objShape_m",
            self.Columns.STATICOBJECTSHAPE14: ".CollEnvModelPort.staticObjects[14].objShape_m",
            self.Columns.STATICOBJECTSHAPE15: ".CollEnvModelPort.staticObjects[15].objShape_m",
            self.Columns.STATICOBJECTSHAPE16: ".CollEnvModelPort.staticObjects[16].objShape_m",
            self.Columns.STATICOBJECTSHAPE17: ".CollEnvModelPort.staticObjects[17].objShape_m",
            self.Columns.STATICOBJECTSHAPE18: ".CollEnvModelPort.staticObjects[18].objShape_m",
            self.Columns.STATICOBJECTSHAPE19: ".CollEnvModelPort.staticObjects[19].objShape_m",
            self.Columns.STATICOBJECTSHAPE20: ".CollEnvModelPort.staticObjects[20].objShape_m",
            self.Columns.STATICOBJECTSHAPE21: ".CollEnvModelPort.staticObjects[21].objShape_m",
            self.Columns.STATICOBJECTSHAPE22: ".CollEnvModelPort.staticObjects[22].objShape_m",
            self.Columns.STATICOBJECTSHAPE23: ".CollEnvModelPort.staticObjects[23].objShape_m",
            self.Columns.STATICOBJECTSHAPE24: ".CollEnvModelPort.staticObjects[24].objShape_m",
            self.Columns.STATICOBJECTSHAPE25: ".CollEnvModelPort.staticObjects[25].objShape_m",
            self.Columns.STATICOBJECTSHAPE26: ".CollEnvModelPort.staticObjects[26].objShape_m",
            self.Columns.STATICOBJECTSHAPE27: ".CollEnvModelPort.staticObjects[27].objShape_m",
            self.Columns.STATICOBJECTSHAPE28: ".CollEnvModelPort.staticObjects[28].objShape_m",
            self.Columns.STATICOBJECTSHAPE29: ".CollEnvModelPort.staticObjects[29].objShape_m",
            self.Columns.STATICOBJECTSHAPE30: ".CollEnvModelPort.staticObjects[30].objShape_m",
            self.Columns.STATICOBJECTSHAPE31: ".CollEnvModelPort.staticObjects[31].objShape_m",
            self.Columns.DGPSHUNTERX: ".RangeHunterPosLocal.RangeHunterPosLocalX",
            self.Columns.DGPSHUNTERY: ".RangeHunterPosLocal.RangeHunterPosLocalY",
            self.Columns.DGPSTARGETX: ".RangeTargetPosLocal.RangeTargetPosLocalX",
            self.Columns.DGPSTARGETY: ".RangeTargetPosLocal.RangeTargetPosLocalY",
            self.Columns.DGPSTARGET2X: ".Range2TargetPosLocal.Range2TargetPosLocalX",
            self.Columns.DGPSTARGET2Y: ".Range2TargetPosLocal.Range2TargetPosLocalY",
            self.Columns.DGPSTARGET3X: ".Range3TargetPosLocal.Range3TargetPosLocalX",
            self.Columns.DGPSTARGET3Y: ".Range3TargetPosLocal.Range3TargetPosLocalY",
            self.Columns.DGPSTARGET4X: ".Range4TargetPosLocal.Range4TargetPosLocalX",
            self.Columns.DGPSTARGET4Y: ".Range4TargetPosLocal.Range4TargetPosLocalY",
            self.Columns.DGPSEGOYAW: ".HeadingPitchRoll.AngleHeading",
            self.Columns.ODOESTIMX: ".OdoEstimationPort.xPosition_m",
            self.Columns.ODOESTIMY: ".OdoEstimationPort.yPosition_m",
            self.Columns.RTAREFTSUS: ".RTA_BUFFER_0.u_RefTs_us",
            self.Columns.RTAMAXEVENTINDEX: ".RTA_BUFFER_0.u_MaxEventIndex",
            self.Columns.CAR_VX: "Car.vx",
            self.Columns.CARYAWRATE: "Car.YawRate",
            self.Columns.LATSLOPE: "Car.Road.Route.LatSlope",
            self.Columns.COLLISIONCOUNT: "Sensor.Collision.Vhcl.Fr1.Count",
            self.Columns.LONGSLOPE: "Car.Road.Route.LongSlope",
            self.Columns.TIME: "Time",
            self.Columns.CAR_AX: "Car.ax",
            self.Columns.CAR_AY: "Car.ay",
            self.Columns.VHCL_V: "Vhcl.v",
            self.Columns.VHCLYAWRATE: "Vhcl.YawRate",
            self.Columns.VEHICLEROAD: "SI.trafficObject.Vehicle.sRoad",
            self.Columns.PARKINGLANEMARKING: "SI.trafficObject.parkingLaneMarking.sRoad",
            self.Columns.ODOROAD: "Traffic.Odo.sRoad",
            self.Columns.LSCAREQUESTMODE: "LSCA.brakePort.requestMode",
            self.Columns.BRAKEMODESTATE: "LSCA.statusPort.brakingModuleState_nu",
            self.Columns.CAR_V: "Car.v",
            self.Columns.CAR_VX: ".EgoMotionPort.vel_mps",
            self.Columns.CARYAWRATE: ".EgoMotionPort.yawRate_radps",
        }
