#!/usr/bin/env python3
"""Defining vehicle coordinates helper testcases"""
import math
import typing

from pl_parking.PLP.CEM.constants import GroundTruthCem
from pl_parking.PLP.CEM.ground_truth.kml_parser import CemGroundTruth
from pl_parking.PLP.CEM.ground_truth.utm_helper import UtmHelper
from pl_parking.PLP.CEM.inputs.input_CemPclReader import PCLDelimiter, PCLPoint
from pl_parking.PLP.CEM.inputs.input_CemSlotReader import Slot, SlotPoint
from pl_parking.PLP.CEM.inputs.input_DGPSReader import DgpsTimeframe


class VehicleCoordinateHelper:
    """Provides helper functions for vehicle coordinates."""

    @staticmethod
    def is_point_relevent(x_vehicle: float, y_vehicle: float):
        """Check if a point is relevant based on its distance from the vehicle.

        Args:
            x_vehicle (float): The x-coordinate of the point in vehicle coordinates.
            y_vehicle (float): The y-coordinate of the point in vehicle coordinates.

        Returns:
            bool: True if the point is relevant, False otherwise.
        """
        distance = math.sqrt(x_vehicle * x_vehicle + y_vehicle * y_vehicle)
        if distance < GroundTruthCem.relevent_distance:
            return True
        else:
            return False

    @staticmethod
    def pcl_utm_to_vehicle(
        pcl_ground_truth_utm: typing.List[PCLDelimiter], dgps: DgpsTimeframe
    ) -> typing.List[PCLDelimiter]:
        """Convert PCL ground truth points from UTM to vehicle coordinates.

        Args:
            pcl_ground_truth_utm (typing.List[PCLDelimiter]): List of PCL ground truth points in UTM coordinates.
            dgps (DgpsTimeframe): DGPS data for vehicle position.

        Returns:
            typing.List[PCLDelimiter]: List of PCL ground truth points in vehicle coordinates.
        """
        out: typing.List[PCLDelimiter] = []

        for parking_marker in pcl_ground_truth_utm:
            start_point_vehicle = UtmHelper.world_to_vehicle_coord(
                parking_marker.start_point.x,
                parking_marker.start_point.y,
                dgps.utm_x,
                dgps.utm_y,
                dgps.heading_from_north_rad,
            )
            end_point_vehicle = UtmHelper.world_to_vehicle_coord(
                parking_marker.end_point.x,
                parking_marker.end_point.y,
                dgps.utm_x,
                dgps.utm_y,
                dgps.heading_from_north_rad,
            )

            ok1 = VehicleCoordinateHelper.is_point_relevent(start_point_vehicle[0], start_point_vehicle[1])
            ok2 = VehicleCoordinateHelper.is_point_relevent(end_point_vehicle[0], end_point_vehicle[1])

            if ok1 or ok2:
                parking_marker_vehicle = PCLDelimiter(
                    parking_marker.delimiter_id,
                    parking_marker.delimiter_type,
                    PCLPoint(start_point_vehicle[0], start_point_vehicle[1]),
                    PCLPoint(end_point_vehicle[0], end_point_vehicle[1]),
                    parking_marker.confidence_percent,
                )

                out.append(parking_marker_vehicle)

        return out

    @staticmethod
    def slot_utm_to_vehicle(slot_ground_truth_utm: typing.List[Slot], dgps: DgpsTimeframe) -> typing.List[Slot]:
        """Converts slot ground truth points from UTM to vehicle coordinates."""
        out: typing.List[Slot] = []

        for slot in slot_ground_truth_utm:
            ok = False
            vertices_vehicle: typing.List[SlotPoint] = []

            for vertex in slot.slot_corners:
                vertex_vehicle = UtmHelper.world_to_vehicle_coord(
                    vertex.x, vertex.y, dgps.utm_x, dgps.utm_y, dgps.heading_from_north_rad
                )

                ok |= VehicleCoordinateHelper.is_point_relevent(vertex_vehicle[0], vertex_vehicle[1])
                vertices_vehicle.append(SlotPoint(vertex_vehicle[0], vertex_vehicle[1]))

            if ok:
                slot_vehicle = Slot(
                    slot.slot_id, slot.existence_probability, vertices_vehicle, slot.scenario_confidence
                )
                out.append(slot_vehicle)

        return out

    def cem_ground_truth_utm_to_vehicle(cem_ground_truth: CemGroundTruth, dgps: DgpsTimeframe) -> CemGroundTruth:
        """Converts CEM ground truth points from UTM to vehicle coordinates."""
        return CemGroundTruth(
            parking_markers=VehicleCoordinateHelper.pcl_utm_to_vehicle(cem_ground_truth.parking_markers, dgps),
            wheelstoppers=VehicleCoordinateHelper.pcl_utm_to_vehicle(cem_ground_truth.wheelstoppers, dgps),
            parking_slots=VehicleCoordinateHelper.slot_utm_to_vehicle(cem_ground_truth.parking_slots, dgps),
        )
