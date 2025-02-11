"""pedestrian crossing helper module for CEM"""

import math
import typing

from pl_parking.PLP.CEM.constants import AssociationConstants
from pl_parking.PLP.CEM.ft_pose_helper import FtPoseHelper
from pl_parking.PLP.CEM.inputs.input_CemPedCrossReader import PedCrossDetection, PedCrossPoint
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import RelativeMotion
from pl_parking.PLP.CEM.inputs.input_PmsdPedCrossReader import PMSDPedCross, PMSDPedCrossPoint, PMSDPedCrossTimeFrame


class FtPedHelper:
    """Helper class for pedestrian crossing operations."""

    @staticmethod
    def distance_point_vehicle(point: PedCrossPoint) -> float:
        """Calculate the distance of a point from the vehicle."""
        return math.sqrt(point.x * point.x + point.y * point.y)

    @staticmethod
    def get_closest_point(ped: PedCrossDetection) -> PedCrossPoint:
        """Get the closest point in a pedestrian crossing to the vehicle."""
        distances = [FtPedHelper.distance_point_vehicle(i) for i in ped.ped_corners]
        index = distances.index(max(distances))
        return ped.ped_corners[index]

    @staticmethod
    def distance_ped_vehicle(self, ped: PedCrossDetection) -> float:
        """Calculate the distance of a pedestrian crossing from the vehicle."""
        return FtPedHelper.distance_point_vehicle(FtPedHelper.get_center_point(self, PedCrossDetection))

    @staticmethod
    def transform_ped(self, ped: PedCrossDetection, relative_motion: RelativeMotion):
        """Transform a pedestrian crossing using relative motion."""
        transformed_corner = [FtPoseHelper.transform_point([s.x, s.y], relative_motion) for s in ped.ped_corners]
        transformed_point = [PedCrossPoint(c[0], c[1]) for c in transformed_corner]
        return PedCrossDetection(ped.Ped_id, transformed_point, ped.scenario_confidence)

    def get_PedCross_timeframe_index(
        self,
        timestamp_before: int,
        timestamp_after: int,
        PEDs: typing.List[PMSDPedCrossTimeFrame],
        start_index: int = 0,
    ):
        """Get the index of a Pedestrian Crossing timeframe."""
        for index, tf in enumerate(PEDs[start_index:]):
            if tf.timestamp > timestamp_before:
                if index > start_index and timestamp_after < PEDs[index - 1].timestamp:
                    return index - 1
                else:
                    return None

    def get_peds_with_associated_input(
        self, CEM: typing.List[PedCrossDetection], PedCross_timeframes: typing.List[PMSDPedCrossTimeFrame]
    ) -> typing.List[PedCrossDetection]:
        """Get pedestrian crossings associated with input Pedestrian Crossings."""
        output: typing.List[PedCrossDetection] = []

        for ped_timeframe in PedCross_timeframes:
            for pmsd_ped in ped_timeframe.pedestrian_crossing_detection:
                FtPedHelper.order_points_counter_clockwise(self, pmsd_ped)

        for ped in CEM:
            FtPedHelper.order_points_counter_clockwise(self, ped)
            done = False
            for ped_timeframe in PedCross_timeframes:
                for pmsd_ped in ped_timeframe.pedestrian_crossing_detection:
                    distance = FtPedHelper.get_ped_distance(self, pmsd_ped, ped)
                    if distance < AssociationConstants.PED_ASSOCIATION_RADIUS:
                        output.append(ped)
                        done = True
                        break
                if done:
                    break
        return output

    def get_center_point(self, ped: typing.Union[PedCrossDetection, PMSDPedCross]) -> PedCrossPoint:
        """Calculate the center point of a pedestrian crossing."""
        return PedCrossPoint(
            sum([corner.x for corner in ped.ped_corners]) / 4, sum([corner.y for corner in ped.ped_corners]) / 4
        )

    @staticmethod
    def get_point_distance(
        self, p1: typing.Union[PedCrossPoint, PMSDPedCrossPoint], p2: typing.Union[PedCrossPoint, PMSDPedCrossPoint]
    ):
        """Calculate the distance between two points."""
        xd = p1.x - p2.x
        yd = p1.y - p2.y
        return math.sqrt(xd * xd + yd * yd)

    def get_ped_distance(self, ped: typing.Union[PedCrossDetection, PMSDPedCross], gt: PedCrossDetection):
        """
        Calculate the distance between a measured pedestrian crossing and a ground truth pedestrian crossing.

        Args:
            pedestrian crossing (Union[PedCrossDetection, PMSDPedCrossing]): The measured pedestrian crossing.
            gt (PedCrossingDetection): The ground truth pedestrian crossing.

        Returns:
            float: The distance between the measured pedestrian crossing and the ground truth pedestrian crossing.
        """
        gt_center = FtPedHelper.get_center_point(self, gt)
        ped_center = FtPedHelper.get_center_point(self, ped)
        distance = FtPedHelper.get_point_distance(self, gt_center, ped_center)
        for i in range(4):
            distance += FtPedHelper.get_point_distance(self, ped.ped_corners[i], gt.ped_corners[i])

        return distance / 5

    @staticmethod
    def order_points_counter_clockwise(self, ped: typing.Union[PedCrossDetection, PMSDPedCross]) -> None:
        """Order the corner points of a pedestrian crossing counter-clockwise."""
        center = FtPedHelper.get_center_point(self, ped)
        # center = self.get_center_point(self, ped)
        ped.ped_corners.sort(key=lambda p: math.atan2(p.x - center.x, p.y - center.y), reverse=True)

    def associate_ped_list(
        self, current: typing.List[PedCrossDetection], prev: typing.List[PedCrossDetection]
    ) -> typing.Dict[int, int]:
        """Associate pedestrian crossings between current and previous timeframes."""
        for prev_ped in prev:

            FtPedHelper.order_points_counter_clockwise(self, prev_ped)
        association = {}
        for cur_ixd, cur_ped in enumerate(current):
            FtPedHelper.order_points_counter_clockwise(self, cur_ped)
            for prev_ixd, prev_ped in enumerate(prev):
                distance = FtPedHelper.get_ped_distance(self, cur_ped, prev_ped)
                if distance < AssociationConstants.MAX_SLOT_DISTANCE:
                    if (
                        cur_ixd not in association
                        or FtPedHelper.get_ped_distance(self, prev[association[cur_ixd]], cur_ped) > distance
                    ):
                        association[cur_ixd] = prev_ixd

        rev_association = {}

        for cur_index, prev_ixd in association.items():
            if prev_ixd not in rev_association:
                rev_association[prev_ixd] = cur_index
            else:
                distance_1 = FtPedHelper.get_ped_distance(self, prev[prev_ixd], current[cur_index])
                distance_2 = FtPedHelper.get_ped_distance(self, prev[prev_ixd], current[rev_association[prev_ixd]])
                if distance_1 < distance_2:
                    rev_association[prev_ixd] = cur_index

        return rev_association
