"""Helper file for TPP Test Scripts."""

import math
import os
import time
from json import dumps

# import cv2
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from tsf.core.report import (
    CustomReportTestCase,
    ProcessingResult,
    ProcessingResultsList,
    TeststepResult,
)
from tsf.core.testcase import (
    CustomReportTestStep,
)
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
from pl_parking.PLP.CV.TPP.constants import Thresholds

# TODO: Refactor
# TODO: Remove unnecessary functionality
# TODO: Bring required functions from TRC helper
# TODO: Move constants to a different file
# TODO: Update reader
# TODO: Documentation


# Path for test data, some tests will not work without this
script_dir = os.path.dirname(os.path.abspath(__file__))
relative_path = os.path.join(
    script_dir, "Recordings", "snip1_2022-03-04_12-23-43.012_Otto_LI-DC518_1646393095222790_1646393110222790"
)
# img_path = relative_path + "3D_Labeling\\Images_Cylindrical\\"
#
# img_path_front = img_path + "Front\\"
# img_path_left = img_path + "Left\\"
# img_path_rear = img_path + "Rear\\"
# img_path_right = img_path + "Right\\"

WIDTH = 960
HEIGHT = 640

IMG_WIDTH = 512.0
IMG_HEIGHT = 384.0
FT_TPP = "FT_TPP"

PI = 3.141592653589  # [radians]


def get_color(result):
    """
    Color the text based on the test case result.
    :param result: The result of the test case.
    :return: The color of the text.
    """
    if result == fc.PASS:
        # Green
        return "#28a745"
    elif result == fc.FAIL:
        # Red
        return "#dc3545"
    elif result == fc.INPUT_MISSING or result == "n/a" or result == "data nok":
        # Orange
        return "#ffc107"
    elif result == fc.NOT_ASSESSED or result == "data nok":
        # Grey
        return "#818589"
    else:
        # Red
        return "#dc3545"


class TPPCustomTeststepReport(CustomReportTestStep):
    """Class used to generate a custom test step report."""

    def overview(  # noqa: D102 Will be fixed in common_ft_helper then merged here
        self,
        processing_details_list: ProcessingResultsList,
        # teststep_result: List["TeststepResult"],
    ):
        s = ""

        pr_list = processing_details_list  # noqa: F841 Will be fixed in common_ft_helper then merged here
        s += "<br>"
        s += "<br>"

        # for d in range(len(pr_list)):
        #     json_entries = ProcessingResult.from_json(
        #         pr_list.processing_result_files[d])
        #     if "Plots" in json_entries.details and len(json_entries.details["Plots"]) > 1:
        #         s += f'<h4>Plots for failed measurements</h4>'
        #         s += f'<font color="red"><h7>{json_entries.details["file_name"]}</h7></font>'
        #         for plot in range(len(json_entries.details["Plots"])):

        #             s += json_entries.details["Plots"][plot]
        #             try:
        #                 s += f'<br>'
        #                 s += f'<h7>{json_entries.details["Remarks"][plot]}</h7>'
        #             except:
        #                 pass

        return s

    def details(self, processing_details: ProcessingResult, teststep_result: "TeststepResult") -> str:  # noqa: D102
        s = "<br>"
        # color = ""
        m_res = teststep_result.measured_result
        e_res = teststep_result.teststep_definition.expected_results[None]
        (
            _,
            status,
        ) = e_res.compute_result_status(m_res)
        verdict = status.key.lower()

        if "data nok" in verdict:
            verdict = fc.NOT_ASSESSED

        s += f'<span align="center" style="width: 100%; height: 100%; display: block;background-color: {get_color(verdict)}; color : #ffffff">Step result: {verdict.upper()}</span>'

        for k, v in processing_details.details.items():
            if "Plots" in k:
                s += "<div>"
                for plot in v:
                    s += plot
                s += "</div>"

        return s


class TPPCustomTestcaseReport(CustomReportTestCase):
    """Class used to generate a custom test case report."""

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()
        self.results = None
        self.result_dict = {}
        self.result_list = []
        self.anchor_list = []
        self.start_time = None

    def on_result(self, pr_details: ProcessingResult, ts_result: TeststepResult):  # noqa: D102

        if "Processing_time" in pr_details and self.start_time is None:
            self.start_time = pr_details["Processing_time"]
        # self._env.testrun.testcase_results
        if "Additional_results" in pr_details:
            a = {"Measurement": pr_details["file_name"]}

            a.update(pr_details["Additional_results"])
            self.result_list.append(a)
            self.anchor_list.append(
                f'"../teststeps_details/{ts_result.teststep_definition.id}_details_for_{ts_result.test_input.id}.html"'
            )

    def overview(self):  # noqa: D102

        results_dict = {
            fc.PASS.title(): 0,
            fc.FAIL.title(): 0,
            fc.INPUT_MISSING.title(): 0,
            fc.NOT_ASSESSED.title(): 0,
        }

        s = ""
        if self.start_time is not None:
            process_time = time.time() - self.start_time
            process_time = time.strftime("%M:%S", time.gmtime(process_time))
            s += "<h4> Processing time</h4>"
            s += f"<h5>{process_time} seconds</h5>"
            s += "<br>"
        try:
            columns = []
            row_events = []
            for r in self.result_list:
                columns.extend(list(r.keys()))
                break

            for d in self.result_list:
                r = []
                for c in columns:
                    if c in d:
                        v = d[c]
                        if isinstance(v, dict):
                            if "color" in v:
                                r.append(
                                    str(
                                        f"""<span align="center" style="width: 100%; height: 100%; display: block;background-color: {v['color']}; color : #ffffff">{v['value']}</span>"""
                                    )
                                )
                            else:
                                r.append(
                                    str(
                                        f"""<span align="center" style="width: 100%; height: 100%; display: block">{v['value']}</span>"""
                                    )
                                )
                        elif "Measurement" in c:
                            # r.append(v)
                            r.append(
                                str(
                                    f"""<span align="center" style="background-color: {d['Verdict']['color']}; color : #ffffff">{v}</span>"""
                                )
                            )

                            try:
                                results_dict[d["Verdict"]["value"]] += 1
                            except Exception as e:
                                print(str(e))
                        else:
                            r.append(v)

                    else:
                        r.append("")
                row_events.append(r)
            # for index in range(len(row_events)):

            #     row_events[index][0] = str(
            #         f"""<a href={self.anchor_list[index]}>{row_events[index][0]}</a>""")

            column_names = [{"title": str(c)} for c in columns]
            additional_tables = (
                """
            <h2>Additional Information</h2>
    <script>
    var table_column_names = """
                + dumps(column_names)
                + """;
var table_rows_events =  """
                + dumps(row_events)
                + """
$(document).ready(function() {
$('#events_table').DataTable( {
paging:    true,
searching: true,
info:      true,
scrollX: true,
ordering: true,
data: table_rows_events,
columns: table_column_names
} );
});
</script>
<table class="table-sm table-striped compact nowrap" id="events_table">
<caption>Table: Additional Information</caption>
</table>
"""
            )
            s += "<h4>Overview results</h4>"
            s += "<br>"
            s += f"<h6>Passed: {results_dict[fc.PASS.title()]}</h6>"
            s += f"<h6>Failed: {results_dict[fc.FAIL.title()]}</h6>"
            s += f"<h6>Input missing: {results_dict[fc.INPUT_MISSING.title()]}</h6>"
            s += f"<h6>Not assessed: {results_dict[fc.NOT_ASSESSED.title()]}</h6>"
            s += "<br>"
            s += additional_tables

        except:  # noqa: E722 Will be fixed in common_ft_helper then merged here
            s += "<h6>No additional info available</h6>"
        return s


