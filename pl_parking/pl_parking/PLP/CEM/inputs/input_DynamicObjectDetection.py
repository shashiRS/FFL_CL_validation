#!/usr/bin/env python3
"""Defining input DynamicObjectDetection testcases"""
import math
import typing
from dataclasses import dataclass
from enum import Enum

import numpy as np

from pl_parking.PLP.CEM.inputs.input_CemTpfReader import DynPoint, ObjectClass


class GrappaDetectorType(Enum):
    """Enumeration for types of Grappa detectors."""

    PED: int = 0
    BCL: int = 1
    MTB: int = 2
    RIDER: int = 3
    CAR: int = 4
    TRUCK: int = 5
    VEHICLE: int = 6


class DynamicObjectCamera(Enum):
    """Enumeration for cameras used in dynamic object detection."""

    FRONT: int = 0
    REAR: int = 1
    LEFT: int = 2
    RIGHT: int = 3


@dataclass
class DynamicObjectDetection:
    """
    Dataclass representing a dynamic object detection with attributes:
    object_id, class_type, confidence, center_x, center_y, and polygon.
    """

    object_id: int
    class_type: ObjectClass
    confidence: float  # [0..1]
    center_x: float
    center_y: float
    polygon: typing.List[DynPoint]  # For cylinder object, it's just sampled circle


@dataclass
class CylinderDynamicObjectDetection(DynamicObjectDetection):
    """Dataclass representing a cylinder dynamic object detection with additional radius attribute."""

    radius: float


@dataclass
class CuboidDynamicObjectDetection(DynamicObjectDetection):
    """Dataclass representing a cuboid dynamic object detection with additional length and width attributes."""

    length: float
    width: float


@dataclass
class DynamicObjectDetectionTimeframe:
    """Dataclass representing a timeframe with dynamic object detections with attributes."""

    timestamp: int
    num_objects: int
    dynamic_objects: typing.List[DynamicObjectDetection]


class DynamicObjectDetectionReader:
    """Reads data for dynamic object detection."""

    def __init__(self, reader):
        """Initialize object attributes."""
        self.data = reader
        self.camera_strings = self.__get_camera_strings()

    @staticmethod
    def __get_camera_strings():
        """Returns a dictionary mapping camera types to their corresponding strings."""
        return {
            DynamicObjectCamera.FRONT: "Front",
            DynamicObjectCamera.REAR: "Rear",
            DynamicObjectCamera.LEFT: "Left",
            DynamicObjectCamera.RIGHT: "Right",
        }

    def convert_to_class(self) -> typing.Dict[DynamicObjectCamera, typing.List[DynamicObjectDetectionTimeframe]]:
        """Converts data to a dictionary mapping DynamicObjectCamera to a list of DynamicObjectDetectionTimeframe."""
        out: typing.Dict[DynamicObjectCamera, typing.List[DynamicObjectDetectionTimeframe]] = {}

        for _, row in self.data.iterrows():
            for camera in DynamicObjectCamera:
                if camera not in out:
                    out[camera] = []
                timestamp = int(row[f"{self.camera_strings[camera]}_timestamp"])
                if timestamp == 0 or (len(out[camera]) > 0 and timestamp == out[camera][-1].timestamp):
                    continue

                dynamic_objects = []

                number_of_dynamic_objects = int(row[f"{self.camera_strings[camera]}_numObjects"])
                for i in range(number_of_dynamic_objects):
                    object_id = int(row[("objects.id", i)])
                    grappa_class_type = GrappaDetectorType(
                        int(row[(f"{self.camera_strings[camera]}_objects_classType", i)])
                    )
                    confidence = row[(f"{self.camera_strings[camera]}_objects_confidence", i)]
                    center_x = row[(f"{self.camera_strings[camera]}_objects_centerPointWorld.x", i)]
                    center_y = row[(f"{self.camera_strings[camera]}_objects_centerPointWorld.y", i)]

                    dynamic_object_type: ObjectClass = None
                    if grappa_class_type == GrappaDetectorType.PED:
                        dynamic_object_type = ObjectClass.PEDESTRIAN
                    elif grappa_class_type == GrappaDetectorType.CAR:
                        dynamic_object_type = ObjectClass.CAR
                    elif grappa_class_type == GrappaDetectorType.MTB:
                        dynamic_object_type = ObjectClass.MOTORCYCLE
                    elif grappa_class_type == GrappaDetectorType.BCL:
                        dynamic_object_type = ObjectClass.BICYCLE
                    else:
                        dynamic_object_type = ObjectClass.UNKNOWN

                    if dynamic_object_type == ObjectClass.CAR or dynamic_object_type == ObjectClass.BICYCLE:
                        length_2 = row[(f"{self.camera_strings[camera]}_objects_cuboidSizeWorld.x", i)] * 0.5
                        width_2 = row[(f"{self.camera_strings[camera]}_objects_cuboidSizeWorld.y", i)] * 0.5
                        cos_yaw = math.cos(row[(f"{self.camera_strings[camera]}_objects_cuboidYawWorld", i)])
                        sin_yaw = math.sin(row[(f"{self.camera_strings[camera]}_objects_cuboidYawWorld", i)])

                        pnt0_x = center_x + length_2 * cos_yaw - width_2 * sin_yaw
                        pnt0_y = center_y + length_2 * sin_yaw + width_2 * cos_yaw
                        pnt1_x = center_x - length_2 * cos_yaw - width_2 * sin_yaw
                        pnt1_y = center_y - length_2 * sin_yaw + width_2 * cos_yaw
                        pnt2_x = center_x - length_2 * cos_yaw + width_2 * sin_yaw
                        pnt2_y = center_y - length_2 * sin_yaw - width_2 * cos_yaw
                        pnt3_x = center_x + length_2 * cos_yaw + width_2 * sin_yaw
                        pnt3_y = center_y + length_2 * sin_yaw - width_2 * cos_yaw

                        polygon = [
                            DynPoint(pnt0_x, pnt0_y, 0, 0),
                            DynPoint(pnt1_x, pnt1_y, 0, 0),
                            DynPoint(pnt2_x, pnt2_y, 0, 0),
                            DynPoint(pnt3_x, pnt3_y, 0, 0),
                        ]

                        dynamic_object = CuboidDynamicObjectDetection(
                            object_id, dynamic_object_type, confidence, center_x, center_y, polygon, length_2, width_2
                        )
                        dynamic_objects.append(dynamic_object)
                    elif dynamic_object_type == ObjectClass.PEDESTRIAN or dynamic_object_type == ObjectClass.MOTORCYCLE:
                        raduis = row[(f"{self.camera_strings[camera]}_objects_planeSizeWorld.x", i)] * 0.5

                        nbr_points_to_sample = 50
                        angles = np.array(range(0, nbr_points_to_sample)) * 2 * np.pi / nbr_points_to_sample
                        polygon = [
                            DynPoint(center_x + raduis * math.sin(angle), center_y + raduis * math.cos(angle), 0, 0)
                            for angle in angles
                        ]

                        dynamic_object = CylinderDynamicObjectDetection(
                            object_id, dynamic_object_type, confidence, center_x, center_y, polygon, raduis
                        )
                        dynamic_objects.append(dynamic_object)

                timeframe = DynamicObjectDetectionTimeframe(timestamp, len(dynamic_objects), dynamic_objects)
                out[camera].append(timeframe)
        return out
