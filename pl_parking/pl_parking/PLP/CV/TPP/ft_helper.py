"""Helper file for TPP Test Scripts."""

import math
import os
import re
import time
from json import dumps

import cv2
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
import pl_parking.PLP.CV.TPP.constants as ct
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
img_path = relative_path + "3D_Labeling\\Images_Cylindrical\\"

img_path_front = img_path + "Front\\"
img_path_left = img_path + "Left\\"
img_path_rear = img_path + "Rear\\"
img_path_right = img_path + "Right\\"

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


class TPPSignals(SignalDefinition):
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

        for idx in range(0, 256):  # TODO: Edit magin numbers (256 = max num of obj)
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
        ):  # TODO: Edit magin numbers (22 = len grappa det indexes, but only the first 6 are of interest)
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


def check_size(df: pd.DataFrame, size: str, className: str) -> bool:
    """
    Compare the sizes of TPP object with defined thresholds.
    :param df: Pandas DataFrame containing TPP objects.
    :param size: The name of the size that will be checked (i.e. width, height, length).
    :param className: Tha class type that will be checked (i.e. Car, Pedestrian).
    :return: False if any checks fails, True otherwise.
    """
    for current_size in list(df[size]):
        if (
            current_size < ct.ObjectSizes[className][size]["min"]
            or current_size > ct.ObjectSizes[className][size]["max"]
        ):
            return False
    return True


def check_yaw(df: pd.DataFrame) -> bool:
    """
    Check the yaw value of TPP object.
    :param df: Pandas DataFrame containing TPP objects.
    :return: False if any checks fails, True otherwise.
    """
    for yaw in list(df[TPPSignals.Columns.YAW]):
        if (yaw < -PI) or (yaw > PI):
            return False
    return True


def check_confidence(df: pd.DataFrame):
    """
    Check the confidence value of TPP object.
    :param df: Pandas DataFrame containing TPP objects.
    :return: False if any checks fails, True otherwise.
    """
    for conf in list(df[TPPSignals.Columns.CONFIDENCE]):
        if (conf <= 0.0) or (conf >= 1.0):
            return False
    return True


def check_class_type(df: pd.DataFrame, expected_classes: list):
    """
    Check the class type of TPP object.
    :param df: Pandas DataFrame containing TPP objects.
    :param expected_classes: A string with the name of the expected class type.
    :return: False if any checks fails, True otherwise.
    """
    no_obj = len(df)
    no_required_classes = 0
    for classType in expected_classes:
        no_required_classes = no_required_classes + len(df[df["classType"] == ct.ClassTypes[classType]])

    return no_obj == no_required_classes


def is_in_image(x, y):
    """
    Check if a point is inside the image.
    Image is defined by width and height.
    :param x: x coordinate of the pixel.
    :param y: y coordinate of the pixel.
    :return: False when the point is not in image. True otherwise.
    """
    x_in_range = (0 <= x) & (x <= IMG_WIDTH)
    y_in_range = (0 <= y) & (y <= IMG_HEIGHT)
    return x_in_range & y_in_range


def check_center_point(df: pd.DataFrame):
    """
    Compute Euclidean Distance between the center of the object and (0,0) and compare it to the detection range.
    :param df: Pandas DataFrame containing TPP objects.
    :return: False if any checks fails, True otherwise.
    """
    return (
        ((df[TPPSignals.Columns.CENTERX] ** 2 + df[TPPSignals.Columns.CENTERY] ** 2) ** (1 / 2))
        <= ct.TPP_DETECTION_RANGE
    ).all()


# TODO: Remove if not used
def points_to_float_list(string_with_points):
    """
    Convert a string containing points to a list of floats.
    :param string_with_points: a string containing 3D points.
    :return: a list of 3D points.
    """
    string_list = re.findall("[-]?[0-9.0-9e+-]+", string_with_points)

    list_of_points = []
    for s in string_list:
        list_of_points.append(float(s))
    list_of_points = np.array(list_of_points).reshape(8, 3)

    return list_of_points


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
def read_images(image_path):
    """
    Read images from a specified path.
    :param image_path: Path to the file with images.
    :return: a list with the read images.
    """
    img_list = []

    for _, file_name in enumerate(os.listdir(image_path)):
        if file_name.split(".")[-1].lower() in {"jpg", "png"}:
            # if frame_counter % 1 == 0: # condition used to read less images
            img = cv2.imread(image_path + file_name)
            res = cv2.resize(img, dsize=(960, 640), interpolation=cv2.INTER_CUBIC)
            res_rgb = cv2.cvtColor(res, cv2.COLOR_BGR2RGB)

            img_list.append(res_rgb)

    return img_list


# TODO: Remove if not used
def generate_frames():
    """
    Generate a list of 2x2 frames from images provided by the camera.
    :return: a list with all the generated frames.
    """
    frames_list = []

    # get images
    img_list_front = read_images(img_path_front)
    img_list_left = read_images(img_path_left)
    img_list_rear = read_images(img_path_rear)
    img_list_right = read_images(img_path_right)

    for i in range(0, 150):
        frame = np.zeros((2 * HEIGHT, 2 * WIDTH, 3), dtype=np.uint8)

        setFrame(frame, img_list_front[i], 0, 0)
        setFrame(frame, img_list_left[i], 1, 0)
        setFrame(frame, img_list_rear[i], 0, 1)
        setFrame(frame, img_list_right[i], 1, 1)

        frames_list.append(frame)

    return frames_list


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


def generate_2d_objects(df: pd.DataFrame):
    """
    Generate smaller dataframes to easily draw 2d rectangles.
    :param df: DataFrame containing all required data(fid, oid, points).
    :return: DataFrame only with required columns to generate 2D figures.
    """
    sdf = df[["fid", "objectId", "objectClass"]].copy()
    pts_x = []
    pts_y = []
    for _, row in df.iterrows():
        pts = points_to_float_list(row.points)
        p_x = [pts[0][0], pts[2][0], pts[6][0], pts[4][0], pts[0][0]]
        p_y = [pts[0][1], pts[2][1], pts[6][1], pts[4][1], pts[0][1]]
        pts_x.append(p_x)
        pts_y.append(p_y)
    sdf["pts_x"] = pts_x
    sdf["pts_y"] = pts_y

    return sdf


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


# TODO: Remove if not used
# Not used
"""
def getErrors(errorDict: dict, errorTh: dict):

    significantErrorDict = dict()

    for d in errorDict:
        if (errorDict[d] > errorTh[d]):
            significantErrorDict[d] = errorDict[d]

    return significantErrorDict
"""


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
    :return: A list withh all errors provided by center points for each frame.
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
