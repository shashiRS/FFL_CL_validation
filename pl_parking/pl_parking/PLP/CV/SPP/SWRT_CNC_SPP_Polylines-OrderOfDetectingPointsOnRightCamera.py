#!/usr/bin/env python3
"""Validation of Test Case SWRT_CNC_SPP_Polylines-OrderOfDetectingPointsOnRightCamera."""

import logging
import os
import sys

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, get_color
from pl_parking.PLP.CV.SPP.constants import SensorSource, SppSigStatus
from pl_parking.PLP.CV.SPP.ft_helper import (
    SPPPreprocessor,
    SPPSignals,
    extract_polylines,
    get_number_of_polygons,
    get_number_of_polylines,
    get_polylines_sig_status,
)

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_pre_processor,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

__author__ = "<uib11434>"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "testcase_39967"


@teststep_definition(
    step_number=1,
    name="SWRT_CNC_SPP_Polylines-OrderOfDetectingPointsOnRightCamera",
    description="Check if the order of detecting the points on the right camera starts from positive values towards "
    "negative values on x-axis for each polyline.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SPPSignals)
@register_pre_processor(alias="check_signals", pre_processor=SPPPreprocessor)
class SppPolylinesOrderOfDetectingPointsOnRightCameraTestStep(TestStep):
    """Test step definition."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step."""
        super().__init__()
        self.test_result = fc.INPUT_MISSING
        self.sig_sum = None

    def process(self):
        """Process the simulated files."""
        _log.debug("Starting processing...")

        # Update the details from the results page with the needed information. All the information from
        # self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Initializing the result with data nok
        self.result.measured_result = DATA_NOK

        # Create empty lists for titles, plots and remarks, if they are needed.
        # Plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        # Initializing the dictionary with data for final evaluation table
        signal_summary = {}
        camera = SensorSource.SPP_RSC_DATA
        cam_test_result = DATA_NOK

        cameras_from_preprocessor, reader_df = self.pre_processors["check_signals"]
        pre_processor_result = cameras_from_preprocessor[camera]
        eval_cond = False
        cam_evaluation = " ".join(
            "All vertices are order on the right camera, they start from positive values towards negative values on "
            "x-axis for each polyline".split()
        )

        # get the availability of the signals
        signals_available, list_of_failed = pre_processor_result[0]

        if signals_available:
            # loop over the dataframe
            for frame, row in reader_df.iterrows():
                polylines_sig_status = get_polylines_sig_status(camera, row)
                number_of_polygons = get_number_of_polygons(camera, row)
                number_of_polylines = get_number_of_polylines(camera, row)

                if (
                    polylines_sig_status == SppSigStatus.AL_SIG_STATE_OK
                    and number_of_polygons > 0
                    and number_of_polylines > 0
                ):
                    eval_cond = True
                    start_index = number_of_polygons
                    end_index = number_of_polygons + number_of_polylines
                    polylines = extract_polylines(camera=camera, start=start_index, end=end_index, row=row)

                    for polyline_index, polyline in enumerate(polylines):
                        if not all(polyline[i][0] >= polyline[i + 1][0] for i in range(len(polyline) - 1)):
                            list_of_failed.append(
                                f"At frame {frame} vertices of "
                                f"Polyline[{polyline_index + number_of_polygons}] "
                                f"are not in descending order on x-axis"
                            )

            if eval_cond:
                if len(list_of_failed) > 0:
                    cam_test_result = fc.FAIL
                    # create an evaluation text for the moment when the test is failed
                    cam_evaluation = " ".join(
                        f"The evaluation is FAILED for {len(list_of_failed)} polylines: {list_of_failed[0]}".split()
                    )
                else:
                    cam_test_result = fc.PASS

            else:
                cam_evaluation = " ".join(
                    "Precondition are not meet: pSppPolylines.sSigHeader.eSigStatus != AL_SIG_STATE_OK, "
                    "pSppPolylines.numberOfPolygons <= 0, pSppPolylines.numberOfPolylines <= 0".split()
                )

        else:
            cam_evaluation = " ".join("Not all required signals are available in the bsig file. ".split())

        signal_summary[camera] = cam_evaluation

        remark = " ".join(
            "Check if the order of detecting the points on the right camera starts from positive values "
            "towards negative values on x-axis for each polyline.".split()
        )

        # The signal summary and observations will be converted to pandas
        # and finally the html table will be created with them
        self.sig_sum = fh.convert_dict_to_pandas(
            signal_summary=signal_summary,
            table_remark=remark,
            table_header_left="Camera Evaluation",
        )
        plots.append(self.sig_sum)

        if cam_test_result == DATA_NOK:
            self.test_result = fc.INPUT_MISSING
            self.result.measured_result = DATA_NOK
        elif cam_test_result == fc.FAIL:
            self.test_result = fc.FAIL
            self.result.measured_result = FALSE
        elif cam_test_result == fc.PASS:
            self.test_result = fc.PASS
            self.result.measured_result = TRUE

        result_df = {
            "Verdict": {"value": self.test_result.title(), "color": get_color(self.test_result)},
            fc.REQ_ID: ["1565911"],
            fc.TESTCASE_ID: ["39967"],
            fc.TEST_DESCRIPTION: [
                "Check if the order of detecting the points on the right camera starts from positive "
                "values towards negative values on x-axis for each polyline"
            ],
        }

        self.result.details["Additional_results"] = result_df

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)


