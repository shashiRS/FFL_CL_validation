#!/usr/bin/env python3
"""Defining input PmsdSlotReader testcases"""
import typing
from dataclasses import dataclass


@dataclass
class SlotPoint:
    """Represents a point in the coordinate system."""

    x: float
    y: float

    def __sub__(self, other):
        return SlotPoint(self.x - other.x, self.y - other.y)


@dataclass
class SlotScenarioConfidences:
    """Represents confidence levels for different slot scenarios."""

    angled: int
    parallel: int
    perpendicular: int


@dataclass
class Slot:
    """Represents a parking slot."""

    slot_timestamp: int
    existence_probability: float
    slot_corners: typing.List[SlotPoint]
    scenario_confidence: SlotScenarioConfidences


@dataclass
class SlotTimeFrame:
    """Represents a time frame containing parking slots."""

    timestamp: int
    number_of_slots: int
    parking_slots: typing.List[Slot]


class SlotReader:
    """Reader class for slots."""

    def __init__(self, reader):
        """Initialize object attributes."""
        self.data = reader
        self.synthetic_flag = self.__is_synthetic()
        self.number_of_delimiters = len(self.data.filter(regex="CemSlot_timestamp").columns)

    def __is_synthetic(self):
        """Check if the data contains synthetic signals."""
        if "synthetic_signal" in self.data.columns:
            return True
        else:
            return False

    def convert_to_class(self) -> typing.List[SlotTimeFrame]:
        """
        Converts data to SlotTimeFrame instances.

        Returns:
            typing.List[SlotTimeFrame]: List of SlotTimeFrame instances.
        """
        out = []
        for _, row in self.data.iterrows():
            slot_array: typing.List[SlotTimeFrame] = []
            if len(slot_array) > 0:
                if slot_array[-1].timestamp == row["CemSlot_timestamp"]:
                    continue

            for i in range(int(row["CemSlot_numberOfSlots"])):
                if row[("CemSlot_existenceProbability", i)] != 0:
                    corners = []
                    for k in range(4):
                        p = SlotPoint(float(row[(f"CemSlot_P{k}_x", i)]), float(row[(f"CemSlot_P{k}_y", i)]))
                        corners.append(p)

                    scenario_confidence = SlotScenarioConfidences(
                        int(row[("CemSlot_sc_angled", i)]),
                        int(row[("CemSlot_sc_parallel", i)]),
                        int(row[("CemSlot_sc_perpendicular", i)]),
                    )

                    slot = Slot(
                        0,
                        float(row[("CemSlot_existenceProbability", i)]),
                        corners,
                        scenario_confidence,
                    )

                    slot_array.append(slot)

            tf = SlotTimeFrame(row["CemSlot_timestamp"], row["CemSlot_numberOfSlots"], slot_array)
            out.append(tf)
        return out
