#!/usr/bin/env python3
"""Defining input PsdSlotReader testcases"""
import typing
from dataclasses import dataclass
from enum import IntEnum


@dataclass
class PSDSlotPoint:
    """Dataclass representing a point on a PSD slot."""

    x: float
    y: float


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
        self.camera_names = ["Front", "Left", "Rear", "Right"]
        self.data = reader

    def convert_to_class(self) -> typing.Dict[PSDCamera, typing.List[PSDTimeFrame]]:
        """Converts data to a dictionary mapping PSDCamera to a list of PSDTimeFrame."""
        out: typing.Dict[PSDCamera, typing.List[PSDTimeFrame]] = {}
        for camera in PSDCamera:
            current_cam = self.camera_names[int(camera)]
            tfArray: typing.List[PSDTimeFrame] = []
            for _, row in self.data.iterrows():
                # Remove duplicated timestamps
                if len(tfArray) > 0:
                    if row[f"PsdSlot_{current_cam}_timestamp"] == tfArray[-1].timestamp:
                        continue

                slot_array = []
                for i in range(int(row[f"PsdSlot_{current_cam}_numberOfSlots"])):
                    corners = []
                    for k in range(4):
                        p = PSDSlotPoint(
                            float(row[(f"PsdSlot_{current_cam}_parkingLines_P{k}_x", i)]),
                            float(row[(f"PsdSlot_{current_cam}_parkingLines_P{k}_y", i)]),
                        )
                        corners.append(p)

                    scenario_confidence = PSDSlotScenarioConfidences(
                        int(row[(f"PsdSlot_{current_cam}_parkingLines_sc_angled", i)]),
                        int(row[(f"PsdSlot_{current_cam}_parkingLines_sc_parallel", i)]),
                        int(row[(f"PsdSlot_{current_cam}_parkingLines_sc_perpendicular", i)]),
                    )

                    slot = PSDSlot(
                        float(row[(f"PsdSlot_{current_cam}_parkingLines_existenceProbability", i)]),
                        corners,
                        scenario_confidence,
                    )
                    slot_array.append(slot)
                tf = PSDTimeFrame(
                    row[f"PsdSlot_{current_cam}_timestamp"], row[f"PsdSlot_{current_cam}_numberOfSlots"], slot_array
                )
                tfArray.append(tf)
            out[camera] = tfArray
        return out
