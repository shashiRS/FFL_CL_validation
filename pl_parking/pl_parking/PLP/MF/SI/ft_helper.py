"""Helper functions for the feature tests."""

import math

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from shapely.geometry import Polygon

from pl_parking.common_ft_helper import SISignals
from pl_parking.PLP.MF.constants import ConstantsSI, ConstantsTrajpla


def perpendicular_distance_to_line(point, line_points):
    """
    Calculate the perpendicular distance between a point and a line defined by two points.

    Args:
        point: A tuple (x0, y0) representing the point.
        line_points: A tuple of two points ((x1, y1), (x2, y2)) defining the line.

    Returns:
        The perpendicular distance between the point and the line.
    """
    x0, y0 = point
    x1, y1, x2, y2 = line_points

    # Calculate coefficients A, B, C for the line equation
    A = y2 - y1
    B = x1 - x2
    C = x2 * y1 - x1 * y2

    # Calculate the perpendicular distance
    numerator = abs(A * x0 + B * y0 + C)
    denominator = math.sqrt(A**2 + B**2)
    return numerator / denominator


def get_parking_scenario_from_name(file_name):
    """Get the parking scenario from the file name."""
    if "par" in file_name.lower():
        return "parallel"
    elif "perp" in file_name.lower():
        return "perpendicular"
    elif "ang" in file_name.lower():
        return "angular"


def calclate_euclidian_dist_between_points(point1, point2):
    """
    Calculate the Euclidean distance between two points in 2D space.

    :param point1: Tuple (x1, y1) - coordinates of the first point
    :param point2: Tuple (x2, y2) - coordinates of the second point
    :return: Distance between the two points
    """
    x1, y1 = point1
    x2, y2 = point2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def intersection_fig_trace_method(delim_coords, slot_coords):
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
    try:
        # Converting JSON and signal coordinates into polygons for geometric operations.
        delim_polygon = Polygon(delim_coords)
        slot_polygon = Polygon(slot_coords)
    except ValueError as e:
        raise ValueError(f"Invalid polygon coordinates. Reason: {e}") from e
    if not delim_polygon.is_valid:
        # print("Delimiter polygon is invalid!")
        delim_polygon = delim_polygon.buffer(0)
    if not slot_polygon.is_valid:
        # print("Slot polygon is invalid!")
        slot_polygon = slot_polygon.buffer(0)
    if delim_coords[0] != delim_coords[-1]:
        delim_coords.append(delim_coords[0])

    if slot_coords[0] != slot_coords[-1]:
        slot_coords.append(slot_coords[0])
    delim_polygon = delim_polygon.simplify(0.001)
    slot_polygon = slot_polygon.simplify(0.001)

    # Calculating the intersection between signal_polygon and json_polygon.
    intersection = slot_polygon.intersection(delim_polygon)
    intersection_coords = list(intersection.exterior.coords)

    if not intersection.is_empty:
        intersection_coords = [
            tuple(point[0] for point in intersection_coords),
            tuple(point[1] for point in intersection_coords),
        ]
    return intersection_coords


def calculate_overlap(delim_coords, slot_coords):
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
        delim_polygon = Polygon(delim_coords)
        slot_polygon = Polygon(slot_coords)
    except ValueError as e:
        raise ValueError(f"Invalid polygon coordinates. Reason: {e}") from e
    if not delim_polygon.is_valid:
        # print("Delimiter polygon is invalid!")
        delim_polygon = delim_polygon.buffer(0)
    if not slot_polygon.is_valid:
        # print("Slot polygon is invalid!")
        slot_polygon = slot_polygon.buffer(0)
    if delim_coords[0] != delim_coords[-1]:
        delim_coords.append(delim_coords[0])

    if slot_coords[0] != slot_coords[-1]:
        slot_coords.append(slot_coords[0])
    delim_polygon = delim_polygon.simplify(0.001)
    slot_polygon = slot_polygon.simplify(0.001)
    # Calculating the intersection between signal_polygon and json_polygon.
    intersection = slot_polygon.intersection(delim_polygon)

    # Calculate overlap percentage
    overlap_percentage = 0.0
    if not intersection.is_empty:
        intersection_area = intersection.area
        json_polygon_area = delim_polygon.area
        signal_polygon_area = slot_polygon.area

        relative_overlap_parking_box_1 = intersection_area / json_polygon_area
        relative_overlap_parking_box_2 = intersection_area / signal_polygon_area
        overlap_percentage = max(relative_overlap_parking_box_1, relative_overlap_parking_box_2) * 100
    return intersection, overlap_percentage


def calculate_overlap_for_two_obj(delim_coords, slot_coords):
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
        delim_polygon = Polygon(delim_coords)
        slot_polygon = Polygon(slot_coords)
    except ValueError as e:
        raise ValueError(f"Invalid polygon coordinates. Reason: {e}") from e
    if not delim_polygon.is_valid:
        # print("Delimiter polygon is invalid!")
        delim_polygon = delim_polygon.buffer(0)
    if not slot_polygon.is_valid:
        # print("Slot polygon is invalid!")
        slot_polygon = slot_polygon.buffer(0)

    delim_polygon = delim_polygon.simplify(0.001)
    slot_polygon = slot_polygon.simplify(0.001)
    # Calculating the intersection between signal_polygon and json_polygon.
    intersection = slot_polygon.intersection(delim_polygon)

    # Calculate overlap percentage
    overlap_percentage = 0.0
    if not intersection.is_empty:
        intersection_area = intersection.area
        json_polygon_area = delim_polygon.area
        signal_polygon_area = slot_polygon.area

        relative_overlap_parking_box_1 = intersection_area / json_polygon_area
        relative_overlap_parking_box_2 = intersection_area / signal_polygon_area
        overlap_percentage = max(relative_overlap_parking_box_1, relative_overlap_parking_box_2) * 100
    return intersection, overlap_percentage


def calculate_width_angular(a, parallel_tolerance=0.1):
    """
    Calculate the perpendicular distance between two lines defined by points.
    This function calculates the perpendicular distance between two lines defined by
    the coordinates of four points (x1, y1), (x2, y2), (x3, y3), and (x4, y4). The
    lines are considered parallel if the absolute value of the determinant of their
    direction vectors is less than the specified parallel tolerance.
    Args:
        a (tuple): A tuple containing the coordinates of four points (x1, y1, x2, y2, x3, y3, x4, y4).
        parallel_tolerance (float, optional): The tolerance to determine if the lines are parallel.
                                              Defaults to 0.1.
    Returns:
        float: The perpendicular distance between the two lines if they are not parallel,
               otherwise returns 0.
    """
    x1, y1, x2, y2, x3, y3, x4, y4 = a
    # dx1, dy1 = x2 - x1, y2 - y1
    # dx2, dy2 = x4 - x3, y4 - y3
    # if abs(dx1 * dy2 - dy1 * dx2):  # < parallel_tolerance:
    #     dist = abs((y4 - y3) * x1 - (x4 - x3) * y1 + x4 * y3 - y4 * x3) / math.sqrt((y4 - y3) ** 2 + (x4 - x3) ** 2)
    #     return dist
    # else:
    #     return 0

    return abs((y4 - y3) * x1 - (x4 - x3) * y1 + x4 * y3 - y4 * x3) / math.sqrt((y4 - y3) ** 2 + (x4 - x3) ** 2)


def convert_to_tuples(coord_list):
    """COnvert to tuple"""
    return [(coord_list[i], coord_list[i + 1]) for i in range(0, len(coord_list), 2)]


obj_shape = ["staticObject_{}_objShape_m.array_x_dir_{}", "staticObject_{}_objShape_m.array_y_dir_{}"]
combined_list = [
    "pb_slotCoordinates_FrontLeftx_0",
    "pb_slotCoordinates_FrontLefty_0",
    "pb_slotCoordinates_FrontRightx_0",
    "pb_slotCoordinates_FrontRighty_0",
    "pb_slotCoordinates_RearLeftx_0",
    "pb_slotCoordinates_RearLefty_0",
    "pb_slotCoordinates_RearRightx_0",
    "pb_slotCoordinates_RearRighty_0",
]
combined_list_for_all_pb = [
    "pb_slotCoordinates_FrontLeftx_{}",
    "pb_slotCoordinates_FrontLefty_{}",
    "pb_slotCoordinates_FrontRightx_{}",
    "pb_slotCoordinates_FrontRighty_{}",
    "pb_slotCoordinates_RearLeftx_{}",
    "pb_slotCoordinates_RearLefty_{}",
    "pb_slotCoordinates_RearRightx_{}",
    "pb_slotCoordinates_RearRighty_{}",
]
delimiter_list = [
    "delimiters_startPointXPosition_{}",
    "delimiters_startPointYPosition_{}",
    "delimiters_endPointXPosition_{}",
    "delimiters_endPointYPosition_{}",
]
gt_delimiter_list = [
    "GT_DelimiterX_0",
    "GT_DelimiterY_0",
    "GT_DelimiterX_1",
    "GT_DelimiterY_1",
]
gt_delimiter_length = [
    "spaceMarkings_{}.array_x_0",
    "spaceMarkings_{}.array_y_0",
    "spaceMarkings_{}.array_x_1",
    "spaceMarkings_{}.array_y_1",
]
combine_list_static_object = [
    "staticObject_0_objShape_m",
    "staticObject_1_objShape_m",
]
combine_list_mODSlots_CNN_list = [
    "mODSlots.slot_corners._0_.x",
    "mODSlots.slot_corners._0_.y",
    "mODSlots.slot_corners._1_.x",
    "mODSlots.slot_corners._1_.y",
    "mODSlots.slot_corners._2_.x",
    "mODSlots.slot_corners._2_.y",
    "mODSlots.slot_corners._3_.x",
    "mODSlots.slot_corners._3_.y",
]

combine_list_cnnBasedParkingSpaces_parkingSlots_slotCorners = [
    "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_0.x",
    "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_0.y",
    "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_1.x",
    "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_1.y",
    "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_2.x",
    "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_2.y",
    "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_3.x",
    "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_3.y",
]


def find_third_point(a, b):
    """
    Calculate the third point of a right-angled triangle.

    :param a: Tuple of coordinates (x1, y1) of the top vertex
    :param b: Tuple of coordinates (x2, y2) of the 90-degree vertex
    :return: Tuple of coordinates (x3, y3) of the third vertex
    """
    x1, y1 = a
    x2, y2 = b

    # Horizontal and vertical distances
    dx = x2 - x1
    dy = y2 - y1

    # Third point options
    c1 = (x2 - dy, y2 + dx)
    c2 = (x2 + dy, y2 - dx)

    return c1, c2  # Return both options (above or below)


def x_at_y(x1, y1, x2, y2, y):
    """Calculate the x-coordinate on a line at a given y-value."""
    if y2 - y1 == 0:  # Handle horizontal line
        return x1
    return x1 + (y - y1) / (y2 - y1) * (x2 - x1)


def process_from_two_objects_with_delimiter_between(df: pd.DataFrame, parking_type):
    """Process object shapes"""
    pb_list = [
        "pb_slotCoordinates_FrontLeftx_{}",
        "pb_slotCoordinates_FrontLefty_{}",
        "pb_slotCoordinates_RearLeftx_{}",
        "pb_slotCoordinates_RearLefty_{}",
        "pb_slotCoordinates_RearRightx_{}",
        "pb_slotCoordinates_RearRighty_{}",
        "pb_slotCoordinates_FrontRightx_{}",
        "pb_slotCoordinates_FrontRighty_{}",
        "pb_slotCoordinates_FrontLeftx_{}",
        "pb_slotCoordinates_FrontLefty_{}",
    ]
    # Combine all coordinates into a single list for each parking box

    df["Parking Box 0"] = df[[x.format(0) for x in pb_list]].apply(lambda row: row.values.tolist(), axis=1)

    ap_state_mask = (df[SISignals.Columns.AP_STATE] == ConstantsTrajpla.AP_SCAN_IN) | (
        df[SISignals.Columns.AP_STATE] == ConstantsTrajpla.AP_AVG_ACTIVE_IN
    )
    pb_mask = df["Parking Box 0"].apply(lambda lst: any(x != 0 for x in lst))
    pb_signal = df["Parking Box 0"][ap_state_mask & pb_mask]
    timestamp_to_verify = pb_signal.index[0]

    max_obj_0_array = int(max(df[SISignals.Columns.STATICOBJECT_ACTUALSIZE_0]))
    max_obj_1_array = int(max(df[SISignals.Columns.STATICOBJECT_ACTUALSIZE_1]))
    marker_single_df = pd.DataFrame()

    ap_time = df[SISignals.Columns.TIME]
    # marker = [x.format(0) for x in gt_delimiter_list]
    # marker += [x.format(1) for x in gt_delimiter_list]
    marker_single_df[SISignals.Columns.DELIMITERS_COORDINATES_LIST.format(0)] = df[gt_delimiter_list].apply(
        lambda row: row.values.tolist(), axis=1
    )
    # ego_x = df[SISignals.Columns.ODOESTIMATION_XPOSITION_M]
    # ego_y = df[SISignals.Columns.ODOESTIMATION_YPOSITION_M]
    # ego_yaw = df[SISignals.Columns.ODOESTIMATION_YANGLE]
    # ego_vehicle = df[[SISignals.Columns.ODOESTIMATION_XPOSITION_M, SISignals.Columns.ODOESTIMATION_YPOSITION_M,
    #                   SISignals.Columns.ODOESTIMATION_YANGLE]]
    ego_x = df[SISignals.Columns.EGO_POS_X]
    ego_y = df[SISignals.Columns.EGO_POS_Y]
    ego_yaw = df[SISignals.Columns.EGO_POS_YAW]
    ego_vehicle = df[[SISignals.Columns.EGO_POS_X, SISignals.Columns.EGO_POS_Y, SISignals.Columns.EGO_POS_YAW]]
    # Apply the function by pairing seriesA with corresponding rows in seriesB
    marker_single_df[SISignals.Columns.DELIMITERS_COORDINATES_LIST.format(0)] = marker_single_df[
        SISignals.Columns.DELIMITERS_COORDINATES_LIST.format(0)
    ].combine(
        ego_vehicle.apply(tuple, axis=1),
        lambda coord, ego_data: transform_odo(coord, ego_data[0], ego_data[1], ego_data[2]),
    )

    # Create a list of columns for each object shape
    obj_0_list = [x.format(0, i) for i in range(max_obj_0_array) for x in obj_shape]
    obj_1_list = [x.format(1, i) for i in range(max_obj_1_array) for x in obj_shape]

    # Create columns containing all the coordinates for each object shape
    df["objshape_0_coords"] = df[obj_0_list].apply(lambda row: row.values.tolist(), axis=1)

    df["objshape_1_coords"] = df[obj_1_list].apply(lambda row: row.values.tolist(), axis=1)

    df["objshape_0_coords"] = df["objshape_0_coords"].combine(
        ego_vehicle.apply(tuple, axis=1),
        lambda coord, ego_data: transform_odo_obj_shape(coord, ego_data[0], ego_data[1], ego_data[2]),
    )
    df["objshape_1_coords"] = df["objshape_1_coords"].combine(
        ego_vehicle.apply(tuple, axis=1),
        lambda coord, ego_data: transform_odo_obj_shape(coord, ego_data[0], ego_data[1], ego_data[2]),
    )
    # Separate x and y values for plotting
    collected_info = {
        ts: {
            "ts": round(ap_time.loc[ts], 2),
            "verdict": None,
            "obj_1": None,
            "fail_reason": None,
            "ego_vehicle": [(ego_x.loc[ts], ego_y.loc[ts], ego_yaw.loc[ts])],
            "obj_2": None,
            "delimiter": None,
            "pb": None,
        }
        for ts in pb_signal.index
    }
    pb_slot = pb_signal.loc[timestamp_to_verify]

    if not pb_signal.empty:
        for idx in pb_signal.index:
            pb_slot = pb_signal.loc[idx]
            coords1 = df["objshape_0_coords"].loc[idx]
            coords1.append(coords1[0])
            coords1.append(coords1[1])
            delimiter = marker_single_df[SISignals.Columns.DELIMITERS_COORDINATES_LIST.format(0)].loc[idx]

            x1, y1 = coords1[::2], coords1[1::2]  # column1

            coords2 = df["objshape_1_coords"].loc[idx]
            coords2.append(coords2[0])
            coords2.append(coords2[1])
            x2, y2 = coords2[::2], coords2[1::2]  # column2

            if max(x1) > max(x2):
                x1, y1, x2, y2 = x2, y2, x1, y1
            index_of_max_x1 = x1.index(max(x1))
            index_of_max_x2 = x2.index(min(x2))

            # dist_to_left = calclate_euclidian_dist_between_points([delimiter[0], delimiter[1]],[max(x1),y1[index_of_max_x1]])
            # dist_to_right = calclate_euclidian_dist_between_points([delimiter[0], delimiter[1]],[min(x2),y2[index_of_max_x2]])
            # # Define the line as two endpoints
            # line = LineString([(delimiter[:2]), (delimiter[2:])])
            # if parking_type == "angular":
            dist_to_left = perpendicular_distance_to_line([max(x1), y1[index_of_max_x1]], delimiter)
            dist_to_right = perpendicular_distance_to_line([min(x2), y2[index_of_max_x2]], delimiter)

            if parking_type == "parallel":
                threshold = ConstantsSI.MIN_LEN_PARALLEL
            else:
                threshold = ConstantsSI.MIN_WDTH_PERP
            if dist_to_left >= threshold:
                verdict = False
                dist_list = []
                for i in range(2):
                    dist_list.append(
                        calclate_euclidian_dist_between_points(
                            [delimiter[i], delimiter[i + 1]], [pb_slot[4], pb_slot[5]]
                        )
                    )
                    dist_list.append(
                        calclate_euclidian_dist_between_points(
                            [delimiter[i], delimiter[i + 1]], [pb_slot[6], pb_slot[7]]
                        )
                    )
                if min(dist_list) <= 1:
                    verdict = True
                collected_info[idx][
                    "fail_reason"
                ] = f"There was sufficient space for a parking box the left side of the delimiter({dist_to_left} m)."
            elif dist_to_right >= threshold:
                verdict = False
                dist_list = []
                for i in range(2):
                    dist_list.append(
                        calclate_euclidian_dist_between_points(
                            [delimiter[i], delimiter[i + 1]], [pb_slot[0], pb_slot[1]]
                        )
                    )
                    dist_list.append(
                        calclate_euclidian_dist_between_points(
                            [delimiter[i], delimiter[i + 1]], [pb_slot[2], pb_slot[3]]
                        )
                    )
                if min(dist_list) <= 1:
                    verdict = True
                collected_info[idx][
                    "fail_reason"
                ] = f"There was sufficient space for a parking box the right side of the delimiter({dist_to_right} m)."
            else:
                collected_info[idx]["fail_reason"] = "Parking box is positioned correctly."
                verdict = True

            collected_info[idx]["pb"] = pb_slot
            collected_info[idx]["delimiter"] = delimiter
            collected_info[idx]["obj_1"] = (x1, y1)
            collected_info[idx]["obj_2"] = (x2, y2)
            collected_info[idx]["verdict"] = verdict
            # _, overlap_perc = calculate_overlap(
            #     [(x, y) for x, y in zip(pb_slot[::2], pb_slot[1::2])], [(x, y) for x, y in zip(x1, y1)]
            # )
            # if overlap_perc:
            #     collected_info[idx]["fail_reason"] = "Parking box is overlapping with the object on the left."
            # _, overlap_perc = calculate_overlap(
            #     [(x, y) for x, y in zip(pb_slot[::2], pb_slot[1::2])], [(x, y) for x, y in zip(x2, y2)]
            # )
            # if overlap_perc:
            #     if collected_info[idx]["fail_reason"] is None:
            #         collected_info[idx]["fail_reason"] = "Parking box is overlapping with the object on the right."
            #     else:
            #         collected_info[idx][
            #             "fail_reason"
            #         ] += " Parking box is also overlapping with the object on the right."
            # if collected_info[idx]["fail_reason"] is not None:
            #     collected_info[idx]["verdict"] = False
    else:
        idx = df.index[-1]
        pb_slot = [None] * 8
        coords1 = df["objshape_0_coords"].loc[idx]
        coords1.append(coords1[0])
        coords1.append(coords1[1])
        delimiter = marker_single_df[SISignals.Columns.DELIMITERS_COORDINATES_LIST.format(0)].loc[idx]
        x1, y1 = coords1[::2], coords1[1::2]  # column1

        coords2 = df["objshape_1_coords"].loc[idx]
        coords2.append(coords2[0])
        coords2.append(coords2[1])
        x2, y2 = coords2[::2], coords2[1::2]  # column2
        collected_info[idx]["pb"] = pb_slot
        collected_info[idx]["delimiter"] = delimiter
        collected_info[idx]["obj_1"] = (x1, y1)
        collected_info[idx]["obj_2"] = (x2, y2)
        collected_info[idx]["verdict"] = False

    return collected_info


