#!/usr/bin/env python3
"""KPI for park in success rate"""

import logging
import os
import sys
from typing import List

import pandas as pd
import plotly.graph_objects as go
from tsf.core.common import AggregateFunction, RelationOperator
from tsf.core.report import (
    ProcessingResult,
    ProcessingResultsList,
)
from tsf.core.results import NAN, ExpectedResult, Result
from tsf.core.testcase import (
    CustomReportTestStep,
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.db.results import Result, TeststepResult  # noqa: F811
from tsf.io.signals import SignalDefinition

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants

__author__ = "Pinzariu, George-Claudiu (uif94738)"
__copyright__ = "2024-2012, Continental AG"
__version__ = "1.0"
__status__ = "Development"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ALIAS = "Parking_Success_Rate"


class CustomTeststepReport(CustomReportTestStep):
    """Custom ntest step report class"""

    def overview(
        self,
        processing_details_list: ProcessingResultsList,
        teststep_result: List["TeststepResult"],
    ):
        """This function customize the overview page in report."""
        s = ""

        file_counter = 0

        self.result_list = []
        pr_list = processing_details_list

        for file in range(len(pr_list)):
            json_entries = ProcessingResult.from_json(pr_list.processing_result_files[file])

            if json_entries["Additional_results"] != "-":
                file_counter += 1

                a = {"Measurement": json_entries["file_name"]}
                a.update(json_entries["Additional_results"])
                self.result_list.append(a)

        s += "<br>"
        s += "<br>"
        try:
            from json import dumps

            columns = []
            row_events = []
            for r in self.result_list:
                columns.extend(list(r.keys()))
                break

            for d in self.result_list:
                r = []
                for c in columns:
                    if c in d:
                        v = d[c]
                        if isinstance(v, dict):
                            if "color" in v:
                                r.append(
                                    str(
                                        f"""<span align="center" style="width: 100%; height: 100%; display: block;background-color: {v['color']}; color : #ffffff">{v['value']}</span>"""
                                    )
                                )
                            else:
                                r.append(
                                    str(
                                        f"""<span align="center" style="width: 100%; height: 100%; display: block">{v['value']}</span>"""
                                    )
                                )
                        elif "Measurement" in c:
                            r.append(
                                str(
                                    f"""<span align="center" style="background-color: {d['Verdict']['color']}; color : #ffffff">{v}</span>"""
                                )
                            )
                        else:
                            r.append(v)

                    else:
                        r.append("")
                row_events.append(r)

            column_names = [{"title": str(c)} for c in columns]
            additional_tables = (
                """
        <h2>Additional Information</h2>
<script>
var table_column_names = """
                + dumps(column_names)
                + """;
var table_rows_events =  """
                + dumps(row_events)
                + """
$(document).ready(function() {
$('#events_table').DataTable( {
paging:    true,
searching: true,
info:      true,
scrollX: true,
ordering: true,
data: table_rows_events,
columns: table_column_names
} );
});
</script>
<table class="table-sm table-striped compact nowrap" id="events_table">
</table>
"""
            )
            s += additional_tables

        except Exception:
            s += "<h6>No additional info available</h6>"
        return s

    def details(self, processing_details: ProcessingResult, teststep_result: "TeststepResult") -> str:
        """This function customize the details page in report."""
        s = "<br>"
        m_res = teststep_result.measured_result
        e_res = teststep_result.teststep_definition.expected_results[None]
        (
            _,
            status,
        ) = e_res.compute_result_status(m_res)
        verdict = status.key.lower()

        if "data nok" in verdict:
            verdict = fc.NOT_ASSESSED
        s += (
            '<span align="center" style="width: 100%; height: 100%; display: block;background-color:'
            f' {fh.get_color(verdict)}; color : #ffffff">Step result: {verdict.upper()}</span>'
        )
        for k, v in processing_details.details.items():
            if "Plots" in k:
                s += "<div>"
                for plot in v:
                    s += plot
                s += "</div>"

        return s


class TestSignals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIMESTAMP = "mts_ts"
        PPC_PARKING_MODE = "PPC_PARKING_MODE"
        PPC_STATE_VAR_MODE = "STATE_VAR_MODE"
        PARKING_SCENARIO = "PARKING_SCENARIO"
        CORE_STOP_REASON = "CORE_STOP_REASON"
        Slotcoordinates_x = "Slotcoordinates_{}_{}_x"
        Slotcoordinates_y = "Slotcoordinates_{}_{}_y"
        SLOTCOORDINATES = "SLOTCOORDINATES"
        IS_ADC5X = "IS_ADC5X"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["ADC5xx_Device", "MTA_ADC5"]

        self._properties = {
            self.Columns.PPC_PARKING_MODE: [
                ".EM_DATA.EmCtrlCommandPort.ppcParkingMode_nu",
                "MTA_ADC5.APPDEMO_PARKSM_DATA.ctrlCommandPort.ppcParkingMode_nu",
            ],
            self.Columns.PARKING_SCENARIO: [
                "ADC5xx_Device.EM_DATA.EmApParkingBoxPort.parkingBoxes[0].parkingScenario_nu",
                "MTA_ADC5.SI_DATA.m_parkingBoxesPort.parkingBoxes[0].parkingScenario_nu",
            ],
            self.Columns.CORE_STOP_REASON: [
                "ADC5xx_Device.EM_DATA.EmPARRKSMCoreStatusPort.coreStopReason_nu",
                "MTA_ADC5.MF_PARKSM_CORE_DATA.parksmCoreStatusPort.coreStopReason_nu",
            ],
            self.Columns.PPC_STATE_VAR_MODE: [
                ".EM_DATA.EmPSMDebugPort.stateVarPPC_nu",
                "MTA_ADC5.APPDEMO_PARKSM_DATA.psmDebugPort.stateVarPPC_nu",
            ],
        }


def fetch_verdict(verdict):
    """Function return a string accordingly to verdict."""
    if verdict:
        return "PASSED"
    else:
        return "FAILED"


class BaseStep(TestStep):
    """Teststep that contains all generic functions that can be used by other test steps"""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        plot_titles, plots, remarks = fh.rep([], 3)
        self.test_result = fc.NOT_ASSESSED
        evaluation_conditions = [False] * 4
        # Read measurement

        df = self.readers[ALIAS]  # for rrec
        df[TestSignals.Columns.TIMESTAMP] = df.index

        df[TestSignals.Columns.TIMESTAMP] -= df[TestSignals.Columns.TIMESTAMP].iat[0]
        df[TestSignals.Columns.TIMESTAMP] /= constants.GeneralConstants.US_IN_S
        ppc_parking_mode = df[TestSignals.Columns.PPC_PARKING_MODE]

        state_var = df[TestSignals.Columns.PPC_STATE_VAR_MODE]
        parking_in_mask = ppc_parking_mode == constants.ParkingModes.PARK_IN
        parking_mode = df[TestSignals.Columns.CORE_STOP_REASON]
        parking_success_mask = parking_mode == constants.CoreStopStatus.PARKING_SUCCESS
        perform_parking = state_var == constants.ParkingMachineStates.PPC_PERFORM_PARKING
        perform_park_in_mask = parking_in_mask & perform_parking

        if any(perform_park_in_mask):
            self.number_of_attempts = 1
            if any(parking_success_mask):
                self.test_result = fc.PASS
                self.result.measured_result = Result(100, unit="%")
                signal_summary = pd.DataFrame(
                    {
                        "Result": {
                            "1": "Successfull parking",
                        },
                    }
                )

                sig_sum = fh.build_html_table(signal_summary)
                fig = go.Figure()
                plot_titles.append("")
                plots.append(sig_sum)
                remarks.append("")
            else:

                self.test_result = fc.FAIL
                self.result.measured_result = Result(0, unit="%")

                if any(state_var == constants.ParkingMachineStates.PPC_PARKING_CANCELED):
                    signal_summary = pd.DataFrame(
                        {
                            "Result": {
                                "1": "Maneuver canceled by the driver",
                            },
                        }
                    )
                else:
                    evaluation_conditions[3] = False
                    if any(parking_in_mask):
                        evaluation_conditions[0] = True
                    if any(perform_parking):
                        evaluation_conditions[1] = True
                    if any(perform_park_in_mask):
                        evaluation_conditions[2] = True

                    signal_summary = pd.DataFrame(
                        {
                            "Evaluation": {
                                "1": f"Signal {signals_obj.Columns.PPC_PARKING_MODE} should be in mode PARK IN ({constants.ParkingModes.PARK_IN})",
                                "2": f"Signal {signals_obj.Columns.PPC_STATE_VAR_MODE} should be in state PPC PERFORM PARKING ({constants.ParkingMachineStates.PPC_PERFORM_PARKING})",
                                "3": "Above conditions should be fulfilled at the same time",
                                "4": f"Signal {signals_obj.Columns.CORE_STOP_REASON} should be set to PARKING SUCCESS ({constants.CoreStopStatus.PARKING_SUCCESS})",
                            },
                            "Result": {
                                "1": f"{fetch_verdict(evaluation_conditions[0])}",
                                "2": f"{fetch_verdict(evaluation_conditions[1])}",
                                "3": f"{fetch_verdict(evaluation_conditions[2])}",
                                "4": f"{fetch_verdict(evaluation_conditions[3])}",
                            },
                        }
                    )

                sig_sum = fh.build_html_table(signal_summary)

                plot_titles.append("")
                plots.append(sig_sum)
                remarks.append("")
        if self.test_result == fc.FAIL:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df[TestSignals.Columns.TIMESTAMP].values.tolist(),
                    y=df[TestSignals.Columns.PPC_STATE_VAR_MODE].values.tolist(),
                    mode="lines",
                    name=TestSignals.Columns.PPC_STATE_VAR_MODE,
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df[TestSignals.Columns.TIMESTAMP].values.tolist(),
                    y=df[TestSignals.Columns.CORE_STOP_REASON].values.tolist(),
                    mode="lines",
                    name=TestSignals.Columns.CORE_STOP_REASON,
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df[TestSignals.Columns.TIMESTAMP].values.tolist(),
                    y=df[TestSignals.Columns.PPC_PARKING_MODE].values.tolist(),
                    mode="lines",
                    name=TestSignals.Columns.PPC_PARKING_MODE,
                )
            )

            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            plot_titles.append("Graphical Overview")
            plots.append(fig)
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


