"""Camera implementation"""

import math


class BaseLense:
    """Base Lense Abstract Class"""

    def __init__(self):
        """Init"""
        pass

    def projectCameraToUnitImager(self, cam_x, cam_y, cam_z):
        """Camera to unit imager projection"""
        pass

    def projectUnitImagerToCamera(self, uim_x, uim_y):
        """Unit imager projection to camera projection"""
        pass


class CylinderLense(BaseLense):
    """Cylindrical Lense Class"""

    def __init__(self):
        """Init"""
        super().__init__()

    def projectCameraToUnitImager(self, cam_x, cam_y, cam_z):
        """
        Project a point from Camera coordinate system to Unit Image coordinate system

        :param cam_x
        :param cam_y
        :param cam_z
        :return: x, y.
        """
        uim_x = 0
        uim_y = 0

        # length of camera vector projected to X-Z plane
        length_xz = math.sqrt(cam_x**2 + cam_z**2)

        if length_xz == 0:
            # point on camera y axis is not projectable
            return uim_x, uim_y, False

        # theta = angle in 2D between camera axis (Z) and projection of line from camera center to (xw, yw, zw) on XZ plane [rad]
        theta = math.atan2(cam_x, cam_z)

        uim_x = theta
        uim_y = cam_y / length_xz

        return uim_x, uim_y, True

    def projectUnitImagerToCamera(self, uim_x, uim_y):
        """
         Project a point from Unit Image coordinate system to Camera coordinate system

        :param uim_x
        :param uim_y
        :return: cam_z, cam_y, cam_z
        """
        # create 3D vector, having X-Z-length 1
        cam_x = math.sin(uim_x)
        cam_y = uim_y
        cam_z = math.cos(uim_x)
        return cam_x, cam_y, cam_z, True


