"""TestCases performing all necessary checks for the input signal state."""

import logging
import os

import pandas as pd
import plotly.graph_objects as go
from tsf.core.results import FALSE, TRUE, BooleanResult
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

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TPP_INPUTSIGSTATE = "TPP_INPUTSIGSTATE"


# Define reader for each camera
class TPPSigState(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        GRAPPA_DETECTION_SIG_STATUS_FRONT = "sigStatusGrappaFront"
        GRAPPA_DETECTION_TIMESTAMP_FRONT = "timeStampGrappaFront"
        TPP_OUTPUT_SIG_STATUS_FRONT = "sigStatusTppFront"
        TPP_OUTPUT_NUM_BBOXES_FRONT = "numBBoxTppFront"
        TPP_OUTPUT_NUM_CUBOIDS_FRONT = "numCuboidTppFront"

        GRAPPA_DETECTION_SIG_STATUS_REAR = "sigStatusGrappaRear"
        GRAPPA_DETECTION_TIMESTAMP_REAR = "timeStampGrappaRear"
        TPP_OUTPUT_SIG_STATUS_REAR = "sigStatusTppRear"
        TPP_OUTPUT_NUM_BBOXES_REAR = "numBBoxTppRear"
        TPP_OUTPUT_NUM_CUBOIDS_REAR = "numCuboidTppRear"

        GRAPPA_DETECTION_SIG_STATUS_LEFT = "sigStatusGrappaLeft"
        GRAPPA_DETECTION_TIMESTAMP_LEFT = "timeStampGrappaLeft"
        TPP_OUTPUT_SIG_STATUS_LEFT = "sigStatusTppLeft"
        TPP_OUTPUT_NUM_BBOXES_LEFT = "numBBoxTppLeft"
        TPP_OUTPUT_NUM_CUBOIDS_LEFT = "numCuboidTppLeft"

        GRAPPA_DETECTION_SIG_STATUS_RIGHT = "sigStatusGrappaRight"
        GRAPPA_DETECTION_TIMESTAMP_RIGHT = "timeStampGrappaRight"
        TPP_OUTPUT_SIG_STATUS_RIGHT = "sigStatusTppRight"
        TPP_OUTPUT_NUM_BBOXES_RIGHT = "numBBoxTppRight"
        TPP_OUTPUT_NUM_CUBOIDS_RIGHT = "numCuboidTppRight"

    def get_properties(self):
        """Generate a string of signals to be read."""
        signal_dict = {
            self.Columns.GRAPPA_DETECTION_SIG_STATUS_FRONT: ".GRAPPA_FC_DATA.DetectionResults.sSigHeader.eSigStatus",
            self.Columns.GRAPPA_DETECTION_TIMESTAMP_FRONT: ".GRAPPA_FC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
            self.Columns.TPP_OUTPUT_SIG_STATUS_FRONT: ".TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
            self.Columns.TPP_OUTPUT_NUM_BBOXES_FRONT: ".TPP_FC_DATA.pRum2ObjectDetection3DOutput.numberOfBBoxObjects",
            self.Columns.TPP_OUTPUT_NUM_CUBOIDS_FRONT: ".TPP_FC_DATA.pRum2ObjectDetection3DOutput.numberOfCuboidObjects",
            self.Columns.GRAPPA_DETECTION_SIG_STATUS_REAR: ".GRAPPA_RC_DATA.DetectionResults.sSigHeader.eSigStatus",
            self.Columns.GRAPPA_DETECTION_TIMESTAMP_REAR: ".GRAPPA_RC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
            self.Columns.TPP_OUTPUT_SIG_STATUS_REAR: ".TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
            self.Columns.TPP_OUTPUT_NUM_BBOXES_REAR: ".TPP_RC_DATA.pRum2ObjectDetection3DOutput.numberOfBBoxObjects",
            self.Columns.TPP_OUTPUT_NUM_CUBOIDS_REAR: ".TPP_RC_DATA.pRum2ObjectDetection3DOutput.numberOfCuboidObjects",
            self.Columns.GRAPPA_DETECTION_SIG_STATUS_LEFT: ".GRAPPA_LSC_DATA.DetectionResults.sSigHeader.eSigStatus",
            self.Columns.GRAPPA_DETECTION_TIMESTAMP_LEFT: ".GRAPPA_LSC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
            self.Columns.TPP_OUTPUT_SIG_STATUS_LEFT: ".TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
            self.Columns.TPP_OUTPUT_NUM_BBOXES_LEFT: ".TPP_LSC_DATA.pRum2ObjectDetection3DOutput.numberOfBBoxObjects",
            self.Columns.TPP_OUTPUT_NUM_CUBOIDS_LEFT: ".TPP_LSC_DATA.pRum2ObjectDetection3DOutput.numberOfCuboidObjects",
            self.Columns.GRAPPA_DETECTION_SIG_STATUS_RIGHT: ".GRAPPA_RSC_DATA.DetectionResults.sSigHeader.eSigStatus",
            self.Columns.GRAPPA_DETECTION_TIMESTAMP_RIGHT: ".GRAPPA_RSC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
            self.Columns.TPP_OUTPUT_SIG_STATUS_RIGHT: ".TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
            self.Columns.TPP_OUTPUT_NUM_BBOXES_RIGHT: ".TPP_RSC_DATA.pRum2ObjectDetection3DOutput.numberOfBBoxObjects",
            self.Columns.TPP_OUTPUT_NUM_CUBOIDS_RIGHT: ".TPP_RSC_DATA.pRum2ObjectDetection3DOutput.numberOfCuboidObjects",
        }

        return signal_dict

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "ADC5xx_Device", "M7board.EM_Thread", "CarPC.EM_Thread", "MTA_ADC5"]

        self._properties = self.get_properties()


