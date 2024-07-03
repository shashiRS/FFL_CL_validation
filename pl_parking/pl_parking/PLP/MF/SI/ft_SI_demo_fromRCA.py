#!/usr/bin/env python3
"""SI demo functional test for CAEdge"""
import logging
import os
import sys

import plotly.graph_objects as go

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
from time import time as start_time

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
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport

__author__ = "BA ADAS ENP SIMU KPI"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

EXAMPLE = "ROOT_CAUSE_SI"
now_time = start_time()


class StoreStepResults:
    """Initializes variables for multiple steps and provides a method
    to check their status and return corresponding results and color codes.
    """

    def __init__(self):
        """Initialize object attributes."""
        self.step_1 = fc.INPUT_MISSING
        self.step_2 = fc.INPUT_MISSING
        self.step_3 = fc.INPUT_MISSING
        self.step_4 = fc.INPUT_MISSING
        self.step_5 = fc.INPUT_MISSING
        self.step_6 = fc.INPUT_MISSING
        self.step_7 = fc.INPUT_MISSING
        self.step_8 = fc.INPUT_MISSING

    def check_result(self):
        """
        The function `check_result` checks the status of multiple steps and returns a corresponding result and color code.
        :return: The `check_result` method is returning a tuple with two values. The first value is one of the constants
        `fc.PASS`, `fc.INPUT_MISSING`, `fc.NOT_ASSESSED`, or `fc.FAIL` based on the conditions checked in the method. The
        second value is a color code represented as a string.
        """
        if (
            self.step_1 == fc.PASS
            and self.step_2 == fc.PASS
            and self.step_3 == fc.PASS
            and self.step_4 == fc.PASS
            and self.step_5 == fc.PASS
            and self.step_6 == fc.PASS
            and self.step_7 == fc.PASS
            and self.step_8 == fc.PASS
        ):
            return fc.PASS, "#28a745"
        elif (
            self.step_1 == fc.INPUT_MISSING
            or self.step_2 == fc.INPUT_MISSING
            or self.step_3 == fc.INPUT_MISSING
            or self.step_4 == fc.INPUT_MISSING
            or self.step_5 == fc.INPUT_MISSING
            or self.step_6 == fc.INPUT_MISSING
            or self.step_7 == fc.INPUT_MISSING
            or self.step_8 == fc.INPUT_MISSING
        ):
            return fc.INPUT_MISSING, "rgb(33,39,43)"
        elif (
            self.step_1 == fc.NOT_ASSESSED
            or self.step_2 == fc.NOT_ASSESSED
            or self.step_3 == fc.NOT_ASSESSED
            or self.step_4 == fc.NOT_ASSESSED
            or self.step_5 == fc.NOT_ASSESSED
            or self.step_6 == fc.NOT_ASSESSED
            or self.step_7 == fc.NOT_ASSESSED
            or self.step_8 == fc.NOT_ASSESSED
        ):
            return fc.NOT_ASSESSED, "rgb(129, 133, 137)"
        else:
            # self.case_result == fc.FAIL
            return fc.FAIL, "#dc3545"


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        NUMBER_OF_PARKMARK = "NumberOfParkingMarks"
        NUMBER_OF_PARKMARK_VFB = "NumberOfParkingMarks_resim"
        NUMBER_OF_STATOBJ = "NumberOfStaticObjects"
        NUMBER_OF_STATOBJ_VFB = "NumberOfStaticObjects_resim"
        NUMBER_OF_VALID_PB = "NumberOfValidPB"
        NUMBER_OF_VALID_PB_VFB = "NumberOfValidPB_resim"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["ADC5xx_Device", "ADAS_CAN", "SIM VFB"]

        self._properties = {
            self.Columns.NUMBER_OF_PARKMARK: ".EM_DATA.EmApEnvModelPort.numberOfParkMarkings_u8",
            self.Columns.NUMBER_OF_PARKMARK_VFB: ".SiCoreGeneric.m_environmentModelPort.numberOfParkMarkings_u8",
            self.Columns.NUMBER_OF_STATOBJ: ".EM_DATA.EmApEnvModelPort.numberOfStaticObjects_u8",
            self.Columns.NUMBER_OF_STATOBJ_VFB: ".SiCoreGeneric.m_environmentModelPort.numberOfStaticObjects_u8",
            self.Columns.NUMBER_OF_VALID_PB: ".EM_DATA.EmApParkingBoxPort.numValidParkingBoxes_nu",
            self.Columns.NUMBER_OF_VALID_PB_VFB: ".SiCoreGeneric.m_parkingBoxesPort.numValidParkingBoxes_nu",
        }


signals_obj = Signals()
verdict_obj = StoreStepResults()