class TPPSignals_R3(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        # Front Camera
        TIMESTAMP_FRONT = "timestampFront"
        VERSIONNUMBER_FRONT = "versionNumberFront"
        SIGTIMESTAMP_FRONT = "sigTimestampFront"
        SIGMEASCOUNTER_FRONT = "sigMeasCounterFront"
        SIGCYCLECOUNTER_FRONT = "sigCycleCounterFront"
        SIGSTATUS_FRONT = "sigStatusFront"
        SENSORSOURCE_FRONT = "sensorSourceFront"
        NUMOBJECTS_FRONT = "numObjectsFront"
        CLASSTYPE_FRONT = "classTypeFront"
        CONFIDENCE_FRONT = "confidenceFront"
        CENTERX_FRONT = "center_xFront"
        CENTERY_FRONT = "center_yFront"
        CENTERZ_FRONT = "center_zFront"
        LENGTH_FRONT = "lengthFront"
        WIDTH_FRONT = "widthFront"
        HEIGHT_FRONT = "heightFront"
        WIDTH_2D_FRONT = "width_2dFront"
        HEIGHT_2D_FRONT = "height_2dFront"
        YAW_FRONT = "yawFront"

        # Left Camera
        TIMESTAMP_LEFT = "timestampLeft"
        VERSIONNUMBER_LEFT = "versionNumberLeft"
        SIGTIMESTAMP_LEFT = "sigTimestampLeft"
        SIGMEASCOUNTER_LEFT = "sigMeasCounterLeft"
        SIGCYCLECOUNTER_LEFT = "sigCycleCounterLeft"
        SIGSTATUS_LEFT = "sigStatusLeft"
        SENSORSOURCE_LEFT = "sensorSourceLeft"
        NUMOBJECTS_LEFT = "numObjectsLeft"
        CLASSTYPE_LEFT = "classTypeLeft"
        CONFIDENCE_LEFT = "confidenceLeft"
        CENTERX_LEFT = "center_xLeft"
        CENTERY_LEFT = "center_yLeft"
        CENTERZ_LEFT = "center_zLeft"
        LENGTH_LEFT = "lengthLeft"
        WIDTH_LEFT = "widthLeft"
        HEIGHT_LEFT = "heightLeft"
        WIDTH_2D_LEFT = "width_2dLeft"
        HEIGHT_2D_LEFT = "height_2dLeft"
        YAW_LEFT = "yawLeft"

        # Rear Camera
        TIMESTAMP_REAR = "timestampRear"
        VERSIONNUMBER_REAR = "versionNumberRear"
        SIGTIMESTAMP_REAR = "sigTimestampRear"
        SIGMEASCOUNTER_REAR = "sigMeasCounterRear"
        SIGCYCLECOUNTER_REAR = "sigCycleCounterRear"
        SIGSTATUS_REAR = "sigStatusRear"
        SENSORSOURCE_REAR = "sensorSourceRear"
        NUMOBJECTS_REAR = "numObjectsRear"
        CLASSTYPE_REAR = "classTypeRear"
        CONFIDENCE_REAR = "confidenceRear"
        CENTERX_REAR = "center_xRear"
        CENTERY_REAR = "center_yRear"
        CENTERZ_REAR = "center_zRear"
        LENGTH_REAR = "lengthRear"
        WIDTH_REAR = "widthRear"
        HEIGHT_REAR = "heightRear"
        WIDTH_2D_REAR = "width_2dRear"
        HEIGHT_2D_REAR = "height_2dRear"
        YAW_REAR = "yawRear"

        # Right Camera
        TIMESTAMP_RIGHT = "timestampRight"
        VERSIONNUMBER_RIGHT = "versionNumberRight"
        SIGTIMESTAMP_RIGHT = "sigTimestampRight"
        SIGMEASCOUNTER_RIGHT = "sigMeasCounterRight"
        SIGCYCLECOUNTER_RIGHT = "sigCycleCounterRight"
        SIGSTATUS_RIGHT = "sigStatusRight"
        SENSORSOURCE_RIGHT = "sensorSourceRight"
        NUMOBJECTS_RIGHT = "numObjectsRight"
        CLASSTYPE_RIGHT = "classTypeRight"
        CONFIDENCE_RIGHT = "confidenceRight"
        CENTERX_RIGHT = "center_xRight"
        CENTERY_RIGHT = "center_yRight"
        CENTERZ_RIGHT = "center_zRight"
        LENGTH_RIGHT = "lengthRight"
        WIDTH_RIGHT = "widthRight"
        HEIGHT_RIGHT = "heightRight"
        WIDTH_2D_RIGHT = "width_2dRight"
        HEIGHT_2D_RIGHT = "height_2dRight"
        YAW_RIGHT = "yawRight"

    def get_properties(self):
        """Generate a string of signals to be read."""
        signal_dict = {}

        # Front
        signal_dict[self.Columns.TIMESTAMP_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            ".DynamicObjectsFront.timestamp",
        ]
        signal_dict[self.Columns.VERSIONNUMBER_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.uiVersionNumber",
        ]
        signal_dict[self.Columns.SIGTIMESTAMP_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
        ]
        signal_dict[self.Columns.SIGMEASCOUNTER_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiMeasurementCounter",
        ]
        signal_dict[self.Columns.SIGCYCLECOUNTER_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiCycleCounter",
        ]
        signal_dict[self.Columns.SIGSTATUS_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
        ]
        signal_dict[self.Columns.SENSORSOURCE_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.eSensorSource",
        ]
        signal_dict[self.Columns.NUMOBJECTS_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.numberOfObjects",
            ".DynamicObjectsFront.numObjects",
        ]
        signal_dict[self.Columns.CLASSTYPE_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].classType",
            ".DynamicObjectsFront.objects[%].classType",
        ]
        signal_dict[self.Columns.CONFIDENCE_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].confidence",
            ".DynamicObjectsFront.objects[%].confidence",
        ]
        signal_dict[self.Columns.CENTERX_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_x",
            ".DynamicObjectsFront.objects[%].centerPointWorld.x",
        ]
        signal_dict[self.Columns.CENTERY_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_y",
            ".DynamicObjectsFront.objects[%].centerPointWorld.y",
        ]
        signal_dict[self.Columns.CENTERZ_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_z",
            ".DynamicObjectsFront.objects[%].centerPointWorld.z",
        ]

        signal_dict[self.Columns.LENGTH_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.length",
            ".DynamicObjectsFront.objects[%].cuboidSizeWorld.x",
        ]
        signal_dict[self.Columns.WIDTH_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.width",
            ".DynamicObjectsFront.objects[%].cuboidSizeWorld.y",
        ]
        signal_dict[self.Columns.HEIGHT_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.height",
            ".DynamicObjectsFront.objects[%].cuboidSizeWorld.z",
        ]
        # Sizes of the Bounding Boxes
        # Only on CarPC
        signal_dict[self.Columns.WIDTH_2D_FRONT] = [".DynamicObjectsFront.objects[%].planeSizeWorld.x"]
        signal_dict[self.Columns.HEIGHT_2D_FRONT] = [".DynamicObjectsFront.objects[%].planeSizeWorld.y"]

        signal_dict[self.Columns.YAW_FRONT] = [
            ".RUM2TPP_FC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectYaw",
            ".DynamicObjectsFront.objects[%].cuboidYawWorld",
        ]

        # Left
        signal_dict[self.Columns.TIMESTAMP_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            ".DynamicObjectsLeft.timestamp",
        ]
        signal_dict[self.Columns.VERSIONNUMBER_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.uiVersionNumber",
        ]
        signal_dict[self.Columns.SIGTIMESTAMP_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
        ]
        signal_dict[self.Columns.SIGMEASCOUNTER_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiMeasurementCounter",
        ]
        signal_dict[self.Columns.SIGCYCLECOUNTER_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiCycleCounter",
        ]
        signal_dict[self.Columns.SIGSTATUS_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
        ]

        signal_dict[self.Columns.SENSORSOURCE_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.eSensorSource",
        ]
        signal_dict[self.Columns.NUMOBJECTS_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.numberOfObjects",
            ".DynamicObjectsLeft.numObjects",
        ]
        signal_dict[self.Columns.CLASSTYPE_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].classType",
            ".DynamicObjectsLeft.objects[%].classType",
        ]
        signal_dict[self.Columns.CONFIDENCE_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].confidence",
            ".DynamicObjectsLeft.objects[%].confidence",
        ]
        signal_dict[self.Columns.CENTERX_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_x",
            ".DynamicObjectsLeft.objects[%].centerPointWorld.x",
        ]
        signal_dict[self.Columns.CENTERY_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_y",
            ".DynamicObjectsLeft.objects[%].centerPointWorld.y",
        ]
        signal_dict[self.Columns.CENTERZ_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_z",
            ".DynamicObjectsLeft.objects[%].centerPointWorld.z",
        ]

        signal_dict[self.Columns.LENGTH_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.length",
            ".DynamicObjectsLeft.objects[%].cuboidSizeWorld.x",
        ]
        signal_dict[self.Columns.WIDTH_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.width",
            ".DynamicObjectsLeft.objects[%].cuboidSizeWorld.y",
        ]
        signal_dict[self.Columns.HEIGHT_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.height",
            ".DynamicObjectsLeft.objects[%].cuboidSizeWorld.z",
        ]
        # Sizes of the Bounding Boxes
        # Only on CarPC
        signal_dict[self.Columns.WIDTH_2D_LEFT] = [".DynamicObjectsLeft.objects[%].planeSizeWorld.x"]
        signal_dict[self.Columns.HEIGHT_2D_LEFT] = [".DynamicObjectsLeft.objects[%].planeSizeWorld.y"]

        signal_dict[self.Columns.YAW_LEFT] = [
            ".RUM2TPP_LSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectYaw",
            ".DynamicObjectsLeft.objects[%].cuboidYawWorld",
        ]

        # Rear
        signal_dict[self.Columns.TIMESTAMP_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            ".DynamicObjectsRear.timestamp",
        ]
        signal_dict[self.Columns.VERSIONNUMBER_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.uiVersionNumber",
        ]
        signal_dict[self.Columns.SIGTIMESTAMP_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
        ]
        signal_dict[self.Columns.SIGMEASCOUNTER_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiMeasurementCounter",
        ]
        signal_dict[self.Columns.SIGCYCLECOUNTER_REAR] = (
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiCycleCounter"
        )
        signal_dict[self.Columns.SIGSTATUS_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
        ]

        signal_dict[self.Columns.SENSORSOURCE_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.eSensorSource",
        ]
        signal_dict[self.Columns.NUMOBJECTS_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.numberOfObjects",
            ".DynamicObjectsRear.numObjects",
        ]
        signal_dict[self.Columns.CLASSTYPE_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].classType",
            ".DynamicObjectsRear.objects[%].classType",
        ]
        signal_dict[self.Columns.CONFIDENCE_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].confidence",
            ".DynamicObjectsRear.objects[%].confidence",
        ]
        signal_dict[self.Columns.CENTERX_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_x",
            ".DynamicObjectsRear.objects[%].centerPointWorld.x",
        ]
        signal_dict[self.Columns.CENTERY_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_y",
            ".DynamicObjectsRear.objects[%].centerPointWorld.y",
        ]
        signal_dict[self.Columns.CENTERZ_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_z",
            ".DynamicObjectsRear.objects[%].centerPointWorld.z",
        ]

        signal_dict[self.Columns.LENGTH_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.length",
            ".DynamicObjectsRear.objects[%].cuboidSizeWorld.x",
        ]
        signal_dict[self.Columns.WIDTH_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.width",
            ".DynamicObjectsRear.objects[%].cuboidSizeWorld.y",
        ]
        signal_dict[self.Columns.HEIGHT_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.height",
            ".DynamicObjectsRear.objects[%].cuboidSizeWorld.z",
        ]
        # Sizes of the Bounding Boxes
        # Only on CarPC
        signal_dict[self.Columns.WIDTH_2D_REAR] = [".DynamicObjectsRear.objects[%].planeSizeWorld.x"]
        signal_dict[self.Columns.HEIGHT_2D_REAR] = [".DynamicObjectsRear.objects[%].planeSizeWorld.y"]

        signal_dict[self.Columns.YAW_REAR] = [
            ".RUM2TPP_RC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectYaw",
            ".DynamicObjectsRear.objects[%].cuboidYawWorld",
        ]

        # Right
        signal_dict[self.Columns.TIMESTAMP_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            ".DynamicObjectsRight.timestamp",
        ]
        signal_dict[self.Columns.VERSIONNUMBER_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.uiVersionNumber",
        ]
        signal_dict[self.Columns.SIGTIMESTAMP_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
        ]
        signal_dict[self.Columns.SIGMEASCOUNTER_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiMeasurementCounter",
        ]
        signal_dict[self.Columns.SIGCYCLECOUNTER_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiCycleCounter",
        ]
        signal_dict[self.Columns.SIGSTATUS_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
        ]

        signal_dict[self.Columns.SENSORSOURCE_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.eSensorSource",
        ]
        signal_dict[self.Columns.NUMOBJECTS_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.numberOfObjects",
            ".DynamicObjectsRight.numObjects",
        ]
        signal_dict[self.Columns.CLASSTYPE_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].classType",
            ".DynamicObjectsRight.objects[%].classType",
        ]
        signal_dict[self.Columns.CONFIDENCE_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].confidence",
            ".DynamicObjectsRight.objects[%].confidence",
        ]
        signal_dict[self.Columns.CENTERX_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_x",
            ".DynamicObjectsRight.objects[%].centerPointWorld.x",
        ]
        signal_dict[self.Columns.CENTERY_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_y",
            ".DynamicObjectsRight.objects[%].centerPointWorld.y",
        ]
        signal_dict[self.Columns.CENTERZ_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].centerPoint_z",
            ".DynamicObjectsRight.objects[%].centerPointWorld.z",
        ]

        signal_dict[self.Columns.LENGTH_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.length",
            ".DynamicObjectsRight.objects[%].cuboidSizeWorld.x",
        ]
        signal_dict[self.Columns.WIDTH_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.width",
            ".DynamicObjectsRight.objects[%].cuboidSizeWorld.y",
        ]
        signal_dict[self.Columns.HEIGHT_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectSize.height",
            ".DynamicObjectsRight.objects[%].cuboidSizeWorld.z",
        ]
        # Sizes of the Bounding Boxes
        # Only on CarPC
        signal_dict[self.Columns.WIDTH_2D_RIGHT] = [".DynamicObjectsRight.objects[%].planeSizeWorld.x"]
        signal_dict[self.Columns.HEIGHT_2D_RIGHT] = [".DynamicObjectsRight.objects[%].planeSizeWorld.y"]

        signal_dict[self.Columns.YAW_RIGHT] = [
            ".RUM2TPP_RSC_DATA.pRum2ObjectDetection3DOutput.objects[%].objectYaw",
            ".DynamicObjectsRight.objects[%].cuboidYawWorld",
        ]

        return signal_dict

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "ADC5xx_Device", "M7board.EM_Thread", "CarPC.EM_Thread", "MTA_ADC5"]

        self._properties = self.get_properties()


