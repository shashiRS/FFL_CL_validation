#!/usr/bin/env python3
"""
In this ALIAS we would learn how to create the pre-processors and use them in tandem with teststeps.
Pre-processors allow for single reading of data and generate an intermediate dataframe which can be later used with all
the teststeps.
Thus, reducing the amount of open and close operations with each teststep.

TRY IT OUT!
Just run the file.
"""
import logging
import os
import sys
from typing import List

import numpy as np
import pandas as pd
import plotly.graph_objects as go

# import torch
import pl_parking.common_ft_helper as fh

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

import os
import sys

from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.db.results import Result

import pl_parking.common_constants as fc

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

import json

from tsf.core.report import (
    ProcessingResult,
    ProcessingResultsList,
    TeststepResult,
)
from tsf.core.testcase import (
    CustomReportTestStep,
    PreProcessor,
    register_pre_processor,
)

from pl_parking.common_ft_helper import MfCustomTestcaseReport
from pl_parking.PLP.MF.GRAPPA.ft_grappa_helper import ALIASSignals

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "Semseg_kpi"
CLASS_NAME = "Pedestrian"


class MfCustomTeststepReport(CustomReportTestStep):
    """Custom MF test step report class."""

    def overview(
        self,
        processing_details_list: ProcessingResultsList,
        teststep_result: List["TeststepResult"],
    ):
        """Generate an overview of the test step report.

        Args:
            processing_details_list (ProcessingResultsList): List of processing results.
            teststep_result (List[TeststepResult]): List of test step results.

        Returns:
            str: Overview of the test step report.
        """
        s = ""

        # pr_list = processing_details_list
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

    def details(self, processing_details: ProcessingResult, teststep_result: "TeststepResult") -> str:
        """Generate details of the test step report.

        Args:
            processing_details (ProcessingResult): Processing results.
            teststep_result (TeststepResult): Test step result.

        Returns:
            str: Details of the test step report.
        """
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

        s += f'<span align="center" style="width: 100%; height: 100%; display: block;background-color: {fh.get_color(verdict)}; color : #ffffff">Step result: {verdict.upper()}</span>'

        for k, v in processing_details.details.items():
            if "Plots" in k:
                s += "<div>"
                for plot in v:

                    s += plot
                s += "</div>"

        return s


