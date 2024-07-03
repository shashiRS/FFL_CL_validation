"""PMSD Association"""

from dataclasses import dataclass
from enum import IntEnum

import numpy as np
from scipy.spatial.transform import Rotation as Rot

from pl_parking.PLP.CEM.inputs.input_CemPclReader import PCLDelimiter
from pl_parking.PLP.CEM.inputs.input_PmdReader import PMDLine
from pl_parking.PLP.CV.PMSD.gps_utils import GPS_utils as Gps


@dataclass
class VehiclePoint:
    """Vehicle point"""

    x: float
    y: float

    def __iter__(self):
        yield from (self.x, self.y)

    def __sub__(self, other: "VehiclePoint"):
        return np.array((self.x - other.x, self.y - other.y))


@dataclass
class VehicleLine:
    """Vehicle line"""

    start: VehiclePoint
    end: VehiclePoint

    @classmethod
    def from_cem_pcl(cls, pcl: PCLDelimiter):
        """Transform pcl to vehicle line"""
        return VehicleLine(
            VehiclePoint(pcl.start_point.x, pcl.start_point.y), VehiclePoint(pcl.end_point.x, pcl.end_point.y)
        )

    @classmethod
    def from_cem_pmd(cls, pmd: PMDLine):
        """Transform pmd to vehicle line"""
        return VehicleLine(
            VehiclePoint(pmd.line_start.x, pmd.line_start.y), VehiclePoint(pmd.line_end.x, pmd.line_end.y)
        )

    def len2(self):
        """Square length"""
        return np.sum((self.end - self.start) ** 2)

    @staticmethod
    def segment_point_distance(A, B, P):
        """Segment line AB, point P, where each one is an array([x, y])"""
        if all(A == P) or all(B == P):
            return 0
        if np.arccos(np.dot((P - A) / np.linalg.norm(P - A), (B - A) / np.linalg.norm(B - A))) > np.pi / 2:
            return np.linalg.norm(P - A)
        if np.arccos(np.dot((P - B) / np.linalg.norm(P - B), (A - B) / np.linalg.norm(A - B))) > np.pi / 2:
            return np.linalg.norm(P - B)
        return np.linalg.norm(np.cross(A - B, A - P)) / np.linalg.norm(B - A)

    def swap_line_end_points(self, gt_line: "VehicleLine"):
        """Swap line end points"""

        def sqr_len(x):
            return np.sum(x**2)

        if sqr_len(gt_line.start - self.start) + sqr_len(gt_line.end - self.end) > sqr_len(
            gt_line.start - self.end
        ) + sqr_len(gt_line.end - self.start):
            gt_line.start, gt_line.end = gt_line.end, gt_line.start

    def hangout_distance_line(self, gt_line: "VehicleLine") -> tuple[float, float]:
        """Calculate hangout distance of line"""
        self.swap_line_end_points(gt_line)
        return gt_line.hangout_distance_point(self.start), gt_line.hangout_distance_point(self.end)

    def hangout_distance_point(self, other: VehiclePoint) -> float:
        """Calculate hangout distance of point"""
        intersect = self.intersection_perpendicular_point(other)
        is_projected = self.is_point_inside(intersect)
        distance = (
            np.linalg.norm(intersect - other)
            if is_projected
            else min(np.linalg.norm(self.start - other), np.linalg.norm(self.end - other))
        )
        return distance

    def simple_endpoint_distance_line(self, gt_line: "VehicleLine") -> float:
        """Calculate endpoint distance from gt line"""
        self.swap_line_end_points(gt_line)
        return (gt_line.simple_distance_endpoint(self.start) + gt_line.simple_distance_endpoint(self.end)) / 2

    def simple_distance_endpoint(self, other: VehiclePoint) -> float:
        """Calculate endpoint distance from gt endpoint"""
        distance = min(np.linalg.norm(self.start - other), np.linalg.norm(self.end - other))
        return distance

    def __abs__(self) -> float:
        return np.linalg.norm(self.start - self.end)

    def is_point_inside(self, other: VehiclePoint) -> bool:
        """Is point inside"""
        sqr_length = np.sum((self.start - self.end) ** 2)
        sqr_len_point_to_start = np.sum((other - self.start) ** 2)
        sqr_len_point_to_end = np.sum((other - self.end) ** 2)

        return sqr_length >= sqr_len_point_to_start + sqr_len_point_to_end

    def intersection_perpendicular_point(self, other: VehiclePoint) -> VehiclePoint:
        """Intersection perpendicular point"""
        unit_segment = (self.end - self.start) / abs(self)
        intersect = unit_segment * unit_segment.dot(other - self.start)
        return VehiclePoint(self.start.x + intersect[0], self.start.y + intersect[1])

    def seg_intersect(self, other: "VehicleLine") -> np.ndarray:
        """Segment intersection"""
        da = self.end - self.start
        db = other.end - other.start
        dp = self.start - other.start
        dap = np.array([-da[1], da[0]])
        return (np.dot(dap, dp) / np.dot(dap, db).astype(float)) * db + np.array((*other.start,))

    def angle(self, other: "VehicleLine") -> float:
        """Angle of lines"""
        v1 = self.start - self.end
        v2 = other.start - other.end
        cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        angle = np.arccos(cos_theta) * 180 / np.pi
        return angle if angle < 90.0 else 180 - angle


