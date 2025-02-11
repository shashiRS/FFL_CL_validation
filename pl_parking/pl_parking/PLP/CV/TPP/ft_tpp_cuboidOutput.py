"""TestCases performing all necessary checks for cuboid output."""

import logging
import math
import os

import numpy as np
import pandas as pd
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
import pl_parking.PLP.CV.TPP.ft_helper as fh_tpp

# import pl_parking.PLP.CV.TPP.tpp_signals_r4 as tpp_reader_r4
import pl_parking.PLP.CV.TPP.ft_helper as tpp_reader_r4
from pl_parking.common_ft_helper import rep

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

FT_TPP = "FT_TPP_CUBOID_OUTPUT"
example_obj = tpp_reader_r4.TPPSignals()


# TODO: Check the required names for test-step definition


def validate_cuboid_sizes(
    reader: pd.DataFrame,
    number_of_objects_signal: str,
    class_signal: str,
    width_signal: str,
    height_signal: str,
    length_signal: str,
    timestamp_signal: str,
) -> (str, str, list):
    """
    Validate the width, length and height for each detection.
    test_result: PASS/FAIL.
    description: The status of the signal.
    list_of_errors: Usefully data about the errors found. Empty list if no errors founds.
    :param reader: DataFrame containing the signals read from the recording.
    :param number_of_objects_signal: The signal containing the number of objects.
    :param class_signal: The signal string containing the class type.
    :param width_signal: The signal string containing the width.
    :param height_signal: The signal string containing the height.
    :param length_signal: The signal string containing the length.
    :param timestamp_signal: The signal containing the timestamp.
    :return: (test_result, description, list_of_errors)
    """
    available_signals = reader.columns

    test_result = fc.PASS
    is_description_set = False  # Flag used to set the description for the first failing event
    description = "The evaluation of the signal is <b>PASSED</b>."
    list_of_errors = []
    if (
        timestamp_signal in available_signals
        and number_of_objects_signal in available_signals
        and np.array([class_signal in sig for sig in available_signals]).any()
        and np.array([height_signal in sig for sig in available_signals]).any()
        and np.array([width_signal in sig for sig in available_signals]).any()
        and np.array([length_signal in sig for sig in available_signals]).any()
    ):
        for _, row in reader.iterrows():  # Iterate all frames
            n = int(row[number_of_objects_signal])
            ts = int(row[timestamp_signal])
            for i in range(n):  # Iterate all detections for a frame
                class_type = row[(class_signal, i)]
                width = row[(width_signal, i)]
                height = row[(height_signal, i)]
                length = row[(length_signal, i)]

                error_dict = {
                    "ts": ts,
                    "id": int(i),
                    "class_type": int(class_type),
                    "width": width,
                    "height": height,
                    "length": length,
                    "width_signal_name": example_obj.get_properties()[width_signal][0],
                    "height_signal_name": example_obj.get_properties()[height_signal][0],
                    "length_signal_name": example_obj.get_properties()[length_signal][0],
                }

                if (
                    class_type != ct.CuboidClassTypes["CAR"]
                    and class_type != ct.CuboidClassTypes["VAN"]
                    and class_type != ct.CuboidClassTypes["TRUCK"]
                ):  # Get the class name based on the class id
                    class_name = "UNKNOWN"
                    for key, value in ct.CuboidClassTypes.items():
                        if value == class_type:
                            class_name = key

                    error_dict["class_name"] = class_name

                    min_size = ct.ObjectSizes[class_name]["width"]["min"]
                    max_size = ct.ObjectSizes[class_name]["width"]["max"]
                    if (width < min_size) or (width > max_size):
                        test_result = fc.FAIL
                        error_dict["value"] = width
                        error_dict["description"] = "width out of bounds"
                        error_dict["expected_result"] = f"[{min_size}, {max_size}]"

                    min_size = ct.ObjectSizes[class_name]["height"]["min"]
                    max_size = ct.ObjectSizes[class_name]["height"]["max"]
                    if (height < min_size) or (height > max_size):
                        test_result = fc.FAIL
                        error_dict["value"] = height
                        error_dict["description"] = "height out of bounds"
                        error_dict["expected_result"] = f"[{min_size}, {max_size}]"

                    min_size = ct.ObjectSizes[class_name]["length"]["min"]
                    max_size = ct.ObjectSizes[class_name]["length"]["max"]
                    if (length < min_size) or (length > max_size):
                        test_result = fc.FAIL
                        error_dict["value"] = length
                        error_dict["description"] = "length out of bounds"
                        error_dict["expected_result"] = f"[{min_size}, {max_size}]"

                    if test_result == fc.FAIL:
                        # Remember the first failing description
                        if is_description_set is False:
                            description = " ".join(
                                f"The evaluation of the signals is <b>FAILED</b> at"
                                f" timestamp <b>{error_dict['ts']}</b> for object with ID <b>{error_dict['id']}</b> "
                                f"and class <b>{error_dict['class_name']}</b> ({error_dict['class_type']}) with"
                                f" <b>{error_dict['description']}</b> (received) {error_dict['value']}, expecting"
                                f" {error_dict['expected_result']}).".split()
                            )
                            is_description_set = True
                        # Remember all errors
                        list_of_errors.append(error_dict)

    else:
        test_result = fc.INPUT_MISSING
        description = " ".join("Signals <b>not evaluated</b> because are not available.".split())

    return test_result, description, list_of_errors


