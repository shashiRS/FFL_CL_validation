"""TestCases checking the corner points of the detected object."""

import logging
import os
import sys

import numpy as np
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
import pl_parking.PLP.CEM.TPF.ft_helper as fh_tpf

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

FT_TPF_CENTER_POINT = "FT_TPF_CENTER_POINT"
CENTER_POINT_ERROR = 0.02  # [m]

tpf_object = fh_tpf.TPFSignals()


@teststep_definition(
    step_number=1,
    name="CenterPoint",
    description="This test will verify if the position of the center point is in the middle of the corner points, with "
    "a 2 cm error.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPF_CENTER_POINT, fh_tpf.TPFSignals)
class TestStepCenterPoint(TestStep):
    """Test step definition."""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.artifacts = None

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")

        test_result = fc.PASS
        plot_titles, plots, remarks = fh.rep([], 3)
        signal_summary = {}
        point_error_list = []
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        tpf_reader = self.readers[FT_TPF_CENTER_POINT]
        tpf_reader = tpf_reader.iloc[10:]  # First timestamps might not be initialized, so remove them

        sig = tpf_object.Columns
        required_tpf_signals = [
            sig.SIGSTATUS,
            sig.SIGTIMESTAMP,
            (sig.OBJECTS_OBJECTCLASS, 0),
            (sig.OBJECTS_CLASSPROBABILITY, 0),
            (sig.OBJECTS_SHAPE_POINTS_0_POSITION_X, 0),
            (sig.OBJECTS_SHAPE_POINTS_1_POSITION_X, 0),
            (sig.OBJECTS_SHAPE_POINTS_2_POSITION_X, 0),
            (sig.OBJECTS_SHAPE_POINTS_3_POSITION_X, 0),
            (sig.OBJECTS_SHAPE_POINTS_0_POSITION_Y, 0),
            (sig.OBJECTS_SHAPE_POINTS_1_POSITION_Y, 0),
            (sig.OBJECTS_SHAPE_POINTS_2_POSITION_Y, 0),
            (sig.OBJECTS_SHAPE_POINTS_3_POSITION_Y, 0),
            (sig.OBJECTS_SHAPE_REFERENCEPOINT_X, 0),
            (sig.OBJECTS_SHAPE_REFERENCEPOINT_Y, 0),
            (sig.OBJECTS_ID, 0),
            sig.NUMBER_OF_OBJECTS,
        ]

        point_description = "The evaluation of the signal is <b>PASSED</b>."

        number_of_unavailable_signals = 0
        for signal_name in required_tpf_signals:
            if signal_name not in list(tpf_reader.columns):
                number_of_unavailable_signals += 1

        if number_of_unavailable_signals == 0:
            # The center point should be in the middle of the shape points.
            for _, row in tpf_reader.iterrows():
                number_of_objects = int(row[sig.NUMBER_OF_OBJECTS])
                signal_state = row[sig.SIGSTATUS]
                # Run the test only if the signal state is ok
                if signal_state == fc.AL_SIG_STATE_OK:
                    for object_index in range(number_of_objects):
                        p0x = row[(sig.OBJECTS_SHAPE_POINTS_0_POSITION_X, object_index)]
                        p1x = row[(sig.OBJECTS_SHAPE_POINTS_1_POSITION_X, object_index)]
                        p2x = row[(sig.OBJECTS_SHAPE_POINTS_2_POSITION_X, object_index)]
                        p3x = row[(sig.OBJECTS_SHAPE_POINTS_3_POSITION_X, object_index)]
                        p0y = row[(sig.OBJECTS_SHAPE_POINTS_0_POSITION_Y, object_index)]
                        p1y = row[(sig.OBJECTS_SHAPE_POINTS_1_POSITION_Y, object_index)]
                        p2y = row[(sig.OBJECTS_SHAPE_POINTS_2_POSITION_Y, object_index)]
                        p3y = row[(sig.OBJECTS_SHAPE_POINTS_3_POSITION_Y, object_index)]
                        pts_x = [p0x, p1x, p2x, p3x]
                        pts_y = [p0y, p1y, p2y, p3y]
                        centroid = np.array([sum(pts_x) / len(pts_x), sum(pts_y) / len(pts_y)])
                        center_x = row[(sig.OBJECTS_SHAPE_REFERENCEPOINT_X, object_index)]
                        center_y = row[(sig.OBJECTS_SHAPE_REFERENCEPOINT_Y, object_index)]
                        reference_point = np.array([center_x, center_y])
                        reference_point_error = np.linalg.norm(centroid - reference_point)

                        if reference_point_error > CENTER_POINT_ERROR:
                            error_dict = {
                                "Signal name": tpf_object.get_properties()[sig.OBJECTS_SHAPE_REFERENCEPOINT_X],
                                "Timestamp": row[sig.SIGTIMESTAMP],
                                "Object ID": row[(sig.OBJECTS_ID, object_index)],
                                "Class": row[(sig.OBJECTS_OBJECTCLASS, object_index)],
                                "Confidence": row[(sig.OBJECTS_CLASSPROBABILITY, object_index)],
                                "Reference Point": [reference_point[0], reference_point[1]],
                                "Centroid": [centroid[0], centroid[1]],
                                "Error": reference_point_error,
                                "Description": "it is not in the middle of the shape points",
                                "Expected result": "expected < 2cm",
                            }
                            if test_result != fc.FAIL:
                                point_description = " ".join(
                                    f"The evaluation of the signal is <b>FAILED</b> at timestamp "
                                    f"{error_dict['Timestamp']} for object with ID {error_dict['Object ID']}, "
                                    f"class {error_dict['Class']} and confidence {error_dict['Confidence']} with "
                                    f"<b>Reference Point</b> {error_dict['Reference Point']} because "
                                    f"{error_dict['Description']} (expecting {error_dict['Centroid']}) with an "
                                    f"error of {error_dict['Error']}m ({error_dict['Expected result']}).".split()
                                )
                            test_result = fc.FAIL
                            point_error_list.append(error_dict)

        else:
            point_description = " ".join("Signal <b>not evaluated</b> because it is not available.".split())
            test_result = fc.NOT_ASSESSED

        signal_summary[tpf_object.get_properties()[sig.OBJECTS_SHAPE_REFERENCEPOINT_X][0]] = point_description
        remark = (
            ""
            "This test will verify if the position of the center point is in the middle of the corner points, with "
            "a 2 cm error.",
        )

        self.sig_sum = fh.convert_dict_to_pandas(
            signal_summary=signal_summary,
        )
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append(remark)
        # TODO: Update the IDs
        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2032270"],
            fc.TESTCASE_ID: ["89526"],
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
    requirement="2032270",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_BZbm4OU_Ee6f_fKhM-zv_g&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@testcase_definition(
    name="CenterPoint",
    description="This test will verify if the position of the center point is in the middle of the corner points, with "
    "a 2 cm error.",
)
@register_inputs("/parking")
class CenterPoint(TestCase):
    """Timestamp test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepCenterPoint,
        ]
