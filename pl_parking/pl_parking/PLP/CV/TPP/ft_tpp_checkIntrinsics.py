"""TestCases performing all necessary checks for the intrinsics."""

import logging
import os

import pandas as pd
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.PLP.CV.TPP.constants import IMG_HEIGHT, IMG_WIDTH

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TPP_INTRINSICS = "TPP_INTRINSICS"


# Define reader for each camera
class TPPIntrinsics(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        GRAPPA_DETECTION_SIG_STATUS_FRONT = "sigStatusGrappaFront"
        GRAPPA_DETECTION_TIMESTAMP_FRONT = "timestampGrappaFront"
        FOCAL_X_FRONT = "focalXFront"
        FOCAL_Y_FRONT = "focalYFront"
        CENTER_X_FRONT = "centerXFront"
        CENTER_Y_FRONT = "centerYFront"

        GRAPPA_DETECTION_SIG_STATUS_REAR = "sigStatusGrappaRear"
        GRAPPA_DETECTION_TIMESTAMP_REAR = "timestampGrappaRear"
        FOCAL_X_REAR = "focalXRear"
        FOCAL_Y_REAR = "focalYRear"
        CENTER_X_REAR = "centerXRear"
        CENTER_Y_REAR = "centerYRear"

        GRAPPA_DETECTION_SIG_STATUS_LEFT = "sigStatusGrappaLeft"
        GRAPPA_DETECTION_TIMESTAMP_LEFT = "timestampGrappaLeft"
        FOCAL_X_LEFT = "focalXLeft"
        FOCAL_Y_LEFT = "focalYLeft"
        CENTER_X_LEFT = "centerXLeft"
        CENTER_Y_LEFT = "centerYLeft"

        GRAPPA_DETECTION_SIG_STATUS_RIGHT = "sigStatusGrappaRight"
        GRAPPA_DETECTION_TIMESTAMP_RIGHT = "timestampGrappaRight"
        FOCAL_X_RIGHT = "focalXRight"
        FOCAL_Y_RIGHT = "focalYRight"
        CENTER_X_RIGHT = "centerXRight"
        CENTER_Y_RIGHT = "centerYRight"

    def get_properties(self):
        """Generate a string of signals to be read."""
        signal_dict = {
            self.Columns.GRAPPA_DETECTION_SIG_STATUS_FRONT: ".GRAPPA_FC_DATA.DetectionResults.sSigHeader.eSigStatus",
            self.Columns.GRAPPA_DETECTION_TIMESTAMP_FRONT: ".GRAPPA_FC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
            self.Columns.FOCAL_X_FRONT: ".GRAPPA_FC_DATA.DetectionResults.sReferenceImageIntrinsics.focalX",
            self.Columns.FOCAL_Y_FRONT: ".GRAPPA_FC_DATA.DetectionResults.sReferenceImageIntrinsics.focalY",
            self.Columns.CENTER_X_FRONT: ".GRAPPA_FC_DATA.DetectionResults.sReferenceImageIntrinsics.centerX",
            self.Columns.CENTER_Y_FRONT: ".GRAPPA_FC_DATA.DetectionResults.sReferenceImageIntrinsics.centerY",
            self.Columns.GRAPPA_DETECTION_SIG_STATUS_REAR: ".GRAPPA_RC_DATA.DetectionResults.sSigHeader.eSigStatus",
            self.Columns.GRAPPA_DETECTION_TIMESTAMP_REAR: ".GRAPPA_RC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
            self.Columns.FOCAL_X_REAR: ".GRAPPA_RC_DATA.DetectionResults.sReferenceImageIntrinsics.focalX",
            self.Columns.FOCAL_Y_REAR: ".GRAPPA_RC_DATA.DetectionResults.sReferenceImageIntrinsics.focalY",
            self.Columns.CENTER_X_REAR: ".GRAPPA_RC_DATA.DetectionResults.sReferenceImageIntrinsics.centerX",
            self.Columns.CENTER_Y_REAR: ".GRAPPA_RC_DATA.DetectionResults.sReferenceImageIntrinsics.centerY",
            self.Columns.GRAPPA_DETECTION_SIG_STATUS_LEFT: ".GRAPPA_LSC_DATA.DetectionResults.sSigHeader.eSigStatus",
            self.Columns.GRAPPA_DETECTION_TIMESTAMP_LEFT: ".GRAPPA_LSC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
            self.Columns.FOCAL_X_LEFT: ".GRAPPA_LSC_DATA.DetectionResults.sReferenceImageIntrinsics.focalX",
            self.Columns.FOCAL_Y_LEFT: ".GRAPPA_LSC_DATA.DetectionResults.sReferenceImageIntrinsics.focalY",
            self.Columns.CENTER_X_LEFT: ".GRAPPA_LSC_DATA.DetectionResults.sReferenceImageIntrinsics.centerX",
            self.Columns.CENTER_Y_LEFT: ".GRAPPA_LSC_DATA.DetectionResults.sReferenceImageIntrinsics.centerY",
            self.Columns.GRAPPA_DETECTION_SIG_STATUS_RIGHT: ".GRAPPA_RSC_DATA.DetectionResults.sSigHeader.eSigStatus",
            self.Columns.GRAPPA_DETECTION_TIMESTAMP_RIGHT: ".GRAPPA_RSC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
            self.Columns.FOCAL_X_RIGHT: ".GRAPPA_RSC_DATA.DetectionResults.sReferenceImageIntrinsics.focalX",
            self.Columns.FOCAL_Y_RIGHT: ".GRAPPA_RSC_DATA.DetectionResults.sReferenceImageIntrinsics.focalY",
            self.Columns.CENTER_X_RIGHT: ".GRAPPA_RSC_DATA.DetectionResults.sReferenceImageIntrinsics.centerX",
            self.Columns.CENTER_Y_RIGHT: ".GRAPPA_RSC_DATA.DetectionResults.sReferenceImageIntrinsics.centerY",
        }

        return signal_dict

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "ADC5xx_Device", "M7board.EM_Thread", "CarPC.EM_Thread", "MTA_ADC5"]

        self._properties = self.get_properties()