def validate_cuboid_yaw(
    reader: pd.DataFrame, number_of_objects_signal: str, class_signal: str, yaw_signal: str, timestamp_signal: str
) -> (str, str, list):
    """
    Validate the yaw for each detection with cuboid class.
    test_result: PASS/FAIL.
    description: The status of the signal.
    list_of_errors: Usefully data about the errors found. Empty list if no errors founds.
    :param reader: DataFrame containing the signals read from the recording.
    :param number_of_objects_signal: The signal containing the number of objects.
    :param class_signal: The signal string containing the class type.
    :param yaw_signal: The signal string containing the yaw.
    :param timestamp_signal: The signal containing the timestamp.
    :return: (test_result, description, list_of_errors)
    """
    available_signals = reader.columns

    test_result = fc.PASS
    is_description_set = False  # Flag to set the description for the first failing event
    description = "The evaluation of the signal is <b>PASSED</b>."
    list_of_errors = []

    if (
        timestamp_signal in available_signals
        and number_of_objects_signal in available_signals
        and np.array([class_signal in sig for sig in available_signals]).any()
        and np.array([yaw_signal in sig for sig in available_signals]).any()
    ):
        for _, row in reader.iterrows():  # Iterate all frames
            n = int(row[number_of_objects_signal])
            ts = int(row[timestamp_signal])
            for i in range(n):  # Iterate all detections for a frame
                class_type = row[(class_signal, i)]
                yaw = row[(yaw_signal, i)]

                error_dict = {
                    "ts": ts,
                    "id": int(i),
                    "class_type": int(class_type),
                    "yaw": yaw,
                    "yaw_signal_name": example_obj.get_properties()[yaw_signal][0],
                }

                if (
                    class_type != ct.CuboidClassTypes["CAR"]
                    and class_type != ct.CuboidClassTypes["VAN"]
                    and class_type != ct.CuboidClassTypes["TRUCK"]
                ):  # Get the class name based on the class id
                    class_name = "UNKNOWN"
                    for key, value in ct.CuboidClassTypes.items():
                        if value == class_type:
                            class_name = key

                    error_dict["class_name"] = class_name

                    PI = math.pi  # [radians]
                    min_size = -PI
                    max_size = PI
                    if (yaw < min_size) or (yaw > max_size):
                        test_result = fc.FAIL
                        error_dict["value"] = yaw
                        error_dict["description"] = "yaw out of bounds"
                        error_dict["expected_result"] = f"[{min_size}, {max_size}]"

                    if test_result == fc.FAIL:
                        # Remember the first failing description
                        if is_description_set is False:
                            description = " ".join(
                                f"The evaluation of the signals is <b>FAILED</b> at timestamp <b>{error_dict['ts']}</b> "
                                f"for object with ID <b>{error_dict['id']}</b> and class <b>{error_dict['class_name']}</b> "
                                f"({error_dict['class_type']}) with <b>{error_dict['description']}</b> (received "
                                f"{error_dict['value']}, expecting {error_dict['expected_result']}).".split()
                            )
                            is_description_set = True
                        # Remember all errors
                        list_of_errors.append(error_dict)

    else:
        test_result = fc.INPUT_MISSING
        description = " ".join("Signals <b>not evaluated</b> because are not available.".split())

    return test_result, description, list_of_errors


