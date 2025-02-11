#!/usr/bin/env python3
"""Defining input CemWsReader testcases"""
# PM and WS convert to class functions
import typing
from dataclasses import dataclass

from pl_parking.PLP.CEM.constants import ConstantsCemInput
from pl_parking.PLP.CEM.inputs.input_PmdReader import PMDCamera, PMDLine, PMDLinePoint, PMDTimeFrame


@dataclass
class WSPoint:
    """Represents a point in a Point Cloud (WS)."""

    x: float
    y: float

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


@dataclass
class WSDelimiter:
    """Represents a delimiter in a WS."""

    delimiter_id: int
    delimiter_type: int
    start_point: WSPoint
    end_point: WSPoint
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
class WSTimeFrame:
    """Represents a time frame in WS data."""

    timestamp: int
    num_pcl_delimiters: int
    pcl_delimiter_array: typing.List[WSDelimiter]
    wheel_stopper_array: typing.List[WSDelimiter]
    wheel_locker_array: typing.List[WSDelimiter]
    stop_line_array: typing.List[WSDelimiter]


class WsDelimiterReader:
    """Reader for the WS Delimiter"""

    def __init__(self, reader):
        """Initialize object attributes."""
        self.data = reader

        self.synthetic_flag = self.__is_synthetic()
        self.number_of_delimiters = len(self.data.filter(regex="delimiterId").columns)
        self.WSEnum = ConstantsCemInput.WSEnum
        self.WSEnum = ConstantsCemInput.WSEnum

    def __is_synthetic(self):
        """Check if the data contains synthetic signals."""
        if "synthetic_signal" in self.data.columns:
            return True
        else:
            return False

    def convert_to_class(self) -> typing.List[WSTimeFrame]:
        """Convert the read data to a list of WSTimeFrame objects."""
        out: typing.List[WSTimeFrame] = []

        for _, row in self.data.as_plain_df.iterrows():
            pcl_delimiter_array = []
            ws_delimiter_array = []
            wl_delimiter_array = []
            sl_delimiter_array = []
            if len(out) > 0:
                if row["CemWs_timestamp"] == out[-1].timestamp:
                    continue

            for i in range(int(row["CemWs_numberOfLines"])):
                if (
                    int(row[("CemWs_delimiterType", i)]) == self.WSEnum
                    or int(row[("CemWs_delimiterType", i)]) == self.WSEnum
                ):
                    delimiter = WSDelimiter(
                        int(row[("CemWs_delimiterId", i)]),
                        int(row[("CemWs_delimiterType", i)]),
                        WSPoint(
                            float(row[("CemWs_parkingLines_lineStartX", i)]),
                            float(row[("CemWs_parkingLines_lineStartY", i)]),
                        ),
                        WSPoint(
                            float(row[("CemWs_parkingLines_lineEndX", i)]),
                            float(row[("CemWs_parkingLines_lineEndY", i)]),
                        ),
                        float(row[("CemWs_parkingLines_lineConfidence", i)]),
                    )

                    if int(row[("CemWs_delimiterType", i)]) == self.WSEnum:
                        pcl_delimiter_array.append(delimiter)
                    else:
                        ws_delimiter_array.append(delimiter)
                        wl_delimiter_array.append(delimiter)
                        sl_delimiter_array.append(delimiter)

            tf = WSTimeFrame(
                row["CemWs_timestamp"],
                row["CemWs_numberOfLines"],
                pcl_delimiter_array,
                ws_delimiter_array,
                wl_delimiter_array,
                sl_delimiter_array,
            )
            out.append(tf)

        return out


class WSDetectionReader:
    """Reads data for WSDetection."""

    def __init__(self, reader):
        """Initialize object attributes."""
        self.data = reader
        self.camera_strings = self.__get_camera_strings()

    @staticmethod
    def __get_camera_strings():
        """Returns a dictionary mapping camera types to their corresponding strings."""
        return {PMDCamera.FRONT: "Front", PMDCamera.REAR: "Rear", PMDCamera.LEFT: "Left", PMDCamera.RIGHT: "Right"}

    def convert_to_class(self) -> typing.Dict[PMDCamera, typing.List[PMDTimeFrame]]:
        """Converts data to a dictionary mapping PMDCamera to a list of PMDTimeFrame."""
        out: typing.Dict[PMDCamera, typing.List[PMDTimeFrame]] = {}

        for camera in PMDCamera:
            timeframes = []

            for _, row in self.data.iterrows():

                timestamp = row[f"PMDWs_{self.camera_strings[camera]}_timestamp"]
                number_of_lines = int(row[f"PMDWs_{self.camera_strings[camera]}_numberOfLines"])
                pmd_lines = []

                for i in range(number_of_lines):
                    line = PMDLine(
                        PMDLinePoint(
                            row[(f"PMDWs_{self.camera_strings[camera]}_lineStartX", i)] * -1,
                            row[(f"PMDWs_{self.camera_strings[camera]}_lineStartY", i)] * -1,
                        ),
                        PMDLinePoint(
                            row[(f"PMDWs_{self.camera_strings[camera]}_lineEndX", i)] * -1,
                            row[(f"PMDWs_{self.camera_strings[camera]}_lineEndY", i)] * -1,
                        ),
                        row[(f"PMDWs_{self.camera_strings[camera]}_lineConfidence", i)],
                    )

                    pmd_lines.append(line)

                timeframes.append(PMDTimeFrame(timestamp, camera, number_of_lines, pmd_lines))

            out[camera] = timeframes

        return out
