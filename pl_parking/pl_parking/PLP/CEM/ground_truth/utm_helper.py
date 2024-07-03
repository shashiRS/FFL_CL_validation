#!/usr/bin/env python3
"""Defining utm helper testcases"""
import math
import typing

from pyproj import Proj


class UtmHelper:
    """Utility class for handling UTM coordinates."""

    def get_utm_zone_from_lon(longitude):
        """
        Function to get UTM zone from latitude and longitude coordinates
        :param longitude: (scalar or array (numpy or python)) – Input latitude coordinate(s)
        :return zone: UTM zone of each town center from the longitude, starting at zone 1 from -180°E to -174°E
        """
        # Src: https://stackoverflow.com/questions/9186496/determining-utm-zone-to-convert-from-longitude-latitude
        # For more details read https://en.wikipedia.org/wiki/Universal_Transverse_Mercator_coordinate_system#UTM_zone
        return (math.floor((longitude + 180) / 6) % 60) + 1

    def get_utm_from_lat_lon(latitude: float, longitude: float) -> typing.Tuple[float, float]:
        """
        Function to get x y coordinate from latitude and longitude coordinates
        :param latitude: (pandas.Series or a float) – Input longitude coordinate(s) in degrees
        :param longitude: (pandas.Series or a float) – Input latitude coordinate(s) in degrees
        :return XX, YY: x and y in the desired coordinate system
        """
        # get UTM zone using longitude value
        if isinstance(longitude, float):
            zone = UtmHelper.get_utm_zone_from_lon(longitude)
        else:
            zone = UtmHelper.get_utm_zone_from_lon(longitude.iloc[0])

        # LatLon with WGS84 datum used by GPS units and Google Earth
        # ellps is Ellipsoids supported by pyproj.PROJ
        p = Proj(proj="utm", zone=zone, ellps="WGS84")
        xx, yy = p(longitude, latitude)
        return xx, yy

    @staticmethod
    def deg_to_rad(angle_degree):
        """Converts angle from degrees to radians."""
        return angle_degree * math.pi / 180

    @staticmethod
    def get_relative_rotation_from_east(north_angle_degree):
        """
        Determine relative rotation (i.e. new orientation in degrees counter-clockwise from E)
        Currently the vehicle local coordinate need to consider the orientation from the east in counter-clockwise
        :param north_angle_degree: angle from north in degree
        :return: relative rotation in degrees counter-clockwise from East
        """
        return UtmHelper.deg_to_rad(90 - north_angle_degree)

    @staticmethod
    def world_to_vehicle_coord(utm_point_x, utm_point_y, utm_ego_pose_x, utm_ego_pose_y, heading_from_north_rad):
        """
        :param utm_point_x: x location (in utm coordinate)
        :param utm_point_y: y location (in utm coordinate)
        :param utm_ego_pose_x: x vehicle location (in utm coordinate)
        :param utm_ego_pose_y: y vehicle location (in utm coordinate)
        :param heading_from_north_rad: vehicle orientation from north axis in radian (clockwise)
        :return: vehicle_coord_point_x and vehicle_coord_point_y that are ground truth points in vehicle coordinates
        """
        rotated_vehicle_coord_x = utm_point_x - utm_ego_pose_x
        rotated_vehicle_coord_y = utm_point_y - utm_ego_pose_y

        cos_heading_from_north = math.cos(heading_from_north_rad)
        sin_heading_from_north = math.sin(heading_from_north_rad)

        vehicle_coord_point_x = (
            cos_heading_from_north * rotated_vehicle_coord_x + sin_heading_from_north * rotated_vehicle_coord_y
        )
        vehicle_coord_point_y = (
            -sin_heading_from_north * rotated_vehicle_coord_x + cos_heading_from_north * rotated_vehicle_coord_y
        )

        return vehicle_coord_point_x, vehicle_coord_point_y