@teststep_definition(
    step_number=1,
    name="SI",
    description="Verify that number of parking markings, of static objects and of valid parking boxes has values greater than 0 until a slot is selected by the driver.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class SI_STEP(TestStep):
    """Test step class"""

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize test step"""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_5 = fc.NOT_ASSESSED

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}

            try:
                df = self.readers[EXAMPLE].signals
                df[Signals.Columns.TIMESTAMP] = df.index  # for bsig
            except Exception:
                df = self.readers[EXAMPLE]  # for rrec
                df[Signals.Columns.TIMESTAMP] = df.index

            # Converting microseconds to seconds
            df[Signals.Columns.TIMESTAMP] = df[Signals.Columns.TIMESTAMP] / constants.GeneralConstants.US_IN_S
            # Converting epoch time to seconds passed
            df[Signals.Columns.TIMESTAMP] = df[Signals.Columns.TIMESTAMP] - df[Signals.Columns.TIMESTAMP].iat[0]
            global time
            time = df[Signals.Columns.TIMESTAMP]

            num_of_parkmark = df[Signals.Columns.NUMBER_OF_PARKMARK]
            num_of_statobj = df[Signals.Columns.NUMBER_OF_STATOBJ]
            num_of_validpb = df[Signals.Columns.NUMBER_OF_VALID_PB]
            num_of_parkmark_vfb = df[Signals.Columns.NUMBER_OF_PARKMARK_VFB]
            num_of_statobj_vfb = df[Signals.Columns.NUMBER_OF_STATOBJ_VFB]
            num_of_validpb_vfb = df[Signals.Columns.NUMBER_OF_VALID_PB_VFB]

            evaluation1 = " ".join(
                f"The evaluation of {signals_obj._properties[Signals.Columns.NUMBER_OF_PARKMARK_VFB]} is PASSED with valid values"
                f" >= 0.".split()
            )

            evaluation2 = " ".join(
                f"The evaluation of {signals_obj._properties[Signals.Columns.NUMBER_OF_STATOBJ_VFB]} is PASSED with valid values"
                f" >= 0.".split()
            )

            evaluation3 = " ".join(
                f"The evaluation of {signals_obj._properties[Signals.Columns.NUMBER_OF_VALID_PB_VFB]} is PASSED with valid values"
                f" >= 0.".split()
            )

            for idx, val in enumerate(df[Signals.Columns.NUMBER_OF_VALID_PB_VFB]):
                if val is not None:
                    t2 = idx
                    break
            if t2 is not None:
                eval_cond = [True] * 3

                for idx in range(t2, len(df[Signals.Columns.NUMBER_OF_VALID_PB])):
                    if df[Signals.Columns.NUMBER_OF_PARKMARK_VFB].iloc[idx] < 0 and eval_cond[0]:
                        evaluation1 = " ".join(
                            f"The evaluation of {signals_obj._properties[Signals.Columns.NUMBER_OF_PARKMARK]} is FAILED because is  "
                            f" < 0 at timestamp {round(time.iloc[idx],3)}.".split()
                        )
                        eval_cond[0] = False

                    if df[Signals.Columns.NUMBER_OF_STATOBJ_VFB].iloc[idx] < 0 and eval_cond[1]:
                        evaluation2 = " ".join(
                            f"The evaluation of {signals_obj._properties[Signals.Columns.NUMBER_OF_STATOBJ]} is FAILED because is"
                            f" < 0 at timestamp {round(time.iloc[idx],3)}.".split()
                        )

                        eval_cond[1] = False

                    if df[Signals.Columns.NUMBER_OF_VALID_PB_VFB].iloc[idx] < 0 and eval_cond[2]:
                        evaluation3 = " ".join(
                            f"The evaluation of {signals_obj._properties[Signals.Columns.NUMBER_OF_VALID_PB]} is FAILED because is "
                            f" < 0 at timestamp {round(time.iloc[idx],3)}.".split()
                        )
                        eval_cond[2] = False
                    if all(eval_cond):
                        self.result.measured_result = TRUE
                        verdict_obj.step_5 = fc.PASS
                        self.result.details["root_cause_text"] = "passed"
                    else:
                        self.result.measured_result = FALSE
                        verdict_obj.step_5 = fc.FAIL
                        self.result.details["root_cause_text"] = "failed"
            else:
                evaluation1 = evaluation2 = evaluation3 = "Trigger not found!"
                self.result.measured_result = DATA_NOK
                verdict_obj.step_5 = fc.NOT_ASSESSED
                self.result.details["root_cause_text"] = "not assessed"

            signal_summary["Number of parking markings"] = evaluation1
            signal_summary["Number of static objects"] = evaluation2
            signal_summary["Number of valid parking boxes"] = evaluation3
            self.sig_sum = fh.convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")

            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(
                    x=time,
                    y=num_of_parkmark,
                    mode="lines",
                    name=Signals.Columns.NUMBER_OF_PARKMARK,
                    visible="legendonly",
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=time, y=num_of_statobj, mode="lines", name=Signals.Columns.NUMBER_OF_STATOBJ, visible="legendonly"
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=time,
                    y=num_of_validpb,
                    mode="lines",
                    name=Signals.Columns.NUMBER_OF_VALID_PB,
                    visible="legendonly",
                )
            )
            self.fig.add_trace(
                go.Scatter(x=time, y=num_of_parkmark_vfb, mode="lines", name=Signals.Columns.NUMBER_OF_PARKMARK_VFB)
            )
            self.fig.add_trace(
                go.Scatter(x=time, y=num_of_statobj_vfb, mode="lines", name=Signals.Columns.NUMBER_OF_STATOBJ_VFB)
            )
            self.fig.add_trace(
                go.Scatter(x=time, y=num_of_validpb_vfb, mode="lines", name=Signals.Columns.NUMBER_OF_VALID_PB_VFB)
            )

            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("req-001")
@testcase_definition(
    name="SI Root Cause Analysis(demo CAEdge)",
    description="Verify the output checks of components for SI(demo CAEdge).",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class SIdemo(TestCase):
    # custom_report = CustomTestcaseReport
    """SI Demo test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test step."""
        return [
            SI_STEP,
        ]
