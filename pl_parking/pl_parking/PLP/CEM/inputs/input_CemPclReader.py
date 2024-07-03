#!/usr/bin/env python3
"""Defining input CemPclReader testcases"""
# PM and WS convert to class functions
import typing
from dataclasses import dataclass

from pl_parking.PLP.CEM.constants import ConstantsCemInput


@dataclass
class PCLPoint:
    """Represents a point in a Point Cloud (PCL)."""

    x: float
    y: float

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


@dataclass
class PCLDelimiter:
    """Represents a delimiter in a PCL."""

    delimiter_id: int
    delimiter_type: int
    start_point: PCLPoint
    end_point: PCLPoint
    confidence_percent: float

    def __eq__(self, other):
        return (
            self.delimiter_id == other.delimiter_id
            and self.delimiter_type == other.delimiter_type
            and self.start_point == other.start_point
            and self.end_point == other.end_point
            and self.confidence_percent == other.confidence_percent
        )

    def __hash__(self):
        return id(self)


@dataclass
class PCLTimeFrame:
    """Represents a time frame in PCL data."""

    timestamp: int
    num_pcl_delimiters: int
    pcl_delimiter_array: typing.List[PCLDelimiter]
    wheel_stopper_array: typing.List[PCLDelimiter]
    wheel_locker_array: typing.List[PCLDelimiter]
    stop_line_array: typing.List[PCLDelimiter]


class PclDelimiterReader:
    """Reader for the PCL Delimiter"""

    def __init__(self, reader):
        """Initialize object attributes."""
        self.data = reader

        self.synthetic_flag = self.__is_synthetic()
        self.number_of_delimiters = len(self.data.filter(regex="delimiterId").columns)
        self.PCLEnum = ConstantsCemInput.PCLEnum
        self.WSEnum = ConstantsCemInput.WSEnum

    def __is_synthetic(self):
        """Check if the data contains synthetic signals."""
        if "synthetic_signal" in self.data.columns:
            return True
        else:
            return False

    def convert_to_class(self) -> typing.List[PCLTimeFrame]:
        """Convert the read data to a list of PCLTimeFrame objects."""
        out: typing.List[PCLTimeFrame] = []
        for _, row in self.data.as_plain_df.iterrows():
            pcl_delimiter_array = []
            ws_delimiter_array = []
            wl_delimiter_array = []
            sl_delimiter_array = []
            if len(out) > 0:
                if row["numPclDelimiters_timestamp"] == out[-1].timestamp:
                    continue

            for i in range(int(row["numPclDelimiters"])):
                if int(row[("delimiterType", i)]) == self.PCLEnum or int(row[("delimiterType", i)]) == self.WSEnum:
                    delimiter = PCLDelimiter(
                        int(row[("delimiterId", i)]),
                        int(row[("delimiterType", i)]),
                        PCLPoint(float(row[("P0_x", i)]), float(row[("P0_y", i)])),
                        PCLPoint(float(row[("P1_x", i)]), float(row[("P1_y", i)])),
                        float(row[("confidencePercent", i)]),
                    )

                    if int(row[("delimiterType", i)]) == self.PCLEnum:
                        pcl_delimiter_array.append(delimiter)
                    else:
                        ws_delimiter_array.append(delimiter)
                        wl_delimiter_array.append(delimiter)
                        sl_delimiter_array.append(delimiter)

            tf = PCLTimeFrame(
                row["numPclDelimiters_timestamp"],
                row["numPclDelimiters"],
                pcl_delimiter_array,
                ws_delimiter_array,
                wl_delimiter_array,
                sl_delimiter_array,
            )
            out.append(tf)

        return out
