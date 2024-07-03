"""PMSD helpre scripts"""

from dataclasses import dataclass
from typing import Any, TypedDict, Union

import numpy as np
from tsf.io.signals import SignalDefinition

from pl_parking.PLP.CV.PMSD.association import VehicleLine, VehiclePoint
from pl_parking.PLP.CV.PMSD.constants import Platforms


class Parking:
    """Stores sensor data calculated in TRC coordinate system if the memory threshold is satisfied"""

    data_dict = {Platforms.SIM: {}, Platforms.VEHICLE: {}}

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
            if "AP.headUnitVisualizationPort.screen_nu" in reader.signals:
                basestring = "AP."
            else:
                # other checks for NEXT will be necessary to be added
                basestring = "ADC5xx_Device."

            # if basestring is None:
            # write_log_message("Error while reading mf_sil base string", "error", LOGGER)
            # else:
            # write_log_message("mf_sil string found", "success", LOGGER)

        if platform == Platforms.VEHICLE:
            if "M7board.EM_Thread.ApParkingBoxPort.numValidParkingBoxes_nu" in reader.signals:
                basestring = "M7board.EM_Thread."
            if "CarPC.EM_Thread.ApParkingBoxPort.numValidParkingBoxes_nu" in reader.signals:
                basestring = "CarPC.EM_Thread."
            # message output
            # if basestring is None:
            # write_log_message("Error while reading M7 base string", "error", LOGGER)
            # else:
            # write_log_message("M7 string found", "success", LOGGER)

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
                "LongSlope": {"string": "Car.Road.Route.LongSlope", "type": float},
                "time": {"string": "Time", "type": float},
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
    def data_mapping_pmsd(base_string):
        """PMSD data mapping"""
        return {
            "FC_numParkingLines": {"string": ("PMSD_FC_DATA.PmsdParkingLinesOutputFc.numParkingLines",), "type": float},
            "FC_lineConfidence": {
                "string": ("PMSD_FC_DATA.PmsdParkingLinesOutputFc.lineList.lineConfidence",),
                "type": float,
            },
            "RC_numParkingLines": {"string": ("PMSD_RC_DATA.PmsdParkingLinesOutputRc.numParkingLines",), "type": float},
            "RC_lineConfidence": {
                "string": ("PMSD_RC_DATA.PmsdParkingLinesOutputRc.lineList.lineConfidence",),
                "type": float,
            },
            "LSC_numParkingLines": {
                "string": ("PMSD_LSC_DATA.PmsdParkingLinesOutputLsc.numParkingLines",),
                "type": float,
            },
            "LSC_lineConfidence": {
                "string": ("PMSD_LSC_DATA.PmsdParkingLinesOutputLsc.lineList.lineConfidence",),
                "type": float,
            },
            "RSC_numParkingLines": {
                "string": ("PMSD_RSC_DATA.PmsdParkingLinesOutputRsc.numParkingLines",),
                "type": float,
            },
            "RSC_lineConfidence": {
                "string": ("PMSD_RSC_DATA.PmsdParkingLinesOutputRsc.lineList.lineConfidence",),
                "type": float,
            },
        }


class Ego_Params(TypedDict):
    """Ego vehicle parameters"""

    GTReferencePointXFromRear: float
    GTReferencePointYFromCenter: float
    RearOverhang: float
    FrontOverhang: float
    VehicleLength: float
    rpARSx: float
    rpARSy: float
    rpYawARS: float
    rpCAMx: float
    rpCAMy: float
    rpYawCAM: float
    rpSRRFLx: float
    rpSRRFLy: float
    rpYawSRRFL: float
    rpSRRFRx: float
    rpSRRFRy: float
    rpYawSRRFR: float
    rpSRRRLx: float
    rpSRRRLy: float
    rpYawSRRRL: float
    rpSRRRRx: float
    rpSRRRRy: float
    rpYawSRRRR: float
    GTOffsetX: float
    GTOffsetY: float
    ARSRange: float
    ValeoRange: float
    SRRFLRange: float
    SRRFRRange: float
    SRRRLRange: float
    SRRRRRange: float
    mpYawSRRFL: float
    mpYawSRRFR: float
    mpYawSRRRL: float
    mpYawSRRRR: float


