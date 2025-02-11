"""Helper file for TPF test scripts."""

import logging

from tsf.io.signals import SignalDefinition

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class TPFSignals(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        # # # # # # # # # # Signal Header # # # # # # # # # #
        SIGTIMESTAMP = "sigTimestamp"
        SIGMEASCOUNTER = "sigMeasCounter"
        SIGCYCLECOUNTER = "sigCycleCounter"
        SIGSTATUS = "sigStatus"
        # # # # # # # # # # # Detections # # # # # # # # # # #
        OBJECTS_SHAPE_POINTS_0_POSITION_X = "objects.shape.points[0].position.x"
        OBJECTS_SHAPE_POINTS_1_POSITION_X = "objects.shape.points[1].position.x"
        OBJECTS_SHAPE_POINTS_2_POSITION_X = "objects.shape.points[2].position.x"
        OBJECTS_SHAPE_POINTS_3_POSITION_X = "objects.shape.points[3].position.x"
        OBJECTS_SHAPE_POINTS_0_POSITION_Y = "objects.shape.points[0].position.y"
        OBJECTS_SHAPE_POINTS_1_POSITION_Y = "objects.shape.points[1].position.y"
        OBJECTS_SHAPE_POINTS_2_POSITION_Y = "objects.shape.points[2].position.y"
        OBJECTS_SHAPE_POINTS_3_POSITION_Y = "objects.shape.points[3].position.y"
        OBJECTS_SHAPE_POINTS_0_VARIANCE_X = "objects.shape.points[0].varianceX"
        OBJECTS_SHAPE_POINTS_1_VARIANCE_X = "objects.shape.points[1].varianceX"
        OBJECTS_SHAPE_POINTS_2_VARIANCE_X = "objects.shape.points[2].varianceX"
        OBJECTS_SHAPE_POINTS_3_VARIANCE_X = "objects.shape.points[3].varianceX"
        OBJECTS_SHAPE_POINTS_0_VARIANCE_Y = "objects.shape.points[0].varianceY"
        OBJECTS_SHAPE_POINTS_1_VARIANCE_Y = "objects.shape.points[1].varianceY"
        OBJECTS_SHAPE_POINTS_2_VARIANCE_Y = "objects.shape.points[2].varianceY"
        OBJECTS_SHAPE_POINTS_3_VARIANCE_Y = "objects.shape.points[3].varianceY"
        OBJECTS_SHAPE_POINTS_0_COVARIANCE_XY = "objects.shape.points[0].covarianceXY"
        OBJECTS_SHAPE_POINTS_1_COVARIANCE_XY = "objects.shape.points[1].covarianceXY"
        OBJECTS_SHAPE_POINTS_2_COVARIANCE_XY = "objects.shape.points[2].covarianceXY"
        OBJECTS_SHAPE_POINTS_3_COVARIANCE_XY = "objects.shape.points[3].covarianceXY"
        OBJECTS_SHAPE_REFERENCEPOINT_X = "objects.shape.referencePoint.x"
        OBJECTS_SHAPE_REFERENCEPOINT_Y = "objects.shape.referencePoint.y"
        OBJECTS_VELOCITY_X = "objects.velocity.x"
        OBJECTS_VELOCITY_Y = "objects.velocity.y"
        OBJECTS_VELOCITYSTANDARDDEVIATION_X = "objects.velocityStandardDeviation.x"
        OBJECTS_VELOCITYSTANDARDDEVIATION_Y = "objects.velocityStandardDeviation.y"
        OBJECTS_ACCELERATION_X = "objects.acceleration.x"
        OBJECTS_ACCELERATION_Y = "objects.acceleration.y"
        OBJECTS_ACCELERATIONSTANDARDDEVIATION_X = "objects.accelerationStandardDeviation.x"
        OBJECTS_ACCELERATIONSTANDARDDEVIATION_Y = "objects.accelerationStandardDeviation.y"
        OBJECTS_ID = "objects.id"
        OBJECTS_OBJECTCLASS = "objects.objectClass"
        OBJECTS_CLASSPROBABILITY = "objects.classProbability"
        OBJECTS_DYNAMICPROPERTY = "objects.dynamicProperty"
        OBJECTS_LIFETIME = "objects.lifetime"
        OBJECTS_STATE = "objects.state"
        OBJECTS_EXISTENCECERTAINTY = "objects.existenceCertainty"
        OBJECTS_ORIENTATION = "objects.orientation"
        OBJECTS_ORIENTATIONSTANDARDDEVIATION = "objects.orientationStandardDeviation"
        OBJECTS_YAWRATE = "objects.yawRate"
        OBJECTS_YAWRATESTANDARDDEVIATION = "objects.yawRateStandardDeviation"
        # # # # # # # # # # # Output port # # # # # # # # # # #
        VERSION_NUMBER = "uiVersionNumber"
        NUMBER_OF_OBJECTS = "numberOfObjects"

    def get_properties(self):
        """Generate a string of signals to be read."""
        signal_dict = {}

        # Signal Header
        signal_dict[self.Columns.SIGTIMESTAMP] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.sSigHeader.uiTimeStamp",
            "SIM VFB.TPPINSTANCE_rsc.CEM200_TPF2_DATA.m_tpObjectList.sSigHeader.uiTimeStamp",
            "dynamicEnvironment.sSigHeader.uiTimeStamp",
        ]
        signal_dict[self.Columns.SIGMEASCOUNTER] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.sSigHeader.uiMeasurementCounter",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.sSigHeader.uiMeasurementCounter",
            "dynamicEnvironment.sSigHeader.uiMeasurementCounter",
        ]
        signal_dict[self.Columns.SIGCYCLECOUNTER] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.sSigHeader.uiCycleCounter",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.sSigHeader.uiCycleCounter",
            "dynamicEnvironment.sSigHeader.uiCycleCounter",
        ]
        signal_dict[self.Columns.SIGSTATUS] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.sSigHeader.eSigStatus",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.sSigHeader.eSigStatus",
            "dynamicEnvironment.sSigHeader.eSigStatus",
        ]
        # Detections
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_0_POSITION_X] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[0].position.x",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[0].position.x",
            "dynamicEnvironment.objects._%_.shape.points._0_.position.x",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_1_POSITION_X] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[1].position.x",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[1].position.x",
            "dynamicEnvironment.objects._%_.shape.points._1_.position.x",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_2_POSITION_X] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[2].position.x",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[2].position.x",
            "dynamicEnvironment.objects._%_.shape.points._2_.position.x",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_3_POSITION_X] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[3].position.x",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[3].position.x",
            "dynamicEnvironment.objects._%_.shape.points._3_.position.x",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_0_POSITION_Y] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[0].position.y",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[0].position.y",
            "dynamicEnvironment.objects._%_.shape.points._0_.position.y",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_1_POSITION_Y] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[1].position.y",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[1].position.y",
            "dynamicEnvironment.objects._%_.shape.points._1_.position.y",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_2_POSITION_Y] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[2].position.y",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[2].position.y",
            "dynamicEnvironment.objects._%_.shape.points._2_.position.y",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_3_POSITION_Y] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[3].position.y",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[3].position.y",
            "dynamicEnvironment.objects._%_.shape.points._3_.position.y",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_0_VARIANCE_X] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[0].varianceX",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[0].varianceX",
            "dynamicEnvironment.objects._%_.shape.points._0_.varianceX",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_1_VARIANCE_X] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[1].varianceX",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[1].varianceX",
            "dynamicEnvironment.objects._%_.shape.points._1_.varianceX",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_2_VARIANCE_X] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[2].varianceX",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[2].varianceX",
            "dynamicEnvironment.objects._%_.shape.points._2_.varianceX",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_3_VARIANCE_X] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[3].varianceX",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[3].varianceX",
            "dynamicEnvironment.objects._%_.shape.points._3_.varianceX",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_0_VARIANCE_Y] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[0].varianceY",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[0].varianceY",
            "dynamicEnvironment.objects._%_.shape.points._0_.varianceY",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_1_VARIANCE_Y] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[1].varianceY",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[1].varianceY",
            "dynamicEnvironment.objects._%_.shape.points._1_.varianceY",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_2_VARIANCE_Y] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[2].varianceY",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[2].varianceY",
            "dynamicEnvironment.objects._%_.shape.points._2_.varianceY",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_3_VARIANCE_Y] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[3].varianceY",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[3].varianceY",
            "dynamicEnvironment.objects._%_.shape.points._3_.varianceY",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_0_COVARIANCE_XY] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[0].covarianceXY",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[0].covarianceXY",
            "dynamicEnvironment.objects._%_.shape.points._0_.covarianceXY",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_1_COVARIANCE_XY] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[1].covarianceXY",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[1].covarianceXY",
            "dynamicEnvironment.objects._%_.shape.points._1_.covarianceXY",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_2_COVARIANCE_XY] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[2].covarianceXY",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[2].covarianceXY",
            "dynamicEnvironment.objects._%_.shape.points._2_.covarianceXY",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_POINTS_3_COVARIANCE_XY] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[3].covarianceXY",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.points[3].covarianceXY",
            "dynamicEnvironment.objects._%_.shape.points._3_.covarianceXY",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_REFERENCEPOINT_X] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.referencePoint.x",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.referencePoint.x",
            "dynamicEnvironment.objects._%_.shape.referencePoint.x",
        ]
        signal_dict[self.Columns.OBJECTS_SHAPE_REFERENCEPOINT_Y] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.referencePoint.y",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].shapePoints.referencePoint.y",
            "dynamicEnvironment.objects._%_.shape.referencePoint.y",
        ]
        signal_dict[self.Columns.OBJECTS_VELOCITY_X] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].velocity.x",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].velocity.x",
            "dynamicEnvironment.objects._%_.velocity.x",
        ]
        signal_dict[self.Columns.OBJECTS_VELOCITY_Y] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].velocity.y",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].velocity.y",
            "dynamicEnvironment.objects._%_.velocity.y",
        ]
        signal_dict[self.Columns.OBJECTS_VELOCITYSTANDARDDEVIATION_X] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].velocityStandardDeviation.x",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].velocityStandardDeviation.x",
            "dynamicEnvironment.objects._%_.velocityStandardDeviation.x",
        ]
        signal_dict[self.Columns.OBJECTS_VELOCITYSTANDARDDEVIATION_Y] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].velocityStandardDeviation.y",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].velocityStandardDeviation.y",
            "dynamicEnvironment.objects._%_.velocityStandardDeviation.y",
        ]
        signal_dict[self.Columns.OBJECTS_ACCELERATION_X] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].acceleration.x",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].acceleration.x",
            "dynamicEnvironment.objects._%_.acceleration.x",
        ]
        signal_dict[self.Columns.OBJECTS_ACCELERATION_Y] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].acceleration.y",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].acceleration.y",
            "dynamicEnvironment.objects._%_.acceleration.y",
        ]
        signal_dict[self.Columns.OBJECTS_ACCELERATIONSTANDARDDEVIATION_X] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].accelerationStandardDeviation.x",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].accelerationStandardDeviation.x",
            "dynamicEnvironment.objects._%_.accelerationStandardDeviation.x",
        ]
        signal_dict[self.Columns.OBJECTS_ACCELERATIONSTANDARDDEVIATION_Y] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].accelerationStandardDeviation.y",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].accelerationStandardDeviation.y",
            "dynamicEnvironment.objects._%_.accelerationStandardDeviation.y",
        ]
        signal_dict[self.Columns.OBJECTS_ID] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].id",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].id",
            "dynamicEnvironment.objects._%_.id",
        ]
        signal_dict[self.Columns.OBJECTS_OBJECTCLASS] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].objectClass",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].objectClass",
            "dynamicEnvironment.objects._%_.objectClass",
        ]
        signal_dict[self.Columns.OBJECTS_CLASSPROBABILITY] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].classProbability",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].classProbability",
            "dynamicEnvironment.objects._%_.classProbability",
        ]
        signal_dict[self.Columns.OBJECTS_DYNAMICPROPERTY] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].dynamicProperty",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].dynamicProperty",
            "dynamicEnvironment.objects._%_.dynamicProperty",
        ]
        signal_dict[self.Columns.OBJECTS_LIFETIME] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].lifetime",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].lifetime",
            "dynamicEnvironment.objects._%_.lifetime",
        ]
        signal_dict[self.Columns.OBJECTS_STATE] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].state",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].state",
            "dynamicEnvironment.objects._%_.state",
        ]
        signal_dict[self.Columns.OBJECTS_EXISTENCECERTAINTY] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].existenceCertainty",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].existenceCertainty",
            "dynamicEnvironment.objects._%_.existenceCertainty",
        ]
        signal_dict[self.Columns.OBJECTS_ORIENTATION] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].orientation",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].orientation",
            "dynamicEnvironment.objects._%_.orientation",
        ]
        signal_dict[self.Columns.OBJECTS_ORIENTATIONSTANDARDDEVIATION] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].orientationStandardDeviation",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].orientationStandardDeviation",
            "dynamicEnvironment.objects._%_.orientationStandardDeviation",
        ]
        signal_dict[self.Columns.OBJECTS_YAWRATE] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].yawRate",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].yawRate",
            "dynamicEnvironment.objects._%_.yawRate",
        ]
        signal_dict[self.Columns.OBJECTS_YAWRATESTANDARDDEVIATION] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.objects[%].yawRateStandardDeviation",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.objects[%].yawRateStandardDeviation",
            "dynamicEnvironment.objects._%_.yawRateStandardDeviation",
        ]
        signal_dict[self.Columns.VERSION_NUMBER] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.uiVersionNumber",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.uiVersionNumber",
            "dynamicEnvironment.uiVersionNumber",
        ]
        signal_dict[self.Columns.NUMBER_OF_OBJECTS] = [
            "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.numberOfObjects",
            "SIM VFB.CEM200_TPF2_DATA.m_tpObjectList.numberOfObjects",
            "dynamicEnvironment.numberOfObjects",
        ]

        return signal_dict

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "ADC5xx_Device", "M7board.EM_Thread", "CarPC.EM_Thread", "MTA_ADC5"]

        self._properties = self.get_properties()
