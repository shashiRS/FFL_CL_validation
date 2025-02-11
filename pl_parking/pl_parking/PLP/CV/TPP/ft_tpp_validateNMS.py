"""TestCases checking the maximum number of output detections of TPP."""

import logging
import math
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from shapely import Polygon
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.CV.TPP.constants as ct

# import pl_parking.PLP.CV.TPP.tpp_signals_r4 as tpp_reader_r4
import pl_parking.PLP.CV.TPP.ft_helper as tpp_reader_r4
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, rep

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

NMS_IOU_TH = 0.01
TPP_NMS = "TPP_NMS"
example_obj = tpp_reader_r4.TPPSignals()


def check_signal_availability(signal_definition, required_signal: str, list_of_available_signals: list) -> dict:
    """
    Check if the required signal is available in the current recording.
    :param signal_definition: The object with the signal definition
    :param required_signal: The name of the required signal.
    :param list_of_available_signals: The list with the available signals.
    :return: False if any checks fails, True otherwise.
    """
    signal_dict = {
        "ColumnName": required_signal,
        "SignalName": signal_definition.get_properties()[required_signal][0],
    }
    if required_signal not in list_of_available_signals:
        signal_dict["Availability"] = "Not Available"
    else:
        signal_dict["Availability"] = "Available"

    return signal_dict


# TODO: Refactor to be used for all types of signals
def check_required_signals(list_of_available_signals: list) -> pd.DataFrame:
    """
    Check if the signals have been successfully stored in the reader DataFrame.
    :param list_of_available_signals: The list with the available signals.
    :return: DataFrame with the name of the signals and their availability.
    """
    signal_availability = []  # List of the signals that are required and their availability
    sig = tpp_reader_r4.TPPSignals.Columns  # The strings for the signals

    # Front instance
    signal_availability.append(check_signal_availability(example_obj, sig.NUM_CUBOID_FRONT, list_of_available_signals))
    signal_availability.append(check_signal_availability(example_obj, sig.NUM_BBOX_FRONT, list_of_available_signals))
    signal_availability.append(
        check_signal_availability(example_obj, sig.SIGTIMESTAMP_FRONT, list_of_available_signals)
    )
    signal_availability.append(
        check_signal_availability(example_obj, sig.SIGCYCLECOUNTER_FRONT, list_of_available_signals)
    )

    # Left instance
    signal_availability.append(check_signal_availability(example_obj, sig.NUM_CUBOID_LEFT, list_of_available_signals))
    signal_availability.append(check_signal_availability(example_obj, sig.NUM_BBOX_LEFT, list_of_available_signals))
    signal_availability.append(check_signal_availability(example_obj, sig.SIGTIMESTAMP_LEFT, list_of_available_signals))
    signal_availability.append(
        check_signal_availability(example_obj, sig.SIGCYCLECOUNTER_LEFT, list_of_available_signals)
    )

    # Rear instance
    signal_availability.append(check_signal_availability(example_obj, sig.NUM_CUBOID_REAR, list_of_available_signals))
    signal_availability.append(check_signal_availability(example_obj, sig.NUM_BBOX_REAR, list_of_available_signals))
    signal_availability.append(check_signal_availability(example_obj, sig.SIGTIMESTAMP_REAR, list_of_available_signals))
    signal_availability.append(
        check_signal_availability(example_obj, sig.SIGCYCLECOUNTER_REAR, list_of_available_signals)
    )

    # Right instance
    signal_availability.append(check_signal_availability(example_obj, sig.NUM_CUBOID_RIGHT, list_of_available_signals))
    signal_availability.append(check_signal_availability(example_obj, sig.NUM_BBOX_RIGHT, list_of_available_signals))
    signal_availability.append(
        check_signal_availability(example_obj, sig.SIGTIMESTAMP_RIGHT, list_of_available_signals)
    )
    signal_availability.append(
        check_signal_availability(example_obj, sig.SIGCYCLECOUNTER_RIGHT, list_of_available_signals)
    )

    # Generate a data frame with the status of the signals
    required_signals_df = pd.DataFrame(signal_availability)

    return required_signals_df


