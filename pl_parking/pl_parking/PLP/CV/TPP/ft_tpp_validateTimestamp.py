"""TestCase: Validate timestamp. Timestamp should be ascending."""

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
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.CV.TPP.ft_helper as fh_tpp
from pl_parking.common_ft_helper import rep

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


FT_TPP = "FT_TPP_TIMESTAMP"
TPP_NUM_DETECTIONS_GRAPPA = "TPP_NUM_DETECTIONS_GRAPPA"


class TimestampSignals(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TPP_TS_FRONT = "TppTimestampFront"
        TPP_TS_LEFT = "TppTimestampLeft"
        TPP_TS_REAR = "TppTimestampRear"
        TPP_TS_RIGHT = "TppTimestampRight"
        GRAPPA_TS_FRONT = "GrappaTimestampFront"
        GRAPPA_TS_LEFT = "GrappaTimestampLeft"
        GRAPPA_TS_REAR = "GrappaTimestampRear"
        GRAPPA_TS_RIGHT = "GrappaTimestampRight"

    def get_properties(self):
        """Generate a string of signals to be read."""
        signal_dict = {}

        signal_dict[self.Columns.GRAPPA_TS_FRONT] = [".GRAPPA_FC_DATA.DetectionResults.sSigHeader.uiTimeStamp"]
        signal_dict[self.Columns.GRAPPA_TS_REAR] = [".GRAPPA_RC_DATA.DetectionResults.sSigHeader.uiTimeStamp"]
        signal_dict[self.Columns.GRAPPA_TS_LEFT] = [".GRAPPA_LSC_DATA.DetectionResults.sSigHeader.uiTimeStamp"]
        signal_dict[self.Columns.GRAPPA_TS_RIGHT] = [".GRAPPA_RSC_DATA.DetectionResults.sSigHeader.uiTimeStamp"]
        signal_dict[self.Columns.TPP_TS_FRONT] = [".TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp"]
        signal_dict[self.Columns.TPP_TS_REAR] = [".TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp"]
        signal_dict[self.Columns.TPP_TS_LEFT] = [".TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp"]
        signal_dict[self.Columns.TPP_TS_RIGHT] = [".TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp"]

        return signal_dict

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "ADC5xx_Device", "M7board.EM_Thread", "CarPC.EM_Thread", "MTA_ADC5"]

        self._properties = self.get_properties()


# example_obj = fh_tpp.TPPSignals()
example_obj = TimestampSignals()


def check_signal_availability(signal_definition, required_signal: str, list_of_available_signals: list) -> dict:
    """
    Check if the required signal is available in the current recording.
    :param signal_definition: The object with the signal definition
    :param required_signal: The name of the required signal.
    :param list_of_available_signals: The list with the available signals.
    :return: False if any checks fails, True otherwise.
    """
    # TODO: Refactor for R4.0
    signal_dict = {
        "ColumnName": required_signal,
        "SignalName": signal_definition.get_properties()[required_signal][0],
    }
    if required_signal not in list_of_available_signals:
        signal_dict["Availability"] = "Not Available"
    else:
        signal_dict["Availability"] = "Available"

    return signal_dict