class TPPSignalsR2(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        VERSIONNUMBER = "versionNumber"
        SIGTIMESTAMP = "sigTimestamp"
        SIGMEASCOUNTER = "sigMeasCounter"
        SIGCYCLECOUNTER = "sigCycleCounter"
        SIGSTATUS = "sigStatus"
        SENSORSOURCE = "sensorSource"
        NUMOBJECTS = "numObjects"
        CLASSTYPE = "classType"
        CONFIDENCE = "confidence"
        CENTERX = "center_x"
        CENTERY = "center_y"
        CENTERZ = "center_z"
        LENGTH = "length"
        WIDTH = "width"
        HEIGHT = "height"
        YAW = "yaw"

    def get_properties(self):
        """Generate a string of signals to be read."""
        signal_dict = {}
        signal_dict[self.Columns.VERSIONNUMBER] = ".RUM2TPP_FC_DATA.Rum2ObjectDetection3DOutputFc.uiVersionNumber"
        signal_dict[self.Columns.SIGTIMESTAMP] = ".RUM2TPP_FC_DATA.Rum2ObjectDetection3DOutputFc.sSigHeader.uiTimeStamp"
        signal_dict[self.Columns.SIGMEASCOUNTER] = (
            ".RUM2TPP_FC_DATA.Rum2ObjectDetection3DOutputFc.sSigHeader.uiMeasurementCounter"
        )
        signal_dict[self.Columns.SIGCYCLECOUNTER] = (
            ".RUM2TPP_FC_DATA.Rum2ObjectDetection3DOutputFc.sSigHeader.uiCycleCounter"
        )
        signal_dict[self.Columns.SIGSTATUS] = ".RUM2TPP_FC_DATA.Rum2ObjectDetection3DOutputFc.sSigHeader.eSigStatus"
        signal_dict[self.Columns.SENSORSOURCE] = ".RUM2TPP_FC_DATA.Rum2ObjectDetection3DOutputFc.eSensorSource"
        signal_dict[self.Columns.NUMOBJECTS] = ".RUM2TPP_FC_DATA.Rum2ObjectDetection3DOutputFc.numberOfObjects"

        for idx in range(0, 64):  # 64 is MAX_NO_OUTPUT TODO: Edit magic numbers
            signal_dict[self.Columns.CLASSTYPE + str(idx)] = (
                f".RUM2TPP_FC_DATA.Rum2ObjectDetection3DOutputFc.objects[{idx}].classType"
            )
            signal_dict[self.Columns.CONFIDENCE + str(idx)] = (
                f".RUM2TPP_FC_DATA.Rum2ObjectDetection3DOutputFc.objects[{idx}].confidence"
            )
            signal_dict[self.Columns.CENTERX + str(idx)] = (
                f".RUM2TPP_FC_DATA.Rum2ObjectDetection3DOutputFc.objects[{idx}].centerPoint_x"
            )
            signal_dict[self.Columns.CENTERY + str(idx)] = (
                f".RUM2TPP_FC_DATA.Rum2ObjectDetection3DOutputFc.objects[{idx}].centerPoint_y"
            )
            signal_dict[self.Columns.CENTERZ + str(idx)] = (
                f".RUM2TPP_FC_DATA.Rum2ObjectDetection3DOutputFc.objects[{idx}].centerPoint_z"
            )
            signal_dict[self.Columns.LENGTH + str(idx)] = (
                f".RUM2TPP_FC_DATA.Rum2ObjectDetection3DOutputFc.objects[{idx}].objectSize.length"
            )
            signal_dict[self.Columns.WIDTH + str(idx)] = (
                f".RUM2TPP_FC_DATA.Rum2ObjectDetection3DOutputFc.objects[{idx}].objectSize.width"
            )
            signal_dict[self.Columns.HEIGHT + str(idx)] = (
                f".RUM2TPP_FC_DATA.Rum2ObjectDetection3DOutputFc.objects[{idx}].objectSize.height"
            )
            signal_dict[self.Columns.YAW + str(idx)] = (
                f".RUM2TPP_FC_DATA.Rum2ObjectDetection3DOutputFc.objects[{idx}].objectYaw"
            )

        return signal_dict

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "ADC5xx_Device", "M7board.EM_Thread", "CarPC.EM_Thread"]

        self._properties = self.get_properties()