def process_from_one_object_and_delimiter(df: pd.DataFrame):
    """Process object shapes"""
    THRESHOLD_TOLERANCE = 0.001

    pb_list = [
        "pb_slotCoordinates_FrontLeftx_{}",
        "pb_slotCoordinates_FrontLefty_{}",
        "pb_slotCoordinates_RearLeftx_{}",
        "pb_slotCoordinates_RearLefty_{}",
        "pb_slotCoordinates_RearRightx_{}",
        "pb_slotCoordinates_RearRighty_{}",
        "pb_slotCoordinates_FrontRightx_{}",
        "pb_slotCoordinates_FrontRighty_{}",
        "pb_slotCoordinates_FrontLeftx_{}",
        "pb_slotCoordinates_FrontLefty_{}",
    ]
    # Combine all coordinates into a single list for each parking box

    df["Parking Box 0"] = df[[x.format(0) for x in pb_list]].apply(lambda row: row.values.tolist(), axis=1)

    ap_state_mask = (df[SISignals.Columns.AP_STATE] == ConstantsTrajpla.AP_SCAN_IN) | (
        df[SISignals.Columns.AP_STATE] == ConstantsTrajpla.AP_AVG_ACTIVE_IN
    )
    pb_mask = df["Parking Box 0"].apply(lambda lst: any(x != 0 for x in lst))
    pb_signal = df["Parking Box 0"][ap_state_mask & pb_mask]
    timestamp_to_verify = pb_signal.index[0]

    max_obj_0_array = int(max(df[SISignals.Columns.STATICOBJECT_ACTUALSIZE_0]))

    marker_single_df = pd.DataFrame()

    ap_time = df[SISignals.Columns.TIME]

    marker_single_df[SISignals.Columns.DELIMITERS_COORDINATES_LIST.format(0)] = df[gt_delimiter_list].apply(
        lambda row: row.values.tolist(), axis=1
    )

    ego_x = df[SISignals.Columns.EGO_POS_X]
    ego_y = df[SISignals.Columns.EGO_POS_Y]
    ego_yaw = df[SISignals.Columns.EGO_POS_YAW]
    ego_vehicle = df[[SISignals.Columns.EGO_POS_X, SISignals.Columns.EGO_POS_Y, SISignals.Columns.EGO_POS_YAW]]
    # Apply the function by pairing seriesA with corresponding rows in seriesB
    marker_single_df[SISignals.Columns.DELIMITERS_COORDINATES_LIST.format(0)] = marker_single_df[
        SISignals.Columns.DELIMITERS_COORDINATES_LIST.format(0)
    ].combine(
        ego_vehicle.apply(tuple, axis=1),
        lambda coord, ego_data: transform_odo(coord, ego_data[0], ego_data[1], ego_data[2]),
    )

    # Create a list of columns for each object shape
    obj_0_list = [x.format(0, i) for i in range(max_obj_0_array) for x in obj_shape]
    # obj_1_list = [x.format(1, i) for i in range(max_obj_1_array) for x in obj_shape]

    # Create columns containing all the coordinates for each object shape
    df["objshape_0_coords"] = df[obj_0_list].apply(lambda row: row.values.tolist(), axis=1)

    # df["objshape_1_coords"] = df[obj_1_list].apply(lambda row: row.values.tolist(), axis=1)

    df["objshape_0_coords"] = df["objshape_0_coords"].combine(
        ego_vehicle.apply(tuple, axis=1),
        lambda coord, ego_data: transform_odo_obj_shape(coord, ego_data[0], ego_data[1], ego_data[2]),
    )

    # Separate x and y values for plotting
    collected_info = {
        ts: {
            "ts": round(ap_time.loc[ts], 2),
            "verdict": None,
            "obj_1": None,
            "fail_reason": None,
            "ego_vehicle": [(ego_x.loc[ts], ego_y.loc[ts], ego_yaw.loc[ts])],
            "obj_2": None,
            "misalignment_dist": None,
            "misalignment": (None, None) * 2,
            "delimiter": None,
            "pb": None,
        }
        for ts in pb_signal.index
    }
    pb_slot = pb_signal.loc[timestamp_to_verify]

    if not pb_signal.empty:
        for idx in pb_signal.index:
            pb_slot = pb_signal.loc[idx]
            coords1 = df["objshape_0_coords"].loc[idx]
            coords1.append(coords1[0])
            coords1.append(coords1[1])
            delimiter = marker_single_df[SISignals.Columns.DELIMITERS_COORDINATES_LIST.format(0)].loc[idx]

            x1, y1 = coords1[::2], coords1[1::2]  # column1
            # For testing purposes
            # pass criteria
            # pb_slot[1] = delimiter[1]
            # pb_slot[3] = delimiter[1]
            # pb_slot[9] = delimiter[1]
            # End point of a delimiter
            end_point_delim = (delimiter[0], delimiter[1])
            # Point of the opening of the parking slot

            opening_point = (pb_slot[2], pb_slot[3])

            alignment_distance = abs(opening_point[1] - end_point_delim[1])
            if alignment_distance <= THRESHOLD_TOLERANCE:
                collected_info[idx]["verdict"] = True
            else:
                collected_info[idx]["verdict"] = False
                misalign_x = [opening_point[0], pb_slot[2], pb_slot[2], opening_point[0], opening_point[0]]
                misalign_y = [opening_point[1], pb_slot[3], delimiter[1], delimiter[1], opening_point[1]]
                collected_info[idx]["misalignment"] = (misalign_x, misalign_y)
                collected_info[idx]["misalignment_dist"] = round(alignment_distance, 3)

                collected_info[idx][
                    "fail_reason"
                ] = f"The roadside extension of the PB was not alligned with the delimiter edge.Misalignment distance is {round(alignment_distance,3)} m."

            collected_info[idx]["pb"] = pb_slot
            collected_info[idx]["delimiter"] = delimiter
            collected_info[idx]["obj_1"] = (x1, y1)

    else:
        idx = df.index[-1]
        pb_slot = [None] * 8
        coords1 = df["objshape_0_coords"].loc[idx]
        coords1.append(coords1[0])
        coords1.append(coords1[1])
        delimiter = marker_single_df[SISignals.Columns.DELIMITERS_COORDINATES_LIST.format(0)].loc[idx]
        collected_info[idx]["fail_reason"] = "No parking box detected."
        x1, y1 = coords1[::2], coords1[1::2]  # column1
        collected_info[idx]["pb"] = pb_slot
        collected_info[idx]["delimiter"] = delimiter
        collected_info[idx]["obj_1"] = (x1, y1)
        collected_info[idx]["verdict"] = False

    return collected_info


# Check if the centroid of polygon1 is between the centroids of polygon2 and polygon3
def centroid_is_between(point, point1, point2):
    """Check if a point lies between two other points (inclusive)."""
    return point.x < point1.x < point2.x or point2.x < point1.x < point.x


def process_from_two_objects(df: pd.DataFrame):
    """Process object shapes"""
    try:
        pb_list = [
            "pb_slotCoordinates_FrontLeftx_{}",
            "pb_slotCoordinates_FrontLefty_{}",
            "pb_slotCoordinates_RearLeftx_{}",
            "pb_slotCoordinates_RearLefty_{}",
            "pb_slotCoordinates_RearRightx_{}",
            "pb_slotCoordinates_RearRighty_{}",
            "pb_slotCoordinates_FrontRightx_{}",
            "pb_slotCoordinates_FrontRighty_{}",
            "pb_slotCoordinates_FrontLeftx_{}",
            "pb_slotCoordinates_FrontLefty_{}",
        ]
        # Combine all coordinates into a single list for each parking box
        ego_x = df[SISignals.Columns.EGO_POS_X]
        ego_y = df[SISignals.Columns.EGO_POS_Y]
        ego_yaw = df[SISignals.Columns.EGO_POS_YAW]
        ap_time = df[SISignals.Columns.TIME]
        collected_info = {
            df.index[0]: {
                "ts": round(ap_time.loc[df.index[0]], 2),
                "verdict": None,
                "obj_1": (None, None),
                "fail_reason": (None, None),
                "ego_vehicle": [(ego_x.loc[df.index[0]], ego_y.loc[df.index[0]], ego_yaw.loc[df.index[0]])],
                "obj_2": (None, None),
                "possible_space": None,
                "is_wide_enough": None,
                "pb": (None, None),
            }
        }
        ego_vehicle = df[[SISignals.Columns.EGO_POS_X, SISignals.Columns.EGO_POS_Y, SISignals.Columns.EGO_POS_YAW]]
        df["Parking Box 0"] = df[[x.format(0) for x in pb_list]].apply(lambda row: row.values.tolist(), axis=1)
        vertical_delimiters = []
        # Create a list of columns for each object shape
        max_obj_0_array = int(max(df[SISignals.Columns.STATICOBJECT_ACTUALSIZE_0]))
        max_obj_1_array = int(max(df[SISignals.Columns.STATICOBJECT_ACTUALSIZE_1]))

        obj_0_list = [x.format(0, i) for i in range(max_obj_0_array) for x in obj_shape]
        obj_1_list = [x.format(1, i) for i in range(max_obj_1_array) for x in obj_shape]

        # Create columns containing all the coordinates for each object shape
        df["objshape_0_coords"] = df[obj_0_list].apply(lambda row: row.values.tolist(), axis=1)
        df["objshape_0_coords"] = df["objshape_0_coords"].combine(
            ego_vehicle.apply(tuple, axis=1),
            lambda coord, ego_data: transform_odo_obj_shape(coord, ego_data[0], ego_data[1], ego_data[2]),
        )

        df["objshape_1_coords"] = df[obj_1_list].apply(lambda row: row.values.tolist(), axis=1)
        df["objshape_1_coords"] = df["objshape_1_coords"].combine(
            ego_vehicle.apply(tuple, axis=1),
            lambda coord, ego_data: transform_odo_obj_shape(coord, ego_data[0], ego_data[1], ego_data[2]),
        )
        # Get the number of vertices for each object shape
        # for idx in df.index:
        idx = df.index[0]
        pb_coords = df["Parking Box 0"].loc[idx]

        # Separate x and y values for plotting
        if max_obj_0_array < max_obj_1_array:
            body_traversable_obj = df["objshape_0_coords"].loc[idx]
            vehicle = df["objshape_1_coords"].loc[idx]
        else:
            body_traversable_obj = df["objshape_1_coords"].loc[idx]
            vehicle = df["objshape_0_coords"].loc[idx]
        # Get coords for 1st timestamp TODO : this is for development only
        coords1 = df["objshape_0_coords"].loc[idx]
        coords1.append(coords1[0])
        coords1.append(coords1[1])
        x1, y1 = coords1[::2], coords1[1::2]  # column1

        coords2 = df["objshape_1_coords"].loc[idx]
        coords2.append(coords2[0])
        coords2.append(coords2[1])
        x2 = coords2[::2]

        y1_abs = [abs(i) for i in y1]
        y1_min_index = y1_abs.index(min(y1_abs))
        y1_max_index = y1_abs.index(max(y1_abs))

        min_y = y1[y1_min_index]
        max_y = y1[y1_max_index]

        x_left = [min(max(x1), max(x2))]
        x_right = [max(min(x1), min(x2))]
        y_left_idx = x1.index(min(x1)) if min(min(x1), min(x2)) == min(x1) else x2.index(min(x2))
        y_right_idx = x1.index(max(x1)) if max(max(x1), max(x2)) == max(x1) else x2.index(max(x2))

        y_left = [y1[y_left_idx]]
        y_right = [y1[y_right_idx]]

        coords1 = np.array(list(zip(x_left, y_left)))
        coords2 = np.array(list(zip(x_right, y_right)))

        # Compute all pairwise distances
        distances = cdist(coords1, coords2)

        # Find the minimum distance and indices
        min_distance = round(distances.min(), 2)

        i, j = np.unravel_index(distances.argmin(), distances.shape)

        detected_space = (
            coords1[i][0],
            min_y,
            coords1[i][0],
            max_y,
            coords2[j][0],
            max_y,
            coords2[j][0],
            min_y,
            coords1[i][0],
            min_y,
        )
        obj_polygon = Polygon(
            [(x, y) for x, y in zip(list(body_traversable_obj[::2]), list(body_traversable_obj[1::2]))]
        )
        pb_polygon = Polygon([(x, y) for x, y in zip(list(pb_coords[::2]), list(pb_coords[1::2]))])
        vehicle_polygon = Polygon([(x, y) for x, y in zip(list(vehicle[::2]), list(vehicle[1::2]))])

        # Calculate the centroids
        centroid_obj_polygon = obj_polygon.centroid
        centroid_pb_polygon = pb_polygon.centroid
        centroid_vehicle_polygon = vehicle_polygon.centroid
        if centroid_is_between(centroid_obj_polygon, centroid_pb_polygon, centroid_vehicle_polygon):
            intersection, overlap_percentage = calculate_overlap_for_two_obj(obj_polygon, pb_polygon)
            if overlap_percentage > 0:
                collected_info[idx]["verdict"] = False
                collected_info[idx]["fail_reason"] = "The object is overlapping with the parking box."
            else:
                collected_info[idx]["verdict"] = True
                collected_info[idx]["fail_reason"] = "The object is not overlapping with the parking box."
        else:
            if min_distance >= ConstantsSI.MIN_LEN_PARALLEL:
                collected_info[idx]["verdict"] = False
                collected_info[idx]["is_wide_enough"] = (False, min_distance)
                collected_info[idx][
                    "fail_reason"
                ] = f"Ego car failed to detect this slot, width of the space: {min_distance} m is bigger than minimum required {ConstantsSI.MIN_LEN_PARALLEL}."
            else:
                collected_info[idx]["verdict"] = True
                collected_info[idx]["is_wide_enough"] = (True, min_distance)
                collected_info[idx][
                    "fail_reason"
                ] = f"Ego car did not detect this slot , because the width of the space is too small: {min_distance} m. Minimum required width is {ConstantsSI.MIN_LEN_PARALLEL} m."
        collected_info[idx]["obj_1"] = body_traversable_obj
        collected_info[idx]["obj_2"] = vehicle
        collected_info[idx]["pb"] = pb_coords
        collected_info[idx]["possible_space"] = detected_space

        return collected_info
    except Exception as err:
        print(str(err))
        import os
        import sys

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")
    return vertical_delimiters


