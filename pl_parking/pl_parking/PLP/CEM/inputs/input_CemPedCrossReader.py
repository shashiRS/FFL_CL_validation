#!/usr/bin/env python3
"""Defining input CemPedestrianReader pedestrian crossing testcases"""
import typing
from dataclasses import dataclass


@dataclass
class PedCrossPoint:
    """Represents a point in the coordinate system."""

    x: float
    y: float


@dataclass
class PedCrossScenarioConfidences:
    """Represents confidence levels for different pedestrian detection."""

    confidence_percent: float


@dataclass
class PedCrossDetection:
    """Represents a pedestrian crossing detection."""

    Ped_id: int
    ped_corners: typing.List[PedCrossPoint]
    scenario_confidence: PedCrossScenarioConfidences


@dataclass
class PedCrossTimeFrame:
    """Represents a time frame containing pedestrian crossing detection."""

    timestamp: int
    number_of_peds: int
    pedestrian_crossing_detection: typing.List[PedCrossDetection]


class PedCrossReader:
    """Reader class for pedestrian crossing detection."""

    def __init__(self, reader):
        """Initialize object attributes."""
        self.data = reader
        self.synthetic_flag = self.__is_synthetic()
        self.number_of_delimiters = len(self.data.filter(regex="CemPed_pedId").columns)

    def __is_synthetic(self):
        """Check if the data contains synthetic signals."""
        if "synthetic_signal" in self.data.columns:
            return True
        else:
            return False

    def convert_to_class(self) -> typing.List[PedCrossTimeFrame]:
        """
        Converts data to PedCrossTimeFrame instances.

        Returns:
            typing.List[PedCrossTimeFrame]: List of PedCrossTimeFrame instances.
        """
        out = []
        for _, row in self.data.iterrows():
            ped_cross_array: typing.List[PedCrossTimeFrame] = []
            if len(ped_cross_array) > 0:
                if ped_cross_array[-1].timestamp == row["CemPed_timestamp"]:
                    continue

            for i in range(int(row["Cem_numberOfPedCrossings"])):
                if row[("Cem_pedCrossings_Id", i)] != 0:
                    corners = []
                    for k in range(4):
                        p = PedCrossPoint(
                            float(row[(f"Cem_pedCrossings_P{k}_x", i)]), float(row[(f"Cem_pedCrossings_P{k}_y", i)])
                        )
                        corners.append(p)

                    scenario_confidence = PedCrossScenarioConfidences(
                        int(row[("Cem_pedCrossings_Confidence", i)]),
                    )

                    ped_cross_detection = PedCrossDetection(
                        int(row[("Cem_pedCrossings_Id", i)]),
                        corners,
                        scenario_confidence,
                    )

                    ped_cross_array.append(ped_cross_detection)

            tf = PedCrossTimeFrame(row["Cem_pedCrossings_timestamp"], row["Cem_numberOfPedCrossings"], ped_cross_array)
            out.append(tf)
        return out
