#!/usr/bin/env python3
"""Defining input CemVedodoReader testcases"""
# Vedodo
import math
import typing
from dataclasses import dataclass

import numpy as np
from scipy.interpolate import interp1d


@dataclass
class VedodoTimeframe:
    """Dataclass representing a timestamped Vedodo timeframe."""

    timestamp: int
    x: float
    y: float
    yaw: float


@dataclass
class RelativeMotion:
    """Dataclass representing the relative motion."""

    lateral_translation: float
    longitudinal_translation: float
    yaw_rotation: float


class VedodoBuffer:
    """Buffer class for storing Vedodo data."""

    def __init__(self, buffer: typing.List[VedodoTimeframe]):
        """Initialize object attributes."""
        self.buffer = buffer
        self.x_interpolation_method = interp1d([tf.timestamp for tf in buffer], [tf.x for tf in buffer])
        self.y_interpolation_method = interp1d([tf.timestamp for tf in buffer], [tf.y for tf in buffer])
        self.yaw_interpolation_method = interp1d([tf.timestamp for tf in buffer], np.unwrap([tf.yaw for tf in buffer]))

    def estimate_vehicle_pose(self, target_timestamp: int):
        """Estimate the vehicle pose at a target timestamp."""
        return VedodoTimeframe(
            target_timestamp,
            self.x_interpolation_method(target_timestamp)[()],
            self.y_interpolation_method(target_timestamp)[()],
            self.yaw_interpolation_method(target_timestamp)[()],
        )

    def calc_relative_motion(self, ts1: int, ts2: int):
        """Calculate the relative motion between two timestamps."""
        pose1 = self.estimate_vehicle_pose(ts1)
        pose2 = self.estimate_vehicle_pose(ts2)

        dx = pose2.x - pose1.x
        dy = pose2.y - pose1.y
        dyaw = pose2.yaw - pose1.yaw

        long_diff = math.cos(pose1.yaw) * dx + math.sin(pose1.yaw) * dy
        lat_diff = -math.sin(pose1.yaw) * dx + math.cos(pose1.yaw) * dy

        return RelativeMotion(lat_diff, long_diff, dyaw)


class VedodoReader:
    """Class for reading and processing data from Vedodo."""

    def __init__(self, reader):
        """Initialize object attributes."""
        self._synthetic_flag = self.__is_synthetic(reader)
        self.data = reader

    @staticmethod
    def __is_synthetic(reader):
        """Check if the data from the reader is synthetic.

        Args:
            reader: The reader object.

        Returns:
            bool: True if the data is synthetic, False otherwise.
        """
        if "synthetic_signal" in reader.as_plain_df.columns.tolist():
            return True
        else:
            return False

    def convert_to_class(self) -> VedodoBuffer:
        """Converts data from the reader to VedodoBuffer class objects"""
        vedodo_buffer: typing.List[VedodoTimeframe] = []

        for _, row in self.data.as_plain_df.iterrows():
            vedodo_buffer.append(VedodoTimeframe(row["vedodo_timestamp_us"], row["x"], row["y"], row["yaw"]))

        return VedodoBuffer(vedodo_buffer)