def process_data_three_obj_shapes(df: pd.DataFrame):
    """Process object shapes"""
    try:
        pb_list = [
            "pb_slotCoordinates_FrontLeftx_{}",
            "pb_slotCoordinates_FrontLefty_{}",
            "pb_slotCoordinates_RearLeftx_{}",
            "pb_slotCoordinates_RearLefty_{}",
            "pb_slotCoordinates_RearRightx_{}",
            "pb_slotCoordinates_RearRighty_{}",
            "pb_slotCoordinates_FrontRightx_{}",
            "pb_slotCoordinates_FrontRighty_{}",
            "pb_slotCoordinates_FrontLeftx_{}",
            "pb_slotCoordinates_FrontLefty_{}",
        ]
        # Combine all coordinates into a single list for each parking box
        ego_x = df[SISignals.Columns.EGO_POS_X]
        ego_y = df[SISignals.Columns.EGO_POS_Y]
        ego_yaw = df[SISignals.Columns.EGO_POS_YAW]
        ap_time = df[SISignals.Columns.TIME]
        num_valid_pb_series = df[SISignals.Columns.NUMVALIDPARKINGBOXES_NU] == 2
        verdict = False
        if any(num_valid_pb_series):
            verdict = True
            ts = df[num_valid_pb_series].index[0]
            fail_reason = "Both parking boxes detected."
        elif any(df[SISignals.Columns.NUMVALIDPARKINGBOXES_NU] == 1):
            fail_reason = "Only one parking box detected."
            num_valid_pb_series = df[df[SISignals.Columns.NUMVALIDPARKINGBOXES_NU] == 1]
            ts = df[num_valid_pb_series].index[0]
        else:
            fail_reason = "No parking box detected."
            ts = df.index[0]
        collected_info = {
            ts: {
                "ts": round(ap_time.loc[ts], 2),
                "verdict": verdict,
                "obj_1": (None, None),
                "obj_0": (None, None),
                "fail_reason": fail_reason,
                "ego_vehicle": [(ego_x.loc[ts], ego_y.loc[ts], ego_yaw.loc[ts])],
                "obj_2": (None, None),
                "possible_space": None,
                "is_wide_enough": None,
                "pb_0": (None, None),
                "pb_1": (None, None),
            }
        }
        ego_vehicle = df[[SISignals.Columns.EGO_POS_X, SISignals.Columns.EGO_POS_Y, SISignals.Columns.EGO_POS_YAW]]
        df["Parking Box 0"] = df[[x.format(0) for x in pb_list]].apply(lambda row: row.values.tolist(), axis=1)
        df["Parking Box 1"] = df[[x.format(1) for x in pb_list]].apply(lambda row: row.values.tolist(), axis=1)

        vertical_delimiters = []
        # Create a list of columns for each object shape

        obj_0_list = [x.format(0, i) for i in range(4) for x in obj_shape]
        obj_1_list = [x.format(1, i) for i in range(4) for x in obj_shape]
        obj_2_list = [x.format(2, i) for i in range(4) for x in obj_shape]

        # Create columns containing all the coordinates for each object shape
        df["objshape_0_coords"] = df[obj_0_list].apply(lambda row: row.values.tolist(), axis=1)
        df["objshape_0_coords"] = df["objshape_0_coords"].combine(
            ego_vehicle.apply(tuple, axis=1),
            lambda coord, ego_data: transform_odo_obj_shape(coord, ego_data[0], ego_data[1], ego_data[2]),
        )

        df["objshape_1_coords"] = df[obj_1_list].apply(lambda row: row.values.tolist(), axis=1)
        df["objshape_1_coords"] = df["objshape_1_coords"].combine(
            ego_vehicle.apply(tuple, axis=1),
            lambda coord, ego_data: transform_odo_obj_shape(coord, ego_data[0], ego_data[1], ego_data[2]),
        )
        df["objshape_2_coords"] = df[obj_2_list].apply(lambda row: row.values.tolist(), axis=1)
        df["objshape_2_coords"] = df["objshape_2_coords"].combine(
            ego_vehicle.apply(tuple, axis=1),
            lambda coord, ego_data: transform_odo_obj_shape(coord, ego_data[0], ego_data[1], ego_data[2]),
        )
        # Get the number of vertices for each object shape
        # for idx in df.index:

        pb_coords = df["Parking Box 0"].loc[ts]
        pb_coords1 = df["Parking Box 1"].loc[ts]

        # Separate x and y values for plotting
        body_traversable_obj_0 = df["objshape_0_coords"].loc[ts]
        body_traversable_obj_1 = df["objshape_1_coords"].loc[ts]
        body_traversable_obj_2 = df["objshape_2_coords"].loc[ts]

        collected_info[ts]["obj_0"] = body_traversable_obj_0
        collected_info[ts]["obj_1"] = body_traversable_obj_1
        collected_info[ts]["obj_2"] = body_traversable_obj_2
        collected_info[ts]["pb_0"] = pb_coords
        collected_info[ts]["pb_1"] = pb_coords1

        return collected_info
    except Exception as err:
        print(str(err))
        import os
        import sys

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")
    return vertical_delimiters


###### method to calculate distance from quadrilateral points
def distance(point1, point2):
    """Calculate the distance between two points."""
    return math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)


def quadrilateral_distances(vertices):
    """Calculate distances between the vertices of a quadrilateral."""
    if len(vertices) != 4:
        raise ValueError("There must be exactly four vertices.")

    dists = {
        "AB": distance(vertices[0], vertices[1]),
        "BC": distance(vertices[1], vertices[2]),
        "CD": distance(vertices[2], vertices[3]),
        "DA": distance(vertices[3], vertices[0]),
        "AC": distance(vertices[0], vertices[2]),
        "BD": distance(vertices[1], vertices[3]),
    }

    return dists


def calculate_orientation(parking_box_coords):
    """
    Calculate the orientation of a rectangular parking box.
    The orientation is derived from one of the sides (first two points).

    parking_box_coords: A list of four (x, y) coordinates representing the corners of the parking box.

    Returns: The orientation angle in degrees, relative to the horizontal axis.
    """
    # Choose the first two points to represent one of the edges of the box
    (x1, y1), (x2, y2) = parking_box_coords[0], parking_box_coords[1]

    # Calculate the angle between the two points relative to the horizontal axis
    angle = np.arctan2(y2 - y1, x2 - x1)

    # Convert the angle to degrees
    angle_degrees = np.degrees(angle)

    # Ensure the angle is positive (0 to 360 degrees)
    if angle_degrees < 0:
        angle_degrees += 360

    return angle_degrees


def is_all_zeros(lst):
    """Check if all zeros"""
    return all(x == 0 for x in lst)


def get_match(side, vertices, vertices_pb, threshold=4):
    """Calculate distances between the vertices of a quadrilateral."""
    if len(vertices) != 4:
        raise ValueError("There must be exactly four vertices.")
    # Extract the points from the lists to match the side
    if side == "AB":
        return get_result(vertices, [vertices_pb[0][0], vertices_pb[0][1], vertices_pb[1][0], vertices_pb[1][1]])
    elif side == "CD":
        return get_result(vertices, [vertices_pb[2][0], vertices_pb[2][1], vertices_pb[3][0], vertices_pb[3][1]])


def get_result(a, b, threshold=4):
    """
    Check if two sets of coordinates are near each other.

    Parameters:
    - a: List[float], first set of coordinates [x1, y1, x2, y2]
    - b: List[float], second set of coordinates [x3, y3, x4, y4]
    - threshold: float, the distance threshold for comparison

    Returns:
    - bool: True if any pair of coordinates is within the threshold distance, False otherwise.
    """
    # Give a default value if all coordinates are 0
    if all(x == 0 for x in a):
        a = [255] * 4
    # Extract points from the lists
    point_a1 = (a[0], a[1])  # (x1, y1)
    point_a2 = (a[2], a[3])  # (x2, y2)
    point_b1 = (b[0], b[1])  # (x3, y3)
    point_b2 = (b[2], b[3])  # (x4, y4)

    # Calculate the distances
    distance_a1_b1 = np.sqrt((point_b1[0] - point_a1[0]) ** 2 + (point_b1[1] - point_a1[1]) ** 2)
    distance_a1_b2 = np.sqrt((point_b2[0] - point_a1[0]) ** 2 + (point_b2[1] - point_a1[1]) ** 2)
    distance_a2_b1 = np.sqrt((point_b1[0] - point_a2[0]) ** 2 + (point_b1[1] - point_a2[1]) ** 2)
    distance_a2_b2 = np.sqrt((point_b2[0] - point_a2[0]) ** 2 + (point_b2[1] - point_a2[1]) ** 2)

    return min(distance_a1_b1, distance_a1_b2, distance_a2_b1, distance_a2_b2)


def get_parking_id(num_pbs):
    """Simple dictionary"""
    a = {
        0: 0,
        1: 0,
        2: 1,
        3: 2,
        4: 3,
        5: 4,
        6: 5,
        7: 6,
        8: 7,
    }
    return a[num_pbs]


def match_delim_to_pb(collected_delims: dict, vertices_pb: list):
    """
    Matches delimiters to the provided vertices and returns the matching result.
    This function takes a dictionary of collected delimiters and a list of vertices,
    and attempts to find the best matching delimiters for the vertices. It ensures
    that the same delimiter does not match both sides.
    Args:
        collected_delims (dict): A dictionary where keys are delimiter identifiers and values are delimiter coordinates.
        vertices_pb (list): A list of vertices to match the delimiters against.
    Returns:
        tuple: A tuple containing:
            - bool: True if a valid match is found, False otherwise.
            - dict: A dictionary with the match result, containing:
                - "id" (str): The identifier of the matched delimiters.
                - "coordinates" (list): A list of coordinates for the matched delimiters.
            - list: The coordinates of the matched delimiters, or None if no match is found.
    """
    check_AB = {}

    for key, val in collected_delims.items():
        check_AB[key] = get_match("AB", val, vertices_pb)
    check_CD = {}
    for key, val in collected_delims.items():
        check_CD[key] = get_match("CD", val, vertices_pb)

    # Check the min distance
    # Make sure it's not the same delimiter that matches with both sides
    min_AB_key = min(check_AB, key=check_AB.get)
    min_CD_key = min(check_CD, key=check_CD.get)
    if min_AB_key != min_CD_key:
        delimiter_coords = collected_delims[min_AB_key] + collected_delims[min_CD_key]
        a = list(zip(collected_delims[min_AB_key][::2], collected_delims[min_AB_key][1::2]))
        b = list(zip(collected_delims[min_CD_key][::2], collected_delims[min_CD_key][1::2]))
        return True, {"id": f"{min_AB_key}_{min_CD_key}", "coordinates": [[a[0], a[1]], [b[0], b[1]]]}, delimiter_coords
    return False, {"id": "255", "coordinates": [[(None, None), (None, None)]] * 2}, None


def match_delim_to_delim(collected_delims: dict, collected_delims_2: dict):
    """Matches delimiters from two dictionaries and returns a list of final matches.
    This function takes two dictionaries of collected delimiters, compares them, and finds unique matches.
    It then creates a list of dictionaries containing the matched delimiter coordinates and their respective IDs.
    Args:
        collected_delims (dict): A dictionary where keys are delimiter IDs and values are lists of delimiter coordinates.
        collected_delims_2 (dict): A second dictionary where keys are delimiter IDs and values are lists of delimiter coordinates.
    Returns:
        list: A list of dictionaries, each containing:
            - "id" (str): A string representing the matched delimiter IDs in the format "key1_key2".
            - "delimiter_coords" (list): A list of combined delimiter coordinates from both dictionaries.
            - "coordinates" (list): A list of lists, each containing tuples of coordinates for the matched delimiters.
    """
    final_matches = []
    check_delims = {}

    for key, val in collected_delims.items():
        for k, v in collected_delims_2.items():
            if key != k:
                check_delims[f"{key}_{k}"] = get_result(val, v)
    # Create a new dictionary with only unique values
    unique_dict = {}
    for key, value in check_delims.items():
        if value not in unique_dict.values():
            unique_dict[key] = value

    # # Check the min distance
    # # Make sure it's not the same delimiter that matches with both sides
    for key, _ in unique_dict.items():
        key_1, key_2 = key.split("_")
        key_1 = int(key_1)
        key_2 = int(key_2)
        delimiter_coords = collected_delims[key_1] + collected_delims_2[key_2]

        # if min_AB_key != min_CD_key:
        #     delimiter_coords = collected_delims[min_AB_key] + collected_delims[min_CD_key]
        a = list(zip(collected_delims[key_1][::2], collected_delims[key_1][1::2]))
        b = list(zip(collected_delims[key_2][::2], collected_delims[key_2][1::2]))
        final_matches.append(
            {
                "id": f"{key_1}_{key_2}",
                "delimiter_coords": delimiter_coords,
                "coordinates": [[a[0], a[1]], [b[0], b[1]]],
            }
        )
    return final_matches


def transform_odo(coords, x_odo, y_odo, yaw):
    """Transform the coordinates based on the odometry position."""
    if all(coord == 0 for coord in coords):
        return coords

    rotation_matrix = np.array([[np.cos(yaw), -np.sin(yaw)], [np.sin(yaw), np.cos(yaw)]])

    point = np.array(coords)
    point_a = point[0], point[1]
    point_b = point[2], point[3]
    # First, apply the rotation to the point relative to origin (0,0)
    rotated_point_a = rotation_matrix @ point_a
    rotated_point_b = rotation_matrix @ point_b
    rotated_point_a = rotated_point_a + np.array([x_odo, y_odo])
    rotated_point_b = rotated_point_b + np.array([x_odo, y_odo])

    return rotated_point_a.tolist() + rotated_point_b.tolist()