@dataclass
class LineBoundary:
    """Rectangle boundary around line"""

    corners: tuple[VehiclePoint, ...]  # must be rectangle

    @classmethod
    def for_line(cls, line: VehicleLine) -> "LineBoundary":
        """Get boundary for line"""
        boundary_radius = 0.5  # in meter unit

        dir_vec = line.start - line.end
        dir_vec = dir_vec / np.linalg.norm(dir_vec)
        norm_vec = np.array((-dir_vec[1], dir_vec[0]))
        dir_vec, norm_vec = dir_vec * boundary_radius, norm_vec * boundary_radius
        corners = []
        corners.append(VehiclePoint(*(np.array((*line.start,)) + dir_vec - norm_vec)))
        corners.append(VehiclePoint(*(np.array((*line.start,)) + dir_vec + norm_vec)))
        corners.append(VehiclePoint(*(np.array((*line.end,)) - dir_vec + norm_vec)))
        corners.append(VehiclePoint(*(np.array((*line.end,)) - dir_vec - norm_vec)))

        return LineBoundary(tuple(corners))

    def point_in(self, point: VehiclePoint) -> bool:
        """Is point inside boundary"""
        # works for rectangle(corners[0:3]) only
        p_c0 = point - self.corners[0]
        c1_c0 = self.corners[1] - self.corners[0]
        c3_c0 = self.corners[3] - self.corners[0]
        return (0 < p_c0 @ c1_c0 < c1_c0 @ c1_c0) and (0 < p_c0 @ c3_c0 < c3_c0 @ c3_c0)

    def line_crossing(self, line: VehicleLine) -> bool:
        """Is the line crossing the boundary"""
        for start, end in zip(self.corners[0:3], self.corners[1:4]):
            boundary_line = VehicleLine(start, end)
            intersect = VehiclePoint(*boundary_line.seg_intersect(line))
            if boundary_line.is_point_inside(intersect) and line.is_point_inside(intersect):
                return True
        return False

    def false_positive(self, line: VehicleLine):
        """False positive rate"""
        return not (self.line_crossing(line) or self.point_in(line.start) or self.point_in(line.end))

    def true_positive(self, line: VehicleLine):
        """True positive rate"""
        return self.line_crossing(line) or self.point_in(line.start) or self.point_in(line.end)


@dataclass
class GeoPoint:
    """Geo point"""

    lat: float
    lon: float
    height: float

    def __init__(self, latitude: float, longitude: float, altitude: float) -> None:
        self.lat = latitude
        self.lon = longitude
        self.height = altitude


