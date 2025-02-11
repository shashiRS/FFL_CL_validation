"""Grappa Helper file"""

import os
import sys
from typing import Dict, List

import numpy as np

# import torch

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
# import json

# import matplotlib.patches as patches
# import matplotlib.pyplot as plt
# import pandas as pd
# from matplotlib.patches import Polygon, Rectangle
# from shapely.geometry import LineString, box
# from shapely.geometry import Polygon as shapely_Polygon
# from torch import Tensor
from tsf.core.common import Artifact

# from tsf.core.testcase import (
#     PreProcessor,
# )
from tsf.io.datamodel import SignalDataFrame
from tsf.io.generic import IReader, ISignalReader
from tsf.io.signals import SignalDefinition

# def plot_polygon_and_bbox(polygon, bbox):  # noqa: D103
#     # Create a figure and axis
#     fig, ax = plt.subplots()

#     # Plot the polygon
#     poly = Polygon(polygon, alpha=0.5)
#     ax.add_patch(poly)

#     # Plot the bounding box
#     bbox_x1, bbox_y1 = bbox[0]
#     bbox_width = bbox[1][0] - bbox_x1
#     bbox_height = bbox[1][1] - bbox_y1
#     rect = Rectangle((bbox_x1, bbox_y1), bbox_width, bbox_height, alpha=0.5)
#     ax.add_patch(rect)

#     # Set limits and labels
#     ax.set_xlim(min(bbox_x1, min(x for x, y in polygon)) - 50, max(bbox[1][0], max(x for x, y in polygon)) + 50)
#     ax.set_ylim(min(bbox_y1, min(y for x, y in polygon)) - 50, max(bbox[1][1], max(y for x, y in polygon)) + 50)
#     # ax.set_aspect('equal', 'box')
#     ax.set_xlabel("X")
#     ax.set_ylabel("Y")
#     ax.set_title("Polygon and Bounding Box")

#     # Show the plot
#     plt.grid(True)
#     plt.show()


# def line_iou_last(line_coords, bbox_coords, thickness):  # noqa: D103
#     # Unpack the line coordinates
#     (x1, y1), (x2, y2) = line_coords

#     # Unpack the bounding box coordinates
#     (bx1, by1), (bx2, by2) = bbox_coords

#     # Create the bounding box
#     bbox = box(bx1, by1, bx2, by2)

#     # Create the line and buffer it to create a thin rectangle
#     line = LineString([(x1, y1), (x2, y2)]).buffer(thickness / 2, cap_style=2)

#     # Calculate intersection and union
#     intersection = line.intersection(bbox).area
#     union = line.area + bbox.area - intersection

#     # Calculate IoU
#     iou = intersection / union

#     return iou, line, bbox


# def plot_shapes(line, bbox, line_coords, bbox_coords):  # noqa: D103
#     fig, ax = plt.subplots()

#     # Plot the bounding box
#     bbox_patch = patches.Polygon(xy=list(bbox.exterior.coords), closed=True, edgecolor="red", facecolor="none")
#     ax.add_patch(bbox_patch)

#     # Plot the line (as a thin rectangle)
#     line_patch = patches.Polygon(xy=list(line.exterior.coords), closed=True, edgecolor="blue", facecolor="none")
#     ax.add_patch(line_patch)

#     # Plot the original line
#     (x1, y1), (x2, y2) = line_coords
#     plt.plot([x1, x2], [y1, y2], "bo-")

#     # Plot the bounding box coordinates
#     (bx1, by1), (bx2, by2) = bbox_coords
#     plt.plot([bx1, bx2, bx2, bx1, bx1], [by1, by1, by2, by2, by1], "ro-")

#     # Set the plot limits
#     ax.set_xlim(min(bx1, bx2, x1, x2) - 1, max(bx1, bx2, x1, x2) + 1)
#     ax.set_ylim(min(by1, by2, y1, y2) - 1, max(by1, by2, y1, y2) + 1)

#     # Set the aspect ratio to be equal
#     ax.set_aspect("equal", adjustable="box")

#     plt.show()


# class PredictionObject:
#     """This class represents the match result of a prediction, which can be either FP, FN or TP."""

#     def __init__(self, is_tp: bool, score: float, coordinates, iou, timestamp):
#         self.is_tp = is_tp
#         self.score = score
#         self.coordinates = coordinates
#         self.timestamp = timestamp
#         self.iou = iou
#         self.ignore = False

#     def __eq__(self, other):
#         return self.score == other.score

#     def __lt__(self, other):
#         return self.score < other.score

#     def __repr__(self):

#         return f"{self.timestamp}s iou= {self.iou}), tp {self.is_tp}"


# class GroundTruthObject:
#     """This class represents the match result of a prediction, which can be either FP, FN or TP."""

#     def __init__(self, coordinates: list, timestamp: int, ignore: bool, ignore_box: bool):

#         self.coordinates = coordinates
#         self.timestamp = timestamp
#         self.ignore = ignore
#         self.ignore_box = ignore_box

#     def __eq__(self, other):
#         return self.score == other.score

#     def __lt__(self, other):
#         return self.score < other.score

#     def __repr__(self):

#         return f"{self.timestamp} s "


# class GrappaConstants:
#     """Defining constants used to store the class name of the objects"""

#     LINE = "Line"
#     CUBOID = "Cuboid"
#     BOX = "Box"
#     POLYGON = "Polygon"


class MyJsonReader(IReader, ISignalReader):
    """JSON READER"""

    def __init__(self, filename: str, signal_definition: SignalDefinition, **kwargs):
        """Class to initialise variables"""
        super().__init__(**kwargs)
        self.filename = filename
        self._defs = signal_definition

    @property
    def file_extensions(self) -> List[str]:
        """Define what type of file will be read by this class."""
        return [".json"]

    def open(self, use_regression_signal_mapping=False):
        """Opens the data source and prepares for reading."""
        pass

    def close(self):
        """Closes the data source."""
        pass

    @property
    def artifacts(self) -> List[Artifact]:
        """Returns a artifact type list.."""
        return [Artifact(f, None, None) for f in self.filename]

    @property
    def signals(self) -> SignalDataFrame:
        """Returns read objects as subclassed pandas dataframe.

        :return: A object dataframe.
        """
        sdf = SignalDataFrame()
        sdf["new_column"] = range(1, 100)  # Adding some data to simulate data being read from the .foo file
        return sdf

    def signal_data(self, items: List[str]) -> Dict[str, np.array]:
        """Fetch list of signals in single call."""
        return {k: self._df[k].values for k in items}

    def __getitem__(self, item) -> np.array:
        """Expose the signal df.

        :return: Array
        """
        return self._df[item]


