"""TestCases checking the maximum number of output detections of TPP."""

import logging
import os

import pandas as pd
import plotly.graph_objects as go
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

TPP_NUM_DETECTIONS = "TPP_NUM_DETECTIONS"
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


def isNumberOfObjectsValid(
    reader: pd.DataFrame, number_of_objects_signal: str, timestamp_signal: str, cycle_counter_signal: str
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
    :param cycle_counter_signal: The signal containing the cycle-counter.
    :return: (test_result, description, list_of_errors)
    """
    available_signals = reader.columns
    test_result = fc.PASS
    description = "The evaluation of the signal is <b>PASSED</b>."
    list_of_errors = []

    if (
        number_of_objects_signal in available_signals
        and timestamp_signal in available_signals
        and cycle_counter_signal in available_signals
    ):
        for _, row in reader.iterrows():
            if row[number_of_objects_signal] >= ct.TPP_MAX_NUMBER_OF_DETECTIONS or row[number_of_objects_signal] < 0:
                error_dict = {
                    "ts": int(row[timestamp_signal]),
                    "cycleCounter": int(row[cycle_counter_signal]),
                    "value": int(row[number_of_objects_signal]),
                    "description": "out of bounds",
                    "expected_result": f"[0, {ct.TPP_MAX_NUMBER_OF_DETECTIONS})",
                    "signal_name": example_obj.get_properties()[number_of_objects_signal][0],
                }
                list_of_errors.append(error_dict)
                if test_result != fc.FAIL:
                    description = " ".join(
                        f"The evaluation of the signal is <b>FAILED</b> at timestamp <b>{error_dict['ts']}</b> "
                        f"(Cycle Counter {error_dict['cycleCounter']}) with value <b>{error_dict['value']}</b> which is"
                        f" <b>{error_dict['description']}</b> ({error_dict['expected_result']}).".split()
                    )
                test_result = fc.FAIL
    else:
        test_result = fc.INPUT_MISSING
        description = " ".join("Signal <b>not evaluated</b> because it is not available.".split())

    return test_result, description, list_of_errors


@teststep_definition(
    step_number=1,
    name="TPP Number of objects Test",
    description=f"Check if the maximum number of objects is between [0, {ct.TPP_MAX_NUMBER_OF_DETECTIONS})",
    expected_result=BooleanResult(TRUE),
)
@register_signals(TPP_NUM_DETECTIONS, tpp_reader_r4.TPPSignals)
class TestNumberOfDetectionsTestStep(TestStep):
    """Test step definition."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test-step."""
        super().__init__()
        self.sig_sum = None

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        reader = self.readers[TPP_NUM_DETECTIONS]
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        signal_summary = {}
        plot_titles, plots, remarks = rep([], 3)

        sig = tpp_reader_r4.TPPSignals.Columns  # The strings for the signals

        reader = reader.iloc[10:]

        # Validate the front instance of the camera
        test_result_front1, description_front1, list_of_errors_front1 = isNumberOfObjectsValid(
            reader, sig.NUM_CUBOID_FRONT, sig.SIGTIMESTAMP_FRONT, sig.SIGCYCLECOUNTER_FRONT
        )
        test_result_front2, description_front2, list_of_errors_front2 = isNumberOfObjectsValid(
            reader, sig.NUM_BBOX_FRONT, sig.SIGTIMESTAMP_FRONT, sig.SIGCYCLECOUNTER_FRONT
        )

        # Validate the rear instance of the camera
        test_result_rear1, description_rear1, list_of_errors_rear1 = isNumberOfObjectsValid(
            reader, sig.NUM_CUBOID_REAR, sig.SIGTIMESTAMP_REAR, sig.SIGCYCLECOUNTER_REAR
        )
        test_result_rear2, description_rear2, list_of_errors_rear2 = isNumberOfObjectsValid(
            reader, sig.NUM_BBOX_REAR, sig.SIGTIMESTAMP_REAR, sig.SIGCYCLECOUNTER_REAR
        )

        # Validate the left instance of the camera
        test_result_left1, description_left1, list_of_errors_left1 = isNumberOfObjectsValid(
            reader, sig.NUM_CUBOID_LEFT, sig.SIGTIMESTAMP_LEFT, sig.SIGCYCLECOUNTER_LEFT
        )
        test_result_left2, description_left2, list_of_errors_left2 = isNumberOfObjectsValid(
            reader, sig.NUM_BBOX_LEFT, sig.SIGTIMESTAMP_LEFT, sig.SIGCYCLECOUNTER_LEFT
        )

        # Validate the right instance of the camera
        test_result_right1, description_right1, list_of_errors_right1 = isNumberOfObjectsValid(
            reader, sig.NUM_CUBOID_RIGHT, sig.SIGTIMESTAMP_RIGHT, sig.SIGCYCLECOUNTER_RIGHT
        )
        test_result_right2, description_right2, list_of_errors_right2 = isNumberOfObjectsValid(
            reader, sig.NUM_BBOX_RIGHT, sig.SIGTIMESTAMP_RIGHT, sig.SIGCYCLECOUNTER_RIGHT
        )

        # Generate the status of each instance
        signal_summary[example_obj.get_properties()[sig.NUM_CUBOID_FRONT][0]] = description_front1
        signal_summary[example_obj.get_properties()[sig.NUM_BBOX_FRONT][0]] = description_front2
        signal_summary[example_obj.get_properties()[sig.NUM_CUBOID_REAR][0]] = description_rear1
        signal_summary[example_obj.get_properties()[sig.NUM_BBOX_REAR][0]] = description_rear2
        signal_summary[example_obj.get_properties()[sig.NUM_CUBOID_LEFT][0]] = description_left1
        signal_summary[example_obj.get_properties()[sig.NUM_BBOX_LEFT][0]] = description_left2
        signal_summary[example_obj.get_properties()[sig.NUM_CUBOID_RIGHT][0]] = description_right1
        signal_summary[example_obj.get_properties()[sig.NUM_BBOX_RIGHT][0]] = description_right2

        remark = f"The number of objects should be between [0, {ct.TPP_MAX_NUMBER_OF_DETECTIONS})."
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
            test_result_front1 == fc.PASS
            and test_result_front2 == fc.PASS
            and test_result_rear1 == fc.PASS
            and test_result_rear2 == fc.PASS
            and test_result_left1 == fc.PASS
            and test_result_left2 == fc.PASS
            and test_result_right1 == fc.PASS
            and test_result_right2 == fc.PASS
        ):
            test_result = fc.PASS
        elif (
            test_result_front1 == fc.NOT_ASSESSED
            or test_result_front2 == fc.NOT_ASSESSED
            or test_result_rear1 == fc.NOT_ASSESSED
            or test_result_rear2 == fc.NOT_ASSESSED
            or test_result_left1 == fc.NOT_ASSESSED
            or test_result_left2 == fc.NOT_ASSESSED
            or test_result_right1 == fc.NOT_ASSESSED
            or test_result_right2 == fc.NOT_ASSESSED
        ):
            test_result = fc.NOT_ASSESSED
        else:
            test_result = fc.FAIL

        # In case of error on an instance, plot the number of objects and the errors
        if test_result_front1 == fc.FAIL or test_result_front2 == fc.FAIL:
            list_of_errors_front = list_of_errors_front1 + list_of_errors_front2
            front_errors_df = pd.DataFrame(list_of_errors_front)
            fig_front = go.Figure(
                go.Bar(
                    x=reader[sig.SIGCYCLECOUNTER_FRONT],
                    y=reader[sig.NUM_BBOX_FRONT],
                    name="Number of cuboids",
                    marker={"color": "blue"},
                    hovertemplate="NumberOfDetections: %{y}" + "<br>Cycle Counter: %{x}",
                )
            )
            fig_front.add_trace(
                go.Bar(
                    x=reader[sig.SIGCYCLECOUNTER_FRONT],
                    y=reader[sig.NUM_CUBOID_FRONT],
                    name="Number of bboxes",
                    marker={"color": "purple"},
                    hovertemplate="NumberOfDetections: %{y}" + "<br>Cycle Counter: %{x}",
                )
            )
            # Draw the upper limit
            fig_front.add_hrect(
                y0=0,
                y1=ct.TPP_MAX_NUMBER_OF_DETECTIONS,
                fillcolor="Green",
                annotation_text="Valid Range",
                annotation_position="right top",
                opacity=0.15,
            )
            # Display where the number of the detections is exceeding the limit
            fig_front.add_trace(
                go.Scatter(
                    x=front_errors_df["cycleCounter"],
                    y=front_errors_df["value"],
                    name="Invalid number of objects",
                    mode="markers",
                    marker={"color": "red"},
                    hovertemplate="Too Many Detections: %{y}" + "<br>Cycle Counter: %{x}",
                )
            )
            fig_front["layout"]["yaxis"].update(title_text="Number of Objects")
            fig_front["layout"]["xaxis"].update(title_text="Cycle Counter")
            remark = (
                f"<b>Failed</b> because the number of objects is not in [0, {ct.TPP_MAX_NUMBER_OF_DETECTIONS}).<br>"
                f"<b>Valid Range:</b> Lower limit at y=0, upper limit at y={ct.TPP_MAX_NUMBER_OF_DETECTIONS}. <br>"
                f"<b>Invalid number of objects:</b> Any number of objects out of Valid Range. <br>"
                f"<b>Number of cuboids:</b> {example_obj.get_properties()[sig.NUM_CUBOID_FRONT][0]}.<br>"
                f"<b>Number of bounding boxes:</b> {example_obj.get_properties()[sig.NUM_BBOX_FRONT][0]}.<br>"
                f"<b>Cycle counter:</b> {example_obj.get_properties()[sig.SIGCYCLECOUNTER_FRONT][0]}.<br>"
            )
            plot_titles.append("Number of Objects for Front Camera")
            plots.append(fig_front)
            remarks.append(remark)

        if test_result_rear1 == fc.FAIL or test_result_rear2 == fc.FAIL:
            list_of_errors_rear = list_of_errors_rear1 + list_of_errors_rear2
            rear_errors_df = pd.DataFrame(list_of_errors_rear)
            fig_rear = go.Figure(
                go.Bar(
                    x=reader[sig.SIGCYCLECOUNTER_REAR],
                    y=reader[sig.NUM_BBOX_REAR],
                    name="Number of bboxes",
                    marker={"color": "blue"},
                    hovertemplate="NumberOfDetections: %{y}" + "<br>Cycle Counter: %{x}",
                )
            )
            fig_rear.add_trace(
                go.Bar(
                    x=reader[sig.SIGCYCLECOUNTER_REAR],
                    y=reader[sig.NUM_CUBOID_REAR],
                    name="Number of cuboids",
                    marker={"color": "purple"},
                    hovertemplate="NumberOfDetections: %{y}" + "<br>Cycle Counter: %{x}",
                )
            )
            # Draw the upper limit
            fig_rear.add_hrect(
                y0=0,
                y1=ct.TPP_MAX_NUMBER_OF_DETECTIONS,
                fillcolor="Green",
                annotation_text="Valid Range",
                annotation_position="right top",
                opacity=0.15,
            )
            fig_rear.add_trace(
                go.Scatter(
                    x=rear_errors_df["cycleCounter"],
                    y=rear_errors_df["value"],
                    name="Invalid number of objects",
                    mode="markers",
                    marker={"color": "red"},
                    hovertemplate="Too Many Detections: %{y}" + "<br>Cycle Counter: %{x}",
                )
            )
            fig_rear["layout"]["yaxis"].update(title_text="Number of Objects")
            fig_rear["layout"]["xaxis"].update(title_text="Cycle Counter")
            remark = (
                f"<b>Failed</b> because the number of objects is not in [0, {ct.TPP_MAX_NUMBER_OF_DETECTIONS}).<br>"
                f"<b>Valid Range:</b> Lower limit at y=0, upper limit at y={ct.TPP_MAX_NUMBER_OF_DETECTIONS}. <br>"
                f"<b>Invalid number of objects:</b> Any number of objects out of Valid Range. <br>"
                f"<b>Number of cuboids:</b> {example_obj.get_properties()[sig.NUM_CUBOID_REAR][0]}.<br>"
                f"<b>Number of bounding boxes:</b> {example_obj.get_properties()[sig.NUM_BBOX_REAR][0]}.<br>"
                f"<b>Cycle counter:</b> {example_obj.get_properties()[sig.SIGCYCLECOUNTER_REAR][0]}.<br>"
            )
            plot_titles.append("Number of Objects for Rear Camera")
            plots.append(fig_rear)
            remarks.append(remark)

        if test_result_left1 == fc.FAIL or test_result_left2 == fc.FAIL:
            list_of_errors_left = list_of_errors_left1 + list_of_errors_left2
            left_errors_df = pd.DataFrame(list_of_errors_left)
            fig_left = go.Figure(
                go.Bar(
                    x=reader[sig.SIGCYCLECOUNTER_LEFT],
                    y=reader[sig.NUM_BBOX_LEFT],
                    name="Number of bboxes",
                    marker={"color": "blue"},
                    hovertemplate="NumberOfDetections: %{y}" + "<br>Cycle Counter: %{x}",
                )
            )
            fig_left.add_trace(
                go.Bar(
                    x=reader[sig.SIGCYCLECOUNTER_LEFT],
                    y=reader[sig.NUM_CUBOID_LEFT],
                    name="Number of cuboids",
                    marker={"color": "purple"},
                    hovertemplate="NumberOfDetections: %{y}" + "<br>Cycle Counter: %{x}",
                )
            )
            # Draw the upper limit
            fig_left.add_hrect(
                y0=0,
                y1=ct.TPP_MAX_NUMBER_OF_DETECTIONS,
                fillcolor="Green",
                annotation_text="Valid Range",
                annotation_position="right top",
                opacity=0.15,
            )

            fig_left.add_trace(
                go.Scatter(
                    x=left_errors_df["cycleCounter"],
                    y=left_errors_df["value"],
                    name="Invalid number of objects",
                    mode="markers",
                    marker={"color": "red"},
                    hovertemplate="Too Many Detections: %{y}" + "<br>Cycle Counter: %{x}",
                )
            )
            fig_left["layout"]["yaxis"].update(title_text="Number of Objects")
            fig_left["layout"]["xaxis"].update(title_text="Cycle Counter")
            remark = (
                f"<b>Failed</b> because the number of objects is not in [0, {ct.TPP_MAX_NUMBER_OF_DETECTIONS}).<br>"
                f"<b>Valid Range:</b> Lower limit at y=0, upper limit at y={ct.TPP_MAX_NUMBER_OF_DETECTIONS}. <br>"
                f"<b>Invalid number of objects:</b> Any number of objects out of Valid Range. <br>"
                f"<b>Number of cuboids:</b> {example_obj.get_properties()[sig.NUM_CUBOID_LEFT][0]}.<br>"
                f"<b>Number of bounding boxes:</b> {example_obj.get_properties()[sig.NUM_BBOX_LEFT][0]}.<br>"
                f"<b>Cycle counter:</b> {example_obj.get_properties()[sig.SIGCYCLECOUNTER_LEFT][0]}.<br>"
            )
            plot_titles.append("Number of Objects for Left Camera")
            plots.append(fig_left)
            remarks.append(remark)

        if test_result_right1 == fc.FAIL or test_result_right2 == fc.FAIL:
            list_of_errors_right = list_of_errors_right1 + list_of_errors_right2
            right_errors_df = pd.DataFrame(list_of_errors_right)
            fig_right = go.Figure(
                go.Bar(
                    x=reader[sig.SIGCYCLECOUNTER_RIGHT],
                    y=reader[sig.NUM_BBOX_RIGHT],
                    name="Number of bboxes",
                    marker={"color": "blue"},
                    hovertemplate="NumberOfDetections: %{y}" + "<br>Cycle Counter: %{x}",
                )
            )
            fig_right.add_trace(
                go.Bar(
                    x=reader[sig.SIGCYCLECOUNTER_RIGHT],
                    y=reader[sig.NUM_CUBOID_RIGHT],
                    name="Number of cuboids",
                    marker={"color": "purple"},
                    hovertemplate="NumberOfDetections: %{y}" + "<br>Cycle Counter: %{x}",
                )
            )
            # Draw the upper limit
            fig_right.add_hrect(
                y0=0,
                y1=ct.TPP_MAX_NUMBER_OF_DETECTIONS,
                fillcolor="Green",
                annotation_text="Valid Range",
                annotation_position="right top",
                opacity=0.15,
            )
            fig_right.add_trace(
                go.Scatter(
                    x=right_errors_df["cycleCounter"],
                    y=right_errors_df["value"],
                    name="Invalid number of objects",
                    mode="markers",
                    marker={"color": "red"},
                    hovertemplate="Too Many Detections: %{y}" + "<br>Cycle Counter: %{x}",
                )
            )
            fig_right["layout"]["yaxis"].update(title_text="Number of Objects")
            fig_right["layout"]["xaxis"].update(title_text="Cycle Counter")
            remark = (
                f"<b>Failed</b> because the number of objects is not in [0, {ct.TPP_MAX_NUMBER_OF_DETECTIONS}).<br>"
                f"<b>Valid Range:</b> Lower limit at y=0, upper limit at y={ct.TPP_MAX_NUMBER_OF_DETECTIONS}. <br>"
                f"<b>Invalid number of objects:</b> Any number of objects out of Valid Range. <br>"
                f"<b>Number of cuboids:</b> {example_obj.get_properties()[sig.NUM_CUBOID_RIGHT][0]}.<br>"
                f"<b>Number of bounding boxes:</b> {example_obj.get_properties()[sig.NUM_BBOX_RIGHT][0]}.<br>"
                f"<b>Cycle counter:</b> {example_obj.get_properties()[sig.SIGCYCLECOUNTER_RIGHT][0]}.<br>"
            )
            plot_titles.append("Number of Objects for Right Camera")
            plots.append(fig_right)
            remarks.append(remark)

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
    name="TPP NumberOfDetections",
    description=f"Number of objects should be between [0, {ct.TPP_MAX_NUMBER_OF_DETECTIONS}).",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class TestNumberOfDetections(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestNumberOfDetectionsTestStep,
        ]
