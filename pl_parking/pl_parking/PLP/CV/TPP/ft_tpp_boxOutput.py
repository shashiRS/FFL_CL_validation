"""TestCases performing all necessary checks for box output."""

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

FT_TPP = "FT_TPP_BOX_OUTPUT"
example_obj = tpp_reader_r4.TPPSignals()


# TODO: Check the required names for test-step definition


def validate_box_sizes(
    reader: pd.DataFrame,
    number_of_objects_signal: str,
    class_signal: str,
    width_signal: str,
    height_signal: str,
    timestamp_signal: str,
) -> (str, str, list):
    """
    Validate the width and height for each detection.
    test_result: PASS/FAIL.
    description: The status of the signal.
    list_of_errors: Usefully data about the errors found. Empty list if no errors founds.
    :param reader: DataFrame containing the signals read from the recording.
    :param number_of_objects_signal: The signal containing the number of objects.
    :param class_signal: The signal string containing the class type.
    :param width_signal: The signal string containing the width.
    :param height_signal: The signal string containing the height.
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
    ):
        for _, row in reader.iterrows():  # Iterate all frames
            n = int(row[number_of_objects_signal])
            ts = int(row[timestamp_signal])
            for i in range(n):  # Iterate all detections for a frame
                class_type = row[(class_signal, i)]
                width = row[(width_signal, i)]
                height = row[(height_signal, i)]

                error_dict = {
                    "ts": ts,
                    "id": int(i),
                    "class_type": int(class_type),
                    "width": width,
                    "height": height,
                    "width_signal_name": example_obj.get_properties()[width_signal][0],
                    "height_signal_name": example_obj.get_properties()[height_signal][0],
                }

                if (
                    class_type == ct.BoxClassTypes["PEDESTRIAN"]
                    or class_type == ct.BoxClassTypes["TWOWHEELER"]
                    or class_type == ct.BoxClassTypes["SHOPPINGCART"]
                    or class_type == ct.BoxClassTypes["ANIMAL"]
                ):
                    # Get the class name based on the class id
                    class_name = "UNKNOWN"
                    for key, value in ct.BoxClassTypes.items():
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


def validate_box_yaw(
    reader: pd.DataFrame, number_of_objects_signal: str, class_signal: str, yaw_signal: str, timestamp_signal: str
) -> (str, str, list):
    """
    Validate the yaw for each detection with box class.
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
                    class_type == ct.BoxClassTypes["PEDESTRIAN"]
                    or class_type == ct.BoxClassTypes["TWOWHEELER"]
                    or class_type == ct.BoxClassTypes["SHOPPINGCART"]
                    or class_type == ct.BoxClassTypes["ANIMAL"]
                ):
                    # Get the class name based on the class id
                    class_name = "UNKNOWN"
                    for key, value in ct.BoxClassTypes.items():
                        if value == class_type:
                            class_name = key

                    error_dict["class_name"] = class_name

                    PI = 3.141592653589  # [radians]
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


def validate_box_confidence(
    reader: pd.DataFrame,
    number_of_objects_signal: str,
    class_signal: str,
    confidence_signal: str,
    timestamp_signal: str,
) -> (str, str, list):
    """
    Validate the yaw for each detection with box class.
    test_result: PASS/FAIL.
    description: The status of the signal.
    list_of_errors: Usefully data about the errors found. Empty list if no errors founds.
    :param reader: DataFrame containing the signals read from the recording.
    :param number_of_objects_signal: The signal containing the number of objects.
    :param class_signal: The signal string containing the class type.
    :param confidence_signal: The signal string containing the yaw.
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

                error_dict = {}
                error_dict["ts"] = ts
                error_dict["id"] = int(i)
                error_dict["class_type"] = int(class_type)
                error_dict["confidence"] = confidence
                error_dict["confidence_signal_name"] = example_obj.get_properties()[confidence_signal][0]

                if (
                    class_type == ct.BoxClassTypes["PEDESTRIAN"]
                    or class_type == ct.BoxClassTypes["TWOWHEELER"]
                    or class_type == ct.BoxClassTypes["SHOPPINGCART"]
                    or class_type == ct.BoxClassTypes["ANIMAL"]
                ):
                    # Get the class name based on the class id
                    class_name = "UNKNOWN"
                    for key, value in ct.BoxClassTypes.items():
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


def validate_box_center_point(
    reader: pd.DataFrame,
    number_of_objects_signal: str,
    class_signal: str,
    center_x_signal: str,
    center_y_signal: str,
    timestamp_signal: str,
    camera_name: str,
) -> (str, str, list):
    """
    Validate the position of the center point for each detection with box class.
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
                    class_type == ct.BoxClassTypes["PEDESTRIAN"]
                    or class_type == ct.BoxClassTypes["TWOWHEELER"]
                    or class_type == ct.BoxClassTypes["SHOPPINGCART"]
                    or class_type == ct.BoxClassTypes["ANIMAL"]
                ):
                    # Get the class name based on the class id
                    class_name = "UNKNOWN"
                    for key, value in ct.BoxClassTypes.items():
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


