"""pcl helper module for CEM"""

import math
import sys
import typing

from numpy import arccos, cross, dot, pi
from numpy.linalg import norm

from pl_parking.PLP.CEM.constants import ConstantsCem
from pl_parking.PLP.CEM.ft_pose_helper import FtPoseHelper
from pl_parking.PLP.CEM.ground_truth.vehicle_coordinates_helper import VehicleCoordinateHelper
from pl_parking.PLP.CEM.inputs.input_CemPclReader import PCLDelimiter, PCLPoint, PCLTimeFrame
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import RelativeMotion
from pl_parking.PLP.CEM.inputs.input_DGPSReader import DgpsTimeframe
from pl_parking.PLP.CEM.inputs.input_PmdReader import PMDCamera, PMDLine, PMDLinePoint, PMDTimeFrame
from pl_parking.PLP.CV.PMSD.association import Association, VehicleLine


class FtPclHelper:
    """Helper class for PCL operations."""

    @staticmethod
    def distance_point_vehicle(point: PCLPoint) -> float:
        """Calculate distance of a point from the vehicle.

        Args:
            point (PCLPoint): Point coordinates.

        Returns:
            float: Distance from the vehicle.
        """
        return math.sqrt(point.x * point.x + point.y * point.y)

    @staticmethod
    def get_closest_point(pcl: PCLDelimiter) -> PCLPoint:
        """Get the closest point to the vehicle from a PCL delimiter.

        Args:
            pcl (PCLDelimiter): PCL delimiter containing start and end points.

        Returns:
            PCLPoint: Closest point to the vehicle.
        """
        if FtPclHelper.distance_point_vehicle(pcl.start_point) < FtPclHelper.distance_point_vehicle(pcl.end_point):
            return pcl.start_point
        else:
            return pcl.end_point

    @staticmethod
    def distance_pcl_vehicle(pcl: PCLDelimiter) -> float:
        """Calculate minimum distance of a PCL delimiter from the vehicle."""
        return min(
            FtPclHelper.distance_point_vehicle(pcl.start_point), FtPclHelper.distance_point_vehicle(pcl.end_point)
        )

    @staticmethod
    def find_missing_pcl_line_ids(prevTimeframe: PCLTimeFrame, curTimeframe: PCLTimeFrame) -> typing.List[PCLDelimiter]:
        """Find missing PCL line IDs between two timeframes."""
        curIds = set()

        for pcl in curTimeframe.pcl_delimiter_array:
            curIds.add(pcl.delimiter_id)

        ret = []
        for pcl in prevTimeframe.pcl_delimiter_array:
            if pcl.delimiter_id not in curIds:
                ret.append(pcl)

        return ret

    @staticmethod
    def get_closest_line(lines: typing.List[PCLDelimiter]) -> typing.Tuple[PCLDelimiter, float]:
        """Find the closest PCL line to the vehicle.

        Args:
            lines (typing.List[PCLDelimiter]): List of PCL delimiters.

        Returns:
            typing.Tuple[PCLDelimiter, float]: Closest PCL delimiter and its distance from the vehicle.
        """
        minDistance = sys.float_info.max
        closestPcl = None

        for line in lines:
            dist = FtPclHelper.distance_pcl_vehicle(line)
            if dist < minDistance:
                minDistance = dist
                closestPcl = line

        return closestPcl, minDistance

    @staticmethod
    def get_furthest_line(lines: typing.List[PCLDelimiter]) -> typing.Tuple[PCLDelimiter, float]:
        """Find the furthest PCL line to the vehicle.

        Args:
            lines (typing.List[PCLDelimiter]): List of PCL delimiters.

        Returns:
            typing.Tuple[PCLDelimiter, float]: Furthest PCL delimiter and its distance from the vehicle.
        """
        maxDistance = sys.float_info.min
        furthestPcl = None

        for line in lines:
            dist = FtPclHelper.distance_pcl_vehicle(line)
            if dist > maxDistance:
                maxDistance = dist
                furthestPcl = line

        return furthestPcl, maxDistance

    @staticmethod
    def transform_pcl(pcl: PCLDelimiter, relative_motion: RelativeMotion):
        """Transform a PCL delimiter based on relative motion.

        Args:
            pcl (PCLDelimiter): PCL delimiter to transform.
            relative_motion (RelativeMotion): Relative motion information.

        Returns:
            PCLDelimiter: Transformed PCL delimiter.
        """
        start_point = FtPoseHelper.transform_point((pcl.start_point.x, pcl.start_point.y), relative_motion)
        end_point = FtPoseHelper.transform_point((pcl.end_point.x, pcl.end_point.y), relative_motion)

        return PCLDelimiter(
            pcl.delimiter_id,
            pcl.delimiter_type,
            PCLPoint(start_point[0], start_point[1]),
            PCLPoint(end_point[0], end_point[1]),
            pcl.confidence_percent,
        )

    @staticmethod
    def distance_pcl_points(pnt1: typing.Union[PCLPoint, PMDLinePoint], pnt2: typing.Union[PCLPoint, PMDLinePoint]):
        """Calculate distance between two points in a PCL.

        Args:
            pnt1 (typing.Union[PCLPoint, PMDLinePoint]): First point.
            pnt2 (typing.Union[PCLPoint, PMDLinePoint]): Second point.

        Returns:
            float: Distance between the two points.
        """
        dx = pnt1.x - pnt2.x
        dy = pnt1.y - pnt2.y
        return math.sqrt(dx * dx + dy * dy)

    @staticmethod
    def segment_point_distance(A, B, P):
        """Segment line AB, point P, where each one is an array([x, y])"""
        if all(A == P) or all(B == P):
            return 0
        if arccos(dot((P - A) / norm(P - A), (B - A) / norm(B - A))) > pi / 2:
            return norm(P - A)
        if arccos(dot((P - B) / norm(P - B), (A - B) / norm(A - B))) > pi / 2:
            return norm(P - B)
        return norm(cross(A - B, A - P)) / norm(B - A)

    @staticmethod
    def is_pcl_pcl_association_valid(
        pcl: PCLDelimiter, gt_pcl: PCLDelimiter, association_radius: float
    ) -> typing.Tuple[bool, float, float, float]:
        """Check validity of PCL-PCL association.

        Args:
            pcl (PCLDelimiter): PCL delimiter to associate.
            gt_pcl (PCLDelimiter): Ground truth PCL delimiter.
            association_radius (float): Association radius.

        Returns:
            typing.Tuple[bool, float, float, float]: Tuple indicating validity and association details.
        """
        line = VehicleLine.from_cem_pcl(pcl)
        gt_line = VehicleLine.from_cem_pcl(gt_pcl)
        return Association.match(gt_line, line, Association.AlgoType.ALGO_RECTANGLE)

    @staticmethod
    def is_pcl_pmd_association_valid(
        pcl: PCLDelimiter, pmd: PMDLine, association_radius: float
    ) -> typing.Tuple[bool, float, float, float]:
        """Check validity of PCL-PMD association.

        Args:
            pcl (PCLDelimiter): PCL delimiter to associate.
            pmd (PMDLine): PMD line to associate.
            association_radius (float): Association radius.

        Returns:
            typing.Tuple[bool, float, float, float]: Tuple indicating validity and association details.
        """
        line = VehicleLine.from_cem_pmd(pmd)
        gt_line = VehicleLine.from_cem_pcl(pcl)
        return Association.match(gt_line, line, Association.AlgoType.ALGO_RECTANGLE)

    @staticmethod
    def associate_pcl_to_ground_truth(
        pcl_cem_list: typing.List[PCLDelimiter],
        pcl_ground_truth_list: typing.List[PCLDelimiter],
        association_radius: float,
    ) -> typing.Tuple[typing.List[typing.Tuple[PCLDelimiter, PCLDelimiter]], typing.List[PCLDelimiter]]:
        """Associate PCL CEM output to the ground truth

        Args:
            pcl_cem_list (typing.List[PCLDelimiter]): list of PCL CEM output
            pcl_ground_truth_list (typing.List[PCLDelimiter): list of PCL ground truth

        Returns:
            typing.Tuple[typing.List[typing.Tuple[PCLDelimiter, PCLDelimiter]], typing.List[PCLDelimiter]]: \
                association pair list including the unassociated PCL CEM output (the first element of the pair is the \
                    CEM PCL output and the second one is the associated ground truth), unassociated PCL ground truth
        """
        association: typing.List[typing.Tuple[PCLDelimiter, PCLDelimiter]] = []

        ground_truth_set = set(pcl_ground_truth_list)
        for pcl in pcl_cem_list:
            min_dist = sys.float_info.max
            associated_ground_truth = None

            for ground_truth in ground_truth_set:
                is_valid_association, _, _, line_dist = FtPclHelper.is_pcl_pcl_association_valid(
                    pcl, ground_truth, association_radius
                )

                if is_valid_association and line_dist < min_dist:
                    min_dist = line_dist
                    associated_ground_truth = ground_truth

            if associated_ground_truth is not None:
                ground_truth_set.remove(associated_ground_truth)

            association.append((pcl, associated_ground_truth))

        not_associated_ground_truth = list(ground_truth_set)

        return association, not_associated_ground_truth

    @staticmethod
    def associate_pmd_to_ground_truth(
        pmd_list: typing.List[PMDLine], pcl_ground_truth_list: typing.List[PCLDelimiter], association_radius: float
    ) -> typing.Tuple[typing.List[typing.Tuple[PMDLine, PCLDelimiter]], typing.List[PCLDelimiter]]:
        """Associate PMD to the ground truth

        Args:
            pmd_list (typing.List[PMDLine]): PMD lines list
            pcl_ground_truth_list (typing.List[PCLDelimiter): list of PCL ground truth

        Returns:
            typing.Tuple[typing.List[typing.Tuple[PMDLine, PCLDelimiter]], typing.List[PCLDelimiter]]: \
                association pair list including the unassociated PMD (the first element of the pair is the \
                    PMD and the second one is the associated ground truth), unassociated PCL ground truth
        """
        association: typing.List[typing.Tuple[PMDLine, PCLDelimiter]] = []

        ground_truth_set = set(pcl_ground_truth_list)
        for pmd in pmd_list:
            min_dist = sys.float_info.max
            associated_ground_truth = None

            for ground_truth in ground_truth_set:
                is_valid_association, _, _, line_dist = FtPclHelper.is_pcl_pmd_association_valid(
                    ground_truth, pmd, association_radius
                )

                if is_valid_association and line_dist < min_dist:
                    min_dist = line_dist
                    associated_ground_truth = ground_truth

            if associated_ground_truth is not None:
                ground_truth_set.remove(associated_ground_truth)

            association.append((pmd, associated_ground_truth))

        not_associated_ground_truth = list(ground_truth_set)

        return association, not_associated_ground_truth

    @staticmethod
    def calculate_cem_pcl_false_positive_iso(
        pcl_cem: typing.List[PCLDelimiter], pcl_ground_truth: typing.List[PCLDelimiter], association_radius: float
    ) -> float:
        """Calculate false positive rate for CEM PCL using ISO method."""
        nbr_pcl_lines = len(pcl_cem)
        if nbr_pcl_lines == 0:
            return 0

        association, _ = FtPclHelper.associate_pcl_to_ground_truth(pcl_cem, pcl_ground_truth, association_radius)
        nbr_unassociated_pcl = len([pcl for pcl, ground_truth in association if ground_truth is None])

        return nbr_unassociated_pcl / nbr_pcl_lines

    @staticmethod
    def calculate_cem_pcl_false_positive_utm(
        dgps: DgpsTimeframe,
        pcl_cem: typing.List[PCLDelimiter],
        pcl_ground_truth_utm: typing.List[PCLDelimiter],
        association_radius: float,
    ) -> float:
        """Calculate false positive rate for CEM PCL using UTM method."""
        nbr_pcl_lines = len(pcl_cem)
        if nbr_pcl_lines == 0:
            return 0

        pcl_ground_truth_iso = VehicleCoordinateHelper.pcl_utm_to_vehicle(pcl_ground_truth_utm, dgps)
        return FtPclHelper.calculate_cem_pcl_false_positive_iso(pcl_cem, pcl_ground_truth_iso, association_radius)

    @staticmethod
    def calculate_cem_pcl_precision_iso(
        pcl_cem: typing.List[PCLDelimiter], pcl_ground_truth: typing.List[PCLDelimiter], association_radius: float
    ) -> float:
        """Calculate precision for CEM PCL using ISO method."""
        nbr_pcl_lines = len(pcl_cem)
        if nbr_pcl_lines == 0:
            return 0

        association, _ = FtPclHelper.associate_pcl_to_ground_truth(pcl_cem, pcl_ground_truth, association_radius)
        nbr_associated_pcl = len([pcl for pcl, ground_truth in association if ground_truth])

        return nbr_associated_pcl / nbr_pcl_lines

    @staticmethod
    def calculate_cem_pcl_precision_utm(
        dgps: DgpsTimeframe,
        pcl_cem: typing.List[PCLDelimiter],
        pcl_ground_truth_utm: typing.List[PCLDelimiter],
        association_radius: float,
    ) -> float:
        """Calculate precision for CEM PCL using UTM method."""
        nbr_pcl_lines = len(pcl_cem)
        if nbr_pcl_lines == 0:
            return 0

        pcl_ground_truth_iso = VehicleCoordinateHelper.pcl_utm_to_vehicle(pcl_ground_truth_utm, dgps)
        return FtPclHelper.calculate_cem_pcl_precision_iso(pcl_cem, pcl_ground_truth_iso, association_radius)

    @staticmethod
    def calculate_cem_pcl_true_positive_iso(
        pcl_cem: typing.List[PCLDelimiter], pcl_ground_truth: typing.List[PCLDelimiter], association_radius: float
    ) -> float:
        """Calculate true positive rate for CEM PCL using ISO method."""
        nbr_gt_lines = len(pcl_ground_truth)
        if nbr_gt_lines == 0:
            return 0

        association, _ = FtPclHelper.associate_pcl_to_ground_truth(pcl_cem, pcl_ground_truth, association_radius)
        nbr_associated_pcl = len([pcl for pcl, ground_truth in association if ground_truth])

        return nbr_associated_pcl / nbr_gt_lines

    @staticmethod
    def calculate_pmd_false_positive_iso(
        pmd_lines: typing.List[PMDLine], pcl_ground_truth: typing.List[PCLDelimiter], association_radius: float
    ) -> float:
        """Calculate false positive rate for PMD using ISO method."""
        nbr_pmd_lines = len(pmd_lines)
        if nbr_pmd_lines == 0:
            return 0

        association, _ = FtPclHelper.associate_pmd_to_ground_truth(pmd_lines, pcl_ground_truth, association_radius)
        nbr_unassociated_pcl = len([pmd for pmd, ground_truth in association if ground_truth is None])

        return nbr_unassociated_pcl / nbr_pmd_lines

    @staticmethod
    def calculate_pmd_false_positive_utm(
        dgps: DgpsTimeframe,
        pmd_lines: typing.List[PMDLine],
        pcl_ground_truth_utm: typing.List[PCLDelimiter],
        association_radius: float,
    ) -> float:
        """Calculate false positive rate for PMD using UTM method."""
        nbr_pmd_lines = len(pmd_lines)
        if nbr_pmd_lines == 0:
            return 0

        pcl_ground_truth_iso = VehicleCoordinateHelper.pcl_utm_to_vehicle(pcl_ground_truth_utm, dgps)
        return FtPclHelper.calculate_pmd_false_positive_iso(pmd_lines, pcl_ground_truth_iso, association_radius)

    @staticmethod
    def calculate_pmd_true_positive_iso(
        pmd_lines: typing.List[PMDLine], pcl_ground_truth: typing.List[PCLDelimiter], association_radius: float
    ) -> float:
        """Calculate true positive rate for PMD using ISO method."""
        nbr_gt_lines = len(pcl_ground_truth)
        if nbr_gt_lines == 0:
            return 0

        association, _ = FtPclHelper.associate_pmd_to_ground_truth(pmd_lines, pcl_ground_truth, association_radius)
        nbr_associated_pmd = len([pmd for pmd, ground_truth in association if ground_truth is None])

        return nbr_associated_pmd / nbr_gt_lines

    @staticmethod
    def get_PMD_timeframe_index(
        timestamp_before: int, timestamp_after: int, PMDs: typing.List[PMDTimeFrame], start_index: int = 0
    ):
        """Get PMD timeframe index within given timestamps."""
        for index, tf in enumerate(PMDs[start_index:]):
            if tf.timestamp > timestamp_before:
                if index > start_index and timestamp_after < PMDs[index - 1].timestamp:
                    return index - 1
                else:
                    return None

    @staticmethod
    def get_marker_with_associated_input(
        CEM: typing.List[PCLDelimiter], PMD_timeframes: typing.List[PMDTimeFrame], association_radius: float
    ) -> typing.List[PCLDelimiter]:
        """Get marker with associated input within specified association radius."""
        output: typing.List[PCLDelimiter] = []

        for pcl in CEM:
            done = False
            for pmd_timeframe in PMD_timeframes:
                for pmd in pmd_timeframe.pmd_lines:
                    association = FtPclHelper.is_pcl_pmd_association_valid(pcl, pmd, association_radius)
                    if association[0]:
                        output.append(pcl)
                        done = True
                        break
                if done:
                    break
        return output

    # Return a dictionary 1 to 1 where the key is a prev index and the value is a current index
    @staticmethod
    def associate_PCL_list(
        current: typing.List[PCLDelimiter], prev: typing.List[PCLDelimiter], association_radius: float
    ) -> typing.Dict[int, int]:
        """
        Associate PCL lists between current and previous timeframes.

        Args:
            current: List of PCL markers in the current timeframe.
            prev: List of PCL markers in the previous timeframe.
            association_radius: Radius for association.

        Returns:
            Dict[int, int]: Dictionary mapping indices of current markers to indices of associated previous markers.
        """
        association: typing.Dict[int, (int, float)] = {}
        for cur_ixd, cur_marker in enumerate(current):
            for prev_data, prev_marker in enumerate(prev):
                score = FtPclHelper.is_pcl_pcl_association_valid(cur_marker, prev_marker, association_radius)
                if score[0]:
                    if cur_ixd not in association or association[cur_ixd][1] > score[3]:
                        association[cur_ixd] = (prev_data, score[3])

        rev_association = {}
        # Create one to one dictionary
        for cur_index, prev_data in association.items():
            if prev_data[0] not in rev_association:
                rev_association[prev_data[0]] = cur_index
            else:
                score_2 = FtPclHelper.is_pcl_pcl_association_valid(
                    current[cur_index], prev[rev_association[prev_data[0]]], association_radius
                )
                if prev_data[1] < score_2[3]:
                    rev_association[prev_data[0]] = cur_index

        return rev_association

    @staticmethod
    def get_evaluation_ts_ws(ws_data):
        """Get evaluation timestamp for WS data."""
        input_list = [
            ws_data[PMDCamera.FRONT][ws_data[PMDCamera.FRONT]["numberOfLines"] > 0],
            ws_data[PMDCamera.REAR][ws_data[PMDCamera.REAR]["numberOfLines"] > 0],
            ws_data[PMDCamera.LEFT][ws_data[PMDCamera.LEFT]["numberOfLines"] > 0],
            ws_data[PMDCamera.RIGHT][ws_data[PMDCamera.RIGHT]["numberOfLines"] > 0],
        ]

        first_in_ts = min(
            [
                min(input_list[PMDCamera.FRONT]["timestamp"].values),
                min(input_list[PMDCamera.REAR]["timestamp"].values),
                min(input_list[PMDCamera.LEFT]["timestamp"].values),
                min(input_list[PMDCamera.RIGHT]["timestamp"].values),
            ]
        )

        last_in_ts = max(
            [
                max(input_list[PMDCamera.FRONT]["timestamp"].values),
                max(input_list[PMDCamera.REAR]["timestamp"].values),
                max(input_list[PMDCamera.LEFT]["timestamp"].values),
                max(input_list[PMDCamera.RIGHT]["timestamp"].values),
            ]
        )

        delay = ConstantsCem.SYNC_INPUT_OUTPUT_CYCLES * ConstantsCem.CYCLE_PERIOD_TIME_MS
        first_out_ts = first_in_ts + (delay * 1e3)
        last_out_ts = last_in_ts + (delay * 1e3)
        return first_in_ts, first_out_ts, last_in_ts, last_out_ts

    @staticmethod
    def get_pcl_from_json_gt(gt_data):
        """Get PCL from JSON ground truth data."""
        line_gt_output = dict()
        lines_all_ts = gt_data["LinesCem"]

        for _, lines in enumerate(lines_all_ts):

            if lines["SensorSource"] == "CV_COMMON_E_SENSOR_SOURCE_T_NOT_APPLICABLE":
                ts_lines = lines["SignalHeader"]["timestamp"]
                line_gt_output[ts_lines] = list()

                for line in lines["PmdParkingLineList"]:
                    line_out = PCLDelimiter(
                        line["lineId"],
                        2,
                        PCLPoint(line["lineStartXInM"], line["lineStartYInM"]),
                        PCLPoint(line["lineEndXinM"], line["lineEndYinM"]),
                        line["lineConfidence"],
                    )
                    line_gt_output[ts_lines].append(line_out)

        return line_gt_output