class SemsegPreprocessor(PreProcessor):
    """Preprocessor class to compute all data before the teststeps."""

    def pre_process(self):
        """Function used to do all the calculations."""
        json_grappa_file_path = self.artifacts[0].file_path.source_path
        json_GT_file_path = json_grappa_file_path.replace("predictions", "gt")
        location_path, file_path = os.path.split(json_grappa_file_path)
        CLASS_NAMES = [
            "Background",
            "Ground",
            "Drivable area",
            "Static object",
            "Dynamic object",
            "Parking marker",
            "Curb side",
            "Curb top",
            "Stopline marker",
            "Ped-crossing marker",
            "Candidate house",
        ]

        def load_json(filepath):
            """
            Load JSON data from a file.

            Parameters:
            - filepath: str, the path to the JSON file.

            Returns:
            - data: dictionary, the parsed JSON data.
            """
            with open(filepath) as file:
                data = json.load(file)
            return data

        def load_binary_image(filepath, width, height):
            """
            Load a binary image file and return it as a 2D numpy array.

            Parameters:
            - filepath: str, the relative path to the binary file.
            - width: int, the width of the image.
            - height: int, the height of the image.

            Returns:
            - data: 2D numpy array of the image.
            """
            data = np.fromfile(filepath, dtype=np.uint8, count=width * height).reshape((height, width))
            return data.astype(np.int64)

        def calculate_iou(data1, data2, num_classes=11):
            """
            Calculate the Intersection over Union (IoU) for each class between two images.

            Parameters:
            - data1: 2D numpy array of the first image.
            - data2: 2D numpy array of the second image.
            - num_classes: int, the number of classes.

            Returns:
            - iou_per_class: dictionary with class index as key and IoU as value.
            """
            iou_per_class = {}
            for cls in range(num_classes):
                intersection = np.sum((data1 == cls) & (data2 == cls))
                union = np.sum((data1 == cls) | (data2 == cls))
                if union == 0:
                    iou = float("nan")  # To handle the case where there is no occurrence of a class in either image
                else:
                    iou = intersection / union
                iou_per_class[CLASS_NAMES[cls]] = iou
            return iou_per_class

        def match_and_calculate_iou(json1, json2):
            """
            Match frames by timestamp and calculate IoU for matched frames.

            Parameters:
            - json1: dictionary, first JSON containing prediction metadata.
            - json2: dictionary, second JSON containing ground truth metadata.

            Returns:
            - results: dictionary with timestamps as keys and IoU dictionaries as values.
            """
            width = int(json1["resolution"]["width"])
            height = int(json1["resolution"]["height"])

            # Create dictionaries to map timestamps to binary files
            files1 = {
                frame["timestamp"]: f"{location_path}\\predictions\\{frame['binary_file']}" for frame in json1["frames"]
            }
            files2 = {frame["timestamp"]: f"{location_path}\\gt\\{frame['binary_file']}" for frame in json2["frames"]}

            # Match files based on timestamps
            common_timestamps = set(files1.keys()).intersection(files2.keys())

            results = {}

            for timestamp in common_timestamps:
                data1 = load_binary_image(files1[timestamp], width, height)
                data2 = load_binary_image(files2[timestamp], width, height)
                iou = calculate_iou(data1, data2)
                results[timestamp] = iou

            return results

        def calculate_mean_iou_per_class(iou_results):
            """
            Calculate the mean IoU for each class and the overall mean IoU, ignoring NaN values.

            Parameters:
            - iou_results: dictionary with timestamps as keys and IoU dictionaries as values.

            Returns:
            - mean_iou_per_class: dictionary with class names as keys and mean IoU as values, including an 'Overall Mean IoU'.
            """
            mean_iou_per_class = {}
            overall_ious = []

            for cls in CLASS_NAMES:
                class_ious = []
                for iou in iou_results.values():
                    if cls in iou and not np.isnan(iou[cls]):
                        class_ious.append(iou[cls])

                if class_ious:
                    mean_iou = np.mean(class_ious)
                    mean_iou_per_class[cls] = mean_iou
                    overall_ious.extend(class_ious)
                else:
                    mean_iou_per_class[cls] = np.nan

            if overall_ious:
                mean_iou_per_class["Overall Mean IoU"] = np.mean(overall_ious)
            else:
                mean_iou_per_class["Overall Mean IoU"] = np.nan

            return mean_iou_per_class

        # def export_iou_results(iou_results, mean_iou_per_class):
        #     # Prepare the data for the DataFrame
        #     rows = []
        #     for timestamp, iou in iou_results.items():
        #         for cls, value in iou.items():
        #             rows.append({
        #                 'Timestamp': timestamp,
        #                 'Class': cls,
        #                 'IoU': value if not np.isnan(value) else 0
        #             })

        #     # Create DataFrame
        #     df = pd.DataFrame(rows)

        #     # Create a Plotly figure
        #     fig = go.Figure()

        #     # Add a trace for each class
        #     for cls in CLASS_NAMES:
        #         class_data = df[df['Class'] == cls]
        #         fig.add_trace(go.Scatter(x=class_data['Timestamp'], y=class_data['IoU'], mode='lines', name=cls))

        #     # Update layout
        #     fig.update_layout(
        #         title='IoU Results Over Time',
        #         xaxis_title='Timestamp',
        #         yaxis_title='IoU',
        #         legend_title='Class',
        #         yaxis=dict(range=[0, 1])  # Assuming IoU ranges from 0 to 1
        #     )

        #     return fig

        def export_iou_results(iou_results):
            figs = []
            for cls in CLASS_NAMES:
                # Prepare the data for the histogram for the current class
                iou_values = []
                for timestamp in iou_results:
                    if cls in iou_results[timestamp]:
                        value = iou_results[timestamp][cls]
                        if not np.isnan(value):
                            iou_values.append(value)

                # Check if there are non-NaN values for the current class
                if iou_values:
                    # Create a histogram for the current class
                    fig = go.Figure(data=[go.Histogram(x=iou_values, xbins=dict(start=0, end=1, size=0.05))])

                    # Update layout for the current class
                    fig.update_layout(
                        title=f"IoU Distribution for {cls}",
                        xaxis_title="IoU",
                        yaxis_title="Number of Occurrences",
                        xaxis=dict(
                            tickmode="linear",  # Set ticks in linear mode
                            dtick=0.1,  # Set the distance between ticks
                            range=[0, 1],  # Set the range of x-axis
                        ),
                        yaxis=dict(type="linear"),  # Set y-axis type as linear
                        bargap=0.05,  # Set the gap between bars
                        margin=dict(l=20, r=20, t=40, b=20),  # Set the margin
                    )

                    figs.append(fig)

            return figs

        def export_iou_results_to_dict(iou_results):
            """
            Export IoU results to a dictionary.

            Parameters:
            - iou_results: dictionary with timestamps as keys and IoU dictionaries as values.

            Returns:
            - results: dictionary with 'IoU Results' and 'Mean IoU per Class' keys.
            """
            # Flatten IoU results for creating a DataFrame
            rows = []
            for timestamp, iou in iou_results.items():
                for cls, value in iou.items():
                    rows.append({"Timestamp": timestamp, "Class": cls, "IoU": value})

            # Create DataFrame
            df = pd.DataFrame(rows)

            # Replace NaN with 0 for the graph
            df["IoU"].fillna(0, inplace=True)

            # Calculate mean IoU per class
            mean_iou_per_class = calculate_mean_iou_per_class(iou_results)

            results = {
                # 'IoU Results': iou_results,
                "Mean IoU per Class": mean_iou_per_class
            }

            return results

        # Load JSON files
        data_semseg = load_json(json_grappa_file_path)
        data_gt = load_json(json_GT_file_path)

        # Calculate IoU results
        iou_results = match_and_calculate_iou(data_semseg, data_gt)

        # Calculate and print the mean IoU per class
        calculate_mean_iou_per_class(iou_results)

        plot = export_iou_results(iou_results)

        table_sig_sum = export_iou_results_to_dict(iou_results)

        return iou_results, table_sig_sum, plot


