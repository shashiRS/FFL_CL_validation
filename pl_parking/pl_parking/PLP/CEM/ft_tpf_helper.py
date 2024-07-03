"""TPF helper module for CEM"""

import math
import sys
import typing

import numpy as np
import pandas as pd
from shapely import geometry

from pl_parking.PLP.CEM.constants import ConstantsCem, TpfFovConstatns
from pl_parking.PLP.CEM.ft_pose_helper import FtPoseHelper
from pl_parking.PLP.CEM.inputs.input_CemTpfReader import DynamicObject, DynPoint, TPFTimeFrame
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import RelativeMotion, VedodoBuffer
from pl_parking.PLP.CEM.inputs.input_DynamicObjectDetection import (
    DynamicObjectCamera,
    DynamicObjectDetection,
    DynamicObjectDetectionTimeframe,
)


class FtTPFHelper:
    """Helper class for processing TPF data."""

    def __init__(self, parent):
        """Initialize object attributes."""
        self.parent = parent

    @staticmethod
    def is_current_associated_to_prev(
        current: DynamicObject, previous: DynamicObject, timestampDiff: int, relative_motion: RelativeMotion
    ) -> bool:
        """Check if the current dynamic object is associated with the previous one."""
        output = True
        if not (
            (current.lifetime - previous.lifetime) == math.floor(timestampDiff / 1000)
            or (current.lifetime - previous.lifetime) == math.ceil(timestampDiff / 1000)
        ):
            output = False

        transformed_point = FtPoseHelper.transform_point([previous.center_x, previous.center_y], relative_motion)
        transformed_velocity = FtPoseHelper.transform_vector(
            [previous.velocity_x, previous.velocity_y], relative_motion
        )
        transformed_variance = FtPoseHelper.transform_vector(
            [previous.velocity_std_x, previous.velocity_std_y], relative_motion
        )

        max_x_diff = (transformed_velocity[0] + transformed_variance[0] * 3) * timestampDiff * 1e-6
        min_x_diff = (transformed_velocity[0] - transformed_variance[0] * 3) * timestampDiff * 1e-6

        max_y_diff = (transformed_velocity[1] + transformed_variance[1] * 3) * timestampDiff * 1e-6
        min_y_diff = (transformed_velocity[1] - transformed_variance[1] * 3) * timestampDiff * 1e-6

        if current.center_x - transformed_point[0] > max_x_diff or min_x_diff > current.center_x - transformed_point[0]:
            output = False
        if current.center_y - transformed_point[1] > max_y_diff or min_y_diff > current.center_y - transformed_point[1]:
            output = False

        return output

    @staticmethod
    def check_if_object_in_timeframe(object: DynamicObject, timeframe: TPFTimeFrame) -> bool:
        """Check if the dynamic object is within the specified time frame."""
        output = False
        for other in timeframe.dynamic_objects:
            if other.object_id == object.object_id:
                output = True
                break
        return output

    @staticmethod
    def associate_RTP_To_FTP(
        FTPs: typing.List[DynamicObject], RTPs: typing.List[DynamicObjectDetection]
    ) -> typing.List[typing.List[DynamicObjectDetection]]:
        """Associate RTPs to FTPs based on their characteristics."""
        output: typing.List[typing.List[DynamicObjectDetection]] = []

        for _ in range(len(FTPs)):
            output.append([])

        for rtp in RTPs:
            best_ftp: typing.Tuple[DynamicObject, float] = (None, None)
            for i, ftp in enumerate(FTPs):
                score = FtTPFHelper.associate_RTP_To_FTP_score(ftp, rtp)
                if score is not None:
                    if best_ftp[1] is None or best_ftp[1] < score:
                        best_ftp = (i, score)
            if best_ftp[1] is not None:
                output[best_ftp[0]].append(rtp)

        return output

    @staticmethod
    # Returns none if it is not associated
    def associate_RTP_To_FTP_score(FTP: DynamicObject, RTP: DynamicObjectDetection) -> float:
        """Calculate the association score between FTP and RTP."""
        if FTP.object_class != RTP.class_type:
            return None

        ftp_poly = geometry.Polygon([[p.x, p.y] for p in FTP.shape])
        rtp_poly = geometry.Polygon([[p.x, p.y] for p in RTP.polygon])
        area_i = rtp_poly.intersection(ftp_poly).area
        area_ftp = ftp_poly.area
        area_rtp = rtp_poly.area

        ratio_1 = area_i / area_ftp
        ratio_2 = area_i / area_rtp

        if ratio_1 > 0.7 and ratio_2 > 0.7:
            return ratio_1 + ratio_2
        else:
            return None

    @staticmethod
    def get_relevant_RTP_Frames(
        sensor_timeframe: typing.List[DynamicObjectDetectionTimeframe], T_6_timestamp: int
    ) -> typing.List[DynamicObjectDetectionTimeframe]:
        """Get relevant RTP frames for a given sensor timeframe."""
        output = []
        # TODO optimism start of the search
        for tf in sensor_timeframe:
            time_before_T6_us = T_6_timestamp - tf.timestamp
            if time_before_T6_us < 0:
                break
            if time_before_T6_us < ConstantsCem.AP_E_TIME_BEFORE_CURRENT_T_CONTRIBUTION_MS * 1e3:
                output.append(tf)
        return output

    @staticmethod
    def get_single_relevant_RTP_frame(
        detection_timeframes: typing.List[DynamicObjectDetectionTimeframe], tpf_timestamp: int
    ) -> DynamicObjectDetectionTimeframe:
        """Get a single relevant RTP frame for a given sensor timeframe."""
        output: DynamicObjectDetectionTimeframe = None
        for timeframe in detection_timeframes:
            if tpf_timestamp > timeframe.timestamp:
                output = timeframe
            else:
                break

        if output is not None:
            timestamp_diff_ms = (tpf_timestamp - timeframe.timestamp) * 1e-3
            if timestamp_diff_ms > ConstantsCem.AP_E_TIME_BEFORE_CURRENT_T_CONTRIBUTION_MS:
                output = None

        return output

    @staticmethod
    def get_Tp_by_id(
        tp_list: typing.List[typing.Union[DynamicObject, DynamicObjectDetection]], id: int
    ) -> typing.Union[DynamicObject, DynamicObjectDetection]:
        """Get a Tp by its ID from a list."""
        return next(tp for tp in tp_list if tp.object_id == id)

    @staticmethod
    def get_vehicle_tpf_distance(tpf_object: DynamicObject):
        """Calculate the distance of a TPF object from the vehicle."""
        distances = [math.sqrt(pnt.x * pnt.x + pnt.y * pnt.y) for pnt in tpf_object.shape]
        return np.min(distances)

    @staticmethod
    def get_furthest_tpf(objects: typing.List[DynamicObject]) -> typing.Tuple[DynamicObject, float]:
        """Find the object farthest from a reference point within a list of TPF objects."""
        max_distance = sys.float_info.min
        furthest_object = None

        for tpf_object in objects:
            dist = FtTPFHelper.get_vehicle_tpf_distance(tpf_object)
            if dist > max_distance:
                max_distance = dist
                furthest_object = tpf_object

        return furthest_object, max_distance

    @staticmethod
    def get_closest_tpf(objects: typing.List[DynamicObject]) -> typing.Tuple[DynamicObject, float]:
        """Find the object closest to a reference point within a list of TPF objects."""
        min_distance = sys.float_info.max
        closest_object = None

        for tpf_object in objects:
            dist = FtTPFHelper.get_vehicle_tpf_distance(tpf_object)
            if dist < min_distance:
                min_distance = dist
                closest_object = tpf_object

        return closest_object, min_distance

    @staticmethod
    def get_missing_tpf_objects(
        prev_tpf_object_list: typing.List[DynamicObject], cur_tpf_object_list: typing.List[DynamicObject]
    ) -> typing.List[DynamicObject]:
        """Identify the objects that are missing in the current TPF compared to the previous TPF."""
        cur_ids: typing.Set[int] = set([tpf.object_id for tpf in cur_tpf_object_list])
        missing_object = [tpf for tpf in prev_tpf_object_list if tpf.object_id not in cur_ids]
        return missing_object

    @staticmethod
    def transform_tpf(tpf_object: DynamicObject, relative_motion: RelativeMotion) -> DynamicObject:
        """Transform the coordinates of a dynamic object in a TPF frame based on the relative motion."""
        transformed_coordinates = [
            FtPoseHelper.transform_point((pnt.x, pnt.y), relative_motion) for pnt in tpf_object.shape
        ]
        transformed_shape = [DynPoint(pnt[0], pnt[1]) for pnt in transformed_coordinates]

        return DynamicObject(
            tpf_object.object_id,
            tpf_object.object_class,
            tpf_object.class_certainty,
            tpf_object.dyn_property,
            tpf_object.dyn_property_certainty,
            transformed_shape,
            tpf_object.existence_prob,
            tpf_object.orientation + relative_motion.yaw_rotation,
            tpf_object.orientation_std,
            tpf_object.velocity_x,
            tpf_object.velocity_y,
            tpf_object.yaw_rate,
            tpf_object.velocity_std_x,
            tpf_object.velocity_std_y,
            tpf_object.yaw_rate_std,
            tpf_object.center_x,
            tpf_object.center_y,
            tpf_object.state,
            tpf_object.contained_in_last_sensor_update,
            tpf_object.lifetime,
        )

    @staticmethod
    def check_only_one_camera_is_active(
        input: typing.Dict[DynamicObjectCamera, typing.List[DynamicObjectDetectionTimeframe]],
    ) -> bool:
        """Check if only one camera is active based on the input data."""
        active_timeframe = dict()
        for camera in input:
            active_timeframe[camera] = sum([1 for timeframe in input[camera] if timeframe.num_objects > 0])

        number_active_cameras = sum([1 for camera, frame in active_timeframe.items() if frame > 0])

        return number_active_cameras <= 1

    @staticmethod
    def calculate_azimuth_angle(tpf: DynamicObject):
        """Calculate the azimuth angle of the dynamic object."""
        return 0  # TODO

    @staticmethod
    def is_object_in_car_FOV(tpf: DynamicObject) -> bool:
        """Check if the dynamic object is within the car's field of view."""
        distance = FtTPFHelper.get_vehicle_tpf_distance(tpf)
        # TODO: cehck if tpf is in azimuth range (need camera FoVs)

        if distance <= TpfFovConstatns.DISTANCE_RANGE:
            return True
        else:
            return False


