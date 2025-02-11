"""Helper file providing functionality used in the calculation of KPIs"""

from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.optimize import linear_sum_assignment
from shapely import Polygon, intersection

import pl_parking.common_ft_helper as fh

# intersection over union threshold
iou_th = 0.10  # [% * 100]

# TPR threshold
tpr_cars = 70  # [%]
position_accuracy_th = 5  # [m]


def associate_based_on_distance(pred_df, gt_df, threshold=8):
    """
    Associate the GT object with the PRED object using the Hungarian Algorithm.
    Will compute the distance between the centroids of the bounding boxes and store them in a distance matrix.
    Will use the Hungarian Algorithm to get the best association.
    Will output a pandas dataframe with (GT index, PRED index, distance between GT and PRED).
    """
    gt_start_index = gt_df.index.values[0]
    pred_start_index = pred_df.index.values[0]

    pred_boxes = [[[row[f"x{i}"], row[f"y{i}"]] for i in range(4)] for idx, row in pred_df.iterrows()]
    gt_boxes = [[[row[f"x{i}"], row[f"y{i}"]] for i in range(4)] for idx, row in gt_df.iterrows()]
    pred_centers = [[np.mean([pts[0] for pts in box]), np.mean([pts[1] for pts in box])] for box in pred_boxes]
    gt_centers = [[np.mean([pts[0] for pts in box]), np.mean([pts[1] for pts in box])] for box in gt_boxes]
    real_objects = np.array(gt_centers)
    detected_objects = np.array(pred_centers)

    # Step 1: Calculate pairwise distance matrix between real and detected objects
    distance_matrix = np.linalg.norm(real_objects[:, np.newaxis] - detected_objects, axis=2)

    # Step 2: Apply the distance threshold by masking out distances over the threshold
    threshold_matrix = distance_matrix.copy()
    threshold_matrix[threshold_matrix > threshold] = np.inf

    # Step 3: Handle infeasibility by replacing np.inf with a large value
    large_value = 1e6  # Large value to approximate 'infinite' cost
    threshold_matrix[np.isinf(threshold_matrix)] = large_value

    # Step 4: Use Hungarian Algorithm to find optimal assignment within threshold
    row_ind, col_ind = linear_sum_assignment(threshold_matrix)

    # Filter pairs that are within the threshold
    matches = []
    for r, c in zip(row_ind, col_ind):
        if distance_matrix[r, c] <= threshold:  # Check original distances within threshold
            matches.append((r, c))  # (real object index, detected object index)

    # Identify unmatched objects (misses and ghosts)
    # matched_real = {m[0] for m in matches}
    # matched_detected = {m[1] for m in matches}
    # missed_real = set(range(len(real_objects))) - matched_real
    # ghost_detections = set(range(len(detected_objects))) - matched_detected
    my_dict = [
        {"gt_idx": m[0] + gt_start_index, "pred_idx": m[1] + pred_start_index, "dist": distance_matrix[m[0], m[1]]}
        for m in matches
    ]
    return pd.DataFrame(my_dict)


def cast_to_optional_float(string_value: str) -> Optional[float]:
    """Casts a string to an Optional[float].

    Args:
        string_value: The string to cast.

    Returns:
        The float value if the string can be converted, otherwise None.
    """
    try:
        return float(string_value)
    except ValueError:
        return None


def generate_html_fraction(kpi_name: str, numerator: list, denominator: list) -> str:
    """
    Generate HTML code for KPI formula. Will output kpi_name = sum(numerator) / sum(denominator).
    :param kpi_name: The name of the KPI.
    :param numerator: A list with the variables contained by the nominator.
    :param denominator: A list with the variables contained by the denominator.
    :return: HTML string containing math ml for drawing the fraction.
    """
    html_string = '<math display="block">'
    html_string += f"<mi>{kpi_name}</mi> <mo>=</mo>"  # Define KPI =

    # Define the fraction
    html_string += "<mrow><mfrac>"

    # Define the numerator
    html_string += "<mrow>"
    for val in numerator:
        html_string += f"<mi>{val}</mi>"
        if val != numerator[-1]:
            html_string += "<mo>+</mo>"
    html_string += "</mrow>"

    # Define the denominator
    html_string += "<mrow>"
    for val in denominator:
        html_string += f"<mi>{val}</mi>"
        if val != denominator[-1]:
            html_string += "<mo>+</mo>"
    html_string += "</mrow>"

    # Close the tags
    html_string += "</mfrac></mrow>"
    html_string += "</math><p></p>"

    return html_string


