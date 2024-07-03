#!/usr/bin/env python3
"""Defining input DGPSReader testcases"""
import typing
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from pl_parking.common_ft_helper import read_signal
from pl_parking.PLP.CEM.ground_truth.utm_helper import UtmHelper
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import VedodoReader


@dataclass
class DgpsTimeframe:
    """Dataclass representing a DgpsTimeframe."""

    timestamp: int
    # original signal
    longitude: float
    latitude: float
    heading_deg: float
    # utm
    utm_x: float
    utm_y: float
    heading_from_north_rad: float


class DGPSBuffer:
    """Buffer class for adressing DGPS data."""

    def __init__(self, buffer: typing.List[DgpsTimeframe]):
        """Initialize object attributes."""
        self.buffer = buffer
        # original signals
        self.longitude_interpolation_method = interp1d(
            [tf.timestamp for tf in self.buffer], [tf.longitude for tf in self.buffer]
        )
        self.latitude_interpolation_method = interp1d(
            [tf.timestamp for tf in self.buffer], [tf.latitude for tf in self.buffer]
        )
        self.heading_interpolation_method = interp1d(
            [tf.timestamp for tf in buffer], np.unwrap([tf.heading_deg for tf in self.buffer])
        )
        # utm
        self.utm_x_interpolation_method = interp1d(
            [tf.timestamp for tf in self.buffer], [tf.utm_x for tf in self.buffer]
        )
        self.utm_y_interpolation_method = interp1d(
            [tf.timestamp for tf in self.buffer], [tf.utm_y for tf in self.buffer]
        )
        self.heading_from_north_interpolation_method = interp1d(
            [tf.timestamp for tf in buffer], np.unwrap([tf.heading_from_north_rad for tf in buffer])
        )

    def estimate_vehicle_pose(self, target_timestamp: int):
        """Estimates vehicle pose at a target timestamp."""
        if target_timestamp < self.buffer[0].timestamp or target_timestamp > self.buffer[-1].timestamp:
            return None
        return DgpsTimeframe(
            target_timestamp,
            self.longitude_interpolation_method(target_timestamp)[()],
            self.latitude_interpolation_method(target_timestamp)[()],
            self.heading_interpolation_method(target_timestamp)[()],
            self.utm_x_interpolation_method(target_timestamp)[()],
            self.utm_y_interpolation_method(target_timestamp)[()],
            self.heading_from_north_interpolation_method(target_timestamp)[()],
        )


class DGPSReader:
    """Class for reading and processing DGPS data."""

    def __init__(self, reader):
        """Initialize object attributes."""
        self.offset = None
        self.data = reader

    @staticmethod
    def data_mapping(base_string):
        """Maps base string to data keys for a vehicle pose."""
        return {
            "timestamp": "Time.UTCTime",
            "longitude": "Position.Longitude",
            "latitude": "Position.Latitude",
            "heading": "Angles.Heading",
        }

    def __get_base_string(self, reader):
        """Gets the base string for the reader."""
        return "Ethernet RT-Range.Hunter"

    def __get_ODO_time_string(self, reader):
        """Gets the ODO time string from the reader."""
        reader_obj = VedodoReader(reader)
        base = reader_obj.get_base_string(reader)
        map = reader_obj.data_mapping(base)
        return f'{base}.{map["timestamp"]}'

    def __read_all_to_pandas(self, reader):
        """Reads all data to a pandas DataFrame from the reader."""
        self.data = pd.DataFrame()
        data_map = self.data_mapping(self.base_string)

        for new_signal_name, signal_name in data_map.items():
            _, self.data = read_signal(reader, self.data, new_signal_name, f"{self.base_string}.{signal_name}")

        self.data = self.data[self.data["timestamp"] > 0]
        odoString = self.__get_ODO_time_string(reader)
        self.offset = self.data["timestamp"].iloc[-1] - reader[odoString][-1]

    def convert_to_class(self) -> DGPSBuffer:
        """Converts data to a DGPSBuffer class."""
        dgps_buffer: typing.List[DgpsTimeframe] = []
        self.data = self.data[self.data["dpgs_timestamp"] > 0]
        self.offset = self.data["dpgs_timestamp"].iloc[-1] - self.data["vedodo_timestamp_us"].iloc[-1]

        for _, row in self.data.iterrows():
            utm_x, utm_y = UtmHelper.get_utm_from_lat_lon(row["dpgs_latitude"], row["dpgs_longitude"])
            heading_from_north_rad = UtmHelper.get_relative_rotation_from_east(row["dpgs_heading"])  # TODO: check

            dgps = DgpsTimeframe(
                row["dpgs_timestamp"] - self.offset,
                row["dpgs_longitude"],
                row["dpgs_latitude"],
                row["dpgs_heading"],
                utm_x,
                utm_y,
                heading_from_north_rad,
            )
            dgps_buffer.append(dgps)

        return DGPSBuffer(dgps_buffer)
