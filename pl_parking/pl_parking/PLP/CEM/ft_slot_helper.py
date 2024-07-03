"""slot helper module for CEM"""

import math
import sys
import typing

from pl_parking.PLP.CEM.constants import AssociationConstants
from pl_parking.PLP.CEM.ft_pose_helper import FtPoseHelper
from pl_parking.PLP.CEM.inputs.input_CemSlotReader import Slot, SlotPoint, SlotTimeFrame
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import RelativeMotion
from pl_parking.PLP.CEM.inputs.input_PsdSlotReader import PSDSlot, PSDSlotPoint, PSDTimeFrame


class FtSlotHelper:
    """Helper class for slot operations."""

    @staticmethod
    def distance_point_vehicle(point: SlotPoint) -> float:
        """Calculate the distance of a point from the vehicle."""
        return math.sqrt(point.x * point.x + point.y * point.y)

    @staticmethod
    def get_closest_point(slot: Slot) -> SlotPoint:
        """Get the closest point in a slot to the vehicle."""
        distances = [FtSlotHelper.distance_point_vehicle(i) for i in slot.slot_corners]
        index = distances.index(max(distances))
        return slot.slot_corners[index]

    @staticmethod
    def distance_slot_vehicle(slot: Slot) -> float:
        """Calculate the distance of a slot from the vehicle."""
        return FtSlotHelper.distance_point_vehicle(FtSlotHelper.get_center_point(Slot))

    @staticmethod
    def find_missing_slot_ids(prevTimeframe: SlotTimeFrame, curTimeframe: SlotTimeFrame) -> typing.List[SlotTimeFrame]:
        """Find missing slot IDs between two timeframes."""
        curIds = set()

        for slot in curTimeframe.parking_slots:
            curIds.add(slot.slot_id)
        ret = []
        for slot in prevTimeframe.parking_slots:
            if slot.slot_id not in curIds:
                ret.append(slot)

        return ret

    @staticmethod
    def get_closest_slot(slots: typing.List[Slot]) -> typing.Tuple[Slot, float]:
        """Get the closest slot,based on a minimum distance, from a list of slots."""
        min_distance = sys.float_info.max
        closest_slot = None

        for slot in slots:
            dist = FtSlotHelper.distance_slot_vehicle(slot)
            if dist < min_distance:
                dist = min_distance
                closest_slot = slot

        return closest_slot, min_distance

    @staticmethod
    def get_furthest_slot(slots: typing.List[Slot]) -> typing.Tuple[Slot, float]:
        """Get the furthest slot,based on a maximum distance, from a list of slots."""
        maxDistance = sys.float_info.min
        furthest_slot = None

        for slot in slots:
            dist = FtSlotHelper.distance_slot_vehicle(slot)
            if dist > maxDistance:
                dist = maxDistance
                furthest_slot = slot

        return furthest_slot, maxDistance

    @staticmethod
    def transform_slot(slot: Slot, relative_motion: RelativeMotion):
        """Transform a slot using relative motion."""
        transformed_corner = [FtPoseHelper.transform_point([s.x, s.y], relative_motion) for s in slot.slot_corners]
        transformed_point = [SlotPoint(c[0], c[1]) for c in transformed_corner]
        return Slot(slot.slot_id, slot.existence_probability, transformed_point, slot.scenario_confidence)

    @staticmethod
    def calculate_scenario_confidence_correctness(
        measurements: typing.List[typing.Union[Slot, PSDSlot]], ground_truth: typing.List[Slot]
    ) -> typing.Tuple[float, int]:
        """Calculate the correctness of scenario confidence."""
        sum_confidence = 0.0
        association = FtSlotHelper.associate_slot_ground_truth(measurements, ground_truth)
        for gt_num, slot_num in association.items():
            conf = FtSlotHelper.calculate_pair_scenario_confidence(measurements[slot_num], ground_truth[gt_num])
            if conf[1]:
                sum_confidence += conf[0]

        return sum_confidence, len(association)

    @staticmethod
    def calculate_accuracy_correctness(
        measurements: typing.List[typing.Union[Slot, PSDSlot]], ground_truth: typing.List[Slot]
    ) -> typing.Tuple[float, int]:
        """
        Calculate the correctness of accuracy.

        Args:
            measurements (List[Union[Slot, PSDSlot]]): The list of measured slots.
            ground_truth (List[Slot]): The list of ground truth slots.

        Returns:
            Tuple[float, int]: A tuple containing the sum of confidence values and the number of associations.
        """
        sum_confidence = 0.0
        association = FtSlotHelper.associate_slot_ground_truth(measurements, ground_truth)
        for gt_num, slot_num in association.items():
            sum_confidence += FtSlotHelper.get_slot_distance(measurements[slot_num], ground_truth[gt_num])

        return sum_confidence, len(association)

    # slots should be in the same coordinate systems
    @staticmethod
    def associate_slot_ground_truth(
        measurements: typing.List[typing.Union[Slot, PSDSlot]], ground_truth: typing.List[Slot]
    ) -> typing.Dict[int, int]:
        """
        Associate measured slots with ground truth slots.

        Args:
            measurements (List[Union[Slot, PSDSlot]]): The list of measured slots.
            ground_truth (List[Slot]): The list of ground truth slots.

        Returns:
            Dict[int, int]: A dictionary where the keys are indices of ground truth slots and values are indices of associated measured slots.
        """
        association = {}

        for gt_ixd, gt in enumerate(ground_truth):
            FtSlotHelper.order_points_counter_clockwise(gt)
            for slot_ixd, slot in enumerate(measurements):
                FtSlotHelper.order_points_counter_clockwise(slot)
                distance = FtSlotHelper.get_slot_distance(slot, gt)
                if distance < AssociationConstants.MAX_SLOT_DISTANCE:
                    if (
                        gt_ixd not in association
                        or FtSlotHelper.get_slot_distance(measurements[association[gt_ixd]], gt) > distance
                    ):
                        association[gt_ixd] = slot_ixd

        return association

    # Slot corners need to be ordered the in same way
    @staticmethod
    def get_slot_distance(slot: typing.Union[Slot, PSDSlot], gt: Slot):
        """
        Calculate the distance between a measured slot and a ground truth slot.

        Args:
            slot (Union[Slot, PSDSlot]): The measured slot.
            gt (Slot): The ground truth slot.

        Returns:
            float: The distance between the measured slot and the ground truth slot.
        """
        gt_center = FtSlotHelper.get_center_point(gt)
        slot_center = FtSlotHelper.get_center_point(slot)
        distance = FtSlotHelper.get_point_distance(gt_center, slot_center)
        for i in range(4):
            distance += FtSlotHelper.get_point_distance(slot.slot_corners[i], gt.slot_corners[i])

        return distance / 5

    @staticmethod
    def order_points_counter_clockwise(slot: typing.Union[Slot, PSDSlot]) -> None:
        """Order the corner points of a slot counter-clockwise."""
        center = FtSlotHelper.get_center_point(slot)
        slot.slot_corners.sort(key=lambda p: math.atan2(p.x - center.x, p.y - center.y), reverse=True)

    @staticmethod
    def get_center_point(slot: typing.Union[Slot, PSDSlot]) -> SlotPoint:
        """Calculate the center point of a slot."""
        return SlotPoint(
            sum([corner.x for corner in slot.slot_corners]) / 4, sum([corner.y for corner in slot.slot_corners]) / 4
        )

    @staticmethod
    def get_point_distance(p1: typing.Union[SlotPoint, PSDSlotPoint], p2: typing.Union[SlotPoint, PSDSlotPoint]):
        """Calculate the distance between two points."""
        xd = p1.x - p2.x
        yd = p1.y - p2.y
        return math.sqrt(xd * xd + yd * yd)

    @staticmethod
    def calculate_pair_scenario_confidence(slot: typing.Union[Slot, PSDSlot], gt: Slot) -> typing.Tuple[float, bool]:
        """Calculate the scenario confidence for a pair of slots."""
        if (
            gt.scenario_confidence.angled > 0
            or gt.scenario_confidence.parallel > 0.0
            or gt.scenario_confidence.perpendicular > 0.0
        ):
            confidence = (
                gt.scenario_confidence.angled * slot.scenario_confidence.angled
                + gt.scenario_confidence.parallel * slot.scenario_confidence.parallel
                + gt.scenario_confidence.perpendicular * slot.scenario_confidence.perpendicular
            )
            confidence /= 10000
            return confidence, True
        else:
            return 0, False

    @staticmethod
    def get_PSD_timeframe_index(
        timestamp_before: int, timestamp_after: int, PSDs: typing.List[PSDTimeFrame], start_index: int = 0
    ):
        """Get the index of a PSD timeframe."""
        for index, tf in enumerate(PSDs[start_index:]):
            if tf.timestamp > timestamp_before:
                if index > start_index and timestamp_after < PSDs[index - 1].timestamp:
                    return index - 1
                else:
                    return None

    @staticmethod
    def get_solts_with_associated_input(
        CEM: typing.List[Slot], PSD_timeframes: typing.List[PSDTimeFrame]
    ) -> typing.List[Slot]:
        """Get slots associated with input PSDs."""
        output: typing.List[Slot] = []

        for psd_timeframe in PSD_timeframes:
            for psd_slot in psd_timeframe.parking_slots:
                FtSlotHelper.order_points_counter_clockwise(psd_slot)

        for slot in CEM:
            FtSlotHelper.order_points_counter_clockwise(slot)
            done = False
            for psd_timeframe in PSD_timeframes:
                for psd_slot in psd_timeframe.parking_slots:
                    distance = FtSlotHelper.get_slot_distance(psd_slot, slot)
                    if distance < AssociationConstants.MAX_SLOT_DISTANCE:
                        output.append(slot)
                        done = True
                        break
                if done:
                    break
        return output

    # Return a dictionary 1 to 1 where the key is a prev index and the value is a current index
    @staticmethod
    def associate_slot_list(current: typing.List[Slot], prev: typing.List[Slot]) -> typing.Dict[int, int]:
        """Associate slots between current and previous timeframes."""
        for prev_slot in prev:
            FtSlotHelper.order_points_counter_clockwise(prev_slot)
        association = {}
        for cur_ixd, cur_slot in enumerate(current):
            FtSlotHelper.order_points_counter_clockwise(cur_slot)
            for prev_ixd, prev_slot in enumerate(prev):
                distance = FtSlotHelper.get_slot_distance(cur_slot, prev_slot)
                if distance < AssociationConstants.MAX_SLOT_DISTANCE:
                    if (
                        cur_ixd not in association
                        or FtSlotHelper.get_slot_distance(prev[association[cur_ixd]], cur_slot) > distance
                    ):
                        association[cur_ixd] = prev_ixd

        rev_association = {}

        for cur_index, prev_ixd in association.items():
            if prev_ixd not in rev_association:
                rev_association[prev_ixd] = cur_index
            else:
                distance_1 = FtSlotHelper.get_slot_distance(prev[prev_ixd], current[cur_index])
                distance_2 = FtSlotHelper.get_slot_distance(prev[prev_ixd], current[rev_association[prev_ixd]])
                if distance_1 < distance_2:
                    rev_association[prev_ixd] = cur_index

        return rev_association
