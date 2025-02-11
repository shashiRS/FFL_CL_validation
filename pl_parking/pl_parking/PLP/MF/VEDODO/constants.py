"""In constants.py file contains the signal names"""

from dataclasses import dataclass


@dataclass
class RadarSignalUrl:
    """This class contains Radar signals URLs"""

    drivenDistance: str = "CarPC.EM_Thread.EgoMotionPort.drivenDistance_m"


@dataclass
class CarMakerUrl:
    """This class contains Carmaker recordings signals URLs"""

    velocityX: str = "Car.vx"
    longitudinalVelocity_mps: str = "AP.odoEstimationPort.longiVelocity_mps"
    velocityY: str = "Car.vy"
    lateralVelocity_mps: str = "AP.odoEstimationPort.lateralVelocity_mps"
    time: str = "Time"
    yawrate_estimation: str = "AP.odoEstimationPort.yawRate_radps"
    yawrate_gt: str = "Car.YawRate"
    odoEstX: str = "AP.odoEstimationPort.xPosition_m"
    odoEstY: str = "AP.odoEstimationPort.yPosition_m"
    odoCmRefX: str = "AP.odoDebugPort.odoCmRefxPosition_m"
    odoCmRefY: str = "AP.odoDebugPort.odoCmRefyPosition_m"
    odoCmRefyawAngEgoRaCur: str = "AP.odoDebugPort.odoCmRefyawAngEgoRaCur_rad"
    yawAngle: str = "AP.odoEstimationPort.yawAngle_rad"
    drivenDistance_m: str = "AP.odoEstimationPort.drivenDistance_m"
    estVelocityX: str = "AP.odoEstimationPort.xVelocity_mps"
    estVelocityY: str = "AP.odoEstimationPort.yVelocity_mps"
    timeMicroSec: str = "AP.odoEstimationPort.sSigHeader.uiTimeStamp"
    longiAcceleration: str = "AP.odoEstimationPort.longiAcceleration_mps2"
    verticalAcceleration: str = "AP.odoEstimationPort.verticalAcceleration_mps2"
    lateralAcceleration: float = "AP.odoEstimationPort.lateralAcceleration_mps2"
    uiTimeStamp: str = "AP.odoEstimationPort.sSigHeader.uiTimeStamp"
    rollRate_estimation: str = "AP.odoEstimationPort.rollRate_radps"
    rollAngle_estimation: str = "AP.odoEstimationPort.rollAngle_rad"
    pitchAngle_estimation: str = "AP.odoEstimationPort.pitchAngle_rad"
    motionStatus: str = "AP.odoEstimationPort.motionStatus_nu"
    gt_pitchAngle: str = "Car.Pitch"
    az: str = "Car.az"
    ay: str = "Car.ay"
    ax: str = "Car.ax"
    gt_yawAngle: str = "Car.Yaw"
    gt_rollAngle: str = "Car.Roll"
    gt_side_slip_angle: str = "Car.SideSlipAngle"
    gt_pitch_rate: str = "Car.PitchVel"
    odo_pitch_rate: str = "AP.odoEstimationPort.pitchRate_radps"
    wheelPulsesFL_nu: str = "AP.odoInputPort.odoSigFcanPort.wheelMeasurements.wheelPulse.wheelPulsesFL_nu"
    wheelPulsesFR_nu: str = "AP.odoInputPort.odoSigFcanPort.wheelMeasurements.wheelPulse.wheelPulsesFR_nu"
    wheelPulsesRL_nu: str = "AP.odoInputPort.odoSigFcanPort.wheelMeasurements.wheelPulse.wheelPulsesRL_nu"
    wheelPulsesRR_nu: str = "AP.odoInputPort.odoSigFcanPort.wheelMeasurements.wheelPulse.wheelPulsesRR_nu"
    eSigStatus: str = "AP.odoEstimationPort.sSigHeader.eSigStatus"
    SteerAngleFL: str = "AP.odoDebugPort.steerAngleFL"
    SteerAngleFR: str = "AP.odoDebugPort.steerAngleFR"
    est_side_slip_angle: str = "AP.odoEstimationPort.sideSlipAngle_rad"
    uiCycleCounter: str = "AP.odoEstimationPort.sSigHeader.uiCycleCounter"
    uiMeasurementCounter: str = "AP.odoEstimationPort.sSigHeader.uiMeasurementCounter"
    heightOdo: str = "AP.odoEstimationPort.suspHeight_m"
    breakctrlstatusport: str = "DM.Brake"
    odoSteerAngRearAxle: str = "AP.odoEstimationPort.steerAngRearAxle_rad"
    odosteerAngFrontAxle: str = "AP.odoEstimationPort.steerAngFrontAxle_rad"
    odowheelAngleFL: str = "AP.odoEstimationPort.wheelAngleFL_rad"
    odowheelAngleFR: str = "AP.odoEstimationPort.wheelAngleFR_rad"
    odo_xPositionPredictBuffer3: str = "AP.odoEstimationOutputPort.odoPredictionBuffer_3.xPosition_m"
    odo_yawAnglePredictBuffer3: str = "AP.odoEstimationOutputPort.odoPredictionBuffer_3.yawAngle_rad"
    odo_yPositionPredictBuffer3: str = "AP.odoEstimationOutputPort.odoPredictionBuffer_3.yPosition_m"
    odo_xPositionPastBuffer30: str = "AP.odoEstimationOutputPort.odoEstimationBuffer_30.xPosition_m"
    odo_yawAnglePastBuffer30: str = "AP.odoEstimationOutputPort.odoEstimationBuffer_30.yawAngle_rad"
    odo_yPositionPastBuffer30: str = "AP.odoEstimationOutputPort.odoEstimationBuffer_30.yPosition_m"
    resetParking: str = "AP.resetParkingComponents_nu"
    num_strokes: str = "AP.numberOfStrokes"


@dataclass
class DgpsSignalUrl:
    """This class contains DGPS or Real recordings signals URLs"""

    egoVelocity: str = "Ethernet RT-Range.Hunter.VelocityVehicle.LongitudinalVelocity_mps"


@dataclass
class UnitConversion:
    """This class contains unit conversion formulas"""

    microsecondsToSeconds: float = 1 / 1_000_000
    kphToMps: float = 1 / 3.6
    mpsToKph: float = 3.6
    millisecondsToSeconds: float = 1 / 1000


@dataclass
class OtherConstants:
    """This class contains variable with constant values"""

    maxVehicleParkingSpeed: float = 10  # MPS
    WHEELBASE_M: float = 2.79
