#!/usr/bin/env python3
"""Defining input CemErgReader testcases"""
import typing
from dataclasses import dataclass
from enum import Enum

import pandas as pd


class ObjectClass(Enum):
    """Enumeration representing different types of objects."""

    UNKNOWN: int = 0
    CAR: int = 1
    PEDESTRIAN: int = 2
    MOTORCYCLE: int = 3
    BICYCLE: int = 4


@dataclass
class DynPoint:
    """Represents a dynamic point with coordinates and variance."""

    x: float
    y: float
    var_x: float
    var_y: float


@dataclass
class DynamicObjectDetection:
    """Represents a detected dynamic object."""

    object_id: int
    class_type: ObjectClass
    confidence: float  # [0..1]
    center_x: float
    center_y: float
    polygon: typing.List[DynPoint]  # For cylinder object, it's just sampled circle


@dataclass
class CylinderDynamicObjectDetection(DynamicObjectDetection):
    """Represents a detected cylinder-shaped dynamic object."""

    radius: float


@dataclass
class CuboidDynamicObjectDetection(DynamicObjectDetection):
    """Represents a detected cuboid-shaped dynamic object."""

    length: float
    width: float


class ErgDoReader:
    """Reads and processes DO data from an ERG file."""

    def __init__(self, reader):
        """Initialize object attributes."""
        self.number_of_do = self.__get_number_of_objects(reader)
        self.__read_all_to_pandas(reader)

    @staticmethod
    def data_mapping():
        """Defines the mapping of data fields."""
        return {
            "DynamicObjects": {
                "id": "refObjID_nu",
                "confidence": "classConfidence_perc",
                "ExistenceProb": "existenceProb_perc",
                "classType": "objClass_nu",
                "pnt0_x": "objShape_m.array._0_.x_dir",
                "pnt1_x": "objShape_m.array._1_.x_dir",
                "pnt2_x": "objShape_m.array._2_.x_dir",
                "pnt3_x": "objShape_m.array._3_.x_dir",
                "pnt0_y": "objShape_m.array._0_.y_dir",
                "pnt1_y": "objShape_m.array._1_.y_dir",
                "pnt2_y": "objShape_m.array._2_.y_dir",
                "pnt3_y": "objShape_m.array._3_.y_dir",
            }
        }

    def __get_number_of_objects(self, reader) -> int:
        """Get the number of objects from the data reader.

        Args:
            reader: The data reader object.

        Returns:
            int: The number of objects.
        """
        data_map = self.data_mapping()

        i = 0
        while True:
            signal_name = (data_map["DynamicObjects"]["id"], i)
            if signal_name not in reader:
                number_of_objects = i
                break
            i += 1
        return number_of_objects

    def __read_all_to_pandas(self, reader) -> pd.DataFrame:
        """Reads all data from the reader and converts it to a pandas DataFrame."""
        data_map = self.data_mapping()

        self.data = pd.DataFrame()
        columns_rename = {}

        for new_name, signal_name in data_map["DynamicObjects"].items():
            for i in range(self.number_of_do):
                columns_rename[(signal_name, i)] = "{}[{}].{}".format("DynamicObjects", i, new_name)

        data = reader.as_plain_df[list(columns_rename.keys())]
        new_data = data.rename(columns=columns_rename)

        self.data = new_data.mode(numeric_only=False)
        return

    def convert_to_class(self) -> typing.List[typing.List[DynPoint]]:
        """Converts data to a list of lists of DynPoint objects."""
        polygons = []
        for _, row in self.data.iterrows():
            dynamic_objects = []
            for i in range(self.number_of_do):
                polygon = [
                    DynPoint(row[f"objects[{i}].pnt0_x"], row[f"objects[{i}].pnt0_y"], 0, 0),
                    DynPoint(row[f"objects[{i}].pnt1_x"], row[f"objects[{i}].pnt1_y"], 0, 0),
                    DynPoint(row[f"objects[{i}].pnt2_x"], row[f"objects[{i}].pnt2_y"], 0, 0),
                    DynPoint(row[f"objects[{i}].pnt3_x"], row[f"objects[{i}].pnt3_y"], 0, 0),
                ]

                dynamic_objects.append(polygon)

            polygons.append(dynamic_objects)
        return polygons