def generate_html_description() -> str:
    """
    Custom function for generating an HTML string with the definition of the KPIs.
    :return: HTML string with the KPI formulas and definitions.
    """
    kpi_description = "<h3>Description</h3>"  # Title of the description
    kpi_formulas = ""  # Formulas for KPIs
    kpi_formulas += generate_html_fraction("Precision", ["TP"], ["TP", "FP"])
    kpi_formulas += generate_html_fraction("Recall", ["TP"], ["TP", "FN"])
    kpi_formulas += generate_html_fraction("TPR", ["TP"], ["TP", "FP", "FN"])
    kpi_formulas += generate_html_fraction("FPR", ["FP"], ["TP", "FP", "FN"])
    kpi_formulas += generate_html_fraction("FNR", ["FN"], ["TP", "FP", "FN"])
    kpi_legend = ""  # Definition
    kpi_legend += "<p>Precision - relevant instances among the retrieved instances</p>"
    kpi_legend += "<p>Recall - relevant instances that were retrieved</p>"
    kpi_legend += "<p>TPR - True Positive Rate</p>"
    kpi_legend += "<p>FPR - False Positive Rate</p>"
    kpi_legend += "<p>FNR - False Negative Rate</p>"
    kpi_legend += "<p>TP - Number of True Positive</p>"
    kpi_legend += "<p>FP - Number of False Positive</p>"
    kpi_legend += "<p>FN - Number of False Negative</p>"
    kpi_description += kpi_formulas
    kpi_description += kpi_legend

    return kpi_description


def convert_reader(df: pd.DataFrame) -> pd.DataFrame:
    """Convert TPF reader."""
    detection_list = []
    for _, row in df.iterrows():
        n = int(row["numberOfObjects"])
        for i in range(n):
            obj_dict = {
                "ts": int(row["sigTimestamp"]),
                "numObj": n,
                "id": int(row[("objects.id", i)]),
                "class": int(row[("objects.objectClass", i)]),
            }

            for j in range(4):  # There are 4 corner points
                obj_dict[f"x{j}"] = row[(f"objects.shape.points[{j}].position.x", i)]
                obj_dict[f"y{j}"] = row[(f"objects.shape.points[{j}].position.y", i)]

            detection_list.append(obj_dict)

    return pd.DataFrame(detection_list)


def convert_reader_all_frames(df: pd.DataFrame) -> pd.DataFrame:
    """Convert TPF reader. Store even the frames with no detections."""
    detection_list = []
    for _, row in df.iterrows():
        n = int(row["numberOfObjects"])
        if n == 0:
            obj_dict = {"ts": int(row["sigTimestamp"]), "numObj": 0, "id": 0, "class": 0}

            for j in range(4):  # There are 4 corner points
                obj_dict[f"x{j}"] = 0
                obj_dict[f"y{j}"] = 0
            detection_list.append(obj_dict)

        else:
            for i in range(n):
                obj_dict = {
                    "ts": int(row["sigTimestamp"]),
                    "numObj": n,
                    "id": int(row[("objects.id", i)]),
                    "class": int(row[("objects.objectClass", i)]),
                }

                for j in range(4):  # There are 4 corner points
                    obj_dict[f"x{j}"] = row[(f"objects.shape.points[{j}].position.x", i)]
                    obj_dict[f"y{j}"] = row[(f"objects.shape.points[{j}].position.y", i)]

                detection_list.append(obj_dict)

    return pd.DataFrame(detection_list)


def get_iou_shapely(gt_row, pred_row):
    """Get intersection over union between GT object and predicted object."""
    pts_pred = [[pred_row[f"x{i}"], pred_row[f"y{i}"]] for i in range(4)]
    pts_gt = [[gt_row[f"x{i}"], gt_row[f"y{i}"]] for i in range(4)]

    poly_pred = Polygon(pts_pred)
    poly_gt = Polygon(pts_gt)

    intersection_poly = intersection(poly_gt, poly_pred)
    union_poly = poly_gt.union(poly_pred)
    iou = intersection_poly.area / union_poly.area

    return iou


