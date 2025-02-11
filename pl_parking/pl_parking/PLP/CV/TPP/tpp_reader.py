"""Helper file used to define the readers for TPP."""

import logging

from tsf.io.signals import SignalDefinition

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class TPPReader(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        # Front Camera
        TIMESTAMP_FRONT = "timestampFront"
        VERSIONNUMBER_FRONT = "versionNumberFront"
        SIGTIMESTAMP_FRONT = "sigTimestampFront"
        SIGMEASCOUNTER_FRONT = "sigMeasCounterFront"
        SIGCYCLECOUNTER_FRONT = "sigCycleCounterFront"
        SIGSTATUS_FRONT = "sigStatusFront"
        SENSORSOURCE_FRONT = "sensorSourceFront"
        NUMOBJECTS_FRONT = "numObjectsFront"
        CLASSTYPE_FRONT = "classTypeFront"
        CONFIDENCE_FRONT = "confidenceFront"
        CENTERX_FRONT = "center_xFront"
        CENTERY_FRONT = "center_yFront"
        CENTERZ_FRONT = "center_zFront"
        LENGTH_FRONT = "lengthFront"
        WIDTH_FRONT = "widthFront"
        HEIGHT_FRONT = "heightFront"
        WIDTH_2D_FRONT = "width_2dFront"
        HEIGHT_2D_FRONT = "height_2dFront"
        YAW_FRONT = "yawFront"

        # Left Camera
        TIMESTAMP_LEFT = "timestampLeft"
        VERSIONNUMBER_LEFT = "versionNumberLeft"
        SIGTIMESTAMP_LEFT = "sigTimestampLeft"
        SIGMEASCOUNTER_LEFT = "sigMeasCounterLeft"
        SIGCYCLECOUNTER_LEFT = "sigCycleCounterLeft"
        SIGSTATUS_LEFT = "sigStatusLeft"
        SENSORSOURCE_LEFT = "sensorSourceLeft"
        NUMOBJECTS_LEFT = "numObjectsLeft"
        CLASSTYPE_LEFT = "classTypeLeft"
        CONFIDENCE_LEFT = "confidenceLeft"
        CENTERX_LEFT = "center_xLeft"
        CENTERY_LEFT = "center_yLeft"
        CENTERZ_LEFT = "center_zLeft"
        LENGTH_LEFT = "lengthLeft"
        WIDTH_LEFT = "widthLeft"
        HEIGHT_LEFT = "heightLeft"
        WIDTH_2D_LEFT = "width_2dLeft"
        HEIGHT_2D_LEFT = "height_2dLeft"
        YAW_LEFT = "yawLeft"

        # Rear Camera
        TIMESTAMP_REAR = "timestampRear"
        VERSIONNUMBER_REAR = "versionNumberRear"
        SIGTIMESTAMP_REAR = "sigTimestampRear"
        SIGMEASCOUNTER_REAR = "sigMeasCounterRear"
        SIGCYCLECOUNTER_REAR = "sigCycleCounterRear"
        SIGSTATUS_REAR = "sigStatusRear"
        SENSORSOURCE_REAR = "sensorSourceRear"
        NUMOBJECTS_REAR = "numObjectsRear"
        CLASSTYPE_REAR = "classTypeRear"
        CONFIDENCE_REAR = "confidenceRear"
        CENTERX_REAR = "center_xRear"
        CENTERY_REAR = "center_yRear"
        CENTERZ_REAR = "center_zRear"
        LENGTH_REAR = "lengthRear"
        WIDTH_REAR = "widthRear"
        HEIGHT_REAR = "heightRear"
        WIDTH_2D_REAR = "width_2dRear"
        HEIGHT_2D_REAR = "height_2dRear"
        YAW_REAR = "yawRear"

        # Right Camera
        TIMESTAMP_RIGHT = "timestampRight"
        VERSIONNUMBER_RIGHT = "versionNumberRight"
        SIGTIMESTAMP_RIGHT = "sigTimestampRight"
        SIGMEASCOUNTER_RIGHT = "sigMeasCounterRight"
        SIGCYCLECOUNTER_RIGHT = "sigCycleCounterRight"
        SIGSTATUS_RIGHT = "sigStatusRight"
        SENSORSOURCE_RIGHT = "sensorSourceRight"
        NUMOBJECTS_RIGHT = "numObjectsRight"
        CLASSTYPE_RIGHT = "classTypeRight"
        CONFIDENCE_RIGHT = "confidenceRight"
        CENTERX_RIGHT = "center_xRight"
        CENTERY_RIGHT = "center_yRight"
        CENTERZ_RIGHT = "center_zRight"
        LENGTH_RIGHT = "lengthRight"
        WIDTH_RIGHT = "widthRight"
        HEIGHT_RIGHT = "heightRight"
        WIDTH_2D_RIGHT = "width_2dRight"
        HEIGHT_2D_RIGHT = "height_2dRight"
        YAW_RIGHT = "yawRight"

    def get_properties(self):
        """Generate a string of signals to be read."""
        signal_dict = {}

        # Front
        signal_dict[self.Columns.TIMESTAMP_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            ".DynamicObjectsFront.timestamp",
        ]
        signal_dict[self.Columns.VERSIONNUMBER_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.uiVersionNumber",
        ]
        signal_dict[self.Columns.SIGTIMESTAMP_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
        ]
        signal_dict[self.Columns.SIGMEASCOUNTER_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiMeasurementCounter",
        ]
        signal_dict[self.Columns.SIGCYCLECOUNTER_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiCycleCounter",
        ]
        signal_dict[self.Columns.SIGSTATUS_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
        ]
        signal_dict[self.Columns.SENSORSOURCE_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.eSensorSource",
        ]
        signal_dict[self.Columns.NUMOBJECTS_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.numberOfObjects",
            ".DynamicObjectsFront.numObjects",
        ]
        signal_dict[self.Columns.CLASSTYPE_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].classType",
            ".DynamicObjectsFront.objects[%].classType",
        ]
        signal_dict[self.Columns.CONFIDENCE_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].confidence",
            ".DynamicObjectsFront.objects[%].confidence",
        ]
        signal_dict[self.Columns.CENTERX_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_x",
            ".DynamicObjectsFront.objects[%].centerPointWorld.x",
        ]
        signal_dict[self.Columns.CENTERY_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_y",
            ".DynamicObjectsFront.objects[%].centerPointWorld.y",
        ]
        signal_dict[self.Columns.CENTERZ_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_z",
            ".DynamicObjectsFront.objects[%].centerPointWorld.z",
        ]

        signal_dict[self.Columns.LENGTH_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.length",
            ".DynamicObjectsFront.objects[%].cuboidSizeWorld.x",
        ]
        signal_dict[self.Columns.WIDTH_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.width",
            ".DynamicObjectsFront.objects[%].cuboidSizeWorld.y",
        ]
        signal_dict[self.Columns.HEIGHT_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.height",
            ".DynamicObjectsFront.objects[%].cuboidSizeWorld.z",
        ]
        # Sizes of the Bounding Boxes
        # Only on CarPC
        signal_dict[self.Columns.WIDTH_2D_FRONT] = [".DynamicObjectsFront.objects[%].planeSizeWorld.x"]
        signal_dict[self.Columns.HEIGHT_2D_FRONT] = [".DynamicObjectsFront.objects[%].planeSizeWorld.y"]

        signal_dict[self.Columns.YAW_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectYaw",
            ".DynamicObjectsFront.objects[%].cuboidYawWorld",
        ]

        # Left
        signal_dict[self.Columns.TIMESTAMP_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            ".DynamicObjectsLeft.timestamp",
        ]
        signal_dict[self.Columns.VERSIONNUMBER_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.uiVersionNumber",
        ]
        signal_dict[self.Columns.SIGTIMESTAMP_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
        ]
        signal_dict[self.Columns.SIGMEASCOUNTER_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiMeasurementCounter",
        ]
        signal_dict[self.Columns.SIGCYCLECOUNTER_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiCycleCounter",
        ]
        signal_dict[self.Columns.SIGSTATUS_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
        ]

        signal_dict[self.Columns.SENSORSOURCE_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.eSensorSource",
        ]
        signal_dict[self.Columns.NUMOBJECTS_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.numberOfObjects",
            ".DynamicObjectsLeft.numObjects",
        ]
        signal_dict[self.Columns.CLASSTYPE_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].classType",
            ".DynamicObjectsLeft.objects[%].classType",
        ]
        signal_dict[self.Columns.CONFIDENCE_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].confidence",
            ".DynamicObjectsLeft.objects[%].confidence",
        ]
        signal_dict[self.Columns.CENTERX_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_x",
            ".DynamicObjectsLeft.objects[%].centerPointWorld.x",
        ]
        signal_dict[self.Columns.CENTERY_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_y",
            ".DynamicObjectsLeft.objects[%].centerPointWorld.y",
        ]
        signal_dict[self.Columns.CENTERZ_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_z",
            ".DynamicObjectsLeft.objects[%].centerPointWorld.z",
        ]

        signal_dict[self.Columns.LENGTH_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.length",
            ".DynamicObjectsLeft.objects[%].cuboidSizeWorld.x",
        ]
        signal_dict[self.Columns.WIDTH_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.width",
            ".DynamicObjectsLeft.objects[%].cuboidSizeWorld.y",
        ]
        signal_dict[self.Columns.HEIGHT_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.height",
            ".DynamicObjectsLeft.objects[%].cuboidSizeWorld.z",
        ]
        # Sizes of the Bounding Boxes
        # Only on CarPC
        signal_dict[self.Columns.WIDTH_2D_LEFT] = [".DynamicObjectsLeft.objects[%].planeSizeWorld.x"]
        signal_dict[self.Columns.HEIGHT_2D_LEFT] = [".DynamicObjectsLeft.objects[%].planeSizeWorld.y"]

        signal_dict[self.Columns.YAW_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectYaw",
            ".DynamicObjectsLeft.objects[%].cuboidYawWorld",
        ]

        # Rear
        signal_dict[self.Columns.TIMESTAMP_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            ".DynamicObjectsRear.timestamp",
        ]
        signal_dict[self.Columns.VERSIONNUMBER_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.uiVersionNumber",
        ]
        signal_dict[self.Columns.SIGTIMESTAMP_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
        ]
        signal_dict[self.Columns.SIGMEASCOUNTER_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiMeasurementCounter",
        ]
        signal_dict[self.Columns.SIGCYCLECOUNTER_REAR] = (
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiCycleCounter"
        )
        signal_dict[self.Columns.SIGSTATUS_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
        ]

        signal_dict[self.Columns.SENSORSOURCE_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.eSensorSource",
        ]
        signal_dict[self.Columns.NUMOBJECTS_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.numberOfObjects",
            ".DynamicObjectsRear.numObjects",
        ]
        signal_dict[self.Columns.CLASSTYPE_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].classType",
            ".DynamicObjectsRear.objects[%].classType",
        ]
        signal_dict[self.Columns.CONFIDENCE_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].confidence",
            ".DynamicObjectsRear.objects[%].confidence",
        ]
        signal_dict[self.Columns.CENTERX_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_x",
            ".DynamicObjectsRear.objects[%].centerPointWorld.x",
        ]
        signal_dict[self.Columns.CENTERY_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_y",
            ".DynamicObjectsRear.objects[%].centerPointWorld.y",
        ]
        signal_dict[self.Columns.CENTERZ_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_z",
            ".DynamicObjectsRear.objects[%].centerPointWorld.z",
        ]

        signal_dict[self.Columns.LENGTH_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.length",
            ".DynamicObjectsRear.objects[%].cuboidSizeWorld.x",
        ]
        signal_dict[self.Columns.WIDTH_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.width",
            ".DynamicObjectsRear.objects[%].cuboidSizeWorld.y",
        ]
        signal_dict[self.Columns.HEIGHT_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.height",
            ".DynamicObjectsRear.objects[%].cuboidSizeWorld.z",
        ]
        # Sizes of the Bounding Boxes
        # Only on CarPC
        signal_dict[self.Columns.WIDTH_2D_REAR] = [".DynamicObjectsRear.objects[%].planeSizeWorld.x"]
        signal_dict[self.Columns.HEIGHT_2D_REAR] = [".DynamicObjectsRear.objects[%].planeSizeWorld.y"]

        signal_dict[self.Columns.YAW_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectYaw",
            ".DynamicObjectsRear.objects[%].cuboidYawWorld",
        ]

        # Right
        signal_dict[self.Columns.TIMESTAMP_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            ".DynamicObjectsRight.timestamp",
        ]
        signal_dict[self.Columns.VERSIONNUMBER_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.uiVersionNumber",
        ]
        signal_dict[self.Columns.SIGTIMESTAMP_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
        ]
        signal_dict[self.Columns.SIGMEASCOUNTER_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiMeasurementCounter",
        ]
        signal_dict[self.Columns.SIGCYCLECOUNTER_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiCycleCounter",
        ]
        signal_dict[self.Columns.SIGSTATUS_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
        ]

        signal_dict[self.Columns.SENSORSOURCE_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.eSensorSource",
        ]
        signal_dict[self.Columns.NUMOBJECTS_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.numberOfObjects",
            ".DynamicObjectsRight.numObjects",
        ]
        signal_dict[self.Columns.CLASSTYPE_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].classType",
            ".DynamicObjectsRight.objects[%].classType",
        ]
        signal_dict[self.Columns.CONFIDENCE_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].confidence",
            ".DynamicObjectsRight.objects[%].confidence",
        ]
        signal_dict[self.Columns.CENTERX_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_x",
            ".DynamicObjectsRight.objects[%].centerPointWorld.x",
        ]
        signal_dict[self.Columns.CENTERY_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_y",
            ".DynamicObjectsRight.objects[%].centerPointWorld.y",
        ]
        signal_dict[self.Columns.CENTERZ_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_z",
            ".DynamicObjectsRight.objects[%].centerPointWorld.z",
        ]

        signal_dict[self.Columns.LENGTH_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.length",
            ".DynamicObjectsRight.objects[%].cuboidSizeWorld.x",
        ]
        signal_dict[self.Columns.WIDTH_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.width",
            ".DynamicObjectsRight.objects[%].cuboidSizeWorld.y",
        ]
        signal_dict[self.Columns.HEIGHT_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.height",
            ".DynamicObjectsRight.objects[%].cuboidSizeWorld.z",
        ]
        # Sizes of the Bounding Boxes
        # Only on CarPC
        signal_dict[self.Columns.WIDTH_2D_RIGHT] = [".DynamicObjectsRight.objects[%].planeSizeWorld.x"]
        signal_dict[self.Columns.HEIGHT_2D_RIGHT] = [".DynamicObjectsRight.objects[%].planeSizeWorld.y"]

        signal_dict[self.Columns.YAW_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectYaw",
            ".DynamicObjectsRight.objects[%].cuboidYawWorld",
        ]

        return signal_dict

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "ADC5xx_Device", "M7board.EM_Thread", "CarPC.EM_Thread", "MTA_ADC5"]

        self._properties = self.get_properties()