def validate_cuboid_confidence(
    reader: pd.DataFrame,
    number_of_objects_signal: str,
    class_signal: str,
    confidence_signal: str,
    timestamp_signal: str,
) -> (str, str, list):
    """
    Validate the confidence for each detection with cuboid class.
    test_result: PASS/FAIL.
    description: The status of the signal.
    list_of_errors: Usefully data about the errors found. Empty list if no errors founds.
    :param reader: DataFrame containing the signals read from the recording.
    :param number_of_objects_signal: The signal containing the number of objects.
    :param class_signal: The signal string containing the class type.
    :param confidence_signal: The signal string containing the confidence.
    :param timestamp_signal: The signal containing the timestamp.
    :return: (test_result, description, list_of_errors)
    """
    available_signals = reader.columns

    test_result = fc.PASS
    is_description_set = False  # Flag to set the description for the first failing event
    description = "The evaluation of the signal is <b>PASSED</b>."
    list_of_errors = []

    if (
        timestamp_signal in available_signals
        and number_of_objects_signal in available_signals
        and np.array([class_signal in sig for sig in available_signals]).any()
        and np.array([confidence_signal in sig for sig in available_signals]).any()
    ):
        for _, row in reader.iterrows():  # Iterate all frames
            n = int(row[number_of_objects_signal])
            ts = int(row[timestamp_signal])
            for i in range(n):  # Iterate all detections for a frame
                class_type = row[(class_signal, i)]
                confidence = row[(confidence_signal, i)]

                error_dict = {
                    "ts": ts,
                    "id": int(i),
                    "class_type": int(class_type),
                    "confidence": confidence,
                    "confidence_signal_name": example_obj.get_properties()[confidence_signal][0],
                }

                if (
                    class_type != ct.CuboidClassTypes["CAR"]
                    and class_type != ct.CuboidClassTypes["VAN"]
                    and class_type != ct.CuboidClassTypes["TRUCK"]
                ):  # Get the class name based on the class id
                    class_name = "UNKNOWN"
                    for key, value in ct.CuboidClassTypes.items():
                        if value == class_type:
                            class_name = key

                    error_dict["class_name"] = class_name

                    min_size = 0
                    max_size = 1
                    if (confidence < min_size) or (confidence > max_size):
                        test_result = fc.FAIL
                        error_dict["value"] = confidence
                        error_dict["description"] = "confidence out of bounds"
                        error_dict["expected_result"] = f"[{min_size}, {max_size}]"

                    if test_result == fc.FAIL:
                        # Remember the first failing description
                        if is_description_set is False:
                            description = " ".join(
                                f"The evaluation of the signals is <b>FAILED</b> at timestamp <b>{error_dict['ts']}</b> "
                                f"for object with ID <b>{error_dict['id']}</b> and class <b>{error_dict['class_name']}</b> "
                                f"({error_dict['class_type']}) with <b>{error_dict['description']}</b> (received "
                                f"{error_dict['value']}, expecting {error_dict['expected_result']}).".split()
                            )
                            is_description_set = True
                        # Remember all errors
                        list_of_errors.append(error_dict)

    else:
        test_result = fc.INPUT_MISSING
        description = " ".join("Signals <b>not evaluated</b> because are not available.".split())

    return test_result, description, list_of_errors


def validate_cuboid_center_point(
    reader: pd.DataFrame,
    number_of_objects_signal: str,
    class_signal: str,
    center_x_signal: str,
    center_y_signal: str,
    timestamp_signal: str,
    camera_name: str,
) -> (str, str, list):
    """
    Validate the position of the center point for each detection with cuboid class.
    test_result: PASS/FAIL.
    description: The status of the signal.
    list_of_errors: Usefully data about the errors found. Empty list if no errors founds.
    :param reader: DataFrame containing the signals read from the recording.
    :param number_of_objects_signal: The signal containing the number of objects.
    :param class_signal: The signal string containing the class type.
    :param center_x_signal: The signal string containing the x coordinate of the center point.
    :param center_y_signal: The signal string containing the y coordinate of the center point.
    :param camera_name: The name of the camera (FRONT/REAR/LEFT/RIGHT).
    :param timestamp_signal: The signal containing the timestamp.
    :return: (test_result, description, list_of_errors)
    """
    available_signals = reader.columns

    test_result = fc.PASS
    is_description_set = False  # Flag to set the description for the first failing event
    description = "The evaluation of the signal is <b>PASSED</b>."
    list_of_errors = []

    if (
        timestamp_signal in available_signals
        and number_of_objects_signal in available_signals
        and np.array([class_signal in sig for sig in available_signals]).any()
        and np.array([center_x_signal in sig for sig in available_signals]).any()
        and np.array([center_y_signal in sig for sig in available_signals]).any()
    ):
        for _, row in reader.iterrows():  # Iterate all frames
            n = int(row[number_of_objects_signal])
            ts = int(row[timestamp_signal])
            for i in range(n):  # Iterate all detections for a frame
                class_type = row[(class_signal, i)]
                center_x = row[(center_x_signal, i)]
                center_y = row[(center_y_signal, i)]

                error_dict = {
                    "ts": ts,
                    "id": int(i),
                    "camera_name": camera_name,
                    "class_type": int(class_type),
                    "center_x": center_x,
                    "center_y": center_y,
                    "center_x_signal_name": example_obj.get_properties()[center_x_signal][0],
                    "center_y_signal_name": example_obj.get_properties()[center_y_signal][0],
                }

                if (
                    class_type != ct.CuboidClassTypes["CAR"]
                    and class_type != ct.CuboidClassTypes["VAN"]
                    and class_type != ct.CuboidClassTypes["TRUCK"]
                ):  # Get the class name based on the class id
                    class_name = "UNKNOWN"
                    for key, value in ct.CuboidClassTypes.items():
                        if value == class_type:
                            class_name = key

                    error_dict["class_name"] = class_name

                    # TODO: Read the position of the camera from recording
                    # Each camera have a certain area where the center points should be located
                    if camera_name == "FRONT":
                        if center_x < 0:  # point behind camera
                            test_result = fc.FAIL
                            error_dict["description"] = "center point behind camera"
                            error_dict["value"] = f"(x = {center_x}, y = {center_y}))"
                            error_dict["expected_result"] = "Center Point X > 0"

                    elif camera_name == "REAR":
                        if center_x > 0:  # point behind camera
                            test_result = fc.FAIL
                            error_dict["description"] = "center point behind camera"
                            error_dict["value"] = f"(x = {center_x}, y = {center_y}))"
                            error_dict["expected_result"] = "Center Point X < 0"

                    elif camera_name == "LEFT":
                        if center_y < 0:  # point behind camera
                            test_result = fc.FAIL
                            error_dict["description"] = "center point behind camera"
                            error_dict["value"] = f"(x = {center_x}, y = {center_y}))"
                            error_dict["expected_result"] = "Center Point Y > 0"

                    elif camera_name == "RIGHT":
                        if center_y > 0:  # point behind camera
                            test_result = fc.FAIL
                            error_dict["description"] = "center point behind camera"
                            error_dict["value"] = f"(x = {center_x}, y = {center_y}))"
                            error_dict["expected_result"] = "Center Point Y < 0"

                    else:  # Wrong camera name
                        test_result = fc.FAIL
                        error_dict["description"] = "Camera side unknown. Check implementation"
                        error_dict["value"] = camera_name
                        error_dict["expected_result"] = "FRONT/REAR/LEFT/RIGHT"

                    if test_result == fc.FAIL:
                        # Remember the first failing description
                        if is_description_set is False:
                            description = " ".join(
                                f"The evaluation of the signals is <b>FAILED</b> at timestamp <b>{error_dict['ts']}</b> "
                                f"for object with ID <b>{error_dict['id']}</b> and class <b>{error_dict['class_name']}</b> "
                                f"({error_dict['class_type']}) with <b>{error_dict['description']}</b> (received "
                                f"{error_dict['value']}, expecting {error_dict['expected_result']}).".split()
                            )
                            is_description_set = True
                        # Remember all errors
                        list_of_errors.append(error_dict)

    else:
        test_result = fc.INPUT_MISSING
        description = " ".join("Signals <b>not evaluated</b> because are not available.".split())

    return test_result, description, list_of_errors