example_obj = TPPIntrinsics()


@teststep_definition(
    step_number=1,
    name="TPP Intrinsics Test",
    description="Check the values of the intrinsics",
    expected_result=BooleanResult(TRUE),
)
@register_signals(TPP_INTRINSICS, TPPIntrinsics)
class TestIntrinsicsTestStep(TestStep):
    """Test step definition."""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the test-step."""
        super().__init__()
        self.sig_sum = ""

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        reader = self.readers[TPP_INTRINSICS].signals
        reader = reader.iloc[4:]  # Skip the first frames because the values might not be initialized
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        test_result = fc.INPUT_MISSING  # Result initialization
        signal_summary = {}
        plot_titles, plots, remarks = fh.rep([], 3)

        description = "The <b>evaluation</b> of the signal is <b>PASSED</b>."

        list_of_errors = []

        for _, row in reader.iterrows():
            if row[TPPIntrinsics.Columns.GRAPPA_DETECTION_SIG_STATUS_FRONT] != fc.AL_SIG_STATE_INVALID:
                if (
                    row[TPPIntrinsics.Columns.FOCAL_X_FRONT] == 0
                    and row[TPPIntrinsics.Columns.FOCAL_Y_FRONT] == 0
                    and row[TPPIntrinsics.Columns.CENTER_X_FRONT] == 0
                    and row[TPPIntrinsics.Columns.CENTER_Y_FRONT] == 0
                ) or (
                    (
                        row[TPPIntrinsics.Columns.CENTER_X_FRONT] > IMG_WIDTH
                        or row[TPPIntrinsics.Columns.CENTER_X_FRONT] < 0
                    )
                    or (
                        row[TPPIntrinsics.Columns.CENTER_Y_FRONT] > IMG_HEIGHT
                        or row[TPPIntrinsics.Columns.CENTER_Y_FRONT] < 0
                    )
                ):
                    error_dict = {
                        "ts": row[TPPIntrinsics.Columns.GRAPPA_DETECTION_TIMESTAMP_FRONT],
                        "side": "Front",
                        "center_point_x": row[TPPIntrinsics.Columns.CENTER_X_FRONT],
                        "center_point_y": row[TPPIntrinsics.Columns.CENTER_Y_FRONT],
                        "focal_x": row[TPPIntrinsics.Columns.FOCAL_X_FRONT],
                        "focal_y": row[TPPIntrinsics.Columns.FOCAL_Y_FRONT],
                    }
                    list_of_errors.append(error_dict)

            if row[TPPIntrinsics.Columns.GRAPPA_DETECTION_SIG_STATUS_REAR] != fc.AL_SIG_STATE_INVALID:
                if (
                    row[TPPIntrinsics.Columns.FOCAL_X_REAR] == 0
                    and row[TPPIntrinsics.Columns.FOCAL_Y_REAR] == 0
                    and row[TPPIntrinsics.Columns.CENTER_X_REAR] == 0
                    and row[TPPIntrinsics.Columns.CENTER_Y_REAR] == 0
                ) or (
                    (
                        row[TPPIntrinsics.Columns.CENTER_X_REAR] > IMG_WIDTH
                        or row[TPPIntrinsics.Columns.CENTER_X_REAR] < 0
                    )
                    or (
                        row[TPPIntrinsics.Columns.CENTER_Y_REAR] > IMG_HEIGHT
                        or row[TPPIntrinsics.Columns.CENTER_Y_REAR] < 0
                    )
                ):
                    error_dict = {
                        "ts": row[TPPIntrinsics.Columns.GRAPPA_DETECTION_TIMESTAMP_REAR],
                        "side": "Rear",
                        "center_point_x": row[TPPIntrinsics.Columns.CENTER_X_REAR],
                        "center_point_y": row[TPPIntrinsics.Columns.CENTER_Y_REAR],
                        "focal_x": row[TPPIntrinsics.Columns.FOCAL_X_REAR],
                        "focal_y": row[TPPIntrinsics.Columns.FOCAL_Y_REAR],
                    }
                    list_of_errors.append(error_dict)

            if row[TPPIntrinsics.Columns.GRAPPA_DETECTION_SIG_STATUS_LEFT] != fc.AL_SIG_STATE_INVALID:
                if (
                    row[TPPIntrinsics.Columns.FOCAL_X_LEFT] == 0
                    and row[TPPIntrinsics.Columns.FOCAL_Y_LEFT] == 0
                    and row[TPPIntrinsics.Columns.CENTER_X_LEFT] == 0
                    and row[TPPIntrinsics.Columns.CENTER_Y_LEFT] == 0
                ) or (
                    (
                        row[TPPIntrinsics.Columns.CENTER_X_LEFT] > IMG_WIDTH
                        or row[TPPIntrinsics.Columns.CENTER_X_LEFT] < 0
                    )
                    or (
                        row[TPPIntrinsics.Columns.CENTER_Y_LEFT] > IMG_HEIGHT
                        or row[TPPIntrinsics.Columns.CENTER_Y_LEFT] < 0
                    )
                ):
                    error_dict = {
                        "ts": row[TPPIntrinsics.Columns.GRAPPA_DETECTION_TIMESTAMP_LEFT],
                        "side": "Left",
                        "center_point_x": row[TPPIntrinsics.Columns.CENTER_X_LEFT],
                        "center_point_y": row[TPPIntrinsics.Columns.CENTER_Y_LEFT],
                        "focal_x": row[TPPIntrinsics.Columns.FOCAL_X_LEFT],
                        "focal_y": row[TPPIntrinsics.Columns.FOCAL_Y_LEFT],
                    }
                    list_of_errors.append(error_dict)

            if row[TPPIntrinsics.Columns.GRAPPA_DETECTION_SIG_STATUS_RIGHT] != fc.AL_SIG_STATE_INVALID:
                if (
                    row[TPPIntrinsics.Columns.FOCAL_X_RIGHT] == 0
                    and row[TPPIntrinsics.Columns.FOCAL_Y_RIGHT] == 0
                    and row[TPPIntrinsics.Columns.CENTER_X_RIGHT] == 0
                    and row[TPPIntrinsics.Columns.CENTER_Y_RIGHT] == 0
                ) or (
                    (
                        row[TPPIntrinsics.Columns.CENTER_X_RIGHT] > IMG_WIDTH
                        or row[TPPIntrinsics.Columns.CENTER_X_RIGHT] < 0
                    )
                    or (
                        row[TPPIntrinsics.Columns.CENTER_Y_RIGHT] > IMG_HEIGHT
                        or row[TPPIntrinsics.Columns.CENTER_Y_RIGHT] < 0
                    )
                ):
                    error_dict = {
                        "ts": row[TPPIntrinsics.Columns.GRAPPA_DETECTION_TIMESTAMP_RIGHT],
                        "side": "Right",
                        "center_point_x": row[TPPIntrinsics.Columns.CENTER_X_RIGHT],
                        "center_point_y": row[TPPIntrinsics.Columns.CENTER_Y_RIGHT],
                        "focal_x": row[TPPIntrinsics.Columns.FOCAL_X_RIGHT],
                        "focal_y": row[TPPIntrinsics.Columns.FOCAL_Y_RIGHT],
                    }
                    list_of_errors.append(error_dict)

        signal_name_front = [
            example_obj.get_properties()[TPPIntrinsics.Columns.FOCAL_X_FRONT][:-1],
            example_obj.get_properties()[TPPIntrinsics.Columns.FOCAL_Y_FRONT][:-1],
            example_obj.get_properties()[TPPIntrinsics.Columns.CENTER_X_FRONT][:-1],
            example_obj.get_properties()[TPPIntrinsics.Columns.CENTER_Y_FRONT][:-1],
        ]
        signal_name_left = [
            example_obj.get_properties()[TPPIntrinsics.Columns.FOCAL_X_LEFT][:-1],
            example_obj.get_properties()[TPPIntrinsics.Columns.FOCAL_Y_LEFT][:-1],
            example_obj.get_properties()[TPPIntrinsics.Columns.CENTER_X_LEFT][:-1],
            example_obj.get_properties()[TPPIntrinsics.Columns.CENTER_Y_LEFT][:-1],
        ]
        signal_name_rear = [
            example_obj.get_properties()[TPPIntrinsics.Columns.FOCAL_X_REAR][:-1],
            example_obj.get_properties()[TPPIntrinsics.Columns.FOCAL_Y_REAR][:-1],
            example_obj.get_properties()[TPPIntrinsics.Columns.CENTER_X_REAR][:-1],
            example_obj.get_properties()[TPPIntrinsics.Columns.CENTER_Y_REAR][:-1],
        ]
        signal_name_right = [
            example_obj.get_properties()[TPPIntrinsics.Columns.FOCAL_X_RIGHT][:-1],
            example_obj.get_properties()[TPPIntrinsics.Columns.FOCAL_Y_RIGHT][:-1],
            example_obj.get_properties()[TPPIntrinsics.Columns.CENTER_X_RIGHT][:-1],
            example_obj.get_properties()[TPPIntrinsics.Columns.CENTER_Y_RIGHT][:-1],
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
                    f"center point and focal length have unexpected values on the {err['side']} instance of the "
                    f"camera:\n Center Point ({err['center_point_x']}, {err['center_point_y']}) "
                    f"\n Focal Length ({err['focal_x']}, {err['focal_y']}) \n"
                    f"Focal Length needs to be > 0 and Center Point within the image (width: 832, height: 640)".split()
                )

            if len(errors_left_df) > 0:
                err = errors_left_df.iloc[0]
                description_left = " ".join(
                    f"The <b>evaluation</b> of the signals is <b>FAILED</b> at timestamp {err['ts']} because the "
                    f"center point and focal length have unexpected values on the {err['side']} instance of the "
                    f"camera:\n Center Point ({err['center_point_x']}, {err['center_point_y']}) "
                    f"\n Focal Length ({err['focal_x']}, {err['focal_y']}) \n"
                    f"Focal Length needs to be > 0 and Center Point within the image (width: 832, height: 640)".split()
                )

            if len(errors_rear_df) > 0:
                err = errors_rear_df.iloc[0]
                description_rear = " ".join(
                    f"The <b>evaluation</b> of the signals is <b>FAILED</b> at timestamp {err['ts']} because the "
                    f"center point and focal length have unexpected values on the {err['side']} instance of the "
                    f"camera:\n Center Point ({err['center_point_x']}, {err['center_point_y']}) "
                    f"\n Focal Length ({err['focal_x']}, {err['focal_y']}) \n"
                    f"Focal Length needs to be > 0 and Center Point within the image (width: 832, height: 640)".split()
                )

            if len(errors_right_df) > 0:
                err = errors_right_df.iloc[0]
                description_right = " ".join(
                    f"The <b>evaluation</b> of the signals is <b>FAILED</b> at timestamp {err['ts']} because the "
                    f"center point and focal length have unexpected values on the {err['side']} instance of the "
                    f"camera:\n Center Point ({err['center_point_x']}, {err['center_point_y']}) "
                    f"\n Focal Length ({err['focal_x']}, {err['focal_y']}) \n"
                    f"Focal Length needs to be > 0 and Center Point within the image (width: 832, height: 640)".split()
                )

            signal_summary[".GRAPPA_FC_DATA.DetectionResults.sReferenceImageIntrinsics"] = description_front
            signal_summary[".GRAPPA_RC_DATA.DetectionResults.sReferenceImageIntrinsics"] = description_rear
            signal_summary[".GRAPPA_LSC_DATA.DetectionResults.sReferenceImageIntrinsics"] = description_left
            signal_summary[".GRAPPA_RSC_DATA.DetectionResults.sReferenceImageIntrinsics"] = description_right
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
            fc.REQ_ID: ["1645911"],
            fc.TESTCASE_ID: ["39743"],
            fc.TEST_DESCRIPTION: ["Validate the intrinsics"],
            fc.TEST_RESULT: [test_result],
        }
        self.result.details["Additional_results"] = result_df

        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")


@testcase_definition(
    name="TPP Intrinsics Range Check",
    description="This test will verify if the GRAPPA intrinsics are defined and in range.",
)
@register_inputs("/parking")
class TestIntrinsics(TestCase):
    """Example test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestIntrinsicsTestStep,
        ]
