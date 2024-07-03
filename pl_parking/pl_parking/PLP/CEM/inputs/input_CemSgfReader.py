#!/usr/bin/env python3
"""Defining input CemSgfReader testcases"""
import typing
from dataclasses import dataclass


@dataclass
class StaticObject:
    """Static object with various attributes."""

    object_id: int
    element_classification: int
    element_semantic: int
    num_vertices: int
    vertex_start_index: int
    wheel_traversable_confidence: int
    body_traversable_confidence: int
    high_confidence: int
    hanging_confidence: int


@dataclass
class ObjectTimeFrame:
    """Represents a time frame containing objects."""

    timestamp: int
    num_objects: int
    static_objects: typing.List[StaticObject]


class SGFReader:
    """Reader class for SGF files."""

    def __init__(self, reader):
        """Initialize object attributes."""
        self.data = reader.as_plain_df
        self._synthetic_flag = self.__is_synthetic()
        self.number_of_objects = self.__get_number_of_objects()
        self.max_num_polygons = self.__get_max_num_polygons()

    def __is_synthetic(self):
        """Check if the data contains synthetic signals."""
        if "synthetic_signal" in self.data.columns.tolist():
            return True
        else:
            return False

    def __get_number_of_objects(self):
        """Get the number of objects in the time frame."""
        return len(self.data.filter(regex="numVertices_polygon").columns)

    def __get_max_num_polygons(self):
        """Get the maximum number of polygons in the time frame."""
        return int(self.data.numPolygons.max())
