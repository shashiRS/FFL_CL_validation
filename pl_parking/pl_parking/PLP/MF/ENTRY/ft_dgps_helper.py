"""DGPS helper for ENTRY tests"""

from typing import List

import numpy as np
import pandas as pd

import pl_parking.PLP.MF.constants as fc

# from pl_parking.PLP.MF.ENTRY.usemLagLeadShrinkHelper import ParkingSlotHelper , \
# ParkingBoxPoints, EgoInfo
from pl_parking.PLP.MF.ENTRY.usemLagLeadShrinkHelper import ParkingBoxPoints


class BoxPoints:
    """Class for the left and right points"""

    def __init__(self):
        """Initialize object attributes."""
        self.p1_left = np.array([0, 0])
        self.p1_right = np.array([0, 0])
        self.p2_left = np.array([0, 0])
        self.p2_right = np.array([0, 0])


class DgpsSignalsProcessing:
    """
    Class that extracts and performs all the transformations necessary for the DGPS points
    to PVF system of coordinates and compensates for odometry
    """

    def __init__(self, data_frame: pd.DataFrame):
        """Initializes the instance variables"""
        self.__signals = data_frame.copy()
        self.signals_copy = data_frame.copy()

        self.__x_ref = 0
        self.__y_ref = 0
        self.__angle_ref = 0

        self.sg_time = "TimeStamp"
        self.sg_ego_yaw = "DgpsEgoYaw"
        self.sg_oddo_x = "OdoEstimX"
        self.sg_oddo_y = "OdoEstimY"
        self.sg_transf_to_odo = "TransfToOdom"
        self.sg_dgps_hx = "DgpsHunterX"
        self.sg_dgps_hy = "DgpsHunterY"
        self.sg_dgps_tx = "DgpsTargetX"
        self.sg_dgps_ty = "DgpsTargetY"
        self.sg_dgps_t2x = "DgpsTarget2X"
        self.sg_dgps_t2y = "DgpsTarget2Y"
        self.sg_dgps_t3x = "DgpsTarget3X"
        self.sg_dgps_t3y = "DgpsTarget3Y"
        self.sg_dgps_t4x = "DgpsTarget4X"
        self.sg_dgps_t4y = "DgpsTarget4Y"

        self.signals_copy.set_index(self.sg_time, inplace=True)

    def process(self):
        """Transform the dgps points from dgps coordinates system to global coordinates system used by PVF"""
        self.__extract_reference_point()
        self.__tranf_dgp_points()
        self.create_boxes()

    def get_signals(self):
        """Function to get signals"""
        return self.__signals

    @staticmethod
    def extract_points_dgps_box_left(signals: pd.DataFrame, idx: np.int64) -> ParkingBoxPoints:
        """Extracts the points on the left side of the DGPS box"""
        points_box_left = []
        points_box_left.append(
            np.array(
                [
                    signals[fc.DgpsBoxesColumns.BOX_1_CORNER_LEFT_X_1][idx],
                    signals[fc.DgpsBoxesColumns.BOX_1_CORNER_LEFT_Y_1][idx],
                ]
            )
        )
        points_box_left.append(
            np.array(
                [
                    signals[fc.DgpsBoxesColumns.BOX_1_CORNER_RIGHT_X_1][idx],
                    signals[fc.DgpsBoxesColumns.BOX_1_CORNER_RIGHT_Y_1][idx],
                ]
            )
        )
        points_box_left.append(
            np.array(
                [
                    signals[fc.DgpsBoxesColumns.BOX_1_CORNER_LEFT_X_2][idx],
                    signals[fc.DgpsBoxesColumns.BOX_1_CORNER_LEFT_Y_2][idx],
                ]
            )
        )
        points_box_left.append(
            np.array(
                [
                    signals[fc.DgpsBoxesColumns.BOX_1_CORNER_RIGHT_X_2][idx],
                    signals[fc.DgpsBoxesColumns.BOX_1_CORNER_RIGHT_Y_2][idx],
                ]
            )
        )
        dgps_box_left = DgpsSignalsProcessing.extract_points_dgps_box(points_box_left)

        return dgps_box_left

    @staticmethod
    def extract_points_dgps_box_right(signals: pd.DataFrame, idx: np.int64) -> ParkingBoxPoints:
        """Extracts the points on the right side of the DGPS box"""
        points_box_right = []
        points_box_right.append(
            np.array(
                [
                    signals[fc.DgpsBoxesColumns.BOX_2_CORNER_LEFT_X_1][idx],
                    signals[fc.DgpsBoxesColumns.BOX_2_CORNER_LEFT_Y_1][idx],
                ]
            )
        )
        points_box_right.append(
            np.array(
                [
                    signals[fc.DgpsBoxesColumns.BOX_2_CORNER_RIGHT_X_1][idx],
                    signals[fc.DgpsBoxesColumns.BOX_2_CORNER_RIGHT_Y_1][idx],
                ]
            )
        )
        points_box_right.append(
            np.array(
                [
                    signals[fc.DgpsBoxesColumns.BOX_2_CORNER_LEFT_X_2][idx],
                    signals[fc.DgpsBoxesColumns.BOX_2_CORNER_LEFT_Y_2][idx],
                ]
            )
        )
        points_box_right.append(
            np.array(
                [
                    signals[fc.DgpsBoxesColumns.BOX_2_CORNER_RIGHT_X_2][idx],
                    signals[fc.DgpsBoxesColumns.BOX_2_CORNER_RIGHT_Y_2][idx],
                ]
            )
        )

        dgps_box_right = DgpsSignalsProcessing.extract_points_dgps_box(points_box_right)

        return dgps_box_right

    @staticmethod
    def extract_points_dgps_box(points_box: List[np.ndarray]) -> ParkingBoxPoints:
        """Arranges points on the left and right sides of the DGPS box in the proper order"""
        # Sort Points on X axis to have the left side first
        points_box.sort(key=lambda x: x[0])

        IDX_RIGHT_FIRST_POINT = 2
        IDX_RIGHT_SECOND_POINT = 3
        # Sort Points on Y axis to have top corner first
        points_left = [points_box[0], points_box[1]]
        points_left.sort(key=lambda y: y[1], reverse=True)
        points_right = [points_box[IDX_RIGHT_FIRST_POINT], points_box[IDX_RIGHT_SECOND_POINT]]
        points_right.sort(key=lambda y: y[1], reverse=True)

        dgps_box = ParkingBoxPoints(points_left[0], points_left[1], points_right[0], points_right[1])

        return dgps_box

    def __tranf_dgp_points(self):
        """Two transformations are applied:
        - first transformation applied to the dgps points to move them in PVF system coordinates (without odometry
        transformation applied)
        - second transformation applied to the dgps points to compensate the odometry transformation
        - third transformation applied to the dgps compensate the difference between odometry estimation of the ego and
        dgps from dgps (only translation)
        """
        for i, _ in enumerate(self.__signals[self.sg_dgps_hx][:-1]):
            [self.__signals[self.sg_dgps_hx].values[i], self.__signals[self.sg_dgps_hy].values[i]] = (
                transf_global_to_local(
                    self.__signals[self.sg_dgps_hx].values[i],
                    self.__signals[self.sg_dgps_hy].values[i],
                    self.__x_ref,
                    self.__y_ref,
                    -self.__angle_ref,
                )
            )

            x_diff = self.__signals[self.sg_oddo_x].values[i] - self.__signals[self.sg_dgps_hx].values[i]
            y_diff = self.__signals[self.sg_oddo_y].values[i] - self.__signals[self.sg_dgps_hy].values[i]
            [self.__signals[self.sg_dgps_hx].values[i], self.__signals[self.sg_dgps_hy].values[i]] = (
                transf_global_to_local(
                    self.__signals[self.sg_dgps_hx].values[i],
                    self.__signals[self.sg_dgps_hy].values[i],
                    self.__signals[self.sg_transf_to_odo][i][fc.TransfToOdomConstants.X_COORD],
                    self.__signals[self.sg_transf_to_odo][i][fc.TransfToOdomConstants.Y_COORD],
                    self.__signals[self.sg_transf_to_odo][i][fc.TransfToOdomConstants.ANGLE],
                )
            )

            [self.__signals[self.sg_dgps_tx].values[i], self.__signals[self.sg_dgps_ty].values[i]] = (
                transf_global_to_local(
                    self.__signals[self.sg_dgps_tx].values[i],
                    self.__signals[self.sg_dgps_ty].values[i],
                    self.__x_ref,
                    self.__y_ref,
                    -self.__angle_ref,
                )
            )

            [self.__signals[self.sg_dgps_tx].values[i], self.__signals[self.sg_dgps_ty].values[i]] = (
                transf_global_to_local(
                    self.__signals[self.sg_dgps_tx].values[i],
                    self.__signals[self.sg_dgps_ty].values[i],
                    self.__signals[self.sg_transf_to_odo][i][fc.TransfToOdomConstants.X_COORD],
                    self.__signals[self.sg_transf_to_odo][i][fc.TransfToOdomConstants.Y_COORD],
                    self.__signals[self.sg_transf_to_odo][i][fc.TransfToOdomConstants.ANGLE],
                )
            )

            [self.__signals[self.sg_dgps_t2x].values[i], self.__signals[self.sg_dgps_t2y].values[i]] = (
                transf_global_to_local(
                    self.__signals[self.sg_dgps_t2x].values[i],
                    self.__signals[self.sg_dgps_t2y].values[i],
                    self.__x_ref,
                    self.__y_ref,
                    -self.__angle_ref,
                )
            )

            [self.__signals[self.sg_dgps_t2x].values[i], self.__signals[self.sg_dgps_t2y].values[i]] = (
                transf_global_to_local(
                    self.__signals[self.sg_dgps_t2x].values[i],
                    self.__signals[self.sg_dgps_t2y].values[i],
                    self.__signals[self.sg_transf_to_odo][i][fc.TransfToOdomConstants.X_COORD],
                    self.__signals[self.sg_transf_to_odo][i][fc.TransfToOdomConstants.Y_COORD],
                    self.__signals[self.sg_transf_to_odo][i][fc.TransfToOdomConstants.ANGLE],
                )
            )

            [self.__signals[self.sg_dgps_t3x].values[i], self.__signals[self.sg_dgps_t3y].values[i]] = (
                transf_global_to_local(
                    self.__signals[self.sg_dgps_t3x].values[i],
                    self.__signals[self.sg_dgps_t3y].values[i],
                    self.__x_ref,
                    self.__y_ref,
                    -self.__angle_ref,
                )
            )

            [self.__signals[self.sg_dgps_t3x].values[i], self.__signals[self.sg_dgps_t3y].values[i]] = (
                transf_global_to_local(
                    self.__signals[self.sg_dgps_t3x].values[i],
                    self.__signals[self.sg_dgps_t3y].values[i],
                    self.__signals[self.sg_transf_to_odo][i][fc.TransfToOdomConstants.X_COORD],
                    self.__signals[self.sg_transf_to_odo][i][fc.TransfToOdomConstants.Y_COORD],
                    self.__signals[self.sg_transf_to_odo][i][fc.TransfToOdomConstants.ANGLE],
                )
            )

            [self.__signals[self.sg_dgps_t4x].values[i], self.__signals[self.sg_dgps_t4y].values[i]] = (
                transf_global_to_local(
                    self.__signals[self.sg_dgps_t4x].values[i],
                    self.__signals[self.sg_dgps_t4y].values[i],
                    self.__x_ref,
                    self.__y_ref,
                    -self.__angle_ref,
                )
            )

            [self.__signals[self.sg_dgps_t4x].values[i], self.__signals[self.sg_dgps_t4y].values[i]] = (
                transf_global_to_local(
                    self.__signals[self.sg_dgps_t4x].values[i],
                    self.__signals[self.sg_dgps_t4y].values[i],
                    self.__signals[self.sg_transf_to_odo][i][fc.TransfToOdomConstants.X_COORD],
                    self.__signals[self.sg_transf_to_odo][i][fc.TransfToOdomConstants.Y_COORD],
                    self.__signals[self.sg_transf_to_odo][i][fc.TransfToOdomConstants.ANGLE],
                )
            )

            self.__translate_dgps_points_odo_estim(x_diff, y_diff, i)

    def __translate_dgps_points_odo_estim(self, x_diff, y_diff, idx):
        """Translate dgps points applying the difference between odo estimation of ego and dgps points of ego"""
        self.__signals[self.sg_dgps_hx].values[idx] += x_diff
        self.__signals[self.sg_dgps_hy].values[idx] += y_diff
        self.__signals[self.sg_dgps_tx].values[idx] += x_diff
        self.__signals[self.sg_dgps_ty].values[idx] += y_diff
        self.__signals[self.sg_dgps_t2x].values[idx] += x_diff
        self.__signals[self.sg_dgps_t2y].values[idx] += y_diff
        self.__signals[self.sg_dgps_t3x].values[idx] += x_diff
        self.__signals[self.sg_dgps_t3y].values[idx] += y_diff
        self.__signals[self.sg_dgps_t4x].values[idx] += x_diff
        self.__signals[self.sg_dgps_t4y].values[idx] += y_diff

    def obtain_points_box(self, x1, y1, x2, y2):
        """Obtain the corner points of the box having the middle points of two parallel sides"""
        p1 = np.array([x1, y1])
        p2 = np.array([x2, y2])

        # Calculate a vector between p1 and p2
        p_vect = p2 - p1

        # Perpendicular vector (counter clockwise) to p_vect
        p_perpend = p_vect[[1, 0]]
        p_perpend[[0]] *= -1

        box_points = BoxPoints()

        if p_vect.any() != 0.0:
            # Normalize perpendicular to p_vect
            np.seterr(invalid="ignore")
            p_norm = p_perpend / np.linalg.norm(p_perpend)

            box_points.p1_left = p1 - p_norm * fc.DgpsConstants.WIDTH_BOX_M / 2
            box_points.p1_right = p1 + p_norm * fc.DgpsConstants.WIDTH_BOX_M / 2
            box_points.p2_left = p2 - p_norm * fc.DgpsConstants.WIDTH_BOX_M / 2
            box_points.p2_right = p2 + p_norm * fc.DgpsConstants.WIDTH_BOX_M / 2

        return box_points

    def create_boxes(self):
        """Create the boxes from dGPS signals"""
        box_1_corner_left_x_1 = []
        box_1_corner_left_y_1 = []
        box_1_corner_right_x_1 = []
        box_1_corner_right_y_1 = []
        box_1_corner_left_x_2 = []
        box_1_corner_left_y_2 = []
        box_1_corner_right_x_2 = []
        box_1_corner_right_y_2 = []
        box_2_corner_left_x_1 = []
        box_2_corner_left_y_1 = []
        box_2_corner_right_x_1 = []
        box_2_corner_right_y_1 = []
        box_2_corner_left_x_2 = []
        box_2_corner_left_y_2 = []
        box_2_corner_right_x_2 = []
        box_2_corner_right_y_2 = []

        for _, row in self.__signals.iterrows():
            box_1_pts = self.obtain_points_box(
                row[self.sg_dgps_tx], row[self.sg_dgps_ty], row[self.sg_dgps_t2x], row[self.sg_dgps_t2y]
            )
            box_2_pts = self.obtain_points_box(
                row[self.sg_dgps_t3x], row[self.sg_dgps_t3y], row[self.sg_dgps_t4x], row[self.sg_dgps_t4y]
            )
            box_1_corner_left_x_1.append(box_1_pts.p1_left[0])
            box_1_corner_left_y_1.append(box_1_pts.p1_left[1])
            box_1_corner_right_x_1.append(box_1_pts.p1_right[0])
            box_1_corner_right_y_1.append(box_1_pts.p1_right[1])
            box_1_corner_left_x_2.append(box_1_pts.p2_left[0])
            box_1_corner_left_y_2.append(box_1_pts.p2_left[1])
            box_1_corner_right_x_2.append(box_1_pts.p2_right[0])
            box_1_corner_right_y_2.append(box_1_pts.p2_right[1])
            box_2_corner_left_x_1.append(box_2_pts.p1_left[0])
            box_2_corner_left_y_1.append(box_2_pts.p1_left[1])
            box_2_corner_right_x_1.append(box_2_pts.p1_right[0])
            box_2_corner_right_y_1.append(box_2_pts.p1_right[1])
            box_2_corner_left_x_2.append(box_2_pts.p2_left[0])
            box_2_corner_left_y_2.append(box_2_pts.p2_left[1])
            box_2_corner_right_x_2.append(box_2_pts.p2_right[0])
            box_2_corner_right_y_2.append(box_2_pts.p2_right[1])

        self.__signals[fc.DgpsBoxesColumns.BOX_1_CORNER_LEFT_X_1] = box_1_corner_left_x_1
        self.__signals[fc.DgpsBoxesColumns.BOX_1_CORNER_LEFT_Y_1] = box_1_corner_left_y_1
        self.__signals[fc.DgpsBoxesColumns.BOX_1_CORNER_RIGHT_X_1] = box_1_corner_right_x_1
        self.__signals[fc.DgpsBoxesColumns.BOX_1_CORNER_RIGHT_Y_1] = box_1_corner_right_y_1
        self.__signals[fc.DgpsBoxesColumns.BOX_1_CORNER_LEFT_X_2] = box_1_corner_left_x_2
        self.__signals[fc.DgpsBoxesColumns.BOX_1_CORNER_LEFT_Y_2] = box_1_corner_left_y_2
        self.__signals[fc.DgpsBoxesColumns.BOX_1_CORNER_RIGHT_X_2] = box_1_corner_right_x_2
        self.__signals[fc.DgpsBoxesColumns.BOX_1_CORNER_RIGHT_Y_2] = box_1_corner_right_y_2
        self.__signals[fc.DgpsBoxesColumns.BOX_2_CORNER_LEFT_X_1] = box_2_corner_left_x_1
        self.__signals[fc.DgpsBoxesColumns.BOX_2_CORNER_LEFT_Y_1] = box_2_corner_left_y_1
        self.__signals[fc.DgpsBoxesColumns.BOX_2_CORNER_RIGHT_X_1] = box_2_corner_right_x_1
        self.__signals[fc.DgpsBoxesColumns.BOX_2_CORNER_RIGHT_Y_1] = box_2_corner_right_y_1
        self.__signals[fc.DgpsBoxesColumns.BOX_2_CORNER_LEFT_X_2] = box_2_corner_left_x_2
        self.__signals[fc.DgpsBoxesColumns.BOX_2_CORNER_LEFT_Y_2] = box_2_corner_left_y_2
        self.__signals[fc.DgpsBoxesColumns.BOX_2_CORNER_RIGHT_X_2] = box_2_corner_right_x_2
        self.__signals[fc.DgpsBoxesColumns.BOX_2_CORNER_RIGHT_Y_2] = box_2_corner_right_y_2

    @staticmethod
    def extract_points_side_lines_dgps_boxes(signals: pd.DataFrame, idx: np.int64) -> List[List[np.ndarray]]:
        """Extract the points of side boxes closest to the parking box (left/right side)"""
        points_boxes_1 = []
        points_boxes_2 = []
        points_boxes_1.append(
            np.array(
                [
                    signals[fc.DgpsBoxesColumns.BOX_1_CORNER_LEFT_X_1][idx],
                    signals[fc.DgpsBoxesColumns.BOX_1_CORNER_LEFT_Y_1][idx],
                ]
            )
        )
        points_boxes_1.append(
            np.array(
                [
                    signals[fc.DgpsBoxesColumns.BOX_1_CORNER_RIGHT_X_1][idx],
                    signals[fc.DgpsBoxesColumns.BOX_1_CORNER_RIGHT_Y_1][idx],
                ]
            )
        )
        points_boxes_1.append(
            np.array(
                [
                    signals[fc.DgpsBoxesColumns.BOX_1_CORNER_LEFT_X_2][idx],
                    signals[fc.DgpsBoxesColumns.BOX_1_CORNER_LEFT_Y_2][idx],
                ]
            )
        )
        points_boxes_1.append(
            np.array(
                [
                    signals[fc.DgpsBoxesColumns.BOX_1_CORNER_RIGHT_X_2][idx],
                    signals[fc.DgpsBoxesColumns.BOX_1_CORNER_RIGHT_Y_2][idx],
                ]
            )
        )
        points_boxes_2.append(
            np.array(
                [
                    signals[fc.DgpsBoxesColumns.BOX_2_CORNER_LEFT_X_1][idx],
                    signals[fc.DgpsBoxesColumns.BOX_2_CORNER_LEFT_Y_1][idx],
                ]
            )
        )
        points_boxes_2.append(
            np.array(
                [
                    signals[fc.DgpsBoxesColumns.BOX_2_CORNER_RIGHT_X_1][idx],
                    signals[fc.DgpsBoxesColumns.BOX_2_CORNER_RIGHT_Y_1][idx],
                ]
            )
        )
        points_boxes_2.append(
            np.array(
                [
                    signals[fc.DgpsBoxesColumns.BOX_2_CORNER_LEFT_X_2][idx],
                    signals[fc.DgpsBoxesColumns.BOX_2_CORNER_LEFT_Y_2][idx],
                ]
            )
        )
        points_boxes_2.append(
            np.array(
                [
                    signals[fc.DgpsBoxesColumns.BOX_2_CORNER_RIGHT_X_2][idx],
                    signals[fc.DgpsBoxesColumns.BOX_2_CORNER_RIGHT_Y_2][idx],
                ]
            )
        )

        # Sort Points to get the side of the box used for Lag (left) and the one used for Lead(right)
        if points_boxes_1[0][0] >= points_boxes_2[0][0]:
            points_boxes_1.sort(key=lambda x: x[0])
            points_boxes_2.sort(key=lambda x: x[0], reverse=True)
        # swap sort if the boxes are swapped
        else:
            points_boxes_1.sort(key=lambda x: x[0], reverse=True)
            points_boxes_2.sort(key=lambda x: x[0])

        # Sort Points to have the top corner first
        points_left = [points_boxes_1[0], points_boxes_1[1]]
        points_left.sort(key=lambda y: y[1], reverse=True)
        points_right = [points_boxes_2[0], points_boxes_2[1]]
        points_right.sort(key=lambda y: y[1], reverse=True)

        return [[points_left[0], points_left[1]], [points_right[0], points_right[1]]]

    def __extract_reference_point(self):
        timestamp_idx = self.remove_sampling_frequency_issue()
        idx = len(self.signals_copy.loc[:timestamp_idx])

        self.__x_ref = self.__signals[self.sg_dgps_hx][idx]
        self.__y_ref = self.__signals[self.sg_dgps_hy][idx]
        self.__angle_ref = np.deg2rad(self.__signals[self.sg_ego_yaw][idx])

    def remove_sampling_frequency_issue(self):
        """Remove possible issue due to sampling frequency"""
        # TODO TO add to constants

        US_IN_S = 1000000
        THRESOLD_TIME_S = 0.5
        THRESOLD_ANGLE_DEG = 1
        THRESOLD_DISTANCE_M = 1

        idx_start = self.__signals[self.sg_time].iloc[0]

        idx_yaw = idx_start
        idx_hx = idx_start
        idx_hy = idx_start

        for idx, row in self.signals_copy.iterrows():
            if ((idx - idx_start) / US_IN_S) < THRESOLD_TIME_S:
                if self.__check_diff_one_param(row, self.sg_ego_yaw, THRESOLD_ANGLE_DEG, idx_yaw):
                    idx_start = idx
                    idx_yaw = idx
                    if self.__check_diff_one_param(row, self.sg_dgps_hx, THRESOLD_DISTANCE_M, idx_hx):
                        idx_hx = idx
                    if self.__check_diff_one_param(row, self.sg_dgps_hy, THRESOLD_DISTANCE_M, idx_hy):
                        idx_hy = idx
                    if self.__check_rest_param_diff(
                        row, self.sg_dgps_hx, self.sg_dgps_hy, THRESOLD_DISTANCE_M, THRESOLD_DISTANCE_M
                    ):
                        return idx
                elif self.__check_diff_one_param(row, self.sg_dgps_hx, THRESOLD_DISTANCE_M, idx_hx):
                    idx_start = idx
                    idx_hx = idx
                    if self.__check_diff_one_param(row, self.sg_dgps_hy, THRESOLD_DISTANCE_M, idx_hy):
                        idx_hy = idx
                    if self.__check_diff_one_param(row, self.sg_ego_yaw, THRESOLD_ANGLE_DEG, idx_yaw):
                        idx_yaw = idx
                    if self.__check_rest_param_diff(
                        row, self.sg_dgps_hy, self.sg_ego_yaw, THRESOLD_DISTANCE_M, THRESOLD_ANGLE_DEG
                    ):
                        return idx
                elif self.__check_diff_one_param(row, self.sg_dgps_hy, THRESOLD_DISTANCE_M, idx_hy):
                    idx_start = idx
                    idx_hy = idx
                    if self.__check_diff_one_param(row, self.sg_dgps_hx, THRESOLD_DISTANCE_M, idx_hx):
                        idx_hx = idx
                    if self.__check_diff_one_param(row, self.sg_ego_yaw, THRESOLD_ANGLE_DEG, idx_yaw):
                        idx_yaw = idx
                    if self.__check_rest_param_diff(
                        row, self.sg_dgps_hx, self.sg_ego_yaw, THRESOLD_DISTANCE_M, THRESOLD_ANGLE_DEG
                    ):
                        return idx

        return idx_start

    def __check_diff_one_param(self, row, column_1: str, thresold_1, idx: int) -> bool:
        """Check if there is sampling frequency issue with one parameter.
        Parameter could be: DGPS_HUNTER_X, DGPS_HUNTER_Y, DGPS_EGO_YAW
        """
        if abs(row[column_1] - self.signals_copy[column_1][idx]) > thresold_1:
            return True

        return False

    def __check_rest_param_diff(self, row, column_1: str, column_2: str, thresold_1, thresold_2) -> bool:
        """Check if there is sampling frequency issue with the rest of the parameters.
        Parameters could be: DGPS_HUNTER_X, DGPS_HUNTER_Y, DGPS_EGO_YAW
        """
        cond_bool = [
            abs(row[column_1] - self.signals_copy[column_1].values[0]) > thresold_1,
            abs(row[column_2] - self.signals_copy[column_2].values[0]) > thresold_2,
        ]
        if all(cond_bool):
            return True

        return False


def transf_global_to_local(x_global, y_global, x_local, y_local, angle):
    """Transforming the coordinates x,y from global to local x,y coordinates system by applying
    the matrices for translations and rotations in space

    :param x_local: x coordinate of the point in global coordinates system which will be transformed in local
    :param y_local: y coordinate of the point in global coordinates system which will be transformed in local
    :param x_global: x coordinate of the point in local coordinates system from where
                    the local point will be transformed
    :param y_global: y coordinate of the point in local coordinates system from where
                    the local point will be transformed
    :param angle: the angle between global and local coordinates system
    :return : local point transformed in local coordinates system
    """
    rotation_matrix = generate_rotation_matrix(-angle)
    global_pts_matrix = np.array([x_global, y_global])
    local_pts_matrix = np.array([x_local, y_local])
    calc_matrix = global_pts_matrix - local_pts_matrix
    # calc_matrix= np.array([x_global, y_global]) - np.array([x_local, y_local])
    transformed_pts_matrix = np.dot(rotation_matrix, calc_matrix)

    return [transformed_pts_matrix[0], transformed_pts_matrix[1]]


def generate_rotation_matrix(angle):
    """Function to generate rotation matrix using angle as parameter."""
    rotation_matrix = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])

    return rotation_matrix