class TPPSignals(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        # # # # # # # # # # # Front Camera # # # # # # # # # # #
        TIMESTAMP_FRONT = "timestampFront"
        VERSIONNUMBER_FRONT = "versionNumberFront"
        # # # # # # # # # # Signal Header # # # # # # # # # #
        SIGTIMESTAMP_FRONT = "sigTimestampFront"
        SIGMEASCOUNTER_FRONT = "sigMeasCounterFront"
        SIGCYCLECOUNTER_FRONT = "sigCycleCounterFront"
        SIGSTATUS_FRONT = "sigStatusFront"
        # SENSORSOURCE_FRONT = "sensorSourceFront"
        # # # # # # # # # # # # Cuboids # # # # # # # # # # # #
        NUM_CUBOID_FRONT = "numCuboidFront"
        # CAR_CONFIDENCE_FRONT = "carConfidenceFront"  # TODO: Check the order
        # VAN_CONFIDENCE_FRONT = "vanConfidenceFront"  # TODO: Check the order
        # TRUCK_CONFIDENCE_FRONT = "TruckConfidenceFront"  # TODO: Check the order
        CUBOID_SUBCLASS_CONFIDENCE_FRONT = "cuboidSubClassConfidenceFront"
        CUBOID_CENTERX_FRONT = "cuboidCenter_xFront"
        CUBOID_CENTERY_FRONT = "cuboidCenter_yFront"
        CUBOID_CENTERZ_FRONT = "cuboidCenter_zFront"
        CUBOID_LENGTH_FRONT = "cuboidLengthFront"
        CUBOID_WIDTH_FRONT = "cuboidWidthFront"
        CUBOID_HEIGHT_FRONT = "cuboidHeightFront"
        CUBOID_CLASSTYPE_FRONT = "cuboidClassTypeFront"
        CUBOID_CONFIDENCE_FRONT = "cuboidConfidenceFront"
        CUBOID_YAW_FRONT = "cuboidYawFront"
        # # # # # # # # # # Bounding Boxes # # # # # # # # # #
        NUM_BBOX_FRONT = "numBBoxFront"
        # PEDESTRIAN_CONFIDENCE_FRONT = "pedestrianConfidenceFront"  # TODO: Check the order
        # TWOWHEELER_CONFIDENCE_FRONT = "twowheelerConfidenceFront"  # TODO: Check the order
        # SHOPPING_CART_CONFIDENCE_FRONT = "shoppingCartConfidenceFront"  # TODO: Check the order
        # ANIMAL_CONFIDENCE_FRONT = "animalConfidenceFront"  # TODO: Check the order
        BOX_SUBCLASS_CONFIDENCE_FRONT = "boxSubClassConfidenceFront"
        BOX_CENTERX_FRONT = "boxCenter_xFront"
        BOX_CENTERY_FRONT = "boxCenter_yFront"
        BOX_CENTERZ_FRONT = "boxCenter_zFront"
        BOX_WIDTH_FRONT = "boxWidthFront"
        BOX_HEIGHT_FRONT = "boxHeightFront"
        BOX_CLASSTYPE_FRONT = "boxClassTypeFront"
        BOX_CONFIDENCE_FRONT = "boxConfidenceFront"
        BOX_YAW_FRONT = "boxYawFront"

        # # # # # # # # # # # Left Camera # # # # # # # # # # #
        TIMESTAMP_LEFT = "timestampLeft"
        VERSIONNUMBER_LEFT = "versionNumberLeft"
        # # # # # # # # # # Signal Header # # # # # # # # # #
        SIGTIMESTAMP_LEFT = "sigTimestampLeft"
        SIGMEASCOUNTER_LEFT = "sigMeasCounterLeft"
        SIGCYCLECOUNTER_LEFT = "sigCycleCounterLeft"
        SIGSTATUS_LEFT = "sigStatusLeft"
        # # # # # # # # # # # # Cuboids # # # # # # # # # # # #
        NUM_CUBOID_LEFT = "numCuboidLeft"
        # CAR_CONFIDENCE_LEFT = "carConfidenceLeft"  # TODO: Check the order
        # VAN_CONFIDENCE_LEFT = "vanConfidenceLeft"  # TODO: Check the order
        # TRUCK_CONFIDENCE_LEFT = "TruckConfidenceLeft"  # TODO: Check the order
        CUBOID_SUBCLASS_CONFIDENCE_LEFT = "cuboidSubClassConfidenceLeft"
        CUBOID_CENTERX_LEFT = "cuboidCenter_xLeft"
        CUBOID_CENTERY_LEFT = "cuboidCenter_yLeft"
        CUBOID_CENTERZ_LEFT = "cuboidCenter_zLeft"
        CUBOID_LENGTH_LEFT = "cuboidLengthLeft"
        CUBOID_WIDTH_LEFT = "cuboidWidthLeft"
        CUBOID_HEIGHT_LEFT = "cuboidHeightLeft"
        CUBOID_CLASSTYPE_LEFT = "cuboidClassTypeLeft"
        CUBOID_CONFIDENCE_LEFT = "cuboidConfidenceLeft"
        CUBOID_YAW_LEFT = "cuboidYawLeft"
        # # # # # # # # # # Bounding Boxes # # # # # # # # # #
        NUM_BBOX_LEFT = "numBBoxLeft"
        # PEDESTRIAN_CONFIDENCE_LEFT = "pedestrianConfidenceLeft"  # TODO: Check the order
        # TWOWHEELER_CONFIDENCE_LEFT = "twowheelerConfidenceLeft"  # TODO: Check the order
        # SHOPPING_CART_CONFIDENCE_LEFT = "shoppingCartConfidenceLeft"  # TODO: Check the order
        # ANIMAL_CONFIDENCE_LEFT = "animalConfidenceLeft"  # TODO: Check the order
        BOX_SUBCLASS_CONFIDENCE_LEFT = "boxSubClassConfidenceLeft"
        BOX_CENTERX_LEFT = "boxCenter_xLeft"
        BOX_CENTERY_LEFT = "boxCenter_yLeft"
        BOX_CENTERZ_LEFT = "boxCenter_zLeft"
        BOX_WIDTH_LEFT = "boxWidthLeft"
        BOX_HEIGHT_LEFT = "boxHeightLeft"
        BOX_CLASSTYPE_LEFT = "boxClassTypeLeft"
        BOX_CONFIDENCE_LEFT = "boxConfidenceLeft"
        BOX_YAW_LEFT = "boxYawLeft"

        # # # # # # # # # # # Rear Camera # # # # # # # # # # #
        TIMESTAMP_REAR = "timestampRear"
        VERSIONNUMBER_REAR = "versionNumberRear"
        # # # # # # # # # # Signal Header # # # # # # # # # #
        SIGTIMESTAMP_REAR = "sigTimestampRear"
        SIGMEASCOUNTER_REAR = "sigMeasCounterRear"
        SIGCYCLECOUNTER_REAR = "sigCycleCounterRear"
        SIGSTATUS_REAR = "sigStatusRear"
        # # # # # # # # # # # # Cuboids # # # # # # # # # # # #
        NUM_CUBOID_REAR = "numCuboidRear"
        # CAR_CONFIDENCE_REAR = "carConfidenceRear"  # TODO: Check the order
        # VAN_CONFIDENCE_REAR = "vanConfidenceRear"  # TODO: Check the order
        # TRUCK_CONFIDENCE_REAR = "TruckConfidenceRear"  # TODO: Check the order
        CUBOID_SUBCLASS_CONFIDENCE_REAR = "cuboidSubClassConfidenceRear"
        CUBOID_CENTERX_REAR = "cuboidCenter_xRear"
        CUBOID_CENTERY_REAR = "cuboidCenter_yRear"
        CUBOID_CENTERZ_REAR = "cuboidCenter_zRear"
        CUBOID_LENGTH_REAR = "cuboidLengthRear"
        CUBOID_WIDTH_REAR = "cuboidWidthRear"
        CUBOID_HEIGHT_REAR = "cuboidHeightRear"
        CUBOID_CLASSTYPE_REAR = "cuboidClassTypeRear"
        CUBOID_CONFIDENCE_REAR = "cuboidConfidenceRear"
        CUBOID_YAW_REAR = "cuboidYawRear"
        # # # # # # # # # # Bounding Boxes # # # # # # # # # #
        NUM_BBOX_REAR = "numBBoxRear"
        # PEDESTRIAN_CONFIDENCE_REAR = "pedestrianConfidenceRear"  # TODO: Check the order
        # TWOWHEELER_CONFIDENCE_REAR = "twowheelerConfidenceRear"  # TODO: Check the order
        # SHOPPING_CART_CONFIDENCE_REAR = "shoppingCartConfidenceRear"  # TODO: Check the order
        # ANIMAL_CONFIDENCE_REAR = "animalConfidenceRear"  # TODO: Check the order
        BOX_SUBCLASS_CONFIDENCE_REAR = "boxSubClassConfidenceRear"
        BOX_CENTERX_REAR = "boxCenter_xRear"
        BOX_CENTERY_REAR = "boxCenter_yRear"
        BOX_CENTERZ_REAR = "boxCenter_zRear"
        BOX_WIDTH_REAR = "boxWidthRear"
        BOX_HEIGHT_REAR = "boxHeightRear"
        BOX_CLASSTYPE_REAR = "boxClassTypeRear"
        BOX_CONFIDENCE_REAR = "boxConfidenceRear"
        BOX_YAW_REAR = "boxYawRear"

        # # # # # # # # # # # Right Camera # # # # # # # # # # #
        TIMESTAMP_RIGHT = "timestampRight"
        VERSIONNUMBER_RIGHT = "versionNumberRight"
        # # # # # # # # # # Signal Header # # # # # # # # # #
        SIGTIMESTAMP_RIGHT = "sigTimestampRight"
        SIGMEASCOUNTER_RIGHT = "sigMeasCounterRight"
        SIGCYCLECOUNTER_RIGHT = "sigCycleCounterRight"
        SIGSTATUS_RIGHT = "sigStatusRight"
        # # # # # # # # # # # # Cuboids # # # # # # # # # # # #
        NUM_CUBOID_RIGHT = "numCuboidRight"
        # CAR_CONFIDENCE_RIGHT = "carConfidenceRight"  # TODO: Check the order
        # VAN_CONFIDENCE_RIGHT = "vanConfidenceRight"  # TODO: Check the order
        # TRUCK_CONFIDENCE_RIGHT = "TruckConfidenceRight"  # TODO: Check the order
        CUBOID_SUBCLASS_CONFIDENCE_RIGHT = "cuboidSubClassConfidenceRight"
        CUBOID_CENTERX_RIGHT = "cuboidCenter_xRight"
        CUBOID_CENTERY_RIGHT = "cuboidCenter_yRight"
        CUBOID_CENTERZ_RIGHT = "cuboidCenter_zRight"
        CUBOID_LENGTH_RIGHT = "cuboidLengthRight"
        CUBOID_WIDTH_RIGHT = "cuboidWidthRight"
        CUBOID_HEIGHT_RIGHT = "cuboidHeightRight"
        CUBOID_CLASSTYPE_RIGHT = "cuboidClassTypeRight"
        CUBOID_CONFIDENCE_RIGHT = "cuboidConfidenceRight"
        CUBOID_YAW_RIGHT = "cuboidYawRight"
        # # # # # # # # # # Bounding Boxes # # # # # # # # # #
        NUM_BBOX_RIGHT = "numBBoxRight"
        # PEDESTRIAN_CONFIDENCE_RIGHT = "pedestrianConfidenceRight"  # TODO: Check the order
        # TWOWHEELER_CONFIDENCE_RIGHT = "twowheelerConfidenceRight"  # TODO: Check the order
        # SHOPPING_CART_CONFIDENCE_RIGHT = "shoppingCartConfidenceRight"  # TODO: Check the order
        # ANIMAL_CONFIDENCE_RIGHT = "animalConfidenceRight"  # TODO: Check the order
        BOX_SUBCLASS_CONFIDENCE_RIGHT = "boxSubClassConfidenceRight"
        BOX_CENTERX_RIGHT = "boxCenter_xRight"
        BOX_CENTERY_RIGHT = "boxCenter_yRight"
        BOX_CENTERZ_RIGHT = "boxCenter_zRight"
        BOX_WIDTH_RIGHT = "boxWidthRight"
        BOX_HEIGHT_RIGHT = "boxHeightRight"
        BOX_CLASSTYPE_RIGHT = "boxClassTypeRight"
        BOX_CONFIDENCE_RIGHT = "boxConfidenceRight"
        BOX_YAW_RIGHT = "boxYawRight"

    def get_properties(self):
        """Generate a string of signals to be read."""
        signal_dict = {}

        # Front
        signal_dict[self.Columns.TIMESTAMP_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.timestamp",
        ]
        signal_dict[self.Columns.VERSIONNUMBER_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.uiVersionNumber",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.uiVersionNumber",
        ]
        signal_dict[self.Columns.SIGTIMESTAMP_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.timestamp",
        ]
        signal_dict[self.Columns.SIGMEASCOUNTER_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiMeasurementCounter",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.sSigHeader.uiMeasurementCounter",
        ]
        signal_dict[self.Columns.SIGCYCLECOUNTER_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiCycleCounter",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.sSigHeader.uiCycleCounter",
        ]
        signal_dict[self.Columns.SIGSTATUS_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.signalStatus",
        ]
        # Cuboids
        signal_dict[self.Columns.NUM_CUBOID_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.numberOfCuboidObjects",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.numberOfCuboidObjects",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.numberOfCuboidObjects",
        ]
        # signal_dict[self.Columns.CAR_CONFIDENCE_FRONT] = [
        #     "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences[0]",
        # ]
        # signal_dict[self.Columns.VAN_CONFIDENCE_FRONT] = [
        #     "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences[1]",
        # ]
        # signal_dict[self.Columns.TRUCK_CONFIDENCE_FRONT] = [
        #     "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences[2]",
        # ]
        signal_dict[self.Columns.CUBOID_SUBCLASS_CONFIDENCE_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences",
        ]
        signal_dict[self.Columns.CUBOID_CENTERX_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.x",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.x",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.cuboidObjects[%].centerPoint.x",
        ]
        signal_dict[self.Columns.CUBOID_CENTERY_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.y",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.y",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.cuboidObjects[%].centerPoint.y",
        ]
        signal_dict[self.Columns.CUBOID_CENTERZ_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.z",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.z",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.cuboidObjects[%].centerPoint.z",
        ]
        signal_dict[self.Columns.CUBOID_LENGTH_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.length",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.length",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.cuboidObjects[%].objectSize.length",
        ]
        signal_dict[self.Columns.CUBOID_WIDTH_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.width",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.width",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.cuboidObjects[%].objectSize.width",
        ]
        signal_dict[self.Columns.CUBOID_HEIGHT_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.height",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.height",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.cuboidObjects[%].objectSize.height",
        ]
        signal_dict[self.Columns.CUBOID_CLASSTYPE_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassId",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassId",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.cuboidObjects[%].subClassId",
        ]
        signal_dict[self.Columns.CUBOID_CONFIDENCE_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].confidence",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.cuboidObjects[%].confidence",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.cuboidObjects[%].confidence",
        ]
        signal_dict[self.Columns.CUBOID_YAW_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectYaw",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectYaw",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.cuboidObjects[%].objectYaw",
        ]
        # BBoxes
        signal_dict[self.Columns.NUM_BBOX_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.numberOfBBoxObjects",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.numberOfBBoxObjects",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.numberOfBBoxObjects",
        ]
        # signal_dict[self.Columns.PEDESTRIAN_CONFIDENCE_FRONT] = [
        #     "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences[0]",
        # ]
        # signal_dict[self.Columns.TWOWHEELER_CONFIDENCE_FRONT] = [
        #     "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences[1]",
        # ]
        # signal_dict[self.Columns.SHOPPING_CART_CONFIDENCE_FRONT] = [
        #     "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences[2]",
        # ]
        # signal_dict[self.Columns.ANIMAL_CONFIDENCE_FRONT] = [
        #     "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences[3]",
        # ]
        signal_dict[self.Columns.BOX_SUBCLASS_CONFIDENCE_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences",
        ]
        signal_dict[self.Columns.BOX_CENTERX_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.x",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.x",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.bBoxObjects[%].centerPoint.x",
        ]
        signal_dict[self.Columns.BOX_CENTERY_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.y",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.y",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.bBoxObjects[%].centerPoint.y",
        ]
        signal_dict[self.Columns.BOX_CENTERZ_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.z",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.z",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.bBoxObjects[%].centerPoint.z",
        ]
        signal_dict[self.Columns.BOX_WIDTH_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectSize.width",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectSize.width",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.bBoxObjects[%].objectSize.width",
        ]
        signal_dict[self.Columns.BOX_HEIGHT_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectSize.height",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectSize.height",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.bBoxObjects[%].objectSize.height",
        ]
        signal_dict[self.Columns.BOX_CLASSTYPE_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassId",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassId",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.bBoxObjects[%].subClassId",
        ]
        signal_dict[self.Columns.BOX_CONFIDENCE_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].confidence",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].confidence",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.bBoxObjects[%].confidence",
        ]
        signal_dict[self.Columns.BOX_YAW_FRONT] = [
            "MTA_ADC5.TPP_FC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectYaw",
            "SIM VFB.TPPINSTANCE_fc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectYaw",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListFront.bBoxObjects[%].objectYaw",
        ]

        # Left
        signal_dict[self.Columns.TIMESTAMP_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.timestamp",
        ]
        signal_dict[self.Columns.VERSIONNUMBER_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.uiVersionNumber",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.uiVersionNumber",
        ]
        signal_dict[self.Columns.SIGTIMESTAMP_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.timestamp",
        ]
        signal_dict[self.Columns.SIGMEASCOUNTER_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiMeasurementCounter",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.sSigHeader.uiMeasurementCounter",
        ]
        signal_dict[self.Columns.SIGCYCLECOUNTER_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiCycleCounter",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.sSigHeader.uiCycleCounter",
        ]
        signal_dict[self.Columns.SIGSTATUS_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.signalStatus",
        ]
        # Cuboids
        signal_dict[self.Columns.NUM_CUBOID_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.numberOfCuboidObjects",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.numberOfCuboidObjects",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.numberOfCuboidObjects",
        ]
        # signal_dict[self.Columns.CAR_CONFIDENCE_LEFT] = [
        #     "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences[0]",
        # ]
        # signal_dict[self.Columns.VAN_CONFIDENCE_LEFT] = [
        #     "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences[1]",
        # ]
        # signal_dict[self.Columns.TRUCK_CONFIDENCE_LEFT] = [
        #     "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences[2]",
        # ]
        signal_dict[self.Columns.CUBOID_SUBCLASS_CONFIDENCE_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences",
        ]
        signal_dict[self.Columns.CUBOID_CENTERX_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.x",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.x",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.cuboidObjects[%].centerPoint.x",
        ]
        signal_dict[self.Columns.CUBOID_CENTERY_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.y",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.y",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.cuboidObjects[%].centerPoint.y",
        ]
        signal_dict[self.Columns.CUBOID_CENTERZ_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.z",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.z",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.cuboidObjects[%].centerPoint.z",
        ]
        signal_dict[self.Columns.CUBOID_LENGTH_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.length",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.length",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.cuboidObjects[%].objectSize.length",
        ]
        signal_dict[self.Columns.CUBOID_WIDTH_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.width",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.width",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.cuboidObjects[%].objectSize.width",
        ]
        signal_dict[self.Columns.CUBOID_HEIGHT_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.height",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.height",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.cuboidObjects[%].objectSize.height",
        ]
        signal_dict[self.Columns.CUBOID_CLASSTYPE_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassId",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassId",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.cuboidObjects[%].subClassId",
        ]
        signal_dict[self.Columns.CUBOID_CONFIDENCE_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].confidence",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].confidence",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.cuboidObjects[%].confidence",
        ]
        signal_dict[self.Columns.CUBOID_YAW_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectYaw",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectYaw",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.cuboidObjects[%].objectYaw",
        ]
        # BBoxes
        signal_dict[self.Columns.NUM_BBOX_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.numberOfBBoxObjects",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.numberOfBBoxObjects",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.numberOfBBoxObjects",
        ]
        # signal_dict[self.Columns.PEDESTRIAN_CONFIDENCE_LEFT] = [
        #     "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences[0]",
        # ]
        # signal_dict[self.Columns.TWOWHEELER_CONFIDENCE_LEFT] = [
        #     "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences[1]",
        # ]
        # signal_dict[self.Columns.SHOPPING_CART_CONFIDENCE_LEFT] = [
        #     "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences[2]",
        # ]
        # signal_dict[self.Columns.ANIMAL_CONFIDENCE_LEFT] = [
        #     "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences[3]",
        # ]
        signal_dict[self.Columns.BOX_SUBCLASS_CONFIDENCE_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences",
        ]
        signal_dict[self.Columns.BOX_CENTERX_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.x",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.x",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.bBoxObjects[%].centerPoint.x",
        ]
        signal_dict[self.Columns.BOX_CENTERY_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.y",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.y",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.bBoxObjects[%].centerPoint.y",
        ]
        signal_dict[self.Columns.BOX_CENTERZ_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.z",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.z",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.bBoxObjects[%].centerPoint.z",
        ]
        signal_dict[self.Columns.BOX_WIDTH_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectSize.width",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectSize.width",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.bBoxObjects[%].objectSize.width",
        ]
        signal_dict[self.Columns.BOX_HEIGHT_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectSize.height",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectSize.height",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.bBoxObjects[%].objectSize.height",
        ]
        signal_dict[self.Columns.BOX_CLASSTYPE_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassId",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassId",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.bBoxObjects[%].subClassId",
        ]
        signal_dict[self.Columns.BOX_CONFIDENCE_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].confidence",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].confidence",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.bBoxObjects[%].confidence",
        ]
        signal_dict[self.Columns.BOX_YAW_LEFT] = [
            "MTA_ADC5.TPP_LSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectYaw",
            "SIM VFB.TPPINSTANCE_lsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectYaw",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListLeft.bBoxObjects[%].objectYaw",
        ]

        # Rear
        signal_dict[self.Columns.TIMESTAMP_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.timestamp",
        ]
        signal_dict[self.Columns.VERSIONNUMBER_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.uiVersionNumber",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.uiVersionNumber",
        ]
        signal_dict[self.Columns.SIGTIMESTAMP_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.timestamp",
        ]
        signal_dict[self.Columns.SIGMEASCOUNTER_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiMeasurementCounter",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.sSigHeader.uiMeasurementCounter",
        ]
        signal_dict[self.Columns.SIGCYCLECOUNTER_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiCycleCounter",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.sSigHeader.uiCycleCounter",
        ]
        signal_dict[self.Columns.SIGSTATUS_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.signalStatus",
        ]
        # Cuboids
        signal_dict[self.Columns.NUM_CUBOID_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.numberOfCuboidObjects",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.numberOfCuboidObjects",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.numberOfCuboidObjects",
        ]
        # signal_dict[self.Columns.CAR_CONFIDENCE_REAR] = [
        #     "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences[0]",
        # ]
        # signal_dict[self.Columns.VAN_CONFIDENCE_REAR] = [
        #     "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences[1]",
        # ]
        # signal_dict[self.Columns.TRUCK_CONFIDENCE_REAR] = [
        #     "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences[2]",
        # ]
        signal_dict[self.Columns.CUBOID_SUBCLASS_CONFIDENCE_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences",
        ]
        signal_dict[self.Columns.CUBOID_CENTERX_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.x",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.x",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.cuboidObjects[%].centerPoint.x",
        ]
        signal_dict[self.Columns.CUBOID_CENTERY_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.y",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.y",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.cuboidObjects[%].centerPoint.y",
        ]
        signal_dict[self.Columns.CUBOID_CENTERZ_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.z",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.z",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.cuboidObjects[%].centerPoint.z",
        ]
        signal_dict[self.Columns.CUBOID_LENGTH_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.length",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.length",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.cuboidObjects[%].objectSize.length",
        ]
        signal_dict[self.Columns.CUBOID_WIDTH_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.width",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.width",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.cuboidObjects[%].objectSize.width",
        ]
        signal_dict[self.Columns.CUBOID_HEIGHT_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.height",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.height",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.cuboidObjects[%].objectSize.height",
        ]
        signal_dict[self.Columns.CUBOID_CLASSTYPE_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassId",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassId",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.cuboidObjects[%].subClassId",
        ]
        signal_dict[self.Columns.CUBOID_CONFIDENCE_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].confidence",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.cuboidObjects[%].confidence",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.cuboidObjects[%].confidence",
        ]
        signal_dict[self.Columns.CUBOID_YAW_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectYaw",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectYaw",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.cuboidObjects[%].objectYaw",
        ]
        # BBoxes
        signal_dict[self.Columns.NUM_BBOX_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.numberOfBBoxObjects",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.numberOfBBoxObjects",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.numberOfBBoxObjects",
        ]
        # signal_dict[self.Columns.PEDESTRIAN_CONFIDENCE_REAR] = [
        #     "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences[0]",
        # ]
        # signal_dict[self.Columns.TWOWHEELER_CONFIDENCE_REAR] = [
        #     "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences[1]",
        # ]
        # signal_dict[self.Columns.SHOPPING_CART_CONFIDENCE_REAR] = [
        #     "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences[2]",
        # ]
        # signal_dict[self.Columns.ANIMAL_CONFIDENCE_REAR] = [
        #     "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences[3]",
        # ]
        signal_dict[self.Columns.BOX_SUBCLASS_CONFIDENCE_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences",
        ]
        signal_dict[self.Columns.BOX_CENTERX_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.x",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.x",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.bBoxObjects[%].centerPoint.x",
        ]
        signal_dict[self.Columns.BOX_CENTERY_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.y",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.y",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.bBoxObjects[%].centerPoint.y",
        ]
        signal_dict[self.Columns.BOX_CENTERZ_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.z",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.z",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.bBoxObjects[%].centerPoint.z",
        ]
        signal_dict[self.Columns.BOX_WIDTH_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectSize.width",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectSize.width",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.bBoxObjects[%].objectSize.width",
        ]
        signal_dict[self.Columns.BOX_HEIGHT_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectSize.height",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectSize.height",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.bBoxObjects[%].objectSize.height",
        ]
        signal_dict[self.Columns.BOX_CLASSTYPE_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassId",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassId",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.bBoxObjects[%].subClassId",
        ]
        signal_dict[self.Columns.BOX_CONFIDENCE_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].confidence",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].confidence",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.bBoxObjects[%].confidence",
        ]
        signal_dict[self.Columns.BOX_YAW_REAR] = [
            "MTA_ADC5.TPP_RC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectYaw",
            "SIM VFB.TPPINSTANCE_rc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectYaw",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRear.bBoxObjects[%].objectYaw",
        ]

        # Right
        signal_dict[self.Columns.TIMESTAMP_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.timestamp",
        ]
        signal_dict[self.Columns.VERSIONNUMBER_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.uiVersionNumber",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.uiVersionNumber",
        ]
        signal_dict[self.Columns.SIGTIMESTAMP_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.sSigHeader.uiTimeStamp",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.timestamp",
        ]
        signal_dict[self.Columns.SIGMEASCOUNTER_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiMeasurementCounter",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.sSigHeader.uiMeasurementCounter",
        ]
        signal_dict[self.Columns.SIGCYCLECOUNTER_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.uiCycleCounter",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.sSigHeader.uiCycleCounter",
        ]
        signal_dict[self.Columns.SIGSTATUS_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.sSigHeader.eSigStatus",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.signalStatus",
        ]
        # Cuboids
        signal_dict[self.Columns.NUM_CUBOID_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.numberOfCuboidObjects",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.numberOfCuboidObjects",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.numberOfCuboidObjects",
        ]
        # signal_dict[self.Columns.CAR_CONFIDENCE_RIGHT] = [
        #     "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences[0]",
        # ]
        # signal_dict[self.Columns.VAN_CONFIDENCE_RIGHT] = [
        #     "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences[1]",
        # ]
        # signal_dict[self.Columns.TRUCK_CONFIDENCE_RIGHT] = [
        #     "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences[2]",
        # ]
        signal_dict[self.Columns.CUBOID_SUBCLASS_CONFIDENCE_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassConfidences",
        ]
        signal_dict[self.Columns.CUBOID_CENTERX_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.x",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.x",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.cuboidObjects[%].centerPoint.x",
        ]
        signal_dict[self.Columns.CUBOID_CENTERY_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.y",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.y",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.cuboidObjects[%].centerPoint.y",
        ]
        signal_dict[self.Columns.CUBOID_CENTERZ_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.z",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].centerPoint.z",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.cuboidObjects[%].centerPoint.z",
        ]
        signal_dict[self.Columns.CUBOID_LENGTH_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.length",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.length",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.cuboidObjects[%].objectSize.length",
        ]
        signal_dict[self.Columns.CUBOID_WIDTH_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.width",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.width",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.cuboidObjects[%].objectSize.width",
        ]
        signal_dict[self.Columns.CUBOID_HEIGHT_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.height",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectSize.height",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.cuboidObjects[%].objectSize.height",
        ]
        signal_dict[self.Columns.CUBOID_CLASSTYPE_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassId",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].subClassId",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.cuboidObjects[%].subClassId",
        ]
        signal_dict[self.Columns.CUBOID_CONFIDENCE_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].confidence",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].confidence",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.cuboidObjects[%].confidence",
        ]
        signal_dict[self.Columns.CUBOID_YAW_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectYaw",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.cuboidObjects[%].objectYaw",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.cuboidObjects[%].objectYaw",
        ]
        # BBoxes
        signal_dict[self.Columns.NUM_BBOX_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.numberOfBBoxObjects",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.numberOfBBoxObjects",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.numberOfBBoxObjects",
        ]
        # signal_dict[self.Columns.PEDESTRIAN_CONFIDENCE_RIGHT] = [
        #     "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences[0]",
        # ]
        # signal_dict[self.Columns.TWOWHEELER_CONFIDENCE_RIGHT] = [
        #     "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences[1]",
        # ]
        # signal_dict[self.Columns.SHOPPING_CART_CONFIDENCE_RIGHT] = [
        #     "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences[2]",
        # ]
        # signal_dict[self.Columns.ANIMAL_CONFIDENCE_RIGHT] = [
        #     "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences[3]",
        # ]
        signal_dict[self.Columns.BOX_SUBCLASS_CONFIDENCE_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassConfidences",
        ]
        signal_dict[self.Columns.BOX_CENTERX_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.x",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.x",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.bBoxObjects[%].centerPoint.x",
        ]
        signal_dict[self.Columns.BOX_CENTERY_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.y",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.y",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.bBoxObjects[%].centerPoint.y",
        ]
        signal_dict[self.Columns.BOX_CENTERZ_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.z",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].centerPoint.z",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.bBoxObjects[%].centerPoint.z",
        ]
        signal_dict[self.Columns.BOX_WIDTH_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectSize.width",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectSize.width",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.bBoxObjects[%].objectSize.width",
        ]
        signal_dict[self.Columns.BOX_HEIGHT_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectSize.height",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectSize.height",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.bBoxObjects[%].objectSize.height",
        ]
        signal_dict[self.Columns.BOX_CLASSTYPE_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassId",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].subClassId",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.bBoxObjects[%].subClassId",
        ]
        signal_dict[self.Columns.BOX_CONFIDENCE_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].confidence",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].confidence",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.bBoxObjects[%].confidence",
        ]
        signal_dict[self.Columns.BOX_YAW_RIGHT] = [
            "MTA_ADC5.TPP_RSC_DATA.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectYaw",
            "SIM VFB.TPPINSTANCE_rsc.pRum2ObjectDetection3DOutput.boundingBoxObjects[%].objectYaw",
            "AP.svcModelProcessingOutput.data.dynamicObjectsListRight.bBoxObjects[%].objectYaw",
        ]

        return signal_dict

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "ADC5xx_Device", "M7board.EM_Thread", "CarPC.EM_Thread", "MTA_ADC5"]

        self._properties = self.get_properties()


