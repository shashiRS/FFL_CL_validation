#!/usr/bin/env python3
"""Defining input CemTpfReader testcases"""
# TPF
import typing
from dataclasses import dataclass
from enum import Enum


class MaintenanceState(Enum):
    """Enumeration for maintenance states."""

    MEASURED: int = 0
    PREDICTED: int = 1
    DELETED: int = 2
    INVALID: int = 3


class DynamicProperty(Enum):
    """Enumeration for dynamic properties."""

    UNKNOWN: int = 0
    MOVING: int = 1
    STATIONARY: int = 2
    STOPPED: int = 3


class ObjectClass(Enum):
    """Enumeration representing different types of objects."""

    UNKNOWN: int = 0
    CAR: int = 1
    PEDESTRIAN: int = 2
    TWOWHEELER: int = 3
    VAN: int = 4
    TRUCK: int = 5
    SHOPPING_CART: int = 6
    ANIMAL: int = 7


@dataclass
class DynPoint:
    """Represents a dynamic point with coordinates and variance."""

    x: float
    y: float
    var_x: float
    var_y: float
    covar: float


@dataclass
class DynamicObject:
    """Represents a detected dynamic object."""

    object_id: int
    object_class: ObjectClass
    class_certainty: float
    dyn_property: DynamicProperty
    # dyn_property_certainty: int
    shape: typing.List[DynPoint]
    existence_prob: float
    orientation: float
    orientation_std: float
    velocity_x: float
    velocity_y: float
    yaw_rate: float
    velocity_std_x: float
    velocity_std_y: float
    yaw_rate_std: float
    center_x: float
    center_y: float
    acceleration_x: float
    acceleration_y: float
    acceleration_std_x: float
    acceleration_std_y: float
    state: MaintenanceState
    # contained_in_last_sensor_update: int
    lifetime: int


@dataclass
class TPFTimeFrame:
    """Timeframe for TPF data."""

    timestamp: int
    num_objects: int
    dynamic_objects: typing.List[DynamicObject]


class TPFReader:
    """Reader class for TPF."""

    def __init__(self, reader):
        """Initialize object attributes."""
        self.data = reader
        self._synthetic_flag = self.__is_synthetic()
        # self.number_of_objects = len(self.data.filter(regex="objects.existenceProb").columns)
        self.number_of_objects = len(self.data.filter(regex="objects.existenceCertainty").columns)

    def __is_synthetic(self):
        """Check if the data contains synthetic signals."""
        if "synthetic_signal" in self.data.columns.tolist():
            return True
        else:
            return False

    def convert_to_class(self) -> typing.List[TPFTimeFrame]:
        """Converts TPF data to a list of TPFTimeFrame objects."""
        timeframes: typing.List[TPFTimeFrame] = []

        for _, row in self.data.iterrows():
            objects: typing.List[DynamicObject] = []
            timestamp = int(row["sigTimestamp"])
            # self.number_of_objects = int(row["numberOfObjects"])
            if len(timeframes) > 0 and timestamp == timeframes[-1].timestamp:
                continue

            for i in range(self.number_of_objects):
                existence_prob = float(row[("objects.existenceCertainty", i)])

                if existence_prob > 0.:
                    object_id = int(row[("objects.id", i)])
                    object_class = ObjectClass(int(row[("objects.objectClass", i)]))
                    class_certainty = float(row[("objects.classProbability", i)])
                    dyn_property = DynamicProperty(int(row[("objects.dynamicProperty", i)]))
                    existence_prob = int(row[("objects.existenceCertainty", i)])
                    orientation = row[("objects.orientation", i)]
                    orientation_std = row[("objects.orientationStandardDeviation", i)]
                    velocity_x = row[("objects.velocity.x", i)]
                    velocity_y = row[("objects.velocity.y", i)]
                    yaw_rate = row[("objects.yawRate", i)]
                    velocity_std_x = row[("objects.velocityStandardDeviation.x", i)]
                    velocity_std_y = row[("objects.velocityStandardDeviation.y", i)]
                    yaw_rate_std = row[("objects.yawRateStandardDeviation", i)]
                    center_x = row[("objects.shape.referencePoint.x", i)]
                    center_y = row[("objects.shape.referencePoint.y", i)]
                    acceleration_x = row[("objects.acceleration.x", i)]
                    acceleration_y = row[("objects.acceleration.y", i)]
                    acceleration_std_x = row[("objects.accelerationStandardDeviation.x", i)]
                    acceleration_std_y = row[("objects.accelerationStandardDeviation.y", i)]
                    state = MaintenanceState(row[("objects.state", i)])
                    lifetime = int(row[("objects.lifetime", i)])

                    points: typing.List[DynPoint] = []
                    for j in range(4):
                        pnt_x = row[(f"objects.shape.points[{j}].position.x", i)]
                        pnt_y = row[(f"objects.shape.points[{j}].position.y", i)]
                        pnt_var_x = row[(f"objects.shape.points[{j}].varianceX", i)]
                        pnt_var_y = row[(f"objects.shape.points[{j}].varianceY", i)]
                        pnt_covar = row[(f"objects.shape.points[{j}].covarianceXY", i)]

                        points.append(DynPoint(pnt_x, pnt_y, pnt_var_x, pnt_var_y, pnt_covar))

                    dynamic_object = DynamicObject(
                        object_id,
                        object_class,
                        class_certainty,
                        dyn_property,
                        # dyn_property_certainty,
                        points,
                        existence_prob,
                        orientation,
                        orientation_std,
                        velocity_x,
                        velocity_y,
                        yaw_rate,
                        velocity_std_x,
                        velocity_std_y,
                        yaw_rate_std,
                        center_x,
                        center_y,
                        acceleration_x,
                        acceleration_y,
                        acceleration_std_x,
                        acceleration_std_y,
                        state,
                        # contained_in_last_sensor_update,
                        lifetime,
                    )
                    objects.append(dynamic_object)

            tf = TPFTimeFrame(timestamp, len(objects), objects)
            timeframes.append(tf)

        return timeframes