# def last_iou_bbox(bbox1_coords, bbox2_coords):  # noqa: D103
#     # Unpack the bounding box coordinates
#     (bx1_1, by1_1), (bx2_1, by2_1) = bbox1_coords
#     (bx1_2, by1_2), (bx2_2, by2_2) = bbox2_coords

#     # Create the bounding boxes
#     bbox1 = box(bx1_1, by1_1, bx2_1, by2_1)
#     bbox2 = box(bx1_2, by1_2, bx2_2, by2_2)

#     # Calculate intersection and union
#     intersection = bbox1.intersection(bbox2).area
#     union = bbox1.area + bbox2.area - intersection

#     # Calculate IoU
#     iou = intersection / union
#     return iou, bbox1, bbox2


# def plot_bboxes(bbox1_coords, bbox2_coords):  # noqa: D103
#     fig, ax = plt.subplots()

#     # Unpack the bounding box coordinates
#     (bx1_1, by1_1), (bx2_1, by2_1) = bbox1_coords
#     (bx1_2, by1_2), (bx2_2, by2_2) = bbox2_coords

#     # Plot the first bounding box
#     bbox1_patch = patches.Rectangle((bx1_1, by1_1), bx2_1 - bx1_1, by2_1 - by1_1, edgecolor="red", facecolor="none")
#     ax.add_patch(bbox1_patch)

#     # Plot the second bounding box
#     bbox2_patch = patches.Rectangle((bx1_2, by1_2), bx2_2 - bx1_2, by2_2 - by1_2, edgecolor="green", facecolor="none")
#     ax.add_patch(bbox2_patch)

#     # Set the plot limits
#     ax.set_xlim(min(bx1_1, bx2_1, bx1_2, bx2_2) - 1, max(bx1_1, bx2_1, bx1_2, bx2_2) + 1)
#     ax.set_ylim(min(by1_1, by2_1, by1_2, by2_2) - 1, max(by1_1, by2_1, by1_2, by2_2) + 1)

#     # Set the aspect ratio to be equal
#     ax.set_aspect("equal", adjustable="box")

#     plt.show()


class ALIASSignals(SignalDefinition):
    """Example signal reading mapping for signals."""

    class Columns(SignalDefinition.Columns):
        """Example signal reading mapping for signals."""

        FOO = "FOO"

    def __init__(self):
        super().__init__()

        self._root = None

        self._properties = {
            self.Columns.FOO: "Col1",
        }

        ###################################################################
        # Note: Here is how map the extension to your specific reader #####
        ###################################################################
        self._extension_map = {
            ".json": MyJsonReader,
        }


# def ignorebox_bbox(bbox1, bbox2):
#     """
#     Calculate the IoU of two bounding boxes.
#     Each bbox should be in the format [x_min, y_min, x_max, y_max].
#     """
#     x1_min, y1_min, x1_max, y1_max = bbox1
#     x2_min, y2_min, x2_max, y2_max = bbox2[0][0], bbox2[0][1], bbox2[1][0], bbox2[1][1]

#     # Determine the coordinates of the intersection rectangle
#     inter_x_min = max(x1_min, x2_min)
#     inter_y_min = max(y1_min, y2_min)
#     inter_x_max = min(x1_max, x2_max)
#     inter_y_max = min(y1_max, y2_max)

#     # Compute the area of the intersection rectangle
#     inter_area = max(0, inter_x_max - inter_x_min) * max(0, inter_y_max - inter_y_min)

#     # Compute the area of both bounding boxes
#     bbox1_area = (x1_max - x1_min) * (y1_max - y1_min)
#     bbox2_area = (x2_max - x2_min) * (y2_max - y2_min)

#     # Compute the Intersection over Union (IoU)
#     iou = inter_area / float(bbox1_area + bbox2_area - inter_area)

#     return iou


# def ignore_box_line(line, bbox, line_width=1):
#     """
#     Calculate the IoU of a line with a bounding box.
#     line: [(x1, y1), (x2, y2)] - start and end points of the line
#     bbox: [x_min, y_min, x_max, y_max] - the bounding box
#     line_width: width of the line to create a bounding box around it
#     """
#     (x1, y1), (x2, y2) = line
#     line_bbox = [
#         min(x1, x2) - line_width / 2,
#         min(y1, y2) - line_width / 2,
#         max(x1, x2) + line_width / 2,
#         max(y1, y2) + line_width / 2,
#     ]

#     return ignorebox_bbox(line_bbox, bbox)


# def polygon_bbox_iou(polygon_coords, bbox):
#     """
#     Calculate the IoU of a polygon with a bounding box.
#     polygon_coords: [(x1, y1), (x2, y2), ...] - vertices of the polygon
#     bbox: [x_min, y_min, x_max, y_max] - the bounding box
#     """
#     polygon = Polygon(polygon_coords)
#     bbox_polygon = box(bbox[0][0], bbox[0][1], bbox[1][0], bbox[1][1])
#     if not polygon.is_valid:
#         polygon = polygon.buffer(0)
#     inter_area = polygon.intersection(bbox_polygon).area
#     union_area = polygon.union(bbox_polygon).area

#     iou = inter_area / union_area
#     return iou


# def cuboid_bbox_iou(cuboid, bbox):
#     """
#     Calculate the IoU of a cuboid with a bounding box in 2D space (top-down view).
#     cuboid: [x_min, y_min, x_max, y_max, z_min, z_max] - the cuboid
#     bbox: [x_min, y_min, x_max, y_max] - the bounding box
#     """
#     cuboid_2d = cuboid[:4]  # Take only the x, y coordinates

#     return ignorebox_bbox(cuboid_2d, bbox)


# class MyPreprocessor(PreProcessor):
#     """Preprocessor class to compute all data before the teststeps."""

