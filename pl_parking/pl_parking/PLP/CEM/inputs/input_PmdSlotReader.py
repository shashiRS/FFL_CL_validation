#!/usr/bin/env python3
"""Defining input PmdSlotReader testcases"""
import typing
from dataclasses import dataclass
from enum import IntEnum


@dataclass
class PMDSlotPoint:
    """Dataclass representing a point on a PMD slot."""

    x: float
    y: float


class PMDCamera(IntEnum):
    """Enumeration for PMD camera types."""

    FRONT: int = 0
    REAR: int = 1
    LEFT: int = 2
    RIGHT: int = 3


@dataclass
class PMDSlotScenarioConfidences:
    """Dataclass representing confidences of different parking scenarios for a PMD slot."""

    angled: int
    parallel: int
    perpendicular: int


@dataclass
class PMDSlot:
    """
    Dataclass representing a PMD slot with attributes:
    existence_probability, slot_corners, and scenario_confidence.
    """

    existence_probability: float
    slot_corners: typing.List[PMDSlotPoint]
    scenario_confidence: PMDSlotScenarioConfidences


@dataclass
class PMDTimeFrame:
    """
    Dataclass representing a timeframe with PMD data with attributes:
    timestamp, number_of_slots, and parking_slots.
    """

    timestamp: int
    number_of_slots: int
    parking_slots: typing.List[PMDSlot]


class PMDSlotReader:
    """Reads data for PMD slots."""

    def __init__(self, reader):
        """Initialize object attributes."""
        self.camera_names = ["Front", "Left", "Rear", "Right"]
        self.data = reader

    def convert_to_class(self) -> typing.Dict[PMDCamera, typing.List[PMDTimeFrame]]:
        """Converts data to a dictionary mapping PMDCamera to a list of PMDTimeFrame."""
        out: typing.Dict[PMDCamera, typing.List[PMDTimeFrame]] = {}
        for camera in PMDCamera:
            current_cam = self.camera_names[int(camera)]
            tfArray: typing.List[PMDTimeFrame] = []
            for _, row in self.data.iterrows():
                # Remove duplicated timestamps
                if len(tfArray) > 0:
                    if row[f"PmsdSlot_{current_cam}_timestamp"] == tfArray[-1].timestamp:
                        continue

                slot_array = []
                for i in range(int(row[f"PmsdSlot_{current_cam}_numberOfSlots"])):
                    corners = []
                    for k in range(4):
                        p = PMDSlotPoint(
                            float(row[(f"PmsdSlot_{current_cam}_P{k}_x", i)]),
                            float(row[(f"PmsdSlot_{current_cam}_P{k}_y", i)]),
                        )
                        corners.append(p)

                    scenario_confidence = PMDSlotScenarioConfidences(
                        int(row[(f"PmsdSlot_{current_cam}_sc_angled", i)]),
                        int(row[(f"PmsdSlot_{current_cam}_sc_parallel", i)]),
                        int(row[(f"PmsdSlot_{current_cam}_sc_perpendicular", i)]),
                    )

                    slot = PMDSlot(
                        float(row[(f"PmsdSlot_{current_cam}_existenceProbability", i)]),
                        corners,
                        scenario_confidence,
                    )
                    slot_array.append(slot)
                tf = PMDTimeFrame(
                    row[f"PmsdSlot_{current_cam}_timestamp"], row[f"PmsdSlot_{current_cam}_numberOfSlots"], slot_array
                )
                tfArray.append(tf)
            out[camera] = tfArray
        return out
