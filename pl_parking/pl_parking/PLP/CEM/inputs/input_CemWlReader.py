#!/usr/bin/env python3
"""Defining input CemWlReader testcases"""
# WL SVC
import typing

from pl_parking.PLP.CEM.inputs.input_PmdReader import PMDCamera, PMDLine, PMDLinePoint, PMDTimeFrame


class WLDetectionReader:
    """Reads data for WLDetection."""

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
                timestamp = row[f"CemWl_{self.camera_strings[camera]}_timestamp"]
                number_of_lines = int(row[f"CemWl_{self.camera_strings[camera]}_numberOfLines"])
                pmd_lines = []

                for i in range(number_of_lines):
                    line = PMDLine(
                        row[(f"CemWl_{self.camera_strings[camera]}_parkingLines_lineId", i)],
                        PMDLinePoint(
                            row[(f"CemWl_{self.camera_strings[camera]}_parkingLines_lineStartX", i)] * -1,
                            row[(f"CemWl_{self.camera_strings[camera]}_parkingLines_lineStartY", i)] * -1,
                        ),
                        PMDLinePoint(
                            row[(f"CemWl_{self.camera_strings[camera]}_parkingLines_lineEndX", i)] * -1,
                            row[(f"CemWl_{self.camera_strings[camera]}_parkingLines_lineEndY", i)] * -1,
                        ),
                        row[(f"CemWl_{self.camera_strings[camera]}_parkingLines_lineConfidence", i)],
                    )

                    pmd_lines.append(line)

                timeframes.append(PMDTimeFrame(timestamp, camera, number_of_lines, pmd_lines))

            out[camera] = timeframes

        return out
