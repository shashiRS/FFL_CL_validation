#!/usr/bin/env python3
"""Defining  pmsd ConfidenceLevel testcases"""
import logging
import os

import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


import pandas as pd
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
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep

SIGNAL_DATA = "PMSD_List_of_ParkingMarkings"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD Confidence level of detected parking markings",
    description="This teststep checks Confidence level of detected parking markings",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdConfidenceLevelTestStep(TestStep):
    """PMSD Line Confidence Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarsk based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)
        signal_summary = {}

        reader = self.readers[SIGNAL_DATA]

        df = reader.as_plain_df
        df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]

        FC_Conf = df.loc[:, df.columns.str.contains("PMDCamera_Front_parkingLines_lineConfidence")]
        RC_Conf = df.loc[:, df.columns.str.contains("PMDCamera_Rear_parkingLines_lineConfidence")]
        LSC_Conf = df.loc[:, df.columns.str.contains("PMDCamera_Left_parkingLines_lineConfidence")]
        RSC_Conf = df.loc[:, df.columns.str.contains("PMDCamera_Right_parkingLines_lineConfidence")]

        evaluation = ["", "", "", ""]
        if not FC_Conf.empty:
            evaluation[0] = (
                "Front camera confidence level values for each detected parking markings are present in the measurement."
            )
            FC_result = True
        else:
            evaluation[0] = (
                "Front camera confidence level values for each detected parking markings are not present in the measurement."
            )
            FC_result = False

        if not RC_Conf.empty:
            evaluation[1] = (
                "Rear camera confidence level values for each detected parking markings are present in the measurement."
            )
            RC_result = True
        else:
            evaluation[1] = (
                "Rear camera confidence level values for each detected parking markings are not present in the measurement."
            )
            RC_result = False

        if not LSC_Conf.empty:
            evaluation[2] = (
                "Left camera confidence level values for each detected parking markings are present in the measurement."
            )
            LSC_result = True
        else:
            evaluation[2] = (
                "Left camera confidence level values for each detected parking markings are not present in the measurement."
            )
            LSC_result = False

        if not RSC_Conf.empty:
            evaluation[3] = (
                "Right camera confidence level values for each detected parking markings are present in the measurement."
            )
            RSC_result = True
        else:
            evaluation[3] = (
                "Right camera confidence level values for each detected parking markings are not present in the measurement."
            )
            RSC_result = False

        cond_bool = [
            FC_result,
            RC_result,
            LSC_result,
            RSC_result,
        ]

        test_result = fc.PASS if all(cond_bool) else fc.FAIL

        signal_summary = pd.DataFrame(
            {
                "Signal Evaluation": {
                    "1": "PMSD_FC_DATA.ParkingLines.parkingLines[%].confidence",
                    "2": "PMSD_RC_DATA.ParkingLines.parkingLines[%].confidence",
                    "3": "PMSD_LSC_DATA.ParkingLines.parkingLines[%].confidence",
                    "4": "PMSD_RSC_DATA.ParkingLines.parkingLines[%].confidence",
                },
                "Result": {
                    "1": evaluation[0],
                    "2": evaluation[1],
                    "3": evaluation[2],
                    "4": evaluation[3],
                },
                "Verdict": {
                    "1": "PASSED" if FC_result else "FAILED",
                    "2": "PASSED" if RC_result else "FAILED",
                    "3": "PASSED" if LSC_result else "FAILED",
                    "4": "PASSED" if RSC_result else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PMSD Line Confidence")
        self.result.details["Plots"].append(sig_sum)

        plot_list = [FC_Conf, RC_Conf, LSC_Conf, RSC_Conf]

        for val in plot_list:

            plot_data = val.max(axis=0)
            # Initialize empty lists
            index_list = []
            value_list = []
            # Iterate over the Series to separate indices and values
            for index, value in plot_data.items():
                index_list.append(index)
                value_list.append(value)

            # Split each string
            split_list = [string.split("_")[4] for string in index_list]
            # Convert each element to integer
            int_list = list(map(int, split_list))

            xaxis_name = val.keys()[0].split("_")
            x_axis_name = "".join(xaxis_name[1] + xaxis_name[2] + xaxis_name[3])

            #  Plots for all four cameras
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=int_list,
                    y=value_list,
                    mode="lines",
                    line=dict(color="Green", width=3),
                    name="PMSD_FC_DATA.ParkingLines.parkingLines[%].confidence",
                )
            )
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Line Confidence range[0-300]",
                yaxis_title=f"{x_axis_name} max value[float]",
            )
            plot_titles.append("Line Confidence representation")
            plots.append(fig)
            remarks.append("")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1987864"],
            fc.TESTCASE_ID: ["58797"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Verify confidence level values for each detected parking markings are present in the measurement."
            ],
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


@verifies("1987864")
@testcase_definition(
    name="SWRT_CNC_PMSD_ParkingMarkingsConfLevel",
    description="Verify Parking Markings Confidence Level",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_uZcggNsGEe62R7UY0u3jZg&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
@register_inputs("/parking")
# @register_inputs("/parking")
class PmsdConfidenceLevel(TestCase):
    """ConfidenceLevel test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdConfidenceLevelTestStep,
        ]