def get_polygon(length: float, width: float, yaw: float, center_x: float, center_y: float):
    """Transform the trafic participant into a polygon (bounding box on the ground)."""
    # length = row[(f"cuboidLength{self.camera_strings[camera]}", i)]
    # width = row[(f"cuboidWidth{self.camera_strings[camera]}", i)]
    # yaw = row[(f"cuboidYaw{self.camera_strings[camera]}", i)]
    cos_yaw = math.cos(yaw)
    sin_yaw = math.sin(yaw)

    length_2 = length * 0.5
    width_2 = width * 0.5
    pnt0_x = center_x + length_2 * cos_yaw - width_2 * sin_yaw
    pnt0_y = center_y + length_2 * sin_yaw + width_2 * cos_yaw
    pnt1_x = center_x - length_2 * cos_yaw - width_2 * sin_yaw
    pnt1_y = center_y - length_2 * sin_yaw + width_2 * cos_yaw
    pnt2_x = center_x - length_2 * cos_yaw + width_2 * sin_yaw
    pnt2_y = center_y - length_2 * sin_yaw - width_2 * cos_yaw
    pnt3_x = center_x + length_2 * cos_yaw + width_2 * sin_yaw
    pnt3_y = center_y + length_2 * sin_yaw - width_2 * cos_yaw

    polygon = [
        [pnt0_x, pnt0_y],
        [pnt1_x, pnt1_y],
        [pnt2_x, pnt2_y],
        [pnt3_x, pnt3_y],
    ]
    return Polygon(polygon)


def are_objects_overlapping(
    reader: pd.DataFrame,
    number_of_objects_signal: str,
    timestamp_signal: str,
    length_signal: str,
    width_signal: str,
    yaw_signal: str,
    center_x_signal: str,
    center_y_signal: str,
) -> (str, str, list):
    """
    Validate the number of objects for an instance of the camera and generate a report.
    The number of objects should be from 0 to TPP_MAX_NUMBER_OF_DETECTIONS.
    test_result: PASS/FAIL.
    description: The status of the signal.
    list_of_errors: Usefully data about the errors found. Empty list if no errors founds.
    :param reader: DataFrame containing the signals read from the recording.
    :param number_of_objects_signal: The signal containing the number of objects.
    :param timestamp_signal: The signal containing the timestamp.
    :param length_signal: The signal containing the length.
    :param width_signal: The signal containing the width.
    :param yaw_signal: The signal containing the yaw.
    :param center_x_signal: The signal containing the center_x.
    :param center_y_signal: The signal containing the center_y.
    :return: (test_result, description, list_of_errors)
    """
    available_signals = reader.columns
    test_result = fc.PASS
    description = "The evaluation of the signal is <b>PASSED</b>."
    list_of_errors = []

    if (
        number_of_objects_signal in available_signals
        and timestamp_signal in available_signals
        and (length_signal, 0) in available_signals
        and (width_signal, 0) in available_signals
        and (yaw_signal, 0) in available_signals
        and (center_x_signal, 0) in available_signals
        and (center_y_signal, 0) in available_signals
    ):
        # Compute IoU for 2 different detections on the same frame
        for _, row in reader.iterrows():
            number_of_objects = int(row[number_of_objects_signal])
            for idx_1 in range(number_of_objects):
                idx_2 = idx_1 + 1
                # for idx_2 in range(number_of_objects):
                while idx_2 < number_of_objects:
                    # if idx_1 != idx_2:
                    poly_1 = get_polygon(
                        length=row[(length_signal, idx_1)],
                        width=row[(width_signal, idx_1)],
                        yaw=row[(yaw_signal, idx_1)],
                        center_x=row[(center_x_signal, idx_1)],
                        center_y=row[(center_y_signal, idx_1)],
                    )
                    poly_2 = get_polygon(
                        length=row[(length_signal, idx_2)],
                        width=row[(width_signal, idx_2)],
                        yaw=row[(yaw_signal, idx_2)],
                        center_x=row[(center_x_signal, idx_2)],
                        center_y=row[(center_y_signal, idx_2)],
                    )
                    poly_intersection = poly_1.intersection(poly_2)
                    poly_union = poly_1.union(poly_2)
                    poly_iou = poly_intersection.area / poly_union.area

                    if poly_iou > NMS_IOU_TH:
                        error_dict = {
                            "ts": int(row[timestamp_signal]),
                            "index_1": idx_1,
                            "index_2": idx_2,
                            "value": poly_iou,
                            "description": "detections are overlapping",
                        }
                        list_of_errors.append(error_dict)
                        if test_result != fc.FAIL:
                            description = " ".join(
                                f"The evaluation is <b>FAILED</b> at timestamp {error_dict['ts']} for objects "
                                f"{error_dict['index_1']} and {error_dict['index_2']} with IOU value of "
                                f"{error_dict['value']} ({error_dict['description']}).".split()
                            )
                        test_result = fc.FAIL
                    idx_2 += 1
    else:
        test_result = fc.INPUT_MISSING
        description = " ".join("Signals <b>not evaluated</b> because they are not available.".split())

    return test_result, description, list_of_errors


