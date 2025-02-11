"""slot helper module for CEM"""

import math
import sys
import typing

from pl_parking.PLP.CEM.constants import AssociationConstants, CemSlotScenario
from pl_parking.PLP.CEM.ft_pose_helper import FtPoseHelper
from pl_parking.PLP.CEM.ground_truth.vehicle_coordinates_helper import VehicleCoordinateHelper
from pl_parking.PLP.CEM.inputs.input_CemSlotReader import Slot, SlotPoint, SlotScenarioConfidences, SlotTimeFrame
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import RelativeMotion, VedodoTimeframe
from pl_parking.PLP.CEM.inputs.input_PmdSlotReader import PMDSlot, PMDSlotPoint, PMDTimeFrame


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
        return Slot(
            slot.slot_timestamp, slot.slot_id, slot.existence_probability, transformed_point, slot.scenario_confidence
        )

    @staticmethod
    def calculate_scenario_confidence_correctness(
        measurements: typing.List[typing.Union[Slot, PMDSlot]], ground_truth: typing.List[Slot]
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
        measurements: typing.List[typing.Union[Slot, PMDSlot]], ground_truth: typing.List[Slot]
    ) -> typing.Tuple[float, int]:
        """
        Calculate the correctness of accuracy.

        Args:
            measurements (List[Union[Slot, PMDSlot]]): The list of measured slots.
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
        measurements: typing.List[typing.Union[Slot, PMDSlot]], ground_truth: typing.List[Slot]
    ) -> typing.Dict[int, int]:
        """
        Associate measured slots with ground truth slots.

        Args:
            measurements (List[Union[Slot, PMDSlot]]): The list of measured slots.
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
                if distance < AssociationConstants.MAX_SLOT_DISTANCE_ERG_KPI:
                    if (
                        gt_ixd not in association
                        or FtSlotHelper.get_slot_distance(measurements[association[gt_ixd]], gt) > distance
                    ):
                        association[gt_ixd] = slot_ixd

        return association

    # Slot corners need to be ordered the in same way
    @staticmethod
    def get_slot_distance(slot: typing.Union[Slot, PMDSlot], gt: Slot):
        """
        Calculate the distance between a measured slot and a ground truth slot.

        Args:
            slot (Union[Slot, PMDSlot]): The measured slot.
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
    def order_points_counter_clockwise(slot: typing.Union[Slot, PMDSlot]) -> None:
        """Order the corner points of a slot counter-clockwise."""
        center = FtSlotHelper.get_center_point(slot)
        slot.slot_corners.sort(key=lambda p: math.atan2(p.x - center.x, p.y - center.y), reverse=True)

    @staticmethod
    def get_center_point(slot: typing.Union[Slot, PMDSlot]) -> SlotPoint:
        """Calculate the center point of a slot."""
        return SlotPoint(
            sum([corner.x for corner in slot.slot_corners]) / 4, sum([corner.y for corner in slot.slot_corners]) / 4
        )

    @staticmethod
    def get_point_distance(p1: typing.Union[SlotPoint, PMDSlotPoint], p2: typing.Union[SlotPoint, PMDSlotPoint]):
        """Calculate the distance between two points."""
        xd = p1.x - p2.x
        yd = p1.y - p2.y
        return math.sqrt(xd * xd + yd * yd)

    @staticmethod
    def calculate_pair_scenario_confidence(slot: typing.Union[Slot, PMDSlot], gt: Slot) -> typing.Tuple[float, bool]:
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
        timestamp_before: int, timestamp_after: int, PSDs: typing.List[PMDTimeFrame], start_index: int = 0
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
        CEM: typing.List[Slot], PSD_timeframes: typing.List[PMDTimeFrame]
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
        """Associate slots between current and previous timeframes.
        Returns: GT slots paired to detected slots
             # if return value is {1,0}, then GT slot[1] is paired to Detected slot[0]
        """
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

    @staticmethod
    def scenario_to_vehicle_coord(point_x, point_y, ego_pose_x, ego_pose_y, heading_rad):
        """
        :param point_x: x location (in utm coordinate)
        :param point_y: y location (in utm coordinate)
        :param ego_pose_x: x vehicle location (in utm coordinate)
        :param ego_pose_y: y vehicle location (in utm coordinate)
        :param heading_rad: vehicle orientation from north axis in radian (clockwise)
        :return: vehicle_coord_point_x and vehicle_coord_point_y that are ground truth points in vehicle coordinates
        """
        rotated_vehicle_coord_x = point_x - ego_pose_x
        rotated_vehicle_coord_y = point_y - ego_pose_y

        cos_heading_from_north = math.cos(heading_rad)
        sin_heading_from_north = math.sin(heading_rad)

        vehicle_coord_point_x = (
            cos_heading_from_north * rotated_vehicle_coord_x + sin_heading_from_north * rotated_vehicle_coord_y
        )
        vehicle_coord_point_y = (
            -sin_heading_from_north * rotated_vehicle_coord_x + cos_heading_from_north * rotated_vehicle_coord_y
        )

        return vehicle_coord_point_x, vehicle_coord_point_y

    @staticmethod
    def slot_to_vehicle(slot_gt: typing.List[Slot], ego_pos: VedodoTimeframe) -> typing.List[Slot]:
        """Converts slot ground truth points from UTM to vehicle coordinates."""
        out: typing.List[Slot] = []

        for slot in slot_gt:
            ok = False
            vertices_vehicle: typing.List[SlotPoint] = []

            for vertex in slot.slot_corners:
                vertex_vehicle = FtSlotHelper.scenario_to_vehicle_coord(
                    vertex.x, vertex.y, ego_pos.x, ego_pos.y, ego_pos.yaw
                )

                ok |= VehicleCoordinateHelper.is_point_relevent(vertex_vehicle[0], vertex_vehicle[1])
                vertices_vehicle.append(SlotPoint(vertex_vehicle[0], vertex_vehicle[1]))

            if ok:
                slot_vehicle = Slot(
                    slot.slot_id, slot.existence_probability, vertices_vehicle, slot.scenario_confidence
                )
                out.append(slot_vehicle)

        return out

    @staticmethod
    def get_slot_from_json_gt(gt_data):
        """Get PCL from JSON ground truth data."""
        slot_gt_output = dict()
        slots_all_ts = gt_data["PfsParkingSlots"]

        for _, slots in enumerate(slots_all_ts):
            ts_slots = slots["sSigHeader"]["uiTimeStamp"]
            slot_gt_output[ts_slots] = list()

            for slot in slots["parkingSlots"]:
                corners = []
                for k in range(4):
                    p = SlotPoint(float(slot["slotCorners"][k]["x"]), float(slot["slotCorners"][k]["y"]))
                    corners.append(p)

                slot_out = Slot(
                    ts_slots,
                    float(slot["slotId"]),
                    float(slot["existenceProbability"]),
                    corners,
                    SlotScenarioConfidences(
                        slot["parkingScenarioConfidence"]["angled"],
                        slot["parkingScenarioConfidence"]["parallel"],
                        slot["parkingScenarioConfidence"]["perpendicular"],
                    ),
                )

                slot_gt_output[ts_slots].append(slot_out)

        return slot_gt_output

    @staticmethod
    def get_slot_scenario(slot: typing.Union[Slot, PMDSlot]):
        """
        Adjust the slot corner point list by rotation.
        The list is correct when the corner distance is minimal between the detected and the gt slot
        """
        if (
            slot.scenario_confidence.angled >= slot.scenario_confidence.parallel
            and slot.scenario_confidence.angled >= slot.scenario_confidence.perpendicular
        ):
            return CemSlotScenario.SLOT_SCENARIO_ANGLED
        if (
            slot.scenario_confidence.parallel >= slot.scenario_confidence.angled
            and slot.scenario_confidence.parallel >= slot.scenario_confidence.perpendicular
        ):
            return CemSlotScenario.SLOT_SCENARIO_PARALLEL
        if (
            slot.scenario_confidence.perpendicular >= slot.scenario_confidence.angled
            and slot.scenario_confidence.perpendicular >= slot.scenario_confidence.parallel
        ):
            return CemSlotScenario.SLOT_SCENARIO_PERPENDICULAR