example_obj = TPPSigState()


@teststep_definition(
    step_number=1,
    name="TPP Input Signal State Test",
    description="Check the input signal state",
    expected_result=BooleanResult(TRUE),
)
@register_signals(TPP_INPUTSIGSTATE, TPPSigState)
class TestInputSigStateTestStep(TestStep):
    """Test step definition."""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the test-step."""
        super().__init__()
        self.sig_sum = ""

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        reader = self.readers[TPP_INPUTSIGSTATE].signals
        reader = reader.iloc[4:]  # Skip the first frames because the values might not be initialized
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        test_result = fc.INPUT_MISSING  # Result initialization
        signal_summary = {}
        plot_titles, plots, remarks = fh.rep([], 3)

        description = "The <b>evaluation</b> of the signal is <b>PASSED</b>."

        list_of_errors = []

        # reader[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_FRONT] = [fc.AL_SIG_STATE_INVALID] * len(reader)

        for _, row in reader.iterrows():
            if row[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_FRONT] != fc.AL_SIG_STATE_OK:
                if (
                    row[TPPSigState.Columns.TPP_OUTPUT_NUM_BBOXES_FRONT] != 0
                    or row[TPPSigState.Columns.TPP_OUTPUT_NUM_CUBOIDS_FRONT] != 0
                ):
                    nrDetections = (
                        row[TPPSigState.Columns.TPP_OUTPUT_NUM_BBOXES_FRONT]
                        + row[TPPSigState.Columns.TPP_OUTPUT_NUM_CUBOIDS_FRONT]
                    )
                    error_dict = {
                        "ts": row[TPPSigState.Columns.GRAPPA_DETECTION_TIMESTAMP_FRONT],
                        "side": "Front",
                        "nrDetections": nrDetections,
                        "sigState": row[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_FRONT],
                    }
                    list_of_errors.append(error_dict)

            if row[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_REAR] != fc.AL_SIG_STATE_OK:
                if (
                    row[TPPSigState.Columns.TPP_OUTPUT_NUM_BBOXES_REAR] != 0
                    or row[TPPSigState.Columns.TPP_OUTPUT_NUM_CUBOIDS_REAR] != 0
                ):
                    nrDetections = (
                        row[TPPSigState.Columns.TPP_OUTPUT_NUM_BBOXES_REAR]
                        + row[TPPSigState.Columns.TPP_OUTPUT_NUM_CUBOIDS_REAR]
                    )
                    error_dict = {
                        "ts": row[TPPSigState.Columns.GRAPPA_DETECTION_TIMESTAMP_REAR],
                        "side": "Rear",
                        "nrDetections": nrDetections,
                        "sigState": row[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_REAR],
                    }
                    list_of_errors.append(error_dict)

            if row[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_LEFT] != fc.AL_SIG_STATE_OK:
                if (
                    row[TPPSigState.Columns.TPP_OUTPUT_NUM_BBOXES_LEFT] != 0
                    or row[TPPSigState.Columns.TPP_OUTPUT_NUM_CUBOIDS_LEFT] != 0
                ):
                    nrDetections = (
                        row[TPPSigState.Columns.TPP_OUTPUT_NUM_BBOXES_LEFT]
                        + row[TPPSigState.Columns.TPP_OUTPUT_NUM_CUBOIDS_LEFT]
                    )
                    error_dict = {
                        "ts": row[TPPSigState.Columns.GRAPPA_DETECTION_TIMESTAMP_LEFT],
                        "side": "Left",
                        "nrDetections": nrDetections,
                        "sigState": row[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_LEFT],
                    }
                    list_of_errors.append(error_dict)

            if row[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_RIGHT] != fc.AL_SIG_STATE_OK:
                if (
                    row[TPPSigState.Columns.TPP_OUTPUT_NUM_BBOXES_RIGHT] != 0
                    or row[TPPSigState.Columns.TPP_OUTPUT_NUM_CUBOIDS_RIGHT] != 0
                ):
                    nrDetections = (
                        row[TPPSigState.Columns.TPP_OUTPUT_NUM_BBOXES_RIGHT]
                        + row[TPPSigState.Columns.TPP_OUTPUT_NUM_CUBOIDS_RIGHT]
                    )
                    error_dict = {
                        "ts": row[TPPSigState.Columns.GRAPPA_DETECTION_TIMESTAMP_RIGHT],
                        "side": "Right",
                        "nrDetections": nrDetections,
                        "sigState": row[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_RIGHT],
                    }
                    list_of_errors.append(error_dict)

        signal_name_front = [
            example_obj.get_properties()[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_FRONT][:],
        ]
        signal_name_left = [
            example_obj.get_properties()[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_LEFT][:],
        ]
        signal_name_rear = [
            example_obj.get_properties()[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_REAR][:],
        ]
        signal_name_right = [
            example_obj.get_properties()[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_RIGHT][:],
        ]

        description_front = description
        description_left = description
        description_rear = description
        description_right = description

        if len(list_of_errors) > 0:
            test_result = fc.FAIL
            error_df = pd.DataFrame(list_of_errors)

            errors_front_df = error_df[error_df["side"] == "Front"]
            errors_left_df = error_df[error_df["side"] == "Left"]
            errors_rear_df = error_df[error_df["side"] == "Rear"]
            errors_right_df = error_df[error_df["side"] == "Right"]

            if len(errors_front_df) > 0:
                err = errors_front_df.iloc[0]
                description_front = " ".join(
                    f"The <b>evaluation</b> of the signals is <b>FAILED</b> at timestamp {err['ts']} because the "
                    f"signal state of the mandatory input from GRAPPA on the {err['side']} instance is {err['sigState']} and "
                    f"the input was processed resulting in a number of {err['nrDetections']} detections.".split()
                )

            if len(errors_left_df) > 0:
                err = errors_left_df.iloc[0]
                description_left = " ".join(
                    f"The <b>evaluation</b> of the signals is <b>FAILED</b> at timestamp {err['ts']} because the "
                    f"signal state of the mandatory input from GRAPPA on the {err['side']} instance is {err['sigState']} and "
                    f"the input was processed resulting in a number of {err['nrDetections']} detections.".split()
                )

            if len(errors_rear_df) > 0:
                err = errors_rear_df.iloc[0]
                description_rear = " ".join(
                    f"The <b>evaluation</b> of the signals is <b>FAILED</b> at timestamp {err['ts']} because the "
                    f"signal state of the mandatory input from GRAPPA on the {err['side']} instance is {err['sigState']} and "
                    f"the input was processed resulting in a number of {err['nrDetections']} detections.".split()
                )

            if len(errors_right_df) > 0:
                err = errors_right_df.iloc[0]
                description_right = " ".join(
                    f"The <b>evaluation</b> of the signals is <b>FAILED</b> at timestamp {err['ts']} because the "
                    f"signal state of the mandatory input from GRAPPA on the {err['side']} instance is {err['sigState']} and "
                    f"the input was processed resulting in a number of {err['nrDetections']} detections.".split()
                )

            signal_summary[".GRAPPA_FC_DATA.DetectionResults.sSigHeader.eSigStatus"] = description_front
            signal_summary[".GRAPPA_RC_DATA.DetectionResults.sSigHeader.eSigStatus"] = description_rear
            signal_summary[".GRAPPA_LSC_DATA.DetectionResults.sSigHeader.eSigStatus"] = description_left
            signal_summary[".GRAPPA_RSC_DATA.DetectionResults.sSigHeader.eSigStatus"] = description_right
            remark = (
                "Input timestamp (provided by GRAPPA) should be the same as the output timestamp (provided by TPP) "
                "and should be ascending."
            )
            self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_remark=remark)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")

            self.result.measured_result = FALSE
        else:
            test_result = fc.PASS

            # create multiple keys in signal_summary dict to be able to display all relevant signal names in the table
            all_signal_names = signal_name_front + signal_name_left + signal_name_right + signal_name_rear
            signal_summary = {signal: description for signal in all_signal_names}

            remark = (
                "Input timestamp (provided by GRAPPA) should be the same as the output timestamp (provided by TPP) "
                "and should be ascending."
            )
            self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_remark=remark)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")

            self.result.measured_result = TRUE

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1492738"],
            fc.TESTCASE_ID: ["48050"],
            fc.TEST_DESCRIPTION: ["Check if TPP only processes OK input"],
            fc.TEST_RESULT: [test_result],
        }
        self.result.details["Additional_results"] = result_df

        figFront = go.Figure()
        figFront.add_trace(
            go.Scatter(
                x=reader[TPPSigState.Columns.GRAPPA_DETECTION_TIMESTAMP_FRONT],
                y=reader[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_FRONT],
                mode="lines",
                name="Front_inputSigState",
            )
        )
        figFront.add_trace(
            go.Scatter(
                x=reader[TPPSigState.Columns.GRAPPA_DETECTION_TIMESTAMP_FRONT],
                y=reader[TPPSigState.Columns.TPP_OUTPUT_NUM_BBOXES_FRONT]
                + reader[TPPSigState.Columns.TPP_OUTPUT_NUM_CUBOIDS_FRONT],
                mode="lines",
                name="Front_detections",
            )
        )
        figFront.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Timestamp[ms]"
        )
        plots.append(figFront)
        plot_titles.append("Front")
        remarks.append("")

        figRear = go.Figure()
        figRear.add_trace(
            go.Scatter(
                x=reader[TPPSigState.Columns.GRAPPA_DETECTION_TIMESTAMP_REAR],
                y=reader[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_REAR],
                mode="lines",
                name="Rear_inputSigState",
            )
        )
        figRear.add_trace(
            go.Scatter(
                x=reader[TPPSigState.Columns.GRAPPA_DETECTION_TIMESTAMP_REAR],
                y=reader[TPPSigState.Columns.TPP_OUTPUT_NUM_BBOXES_REAR]
                + reader[TPPSigState.Columns.TPP_OUTPUT_NUM_CUBOIDS_REAR],
                mode="lines",
                name="Rear_detections",
            )
        )
        figRear.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Timestamp[ms]"
        )
        plots.append(figRear)
        plot_titles.append("Rear")
        remarks.append("")

        figLeft = go.Figure()
        figLeft.add_trace(
            go.Scatter(
                x=reader[TPPSigState.Columns.GRAPPA_DETECTION_TIMESTAMP_LEFT],
                y=reader[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_LEFT],
                mode="lines",
                name="Left_inputSigState",
            )
        )
        figLeft.add_trace(
            go.Scatter(
                x=reader[TPPSigState.Columns.GRAPPA_DETECTION_TIMESTAMP_LEFT],
                y=reader[TPPSigState.Columns.TPP_OUTPUT_NUM_BBOXES_LEFT]
                + reader[TPPSigState.Columns.TPP_OUTPUT_NUM_CUBOIDS_LEFT],
                mode="lines",
                name="Left_detections",
            )
        )
        figLeft.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Timestamp[ms]"
        )
        plots.append(figLeft)
        plot_titles.append("Left")
        remarks.append("")

        figRight = go.Figure()
        figRight.add_trace(
            go.Scatter(
                x=reader[TPPSigState.Columns.GRAPPA_DETECTION_TIMESTAMP_RIGHT],
                y=reader[TPPSigState.Columns.GRAPPA_DETECTION_SIG_STATUS_RIGHT],
                mode="lines",
                name="Right_inputSigState",
            )
        )
        figRight.add_trace(
            go.Scatter(
                x=reader[TPPSigState.Columns.GRAPPA_DETECTION_TIMESTAMP_RIGHT],
                y=reader[TPPSigState.Columns.TPP_OUTPUT_NUM_BBOXES_RIGHT]
                + reader[TPPSigState.Columns.TPP_OUTPUT_NUM_CUBOIDS_RIGHT],
                mode="lines",
                name="Right_detections",
            )
        )
        figRight.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Timestamp[ms]"
        )
        plots.append(figRight)
        plot_titles.append("Right")
        remarks.append("")

        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")


@verifies(
    requirement="1492738",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_ErP2cUMsEe68PtCWeWkWbA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@testcase_definition(
    name="TPP Input Signal State Check",
    description="This test will verify if GRAPPA has (only) OK signal state for the frames where it is processed and an output is provided.",
)
@register_inputs("/parking")
class TestSigState(TestCase):
    """Example test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestInputSigStateTestStep,
        ]