def validate_cuboid_class_type(
    reader: pd.DataFrame,
    number_of_objects_signal: str,
    class_signal: str,
    timestamp_signal: str,
) -> (str, str, list):
    """
    Validate the class id for each detection with cuboid class.
    test_result: PASS/FAIL.
    description: The status of the signal.
    list_of_errors: Usefully data about the errors found. Empty list if no errors founds.
    :param reader: DataFrame containing the signals read from the recording.
    :param number_of_objects_signal: The signal containing the number of objects.
    :param class_signal: The signal string containing the class type.
    :param timestamp_signal: The signal containing the timestamp.
    :return: (test_result, description, list_of_errors)
    """
    available_signals = reader.columns

    test_result = fc.PASS
    is_description_set = False  # Flag to set the description for the first failing event
    description = "The evaluation of the signal is <b>PASSED</b>."
    list_of_errors = []

    if (
        timestamp_signal in available_signals
        and number_of_objects_signal in available_signals
        and np.array([class_signal in sig for sig in available_signals]).any()
    ):
        for _, row in reader.iterrows():  # Iterate all frames
            n = int(row[number_of_objects_signal])
            ts = int(row[timestamp_signal])
            for i in range(n):  # Iterate all detections for a frame
                class_type = row[(class_signal, i)]

                error_dict = {"ts": ts, "id": int(i), "class_type": int(class_type)}

                if (
                    class_type != ct.CuboidClassTypes["CAR"]
                    and class_type != ct.CuboidClassTypes["VAN"]
                    and class_type != ct.CuboidClassTypes["TRUCK"]
                ):
                    # Get the class name based on the class id
                    class_name = "UNKNOWN"

                    # TODO: Modify for R4
                    test_result = fc.FAIL
                    error_dict["description"] = "class id is unknown"
                    error_dict["value"] = class_type
                    error_dict["expected_result"] = "CAR/VAN/TRUCK"

                    if test_result == fc.FAIL:
                        # Remember the first failing description
                        if is_description_set is False:
                            description = " ".join(
                                f"The evaluation of the signals is <b>FAILED</b> at timestamp <b>{error_dict['ts']}</b> "
                                f"for object with ID <b>{error_dict['id']}</b> and class <b>{class_name}</b> "
                                f"({error_dict['class_type']}) with <b>{error_dict['description']}</b> (received "
                                f"{error_dict['value']}, expecting {error_dict['expected_result']}).".split()
                            )
                            is_description_set = True
                        # Remember all errors
                        list_of_errors.append(error_dict)

    else:
        test_result = fc.INPUT_MISSING
        description = " ".join("Signals <b>not evaluated</b> because are not available.".split())

    return test_result, description, list_of_errors