class CameraModel:
    """Camera Model Class"""

    def __init__(self, lensemodel: BaseLense, calibration: dict):
        """
        Camera initialization
        param lensemodel : lense type -> cylindrical
        param calibration dictionary
        """
        self.calibration = None
        self.rotCam2World = None
        self.rotWorld2Cam = None
        self.lenseModel = lensemodel
        if calibration is not None:
            self.setCalibration(calibration)

    def __copy__(self):
        """Copy method"""
        return CameraModel(lensemodel=self.lenseModel, calibration=self.calibration)

    def updateCalibration(self):
        """Update current calibration, recompute internal transformation matrices"""
        self.rotCam2World = self.getRotCam2World()
        self.rotWorld2Cam = self.getRotWorld2Cam()

    def setCalibration(self, calibration):
        """Calibration setter"""
        if self.calibration != calibration:
            self.calibration = calibration
            self.updateCalibration()

    def getRotWorld2Cam(self):
        """Getter for world2cam transformation matrix"""
        rotWorld2Cam = [None] * 9

        if self.rotCam2World is None:
            self.rotCam2World = self.getRotCam2World()

        rotWorld2Cam[0] = self.rotCam2World[0]
        rotWorld2Cam[1] = self.rotCam2World[3]
        rotWorld2Cam[2] = self.rotCam2World[6]
        rotWorld2Cam[3] = self.rotCam2World[1]
        rotWorld2Cam[4] = self.rotCam2World[4]
        rotWorld2Cam[5] = self.rotCam2World[7]
        rotWorld2Cam[6] = self.rotCam2World[2]
        rotWorld2Cam[7] = self.rotCam2World[5]
        rotWorld2Cam[8] = self.rotCam2World[8]
        return rotWorld2Cam

    def getRotCam2World(self):
        """Getter for cam2world transformation matrix"""
        sx = math.sin(self.calibration["rotation_yaw"])
        cx = math.cos(self.calibration["rotation_yaw"])

        sy = math.sin(self.calibration["rotation_pitch"])
        cy = math.cos(self.calibration["rotation_pitch"])

        sz = math.sin(self.calibration["rotation_roll"])
        cz = math.cos(self.calibration["rotation_roll"])

        rotCam2World = [None] * 9

        rotCam2World[0] = cz * cy
        rotCam2World[1] = -sz * cx + cz * sy * sx
        rotCam2World[2] = sz * sx + cz * sy * cx
        rotCam2World[3] = sz * cy
        rotCam2World[4] = cz * cx + sz * sy * sx
        rotCam2World[5] = -cz * sx + sz * sy * cx
        rotCam2World[6] = -sy
        rotCam2World[7] = cy * sx
        rotCam2World[8] = cy * cx

        return rotCam2World

    def projectImage2World(self, img_x, img_y):
        """Project a point from Image coordinate system to World coordinate system
          Parameters:
        -----------
        img_x - x coordinate in image
        img_x - y coordinate in image
        Returns world_x, world_y, world_z, validity of projection

        """
        cam_x, cam_y, cam_z, valid = self.projectImage2Camera(img_x, img_y)
        world_x, world_y, world_z = self.transformCamera2World(cam_x, cam_y, cam_z)
        return world_x, world_y, world_z, valid

    def projectImage2WorldGivenOneCoord(self, img_x, img_y, given_coord_world, given_coord_world_value):
        """Project a point in Image coordinate system to World coordinate system given a world axis and value
          Parameters:
        -----------
        img_x - x coordinate in image
        img_x - y coordinate in image
        given_coord_world: x, y, or z
        given_coord_world_value: value of given_coord_world
        Returns world_x, world_y, world_z
        """
        cam_x, cam_y, cam_z, valid = self.projectImage2Camera(img_x, img_y)

        if given_coord_world == "x":
            cam_axis_x, cam_axis_y, cam_axis_z = self.rotCam2World[0:3]
            cam_translation = self.calibration["position_x"]
        elif given_coord_world == "y":
            cam_axis_x, cam_axis_y, cam_axis_z = self.rotCam2World[3:6]
            cam_translation = self.calibration["position_y"]
        elif given_coord_world == "z":
            cam_axis_x, cam_axis_y, cam_axis_z = self.rotCam2World[6:9]
            cam_translation = self.calibration["position_z"]
        else:
            raise ValueError(f'Unknown value "{given_coord_world}" of given_coord_world.')

        world_point_unscaled = cam_axis_x * cam_x + cam_axis_y * cam_y + cam_axis_z * cam_z
        if world_point_unscaled == 0.0:
            scale = 0.0
        else:
            scale = (given_coord_world_value - cam_translation) / world_point_unscaled

        if scale <= 0.0:
            valid = False

        world_x = (
            self.rotCam2World[0] * cam_x + self.rotCam2World[1] * cam_y + self.rotCam2World[2] * cam_z
        ) * scale + self.calibration["position_x"]
        world_y = (
            self.rotCam2World[3] * cam_x + self.rotCam2World[4] * cam_y + self.rotCam2World[5] * cam_z
        ) * scale + self.calibration["position_y"]
        world_z = (
            self.rotCam2World[6] * cam_x + self.rotCam2World[7] * cam_y + self.rotCam2World[8] * cam_z
        ) * scale + self.calibration["position_z"]

        return world_x, world_y, world_z, valid

    def projectWorld2Image(self, world_x, world_y, world_z):
        """Project a point from World coordinate system to Image coordinate system
        Parameters:
        -----------
        world_x - x coordinate in 3D world ( ISO coordynate system)
        world_y - y coordinate in 3D world ( ISO coordynate system)
        world_z - z coordinate in 3D world ( ISO coordynate system)
        Returns img_x, img_y, projection validity
        """
        cam_x, cam_y, cam_z = self.transformWorld2Cam(world_x, world_y, world_z)
        return self.projectCamera2Image(cam_x, cam_y, cam_z)

    def projectImage2Camera(self, x_img, y_img):
        """Project a point from Image coordinate system to Camera coordinate system
        Parameters:
        -----------
        img_x - x coordinate in image
        img_x - y coordinate in image
        Returns cam_z, cam_y, cam_z
        """
        assert self.calibration["focal_length_x"] > 0, "calibration error: focal_length_x must be greater 0"
        assert self.calibration["focal_length_y"] > 0, "calibration error: focal_length_y must be greater 0"

        unit_imager_x = (x_img - self.calibration["prin_axis_x"]) / self.calibration["focal_length_x"]
        unit_imager_y = (y_img - self.calibration["prin_axis_y"]) / self.calibration["focal_length_y"]

        return self.lenseModel.projectUnitImagerToCamera(unit_imager_x, unit_imager_y)

    def projectCamera2Image(self, cam_x, cam_y, cam_z):
        """Project a point from Camera coordinate system to Image coordinate system
        Parameters:
        -----------
        cam_x - x coordinate in camera coordynate system)
        cam_y - y coordinate in camera coordynate system)
        cam_z - z coordinate in camera coordynate system)
        Return img_x, img_y
        """
        x_unit_img, y_unit_img, valid = self.lenseModel.projectCameraToUnitImager(cam_x, cam_y, cam_z)

        img_x = x_unit_img * self.calibration["focal_length_x"] + self.calibration["principal_point_x"]
        img_y = y_unit_img * self.calibration["focal_length_y"] + self.calibration["principal_point_y"]

        # catch out of image
        if (
            (img_x < -0.5)
            or (img_x >= self.calibration["image_width"] - 0.5)
            or (img_y < -0.5)
            or (img_y >= self.calibration["image_height"] - 0.5)
        ):
            valid = False

        return img_x, img_y, valid

    def transformCamera2World(self, cam_x, cam_y, cam_z):
        """Transform a point from Camera coordinate system to World coordinate system
        Parameters:
        -----------
        cam_x - x coordinate in camera coordynate system)
        cam_y - y coordinate in camera coordynate system)
        cam_z - z coordinate in camera coordynate system)
        Return world_x, world_y, world_z
        """
        world_x = (
            self.rotCam2World[0] * cam_x + self.rotCam2World[1] * cam_y + self.rotCam2World[2] * cam_z
        ) + self.calibration["position_x"]
        world_y = (
            self.rotCam2World[3] * cam_x + self.rotCam2World[4] * cam_y + self.rotCam2World[5] * cam_z
        ) + self.calibration["position_y"]
        world_z = (
            self.rotCam2World[6] * cam_x + self.rotCam2World[7] * cam_y + self.rotCam2World[8] * cam_z
        ) + self.calibration["position_z"]
        return world_x, world_y, world_z

    def transformWorld2Cam(self, world_x, world_y, world_z):
        """Transform a point in World coordinate system to Camera coordinate system
        Parameters:
        -----------
        world_x - x coordinate in 3D world ( ISO coordynate system)
        world_y - y coordinate in 3D world ( ISO coordynate system)
        world_z - z coordinate in 3D world ( ISO coordynate system)
        Return cam_x, cam_y, cam_z
        """
        delta_x = world_x - self.calibration["position_x"]
        delta_y = world_y - self.calibration["position_y"]
        delta_z = world_z - self.calibration["position_z"]

        cam_x = self.rotWorld2Cam[0] * delta_x + self.rotWorld2Cam[1] * delta_y + self.rotWorld2Cam[2] * delta_z
        cam_y = self.rotWorld2Cam[3] * delta_x + self.rotWorld2Cam[4] * delta_y + self.rotWorld2Cam[5] * delta_z
        cam_z = self.rotWorld2Cam[6] * delta_x + self.rotWorld2Cam[7] * delta_y + self.rotWorld2Cam[8] * delta_z

        return cam_x, cam_y, cam_z
