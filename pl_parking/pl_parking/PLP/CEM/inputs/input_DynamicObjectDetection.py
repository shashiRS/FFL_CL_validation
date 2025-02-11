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


class TppCuboidType(Enum):
    """Enumeration for types of Grappa detectors."""

    UNKNOWN: int = 0
    CAR: int = 1
    VAN: int = 2
    TRUCK: int = 3


class TppBoundingBoxType(Enum):
    """Enumeration for types of Grappa detectors."""

    UNKNOWN: int = 0
    PEDESTRIAN: int = 1
    TWOWHEELER: int = 2
    SHOPPING_CART: int = 3
    ANIMAL: int = 4


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
                timestamp = int(row[f"sigTimestamp{self.camera_strings[camera]}"])
                if timestamp == 0 or (len(out[camera]) > 0 and timestamp == out[camera][-1].timestamp):
                    continue

                dynamic_objects = []

                number_of_dynamic_cuboids = int(row[f"numCuboid{self.camera_strings[camera]}"])
                number_of_dynamic_bboxes = int(row[f"numBBox{self.camera_strings[camera]}"])

                # Convert the cuboids
                for i in range(number_of_dynamic_cuboids):
                    # object_id = int(row[("objects.id", i)])
                    object_id = i
                    confidence = row[(f"cuboidConfidence{self.camera_strings[camera]}", i)]
                    center_x = row[(f"cuboidCenter_x{self.camera_strings[camera]}", i)]
                    center_y = row[(f"cuboidCenter_y{self.camera_strings[camera]}", i)]
                    dynamic_object_type = int(row[(f"cuboidClassType{self.camera_strings[camera]}", i)])

                    # Map TPP class to TPF class
                    if dynamic_object_type == TppCuboidType.CAR.value:
                        dynamic_object_type = ObjectClass.CAR
                    elif dynamic_object_type == TppCuboidType.VAN.value:
                        dynamic_object_type = ObjectClass.VAN
                    elif dynamic_object_type == TppCuboidType.TRUCK.value:
                        dynamic_object_type = ObjectClass.TRUCK
                    else:
                        dynamic_object_type = ObjectClass.UNKNOWN

                    if (
                        dynamic_object_type == ObjectClass.CAR
                        or dynamic_object_type == ObjectClass.VAN
                        or dynamic_object_type == ObjectClass.TRUCK
                    ):
                        length = row[(f"cuboidLength{self.camera_strings[camera]}", i)]
                        width = row[(f"cuboidWidth{self.camera_strings[camera]}", i)]
                        yaw = row[(f"cuboidYaw{self.camera_strings[camera]}", i)]
                        cos_yaw = math.cos(yaw)
                        sin_yaw = math.sin(yaw)

                        length_2 = length * 0.5
                        width_2 = width * 0.5
                        pnt0_x = center_x + length_2 * cos_yaw - width_2 * sin_yaw
                        pnt0_y = center_y + length_2 * sin_yaw + width_2 * cos_yaw
                        pnt1_x = center_x - length_2 * cos_yaw - width_2 * sin_yaw
                        pnt1_y = center_y - length_2 * sin_yaw + width_2 * cos_yaw
                        pnt2_x = center_x - length_2 * cos_yaw + width_2 * sin_yaw
                        pnt2_y = center_y - length_2 * sin_yaw - width_2 * cos_yaw
                        pnt3_x = center_x + length_2 * cos_yaw + width_2 * sin_yaw
                        pnt3_y = center_y + length_2 * sin_yaw - width_2 * cos_yaw

                        polygon = [
                            DynPoint(x=pnt0_x, y=pnt0_y, var_x=0, var_y=0, covar=0),
                            DynPoint(x=pnt1_x, y=pnt1_y, var_x=0, var_y=0, covar=0),
                            DynPoint(x=pnt2_x, y=pnt2_y, var_x=0, var_y=0, covar=0),
                            DynPoint(x=pnt3_x, y=pnt3_y, var_x=0, var_y=0, covar=0),
                        ]

                        dynamic_object = CuboidDynamicObjectDetection(
                            object_id, dynamic_object_type, confidence, center_x, center_y, polygon, length, width
                        )
                        dynamic_objects.append(dynamic_object)

                # Convert the bounding boxes
                for i in range(number_of_dynamic_bboxes):
                    # object_id = int(row[("objects.id", i)])
                    object_id = i
                    confidence = row[(f"boxConfidence{self.camera_strings[camera]}", i)]
                    center_x = row[(f"boxCenter_x{self.camera_strings[camera]}", i)]
                    center_y = row[(f"boxCenter_y{self.camera_strings[camera]}", i)]
                    dynamic_object_type = int(row[(f"boxClassType{self.camera_strings[camera]}", i)])

                    # Map TPP class to TPF class
                    if dynamic_object_type == TppBoundingBoxType.PEDESTRIAN.value:
                        dynamic_object_type = ObjectClass.PEDESTRIAN
                    elif dynamic_object_type == TppBoundingBoxType.TWOWHEELER.value:
                        dynamic_object_type = ObjectClass.TWOWHEELER
                    elif dynamic_object_type == TppBoundingBoxType.SHOPPING_CART.value:
                        dynamic_object_type = ObjectClass.SHOPPING_CART
                    elif dynamic_object_type == TppBoundingBoxType.ANIMAL.value:
                        dynamic_object_type = ObjectClass.ANIMAL
                    else:
                        dynamic_object_type = ObjectClass.UNKNOWN

                    if (
                        dynamic_object_type == ObjectClass.PEDESTRIAN
                        or dynamic_object_type == ObjectClass.TWOWHEELER
                        or dynamic_object_type == ObjectClass.SHOPPING_CART
                        or dynamic_object_type == ObjectClass.ANIMAL
                    ):
                        width = row[(f"boxWidth{self.camera_strings[camera]}", i)]

                        radius = width * 0.5

                        nbr_points_to_sample = 12  # Used tp be 50
                        angles = np.array(range(0, nbr_points_to_sample)) * 2 * np.pi / nbr_points_to_sample
                        polygon = [
                            DynPoint(center_x + radius * math.sin(angle), center_y + radius * math.cos(angle), 0, 0, 0)
                            for angle in angles
                        ]

                        dynamic_object = CylinderDynamicObjectDetection(
                            object_id, dynamic_object_type, confidence, center_x, center_y, polygon, radius
                        )
                        dynamic_objects.append(dynamic_object)

                timeframe = DynamicObjectDetectionTimeframe(timestamp, len(dynamic_objects), dynamic_objects)
                out[camera].append(timeframe)
        return out