def compute_frame_kpi(gt_df, pred_df, ts):
    """Compute the KPIs for the current frame."""
    # Get the values for the current timestamp
    this_pred_df = pred_df[pred_df["ts"] == ts]
    this_gt_df = gt_df[gt_df["ts"] == ts]

    # Make sure proper data is used
    if this_pred_df.empty:
        num_pred_obj = 0
        association_df = pd.DataFrame([])
    else:
        if this_pred_df["numObj"].iloc[0] == 0:
            num_pred_obj = 0
            association_df = pd.DataFrame([])
        else:
            num_pred_obj = len(this_pred_df)
            association_df = associate_based_on_distance(gt_df=this_gt_df, pred_df=this_pred_df)

    # Compute TP, FP, FN
    number_of_pred_obj = num_pred_obj
    number_of_gt_obj = len(this_gt_df)
    number_of_associated_obj = len(association_df)

    # Compute KPIs #
    tp = number_of_associated_obj
    fp = number_of_pred_obj - number_of_associated_obj
    fn = number_of_gt_obj - number_of_associated_obj

    # Compute the rates
    if (tp + fp + fn) != 0:
        tpr = tp / (tp + fp + fn)
        fpr = fp / (tp + fp + fn)
        fnr = fn / (tp + fp + fn)
    else:
        tpr = 0
        fpr = 0
        fnr = 0

    # Compute a different metric
    if tp + fp > 0:
        precision = tp / (tp + fp)
    else:
        precision = 0
    if tp + fn > 0:
        recall = tp / (tp + fn)
    else:
        recall = 0

    kpi_dict = {
        "ts": ts,
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TPR": tpr * 100,
        "FPR": fpr * 100,
        "FNR": fnr * 100,
        "precision": precision * 100,
        "recall": recall * 100,
    }
    return kpi_dict


def generate_bar_chart_TPR(df: pd.DataFrame) -> go.Figure:
    """
    Draw a bar chart with TPR, FPR, FNR based on time.
    :param df: Pandas Data Frame with the KPI values for each time frame.
    :return: plot as graphical object.
    """
    fig = go.Figure()
    ms_time = (df["ts"] - df["ts"].iloc[0]) / 1000000

    ms_time_3dec = [f"{time:.3f}" for time in ms_time]

    ms_time_str = [str(time) for time in ms_time_3dec]
    red_color = "#e85741"
    blue_color = "#417ee8"
    green_color = "#18c586"
    fig.add_trace(go.Bar(x=ms_time_str, y=df["TPR"], marker_color=green_color, name="TPR"))
    fig.add_trace(go.Bar(x=ms_time_str, y=df["FPR"], marker_color=blue_color, name="FPR"))
    fig.add_trace(go.Bar(x=ms_time_str, y=df["FNR"], marker_color=red_color, name="FNR"))

    fig.update_layout(barmode="stack")
    fig.update_layout(bargap=0)
    fig.update_layout(bargroupgap=0)
    fig.update_yaxes(range=[0, 100])

    fig.update_layout(hovermode="x unified")

    fig["layout"]["yaxis"].update(title_text="KPI Value [%]")
    fig["layout"]["xaxis"].update(title_text="Time [s]")

    return fig