signals_obj = TestSignals()


@teststep_definition(
    step_number=1,
    name="PAR",
    description="Parallel scenario.",
    expected_result=ExpectedResult(
        95,
        unit="%",
        operator=RelationOperator.GREATER_OR_EQUAL,
        aggregate_function=AggregateFunction.AT_LEAST_95_PERCENT,
    ),
)
@register_signals(ALIAS, TestSignals)
class Step1(BaseStep):
    """Test step class"""

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:
            self.result.details.update(
                {
                    "Plots": [],
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.test_result = fc.NOT_ASSESSED
            usecases = {
                key: val
                for key, val in constants.ParkingUseCases.parking_usecase_id.items()
                if val.lower().startswith("parallel")
            }
            if any(element in self.result.details["file_name"] for element in list(usecases.keys())):
                super().process()
                additional_results_dict = {
                    "Verdict": {"value": self.test_result.title(), "color": fh.get_color(self.test_result)}
                }
                self.result.details["Additional_results"] = additional_results_dict
            else:
                self.result.measured_result = NAN
                self.test_result = fc.NOT_ASSESSED

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=2,
    name="PERP/ANG FWD",
    description="Perpendicular and angular forwards scenario.",
    expected_result=ExpectedResult(
        95,
        unit="%",
        operator=RelationOperator.GREATER_OR_EQUAL,
        aggregate_function=AggregateFunction.AT_LEAST_95_PERCENT,
    ),
)
@register_signals(ALIAS, TestSignals)
class Step2(BaseStep):
    """Test step class"""

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:

            self.result.details.update(
                {
                    "Plots": [],
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.test_result = fc.NOT_ASSESSED
            parking_types = ["forwards angular", "forwards perpendicular"]
            usecases = {}
            for test in parking_types:
                usecases.update(
                    {
                        key: val
                        for key, val in constants.ParkingUseCases.parking_usecase_id.items()
                        if val.lower().startswith(test)
                    }
                )
            if any(element in self.result.details["file_name"] for element in list(usecases.keys())):
                super().process()
                additional_results_dict = {
                    "Verdict": {"value": self.test_result.title(), "color": fh.get_color(self.test_result)},
                }
                self.result.details["Additional_results"] = additional_results_dict
            else:
                self.result.measured_result = NAN
                self.test_result = fc.NOT_ASSESSED

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=3,
    name="PERP/ANG BKWD",
    description="Perpendicular and angular backwards scenario.",
    expected_result=ExpectedResult(
        95,
        unit="%",
        operator=RelationOperator.GREATER_OR_EQUAL,
        aggregate_function=AggregateFunction.AT_LEAST_95_PERCENT,
    ),
)
@register_signals(ALIAS, TestSignals)
class Step3(BaseStep):
    """Test step class"""

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:

            self.result.details.update(
                {
                    "Plots": [],
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.test_result = fc.NOT_ASSESSED
            parking_types = ["backwards angular", "backwards perpendicular"]
            usecases = {}
            for test in parking_types:
                usecases.update(
                    {
                        key: val
                        for key, val in constants.ParkingUseCases.parking_usecase_id.items()
                        if val.lower().startswith(test)
                    }
                )
            if any(element in self.result.details["file_name"] for element in list(usecases.keys())):
                super().process()
                additional_results_dict = {
                    "Verdict": {"value": self.test_result.title(), "color": fh.get_color(self.test_result)},
                }
                self.result.details["Additional_results"] = additional_results_dict
            else:
                self.result.measured_result = NAN
                self.test_result = fc.NOT_ASSESSED

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("966658")
@testcase_definition(
    name="Park in success rate",
    description="The park in success rate considers the number of successfully finished AP park in maneuvers in relation to the overall number of the initiated AP park in maneuvers for a particular scenario(parallel, perpendicular/angular fowards and perpendicular/angular backwards). The park in success rate is given in percents",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FMD_rKDgEclZEe2iKqc0KPO99Q&artifactInModule=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_PfA1C8lcEe2iKqc0KPO99Q&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_lWHOEPvsEeqIqKySVwTVNQ%2Fcomponents%2F_u4eQYMlKEe2iKqc0KPO99Q&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class ParkinSuccessKPI(TestCase):
    """Test case class"""

    # custom_report = MfCustomTestcaseReport
    @property
    def test_steps(self):
        """Define the test steps."""
        return [Step1, Step2, Step3]