#     def pre_process(self):
#         """Function used to do all the calculations."""
#         json_grappa_file_path = self.artifacts[0].file_path.source_path
#         json_GT_file_path = json_grappa_file_path.replace("grappa", "gt")
#         # df_r = self.side_load["RoadLabelAbsolute"]
#         with open(json_grappa_file_path) as read_file:
#             data_grappa = json.load(read_file)

#         with open(json_GT_file_path) as read_file:
#             data_gt = json.load(read_file)

#         def read_json_grappa(grappa_json: dict[dict]):
#             """Extract needed informations for grappa json"""
#             class_dictionary = {
#                 "Line": [],
#                 "Cuboid": [],
#                 "Box": [],
#                 "Polygon": [],
#             }

#             object_name = ""  # noqa: F841
#             value_coordinates = []
#             timestamp = []  # noqa: F841
#             first_timestamp = 0  # noqa: F841
#             polygon = []
#             cuboid = []
#             line = []
#             box = []
#             idx_polygon = []
#             idx_cuboid = []
#             idx_line = []
#             idx_box = []
#             median = 0  # noqa: F841
#             all_objects = []  # noqa: F841
#             CUBOID_LEN = 8  # noqa: F841
#             LINE_LEN = 2  # noqa: F841
#             BOX_LEN = 2  # noqa: F841
#             POLYGON_LEN = 4  # noqa: F841
#             for frame in grappa_json:
#                 if frame.get("cuboidDetections", None):
#                     for prediction in frame["cuboidDetections"]:
#                         if prediction["subClass"] == "car":
#                             value_coordinates = prediction["keypoints"]
#                             for element in value_coordinates:
#                                 element[1] = element[1] - 16  # TODO To remove this in future jsons
#                             idx_cuboid.append(frame["timestamp"] - 1)  # TODO To remove this in future jsons
#                             cuboid.append(
#                                 PredictionObject(
#                                     is_tp=False,
#                                     score=prediction["confidence"],
#                                     timestamp=frame["timestamp"] - 1,
#                                     coordinates=value_coordinates,
#                                     iou=0,
#                                 )
#                             )
#                 if frame.get("boundingBoxDetections", None):
#                     for prediction in frame["boundingBoxDetections"]:
#                         if prediction["subClass"] == "pedestrian":
#                             value_coordinates = prediction["keypoints"]
#                             for element in value_coordinates:
#                                 element[1] = element[1] - 16  # TODO To remove this in future jsons
#                             idx_box.append(frame["timestamp"] - 1)  # TODO To remove this in future jsons
#                             box.append(
#                                 PredictionObject(
#                                     is_tp=False,
#                                     score=prediction["confidence"],
#                                     timestamp=frame["timestamp"] - 1,
#                                     coordinates=value_coordinates,
#                                     iou=0,
#                                 )
#                             )
#                 if frame.get("wheelStopperDetections", None):
#                     for prediction in frame["wheelStopperDetections"]:
#                         if prediction["subClass"] == "wheelStopper":
#                             value_coordinates = prediction["keypoints"]
#                             for element in value_coordinates:
#                                 element[1] = element[1] - 16  # TODO To remove this in future jsons
#                             idx_line.append(frame["timestamp"] - 1)  # TODO To remove this in future jsons
#                             line.append(
#                                 PredictionObject(
#                                     is_tp=False,
#                                     score=prediction["confidence"],
#                                     timestamp=frame["timestamp"] - 1,
#                                     coordinates=value_coordinates,
#                                     iou=0,
#                                 )
#                             )
#                 if frame.get("parkingSpotDetections", None):
#                     for prediction in frame["parkingSpotDetections"]:
#                         if prediction["subClass"] == "normalparkingSpot":

#                             value_coordinates = prediction["keypoints"]
#                             for element in value_coordinates:
#                                 element[1] = element[1] - 16  # TODO To remove this in future jsons
#                             idx_polygon.append(frame["timestamp"] - 1)  # TODO To remove this in future jsons
#                             polygon.append(
#                                 PredictionObject(
#                                     is_tp=False,
#                                     score=prediction["confidence"],
#                                     timestamp=frame["timestamp"] - 1,
#                                     coordinates=value_coordinates,
#                                     iou=0,
#                                 )
#                             )

#             class_dictionary["Box"] = pd.Series(box, index=idx_box, name=GrappaConstants.BOX)
#             class_dictionary["Cuboid"] = pd.Series(cuboid, index=idx_cuboid, name=GrappaConstants.CUBOID)
#             class_dictionary["Line"] = pd.Series(line, index=idx_line, name=GrappaConstants.LINE)
#             class_dictionary["Polygon"] = pd.Series(polygon, index=idx_polygon, name=GrappaConstants.POLYGON)
#             return class_dictionary

#         def read_json_gt(data_gt):
#             stored_gt = {
#                 "Line": [],
#                 "Cuboid": [],
#                 "Box": [],
#                 "Polygon": [],
#             }

#             object_name = ""  # noqa: F841
#             value_coordinates = []  # noqa: F841
#             timestamp = []
#             first_timestamp = 0  # noqa: F841
#             polygon = []
#             cuboid = []
#             line = []
#             box = []
#             idx_polygon = []
#             idx_cuboid = []
#             idx_line = []
#             idx_box = []
#             median = 0  # noqa: F841
#             all_objects = []  # noqa: F841
#             CUBOID_LEN = 8  # noqa: F841
#             LINE_LEN = 2  # noqa: F841
#             BOX_LEN = 2  # noqa: F841
#             POLYGON_LEN = 4  # noqa: F841
#             for frame in data_gt:
#                 if frame.get("timestamp", None):
#                     timestamp.append(frame["timestamp"])
#                 if frame.get("polygon", None):
#                     if frame["polygon"].get("labels", None):
#                         for object in frame["polygon"]["labels"]:
#                             # if object['ignored'] is not True:
#                             # value_coordinates = object['keypoints']
#                             idx_polygon.append(frame["timestamp"])

#                             polygon.append(
#                                 GroundTruthObject(
#                                     timestamp=frame["timestamp"],
#                                     coordinates=object["keypoints"],
#                                     ignore=object["ignored"],
#                                     ignore_box=False,
#                                 )
#                             )

