"""TestCases performing all necessary checks for the extrinsics."""

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
from pl_parking.PLP.CV.TPP.constants import POS_MAX_VALUE, POS_MIN_VALUE, ROT_MAX_VALUE, ROT_MIN_VALUE

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TPP_EXTRINSICS = "TPP_EXTRINSICS"


# Define reader for each camera
class TPPExtrinsics(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        EXTRINSICS_SIG_STATUS_FRONT = "sigStatusExtrinsicsFront"
        EXTRINSICS_TIMESTAMP_FRONT = "timestampExtrinsicsFront"
        POS_X_FRONT = "posXFront"
        POS_Y_FRONT = "posYFront"
        POS_Z_FRONT = "posZFront"
        ROT_X_FRONT = "rotXFront"
        ROT_Y_FRONT = "rotYFront"
        ROT_Z_FRONT = "rotZFront"

        EXTRINSICS_SIG_STATUS_LEFT = "sigStatusExtrinsicsLeft"
        EXTRINSICS_TIMESTAMP_LEFT = "timestampExtrinsicsLeft"
        POS_X_LEFT = "posXLeft"
        POS_Y_LEFT = "posYLeft"
        POS_Z_LEFT = "posZLeft"
        ROT_X_LEFT = "rotXLeft"
        ROT_Y_LEFT = "rotYLeft"
        ROT_Z_LEFT = "rotZLeft"

        EXTRINSICS_SIG_STATUS_REAR = "sigStatusExtrinsicsRear"
        EXTRINSICS_TIMESTAMP_REAR = "timestampExtrinsicsRear"
        POS_X_REAR = "posXRear"
        POS_Y_REAR = "posYRear"
        POS_Z_REAR = "posZRear"
        ROT_X_REAR = "rotXRear"
        ROT_Y_REAR = "rotYRear"
        ROT_Z_REAR = "rotZRear"

        EXTRINSICS_SIG_STATUS_RIGHT = "sigStatusExtrinsicsRight"
        EXTRINSICS_TIMESTAMP_RIGHT = "timestampExtrinsicsRight"
        POS_X_RIGHT = "posXRight"
        POS_Y_RIGHT = "posYRight"
        POS_Z_RIGHT = "posZRight"
        ROT_X_RIGHT = "rotXRight"
        ROT_Y_RIGHT = "rotYRight"
        ROT_Z_RIGHT = "rotZRight"

    def get_properties(self):
        """Generate a string of signals to be read."""
        signal_dict = {
            self.Columns.EXTRINSICS_SIG_STATUS_FRONT: ".CFG_DATA.mecal_FcEolCalibrationsExtrinsicsISO.sSigHeader.eSigStatus",
            self.Columns.EXTRINSICS_TIMESTAMP_FRONT: ".CFG_DATA.mecal_FcEolCalibrationsExtrinsicsISO.sSigHeader.uiTimeStamp",
            self.Columns.POS_X_FRONT: ".CFG_DATA.mecal_FcEolCalibrationsExtrinsicsISO.posX_mm",
            self.Columns.POS_Y_FRONT: ".CFG_DATA.mecal_FcEolCalibrationsExtrinsicsISO.posY_mm",
            self.Columns.POS_Z_FRONT: ".CFG_DATA.mecal_FcEolCalibrationsExtrinsicsISO.posZ_mm",
            self.Columns.ROT_X_FRONT: ".CFG_DATA.mecal_FcEolCalibrationsExtrinsicsISO.rotX_rad",
            self.Columns.ROT_Y_FRONT: ".CFG_DATA.mecal_FcEolCalibrationsExtrinsicsISO.rotY_rad",
            self.Columns.ROT_Z_FRONT: ".CFG_DATA.mecal_FcEolCalibrationsExtrinsicsISO.rotZ_rad",
            self.Columns.EXTRINSICS_SIG_STATUS_LEFT: ".CFG_DATA.mecal_LscEolCalibrationsExtrinsicsISO.sSigHeader.eSigStatus",
            self.Columns.EXTRINSICS_TIMESTAMP_LEFT: ".CFG_DATA.mecal_LscEolCalibrationsExtrinsicsISO.sSigHeader.uiTimeStamp",
            self.Columns.POS_X_LEFT: ".CFG_DATA.mecal_LscEolCalibrationsExtrinsicsISO.posX_mm",
            self.Columns.POS_Y_LEFT: ".CFG_DATA.mecal_LscEolCalibrationsExtrinsicsISO.posY_mm",
            self.Columns.POS_Z_LEFT: ".CFG_DATA.mecal_LscEolCalibrationsExtrinsicsISO.posZ_mm",
            self.Columns.ROT_X_LEFT: ".CFG_DATA.mecal_LscEolCalibrationsExtrinsicsISO.rotX_rad",
            self.Columns.ROT_Y_LEFT: ".CFG_DATA.mecal_LscEolCalibrationsExtrinsicsISO.rotY_rad",
            self.Columns.ROT_Z_LEFT: ".CFG_DATA.mecal_LscEolCalibrationsExtrinsicsISO.rotZ_rad",
            self.Columns.EXTRINSICS_SIG_STATUS_REAR: ".CFG_DATA.mecal_RcEolCalibrationsExtrinsicsISO.sSigHeader.eSigStatus",
            self.Columns.EXTRINSICS_TIMESTAMP_REAR: ".CFG_DATA.mecal_RcEolCalibrationsExtrinsicsISO.sSigHeader.uiTimeStamp",
            self.Columns.POS_X_REAR: ".CFG_DATA.mecal_RcEolCalibrationsExtrinsicsISO.posX_mm",
            self.Columns.POS_Y_REAR: ".CFG_DATA.mecal_RcEolCalibrationsExtrinsicsISO.posY_mm",
            self.Columns.POS_Z_REAR: ".CFG_DATA.mecal_RcEolCalibrationsExtrinsicsISO.posZ_mm",
            self.Columns.ROT_X_REAR: ".CFG_DATA.mecal_RcEolCalibrationsExtrinsicsISO.rotX_rad",
            self.Columns.ROT_Y_REAR: ".CFG_DATA.mecal_RcEolCalibrationsExtrinsicsISO.rotY_rad",
            self.Columns.ROT_Z_REAR: ".CFG_DATA.mecal_RcEolCalibrationsExtrinsicsISO.rotZ_rad",
            self.Columns.EXTRINSICS_SIG_STATUS_RIGHT: ".CFG_DATA.mecal_RscEolCalibrationsExtrinsicsISO.sSigHeader.eSigStatus",
            self.Columns.EXTRINSICS_TIMESTAMP_RIGHT: ".CFG_DATA.mecal_RscEolCalibrationsExtrinsicsISO.sSigHeader.uiTimeStamp",
            self.Columns.POS_X_RIGHT: ".CFG_DATA.mecal_RscEolCalibrationsExtrinsicsISO.posX_mm",
            self.Columns.POS_Y_RIGHT: ".CFG_DATA.mecal_RscEolCalibrationsExtrinsicsISO.posY_mm",
            self.Columns.POS_Z_RIGHT: ".CFG_DATA.mecal_RscEolCalibrationsExtrinsicsISO.posZ_mm",
            self.Columns.ROT_X_RIGHT: ".CFG_DATA.mecal_RscEolCalibrationsExtrinsicsISO.rotX_rad",
            self.Columns.ROT_Y_RIGHT: ".CFG_DATA.mecal_RscEolCalibrationsExtrinsicsISO.rotY_rad",
            self.Columns.ROT_Z_RIGHT: ".CFG_DATA.mecal_RscEolCalibrationsExtrinsicsISO.rotZ_rad",
        }

        return signal_dict

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "ADC5xx_Device", "M7board.EM_Thread", "CarPC.EM_Thread", "MTA_ADC5"]

        self._properties = self.get_properties()


