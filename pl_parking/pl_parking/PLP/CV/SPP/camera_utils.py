"""Camera utils scripts for SPP Test Scripts."""

import logging

import numpy as np

# CAMERA and IMAGE constants
IMG_WIDTH, IMG_HEIGHT = 832, 640  # available in grappa types constants

# cylindrical camera used in parking is a virtual camera described in chips ( undistortion is made there)
# position is took from mecal
# rotation is fixed
front_rotation = np.array([-np.pi / 2, 0, -np.pi / 2])
left_rotation = np.array([-np.pi / 2, 0, 0])
right_rotation = np.array([-np.pi / 2, 0, np.pi])
rear_rotation = np.array([-np.pi / 2, 0, np.pi / 2])
rotations = [front_rotation, left_rotation, right_rotation, rear_rotation]

from pl_parking.PLP.CV.SPP.camera import CameraModel, CylinderLense

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)


def verifyCalibration(calib_dict: dict):
    """Verification of calibration dictionary
    ---------
    Parameters
    ----------
    calib_dict : dict
        Calibration dictionary which contains camera extrinsics and intrinsics
    """
    logger.info("Checking Calibration")
    # check for required fields
    required_fields = [
        "position_x",
        "position_y",
        "position_z",
        "rotation_yaw",
        "rotation_pitch",
        "rotation_roll",
        "image_width",
        "image_height",
        "focal_length_x",
        "focal_length_y",
        "principal_point_x",
        "principal_point_y",
    ]
    for field in required_fields:
        if field not in calib_dict.keys():
            logger.error("Error.Not all fields are set")
            return False
    # no zero set extrinscs
    if calib_dict["position_x"] == 0.0 and calib_dict["position_y"] == 0.0 and calib_dict["position_z"] == 0.0:
        logger.error("Error.Extrinsics[position] are set to zero")
        return False
    if calib_dict["rotation_yaw"] == 0.0 and calib_dict["rotation_pitch"] == 0.0 and calib_dict["rotation_roll"] == 0.0:
        logger.error("Error.Extrinsics[rotation] are set to zero")
        return False

    # no zero set intrinsics
    if calib_dict["image_width"] == 0 or calib_dict["image_height"] == 0:
        logger.error("Error.Image width/height is set to zero")
        return False
    if calib_dict["focal_length_x"] == 0 or calib_dict["focal_length_y"] == 0:
        logger.error("Error.Focal lenght is set to zero")
        return False
    if calib_dict["principal_point_x"] == 0 or calib_dict["principal_point_x"] == 0:
        logger.error("Error.Principal point is set to zero")
        return False
    return True


def createCylindricalCamera(
    cameraId: int, pos_x: float, pos_y: float, pos_z: float, fx: int, fy: int, px: int, py: int
):
    """Creates a reference cylindrical camera based on camera extrinsics and image intrinsics.

    Parameters
    ----------
    cameraId : int
        Camera identifier a.k.a sensor source( 1-FRONT CAM, 2-LEFT CAM, 3-RIGHT CAM, 4-REAR CAM]
    pos_x : float
        Camera position on x-axis in vehicle coordinate system ISO.Value of this signal can be found at
        PARAMETER_HANDLER_DATA.[CAMERA]_EOLCalibrationExtrinsicsISO.posX_mm
    pos_y : float
        Camera position on y-axis in vehicle coordinate system ISO.Value of this signal can be found at
        PARAMETER_HANDLER_DATA.[CAMERA]_EOLCalibrationExtrinsicsISO.posY_mm
    pos_z : float
        Camera position on z-axis in vehicle coordinate system ISO.Value of this signal can be found at
        PARAMETER_HANDLER_DATA.[CAMERA]_EOLCalibrationExtrinsicsISO.posZ_mm
    fx : int
        Focal length on x axis of the image on which we operate.Value of this signal can be found at
        MTA_ADC5.GRAPPA_[CAMERA]_IMAGE.GrappaSemSeg[CAMERA]Image.imageHeader.intrinsics.focalX
    fy : int
        Focal length on y axis of the image on which we operate.Value of this signal can be found at
        MTA_ADC5.GRAPPA_[CAMERA]_IMAGE.GrappaSemSeg[CAMERA]Image.imageHeader.intrinsics.focalY
    px : int
        Principal point on x axis of the image on which we operate.Value of this signal can be found at
        MTA_ADC5.GRAPPA_[CAMERA]_IMAGE.GrappaSemSeg[CAMERA]Image.imageHeader.intrinsics.centerX
    py : int
        Principal point on y axis  of the image on which we operate.Value of this signal can be found at
        MTA_ADC5.GRAPPA_[CAMERA]_IMAGE.GrappaSemSeg[CAMERA]Image.imageHeader.intrinsics.centerY
    """
    if (cameraId >= 1) and (cameraId <= 4):
        rotation = rotations[cameraId - 1]  # fixed rotation, virtual camera
        calib = dict()
        calib["position_x"] = pos_x / 1000.0
        calib["position_y"] = pos_y / 1000.0
        calib["position_z"] = pos_z / 1000.0
        calib["rotation_yaw"] = rotation[0]
        calib["rotation_pitch"] = rotation[1]
        calib["rotation_roll"] = rotation[2]
        calib["image_width"] = IMG_WIDTH
        calib["image_height"] = IMG_HEIGHT
        calib["focal_length_x"] = fx
        calib["focal_length_y"] = fy
        calib["principal_point_x"] = px
        calib["principal_point_y"] = py
        validCalib = verifyCalibration(calib)
        if validCalib:
            camera = CameraModel(CylinderLense(), calib)
            return camera
        else:
            logger.error("Error.Invalid camera calibration")
    else:
        logger.error("Error.Invalid camera id")
    return None
