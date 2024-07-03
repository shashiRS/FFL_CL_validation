#!/usr/bin/env python3
"""Defining  pmsd FCConfidenceRange testcases"""
import logging
import os

import plotly.graph_objects as go

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
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CV.PMSD.constants import ConstantsPmsd

EXAMPLE = "PMSD_CONFIDENCE"


class PSMD_FCCConfidence(SignalDefinition):
    """MF signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIMESTAMP = "TimeStamp"
        FCNUMPARKINGLINES = "FC_numParkingLines"
        FCLINECONFIDENCE = "FC_lineConfidence"
        RCNUMPARKINGLINES = "RC_numParkingLines"
        RCLINECONFIDENCE = "RC_lineConfidence"
        LSCNUMPARKINGLINES = "LSC_numParkingLines"
        LSCLINECONFIDENCE = "LSC_lineConfidence"
        RSCNUMPARKINGLINES = "RSC_numParkingLines"
        RSCLINECONFIDENCE = "RSC_lineConfidence"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "ADC5xx_Device", "M7board.EM_Thread", "CarPC.EM_Thread"]

        self._properties = {
            self.Columns.TIMESTAMP: ".TimeStamp",
            self.Columns.FCNUMPARKINGLINES: ".PMSD_FC_DATA.PmsdParkingLinesOutputFc.numParkingLines",
            self.Columns.FCLINECONFIDENCE: ".PMSD_FC_DATA.PmsdParkingLinesOutputFc.lineList[%].lineConfidence",
            self.Columns.RCNUMPARKINGLINES: ".PMSD_RC_DATA.PmsdParkingLinesOutputRc.numParkingLines",
            self.Columns.RCLINECONFIDENCE: ".PMSD_RC_DATA.PmsdParkingLinesOutputRc.lineList[%].lineConfidence",
            self.Columns.LSCNUMPARKINGLINES: ".PMSD_LSC_DATA.PmsdParkingLinesOutputLsc.numParkingLines",
            self.Columns.LSCLINECONFIDENCE: ".PMSD_LSC_DATA.PmsdParkingLinesOutputLsc.lineList[%].lineConfidence",
            self.Columns.RSCNUMPARKINGLINES: ".PMSD_RSC_DATA.PmsdParkingLinesOutputRsc.numParkingLines",
            self.Columns.RSCLINECONFIDENCE: ".PMSD_RSC_DATA.PmsdParkingLinesOutputRsc.lineList[%].lineConfidence",
        }


@teststep_definition(
    step_number=1,
    name="PMSD Line Range",
    description="Parking Lines and line Confidence is within the range",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, PSMD_FCCConfidence)
class PmsdLineConfTestStep(TestStep):
    """PMSD Line Confidence Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """Process data and update result details with plot-related information and the file name of the first artifact."""
        _log.debug("Starting processing...")

        reader = self.readers[EXAMPLE].signals

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)
        signal_summary = {}

        FC_ParkingLines = (reader["FC_numParkingLines"] == 0).all()
        RC_ParkingLines = (reader["RC_numParkingLines"] == 0).all()
        LSC_ParkingLines = (reader["LSC_numParkingLines"] == 0).all()
        RSC_ParkingLines = (reader["RSC_numParkingLines"] == 0).all()

        evaluation = ["", "", "", ""]

        fc_confidence_columns = [col for col in reader.columns if "FC_lineConfidence" in col]
        FC_result = False
        if FC_ParkingLines:
            evaluation[0] = "There are no FC Parking lines detected, hence no confidenceline found"
            FC_result = True
        else:
            for key in fc_confidence_columns:
                if all(
                    ele >= ConstantsPmsd.LINE_CONFIDENCE_MIN or ele <= ConstantsPmsd.LINE_CONFIDENCE_MAX
                    for ele in reader[key]
                ):
                    evaluation[0] = "signal FCLineConfidence is PASSED, with values within the range"
                    FC_result = True
                else:
                    evaluation[0] = "FC Line Confidence at frame " + str(key) + " is outside the range 0-1"

        rc_confidence_columns = [col for col in reader.columns if "RC_lineConfidence" in col]
        RC_result = False
        if RC_ParkingLines:
            evaluation[1] = "There are no RC Parking lines detected, hence no confidenceline found"
            RC_result = True
        else:
            for key in rc_confidence_columns:
                if all(
                    ele >= ConstantsPmsd.LINE_CONFIDENCE_MIN or ele <= ConstantsPmsd.LINE_CONFIDENCE_MAX
                    for ele in reader[key]
                ):
                    evaluation[1] = "signal RC LineConfidence is PASSED, with values within the range"
                    RC_result = True
                else:
                    evaluation[1] = "RC Line Confidence at frame " + str(key) + " is outside the range 0-1"

        lsc_confidence_columns = [col for col in reader.columns if "LSC_lineConfidence" in col]
        LSC_result = False
        if LSC_ParkingLines:
            evaluation[2] = "There are no LSC Parking lines detected, hence no confidenceline found"
            LSC_result = True
        else:
            for key in lsc_confidence_columns:
                if all(
                    ele >= ConstantsPmsd.LINE_CONFIDENCE_MIN or ele <= ConstantsPmsd.LINE_CONFIDENCE_MAX
                    for ele in reader[key]
                ):
                    evaluation[2] = "signal LSCLineConfidence is PASSED, with values within the range"
                    LSC_result = True
                else:
                    evaluation[2] = "LSC Line Confidence at frame " + str(key) + " is outside the range 0-1"

        rsc_confidence_columns = [col for col in reader.columns if "RSC_lineConfidence" in col]
        RSC_result = False
        if RSC_ParkingLines:
            evaluation[3] = "There are no RSC Parking lines detected, hence no confidenceline found"
            RSC_result = True
        else:
            for key in rsc_confidence_columns:
                if all(
                    ele >= ConstantsPmsd.LINE_CONFIDENCE_MIN or ele <= ConstantsPmsd.LINE_CONFIDENCE_MAX
                    for ele in reader[key]
                ):
                    evaluation[3] = "signal RSCLineConfidence is PASSED, with values within the range"
                    RSC_result = True
                else:
                    evaluation[3] = "RSC Line Confidence at frame " + str(key) + " is outside the range 0-1"

        cond_bool = [
            FC_result,
            RC_result,
            LSC_result,
            RSC_result,
        ]

        test_result = fc.PASS if all(cond_bool) else fc.FAIL

        signal_summary["FC_LineConfidence"] = evaluation[0]
        signal_summary["RC_LineConfidence"] = evaluation[1]
        signal_summary["LSC_LineConfidence"] = evaluation[2]
        signal_summary["RSC_LineConfidence"] = evaluation[3]

        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Signal Evaluation", "Summary"]),
                    cells=dict(values=[list(signal_summary.keys()), list(signal_summary.values())]),
                )
            ]
        )

        plot_titles.append("Signal Evaluation")
        plots.append(fig)
        remarks.append("PMSD Evaluation")

        # fig = go.Figure()

        # for key in fc_confidence_columns:
        #     fig.add_trace(
        #         go.Scatter(x=list(range(len(reader[key]))), y=list(reader[key]), mode='lines', line=dict(color='darkblue')))
        #     fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Frames",
        #                            yaxis_title="LineConfidence")
        #     fig.update_traces(showlegend=False, line=dict(width=1), selector=dict(type='scatter'))

        # plot_titles.append("Graphical Overview FCLineConfidence ")
        # plots.append(fig)
        # remarks.append("FCLineConfidence")

        # fig = go.Figure()

        # for key in rc_confidence_columns:
        #     fig.add_trace(
        #         go.Scatter(x=list(range(len(reader[key]))), y=list(reader[key]), mode='lines', line=dict(color='darkblue')))
        #     fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Frames",
        #                            yaxis_title="LineConfidence")
        #     fig.update_traces(showlegend=False, line=dict(width=1), selector=dict(type='scatter'))

        # plot_titles.append("Graphical Overview RCLineConfidence ")
        # plots.append(fig)
        # remarks.append("RCLineConfidence")

        # fig = go.Figure()

        # for key in lsc_confidence_columns:
        #     fig.add_trace(
        #         go.Scatter(x=list(range(len(reader[key]))), y=list(reader[key]), mode='lines', line=dict(color='darkblue')))
        #     fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Frames",
        #                            yaxis_title="LineConfidence")
        #     fig.update_traces(showlegend=False, line=dict(width=1), selector=dict(type='scatter'))

        # plot_titles.append("Graphical Overview LSCLineConfidence ")
        # plots.append(fig)
        # remarks.append("LSCLineConfidence")

        # fig = go.Figure()

        # for key in rsc_confidence_columns:
        #     fig.add_trace(
        #         go.Scatter(x=list(range(len(reader[key]))), y=list(reader[key]), mode='lines', line=dict(color='darkblue')))
        #     fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Frames",
        #                            yaxis_title="LineConfidence")
        #     fig.update_traces(showlegend=False, line=dict(width=1), selector=dict(type='scatter'))

        # plot_titles.append("Graphical Overview RSCLineConfidence ")
        # plots.append(fig)
        # remarks.append("RSCLineConfidence")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["Lx_Func_276"],
            fc.TESTCASE_ID: ["L3_SW_PMSD_70"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: ["Parking Lines and line Confidence is within the range"],
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


@verifies("Lx_Func_276")
@testcase_definition(
    name="PMSD LineConf",
    description="",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class PmsdLineConf(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdLineConfTestStep,
        ]
