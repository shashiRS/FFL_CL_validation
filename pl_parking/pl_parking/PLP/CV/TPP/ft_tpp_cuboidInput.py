"""TestCases performing all necessary checks for cuboid input."""

import logging
import os

import pandas as pd

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

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

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.CV.TPP.constants as ct
import pl_parking.PLP.CV.TPP.ft_helper as fh_tpp
from pl_parking.common_ft_helper import rep

FT_TPP = "FT_TPP_CUBOID_INPUT"

# TODO: Check the required names for teststep definition


@teststep_definition(
    step_number=1,
    name="TPP_ValidateInputCuboidConfidence",
    description="This test will verify if the confidence of cuboids provided by GRAPPA is in [0, 1] range",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPP, fh_tpp.GrappaSignals)
class TestCuboidConfidenceInputTestStep(TestStep):
    """Test Step definition."""

    custom_report = fh_tpp.TPPCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        reader = self.readers[FT_TPP]
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)

        # Geenerate a DF
        dict_list = []
        for _, row in reader.iterrows():
            ts = int(row["ts"])

            for classId in ct.GrappaCuboids:  # TODO: Remove magic numbers (6 represents the class IDs)
                first_idx_name = fh_tpp.GrappaSignals.Columns.DET_IDX_FIRST + str(classId)
                last_idx_name = fh_tpp.GrappaSignals.Columns.DET_IDX_LAST + str(classId)
                first_idx = int(row[first_idx_name])
                last_idx = int(row[last_idx_name])
                obj_dict = {}
                for i in range(first_idx, last_idx):
                    obj_dict["ts"] = ts
                    obj_dict["grappaClassId"] = int(row[fh_tpp.GrappaSignals.Columns.CLASS_ID + str(i)])
                    obj_dict["grappaClassConf"] = row[fh_tpp.GrappaSignals.Columns.CLASS_CONF + str(i)]
                    dict_list.append(obj_dict)

        df = pd.DataFrame(dict_list)

        # Perform confidence checks
        invalid_conf_df = df[(df["grappaClassConf"] < 0 | (df["grappaClassConf"] > 1))]

        if len(invalid_conf_df) > 0:
            test_result = fc.FAIL
        else:
            test_result = fc.PASS
        """
        fig = go.Figure(go.Pie(values=[valid_no_frames, invalid_no_frames], labels=['ok', 'not ok'],
                               marker={'colors': ['green', 'red']}))

        plot_titles.insert(0, "Ratio of invalid frames")
        plots.insert(0, fig)
        remarks.insert(0, "Ratio of invalid frames to number of frames")

        if len(invalid_frames_list) == 0:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL
        """
        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["TODO"],
            fc.TESTCASE_ID: ["TODO"],
            fc.TEST_SAFETY_RELEVANT: ["TODO"],
            fc.TEST_DESCRIPTION: ["TODO"],
            fc.TEST_RESULT: [test_result],
        }

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE
        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = result_df


@verifies("TODO")
@testcase_definition(
    name="TPP TPP_ValidateInputCuboidConfidence",
    description="This test will verify if the confidence of cuboids provided by GRAPPA is in [0, 1] range",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TestCuboidConfidenceInput(TestCase):
    """Input of cuboid confidence test case."""

    custom_report = fh_tpp.TPPCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestCuboidConfidenceInputTestStep,
        ]


@teststep_definition(
    step_number=1,
    name="TPP_ValidateInputCuboidClassTypes",
    description="This test will verify the class types of cuboids provided by GRAPPA",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPP, fh_tpp.GrappaSignals)