@teststep_definition(
    step_number=1,
    name="Semseg mean IoU",  # this would be shown as a test step name in html report
    description=("Check that mean IoU of set does not exceed the threshold."),
    expected_result=">= 0.5",  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(alias=ALIAS, definition=ALIASSignals)
@register_pre_processor(alias="some_activation", pre_processor=SemsegPreprocessor)
class TestStepKpiSemseg(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
    """

    custom_report = MfCustomTeststepReport  # Specific overview

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        signal_summary = {}
        self.test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.details.update(
            {
                "Plots": [],
                "Plot_titles": [],
                "Remarks": [],
                "file_name": os.path.basename(self.artifacts[0].file_path.source_path),
            }
        )

        (iou_results, table_sig_sum, plot) = self.pre_processors["some_activation"]

        def build_html_table(dataframe: pd.DataFrame, table_remark="", table_title=""):
            """Constructs an HTML table from a DataFrame along with optional table remarks and title."""
            # Initialize the HTML string with line break and title
            html_string = "<br>"
            html_string += "<h4>" + table_title + "</h4>"

            dataframe.loc[dataframe["Class name"] == "Overall Mean IoU"] = dataframe.loc[
                dataframe["Class name"] == "Overall Mean IoU"
            ].applymap(lambda x: f"<b>{x}</b>")

            # Convert DataFrame to HTML table
            table_html = dataframe.to_html(classes="table table-hover ", index=False, escape=False)

            # Apply styling to the table headers and rows
            table_html = table_html.replace("<th>", '<th style ="background-color: #FFA500">')
            table_html = table_html.replace('<tr style="text-align: right;">', '<tr style="text-align: center;">')
            table_html = table_html.replace("<tr>", '<tr style="text-align: center;">')

            # Add table remark with styling
            table_remark = "<h6>" + table_remark + "</h6>"

            # Wrap the table and remark in a div
            table_html = "<div>" + table_html + "<br>" + table_remark + "</div>"

            # Append the table HTML to the overall HTML string
            html_string += table_html

            return html_string

        def convert_dict_to_pandas_semseg(signal_summary: dict, table_remark="", table_title=""):
            evaluation_summary = pd.DataFrame(
                {
                    "Class name": {key: key for key, val in signal_summary.items()},
                    "IoU": {key: val for key, val in signal_summary.items()},
                }
            )
            return build_html_table(
                evaluation_summary,
                table_remark,
                table_title,
            )

        self.result.measured_result = Result(table_sig_sum["Mean IoU per Class"]["Overall Mean IoU"])
        remark = " ".join(
            "This table presents the mean Intersection over Union (IoU) for each class. \
                       If the value is 0, it indicates that the class was detected, but the IoU was not computed. \
                       If the value is NaN, it suggests that the class was not found in the entire dataset.".split()
        )
        signal_summary = table_sig_sum["Mean IoU per Class"]
        self.sig_sum = convert_dict_to_pandas_semseg(signal_summary, remark)
        plots.append(self.sig_sum)
        # remarks.append("This table presents the mean Intersection over Union (IoU) for each class. \
        #                If the value is 0, it indicates that the class was detected, but the IoU was not computed. \
        #                If the value is NaN, it suggests that the class was not found in the entire dataset.")
        for _idx, fig in enumerate(plot):
            # fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            # fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            # # self.result.details["Plots"].append(
            # #     self.fig.to_html(full_html=False, include_plotlyjs=False))
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)

        additional_results_dict = {
            "Verdict": {"Overall Mean IoU": table_sig_sum["Mean IoU per Class"]["Overall Mean IoU"]},
        }
        self.result.details["Additional_results"] = additional_results_dict


# Define the test case definition. This will include the name of the test case and a description of the test.
@testcase_definition(
    name="Semseg KPI",
    description=("This KPI compares a set of binary semsegs with ground truth (gt) against a predictions set."),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class TestExample(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepKpiSemseg]  # in this list all the needed test steps are included