example_obj = TPPExtrinsics()


@teststep_definition(
    step_number=1,
    name="TPP Extrinsic Params Test",
    description="Check the values of the extrinsic parameters",
    expected_result=BooleanResult(TRUE),
)
@register_signals(TPP_EXTRINSICS, TPPExtrinsics)
class TestExtrinsicsTestStep(TestStep):
    """Test step definition."""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the test-step."""
        super().__init__()
        self.sig_sum = ""

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        reader = self.readers[TPP_EXTRINSICS]
        reader = reader.iloc[4:]  # Skip the first frames because the values might not be initialized
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        test_result = fc.INPUT_MISSING  # Result
        signal_summary = {}
        plot_titles, plots, remarks = fh.rep([], 3)

        description = "The <b>evaluation</b> of the signal is <b>PASSED</b>."

        list_of_errors = []

        for _, row in reader.iterrows():
            if row[TPPExtrinsics.Columns.EXTRINSICS_SIG_STATUS_FRONT] != fc.AL_SIG_STATE_INVALID:
                if (
                    (
                        row[TPPExtrinsics.Columns.POS_X_FRONT] == 0
                        or row[TPPExtrinsics.Columns.POS_X_FRONT] > POS_MAX_VALUE
                        or row[TPPExtrinsics.Columns.POS_X_FRONT] < POS_MIN_VALUE
                    )
                    or (
                        row[TPPExtrinsics.Columns.POS_Y_FRONT] == 0
                        or row[TPPExtrinsics.Columns.POS_Y_FRONT] > POS_MAX_VALUE
                        or row[TPPExtrinsics.Columns.POS_Y_FRONT] < POS_MIN_VALUE
                    )
                    or (
                        row[TPPExtrinsics.Columns.POS_Z_FRONT] == 0
                        or row[TPPExtrinsics.Columns.POS_Z_FRONT] > POS_MAX_VALUE
                        or row[TPPExtrinsics.Columns.POS_Z_FRONT] < POS_MIN_VALUE
                    )
                ) or (
                    (
                        row[TPPExtrinsics.Columns.ROT_X_FRONT] > ROT_MAX_VALUE
                        or row[TPPExtrinsics.Columns.ROT_X_FRONT] < ROT_MIN_VALUE
                    )
                    or (
                        row[TPPExtrinsics.Columns.ROT_Y_FRONT] > ROT_MAX_VALUE
                        or row[TPPExtrinsics.Columns.ROT_Y_FRONT] < ROT_MIN_VALUE
                    )
                    or (
                        row[TPPExtrinsics.Columns.ROT_Z_FRONT] > ROT_MAX_VALUE
                        or row[TPPExtrinsics.Columns.ROT_Z_FRONT] < ROT_MIN_VALUE
                    )
                ):
                    error_dict = {
                        "ts": row[TPPExtrinsics.Columns.EXTRINSICS_TIMESTAMP_FRONT],
                        "side": "Front",
                        "x_pos": row[TPPExtrinsics.Columns.POS_X_FRONT],
                        "y_pos": row[TPPExtrinsics.Columns.POS_Y_FRONT],
                        "z_pos": row[TPPExtrinsics.Columns.POS_Z_FRONT],
                        "x_rot": row[TPPExtrinsics.Columns.ROT_X_FRONT],
                        "y_rot": row[TPPExtrinsics.Columns.ROT_Y_FRONT],
                        "z_rot": row[TPPExtrinsics.Columns.ROT_Z_FRONT],
                    }
                    list_of_errors.append(error_dict)

            if row[TPPExtrinsics.Columns.EXTRINSICS_SIG_STATUS_LEFT] != fc.AL_SIG_STATE_INVALID:
                if (
                    (
                        row[TPPExtrinsics.Columns.POS_X_LEFT] == 0
                        or row[TPPExtrinsics.Columns.POS_X_LEFT] > POS_MAX_VALUE
                        or row[TPPExtrinsics.Columns.POS_X_LEFT] < POS_MIN_VALUE
                    )
                    or (
                        row[TPPExtrinsics.Columns.POS_Y_LEFT] == 0
                        or row[TPPExtrinsics.Columns.POS_Y_LEFT] > POS_MAX_VALUE
                        or row[TPPExtrinsics.Columns.POS_Y_LEFT] < POS_MIN_VALUE
                    )
                    or (
                        row[TPPExtrinsics.Columns.POS_Z_LEFT] == 0
                        or row[TPPExtrinsics.Columns.POS_Z_LEFT] > POS_MAX_VALUE
                        or row[TPPExtrinsics.Columns.POS_Z_LEFT] < POS_MIN_VALUE
                    )
                ) or (
                    (
                        row[TPPExtrinsics.Columns.ROT_X_LEFT] > ROT_MAX_VALUE
                        or row[TPPExtrinsics.Columns.ROT_X_LEFT] < ROT_MIN_VALUE
                    )
                    or (
                        row[TPPExtrinsics.Columns.ROT_Y_LEFT] > ROT_MAX_VALUE
                        or row[TPPExtrinsics.Columns.ROT_Y_LEFT] < ROT_MIN_VALUE
                    )
                    or (
                        row[TPPExtrinsics.Columns.ROT_Z_LEFT] > ROT_MAX_VALUE
                        or row[TPPExtrinsics.Columns.ROT_Z_LEFT] < ROT_MIN_VALUE
                    )
                ):
                    error_dict = {
                        "ts": row[TPPExtrinsics.Columns.EXTRINSICS_TIMESTAMP_LEFT],
                        "side": "Left",
                        "x_pos": row[TPPExtrinsics.Columns.POS_X_LEFT],
                        "y_pos": row[TPPExtrinsics.Columns.POS_Y_LEFT],
                        "z_pos": row[TPPExtrinsics.Columns.POS_Z_LEFT],
                        "x_rot": row[TPPExtrinsics.Columns.ROT_X_LEFT],
                        "y_rot": row[TPPExtrinsics.Columns.ROT_Y_LEFT],
                        "z_rot": row[TPPExtrinsics.Columns.ROT_Z_LEFT],
                    }
                    list_of_errors.append(error_dict)

            if row[TPPExtrinsics.Columns.EXTRINSICS_SIG_STATUS_REAR] != fc.AL_SIG_STATE_INVALID:
                if (
                    (
                        row[TPPExtrinsics.Columns.POS_X_REAR] == 0
                        or row[TPPExtrinsics.Columns.POS_X_REAR] > POS_MAX_VALUE
                        or row[TPPExtrinsics.Columns.POS_X_REAR] < POS_MIN_VALUE
                    )
                    or (
                        row[TPPExtrinsics.Columns.POS_Y_REAR] == 0
                        or row[TPPExtrinsics.Columns.POS_Y_REAR] > POS_MAX_VALUE
                        or row[TPPExtrinsics.Columns.POS_Y_REAR] < POS_MIN_VALUE
                    )
                    or (
                        row[TPPExtrinsics.Columns.POS_Z_REAR] == 0
                        or row[TPPExtrinsics.Columns.POS_Z_REAR] > POS_MAX_VALUE
                        or row[TPPExtrinsics.Columns.POS_Z_REAR] < POS_MIN_VALUE
                    )
                ) or (
                    (
                        row[TPPExtrinsics.Columns.ROT_X_REAR] > ROT_MAX_VALUE
                        or row[TPPExtrinsics.Columns.ROT_X_REAR] < ROT_MIN_VALUE
                    )
                    or (
                        row[TPPExtrinsics.Columns.ROT_Y_REAR] > ROT_MAX_VALUE
                        or row[TPPExtrinsics.Columns.ROT_Y_REAR] < ROT_MIN_VALUE
                    )
                    or (
                        row[TPPExtrinsics.Columns.ROT_Z_REAR] > ROT_MAX_VALUE
                        or row[TPPExtrinsics.Columns.ROT_Z_REAR] < ROT_MIN_VALUE
                    )
                ):
                    error_dict = {
                        "ts": row[TPPExtrinsics.Columns.EXTRINSICS_TIMESTAMP_REAR],
                        "side": "Rear",
                        "x_pos": row[TPPExtrinsics.Columns.POS_X_REAR],
                        "y_pos": row[TPPExtrinsics.Columns.POS_Y_REAR],
                        "z_pos": row[TPPExtrinsics.Columns.POS_Z_REAR],
                        "x_rot": row[TPPExtrinsics.Columns.ROT_X_REAR],
                        "y_rot": row[TPPExtrinsics.Columns.ROT_Y_REAR],
                        "z_rot": row[TPPExtrinsics.Columns.ROT_Z_REAR],
                    }
                    list_of_errors.append(error_dict)

            if row[TPPExtrinsics.Columns.EXTRINSICS_SIG_STATUS_RIGHT] != fc.AL_SIG_STATE_INVALID:
                if (
                    (
                        row[TPPExtrinsics.Columns.POS_X_RIGHT] == 0
                        or row[TPPExtrinsics.Columns.POS_X_RIGHT] > POS_MAX_VALUE
                        or row[TPPExtrinsics.Columns.POS_X_RIGHT] < POS_MIN_VALUE
                    )
                    or (
                        row[TPPExtrinsics.Columns.POS_Y_RIGHT] == 0
                        or row[TPPExtrinsics.Columns.POS_Y_RIGHT] > POS_MAX_VALUE
                        or row[TPPExtrinsics.Columns.POS_Y_RIGHT] < POS_MIN_VALUE
                    )
                    or (
                        row[TPPExtrinsics.Columns.POS_Z_RIGHT] == 0
                        or row[TPPExtrinsics.Columns.POS_Z_RIGHT] > POS_MAX_VALUE
                        or row[TPPExtrinsics.Columns.POS_Z_RIGHT] < POS_MIN_VALUE
                    )
                ) or (
                    (
                        row[TPPExtrinsics.Columns.ROT_X_RIGHT] > ROT_MAX_VALUE
                        or row[TPPExtrinsics.Columns.ROT_X_RIGHT] < ROT_MIN_VALUE
                    )
                    or (
                        row[TPPExtrinsics.Columns.ROT_Y_RIGHT] > ROT_MAX_VALUE
                        or row[TPPExtrinsics.Columns.ROT_Y_RIGHT] < ROT_MIN_VALUE
                    )
                    or (
                        row[TPPExtrinsics.Columns.ROT_Z_RIGHT] > ROT_MAX_VALUE
                        or row[TPPExtrinsics.Columns.ROT_Z_RIGHT] < ROT_MIN_VALUE
                    )
                ):
                    error_dict = {
                        "ts": row[TPPExtrinsics.Columns.EXTRINSICS_TIMESTAMP_RIGHT],
                        "side": "Right",
                        "x_pos": row[TPPExtrinsics.Columns.POS_X_RIGHT],
                        "y_pos": row[TPPExtrinsics.Columns.POS_Y_RIGHT],
                        "z_pos": row[TPPExtrinsics.Columns.POS_Z_RIGHT],
                        "x_rot": row[TPPExtrinsics.Columns.ROT_X_RIGHT],
                        "y_rot": row[TPPExtrinsics.Columns.ROT_Y_RIGHT],
                        "z_rot": row[TPPExtrinsics.Columns.ROT_Z_RIGHT],
                    }
                    list_of_errors.append(error_dict)

        signal_name_front = [
            example_obj.get_properties()[TPPExtrinsics.Columns.POS_X_FRONT],
            example_obj.get_properties()[TPPExtrinsics.Columns.ROT_X_FRONT],
        ]
        signal_name_left = [
            example_obj.get_properties()[TPPExtrinsics.Columns.POS_X_LEFT],
            example_obj.get_properties()[TPPExtrinsics.Columns.ROT_X_LEFT],
        ]
        signal_name_rear = [
            example_obj.get_properties()[TPPExtrinsics.Columns.POS_X_REAR],
            example_obj.get_properties()[TPPExtrinsics.Columns.ROT_X_REAR],
        ]
        signal_name_right = [
            example_obj.get_properties()[TPPExtrinsics.Columns.POS_X_RIGHT],
            example_obj.get_properties()[TPPExtrinsics.Columns.ROT_X_RIGHT],
        ]

        description_front = description
        description_left = description
        description_rear = description
        description_right = description

        if len(list_of_errors) == 0:
            test_result = fc.PASS

            # Generate the summary report
            signal_summary[signal_name_front[0]] = description_front
            signal_summary[signal_name_front[1]] = description_front
            signal_summary[signal_name_left[0]] = description_left
            signal_summary[signal_name_left[1]] = description_left
            signal_summary[signal_name_rear[0]] = description_rear
            signal_summary[signal_name_rear[1]] = description_rear
            signal_summary[signal_name_right[0]] = description_right
            signal_summary[signal_name_right[1]] = description_right
            remark = (
                "Input timestamp (provided by GRAPPA) should be the same as the output timestamp (provided by TPP) "
                "and should be ascending."
            )
            self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_remark=remark)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")

            self.result.measured_result = TRUE
        else:
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
                    f"camera position or camera rotation values are not in the defined range on the {err['side']} "
                    f"instance of the camera: "
                    f"Camera Position({err['x_pos']}, {err['y_pos']}, {err['z_pos']}) "
                    f"Camera Rotation({err['x_rot']}, {err['y_rot']}, {err['z_rot']}) "
                    f"Position range: -5000, 5000 "
                    f"Rotation range: -PI, PI".split()
                )

            if len(errors_left_df) > 0:
                err = errors_left_df.iloc[0]
                description_left = " ".join(
                    f"The <b>evaluation</b> of the signals is <b>FAILED</b> at timestamp {err['ts']} because the "
                    f"camera position or camera rotation values are not in the defined range on the {err['side']} "
                    f"instance of the camera: "
                    f"Camera Position({err['x_pos']}, {err['y_pos']}, {err['z_pos']}) "
                    f"Camera Rotation({err['x_rot']}, {err['y_rot']}, {err['z_rot']}) "
                    f"Position range: -5000, 5000 "
                    f"Rotation range: -PI, PI".split()
                )

            if len(errors_rear_df) > 0:
                err = errors_rear_df.iloc[0]
                description_rear = " ".join(
                    f"The <b>evaluation</b> of the signals is <b>FAILED</b> at timestamp {err['ts']} because the "
                    f"camera position or camera rotation values are not in the defined range on the {err['side']} "
                    f"instance of the camera: "
                    f"Camera Position({err['x_pos']}, {err['y_pos']}, {err['z_pos']}) "
                    f"Camera Rotation({err['x_rot']}, {err['y_rot']}, {err['z_rot']}) "
                    f"Position range: -5000, 5000 "
                    f"Rotation range: -PI, PI".split()
                )

            if len(errors_right_df) > 0:
                err = errors_right_df.iloc[0]
                description_right = " ".join(
                    f"The <b>evaluation</b> of the signals is <b>FAILED</b> at timestamp {err['ts']} because the "
                    f"camera position or camera rotation values are not in the defined range on the {err['side']} "
                    f"instance of the camera: "
                    f"Camera Position({err['x_pos']}, {err['y_pos']}, {err['z_pos']}) "
                    f"Camera Rotation({err['x_rot']}, {err['y_rot']}, {err['z_rot']}) "
                    f"Position range: -5000, 5000 "
                    f"Rotation range: -PI, PI".split()
                )
            # Generate the summary report
            signal_summary[signal_name_front[0]] = description_front
            signal_summary[signal_name_front[1]] = description_front
            signal_summary[signal_name_left[0]] = description_left
            signal_summary[signal_name_left[1]] = description_left
            signal_summary[signal_name_rear[0]] = description_rear
            signal_summary[signal_name_rear[1]] = description_rear
            signal_summary[signal_name_right[0]] = description_right
            signal_summary[signal_name_right[1]] = description_right
            remark = (
                "Input timestamp (provided by GRAPPA) should be the same as the output timestamp (provided by TPP) "
                "and should be ascending."
            )
            self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_remark=remark)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")

            self.result.measured_result = FALSE

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1668571"],
            fc.TESTCASE_ID: ["40884"],
            fc.TEST_DESCRIPTION: ["Validate extrinsics"],
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
    name="TPP Extrinsics Range Check",
    description="Check the values of the extrinsics",
)
@register_inputs("/parking")
class TestExtrinsics(TestCase):
    """Example test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestExtrinsicsTestStep,
        ]