def transform_odo_obj_shape(coords, x_odo, y_odo, yaw):
    """Transform the coordinates based on the odometry position."""
    if all(coord == 0 for coord in coords):
        return coords

    rotation_matrix = np.array([[np.cos(yaw), -np.sin(yaw)], [np.sin(yaw), np.cos(yaw)]])
    for i in range(0, len(coords), 2):
        point = np.array(coords[i : i + 2])
        point_a = point[0], point[1]
        # First, apply the rotation to the point relative to origin (0,0)
        rotated_point_a = rotation_matrix @ point_a
        rotated_point_a = rotated_point_a + np.array([x_odo, y_odo])
        coords[i] = rotated_point_a[0]
        coords[i + 1] = rotated_point_a[1]
    return coords


def get_point_color(result: int):
    """Get the color of the point."""
    if result == 1:
        return "green"
    return "red"


def get_slot_color(result: int):
    """Get the color of the point."""
    color_dict = {
        "FAIL": "rgba(255, 0, 0, 0.3)",  # signal is not valid
        False: "rgba(255, 0, 0, 0.3)",  # signal is not valid
        "PASS": "rgba(0, 255, 0, 0.3)",
        True: "rgba(0, 255, 0, 0.3)",
        "Unknown": "#818589",
    }
    return color_dict[result]


def transform_coordinates_using_new_origin(old_origin, coordinates):
    """
    Transform coordinates from an old origin to a new origin.

    Parameters:
    - old_origin: Tuple (x_old, y_old), the coordinates of the old origin.
    - new_origin: Tuple (x_new, y_new), the coordinates of the new origin.
    - coordinates: List of tuples [(x1, y1), (x2, y2), ...], the coordinates to transform.

    Returns:
    - List of transformed coordinates.
    """
    new_origin = (0, 0)
    try:
        # Calculate the offset between old and new origins
        offset_x = new_origin[0] - old_origin[0]
        offset_y = new_origin[1] - old_origin[1]

        # Transform each coordinate
        transformed_coords = [(x + offset_x, y + offset_y) for x, y in coordinates]
        old_origin = tuple(old_origin)
        new_origin = tuple(new_origin)
    except Exception:
        for i in range(0, len(coordinates), 2):
            x, y = coordinates[i], coordinates[i + 1]
            x = x + offset_x
            y = y + offset_y
            coordinates[i] = x
            coordinates[i + 1] = y
        return coordinates

    return transformed_coords


def get_all_parking_boxes(df: pd.DataFrame):
    """
    Extracts and combines parking box coordinates from the given DataFrame.
    This function identifies all columns in the DataFrame that contain parking box coordinates,
    combines these coordinates into a single list for each parking box, and filters out columns
    that contain only zero values.
    Args:
        df (pd.DataFrame): The input DataFrame containing parking box coordinate columns.
    Returns:
        Tuple[pd.DataFrame, List[str]]:
            - A DataFrame containing the combined parking box coordinates.
            - A list of column names that contain non-zero values.
    """
    pb_signal_df = pd.DataFrame()
    pb_count = len([x for x in list(df.columns) if SISignals.Columns.PB_SLOTCORDINATES_FRONTLEFT_X in x])
    # Combine all coordinates into a single list for each parking box
    for i in range(pb_count):
        pb_signal_df[SISignals.Columns.PARKBOX_COORDINATES_LIST.format(i)] = df[
            [x.format(i) for x in combined_list_for_all_pb]
        ].apply(lambda row: row.values.tolist(), axis=1)
    pb_col_with_values = [col for col in pb_signal_df.columns if not pb_signal_df[col].apply(is_all_zeros).all()]
    pb_signal_df = pb_signal_df[pb_col_with_values]
    return pb_signal_df, pb_col_with_values


def get_result_color(result: int):
    """Get the color of the point."""
    color_dict = {
        "FAIL": "#dc3545",  # signal is not valid
        False: "#dc3545",  # signal is not valid
        "PASS": "#28a745",
        True: "#28a745",
        "Unknown": "#818589",
    }
    text_dict = {
        "FAIL": "FAIL",
        False: "FAIL",
        "PASS": "PASS",
        True: "PASS",
        "Unknown": "NOT ASSESSED",
    }

    return (
        f'<span align="center" style="width: 100%; height: 100%; display: block;background-color: {color_dict[result]}'
        f' ; color : #ffffff">{text_dict[result]}</span>'
    )


def ap_state_dict(state: int):
    """Get the state of the AP."""
    state_dict = {
        0: "AP_INACTIVE",
        1: "AP_SCAN_IN",
        2: "AP_SCAN_OUT",
        3: "AP_AVG_ACTIVE_IN",
        4: "AP_AVG_ACTIVE_OUT",
        5: "AP_AVG_PAUSE",
        6: "AP_AVG_UNDO",
        7: "AP_ACTIVE_HANDOVER_AVAILABLE",
        8: "AP_AVG_FINISHED",
    }

    return f"{state_dict[state]} ({state})"


def create_hidden_table(table_string, tableid="id", button_text="Show additional information"):
    """Creates a hidden table in HTML format with unique IDs and improved styling."""
    table_string += """<style>
        /* Style the button */
        button {
            background-color: #FFA500;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            cursor: pointer;
            border-radius: 5px;
            margin-bottom: 20px; /* Add some space below the button */
        }

        /* Button hover effect */
        button:hover {
            background-color: #E09100;
        }

        .button-container {
            text-align: center;
            margin-top: 20px;
        }

        /* Style the table container to center it and ensure it's hidden initially */
        .table-container {
            display: none;  /* Hidden by default */
            text-align: center;
            margin-top: 20px;
        }

        table {
            margin: 0 auto; /* Center the table */
            border-collapse: collapse; /* Clean borders */
            width: 80%; /* Table width */
        }

        table, th, td {
            border: 1px solid #ddd; /* Table border */
        }

        th, td {
            padding: 8px; /* Padding for cells */
            text-align: center; /* Center text */
        }

        th {
            background-color: #f2f2f2; /* Header background */
        }

    </style>

    <script>
        function toggleTable(tableId) {
            var table = document.getElementById(tableId);
            var style = window.getComputedStyle(table);

            if (style.display === "none") {
                table.style.display = "block";  // Show the table container
            } else {
                table.style.display = "none";  // Hide the table container
            }
        }
    </script>
    """
    # Use the `tableid` in the button to reference the correct table
    table_string = (
        f"""<div class="button-container">
<button onclick="toggleTable('{tableid}')">{button_text}</button>
</div>
<div id="{tableid}" class="table-container">"""
        + table_string
        + "</div>"  # Close the table container div
    )
    return table_string


def are_lines_parallel(line1, line2):
    """
    Determine if two lines are parallel.
    Args:
        line1 (tuple): A tuple of four integers or floats representing the coordinates
                       of the first line in the form (x1, y1, x2, y2).
        line2 (tuple): A tuple of four integers or floats representing the coordinates
                       of the second line in the form (x3, y3, x4, y4).
    Returns:
        bool: True if the lines are parallel, False otherwise.
    Note:
        - If both lines are vertical (i.e., their x-coordinates are the same), they are considered parallel.
        - If one line is vertical and the other is not, they are not parallel.
        - For non-vertical lines, the slopes are compared to determine if the lines are parallel.
    """
    # Unpack the coordinates
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2

    # Calculate slopes for both lines
    # Avoid division by zero for vertical lines
    if (x2 - x1) == 0 and (x4 - x3) == 0:
        return True  # Both lines are vertical and parallel
    elif (x2 - x1) == 0 or (x4 - x3) == 0:
        return False  # One line is vertical, the other is not

    # Calculate slope (dy/dx) for both lines
    slope1 = (y2 - y1) / (x2 - x1)
    slope2 = (y4 - y3) / (x4 - x3)

    # Lines are parallel if slopes are equal
    return slope1 == slope2


def find_parallel_lines(lines_list, tolerance=1e-6):
    """Function to check if two lines are parallel using vector cross product"""

    def are_parallel(line1, line2):
        """Check parall=ellismn"""
        x1, y1, x2, y2 = line1
        x3, y3, x4, y4 = line2
        # Calculate the cross product of direction vectors
        return abs((x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)) < tolerance

    # Iterate over all pairs of lines to find the first parallel pair
    n = len(lines_list)
    for i in range(n):
        for j in range(i + 1, n):
            if are_parallel(lines_list[i], lines_list[j]):
                return i, j  # Return indices of the first pair of parallel lines

    return None  # If no parallel lines are found


def is_horizontal(line, tolerance=2):
    """Function to check is line is horizontal"""
    _, y1, _, y2 = line
    return abs(y1 - y2) < tolerance


def process_data(read_data: pd.DataFrame):
    """Process data for teststeps"""
    try:
        df = read_data.as_plain_df
        df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
        ap_state = df[SISignals.Columns.AP_STATE]
        ego_x = df[SISignals.Columns.EGO_POS_X]
        ego_y = df[SISignals.Columns.EGO_POS_Y]
        ego_yaw = df[SISignals.Columns.EGO_POS_YAW]
        ap_time = df[SISignals.Columns.TIME].values.tolist()

        marker_filtered_df = pd.DataFrame()
        marker_single_df = pd.DataFrame()
        pb_signal_df = pd.DataFrame()

        pb_with_marker_match = {}
        markers_not_matched = {}
        ap_time = [round(i, 3) for i in ap_time]

        pb_count = len([x for x in list(df.columns) if SISignals.Columns.PB_SLOTCORDINATES_FRONTLEFT_X in x])
        # Combine all coordinates into a single list for each parking box
        for i in range(pb_count):
            pb_signal_df[SISignals.Columns.PARKBOX_COORDINATES_LIST.format(i)] = df[
                [x.format(i) for x in combined_list_for_all_pb]
            ].apply(lambda row: row.values.tolist(), axis=1)

        pb_col_with_values = [col for col in pb_signal_df.columns if not pb_signal_df[col].apply(is_all_zeros).all()]
        pb_signal_df = pb_signal_df[pb_col_with_values]

        # Get how many delimiters signals are
        delimiter_count = len([x for x in list(df.columns) if "spaceMarkings_" in x and "array_x_0" in x])
        for delim_idx in range(delimiter_count):
            marker_single_df[SISignals.Columns.DELIMITERS_COORDINATES_LIST.format(delim_idx)] = df[
                [x.format(delim_idx) for x in gt_delimiter_length]
            ].apply(lambda row: row.values.tolist(), axis=1)

        mask_apstate_park_scan_in = (ap_state == ConstantsTrajpla.AP_AVG_ACTIVE_IN) | (
            ap_state == ConstantsTrajpla.AP_SCAN_IN
        )

        # Combine masks to get the final mask with valid values
        mask_final = marker_single_df.applymap(lambda x: any(i != 0 for i in x)).any(axis=1) & mask_apstate_park_scan_in

        marker_filtered_df = marker_single_df[mask_final]

        delim_col_with_values = [
            col for col in marker_filtered_df.columns if not marker_filtered_df[col].apply(is_all_zeros).all()
        ]
        filtered_timestamps = list(marker_filtered_df.index)
        # filtered_timestamps = filtered_timestamps[:69]
        ap_cycle = df["ap_cycle"]
        cycle_increase_ap = ap_cycle.rolling(2).apply(lambda x: x[1] > x[0], raw=True)
        filtered_timestamps = [row for row, val in cycle_increase_ap.items() if val == 1]

        # Create a dictionary to store the collected data
        collect_data_dict = {
            ts: {
                "pb": {},
                "ts": ap_time[list(df.index).index(ts)],
                "ap_state": ap_state.loc[ts],
                "markers": {},
                "intersection": {},
                "marker_match": {},
                "verdict": {},
                "ego_vehicle": [(ego_x.loc[ts], ego_y.loc[ts], ego_yaw.loc[ts])],
                "pb_width": {},
                "pb_with_marker_match": {},
                "delimiter_width_value": {},
                "parking_box_width_value": {},
                "overlap_percentage": {},
                "delim_width": {},
                "description": {},
            }
            for ts in filtered_timestamps
        }

        # Transform apstate to list
        ap_state = ap_state.values.tolist()

        for index_of, timestamp_val in enumerate(filtered_timestamps):

            pb_with_marker_match.clear()
            markers_not_matched.clear()
            delims_from_ts = {x: [] for x in range(len(delim_col_with_values))}
            pb_from_ts = {x: [(0.0, 0.0)] * 4 for x in range(len(pb_col_with_values))}
            if index_of + 1 < len(filtered_timestamps):
                idx = filtered_timestamps[index_of + 1]
            else:
                idx = timestamp_val

            for i, col_name in enumerate(pb_col_with_values):
                pb_coords = pb_signal_df[col_name].loc[idx]
                vertices_pb = list(zip(pb_coords[::2], pb_coords[1::2]))
                pb_from_ts[i] = vertices_pb
            # Remove the parking box with all zeros
            pb_from_ts = {x: y for x, y in pb_from_ts.items() if all(val1 != 0 for val1, val2 in y)}
            if index_of - 1 >= 0:
                idx = filtered_timestamps[index_of - 1]
            else:
                idx = timestamp_val
            for i, col_name in enumerate(delim_col_with_values):
                # delim_coords = df_all[col_name].loc[idx]
                delim_coords = marker_single_df[col_name].loc[idx]

                delim_coords = transform_odo(
                    delim_coords, ego_x.loc[timestamp_val], ego_y.loc[timestamp_val], ego_yaw.loc[timestamp_val]
                )

                delims_from_ts[i] = delim_coords
            delims_from_ts = {x: y for x, y in delims_from_ts.items() if all(val != 0 for val in y)}
            delims_from_ts = {x: y for x, y in delims_from_ts.items() if not is_horizontal(y)}
            if pb_from_ts:
                if len(delims_from_ts) >= 2:
                    for parking_box_id in pb_from_ts.keys():
                        are_matched, markers, delimiter_coords = match_delim_to_pb(
                            delims_from_ts, pb_from_ts[parking_box_id]
                        )
                        if are_matched:
                            pb_with_marker_match[parking_box_id] = (
                                markers,
                                pb_from_ts[parking_box_id],
                                delimiter_coords,
                            )
                        else:
                            markers_not_matched[parking_box_id] = markers
                else:

                    park_box_id = list(pb_from_ts.keys())[0]
                    vertices_pb = pb_from_ts[park_box_id]
                    distances_between_pb = quadrilateral_distances(vertices_pb)
                    AC_width_pb = float(f'{distances_between_pb.get("AC",0):.2f}')
                    collect_data_dict[timestamp_val]["pb"][park_box_id] = [
                        vertices_pb[0],
                        vertices_pb[1],
                        vertices_pb[3],
                        vertices_pb[2],
                        vertices_pb[0],
                    ]
                    collect_data_dict[timestamp_val]["delim_width"][park_box_id] = "N/A"

                    collect_data_dict[timestamp_val]["pb_width"][park_box_id] = AC_width_pb
                    collect_data_dict[timestamp_val]["delimiter_width_value"][park_box_id] = "N/A"
                    collect_data_dict[timestamp_val]["parking_box_width_value"][park_box_id] = AC_width_pb
                    collect_data_dict[timestamp_val]["overlap_percentage"][park_box_id] = "N/A"
                    collect_data_dict[timestamp_val]["intersection"][park_box_id] = [
                        (None, None),
                        (None, None),
                        (None, None),
                        (None, None),
                        (None, None),
                    ]
                    collect_data_dict[timestamp_val]["description"][
                        park_box_id
                    ] = "No valid delimiters found for this parking box."
                    collect_data_dict[timestamp_val]["markers"][park_box_id] = {
                        "id": "255_255",
                        "coordinates": [[(None, None), (None, None)]] * 2,
                    }
                    collect_data_dict[timestamp_val]["verdict"][park_box_id] = "Unknown"
            elif len(delims_from_ts) >= 2:
                collect_data_dict[timestamp_val]["marker_match"] = "marker_only"
                delimiter_without_pb = match_delim_to_delim(delims_from_ts, delims_from_ts)
                for delimiter in delimiter_without_pb:
                    delimiter_coords = delimiter["delimiter_coords"]
                    vertices = list(zip(delimiter_coords[::2], delimiter_coords[1::2]))
                    distances = quadrilateral_distances(vertices)
                    AC_width_delimiter_raw = distances.get("AC", 0)
                    AC_width_delimiter = float(f"{AC_width_delimiter_raw:.1f}")
                    park_box_id = 0
                    collect_data_dict[timestamp_val]["intersection"][park_box_id] = [
                        (None, None),
                        (None, None),
                        (None, None),
                        (None, None),
                        (None, None),
                    ]
                    collect_data_dict[timestamp_val]["delim_width"][
                        park_box_id
                    ] = f"Measured value: <b>{AC_width_delimiter}</b><br>Raw value: <b>{AC_width_delimiter_raw:.5f}</b>"
                    collect_data_dict[timestamp_val]["delimiter_width_value"][park_box_id] = AC_width_delimiter
                    collect_data_dict[timestamp_val]["parking_box_width_value"][park_box_id] = "N/A"
                    collect_data_dict[timestamp_val]["overlap_percentage"][park_box_id] = "N/A"
                    collect_data_dict[timestamp_val]["pb_width"][park_box_id] = "N/A"
                    collect_data_dict[timestamp_val]["pb"][park_box_id] = [
                        (None, None),
                        (None, None),
                        (None, None),
                        (None, None),
                        (None, None),
                    ]
                    delimiter_ids = delimiter["id"].split("_")
                    collect_data_dict[timestamp_val]["description"][
                        park_box_id
                    ] = f"Space between delimiters {delimiter_ids[0]} and delimiter {delimiter_ids[1]}.<br>"

                    collect_data_dict[timestamp_val]["markers"][park_box_id] = delimiter
            if pb_with_marker_match:
                if timestamp_val == 10039999:
                    print("pb_with_marker_match")
                collect_data_dict[timestamp_val]["marker_match"] = "marker_pb"
                collect_data_dict[timestamp_val]["pb_with_marker_match"] = pb_with_marker_match.copy()
                for park_box_id, matched_data in pb_with_marker_match.items():
                    markers = matched_data[0]
                    vertices_pb = matched_data[1]
                    delimiter_coords = matched_data[2]
                    distances_between_pb = quadrilateral_distances(vertices_pb)
                    collect_data_dict[timestamp_val]["description"][
                        park_box_id
                    ] = "No valid delimiters found for this parking box"
                    collect_data_dict[timestamp_val]["pb"][park_box_id] = [
                        vertices_pb[0],
                        vertices_pb[1],
                        vertices_pb[3],
                        vertices_pb[2],
                        vertices_pb[0],
                    ]
                    vertices = list(zip(delimiter_coords[::2], delimiter_coords[1::2]))
                    distances = quadrilateral_distances(vertices)

                    AC_width_pb_raw = distances_between_pb.get("AC", 0)
                    AC_width_pb = float(f"{AC_width_pb_raw:.1f}")
                    AC_width_delimiter_raw = calculate_width_angular(delimiter_coords)
                    AC_width_delimiter = float(f"{AC_width_delimiter_raw:.1f}")
                    delimiter_1 = markers["coordinates"][0]
                    delimiter_2 = markers["coordinates"][1]
                    delimiter_coords_polygon = delimiter_1 + [delimiter_2[1]] + [delimiter_2[0]]
                    slot_coords_polygon = [vertices_pb[0], vertices_pb[1], vertices_pb[3], vertices_pb[2]]
                    try:

                        intersection, overlap_percentage = calculate_overlap(
                            delimiter_coords_polygon, slot_coords_polygon
                        )
                        intersection_coords = intersection_fig_trace_method(
                            delimiter_coords_polygon, slot_coords_polygon
                        )
                    except Exception:
                        collect_data_dict[timestamp_val]["intersection"][park_box_id] = [
                            (None, None),
                            (None, None),
                            (None, None),
                            (None, None),
                            (None, None),
                        ]
                        collect_data_dict[timestamp_val]["description"][
                            park_box_id
                        ] = "No valid delimiters found for this parking box."
                        intersection_coords = [(None, None), (None, None), (None, None), (None, None), (None, None)]
                    intersection_coords = [(x, y) for x, y in zip(*intersection_coords)]
                    collect_data_dict[timestamp_val]["intersection"][park_box_id] = intersection_coords
                    collect_data_dict[timestamp_val]["overlap_percentage"][park_box_id] = overlap_percentage
                    collect_data_dict[timestamp_val]["delimiter_width_value"][park_box_id] = AC_width_delimiter
                    collect_data_dict[timestamp_val]["parking_box_width_value"][park_box_id] = AC_width_pb
                    # Check if the overlap is approximately 100%
                    collect_data_dict[timestamp_val]["delim_width"][
                        park_box_id
                    ] = f"Measured value: <b>{AC_width_delimiter}</b><br>Raw value: <b>{AC_width_delimiter_raw:.5f}</b>"
                    collect_data_dict[timestamp_val]["pb_width"][
                        park_box_id
                    ] = f"Measured value: <b>{AC_width_pb}</b><br>Raw value: <b>{AC_width_pb_raw:.5f}</b>"
                    delimiter_ids = markers["id"].split("_")
                    collect_data_dict[timestamp_val]["description"][
                        park_box_id
                    ] = f"Parking box {park_box_id} was detected \
                    in the space between delimiters {delimiter_ids[0]} and delimiter {delimiter_ids[1]}.<br>"
                    collect_data_dict[timestamp_val]["markers"][park_box_id] = markers
        ts_to_be_removed = []

        for ts, val in collect_data_dict.items():

            if not val["pb"].keys():
                ts_to_be_removed.append(ts)

        collect_data_dict = {k: v for k, v in collect_data_dict.items() if k not in ts_to_be_removed}

        return collect_data_dict
    except Exception as err:
        import os
        import sys

        print(timestamp_val)
        print(str(err))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