def validate_box_class_type(
    reader: pd.DataFrame,
    number_of_objects_signal: str,
    class_signal: str,
    timestamp_signal: str,
) -> (str, str, list):
    """
    Validate the class id for each detection with box class.
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
                    class_type != ct.BoxClassTypes["PEDESTRIAN"]
                    and class_type != ct.BoxClassTypes["TWOWHEELER"]
                    and class_type != ct.BoxClassTypes["SHOPPINGCART"]
                    and class_type != ct.BoxClassTypes["ANIMAL"]
                ):
                    # Get the class name based on the class id
                    class_name = "UNKNOWN"

                    # TODO: Modify for R4
                    test_result = fc.FAIL
                    error_dict["description"] = "class id is unknown"
                    error_dict["value"] = class_type
                    error_dict["expected_result"] = "PEDESTRIAN/TWOWHEELER/SHOPPINGCART/ANIMAL"

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
    name="TPP_ValidateBoxSizesOutput",
    description="This test will verify the value of the sizes for each sub-class of the DynamicObject_t with Box class",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPP, tpp_reader_r4.TPPSignals)
class TestBoxSizesOutputTestStep(TestStep):
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

        test_result_front, description_front, list_of_errors_front = validate_box_sizes(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_FRONT,
            class_signal=sig.BOX_CLASSTYPE_FRONT,
            width_signal=sig.BOX_WIDTH_FRONT,
            height_signal=sig.BOX_HEIGHT_FRONT,
            timestamp_signal=sig.SIGTIMESTAMP_FRONT,
        )
        test_result_rear, description_rear, list_of_errors_rear = validate_box_sizes(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_REAR,
            class_signal=sig.BOX_CLASSTYPE_REAR,
            width_signal=sig.BOX_WIDTH_REAR,
            height_signal=sig.BOX_HEIGHT_REAR,
            timestamp_signal=sig.SIGTIMESTAMP_REAR,
        )
        test_result_left, description_left, list_of_errors_left = validate_box_sizes(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_LEFT,
            class_signal=sig.BOX_CLASSTYPE_LEFT,
            width_signal=sig.BOX_WIDTH_LEFT,
            height_signal=sig.BOX_HEIGHT_LEFT,
            timestamp_signal=sig.SIGTIMESTAMP_LEFT,
        )
        test_result_right, description_right, list_of_errors_right = validate_box_sizes(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_RIGHT,
            class_signal=sig.BOX_CLASSTYPE_RIGHT,
            width_signal=sig.BOX_WIDTH_RIGHT,
            height_signal=sig.BOX_HEIGHT_RIGHT,
            timestamp_signal=sig.SIGTIMESTAMP_RIGHT,
        )

        front_signal_name = ".".join(example_obj.get_properties()[sig.BOX_WIDTH_FRONT][0].split(".")[:-1])
        rear_signal_name = ".".join(example_obj.get_properties()[sig.BOX_WIDTH_REAR][0].split(".")[:-1])
        left_signal_name = ".".join(example_obj.get_properties()[sig.BOX_WIDTH_LEFT][0].split(".")[:-1])
        right_signal_name = ".".join(example_obj.get_properties()[sig.BOX_WIDTH_RIGHT][0].split(".")[:-1])

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
            f"This test will verify if the sizes of a bounding box are in a given range.<br>"
            f"The size is measured in meters [m].<br>"
            f"Bounding boxes have a class type of PEDESTRIAN({ct.BoxClassTypes['PEDESTRIAN']}), "
            f"TWOWHEELER({ct.BoxClassTypes['TWOWHEELER']}), SHOPPINGCART({ct.BoxClassTypes['SHOPPINGCART']}) "
            f"or ANIMAL({ct.BoxClassTypes['ANIMAL']}).<br>"
            f"The range of the sizes are the following: <br>"
            f"{ct.ObjectSizes['PEDESTRIAN']['width']['min']} < pedestrian width < {ct.ObjectSizes['PEDESTRIAN']['width']['max']}<br>"
            f"{ct.ObjectSizes['PEDESTRIAN']['height']['min']} < pedestrian height < {ct.ObjectSizes['PEDESTRIAN']['height']['max']}<br>"
            f"{ct.ObjectSizes['TWOWHEELER']['width']['min']} < twowheeler width < {ct.ObjectSizes['TWOWHEELER']['width']['max']}<br>"
            f"{ct.ObjectSizes['TWOWHEELER']['height']['min']} < twowheeler height < {ct.ObjectSizes['TWOWHEELER']['height']['max']}<br>"
            f"{ct.ObjectSizes['SHOPPINGCART']['width']['min']} < shopping cart width < {ct.ObjectSizes['SHOPPINGCART']['width']['max']}<br>"
            f"{ct.ObjectSizes['SHOPPINGCART']['height']['min']} < shopping cart height < {ct.ObjectSizes['SHOPPINGCART']['height']['max']}<br>"
            f"{ct.ObjectSizes['ANIMAL']['width']['min']} < animal width < {ct.ObjectSizes['ANIMAL']['width']['max']}<br>"
            f"{ct.ObjectSizes['ANIMAL']['height']['min']} < animal height < {ct.ObjectSizes['ANIMAL']['height']['max']}<br>"
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
            fc.REQ_ID: ["1646509"],
            fc.TESTCASE_ID: ["41645"],
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
    requirement="1646509",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_nlLTYHcZEe6n7Ow9oWyCxw&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F18557",
)
@testcase_definition(
    name="TPP TPP_ValidateBoxSizesOutput",
    description="This test will verify the value of the sizes for each sub-class of the DynamicObject_t with Box class",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class TestBoxSizesOutput(TestCase):
    """Output box sizes test case."""

    custom_report = fh_tpp.TPPCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestBoxSizesOutputTestStep,
        ]


@teststep_definition(
    step_number=1,
    name="TPP_ValidateBoxYawAngleOutput",
    description="This test will verify the yaw angle for each TPP Box",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPP, tpp_reader_r4.TPPSignals)
class TestBoxYawOutputTestStep(TestStep):
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

        test_result_front, description_front, list_of_errors_front = validate_box_yaw(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_FRONT,
            class_signal=sig.BOX_CLASSTYPE_FRONT,
            yaw_signal=sig.BOX_YAW_FRONT,
            timestamp_signal=sig.SIGTIMESTAMP_FRONT,
        )
        test_result_rear, description_rear, list_of_errors_rear = validate_box_yaw(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_REAR,
            class_signal=sig.BOX_CLASSTYPE_REAR,
            yaw_signal=sig.BOX_YAW_REAR,
            timestamp_signal=sig.SIGTIMESTAMP_REAR,
        )
        test_result_left, description_left, list_of_errors_left = validate_box_yaw(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_LEFT,
            class_signal=sig.BOX_CLASSTYPE_LEFT,
            yaw_signal=sig.BOX_YAW_LEFT,
            timestamp_signal=sig.SIGTIMESTAMP_LEFT,
        )
        test_result_right, description_right, list_of_errors_right = validate_box_yaw(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_RIGHT,
            class_signal=sig.BOX_CLASSTYPE_RIGHT,
            yaw_signal=sig.BOX_YAW_RIGHT,
            timestamp_signal=sig.SIGTIMESTAMP_RIGHT,
        )

        front_signal_name = ".".join(example_obj.get_properties()[sig.BOX_YAW_FRONT][0].split(".")[:-1])
        rear_signal_name = ".".join(example_obj.get_properties()[sig.BOX_YAW_REAR][0].split(".")[:-1])
        left_signal_name = ".".join(example_obj.get_properties()[sig.BOX_YAW_LEFT][0].split(".")[:-1])
        right_signal_name = ".".join(example_obj.get_properties()[sig.BOX_YAW_RIGHT][0].split(".")[:-1])

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
            f"This test will verify if the yaw of a bounding box is in a given range.<br>"
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
            fc.TESTCASE_ID: ["41648"],
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
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_PKcNYHcaEe6n7Ow9oWyCxw&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F18557",
)
@testcase_definition(
    name="TPP TPP_ValidateBoxYawOutput",
    description="This test will verify the value of the yaw angle for each TPP Box",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class TestBoxYawOutput(TestCase):
    """Output box yaw test case."""

    custom_report = fh_tpp.TPPCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestBoxYawOutputTestStep,
        ]


@teststep_definition(
    step_number=1,
    name="TPP_ValidateBoxConfidenceOutput",
    description="This test will verify the confidence for each TPP Box",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPP, tpp_reader_r4.TPPSignals)
class TestBoxConfidenceOutputTestStep(TestStep):
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

        test_result_front, description_front, list_of_errors_front = validate_box_confidence(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_FRONT,
            class_signal=sig.BOX_CLASSTYPE_FRONT,
            confidence_signal=sig.BOX_CONFIDENCE_FRONT,
            timestamp_signal=sig.SIGTIMESTAMP_FRONT,
        )
        test_result_rear, description_rear, list_of_errors_rear = validate_box_confidence(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_REAR,
            class_signal=sig.BOX_CLASSTYPE_REAR,
            confidence_signal=sig.BOX_CONFIDENCE_REAR,
            timestamp_signal=sig.SIGTIMESTAMP_REAR,
        )
        test_result_left, description_left, list_of_errors_left = validate_box_confidence(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_LEFT,
            class_signal=sig.BOX_CLASSTYPE_LEFT,
            confidence_signal=sig.BOX_CONFIDENCE_LEFT,
            timestamp_signal=sig.SIGTIMESTAMP_LEFT,
        )
        test_result_right, description_right, list_of_errors_right = validate_box_confidence(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_RIGHT,
            class_signal=sig.BOX_CLASSTYPE_RIGHT,
            confidence_signal=sig.BOX_CONFIDENCE_RIGHT,
            timestamp_signal=sig.SIGTIMESTAMP_RIGHT,
        )

        front_signal_name = ".".join(example_obj.get_properties()[sig.BOX_CONFIDENCE_FRONT][0].split(".")[:-1])
        rear_signal_name = ".".join(example_obj.get_properties()[sig.BOX_CONFIDENCE_REAR][0].split(".")[:-1])
        left_signal_name = ".".join(example_obj.get_properties()[sig.BOX_CONFIDENCE_LEFT][0].split(".")[:-1])
        right_signal_name = ".".join(example_obj.get_properties()[sig.BOX_CONFIDENCE_RIGHT][0].split(".")[:-1])

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
            "This test will verify if the bounding box of a bounding box is in a given range.<br>"
            "0 < confidence < 1<br>"
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
            fc.TESTCASE_ID: ["41588"],
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
    requirement="1646518",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_pGgt0HcaEe6n7Ow9oWyCxw&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F18557&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg",
)
@testcase_definition(
    name="TPP TPP_ValidateBoxConfidenceOutput",
    description="This test will verify the value of the confidence for each TPP Box",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class TestBoxConfidenceOutput(TestCase):
    """Output box confidence test case."""

    custom_report = fh_tpp.TPPCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestBoxConfidenceOutputTestStep,
        ]


@teststep_definition(
    step_number=1,
    name="TPP_ValidateBoxCenterPointOutput",
    description="This test will verify the center point for each TPP Box",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPP, tpp_reader_r4.TPPSignals)
class TestBoxCenterPointOutputTestStep(TestStep):
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

        test_result_front, description_front, list_of_errors_front = validate_box_center_point(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_FRONT,
            class_signal=sig.BOX_CLASSTYPE_FRONT,
            center_x_signal=sig.BOX_CENTERX_FRONT,
            center_y_signal=sig.BOX_CENTERY_FRONT,
            camera_name="FRONT",
            timestamp_signal=sig.SIGTIMESTAMP_FRONT,
        )
        test_result_rear, description_rear, list_of_errors_rear = validate_box_center_point(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_REAR,
            class_signal=sig.BOX_CLASSTYPE_REAR,
            center_x_signal=sig.BOX_CENTERX_REAR,
            center_y_signal=sig.BOX_CENTERY_REAR,
            camera_name="REAR",
            timestamp_signal=sig.SIGTIMESTAMP_REAR,
        )
        test_result_left, description_left, list_of_errors_left = validate_box_center_point(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_LEFT,
            class_signal=sig.BOX_CLASSTYPE_LEFT,
            center_x_signal=sig.BOX_CENTERX_LEFT,
            center_y_signal=sig.BOX_CENTERY_LEFT,
            camera_name="LEFT",
            timestamp_signal=sig.SIGTIMESTAMP_LEFT,
        )
        test_result_right, description_right, list_of_errors_right = validate_box_center_point(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_RIGHT,
            class_signal=sig.BOX_CLASSTYPE_RIGHT,
            center_x_signal=sig.BOX_CENTERX_RIGHT,
            center_y_signal=sig.BOX_CENTERY_RIGHT,
            camera_name="RIGHT",
            timestamp_signal=sig.SIGTIMESTAMP_RIGHT,
        )

        front_signal_name = ".".join(example_obj.get_properties()[sig.BOX_CENTERX_FRONT][0].split("."))
        rear_signal_name = ".".join(example_obj.get_properties()[sig.BOX_CENTERX_REAR][0].split("."))
        left_signal_name = ".".join(example_obj.get_properties()[sig.BOX_CENTERX_LEFT][0].split("."))
        right_signal_name = ".".join(example_obj.get_properties()[sig.BOX_CENTERX_RIGHT][0].split("."))

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
            "This test will verify if the center point of a bounding box is in a given camera range.<br>"
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
            fc.TESTCASE_ID: ["41647"],
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
    name="TPP TPP_ValidateBoxCenterPointOutput",
    description="This test will verify the value of the center point for each TPP Box",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class TestBoxClassTypeOutput(TestCase):
    """Output box class type test case."""

    custom_report = fh_tpp.TPPCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestBoxCenterPointOutputTestStep,
        ]


@teststep_definition(
    step_number=1,
    name="TPP_ValidateBoxClassTypeOutput",
    description="This test will verify the class type for each TPP Box",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPP, tpp_reader_r4.TPPSignals)
class TestBoxClassTypeOutputTestStep(TestStep):
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

        test_result_front, description_front, list_of_errors_front = validate_box_class_type(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_FRONT,
            class_signal=sig.BOX_CLASSTYPE_FRONT,
            timestamp_signal=sig.SIGTIMESTAMP_FRONT,
        )
        test_result_rear, description_rear, list_of_errors_rear = validate_box_class_type(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_REAR,
            class_signal=sig.BOX_CLASSTYPE_REAR,
            timestamp_signal=sig.SIGTIMESTAMP_REAR,
        )
        test_result_left, description_left, list_of_errors_left = validate_box_class_type(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_LEFT,
            class_signal=sig.BOX_CLASSTYPE_LEFT,
            timestamp_signal=sig.SIGTIMESTAMP_LEFT,
        )
        test_result_right, description_right, list_of_errors_right = validate_box_class_type(
            reader=reader,
            number_of_objects_signal=sig.NUM_BBOX_RIGHT,
            class_signal=sig.BOX_CLASSTYPE_RIGHT,
            timestamp_signal=sig.SIGTIMESTAMP_RIGHT,
        )

        front_signal_name = ".".join(example_obj.get_properties()[sig.BOX_CLASSTYPE_FRONT][0].split(".")[:-1])
        rear_signal_name = ".".join(example_obj.get_properties()[sig.BOX_CLASSTYPE_REAR][0].split(".")[:-1])
        left_signal_name = ".".join(example_obj.get_properties()[sig.BOX_CLASSTYPE_LEFT][0].split(".")[:-1])
        right_signal_name = ".".join(example_obj.get_properties()[sig.BOX_CLASSTYPE_RIGHT][0].split(".")[:-1])

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
            f"This test will verify if the sizes of a bounding box are in a given range.<br>"
            f"The size is measured in meters [m].<br>"
            f"Bounding boxes have a class type of PEDESTRIAN({ct.BoxClassTypes['PEDESTRIAN']}), "
            f"TWOWHEELER({ct.BoxClassTypes['TWOWHEELER']}), SHOPPINGCART({ct.BoxClassTypes['SHOPPINGCART']}) "
            f"or ANIMAL({ct.BoxClassTypes['ANIMAL']}).<br>"
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
            fc.REQ_ID: ["1650844"],
            fc.TESTCASE_ID: ["41647"],
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
    requirement="1650844",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_gxqYYHc-Ee6n7Ow9oWyCxw&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F18557&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg",
)
@testcase_definition(
    name="TPP TPP_ValidateBoxClassTypeOutput",
    description="This test will verify the value of the class type for each TPP Box",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class TestBoxCenterPointOutput(TestCase):
    """Output box center point test case."""

    custom_report = fh_tpp.TPPCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestBoxClassTypeOutputTestStep,
        ]
