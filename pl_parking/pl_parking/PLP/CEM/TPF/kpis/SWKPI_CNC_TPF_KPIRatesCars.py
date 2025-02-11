"""TPF KPIs"""

import glob
import logging
import os
import sys

# from pathlib import Path
import numpy as np
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

KPI_TPF = "KPI_TPF_READER"
ALIAS_CSV = "KPI_TPF_CSV_GT"

tpf_object = fh_tpf.TPFSignals()


@teststep_definition(
    step_number=1,
    name="TPF_KPI_TruePositiveRate",
    description="Run the True Positive Rate KPI for TPF. Note: Also compute False Positive Rate, "
    "False Negative Rate, Precision and Recall, but this does not affect the verdict.",
    expected_result=f"{utils.tpr_cars}%",
)
@register_signals(KPI_TPF, fh_tpf.TPFSignals)
# @register_side_load(
#     alias=ALIAS_CSV,
#     side_load=side_load.CsvSideLoad,
#     path_spec=PathSpecification(folder=Path("D:\\Testing_TPP_TPF\\recs"), extension=".csv"),
# )
class TestStepKPIRates(TestStep):
    """Test step definition"""

    custom_report = fh.MfCustomTeststepReport  # Specific overview

    def __init__(self):
        """Initialize the test-step."""
        super().__init__()
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
        pred_df = pred_df[(pred_df["numObj"] == 0) | (pred_df["class"] == 1)]  # Class ID for CAR is 1
        unique_ts = np.unique(pred_df["ts"])

        kpi_list = []
        if number_of_unavailable_signals == 0:
            for ts in unique_ts:
                this_pred_df = pred_df[pred_df["ts"] == ts]
                this_gt_df = gt_df[gt_df["ts"] == ts]

                kpi_dict = utils.compute_frame_kpi(gt_df=this_gt_df, pred_df=this_pred_df, ts=ts)
                kpi_list.append(kpi_dict)
        kpi_df = pd.DataFrame(kpi_list)

        # Compute the average value of the KPIs
        # 1. Compute the KPIs for each frame and then compute the average from that values
        # precision_on_all_frames = sum(kpi_df["precision"]) / len(kpi_df["precision"])
        # recall_on_all_frames = sum(kpi_df["recall"]) / len(kpi_df["recall"])
        # tpr_on_all_frames = sum(kpi_df["TPR"]) / len(kpi_df["TPR"])
        # fpr_on_all_frames = sum(kpi_df["FPR"]) / len(kpi_df["FPR"])
        # fnr_on_all_frames = sum(kpi_df["FNR"]) / len(kpi_df["FNR"])
        # 2. Count TP, FP, FN for all frames and then compute the KPIs
        num_tp = sum(kpi_df["TP"])
        num_fp = sum(kpi_df["FP"])
        num_fn = sum(kpi_df["FN"])
        precision_on_all_frames = num_tp / (num_tp + num_fp) * 100
        recall_on_all_frames = num_tp / (num_tp + num_fn) * 100
        tpr_on_all_frames = num_tp / (num_tp + num_fp + num_fn) * 100
        fpr_on_all_frames = num_fp / (num_tp + num_fp + num_fn) * 100
        fnr_on_all_frames = num_fn / (num_tp + num_fp + num_fn) * 100

        # display only the first 3 decimals
        precision_on_all_frames = f"{precision_on_all_frames:.3f}"
        recall_on_all_frames = f"{recall_on_all_frames:.3f}"
        tpr_on_all_frames = f"{tpr_on_all_frames:.3f}"
        fpr_on_all_frames = f"{fpr_on_all_frames:.3f}"
        fnr_on_all_frames = f"{fnr_on_all_frames:.3f}"

        # Define the result of the KPI
        result_value = fc.NOT_ASSESSED
        if float(tpr_on_all_frames) >= utils.tpr_cars:
            result_value = fc.PASS
            description = f"The test has <b>PASSED</b> with the TPR {tpr_on_all_frames}[%] (>= {utils.tpr_cars}[%])."
        else:
            result_value = fc.FAIL
            description = (
                f"The test has <b>FAILED</b> with the TPR {tpr_on_all_frames}[%] being "
                f"less than the given threshold: {utils.tpr_cars}[%]."
            )

        data = {
            "KPI": ["TPR"],
            "Description": [description],
        }
        kpi_result_df = pd.DataFrame(data)
        self.sig_sum = fh.build_html_table(kpi_result_df)
        plot_titles.append("")
        plots.append(fh.build_html_table(kpi_result_df))
        remarks.append("")

        # Define a pandas data frame with the average KPIs and plot a table
        data = {
            "Precision": [precision_on_all_frames + "[%]"],
            "Recall": [recall_on_all_frames + "[%]"],
            "TPR": [tpr_on_all_frames + "[%]"],
            "FPR": [fpr_on_all_frames + "[%]"],
            "FNR": [fnr_on_all_frames + "[%]"],
        }
        average_kpis_df = pd.DataFrame(data)
        plot_titles.append("")
        plots.append(fh.build_html_table(average_kpis_df))
        remarks.append("")

        fig = utils.generate_bar_chart_TPR(kpi_df)
        plot_titles.append("KPI evaluation for cars")
        plots.append(fig)
        remarks.append("")

        fig, remark = utils.generate_kpi_custom_description()
        plot_titles.append("KPI values for the custom scenario")
        plots.append(fig)
        remarks.append(remark)

        avg_tpr_optional = utils.cast_to_optional_float(tpr_on_all_frames)
        self.result.measured_result = Result(avg_tpr_optional)

        result_df = {
            "Verdict": {"value": result_value.title(), "color": fh.get_color(result_value)},
            fc.REQ_ID: [""],
            fc.TESTCASE_ID: ["98137"],
            fc.TEST_RESULT: [tpr_on_all_frames],
        }
        self.result.details["Additional_results"] = result_df

        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")

        # Generate a custom scene to explain the KPIs
        fig, remark = utils.generate_kpi_scenario()
        graph_summary = utils.build_html_table_graph(
            figure=fig, table_remark=remark, table_title="KPI evaluation for cars - Custom Scenario"
        )
        self.result.details["Plots"].append(graph_summary)
        kpi_description = utils.generate_html_description()
        self.result.details["Plots"].append(kpi_description)


@testcase_definition(
    name="TPF_KPI_TruePositiveRate",
    description="Run the True Positive Rate KPI for TPF. Note: Also compute False Positive Rate, "
    "False Negative Rate, Precision and Recall, but this does not affect the verdict.",
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class KPIRates(TestCase):
    """KPI rates on cars"""  # example of required docstring

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepKPIRates]  # in this list all the needed test steps are included