@dataclass
class PMSD_Line_Detection:
    """PMSD detected line"""

    # lineId: int
    lineStartX: float
    lineStartY: float
    lineEndX: float
    lineEndY: float
    lineConfidence: float

    # lineType: int
    # lineColour: int
    # isStartSeen: int
    # isEndSeen: int
    # lineStartXPix: float
    # lineStartYPix: float
    # lineEndXPix: float
    # lineEndYPix: float

    def to_Vehicle(self) -> VehicleLine:
        """Transform to vehicle coordinates"""
        start = VehiclePoint(-self.lineStartX, -self.lineStartY)
        end = VehiclePoint(-self.lineEndX, -self.lineEndY)

        return VehicleLine(start, end)


class LazyDict(dict[str, np.ndarray]):
    """Lazy dict"""

    def __init__(self, factory):
        self.factory = factory

    def __missing__(self, key):
        self[key] = self.factory(key)
        return self[key]


class PMSDSignals(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIMESTAMP = "TimeStamp"
        LATITUDE = "Latitude"
        LONGITUDE = "Longitude"
        ALTITUDE = "Altitude"
        HEADING = "Heading"
        PMDREARNUMBEROFLINES = "PmdRear_numberOfLines"
        PMDREARLINESTARTX = "PmdRear_lineStartX"
        PMDREARLINESTARTY = "PmdRear_lineStartY"
        PMDREARLINEENDX = "PmdRear_lineEndX"
        PMDREARLINEENDY = "PmdRear_lineEndY"
        PMDREARLINECONFIDENCE = "PmdRear_lineConfidence"
        PMDRIGHTNUMBEROFLINES = "PmdRight_numberOfLines"
        PMDRIGHTLINESTARTX = "PmdRight_lineStartX"
        PMDRIGHTLINESTARTY = "PmdRight_lineStartY"
        PMDRIGHTLINEENDX = "PmdRight_lineEndX"
        PMDRIGHTLINEENDY = "PmdRight_lineEndY"
        PMDRIGHTLINECONFIDENCE = "PmdRight_lineConfidence"
        PMDLEFTNUMBEROFLINES = "PmdLeft_numberOfLines"
        PMDLEFTLINESTARTX = "PmdLeft_lineStartX"
        PMDLEFTLINESTARTY = "PmdLeft_lineStartY"
        PMDLEFTLINEENDX = "PmdLeft_lineEndX"
        PMDLEFTLINEENDY = "PmdLeft_lineEndY"
        PMDLEFTLINECONFIDENCE = "PmdLeft_lineConfidence"
        PMDFRONTNUMBEROFLINES = "PmdFront_numberOfLines"
        PMDFRONTLINESTARTX = "PmdFront_lineStartX"
        PMDFRONTLINESTARTY = "PmdFront_lineStartY"
        PMDFRONTLINEENDX = "PmdFront_lineEndX"
        PMDFRONTLINEENDY = "PmdFront_lineEndY"
        PMDFRONTLINECONFIDENCE = "PmdFront_lineConfidence"
        PMDREARPOSX = "PmdRear_posx"
        PMDREARPOSY = "PmdRear_posy"
        PMDRIGHTPOSX = "PmdRight_posx"
        PMDRIGHTPOSY = "PmdRight_posy"
        PMDLEFTPOSX = "PmdLeft_posx"
        PMDLEFTPOSY = "PmdLeft_posy"
        PMDFRONTPOSX = "PmdFront_posx"
        PMDFRONTPOSY = "PmdFront_posy"

        PMSDSLOT_FRONT_TIMESTAMP = "PmsdSlot_Front_timestamp"
        PMSDSLOT_LEFT_TIMESTAMP = "PmsdSlot_Left_timestamp"
        PMSDSLOT_REAR_TIMESTAMP = "PmsdSlot_Rear_timestamp"
        PMSDSLOT_RIGHT_TIMESTAMP = "PmsdSlot_Right_timestamp"
        PMSDSLOT_FRONT_NUMBEROFSLOTS = "PmsdSlot_Front_numberOfSlots"
        PMSDSLOT_LEFT_NUMBEROFSLOTS = "PmsdSlot_Left_numberOfSlots"
        PMSDSLOT_REAR_NUMBEROFSLOTS = "PmsdSlot_Rear_numberOfSlots"
        PMSDSLOT_RIGHT_NUMBEROFSLOTS = "PmsdSlot_Right_numberOfSlots"
        PMSDSLOT_FRONT_P0_X = "PmsdSlot_Front_P0_x"
        PMSDSLOT_LEFT_P0_X = "PmsdSlot_Left_P0_x"
        PMSDSLOT_REAR_P0_X = "PmsdSlot_Rear_P0_x"
        PMSDSLOT_RIGHT_P0_X = "PmsdSlot_Right_P0_x"
        PMSDSLOT_FRONT_P0_Y = "PmsdSlot_Front_P0_y"
        PMSDSLOT_LEFT_P0_Y = "PmsdSlot_Left_P0_y"
        PMSDSLOT_REAR_P0_Y = "PmsdSlot_Rear_P0_y"
        PMSDSLOT_RIGHT_P0_Y = "PmsdSlot_Right_P0_y"
        PMSDSLOT_FRONT_P1_X = "PmsdSlot_Front_P1_x"
        PMSDSLOT_LEFT_P1_X = "PmsdSlot_Left_P1_x"
        PMSDSLOT_REAR_P1_X = "PmsdSlot_Rear_P1_x"
        PMSDSLOT_RIGHT_P1_X = "PmsdSlot_Right_P1_x"
        PMSDSLOT_FRONT_P1_Y = "PmsdSlot_Front_P1_y"
        PMSDSLOT_LEFT_P1_Y = "PmsdSlot_Left_P1_y"
        PMSDSLOT_REAR_P1_Y = "PmsdSlot_Rear_P1_y"
        PMSDSLOT_RIGHT_P1_Y = "PmsdSlot_Right_P1_y"
        PMSDSLOT_FRONT_P2_X = "PmsdSlot_Front_P2_x"
        PMSDSLOT_LEFT_P2_X = "PmsdSlot_Left_P2_x"
        PMSDSLOT_REAR_P2_X = "PmsdSlot_Rear_P2_x"
        PMSDSLOT_RIGHT_P2_X = "PmsdSlot_Right_P2_x"
        PMSDSLOT_FRONT_P2_Y = "PmsdSlot_Front_P2_y"
        PMSDSLOT_LEFT_P2_Y = "PmsdSlot_Left_P2_y"
        PMSDSLOT_REAR_P2_Y = "PmsdSlot_Rear_P2_y"
        PMSDSLOT_RIGHT_P2_Y = "PmsdSlot_Right_P2_y"
        PMSDSLOT_FRONT_P3_X = "PmsdSlot_Front_P3_x"
        PMSDSLOT_LEFT_P3_X = "PmsdSlot_Left_P3_x"
        PMSDSLOT_REAR_P3_X = "PmsdSlot_Rear_P3_x"
        PMSDSLOT_RIGHT_P3_X = "PmsdSlot_Right_P3_x"
        PMSDSLOT_FRONT_P3_Y = "PmsdSlot_Front_P3_y"
        PMSDSLOT_LEFT_P3_Y = "PmsdSlot_Left_P3_y"
        PMSDSLOT_REAR_P3_Y = "PmsdSlot_Rear_P3_y"
        PMSDSLOT_RIGHT_P3_Y = "PmsdSlot_Right_P3_y"
        PMSDSLOT_FRONT_EXISTENCEPROBABILITY = "PmsdSlot_Front_existenceProbability"
        PMSDSLOT_LEFT_EXISTENCEPROBABILITY = "PmsdSlot_Left_existenceProbability"
        PMSDSLOT_REAR_EXISTENCEPROBABILITY = "PmsdSlot_Rear_existenceProbability"
        PMSDSLOT_RIGHT_EXISTENCEPROBABILITY = "PmsdSlot_Right_existenceProbability"

        CAM_FRONT_ISO_POSX = "CamFrontIsoPosX"
        CAM_FRONT_ISO_POSY = "CamFrontIsoPosY"
        CAM_LEFT_ISO_POSX = "CamLeftIsoPosX"
        CAM_LEFT_ISO_POSY = "CamLeftIsoPosY"
        CAM_REAR_ISO_POSX = "CamRearIsoPosX"
        CAM_REAR_ISO_POSY = "CamRearIsoPosY"
        CAM_RIGHT_ISO_POSX = "CamRightIsoPosX"
        CAM_RIGHT_ISO_POSY = "CamRightIsoPosY"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = [
            (
                self.Columns.LATITUDE,
                [
                    "RT-Range Processor.Hunter.Position.Latitude",
                ],
            ),
            (
                self.Columns.LONGITUDE,
                [
                    "RT-Range Processor.Hunter.Position.Longitude",
                ],
            ),
            (
                self.Columns.ALTITUDE,
                [
                    "RT-Range Processor.Hunter.Position.Altitude",
                ],
            ),
            (
                self.Columns.HEADING,
                [
                    "RT-Range Processor.Hunter.Angles.Heading",
                ],
            ),
            (
                self.Columns.PMDREARNUMBEROFLINES,
                [
                    "CarPC.EM_Thread.PmdRear.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDREARLINESTARTX,
                [
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineStartX",
                ],
            ),
            (
                self.Columns.PMDREARLINESTARTY,
                [
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineStartY",
                ],
            ),
            (
                self.Columns.PMDREARLINEENDX,
                [
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineEndX",
                ],
            ),
            (
                self.Columns.PMDREARLINEENDY,
                [
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineEndY",
                ],
            ),
            (
                self.Columns.PMDREARLINECONFIDENCE,
                [
                    "CarPC.EM_Thread.PmdRear.parkingLines[%].lineConfidence",
                ],
            ),
            (
                self.Columns.PMDRIGHTNUMBEROFLINES,
                [
                    "CarPC.EM_Thread.PmdRight.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDRIGHTLINESTARTX,
                [
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineStartX",
                ],
            ),
            (
                self.Columns.PMDRIGHTLINESTARTY,
                [
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineStartY",
                ],
            ),
            (
                self.Columns.PMDRIGHTLINEENDX,
                [
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineEndX",
                ],
            ),
            (
                self.Columns.PMDRIGHTLINEENDY,
                [
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineEndY",
                ],
            ),
            (
                self.Columns.PMDRIGHTLINECONFIDENCE,
                [
                    "CarPC.EM_Thread.PmdRight.parkingLines[%].lineConfidence",
                ],
            ),
            (
                self.Columns.PMDLEFTNUMBEROFLINES,
                [
                    "CarPC.EM_Thread.PmdLeft.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDLEFTLINESTARTX,
                [
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineStartX",
                ],
            ),
            (
                self.Columns.PMDLEFTLINESTARTY,
                [
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineStartY",
                ],
            ),
            (
                self.Columns.PMDLEFTLINEENDX,
                [
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineEndX",
                ],
            ),
            (
                self.Columns.PMDLEFTLINEENDY,
                [
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineEndY",
                ],
            ),
            (
                self.Columns.PMDLEFTLINECONFIDENCE,
                [
                    "CarPC.EM_Thread.PmdLeft.parkingLines[%].lineConfidence",
                ],
            ),
            (
                self.Columns.PMDFRONTNUMBEROFLINES,
                [
                    "CarPC.EM_Thread.PmdFront.numberOfLines",
                ],
            ),
            (
                self.Columns.PMDFRONTLINESTARTX,
                [
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineStartX",
                ],
            ),
            (
                self.Columns.PMDFRONTLINESTARTY,
                [
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineStartY",
                ],
            ),
            (
                self.Columns.PMDFRONTLINEENDX,
                [
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineEndX",
                ],
            ),
            (
                self.Columns.PMDFRONTLINEENDY,
                [
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineEndY",
                ],
            ),
            (
                self.Columns.PMDFRONTLINECONFIDENCE,
                [
                    "CarPC.EM_Thread.PmdFront.parkingLines[%].lineConfidence",
                ],
            ),
            (
                self.Columns.PMDFRONTPOSX,
                [
                    "CarPC.EM_Thread.CameraCurrentExtrinsics_FV.currExtrinsics.posX_mm",
                ],
            ),
            (
                self.Columns.PMDFRONTPOSY,
                [
                    "CarPC.EM_Thread.CameraCurrentExtrinsics_FV.currExtrinsics.posY_mm",
                ],
            ),
            (
                self.Columns.PMDREARPOSX,
                [
                    "CarPC.EM_Thread.CameraCurrentExtrinsics_RV.currExtrinsics.posX_mm",
                ],
            ),
            (
                self.Columns.PMDREARPOSY,
                [
                    "CarPC.EM_Thread.CameraCurrentExtrinsics_RV.currExtrinsics.posY_mm",
                ],
            ),
            (
                self.Columns.PMDLEFTPOSX,
                [
                    "CarPC.EM_Thread.CameraCurrentExtrinsics_ML.currExtrinsics.posX_mm",
                ],
            ),
            (
                self.Columns.PMDLEFTPOSY,
                [
                    "CarPC.EM_Thread.CameraCurrentExtrinsics_ML.currExtrinsics.posY_mm",
                ],
            ),
            (
                self.Columns.PMDRIGHTPOSX,
                [
                    "CarPC.EM_Thread.CameraCurrentExtrinsics_MR.currExtrinsics.posX_mm",
                ],
            ),
            (
                self.Columns.PMDRIGHTPOSY,
                [
                    "CarPC.EM_Thread.CameraCurrentExtrinsics_MR.currExtrinsics.posY_mm",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_FC_DATA.Slots.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_RC_DATA.Slots.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_TIMESTAMP,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_NUMBEROFSLOTS,
                [
                    "MTA_ADC5.PMSD_FC_DATA.Slots.numberOfSlots",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_NUMBEROFSLOTS,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.numberOfSlots",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_NUMBEROFSLOTS,
                [
                    "MTA_ADC5.PMSD_RC_DATA.Slots.numberOfSlots",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_NUMBEROFSLOTS,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.numberOfSlots",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_P0_X,
                [
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_0.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_P0_X,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_0.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_P0_X,
                [
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_0.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_P0_X,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_0.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_P1_X,
                [
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_1.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_P1_X,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_1.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_P1_X,
                [
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_1.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_P1_X,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_1.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_P2_X,
                [
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_2.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_P2_X,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_2.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_P2_X,
                [
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_2.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_P2_X,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_2.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_P3_X,
                [
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_3.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_P3_X,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_3.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_P3_X,
                [
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_3.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_P3_X,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_3.x",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_P0_Y,
                [
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_0.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_P0_Y,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_0.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_P0_Y,
                [
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_0.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_P0_Y,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_0.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_P1_Y,
                [
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_1.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_P1_Y,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_1.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_P1_Y,
                [
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_1.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_P1_Y,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_1.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_P2_Y,
                [
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_2.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_P2_Y,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_2.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_P2_Y,
                [
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_2.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_P2_Y,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_2.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_P3_Y,
                [
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].corner_3.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_P3_Y,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].corner_3.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_P3_Y,
                [
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].corner_3.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_P3_Y,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].corner_3.y",
                ],
            ),
            (
                self.Columns.PMSDSLOT_FRONT_EXISTENCEPROBABILITY,
                [
                    "MTA_ADC5.PMSD_FC_DATA.Slots.parkingSlots[%].existenceProbability",
                ],
            ),
            (
                self.Columns.PMSDSLOT_LEFT_EXISTENCEPROBABILITY,
                [
                    "MTA_ADC5.PMSD_LSC_DATA.Slots.parkingSlots[%].existenceProbability",
                ],
            ),
            (
                self.Columns.PMSDSLOT_REAR_EXISTENCEPROBABILITY,
                [
                    "MTA_ADC5.PMSD_RC_DATA.Slots.parkingSlots[%].existenceProbability",
                ],
            ),
            (
                self.Columns.PMSDSLOT_RIGHT_EXISTENCEPROBABILITY,
                [
                    "MTA_ADC5.PMSD_RSC_DATA.Slots.parkingSlots[%].existenceProbability",
                ],
            ),
            (
                self.Columns.CAM_FRONT_ISO_POSX,
                [
                    "CarPC.EM_Thread.CameraCurrentExtrinsics_FV.isoExtrinsics_XYZ.posX_mm",
                ],
            ),
            (
                self.Columns.CAM_FRONT_ISO_POSY,
                [
                    "CarPC.EM_Thread.CameraCurrentExtrinsics_FV.isoExtrinsics_XYZ.posY_mm",
                ],
            ),
            (
                self.Columns.CAM_LEFT_ISO_POSX,
                [
                    "CarPC.EM_Thread.CameraCurrentExtrinsics_ML.isoExtrinsics_XYZ.posX_mm",
                ],
            ),
            (
                self.Columns.CAM_LEFT_ISO_POSY,
                [
                    "CarPC.EM_Thread.CameraCurrentExtrinsics_ML.isoExtrinsics_XYZ.posY_mm",
                ],
            ),
            (
                self.Columns.CAM_REAR_ISO_POSX,
                [
                    "CarPC.EM_Thread.CameraCurrentExtrinsics_RV.isoExtrinsics_XYZ.posX_mm",
                ],
            ),
            (
                self.Columns.CAM_REAR_ISO_POSY,
                [
                    "CarPC.EM_Thread.CameraCurrentExtrinsics_RV.isoExtrinsics_XYZ.posY_mm",
                ],
            ),
            (
                self.Columns.CAM_RIGHT_ISO_POSX,
                [
                    "CarPC.EM_Thread.CameraCurrentExtrinsics_MR.isoExtrinsics_XYZ.posX_mm",
                ],
            ),
            (
                self.Columns.CAM_RIGHT_ISO_POSY,
                [
                    "CarPC.EM_Thread.CameraCurrentExtrinsics_MR.isoExtrinsics_XYZ.posY_mm",
                ],
            ),
        ]