example_obj = TPPSignals()


class GrappaSignals(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        CLASS_ID = "classId"
        CLASS_CONF = "classConf"
        DET_IDX_FIRST = "detIdxFirst"
        DET_IDX_LAST = "detIdxLast"
        TOP_LEFT_X = "topLeftX"
        TOP_LEFT_Y = "topLeftY"
        BOTTOM_RIGHT_X = "bottomRightX"
        BOTTOM_RIGHT_Y = "bottomRightY"
        TOP_RIGHT_Y = "topRightY"
        BOTTOM_LEFT_Y = "bottomLeftY"
        SECONDARY_FACE_X = "secondaryFaceX"
        SECONDARY_FACE_BOTTOM_Y = "secondaryFaceBottomY"
        SECONDARY_FACE_TOP_Y = "secondaryFaceTopY"
        SECONDARY_FACE_DETECTED = "secondaryFaceDetected"

    def get_properties(self):
        """Generate a string of signals to be read."""
        signal_dict = {}

        for idx in range(0, 256):  # TODO: Edit margin numbers (256 = max num of obj)
            signal_dict[self.Columns.CLASS_ID + str(idx)] = (
                f".GRAPPA_FC_DATA.GrappaDetectionResultsFc.GrappaDetections[{idx}].aClassConfidences[0].eClassID"
            )
            signal_dict[self.Columns.CLASS_CONF + str(idx)] = (
                f".GRAPPA_FC_DATA.GrappaDetectionResultsFc.GrappaDetections[{idx}].aClassConfidences[0].fClassConfidence"
            )
            signal_dict[self.Columns.TOP_LEFT_X + str(idx)] = (
                f".GRAPPA_FC_DATA.GrappaDetectionResultsFc.GrappaDetections[{idx}].fTopLeftX"
            )
            signal_dict[self.Columns.TOP_LEFT_Y + str(idx)] = (
                f".GRAPPA_FC_DATA.GrappaDetectionResultsFc.GrappaDetections[{idx}].fTopLeftY"
            )
            signal_dict[self.Columns.BOTTOM_RIGHT_X + str(idx)] = (
                f".GRAPPA_FC_DATA.GrappaDetectionResultsFc.GrappaDetections[{idx}].fBottomRightX"
            )
            signal_dict[self.Columns.BOTTOM_RIGHT_Y + str(idx)] = (
                f".GRAPPA_FC_DATA.GrappaDetectionResultsFc.GrappaDetections[{idx}].fBottomRightY"
            )
            signal_dict[self.Columns.TOP_RIGHT_Y + str(idx)] = (
                f".GRAPPA_FC_DATA.GrappaDetectionResultsFc.GrappaDetections[{idx}].fTopRightY"
            )
            signal_dict[self.Columns.BOTTOM_LEFT_Y + str(idx)] = (
                f".GRAPPA_FC_DATA.GrappaDetectionResultsFc.GrappaDetections[{idx}].fBottomLeftY"
            )
            signal_dict[self.Columns.SECONDARY_FACE_X + str(idx)] = (
                f".GRAPPA_FC_DATA.GrappaDetectionResultsFc.GrappaDetections[{idx}].fSecondaryFaceX"
            )
            signal_dict[self.Columns.SECONDARY_FACE_BOTTOM_Y + str(idx)] = (
                f".GRAPPA_FC_DATA.GrappaDetectionResultsFc.GrappaDetections[{idx}].fSecondaryFaceBottomY"
            )
            signal_dict[self.Columns.SECONDARY_FACE_TOP_Y + str(idx)] = (
                f".GRAPPA_FC_DATA.GrappaDetectionResultsFc.GrappaDetections[{idx}].fSecondaryFaceTopY"
            )
            signal_dict[self.Columns.SECONDARY_FACE_DETECTED + str(idx)] = (
                f".GRAPPA_FC_DATA.GrappaDetectionResultsFc.GrappaDetections[{idx}].bSecondaryFaceDetected"
            )

        for idx in range(
            0, 6
        ):  # TODO: Edit margin numbers (22 = len grappa det indexes, but only the first 6 are of interest)
            signal_dict[self.Columns.DET_IDX_FIRST + str(idx)] = (
                f".GRAPPA_FC_DATA.GrappaDetectionResultsFc.GrappaDetectionIndexes[{idx}].firstIdx"
            )
            signal_dict[self.Columns.DET_IDX_LAST + str(idx)] = (
                f".GRAPPA_FC_DATA.GrappaDetectionResultsFc.GrappaDetectionIndexes[{idx}].lastIdx"
            )

        return signal_dict

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "ADC5xx_Device", "M7board.EM_Thread", "CarPC.EM_Thread"]

        self._properties = self.get_properties()