@dataclass
class GtLine:
    """Ground truth line"""

    start: GeoPoint
    end: GeoPoint

    def to_vehicle(self, gps: Gps, yaw: float) -> VehicleLine:
        """Transform to vehicle coordinates"""
        # 90 degrees to face East instead of North
        rot_mat = Rot.from_euler("z", (yaw + 90) * np.pi / 180.0).as_matrix()

        h_xy = np.array((*gps.geo2enu(**self.start.__dict__)[:2].A.ravel().tolist(), 1)) @ rot_mat
        start = VehiclePoint(*h_xy[:2])

        h_xy = np.array((*gps.geo2enu(**self.end.__dict__)[:2].A.ravel().tolist(), 1)) @ rot_mat
        end = VehiclePoint(*h_xy[:2])

        return VehicleLine(start, end)


class Association:
    """Park marker association"""

    class AlgoType(IntEnum):
        """Enumerates the different types of association algorithms"""

        ALGO_HANGOUT_ANGLE = 0  # association by hang-out and angle combination
        ALGO_RECTANGLE = 1  # association by rectangle neighbour

    @staticmethod
    def true_positive(trans_gt_line: VehicleLine, trans_pred_line: VehicleLine) -> bool:
        """True positive rate"""
        boundary = LineBoundary.for_line(trans_gt_line)

        return boundary.true_positive(trans_pred_line)

    @staticmethod
    def simple_match(
        gt_lines: list[VehicleLine], detected_lines: list[VehicleLine]
    ) -> list[tuple[VehicleLine, VehicleLine, bool]]:
        """Simple match"""
        result: list[tuple[VehicleLine, VehicleLine, bool]] = []

        for line in detected_lines:
            # not_matched_gt_lines = filter(lambda x: not any(x is gt for pre, gt, _ in result), gt_lines)
            gt_line_candidate = min(gt_lines, key=line.hangout_distance_line)
            result.append((line, gt_line_candidate, Association.true_positive(gt_line_candidate, line)))

        return result

    @staticmethod
    def hangout_match(
        gt_lines: list[VehicleLine], detected_lines: list[VehicleLine], hangout_threshold: float
    ) -> list[tuple[VehicleLine, VehicleLine, bool]]:
        """Hangout match"""
        result: list[tuple[VehicleLine, VehicleLine, bool]] = []

        for line in detected_lines:
            gt_line_candidate = min(gt_lines, key=line.hangout_distance_line)
            dist = line.hangout_distance_line(gt_line_candidate)
            result.append((line, gt_line_candidate, (dist[0] + dist[1]) / 2 <= hangout_threshold))

        return result

    MatchType = tuple[bool, float, float, float]

    @staticmethod
    def hangout_and_angle_match(
        gt_line: VehicleLine, detected_line: VehicleLine, *, hangout_threshold: float, angle_threshold: float
    ) -> MatchType:
        """Hangout and angle match"""
        dist = detected_line.hangout_distance_line(gt_line)
        dist_avg = (dist[0] + dist[1]) / 2
        return (
            dist_avg <= hangout_threshold and detected_line.angle(gt_line) <= angle_threshold,
            dist[0],
            dist[1],
            dist_avg,
        )

    @staticmethod
    def rectangle_match(gt_line: VehicleLine, detected_line: VehicleLine) -> MatchType:
        """Rectangle match"""
        endpoint_distances = detected_line.hangout_distance_line(gt_line)
        return (
            Association.true_positive(gt_line, detected_line),
            endpoint_distances[0],
            endpoint_distances[1],
            (endpoint_distances[0] + endpoint_distances[1]) / 2,
        )

    @staticmethod
    def match(
        gt_line: VehicleLine,
        detected_line: VehicleLine,
        algo: AlgoType = AlgoType.ALGO_HANGOUT_ANGLE,
        *,
        hangout_threshold=0.6,
        angle_threshold=4.0,
    ) -> MatchType:
        """More complex match"""
        if gt_line.len2() <= 0.01:
            return False, 0, 0, 0
        if algo == Association.AlgoType.ALGO_HANGOUT_ANGLE:
            return Association.hangout_and_angle_match(
                gt_line, detected_line, hangout_threshold=hangout_threshold, angle_threshold=angle_threshold
            )
        elif algo == Association.AlgoType.ALGO_RECTANGLE:
            return Association.rectangle_match(gt_line, detected_line)
        else:
            return False, 0, 0, 0