class TestCuboidClassTypesInputTestStep(TestStep):
    """Test Step definition."""

    custom_report = fh_tpp.TPPCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        reader = self.readers[FT_TPP]
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)

        # List signals to be read
        # object_members = [fh_tpp.GrappaSignals.Columns.CLASS_ID, fh_tpp.GrappaSignals.Columns.CLASS_CONF]

        # Geenerate a DF
        dict_list = []
        ok_class_type = True
        for _, row in reader.iterrows():
            ts = int(row["ts"])

            for classId in ct.GrappaCuboids:  # TODO: Remove magic numbers (6 represents the class IDs)
                first_idx_name = fh_tpp.GrappaSignals.Columns.DET_IDX_FIRST + str(classId)
                last_idx_name = fh_tpp.GrappaSignals.Columns.DET_IDX_LAST + str(classId)
                first_idx = int(row[first_idx_name])
                last_idx = int(row[last_idx_name])
                obj_dict = {}
                for i in range(first_idx, last_idx):
                    obj_dict["ts"] = ts
                    # for obj in object_members:
                    #     obj_dict[obj] = row[obj+str(i)]
                    obj_dict["grappaClassId"] = int(row[fh_tpp.GrappaSignals.Columns.CLASS_ID + str(i)])
                    obj_dict["grappaClassConf"] = row[fh_tpp.GrappaSignals.Columns.CLASS_CONF + str(i)]
                    dict_list.append(obj_dict)

                    # Check class types provided by indexes
                    if not obj_dict["grappaClassId"] == classId:
                        ok_class_type = False
                        pass
        # df = pd.DataFrame(dict_list)

        if ok_class_type:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL
        """
        fig = go.Figure(go.Pie(values=[valid_no_frames, invalid_no_frames], labels=['ok', 'not ok'],
                               marker={'colors': ['green', 'red']}))

        plot_titles.insert(0, "Ratio of invalid frames")
        plots.insert(0, fig)
        remarks.insert(0, "Ratio of invalid frames to number of frames")

        if len(invalid_frames_list) == 0:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL
        """
        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["TODO"],
            fc.TESTCASE_ID: ["TODO"],
            fc.TEST_SAFETY_RELEVANT: ["TODO"],
            fc.TEST_DESCRIPTION: ["TODO"],
            fc.TEST_RESULT: [test_result],
        }

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE
        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = result_df


@verifies("TODO")
@testcase_definition(
    name="TPP TPP_ValidateInputCuboidClassTpe",
    description="This test will verify the class types of cuboids provided by GRAPPA",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TestCuboidClassTypesInput(TestCase):
    """Input cuboid class type test case."""

    custom_report = fh_tpp.TPPCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestCuboidClassTypesInputTestStep,
        ]


@teststep_definition(
    step_number=1,
    name="TPP_ValidateInputCuboidKeyPoints",
    description="This test will verify the key points of cuboids provided by GRAPPA",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPP, fh_tpp.GrappaSignals)
