"""
usemSiSlotShrinkageHelper.py

Contains classes helping in implementation of KPIs regarding parking slots shrinkage
"""

from dataclasses import dataclass
from typing import Dict, List, Union

import matplotlib.path as MplPath
import numpy as np
import pandas as pd

import pl_parking.PLP.MF.constants as fc


class ThresholdHelper:
    """The threshold used for point detection (if higher than threshold -> the point is not take into account)"""

    THRESHOLD_DISTANCE_M = 1.001


class LocalConstantsHelper:
    """Constant values used for coordinates functions"""

    STEP_X_COORD = 2


@dataclass
class EgoInfo:
    """Class used for easy handling of ego info"""

    ego_x: float
    ego_y: float
    ego_yaw: float


class LeadLagPointsHelper:
    """
    Class providing functions which help in obtaining park slot coordinates and
    calculating the shrinkage of the parking slot
    """

    def __init__(self) -> None:
        """Initialization method of the class"""
        self.nearest_point_left: float = None
        self.nearest_point_right: float = None

    @staticmethod
    def obtain_static_obj_valid(
        signals: pd.DataFrame, static_obj_shape_dict: Dict[str, list], idx: int, sg_nb_val_static_obj
    ) -> str:
        """Function to obtain valid static objects"""
        nb_valid_static_obj = signals[sg_nb_val_static_obj]
        static_obj_valid = list(static_obj_shape_dict)[: nb_valid_static_obj[idx]]

        return static_obj_valid

    @staticmethod
    def store_vector_signals(df, name_signal: str, nb_elem_signal: int):
        """Method to obtain the signals stored in a vector:
        Ex: M7board.EM_Thread.ApEnvModelPort.staticObjects[0].objShape_m -> multiple static objects
            (M7board.EM_Thread.ApEnvModelPort.staticObjects[0].objShape_m, 0) -> each static object
            contains multiple points

            :param signals: instance of SignalDataFrame class with the desired signals read from the bsig file
            :parm name_signal: signal name created in EntryParkingSignals class
            :parm nb_elem_signal: number of elements stored in a signal
            (ex: M7board.EM_Thread.ApEnvModelPort.staticObjects[0].objShape_m
                                                            -> contains an array with 20 signals)
            :return vector_signals_dict: dictionary with -> keys = name of the column for a certain signal
                                                           -> values = list with all values of the signal
        """
        vector_signals_dict = {}

        if nb_elem_signal > 0:
            for key in df.columns:
                if name_signal in key:
                    vector_signals_dict[key] = []
                    for i in range(nb_elem_signal):
                        vector_signals_dict[key].append(df[key].str[i])
        else:
            # TODO
            # Not verified, will be used for other tests
            for key in df.columns:
                if key == name_signal:
                    vector_signals_dict[key] = []
                    vector_signals_dict[key].append(df[key])

        return vector_signals_dict

    @staticmethod
    def generate_ego_info(signals: pd.DataFrame, idx: int, sg_ego) -> EgoInfo:
        """Method to generate ego info"""
        ego_info = EgoInfo(
            signals[sg_ego][idx][fc.EgoPoseApConstants.X_COORD],
            signals[sg_ego][idx][fc.EgoPoseApConstants.Y_COORD],
            signals[sg_ego][idx][fc.EgoPoseApConstants.YAW_ANGLE],
        )
        return ego_info

    @staticmethod
    def obtain_points_on_sides(
        static_obj_shape_dict: Dict[str, List[float]],
        static_obj_detected: List[str],
        coordinates_delimitation: Union[List[float], List[List[np.ndarray]]],
        idx_filter: int,
        ego_info: EgoInfo,
        parking_box_type: bool = True,
    ) -> List[List[np.ndarray]]:
        """Obtain the coordinates of the static object points that are on the left/right side of the parking box or
        of the left/right side of the DGPS boxes

        if parking_box_type == True coordinates_delimitation is slot_coordinates
        else if parking_box_type == False coordinates_delimitation is sides dgps boxes: -> points_side_left
                                                                                                -> TOP -> x,y
                                                                                                -> BOTTOM -> x,y
                                                                                        -> points_side_right
                                                                                                -> TOP -> x,y
                                                                                                -> BOTTOM -> x,y

        :return : a list with coordinates of the static objects point that are on the left/right side of the parking box
        """
        if parking_box_type:
            min_slot_x_left = max(
                coordinates_delimitation[fc.ParkingBoxConstants.X_COORD_LEFT_TOP],
                coordinates_delimitation[fc.ParkingBoxConstants.X_COORD_LEFT_BOTTOM],
            )
            min_slot_x_right = min(
                coordinates_delimitation[fc.ParkingBoxConstants.X_COORD_RIGHT_TOP],
                coordinates_delimitation[fc.ParkingBoxConstants.X_COORD_RIGHT_BOTTOM],
            )
            y_coord_left_top = coordinates_delimitation[fc.ParkingBoxConstants.Y_COORD_LEFT_TOP]
            y_coord_left_bottom = coordinates_delimitation[fc.ParkingBoxConstants.Y_COORD_LEFT_BOTTOM]
            y_coord_right_top = coordinates_delimitation[fc.ParkingBoxConstants.Y_COORD_RIGHT_TOP]
            y_coord_right_bottom = coordinates_delimitation[fc.ParkingBoxConstants.Y_COORD_RIGHT_BOTTOM]
        else:
            # TODO
            # to check where this will be needed

            min_slot_x_left = min(coordinates_delimitation[0][0][0], coordinates_delimitation[0][1][0])
            min_slot_x_right = min(coordinates_delimitation[1][0][0], coordinates_delimitation[1][1][0])
            y_coord_left_top = coordinates_delimitation[0][0][1]
            y_coord_left_bottom = coordinates_delimitation[0][1][1]
            y_coord_right_top = coordinates_delimitation[1][0][1]
            y_coord_right_bottom = coordinates_delimitation[1][1][1]

        points_on_left_side = []
        points_on_right_side = []
        for val in static_obj_detected:
            for i in range(0, len(static_obj_shape_dict[val]), LocalConstantsHelper.STEP_X_COORD):
                # The point of static object needs to be transformed in global coordinates from local
                # coordinates (ego ref system)
                [x_coord, y_coord] = transf_local_to_global(
                    static_obj_shape_dict[val][i][idx_filter],
                    static_obj_shape_dict[val][i + 1][idx_filter],
                    ego_info.ego_x,
                    ego_info.ego_y,
                    ego_info.ego_yaw,
                )
                if min_slot_x_left >= x_coord and abs(min_slot_x_left - x_coord) < ThresholdHelper.THRESHOLD_DISTANCE_M:
                    if y_coord <= y_coord_left_top and y_coord >= y_coord_left_bottom:
                        points_on_left_side.append(np.array([x_coord, y_coord]))
                if (
                    min_slot_x_right <= x_coord
                    and abs(min_slot_x_right - x_coord) < ThresholdHelper.THRESHOLD_DISTANCE_M
                ):
                    if y_coord <= y_coord_right_top and y_coord >= y_coord_right_bottom:
                        points_on_right_side.append(np.array([x_coord, y_coord]))

        return [points_on_left_side, points_on_right_side]

    def extract_nearest_points_to_slot_sides(
        self,
        points_on_left_side: List[np.ndarray],
        points_on_right_side: List[np.ndarray],
        slot_coordinates: List[float],
    ) -> None:
        """Extract the nearest points th the left/right side of the parking box"""
        points_left = [
            np.array(
                [
                    slot_coordinates[fc.ParkingBoxConstants.X_COORD_LEFT_TOP],
                    slot_coordinates[fc.ParkingBoxConstants.Y_COORD_LEFT_TOP],
                ]
            ),
            np.array(
                [
                    slot_coordinates[fc.ParkingBoxConstants.X_COORD_LEFT_BOTTOM],
                    slot_coordinates[fc.ParkingBoxConstants.Y_COORD_LEFT_BOTTOM],
                ]
            ),
        ]
        points_right = [
            np.array(
                [
                    slot_coordinates[fc.ParkingBoxConstants.X_COORD_RIGHT_TOP],
                    slot_coordinates[fc.ParkingBoxConstants.Y_COORD_RIGHT_TOP],
                ]
            ),
            np.array(
                [
                    slot_coordinates[fc.ParkingBoxConstants.X_COORD_RIGHT_BOTTOM],
                    slot_coordinates[fc.ParkingBoxConstants.Y_COORD_RIGHT_BOTTOM],
                ]
            ),
        ]

        if points_on_left_side:
            self.nearest_point_left = self.obtain_closest_point_on_sides_slot(
                points_on_left_side, points_left[0], points_left[1]
            )

        if points_on_right_side:
            self.nearest_point_right = self.obtain_closest_point_on_sides_slot(
                points_on_right_side, points_right[0], points_right[1]
            )

    def extract_nearest_points_to_dgps_boxes_sides(
        self,
        points_on_left_side: List[np.ndarray],
        points_on_right_side: List[np.ndarray],
        points_sides_dgps_boxes: List[List[np.ndarray]],
    ) -> None:
        """Extract the nearest points th the left/right side of the parking box

        parking_box_type == False coordinates_delimitation is sides dgps boxes: -> points_side_left  -> TOP -> x,y
                                                                                                     -> BOTTOM -> x,y
                                                                                -> points_side_right -> TOP -> x,y
                                                                                                     -> BOTTOM -> x,y
        """
        if points_on_left_side:
            self.nearest_point_left = self.obtain_closest_point_on_sides_slot(
                points_on_left_side, points_sides_dgps_boxes[0][0], points_sides_dgps_boxes[0][1]
            )

        if points_on_right_side:
            self.nearest_point_right = self.obtain_closest_point_on_sides_slot(
                points_on_right_side, points_sides_dgps_boxes[1][0], points_sides_dgps_boxes[1][1]
            )

    def obtain_closest_point_on_sides_slot(
        self, points: List[np.ndarray], p1: np.ndarray, p2: np.ndarray
    ) -> np.ndarray:
        """Obtain the closest point to a side of the parkig box"""
        nearest_point = points[0]
        distance_first = abs(self.calc_dist_point_to_line(p1, p2, points[0]))
        for _, point in list(enumerate(points, start=1))[1:]:
            distance = abs(self.calc_dist_point_to_line(p1, p2, point))
            if distance < distance_first:
                nearest_point = point
                distance_first = distance

        return nearest_point

    @staticmethod
    def calc_dist_point_to_line(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
        """Calculate the length of a line which is starting to a point and is perpendicular to other line

        :param p1: first point of the line
        :param p2: second point of the line
        :param p3: point from where the perpendicular line is starting

        """
        # Supress RuntimeWarning: invalid value encountered in true_divide
        np.seterr(invalid="ignore")

        distance = np.cross(p2 - p1, p3 - p1) / np.linalg.norm(p2 - p1)

        return distance

    @staticmethod
    def calc_lead_lag_shrink(
        points_left: List[np.ndarray],
        points_right: List[np.ndarray],
        nearest_point_left: float,
        nearest_point_right: float,
    ) -> List[float]:
        """Compute the lead and lag"""
        lag_cm = fc.DgpsConstants.INVALID_VALUE_SLOT_SHRINKAGE
        lead_cm = fc.DgpsConstants.INVALID_VALUE_SLOT_SHRINKAGE
        if nearest_point_left is not None:
            lag_cm = (
                LeadLagPointsHelper.calc_dist_point_to_line(points_left[0], points_left[1], nearest_point_left)
                * fc.GeneralConstants.M_TO_CM
                * (-1)
            )

        if nearest_point_right is not None:
            lead_cm = (
                LeadLagPointsHelper.calc_dist_point_to_line(points_right[0], points_right[1], nearest_point_right)
                * fc.GeneralConstants.M_TO_CM
            )

        return [lead_cm, lag_cm]

    @staticmethod
    def obtain_nearest_object_to_side(
        static_obj_shape_dict: Dict[str, List[float]],
        static_obj_detected: List[str],
        side: List[np.array],
        idx_filter: int,
        ego_info: EgoInfo,
    ) -> str:
        """Obtain the nearest object to a side of the parking box"""
        nearest_object = None
        dist_nearest = None

        if static_obj_detected:
            for val in static_obj_detected:
                for i in range(0, len(static_obj_shape_dict[val]), LocalConstantsHelper.STEP_X_COORD):
                    if (
                        static_obj_shape_dict[val][i][idx_filter] != 0.0
                        and static_obj_shape_dict[val][i + 1][idx_filter] != 0.0
                    ):
                        # The point of static object needs to be transformed in global coordinates from local
                        # coordinates (ego ref system)
                        [x_coord, y_coord] = transf_local_to_global(
                            static_obj_shape_dict[val][i][idx_filter],
                            static_obj_shape_dict[val][i + 1][idx_filter],
                            ego_info.ego_x,
                            ego_info.ego_y,
                            ego_info.ego_yaw,
                        )
                        if y_coord <= side[0][1] and y_coord >= side[1][1]:
                            dist_temp = abs(
                                LeadLagPointsHelper.calc_dist_point_to_line(
                                    side[0], side[1], np.array([x_coord, y_coord])
                                )
                            )
                            # obj has to be closer than ThresholdHelper.THRESHOLD_DISTANCE_M to the side
                            if dist_temp < ThresholdHelper.THRESHOLD_DISTANCE_M:
                                if dist_nearest is not None:
                                    if dist_temp < dist_nearest:
                                        nearest_object = val
                                        dist_nearest = dist_temp
                                else:
                                    nearest_object = val
                                    dist_nearest = dist_temp

        return nearest_object

    @staticmethod
    def obtain_leftmost_point_to_side(
        static_obj_points: List[pd.Series], idx_filter: int, ego_info: EgoInfo
    ) -> np.array(float):
        """Get the the leftmost point of the object from a line ( side of the parking box)"""
        leftmost_point = None
        leftmost_x_coord = None
        for i in range(0, len(static_obj_points), LocalConstantsHelper.STEP_X_COORD):
            if static_obj_points[i][idx_filter] != 0.0 and static_obj_points[i + 1][idx_filter] != 0.0:
                [x_coord, y_coord] = transf_local_to_global(
                    static_obj_points[i][idx_filter],
                    static_obj_points[i + 1][idx_filter],
                    ego_info.ego_x,
                    ego_info.ego_y,
                    ego_info.ego_yaw,
                )
                if leftmost_x_coord is None:
                    leftmost_x_coord = x_coord
                    leftmost_point = np.array([x_coord, y_coord])
                else:
                    if x_coord > leftmost_x_coord:
                        leftmost_x_coord = x_coord
                        leftmost_point = np.array([x_coord, y_coord])

        return leftmost_point

    @staticmethod
    def obtain_rightmost_point_to_side(
        static_obj_points: List[pd.Series], idx_filter: int, ego_info: EgoInfo
    ) -> np.array(float):
        """Get the rightmost point of the object from a line ( side of the parking box)"""
        rightmost_point = None
        rightmost_x_coord = None
        for i in range(0, len(static_obj_points), LocalConstantsHelper.STEP_X_COORD):
            if static_obj_points[i][idx_filter] != 0.0 and static_obj_points[i + 1][idx_filter] != 0.0:
                [x_coord, y_coord] = transf_local_to_global(
                    static_obj_points[i][idx_filter],
                    static_obj_points[i + 1][idx_filter],
                    ego_info.ego_x,
                    ego_info.ego_y,
                    ego_info.ego_yaw,
                )
                if rightmost_x_coord is None:
                    rightmost_x_coord = x_coord
                    rightmost_point = np.array([x_coord, y_coord])
                else:
                    if x_coord < rightmost_x_coord:
                        rightmost_x_coord = x_coord
                        rightmost_point = np.array([x_coord, y_coord])

        return rightmost_point


class ParkingSlotHelper:
    """Parking slot helper"""

    @staticmethod
    def extract_slot_coordinates(
        signals: pd.DataFrame, idx_first: int, idx_second: int, sg_slotcoordinates
    ) -> List[List[float]]:
        """Obtain the x,y coordinates of the parking box for two time stamps"""
        first_coordinates = []
        second_coordinates = []
        first_coordinates = list(signals[sg_slotcoordinates][idx_first])
        second_coordinates = list(signals[sg_slotcoordinates][idx_second])

        return [first_coordinates, second_coordinates]


@dataclass
class ParkingBoxPoints:
    """Class used for easy handling of the parking box points"""

    top_left: np.ndarray
    bottom_left: np.ndarray
    top_right: np.ndarray
    bottom_right: np.ndarray


class GhostObjectsHelper:
    """Class providing functions which help in determining ghost object inside parking slot"""

    @staticmethod
    def create_parking_box(
        sides_coord: List[List[np.ndarray]], top_bottom_coord: List[List[np.ndarray]]
    ) -> ParkingBoxPoints:
        """Build the parking box with x coordinates from sides_coord and y coordinates from top_bottom_coord

        sides_coord:-> points_side_left  -> TOP -> x,y
                                         -> BOTTOM -> x,y
                    -> points_side_right -> TOP -> x,y
                                         -> BOTTOM -> x,y
        top_bottom_coord:-> points_side_left  -> TOP -> x,y
                                              -> BOTTOM -> x,y
                         -> points_side_right -> TOP -> x,y
                                              -> BOTTOM -> x,y
        """
        parking_box_points = ParkingBoxPoints(
            np.array([sides_coord[0][0][0], top_bottom_coord[0][0][1]]),
            np.array([sides_coord[0][1][0], top_bottom_coord[0][1][1]]),
            np.array([sides_coord[1][0][0], top_bottom_coord[1][0][1]]),
            np.array([sides_coord[1][1][0], top_bottom_coord[1][1][1]]),
        )

        return parking_box_points

    @staticmethod
    def check_point_inside_polygon(polyg: ParkingBoxPoints, point: List[float], borders: bool = False) -> bool:
        """If borders == True the point is considered inside if it is on one of the sides of the polygon"""
        ACCURACY_BORDERS = 0.0
        if borders:
            ACCURACY_BORDERS = 0.000001

        obj_mpl_path = MplPath.Path(np.array([polyg.bottom_left, polyg.top_left, polyg.top_right, polyg.bottom_right]))

        return obj_mpl_path.contains_point(point, radius=ACCURACY_BORDERS) or obj_mpl_path.contains_point(
            point, radius=-ACCURACY_BORDERS
        )


def generate_rotation_matrix(angle):
    """Method to generate rotation matrix using angle as parameter."""
    rotation_matrix = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])

    return rotation_matrix


def transf_local_to_global(x_local, y_local, x_global, y_global, angle):
    """Transforming the coordinates x,y from local to global x,y coordinates system by applying
    the matrices for translations and rotations in space

    :param x_local: x coordinate of the point in local coordinates system which will be transformed in global
    :param y_local: y coordinate of the point in local coordinates system which will be transformed in global
    :param x_global: x coordinate of the point in global coordinates system from where
                    the local point will be transformed
    :param y_global: y coordinate of the point in global coordinates system from where
                    the local point will be transformed
    :param angle: the angle between local and global coordinates system
    :return : local point transformed in global coordinates system
    """
    rotation_matrix = generate_rotation_matrix(angle)
    global_pts_matrix = np.array([x_global, y_global])
    local_pts_matrix = np.array([x_local, y_local])
    transformed_pts_matrix = np.dot(rotation_matrix, local_pts_matrix) + global_pts_matrix

    return [transformed_pts_matrix[0], transformed_pts_matrix[1]]