class TpfFtp2GtAssociator:
    """This class associates the ground truth to the current FTP objects"""

    def __init__(self, vedodo_buffer: VedodoBuffer, ground_truth: pd.DataFrame):
        """Initialize object attributes."""
        self.vedodo_buffer = vedodo_buffer

        for vedodo_frame in self.vedodo_buffer.buffer:
            if vedodo_frame.timestamp > 0:
                break
        self.initial_timestamp = int(vedodo_frame.timestamp)

        self.gt_objects = []
        for v in ground_truth["object_id"].unique():
            self.gt_objects.append(ground_truth[ground_truth["object_id"] == v])

    def associate(self, tpf_timeframe: TPFTimeFrame) -> typing.Dict[int, int]:
        """Associates the TPF objects found in dynamic_objects to the objects found in the ground_truth DataFrame

        Inputs:
            tpf_timeframe: the list of dynamic objects containing also timestamps and number of objects

        Returns:
            the dict containing the association between the TPF objects and the ground truth objects
        """
        ASSOC_DISTANCE_SQUARED = 2.0  # TODO: move it to constants
        gt_pool_at_timeframe = {}
        associations = {}
        current_timestamp = tpf_timeframe.timestamp
        relative_motion = self.vedodo_buffer.calc_relative_motion(self.initial_timestamp, current_timestamp)
        # first, create a pool of GT objects existing in the timeframe
        for gt_object in self.gt_objects:
            index_prev = gt_object["timestamp"].searchsorted(current_timestamp) - 1
            if index_prev >= 0 and index_prev < len(gt_object) - 1:
                gt_id = gt_object.iat[index_prev, 1]
                ts_0 = gt_object.iat[index_prev, 0]  # the timestamp before the current timestamp
                ts_1 = gt_object.iat[index_prev + 1, 0]  # the timestamp after the current timestamp
                x_0 = gt_object.iat[index_prev, 2]  # the x coordinate before the current timestamp
                x_1 = gt_object.iat[index_prev + 1, 2]  # the x coordinate after the current timestamp
                y_0 = gt_object.iat[index_prev, 3]  # the y coordinate before the current timestamp
                y_1 = gt_object.iat[index_prev + 1, 3]  # the y coordinate after the current timestamp
                w_0 = (ts_1 - current_timestamp) / (ts_1 - ts_0)  # the weight of ts_0
                w_1 = (current_timestamp - ts_0) / (ts_1 - ts_0)  # the weight of ts_1
                x_avg = w_0 * x_0 + w_1 * x_1  # the average x coordinate of the GT object
                y_avg = w_0 * y_0 + w_1 * y_1  # the average y coordinate of the GT object
                gt_pool_at_timeframe[gt_id] = {"x": x_avg, "y": y_avg, "associated": False}

        # next, create a list of candidates that may be associated
        for ftp in tpf_timeframe.dynamic_objects:
            candidates_dist = {}
            center_x, center_y = FtPoseHelper.transform_point([ftp.center_x, ftp.center_y], relative_motion)
            for gt_id, gt_object in gt_pool_at_timeframe.items():
                if gt_object["associated"] is False:
                    dist_squared = (center_x - gt_object["x"]) ** 2 + (center_y - gt_object["y"]) ** 2
                    if dist_squared < ASSOC_DISTANCE_SQUARED:
                        candidates_dist[gt_id] = dist_squared

            # last, go through the candidates and select the best one that has the closest distance
            curr_dist_squared = sys.float_info.max
            gt_id = None
            for candidate, dist in candidates_dist.items():
                if dist < curr_dist_squared:
                    gt_id = candidate
                    curr_dist_squared = dist
            if gt_id is not None:
                associations[ftp.object_id] = gt_id
                gt_pool_at_timeframe[gt_id]["associated"] = True

        return associations

    def get_gt_at_timeframe(
        self, current_timestamp: int
    ) -> typing.Dict[int, typing.Dict[str, typing.Union[float, bool]]]:
        """Get the ground truth data at the specified timestamp."""
        gt_at_timeframe = {}
        # first, create a pool of GT objects existing in the timeframe
        for gt_object in self.gt_objects:
            index_prev = gt_object["timestamp"].searchsorted(current_timestamp) - 1
            if index_prev >= 0 and index_prev < len(gt_object) - 1:
                gt_id = gt_object.iat[index_prev, 1]
                ts_0 = gt_object.iat[index_prev, 0]  # the timestamp before the current timestamp
                ts_1 = gt_object.iat[index_prev + 1, 0]  # the timestamp after the current timestamp
                x_0 = gt_object.iat[index_prev, 2]  # the x coordinate before the current timestamp
                vx_0 = gt_object.iat[index_prev, 4]  # the x velocity before the current timestamp
                x_1 = gt_object.iat[index_prev + 1, 2]  # the x coordinate after the current timestamp
                vx_1 = gt_object.iat[index_prev + 1, 4]  # the x velocity after the current timestamp
                y_0 = gt_object.iat[index_prev, 3]  # the y coordinate before the current timestamp
                vy_0 = gt_object.iat[index_prev, 5]  # the y velocity before the current timestamp
                y_1 = gt_object.iat[index_prev + 1, 3]  # the y coordinate after the current timestamp
                vy_1 = gt_object.iat[index_prev + 1, 5]  # the y velocity after the current timestamp
                w_0 = (ts_1 - current_timestamp) / (ts_1 - ts_0)  # the weight of ts_0
                w_1 = (current_timestamp - ts_0) / (ts_1 - ts_0)  # the weight of ts_1
                x_avg = w_0 * x_0 + w_1 * x_1  # the average x coordinate of the GT object
                vx_avg = w_0 * vx_0 + w_1 * vx_1  # the average x velocity of the GT object
                y_avg = w_0 * y_0 + w_1 * y_1  # the average y coordinate of the GT object
                vy_avg = w_0 * vy_0 + w_1 * vy_1  # the average y velocity of the GT object
                gt_at_timeframe[gt_id] = {"x": x_avg, "vx": vx_avg, "y": y_avg, "vy": vy_avg, "associated": False}
        return gt_at_timeframe