def distance_between_car_obstacle(df: pd.DataFrame):
    """Process object shapes and calculate overlap with polygons having less than 8 coordinates."""
    # Get the number of vertices for each object shape
    max_obj_0_array = int(max(df[SISignals.Columns.STATICOBJECT_ACTUALSIZE_0]))
    max_obj_1_array = int(max(df[SISignals.Columns.STATICOBJECT_ACTUALSIZE_1]))

    # Create a list of columns for each object shape
    obj_0_list = [x.format(0, i) for i in range(max_obj_0_array) for x in obj_shape]
    obj_1_list = [x.format(1, i) for i in range(max_obj_1_array) for x in obj_shape]

    # Create columns containing all the coordinates for each object shape
    df["objshape_0_coords"] = df[obj_0_list].apply(lambda row: row.values.tolist(), axis=1)
    df["objshape_1_coords"] = df[obj_1_list].apply(lambda row: row.values.tolist(), axis=1)

    # Get coords for 1st timestamp TODO : this is for development only
    coords1 = df["objshape_0_coords"].iloc[-1]
    coords1.append(coords1[0])
    coords1.append(coords1[1])
    x1, y1 = coords1[::2], coords1[1::2]  # column1

    coords2 = df["objshape_1_coords"].iloc[-1]
    coords2.append(coords2[0])
    coords2.append(coords2[1])
    x2 = coords2[::2]

    x_left = [min(max(x1), max(x2))]
    x_right = [max(min(x1), min(x2))]
    y_left_idx = x1.index(min(x1)) if min(min(x1), min(x2)) == min(x1) else x2.index(min(x2))
    y_right_idx = x1.index(max(x1)) if max(max(x1), max(x2)) == max(x1) else x2.index(max(x2))

    y_left = [y1[y_left_idx]]
    y_right = [y1[y_right_idx]]

    coords1 = np.array(list(zip(x_left, y_left)))
    coords2 = np.array(list(zip(x_right, y_right)))

    # Compute all pairwise distances
    distances = cdist(coords1, coords2)
    return distances


def process_data_for_length(read_data: pd.DataFrame):
    """Process data for teststeps"""
    # read_data = self.readers[READER_NAME]
    df = read_data.as_plain_df

    df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
    ap_state = df[SISignals.Columns.AP_STATE]
    ego_x = df[SISignals.Columns.EGO_POS_X]
    ego_y = df[SISignals.Columns.EGO_POS_Y]
    ego_yaw = df[SISignals.Columns.EGO_POS_YAW]
    ap_time = df[SISignals.Columns.TIME].values.tolist()

    marker_filtered_df = pd.DataFrame()
    marker_single_df = pd.DataFrame()
    pb_signal_df = pd.DataFrame()

    pb_with_marker_match = {}
    markers_not_matched = {}
    #     table_remark = f"Check when the number of valid parking boxes increases <b>(from signal {SISignals._properties[SISignals.Columns.NUMVALIDPARKINGBOXES_NU][0]})</b> if the width of space between delimiters(from signals <b>pclOutput.delimiters._%_ )</b> has the same dimensions \
    # from detected parking slots found in between the delimiters (from signal <b>parkingBoxPort.parkingBoxes_% )</b> <br><br>"
    ap_time = [round(i, 3) for i in ap_time]

    pb_count = len([x for x in list(df.columns) if SISignals.Columns.PB_SLOTCORDINATES_FRONTLEFT_X in x])
    # Combine all coordinates into a single list for each parking box
    for i in range(pb_count):
        pb_signal_df[SISignals.Columns.PARKBOX_COORDINATES_LIST.format(i)] = df[
            [x.format(i) for x in combined_list_for_all_pb]
        ].apply(lambda row: row.values.tolist(), axis=1)

    pb_col_with_values = [col for col in pb_signal_df.columns if not pb_signal_df[col].apply(is_all_zeros).all()]
    pb_signal_df = pb_signal_df[pb_col_with_values]
    # df[SISignals.Columns.PARKING_SCENARIO_0]

    # Get how many delimiters signals are
    delimiter_count = len([x for x in list(df.columns) if "spaceMarkings_" in x and "array_x_0" in x])
    # for idx in range(delimiter_count):
    #     # Get each delimiter with it's 4 coordinates into a single list
    #     marker = [x.format(idx) for x in delimiter_list]
    #     marker_single_df[SISignals.Columns.DELIMITERS_COORDINATES_LIST.format(idx)] = df[marker].apply(
    #         lambda row: row.values.tolist(), axis=1
    #     )
    for delim_idx in range(delimiter_count):
        marker_single_df[SISignals.Columns.DELIMITERS_COORDINATES_LIST.format(delim_idx)] = df[
            [x.format(delim_idx) for x in gt_delimiter_length]
        ].apply(lambda row: row.values.tolist(), axis=1)
    mask_final = marker_single_df.applymap(lambda x: any(i != 0 for i in x)).any(axis=1)
    delim_with_VALUES = [col for col in marker_single_df.columns if not marker_single_df[col].apply(is_all_zeros).all()]
    marker_filtered_df = marker_single_df[mask_final]
    marker_filtered_df = marker_filtered_df[delim_with_VALUES]
    mask_apstate_park_scan_in = (ap_state == ConstantsTrajpla.AP_AVG_ACTIVE_IN) | (
        ap_state == ConstantsTrajpla.AP_SCAN_IN
    )

    # Combine masks to get the final mask with valid values
    mask_final = marker_single_df.applymap(lambda x: any(i != 0 for i in x)).any(axis=1) & mask_apstate_park_scan_in

    # total_brake_events = mask_brake_events.sum()
    marker_filtered_df = marker_single_df[mask_final]

    delim_col_with_values = [
        col for col in marker_filtered_df.columns if not marker_filtered_df[col].apply(is_all_zeros).all()
    ]
    filtered_timestamps = list(marker_filtered_df.index)
    # filtered_timestamps = filtered_timestamps[:900]
    # filtered_timestamps = filtered_timestamps[:500]

    # Create a dictionary to store the collected data
    collect_data_dict = {
        ts: {
            "pb": {},
            "ts": ap_time[list(df.index).index(ts)],
            "ap_state": ap_state.loc[ts],
            "markers": {},
            "intersection": {},
            "marker_match": {},
            "verdict": {},
            "ego_vehicle": [(ego_x.loc[ts], ego_y.loc[ts], ego_yaw.loc[ts])],
            "pb_width": {},
            "pb_length": {},
            "pb_with_marker_match": {},
            "delimiter_width_value": {},
            "delimiter_lenght_value": {},
            "parking_box_width_value": {},
            "parking_box_lenght_value": {},
            "overlap_percentage": {},
            "delim_width": {},
            "delim_length": {},
            "description": {},
        }
        for ts in filtered_timestamps
    }

    # Transform apstate to list
    ap_state = ap_state.values.tolist()
    horizontal_markings = {ts: {"markers": [(None, None) * 4]} for ts in filtered_timestamps}
    for timestamp_val in filtered_timestamps:

        pb_with_marker_match.clear()
        markers_not_matched.clear()
        delims_from_ts = {x: [] for x in range(len(delim_col_with_values))}
        pb_from_ts = {x: [(0.0, 0.0)] * 4 for x in range(len(pb_col_with_values))}

        for i, col_name in enumerate(pb_col_with_values):
            pb_coords = pb_signal_df[col_name].loc[timestamp_val]
            # park_id = df[signals_obj.Columns.parkingBoxID_nu].loc[timestamp_val]
            vertices_pb = list(zip(pb_coords[::2], pb_coords[1::2]))
            pb_from_ts[i] = vertices_pb
        # Remove the parking box with all zeros
        pb_from_ts = {x: y for x, y in pb_from_ts.items() if all(val1 != 0 for val1, val2 in y)}
        for i, col_name in enumerate(delim_col_with_values):
            delim_coords = marker_single_df[col_name].loc[timestamp_val]
            delim_coords = transform_odo(
                delim_coords, ego_x.loc[timestamp_val], ego_y.loc[timestamp_val], ego_yaw.loc[timestamp_val]
            )

            delims_from_ts[i] = delim_coords
        delims_from_ts = {x: y for x, y in delims_from_ts.items() if all(val != 0 for val in y)}
        horizontal_markings[timestamp_val] = [x for x in delims_from_ts.values() if is_horizontal(x)]
        delims_from_ts = {x: y for x, y in delims_from_ts.items() if not is_horizontal(y)}

        if pb_from_ts:
            if len(delims_from_ts) >= 2:
                for parking_box_id in pb_from_ts.keys():
                    are_matched, markers, delimiter_coords = match_delim_to_pb(
                        delims_from_ts, pb_from_ts[parking_box_id]
                    )
                    if are_matched:
                        pb_with_marker_match[parking_box_id] = (markers, pb_from_ts[parking_box_id], delimiter_coords)
                    else:
                        # markers_not_matched[parking_box_id] = (markers, delimiter_coords)
                        markers_not_matched[parking_box_id] = markers
            else:

                park_box_id = list(pb_from_ts.keys())[0]
                vertices_pb = pb_from_ts[park_box_id]
                distances_between_pb = quadrilateral_distances(vertices_pb)
                AC_width_pb = float(f'{distances_between_pb.get("AC",0):.2f}')
                AB_length_pb = float(f'{distances_between_pb.get("AB",0):.2f}')
                collect_data_dict[timestamp_val]["pb"][park_box_id] = [
                    vertices_pb[0],
                    vertices_pb[1],
                    vertices_pb[3],
                    vertices_pb[2],
                    vertices_pb[0],
                ]
                collect_data_dict[timestamp_val]["delim_width"][park_box_id] = "N/A"
                collect_data_dict[timestamp_val]["delim_length"][park_box_id] = "N/A"
                collect_data_dict[timestamp_val]["pb_width"][park_box_id] = AC_width_pb
                collect_data_dict[timestamp_val]["pb_length"][park_box_id] = AB_length_pb
                collect_data_dict[timestamp_val]["delimiter_width_value"][park_box_id] = "N/A"
                collect_data_dict[timestamp_val]["delimiter_lenght_value"][park_box_id] = "N/A"
                collect_data_dict[timestamp_val]["parking_box_width_value"][park_box_id] = AC_width_pb
                collect_data_dict[timestamp_val]["parking_box_lenght_value"][park_box_id] = AB_length_pb
                collect_data_dict[timestamp_val]["overlap_percentage"][park_box_id] = "N/A"
                collect_data_dict[timestamp_val]["intersection"][park_box_id] = [
                    (None, None),
                    (None, None),
                    (None, None),
                    (None, None),
                    (None, None),
                ]
                collect_data_dict[timestamp_val]["description"][
                    park_box_id
                ] = "No valid delimiters found for this parking box."
                collect_data_dict[timestamp_val]["markers"][park_box_id] = {
                    "id": "255_255",
                    "coordinates": [[(None, None), (None, None)]] * 2,
                }
                collect_data_dict[timestamp_val]["verdict"][park_box_id] = "Unknown"
        elif len(delims_from_ts) >= 2:
            collect_data_dict[timestamp_val]["marker_match"] = "marker_only"
            delimiter_without_pb = match_delim_to_delim(delims_from_ts, delims_from_ts)
            for delimiter in delimiter_without_pb:
                delimiter_coords = delimiter["delimiter_coords"]
                vertices = list(zip(delimiter_coords[::2], delimiter_coords[1::2]))
                distances = quadrilateral_distances(vertices)
                AC_width_delimiter_raw = distances.get("AC", 0)
                AB_length_delimiter_raw = distances.get("AB", 0)
                # AC_width_delimiter_raw = calculate_width_angular(delimiter_coords)
                AC_width_delimiter = float(f"{AC_width_delimiter_raw:.1f}")
                AB_length_delimiter = float(f"{AB_length_delimiter_raw:.1f}")
                park_box_id = 0
                collect_data_dict[timestamp_val]["intersection"][park_box_id] = [
                    (None, None),
                    (None, None),
                    (None, None),
                    (None, None),
                    (None, None),
                ]
                collect_data_dict[timestamp_val]["delim_width"][
                    park_box_id
                ] = f"Measured value: <b>{AC_width_delimiter}</b><br>Raw value: <b>{AC_width_delimiter_raw:.5f}</b>"
                collect_data_dict[timestamp_val]["delim_length"][
                    park_box_id
                ] = f"Measured value: <b>{AB_length_delimiter}</b><br>Raw value: <b>{AB_length_delimiter_raw:.5f}</b>"
                collect_data_dict[timestamp_val]["delimiter_width_value"][park_box_id] = AC_width_delimiter
                collect_data_dict[timestamp_val]["delimiter_lenght_value"][park_box_id] = AB_length_delimiter
                collect_data_dict[timestamp_val]["parking_box_width_value"][park_box_id] = "N/A"
                collect_data_dict[timestamp_val]["parking_box_lenght_value"][park_box_id] = "N/A"
                collect_data_dict[timestamp_val]["overlap_percentage"][park_box_id] = "N/A"
                collect_data_dict[timestamp_val]["pb_width"][park_box_id] = "N/A"
                collect_data_dict[timestamp_val]["pb_length"][park_box_id] = "N/A"
                collect_data_dict[timestamp_val]["pb"][park_box_id] = [
                    (None, None),
                    (None, None),
                    (None, None),
                    (None, None),
                    (None, None),
                ]
                delimiter_ids = delimiter["id"].split("_")
                collect_data_dict[timestamp_val]["description"][
                    park_box_id
                ] = f"Space between delimiters {delimiter_ids[0]} and delimiter {delimiter_ids[1]}.<br>"

                collect_data_dict[timestamp_val]["markers"][park_box_id] = delimiter
        if pb_with_marker_match:

            collect_data_dict[timestamp_val]["marker_match"] = "marker_pb"
            collect_data_dict[timestamp_val]["pb_with_marker_match"] = pb_with_marker_match.copy()
            for park_box_id, matched_data in pb_with_marker_match.items():
                markers = matched_data[0]
                vertices_pb = matched_data[1]
                delimiter_coords = matched_data[2]
                distances_between_pb = quadrilateral_distances(vertices_pb)
                collect_data_dict[timestamp_val]["description"][
                    park_box_id
                ] = "No valid delimiters found for this parking box"
                collect_data_dict[timestamp_val]["pb"][park_box_id] = [
                    vertices_pb[0],
                    vertices_pb[1],
                    vertices_pb[3],
                    vertices_pb[2],
                    vertices_pb[0],
                ]
                vertices = list(zip(delimiter_coords[::2], delimiter_coords[1::2]))
                distances = quadrilateral_distances(vertices)
                # AC_width_delimiter = float(f'{distances.get("AC",0):.2f}')

                AC_width_pb_raw = distances_between_pb.get("AC", 0)
                AC_width_pb = float(f"{AC_width_pb_raw:.1f}")
                AB_length_pb_raw = distances_between_pb.get("AB", 0)
                AB_length_pb = float(f"{AB_length_pb_raw:.1f}")
                AC_width_delimiter_raw = calculate_width_angular(delimiter_coords)
                AC_width_delimiter = float(f"{AC_width_delimiter_raw:.1f}")
                AB_lenght_delimiter_raw = distances.get("AB", 0)
                AB_lenght_delimiter = float(f"{AB_lenght_delimiter_raw:.1f}")
                # AC_width_delimiter = round(calculate_width_angular(delimiter_coords),2)
                delimiter_1 = markers["coordinates"][0]
                delimiter_2 = markers["coordinates"][1]
                delimiter_coords_polygon = delimiter_1 + [delimiter_2[1]] + [delimiter_2[0]]
                slot_coords_polygon = [vertices_pb[0], vertices_pb[1], vertices_pb[3], vertices_pb[2]]
                try:

                    intersection, overlap_percentage = calculate_overlap(delimiter_coords_polygon, slot_coords_polygon)
                    intersection_coords = intersection_fig_trace_method(delimiter_coords_polygon, slot_coords_polygon)
                except Exception:
                    collect_data_dict[timestamp_val]["intersection"][park_box_id] = [
                        (None, None),
                        (None, None),
                        (None, None),
                        (None, None),
                        (None, None),
                    ]
                    collect_data_dict[timestamp_val]["description"][
                        park_box_id
                    ] = "No valid delimiters found for this parking box."
                    intersection_coords = [(None, None), (None, None), (None, None), (None, None), (None, None)]
                intersection_coords = [(x, y) for x, y in zip(*intersection_coords)]
                collect_data_dict[timestamp_val]["intersection"][park_box_id] = intersection_coords
                collect_data_dict[timestamp_val]["overlap_percentage"][park_box_id] = overlap_percentage
                collect_data_dict[timestamp_val]["delimiter_width_value"][park_box_id] = AC_width_delimiter
                collect_data_dict[timestamp_val]["delimiter_lenght_value"][park_box_id] = AB_lenght_delimiter
                collect_data_dict[timestamp_val]["parking_box_width_value"][park_box_id] = AC_width_pb
                collect_data_dict[timestamp_val]["parking_box_lenght_value"][park_box_id] = AB_length_pb
                # Check if the overlap is approximately 100%
                # is_fully_attached = overlap_ratio >= 0.99
                collect_data_dict[timestamp_val]["delim_width"][
                    park_box_id
                ] = f"Measured value: <b>{AC_width_delimiter}</b><br>Raw value: <b>{AC_width_delimiter_raw:.5f}</b>"
                collect_data_dict[timestamp_val]["delim_length"][
                    park_box_id
                ] = f"Measured value: <b>{AB_lenght_delimiter}</b><br>Raw value: <b>{AB_lenght_delimiter_raw:.5f}</b>"
                collect_data_dict[timestamp_val]["pb_width"][
                    park_box_id
                ] = f"Measured value: <b>{AC_width_pb}</b><br>Raw value: <b>{AC_width_pb_raw:.5f}</b>"
                collect_data_dict[timestamp_val]["pb_length"][
                    park_box_id
                ] = f"Measured value: <b>{AB_length_pb}</b><br>Raw value: <b>{AB_length_pb_raw:.5f}</b>"
                delimiter_ids = markers["id"].split("_")
                collect_data_dict[timestamp_val]["description"][
                    park_box_id
                ] = f"Parking box {park_box_id} was detected \
                in the space between delimiters {delimiter_ids[0]} and delimiter {delimiter_ids[1]}.<br>"
                collect_data_dict[timestamp_val]["markers"][park_box_id] = markers
    ts_to_be_removed = []

    for ts, val in collect_data_dict.items():

        if not val["pb"].keys():
            ts_to_be_removed.append(ts)

    collect_data_dict = {k: v for k, v in collect_data_dict.items() if k not in ts_to_be_removed}

    return collect_data_dict, horizontal_markings