def draw_timeframe(
    reader: pd.DataFrame,
    number_of_objects_signal: str,
    length_signal: str,
    width_signal: str,
    yaw_signal: str,
    center_x_signal: str,
    center_y_signal: str,
    class_signal: str,
) -> go.Figure:
    """Convert the detections to bounding boxes for a given timestamp and draw them."""
    num_cuboids = reader[number_of_objects_signal].astype("int64")
    class_type_names = {val: key for key, val in ct.CuboidClassTypes.items()}

    fig = go.Figure()
    for idx in range(num_cuboids):
        center_x = reader[(center_x_signal, idx)]
        center_y = reader[(center_y_signal, idx)]
        length = reader[(length_signal, idx)]
        width = reader[(width_signal, idx)]
        yaw = reader[(yaw_signal, idx)]
        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)
        class_type = int(reader[(class_signal, idx)])
        mapped_class_types = class_type_names[class_type]

        length_2 = length * 0.5
        width_2 = width * 0.5
        pnt0_x = center_x + length_2 * cos_yaw - width_2 * sin_yaw
        pnt0_y = center_y + length_2 * sin_yaw + width_2 * cos_yaw
        pnt1_x = center_x - length_2 * cos_yaw - width_2 * sin_yaw
        pnt1_y = center_y - length_2 * sin_yaw + width_2 * cos_yaw
        pnt2_x = center_x - length_2 * cos_yaw + width_2 * sin_yaw
        pnt2_y = center_y - length_2 * sin_yaw - width_2 * cos_yaw
        pnt3_x = center_x + length_2 * cos_yaw + width_2 * sin_yaw
        pnt3_y = center_y + length_2 * sin_yaw - width_2 * cos_yaw

        polygon = [
            [pnt0_x, pnt0_y],
            [pnt1_x, pnt1_y],
            [pnt2_x, pnt2_y],
            [pnt3_x, pnt3_y],
        ]
        fig.add_trace(
            go.Scatter(
                x=[polygon[i % 4][0] for i in range(5)],
                y=[polygon[i % 4][1] for i in range(5)],
                name=mapped_class_types + " " + str(idx),
            )
        )
    return fig


