"""TestCases checking the corner points of the detected object."""

import logging
import os
import sys

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

FT_TPF_CORNER_POINTS = "FT_TPF_CORNER_POINTS"

tpf_object = fh_tpf.TPFSignals()


@teststep_definition(
    step_number=1,
    name="CornerPoints",
    description="This test will verify if the position of the corner points provided by TPF is defined and in "
    "[-250,250] m range and if the variance and covariance are in [0, 10000] [m^2] range",
    expected_result=BooleanResult(TRUE),
)
@register_signals(FT_TPF_CORNER_POINTS, fh_tpf.TPFSignals)
class TestStepCornerPoints(TestStep):
    """Test step definition."""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

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

        tpf_reader = self.readers[FT_TPF_CORNER_POINTS]
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
            (sig.OBJECTS_SHAPE_POINTS_0_VARIANCE_X, 0),
            (sig.OBJECTS_SHAPE_POINTS_1_VARIANCE_X, 0),
            (sig.OBJECTS_SHAPE_POINTS_2_VARIANCE_X, 0),
            (sig.OBJECTS_SHAPE_POINTS_3_VARIANCE_X, 0),
            (sig.OBJECTS_SHAPE_POINTS_0_VARIANCE_Y, 0),
            (sig.OBJECTS_SHAPE_POINTS_1_VARIANCE_Y, 0),
            (sig.OBJECTS_SHAPE_POINTS_2_VARIANCE_Y, 0),
            (sig.OBJECTS_SHAPE_POINTS_3_VARIANCE_Y, 0),
            (sig.OBJECTS_SHAPE_POINTS_0_COVARIANCE_XY, 0),
            (sig.OBJECTS_SHAPE_POINTS_1_COVARIANCE_XY, 0),
            (sig.OBJECTS_SHAPE_POINTS_2_COVARIANCE_XY, 0),
            (sig.OBJECTS_SHAPE_POINTS_3_COVARIANCE_XY, 0),
            (sig.OBJECTS_ID, 0),
            sig.NUMBER_OF_OBJECTS,
        ]

        point_description = "The evaluation of the signal is <b>PASSED</b>."

        number_of_unavailable_signals = 0
        for signal_name in required_tpf_signals:
            if signal_name not in list(tpf_reader.columns):
                number_of_unavailable_signals += 1

        if number_of_unavailable_signals == 0:
            # The reference point and should be in [-250, 250] m range.
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
                        pts = [p0x, p1x, p2x, p3x, p0y, p1y, p2y, p3y]
                        v0x = row[(sig.OBJECTS_SHAPE_POINTS_0_VARIANCE_X, object_index)]
                        v1x = row[(sig.OBJECTS_SHAPE_POINTS_1_VARIANCE_X, object_index)]
                        v2x = row[(sig.OBJECTS_SHAPE_POINTS_2_VARIANCE_X, object_index)]
                        v3x = row[(sig.OBJECTS_SHAPE_POINTS_3_VARIANCE_X, object_index)]
                        v0y = row[(sig.OBJECTS_SHAPE_POINTS_0_VARIANCE_Y, object_index)]
                        v1y = row[(sig.OBJECTS_SHAPE_POINTS_1_VARIANCE_Y, object_index)]
                        v2y = row[(sig.OBJECTS_SHAPE_POINTS_2_VARIANCE_Y, object_index)]
                        v3y = row[(sig.OBJECTS_SHAPE_POINTS_3_VARIANCE_Y, object_index)]
                        cov0xy = row[(sig.OBJECTS_SHAPE_POINTS_0_COVARIANCE_XY, object_index)]
                        cov1xy = row[(sig.OBJECTS_SHAPE_POINTS_1_COVARIANCE_XY, object_index)]
                        cov2xy = row[(sig.OBJECTS_SHAPE_POINTS_2_COVARIANCE_XY, object_index)]
                        cov3xy = row[(sig.OBJECTS_SHAPE_POINTS_3_COVARIANCE_XY, object_index)]
                        var_list = [v0x, v1x, v2x, v3x, v0y, v1y, v2y, v3y, cov0xy, cov1xy, cov2xy, cov3xy]

                        for p in pts:
                            if p < -250 or p > 250:  # [m]
                                error_dict = {
                                    "Signal name": tpf_object.get_properties()[sig.OBJECTS_SHAPE_REFERENCEPOINT_X],
                                    "Timestamp": row[sig.SIGTIMESTAMP],
                                    "Object ID": row[(sig.OBJECTS_ID, object_index)],
                                    "Class": row[(sig.OBJECTS_OBJECTCLASS, object_index)],
                                    "Confidence": row[(sig.OBJECTS_CLASSPROBABILITY, object_index)],
                                    "Corner Point": p,
                                    "Description": "out of range",
                                    "Expected result": "[-250, 250]",
                                }
                                if test_result != fc.FAIL:
                                    point_description = " ".join(
                                        f"The evaluation of the signal is <b>FAILED</b> at timestamp {error_dict['Timestamp']} "
                                        f"for object with ID {error_dict['Object ID']} and class {error_dict['Class']} "
                                        f"and confidence {error_dict['Confidence']} with <b>Corner Point coordinate</b>"
                                        f" {error_dict['Corner Point']} which is "
                                        f"{error_dict['Description']} ({error_dict['expected_result']}).".split()
                                    )
                                test_result = fc.FAIL
                                point_error_list.append(error_dict)

                        for var in var_list:
                            if var < 0 or var > 10000:  # [m^2]
                                error_dict = {
                                    "Signal name": tpf_object.get_properties()[sig.OBJECTS_SHAPE_REFERENCEPOINT_X],
                                    "Timestamp": row[sig.SIGTIMESTAMP],
                                    "Object ID": row[(sig.OBJECTS_ID, object_index)],
                                    "Class": row[(sig.OBJECTS_OBJECTCLASS, object_index)],
                                    "Confidence": row[(sig.OBJECTS_CLASSPROBABILITY, object_index)],
                                    "Variance": var,
                                    "Description": "out of range",
                                    "Expected result": "[0, 10000]",
                                }
                                if test_result != fc.FAIL:
                                    point_description = " ".join(
                                        f"The evaluation of the signal is <b>FAILED</b> at timestamp {error_dict['Timestamp']} "
                                        f"for object with ID {error_dict['Object ID']} and class {error_dict['Class']} "
                                        f"and confidence {error_dict['Confidence']} with <b>Variance</b> "
                                        f"{error_dict['Variance']} which is "
                                        f"{error_dict['Description']} ({error_dict['Expected result']}).".split()
                                    )
                                test_result = fc.FAIL
                                point_error_list.append(error_dict)
        else:
            point_description = " ".join("Signal <b>not evaluated</b> because it is not available.".split())
            test_result = fc.NOT_ASSESSED

        signal_summary[tpf_object.get_properties()[sig.OBJECTS_SHAPE_REFERENCEPOINT_X][0]] = point_description
        remark = (
            "This test will verify if the position of the corner points by TPF is in [-250,250] [m] range."
            "This test will verify if the variance and covariance is in [0, 10000] [m^2] range."
        )
        self.sig_sum = fh.convert_dict_to_pandas(
            signal_summary=signal_summary,
        )
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append(remark)

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
    name="CornerPoints",
    description="This test will verify if the position of the corner points provided by TPF is defined and in "
    "[-250,250] m range and if the variance and covariance are in [0, 10000] [m^2] range",
)
@register_inputs("/parking")
class CornerPoints(TestCase):
    """Timestamp test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepCornerPoints,
        ]
