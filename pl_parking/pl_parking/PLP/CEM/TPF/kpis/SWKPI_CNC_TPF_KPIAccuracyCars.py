"""TPF KPIs for Accuracy(Position, Orientation, Shape)"""

import glob
import logging
import os
import sys

# from pathlib import Path
import pandas as pd

# import tsf.io.sideload as side_load
# from tsf.core.common import PathSpecification
from tsf.core.results import Result
from tsf.core.testcase import (
    TestCase,
    TestStep,
    # register_side_load,
    register_signals,
    testcase_definition,
    teststep_definition,
)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.CEM.TPF.ft_helper as fh_tpf
import pl_parking.PLP.CEM.TPF.kpis.kpi_utils as utils

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

KPI_TPF = "KPI_TPF_ACCURACY"
# ALIAS_CSV = "KPI_TPF_CSV_GT"

tpf_object = fh_tpf.TPFSignals()


@teststep_definition(
    step_number=1,
    name="TPF_KPI_Accuracy_Cars",
    description="Run the Position Accuracy, Orientation Accuracy and Shape Accuracy KPIs for TPF.",
    expected_result=f"< {utils.position_accuracy_th}m",
)
@register_signals(KPI_TPF, fh_tpf.TPFSignals)
# @register_side_load(
#     alias=ALIAS_CSV,
#     side_load=side_load.CsvSideLoad,
#     path_spec=PathSpecification(folder=Path("D:\\Testing_TPP_TPF\\recs"), extension=".csv"),
# )
class TestStepAccuracyKPI(TestStep):
    """Test step definition"""

    custom_report = fh.MfCustomTeststepReport  # Specific overview

    def __init__(self):
        """Initialize the test-step."""
        super().__init__()
        self.artifacts = None
        self.sig_sum = None

    #
    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = fh.rep([], 3)

        # signal_summary = {}  # Initializing the dictionary with data for final evaluation table

        tpf_reader = self.readers[KPI_TPF]
        # We ignore the first 10 timestamps because the component might not be initialized
        tpf_reader = tpf_reader.iloc[10:]

        sig = tpf_object.Columns
        required_tpf_signals = [
            sig.SIGTIMESTAMP,
            sig.SIGSTATUS,
            sig.NUMBER_OF_OBJECTS,
            (sig.OBJECTS_ID, 0),
            (sig.OBJECTS_OBJECTCLASS, 0),
            (sig.OBJECTS_SHAPE_POINTS_0_POSITION_X, 0),
            (sig.OBJECTS_SHAPE_POINTS_0_POSITION_Y, 0),
            (sig.OBJECTS_SHAPE_POINTS_1_POSITION_X, 0),
            (sig.OBJECTS_SHAPE_POINTS_1_POSITION_Y, 0),
            (sig.OBJECTS_SHAPE_POINTS_2_POSITION_X, 0),
            (sig.OBJECTS_SHAPE_POINTS_2_POSITION_Y, 0),
            (sig.OBJECTS_SHAPE_POINTS_3_POSITION_X, 0),
            (sig.OBJECTS_SHAPE_POINTS_3_POSITION_Y, 0),
        ]

        number_of_unavailable_signals = 0
        for signal_name in required_tpf_signals:
            if signal_name not in list(tpf_reader.columns):
                number_of_unavailable_signals += 1

        # read GT
        # gt_df = self.side_load[ALIAS_CSV]
        file_path = os.path.abspath(self.artifacts[0].file_path)
        current_dir = os.path.dirname(file_path)
        csv_files = glob.glob(os.path.join(current_dir, "*.csv"))
        gt_df = pd.DataFrame([])
        for file in csv_files:
            gt_df = pd.read_csv(file)

        pred_df = utils.convert_reader_all_frames(tpf_reader)
        # Filter cars
        pred_df = pred_df[(pred_df["class"] == 1)].reset_index(drop=True)  # Class ID for CAR is 1

        kpi_df = pd.DataFrame()
        if number_of_unavailable_signals == 0:
            kpi_df = utils.compute_accuracy(gt_df=gt_df, pred_df=pred_df)

        # Compute the average of the accuracies
        n = len(kpi_df)
        avg_point_to_point_error = sum(kpi_df["Point-to-Point error"]) / n
        avg_position_accuracy = sum(kpi_df["Position Accuracy"]) / n
        avg_orientation_accuracy = sum(kpi_df["Orientation Accuracy"]) / n
        avg_shape_accuracy = sum(kpi_df["Shape Accuracy"]) / n

        # display only the first 3 decimals
        avg_point_to_point_error = f"{avg_point_to_point_error:.3f}"
        avg_position_accuracy = f"{avg_position_accuracy:.3f}"
        avg_orientation_accuracy = f"{avg_orientation_accuracy:.3f}"
        avg_shape_accuracy = f"{avg_shape_accuracy:.3f}"

        # Define the result of the KPI
        result_value = fc.NOT_ASSESSED
        if float(avg_position_accuracy) <= utils.position_accuracy_th:
            result_value = fc.PASS
            description = f"The test has <b>PASSED</b> with the Position Accuracy {avg_position_accuracy}[m] (<= {utils.position_accuracy_th}[m])."
        else:
            result_value = fc.FAIL
            description = (
                f"The test has <b>FAILED</b> with the Position Accuracy {avg_position_accuracy}[m] being "
                f"more than the given threshold: {utils.position_accuracy_th}[m]."
            )

        data = {
            "KPI": ["Position Accuracy"],
            "Description": [description],
        }
        kpi_result_df = pd.DataFrame(data)
        self.sig_sum = fh.build_html_table(kpi_result_df)
        plot_titles.append("")
        plots.append(fh.build_html_table(kpi_result_df))
        remarks.append("")

        # Define a pandas data frame with the average KPIs and plot a table
        data = {
            "Point to Point Error": [avg_point_to_point_error + "[m]"],
            "Position Accuracy": [avg_position_accuracy + "[m]"],
            "Orientation Accuracy": [avg_orientation_accuracy + "[degrees]"],
            "Shape Accuracy": [avg_shape_accuracy + "[%]"],
        }
        average_kpis_df = pd.DataFrame(data)
        plot_titles.append("")
        plots.append(fh.build_html_table(average_kpis_df))
        remarks.append(
            "Compute the Position Accuracy for TPF Cars.<br>"
            "Select a time frame and associate the detections with the GT using a distance based association.<br>"
            "Compute the error for each associated pair, then compute the average of the values.<br>"
            "The Position Accuracy is the Euclidean Distance between the GT point and detection point which are the "
            "closest to origin of the bounding boxes.<br>"
        )

        fig = utils.generate_accuracy_kpi_description(pred_df=pred_df, gt_df=gt_df)
        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

        avg_position_accuracy = utils.cast_to_optional_float(avg_position_accuracy)
        self.result.measured_result = Result(avg_position_accuracy)

        result_df = {
            "Verdict": {"value": result_value.title(), "color": fh.get_color(result_value)},
            fc.REQ_ID: ["TBD"],
            fc.TESTCASE_ID: ["98137"],
            fc.TEST_RESULT: [avg_position_accuracy],
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
    name="TPF_KPI_Accuracy_Cars",
    description="Run the Position Accuracy, Orientation Accuracy and Shape Accuracy KPIs for TPF.",
)
class AccuracyKPI(TestCase):
    """KPI Position Accuracy for cars"""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [TestStepAccuracyKPI]