@verifies("L3_SPP_1565911")
@testcase_definition(
    name="SWRT_CNC_SPP_Polylines-OrderOfDetectingPointsOnRightCamera",
    description="This test verifies if the order of detecting the points on the right camera starts from positive "
    "values towards negative values on x-axis for each polyline.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_znNc0F-qEe6hyY-R-i-gng&componentURI=https%3A%2F%2Fjazz.conti.de%2F"
    "rm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg&oslc.configuration="
    "https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17100",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SppPolylinesOrderOfDetectingPointsOnRightCamera(TestCase):
    """Test case definition."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SppPolylinesOrderOfDetectingPointsOnRightCameraTestStep,
        ]


# def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
#     """Optional, call to debug to set up debugging in the simplest possible way.
#
#     When calling the test case you need to provide a valid input to
#     execute the test (e.g. a BSIG file) and report the result.
#
#     This is only meant to jump start testcase debugging.
#     """
#     test_bsigs = [data_folder / f"001_2024.06.04_at_11.48.29.bsig"]
#     # test_bsigs = [data_folder / f"2024.04.08_at_08.34.35_camera-mi_128.bsig"]
#     # test_bsigs = [data_folder / f"test_input_{k}.bsig" for k in range(3)]
#     test_rec = [data_folder / "29_3.11.17_at_14.07.17_camera-mi_128.rrec"]
#     # os.makedirs(data_folder, exist_ok=True)
#     # for b in test_bsigs:
#     #     generate_bsig(b)
#
#     _, testrun_id, cp = debug(
#         SppPolylinesOrderOfDetectingPointsOnRightCamera,
#         *test_bsigs,
#         temp_dir=temp_dir,
#         open_explorer=open_explorer,
#         kpi_report=False,
#         dev_report=True,
#     )
#     return testrun_id, cp
#
#
# if __name__ == "__main__":
#     working_directory = Path(tempfile.mkdtemp("_tsf"))
#
#     # data_folder = working_directory / "data"
#     data_folder = Path('D:\\reporting-ui\\workspace\\pl_parking\\recordings')
#     out_folder = working_directory / "out"
#
#     testrun_id, cp = main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)
#
#     run_spec = out_folder / "run_spec.json"
#     report = Report(
#         testrun_id,
#         Path(os.path.join(out_folder, "report")),
#         out_folder,
#         run_spec,
#         development_details=True,
#         connection_provider=cp,
#         redo_all=True,
#         from_hpc_preprocessing=True,
#         is_regression=False,
#         overview_plugins=[
#             "pl_parking.minimal_example.CustomOverview",
#         ],
#     )
#
#     report.make_all()
#     _log.debug("All done.")
