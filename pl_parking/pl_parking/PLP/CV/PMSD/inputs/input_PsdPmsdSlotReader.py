#!/usr/bin/env python3
"""Defining input PsdSlotReader testcases"""
import typing
from dataclasses import dataclass
from enum import IntEnum

from pl_parking.PLP.CV.PMSD.inputs.input_PmdReader import PMDCamera, PMDReader


@dataclass
class PSDSlotPoint:
    """Dataclass representing a point on a PSD slot."""

    x: float
    y: float

    def __sub__(self, other):
        return PSDSlotPoint(self.x - other.x, self.y - other.y)


class PSDCamera(IntEnum):
    """Enumeration for PSD camera types."""

    FRONT: int = 0
    REAR: int = 1
    LEFT: int = 2
    RIGHT: int = 3


@dataclass
class PSDSlotScenarioConfidences:
    """Dataclass representing confidences of different parking scenarios for a PSD slot."""

    angled: int
    parallel: int
    perpendicular: int


@dataclass
class PSDSlot:
    """
    Dataclass representing a PSD slot with attributes:
    existence_probability, slot_corners, and scenario_confidence.
    """

    existence_probability: float
    slot_corners: typing.List[PSDSlotPoint]
    scenario_confidence: PSDSlotScenarioConfidences


@dataclass
class PSDTimeFrame:
    """
    Dataclass representing a timeframe with PSD data with attributes:
    timestamp, number_of_slots, and parking_slots.
    """

    timestamp: int
    number_of_slots: int
    parking_slots: typing.List[PSDSlot]


class PSDSlotReader:
    """Reads data for PSD slots."""

    def __init__(self, reader):
        """Initialize object attributes."""
        self.data = reader

    def convert_to_class(self) -> typing.Dict[PMDCamera, typing.List[PSDTimeFrame]]:
        """Converts data to a dictionary mapping PSDCamera to a list of PSDTimeFrame."""
        out: typing.Dict[PMDCamera, typing.List[PSDTimeFrame]] = {}
        for camera in PMDCamera:
            current_cam = PMDReader.get_camera_strings()[camera]
            tfArray: typing.List[PSDTimeFrame] = []
            for _, row in self.data.iterrows():
                # Remove duplicated timestamps
                if len(tfArray) > 0:
                    if row[f"PmsdSlot_{current_cam}_timestamp"] == tfArray[-1].timestamp:
                        continue

                slot_array = []
                for i in range(int(row[f"PmsdSlot_{current_cam}_numberOfSlots"])):
                    corners = []
                    for k in range(4):
                        xx = float(row[(f"PmsdSlot_{current_cam}_P{k}_x", i)])
                        yy = float(row[(f"PmsdSlot_{current_cam}_P{k}_y", i)])
                        p = PSDSlotPoint(xx, yy)
                        corners.append(p)

                    scenario_confidence = PSDSlotScenarioConfidences(0, 0, 0)
                    slot = PSDSlot(
                        float(row[(f"PmsdSlot_{current_cam}_existenceProbability", i)]),
                        corners,
                        scenario_confidence,
                    )
                    slot_array.append(slot)
                tf = PSDTimeFrame(
                    row[f"PmsdSlot_{current_cam}_timestamp"], row[f"PmsdSlot_{current_cam}_numberOfSlots"], slot_array
                )
                tfArray.append(tf)
            out[camera] = tfArray
        return out