#                     if frame["polygon"].get("ignore_boxes", None):
#                         for object in frame["polygon"]["ignore_boxes"]:
#                             # if object['ignored'] is not True:
#                             # value_coordinates = object['keypoints']
#                             idx_polygon.append(frame["timestamp"])
#                             polygon.append(
#                                 GroundTruthObject(
#                                     timestamp=frame["timestamp"], coordinates=object, ignore=True, ignore_box=True
#                                 )
#                             )

#                 if frame.get("line", None):
#                     if frame["line"].get("labels", None):
#                         for object in frame["line"]["labels"]:
#                             # if object['ignored'] is not True and \
#                             #     (object['attributes'].get('class_name',None) == 'wheel_stopper' or object['attributes'] == {}):
#                             if (
#                                 object["attributes"].get("class_name", None) == "wheel_stopper"
#                                 or object["attributes"] == {}
#                             ):
#                                 # value_coordinates = object['keypoints']
#                                 idx_line.append(frame["timestamp"])
#                                 line.append(
#                                     GroundTruthObject(
#                                         timestamp=frame["timestamp"],
#                                         coordinates=object["keypoints"],
#                                         ignore=object["ignored"],
#                                         ignore_box=False,
#                                     )
#                                 )
#                     if frame["line"].get("ignore_boxes", None):
#                         for object in frame["line"]["ignore_boxes"]:
#                             # if object['ignored'] is not True:
#                             # value_coordinates = object['keypoints']
#                             idx_line.append(frame["timestamp"])
#                             line.append(
#                                 GroundTruthObject(
#                                     timestamp=frame["timestamp"], coordinates=object, ignore=True, ignore_box=True
#                                 )
#                             )

#                 if frame.get("bbox", None):
#                     if frame["bbox"].get("labels", None):
#                         for object in frame["bbox"]["labels"]:
#                             # if object['ignored'] is not True and object['attributes']['class_name'] == 'pedestrian':
#                             if object["attributes"]["class_name"] == "pedestrian":
#                                 # value_coordinates = object['keypoints']
#                                 idx_box.append(frame["timestamp"])
#                                 box.append(
#                                     GroundTruthObject(
#                                         timestamp=frame["timestamp"],
#                                         coordinates=object["keypoints"],
#                                         ignore=object["ignored"],
#                                         ignore_box=False,
#                                     )
#                                 )
#                     if frame["bbox"].get("ignore_boxes", None):
#                         for object in frame["bbox"]["ignore_boxes"]:
#                             # if object['ignored'] is not True:
#                             # value_coordinates = object['keypoints']
#                             idx_box.append(frame["timestamp"])
#                             box.append(
#                                 GroundTruthObject(
#                                     timestamp=frame["timestamp"], coordinates=object, ignore=True, ignore_box=True
#                                 )
#                             )

#                 if frame.get("cuboid", None):
#                     if frame["cuboid"].get("labels", None):
#                         for object in frame["cuboid"]["labels"]:
#                             if object["attributes"]["class_name"] == "car":
#                                 # if object['ignored'] is not True and object['attributes']['class_name'] == 'car':
#                                 # value_coordinates = object['keypoints']
#                                 idx_cuboid.append(frame["timestamp"])
#                                 cuboid.append(
#                                     GroundTruthObject(
#                                         timestamp=frame["timestamp"],
#                                         coordinates=object["keypoints"],
#                                         ignore=object["ignored"],
#                                         ignore_box=False,
#                                     )
#                                 )
#                 if frame["cuboid"].get("ignore_boxes", None):
#                     for object in frame["cuboid"]["ignore_boxes"]:
#                         # if object['ignored'] is not True:
#                         # value_coordinates = object['keypoints']
#                         idx_cuboid.append(frame["timestamp"])
#                         cuboid.append(
#                             GroundTruthObject(
#                                 timestamp=frame["timestamp"], coordinates=object, ignore=True, ignore_box=True
#                             )
#                         )
#             stored_gt["Box"] = pd.Series(box, index=idx_box, name=GrappaConstants.BOX)
#             stored_gt["Cuboid"] = pd.Series(cuboid, index=idx_cuboid, name=GrappaConstants.CUBOID)
#             stored_gt["Line"] = pd.Series(line, index=idx_line, name=GrappaConstants.LINE)
#             stored_gt["Polygon"] = pd.Series(polygon, index=idx_polygon, name=GrappaConstants.POLYGON)
#             return timestamp, stored_gt

#         def calculate_iou_polygon(poly1, poly2):
#             def area(poly):
#                 # Compute the area of a polygon using the shoelace formula
#                 area = 0
#                 n = len(poly)
#                 for i in range(n):
#                     j = (i + 1) % n
#                     area += poly[i][0] * poly[j][1]
#                     area -= poly[j][0] * poly[i][1]
#                 return abs(area) / 2

#             def intersection_area(poly1, poly2):
#                 # Compute the intersection area between two polygons
#                 min_x1 = min(p[0] for p in poly1)
#                 max_x1 = max(p[0] for p in poly1)
#                 min_y1 = min(p[1] for p in poly1)
#                 max_y1 = max(p[1] for p in poly1)
#                 min_x2 = min(p[0] for p in poly2)
#                 max_x2 = max(p[0] for p in poly2)
#                 min_y2 = min(p[1] for p in poly2)
#                 max_y2 = max(p[1] for p in poly2)

#                 intersection_x = max(0, min(max_x1, max_x2) - max(min_x1, min_x2))
#                 intersection_y = max(0, min(max_y1, max_y2) - max(min_y1, min_y2))
#                 return intersection_x * intersection_y

#             area_union = area(poly1) + area(poly2)
#             area_intersection = intersection_area(poly1, poly2)
#             iou = area_intersection / (area_union - area_intersection) if area_union - area_intersection > 0 else 0

#             return iou

#         def _keypoint_vec_to_bbox2d_vec(bbox) -> Tensor:
#             keypoints = torch.tensor(bbox)

#             xy_mins = keypoints.min(dim=-2).values
#             xy_maxes = keypoints.max(dim=-2).values
#             return torch.stack([xy_mins, xy_maxes], dim=-2)

#         def _calculate_bbox2d_IoU_matrix(bbox2ds_a: Tensor, bbox2ds_b: Tensor) -> Tensor:
#             # I split this part of the function into this helper to make unit testing simpler
#             area_a = (bbox2ds_a[..., 1, :] - bbox2ds_a[..., 0, :]).clamp(min=0).prod(dim=-1)
#             area_b = (bbox2ds_b[..., 1, :] - bbox2ds_b[..., 0, :]).clamp(min=0).prod(dim=-1)