class TPFMetricsHelper:
    """Recall rate calculator"""

    def __init__(self, vedodo_buffer: VedodoBuffer, ground_truth: pd.DataFrame):
        """Initialize object attributes."""
        self.associator = TpfFtp2GtAssociator(vedodo_buffer=vedodo_buffer, ground_truth=ground_truth)

    def calc(self, tpf_timeframe: TPFTimeFrame) -> float:
        """Calculates the recall rate of the TPF module
        Inputs:
            dynamic_objects: the list of dynamic objects containing also timestamps

        Returns:
            the recall rate
        """
        associated_object_list = self.associator.associate(tpf_timeframe)
        total_positives = tpf_timeframe.num_objects
        true_positives = len(associated_object_list)
        num_gt_objects = sum(
            [
                1
                for obj in self.associator.gt_objects
                if 0 < obj["timestamp"].searchsorted(tpf_timeframe.timestamp) < len(obj)
            ]
        )
        false_negatives = num_gt_objects - true_positives  # TODO: check if the GT is in the car FoV

        if total_positives > 0:
            precision_rate = true_positives / total_positives
        else:
            precision_rate = 1.0
        if true_positives + false_negatives > 0:
            recall_rate = true_positives / (true_positives + false_negatives)
        else:
            recall_rate = 1.0

        return {
            "precision_rate": precision_rate * 100,
            "recall_rate": recall_rate * 100.0,
            "Associated_objects": true_positives,
        }