class TestCuboidKeyPointsInputTestStep(TestStep):
    """Test Step definition."""

    custom_report = fh_tpp.TPPCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        reader = self.readers[FT_TPP]
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)

        # List signals to be read
        """
        object_members = [
            fh_tpp.GrappaSignals.Columns.CLASS_ID,
            fh_tpp.GrappaSignals.Columns.CLASS_CONF,
            fh_tpp.GrappaSignals.Columns.TOP_LEFT_X,
            fh_tpp.GrappaSignals.Columns.TOP_LEFT_Y,
            fh_tpp.GrappaSignals.Columns.BOTTOM_RIGHT_X,
            fh_tpp.GrappaSignals.Columns.BOTTOM_RIGHT_Y,
            fh_tpp.GrappaSignals.Columns.TOP_RIGHT_Y,
            fh_tpp.GrappaSignals.Columns.BOTTOM_LEFT_Y,
            fh_tpp.GrappaSignals.Columns.SECONDARY_FACE_X,
            fh_tpp.GrappaSignals.Columns.SECONDARY_FACE_BOTTOM_Y,
            fh_tpp.GrappaSignals.Columns.SECONDARY_FACE_TOP_Y,
            fh_tpp.GrappaSignals.Columns.SECONDARY_FACE_DETECTED,
        ]
        """

        # Geenerate a DF
        dict_list = []
        points_in_image = False
        for _, row in reader.iterrows():
            ts = int(row["ts"])

            for classId in ct.GrappaCuboids:  # TODO: Remove magic numbers (6 represents the class IDs)

                first_idx_name = fh_tpp.GrappaSignals.Columns.DET_IDX_FIRST + str(classId)
                last_idx_name = fh_tpp.GrappaSignals.Columns.DET_IDX_LAST + str(classId)
                first_idx = int(row[first_idx_name])
                last_idx = int(row[last_idx_name])
                obj_dict = {}
                for i in range(first_idx, last_idx):
                    obj_dict["ts"] = ts
                    obj_dict["grappaClassId"] = int(row[fh_tpp.GrappaSignals.Columns.CLASS_ID + str(i)])
                    obj_dict["classConf"] = row[fh_tpp.GrappaSignals.Columns.CLASS_CONF + str(i)]
                    obj_dict["topLeftX"] = row[fh_tpp.GrappaSignals.Columns.TOP_LEFT_X + str(i)]
                    obj_dict["topLeftY"] = row[fh_tpp.GrappaSignals.Columns.TOP_LEFT_Y + str(i)]
                    obj_dict["bottomRightX"] = row[fh_tpp.GrappaSignals.Columns.BOTTOM_RIGHT_X + str(i)]
                    obj_dict["bottomRightY"] = row[fh_tpp.GrappaSignals.Columns.BOTTOM_RIGHT_Y + str(i)]
                    obj_dict["topRightY"] = row[fh_tpp.GrappaSignals.Columns.TOP_RIGHT_Y + str(i)]
                    obj_dict["bottomLeftY"] = row[fh_tpp.GrappaSignals.Columns.BOTTOM_LEFT_Y + str(i)]
                    obj_dict["secondaryFaceX"] = row[fh_tpp.GrappaSignals.Columns.SECONDARY_FACE_X + str(i)]
                    obj_dict["secondaryFaceBottomY"] = row[
                        fh_tpp.GrappaSignals.Columns.SECONDARY_FACE_BOTTOM_Y + str(i)
                    ]
                    obj_dict["secondaryFaceTopY"] = row[fh_tpp.GrappaSignals.Columns.SECONDARY_FACE_TOP_Y + str(i)]

                    obj_dict["secondaryFaceDetected"] = row[
                        fh_tpp.GrappaSignals.Columns.SECONDARY_FACE_DETECTED + str(i)
                    ]

                    dict_list.append(obj_dict)

                    is_top_left_in_image = fh_tpp.is_in_image(obj_dict["topLeftX"], obj_dict["topLeftY"])
                    is_bottom_right_in_image = fh_tpp.is_in_image(obj_dict["bottomRightX"], obj_dict["bottomRightY"])
                    is_top_right_in_image = fh_tpp.is_in_image(obj_dict["bottomRightX"], obj_dict["topRightY"])
                    is_bottom_left_in_image = fh_tpp.is_in_image(obj_dict["topLeftX"], obj_dict["bottomLeftY"])

                    points_in_image = (
                        is_top_left_in_image
                        | is_bottom_right_in_image
                        | is_top_right_in_image
                        | is_bottom_left_in_image
                    )

                    if obj_dict["secondaryFaceDetected"]:
                        is_secondary_face_bottom_in_image = fh_tpp.is_in_image(
                            obj_dict["secondaryFaceX"], obj_dict["secondaryFaceBottomY"]
                        )
                        is_secondary_face_top_in_image = fh_tpp.is_in_image(
                            obj_dict["secondaryFaceX"], obj_dict["secondaryFaceTopY"]
                        )
                        points_in_image = (
                            points_in_image | is_secondary_face_bottom_in_image | is_secondary_face_top_in_image
                        )

                    if not points_in_image:
                        break

        if points_in_image:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["TODO"],
            fc.TESTCASE_ID: ["TODO"],
            fc.TEST_SAFETY_RELEVANT: ["TODO"],
            fc.TEST_DESCRIPTION: ["TODO"],
            fc.TEST_RESULT: [test_result],
        }

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE
        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = result_df


@verifies("TODO")
@testcase_definition(
    name="TPP TPP_ValidateInputCuboidKeyPoints",
    description="This test will verify the key points of cuboids provided by GRAPPA",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TestCuboidKeyPointsInput(TestCase):
    """Input cuboid key points test case."""

    custom_report = fh_tpp.TPPCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestCuboidKeyPointsInputTestStep,
        ]