#             inter_top_left = torch.maximum(bbox2ds_a[..., 0, :], bbox2ds_b[..., 0, :])
#             inter_bot_right = torch.minimum(bbox2ds_a[..., 1, :], bbox2ds_b[..., 1, :])
#             inter_area = (inter_bot_right - inter_top_left).clamp(min=0).prod(dim=-1)

#             iou_matrix = inter_area / (area_a + area_b - inter_area)

#             return iou_matrix

#         def calculate_iou_bbox(bbox1, bbox2):
#             xy_res = torch.tensor([384, 512])
#             bbox2ds_a = _keypoint_vec_to_bbox2d_vec(bbox1)
#             bbox2ds_b = _keypoint_vec_to_bbox2d_vec(bbox2)
#             upscaled_bbox2ds_a = xy_res * bbox2ds_a
#             upscaled_bbox2ds_b = xy_res * bbox2ds_b
#             iou = _calculate_bbox2d_IoU_matrix(bbox2ds_a=upscaled_bbox2ds_a, bbox2ds_b=upscaled_bbox2ds_b)

#             return iou

#         def calculate_iou_line_before(line1, line2):
#             # Calculate the length of each line
#             length_line1 = calculate_distance(line1[0], line1[1])
#             length_line2 = calculate_distance(line2[0], line2[1])

#             # Calculate the endpoints of the overlapping segment
#             intersection_start = max(min(line1[0][0], line1[1][0]), min(line2[0][0], line2[1][0]))
#             intersection_end = min(max(line1[0][0], line1[1][0]), max(line2[0][0], line2[1][0]))

#             # Check if there is no overlap
#             if intersection_start >= intersection_end:
#                 intersection_length = 0
#             else:
#                 intersection_length = intersection_end - intersection_start

#             # Calculate the union length
#             union_length = length_line1 + length_line2 - intersection_length

#             # Calculate IoU
#             iou = intersection_length / union_length if union_length > 0 else 0
#             return iou

#         def calculate_iou_bbox_before_galf(bbox1, bbox2):

#             x1, y1 = bbox1[0]
#             w1, h1 = bbox1[1]

#             x2, y2 = bbox2[0]
#             w2, h2 = bbox2[1]

#             x_left = max(x1, x2)
#             y_top = max(y1, y2)
#             x_right = min(x1 + w1, x2 + w2)
#             y_bottom = min(y1 + h1, y2 + h2)

#             intersection_area = max(0, x_right - x_left) * max(0, y_bottom - y_top)
#             area_bbox1 = w1 * h1
#             area_bbox2 = w2 * h2
#             union_area = area_bbox1 + area_bbox2 - intersection_area
#             # Calculate the IoU
#             iou = intersection_area / union_area
#             return iou

#         def calculate_distance(point1, point2):
#             # Calculate the Euclidean distance between two points
#             return ((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2) ** 0.5

#         def iou(poly1, poly2):
#             """Calculate Intersection over Union (IoU) of two polygons."""
#             # Create Shapely polygons from input lists of coordinates
#             iou_value = 0
#             try:
#                 poly1_shapely = shapely_Polygon(poly1)
#                 poly2_shapely = shapely_Polygon(poly2)
#                 if not poly1_shapely.is_valid:

#                     poly1_shapely = poly1_shapely.buffer(0)
#                 if not poly2_shapely.is_valid:

#                     poly2_shapely = poly2_shapely.buffer(0)
#                 # Calculate intersection area
#                 intersection_area = poly1_shapely.intersection(poly2_shapely).area

#                 # Calculate union area
#                 union_area = poly1_shapely.union(poly2_shapely).area

#                 # Calculate IoU
#                 iou_value = intersection_area / union_area if union_area > 0 else 0.0
#             except Exception as err:
#                 print("An exception occurred")
#                 print(str(err))

#             return iou_value

#         def calculate_iou_line(line1, line2):
#             # # Calculate the length of each line
#             # length_line1 = calculate_distance(line1[0], line1[1])
#             # length_line2 = calculate_distance(line2[0], line2[1])

#             # # Calculate the endpoints of the overlapping segment
#             # intersection_start = max(min(line1[0][0], line1[1][0]), min(line2[0][0], line2[1][0]))
#             # intersection_end = min(max(line1[0][0], line1[1][0]), max(line2[0][0], line2[1][0]))

#             # # Check if there is no overlap
#             # if intersection_start >= intersection_end:
#             #     intersection_length = 0
#             # else:
#             #     intersection_length = intersection_end - intersection_start

#             # # Calculate the union length
#             # union_length = length_line1 + length_line2 - intersection_length
#             pred_object_keypoints = torch.Tensor(line1)
#             gt_object_keypoints = torch.Tensor(line2)
#             # # Calculate IoU
#             # iou = intersection_length / union_length if union_length > 0 else 0
#             input_resolution = [512, 384]
#             xy_res = torch.tensor([input_resolution[1], input_resolution[0]]).to()
#             pred_segments = xy_res * pred_object_keypoints.to()
#             gt_segments = xy_res * gt_object_keypoints.to()

#             # Calculate midpoints for each line segment
#             pred_midpoints = pred_segments.mean(dim=-2)
#             gt_midpoints = gt_segments.mean(dim=-2)

#             # Calculate the length of each GT wheelstopper
#             gt_segment_lengths: Tensor = torch.norm(gt_segments[..., 1, :] - gt_segments[..., 0, :], dim=-1)

#             # Calculate midpoint distance matrix
#             distances: Tensor = torch.norm(gt_segments - pred_segments, dim=-1).sum(dim=-1) + (
#                 3 * torch.norm(gt_midpoints - pred_midpoints, dim=-1)
#             )

#             # Normalize the midpoint distance matrix by the length of each GT wheelstopper
#             distances = distances / gt_segment_lengths

#             return distances.cpu()

#         def calculate_iou_cuboid(cuboid1, cuboid2):
#             # Calculate intersection rectangle coordinates
#             xmin_inter = max(cuboid1[0][0], cuboid2[0][0])
#             ymin_inter = max(cuboid1[0][1], cuboid2[0][1])
#             xmax_inter = min(cuboid1[2][0], cuboid2[2][0])
#             ymax_inter = min(cuboid1[4][1], cuboid2[4][1])