@teststep_definition(
    step_number=1,
    name="TPP_ValidateCuboidSizesOutput",
    description="Width, height and length should be in a given range.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPP, tpp_reader_r4.TPPSignals)
class TestCuboidSizesOutputTestStep(TestStep):
    """Test step definition."""

    custom_report = fh_tpp.TPPCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.sig_sum = None

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        reader = self.readers[FT_TPP]
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        signal_summary = {}
        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)

        sig = tpp_reader_r4.TPPSignals.Columns  # The strings for the signals

        # Each dynamic object has a range for every size (width, length, height)
        # Check the sizes of each cuboid
        test_result_front, description_front, list_of_errors_front = validate_cuboid_sizes(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_FRONT,
            class_signal=sig.CUBOID_CLASSTYPE_FRONT,
            width_signal=sig.CUBOID_WIDTH_FRONT,
            height_signal=sig.CUBOID_HEIGHT_FRONT,
            length_signal=sig.CUBOID_LENGTH_FRONT,
            timestamp_signal=sig.SIGTIMESTAMP_FRONT,
        )
        test_result_rear, description_rear, list_of_errors_rear = validate_cuboid_sizes(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_REAR,
            class_signal=sig.CUBOID_CLASSTYPE_REAR,
            width_signal=sig.CUBOID_WIDTH_REAR,
            height_signal=sig.CUBOID_HEIGHT_REAR,
            length_signal=sig.CUBOID_LENGTH_REAR,
            timestamp_signal=sig.SIGTIMESTAMP_REAR,
        )
        test_result_left, description_left, list_of_errors_left = validate_cuboid_sizes(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_LEFT,
            class_signal=sig.CUBOID_CLASSTYPE_LEFT,
            width_signal=sig.CUBOID_WIDTH_LEFT,
            height_signal=sig.CUBOID_HEIGHT_LEFT,
            length_signal=sig.CUBOID_LENGTH_LEFT,
            timestamp_signal=sig.SIGTIMESTAMP_LEFT,
        )
        test_result_right, description_right, list_of_errors_right = validate_cuboid_sizes(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_RIGHT,
            class_signal=sig.CUBOID_CLASSTYPE_RIGHT,
            width_signal=sig.CUBOID_WIDTH_RIGHT,
            height_signal=sig.CUBOID_HEIGHT_RIGHT,
            length_signal=sig.CUBOID_LENGTH_RIGHT,
            timestamp_signal=sig.SIGTIMESTAMP_RIGHT,
        )

        # Use the signal of the width without the last extension for the report
        front_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_WIDTH_FRONT][0].split(".")[:-1])
        rear_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_WIDTH_REAR][0].split(".")[:-1])
        left_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_WIDTH_LEFT][0].split(".")[:-1])
        right_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_WIDTH_RIGHT][0].split(".")[:-1])

        signal_summary[front_signal_name] = description_front
        signal_summary[rear_signal_name] = description_rear
        signal_summary[left_signal_name] = description_left
        signal_summary[right_signal_name] = description_right
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary=signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        # Explain the behaviour of the test case
        plot_titles.append("")
        plots.append("")
        remarks.append(
            f"This test will verify if the sizes of a cuboid are in a given range.<br>"
            f"The size is measured in meters [m].<br>"
            f"Cuboids have a class type of CAR({ct.CuboidClassTypes['CAR']}) , "
            f"CAR({ct.CuboidClassTypes['VAN']}) or TRUCK({ct.CuboidClassTypes['TRUCK']}).<br>"
            f"The range of the sizes are the following: <br>"
            f"{ct.ObjectSizes['CAR']['width']['min']} < car width < {ct.ObjectSizes['CAR']['width']['max']}<br>"
            f"{ct.ObjectSizes['CAR']['length']['min']} < car length < {ct.ObjectSizes['CAR']['length']['max']}<br>"
            f"{ct.ObjectSizes['CAR']['height']['min']} < car height < {ct.ObjectSizes['CAR']['height']['max']}<br>"
            f"{ct.ObjectSizes['VAN']['width']['min']} < van width < {ct.ObjectSizes['VAN']['width']['max']}<br>"
            f"{ct.ObjectSizes['VAN']['length']['min']} < van length < {ct.ObjectSizes['VAN']['length']['max']}<br>"
            f"{ct.ObjectSizes['VAN']['height']['min']} < van height < {ct.ObjectSizes['VAN']['height']['max']}<br>"
            f"{ct.ObjectSizes['TRUCK']['width']['min']} < truck width < {ct.ObjectSizes['TRUCK']['width']['max']}<br>"
            f"{ct.ObjectSizes['TRUCK']['length']['min']} < truck length < {ct.ObjectSizes['TRUCK']['length']['max']}<br>"
            f"{ct.ObjectSizes['TRUCK']['height']['min']} < truck height < {ct.ObjectSizes['TRUCK']['height']['max']}<br>"
        )

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

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif test_result == fc.NOT_ASSESSED:
            self.result.measured_result = DATA_NOK
        else:
            self.result.measured_result = FALSE

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1646512"],
            fc.TESTCASE_ID: ["41582"],
            fc.TEST_RESULT: [test_result],
        }

        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")

        self.result.details["Additional_results"] = result_df


