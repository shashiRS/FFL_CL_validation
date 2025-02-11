#!/usr/bin/env python3
"""Defining input PmsdPedReader pedestrian crossing testcases"""
import typing
from dataclasses import dataclass
from enum import IntEnum


@dataclass
class PMSDPedCrossPoint:
    """Dataclass representing a point on a Pmsd ped crossing."""

    x: float
    y: float


@dataclass
class PMSDPedScenarioConfidences:
    """Dataclass representing confidences of parking scenarios for a PMSD Ped Crossings."""

    confidence_percent: float


class PMSDPedCrossCamera(IntEnum):
    """Enumeration for Pmsd camera types."""

    FRONT: int = 0
    REAR: int = 1
    LEFT: int = 2
    RIGHT: int = 3


@dataclass
class PMSDPedCross:
    """
    Dataclass representing a Pmsd ped with attributes:
    existence_probability, ped_corners, and scenario_confidence.
    """

    #  Accurate signals of Pedestrian need be updated here.
    ped_corners: typing.List[PMSDPedCrossPoint]
    scenario_confidence: PMSDPedScenarioConfidences


@dataclass
class PMSDPedCrossTimeFrame:
    """
    Dataclass representing a timeframe with Pmsd data with attributes:
    timestamp, number_of_peds, and pedestrian crossing.
    """

    timestamp: int
    number_of_peds: int
    pedestrian_crossing_detection: typing.List[PMSDPedCross]


class PMSDPedCrossReader:
    """Reads data for Pmsd pedestrian crossing detection."""

    def __init__(self, reader):
        """Initialize object attributes."""
        self.camera_names = ["Front", "Left", "Rear", "Right"]
        self.data = reader

    def convert_to_class(self) -> typing.Dict[PMSDPedCrossCamera, typing.List[PMSDPedCrossTimeFrame]]:
        """Converts data to a dictionary mapping PMSDPedCrossCamera to a list of PMSDPedCrossTimeFrame."""
        out: typing.Dict[PMSDPedCrossCamera, typing.List[PMSDPedCrossTimeFrame]] = {}
        for camera in PMSDPedCrossCamera:
            current_cam = self.camera_names[int(camera)]
            tfArray: typing.List[PMSDPedCrossTimeFrame] = []
            for _, row in self.data.iterrows():
                # Remove duplicated timestamps
                if len(tfArray) > 0:

                    if row[f"PMDPEDCROS_{current_cam}_timestamp"] == tfArray[-1].timestamp:
                        continue

                ped_array = []
                for i in range(int(row[f"PMDPEDCROS_{current_cam}_numberOfCrossings"])):

                    corners = []
                    for k in range(4):
                        p = PMSDPedCrossPoint(
                            float(row[(f"PMDPEDCROS_{current_cam}_P{k}_x", i)]),
                            float(row[(f"PMDPEDCROS_{current_cam}_P{k}_y", i)]),
                        )
                        corners.append(p)

                    scenario_confidence = PMSDPedScenarioConfidences(
                        int(row[(f"PMDPEDCROS_{current_cam}_lineConfidence", i)]),
                    )
                    ped = PMSDPedCross(
                        corners,
                        scenario_confidence,
                    )
                    ped_array.append(ped)

                tf = PMSDPedCrossTimeFrame(
                    row[f"PMDPEDCROS_{current_cam}_timestamp"],
                    row[f"PMDPEDCROS_{current_cam}_numberOfCrossings"],
                    ped_array,
                )
                tfArray.append(tf)
            out[camera] = tfArray
        return out
