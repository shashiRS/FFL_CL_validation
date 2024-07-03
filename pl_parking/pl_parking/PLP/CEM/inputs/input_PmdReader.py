#!/usr/bin/env python3
"""Defining input PmdReader testcases"""
# PMD
import typing
from dataclasses import dataclass
from enum import IntEnum


@dataclass
class PMDLinePoint:
    """Dataclass representing a point on a PMD line."""

    x: float
    y: float


@dataclass
class PMDLine:
    """Dataclass representing a PMD line with attributes: line_id, line_start, line_end, and line_confidence."""

    line_id: int
    line_start: PMDLinePoint
    line_end: PMDLinePoint
    line_confidence: float


class PMDCamera(IntEnum):
    """Enumeration for PMD camera types."""

    FRONT: int = 0
    REAR: int = 1
    LEFT: int = 2
    RIGHT: int = 3


@dataclass
class PMDTimeFrame:
    """
    Dataclass representing a timeframe with PMD data with attributes:
    timestamp, camera_id, num_lines, and pmd_lines.
    """

    timestamp: int
    camera_id: PMDCamera
    num_lines: int
    pmd_lines: typing.List[PMDLine]


class PMDReader:
    """Reader for PMD data."""

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
                timestamp = row[f"PMDCamera_{self.camera_strings[camera]}_timestamp"]

                if len(timeframes) > 0:
                    if timestamp == timeframes[-1].timestamp:
                        continue

                number_of_lines = int(row[f"PMDCamera_{self.camera_strings[camera]}_numberOfLines"])
                pmd_lines = []

                for i in range(number_of_lines):
                    line = PMDLine(
                        row[(f"PMDCamera_{self.camera_strings[camera]}_parkingLines_lineId", i)],
                        PMDLinePoint(
                            row[(f"PMDCamera_{self.camera_strings[camera]}_parkingLines_lineStartX", i)] * -1,
                            row[(f"PMDCamera_{self.camera_strings[camera]}_parkingLines_lineStartY", i)] * -1,
                        ),
                        PMDLinePoint(
                            row[(f"PMDCamera_{self.camera_strings[camera]}_parkingLines_lineEndX", i)] * -1,
                            row[(f"PMDCamera_{self.camera_strings[camera]}_parkingLines_lineEndY", i)] * -1,
                        ),
                        row[(f"PMDCamera_{self.camera_strings[camera]}_parkingLines_lineConfidence", i)],
                    )

                    pmd_lines.append(line)

                timeframes.append(PMDTimeFrame(timestamp, camera, number_of_lines, pmd_lines))

            out[camera] = timeframes

        return out
