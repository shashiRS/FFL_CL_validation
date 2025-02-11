"""PCE Bsig reader"""

import logging

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class SimulationFrame:
    """Class representing a simulation frame for evaluation"""

    def __init__(self):
        # list to store polylines
        self.bsig_timestamps = {}
        self.bsig_detections_timestamps = {}
        self.bsig_num_of_detections = {}
        self.bsig_subclass_id = {}
        self.bsig_keypoint_x = {}
        self.bsig_keypoint_y = {}
        self.bsig_orientation = {}
        self.bsig_occlusion = {}

    def get_data_from_bsig(self, df, camera, class_type):
        """Get the sim data of each frame"""
        all_timestamps_in_bsig = []  # captures all timestamps available in bsig
        # captures the timestamps where we have specific detections(cuboid, bounding and polynomial)
        detection_timestamps_in_bsig = []
        num_of_detections_bsig = {}  # captures the number of detections in each frame
        subclass_id_in_bsig = {}  # captures the subclass of each detection
        keypoints_x_in_bsig = {}  # captures the X keypoints of every detection
        keypoints_y_in_bsig = {}  # captures the Y keypoints of every detection
        parking_slot_orientation = {}  # captures the orientation of parking slot
        parking_slot_occlusion = {}  # captures the Y keypoints of every detection

        df_specific_columns = df.drop_duplicates(subset=[f"detection_results_timestamp_{camera}"], keep="last")
        df_valid_specific_columns = df_specific_columns[
            (df_specific_columns[f"detection_results_timestamp_{camera}"] > 0)
        ]
        for _, row in df_valid_specific_columns.iterrows():
            timestamp = int(row[f"detection_results_timestamp_{camera}"])
            all_timestamps_in_bsig.append(timestamp)
            all_timestamps_in_bsig.sort()
            if row[f"num_{class_type}_{camera}"] > 0:
                detection_timestamps_in_bsig.append(timestamp)
                detection_timestamps_in_bsig.sort()
                num_of_detections_bsig[timestamp] = row[f"num_{class_type}_{camera}"]
                for det in range(0, int(num_of_detections_bsig[timestamp])):
                    dict_orientation_conf = {}  # holds the orientation confidences for all the parking slot detection
                    dict_occlusion_conf = {}  # holds the occlusion confidences for all the parking slot detection
                    list_occlusion_class_conf_each_frame = []
                    list_orientation_class_conf_each_frame = []
                    if class_type == "bounding_box_detections":
                        # Read the subclass Id from the bsig
                        subclass_id_in_bsig[f"{timestamp}_{det}"] = row[
                            f"bounding_box_detections_subclass_id_of_{camera}_det_" + str(det)
                        ]
                        # Read keypoints from the bsig
                        for keypoint in range(0, 2):
                            keypoints_x_in_bsig[f"{timestamp}_{det}_{keypoint}"] = row[
                                f"bounding_box_detections_key_points_x_of_{camera}_det_{det}_keypoint_{keypoint}"
                            ]
                            keypoints_y_in_bsig[f"{timestamp}_{det}_{keypoint}"] = row[
                                f"bounding_box_detections_key_points_y_of_{camera}_det_{det}_keypoint_{keypoint}"
                            ]
                    elif class_type == "cuboid_detections":
                        # Read the subclass Id from the bsig
                        subclass_id_in_bsig[f"{timestamp}_{det}"] = row[
                            f"cuboid_detections_subclass_id_of_{camera}_det_{det}"
                        ]
                        # Read keypoints from the bsig
                        for keypoint in range(0, 8):
                            keypoints_x_in_bsig[f"{timestamp}_{det}_{keypoint}"] = row[
                                f"cuboid_detections_key_points_x_of_{camera}_det_{det}_keypoint_{keypoint}"
                            ]
                            keypoints_y_in_bsig[f"{timestamp}_{det}_{keypoint}"] = row[
                                f"cuboid_detections_key_points_y_of_{camera}_det_{det}_keypoint_{keypoint}"
                            ]
                    elif class_type == "parking_slot_detections":
                        # Read the subclass Id from the bsig
                        subclass_id_in_bsig[f"{timestamp}_{det}"] = row[
                            f"parking_slot_subclass_id_of_{camera}_det_{det}"
                        ]
                        # Read keypoints from the bsig
                        for keypoint in range(0, 4):
                            keypoints_x_in_bsig[f"{timestamp}_{det}_{keypoint}"] = row[
                                f"parking_slot_key_points_x_of_{camera}_det_{det}_keypoint_{keypoint}"
                            ]
                            keypoints_y_in_bsig[f"{timestamp}_{det}_{keypoint}"] = row[
                                f"parking_slot_key_points_y_of_{camera}_det_{det}_keypoint_{keypoint}"
                            ]
                        # Read orientation confidence of each and every detected parking slot
                        for conf in range(0, 3):
                            orientation_conf = row[f"parking_orientation_confidence_{camera}_det_{det}", conf]
                            dict_orientation_conf[f"timestamp{timestamp}_det{det}_conf{conf}"] = orientation_conf
                            list_orientation_class_conf_each_frame.append(orientation_conf)
                        # used to get the index of maximum confidence orientation
                        maximum_orientation_confidence = max(dict_orientation_conf.values())
                        # index of maximum confidence orientation
                        parking_slot_orientation[f"{timestamp}_{det}"] = list_orientation_class_conf_each_frame.index(
                            maximum_orientation_confidence
                        )
                        # Read occlusion confidence of each and every detected parking slot
                        for conf in range(0, 4):
                            occluded_corners = []
                            occlusion_conf = row[f"parking_occlusion_confidence_{camera}_det_{det}", conf]
                            dict_occlusion_conf[f"timestamp{timestamp}_det{det}_conf{conf}"] = occlusion_conf
                            list_occlusion_class_conf_each_frame.append(occlusion_conf)
                        # get the corners of the parking slot that are occluded.
                        [
                            occluded_corners.append(list_occlusion_class_conf_each_frame.index(val))
                            for val in list_occlusion_class_conf_each_frame
                            if val > 0.5
                        ]
                        parking_slot_occlusion[f"{timestamp}_{det}"] = occluded_corners
        self.bsig_timestamps[camera] = all_timestamps_in_bsig
        self.bsig_detections_timestamps[camera] = detection_timestamps_in_bsig
        self.bsig_num_of_detections[camera] = num_of_detections_bsig
        self.bsig_keypoint_x[camera] = keypoints_x_in_bsig
        self.bsig_keypoint_y[camera] = keypoints_y_in_bsig
        self.bsig_subclass_id[camera] = subclass_id_in_bsig
        if class_type == "parking_slot_detections":
            self.bsig_orientation[camera] = parking_slot_orientation
            self.bsig_occlusion[camera] = parking_slot_occlusion