@verifies(
    requirement="1646512",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_u3AiQHcZEe6n7Ow9oWyCxw&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F18557&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg",
)
@testcase_definition(
    name="TPP TPP_ValidateCuboidSizesOutput",
    description="This test will verify the sizes for each DynamicObject_t with cuboid class.",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class TestCuboidSizesOutput(TestCase):
    """Output of cuboid sizes test case."""

    custom_report = fh_tpp.TPPCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestCuboidSizesOutputTestStep,
        ]


@teststep_definition(
    step_number=1,
    name="TPP_ValidateCuboidYawAngleOutput",
    description="This test will verify if the yaw angle for TPP Cuboids is in [-pi, pi].",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPP, tpp_reader_r4.TPPSignals)
class TestCuboidYawOutputTestStep(TestStep):
    """Test Step definition."""

    custom_report = fh_tpp.TPPCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.sig_sum = None

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        reader = self.readers[FT_TPP]
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        signal_summary = {}
        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)

        sig = tpp_reader_r4.TPPSignals.Columns  # The strings for the signals

        test_result_front, description_front, list_of_errors_front = validate_cuboid_yaw(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_FRONT,
            class_signal=sig.CUBOID_CLASSTYPE_FRONT,
            yaw_signal=sig.CUBOID_YAW_FRONT,
            timestamp_signal=sig.SIGTIMESTAMP_FRONT,
        )
        test_result_rear, description_rear, list_of_errors_rear = validate_cuboid_yaw(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_REAR,
            class_signal=sig.CUBOID_CLASSTYPE_REAR,
            yaw_signal=sig.CUBOID_YAW_REAR,
            timestamp_signal=sig.SIGTIMESTAMP_REAR,
        )
        test_result_left, description_left, list_of_errors_left = validate_cuboid_yaw(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_LEFT,
            class_signal=sig.CUBOID_CLASSTYPE_LEFT,
            yaw_signal=sig.CUBOID_YAW_LEFT,
            timestamp_signal=sig.SIGTIMESTAMP_LEFT,
        )
        test_result_right, description_right, list_of_errors_right = validate_cuboid_yaw(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_RIGHT,
            class_signal=sig.CUBOID_CLASSTYPE_RIGHT,
            yaw_signal=sig.CUBOID_YAW_RIGHT,
            timestamp_signal=sig.SIGTIMESTAMP_RIGHT,
        )

        front_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_YAW_FRONT][0].split(".")[:-1])
        rear_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_YAW_REAR][0].split(".")[:-1])
        left_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_YAW_LEFT][0].split(".")[:-1])
        right_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_YAW_RIGHT][0].split(".")[:-1])

        signal_summary[front_signal_name] = description_front
        signal_summary[rear_signal_name] = description_rear
        signal_summary[left_signal_name] = description_left
        signal_summary[right_signal_name] = description_right
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary=signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        # Explain the behaviour of the test case
        plot_titles.append("")
        plots.append("")
        remarks.append(
            f"This test will verify if the yaw of a cuboid is in a given range.<br>"
            f"The size is measured in radians [rad].<br>"
            f"{-math.pi} < yaw < {math.pi}<br>"
        )

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

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif test_result == fc.NOT_ASSESSED:
            self.result.measured_result = DATA_NOK
        else:
            self.result.measured_result = FALSE

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1646515"],
            fc.TESTCASE_ID: ["41581"],
            fc.TEST_RESULT: [test_result],
        }

        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")

        self.result.details["Additional_results"] = result_df


@verifies(
    requirement="1646515",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_PKcNYHcaEe6n7Ow9oWyCxw&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F18557&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg",
)
@testcase_definition(
    name="TPP TPP_ValidateCuboidYawOutput",
    description="This test will verify the value of the yaw angle for each TPP Cuboid.",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class TestCuboidYawOutput(TestCase):
    """Cuboid output yaw test case."""

    custom_report = fh_tpp.TPPCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestCuboidYawOutputTestStep,
        ]


@teststep_definition(
    step_number=1,
    name="TPP_ValidateOutputCuboidConfidence",
    description="This test will verify if the confidence each TPP Cuboid is in [0, 1].",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPP, tpp_reader_r4.TPPSignals)