def generate_kpi_scenario() -> (go.Figure, str):
    """
    Generate a custom scene with Predicted and Ground Truth objects.
    In the scene there are 1 TP, 1 FP and 2 FN.
    This function is used for documenting how the KPIs work.
    """
    gt_bbox = np.array([(2, -3.7), (3.8, -3.6), (4, -7.8), (2.2, -7.8)])
    pred_bbox = np.array([(4, -2.7), (5.8, -2.6), (6, -6.8), (4.2, -6.8)])

    fig = go.Figure()
    # Draw a True Positive
    fig.add_trace(
        go.Scatter(
            x=[gt_bbox[i % 4][0] for i in range(5)],
            y=[gt_bbox[i % 4][1] for i in range(5)],
            name="GT 0",
            marker=dict(color="red"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[pred_bbox[i % 4][0] for i in range(5)],
            y=[pred_bbox[i % 4][1] for i in range(5)],
            name="PRED 0",
            marker=dict(color="blue"),
        )
    )
    # Draw a False Positive
    fig.add_trace(
        go.Scatter(
            x=[pred_bbox[i % 4][0] - 1.5 for i in range(5)],
            y=[pred_bbox[i % 4][1] + 12 for i in range(5)],
            name="PRED 1",
            marker=dict(color="aqua"),
        )
    )
    # Draw False Negative
    fig.add_trace(
        go.Scatter(
            x=[gt_bbox[i % 4][0] - 12 for i in range(5)],
            y=[gt_bbox[i % 4][1] - 4 for i in range(5)],
            name="GT 1",
            marker=dict(color="pink"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[gt_bbox[i % 4][0] - 14.5 for i in range(5)],
            y=[gt_bbox[i % 4][1] - 4 for i in range(5)],
            name="GT 2",
            marker=dict(color="pink"),
        )
    )
    # Draw the EGO Vehicle
    fig.add_trace(
        go.Scatter(
            x=[0],
            y=[0],
            name="EGO",
            legendgroup="EGO",
            marker=dict(color="green"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[-1, 3, 3, -1, -1],
            y=[1, 1, -1, -1, 1],
            name="EGO",
            legendgroup="EGO",
            marker=dict(color="green"),
        )
    )
    # Draw the distance between the center of the GT and the center of the PRED
    fig.add_trace(
        go.Scatter(
            x=[np.mean(gt_bbox[:, 0]), np.mean(pred_bbox[:, 0])],
            y=[np.mean(gt_bbox[:, 1]), np.mean(pred_bbox[:, 1])],
            name="DISTANCE",
            marker=dict(color="yellow"),
        )
    )
    # Update the size of the figure
    fig.update_layout(height=800, width=800, autosize=False)
    fig.update_yaxes(
        scaleanchor="x",
        scaleratio=1,
    )

    remark = (
        "If the distance(yellow) is lower than the ASSOCIATION_THRESHOLD, "
        "then the objects will be associated -> True Positive.<br>"
        "If the distance(yellow) is greated than the ASSOCIATION_THRESHOLD, "
        "then the GT 0(red) -> False Negative and PRED 0(blue) -> False Positive.<br>"
        "We assume the distance < ASSOCIATION_THRESHOLD -> True Positive.<br>"
        "GT 1(pink) is not associated to any PRED object -> False Negative.<br>"
        "GT 2(pink) is not associated to any PRED object -> False Negative.<br>"
        "PRED 1(aqua) is not associated to any GT object -> False Positive.<br>"
    )

    return fig, remark


def generate_kpi_custom_description() -> (go.Figure, str):
    """
    This function has documentation purposes.
    It is related to generate_kpi_scenario.
    It will generate a table with the KPIs for the custom scenario and a text with their interpretation.
    """
    # Generate the KPIs
    # Note: The KPI function was not run for this in order to save runtime
    ts = 0
    TP = 1
    FP = 1
    FN = 2
    TPR = TP / (TP + FP + FN) * 100
    FPR = FP / (TP + FP + FN) * 100
    FNR = FN / (TP + FP + FN) * 100
    Precision = TP / (TP + FP) * 100
    Recall = TP / (TP + FN) * 100

    kpi_dict = {
        "ts": ts,
        "TP": TP,
        "FP": FP,
        "FN": FN,
        "TPR": TPR,
        "FPR": FPR,
        "FNR": FNR,
        "Precision": Precision,
        "Recall": Recall,
    }
    kpi_df = pd.DataFrame([kpi_dict])
    fig = fh.build_html_table(kpi_df)

    remark = (
        "KPIs are computed for each frame and stored in a Pandas Data Frame.<br>"
        "When the results for all the frames are available, then average value for the all frames is given.<br>"
        "<b>True Positive Rate</b>(Accuracy) reflects how good the algorithm predicts a real detection.<br>"
        "<b>Precision</b> reflects how many Predicted objects are valid.<br>"
        "<b>Recall</b> reflects how many Real objects(GT) are detected.<br>"
        "An high Precision Score and low Recall Score means most of the detections are valid, "
        "but many real objects were not detected.<br>"
        "A low Precision Score and high Recall Score means most of the real objects were detected, "
        "but there are many False Positives.<br>"
    )
    return fig, remark


def build_html_table_graph(figure, table_remark="", table_title=""):
    """Constructs an HTML table from a DataFrame along with optional table remarks and title."""
    # Initialize the HTML string with line break and title
    html_string = "<br>"
    html_string += "<h4>" + table_title + "</h4>"

    # Convert DataFrame to HTML table
    if "plotly.graph_objs._figure.Figure" in str(type(figure)):
        fig = figure.to_html(full_html=False, include_plotlyjs=False)
    else:
        fig = figure
    table_html = f"<table><tbody><tr><td>{fig}</td><td>{table_remark}</td></tr></tbody></table> "

    # # Apply styling to the table headers and rows
    table_html = table_html.replace("<th>", '<th style ="background-color: #FFA500">')
    table_html = table_html.replace('<tr style="text-align: right;">', '<tr style="text-align: center;">')
    table_html = table_html.replace("<tr>", '<tr style="text-align: center;">')

    # Add table remark with styling

    table_html = "<div>" + table_html + "</div>"

    # Append the table HTML to the overall HTML string
    html_string += table_html

    return html_string


def angle_between_segments(p1, p2, q1, q2):
    """Compute the angle between P[p1, p2] and Q[q1, q2] segments."""
    # Vector a (segment p1 -> p2)
    a = np.array([p2[0] - p1[0], p2[1] - p1[1]])
    # Vector b (segment q1 -> q2)
    b = np.array([q2[0] - q1[0], q2[1] - q1[1]])

    # Dot product and magnitudes
    dot_product = np.dot(a, b)
    mag_a = np.linalg.norm(a)
    mag_b = np.linalg.norm(b)

    # Calculate the angle in radians and then convert to degrees
    angle_rad = np.arccos(dot_product / (mag_a * mag_b))
    angle_deg = np.degrees(angle_rad)

    return angle_rad, angle_deg


def rotate_bounding_box(points, angle_rad):
    """Rotate a bounding box given by the points with a given angle (in radians)."""
    # Calculate the centroid of the bounding box
    centroid = np.mean(points, axis=0)

    # Center the points around the origin
    centered_points = points - centroid

    # Define the rotation matrix
    rotation_matrix = np.array([[np.cos(angle_rad), -np.sin(angle_rad)], [np.sin(angle_rad), np.cos(angle_rad)]])

    # Rotate the points
    rotated_points = np.dot(centered_points, rotation_matrix)

    # Translate the points back to the original centroid
    rotated_points += centroid

    return rotated_points


def match_points_of_the_bounding_boxes(real_objects, detected_objects) -> list:
    """
    Return the indexes of the matched points for the bounding boxes.
    Return will be a list of (real object index, detected object index).
    """
    threshold = 10
    # Step 1: Calculate pairwise distance matrix between real and detected objects
    distance_matrix = np.linalg.norm(real_objects[:, np.newaxis] - detected_objects, axis=2)

    # Step 2: Apply the distance threshold by masking out distances over the threshold
    threshold_matrix = distance_matrix.copy()
    threshold_matrix[threshold_matrix > threshold] = np.inf

    # Step 3: Handle infeasibility by replacing np.inf with a large value
    large_value = 1e6  # Large value to approximate 'infinite' cost
    threshold_matrix[np.isinf(threshold_matrix)] = large_value

    # Step 4: Use Hungarian Algorithm to find optimal assignment within threshold
    row_ind, col_ind = linear_sum_assignment(threshold_matrix)

    # Filter pairs that are within the threshold
    matches = []
    for r, c in zip(row_ind, col_ind):
        if distance_matrix[r, c] <= threshold:  # Check original distances within threshold
            matches.append((r, c))  # (real object index, detected object index)

    return matches


def compute_accuracy(gt_df: pd.DataFrame, pred_df: pd.DataFrame) -> pd.DataFrame:
    """Compute the Position Accuracy, Orientation Accuracy and Shape Accuracy for each object from the current time frame."""
    kpi_list = []  # Store the dictionaries with the KPIs
    unique_ts = np.unique(pred_df["ts"])

    for ts in unique_ts:
        this_pred_df = pred_df[pred_df["ts"] == ts]
        this_gt_df = gt_df[gt_df["ts"] == ts]

        current_association_df = associate_based_on_distance(gt_df=this_gt_df, pred_df=this_pred_df, threshold=7)
        for _, row in current_association_df.iterrows():
            gt_idx = int(row["gt_idx"])
            pred_idx = int(row["pred_idx"])

            pred_obj = pred_df.iloc[pred_idx]
            gt_obj = gt_df.iloc[gt_idx]

            # Select the first 3 points from the bounding boxes (PRED and GT)
            p1 = [pred_obj["x0"], pred_obj["y0"]]
            p2 = [pred_obj["x1"], pred_obj["y1"]]
            p3 = [pred_obj["x2"], pred_obj["y2"]]
            q1 = [gt_obj["x0"], gt_obj["y0"]]
            q2 = [gt_obj["x1"], gt_obj["y1"]]
            q3 = [gt_obj["x2"], gt_obj["y2"]]

            # Make sure to compute the angle between the segments representing the width for both GT and PRED
            if np.linalg.norm(np.array(p1) - np.array(p2)) - np.linalg.norm(np.array(p2) - np.array(p3)) > 0:
                p1 = p2
                p2 = p3
            if np.linalg.norm(np.array(q1) - np.array(q2)) - np.linalg.norm(np.array(q2) - np.array(q3)) > 0:
                q1 = q2
                q2 = q3

            pred_bbox = np.array([[pred_obj[f"x{i}"], pred_obj[f"y{i}"]] for i in range(4)])
            gt_bbox = np.array([[gt_obj[f"x{i}"], gt_obj[f"y{i}"]] for i in range(4)])

            # Rotation
            # Note: The points are not associated, so the rotation may not be the orientation error
            rotation_rad, rotation_deg = angle_between_segments(p1, p2, q1, q2)
            # We want to have the smallest angle
            # If we get the big angle then compute the smallest one
            if rotation_deg > 90:
                rotation_deg = 180 - rotation_deg
            rotated_pred_bbox = rotate_bounding_box(pred_bbox, rotation_rad)

            # Translation
            dx, dy = (
                np.mean(gt_bbox[:, 0]) - np.mean(rotated_pred_bbox[:, 0]),
                np.mean(gt_bbox[:, 1]) - np.mean(rotated_pred_bbox[:, 1]),
            )
            translated_pred_bbox = np.array([(x + dx, y + dy) for x, y in rotated_pred_bbox])

            matches = match_points_of_the_bounding_boxes(gt_bbox, translated_pred_bbox)

            # Run Point-to-Point error
            p2p_error = 0
            for match in matches:
                gt_index = match[0]
                pred_index = match[1]

                p2p_error += np.linalg.norm(gt_bbox[gt_index] - pred_bbox[pred_index])
            p2p_error = p2p_error / 4

            # Run the Position Accuracy
            # Get the index of the closest GT point from origin
            closest_gt_idx = min(enumerate(np.linalg.norm(p) for p in gt_bbox), key=lambda x: x[1])[0]
            # Match the GT point to the Predicted point
            closest_pred_idx = matches[closest_gt_idx][1]
            position_accuracy = np.linalg.norm(gt_bbox[closest_gt_idx] - pred_bbox[closest_pred_idx])

            # Run the Shape Accuracy
            poly_pred = Polygon(translated_pred_bbox)
            poly_gt = Polygon(gt_bbox)

            intersection_poly = intersection(poly_gt, poly_pred)
            union_poly = poly_gt.union(poly_pred)
            shape_erorr = intersection_poly.area / union_poly.area  # Intersection over Union

            kpi_dict = {
                "ts": ts,
                "gt_idx": gt_idx,
                "pred_idx": pred_idx,
                "Point-to-Point error": p2p_error,
                "Position Accuracy": position_accuracy,
                "Orientation Accuracy": rotation_deg,
                "Shape Accuracy": shape_erorr,
            }
            kpi_list.append(kpi_dict)

    return pd.DataFrame(kpi_list)


def draw_timeframe_association(gt_df, pred_df, association_df, ts):
    """Plot a time frame and draw lines between associated objects,"""
    fig = go.Figure()

    for idx, row in gt_df[gt_df["ts"] == ts].iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row[f"x{i % 4}"] for i in range(0, 5)],
                y=[row[f"y{i % 4}"] for i in range(0, 5)],
                marker=dict(color="red"),
                name="GT " + str(idx),
            )
        )

    for idx, row in pred_df[pred_df["ts"] == ts].iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row[f"x{i % 4}"] for i in range(0, 5)],
                y=[row[f"y{i % 4}"] for i in range(0, 5)],
                marker=dict(color="blue"),
                name="PRED " + str(idx),
            )
        )

    # Draw associations
    for _, row in association_df.iterrows():
        pred_row = pred_df.iloc[int(row["pred_idx"])]
        pred_center_x, pred_center_y = [
            np.mean([pred_row[f"x{i}"] for i in range(4)]),
            np.mean([pred_row[f"y{i}"] for i in range(4)]),
        ]
        gt_row = gt_df.iloc[int(row["gt_idx"])]
        gt_center_x, gt_center_y = [
            np.mean([gt_row[f"x{i}"] for i in range(4)]),
            np.mean([gt_row[f"y{i}"] for i in range(4)]),
        ]

        fig.add_trace(
            go.Scatter(
                x=[pred_center_x, gt_center_x],
                y=[pred_center_y, gt_center_y],
                name="Association",
                legendgroup="Association",
                marker=dict(color="yellow"),
            )
        )
    fig.update_layout(height=600, width=600, autosize=False)
    fig.update_yaxes(
        scaleanchor="x",
        scaleratio=1,
    )
    return fig


