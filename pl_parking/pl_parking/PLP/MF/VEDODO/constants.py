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