#             # Calculate intersection area
#             intersection_area = max(0, xmax_inter - xmin_inter) * max(0, ymax_inter - ymin_inter)

#             # Calculate union area
#             cuboid1_area = (cuboid1[2][0] - cuboid1[0][0]) * (cuboid1[4][1] - cuboid1[0][1])
#             cuboid2_area = (cuboid2[2][0] - cuboid2[0][0]) * (cuboid2[4][1] - cuboid2[0][1])
#             union_area = cuboid1_area + cuboid2_area - intersection_area

#             # Calculate IoU
#             iou = intersection_area / union_area if union_area > 0 else 0

#             return iou

#         def calculate_galf_style(pred_results: List[PredictionObject], gt_count):
#             """Adaptation calculation from galf for performance matrix"""
#             pred_results = pred_results.tolist()
#             pred_results.sort(reverse=True)

#             best_f1 = 0.0
#             tp_count = 0
#             fp_count = 0
#             iter_count = 0
#             fn_count = 0
#             best_rec = 0
#             best_prec = 0
#             precision_interp = [1.0]
#             recall_interp = [0.0]
#             precision = []
#             recall = []
#             f1 = []
#             tp = []
#             fp = []
#             fn = []
#             fppi = []  # false positive per image
#             fnpi = []  # false negative per image
#             tppi = []  # true positive per image
#             score = []  # confidence
#             thresholding_index = 0

#             for pred_result in pred_results:
#                 if pred_result.is_tp:
#                     tp_count += 1
#                     iter_count += 1
#                     if gt_count > 0:
#                         precision_interp.append(tp_count / iter_count)
#                         recall_interp.append(tp_count / gt_count)
#                 else:
#                     fp_count += 1
#                     iter_count += 1
#                 with np.errstate(invalid="ignore"):  # Ensures NaNs are silently returned on division by 0
#                     current_precision = np.divide(tp_count, iter_count).item()  # TP / (TP + FP)
#                     current_recall = np.divide(tp_count, gt_count).item()  # TP / (TP + FN)
#                     current_f1 = np.divide(
#                         2.0 * current_precision * current_recall,
#                         (current_precision + current_recall),
#                     ).item()
#                     # [1,2,3,4,5]
#                 fn_count = gt_count - tp_count
#                 precision.append(current_precision)
#                 recall.append(current_recall)
#                 f1.append(current_f1)
#                 tp.append(tp_count)
#                 fp.append(fp_count)
#                 fn.append(gt_count - tp_count)
#                 tppi.append(tp_count / gt_count)
#                 fppi.append(fp_count / gt_count)
#                 fnpi.append(fn_count / gt_count)
#                 score.append(pred_result.score)

#                 if current_f1 > best_f1:
#                     best_f1 = current_f1
#                     best_prec = current_precision
#                     best_rec = current_recall
#                     thresholding_index = pred_result.score
#                 elif current_f1 is None:
#                     best_f1 = 0
#             fppi = max(fppi)
#             fnpi = max(fnpi)
#             tppi = max(tppi)
#             precision_interp.reverse()

#             for i in range(len(precision_interp) - 1):
#                 if precision_interp[i + 1] < precision_interp[i]:
#                     precision_interp[i + 1] = precision_interp[i]

#             precision_interp.reverse()

#             ap = 0.0
#             if len(precision_interp) != 0 and iter_count != 0:
#                 for i in range(1, len(precision_interp)):
#                     ap += precision_interp[i] * (recall_interp[i] - recall_interp[i - 1])
#             elif iter_count == 0:  # No predictions should cause division by zero
#                 ap = float("nan")
#             ap = ap
#             return [
#                 ap,
#                 tp_count,
#                 fp_count,
#                 fn_count,
#                 best_prec,
#                 best_rec,
#                 fppi,
#                 best_f1,
#                 tppi,
#                 fnpi,
#                 thresholding_index,
#                 [score, recall, precision, f1],
#             ]

#         def remove_ignorebox(class_type, obj1, obj2):
#             """Calculate iou based of time and type of object"""
#             if "Box" in class_type:
#                 # return calculate_iou_bbox(obj1, obj2)
#                 # return calculate_iou_bbox_before_galf(obj1, obj2)ignorebox_bbox
#                 return ignorebox_bbox(obj1, obj2)
#             if "Polygon" in class_type:
#                 # return calculate_iou_polygon(obj1, obj2)
#                 # return iou(obj1, obj2)polygon_bbox_iou
#                 return polygon_bbox_iou(obj1, obj2)
#             if "Line" in class_type:
#                 # return calculate_iou_line(obj1, obj2)
#                 # return calculate_iou_line_before(obj1, obj2)ignore_box_line
#                 # return ignore_box_line(obj1, obj2)
#                 thickness = 0.1
#                 return line_iou_last(obj1, obj2, thickness)
#             if "Cuboid" in class_type:
#                 return 0.0
#                 # return cuboid_bbox_iou(obj1, obj2)
#                 return cuboid_bbox_iou(obj1, obj2)
#             return 0

#         def line_inside_bbox_with_threshold(line_coords, bbox_coords, threshold=0.5):
#             # Unpack the line coordinates
#             (x1, y1), (x2, y2) = line_coords

#             # Unpack the bounding box coordinates
#             (bx1, by1), (bx2, by2) = bbox_coords

#             # Create the bounding box
#             bbox = box(bx1, by1, bx2, by2)

#             # Create the line
#             line = LineString([(x1, y1), (x2, y2)])

#             # Calculate intersection
#             intersection = line.intersection(bbox)

#             if intersection.is_empty:
#                 return False

#             # Calculate the proportion of the line inside the bounding box
#             line_length = line.length
#             intersection_length = (
#                 intersection.length
#                 if isinstance(intersection, LineString)
#                 else sum(seg.length for seg in intersection.geoms)
#             )

#             proportion_inside = intersection_length / line_length

#             return proportion_inside >= threshold

#         def calculate_polygon_area(polygon):
#             # Calculate the area of a polygon using the shoelace formula
#             n = len(polygon)
#             area = 0.0
#             for i in range(n):
#                 j = (i + 1) % n
#                 area += polygon[i][0] * polygon[j][1]
#                 area -= polygon[j][0] * polygon[i][1]
#             area = abs(area) / 2.0
#             return area