def are_points_above_line(marking_line, furthest_points):
    """
    Check if points are above the line defined by marking_line.

    Args:
        marking_line (list): Coordinates of the line [x1, y1, x2, y2].
        furthest_points (list): List of points to check, each in the form [x, y].

    Returns:
        bool: True if any point is above the line, False otherwise.
    """
    # Extract the points of the line
    x1, y1, x2, y2 = marking_line

    # Calculate the slope (m) and intercept (b)
    m = (y2 - y1) / (x2 - x1)
    b = y1 - m * x1

    # Check if the line is in the positive or negative region
    line_in_positive_region = y1 > 0 and y2 > 0
    line_in_negative_region = y1 < 0 and y2 < 0

    distances = []
    # Check each point
    for point in furthest_points:
        x_p, y_p = point
        y_line = m * x_p + b  # Y of the line at the X of the point
        # Compare the position of the point based on the region
        if line_in_positive_region:
            distances.append(y_line <= y_p)
        elif line_in_negative_region:
            distances.append(y_line >= y_p)

    return any(distances)  # Any point beyond the line


def euclidean_distance(ego_vehicle, object_position):
    """Calculate Euclidean distance between ego vehicle and object."""
    return math.sqrt((object_position[0] - ego_vehicle[0]) ** 2 + (object_position[1] - ego_vehicle[1]) ** 2)


def cal_orientation_vehicle(vertices_pb_vehicle):
    """Calculate the orientation of the vehicle."""
    x = vertices_pb_vehicle[0]
    y = vertices_pb_vehicle[1]
    return math.atan2(y, x)


def cal_orientation_pb(box_cord_0_1):
    """Calculate the orientation of the parking box."""
    x1, y1 = box_cord_0_1[0]  # Initial position
    x2, y2 = box_cord_0_1[1]  # Next position

    # Calculate orientation
    pb_orientation_in_rad_val = math.atan2(y2 - y1, x2 - x1)
    return pb_orientation_in_rad_val


def is_parallel_parking_box_free(ego_vehicle_orientation, box_orientation):
    """
    Check if the parking box orientation is within the allowable range.

    Parameters:
    ego_vehicle_orientation (float): Orientation of the ego vehicle in radians.
    box_orientation (float): Orientation of the parking box's roadside edge in radians.

    Returns:
    bool: True if the parking box is free for parallel parking, False otherwise.
    """
    # Calculate the relative orientation between the box and ego vehicle
    relative_orientation = box_orientation - ego_vehicle_orientation

    # Normalize the orientation to the range [-π, π] for consistent angle comparison
    relative_orientation = math.atan2(math.sin(relative_orientation), math.cos(relative_orientation))

    return relative_orientation


def calculate_orthogonal_distance(ego_positions, line_start, line_end):
    """
    Calculate orthogonal distance from a point to a line segment.
    If not possible, return the distance to the nearest vertex.

    Parameters:
    ego_pos (tuple): Ego vehicle position (x, y).
    line_start (tuple): Start point of the line (x, y).
    line_end (tuple): End point of the line (x, y).

    Returns:
    float: Distance from the ego position to the line segment.
    """
    ego_x_col, ego_y_col = ego_positions
    park_marker_positions_x_0, park_marker_positions_y_0 = line_start
    park_marker_positions_x_1, park_marker_positions_y_1 = line_end

    # Line segment vector
    dx = park_marker_positions_x_1 - park_marker_positions_x_0
    dy = park_marker_positions_y_1 - park_marker_positions_y_0

    # Check if the line segment is a point
    if dx == 0 and dy == 0:
        return math.sqrt((ego_x_col - park_marker_positions_x_0) ** 2 + (ego_y_col - park_marker_positions_y_0) ** 2)

    # Projection of point onto the line segment
    t = ((ego_x_col - park_marker_positions_x_0) * dx + (ego_y_col - park_marker_positions_y_0) * dy) / (dx**2 + dy**2)

    if 0 <= t <= 1:
        projection_x = park_marker_positions_x_0 + t * dx
        projection_y = park_marker_positions_y_0 + t * dy
        return math.sqrt((ego_x_col - projection_x) ** 2 + (ego_y_col - projection_y) ** 2)

    else:
        distance_start = math.sqrt(
            (ego_x_col - park_marker_positions_x_0) ** 2 + (ego_y_col - park_marker_positions_y_0) ** 2
        )
        distance_end = math.sqrt(
            (ego_x_col - park_marker_positions_x_1) ** 2 + (ego_y_col - park_marker_positions_y_1) ** 2
        )
        return min(distance_start, distance_end)


combined_list_for_all_gt_pb = [
    "GT_ParkingBoxFrontLeftX_{}",
    "GT_ParkingBoxFrontLeftY_{}",
    "GT_ParkingBoxFrontRightX_{}",
    "GT_ParkingBoxFrontRightY_{}",
    "GT_ParkingBoxRearLeftX_{}",
    "GT_ParkingBoxRearLeftY_{}",
    "GT_ParkingBoxRearRightX_{}",
    "GT_ParkingBoxRearRightY_{}",
]


def process_data_GT(read_data: pd.DataFrame):
    """Process data for teststeps"""
    df = read_data.as_plain_df

    df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
    ap_state = df[SISignals.Columns.AP_STATE]
    ego_x = df[SISignals.Columns.EGO_POS_X]
    ego_y = df[SISignals.Columns.EGO_POS_Y]
    ego_yaw = df[SISignals.Columns.EGO_POS_YAW]
    ego_vehicle = df[[SISignals.Columns.EGO_POS_X, SISignals.Columns.EGO_POS_Y, SISignals.Columns.EGO_POS_YAW]]
    ap_time = df[SISignals.Columns.TIME].values.tolist()

    pb_signal_df = pd.DataFrame()

    ap_time = [round(i, 3) for i in ap_time]

    pb_count = len([x for x in list(df.columns) if SISignals.Columns.PB_SLOTCORDINATES_FRONTLEFT_X in x])
    # Combine all coordinates into a single list for each parking box
    for i in range(pb_count):
        pb_signal_df[SISignals.Columns.PARKBOX_COORDINATES_LIST.format(i)] = df[
            [x.format(i) for x in combined_list_for_all_pb]
        ].apply(lambda row: row.values.tolist(), axis=1)

    pb_col_with_values = [col for col in pb_signal_df.columns if not pb_signal_df[col].apply(is_all_zeros).all()]
    pb_signal_df = pb_signal_df[pb_col_with_values]

    gt_pb_count = len([x for x in list(df.columns) if SISignals.Columns.GT_SLOT_P_X_0 in x])
    gt_pb_signal_df = pd.DataFrame()

    # Combine all coordinates into a single list for each GT parking box
    for i in range(int(gt_pb_count)):
        gt_pb_signal_df[SISignals.Columns.GT_SLOT_COORDINATES_LIST.format(i)] = df[
            [
                f"gt_slot_p_x_0_{i}",
                f"gt_slot_p_y_0_{i}",
                f"gt_slot_p_x_1_{i}",
                f"gt_slot_p_y_1_{i}",
                f"gt_slot_p_x_2_{i}",
                f"gt_slot_p_y_2_{i}",
                f"gt_slot_p_x_3_{i}",
                f"gt_slot_p_y_3_{i}",
            ]
        ].apply(lambda row: row.values.tolist(), axis=1)

    gt_pb_col_with_values = [
        col for col in gt_pb_signal_df.columns if not gt_pb_signal_df[col].apply(is_all_zeros).all()
    ]
    gt_pb_signal_df = gt_pb_signal_df[gt_pb_col_with_values]

    gt_pb_signal_df = gt_pb_signal_df.apply(
        lambda row: row.combine(
            ego_vehicle.apply(tuple, axis=1),
            lambda coord, ego_data: transform_odo_obj_shape(coord, ego_data[0], ego_data[1], ego_data[2]),
        )
    )

    mask_apstate_park_scan_in = (ap_state == ConstantsTrajpla.AP_AVG_ACTIVE_IN) | (
        ap_state == ConstantsTrajpla.AP_SCAN_IN
    )

    mask_final = pb_signal_df[mask_apstate_park_scan_in]

    filtered_timestamps = list(mask_final.index)
    # Create a dictionary to store the collected data
    collect_data_dict = {
        ts: {
            "pb": {},
            "pbs_gt": {},
            "ts": ap_time[list(df.index).index(ts)],
            "ap_state": ap_state.loc[ts],
            "verdict": {},
            "ego_vehicle": [(ego_x.loc[ts], ego_y.loc[ts], ego_yaw.loc[ts])],
            "description": {},
        }
        for ts in filtered_timestamps
    }

    # Transform apstate to list
    ap_state = ap_state.values.tolist()

    for timestamp_val in filtered_timestamps:

        pb_from_ts = {x: [(0.0, 0.0)] * 4 for x in range(len(pb_col_with_values))}
        gt_pb_from_ts = {x: [(0.0, 0.0)] * 4 for x in range(len(gt_pb_col_with_values))}
        for i, col_name in enumerate(pb_col_with_values):
            pb_coords = pb_signal_df[col_name].loc[timestamp_val]
            vertices_pb = list(zip(pb_coords[::2], pb_coords[1::2]))
            pb_from_ts[i] = vertices_pb

            gt_pb_coords = gt_pb_signal_df[gt_pb_col_with_values[i]].loc[timestamp_val]
            vertices_gt_pb = list(zip(gt_pb_coords[::2], gt_pb_coords[1::2]))
            gt_pb_from_ts[i] = vertices_gt_pb
        # Remove the parking box with all zeros
        pb_from_ts = {x: y for x, y in pb_from_ts.items() if all(val1 != 0 for val1, val2 in y)}
        gt_pb_from_ts = {x: y for x, y in gt_pb_from_ts.items() if all(val1 != 0 for val1, val2 in y)}
        if pb_from_ts:
            park_box_id = list(pb_from_ts.keys())[0]
            vertices_pb = pb_from_ts[park_box_id]
            collect_data_dict[timestamp_val]["pb"][park_box_id] = [
                vertices_pb[0],
                vertices_pb[1],
                vertices_pb[3],
                vertices_pb[2],
                vertices_pb[0],
            ]
            gt_park_box_id = list(gt_pb_from_ts.keys())[0]
            vertices_gt_pb = gt_pb_from_ts[gt_park_box_id]
            collect_data_dict[timestamp_val]["pbs_gt"][gt_park_box_id] = [
                vertices_gt_pb[0],
                vertices_gt_pb[3],
                vertices_gt_pb[2],
                vertices_gt_pb[1],
                vertices_gt_pb[0],
            ]
            collect_data_dict[timestamp_val]["description"][park_box_id] = ""
            collect_data_dict[timestamp_val]["verdict"][park_box_id] = "Unknown"
    ts_to_be_removed = []

    for ts, val in collect_data_dict.items():

        if not val["pb"].keys():
            ts_to_be_removed.append(ts)

    collect_data_dict = {k: v for k, v in collect_data_dict.items() if k not in ts_to_be_removed}

    return collect_data_dict