class ErgSoReader:
    """Reads and processes SO data from an ERG file."""

    def __init__(self, reader):
        """Initialize object attributes."""
        self.number_of_so = self.__get_number_of_objects(reader)
        self.__read_all_to_pandas(reader)

    @staticmethod
    def data_mapping():
        """Defines the mapping of data fields."""
        return {
            "DynamicObjects": {
                "ObjectRefID": "refObjID_nu",
                "HeightClass": "objHeightClass_nu",
                "ExistenceProb": "existenceProb_perc",
                "_0_.x_dir": "objShape_m.array._0_.x_dir",
                "_1_.x_dir": "objShape_m.array._1_.x_dir",
                "_2_.x_dir": "objShape_m.array._2_.x_dir",
                "_3_.x_dir": "objShape_m.array._3_.x_dir",
                "_4_.x_dir": "objShape_m.array._4_.x_dir",
                "_5_.x_dir": "objShape_m.array._5_.x_dir",
                "_6_.x_dir": "objShape_m.array._6_.x_dir",
                "_7_.x_dir": "objShape_m.array._7_.x_dir",
                "_8_.x_dir": "objShape_m.array._8_.x_dir",
                "_9_.x_dir": "objShape_m.array._9_.x_dir",
                "_10_.x_dir": "objShape_m.array._10_.x_dir",
                "_11_.x_dir": "objShape_m.array._11_.x_dir",
                "_12_.x_dir": "objShape_m.array._12_.x_dir",
                "_13_.x_dir": "objShape_m.array._13_.x_dir",
                "_14_.x_dir": "objShape_m.array._14_.x_dir",
                "_15_.x_dir": "objShape_m.array._15_.x_dir",
                "_0_.y_dir": "objShape_m.array._0_.y_dir",
                "_1_.y_dir": "objShape_m.array._1_.y_dir",
                "_2_.y_dir": "objShape_m.array._2_.y_dir",
                "_3_.y_dir": "objShape_m.array._3_.y_dir",
                "_4_.y_dir": "objShape_m.array._4_.y_dir",
                "_5_.y_dir": "objShape_m.array._5_.y_dir",
                "_6_.y_dir": "objShape_m.array._6_.y_dir",
                "_7_.y_dir": "objShape_m.array._7_.y_dir",
                "_8_.y_dir": "objShape_m.array._8_.y_dir",
                "_9_.y_dir": "objShape_m.array._9_.y_dir",
                "_10_.y_dir": "objShape_m.array._10_.y_dir",
                "_11_.y_dir": "objShape_m.array._11_.y_dir",
                "_12_.y_dir": "objShape_m.array._12_.y_dir",
                "_13_.y_dir": "objShape_m.array._13_.y_dir",
                "_14_.y_dir": "objShape_m.array._14_.y_dir",
                "_15_.y_dir": "objShape_m.array._15_.y_dir",
            }
        }

    def __get_number_of_objects(self, reader) -> int:
        """Get the number of objects from the data reader.

        Args:
            reader: The data reader object.

        Returns:
            int: The number of objects.
        """
        data_map = self.data_mapping()

        i = 0
        while True:
            signal_name = (data_map["DynamicObjects"]["ObjectRefID"], i)
            if signal_name not in reader:
                number_of_objects = i
                break
            i += 1
        return number_of_objects

    def __read_all_to_pandas(self, reader) -> pd.DataFrame:
        """Reads all data from the reader and converts it to a pandas DataFrame."""
        data_map = self.data_mapping()

        self.data = pd.DataFrame()
        columns_rename = {}

        for new_name, signal_name in data_map["DynamicObjects"].items():
            for i in range(self.number_of_so):
                columns_rename[(signal_name, i)] = "{}[{}].{}".format("DynamicObjects", i, new_name)

        data = reader.as_plain_df[list(columns_rename.keys())]
        new_data = data.rename(columns=columns_rename)

        self.data = new_data.mode(numeric_only=False)
        return


@dataclass
class PMDLinePoint:
    """Represents a point in a PMD line."""

    x: float
    y: float


@dataclass
class PMDLine:
    """Represents a PMD line."""

    id: int
    delimiter_type: int
    line_width: float
    line_start: PMDLinePoint
    line_end: PMDLinePoint
    line_probability: float


class ErgPmReader:
    """Reads and processes PM data from an ERG file."""

    def __init__(self, reader):
        """Initialize object attributes."""
        self.number_of_pm = self.__get_number_of_objects(reader)
        self.__read_all_to_pandas(reader)

    @staticmethod
    def data_mapping():
        """Defines the mapping of data fields."""
        return {
            "Parking_lines": {
                "Pos_size_m": "pos_m.actualSize",
                "ExistenceProb": "existenceProb_perc",
                "Width_m": "width_m",
                "lineStartX": "pos_m.array._0_.x_dir",
                "lineEndX": "pos_m.array._1_.x_dir",
                "lineStartY": "pos_m.array._0_.y_dir",
                "lineEndY": "pos_m.array._1_.y_dir",
            }
        }

    def __get_number_of_objects(self, reader) -> int:
        """Get the number of objects from the data reader.

        Args:
            reader: The data reader object.

        Returns:
            int: The number of objects.
        """
        data_map = self.data_mapping()

        i = 0
        while True:
            signal_name = (data_map["Parking_lines"]["ExistenceProb"], i)
            if signal_name not in reader:
                number_of_objects = i
                break
            i += 1
        return number_of_objects

    def __read_all_to_pandas(self, reader) -> pd.DataFrame:
        """Reads all data from the reader and converts it to a pandas DataFrame."""
        data_map = self.data_mapping()

        self.data = pd.DataFrame()
        columns_rename = {}

        for new_name, signal_name in data_map["Parking_lines"].items():
            for i in range(self.number_of_pm):
                columns_rename[(signal_name, i)] = "{}[{}].{}".format("Parking_lines", i, new_name)

        data = reader.as_plain_df[list(columns_rename.keys())]
        new_data = data.rename(columns=columns_rename)

        self.data = new_data.mode(numeric_only=False)
        return

    def convert_to_class(self) -> typing.List[PMDLine]:
        """Converts data to a list of lists of DynPoint objects."""
        parking_lines: typing.List[PMDLine] = []
        try:
            for _, row in self.data.iterrows():
                lines = []
                for i in range(self.number_of_pm):
                    x0, y0 = row[f"Parking_lines[{i}].lineStartX"], row[f"Parking_lines[{i}].lineStartY"]
                    x1, y1 = row[f"Parking_lines[{i}].lineEndX"], row[f"Parking_lines[{i}].lineEndY"]
                    line = PMDLine(
                        i,
                        None,
                        row[f"Parking_lines[{i}].Width_m"],
                        PMDLinePoint(x0, y0),
                        PMDLinePoint(x1, y1),
                        row[f"Parking_lines[{i}].ExistenceProb"],
                    )

                    if any(val != 0 for val in [x0, y0, x1, y1]):
                        lines.append(line)
                parking_lines.append(lines)

        except NameError:
            print("Conflicts to convert reader data to class", "error")

        return parking_lines