#         def calculate_bbox_area(bbox):
#             # Calculate the area of a bounding box
#             width = bbox[1][0] - bbox[0][0]
#             height = bbox[1][1] - bbox[0][1]
#             area = width * height
#             return area

#         def calculate_intersection_last(polygon, bbox):
#             # Calculate the intersection area between the polygon and the bbox

#             # Get the coordinates of the bbox
#             bbox_x1, bbox_y1 = bbox[0]
#             bbox_x2, bbox_y2 = bbox[1]

#             # Initialize the intersection points list
#             intersection_points = []

#             # Iterate through the polygon vertices
#             for i in range(len(polygon)):
#                 # Get the coordinates of two consecutive vertices
#                 x1, y1 = polygon[i]
#                 x2, y2 = polygon[(i + 1) % len(polygon)]

#                 # Calculate the intersection points between the bbox and the line segment
#                 x_intersect = max(min(x1, x2), min(bbox_x1, bbox_x2))
#                 y_intersect = max(min(y1, y2), min(bbox_y1, bbox_y2))

#                 # Check if the intersection point is inside the bbox
#                 if (bbox_x1 <= x_intersect <= bbox_x2) and (bbox_y1 <= y_intersect <= bbox_y2):
#                     intersection_points.append((x_intersect, y_intersect))

#             # Calculate the area of the intersection polygon
#             intersection_area = calculate_polygon_area(intersection_points)
#             return intersection_area

#         def calculate_union_last(polygon, bbox, intersection_area_last):
#             # Calculate the area of the polygon
#             polygon_area = calculate_polygon_area(polygon)

#             # Calculate the area of the bbox
#             bbox_area = calculate_bbox_area(bbox)

#             # Calculate the union area
#             union_area = polygon_area + bbox_area - intersection_area_last
#             return union_area

#         def convert_series_to_list(pandas_series, timestamp):
#             converted_list = []
#             if "Series" in str(type(pandas_series.loc[timestamp])):
#                 for value in pandas_series.at[timestamp]:
#                     converted_list.append(value)
#             else:
#                 converted_list.append(pandas_series.at[timestamp])
#             return converted_list

#         def calculate_iou_last(polygon, bbox, intersection_area_last):
#             union_area_last = calculate_union_last(polygon, bbox, intersection_area_last)
#             iou = intersection_area_last / union_area_last
#             return iou

#         def get_iou(class_type, obj1, obj2):
#             """Calculate iou based of time and type of object"""
#             if "Box" in class_type:
#                 # return calculate_iou_bbox(obj1, obj2)
#                 return calculate_iou_bbox_before_galf(obj1, obj2)
#             if "Polygon" in class_type:
#                 # return calculate_iou_polygon(obj1, obj2)
#                 return iou(obj1, obj2)
#             if "Line" in class_type:
#                 # return calculate_iou_line(obj1, obj2)

#                 return calculate_iou_line_before(obj1, obj2)
#             if "Cuboid" in class_type:
#                 return calculate_iou_cuboid(obj1, obj2)

#             return 0

#         def check_series(grappa_series, gt_series):
#             gt_coords: list[GroundTruthObject] = []
#             grappa_coords: list[PredictionObject] = []
#             iou_dict = {}
#             c = 0
#             THRESHOLD_IOU = {
#                 GrappaConstants.LINE: 0.5,
#                 GrappaConstants.CUBOID: 0.5,
#                 GrappaConstants.POLYGON: 0.5,
#                 GrappaConstants.BOX: 0.5,
#             }
#             threshold_iou = 0.5  # noqa: F841
#             innter_c = 0  # noqa: F841
#             timestamp = 0

#             # 217k total gt
#             # 200k ignore box
#             # 10k gt.ignore = True
#             # 6-7k gr.ignore = false
#             try:
#                 grappa_series  # noqa: B018
#                 gt_series[gt_series.apply(lambda x: x.ignore)]
#                 ignored_bbox_trial = 0
#                 ignored_from_ignore_bbox = 0
#                 # Perform cleanup for ignore_box==True
#                 ignore_box_gt = gt_series[gt_series.apply(lambda x: x.ignore_box)]
#                 gt_series = gt_series[gt_series.apply(lambda x: not x.ignore_box)]
#                 for timestamp in list(dict.fromkeys(grappa_series.index)):
#                     # [x for x in list(dict.fromkeys(grappa_series.index)) if x in list(dict.fromkeys(ignore_box_gt.index))]
#                     # [x for x in [1,2,3] if x in [2,4,5]]
#                     if timestamp in ignore_box_gt.index:
#                         ignored_bbox_trial += 1
#                         gt_coords.clear()
#                         grappa_coords.clear()

#                         gt_coords = convert_series_to_list(ignore_box_gt, timestamp)
#                         grappa_coords = convert_series_to_list(grappa_series, timestamp)

#                         for gt in gt_coords:
#                             c = 0
#                             iou_dict.clear()
#                             for prediction in grappa_coords:
#                                 # iou = round(remove_ignorebox(grappa_series.name ,prediction.coordinates, gt.coordinates),3)
#                                 iou = 0.0
#                                 if grappa_series.name == "Polygon":
#                                     intersection_area_last = calculate_intersection_last(
#                                         prediction.coordinates, gt.coordinates
#                                     )
#                                     iou = calculate_iou_last(
#                                         prediction.coordinates, gt.coordinates, intersection_area_last
#                                     )
#                                 if grappa_series.name == "Line":
#                                     iou = calculate_iou_line_before(prediction.coordinates, gt.coordinates)
#                                 # if line_inside_bbox_with_threshold(prediction.coordinates, gt.coordinates):
#                                 #    prediction.ignore = True
#                                 if grappa_series.name == "Box":
#                                     iou, bbox1, bbox2 = last_iou_bbox(prediction.coordinates, gt.coordinates)
#                                 # print(f"IoU: {iou}")
#                                 # if iou >=0.5

#                                 # if 0.1<=iou <= 0.5:
#                                 #     ignored_bbox_trial+=1
#                                 # Plot the bounding boxes
#                                 # plot_bboxes(prediction.coordinates, gt.coordinates)
#                                 # print(iou)
#                                 # print()
#                                 # iou = remove_ignorebox(grappa_series.name ,prediction.coordinates, gt.coordinates)
#                                 # print(f"IoU: {iou}")