def setFrame(frame: np.array, image: np.array, pos_x: int, pos_y: int):
    """
    Update the 2x2 frame with the input image on a specific position.
    :param frame: Stores the 2x2 frame.
    :param image: Image to replace the one existing in the frame.
    :param pos_x: Position to be replaced (0 <= x <= 1).
    :param pos_y: Position to be replaced (0 <= y <= 1).
    :return: None.
    """
    assert 0 <= pos_x <= 1
    assert 0 <= pos_y <= 1

    startX = pos_x * HEIGHT
    endX = (pos_x + 1) * HEIGHT
    startY = pos_y * WIDTH
    endY = (pos_y + 1) * (WIDTH)
    frame[startX:endX, startY:endY] = image


# TODO: Remove if not used
# def read_images(image_path):
#     """
#     Read images from a specified path.
#     :param image_path: Path to the file with images.
#     :return: a list with the read images.
#     """
#     img_list = []
#
#     for _, file_name in enumerate(os.listdir(image_path)):
#         if file_name.split(".")[-1].lower() in {"jpg", "png"}:
#             # if frame_counter % 1 == 0: # condition used to read less images
#             img = cv2.imread(image_path + file_name)
#             res = cv2.resize(img, dsize=(960, 640), interpolation=cv2.INTER_CUBIC)
#             res_rgb = cv2.cvtColor(res, cv2.COLOR_BGR2RGB)
#
#             img_list.append(res_rgb)
#
#     return img_list


