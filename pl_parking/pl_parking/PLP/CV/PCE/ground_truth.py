"""PCE Ground Truth reader"""

import logging

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class GroundTruthFrame:
    """Class representing a single ground truth camera frame for evaluation"""

    def __init__(self):
        # list to store polylines
        self.gt_timestamps = {}
        self.gt_detections_timestamps = {}
        self.gt_num_of_detections = {}
        self.gt_subclass_id = {}
        self.gt_keypoint_x = {}
        self.gt_keypoint_y = {}
        self.gt_orientation = {}
        self.gt_occlusion = {}

    def get_data_from_label(self, data, camera, class_type):
        """Get the labeled data of each frame"""
        timestamps_in_GT = []  # captures all timestamps available in GT
        # captures the timestamps where we have specific detections(cuboid, bounding and polynomial)
        timestamps_detections = []
        num_of_detections = {}  # captures the number of detections in each frame
        subclass_id = {}  # captures the subclass of each detection
        occluded_corners = {}  # captures the occluded corner of parking slot
        orientation = {}  # captures the orientation of parking slot
        keypoint_x = {}  # captures the X keypoints of every detection
        keypoint_y = {}  # captures the Y keypoints of every detection
        camera_label = f"Chips{camera.swapcase()}"

        if camera_label == "ChipsFC":
            stream_data = data["Sequence"][0]["Labels"][0]["Devices"][0]["Channels"][0]
        elif camera_label == "ChipsRSC":
            stream_data = data["Sequence"][0]["Labels"][0]["Devices"][0]["Channels"][1]
        elif camera_label == "ChipsRC":
            stream_data = data["Sequence"][0]["Labels"][0]["Devices"][0]["Channels"][2]
        else:
            stream_data = data["Sequence"][0]["Labels"][0]["Devices"][0]["Channels"][3]
        if len(stream_data) != 0:
            for stream in stream_data["ObjectLabels"]:
                timestamp = stream["TimeStamp"]
                timestamps_in_GT.append(timestamp)
                count_bounding = 0
                count_cuboid = 0
                cuboid_det = 0
                bounding_det = 0
                count_poly = 0
                poly_det = 0
                for label in stream["FrameObjectLabels"]:
                    # Count the number of bounding box detections in specific frame
                    if (label["category"]) == "Bounding Box":
                        count_bounding = count_bounding + 1
                    # Count the number of cuboid detections in each frame
                    if (label["category"]) == "Cuboid Detections":
                        count_cuboid = count_cuboid + 1
                    # Count the number of polymonial detections in each frame
                    if (label["category"]) == "Polynomial Detections":
                        count_poly = count_poly + 1
                for label in stream["FrameObjectLabels"]:
                    # Reading the Bounding Box detections labeled data
                    if class_type == "BoundingBoxDetections" and (label["category"]) == "Bounding Box":
                        # if number of bounding boxes is greater than 0 and number of bounding boxes read from the
                        # current frame is not equal to the total number of bounding boxes in the current frame
                        if count_bounding > 0 and bounding_det != count_bounding:
                            # store the timestamp of the current frame where we have bounding box detections
                            timestamps_detections.append(timestamp)
                            # store the number of bounding box detections available in current frame
                            num_of_detections[timestamp] = count_bounding
                            # store the subclass ID of the detections in current frame
                            subclass_id[f"{timestamp}_{bounding_det}"] = label["attributes"]["Subclass Id"][0]
                            # store the keypoints of the detections in current frame
                            for keypoint in range(0, 2):
                                keypoint_x[f"{timestamp}_{bounding_det}_{keypoint}"] = label["keypoints"][
                                    f"{keypoint}"
                                ]["x"]
                                keypoint_y[f"{timestamp}_{bounding_det}_{keypoint}"] = label["keypoints"][
                                    f"{keypoint}"
                                ]["y"]
                            # increment the counter until we read all the bounding detections from the current frame
                            bounding_det = bounding_det + 1
                    # Reading the Cuboid detections labeled data
                    elif class_type == "Cuboid Detections" and (label["category"]) == "Cuboid Detections":
                        # if number of cuboid detections is greater than 0 and cuboid detections read from the
                        # current frame is not equal to the total number of cuboid detections in the current frame
                        if count_cuboid > 0 and cuboid_det != count_cuboid:
                            # store the timestamp of the current frame where we have cuboid detections
                            timestamps_detections.append(timestamp)
                            # store the number of cuboid detections available in current frame
                            num_of_detections[timestamp] = count_cuboid
                            # store the subclass ID of the detections in current frame
                            subclass_id[f"{timestamp}_{cuboid_det}"] = label["attributes"]["Subclass Id"][0]
                            # store the keypoints of the detections in current frame
                            for keypoint in range(0, 8):
                                keypoint_x[f"{timestamp}_{cuboid_det}_{keypoint}"] = label["keypoints"][f"{keypoint}"][
                                    "x"
                                ]
                                keypoint_y[f"{timestamp}_{cuboid_det}_{keypoint}"] = label["keypoints"][f"{keypoint}"][
                                    "y"
                                ]
                            # increment the counter for every cuboid detection read from the current frame
                            cuboid_det = cuboid_det + 1
                    # Reading the Polynomial detections labeled data
                    elif class_type == "Polynomial Detections" and (label["category"]) == "Polynomial Detections":
                        # if number of polynomial detections is greater than 0 and number of polynomial detections read
                        # from the current frame is not equal to the total number of polynomial detections in the
                        # current frame
                        if count_poly > 0 and poly_det != count_poly:
                            # store the timestamp of the current frame where we have polynomial detections
                            timestamps_detections.append(timestamp)
                            # stores the corners that are occluded
                            occluded_corner_list = []
                            # store the number of polynomial detections available in current frame
                            num_of_detections[timestamp] = count_poly
                            # store the subclass ID of the polynomial detections in current frame
                            subclass_id[f"{timestamp}_{poly_det}"] = label["attributes"]["Subclass Id"][0]
                            # store the orientation of the polynomial detections in current frame
                            if "Orientation" in label["attributes"]:
                                orientation[f"{timestamp}_{poly_det}"] = label["attributes"]["Orientation"][0]
                            # store the keypoints of the polynomial detections in current frame
                            for keypoint in range(0, 4):
                                keypoint_x[f"{timestamp}_{poly_det}_{keypoint}"] = label["keypoints"][f"{keypoint}"][
                                    "x"
                                ]
                                keypoint_y[f"{timestamp}_{poly_det}_{keypoint}"] = label["keypoints"][f"{keypoint}"][
                                    "y"
                                ]
                            # store the Occlusion of the polynomial detections in current frame
                            if "Occlusion" in label["attributes"]:
                                occluded = list(label["attributes"]["Occlusion"][0])
                                if len(occluded) > 1:
                                    occluded = list(dict.fromkeys(occluded))
                                    occluded.remove(",")
                                for corner in occluded:
                                    occluded_corner_list.append(int(corner))
                                occluded_corners[f"{timestamp}_{poly_det}"] = occluded_corner_list
                            else:
                                occluded_corners[f"{timestamp}_{poly_det}"] = occluded_corner_list
                            poly_det = poly_det + 1
                    timestamps_detections = list(dict.fromkeys(timestamps_detections))
        # available timestamps in label file
        self.gt_timestamps[camera] = timestamps_in_GT
        # timestamps where the specific detections(cuboid/bounding/polynomial/wheel stopper/wheel locker) are available
        self.gt_detections_timestamps[camera] = timestamps_detections
        # number of specific detections(cuboid/bounding/polynomial/wheel stopper/wheel locker) available in all the
        # frames
        self.gt_num_of_detections[camera] = num_of_detections
        # keypoint X of specific detections available in all the frames
        self.gt_keypoint_x[camera] = keypoint_x
        # keypoint Y of specific detections available in all the frames
        self.gt_keypoint_y[camera] = keypoint_y
        # subclass Id of all the detections in each frame
        self.gt_subclass_id[camera] = subclass_id
        if class_type == "Polynomial Detections":
            # orientation of all the polynomial detections in each frame
            self.gt_orientation[camera] = orientation
            # occlusion of all the polynomial detections in each frame
            self.gt_occlusion[camera] = occluded_corners
