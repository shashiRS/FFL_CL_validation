#!/usr/bin/env python3
"""Defining kml parser methods"""
import typing
from dataclasses import dataclass

import geopandas as gpd
from fiona.drvsupport import supported_drivers

from pl_parking.PLP.CEM.constants import ConstantsCemInput
from pl_parking.PLP.CEM.ground_truth.utm_helper import UtmHelper
from pl_parking.PLP.CEM.inputs.input_CemPclReader import PCLDelimiter, PCLPoint
from pl_parking.PLP.CEM.inputs.input_CemSlotReader import Slot, SlotPoint, SlotScenarioConfidences


@dataclass
class CemGroundTruth:
    """Data class representing CEM ground truth."""

    parking_markers: typing.List[PCLDelimiter]
    wheelstoppers: typing.List[PCLDelimiter]
    parking_slots: typing.List[Slot]
    # TODO: add other types


class CemGroundTruthHelper:
    """Helper class for CEM ground truth."""

    @staticmethod
    def get_df_from_kml(gt_file_path: str) -> gpd.GeoDataFrame:
        """Get a GeoDataFrame from a KML file."""
        supported_drivers["KML"] = "rw"
        df = gpd.read_file(gt_file_path, driver="KML")

        return df

    @staticmethod
    def get_parking_markers(df: gpd.GeoDataFrame) -> typing.List[PCLDelimiter]:
        """Get parking markers from a GeoDataFrame."""
        rows = [row for _, row in df.iterrows() if row.Description.split(", ")[0] == "parking_marker"]

        ret: typing.List[PCLDelimiter] = []

        for row in rows:
            x, y = row.geometry.xy  # x: long, y: lat

            start_point = (x[0], y[0])
            end_point = (x[1], y[1])

            start_point_utm = UtmHelper.get_utm_from_lat_lon(start_point[1], start_point[0])
            end_point_utm = UtmHelper.get_utm_from_lat_lon(end_point[1], end_point[0])

            pcl_gt = PCLDelimiter(
                None,
                ConstantsCemInput.PCLEnum,
                PCLPoint(start_point_utm[0], start_point_utm[1]),
                PCLPoint(end_point_utm[0], end_point_utm[1]),
                100.0,
            )

            ret.append(pcl_gt)

        return ret

    @staticmethod
    def get_slot_scenario_confidences(scenario_type: str) -> SlotScenarioConfidences:
        """Get scenario confidences for a slot."""
        angled = 0
        parallel = 0
        perpendicular = 0

        if scenario_type == "angled":
            angled = 100
        if scenario_type == "parallel":
            parallel = 100
        if scenario_type == "perpendicular":
            perpendicular = 100

        return SlotScenarioConfidences(angled, parallel, perpendicular)

    @staticmethod
    def get_parking_slots(df: gpd.GeoDataFrame) -> typing.List[Slot]:
        """Get parking slots from a GeoDataFrame."""
        rows = [row for _, row in df.iterrows() if row.Description.split(", ")[0] == "parking_slot"]

        ret: typing.List[Slot] = []

        for row in rows:
            x, y = row.geometry.exterior.xy
            description = row.Description.split(", ")

            scenario_type = description[1]
            scenario_confidences: SlotScenarioConfidences = CemGroundTruthHelper.get_slot_scenario_confidences(
                scenario_type
            )

            vertices_utm: typing.List[typing.Tuple[float, float]] = [
                UtmHelper.get_utm_from_lat_lon(y[i], x[i]) for i in range(4)
            ]
            slot_points: typing.List[SlotPoint] = [SlotPoint(pnt[0], pnt[1]) for pnt in vertices_utm]

            ret.append(Slot(None, 1.0, slot_points, scenario_confidences))

        return ret

    @staticmethod
    def get_cem_ground_truth(file_path: str) -> CemGroundTruth:
        """Get CEM ground truth from a file."""
        df = CemGroundTruthHelper.get_df_from_kml(file_path)

        parking_markers = CemGroundTruthHelper.get_parking_markers(df)
        wheelstoppers = []
        parking_slots = CemGroundTruthHelper.get_parking_slots(df)

        return CemGroundTruth(parking_markers=parking_markers, wheelstoppers=wheelstoppers, parking_slots=parking_slots)

    @staticmethod
    def get_cem_ground_truth_from_files_list(files: typing.List[str]) -> CemGroundTruth:
        """Get CEM ground truth from a list of files."""
        parking_markers = []
        wheelstoppers = []
        parking_slots = []

        for file_path in files:
            df = CemGroundTruthHelper.get_df_from_kml(file_path)

            parking_markers += CemGroundTruthHelper.get_parking_markers(df)
            wheelstoppers += []
            parking_slots += CemGroundTruthHelper.get_parking_slots(df)

        return CemGroundTruth(parking_markers, wheelstoppers, parking_slots)