def generate_accuracy_kpi_description(gt_df, pred_df):
    """Generate a step by step explanation of how the Position Accuracy is calculated."""
    ts = np.unique(pred_df["ts"])[0]

    # Create a subplot figure with 3 rows and 2 columns
    fig = make_subplots(
        rows=2,
        cols=3,
        subplot_titles=(
            "Select a frame and associate objects",
            "Select an associated pair",
            "Rotate the detection and get the<br>" "Orientation Accuracy",
            "Translate the detection<br>" "and associate GT and PRED points<br>" "Compute the Shape Accuracy",
            "Compute the Euclidean Distance for the<br>" "associated points and get the Point-to-Point error",
            "Find the closesd GT point to the origin and<br>"
            "it's associated PRED point and<br>"
            "compute the Position Accuracy",
        ),
    )

    # Draw the timeframe
    this_gt_df = gt_df[gt_df["ts"] == ts]
    this_pred_df = pred_df[pred_df["ts"] == ts]
    this_association_df = associate_based_on_distance(gt_df=this_gt_df, pred_df=this_pred_df, threshold=8)
    timeframe_fig = draw_timeframe_association(gt_df=gt_df, pred_df=pred_df, association_df=this_association_df, ts=ts)

    timeframe_fig.update_yaxes(
        scaleanchor="x",
        scaleratio=1,
    )

    # Select the first association
    gt_idx = int(this_association_df["gt_idx"].iloc[0])
    pred_idx = int(this_association_df["pred_idx"].iloc[0])

    pred_obj = pred_df.iloc[pred_idx]
    gt_obj = gt_df.iloc[gt_idx]

    pred_bbox = np.array([[pred_obj[f"x{i}"], pred_obj[f"y{i}"]] for i in range(4)])
    gt_bbox = np.array([[gt_obj[f"x{i}"], gt_obj[f"y{i}"]] for i in range(4)])

    pair_fig = go.Figure()
    pair_fig.add_trace(
        go.Scatter(
            x=[pred_bbox[i % 4, 0] for i in range(5)],
            y=[pred_bbox[i % 4, 1] for i in range(5)],
            name="Pred Box",
            marker=dict(color="blue"),
        )
    )
    pair_fig.add_trace(
        go.Scatter(
            x=[gt_bbox[i % 4, 0] for i in range(5)],
            y=[gt_bbox[i % 4, 1] for i in range(5)],
            name="GT Box",
            marker=dict(color="red"),
        )
    )
    pair_fig.update_yaxes(
        scaleanchor="x",
        scaleratio=1,
    )

    # Rotate the detection
    p1 = [pred_obj["x0"], pred_obj["y0"]]
    p2 = [pred_obj["x1"], pred_obj["y1"]]
    p3 = [pred_obj["x2"], pred_obj["y2"]]
    q1 = [gt_obj["x0"], gt_obj["y0"]]
    q2 = [gt_obj["x1"], gt_obj["y1"]]
    q3 = [gt_obj["x2"], gt_obj["y2"]]

    # Make sure to compute the angle between the segments representing the width for both GT and PRED
    if np.linalg.norm(np.array(p1) - np.array(p2)) - np.linalg.norm(np.array(p2) - np.array(p3)) > 0:
        p1 = p2
        p2 = p3
    if np.linalg.norm(np.array(q1) - np.array(q2)) - np.linalg.norm(np.array(q2) - np.array(q3)) > 0:
        q1 = q2
        q2 = q3

    rotation_rad, rotation_deg = angle_between_segments(p1, p2, q1, q2)
    rotated_pred_bbox = rotate_bounding_box(pred_bbox, rotation_rad)
    rotation_fig = go.Figure()
    rotation_fig.add_trace(
        go.Scatter(
            x=[pred_bbox[i % 4, 0] for i in range(5)],
            y=[pred_bbox[i % 4, 1] for i in range(5)],
            name="Pred Box",
            marker=dict(color="blue"),
        )
    )
    rotation_fig.add_trace(
        go.Scatter(
            x=[gt_bbox[i % 4, 0] for i in range(5)],
            y=[gt_bbox[i % 4, 1] for i in range(5)],
            name="GT Box",
            marker=dict(color="red"),
        )
    )
    rotation_fig.add_trace(
        go.Scatter(
            x=[rotated_pred_bbox[i % 4, 0] for i in range(5)],
            y=[rotated_pred_bbox[i % 4, 1] for i in range(5)],
            name="Rotated box",
            marker=dict(color="green"),
        )
    )
    rotation_fig.update_yaxes(
        scaleanchor="x",
        scaleratio=1,
    )

    # Translate the detection
    dx, dy = (
        np.mean(gt_bbox[:, 0]) - np.mean(rotated_pred_bbox[:, 0]),
        np.mean(gt_bbox[:, 1]) - np.mean(rotated_pred_bbox[:, 1]),
    )
    translated_pred_bbox = np.array([(x + dx, y + dy) for x, y in rotated_pred_bbox])

    translation_fig = go.Figure()
    translation_fig.add_trace(
        go.Scatter(
            x=[pred_bbox[i % 4, 0] for i in range(5)],
            y=[pred_bbox[i % 4, 1] for i in range(5)],
            name="Pred Box",
            marker=dict(color="blue"),
        )
    )
    translation_fig.add_trace(
        go.Scatter(
            x=[gt_bbox[i % 4, 0] for i in range(5)],
            y=[gt_bbox[i % 4, 1] for i in range(5)],
            name="GT Box",
            marker=dict(color="red"),
        )
    )
    translation_fig.add_trace(
        go.Scatter(
            x=[translated_pred_bbox[i % 4, 0] for i in range(5)],
            y=[translated_pred_bbox[i % 4, 1] for i in range(5)],
            name="Translated box",
            marker=dict(color="green"),
        )
    )
    translation_fig.update_yaxes(
        scaleanchor="x",
        scaleratio=1,
    )

    # Associate Points
    matches = match_points_of_the_bounding_boxes(gt_bbox, translated_pred_bbox)

    pts_fig = go.Figure()
    pts_fig.add_trace(
        go.Scatter(
            x=[pred_bbox[i % 4, 0] for i in range(5)],
            y=[pred_bbox[i % 4, 1] for i in range(5)],
            name="Pred Box",
            marker=dict(color="blue"),
        )
    )
    pts_fig.add_trace(
        go.Scatter(
            x=[gt_bbox[i % 4, 0] for i in range(5)],
            y=[gt_bbox[i % 4, 1] for i in range(5)],
            name="GT Box",
            marker=dict(color="red"),
        )
    )
    for i in range(4):
        pts_fig.add_trace(
            go.Scatter(
                # box [matches [match_idx] [gt/pred box - 0/1]] [x/y - 0/1]
                x=[gt_bbox[matches[i][0]][0], pred_bbox[matches[i][0]][0]],
                y=[gt_bbox[matches[i][0]][1], pred_bbox[matches[i][0]][1]],
                name="P2P Error",
                marker=dict(color="yellow"),
            )
        )
    pts_fig.update_yaxes(
        scaleanchor="x",
        scaleratio=1,
    )

    # Compute the position accuracy
    closest_gt_idx = min(enumerate(np.linalg.norm(p) for p in gt_bbox), key=lambda x: x[1])[0]
    # Match the GT point to the Predicted point
    closest_pred_idx = matches[closest_gt_idx][1]

    positon_accuracy_fig = go.Figure()
    positon_accuracy_fig.add_trace(
        go.Scatter(
            x=[pred_bbox[i % 4, 0] for i in range(5)],
            y=[pred_bbox[i % 4, 1] for i in range(5)],
            name="Pred Box",
            marker=dict(color="blue"),
        )
    )

    positon_accuracy_fig.add_trace(
        go.Scatter(
            x=[gt_bbox[i % 4, 0] for i in range(5)],
            y=[gt_bbox[i % 4, 1] for i in range(5)],
            name="GT Box",
            marker=dict(color="red"),
        )
    )
    positon_accuracy_fig.add_trace(
        go.Scatter(
            # box [matches [match_idx] [gt/pred box - 0/1]] [x/y - 0/1]
            x=[gt_bbox[closest_gt_idx][0], pred_bbox[closest_pred_idx][0]],
            y=[gt_bbox[closest_gt_idx][1], pred_bbox[closest_pred_idx][1]],
            name="Position Accuracy",
            marker=dict(color="yellow"),
        )
    )
    positon_accuracy_fig.update_yaxes(
        scaleanchor="x",
        scaleratio=1,
    )

    # Row 1, Col 1
    for trace in timeframe_fig.data:
        fig.add_trace(trace, row=1, col=1)
    # Row 1, Col 2
    for trace in pair_fig.data:
        fig.add_trace(trace, row=1, col=2)
    # Row 2, Col 1
    for trace in rotation_fig.data:
        fig.add_trace(trace, row=1, col=3)
    # Row 2, Col 2
    for trace in translation_fig.data:
        fig.add_trace(trace, row=2, col=1)
    # Row 3, Col 1
    for trace in pts_fig.data:
        fig.add_trace(trace, row=2, col=2)
    # Row 3, Col 2
    for trace in positon_accuracy_fig.data:
        fig.add_trace(trace, row=2, col=3)

    # Adjust the layout
    fig.update_layout(height=800, width=1200, title_text="Step by step KPIs")
    fig.update_layout(showlegend=False)

    return fig
