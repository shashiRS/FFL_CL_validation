"""
SI Slot Offer KPI

This KPI is calculated based on measurement data and associated JSON files,
which must be located in the same directory.

The recording name must be included in the filename of the corresponding JSON file.
"""

import base64
import io
import json
import logging
import math
import os
import sys

import numpy as np
import pandas as pd

# import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
from scipy.spatial import KDTree
from shapely.affinity import rotate
from shapely.geometry import Polygon

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

from tsf.core.results import FALSE, NAN, Result  # nopep8
from tsf.core.testcase import (
    PreProcessor,
    TestCase,
    TestStep,
    register_inputs,
    register_pre_processor,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.io.signals import SignalDefinition

import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport
from pl_parking.PLP.MF.constants import SlotOffer

__author__ = "BA ADAS ENP SIMU KPI"
__copyright__ = "2020-2022, Continental AG"
__version__ = "0.16.2"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

EXAMPLE = "SLOT OFFER SI KPI"


def intersection_fig_trace_method(json_coords, signal_coords):
    """
    Compute the intersection of two polygons defined by JSON and signal coordinates.

    Parameters:
    - json_coords (list of tuples): Coordinates of the JSON polygon.
    - signal_coords (list of tuples): Coordinates of the signal polygon.

    Returns:
    - list of tuples: Coordinates of the intersection polygon.
    """
    # Converting JSON and signal coordinates into polygons for geometric operations.
    json_polygon = Polygon(json_coords)
    signal_polygon = Polygon(signal_coords)
    # intersection_fig_trace = go.Scatter()

    # Calculating the intersection between signal_polygon and json_polygon.
    intersection = signal_polygon.intersection(json_polygon)
    intersection_coords = list(intersection.exterior.coords)

    if not intersection.is_empty:
        intersection_coords = [
            tuple(point[0] for point in intersection_coords),
            tuple(point[1] for point in intersection_coords),
        ]
    return intersection_coords


def calculate_overlap(json_coords, signal_coords):
    """
    Calculate the intersection and percentage overlap between two polygons.

    Parameters:
    - json_coords (list of tuples): Coordinates of the JSON polygon.
    - signal_coords (list of tuples): Coordinates of the signal polygon.

    Returns:
    - tuple: A tuple containing the intersection polygon and the percentage overlap based on json_coords.
    """
    try:
        # Converting JSON and signal coordinates into polygons for geometric operations.
        json_polygon = Polygon(json_coords)
        signal_polygon = Polygon(signal_coords)
    except ValueError as e:
        raise ValueError(f"Invalid polygon coordinates. Reason: {e}") from e

    # Calculating the intersection between signal_polygon and json_polygon.
    intersection = signal_polygon.intersection(json_polygon)

    # Calculate overlap percentage
    overlap_percentage = 0.0

    if not intersection.is_empty:
        intersection_area = intersection.area
        json_polygon_area = json_polygon.area
        signal_polygon_area = signal_polygon.area

        relative_overlap_parking_box_1 = intersection_area / json_polygon_area
        relative_overlap_parking_box_2 = intersection_area / signal_polygon_area
        overlap_percentage = max(relative_overlap_parking_box_1, relative_overlap_parking_box_2) * 100

    return intersection, overlap_percentage


def check_rectangle_fit(polygon, x, y, width, length, step_angle=1):
    """
    Check if a rectangle with given dimensions fits inside a polygon at different angles.

    Parameters:
    - polygon (Polygon): The polygon where the vehicle needs to fit.
    - x, y (float): The coordinates of the center of the rectangle (vehicle).
    - width, length (float): The width and length of the rectangle (vehicle).
    - step_angle (int): The angle step in degrees (default is 1 degree).

    Returns:
    - bool: True if the rectangle fits at some angle, False otherwise.
    """
    half_width = width / 2
    half_length = length / 2

    # Coordinates of the unrotated rectangle
    rect_coords = [
        (x - half_length, y - half_width),
        (x + half_length, y - half_width),
        (x + half_length, y + half_width),
        (x - half_length, y + half_width),
    ]

    # Create the rectangular polygon
    rect_polygon = Polygon(rect_coords)

    # Iterate through angles from 0 to 360 degrees
    for angle in range(0, 180, step_angle):
        # Rotate the rectangle
        rotated_rect_polygon = rotate(rect_polygon, angle, origin="centroid")
        # Check if the rotated rectangle fits inside the polygon
        if polygon.contains(rotated_rect_polygon):
            return True  # Return True if a fit is found

    # If no fit is found, return False
    return False


def calculate_polygon_center(x_coordinates=None, y_coordinates=None, points=None):
    """
    Calculate the center of a polygon based on either a list of x and y coordinates
    or a list of points (as dictionaries with 'x' and 'y' keys).

    Parameters:
    - x_coordinates (list, optional): List of x-coordinates.
    - y_coordinates (list, optional): List of y-coordinates.
    - points (list of dicts, optional): List of points with 'x' and 'y' keys.

    Returns:
    - dict or tuple: Coordinates of the center as a dictionary {'x': center_x, 'y': center_y}
        or as a pair of coordinates: centroid_x, centroid_y.
    """
    if points is not None:
        # If points are provided, calculate the center using the first function.
        number_of_points = len(points)
        sum_x = sum(point["x"] for point in points)
        sum_y = sum(point["y"] for point in points)
        center_x = sum_x / number_of_points
        center_y = sum_y / number_of_points
        return {"x": center_x, "y": center_y}
    elif x_coordinates is not None and y_coordinates is not None:
        # If x and y coordinates are provided, calculate the center using the second function.
        centroid_x = np.mean(x_coordinates)
        centroid_y = np.mean(y_coordinates)
        return centroid_x, centroid_y
    else:
        raise ValueError("Either 'points' or both 'x_coordinates' and 'y_coordinates' must be provided.")


def process_json_section(file_data, timestamp, time_obj_string_timestamp, timestamp_dict_GT, section_name):
    """
    Process a JSON section containing timestamped data related to parking slots.

    Parameters:
        file_data (dict): A dictionary containing JSON data.
        timestamp (int): The timestamp to search for in the data.
        time_obj_string_timestamp (str): The key name representing the timestamp in each timed object.
        timestamp_dict_GT (dict): A dictionary to store timestamps as keys and GT slot information as values
        section_name (str): The name of the section within the file_data dictionary to process.

    Returns:
        tuple: A tuple containing two elements:
            - timestamp_dict_GT (dict): Updated dictionary timestamps as keys and GT slot information as values.
    """
    if section_name in file_data:
        section_data = file_data[section_name]

        # Check if the section data is a list
        if isinstance(section_data, list):
            for entry in section_data:
                if "timedObjs" in entry and isinstance(entry["timedObjs"], list):
                    timed_objs_list = entry["timedObjs"]
                    for timed_obj in timed_objs_list:
                        if timestamp == timed_obj.get(time_obj_string_timestamp):
                            parking_boxes = timed_obj.get("parkingBoxes", [])
                            dict_GT_centers = {}

                            for parking_box in parking_boxes:
                                slot_coordinates_m = parking_box.get("slotCoordinates_m", [])
                                gt_park_slot_center = calculate_polygon_center(points=slot_coordinates_m)
                                gt_park_slot_center_key = tuple(gt_park_slot_center.items())
                                dict_GT_centers[gt_park_slot_center_key] = slot_coordinates_m

                            timestamp_dict_GT[timestamp] = dict_GT_centers
                            break
                        else:
                            pass

    return timestamp_dict_GT


def process_signal_coordinates(timestamp, filtered_df, sg_slot_coords):
    """
    Process signal coordinates for a given timestamp and parking slots.

    Parameters:
        timestamp (int): The timestamp for which coordinates are to be processed.
        filtered_df (DataFrame): A pandas DataFrame containing filtered signal data.
        sg_slot_coords (list): A list of names of signals representing the slot coordinates.

    Returns:
        dict: A dictionary containing processed signal coordinates.
            Keys: Slot coordinates (str)
            Values: Dictionary containing slot center coordinates and corresponding signal coordinates.
                Keys: Slot center coordinates (tuple)
                Values: List of signal coordinates.

    Note:
        The function assumes that the signal coordinates for each slot are stored in the filtered_df DataFrame
        under the corresponding slot coordinate key at the given timestamp.
    """
    coord_dict = {}
    for sg_slot_coord in sg_slot_coords:
        coord_dict[sg_slot_coord] = {}
        vehicle_scanned_coords_1_NEW = [
            {
                "x": filtered_df[sg_slot_coord][timestamp][i],
                "y": filtered_df[sg_slot_coord][timestamp][i + 1],
            }
            for i in range(0, len(filtered_df[sg_slot_coord][timestamp]), 2)
        ]
        scanned_slot_center_NEW = calculate_polygon_center(points=vehicle_scanned_coords_1_NEW)
        scanned_slot_center_NEW = tuple(scanned_slot_center_NEW.items())
        coord_dict[sg_slot_coord][scanned_slot_center_NEW] = vehicle_scanned_coords_1_NEW
    return coord_dict


def are_points_collinear(point1, point2, point3, absolute_tolerance=0.1):
    """
    Check if three points are collinear in a 2D plane, dynamically adjusting for distances.

    Parameters:
    - point1, point2, point3: Dictionaries with 'x' and 'y' keys representing the coordinates of the three points.
    - absolute_tolerance: The maximum allowed deviation for collinearity in meters (e.g., ±0.15 meters).

    Returns:
    - True if the points are collinear within the given tolerance, False otherwise.
    """

    def distance(p1, p2):
        """Calculate the Euclidean distance between two points."""
        return ((p2["x"] - p1["x"]) ** 2 + (p2["y"] - p1["y"]) ** 2) ** 0.5

    def cross_product(p1, p2, p3):
        """Calculate the 2D cross product of three points."""
        return (p2["y"] - p1["y"]) * (p3["x"] - p2["x"]) - (p2["x"] - p1["x"]) * (p3["y"] - p2["y"])

    # Calculate distances between points
    dist1 = distance(point1, point2)
    dist2 = distance(point2, point3)

    # Avoid division by zero (e.g., coincident points)
    if dist1 == 0 or dist2 == 0:
        return False

    # Compute the raw cross-product
    raw_cross = abs(cross_product(point1, point2, point3))

    # Normalize the cross-product
    normalized_cross = raw_cross / (dist1 * dist2)

    # Convert absolute tolerance to a normalized value
    normalized_tolerance = absolute_tolerance / min(dist1, dist2)

    return normalized_cross <= normalized_tolerance


# def are_points_collinear(point1, point2, point3, box_id, file_data, vehicle_local, tolerance):
#     """
#     Check if three points are collinear in a 2D plane, adjusting for distances between points.

#     Parameters:
#     - point1, point2, point3: Dictionaries with 'x' and 'y' keys representing the coordinates of the three points.
#     - tolerance: The maximum allowed difference for the normalized cross-product error.
#     A smaller tolerance requires the points to be more strictly collinear to return True.

#     Returns:
#     - True if the points are collinear within the given tolerance, False otherwise.
#     """

#     def cross_product(p1, p2, p3):
#         return (p2["y"] - p1["y"]) * (p3["x"] - p2["x"]) - (p2["x"] - p1["x"]) * (p3["y"] - p2["y"])

#     error = abs(cross_product(point1, point2, point3))

#     for index in file_data[vehicle_local][0]["timedObjs"][0]["parkingBoxes"]:
#         if index["objectId"] == box_id:
#             if index["TypeofPB"] == "angled":
#                 # Normalize the error by the product of distances
#                 dist1 = math.dist([point1["x"], point1["y"]], [point2["x"], point2["y"]])
#                 dist2 = math.dist([point2["x"], point2["y"]], [point3["x"], point3["y"]])
#                 normalization_factor = dist1 * dist2

#                 return (error / normalization_factor) <= tolerance
#             else:
#                 return error <= tolerance


def process_json_for_collinearity(file_data, timestamp, time_obj_string_timestamp, timestamp_dict_GT, section_name):
    """
    Process a JSON section containing timestamped data related to parking slots.

    Parameters:
        file_data (dict): A dictionary containing JSON data.
        timestamp (int): The timestamp to search for in the data.
        time_obj_string_timestamp (str): The key name representing the timestamp in each timed object.
        timestamp_dict_GT (dict): A dictionary to store timestamps as keys and GT slot information as values
        section_name (str): The name of the section within the file_data dictionary to process.

    Returns:
        tuple: A tuple containing two elements:
            - timestamp_dict_GT (dict): Updated dictionary timestamps as keys and GT slot information as values.
    """
    if section_name in file_data:
        section_data = file_data[section_name]

        # Check if the section data is a list
        if isinstance(section_data, list):
            for entry in section_data:
                if "timedObjs" in entry and isinstance(entry["timedObjs"], list):
                    timed_objs_list = entry["timedObjs"]
                    for timed_obj in timed_objs_list:
                        if timestamp == timed_obj.get(time_obj_string_timestamp):
                            parking_boxes = timed_obj.get("parkingBoxes", [])
                            dict_GT_centers = {}

                            for parking_box in parking_boxes:
                                box_id = parking_box.get("objectId")
                                slot_coordinates_m = parking_box.get("slotCoordinates_m", [])
                                gt_park_slot_center = calculate_polygon_center(points=slot_coordinates_m)
                                gt_park_slot_center_key = (box_id, tuple(gt_park_slot_center.items()))
                                dict_GT_centers[gt_park_slot_center_key] = slot_coordinates_m

                            timestamp_dict_GT[timestamp] = dict_GT_centers
                            break
                        else:
                            pass

    return timestamp_dict_GT


def is_horizontal(line, tolerance=2, angle_tolerance=45):
    """
    Function to check if a line is approximately horizontal.
    Args:
        line (tuple): A tuple of (x1, y1, x2, y2) representing a line.
        tolerance (float): Maximum absolute difference between y-coordinates for near-perfect horizontal lines.
        angle_tolerance (float): Maximum deviation from 0° (or 180° for reversed direction) to consider the line horizontal.
    Returns:
        bool: True if the line is approximately horizontal, False otherwise.
    """
    x1, y1, x2, y2 = line

    # Check coordinate-based tolerance
    if abs(y1 - y2) < tolerance:
        return True

    # Check angle-based tolerance
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0:  # Avoid division by zero; this would be vertical
        return False
    angle = abs(math.degrees(math.atan2(dy, dx)))
    return abs(angle) < angle_tolerance or abs(angle - 180) < angle_tolerance


def find_vertical_lines(points):
    """
    Identifies vertical lines from a set of points and appends them to the provided vertical_lines list.
    Args:
        points (list): A list of dictionaries, where each dictionary represents a point with 'x' and 'y' coordinates.
    Returns:
        list: The list containing the identified vertical lines.
    """
    z = []
    vertical_lines = []

    for point in points:
        for other_point in points:
            if other_point != point:
                line = (point["x"], point["y"], other_point["x"], other_point["y"])
                if is_horizontal(line):
                    z.append(line)

    for line in z:
        x1, y1, x2, y2 = line
        x = min(x1, x2)
        y = y1 if x == x1 else y2
        vertical_lines.append((x, y))

    return vertical_lines


def collinearity_check(timestamp_data, **kwargs):
    """
    Detect the first timestamp where parking box coordinates (from Ground Truth) become collinear
    with a reference line (defined by mirror points) and return a dictionary of box IDs with
    their first collinear timestamp.

    Parameters:
        timestamp_data (dict): A dictionary containing timestamp data.
            Keys: Timestamp (int)
            Values: Dictionary where keys are (ID, coordinate tuples) and values are lists of coordinates.
        tolerance (float): Tolerance level for collinearity check (default is 0.1).
        **kwargs: Additional keyword arguments for collinearity check.
            - mirror_x_left (float): X-coordinate of the left mirror.
            - mirror_x_right (float): X-coordinate of the right mirror.
            - mirror_y_left (float): Y-coordinate of the left mirror.
            - mirror_y_right (float): Y-coordinate of the right mirror.

    Returns:
        dict: A dictionary where keys are parking box IDs and values are the first timestamp where collinearity was detected.
    """
    first_collinear_data = {}
    d_next_to = (
        0.5  # Offset to verify collinearity 0.5 meters beyond where the mirrors clear the front line of the parking box
    )

    for timestamp, coordinate_dict in timestamp_data.items():
        final_vertical_line = []
        for (box_id, _), points in coordinate_dict.items():
            collinear_left = False
            collinear_right = False
            if len(points) < 2:
                continue  # Skip if not enough points to check collinearity
            if (
                kwargs.get("mirror_x_left") is not None
                and kwargs.get("mirror_x_right") is not None
                and kwargs.get("mirror_y_left") is not None
                and kwargs.get("mirror_y_right") is not None
            ):

                vertical_lines = find_vertical_lines(points)

                final_vertical_line = tuple(dict.fromkeys(vertical_lines))
                vertical_lines.clear()
                left_mirror = {"x": kwargs["mirror_x_left"] - d_next_to, "y": kwargs["mirror_y_left"]}
                right_mirror = {"x": kwargs["mirror_x_right"] - d_next_to, "y": kwargs["mirror_y_right"]}
                point1 = {"x": final_vertical_line[0][0], "y": final_vertical_line[0][1]}
                point2 = {"x": final_vertical_line[1][0], "y": final_vertical_line[1][1]}
                if abs(point1["y"] - left_mirror["y"]) < abs(point1["y"] - right_mirror["y"]):
                    collinear_left = are_points_collinear(point1, point2, left_mirror)
                else:
                    collinear_right = are_points_collinear(point1, point2, right_mirror)
                # if abs(point1["y"] - left_mirror["y"]) < abs(point1["y"] - right_mirror["y"]):
                #     collinear_left = are_points_collinear(
                #         point1, point2, left_mirror, box_id, file_data, vehicle_local, tolerance
                #     )
                # else:
                #     collinear_right = are_points_collinear(
                #         point1, point2, right_mirror, box_id, file_data, vehicle_local, tolerance
                #     )

                if (collinear_left or collinear_right) and box_id not in first_collinear_data:
                    # Add the first timestamp for this box ID
                    first_collinear_data[box_id] = timestamp
                    break

    return first_collinear_data


def calculate_polygon_orientation(coords):
    """
    Calculate the orientation of a polygon based on the leftmost line and return the angle in absolute value.

    :param coords: List of tuples (x, y) representing the corners of the polygon.
    :return: The angle of the leftmost line in degrees (absolute value).
    """
    final_vertical_line = []
    if len(coords) < 2:
        raise ValueError("There must be at least 2 points to calculate the orientation.")

    coords = [{"x": point[0], "y": point[1]} for point in coords]
    vertical_lines = find_vertical_lines(coords)
    final_vertical_line = tuple(dict.fromkeys(vertical_lines))
    vertical_lines.clear()

    # Coordinates of the points on the leftmost line
    point1 = {"x": final_vertical_line[0][0], "y": final_vertical_line[0][1]}
    point2 = {"x": final_vertical_line[1][0], "y": final_vertical_line[1][1]}
    (x1, y1) = (point1["x"], point1["y"])
    (x2, y2) = (point2["x"], point2["y"])

    # Calculate the angle in radians
    angle_radians = math.atan2(y2 - y1, x2 - x1)

    # Convert to degrees and take the absolute value
    angle_degrees = abs(math.degrees(angle_radians))

    return angle_degrees


def calculate_center_distances_yaw(center_gt_slot, center_scanned_slot, file_data, parking_box_id, angle):
    """
    Calculates the short and long distances between the ground truth slot center and the scanned slot center,
    considering the orientation and type of parking slot.
    Args:
        center_gt_slot (dict): The center coordinates of the ground truth slot.
        center_scanned_slot (dict): The center coordinates of the scanned slot.
        file_data (dict): The data containing information about the parking boxes.
        parking_box_id (str): The ID of the parking box to check.
        angle (float): The orientation angle of the parking slot.
        **kwargs: Additional keyword arguments.
    Returns:
        tuple: A tuple containing:
            - short_distance (float): The calculated short distance.
            - short_distance_check (bool): Whether the short distance is within the threshold.
            - long_distance (float): The calculated long distance.
            - long_distance_check (bool): Whether the long distance is within the threshold.
    """
    short_distance, short_distance_check, long_distance, long_distance_check = None, False, None, False

    for parking_box in file_data["ApplicationStarted"][0]["timedObjs"][0]["parkingBoxes"]:
        if parking_box["objectId"] == parking_box_id:
            parking_type = parking_box["TypeofPB"]

            # Normalize the angle to the range [0, 360)
            angle = angle % 360
            # Find the closest multiple of 90
            closest_multiple_of_90 = round(angle / 90) * 90
            # Calculate the deviation
            deviation = abs(angle - closest_multiple_of_90)
            deviation = np.deg2rad(deviation)
            # Vector between centers
            vector = np.array(
                [center_scanned_slot["x"] - center_gt_slot["x"], center_scanned_slot["y"] - center_gt_slot["y"]]
            )
            # Rotation matrix
            rotation_matrix = np.array(
                [[np.cos(deviation), np.sin(deviation)], [-np.sin(deviation), np.cos(deviation)]]
            )
            # Rotate the vector to align with the parking slot system
            transformed_vector = np.dot(rotation_matrix, vector)
            # Projections on the parking slot axes
            dx = abs(transformed_vector[0])  # Projection on the short axis
            dy = abs(transformed_vector[1])  # Projection on the long axis

            # Assign distances based on the type of parking slot
            if parking_type == "parallel":
                short_distance = dy  # Difference on the Y axis
                long_distance = dx  # Difference on the X axis
            elif parking_type in ["perpendicular", "angled"]:
                short_distance = dx  # Difference on the X axis
                long_distance = dy  # Difference on the Y axis
            else:
                raise ValueError(f"Unknown parking type: {parking_type}")

            short_distance_check = short_distance < SlotOffer.Thresholds.THRESHOLD_CENTER_DISTANCE_SHORT_SIDE
            long_distance_check = long_distance < SlotOffer.Thresholds.THRESHOLD_CENTER_DISTANCE_LONG_SIDE

    return short_distance, short_distance_check, long_distance, long_distance_check


def associate_parking_slots(dict_GT_local, dict_scanned_local, scenario_dict, file_data, timestamp):
    """
    Associates parking slots from the ground truth (GT) data with the scanned slots based on coordinates for a given timestamp.

    Parameters:
        dict_GT_local (dict): Dictionary containing GT data for various timestamps.
        dict_scanned_local (dict): Dictionary containing scanned data for various timestamps.
        timestamp (int): The specific timestamp for which the association is made.

    Returns:
        dict: Dictionary containing the final associations between scanned slots and GT slots for the given timestamp.
    """
    # Check if the timestamp exists in the GT and scanned data
    if timestamp not in dict_scanned_local:
        raise ValueError(f"Timestamp {timestamp} does not exist in the GT or scanned data.")

    # Extract the parking slot centers from the GT data
    gt_centers = list(next(iter(dict_GT_local.values())).keys())

    # Try to extract the numeric coordinates
    try:
        gt_centers_array = [[float(coord[1]) for coord in center] for center in gt_centers]
    except (TypeError, ValueError) as e:
        print(f"Error converting GT centers: {e}")
        return {}

    # Build KDTree for GT
    tree = KDTree(gt_centers_array)

    # Initialize the dictionary for associations
    associations_dict = {}
    vehicle_local = "VehicleLocal" if "VehicleLocal" in file_data else "VehicleLocalSlots"
    # Iterate through each scanned coordinate and try to associate it with a ground truth location
    for SlotCoordinates, scanned_data in dict_scanned_local[timestamp].items():
        for scanned_center, scanned_coords in scanned_data.items():
            try:
                if scanned_center[0][1] == 0.0 and scanned_center[1][1] == 0.0:
                    continue
                # Convert scanned coordinates to a list of numeric values
                scanned_center_array = [float(coord[1]) for coord in scanned_center]
                dist, index = tree.query(scanned_center_array)
                matched_gt_center = gt_centers[index]
                # Add the association to the dictionary
                associations_dict[scanned_center] = {
                    "GT_center": matched_gt_center,
                    "ID_parking_box": file_data[vehicle_local][0]["timedObjs"][0]["parkingBoxes"][index]["objectId"],
                    "distance": dist,
                    "scanned_coordinates": scanned_coords,
                    "parking_scenario": scenario_dict[timestamp].get(SlotCoordinates, "Unknown"),
                }
            except (TypeError, ValueError) as e:
                print(f"Error converting scanned centers: {e}")

    matched_gt_indices = set()
    final_associations = {}

    for scanned_center, assoc_data in associations_dict.items():
        gt_index = assoc_data["ID_parking_box"]
        if gt_index not in matched_gt_indices:
            final_associations[scanned_center] = assoc_data
            matched_gt_indices.add(gt_index)
        else:
            print(f"Conflict: Scanned slot {scanned_center} was ignored due to multiple associations.")

    return final_associations


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        sg_time = "uiTimeStamp"
        sg_parksm_core_status_state = "ParkSmCoreStatusState"
        sg_num_valid_parking_boxes = "NumValidParkingBoxes"
        sg_velocity = "EgoMotionPort"
        sg_position_x = "PositionX"
        sg_position_y = "PositionY"
        sg_position_yaw = "PositionYaw"
        sg_parking_scenario = "ParkingScenario"
        Slotcoordinates_x = "Slotcoordinates_{}_{}_x"
        Slotcoordinates_y = "Slotcoordinates_{}_{}_y"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = [
            "SIM VFB",
            "MTA_ADC5",
        ]
        self._properties = {
            self.Columns.sg_time: [
                ".MF_TRJPLA_DATA.syncRef.m_sig_parkingBoxPort.uiTimeStamp",
                ".MF_TRJPLA_1.syncRef.m_sig_parkingBoxPort.uiTimeStamp",
            ],
            self.Columns.sg_parksm_core_status_state: [
                ".MF_PARKSM_CORE_DATA.parksmCoreStatusPort.parksmCoreState_nu",
                ".MfPsmCore.parksmCoreStatusPort.parksmCoreState_nu",
            ],
            self.Columns.sg_position_x: [
                ".MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.xPosition_m",
                ".VEDODO_0.m_odoEstimationOutputPort.odoEstimation.xPosition_m",
            ],
            self.Columns.sg_position_y: [
                ".MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.yPosition_m",
                ".VEDODO_0.m_odoEstimationOutputPort.odoEstimation.yPosition_m",
            ],
            self.Columns.sg_position_yaw: [
                ".MF_VEDODO_DATA.OdoEstimationOutputPort.odoEstimation.yawAngle_rad",
                ".VEDODO_0.m_odoEstimationOutputPort.odoEstimation.yawAngle_rad",
            ],
            self.Columns.sg_num_valid_parking_boxes: [
                ".SI_DATA.m_parkingBoxesPort.numValidParkingBoxes_nu",
                ".SiCoreGeneric.m_parkingBoxesPort.numValidParkingBoxes_nu",
            ],
            self.Columns.sg_velocity: [".SI_DATA.m_egoMotionPort.vel_mps", ".SiCoreGeneric.m_egoMotionPort.vel_mps"],
        }
        for i in range(SlotOffer.ParkingBoxesSignalIterator.MAX_NUM_PARKING_BOXES):  # 8
            self._properties[f"{self.Columns.sg_parking_scenario}_{i}"] = [
                f".SI_DATA.m_parkingBoxesPort.parkingBoxes[{i}].parkingScenario_nu",
                f".SiCoreGeneric.m_parkingBoxesPort.parkingBoxes[{i}].parkingScenario_nu",
            ]
        iteration_tuples = []
        for i in range(SlotOffer.ParkingBoxesSignalIterator.MAX_NUM_PARKING_BOXES):  # 8
            for j in range(SlotOffer.ParkingBoxesSignalIterator.MAX_NUM_VERTICES_PER_BOX):  # 4
                iteration_tuples.append((i, j))
        slot_coords_x = {
            self.Columns.Slotcoordinates_x.format(x[0], x[1]): [
                f".SI_DATA.m_parkingBoxesPort.parkingBoxes[{x[0]}].slotCoordinates_m.array[{x[1]}].x_dir",
                f".SiCoreGeneric.m_parkingBoxesPort.parkingBoxes[{x[0]}].slotCoordinates_m.array[{x[1]}].x_dir",
            ]
            for x in iteration_tuples
        }
        slot_coords_y = {
            self.Columns.Slotcoordinates_y.format(x[0], x[1]): [
                f".SI_DATA.m_parkingBoxesPort.parkingBoxes[{x[0]}].slotCoordinates_m.array[{x[1]}].y_dir",
                f".SiCoreGeneric.m_parkingBoxesPort.parkingBoxes[{x[0]}].slotCoordinates_m.array[{x[1]}].y_dir",
            ]
            for x in iteration_tuples
        }
        self._properties.update(slot_coords_x)
        self._properties.update(slot_coords_y)


class Preprocessor(PreProcessor):
    """Preprocessor for the ParkEnd test step."""

    def pre_process(self):
        """
        Preprocesses the data before further processing.

        Returns:
        - df: pd.DataFrame, the preprocessed data.
        """

        def get_time_obj_string(file_data):
            # Extract VehicleLocal from file_data
            vehicle_local_coordinates = file_data.get("VehicleLocal") or file_data.get("VehicleLocalSlots")
            if not vehicle_local_coordinates:
                raise ValueError("VehicleLocal/VehicleLocalSlots not found in JSON file")

            # Extract timedObjs from the first element of VehicleLocal
            timed_objs = vehicle_local_coordinates[0].get("timedObjs")
            if not timed_objs:
                raise ValueError("timedObjs not found in VehicleLocal")

            # Look for the key that ends with ".uiTimeStamp" in the first element of timedObjs
            for key in timed_objs[0].keys():
                if key.endswith(".uiTimeStamp"):
                    return key

            # If no key ending with '.uiTimeStamp' is found, raise an error
            raise ValueError("No key ending with '.uiTimeStamp' found in timedObjs")

        file_path = os.path.basename(self.artifacts[0].file_path)
        time_obj_string_timestamp = None
        json_files = []

        if file_path.endswith(".rrec") or file_path.endswith(".bsig"):
            identifier = file_path[:-5]  # Remove the ".rrec" extension
            directory = os.path.dirname(self.artifacts[0].file_path)

            # Search for a JSON file that contains the identifier
            json_files = [f for f in os.listdir(directory) if f.endswith(".json") and identifier in f]

        try:
            json_path = os.path.join(directory, json_files[0])  # Use the first matching JSON file
            with open(json_path) as file:
                file_data = json.loads(file.read())
                time_obj_string_timestamp = get_time_obj_string(file_data)
        except Exception as e:
            _log.error("An error occurred: %s", e)
            raise FileNotFoundError("No JSON file found matching the identifier.") from e

        return file_data, time_obj_string_timestamp


signals_obj = Signals()


@register_signals(EXAMPLE, Signals)
@register_pre_processor(alias="SI_slot_offer", pre_processor=Preprocessor)
class GenericTestStep(TestStep):
    """Generic TestStep to use the calculation for both scenarios"""

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        super().__init__()

    def process(self, case):
        """
        The process function is the main function of a process. It will be called by the framework and should contain
        the actual processing logic. The return value of this function will be stored in the result object, which can then
        be used to create plots or other output artifacts.

        :param self: Represent the instance of the class
        :param case: The case identifier to determine the type of processing(TPR/FPR/FNR).
        :return: A result object
        """
        _log.debug("Starting processing...")
        try:

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                    "file_path": os.path.basename(self.artifacts[0].file_path),
                }
            )

            # Initialize variables
            plot_titles, plots, remarks = fh.rep([], 3)
            df = pd.DataFrame()
            self.result.measured_result = FALSE

            file_data, time_obj_string_timestamp = self.pre_processors["SI_slot_offer"]

            classification_of_pb = {
                "TP": [],
                "FP": [],
                "FN": [],
            }
            type_scenario_map = {
                "parallel": [0],
                "perpendicular": [1],
                "angled": [2, 3],
            }
            dict_scanned_local = {}
            dict_GT_app_start = {}
            dict_GT_local_for_json = {}

            json_timestamps_local = []

            # Get the absolute path of the current script file
            script_path = os.path.realpath(__file__)
            # Extract the directory path
            image_base_path = os.path.dirname(script_path)

            # Define the image filenames
            image1_filename = r"next_to_parkingbox.png"

            # Extract car coordinates
            # from: github-am.geo.conti.de/ADAS/mf_common/blob/2e24136b576160a23685eaf61ccc3abe3ca94b2f/interface/platform/ultrasonic_parking/Vehicle_Params_default_set.h
            mirror_x_left = SlotOffer.CarCoordinates.LEFT_MIRROR_REAR_LEFT_CORNER[0]
            mirror_x_right = SlotOffer.CarCoordinates.RIGHT_MIRROR_REAR_RIGHT_CORNER[0]
            mirror_y_left = SlotOffer.CarCoordinates.LEFT_MIRROR_REAR_LEFT_CORNER[1]
            mirror_y_right = SlotOffer.CarCoordinates.RIGHT_MIRROR_REAR_RIGHT_CORNER[1]
            vehicle_width = SlotOffer.VehicleDimensions.VEHICLE_WIDTH
            vehicle_length = SlotOffer.VehicleDimensions.VEHICLE_LENGTH

            # Initialize boundary variables
            max_x = 0
            min_x = 0
            max_y = 0
            min_y = 0
            try:
                df = self.readers[EXAMPLE].signals
            except Exception:
                df = self.readers[EXAMPLE]

            sg_slot_coords = []
            df_temp = pd.DataFrame()
            scenario_dict = {}
            for i in range(SlotOffer.ParkingBoxesSignalIterator.MAX_NUM_PARKING_BOXES):  # 8
                df_temp = pd.DataFrame()
                for j in range(SlotOffer.ParkingBoxesSignalIterator.MAX_NUM_VERTICES_PER_BOX):  # 4
                    df_temp[signals_obj.Columns.Slotcoordinates_x.format(i, j)] = df[
                        signals_obj.Columns.Slotcoordinates_x.format(i, j)
                    ]
                    df_temp[signals_obj.Columns.Slotcoordinates_y.format(i, j)] = df[
                        signals_obj.Columns.Slotcoordinates_y.format(i, j)
                    ]
                    df.drop(columns=[signals_obj.Columns.Slotcoordinates_x.format(i, j)], axis=1, inplace=True)
                    df.drop(columns=[signals_obj.Columns.Slotcoordinates_y.format(i, j)], axis=1, inplace=True)
                df[f"Slotcoordinates_{i}"] = df_temp.apply(lambda row: row.tolist(), axis=1)
                sg_slot_coords.append(f"Slotcoordinates_{i}")

            df.set_index(Signals.Columns.sg_time, inplace=True)
            if "VehicleLocal" in file_data:
                vehicle_local = "VehicleLocal"
            elif "VehicleLocalSlots" in file_data:
                vehicle_local = "VehicleLocalSlots"
            # Extract JSON timestamps for local vehicles and parking start
            json_timestamps_local = [
                timed_obj[time_obj_string_timestamp]
                for entry in file_data[vehicle_local]
                for timed_obj in entry.get("timedObjs", [])
            ]

            # The reason for the processing of the 'application started' section is
            # to extract the ground truth data is done here because SCANNING_IN is not always present at that time
            for timestamp in json_timestamps_local:
                # Process and extract GT data, resulting in dictionaries filled with all the parking slots
                dict_GT_app_start = process_json_section(
                    file_data,
                    timestamp,
                    time_obj_string_timestamp,
                    dict_GT_app_start,
                    "ApplicationStarted",
                )

            json_timestamps_park = None
            if "ParkingStarted" in file_data and file_data["ParkingStarted"]:
                for entry in file_data["ParkingStarted"]:
                    if "timedObjs" in entry and entry["timedObjs"]:
                        json_timestamps_park = entry["timedObjs"][0].get(time_obj_string_timestamp, None)
                        if json_timestamps_park:
                            break
            # Filter DataFrame based on local timestamps
            filtered_df = df[df.index.isin(json_timestamps_local)]
            # Remove duplicate indexes from the filtered DataFrame
            duplicate_indexes = filtered_df.index.duplicated()
            filtered_df = filtered_df[~duplicate_indexes]
            scanning_in_mask = (
                filtered_df[Signals.Columns.sg_parksm_core_status_state] == constants.ParkSmCoreStatus.SCANNING_IN
            )
            filtered_df = filtered_df[scanning_in_mask]

            if json_timestamps_park:
                filtered_df = filtered_df[filtered_df.index <= json_timestamps_park]

            for timestamp in filtered_df.index:
                scenario_dict[timestamp] = {}
                dict_GT_local_for_json = process_json_for_collinearity(
                    file_data,
                    timestamp,
                    time_obj_string_timestamp,
                    dict_GT_local_for_json,
                    vehicle_local,
                )
                for i in range(SlotOffer.ParkingBoxesSignalIterator.MAX_NUM_PARKING_BOXES):  # 8
                    scenario_dict[timestamp][f"Slotcoordinates_{i}"] = filtered_df[
                        signals_obj.Columns.sg_parking_scenario + f"_{i}"
                    ].at[timestamp]
                coord_dict = process_signal_coordinates(timestamp, filtered_df, sg_slot_coords)
                dict_scanned_local[timestamp] = coord_dict

            collinear_data = collinearity_check(
                dict_GT_local_for_json,
                mirror_x_left=mirror_x_left,
                mirror_x_right=mirror_x_right,
                mirror_y_left=mirror_y_left,
                mirror_y_right=mirror_y_right,
            )

            cond_0 = " ".join(
                "The parking spot must be detected as scanned when the vehicle is next to the existing \
                    parking spot found in the GT data.".split()
            )
            cond_1 = " ".join(
                f"The overlap percentage of the scanned parking slot need to be greater than \
                    {constants.SlotOffer.Thresholds.THRESHOLD_OVERLAP}%".split()
            )
            cond_2 = " ".join(
                f"The orientation difference needs to be less than \
                    {constants.SlotOffer.Thresholds.THRESHOLD_ORIENTATION}°".split()
            )
            cond_3 = " ".join(
                "The type of the scanned parking box has to match the type of the parking box from the GT data.".split()
            )
            cond_4 = " ".join(
                f"The distance between centers needs to be less than \
                    {constants.SlotOffer.Thresholds.THRESHOLD_CENTER_DISTANCE_SHORT_SIDE}m for the short side of the parking box and less than \
                    {constants.SlotOffer.Thresholds.THRESHOLD_CENTER_DISTANCE_LONG_SIDE}m for the long side of the parking box OR \
                        A rectangular polygon of the shape of the ego-vehicle can fit inside the intersection.".split()
            )
            conditions_table = pd.DataFrame(
                {
                    "Prerequisites for a TP": {
                        "0": cond_0,
                        "1": cond_1,
                        "2": cond_2,
                        "3": cond_3,
                        "4": cond_4,
                    },
                },
            )
            cond_table = go.Figure(
                data=[
                    go.Table(
                        columnwidth=[50, 20, 7],
                        header=dict(
                            values=list(conditions_table.columns),
                            fill_color="rgb(255,165,0)",
                            font=dict(size=12, family="Arial", color="rgb(0,0,0)"),
                        ),
                        cells=dict(
                            values=[conditions_table[col] for col in conditions_table.columns],
                            height=40,
                            align="center",
                            font=dict(size=12),
                        ),
                    )
                ]
            )
            cond_table.update_layout(
                constants.PlotlyTemplate.lgt_tmplt,
                height=fh.calc_table_height(conditions_table["Prerequisites for a TP"].to_dict()),
            )
            plots.append(cond_table)

            image_path = os.path.join(image_base_path, "SlotOffer-scenario-img", image1_filename)
            try:
                image = Image.open(image_path)
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
            except FileNotFoundError as e:
                print(f"File not found: {e}")
            except OSError as e:
                print(f"IOError: {e}")

            # Add image
            # Create figure
            fig_img = go.Figure()

            # This trace is added to help the autoresize
            fig_img.add_trace(
                go.Scatter(
                    x=[0, SlotOffer.ImageSize.IMG_WIDTH * SlotOffer.ImageSize.SCALE_FACTOR],
                    y=[0, SlotOffer.ImageSize.IMG_HEIGHT * SlotOffer.ImageSize.SCALE_FACTOR],
                    mode="markers",
                    marker_opacity=0,
                )
            )

            # Configure axes
            fig_img.update_xaxes(
                visible=False, range=[0, SlotOffer.ImageSize.IMG_WIDTH * SlotOffer.ImageSize.SCALE_FACTOR]
            )

            fig_img.update_yaxes(
                visible=False,
                range=[0, SlotOffer.ImageSize.IMG_HEIGHT * SlotOffer.ImageSize.SCALE_FACTOR],
                # the scaleanchor attribute ensures that the aspect ratio stays constant
                scaleanchor="x",
            )

            # Add image and position it in relation to axes
            fig_img.add_layout_image(
                dict(
                    x=0,
                    sizex=SlotOffer.ImageSize.IMG_WIDTH * SlotOffer.ImageSize.SCALE_FACTOR,
                    y=SlotOffer.ImageSize.IMG_HEIGHT * SlotOffer.ImageSize.SCALE_FACTOR,
                    sizey=SlotOffer.ImageSize.IMG_HEIGHT * SlotOffer.ImageSize.SCALE_FACTOR,
                    xref="x",
                    yref="y",
                    opacity=1.0,
                    layer="below",
                    sizing="stretch",
                    source=f"data:image/png;base64,{img_str}",
                )
            )

            fig_img.update_layout(
                margin=dict(l=0, r=0, t=30, b=0),
                title=dict(
                    text="Test scenario: NEXT TO PARKING BOX",
                    y=0.97,
                    x=0.5,
                    xanchor="center",
                    yanchor="top",
                    font=dict(size=20),
                ),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor="rgba(0,0,0,0)",
            )
            plots.append(fig_img)

            rows = []
            final_dict = {
                ts: {
                    "gt_parking_slots": [],
                    "parking_box_id": [],
                    "pb_to_be_collinear_with": [],
                    "vehicle_scanned_slot": [],
                    "overlap_percentage": 0.0,
                    "orientation": 0.0,
                    "centers_distance": 0.0,
                    "vehicle_fits": False,
                    "classification": "FP",
                    "parking_box_type": ["-", "-"],
                    "overlap_area": [],
                    "vehicle": [],
                }
                for ts in collinear_data.values()
            }

            fig_trace_1 = go.Figure()
            frames_1 = []

            for parking_box_id, timestamp in collinear_data.items():
                intersection_coords = [() for _ in range(2)]
                vehicle_scanned_slot = [() for _ in range(2)]
                frame_data_1 = []
                final_associations = associate_parking_slots(
                    dict_GT_app_start, dict_scanned_local, scenario_dict, file_data, timestamp
                )
                new_origin = [
                    filtered_df.loc[timestamp, Signals.Columns.sg_position_x],
                    filtered_df.loc[timestamp, Signals.Columns.sg_position_y],
                    filtered_df.loc[timestamp, Signals.Columns.sg_position_yaw],
                ]

                overlap_percentage = 0.0
                json_orientation = 0.0
                signal_orientation = 0.0
                orientation_difference = 0.0
                short_distance = 0.0
                long_distance = 0.0
                vehicle_rectangle_fits = False
                vehicle_fits = "N/A"
                parking_box_type = "-"
                parking_box_type_check = "-"

                # Add ground truth parking slots to the plot
                for timed_obj in file_data["ApplicationStarted"][0]["timedObjs"]:
                    for parking_box in timed_obj["parkingBoxes"]:
                        x_axis_gt2 = [point["x"] for point in parking_box["slotCoordinates_m"]]
                        x_axis_gt2.append(
                            x_axis_gt2[0]
                        )  # Close the loop for the ground truth parking box coordinates so the shape ends right where it started
                        y_axis_gt2 = [point["y"] for point in parking_box["slotCoordinates_m"]]
                        y_axis_gt2.append(
                            y_axis_gt2[0]
                        )  # Close the loop for the ground truth parking box coordinates so the shape ends right where it started

                        if max_x < max(x_axis_gt2):
                            max_x = max(x_axis_gt2)
                        if min_x > min(x_axis_gt2):
                            min_x = min(x_axis_gt2)
                        if max_y < max(y_axis_gt2):
                            max_y = max(y_axis_gt2)
                        if min_y > min(y_axis_gt2):
                            min_y = min(y_axis_gt2)

                        final_dict[timestamp]["gt_parking_slots"].append((x_axis_gt2, y_axis_gt2))

                # Add the ground truth parking box that the car has to be collinear with, to the figure.
                x_coordinates = []
                y_coordinates = []
                for parking_box in file_data["ApplicationStarted"][0]["timedObjs"][0]["parkingBoxes"]:
                    if parking_box["objectId"] == parking_box_id:
                        for point in parking_box["slotCoordinates_m"]:
                            x_coordinates.append(point["x"])
                            y_coordinates.append(point["y"])
                final_dict[timestamp]["pb_to_be_collinear_with"].append((x_coordinates, y_coordinates))

                for association in final_associations.values():
                    if parking_box_id != association["ID_parking_box"]:
                        continue
                    scanned_slot_for_calculation = []
                    gt_slot_for_calculation = []
                    short_distance_check = False
                    long_distance_check = False

                    # Extract (x, y) coordinates from the parking box with the specified object ID
                    for parking_box in file_data["ApplicationStarted"][0]["timedObjs"][0]["parkingBoxes"]:
                        if parking_box["objectId"] == parking_box_id:
                            for point in parking_box["slotCoordinates_m"]:
                                gt_slot_for_calculation.append((point["x"], point["y"]))

                    # Extract the type of the parking box and check if it matches the scenario
                    for parking_box in file_data["ApplicationStarted"][0]["timedObjs"][0]["parkingBoxes"]:
                        if (
                            parking_box["TypeofPB"] in type_scenario_map
                            and association["parking_scenario"] in type_scenario_map[parking_box["TypeofPB"]]
                        ):
                            parking_box_type_check = f"Matches - {parking_box['TypeofPB']}"
                            parking_box_type = parking_box["TypeofPB"]
                            break
                        parking_box_type_check = f"Does not match to {parking_box['TypeofPB']} type."
                        parking_box_type = parking_box["TypeofPB"]
                        break

                    for coords in association["scanned_coordinates"]:
                        scanned_slot_for_calculation.append((coords["x"], coords["y"]))

                    x_axis_slot = [coord["x"] for coord in association["scanned_coordinates"]]
                    x_axis_slot.append(x_axis_slot[0])  # Closing the loop

                    y_axis_slot = [coord["y"] for coord in association["scanned_coordinates"]]
                    y_axis_slot.append(y_axis_slot[0])  # Closing the loop

                    vehicle_scanned_slot = (x_axis_slot, y_axis_slot)

                    intersection, overlap_percentage = calculate_overlap(
                        gt_slot_for_calculation, scanned_slot_for_calculation
                    )
                    centroid = intersection.centroid
                    x, y = centroid.x, centroid.y
                    vehicle_rectangle_fits = check_rectangle_fit(intersection, x, y, vehicle_width, vehicle_length)
                    vehicle_fits = "FITS" if vehicle_rectangle_fits else "DOES NOT FIT"
                    json_orientation = calculate_polygon_orientation(gt_slot_for_calculation)
                    signal_orientation = calculate_polygon_orientation(scanned_slot_for_calculation)

                    center_gt_slot_for_calculation = calculate_polygon_center(
                        points=[{"x": x, "y": y} for x, y in gt_slot_for_calculation]
                    )
                    center_scanned_slot_for_calculation = calculate_polygon_center(
                        points=[{"x": x, "y": y} for x, y in scanned_slot_for_calculation]
                    )

                    short_distance, short_distance_check, long_distance, long_distance_check = (
                        calculate_center_distances_yaw(
                            center_gt_slot_for_calculation,
                            center_scanned_slot_for_calculation,
                            file_data,
                            parking_box_id,
                            json_orientation,
                        )
                    )
                    orientation_difference = abs(json_orientation - signal_orientation)

                    intersection_coords = intersection_fig_trace_method(
                        gt_slot_for_calculation, scanned_slot_for_calculation
                    )

                    if (
                        overlap_percentage > SlotOffer.Thresholds.THRESHOLD_OVERLAP
                        and orientation_difference < SlotOffer.Thresholds.THRESHOLD_ORIENTATION
                        and "Matches" in parking_box_type_check.strip()
                        and ((short_distance_check and long_distance_check) or vehicle_rectangle_fits)
                    ):
                        classification_of_pb["TP"].append(parking_box_id)
                        final_dict[timestamp]["classification"] = "TP"
                    else:
                        classification_of_pb["FP"].append(parking_box_id)

                if parking_box_id not in classification_of_pb["TP"]:
                    classification_of_pb["FN"].append(parking_box_id)

                vehicle_plot = constants.DrawCarLayer.draw_car(new_origin[0], new_origin[1], new_origin[2])
                final_dict[timestamp]["vehicle"].append(vehicle_plot[1])

                row = {
                    "ID Parking Box": parking_box_id,
                    "Timestamp": timestamp,
                    "Overlap Percentage [%]": round(overlap_percentage, 2) if overlap_percentage != 0 else "-",
                    "Orientation Difference [°]": (
                        round(orientation_difference, 2) if orientation_difference != 0 else "-"
                    ),
                    "Center Difference [m]": (
                        f"ShortDist: {round(short_distance, 2)}, LongDist: {round(long_distance, 2)}"
                        if short_distance != 0 or long_distance != 0
                        else "-"
                    ),
                    "Vehicle Rectangle Fit in Overlap Polygon": (
                        ("FITS" if vehicle_rectangle_fits else "DOES NOT FIT") if vehicle_fits != "N/A" else "-"
                    ),
                    "Type of the parking box": parking_box_type_check,
                    "TP": "<b>X</b>" if parking_box_id in classification_of_pb["TP"] else "",
                    "FP": "<b>X</b>" if parking_box_id in classification_of_pb["FP"] else "",
                    "FN": "<b>X</b>" if parking_box_id in classification_of_pb["FN"] else "",
                }
                rows.append(row)
                signal_summary = pd.DataFrame(rows)

                final_dict[timestamp]["vehicle_scanned_slot"].append(vehicle_scanned_slot)
                final_dict[timestamp]["overlap_area"].append(intersection_coords)
                final_dict[timestamp]["parking_box_id"] = parking_box_id
                final_dict[timestamp]["overlap_percentage"] = overlap_percentage
                final_dict[timestamp]["orientation"] = orientation_difference
                final_dict[timestamp]["centers_distance"] = (short_distance, long_distance)
                final_dict[timestamp]["parking_box_type"] = [parking_box_type, parking_box_type_check]
                final_dict[timestamp]["vehicle_fits"] = vehicle_fits

            layout_config_slider = {}

            # Check if parking box for the first timestamp exists, and add its trace
            if list(final_dict.keys()):
                first_key = list(final_dict.keys())[0]
                if final_dict.get(first_key):
                    color_overlap = (
                        "#000000"
                        if final_dict[first_key]["overlap_percentage"] == 0
                        else (
                            "#008000"
                            if final_dict[first_key]["overlap_percentage"] > SlotOffer.Thresholds.THRESHOLD_OVERLAP
                            else "#ff0000"
                        )
                    )
                    color_orientation = (
                        "#000000"
                        if final_dict[first_key]["orientation"] == 0
                        else (
                            "#008000"
                            if final_dict[first_key]["orientation"] < SlotOffer.Thresholds.THRESHOLD_ORIENTATION
                            else "#ff0000"
                        )
                    )
                    color_center_distance_short = (
                        "#000000"
                        if (
                            final_dict[first_key]["centers_distance"][0] == 0
                            and final_dict[first_key]["centers_distance"][1] == 0
                        )
                        else (
                            "#008000"
                            if final_dict[first_key]["centers_distance"][0]
                            < SlotOffer.Thresholds.THRESHOLD_CENTER_DISTANCE_SHORT_SIDE
                            else "#ff0000"
                        )
                    )
                    color_center_distance_y = (
                        "#000000"
                        if (
                            final_dict[first_key]["centers_distance"][0] == 0
                            and final_dict[first_key]["centers_distance"][1] == 0
                        )
                        else (
                            "#008000"
                            if final_dict[first_key]["centers_distance"][1]
                            < SlotOffer.Thresholds.THRESHOLD_CENTER_DISTANCE_LONG_SIDE
                            else "#ff0000"
                        )
                    )
                    color_parking_box_type_check = (
                        "#000000"
                        if final_dict[first_key]["parking_box_type"][1] == "-"
                        else (
                            "#008000"
                            if "Matches" in final_dict[first_key]["parking_box_type"][1].strip()
                            else "#ff0000"
                        )
                    )
                    color_vehicle_rectangle_fit = (
                        "#000000"
                        if final_dict[first_key]["vehicle_fits"] == "N/A"
                        else ("#008000" if final_dict[first_key]["vehicle_fits"] == "FITS" else "#ff0000")
                    )

                    for pb_id in final_dict[first_key]["gt_parking_slots"]:
                        trace_gt_data = go.Scatter(
                            x=pb_id[0],
                            y=pb_id[1],
                            mode="lines",
                            name="Ground truth parking slots",
                            legendgroup="ground_truth",
                            line=dict(color="blue"),
                            showlegend=False,  # Set showlegend to False for each scatter plot
                        )
                        fig_trace_1.add_trace(trace_gt_data)
                    trace_gt_data_dummy = go.Scatter(
                        x=[None],
                        y=[None],
                        mode="lines",
                        name="Ground truth parking slots",
                        legendgroup="ground_truth",
                        line=dict(color="blue"),
                        showlegend=True,  # Set showlegend to False for each scatter plot
                    )
                    fig_trace_1.add_trace(trace_gt_data_dummy)
                    for pb_id in final_dict[first_key]["pb_to_be_collinear_with"]:
                        trace_pb_to_be_collinear_with = go.Scatter(
                            x=pb_id[0],
                            y=pb_id[1],
                            fill="toself",
                            fillcolor="rgba(163, 160, 169, 1)",
                            line=dict(color="blue"),
                            mode="lines+text",
                            name="PB to be collinear with",
                        )
                        fig_trace_1.add_trace(trace_pb_to_be_collinear_with)
                    for pb_id in final_dict[first_key]["vehicle_scanned_slot"]:
                        trace_vehicle_scanned_slot = go.Scatter(
                            x=pb_id[0],
                            y=pb_id[1],
                            mode="lines+markers",
                            name="Vehicle scanned slot",
                        )
                        fig_trace_1.add_trace(trace_vehicle_scanned_slot)
                    for pb_id in final_dict[first_key]["overlap_area"]:
                        trace_overlap = go.Scatter(
                            x=pb_id[0],
                            y=pb_id[1],
                            fill="toself",
                            fillcolor=(
                                "rgba(0, 255, 0, 0.2)"
                                if final_dict[first_key]["classification"] == "TP"
                                else "rgba(255, 0, 0, 0.2)"
                            ),
                            line=dict(
                                color=(
                                    "rgba(0, 255, 0, 1.0)"
                                    if final_dict[first_key]["classification"] == "TP"
                                    else "rgba(255, 0, 0, 1.0)"
                                )
                            ),
                            mode="lines+text",
                            name="Overlapping area",
                        )
                        fig_trace_1.add_trace(trace_overlap)
                    for vehicle_plots in final_dict[first_key]["vehicle"]:
                        for vehicle_plot in vehicle_plots:
                            fig_trace_1.add_trace(vehicle_plot)

                    layout_config_slider["annotations"] = [
                        go.layout.Annotation(
                            text=f"Additional Information: <br>Overlap(PB with ID {final_dict[first_key]['parking_box_id']}):"
                            f" <span style='color: {color_overlap}'>{round(final_dict[first_key]['overlap_percentage'], 2)}%</span>. <br>"
                            f"Orientation difference: "
                            f" <span style='color: {color_orientation}'>{round(final_dict[first_key]['orientation'], 2)}°</span>.<br>"
                            f"Distance between centers:"
                            f" <span style='color: {color_center_distance_short}'>ShortDist: {round(short_distance, 2)}</span>, <span style='color: {color_center_distance_y}'>LongDist: {round(long_distance, 2)}</span>.<br>"
                            f"Parking Box Type Check: <span style='color: {color_parking_box_type_check}'>{final_dict[first_key]['parking_box_type'][0]}</span>.<br>"
                            f"Vehicle rectangle fit: <span style='color: {color_vehicle_rectangle_fit}'>{final_dict[first_key]['vehicle_fits']}</span>",
                            align="left",
                            showarrow=False,
                            xref="paper",
                            yref="paper",
                            x=1,
                            y=0,
                            bordercolor="black",
                            borderwidth=1,
                        )
                    ]
                    fig_trace_1.update_layout(**layout_config_slider)

            for key, value in final_dict.items():
                frame_data_1 = []
                if value.get("gt_parking_slots", None):  # Only create the parking box trace if coordinates exist
                    for pb_id in value["gt_parking_slots"]:
                        gt_parking_box_trace = go.Scatter(
                            x=pb_id[0],
                            y=pb_id[1],
                            mode="lines",
                            name="Ground truth parking slots",
                            legendgroup="ground_truth",
                            line=dict(color="blue"),
                            showlegend=False,  # Set showlegend to False for each scatter plot
                        )
                        frame_data_1.append(gt_parking_box_trace)
                    max_x = max(max(pb_id[0]) for pb_id in value["gt_parking_slots"] if pb_id[0] is not None)
                    min_x = min(min(pb_id[0]) for pb_id in value["gt_parking_slots"] if pb_id[0] is not None)
                    max_y = max(max(pb_id[1]) for pb_id in value["gt_parking_slots"] if pb_id[1] is not None)
                    min_y = min(min(pb_id[1]) for pb_id in value["gt_parking_slots"] if pb_id[1] is not None)
                    gt_parking_box_trace_dummy = go.Scatter(
                        x=[None],
                        y=[None],
                        mode="lines",
                        name="Ground truth parking slots",
                        legendgroup="ground_truth",
                        line=dict(color="blue"),
                        showlegend=True,  # Set showlegend to False for each scatter plot
                    )
                    frame_data_1.append(gt_parking_box_trace_dummy)
                if value.get("pb_to_be_collinear_with", None):
                    for pb_id in value["pb_to_be_collinear_with"]:
                        pb_to_be_collinear_with_trace = go.Scatter(
                            x=pb_id[0],
                            y=pb_id[1],
                            fill="toself",
                            fillcolor="rgba(163, 160, 169, 1)",
                            line=dict(
                                color="blue",
                            ),
                            mode="lines+text",
                            name="PB to be collinear with",
                        )
                        frame_data_1.append(pb_to_be_collinear_with_trace)
                if value.get("vehicle_scanned_slot", None):
                    for pb_id in value["vehicle_scanned_slot"]:
                        vehicle_scanned_slot_trace = go.Scatter(
                            x=pb_id[0],
                            y=pb_id[1],
                            mode="lines+markers",
                            name="Vehicle scanned slot",
                        )
                        frame_data_1.append(vehicle_scanned_slot_trace)
                if value.get("overlap_area", None):
                    for pb_id in value["overlap_area"]:
                        overlap_trace = go.Scatter(
                            x=pb_id[0],
                            y=pb_id[1],
                            fill="toself",
                            fillcolor=(
                                "rgba(0, 255, 0, 0.2)"
                                if final_dict[key]["classification"] == "TP"
                                else "rgba(255, 0, 0, 0.2)"
                            ),
                            line=dict(
                                color=(
                                    "rgba(0, 255, 0, 1.0)"
                                    if final_dict[key]["classification"] == "TP"
                                    else "rgba(255, 0, 0, 1.0)"
                                )
                            ),
                            mode="lines+text",
                            name="Overlapping area",
                        )
                        frame_data_1.append(overlap_trace)
                if value.get("vehicle", None):
                    for vehicle_plots in value["vehicle"]:
                        for vehicle_plot in vehicle_plots:
                            frame_data_1.append(vehicle_plot)

                frames_1.append(go.Frame(data=frame_data_1, name=str(key)))
            fig_trace_1.frames = frames_1
            sliders = [
                dict(
                    steps=[
                        dict(
                            method="animate",
                            args=[
                                [str(i)],
                                dict(
                                    mode="immediate",
                                    frame=dict(duration=1500, redraw=True),
                                    transition=dict(duration=500),
                                ),
                            ],
                            label=str(i),
                        )
                        for i in collinear_data.values()
                    ],
                    active=0,
                    transition=dict(duration=1000),
                    x=0,
                    xanchor="left",
                    y=0,
                    bgcolor="#FFA500",
                    yanchor="top",
                )
            ]
            fig_trace_1.update_layout(
                dragmode="pan",
                showlegend=True,
                xaxis=dict(range=[min_x - abs(min_x) * 0.8, max_x + abs(max_x) * 0.1]),
                yaxis=dict(range=[min_y - abs(min_y) * 0.6, max_y + abs(max_y) * 0.3]),
                sliders=sliders,
                height=900,
                xaxis_title="Timestamps",
                updatemenus=[
                    dict(
                        type="buttons",
                        showactive=False,
                        buttons=[
                            dict(
                                label="Play",
                                method="animate",
                                args=[
                                    None,
                                    dict(
                                        frame=dict(duration=1500, redraw=True),
                                        transition=dict(duration=500),
                                        fromcurrent=True,
                                        mode="immediate",
                                    ),
                                ],
                            ),
                            dict(
                                label="Pause",
                                method="animate",
                                args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")],
                            ),
                        ],
                    )
                ],
            )

            # Add annotations for each frame
            for frame in fig_trace_1.frames:
                timestamp = int(frame.name)
                if timestamp in final_dict:
                    color_overlap = (
                        "#000000"
                        if final_dict[timestamp]["overlap_percentage"] == 0
                        else (
                            "#008000"
                            if final_dict[timestamp]["overlap_percentage"] > SlotOffer.Thresholds.THRESHOLD_OVERLAP
                            else "#ff0000"
                        )
                    )
                    color_orientation = (
                        "#000000"
                        if final_dict[timestamp]["orientation"] == 0
                        else (
                            "#008000"
                            if final_dict[timestamp]["orientation"] < SlotOffer.Thresholds.THRESHOLD_ORIENTATION
                            else "#ff0000"
                        )
                    )
                    color_center_distance_short = (
                        "#000000"
                        if (
                            final_dict[timestamp]["centers_distance"][0] == 0
                            and final_dict[timestamp]["centers_distance"][1] == 0
                        )
                        else (
                            "#008000"
                            if final_dict[timestamp]["centers_distance"][0]
                            < SlotOffer.Thresholds.THRESHOLD_CENTER_DISTANCE_SHORT_SIDE
                            else "#ff0000"
                        )
                    )
                    color_center_distance_y = (
                        "#000000"
                        if (
                            final_dict[timestamp]["centers_distance"][0] == 0
                            and final_dict[timestamp]["centers_distance"][1] == 0
                        )
                        else (
                            "#008000"
                            if final_dict[timestamp]["centers_distance"][1]
                            < SlotOffer.Thresholds.THRESHOLD_CENTER_DISTANCE_LONG_SIDE
                            else "#ff0000"
                        )
                    )
                    color_parking_box_type_check = (
                        "#000000"
                        if final_dict[timestamp]["parking_box_type"][1] == "-"
                        else (
                            "#008000"
                            if "Matches" in final_dict[timestamp]["parking_box_type"][1].strip()
                            else "#ff0000"
                        )
                    )
                    color_vehicle_rectangle_fit = (
                        "#000000"
                        if final_dict[timestamp]["vehicle_fits"] == "N/A"
                        else ("#008000" if final_dict[timestamp]["vehicle_fits"] == "FITS" else "#ff0000")
                    )

                    value = final_dict[timestamp]
                    frame.layout.annotations = [
                        go.layout.Annotation(
                            text=f"Additional Information: <br>Overlap(PB with ID {value['parking_box_id']}):"
                            f" <span style='color: {color_overlap}'>{round(value['overlap_percentage'], 2)}%</span>. <br>"
                            f"Orientation difference: "
                            f" <span style='color: {color_orientation}'>{round(value['orientation'], 2)}°</span>.<br>"
                            f"Distance between centers:"
                            f" <span style='color: {color_center_distance_short}'>ShortDist: {round(value['centers_distance'][0], 2)}</span>, <span style='color: {color_center_distance_y}'>LongDist: {round(value['centers_distance'][1], 2)}</span>.<br>"
                            f"Parking Box Type Check: <span style='color: {color_parking_box_type_check}'>{value['parking_box_type'][0]}</span>.<br>"
                            f"Vehicle rectangle fit: <span style='color: {color_vehicle_rectangle_fit}'>{value['vehicle_fits']}</span>",
                            align="left",
                            showarrow=False,
                            xref="paper",
                            yref="paper",
                            x=1,
                            y=0,
                            bordercolor="black",
                            borderwidth=1,
                        )
                    ]

            plots.append(fig_trace_1)

            sig_sum = go.Figure(
                data=[
                    go.Table(
                        columnwidth=[1] * (len(signal_summary.columns) - 3) + [0.5, 0.5, 0.5],
                        header=dict(
                            values=list(signal_summary.columns),
                            align="center",
                            fill_color="rgb(255,165,0)",
                            font=dict(size=12, family="Arial", color="rgb(0,0,0)"),
                        ),
                        cells=dict(
                            values=[signal_summary[col] for col in signal_summary.columns],
                            height=40,
                            align="center",
                            font=dict(size=12),
                        ),
                    )
                ]
            )
            sig_sum.update_layout(
                constants.PlotlyTemplate.lgt_tmplt,
                height=fh.calc_table_height(signal_summary["ID Parking Box"].to_dict()),
                title=dict(
                    text="Results for every parking box:",
                    font=dict(size=20, weight="bold"),
                    xanchor="center",
                    yanchor="top",
                    x=0.5,  # Set x to 0.5 to center the title
                    y=0.97,
                ),
                margin=dict(t=40, l=0),
            )
            plots.append(sig_sum)
            plots.insert(2, plots.pop())

            TPR = (
                round(
                    len(classification_of_pb["TP"])
                    / (len(classification_of_pb["TP"]) + len(classification_of_pb["FN"]))
                    * 100,
                    2,
                )
                if len(classification_of_pb["TP"]) != 0
                else 0
            )
            FPR = (
                round(
                    len(classification_of_pb["FP"])
                    / (len(classification_of_pb["TP"]) + len(classification_of_pb["FP"]))
                    * 100,
                    2,
                )
                if len(classification_of_pb["FP"]) != 0
                else 0
            )
            FNR = (
                round(
                    len(classification_of_pb["FN"])
                    / (len(classification_of_pb["TP"]) + len(classification_of_pb["FN"]))
                    * 100,
                    2,
                )
                if len(classification_of_pb["FN"]) != 0
                else 0
            )

            parking_box_rates = pd.DataFrame(
                {
                    "Parking Box Rates": {
                        "0": "True Positive Rate",
                        "1": "False Positive Rate",
                        "2": "False Negative Rate",
                    },
                    "Formula [%]": {
                        "0": "TP / (TP + FN) * 100",
                        "1": "FP / (TP + FP) * 100",
                        "2": "FN / (TP + FN) * 100",
                    },
                    "Value": {
                        "0": f"<b>{TPR}%</b>" if case == "TPR" else f"{TPR}%",
                        "1": f"<b>{FPR}%</b>" if case == "FPR" else f"{FPR}%",
                        "2": f"<b>{FNR}%</b>" if case == "FNR" else f"{FNR}%",
                    },
                    "TestStep Result": {
                        "0": (
                            f"FAILED, expected to be greater than {SlotOffer.Thresholds.THRESHOLD_TPR}%"
                            if case == "TPR" and TPR <= SlotOffer.Thresholds.THRESHOLD_TPR
                            else (
                                f"PASSED - the rate is greater than {SlotOffer.Thresholds.THRESHOLD_TPR}%"
                                if case == "TPR" and TPR > SlotOffer.Thresholds.THRESHOLD_TPR
                                else "-"
                            )
                        ),
                        "1": (
                            f"FAILED, expected to be less than {SlotOffer.Thresholds.THRESHOLD_FPR}%"
                            if case == "FPR" and FPR >= SlotOffer.Thresholds.THRESHOLD_FPR
                            else (
                                f"PASSED - the rate is less than {SlotOffer.Thresholds.THRESHOLD_FPR}%"
                                if case == "FPR" and FPR < SlotOffer.Thresholds.THRESHOLD_FPR
                                else "-"
                            )
                        ),
                        "2": (
                            f"FAILED, expected to be less than {SlotOffer.Thresholds.THRESHOLD_FNR}%"
                            if case == "FNR" and FNR >= SlotOffer.Thresholds.THRESHOLD_FNR
                            else (
                                f"PASSED - the rate is less than {SlotOffer.Thresholds.THRESHOLD_FNR}%"
                                if case == "FNR" and FNR < SlotOffer.Thresholds.THRESHOLD_FNR
                                else "-"
                            )
                        ),
                    },
                }
            )
            pb_rates = go.Figure(
                data=[
                    go.Table(
                        columnwidth=[40, 30, 12],
                        header=dict(
                            values=list(parking_box_rates.columns),
                            fill_color="rgb(255,165,0)",
                            font=dict(size=12, family="Arial", color="rgb(0,0,0)"),
                        ),
                        cells=dict(
                            values=[parking_box_rates[col] for col in parking_box_rates.columns],
                            height=40,
                            align="center",
                            font=dict(size=12),
                        ),
                    )
                ]
            )
            pb_rates.update_layout(
                constants.PlotlyTemplate.lgt_tmplt,
                height=fh.calc_table_height(parking_box_rates["Parking Box Rates"].to_dict()),
                title=dict(
                    text="Parking Box Rates:",
                    font=dict(size=20, weight="bold"),
                    xanchor="center",
                    yanchor="top",
                    x=0.5,
                    y=0.95,
                ),
                margin=dict(t=30, l=0),
            )
            plots.append(pb_rates)
            plots.insert(3, plots.pop())

            self.result.measured_result = NAN
            if "TPR" in case:
                self.result.measured_result = Result.from_string(f"{TPR} %")

            elif "FPR" in case:
                self.result.measured_result = Result.from_string(f"{FPR} %")

            elif "FNR" in case:
                self.result.measured_result = Result.from_string(f"{FNR} %")

            # Add the plots to the result object
            for remark in remarks:
                self.result.details["Remarks"].append(remark)
            for plot in plots:
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=1,
    name="True Positive Rate",
    description=f"The True Positive Rate should be greater than {SlotOffer.Thresholds.THRESHOLD_TPR}%.",
    expected_result=f"> {SlotOffer.Thresholds.THRESHOLD_TPR} %",
)
@register_signals(EXAMPLE, Signals)
@register_pre_processor(alias="SI_slot_offer", pre_processor=Preprocessor)
class TPTestStep(GenericTestStep):
    """
    TPTestStep is a subclass of GenericTestStep that overrides the process method to set a specific case value.

    Methods:
        process(**kwargs): Sets the case to "TPR" and calls the parent class's process method with this value.
    """

    def process(self, **kwargs):
        """
        The function `process` sets the variable `case` to "TPR" and then calls the `process` method of
        the parent class with this value.
        """
        case = "TPR"
        super().process(case)


