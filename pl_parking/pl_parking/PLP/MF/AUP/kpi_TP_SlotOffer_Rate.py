"""True Positive Slot Offer KPI
The KPI must be runned with the measurements and the json files within the same directory.
The name of the measurement and the name of the JSON file must be the same.
"""

import base64
import io
import json
import logging
import os
import sys

import matplotlib.path as MplPath
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
from scipy.spatial import KDTree
from shapely.geometry import Polygon

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
from time import time as start_time

from tsf.core.results import DATA_NOK, TRUE, Result  # nopep8
from tsf.core.testcase import (
    PreProcessor,
    TestCase,
    TestStep,
    register_inputs,
    register_pre_processor,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants

# from pl_parking.PLP.MF.PARKSM.ft_parksm import StatisticsExample
from pl_parking.common_ft_helper import MfCustomTestcaseReport
from pl_parking.PLP.MF.constants import SlotOffer

__author__ = "BA ADAS ENP SIMU KPI"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

EXAMPLE = "TP_SELECTED_SLOT_OFFER_ADCU"
now_time = start_time()


def intersection_fig(json_coords, signal_coords, overlap_percentage, THRESHOLD_OVERLAP, existing_fig=None):
    """
    Compute the intersection of two polygons defined by JSON and signal coordinates
    and visualize the overlapping area on a Plotly figure.

    Parameters:
    - json_coords (list of tuples): Coordinates of the JSON polygon.
    - signal_coords (list of tuples): Coordinates of the signal polygon.
    - existing_fig (plotly.graph_objects.Figure, optional): Existing figure to extend.
    If None, a new figure will be created.

    Returns:
    - plotly.graph_objects.Figure: Figure with the overlapping area added.
    """
    # Converting JSON and signal coordinates into polygons for geometric operations.
    json_polygon = Polygon(json_coords)
    signal_polygon = Polygon(signal_coords)

    # Calculating the intersection between signal_polygon and json_polygon.
    intersection = signal_polygon.intersection(json_polygon)
    intersection_coords = list(intersection.exterior.coords)

    if not intersection.is_empty:
        # If an existing figure is not provided, create a new one.
        if existing_fig is None:
            fig = go.Figure()
        else:
            fig = existing_fig

        # Add the overlapping area to the figure.
        fig.add_trace(
            go.Scatter(
                x=[point[0] for point in intersection_coords],
                y=[point[1] for point in intersection_coords],
                fill="toself",
                fillcolor="rgba(0, 255, 0, 0.2)" if overlap_percentage >= THRESHOLD_OVERLAP else "rgba(255, 0, 0, 0.2)",
                line=dict(
                    color="rgba(0, 255, 0, 1.0)" if overlap_percentage >= THRESHOLD_OVERLAP else "rgba(255, 0, 0, 1.0)"
                ),
                mode="lines+text",
                name="Overlapping area",
            )
        )

        return fig
    else:
        # If there is no overlap, return the existing or provided figure.
        return existing_fig


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
    percetage_calculated_slot = "No Slot Selected"
    if not intersection.is_empty:
        intersection_area = intersection.area
        json_polygon_area = json_polygon.area
        signal_polygon_area = signal_polygon.area

        max_area = max(json_polygon_area, signal_polygon_area)
        if max_area != 0:
            overlap_percentage = (intersection_area / max_area) * 100
        if max_area == json_polygon_area:
            percetage_calculated_slot = "Selected Slot"
        else:
            percetage_calculated_slot = "Ground Truth Parking Slot"

    return intersection, overlap_percentage, percetage_calculated_slot


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


def process_json_section(
    file_data, timestamp, time_obj_string_timestamp, timestamp_dict_GT, gt_park_slot_centers, section_name
):
    """
    Process a JSON section containing timestamped data related to parking slots.

    Parameters:
        file_data (dict): A dictionary containing JSON data.
        timestamp (int): The timestamp to search for in the data.
        time_obj_string_timestamp (str): The key name representing the timestamp in each timed object.
        timestamp_dict_GT (dict): A dictionary to store processed timestamp data.
        gt_park_slot_centers (list): A list to store calculated centers of parking slots.
        section_name (str): The name of the section within the file_data dictionary to process.

    Returns:
        tuple: A tuple containing two elements:
            - timestamp_dict_GT (dict): Updated dictionary with processed timestamp data.
            - gt_park_slot_centers (list): Updated list with calculated centers of parking slots.
    """
    timestamp_data_GT = {}

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
                                gt_park_slot_centers.append(gt_park_slot_center)

                            timestamp_data_GT = dict_GT_centers
                            timestamp_dict_GT[timestamp] = timestamp_data_GT
                        else:
                            # Handle the case when timestamps do not match
                            pass

    return timestamp_dict_GT, gt_park_slot_centers


def process_signal_coordinates(timestamp, filtered_df, sg_slot_coords):
    """
    Process signal coordinates for a given timestamp and parking slots.

    Parameters:
        timestamp (int): The timestamp for which coordinates are to be processed.
        filtered_df (DataFrame): A pandas DataFrame containing filtered signal data.
        sg_slot_coords (list): A list of strings representing the slot coordinates.

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


def check_point_inside_detection_box(point, box):
    """
    Check if a point is inside a detection box.

    Parameters:
    - point (tuple): Coordinates of the point.
    - box (list of dicts): List of dictionaries containing 'x' and 'y' keys defining the box vertices.

    Returns:
    - bool: True if the point is inside the box, False otherwise.
    """
    # Define the accuracy threshold for point inclusion
    ACCURACY_THRESHOLD = 0.000001

    # Extract x and y coordinates from the 'box' dictionary
    coordinates = [(d["x"], d["y"]) for d in box]

    # Check if all coordinates in 'coordinates' are (0, 0)
    if all(coord == (0, 0) for coord in coordinates):
        return False
    else:
        try:
            # Create a matplotlib Path object for efficient point-in-polygon testing
            obj_mpl_path = MplPath.Path(np.array(coordinates))

            # Check if the point is inside the polygon with the specified accuracy
            point_array = np.array([point[0][1], point[1][1]])
            return obj_mpl_path.contains_point(point_array, radius=ACCURACY_THRESHOLD) or obj_mpl_path.contains_point(
                point_array, radius=-ACCURACY_THRESHOLD
            )
        except ValueError as e:
            # Handle exceptions and log an error message
            print(f"Error creating Path object: {e}")
            # write_log_message(f"Error creating Path object: {e}", "error", LOGGER)


def calculate_distance(centers_signal, centers_gt):
    """
    Calculates the Euclidean distance between two specified points.

    Parameters:
    centers_signal (list): A list of tuples representing the signal coordinates. Each tuple is in the form (x, y).
    centers_gt (list): A list of tuples representing the ground truth coordinates. Each tuple is in the form (x, y).

    Returns:
    float: The Euclidean distance between the specified points.
    """
    return np.linalg.norm(np.array([centers_signal[0], centers_signal[1]]) - np.array([centers_gt[0], centers_gt[1]]))
    # return np.linalg.norm(
    #     np.array([centers_signal[0][1], centers_signal[1][1]]) - np.array([centers_gt[0][1], centers_gt[1][1]])
    # )


def are_points_collinear(point1, point2, point3, absolute_tolerance=0.1):
    """
    Check if three points are collinear in a 2D plane, dynamically adjusting for distances.

    Parameters:
    - point1, point2, point3: Dictionaries with 'x' and 'y' keys representing the coordinates of the three points.
    - absolute_tolerance: The maximum allowed deviation for collinearity in meters (e.g., ±0.2 meters).

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


def is_horizontal(line, tolerance=2):
    """Function to check if a line is horizontal"""
    _, y1, _, y2 = line
    return abs(y1 - y2) < tolerance


def find_vertical_lines(points, **kwargs):
    """
    Identifies vertical lines from a set of points and appends them to the provided vertical_lines list.
    Args:
        points (list): A list of dictionaries, where each dictionary represents a point with 'x' and 'y' coordinates.
    Returns:
        list: The updated vertical_lines list containing the identified vertical lines.
    """
    z = []
    horizontal_lines = []
    vertical_lines = []

    for point in points:
        for other_point in points:
            if other_point != point:
                line = (point["x"], point["y"], other_point["x"], other_point["y"])
                if is_horizontal(line):
                    z.append(line)
                    horizontal_lines.append(line)

    for line in z:
        x1, y1, x2, y2 = line
        if kwargs.get("left_points") is not None:
            x = min(x1, x2)
        else:
            x = max(x1, x2)
        y = y1 if x == x1 else y2
        vertical_lines.append((x, y))

    return vertical_lines


def check_collinearity_new(timestamp_data, tolerance=0.2, **kwargs):
    """
    Check collinearity of points in timestamp data.

    Parameters:
        timestamp_data (dict): A dictionary containing timestamp data.
            Keys: Timestamp (int)
            Values: List of points (dict) containing 'x' and 'y' coordinates.
        tolerance (float): Tolerance level for collinearity check (default is 0.2).
        **kwargs: Additional keyword arguments:
            - mirror_x_left (float): X-coordinate of the left mirror.
            - mirror_x_right (float): X-coordinate of the right mirror.
            - mirror_y_left (float): Y-coordinate of the left mirror.
            - mirror_y_right (float): Y-coordinate of the right mirror.
            - rear (float): Y-coordinate of the rear point.

    Returns:
        int or None: Timestamp where collinearity is detected, or None if no collinearity is found within the tolerance.

    Note:
        This function checks collinearity of points based on the provided timestamp data and additional mirror or rear points.
        If mirror points are provided, it checks collinearity between the second pair of coordinates and the mirror points.
        If a rear point is provided, it checks collinearity between the first and last pairs of coordinates and the rear point.
    """
    # Constants
    d_next_to = 0.5

    for timestamp, points in timestamp_data.items():
        collinear_left = False
        collinear_right = False
        if (
            kwargs.get("mirror_x_left") is not None
            and kwargs.get("mirror_x_right") is not None
            and kwargs.get("mirror_y_left") is not None
            and kwargs.get("mirror_y_right") is not None
        ):
            # Check collinearity with mirror points
            # Sort points by the x value
            vertical_lines = find_vertical_lines(points, left_points="left_points")

            final_vertical_line = tuple(dict.fromkeys(vertical_lines))
            vertical_lines.clear()
            left_mirror = {"x": kwargs["mirror_x_left"] - d_next_to, "y": kwargs["mirror_y_left"]}
            right_mirror = {"x": kwargs["mirror_x_right"] - d_next_to, "y": kwargs["mirror_y_right"]}
            # left_mirror = {"x": kwargs["mirror_x_left"] , "y": kwargs["mirror_y_left"] - d_next_to}
            # right_mirror = {"x": kwargs["mirror_x_right"], "y": kwargs["mirror_y_right"] - d_next_to}
            point1 = {"x": final_vertical_line[0][0], "y": final_vertical_line[0][1]}
            point2 = {"x": final_vertical_line[1][0], "y": final_vertical_line[1][1]}
            # if are_points_collinear(point1, point2, left_mirror, tolerance) or \
            #         are_points_collinear(point1, point2, right_mirror, tolerance):
            #     return timestamp
            if abs(point1["y"] - left_mirror["y"]) < abs(point1["y"] - right_mirror["y"]):
                collinear_left = are_points_collinear(point1, point2, left_mirror, tolerance)
            else:
                collinear_right = are_points_collinear(point1, point2, right_mirror, tolerance)
            if collinear_left or collinear_right:
                return timestamp

        elif kwargs.get("rear") is not None:
            vertical_lines = find_vertical_lines(points)
            final_vertical_line = tuple(dict.fromkeys(vertical_lines))
            vertical_lines.clear()

            point1 = {"x": final_vertical_line[0][0], "y": final_vertical_line[0][1]}
            point2 = {"x": final_vertical_line[1][0], "y": final_vertical_line[1][1]}
            rear_point = {"x": kwargs["rear"], "y": 0}
            collinear = are_points_collinear(point1, point2, rear_point, tolerance)
            if collinear:
                return timestamp

    return None


def transform_timestamp(timestamp, epoch):
    """
    Transform a timestamp into a relative time value based on a specified epoch.

    Parameters:
    - timestamp (float): The timestamp to be transformed.
    - epoch (float): The reference epoch.

    Returns:
    - float: The transformed relative time value.
    """
    return (timestamp / constants.GeneralConstants.US_IN_S) - epoch


def associate_parking_slots(dict_GT_local, dict_scanned_local, file_data, timestamp):
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
    # Filter the dictionary to get only the values after the given timestamp
    filtered_gt_centers = {ts: centers for ts, centers in dict_GT_local.items() if ts > timestamp}
    gt_centers = list(next(iter(filtered_gt_centers.values())).keys())

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
    for _, scanned_data in dict_scanned_local[timestamp].items():
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
                    "GT_coordinates": file_data[vehicle_local][0]["timedObjs"][0]["parkingBoxes"][index][
                        "slotCoordinates_m"
                    ],
                    "ID_parking_box": file_data[vehicle_local][0]["timedObjs"][0]["parkingBoxes"][index]["objectId"],
                    "distance": dist,
                    "scanned_coordinates": scanned_coords,
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
    # Find the association with the lowest distance
    associtated_parking_slot = min(associations_dict.items(), key=lambda x: x[1]["distance"])
    return associtated_parking_slot


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        sg_time = "uiTimeStamp"
        sg_parksm_core_status_state = "ParkSmCoreStatusState"
        sg_num_valid_parking_boxes = "NumValidParkingBoxes"
        sg_velocity = "EgoMotionPort"
        Slotcoordinates_x = "Slotcoordinates_{}_{}_x"
        Slotcoordinates_y = "Slotcoordinates_{}_{}_y"
        sg_selection_status = "SelectionStatus"
        sg_position_x = "PositionX"
        sg_position_y = "PositionY"
        sg_position_yaw = "PositionYaw"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = [
            "SIM VFB",
            "MTA_ADC5",
        ]
        self._properties = {
            # self.Columns.sg_time: ".TimeStamp",
            self.Columns.sg_time: [
                ".MF_TRJPLA_DATA.syncRef.m_sig_parkingBoxPort.uiTimeStamp",
                ".MF_TRJPLA_1.syncRef.m_sig_parkingBoxPort.uiTimeStamp",
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
            self.Columns.sg_parksm_core_status_state: [
                ".MF_PARKSM_CORE_DATA.parksmCoreStatusPort.parksmCoreState_nu",
                ".MfPsmCore.parksmCoreStatusPort.parksmCoreState_nu",
            ],
            self.Columns.sg_num_valid_parking_boxes: [
                ".SI_DATA.m_parkingBoxesPort.numValidParkingBoxes_nu",
                ".SiCoreGeneric.m_parkingBoxesPort.numValidParkingBoxes_nu",
            ],
            self.Columns.sg_velocity: [".SI_DATA.m_egoMotionPort.vel_mps", ".SiCoreGeneric.m_egoMotionPort.vel_mps"],
            self.Columns.sg_selection_status: [
                ".MF_TRJPLA_DATA.targetPoses.selectedPoseData.selectionStatus",
                ".MF_TRJPLA_1.targetPoses.selectedPoseData.selectionStatus",
            ],
        }
        iteration_tuples = []
        for i in range(8):  # 8
            for j in range(4):  # 4
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
            vehicle_local_string = "VehicleLocal" if "VehicleLocal" in file_data else "VehicleLocalSlots"
            vehicle_local_coordinates = file_data.get("VehicleLocal") or file_data.get("VehicleLocalSlots")
            if not vehicle_local_string:
                raise ValueError("VehicleLocal/VehicleLocalSlots not found in JSON file")

            # Extract timedObjs from the first element of VehicleLocal
            timed_objs = vehicle_local_coordinates[0].get("timedObjs")
            if not timed_objs:
                raise ValueError("timedObjs not found in VehicleLocal")

            # Look for the key that ends with ".uiTimeStamp" in the first element of timedObjs
            for key in timed_objs[0].keys():
                if key.endswith(".uiTimeStamp"):
                    return key, vehicle_local_string

            # If no key ending with '.uiTimeStamp' is found, raise an error
            raise ValueError("No key ending with '.uiTimeStamp' found in timedObjs")

        file_path = os.path.basename(self.artifacts[0].file_path)
        time_obj_string_timestamp = None
        vehicle_local_string = None
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
                time_obj_string_timestamp, vehicle_local_string = get_time_obj_string(file_data)
        except FileNotFoundError as e:
            raise FileNotFoundError("No JSON file found matching the identifier.") from e

        return file_data, time_obj_string_timestamp, vehicle_local_string


signals_obj = Signals()


@register_pre_processor(alias="AUP_slot_offer", pre_processor=Preprocessor)
class GenericTestStep(TestStep):
    """Generic TestStep to use the calculation for both scenarios"""

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        super().__init__()
        self.test_result = None

    def process(self, collinear_timestamp):
        """
        The process function is the main function of a process. It will be called by the framework and should contain
        the actual processing logic. The return value of this function will be stored in the result object, which can then
        be used to create plots or other output artifacts.

        :param self: Represent the instance of the class
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
            self.test_result = fc.INPUT_MISSING
            plot_titles, plots, remarks = fh.rep([], 3)
            df = pd.DataFrame()
            signal_name = {}
            signal_name = signals_obj._properties
            time = None
            eval_cond = [False] * 3
            self.result.measured_result = TRUE
            TPR = 0
            pre_processor_key = list(x for x in self.pre_processors.keys() if x.startswith("AUP_slot_offer"))[0]
            file_data, time_obj_string_timestamp, vehicle_local_string = self.pre_processors[pre_processor_key]
            file_path = os.path.basename(self.artifacts[0].file_path)
            # Initialize dictionaries and lists
            result_dict = {}
            results = []
            first_collinear_timestamp = None
            dict_scanned_local = {}
            dict_GT_park = {}
            gt_park_slot_centers_park = []
            json_timestamps_park = []
            dict_GT_local = {}
            gt_park_slot_centers_local = []
            json_timestamps_local = []
            local_parking_box_dict = {}
            associate_parking_slot = {}
            # Initialize Plotly figure
            fig_gt = px.scatter(x=[0, 0, 0, 0, 0, 0, 0, 0], y=[0, 0, 0, 0, 0, 0, 0, 0])

            # Get the absolute path of the current script file
            script_path = os.path.realpath(__file__)
            image_path = None
            # Extract the directory path
            image_base_path = os.path.dirname(script_path)

            # Define the image filenames
            image1_filename = r"next_to_parkingbox.png"
            image2_filename = r"fully_passed_parkingbox.png"

            # Extract car coordinates
            # from: github-am.geo.conti.de/ADAS/mf_common/blob/2e24136b576160a23685eaf61ccc3abe3ca94b2f/interface/platform/ultrasonic_parking/Vehicle_Params_default_set.h
            mirror_x_left = SlotOffer.CarCoordinates.LEFT_MIRROR_REAR_LEFT_CORNER[0]
            mirror_x_right = SlotOffer.CarCoordinates.RIGHT_MIRROR_REAR_RIGHT_CORNER[0]
            mirror_y_left = SlotOffer.CarCoordinates.LEFT_MIRROR_REAR_LEFT_CORNER[1]
            mirror_y_right = SlotOffer.CarCoordinates.RIGHT_MIRROR_REAR_RIGHT_CORNER[1]
            rear = SlotOffer.CarCoordinates.REAR_LEFT[0]

            car_fix_coordinates = [
                value for key, value in vars(SlotOffer.CarCoordinates).items() if not key.startswith("__")
            ]
            car_fix_coordinates.append(car_fix_coordinates[0])

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

            for i in range(8):
                df_temp = pd.DataFrame()
                for j in range(4):
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
            # Extract JSON timestamps for local vehicles and parking start
            json_timestamps_local = [
                timed_obj[time_obj_string_timestamp]
                for entry in file_data.get(vehicle_local_string, [])
                # for entry in file_data.get("VehicleLocal", []) + file_data.get("VehicleLocalSlots", [])
                for timed_obj in entry.get("timedObjs", [])
            ]
            # Filter DataFrame based on local timestamps
            filtered_df = df[df.index.isin(json_timestamps_local)]
            # Remove duplicate indexes from the filtered DataFrame
            duplicate_indexes = filtered_df.index.duplicated()
            filtered_df = filtered_df[~duplicate_indexes]

            time = filtered_df.index / constants.GeneralConstants.US_IN_S
            epoch = time[0]
            time = time - epoch

            json_timestamps_park = None
            if "ParkingStarted" in file_data and file_data["ParkingStarted"]:
                for entry in file_data["ParkingStarted"]:
                    if "timedObjs" in entry and entry["timedObjs"]:
                        json_timestamps_park = entry["timedObjs"][0].get(time_obj_string_timestamp, None)
                        if json_timestamps_park:
                            break

            if json_timestamps_park is None:
                self.test_result = fc.INPUT_MISSING
                self.result.measured_result = DATA_NOK
                signal_summary = pd.DataFrame(
                    {
                        "Evaluation": {
                            "0": "Evaluation was not possible due to no selection of a parking box.",
                        },
                        "Verdict": {
                            "0": "FAILED",
                        },
                    }
                )
                sig_sum = fh.build_html_table(signal_summary)
                plots.append(sig_sum)

                fig1 = go.Figure()
                fig1.add_trace(
                    go.Scatter(
                        x=time.tolist(),
                        y=filtered_df[Signals.Columns.sg_num_valid_parking_boxes].values.tolist(),
                        mode="lines",
                        name=f"{signal_name[Signals.Columns.sg_num_valid_parking_boxes]}",
                        yaxis="y",
                        showlegend=True,
                    )
                )
                fig1.add_trace(
                    go.Scatter(
                        x=time.tolist(),
                        y=filtered_df[Signals.Columns.sg_selection_status].values.tolist(),
                        mode="lines",
                        name=f"{signal_name[Signals.Columns.sg_selection_status]}",
                        yaxis="y",
                        showlegend=True,
                    )
                )
                fig1.add_trace(
                    go.Scatter(
                        x=time.tolist(),
                        y=filtered_df[Signals.Columns.sg_velocity].values.tolist(),
                        mode="lines",
                        name=f"{signal_name[Signals.Columns.sg_velocity]}",
                        yaxis="y",
                        showlegend=True,
                    )
                )
                fig1.add_trace(
                    go.Scatter(
                        x=time.tolist(),
                        y=filtered_df[Signals.Columns.sg_parksm_core_status_state].values.tolist(),
                        mode="lines",
                        name=f"{signal_name[Signals.Columns.sg_parksm_core_status_state]}",
                        yaxis="y",
                        showlegend=True,
                    )
                )

                fig1.layout = go.Layout(
                    yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]"
                )
                fig1.update_layout(
                    constants.PlotlyTemplate.lgt_tmplt,
                    title_text="Graphical overview for multiple SlotOffer related signals",
                )
                plots.append(fig1)
                for plot in plots:
                    if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                        self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                    else:
                        self.result.details["Plots"].append(plot)
                return

            for timestamp in filtered_df.index:
                dict_GT_park, gt_park_slot_centers_park = process_json_section(
                    file_data,
                    timestamp,
                    time_obj_string_timestamp,
                    dict_GT_park,
                    gt_park_slot_centers_park,
                    "ParkingStarted",
                )
                dict_GT_local, gt_park_slot_centers_local = process_json_section(
                    file_data,
                    timestamp,
                    time_obj_string_timestamp,
                    dict_GT_local,
                    gt_park_slot_centers_local,
                    vehicle_local_string,
                )
            selection_timestamp = filtered_df.index[filtered_df[Signals.Columns.sg_selection_status] == 2][0]

            for timestamp in filtered_df.index[filtered_df.index >= json_timestamps_park]:
                if timestamp >= selection_timestamp:
                    # Process and extract signals' data, resulting in a second dictionary filled with all scanned parking slots
                    coord_dict = process_signal_coordinates(timestamp, filtered_df, sg_slot_coords)
                    dict_scanned_local[timestamp] = coord_dict
                    # Check condition for 'SlotCoordinates_0'
                    slot_0_values = coord_dict.get("Slotcoordinates_0", {})
                    key_values_0 = next(
                        iter(slot_0_values.keys()), None
                    )  # Get the first tuple from 'Slotcoordinates_0'
                    # Check if 'SlotCoordinates_0' has values different from 0
                    if key_values_0 and all(value != 0 for key, value in key_values_0):
                        # Check condition for all other 'SlotCoordinates'
                        all_other_slots_condition = all(
                            next(iter(coord_dict.get(f"Slotcoordinates_{i}", {}).keys()), ())
                            == (("x", 0.0), ("y", 0.0))
                            for i in range(1, 8)
                        )
                        if all_other_slots_condition:
                            result_dict[timestamp] = coord_dict
                            eval_cond[0] = True

            if eval_cond[0]:
                result_timestamp = result_dict[next(iter(result_dict), None)]
                gt_timestamp = dict_GT_park[json_timestamps_park]
                associate_parking_slot = associate_parking_slots(
                    dict_GT_local, dict_scanned_local, file_data, next(iter(result_dict), None)
                )
                for entry in file_data.get(vehicle_local_string, []):
                    for timesdobjs in entry["timedObjs"]:
                        timestamp = timesdobjs[time_obj_string_timestamp]
                        for index in range(len(timesdobjs["parkingBoxes"])):
                            if (
                                timesdobjs["parkingBoxes"][index]["objectId"]
                                == associate_parking_slot[1]["ID_parking_box"]
                            ):
                                selected_parking_box = timesdobjs["parkingBoxes"][index]["slotCoordinates_m"]
                                local_parking_box_dict[timestamp] = selected_parking_box
                                break

                if "NextTo" in collinear_timestamp:
                    # Check collinearity for both left and right mirrors
                    first_collinear_timestamp = check_collinearity_new(
                        local_parking_box_dict,
                        mirror_x_left=mirror_x_left,
                        mirror_x_right=mirror_x_right,
                        mirror_y_left=mirror_y_left,
                        mirror_y_right=mirror_y_right,
                    )
                    image_path = os.path.join(image_base_path, "TP-SlotOffer-imgs", image1_filename)
                    scenario = "NEXT TO PARKING BOX"
                else:
                    first_collinear_timestamp = check_collinearity_new(local_parking_box_dict, rear=rear)
                    image_path = os.path.join(image_base_path, "TP-SlotOffer-imgs", image2_filename)
                    scenario = "FULLY PASSED THE PARKING BOX"

                if first_collinear_timestamp:
                    if next(iter(result_dict), None) < first_collinear_timestamp:
                        eval_cond[1] = True
                        slot_to_be_calculated = list(result_dict[first_collinear_timestamp].items())[
                            0
                        ]  # The first(remaining) PB is the one selected
                        SlotCoordinates, centers_signal_dict = slot_to_be_calculated

                        # gt_slot_selected = list(gt_timestamp.items())[associate_parking_slot[1]["ID_parking_box"]]
                        for center in gt_timestamp.keys():
                            rounded_center = tuple((k, round(v, 1)) for k, v in center)
                            rounded_gt_center = tuple(
                                (k, round(v, 1)) for k, v in associate_parking_slot[1]["GT_center"]
                            )
                            if rounded_center == rounded_gt_center:
                                gt_slot_selected = list(gt_timestamp.items())[list(gt_timestamp.keys()).index(center)]
                                break
                        _, parking_box_gt = gt_slot_selected

                        # Proceed with the processing for the second item
                        for _, parking_box_signal in centers_signal_dict.items():
                            coordinates_box_gt = [(dict["x"], dict["y"]) for dict in parking_box_gt]
                            coordinates_box_signal = [(dict["x"], dict["y"]) for dict in parking_box_signal]
                            intersection_area, overlap_percentage, percentage_calculated_slot = calculate_overlap(
                                coordinates_box_gt, coordinates_box_signal
                            )
                            results.append(
                                {
                                    SlotCoordinates: {
                                        "Timestamp": first_collinear_timestamp,
                                        "parking_box_signal": parking_box_signal,
                                        "parking_box_gt": parking_box_gt,
                                        "intersection_area": intersection_area,
                                        "overlap_percentage": overlap_percentage,
                                    }
                                }
                            )
                        if overlap_percentage > SlotOffer.Thresholds.THRESHOLD_OVERLAP:
                            eval_cond[2] = True
                            self.test_result = fc.PASS
                            TPR = 100
                        else:
                            self.test_result = fc.FAIL
                            print(
                                f"Regarding {file_path}, the percentage of the overlap was not greater than the threshold, the scenario being {scenario}"
                            )
                    else:
                        self.test_result = fc.FAIL
                        print(
                            f"Regarding {file_path}, the timestamp that we've looked for is not smaller than the timestamp of the collinearity in the {scenario} scenario"
                        )
                else:
                    self.test_result = fc.FAIL
                    print(f"Regarding {file_path}, there is no collinearity found for the scenario {scenario}")
            else:
                self.test_result = fc.FAIL
                print(f"Regarding {file_path}, could not find a timestamp where a single parking box is available.")

            cond_0 = " ".join("One parking space must be selected.".split())

            cond_1 = " ".join(
                "The parking space should be chosen before the car reaches the \
                            designated point of the parking area.".split()
            )
            self.result.measured_result = Result.from_string(f"{TPR} %")
            cond_2 = " ".join(f"The overlap percentage must exceed {SlotOffer.Thresholds.THRESHOLD_OVERLAP}%.".split())
            # Set table datatframe
            signal_summary = pd.DataFrame(
                {
                    "Condition": {
                        "0": cond_0,
                        "1": cond_1,
                        "2": cond_2,
                    },
                    "Result": {
                        "0": (
                            "A parking slot was selected."
                            if eval_cond[0]
                            else "A parking slot was not selected at all."
                        ),
                        "1": (
                            " ".join(
                                f"The parking slot was successfully chosen prior to the \
                                    specified timestamp[{first_collinear_timestamp}({round(transform_timestamp(first_collinear_timestamp, epoch),4)}s)]. Slot was chosen at {next(iter(result_dict), None)}({round(transform_timestamp(next(iter(result_dict), None), epoch),4)}s)".split()
                            )
                            if eval_cond[1]
                            else " ".join(
                                f"The parking slot was not chosen before the \
                                    specified timestamp[{first_collinear_timestamp}({round(transform_timestamp(first_collinear_timestamp, epoch),4)}s))]. Slot was chosen at {next(iter(result_dict), None)}({round(transform_timestamp(next(iter(result_dict), None), epoch),4)}s)".split()
                            )
                        ),
                        "2": (
                            " ".join(
                                f"The calculated overlap percentage ({round(overlap_percentage, 3)}%) exceeds the required \
                                threshold({SlotOffer.Thresholds.THRESHOLD_OVERLAP}%) at timestamp {first_collinear_timestamp}({round(transform_timestamp(first_collinear_timestamp, epoch),4)}s).".split()
                            )
                            if eval_cond[0] and eval_cond[1] and eval_cond[2]
                            else (
                                " ".join(
                                    f"The calculated overlap percentage ({round(overlap_percentage, 3)}%) does not exceed the required \
                                threshold({SlotOffer.Thresholds.THRESHOLD_OVERLAP}%) at timestamp {first_collinear_timestamp}({round(transform_timestamp(first_collinear_timestamp, epoch),4)}s).".split()
                                )
                                if eval_cond[0] and eval_cond[1] and not eval_cond[2]
                                else (
                                    " ".join(
                                        "A overlap percentage could not be calculated due to no parking selection \
                                before specified timestamp.".split()
                                    )
                                    if eval_cond[0] and not eval_cond[1] and not eval_cond[2]
                                    else "A overlap percentage could not be calculated due to no parking selection."
                                )
                            )
                        ),
                    },
                    "Verdict": {
                        "0": "PASSED" if eval_cond[0] else "FAILED",
                        "1": "PASSED" if eval_cond[1] else "FAILED",
                        "2": "PASSED" if eval_cond[2] else "FAILED",
                    },
                }
            )

            # Create table with eval conditions from the summary dict
            sig_sum = go.Figure(
                data=[
                    go.Table(
                        columnwidth=[50, 20, 7],
                        header=dict(
                            values=list(signal_summary.columns),
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
                constants.PlotlyTemplate.lgt_tmplt, height=fh.calc_table_height(signal_summary["Condition"].to_dict())
            )
            # plot_titles.append("Condition Evaluation")
            plots.append(sig_sum)
            remarks.append("")

            try:
                image = Image.open(image_path)
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
            except FileNotFoundError as e:
                print(f"File not found: {e}")
            except OSError as e:
                print(f"IOError: {e}")

            # Create figure
            fig_img = go.Figure()

            # Constants
            img_width = 1150
            img_height = 900
            scale_factor = 0.5

            # Add invisible scatter trace.
            # This trace is added to help the autoresize logic work.
            fig_img.add_trace(
                go.Scatter(
                    x=[0, img_width * scale_factor], y=[0, img_height * scale_factor], mode="markers", marker_opacity=0
                )
            )

            # Configure axes
            fig_img.update_xaxes(visible=False, range=[0, img_width * scale_factor])

            fig_img.update_yaxes(
                visible=False,
                range=[0, img_height * scale_factor],
                # the scaleanchor attribute ensures that the aspect ratio stays constant
                scaleanchor="x",
            )

            # Add image
            fig_img.add_layout_image(
                dict(
                    x=0,
                    sizex=img_width * scale_factor,
                    y=img_height * scale_factor,
                    sizey=img_height * scale_factor,
                    xref="x",
                    yref="y",
                    opacity=1.0,
                    layer="below",
                    sizing="stretch",
                    source=f"data:image/png;base64,{img_str}",
                )
            )

            ## Configure layout to center the image and add a title
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
                xaxis=dict(scaleanchor="y", scaleratio=1),
                yaxis=dict(scaleanchor="x", scaleratio=1),
                plot_bgcolor="rgba(0,0,0,0)",
            )
            plots.append(fig_img)

            # Display a graph that contains all th GT data with all the parking slots detected at a specific timestamp:
            fig_all_gt = go.Figure()
            parking_data = file_data["ParkingStarted"][0]["timedObjs"]

            for timed_obj in parking_data:
                for parking_box in timed_obj["parkingBoxes"]:
                    x_axis_gt2 = [point["x"] for point in parking_box["slotCoordinates_m"]]
                    x_axis_gt2.append(x_axis_gt2[0])
                    y_axis_gt2 = [point["y"] for point in parking_box["slotCoordinates_m"]]
                    y_axis_gt2.append(y_axis_gt2[0])
                    if max_x < max(x_axis_gt2):
                        max_x = max(x_axis_gt2)
                    if min_x > min(x_axis_gt2):
                        min_x = min(x_axis_gt2)
                    if max_y < max(y_axis_gt2):
                        max_y = max(y_axis_gt2)
                    if min_y > min(y_axis_gt2):
                        min_y = min(y_axis_gt2)

                    fig_all_gt.add_scatter(
                        x=x_axis_gt2,
                        y=y_axis_gt2,
                        mode="lines",
                        name="Ground truth parking slots",
                        legendgroup="ground_truth",
                        line=dict(color="blue"),
                        showlegend=False,  # Set showlegend to False for each scatter plot
                    )

            # Add a dummy scatter plot with the same legend group to display the legend only once
            fig_all_gt.add_scatter(
                x=[None],
                y=[None],
                mode="lines",
                marker=dict(color="blue"),
                name="Ground truth parking slots",
                legendgroup="ground_truth",
            )

            fig_all_gt.layout = go.Layout(
                yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="X", yaxis_title="Y"
            )

            if eval_cond[0]:
                x_axis_slot2 = [dict["x"] for dict in list(result_timestamp[next(iter(result_timestamp))].values())[0]]
                x_axis_slot2.append(x_axis_slot2[0])
                y_axis_slot2 = [dict["y"] for dict in list(result_timestamp[next(iter(result_timestamp))].values())[0]]
                y_axis_slot2.append(y_axis_slot2[0])
                fig_all_gt.add_scatter(
                    x=x_axis_slot2,
                    y=y_axis_slot2,
                    name="Vehicle selected slot",
                    mode="lines+markers",
                )

                fig_all_gt.update_layout(
                    height=700,
                    xaxis_range=[
                        min_x - abs(min_x) * SlotOffer.AutoScale.PERCENTAGE_X_GT,
                        max_x + abs(max_x) * SlotOffer.AutoScale.PERCENTAGE_X_GT,
                    ],
                    title_text=(
                        "Timestamp when the slot is selected:"
                        f" {next(iter(result_dict), None)} ({round(transform_timestamp(next(iter(result_dict), None), epoch),4)}s)"
                    ),
                )

                new_origin = [0, 0, 0]

                vehicle_plot = constants.DrawCarLayer.draw_car(new_origin[0], new_origin[1], new_origin[2])
                for p in vehicle_plot[1]:
                    fig_all_gt.add_trace(p)
            else:
                fig_all_gt.add_scatter(
                    x=[None],
                    y=[None],
                    mode="lines",
                    marker=dict(color="red"),
                    name="There was no slot selected.",
                )

            plots.append(fig_all_gt)

            if eval_cond[1]:
                for result in results:
                    for _, data in result.items():
                        # Create Figure
                        fig_gt = go.Figure()
                        # Extract x and y coordinates
                        x_axis_slot = [point["x"] for point in data["parking_box_signal"]]
                        y_axis_slot = [point["y"] for point in data["parking_box_signal"]]

                        centroid_slot = calculate_polygon_center(x_coordinates=x_axis_slot, y_coordinates=y_axis_slot)

                        x_axis_gt = [point["x"] for point in data["parking_box_gt"]]
                        y_axis_gt = [point["y"] for point in data["parking_box_gt"]]

                        centroid_GT = calculate_polygon_center(x_coordinates=x_axis_gt, y_coordinates=y_axis_gt)
                        distance = calculate_distance(centroid_slot, centroid_GT)

                        # Plotting Offered Slot, Target Center, and Ground Truth parking slot
                        x_axis_slot.append(x_axis_slot[0])
                        y_axis_slot.append(y_axis_slot[0])
                        x_axis_gt.append(x_axis_gt[0])
                        y_axis_gt.append(y_axis_gt[0])
                        fig_gt.add_scatter(x=x_axis_slot, y=y_axis_slot, name="Selected Slot", mode="lines+markers")
                        fig_gt.add_scatter(
                            x=[centroid_slot[0]], y=[centroid_slot[1]], mode="markers", name="Center of Selected Slot"
                        )
                        fig_gt.add_scatter(
                            x=[centroid_GT[0]], y=[centroid_GT[1]], mode="markers", name="Center of GT Slot"
                        )

                        fig_gt.add_scatter(x=x_axis_gt, y=y_axis_gt, name="Ground Truth parking slot")
                        # Set layout
                        fig_gt.layout = go.Layout(
                            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]"
                        )

                        # Calculate and set initial zoom level
                        min_x, max_x = min(x_axis_slot), max(x_axis_slot)
                        min_y, max_y = min(y_axis_slot), max(y_axis_slot)

                        color_overlap = (
                            "#008000"
                            if data["overlap_percentage"] > SlotOffer.Thresholds.THRESHOLD_OVERLAP
                            else "#ff0000"
                        )

                        fig_gt.update_layout(
                            xaxis_range=[
                                min_x - abs(min_x) * SlotOffer.AutoScale.PERCENTAGE_X_SLOT,
                                max_x + abs(max_x) * SlotOffer.AutoScale.PERCENTAGE_X_SLOT,
                            ],
                            title_text=(
                                "Timestamp when slot is calculated:"
                                f" {first_collinear_timestamp} ({round(transform_timestamp(first_collinear_timestamp, epoch),4)}s),"
                                "           Overlap:"
                                f" <span style='color: {color_overlap}'>{round(data['overlap_percentage'], 3)}%</span>"
                                f" of the {percentage_calculated_slot}"
                            ),
                            annotations=[
                                go.layout.Annotation(
                                    text=f"Additional Information: <br>The distance from <br>Center of Selected Slot to <br>Center of GT Slot is <br>{round(distance, 4)}m.",
                                    align="left",
                                    showarrow=False,
                                    xref="paper",
                                    yref="paper",
                                    x=1.15,
                                    y=0,
                                    bordercolor="black",
                                    borderwidth=1,
                                )
                            ],
                        )

                        # Find intersection and update figure
                        coordinates_gt = [(point["x"], point["y"]) for point in data["parking_box_gt"]]
                        coordinates_signal = [(point["x"], point["y"]) for point in data["parking_box_signal"]]
                        fig_gt = intersection_fig(
                            coordinates_gt,
                            coordinates_signal,
                            data["overlap_percentage"],
                            SlotOffer.Thresholds.THRESHOLD_OVERLAP,
                            fig_gt,
                        )

                        plots.append(fig_gt)
                        fig_gt.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            fig1 = go.Figure()
            fig1.add_trace(
                go.Scatter(
                    x=time.tolist(),
                    y=filtered_df[Signals.Columns.sg_num_valid_parking_boxes].values.tolist(),
                    mode="lines",
                    name=f"{signal_name[Signals.Columns.sg_num_valid_parking_boxes]}",
                    yaxis="y",
                    showlegend=True,
                )
            )

            fig1.add_trace(
                go.Scatter(
                    x=time.tolist(),
                    y=filtered_df[Signals.Columns.sg_parksm_core_status_state].values.tolist(),
                    mode="lines",
                    name=f"{signal_name[Signals.Columns.sg_parksm_core_status_state]}",
                    yaxis="y",
                    showlegend=True,
                )
            )
            fig1.add_trace(
                go.Scatter(
                    x=time.tolist(),
                    y=filtered_df[Signals.Columns.sg_velocity].values.tolist(),
                    mode="lines",
                    name=f"{signal_name[Signals.Columns.sg_velocity]}",
                    yaxis="y",
                    showlegend=True,
                )
            )
            fig1.add_trace(
                go.Scatter(
                    x=time.tolist(),
                    y=filtered_df[Signals.Columns.sg_selection_status].values.tolist(),
                    mode="lines",
                    name=f"{signal_name[Signals.Columns.sg_selection_status]}",
                    yaxis="y",
                    showlegend=True,
                )
            )

            fig1.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]")
            fig1.update_layout(
                constants.PlotlyTemplate.lgt_tmplt,
                title_text="Graphical overview for multiple SlotOffer related signals",
            )

            plots.append(fig1)
            remarks.append("")

            additional_results_dict = {
                "Verdict": {"value": self.test_result.title(), "color": fh.get_color(self.test_result)},
                "TestStep": {
                    "value": collinear_timestamp,
                    "color": fh.get_color(self.test_result),
                },
            }

            for plot in plots:
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)

            self.result.details["Additional_results"] = additional_results_dict
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=1,
    name="Next to parking box",
    description="The overlap percentage should be calculated when the mirrors of the car are reaching the front of \
                    the designated parking area (0.5 meters beyond the initial line of the targeted slot).",
    expected_result=f"> {SlotOffer.Thresholds.THRESHOLD_TPR} %",
)
@register_signals(EXAMPLE, Signals)
@register_pre_processor(alias="AUP_slot_offer", pre_processor=Preprocessor)
class NextToPBStep(GenericTestStep):
    """0.5 meters beyond first line"""

    def process(self, **kwargs):
        """
        The function `process` sets the variable `collinear_timestamp` to "NextTo" and then calls the `process` method of
        the parent class with this value.
        """
        collinear_timestamp = "NextTo"
        super().process(collinear_timestamp)


@teststep_definition(
    step_number=2,
    name="Fully passed the parking box",
    description="The overlap percentage should be calculated as the rear of the car approaches the point where it has \
                    completely passed the parking slot.",
    expected_result=f"> {SlotOffer.Thresholds.THRESHOLD_TPR} %",
)
@register_signals(EXAMPLE, Signals)
@register_pre_processor(alias="AUP_slot_offer", pre_processor=Preprocessor)
class AfterPBStep(GenericTestStep):
    """After PB"""

    def process(self, **kwargs):
        """
        The function `process` sets the variable `collinear_timestamp` to "After" and then calls the `process` method of the
        parent class with this variable as an argument.
        """
        collinear_timestamp = "After"
        super().process(collinear_timestamp)


@verifies("966639")
@testcase_definition(
    name="Slot Offer for AUP - TP TestCase",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_PfAN_8lcEe2iKqc0KPO99Q&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_lWHOEPvsEeqIqKySVwTVNQ%2Fcomponents%2F_u4eQYMlKEe2iKqc0KPO99Q&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
    description=f"The True Positive Slot Offer Rate evaluates the frequency with which a specific scanned parking \
                    slot is correctly identified as a true positive by the AP function. The pass rate is determined \
                    for each test step using the following formula: \
                    <b>TPR</b> = (Number of measurements where a slot was offered with an overlap > \
                    {SlotOffer.Thresholds.THRESHOLD_OVERLAP}) / (Total number of measurements)",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SelectedOfferedSlot(TestCase):
    """TP SlotOffer test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            NextToPBStep,
            AfterPBStep,
        ]