# TODO: Remove if not used
# def generate_frames():
#     """
#     Generate a list of 2x2 frames from images provided by the camera.
#     :return: a list with all the generated frames.
#     """
#     frames_list = []
#
#     # get images
#     img_list_front = read_images(img_path_front)
#     img_list_left = read_images(img_path_left)
#     img_list_rear = read_images(img_path_rear)
#     img_list_right = read_images(img_path_right)
#
#     for i in range(0, 150):
#         frame = np.zeros((2 * HEIGHT, 2 * WIDTH, 3), dtype=np.uint8)
#
#         setFrame(frame, img_list_front[i], 0, 0)
#         setFrame(frame, img_list_left[i], 1, 0)
#         setFrame(frame, img_list_rear[i], 0, 1)
#         setFrame(frame, img_list_right[i], 1, 1)
#
#         frames_list.append(frame)
#
#     return frames_list


def generate_2d_figure(df: pd.DataFrame, fid: int, color: str):
    """
    Generate a figure with 2D objects for a specified frame.
    :param df: Dataframe containing only the ground points.
    :param fid: The id of the current frame.
    :param color: Color of the drawn object.
    :return: Plotly figure containing all objects for a specified frame.
    """
    fig = go.Figure()

    filtered_df = df[df.fid == fid].copy()
    for _, row in filtered_df.iterrows():
        fig.add_trace(
            go.Scatter(
                x=row.pts_x,
                y=row.pts_y,
                mode="lines",
                hovertext=row.objectId,
                name=str(row.objectClass) + " " + str(row.objectId),
                legendgroup=row.objectId,
                fill="toself",
                hoveron="points+fills",
                text=row.fid,
                marker=dict(color=color),
            )
        )

    return fig