@teststep_definition(
    step_number=2,
    name="False Positive Rate",
    description=f"The False Positive Rate should be less than {SlotOffer.Thresholds.THRESHOLD_FPR}%.",
    expected_result=f"< {SlotOffer.Thresholds.THRESHOLD_FPR} %",
)
@register_signals(EXAMPLE, Signals)
@register_pre_processor(alias="SI_slot_offer", pre_processor=Preprocessor)
class FPTestStep(GenericTestStep):
    """
    FPTestStep is a subclass of GenericTestStep that overrides the process method to set a specific case value.

    Methods:
        process(**kwargs): Sets the case to "FPR" and calls the parent class's process method with this value.
    """

    def process(self, **kwargs):
        """
        The function `process` sets the variable `case` to "FPR" and then calls the `process` method of
        the parent class with this value.
        """
        case = "FPR"
        super().process(case)


@teststep_definition(
    step_number=3,
    name="False Negative Rate",
    description=f"The False Negative Rate should be less than {SlotOffer.Thresholds.THRESHOLD_FNR}%.",
    expected_result=f"< {SlotOffer.Thresholds.THRESHOLD_FNR} %",
)
@register_signals(EXAMPLE, Signals)
@register_pre_processor(alias="SI_slot_offer", pre_processor=Preprocessor)
class FNTestStep(GenericTestStep):
    """
    FNTestStep is a subclass of GenericTestStep that overrides the process method to set a specific case value.

    Methods:
        process(**kwargs): Sets the case to "FNR" and calls the parent class's process method with this value.
    """

    def process(self, **kwargs):
        """
        The function `process` sets the variable `case` to "FNR" and then calls the `process` method of
        the parent class with this value.
        """
        case = "FNR"
        super().process(case)


@testcase_definition(
    name="Slot Offer for SI - TestCase",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FMD_K4BUUCvLEe6mrdm2_agUYg&vvc.configuration=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fcm%2Fstream%2F_G3kr8DgnEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg&artifactInModule=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_8BbkUJs4Ee6Zoo0NnU8erA",
    description="Parking slots are classified as True Positive (<b>TP</b>), False Positive (<b>FP</b>), or False Negative (<b>FN</b>) \
                based on type matching, overlap percentage, orientation difference, and center distance. \
                The classification serves as the basis for calculating the corresponding rates.",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SISlotOfferRate(TestCase):
    """Test Case of the KPI for Slot Offering - SI"""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            TPTestStep,
            FPTestStep,
            FNTestStep,
        ]