@teststep_definition(
    step_number=1,
    name="TPP Non Maximum Suppression",
    description="Check if objects are overlapping.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(TPP_NMS, tpp_reader_r4.TPPSignals)
class TestNonMaximumSuppressionTestStep(TestStep):
    """Test step definition."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test-step."""
        super().__init__()
        self.sig_sum = None

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        reader = self.readers[TPP_NMS]
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        signal_summary = {}
        plot_titles, plots, remarks = rep([], 3)

        sig = tpp_reader_r4.TPPSignals.Columns  # The strings for the signals

        reader = reader.iloc[10:]

        # Validate the front instance of the camera
        test_result_front, description_front, list_of_errors_front = are_objects_overlapping(
            reader,
            sig.NUM_CUBOID_FRONT,
            sig.SIGTIMESTAMP_FRONT,
            sig.CUBOID_LENGTH_FRONT,
            sig.CUBOID_WIDTH_FRONT,
            sig.CUBOID_YAW_FRONT,
            sig.CUBOID_CENTERX_FRONT,
            sig.CUBOID_CENTERY_FRONT,
        )
        # Validate the rear instance of the camera
        test_result_rear, description_rear, list_of_errors_rear = are_objects_overlapping(
            reader,
            sig.NUM_CUBOID_REAR,
            sig.SIGTIMESTAMP_REAR,
            sig.CUBOID_LENGTH_REAR,
            sig.CUBOID_WIDTH_REAR,
            sig.CUBOID_YAW_REAR,
            sig.CUBOID_CENTERX_REAR,
            sig.CUBOID_CENTERY_REAR,
        )
        # Validate the left instance of the camera
        test_result_left, description_left, list_of_errors_left = are_objects_overlapping(
            reader,
            sig.NUM_CUBOID_LEFT,
            sig.SIGTIMESTAMP_LEFT,
            sig.CUBOID_LENGTH_LEFT,
            sig.CUBOID_WIDTH_LEFT,
            sig.CUBOID_YAW_LEFT,
            sig.CUBOID_CENTERX_LEFT,
            sig.CUBOID_CENTERY_LEFT,
        )
        # Validate the right instance of the camera
        test_result_right, description_right, list_of_errors_right = are_objects_overlapping(
            reader,
            sig.NUM_CUBOID_RIGHT,
            sig.SIGTIMESTAMP_RIGHT,
            sig.CUBOID_LENGTH_RIGHT,
            sig.CUBOID_WIDTH_RIGHT,
            sig.CUBOID_YAW_RIGHT,
            sig.CUBOID_CENTERX_RIGHT,
            sig.CUBOID_CENTERY_RIGHT,
        )

        # Generate the status of each instance
        signal_summary[example_obj.get_properties()[sig.NUM_CUBOID_FRONT][0]] = description_front
        signal_summary[example_obj.get_properties()[sig.NUM_CUBOID_REAR][0]] = description_rear
        signal_summary[example_obj.get_properties()[sig.NUM_CUBOID_LEFT][0]] = description_left
        signal_summary[example_obj.get_properties()[sig.NUM_CUBOID_RIGHT][0]] = description_right

        remark = "Objects shall not overlap."
        self.sig_sum = fh.convert_dict_to_pandas(
            signal_summary=signal_summary,
            table_remark=remark,
        )
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        # Check the availability of the required signals
        available_signals = list(reader.columns)
        required_signals_df = check_required_signals(available_signals)
        unavailable_signals_df = required_signals_df[required_signals_df["Availability"] == "Not Available"]
        if not unavailable_signals_df.empty:
            remark = (
                "Signals required to perform the test. If one signal is not available for an instance"
                " of the camera, the test will not be performed for that instance."
            )
            title = "List of unavailable signals"
            self.sig_sum = fh.build_html_table(unavailable_signals_df, remark, title)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")

        if (
            test_result_front == fc.PASS
            and test_result_rear == fc.PASS
            and test_result_left == fc.PASS
            and test_result_right == fc.PASS
        ):
            test_result = fc.PASS
        elif (
            test_result_front == fc.NOT_ASSESSED
            or test_result_rear == fc.NOT_ASSESSED
            or test_result_left == fc.NOT_ASSESSED
            or test_result_right == fc.NOT_ASSESSED
        ):
            test_result = fc.NOT_ASSESSED
        else:
            test_result = fc.FAIL

        # In case of error on an instance, plot the number of objects and the errors
        if test_result_front == fc.FAIL:
            # Store the errors in a dataframe and make sure there are no duplicates
            front_errors_df = pd.DataFrame(list_of_errors_front).drop_duplicates()
            # Store the timestamp and the number of cuboids for a specific camera
            front_reader = reader[[sig.SIGTIMESTAMP_FRONT, sig.NUM_CUBOID_FRONT]].drop_duplicates()
            ts = front_errors_df["ts"].iloc[0]
            # Get the first frame with errors
            front_timeframe_df = reader[reader[sig.SIGTIMESTAMP_FRONT] == ts].iloc[0]

            # Draw a bar chart with the number of cuboids and number of overlapping objects
            fig_front = go.Figure()
            # Draw the number of objects
            fig_front.add_trace(
                go.Bar(
                    x=front_reader[sig.SIGTIMESTAMP_FRONT],
                    y=front_reader[sig.NUM_CUBOID_FRONT],
                    name="Number of cuboids",
                    marker={"color": "blue"},
                    hovertemplate="NumberOfDetections: %{y}" + "<br>Timestamp: %{x}",
                )
            )
            # Draw the number of errors
            unique_ts = np.unique(front_errors_df["ts"])
            fig_front.add_trace(
                go.Bar(
                    x=[ts for ts in unique_ts],
                    y=[len(front_errors_df[front_errors_df["ts"] == ts]) for ts in unique_ts],
                    name="Number of overlaps",
                    marker={"color": "red"},
                    hovertemplate="NumberOfOverlaps: %{y}" + "<br>Timestamp: %{x}",
                )
            )
            fig_front["layout"]["yaxis"].update(title_text="Number of Objects")
            fig_front["layout"]["xaxis"].update(title_text="Cycle Counter")

            remark = (
                f"<b>Failed</b> because TPP provides multiple detections for a single object.<br>"
                f"<b>Overlapping Detections:</b> Objects with Intersection Over Union > {NMS_IOU_TH}. <br>"
                f"<b>Number of cuboids:</b> {example_obj.get_properties()[sig.NUM_CUBOID_FRONT][0]}.<br>"
                f"<b>Timestamp:</b> {example_obj.get_properties()[sig.SIGTIMESTAMP_FRONT][0]}.<br>"
            )
            plot_titles.append("Front Camera")
            plots.append(fig_front)
            remarks.append(remark)
            # Draw the first timeframe with errors
            fig = draw_timeframe(
                front_timeframe_df,
                sig.NUM_CUBOID_FRONT,
                sig.CUBOID_LENGTH_FRONT,
                sig.CUBOID_WIDTH_FRONT,
                sig.CUBOID_YAW_FRONT,
                sig.CUBOID_CENTERX_FRONT,
                sig.CUBOID_CENTERY_FRONT,
                sig.CUBOID_CLASSTYPE_FRONT,
            )
            fig.update_yaxes(
                scaleanchor="x",
                scaleratio=1,
            )
            plot_titles.append(f"Frame {ts}")
            plots.append(fig)
            remarks.append("")

        if test_result_rear == fc.FAIL:
            # Store the errors in a dataframe and make sure there are no duplicates
            rear_errors_df = pd.DataFrame(list_of_errors_rear).drop_duplicates()
            # Store the timestamp and the number of cuboids for a specific camera
            rear_reader = reader[[sig.SIGTIMESTAMP_REAR, sig.NUM_CUBOID_REAR]].drop_duplicates()
            ts = rear_errors_df["ts"].iloc[0]
            # Get the first frame with errors
            rear_timeframe_df = reader[reader[sig.SIGTIMESTAMP_REAR] == ts].iloc[0]

            # Draw a bar chart with the number of cuboids and number of overlapping objects
            fig_rear = go.Figure()
            # Draw the number of objects
            fig_rear.add_trace(
                go.Bar(
                    x=rear_reader[sig.SIGTIMESTAMP_REAR],
                    y=rear_reader[sig.NUM_CUBOID_REAR],
                    name="Number of cuboids",
                    marker={"color": "blue"},
                    hovertemplate="NumberOfDetections: %{y}" + "<br>Timestamp: %{x}",
                )
            )
            # Draw the number of errors
            unique_ts = np.unique(rear_errors_df["ts"])
            fig_rear.add_trace(
                go.Bar(
                    x=[ts for ts in unique_ts],
                    y=[len(rear_errors_df[rear_errors_df["ts"] == ts]) for ts in unique_ts],
                    name="Number of overlaps",
                    marker={"color": "red"},
                    hovertemplate="NumberOfOverlaps: %{y}" + "<br>Timestamp: %{x}",
                )
            )
            fig_rear["layout"]["yaxis"].update(title_text="Number of Objects")
            fig_rear["layout"]["xaxis"].update(title_text="Cycle Counter")

            remark = (
                f"<b>Failed</b> because TPP provides multiple detections for a single object.<br>"
                f"<b>Overlapping Detections:</b> Objects with Intersection Over Union > {NMS_IOU_TH}. <br>"
                f"<b>Number of cuboids:</b> {example_obj.get_properties()[sig.NUM_CUBOID_REAR][0]}.<br>"
                f"<b>Timestamp:</b> {example_obj.get_properties()[sig.SIGTIMESTAMP_REAR][0]}.<br>"
            )
            plot_titles.append("Rear Camera")
            plots.append(fig_rear)
            remarks.append(remark)
            # Draw the first timeframe with errors
            fig = draw_timeframe(
                rear_timeframe_df,
                sig.NUM_CUBOID_REAR,
                sig.CUBOID_LENGTH_REAR,
                sig.CUBOID_WIDTH_REAR,
                sig.CUBOID_YAW_REAR,
                sig.CUBOID_CENTERX_REAR,
                sig.CUBOID_CENTERY_REAR,
                sig.CUBOID_CLASSTYPE_REAR,
            )
            fig.update_yaxes(
                scaleanchor="x",
                scaleratio=1,
            )
            plot_titles.append(f"Frame {ts}")
            plots.append(fig)
            remarks.append("")

        if test_result_left == fc.FAIL:
            # Store the errors in a dataframe and make sure there are no duplicates
            left_errors_df = pd.DataFrame(list_of_errors_left).drop_duplicates()
            # Store the timestamp and the number of cuboids for a specific camera
            left_reader = reader[[sig.SIGTIMESTAMP_LEFT, sig.NUM_CUBOID_LEFT]].drop_duplicates()
            ts = left_errors_df["ts"].iloc[0]
            # Get the first frame with errors
            left_timeframe_df = reader[reader[sig.SIGTIMESTAMP_LEFT] == ts].iloc[0]

            # Draw a bar chart with the number of cuboids and number of overlapping objects
            fig_left = go.Figure()
            # Draw the number of objects
            fig_left.add_trace(
                go.Bar(
                    x=left_reader[sig.SIGTIMESTAMP_LEFT],
                    y=left_reader[sig.NUM_CUBOID_LEFT],
                    name="Number of cuboids",
                    marker={"color": "blue"},
                    hovertemplate="NumberOfDetections: %{y}" + "<br>Timestamp: %{x}",
                )
            )
            # Draw the number of errors
            unique_ts = np.unique(left_errors_df["ts"])
            fig_left.add_trace(
                go.Bar(
                    x=[ts for ts in unique_ts],
                    y=[len(left_errors_df[left_errors_df["ts"] == ts]) for ts in unique_ts],
                    name="Number of overlaps",
                    marker={"color": "red"},
                    hovertemplate="NumberOfOverlaps: %{y}" + "<br>Timestamp: %{x}",
                )
            )
            fig_left["layout"]["yaxis"].update(title_text="Number of Objects")
            fig_left["layout"]["xaxis"].update(title_text="Cycle Counter")

            remark = (
                f"<b>Failed</b> because TPP provides multiple detections for a single object.<br>"
                f"<b>Overlapping Detections:</b> Objects with Intersection Over Union > {NMS_IOU_TH}. <br>"
                f"<b>Number of cuboids:</b> {example_obj.get_properties()[sig.NUM_CUBOID_LEFT][0]}.<br>"
                f"<b>Timestamp:</b> {example_obj.get_properties()[sig.SIGTIMESTAMP_LEFT][0]}.<br>"
            )
            plot_titles.append("Left Camera")
            plots.append(fig_left)
            remarks.append(remark)
            # Draw the first timeframe with errors
            fig = draw_timeframe(
                left_timeframe_df,
                sig.NUM_CUBOID_LEFT,
                sig.CUBOID_LENGTH_LEFT,
                sig.CUBOID_WIDTH_LEFT,
                sig.CUBOID_YAW_LEFT,
                sig.CUBOID_CENTERX_LEFT,
                sig.CUBOID_CENTERY_LEFT,
                sig.CUBOID_CLASSTYPE_LEFT,
            )
            fig.update_yaxes(
                scaleanchor="x",
                scaleratio=1,
            )
            plot_titles.append(f"Frame {ts}")
            plots.append(fig)
            remarks.append("")

        if test_result_right == fc.FAIL:
            # Store the errors in a dataframe and make sure there are no duplicates
            right_errors_df = pd.DataFrame(list_of_errors_right).drop_duplicates().reset_index(drop=True)
            # Store the timestamp and the number of cuboids for a specific camera
            right_reader = reader[[sig.SIGTIMESTAMP_RIGHT, sig.NUM_CUBOID_RIGHT]].drop_duplicates()
            ts = right_errors_df["ts"].iloc[0]
            # Get the first frame with errors
            right_timeframe_df = reader[reader[sig.SIGTIMESTAMP_RIGHT] == ts].iloc[0]

            # Draw a bar chart with the number of cuboids and number of overlapping objects
            fig_right = go.Figure()
            # Draw the number of objects
            fig_right.add_trace(
                go.Bar(
                    x=right_reader[sig.SIGTIMESTAMP_RIGHT],
                    y=right_reader[sig.NUM_CUBOID_RIGHT],
                    name="Number of cuboids",
                    marker={"color": "blue"},
                    hovertemplate="NumberOfDetections: %{y}" + "<br>Timestamp: %{x}",
                )
            )
            # Draw the number of errors
            unique_ts = np.unique(right_errors_df["ts"])
            fig_right.add_trace(
                go.Bar(
                    x=[ts for ts in unique_ts],
                    y=[len(right_errors_df[right_errors_df["ts"] == ts]) for ts in unique_ts],
                    name="Number of overlaps",
                    marker={"color": "red"},
                    hovertemplate="NumberOfOverlaps: %{y}" + "<br>Timestamp: %{x}",
                )
            )
            fig_right["layout"]["yaxis"].update(title_text="Number of Objects")
            fig_right["layout"]["xaxis"].update(title_text="Cycle Counter")

            remark = (
                f"<b>Failed</b> because TPP provides multiple detections for a single object.<br>"
                f"<b>Overlapping Detections:</b> Objects with Intersection Over Union > {NMS_IOU_TH}. <br>"
                f"<b>Number of cuboids:</b> {example_obj.get_properties()[sig.NUM_CUBOID_RIGHT][0]}.<br>"
                f"<b>Timestamp:</b> {example_obj.get_properties()[sig.SIGTIMESTAMP_RIGHT][0]}.<br>"
            )
            plot_titles.append("Right Camera")
            plots.append(fig_right)
            remarks.append(remark)
            # Draw the first timeframe with errors
            fig = draw_timeframe(
                right_timeframe_df,
                sig.NUM_CUBOID_RIGHT,
                sig.CUBOID_LENGTH_RIGHT,
                sig.CUBOID_WIDTH_RIGHT,
                sig.CUBOID_YAW_RIGHT,
                sig.CUBOID_CENTERX_RIGHT,
                sig.CUBOID_CENTERY_RIGHT,
                sig.CUBOID_CLASSTYPE_RIGHT,
            )
            fig.update_yaxes(
                scaleanchor="x",
                scaleratio=1,
            )
            plot_titles.append(f"Frame {ts}")
            plots.append(fig)
            remarks.append("")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1668880"],
            fc.TESTCASE_ID: ["39726"],
            fc.TEST_RESULT: [test_result],
        }

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif test_result == fc.NOT_ASSESSED:
            self.result.measured_result = DATA_NOK
        else:
            self.result.measured_result = FALSE

        self.result.details["Additional_results"] = result_df

        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")


@verifies(
    requirement="1668880",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_8DpcYHi-Ee6n7Ow9oWyCxw&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg",
)
@verifies(
    requirement="1668901",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_HBXcQHjBEe6n7Ow9oWyCxw&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg",
)
@testcase_definition(
    name="TPP Non Maximum Suppression",
    description="Check if objects are overlapping.",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class TestNonMaximumSuppression(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestNonMaximumSuppressionTestStep,
        ]