def validate_timestamp(
    reader: pd.DataFrame, tpp_timestamp_signal: str, grappa_timestamp_signal: str
) -> (str, str, list):
    """
    Validate the timestamp for an instance of the camera and generate a report.
    test_result: The result of the evaluation.
    Will fail when the input timestamp does not match with the output timestamp.
    Will fail when the timestamp is not ascending.
    description: The status of the signal.
    list_of_errors: Usefully data about the errors found, as a list of dictionaries. Empty list if no errors founds.
    :param reader: DataFrame containing the signals read from the recording.
    :param tpp_timestamp_signal: The signal containing the output tpp timestamp.
    :param grappa_timestamp_signal: The signal containing the input grappa timestamp.
    :return: (test_result, description, list_of_errors)
    """
    list_of_errors = []
    test_result = fc.PASS

    tpp_signal_name = example_obj.get_properties()[tpp_timestamp_signal][0]
    grappa_signal_name = example_obj.get_properties()[grappa_timestamp_signal][0]

    # The input and output timestamp signals are required for the validation
    # If the signals are not available, the evaluation will not be performed
    description = ""
    available_signals = list(reader.columns)
    if tpp_timestamp_signal not in available_signals:
        test_result = fc.NOT_ASSESSED
        description = " ".join((description + f" The signal <b>{tpp_signal_name} not available</b>. ").split())
    if grappa_timestamp_signal not in available_signals:
        test_result = fc.NOT_ASSESSED
        description = " ".join((description + f" The signal <b>{grappa_signal_name} not available</b>. ").split())

    if test_result == fc.NOT_ASSESSED:
        description = " ".join(("Signals <b>NOT EVALUATED</b>. " + description).split())
    else:
        # Required signals are available so the evaluation can be done
        description = "The <b>evaluation</b> of the signal is <b>PASSED</b>."
        # The timestamp might not be synchronized and that might affect the evaluation

        last_ts = 0
        for idx, row in reader.iterrows():
            if int(str(idx)) > 3:  # The first timestamps will be skipped because might not be initialized
                if row[tpp_timestamp_signal] != row[grappa_timestamp_signal]:
                    err = {
                        "tpp_ts": int(row[tpp_timestamp_signal]),
                        "grappa_ts": int(row[grappa_timestamp_signal]),
                        "error": "input timestamp is not passed as output timestamp",
                        "tpp_ts_name": tpp_signal_name,
                        "grappa_ts_name": grappa_signal_name,
                    }

                    # Store the description for the first error only
                    if test_result == fc.PASS:
                        description = " ".join(
                            f"The <b>evaluation</b> of the signals is <b>FAILED</b> because input timestamp "
                            f"{err['grappa_ts_name']} with value {err['grappa_ts']} is different to "
                            f"output timestamp {err['tpp_ts_name']} with value {err['tpp_ts']}.".split()
                        )

                    test_result = fc.FAIL
                    list_of_errors.append(err)

                    # The timestamp should be ascending
                    if row[tpp_timestamp_signal] - last_ts <= 0:
                        test_result = fc.FAIL
                        err = {
                            "tpp_ts": int(row[tpp_timestamp_signal]),
                            "grappa_ts": int(row[grappa_timestamp_signal]),
                            "error": "Timestamp is descending.",
                            "tpp_ts_name": tpp_signal_name,
                            "grappa_ts_name": grappa_signal_name,
                        }

                        if test_result == fc.PASS:
                            description = " ".join(
                                f"The <b>evaluation</b> of the signal is <b>FAILED</b> at output timestamp "
                                f"{err['tpp_ts_name']} with value {err['tpp_ts']} because it is not ascending.".split()
                            )

                        list_of_errors.append(err)
                # Store the previous timestamp to compare it with the current one
                last_ts = row[tpp_timestamp_signal]
    return test_result, description, list_of_errors