def merge_2d_figures(fig1, fig2):
    """
    Merge 2d figures.
    :param fig1: Plotly figure.
    :param fig2: Plotly figure.
    :return: Plotly figure containing data from both figures.
    """
    merged_fig = go.Figure(data=fig1.data + fig2.data)
    return merged_fig


class GenericObject3D:
    """Store data for 3D objects from DataFrames."""

    def __init__(self, fid, objectId, centerPoint, size, yaw, className, points):
        """Initialize object attributes."""
        self.fid = fid
        self.objectId = objectId
        self.centerPoint = centerPoint
        self.size = size
        self.yaw = yaw
        self.className = className
        self.points = points


def get_points_error(gt_pts, pred_pts):
    """
    Generate a list with the points errors.
    :param gt_pts: List with groundtruth points.
    :param pred_pts: List with predicted points.
    :return: List with errors.
    """
    points_error_list = []
    for point_id in range(0, 8):
        dx = (gt_pts[point_id][0] - pred_pts[point_id][0]) ** 2
        dy = (gt_pts[point_id][1] - pred_pts[point_id][1]) ** 2
        # dz = (gt_pts[point_id][2] - pred_pts[point_id][2])**2

        d = math.sqrt(dx + dy)

        points_error_list.append(d)
    return points_error_list


# generate average error
def get_average_error(points_error_list):
    """
    Compute the average of the errors for an object.
    :param points_error_list: List with points of an object.
    :return: Average error.
    """
    my_sum = 0
    for p in points_error_list:
        my_sum += p
    n = max(1, len(points_error_list))
    return my_sum / n


# TODO: Remove if not used
# Not used
"""
# generate a dict with error th
def getErrorsTh(errorDict: dict):
    errorTh = dict()

    cfg_f = open("config.yaml", "r")
    cfg = yaml.load(cfg_f, loader.SafeLoader)

    for d in errorDict:
        errorTh[d] = cfg[d]

    return errorTh
"""


def compute_euclidean_distance(gt_points):
    """
    Return the dsitance to the closest point of the object.
    :param gt_points: A list with points from the ground truth dataframe.
    :return: Minimal euclidean distance.
    """
    min_distance = 100
    for p in gt_points:
        x = p[0]
        y = p[1]

        euclidean_distance = np.linalg.norm((x, y))
        min_distance = min(min_distance, euclidean_distance)
    return min_distance


def compareObject3D(gtObject: GenericObject3D, predictedObject: GenericObject3D):
    """
    Compare the objects and returns a dict with errors.
    :param gtObject: Generic ground truth TPP object .
    :param predictedObject: Generic predicted TPP object.
    :return: Return a dictionary containing errors of the detected object.
    """
    errorDict = dict()

    errorDict["errorCenterPoint_x"] = np.abs(gtObject.centerPoint[0] - predictedObject.centerPoint[0])  # [m]
    errorDict["errorCenterPoint_y"] = np.abs(gtObject.centerPoint[1] - predictedObject.centerPoint[1])  # [m]

    errorDict["errorCenterPoint_z"] = np.abs(gtObject.centerPoint[2] - predictedObject.centerPoint[2])  # [m]

    errorDict["errorSize_x"] = np.abs(gtObject.size[0] - predictedObject.size[0])  # [m]
    errorDict["errorSize_y"] = np.abs(gtObject.size[1] - predictedObject.size[1])  # [m]
    errorDict["errorSize_z"] = np.abs(gtObject.size[2] - predictedObject.size[2])  # [m]

    errorDict["errorYaw"] = float(gtObject.yaw - predictedObject.yaw)

    points_error_list = get_points_error(gtObject.points, predictedObject.points)
    errorDict["averageError"] = get_average_error(points_error_list)
    cp_x_error = errorDict["errorCenterPoint_x"][0] ** 2
    cp_y_error = errorDict["errorCenterPoint_y"][0] ** 2
    errorDict["centerError"] = math.sqrt(cp_x_error + cp_y_error)
    # errorDict['euclideanDistance'] = np.linalg.norm((gtObject.centerPoint[0], gtObject.centerPoint[1]))
    errorDict["euclideanDistance"] = compute_euclidean_distance(gtObject.points)

    return errorDict


def average_error_on_frame(df):
    """
    Generate a list with average errors of the objects provided by points in the specified range as a threshold.
    :param df: DataFrame with all the objects.
    :return: A list with average error for each frame.
    """
    sum_list = []
    n = len(np.unique(df.fid))
    for i in range(0, n):
        current_frame_df = df[(df.fid == i) & (df.euclideanDistance < Thresholds.DISTANCE_TH)].copy()
        my_sum = current_frame_df.averageError.sum()
        length = max(1, len(current_frame_df))
        sum_list.append(my_sum / length)
    return sum_list


# TODO: Merge the average functions (dupe-code)
def average_center_error_on_frame(df):
    """
    Generate a list with average errors of the objects provided by center points in range.
    :param df: DataFrame with all the objects.
    :return: A list with all errors provided by center points for each frame.
    """
    sum_list = []
    n = len(np.unique(df.fid))
    for i in range(0, n):
        current_frame_df = df[(df.fid == i) & (df.euclideanDistance < Thresholds.DISTANCE_TH)].copy()
        my_sum = current_frame_df.centerError.sum()
        length = max(1, len(current_frame_df))
        sum_list.append(my_sum / length)
    return sum_list


def update_figure_parameters(fig):
    """
    Update figure by adding shapes and resize it.
    :param fig: Plotly figure to be updated.
    :return: None .
    """
    # Draw the area of interest (circle)
    fig.add_shape(
        type="circle",
        opacity=0.2,
        fillcolor="green",
        x0=-Thresholds.DISTANCE_TH,
        y0=-Thresholds.DISTANCE_TH,
        x1=Thresholds.DISTANCE_TH,
        y1=Thresholds.DISTANCE_TH,
        name="Area of interest",
    )
    # Draw the reference vehicle
    # assuming it's on (0, 0, 0)
    fig.add_shape(type="circle", x0=-0.5, y0=-0.5, x1=0.5, y1=0.5, fillcolor="red", name="Test Vehicle")
    fig.update_layout(height=800, width=800, autosize=False)
    fig.update_xaxes(range=(-30, 30))
    fig.update_yaxes(range=(-30, 30))