@dataclass
class PSDSlotPoint:
    """Represents a point in a PSD slot."""

    x: float
    y: float


@dataclass
class PSDSlotScenarioConfidences:
    """Represents the scenario confidences for a PSD slot."""

    angled: int
    parallel: int
    perpendicular: int


@dataclass
class PSDSlot:
    """Represents a PSD slot."""

    existence_probability: float
    slot_corners: typing.List[PSDSlotPoint]
    scenario_confidence: PSDSlotScenarioConfidences


class ErgPsReader:
    """Reads and processes PS data from an ERG file."""

    def __init__(self, reader):
        """Initialize object attributes."""
        self.number_of_ps = self.__get_number_of_objects(reader)
        self.__read_all_to_pandas(reader)

    @staticmethod
    def data_mapping():
        """Defines the mapping of data fields."""
        return {
            "Parking_slots": {
                "CameraId": "cameraId",
                "slotId": "slotId",
                "sc_angled": "parking_scenario_confidence.angled",
                "sc_parallel": "parking_scenario_confidence.parallel",
                "sc_perpendicular": "parking_scenario_confidence.perpendicular",
                "existenceProbability": "existenceProb_perc",
                "P0_x": "slot_corners._0_.x",
                "P1_x": "slot_corners._1_.x",
                "P2_x": "slot_corners._2_.x",
                "P3_x": "slot_corners._3_.x",
                "P0_y": "slot_corners._0_.y",
                "P1_y": "slot_corners._1_.y",
                "P2_y": "slot_corners._2_.y",
                "P3_y": "slot_corners._3_.y",
            }
        }

    def __get_number_of_objects(self, reader) -> int:
        """Get the number of objects from the data reader.

        Args:
            reader: The data reader object.

        Returns:
            int: The number of objects.
        """
        data_map = self.data_mapping()

        i = 0
        while True:
            signal_name = (data_map["Parking_slots"]["slotId"], i)
            if signal_name not in reader:
                number_of_objects = i
                break
            i += 1
        return number_of_objects

    def __read_all_to_pandas(self, reader) -> pd.DataFrame:
        """Reads all data from the reader and converts it to a pandas DataFrame."""
        data_map = self.data_mapping()

        self.data = pd.DataFrame()
        columns_rename = {}

        for new_name, signal_name in data_map["Parking_slots"].items():
            for i in range(self.number_of_ps):
                columns_rename[(signal_name, i)] = "{}[{}].{}".format("Parking_slots", i, new_name)

        data = reader.as_plain_df[list(columns_rename.keys())]
        new_data = data.rename(columns=columns_rename)

        self.data = new_data.mode(numeric_only=False)
        return

    def convert_to_class(self) -> typing.List[typing.List[PSDSlot]]:
        """Converts data to a list of lists of DynPoint objects."""
        slots_array = []
        try:
            for _, row in self.data.as_plain_df.iterrows():
                slot_array = []
                for i in range(self.number_of_ps):
                    corners = []
                    valid_corner = []
                    for k in range(4):
                        x, y = float(row[f"P{k}_x_{i}"]), float(row[f"P{k}_y_{i}"])
                        p = PSDSlotPoint(x, y)
                        corners.append(p)
                        valid_corner.append(True if x or y != 0 else False)

                    if any(valid_corner):
                        scenario_confidence = PSDSlotScenarioConfidences(
                            int(row["sc_angled", i]), int(row["sc_parallel", i]), int(row["sc_perpendicular", i])
                        )

                        slot = PSDSlot(float(row["existenceProbability", i]), corners, scenario_confidence)

                        slot_array.append(slot)
                slots_array.append(slot_array)

        except NameError:
            print("Conflicts to convert reader data to class", "error")

        return slots_array