def calculate_relative_orientation(box_orientation_in_rad, ego_vehicle_orientation_in_rad):
    """
    Calculate the relative orientation between a box and an ego vehicle.
    Parameters:
    box_orientation_in_rad (float): The orientation of the box in radians.
    ego_vehicle_orientation_in_rad (float): The orientation of the ego vehicle in radians.
    Returns:
    float: The relative orientation in radians, adjusted to be within the range [-pi, pi].
    """
    # Difference between orientations
    relative_orientation = box_orientation_in_rad - ego_vehicle_orientation_in_rad

    # Normalize the difference to be within the range [-pi, pi]
    relative_orientation_in_rad = math.atan2(math.sin(relative_orientation), math.cos(relative_orientation))

    # If the relative orientation is close to pi or -pi (indicating inversion), adjust it
    if abs(relative_orientation_in_rad) > math.pi / 2:  # Ex. greater than 90 degrees
        # Adjust for reverse direction
        if relative_orientation_in_rad > 0:
            relative_orientation_in_rad -= math.pi
        else:
            relative_orientation_in_rad += math.pi

    return relative_orientation_in_rad


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


def translate_and_rotate(point, new_x, new_y, yaw):
    """
    Translates and rotates a single point based on the given origin and yaw angle.

    Parameters:
    - point: A dictionary with 'x' and 'y' keys representing the point to transform.
    - new_x: The new X origin coordinate.
    - new_y: The new Y origin coordinate.
    - yaw: Rotation angle in radians.

    Returns:
    - A dictionary with the transformed 'x' and 'y' coordinates.
    """
    # Convert point to a numpy array
    original_point = np.array([point["x"], point["y"]])

    # Create the rotation matrix
    rotation_matrix = np.array([[np.cos(yaw), -np.sin(yaw)], [np.sin(yaw), np.cos(yaw)]])

    # Apply rotation
    rotated_point = rotation_matrix @ original_point

    # Apply translation
    translated_point = rotated_point + np.array([new_x, new_y])

    # Return the transformed point as a dictionary
    return {"x": translated_point[0], "y": translated_point[1]}


def normalize_angle(angle):
    """
    Normalize the angle to convert 359.99 to 360.
    If the angle is close to 360 (e.g., 359.99), it is rounded to 360.

    Parameters:
    - angle (float): The input angle.

    Returns:
    - float: Normalized angle.
    """
    if round(angle, 2) == 360 or angle >= 359.99:
        return 360
    return angle


def calculate_perpendicular_from_car_to_road(car_line, road_side_edge):
    """
    Calculates the perpendicular distance from the terminal point of the car's line to the road's edge
    and returns the intersection point of the perpendicular line with the road edge.

    Args:
        car_line (list): A list of two dictionaries containing the x and y coordinates of the two points of the car's line.
        road_side_edge (list): A list of two tuples containing the coordinates of the two points of the road's edge.

    Returns:
        tuple: A pair containing:
            - the perpendicular distance from the car's terminal point to the road's edge (float).
            - the intersection point of the perpendicular line with the road edge (tuple or None if no intersection).
    """
    # Extract the coordinates of the two points of the car's line
    x1, y1 = car_line[0]["x"], car_line[0]["y"]
    x2, y2 = car_line[1]["x"], car_line[1]["y"]

    # Extract the coordinates of the two points of the road's edge
    x3, y3 = road_side_edge[0]
    x4, y4 = road_side_edge[1]

    # Function to calculate the slope and y-intercept (b) of a line given two points
    def line_from_points(p1, p2):
        # Calculate the slope (m) and y-intercept (b) of the line defined by points p1 and p2
        slope = (p2[1] - p1[1]) / (p2[0] - p1[0]) if p2[0] != p1[0] else float("inf")
        b = p1[1] - slope * p1[0]
        return slope, b

    # Function to calculate the slope and y-intercept of the perpendicular line
    def perpendicular_line(slope, point):
        # For a horizontal line (slope = 0), the perpendicular is a vertical line
        if slope == 0:
            return float("inf"), point[1]
        # Calculate the slope of the perpendicular line (negative reciprocal of the original slope)
        perp_slope = -1 / slope
        perp_b = point[1] - perp_slope * point[0]
        return perp_slope, perp_b

    # Function to calculate the intersection point of two lines given their slopes and intercepts
    def intersection(line1, line2):
        slope1, b1 = line1
        slope2, b2 = line2
        # If the slopes are equal, the lines are parallel and do not intersect
        if slope1 == slope2:
            return None
        # Calculate the x and y coordinates of the intersection point
        x = (b2 - b1) / (slope1 - slope2)
        y = slope1 * x + b1
        return (x, y)

    # Function to calculate the distance between two points (x1, y1) and (x2, y2)
    def distance_between_points(x1, y1, x2, y2):
        return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    # Calculate the slope of the car's line
    slope_car, _ = line_from_points((x1, y1), (x2, y2))

    # Calculate the slope and y-intercept of the perpendicular line from the car's terminal point
    perp_slope, perp_b = perpendicular_line(slope_car, (x2, y2))

    # Calculate the slope and y-intercept of the road's edge line
    slope_road, b_road = line_from_points((x3, y3), (x4, y4))

    # Calculate the intersection point of the perpendicular line with the road's edge
    intersection_point = intersection((perp_slope, perp_b), (slope_road, b_road))

    # If an intersection exists, calculate the distance between the car's terminal point and the intersection
    if intersection_point:
        distance = distance_between_points(x2, y2, intersection_point[0], intersection_point[1])
    else:
        distance = 0  # If no intersection exists, set distance to 0

    # Return the distance and the intersection point
    return distance, intersection_point


def check_delimiters_on_parking(delimiters, parking_box_vertices):
    """
    Checks the delimiters are present on the parking box.
    :param: delimetes coordiantes.
    :param: parking box coordinates.
    :return: returns the True or False values if the delimiter is available of curb side and first or second side of the PB
    """
    # Threshold to accomdate the present of delimiter if it not exactly collinear with the Parkin box but delimiter is available on parking box side.
    threshold = 0.15

    def is_collinear_and_overlapping(pb_start, pb_end, delim_start, delim_end):
        def cross_product(x1, y1, x2, y2, x, y):
            return abs((x - x1) * (y2 - y1) - (y - y1) * (x2 - x1))

        px1, py1 = pb_start
        px2, py2 = pb_end
        dx1, dy1 = delim_start
        dx2, dy2 = delim_end

        collinear = (
            cross_product(px1, py1, px2, py2, dx1, dy1) <= threshold
            and cross_product(px1, py1, px2, py2, dx2, dy2) <= threshold
        )

        if not collinear:
            return False
        else:
            return True

    parking_box_sides = [
        (parking_box_vertices[0], parking_box_vertices[1], "AB"),
        (parking_box_vertices[1], parking_box_vertices[3], "BD"),
        (parking_box_vertices[3], parking_box_vertices[2], "DC"),
        (parking_box_vertices[2], parking_box_vertices[0], "CA"),
    ]

    result = {}
    found_first_delimiter = False
    found_second_delimiter = False
    found_required_delimters = False

    required_side_for_first_delimiter = ["BD"]
    required_side_for_second_delimiter = ["AB", "DC"]

    for key, value in delimiters.items():
        delimiter_start = (value[0], value[1])
        delimiter_end = (value[2], value[3])
        found = False
        for pb_start, pb_end, pb_side_name in parking_box_sides:
            if is_collinear_and_overlapping(pb_start, pb_end, delimiter_start, delimiter_end):
                result[key] = {
                    "result": "PASS",
                    "parking_box_side": (pb_start, pb_end),
                    "delimiter_vertices": (delimiter_start, delimiter_end),
                    "side_name": pb_side_name,
                }
                if pb_side_name in required_side_for_first_delimiter:
                    found_first_delimiter = True
                if pb_side_name in required_side_for_second_delimiter:
                    found_second_delimiter = True
                found = True
                break
        if not found:
            result[key] = {
                "result": "Fail",
                "parking_box_side": None,
                "delimiter_vertices": (delimiter_start, delimiter_end),
                "side_name": None,
            }
    found_required_delimters = found_first_delimiter and found_second_delimiter
    return result, found_required_delimters


def calculate_distance(point1, point2):
    """
    Calculate the Euclidean distance between two points in 2D space.

    Parameters:
    point1 (tuple): Coordinates of the first point (x1, y1).
    point2 (tuple): Coordinates of the second point (x2, y2).

    Returns:
    float: Distance between the two points.
    """
    return math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)


def find_shortest_distance(vertices):
    """
    Find the shortest distance between any pair of vertices.

    Parameters:
    vertices (list of tuple): List of coordinates for the vertices.

    Returns:
    float: Shortest distance between any two vertices.
    tuple: Pair of points with the shortest distance.
    """
    shortest_distance = float("inf")
    closest_pair = None

    # Loop over all pairs of points manually
    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            point1 = vertices[i]
            point2 = vertices[j]
            distance = calculate_distance(point1, point2)
            if distance < shortest_distance:
                shortest_distance = distance
                closest_pair = (point1, point2)

    return shortest_distance, closest_pair


# Function to transform ego coordinates to world coordinates
def transform_ego_to_world(ego_position, ego_orientation, cnn_slot):
    """
    Transform coordinates from the ego frame to the world frame for a single slot with 4 vertices.

    Parameters:
    - ego_position: (x, y) tuple, the position of the ego vehicle in the world frame.
    - ego_orientation: Orientation of the ego vehicle in radians (yaw angle).
    - cnn_slot: List of n vertices in the ego frame [(x1, y1), (x2, y2), (x3, y3), (x4, y4)].

    Returns:
    - Transformed slot: List of n vertices in the world frame.
    """
    tx, ty = ego_position
    transformed_slot = []

    for vertex in cnn_slot:
        # Extract x and y
        x, y = vertex

        # Apply rotation using trigonometric formulas
        x_rot = x * np.cos(ego_orientation) - y * np.sin(ego_orientation)
        y_rot = x * np.sin(ego_orientation) + y * np.cos(ego_orientation)

        # Apply translation
        world_vertex = (x_rot + tx, y_rot + ty)
        transformed_slot.append(world_vertex)

    return transformed_slot


# Function to calculate the point_distance
def point_distance(p1, p2):
    """Function to calculate point_distance"""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


# Function to calculate the minimum distance between all vertices of two polygons
def vertex_to_vertex_distance(poly1, poly2):
    """Function to calculate vertex_to_vertex_distance"""
    min_dist = float("inf")
    closest_points = None

    # Compare every vertex in poly1 to every vertex in poly2
    for p1 in poly1:
        for p2 in poly2:
            dist = point_distance(p1, p2)
            if dist < min_dist:
                min_dist = dist
                closest_points = (p1, p2)

    return min_dist, closest_points


def transform_coordinates_with_new_origin(old_origin, coordinates):
    """
    Transform coordinates from an old origin to a new origin.

    Parameters:
    - old_origin: Tuple (x_old, y_old), the coordinates of the old origin.
    - new_origin: Tuple (x_new, y_new), the coordinates of the new origin.
    - coordinates: List of tuples [(x1, y1), (x2, y2), ...], the coordinates to transform.

    Returns:
    - List of transformed coordinates.
    """
    new_origin = (0, 0)
    try:
        # Calculate the offset between old and new origins
        offset_x = new_origin[0] - old_origin[0]
        offset_y = new_origin[1] - old_origin[1]

        # Transform each coordinate
        transformed_coords = [(x + offset_x, y + offset_y) for x, y in coordinates]
        old_origin = tuple(old_origin)
        new_origin = tuple(new_origin)
    except Exception:

        return coordinates

    return transformed_coords