#                                 # Plot the shapes
#                                 # if iou > 0.00001:
#                                 #    plot_shapes(line, bbox, prediction.coordinates, gt.coordinates)
#                                 if iou >= THRESHOLD_IOU[grappa_series.name]:
#                                     # plot_polygon_and_bbox(prediction.coordinates, gt.coordinates)
#                                     iou_dict.setdefault(c, iou)
#                                 # else:
#                                 #   plot_polygon_and_bbox(prediction.coordinates, gt.coordinates)

#                                 c += 1
#                                 # prediction.iou = iou
#                             if iou_dict:
#                                 # Get the max iou from the dict and use that index to set object to TP
#                                 prediction_index = max(iou_dict.keys(), key=(lambda key: iou_dict[key]))
#                                 if gt.ignore == True:  # noqa: E712
#                                     ignored_from_ignore_bbox += 1
#                                     grappa_coords[prediction_index].ignore = True
#                                 else:
#                                     print("*******************************************")
#                                 # else:
#                                 #     grappa_coords[prediction_index].is_tp = True
#                                 grappa_coords.pop(prediction_index)
#                 # grappa_series[grappa_series.apply(lambda x: x.ignore)]

#                 ignore_box_gt = gt_series[gt_series.apply(lambda x: x.ignore)]
#                 gt_series = gt_series[gt_series.apply(lambda x: not x.ignore)]  # BBox implementation

#                 ignored_from_gt_ignore_equals_true = 0
#                 # Punem grappa in shaica ( FALSE/IGNORE) tot ce se pupa cu un GT.ignore= true
#                 for timestamp in list(dict.fromkeys(grappa_series.index)):

#                     if timestamp in ignore_box_gt.index:
#                         gt_coords.clear()
#                         grappa_coords.clear()
#                         gt_coords = convert_series_to_list(ignore_box_gt, timestamp)
#                         grappa_coords = convert_series_to_list(grappa_series, timestamp)

#                         for gt in gt_coords:
#                             c = 0
#                             iou_dict.clear()
#                             for prediction in grappa_coords:
#                                 iou = round(get_iou(grappa_series.name, prediction.coordinates, gt.coordinates), 3)
#                                 if grappa_series.name == "Box":
#                                     iou, bbox1, bbox2 = last_iou_bbox(prediction.coordinates, gt.coordinates)
#                                 if iou >= THRESHOLD_IOU[grappa_series.name]:
#                                     iou_dict.setdefault(c, iou)
#                                 c += 1
#                                 # prediction.iou = iou
#                             if iou_dict:
#                                 ignored_from_gt_ignore_equals_true += 1
#                                 # Get the max iou from the dict and use that index to set object to TP
#                                 prediction_index = max(iou_dict.keys(), key=(lambda key: iou_dict[key]))
#                                 if gt.ignore == True:  # noqa: E712
#                                     grappa_coords[prediction_index].ignore = True
#                                 # else:
#                                 #     grappa_coords[prediction_index].is_tp = True
#                                 grappa_coords.pop(prediction_index)
#                 # gt_series = gt_series[gt_series.apply(lambda x: not x.ignore)]
#                 grappa_series = grappa_series[grappa_series.apply(lambda x: not x.ignore)]
#                 # grappa_series = grappa_series[grappa_series.apply(lambda x: x.is_tp)]
#                 gt_coords.clear()
#                 grappa_coords.clear()
#                 iou_dict.clear()
#                 c = 0
#                 timestamp = 0

#                 for timestamp in list(dict.fromkeys(grappa_series.index)):
#                     if timestamp in gt_series.index:
#                         gt_coords.clear()
#                         grappa_coords.clear()
#                         gt_coords = convert_series_to_list(gt_series, timestamp)
#                         grappa_coords = convert_series_to_list(grappa_series, timestamp)

#                         for gt in gt_coords:
#                             c = 0
#                             iou_dict.clear()
#                             for prediction in grappa_coords:
#                                 iou = round(get_iou(grappa_series.name, prediction.coordinates, gt.coordinates), 3)
#                                 if grappa_series.name == "Box":
#                                     iou, bbox1, bbox2 = last_iou_bbox(prediction.coordinates, gt.coordinates)
#                                 if iou >= THRESHOLD_IOU[grappa_series.name]:
#                                     iou_dict.setdefault(c, iou)
#                                 c += 1
#                                 prediction.iou = iou
#                             if iou_dict:
#                                 # Get the max iou from the dict and use that index to set object to TP
#                                 prediction_index = max(iou_dict.keys(), key=(lambda key: iou_dict[key]))
#                                 if gt.ignore == True:  # noqa: E712
#                                     grappa_coords[prediction_index].ignore = True
#                                 else:
#                                     grappa_coords[prediction_index].is_tp = True
#                                 grappa_coords.pop(prediction_index)

#                 print()

#             except Exception as errrr:
#                 print(timestamp)
#                 print(str(errrr))
#                 exc_type, exc_obj, exc_tb = sys.exc_info()
#                 fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
#                 print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")
#             # grappa_series = grappa_series[grappa_series.apply(lambda x:  x.ignore)]
#             # grappa_series = grappa_series[grappa_series.apply(lambda x: x.is_tp)]
#             return grappa_series, gt_series

#         class_dictionary = read_json_grappa(data_grappa)

#         timestamp_gt, gt_classes = read_json_gt(data_gt)

#         stored_results = {}

#         import time

#         # Iterate through both dicts and set True the is_tp attribute in grappa
#         for class_name in gt_classes.keys():
#             print(class_name)
#             start_time = time.time()
#             if class_name == GrappaConstants.BOX:
#                 grappa_series, gt_series = check_series(class_dictionary[class_name], gt_classes[class_name])
#                 class_dictionary.update({class_name: grappa_series})
#                 gt_classes.update({class_name: gt_series})
#                 print(time.time() - start_time)
#                 stored_results.setdefault(
#                     class_name, calculate_galf_style(class_dictionary[class_name], len(gt_classes[class_name]))
#                 )
#             # gt_classes[class_name]
#             # len(gt_classes[class_name])
#         return stored_results, class_dictionary, gt_classes