class TestCuboidConfidenceOutputTestStep(TestStep):
    """Test Step definition."""

    custom_report = fh_tpp.TPPCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.sig_sum = None

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        reader = self.readers[FT_TPP]
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        signal_summary = {}
        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)

        sig = tpp_reader_r4.TPPSignals.Columns  # The strings for the signals

        test_result_front, description_front, list_of_errors_front = validate_cuboid_confidence(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_FRONT,
            class_signal=sig.CUBOID_CLASSTYPE_FRONT,
            confidence_signal=sig.CUBOID_CONFIDENCE_FRONT,
            timestamp_signal=sig.SIGTIMESTAMP_FRONT,
        )
        test_result_rear, description_rear, list_of_errors_rear = validate_cuboid_confidence(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_REAR,
            class_signal=sig.CUBOID_CLASSTYPE_REAR,
            confidence_signal=sig.CUBOID_CONFIDENCE_REAR,
            timestamp_signal=sig.SIGTIMESTAMP_REAR,
        )
        test_result_left, description_left, list_of_errors_left = validate_cuboid_confidence(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_LEFT,
            class_signal=sig.CUBOID_CLASSTYPE_LEFT,
            confidence_signal=sig.CUBOID_CONFIDENCE_LEFT,
            timestamp_signal=sig.SIGTIMESTAMP_LEFT,
        )
        test_result_right, description_right, list_of_errors_right = validate_cuboid_confidence(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_RIGHT,
            class_signal=sig.CUBOID_CLASSTYPE_RIGHT,
            confidence_signal=sig.CUBOID_CONFIDENCE_RIGHT,
            timestamp_signal=sig.SIGTIMESTAMP_RIGHT,
        )

        front_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_CONFIDENCE_FRONT][0].split(".")[:-1])
        rear_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_CONFIDENCE_REAR][0].split(".")[:-1])
        left_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_CONFIDENCE_LEFT][0].split(".")[:-1])
        right_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_CONFIDENCE_RIGHT][0].split(".")[:-1])

        signal_summary[front_signal_name] = description_front
        signal_summary[rear_signal_name] = description_rear
        signal_summary[left_signal_name] = description_left
        signal_summary[right_signal_name] = description_right
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary=signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        # Explain the behaviour of the test case
        plot_titles.append("")
        plots.append("")
        remarks.append(
            "This test will verify if the confidence of a cuboid is in a given range.<br>" "0 < confidence < 1<br>"
        )

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

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif test_result == fc.NOT_ASSESSED:
            self.result.measured_result = DATA_NOK
        else:
            self.result.measured_result = FALSE

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1646518"],
            fc.TESTCASE_ID: ["40896"],
            #
            #
            # lfc.TEST_RESULT: [test_result],
        }

        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")

        self.result.details["Additional_results"] = result_df


@verifies(
    requirement="1646518",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_pGgt0HcaEe6n7Ow9oWyCxw&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F18557&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg",
)
@testcase_definition(
    name="TPP TPP_ValidateCuboidConfidenceOutput",
    description="This test will verify the value of the confidence for each TPP Cuboid",
)
@register_inputs("/parking")
class TestCuboidConfidenceOutput(TestCase):
    """Cuboid output confidence test case."""

    custom_report = fh_tpp.TPPCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestCuboidConfidenceOutputTestStep,
        ]


@teststep_definition(
    step_number=1,
    name="TPP_ValidateCuboidCenterPointOutput",
    description="This test will verify if the center point is in camera range for each TPP Cuboid",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPP, tpp_reader_r4.TPPSignals)
class TestCuboidCenterPointOutputTestStep(TestStep):
    """Test Step definition."""

    custom_report = fh_tpp.TPPCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.sig_sum = None

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        reader = self.readers[FT_TPP]
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        signal_summary = {}
        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)

        sig = tpp_reader_r4.TPPSignals.Columns  # The strings for the signals

        test_result_front, description_front, list_of_errors_front = validate_cuboid_center_point(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_FRONT,
            class_signal=sig.CUBOID_CLASSTYPE_FRONT,
            center_x_signal=sig.CUBOID_CENTERX_FRONT,
            center_y_signal=sig.CUBOID_CENTERY_FRONT,
            camera_name="FRONT",
            timestamp_signal=sig.SIGTIMESTAMP_FRONT,
        )
        test_result_rear, description_rear, list_of_errors_rear = validate_cuboid_center_point(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_REAR,
            class_signal=sig.CUBOID_CLASSTYPE_REAR,
            center_x_signal=sig.CUBOID_CENTERX_REAR,
            center_y_signal=sig.CUBOID_CENTERY_REAR,
            camera_name="REAR",
            timestamp_signal=sig.SIGTIMESTAMP_REAR,
        )
        test_result_left, description_left, list_of_errors_left = validate_cuboid_center_point(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_LEFT,
            class_signal=sig.CUBOID_CLASSTYPE_LEFT,
            center_x_signal=sig.CUBOID_CENTERX_LEFT,
            center_y_signal=sig.CUBOID_CENTERY_LEFT,
            camera_name="LEFT",
            timestamp_signal=sig.SIGTIMESTAMP_LEFT,
        )
        test_result_right, description_right, list_of_errors_right = validate_cuboid_center_point(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_RIGHT,
            class_signal=sig.CUBOID_CLASSTYPE_RIGHT,
            center_x_signal=sig.CUBOID_CENTERX_RIGHT,
            center_y_signal=sig.CUBOID_CENTERY_RIGHT,
            camera_name="RIGHT",
            timestamp_signal=sig.SIGTIMESTAMP_RIGHT,
        )

        front_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_CENTERX_FRONT][0].split(".")[:-1])
        rear_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_CENTERX_REAR][0].split(".")[:-1])
        left_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_CENTERX_LEFT][0].split(".")[:-1])
        right_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_CENTERX_RIGHT][0].split(".")[:-1])

        signal_summary[front_signal_name] = description_front
        signal_summary[rear_signal_name] = description_rear
        signal_summary[left_signal_name] = description_left
        signal_summary[right_signal_name] = description_right
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary=signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        # Explain the behaviour of the test case
        plot_titles.append("")
        plots.append("")
        remarks.append(
            "This test will verify if the center point of a cuboid is in a given camera range.<br>"
            "The center point coordinates are measured in meters [m].<br>"
            "For the front instance of the camera the x coordinate of the center point should be > 0.<br>"
            "For the rear instance of the camera the x coordinate of the center point should be < 0.<br>"
            "For the left instance of the camera the y coordinate of the center point should be > 0.<br>"
            "For the right instance of the camera the y coordinate of the center point should be < 0.<br>"
        )

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

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif test_result == fc.NOT_ASSESSED:
            self.result.measured_result = DATA_NOK
        else:
            self.result.measured_result = FALSE

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1646503"],
            fc.TESTCASE_ID: ["41521"],
            fc.TEST_RESULT: [test_result],
        }

        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")

        self.result.details["Additional_results"] = result_df