def process_data_initial(read_data: pd.DataFrame):
    """Process data for teststeps"""
    df = read_data.as_plain_df

    df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
    ap_state = df[SISignals.Columns.AP_STATE]
    ego_x = df[SISignals.Columns.EGO_POS_X]
    ego_y = df[SISignals.Columns.EGO_POS_Y]
    ego_yaw = df[SISignals.Columns.EGO_POS_YAW]
    # ego_x = df[SISignals.Columns.ODOESTIMATION_XPOSITION_M]
    # ego_y = df[SISignals.Columns.ODOESTIMATION_YPOSITION_M]
    # ego_yaw = df[SISignals.Columns.ODOESTIMATION_YANGLE]
    ap_time = df[SISignals.Columns.TIME].values.tolist()

    marker_filtered_df = pd.DataFrame()
    marker_single_df = pd.DataFrame()
    pb_signal_df = pd.DataFrame()

    pb_with_marker_match = {}
    markers_not_matched = {}
    ap_time = [round(i, 3) for i in ap_time]

    pb_count = len([x for x in list(df.columns) if SISignals.Columns.PB_SLOTCORDINATES_FRONTLEFT_X in x])
    # Combine all coordinates into a single list for each parking box
    for i in range(pb_count):
        pb_signal_df[SISignals.Columns.PARKBOX_COORDINATES_LIST.format(i)] = df[
            [x.format(i) for x in combined_list_for_all_pb]
        ].apply(lambda row: row.values.tolist(), axis=1)

    pb_col_with_values = [col for col in pb_signal_df.columns if not pb_signal_df[col].apply(is_all_zeros).all()]
    pb_signal_df = pb_signal_df[pb_col_with_values]
    df[SISignals.Columns.PARKING_SCENARIO_0]

    # Get how many delimiters signals are
    delimiter_count = len([x for x in list(df.columns) if "spaceMarkings_" in x and "array_x_0" in x])
    for delim_idx in range(delimiter_count):
        marker_single_df[SISignals.Columns.DELIMITERS_COORDINATES_LIST.format(delim_idx)] = df[
            [x.format(delim_idx) for x in gt_delimiter_length]
        ].apply(lambda row: row.values.tolist(), axis=1)

    mask_apstate_park_scan_in = (ap_state == ConstantsTrajpla.AP_AVG_ACTIVE_IN) | (
        ap_state == ConstantsTrajpla.AP_SCAN_IN
    )

    # Combine masks to get the final mask with valid values
    mask_final = marker_single_df.applymap(lambda x: any(i != 0 for i in x)).any(axis=1) & mask_apstate_park_scan_in

    marker_filtered_df = marker_single_df[mask_final]

    delim_col_with_values = [
        col for col in marker_filtered_df.columns if not marker_filtered_df[col].apply(is_all_zeros).all()
    ]
    filtered_timestamps = list(marker_filtered_df.index)

    # Create a dictionary to store the collected data
    collect_data_dict = {
        ts: {
            "pb": {},
            "ts": ap_time[list(df.index).index(ts)],
            "ap_state": ap_state.loc[ts],
            "markers": {},
            "intersection": {},
            "marker_match": {},
            "verdict": {},
            "ego_vehicle": [(ego_x.loc[ts], ego_y.loc[ts], ego_yaw.loc[ts])],
            "pb_width": {},
            "pb_with_marker_match": {},
            "delimiter_width_value": {},
            "parking_box_width_value": {},
            "overlap_percentage": {},
            "delim_width": {},
            "description": {},
        }
        for ts in filtered_timestamps
    }

    # Transform apstate to list
    ap_state = ap_state.values.tolist()

    for timestamp_val in filtered_timestamps:

        pb_with_marker_match.clear()
        markers_not_matched.clear()
        delims_from_ts = {x: [] for x in range(len(delim_col_with_values))}
        pb_from_ts = {x: [(0.0, 0.0)] * 4 for x in range(len(pb_col_with_values))}

        for i, col_name in enumerate(pb_col_with_values):
            pb_coords = pb_signal_df[col_name].loc[timestamp_val]
            vertices_pb = list(zip(pb_coords[::2], pb_coords[1::2]))
            pb_from_ts[i] = vertices_pb
        # Remove the parking box with all zeros
        pb_from_ts = {x: y for x, y in pb_from_ts.items() if all(val1 != 0 for val1, val2 in y)}
        for i, col_name in enumerate(delim_col_with_values):
            delim_coords = marker_single_df[col_name].loc[timestamp_val]
            delim_coords = transform_odo(
                delim_coords, ego_x.loc[timestamp_val], ego_y.loc[timestamp_val], ego_yaw.loc[timestamp_val]
            )

            delims_from_ts[i] = delim_coords
        delims_from_ts = {x: y for x, y in delims_from_ts.items() if all(val != 0 for val in y)}
        delims_from_ts = {x: y for x, y in delims_from_ts.items() if not is_horizontal(y)}
        if pb_from_ts:
            if len(delims_from_ts) >= 2:
                for parking_box_id in pb_from_ts.keys():
                    are_matched, markers, delimiter_coords = match_delim_to_pb(
                        delims_from_ts, pb_from_ts[parking_box_id]
                    )
                    if are_matched:
                        pb_with_marker_match[parking_box_id] = (markers, pb_from_ts[parking_box_id], delimiter_coords)
                    else:
                        markers_not_matched[parking_box_id] = markers
            else:

                park_box_id = list(pb_from_ts.keys())[0]
                vertices_pb = pb_from_ts[park_box_id]
                distances_between_pb = quadrilateral_distances(vertices_pb)
                AC_width_pb = float(f'{distances_between_pb.get("AC",0):.2f}')
                collect_data_dict[timestamp_val]["pb"][park_box_id] = [
                    vertices_pb[0],
                    vertices_pb[1],
                    vertices_pb[3],
                    vertices_pb[2],
                    vertices_pb[0],
                ]
                collect_data_dict[timestamp_val]["delim_width"][park_box_id] = "N/A"

                collect_data_dict[timestamp_val]["pb_width"][park_box_id] = AC_width_pb
                collect_data_dict[timestamp_val]["delimiter_width_value"][park_box_id] = "N/A"
                collect_data_dict[timestamp_val]["parking_box_width_value"][park_box_id] = AC_width_pb
                collect_data_dict[timestamp_val]["overlap_percentage"][park_box_id] = "N/A"
                collect_data_dict[timestamp_val]["intersection"][park_box_id] = [
                    (None, None),
                    (None, None),
                    (None, None),
                    (None, None),
                    (None, None),
                ]
                collect_data_dict[timestamp_val]["description"][
                    park_box_id
                ] = "No valid delimiters found for this parking box."
                collect_data_dict[timestamp_val]["markers"][park_box_id] = {
                    "id": "255_255",
                    "coordinates": [[(None, None), (None, None)]] * 2,
                }
                collect_data_dict[timestamp_val]["verdict"][park_box_id] = "Unknown"
        elif len(delims_from_ts) >= 2:
            collect_data_dict[timestamp_val]["marker_match"] = "marker_only"
            delimiter_without_pb = match_delim_to_delim(delims_from_ts, delims_from_ts)
            for delimiter in delimiter_without_pb:
                delimiter_coords = delimiter["delimiter_coords"]
                vertices = list(zip(delimiter_coords[::2], delimiter_coords[1::2]))
                distances = quadrilateral_distances(vertices)
                AC_width_delimiter_raw = distances.get("AC", 0)
                AC_width_delimiter = float(f"{AC_width_delimiter_raw:.1f}")
                park_box_id = 0
                collect_data_dict[timestamp_val]["intersection"][park_box_id] = [
                    (None, None),
                    (None, None),
                    (None, None),
                    (None, None),
                    (None, None),
                ]
                collect_data_dict[timestamp_val]["delim_width"][
                    park_box_id
                ] = f"Measured value: <b>{AC_width_delimiter}</b><br>Raw value: <b>{AC_width_delimiter_raw:.5f}</b>"
                collect_data_dict[timestamp_val]["delimiter_width_value"][park_box_id] = AC_width_delimiter
                collect_data_dict[timestamp_val]["parking_box_width_value"][park_box_id] = "N/A"
                collect_data_dict[timestamp_val]["overlap_percentage"][park_box_id] = "N/A"
                collect_data_dict[timestamp_val]["pb_width"][park_box_id] = "N/A"
                collect_data_dict[timestamp_val]["pb"][park_box_id] = [
                    (None, None),
                    (None, None),
                    (None, None),
                    (None, None),
                    (None, None),
                ]
                delimiter_ids = delimiter["id"].split("_")
                collect_data_dict[timestamp_val]["description"][
                    park_box_id
                ] = f"Space between delimiters {delimiter_ids[0]} and delimiter {delimiter_ids[1]}.<br>"

                collect_data_dict[timestamp_val]["markers"][park_box_id] = delimiter
        if pb_with_marker_match:

            collect_data_dict[timestamp_val]["marker_match"] = "marker_pb"
            collect_data_dict[timestamp_val]["pb_with_marker_match"] = pb_with_marker_match.copy()
            for park_box_id, matched_data in pb_with_marker_match.items():
                markers = matched_data[0]
                vertices_pb = matched_data[1]
                delimiter_coords = matched_data[2]
                distances_between_pb = quadrilateral_distances(vertices_pb)
                collect_data_dict[timestamp_val]["description"][
                    park_box_id
                ] = "No valid delimiters found for this parking box"
                collect_data_dict[timestamp_val]["pb"][park_box_id] = [
                    vertices_pb[0],
                    vertices_pb[1],
                    vertices_pb[3],
                    vertices_pb[2],
                    vertices_pb[0],
                ]
                vertices = list(zip(delimiter_coords[::2], delimiter_coords[1::2]))
                distances = quadrilateral_distances(vertices)

                AC_width_pb_raw = distances_between_pb.get("AC", 0)
                AC_width_pb = float(f"{AC_width_pb_raw:.1f}")
                AC_width_delimiter_raw = calculate_width_angular(delimiter_coords)
                AC_width_delimiter = float(f"{AC_width_delimiter_raw:.1f}")
                delimiter_1 = markers["coordinates"][0]
                delimiter_2 = markers["coordinates"][1]
                delimiter_coords_polygon = delimiter_1 + [delimiter_2[1]] + [delimiter_2[0]]
                slot_coords_polygon = [vertices_pb[0], vertices_pb[1], vertices_pb[3], vertices_pb[2]]
                try:

                    intersection, overlap_percentage = calculate_overlap(delimiter_coords_polygon, slot_coords_polygon)
                    intersection_coords = intersection_fig_trace_method(delimiter_coords_polygon, slot_coords_polygon)
                except Exception:
                    collect_data_dict[timestamp_val]["intersection"][park_box_id] = [
                        (None, None),
                        (None, None),
                        (None, None),
                        (None, None),
                        (None, None),
                    ]
                    collect_data_dict[timestamp_val]["description"][
                        park_box_id
                    ] = "No valid delimiters found for this parking box."
                    intersection_coords = [(None, None), (None, None), (None, None), (None, None), (None, None)]
                intersection_coords = [(x, y) for x, y in zip(*intersection_coords)]
                collect_data_dict[timestamp_val]["intersection"][park_box_id] = intersection_coords
                collect_data_dict[timestamp_val]["overlap_percentage"][park_box_id] = overlap_percentage
                collect_data_dict[timestamp_val]["delimiter_width_value"][park_box_id] = AC_width_delimiter
                collect_data_dict[timestamp_val]["parking_box_width_value"][park_box_id] = AC_width_pb
                # Check if the overlap is approximately 100%
                collect_data_dict[timestamp_val]["delim_width"][
                    park_box_id
                ] = f"Measured value: <b>{AC_width_delimiter}</b><br>Raw value: <b>{AC_width_delimiter_raw:.5f}</b>"
                collect_data_dict[timestamp_val]["pb_width"][
                    park_box_id
                ] = f"Measured value: <b>{AC_width_pb}</b><br>Raw value: <b>{AC_width_pb_raw:.5f}</b>"
                delimiter_ids = markers["id"].split("_")
                collect_data_dict[timestamp_val]["description"][
                    park_box_id
                ] = f"Parking box {park_box_id} was detected \
                in the space between delimiters {delimiter_ids[0]} and delimiter {delimiter_ids[1]}.<br>"
                collect_data_dict[timestamp_val]["markers"][park_box_id] = markers
    ts_to_be_removed = []

    for ts, val in collect_data_dict.items():

        if not val["pb"].keys():
            ts_to_be_removed.append(ts)

    collect_data_dict = {k: v for k, v in collect_data_dict.items() if k not in ts_to_be_removed}

    return collect_data_dict


# Function to normalize_angle_to_360
def normalize_angle_to_360(angle):
    """
    Normalize the angle to convert 359.60 or greater  to 360.
    If the angle is close to 360 (e.g., 359.99), it is rounded to 360.

    Parameters:
    - angle (float): The input angle.

    Returns:
    - float: Normalized angle.
    """
    if round(angle, 2) == 360 or angle >= 359.99 or angle >= 359.60:
        return 360
    return angle


def process_data_GT_without_scanned_pb(read_data: pd.DataFrame):
    """Process data for teststeps"""
    df = read_data.as_plain_df

    df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
    ap_state = df[SISignals.Columns.AP_STATE]
    ego_x = df[SISignals.Columns.EGO_POS_X]
    ego_y = df[SISignals.Columns.EGO_POS_Y]
    ego_yaw = df[SISignals.Columns.EGO_POS_YAW]
    ego_vehicle = df[[SISignals.Columns.EGO_POS_X, SISignals.Columns.EGO_POS_Y, SISignals.Columns.EGO_POS_YAW]]
    ap_time = df[SISignals.Columns.TIME].values.tolist()

    pb_signal_df = pd.DataFrame()

    ap_time = [round(i, 3) for i in ap_time]

    pb_count = len([x for x in list(df.columns) if SISignals.Columns.PB_SLOTCORDINATES_FRONTLEFT_X in x])
    # Combine all coordinates into a single list for each parking box
    for i in range(pb_count):
        pb_signal_df[SISignals.Columns.PARKBOX_COORDINATES_LIST.format(i)] = df[
            [x.format(i) for x in combined_list_for_all_pb]
        ].apply(lambda row: row.values.tolist(), axis=1)

    # pb_col_with_values = [col for col in pb_signal_df.columns if not pb_signal_df[col].apply(is_all_zeros).all()]
    # pb_signal_df = pb_signal_df[pb_col_with_values]

    gt_pb_count = len([x for x in list(df.columns) if SISignals.Columns.GT_SLOT_P_X_0 in x])
    gt_pb_signal_df = pd.DataFrame()

    # Combine all coordinates into a single list for each GT parking box
    for i in range(int(gt_pb_count)):
        gt_pb_signal_df[SISignals.Columns.GT_SLOT_COORDINATES_LIST.format(i)] = df[
            [
                f"gt_slot_p_x_0_{i}",
                f"gt_slot_p_y_0_{i}",
                f"gt_slot_p_x_1_{i}",
                f"gt_slot_p_y_1_{i}",
                f"gt_slot_p_x_2_{i}",
                f"gt_slot_p_y_2_{i}",
                f"gt_slot_p_x_3_{i}",
                f"gt_slot_p_y_3_{i}",
            ]
        ].apply(lambda row: row.values.tolist(), axis=1)

    # gt_pb_col_with_values = [
    #     col for col in gt_pb_signal_df.columns if not gt_pb_signal_df[col].apply(is_all_zeros).all()
    # ]
    # gt_pb_signal_df = gt_pb_signal_df[gt_pb_col_with_values]

    gt_pb_signal_df = gt_pb_signal_df.apply(
        lambda row: row.combine(
            ego_vehicle.apply(tuple, axis=1),
            lambda coord, ego_data: transform_odo_obj_shape(coord, ego_data[0], ego_data[1], ego_data[2]),
        )
    )

    mask_apstate_park_scan_in = (ap_state == ConstantsTrajpla.AP_AVG_ACTIVE_IN) | (
        ap_state == ConstantsTrajpla.AP_SCAN_IN
    )

    mask_final = pb_signal_df[mask_apstate_park_scan_in]

    filtered_timestamps = list(mask_final.index)
    # Create a dictionary to store the collected data
    collect_data_dict = {
        ts: {
            "pb": {},
            "pbs_gt": {},
            "ts": ap_time[list(df.index).index(ts)],
            "ap_state": ap_state.loc[ts],
            "verdict": {},
            "ego_vehicle": [(ego_x.loc[ts], ego_y.loc[ts], ego_yaw.loc[ts])],
            "description": {},
        }
        for ts in filtered_timestamps
    }

    # Transform apstate to list
    ap_state = ap_state.values.tolist()

    for timestamp_val in filtered_timestamps:

        pb_from_ts = {x: [(0.0, 0.0)] * 4 for x in range(len(pb_signal_df))}
        gt_pb_from_ts = {x: [(0.0, 0.0)] * 4 for x in range(len(gt_pb_signal_df))}
        for i, col_name in enumerate(pb_signal_df):
            pb_coords = pb_signal_df[col_name].loc[timestamp_val]
            vertices_pb = list(zip(pb_coords[::2], pb_coords[1::2]))
            pb_from_ts[i] = vertices_pb

        for i, col_name in enumerate(gt_pb_signal_df):
            gt_pb_coords = gt_pb_signal_df[col_name].loc[timestamp_val]
            vertices_gt_pb = list(zip(gt_pb_coords[::2], gt_pb_coords[1::2]))
            gt_pb_from_ts[i] = vertices_gt_pb

        park_box_id = list(pb_from_ts.keys())[0]
        vertices_pb = pb_from_ts[park_box_id]
        collect_data_dict[timestamp_val]["pb"][park_box_id] = [
            vertices_pb[0],
            vertices_pb[1],
            vertices_pb[3],
            vertices_pb[2],
            vertices_pb[0],
        ]
        gt_park_box_id = list(gt_pb_from_ts.keys())[0]
        vertices_gt_pb = gt_pb_from_ts[gt_park_box_id]
        collect_data_dict[timestamp_val]["pbs_gt"][gt_park_box_id] = [
            vertices_gt_pb[0],
            vertices_gt_pb[3],
            vertices_gt_pb[2],
            vertices_gt_pb[1],
            vertices_gt_pb[0],
        ]
        collect_data_dict[timestamp_val]["description"][park_box_id] = ""
        collect_data_dict[timestamp_val]["verdict"][park_box_id] = "Unknown"
    ts_to_be_removed = []

    for ts, val in collect_data_dict.items():

        if not val["pb"].keys():
            ts_to_be_removed.append(ts)

    collect_data_dict = {k: v for k, v in collect_data_dict.items() if k not in ts_to_be_removed}

    return collect_data_dict
