"""PCE Evaluation to get valid detections"""

import logging

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class Evaluation:
    """Class representing a evaluation"""

    def __init__(self):
        # list to store polylines
        self.valid_timestamps_in_camera = {}
        self.valid_detections_in_camera = {}
        self.valid_num_of_detections = {}

    def evaluate_keypoints(self, gt, st, gt_det, det, timestamp, class_type, camera):
        """Evaluation of each frame"""
        if class_type == "bounding_box_detections":
            gt_bounding_box_keypoints = {
                "x1": gt.gt_keypoint_x[camera][f"{timestamp}_{gt_det}_{0}"],
                "y1": gt.gt_keypoint_y[camera][f"{timestamp}_{gt_det}_{0}"],
                "x2": gt.gt_keypoint_x[camera][f"{timestamp}_{gt_det}_{1}"],
                "y2": gt.gt_keypoint_y[camera][f"{timestamp}_{gt_det}_{1}"],
            }
            bsig_bounding_box_keypoints = {
                "x1": st.bsig_keypoint_x[camera][f"{timestamp}_{det}_{0}"],
                "y1": st.bsig_keypoint_y[camera][f"{timestamp}_{det}_{0}"],
                "x2": st.bsig_keypoint_x[camera][f"{timestamp}_{det}_{1}"],
                "y2": st.bsig_keypoint_y[camera][f"{timestamp}_{det}_{1}"],
            }

            if (
                abs(gt_bounding_box_keypoints["x1"] - bsig_bounding_box_keypoints["x1"]) < 5
                and abs(gt_bounding_box_keypoints["x2"] - bsig_bounding_box_keypoints["x2"]) < 5
                and abs(gt_bounding_box_keypoints["y1"] - bsig_bounding_box_keypoints["y1"]) < 5
                and abs(gt_bounding_box_keypoints["y2"] - bsig_bounding_box_keypoints["y2"]) < 5
            ):
                valid_keypoints = True
            else:
                valid_keypoints = False
        elif class_type == "Cuboid Detections":
            # get the cuboid keypoints from gt
            gt_cuboid_keypoints = {
                "x1": gt.gt_keypoint_x[camera][f"{timestamp}_{gt_det}_{0}"],
                "y1": gt.gt_keypoint_y[camera][f"{timestamp}_{gt_det}_{0}"],
                "x2": gt.gt_keypoint_x[camera][f"{timestamp}_{gt_det}_{1}"],
                "y2": gt.gt_keypoint_y[camera][f"{timestamp}_{gt_det}_{1}"],
                "x3": gt.gt_keypoint_x[camera][f"{timestamp}_{gt_det}_{2}"],
                "y3": gt.gt_keypoint_y[camera][f"{timestamp}_{gt_det}_{2}"],
                "x4": gt.gt_keypoint_x[camera][f"{timestamp}_{gt_det}_{3}"],
                "y4": gt.gt_keypoint_y[camera][f"{timestamp}_{gt_det}_{3}"],
                "x5": gt.gt_keypoint_x[camera][f"{timestamp}_{gt_det}_{4}"],
                "y5": gt.gt_keypoint_y[camera][f"{timestamp}_{gt_det}_{4}"],
                "x6": gt.gt_keypoint_x[camera][f"{timestamp}_{gt_det}_{5}"],
                "y6": gt.gt_keypoint_y[camera][f"{timestamp}_{gt_det}_{5}"],
                "x7": gt.gt_keypoint_x[camera][f"{timestamp}_{gt_det}_{6}"],
                "y7": gt.gt_keypoint_y[camera][f"{timestamp}_{gt_det}_{6}"],
                "x8": gt.gt_keypoint_x[camera][f"{timestamp}_{gt_det}_{7}"],
                "y8": gt.gt_keypoint_y[camera][f"{timestamp}_{gt_det}_{7}"],
            }
            # get the cuboid keypoints from sim
            bsig_cuboid_keypoints = {
                "x1": st.bsig_keypoint_x[camera][f"{timestamp}_{det}_{0}"],
                "y1": st.bsig_keypoint_y[camera][f"{timestamp}_{det}_{0}"],
                "x2": st.bsig_keypoint_x[camera][f"{timestamp}_{det}_{1}"],
                "y2": st.bsig_keypoint_y[camera][f"{timestamp}_{det}_{1}"],
                "x3": st.bsig_keypoint_x[camera][f"{timestamp}_{det}_{2}"],
                "y3": st.bsig_keypoint_y[camera][f"{timestamp}_{det}_{2}"],
                "x4": st.bsig_keypoint_x[camera][f"{timestamp}_{det}_{3}"],
                "y4": st.bsig_keypoint_y[camera][f"{timestamp}_{det}_{3}"],
                "x5": st.bsig_keypoint_x[camera][f"{timestamp}_{det}_{4}"],
                "y5": st.bsig_keypoint_y[camera][f"{timestamp}_{det}_{4}"],
                "x6": st.bsig_keypoint_x[camera][f"{timestamp}_{det}_{5}"],
                "y6": st.bsig_keypoint_y[camera][f"{timestamp}_{det}_{5}"],
                "x7": st.bsig_keypoint_x[camera][f"{timestamp}_{det}_{6}"],
                "y7": st.bsig_keypoint_y[camera][f"{timestamp}_{det}_{6}"],
                "x8": st.bsig_keypoint_x[camera][f"{timestamp}_{det}_{7}"],
                "y8": st.bsig_keypoint_y[camera][f"{timestamp}_{det}_{7}"],
            }
            # compare if the GT and bsig have the keypoin with difference of 30 pixels in x and 10 pixels in y
            #
            if int(gt.gt_subclass_id[camera][f"{timestamp}_{gt_det}"]) == 2:  # if subclass of cuboid detection is truck
                thr_x = 65
                thr_y = 35
            else:
                thr_x = 35
                thr_y = 15
            if (
                abs(gt_cuboid_keypoints["x1"] - bsig_cuboid_keypoints["x1"]) < thr_x
                and abs(gt_cuboid_keypoints["x2"] - bsig_cuboid_keypoints["x2"]) < thr_x
                and abs(gt_cuboid_keypoints["x3"] - bsig_cuboid_keypoints["x3"]) < thr_x
                and abs(gt_cuboid_keypoints["x4"] - bsig_cuboid_keypoints["x4"]) < thr_x
                and abs(gt_cuboid_keypoints["x5"] - bsig_cuboid_keypoints["x5"]) < thr_x
                and abs(gt_cuboid_keypoints["x6"] - bsig_cuboid_keypoints["x6"]) < thr_x
                and abs(gt_cuboid_keypoints["x7"] - bsig_cuboid_keypoints["x7"]) < thr_x
                and abs(gt_cuboid_keypoints["x8"] - bsig_cuboid_keypoints["x8"]) < thr_x
                and abs(gt_cuboid_keypoints["y1"] - bsig_cuboid_keypoints["y1"]) < thr_y
                and abs(gt_cuboid_keypoints["y2"] - bsig_cuboid_keypoints["y2"]) < thr_y
                and abs(gt_cuboid_keypoints["y3"] - bsig_cuboid_keypoints["y3"]) < thr_y
                and abs(gt_cuboid_keypoints["y4"] - bsig_cuboid_keypoints["y4"]) < thr_y
                and abs(gt_cuboid_keypoints["y5"] - bsig_cuboid_keypoints["y5"]) < thr_y
                and abs(gt_cuboid_keypoints["y6"] - bsig_cuboid_keypoints["y6"]) < thr_y
                and abs(gt_cuboid_keypoints["y7"] - bsig_cuboid_keypoints["y7"]) < thr_y
                and abs(gt_cuboid_keypoints["y8"] - bsig_cuboid_keypoints["y8"]) < thr_y
            ):
                # detections will be considered as valid if detections are having the keypoints with
                # expected difference
                valid_keypoints = True
            else:
                # detections will be considered as invalid if detections are not having the keypoints with
                # expected difference
                valid_keypoints = False
        elif class_type == "Polynomial Detections":
            gt_poly_keypoints = {
                "x1": gt.gt_keypoint_x[camera][f"{timestamp}_{gt_det}_{0}"],
                "y1": gt.gt_keypoint_y[camera][f"{timestamp}_{gt_det}_{0}"],
                "x2": gt.gt_keypoint_x[camera][f"{timestamp}_{gt_det}_{1}"],
                "y2": gt.gt_keypoint_y[camera][f"{timestamp}_{gt_det}_{1}"],
                "x3": gt.gt_keypoint_x[camera][f"{timestamp}_{gt_det}_{2}"],
                "y3": gt.gt_keypoint_y[camera][f"{timestamp}_{gt_det}_{2}"],
                "x4": gt.gt_keypoint_x[camera][f"{timestamp}_{gt_det}_{3}"],
                "y4": gt.gt_keypoint_y[camera][f"{timestamp}_{gt_det}_{3}"],
            }
            bsig_poly_keypoints = {
                "x1": st.bsig_keypoint_x[camera][f"{timestamp}_{det}_{0}"],
                "y1": st.bsig_keypoint_y[camera][f"{timestamp}_{det}_{0}"],
                "x2": st.bsig_keypoint_x[camera][f"{timestamp}_{det}_{1}"],
                "y2": st.bsig_keypoint_y[camera][f"{timestamp}_{det}_{1}"],
                "x3": st.bsig_keypoint_x[camera][f"{timestamp}_{det}_{2}"],
                "y3": st.bsig_keypoint_y[camera][f"{timestamp}_{det}_{2}"],
                "x4": st.bsig_keypoint_x[camera][f"{timestamp}_{det}_{3}"],
                "y4": st.bsig_keypoint_y[camera][f"{timestamp}_{det}_{3}"],
            }

            if (
                abs(gt_poly_keypoints["x1"] - bsig_poly_keypoints["x1"]) < 35
                and abs(gt_poly_keypoints["x2"] - bsig_poly_keypoints["x2"]) < 35
                and abs(gt_poly_keypoints["x3"] - bsig_poly_keypoints["x3"]) < 35
                and abs(gt_poly_keypoints["x4"] - bsig_poly_keypoints["x4"]) < 35
                and abs(gt_poly_keypoints["y1"] - bsig_poly_keypoints["y1"]) < 20
                and abs(gt_poly_keypoints["y2"] - bsig_poly_keypoints["y2"]) < 20
                and abs(gt_poly_keypoints["y3"] - bsig_poly_keypoints["y3"]) < 20
                and abs(gt_poly_keypoints["y4"] - bsig_poly_keypoints["y4"]) < 20
            ):
                valid_keypoints = True
            else:
                valid_keypoints = False
        return valid_keypoints

    def get_valid_timestamp_and_detections(self, gt, st, camera, class_type):
        """Get valid timestamps and detections available at that timestamp"""
        valid_subclass = {}
        valid_orientation = {}
        valid_occlusion = {}
        valid_timestamps = []
        valid_keypoints = {}
        valid_detections = {}
        valid_detections_in_each_camera = {}
        for timestamp in gt.gt_timestamps[camera]:
            if timestamp in st.bsig_detections_timestamps[camera] and timestamp in gt.gt_detections_timestamps[camera]:
                # To hold the status if gt detection has its associated detection in bsig/rec
                gt_detection = {}
                # count_1 = {}
                detection = 0
                # To hold the status if bsig detection has its associated detection in gt
                sim_detection = {}
                # set all 64 detections to not associated
                for i in range(0, 64):
                    gt_detection[i] = "not associated"
                    sim_detection[i] = "not associated"
                for gt_det in range(0, int(gt.gt_num_of_detections[camera][timestamp])):
                    for det in range(0, int(st.bsig_num_of_detections[camera][timestamp])):
                        if gt_detection[gt_det] == "not associated" and sim_detection[det] == "not associated":
                            # perform the following to find the associated detections
                            # check if the detection is of same subclass
                            if (
                                int(gt.gt_subclass_id[camera][f"{timestamp}_{gt_det}"])
                                == st.bsig_subclass_id[camera][f"{timestamp}_{det}"]
                            ):
                                valid_subclass[f"{camera}_{timestamp}_{det}"] = True
                                # check if keypoints are associated for same subclass
                                valid_keypoints[f"{camera}_{timestamp}_{det}"] = self.evaluate_keypoints(
                                    gt, st, gt_det, det, timestamp, class_type, camera
                                )
                                if (
                                    class_type == "Polynomial Detections"
                                    and valid_keypoints[f"{camera}_{timestamp}_{det}"] is True
                                ):
                                    # check if orientation is same
                                    if (
                                        int(gt.gt_orientation[camera][f"{timestamp}_{gt_det}"])
                                        == st.bsig_orientation[camera][f"{timestamp}_{det}"]
                                    ):
                                        valid_orientation[f"{camera}_{timestamp}_{det}"] = True
                                    else:
                                        valid_orientation[f"{camera}_{timestamp}_{det}"] = False
                                    # check if occlusion is same
                                    if (
                                        gt.gt_occlusion[camera][f"{timestamp}_{gt_det}"]
                                        == st.bsig_occlusion[camera][f"{timestamp}_{det}"]
                                    ):
                                        valid_occlusion[f"{camera}_{timestamp}_{det}"] = True
                                    else:
                                        valid_occlusion[f"{camera}_{timestamp}_{det}"] = False
                            else:
                                valid_subclass[f"{camera}_{timestamp}_{det}"] = False
                            # check if the detections have same keypoints to confirm the position of the object
                            if class_type == "Polynomial Detections":
                                if (
                                    valid_subclass[f"{camera}_{timestamp}_{det}"] is True
                                    and valid_keypoints[f"{camera}_{timestamp}_{det}"] is True
                                    and valid_orientation[f"{camera}_{timestamp}_{det}"] is True
                                    and valid_occlusion[f"{camera}_{timestamp}_{det}"] is True
                                ):
                                    valid_timestamps.append(timestamp)
                                    valid_detections_in_each_camera[f"{timestamp}_{det}"] = True
                                    detection = detection + 1
                                    gt_detection[gt_det] = "associated"
                                    sim_detection[det] = "associated"
                                else:
                                    valid_detections_in_each_camera[f"{timestamp}_{det}"] = False
                                    gt_detection[gt_det] = "not associated"
                                    sim_detection[det] = "not associated"
                            else:
                                if (
                                    valid_subclass[f"{camera}_{timestamp}_{det}"] is True
                                    and valid_keypoints[f"{camera}_{timestamp}_{det}"] is True
                                ):
                                    valid_timestamps.append(timestamp)
                                    detection = detection + 1
                                    valid_detections_in_each_camera[f"{timestamp}_{det}"] = True
                                    gt_detection[gt_det] = "associated"
                                    sim_detection[det] = "associated"
                                else:
                                    valid_detections_in_each_camera[f"{timestamp}_{det}"] = False
                                    gt_detection[gt_det] = "not associated"
                                    sim_detection[det] = "not associated"
                            if detection > 0:
                                valid_detections[timestamp] = detection
                for i in range(0, int(st.bsig_num_of_detections[camera][timestamp])):
                    if sim_detection[i] == "not associated":
                        valid_detections_in_each_camera[f"{timestamp}_{i}"] = False
        valid_timestamps = list(dict.fromkeys(valid_timestamps))
        self.valid_timestamps_in_camera[camera] = valid_timestamps
        self.valid_detections_in_camera[camera] = valid_detections_in_each_camera
        self.valid_num_of_detections[camera] = valid_detections