@verifies(
    requirement="1646503",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_U0XfwHcZEe6n7Ow9oWyCxw&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F18557&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg",
)
@testcase_definition(
    name="TPP TPP_ValidateCuboidCenterPointOutput",
    description="This test will verify the value of the center point for each TPP Cuboid",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class TestCuboidCenterPointOutput(TestCase):
    """Cuboid output center point test case."""

    custom_report = fh_tpp.TPPCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestCuboidCenterPointOutputTestStep,
        ]


@teststep_definition(
    step_number=1,
    name="TPP_ValidateCuboidClassTypeOutput",
    description="This test will verify the class type for each TPP Cuboid",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPP, tpp_reader_r4.TPPSignals)
class TestCuboidClassTypeOutputTestStep(TestStep):
    """Test Step definition."""

    custom_report = fh_tpp.TPPCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.sig_sum = None

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        reader = self.readers[FT_TPP]
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        signal_summary = {}
        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)

        sig = tpp_reader_r4.TPPSignals.Columns  # The strings for the signals

        test_result_front, description_front, list_of_errors_front = validate_cuboid_class_type(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_FRONT,
            class_signal=sig.CUBOID_CLASSTYPE_FRONT,
            timestamp_signal=sig.SIGTIMESTAMP_FRONT,
        )
        test_result_rear, description_rear, list_of_errors_rear = validate_cuboid_class_type(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_REAR,
            class_signal=sig.CUBOID_CLASSTYPE_REAR,
            timestamp_signal=sig.SIGTIMESTAMP_REAR,
        )
        test_result_left, description_left, list_of_errors_left = validate_cuboid_class_type(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_LEFT,
            class_signal=sig.CUBOID_CLASSTYPE_LEFT,
            timestamp_signal=sig.SIGTIMESTAMP_LEFT,
        )
        test_result_right, description_right, list_of_errors_right = validate_cuboid_class_type(
            reader=reader,
            number_of_objects_signal=sig.NUM_CUBOID_RIGHT,
            class_signal=sig.CUBOID_CLASSTYPE_RIGHT,
            timestamp_signal=sig.SIGTIMESTAMP_RIGHT,
        )

        front_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_CLASSTYPE_FRONT][0].split(".")[:-1])
        rear_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_CLASSTYPE_REAR][0].split(".")[:-1])
        left_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_CLASSTYPE_LEFT][0].split(".")[:-1])
        right_signal_name = ".".join(example_obj.get_properties()[sig.CUBOID_CLASSTYPE_RIGHT][0].split(".")[:-1])

        signal_summary[front_signal_name] = description_front
        signal_summary[rear_signal_name] = description_rear
        signal_summary[left_signal_name] = description_left
        signal_summary[right_signal_name] = description_right
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary=signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        # Explain the behaviour of the test case
        plot_titles.append("")
        plots.append("")
        remarks.append(
            f"This test will verify if the sizes of a cuboid are in a given range.<br>"
            f"The size is measured in meters [m].<br>"
            f"Cuboids have a class type of CAR({ct.CuboidClassTypes['CAR']}) , "
            f"CAR({ct.CuboidClassTypes['VAN']}) or TRUCK({ct.CuboidClassTypes['TRUCK']}).<br>"
        )

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

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif test_result == fc.NOT_ASSESSED:
            self.result.measured_result = DATA_NOK
        else:
            self.result.measured_result = FALSE

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2156562"],
            fc.TESTCASE_ID: ["41583"],
            fc.TEST_RESULT: [test_result],
        }

        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")

        self.result.details["Additional_results"] = result_df


@verifies(
    requirement="2156562",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_FxQbgAXoEe-CvvSfR2-7PA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F18557",
)
@testcase_definition(
    name="TPP TPP_ValidateCuboidClassTypeOutput",
    description="This test will verify the value of the class types for each TPP Cuboid",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class TestCuboidClassTypeOutput(TestCase):
    """Cuboid output class type test case."""

    custom_report = fh_tpp.TPPCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestCuboidClassTypeOutputTestStep,
        ]