@teststep_definition(
    step_number=1,
    name="ValidateTimestamp",
    description="Check that output timestamp is the same with input timestamp and is ascending for"
    " each DynamicObject_t.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPP, TimestampSignals)
class TestTimestampOutputTestStep(TestStep):
    """Test step definition."""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.sig_sum = None

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        reader = self.readers[FT_TPP].signals
        test_result = fc.FAIL

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        reader = reader.iloc[4:]  # First timestamps might not be initialized, so remove them

        signal_summary = {}
        plot_titles, plots, remarks = rep([], 3)
        sig = TimestampSignals.Columns  # The strings for the signals

        # Validate timestamps for each side
        test_result_front, description_front, list_of_errors_front = validate_timestamp(
            reader, sig.TPP_TS_FRONT, sig.GRAPPA_TS_FRONT
        )
        test_result_rear, description_rear, list_of_errors_rear = validate_timestamp(
            reader, sig.TPP_TS_REAR, sig.GRAPPA_TS_REAR
        )
        test_result_left, description_left, list_of_errors_left = validate_timestamp(
            reader, sig.TPP_TS_LEFT, sig.GRAPPA_TS_LEFT
        )
        test_result_right, description_right, list_of_errors_right = validate_timestamp(
            reader, sig.TPP_TS_RIGHT, sig.GRAPPA_TS_RIGHT
        )

        # Generate the summary report
        signal_summary[example_obj.get_properties()[sig.TPP_TS_FRONT][0]] = description_front
        signal_summary[example_obj.get_properties()[sig.TPP_TS_REAR][0]] = description_rear
        signal_summary[example_obj.get_properties()[sig.TPP_TS_LEFT][0]] = description_left
        signal_summary[example_obj.get_properties()[sig.TPP_TS_RIGHT][0]] = description_right
        remark = (
            "Input timestamp (provided by GRAPPA) should be the same as the output timestamp (provided by TPP) "
            "and should be ascending."
        )
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_remark=remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        # Create Plots for each instance only when the validation was done
        # Front Side
        if test_result_front != fc.NOT_ASSESSED:
            mts_ts = (reader.index.values - reader.index.values[0]) / 1000000  # [s]
            grappa_ts = (reader[sig.GRAPPA_TS_FRONT] - reader[sig.GRAPPA_TS_FRONT].iloc[0]) / 1000  # [ms]
            tpp_ts = (reader[sig.TPP_TS_FRONT] - reader[sig.TPP_TS_FRONT].iloc[0]) / 1000  # [ms]
            ts_error = grappa_ts - tpp_ts  # [ms]
            fig = go.Figure(
                go.Scatter(
                    x=mts_ts,
                    y=ts_error,
                    marker={"color": "red"},
                    name="Timestamp Error [ms]",
                    hovertemplate="Error: %{y} [ms]" + "<br>Time: %{x} [s]",
                )
            )
            fig["layout"]["yaxis"].update(title_text="Timestamp Error [ms]")
            fig["layout"]["xaxis"].update(title_text="Time [s]")
            fig.update_traces(showlegend=True)
            fig.add_hline(
                y=0,
                line_color="green",
                line_width=5,
                annotation_text="Valid Range",
                annotation_position="right top",
            )

            remark = (
                f"<b>Timestamp error</b> is computed by subtracting the TPP timestamp from the GRAPPA timestamp. <br>"
                f"<b>Valid Range</b> is at y=0 meaning the Timestamp Error should be 0. <br>"
                f"<b>TPP Timestamp:</b> {example_obj.get_properties()[sig.TPP_TS_FRONT][0]}.<br> "
                f"<b>GRAPPA Timestamp:</b> {example_obj.get_properties()[sig.GRAPPA_TS_FRONT][0]}.<br> "
            )

            plot_titles.append("Front Timestamp")
            plots.append(fig)
            remarks.append(remark)

        # Rear Side
        if test_result_rear != fc.NOT_ASSESSED:
            mts_ts = (reader.index.values - reader.index.values[0]) / 1000000  # [s]
            grappa_ts = (reader[sig.GRAPPA_TS_REAR] - reader[sig.GRAPPA_TS_REAR].iloc[0]) / 1000  # [ms]
            tpp_ts = (reader[sig.TPP_TS_REAR] - reader[sig.TPP_TS_REAR].iloc[0]) / 1000  # [ms]
            ts_error = grappa_ts - tpp_ts  # [ms]
            fig = go.Figure(
                go.Scatter(
                    x=mts_ts,
                    y=ts_error,
                    marker={"color": "red"},
                    name="Timestamp Error [ms]",
                    hovertemplate="Error: %{y} [ms]" + "<br>Time: %{x} [s]",
                )
            )
            fig["layout"]["yaxis"].update(title_text="Timestamp Error [ms]")
            fig["layout"]["xaxis"].update(title_text="Time [s]")
            fig.update_traces(showlegend=True)
            fig.add_hline(
                y=0,
                line_color="green",
                line_width=5,
                annotation_text="Valid Range",
                annotation_position="right top",
            )

            remark = (
                f"<b>Timestamp error</b> is computed by subtracting the TPP timestamp from the GRAPPA timestamp. <br>"
                f"<b>Valid Range</b> is at y=0 meaning the Timestamp Error should be 0. <br>"
                f"<b>TPP Timestamp:</b> {example_obj.get_properties()[sig.TPP_TS_REAR][0]}.<br> "
                f"<b>GRAPPA Timestamp:</b> {example_obj.get_properties()[sig.GRAPPA_TS_REAR][0]}.<br> "
            )

            plot_titles.append("Rear Timestamp")
            plots.append(fig)
            remarks.append(remark)

        # Left Side
        if test_result_left != fc.NOT_ASSESSED:
            mts_ts = (reader.index.values - reader.index.values[0]) / 1000000  # [s]
            grappa_ts = (reader[sig.GRAPPA_TS_LEFT] - reader[sig.GRAPPA_TS_LEFT].iloc[0]) / 1000  # [ms]
            tpp_ts = (reader[sig.TPP_TS_LEFT] - reader[sig.TPP_TS_LEFT].iloc[0]) / 1000  # [ms]
            ts_error = grappa_ts - tpp_ts  # [ms]
            fig = go.Figure(
                go.Scatter(
                    x=mts_ts,
                    y=ts_error,
                    marker={"color": "red"},
                    name="Timestamp Error [ms]",
                    hovertemplate="Error: %{y} [ms]" + "<br>Time: %{x} [s]",
                )
            )
            fig["layout"]["yaxis"].update(title_text="Timestamp Error [ms]")
            fig["layout"]["xaxis"].update(title_text="Time [s]")
            fig.update_traces(showlegend=True)
            fig.add_hline(
                y=0,
                line_color="green",
                line_width=5,
                annotation_text="Valid Range",
                annotation_position="right top",
            )

            remark = (
                f"<b>Timestamp error</b> is computed by subtracting the TPP timestamp from the GRAPPA timestamp. <br>"
                f"<b>Valid Range</b> is at y=0 meaning the Timestamp Error should be 0. <br>"
                f"<b>TPP Timestamp:</b> {example_obj.get_properties()[sig.TPP_TS_LEFT][0]}.<br> "
                f"<b>GRAPPA Timestamp:</b> {example_obj.get_properties()[sig.GRAPPA_TS_LEFT][0]}.<br> "
            )

            plot_titles.append("Left Timestamp")
            plots.append(fig)
            remarks.append(remark)

        # Right Side
        if test_result_right != fc.NOT_ASSESSED:
            mts_ts = (reader.index.values - reader.index.values[0]) / 1000000  # [s]
            grappa_ts = (reader[sig.GRAPPA_TS_RIGHT] - reader[sig.GRAPPA_TS_RIGHT].iloc[0]) / 1000  # [ms]
            tpp_ts = (reader[sig.TPP_TS_RIGHT] - reader[sig.TPP_TS_RIGHT].iloc[0]) / 1000  # [ms]
            ts_error = grappa_ts - tpp_ts  # [ms]
            fig = go.Figure(
                go.Scatter(
                    x=mts_ts,
                    y=ts_error,
                    marker={"color": "red"},
                    name="Timestamp Error [ms]",
                    hovertemplate="Error: %{y} [ms]" + "<br>Time: %{x} [s]",
                )
            )
            fig["layout"]["yaxis"].update(title_text="Timestamp Error [ms]")
            fig["layout"]["xaxis"].update(title_text="Time [s]")
            fig.update_traces(showlegend=True)
            fig.add_hline(
                y=0,
                line_color="green",
                line_width=5,
                annotation_text="Valid Range",
                annotation_position="right top",
            )

            remark = (
                f"<b>Timestamp error</b> is computed by subtracting the TPP timestamp from the GRAPPA timestamp. <br>"
                f"<b>Valid Range</b> is at y=0 meaning the Timestamp Error should be 0. <br>"
                f"<b>TPP Timestamp:</b> {example_obj.get_properties()[sig.TPP_TS_RIGHT][0]}.<br> "
                f"<b>GRAPPA Timestamp</b>: {example_obj.get_properties()[sig.GRAPPA_TS_RIGHT][0]}.<br> "
            )

            plot_titles.append("Right Timestamp")
            plots.append(fig)
            remarks.append(remark)

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
        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1647399"],
            fc.TESTCASE_ID: ["46225"],
            fc.TEST_RESULT: [test_result],
        }

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif test_result == fc.NOT_ASSESSED:
            self.result.measured_result = DATA_NOK
        else:
            self.result.measured_result = FALSE

        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")

        self.result.details["Additional_results"] = result_df


@verifies(
    requirement="1647399",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_EjL-AHceEe6n7Ow9oWyCxw&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F18557&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg",
)
@testcase_definition(
    name="TPP ValidateTimestamp",
    description="Check that output timestamp is the same with input timestamp and is ascending for each"
    " DynamicObject_t.",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class TestTimestampOutput(TestCase):
    """Timestamp test case."""

    custom_report = fh_tpp.TPPCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestTimestampOutputTestStep,
        ]
