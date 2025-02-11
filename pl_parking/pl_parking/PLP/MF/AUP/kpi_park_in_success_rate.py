#!/usr/bin/env python3
"""Success of park in manuever KPI"""
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
    TeststepResult,
)
from tsf.core.results import DATA_NOK, NAN, ExpectedResult, Result
from tsf.core.testcase import (
    CustomReportTestStep,
    PreProcessor,
    TestCase,
    TestStep,
    register_inputs,
    register_pre_processor,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh  # nopep8
import pl_parking.PLP.MF.constants as constants

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))  # nopep8
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "Grubii Otilia"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

EXAMPLE = "VEHICLE_FINISH"


class MfCustomTeststepReport(CustomReportTestStep):
    """This is a custom test step report."""

    def overview(
        self,
        processing_details_list: ProcessingResultsList,
        teststep_result: List["TeststepResult"],
    ):
        """This is function which modify the overview page in report."""
        s = ""
        file_counter = 0
        self.result_list = []

        pr_list = processing_details_list

        for file in range(len(pr_list)):
            json_entries = ProcessingResult.from_json(pr_list.processing_result_files[file])
            # try:
            if json_entries["Additional_results_ts"] != "-":
                file_counter += 1

                a = {"Measurement": json_entries["file_name"]}
                a.update(json_entries["Additional_results_ts"])
                self.result_list.append(a)
            # except:
            #     pass
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

        return s

    def details(self, processing_details: ProcessingResult, teststep_result: "TeststepResult") -> str:
        """This function modify the details page from report."""
        s = "<br>"
        # color = ''
        # m_res = teststep_result.measured_result
        # e_res = teststep_result.teststep_definition.expected_results[None]
        # (_, status,) = e_res.compute_result_status(m_res)
        # verdict = status.key.lower()

        # if "data nok" in verdict:
        #     verdict = fc.NOT_ASSESSED

        # s += f'<span align="center" style="width: 100%; height: 100%; display: block;background-color: {fh.get_color(verdict)}; color : #ffffff">Step result: {verdict.upper()}</span>'

        for k, v in processing_details.details.items():
            if "Plots" in k:
                s += "<div>"
                for plot in v:

                    s += plot
                s += "</div>"

        return s


class StoreStepResults:
    """Initializes variables for multiple steps and provides a method
    to check their status and return corresponding results and color codes.
    """

    def __init__(self):
        """Initialize the test steps results"""
        self.step_1 = fc.INPUT_MISSING
        self.step_2 = fc.INPUT_MISSING
        self.step_3 = fc.INPUT_MISSING
        self.park_verdict_1 = "Unknown"
        self.park_verdict_2 = "Unknown"
        self.park_verdict_3 = "Unknown"

    def check_result(self):
        """
        The function `check_result` checks the status of multiple steps and returns a corresponding result and color code.
        :return: The `check_result` method is returning a tuple with two values. The first value is one of the constants
        `fc.PASS`, `fc.INPUT_MISSING`, `fc.NOT_ASSESSED`, or `fc.FAIL` based on the conditions checked in the method. The
        second value is a color code represented as a string.
        """
        if self.step_1 == fc.PASS or self.step_2 == fc.PASS or self.step_3 == fc.PASS:
            return fc.PASS, "#28a745"
        elif self.step_1 == fc.NOT_ASSESSED and self.step_2 == fc.NOT_ASSESSED and self.step_3 == fc.NOT_ASSESSED:
            return fc.NOT_ASSESSED, "rgb(129, 133, 137)"
        else:
            # self.case_result == fc.FAIL
            return fc.FAIL, "#dc3545"

    def check_parking_success(self):
        """
        The function `check_result` checks the status of multiple steps and returns a corresponding result and color code.
        :return: The `check_result` method is returning a tuple with two values. The first value is one of the constants
        `fc.PASS`, `fc.INPUT_MISSING`, `fc.NOT_ASSESSED`, or `fc.FAIL` based on the conditions checked in the method. The
        second value is a color code represented as a string.
        """
        if self.park_verdict_1 == "Success" or self.park_verdict_2 == "Success" or self.park_verdict_3 == "Success":
            return "Success"
        elif self.park_verdict_1 == "Unknown" and self.park_verdict_2 == "Unknown" and self.park_verdict_3 == "Unknown":
            return "Unknown"
        else:
            return "Failed"


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


signal_obj = TestSignals()
verdict_obj = StoreStepResults()


def fetch_verdict(verdict):
    """Function return a string accordingly to verdict."""
    if verdict:
        return "PASSED"
    else:
        return "FAILED"


class ParkInEndPreProcessor(PreProcessor):
    """Preprocessor class for park end position."""

    def pre_process(self):
        """Preprocesses the data before further processing."""
        df = self.readers[EXAMPLE]
        df[TestSignals.Columns.TIMESTAMP] = df.index
        df[TestSignals.Columns.TIMESTAMP] -= df[TestSignals.Columns.TIMESTAMP].iat[0]
        df[TestSignals.Columns.TIMESTAMP] /= constants.GeneralConstants.US_IN_S
        time = df[TestSignals.Columns.TIMESTAMP]
        plot_titles, plots, remarks = fh.rep([], 3)
        signal_summary = {}

        file_path = os.path.abspath(self.artifacts[0].file_path)
        parking_type = fh.get_parking_type_from_file_path(file_path)
        parking_type = parking_type.lower()
        ppc_parking_mode = df[TestSignals.Columns.PPC_PARKING_MODE]

        state_var = df[TestSignals.Columns.PPC_STATE_VAR_MODE]
        parking_in_mask = ppc_parking_mode == constants.ParkingModes.PARK_IN
        parking_mode = df[TestSignals.Columns.CORE_STOP_REASON]
        parking_success_mask = parking_mode == constants.CoreStopStatus.PARKING_SUCCESS
        perform_parking = state_var == constants.ParkingMachineStates.PPC_PERFORM_PARKING
        perform_park_in_mask = parking_in_mask & perform_parking
        evaluation_conditions = [False] * 4

        if any(perform_park_in_mask):
            self.number_of_attempts = 1
            if any(parking_success_mask):
                self.test_result = fc.PASS
                meas_result = 100
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
                meas_result = 0

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
                                "1": f"Signal {TestSignals.Columns.PPC_PARKING_MODE} should be in mode PARK IN ({constants.ParkingModes.PARK_IN})",
                                "2": f"Signal {TestSignals.Columns.PPC_STATE_VAR_MODE} should be in state PPC PERFORM PARKING ({constants.ParkingMachineStates.PPC_PERFORM_PARKING})",
                                "3": "Above conditions should be fulfilled at the same time",
                                "4": f"Signal {TestSignals.Columns.CORE_STOP_REASON} should be set to PARKING SUCCESS ({constants.CoreStopStatus.PARKING_SUCCESS})",
                            },
                            "Result": {
                                "1": f"{fetch_verdict(evaluation_conditions[0])}",
                                "2": f"{fetch_verdict(evaluation_conditions[1])}",
                                "3": f"{fetch_verdict(evaluation_conditions[2])}",
                                "4": f"{fetch_verdict(evaluation_conditions[3])}",
                            },
                        }
                    )
        else:
            signal_summary = pd.DataFrame(
                {
                    "Result": {
                        "1": "No parking maneuver detected",
                    },
                }
            )
            meas_result = 0

        sig_sum = fh.build_html_table(signal_summary)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=time,
                y=df[TestSignals.Columns.PPC_STATE_VAR_MODE],
                mode="lines",
                name=TestSignals.Columns.PPC_STATE_VAR_MODE,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=time,
                y=df[TestSignals.Columns.CORE_STOP_REASON],
                mode="lines",
                name=TestSignals.Columns.CORE_STOP_REASON,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=time,
                y=df[TestSignals.Columns.PPC_PARKING_MODE],
                mode="lines",
                name=TestSignals.Columns.PPC_PARKING_MODE,
            )
        )

        fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]")
        fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

        return [sig_sum, fig, meas_result, parking_type]


@teststep_definition(
    step_number=1,
    name="PERP/ANG FORWARD",
    description="Perpendicular and angular forwards scenario.",
    expected_result=ExpectedResult(
        95,
        unit="%",
        operator=RelationOperator.GREATER_OR_EQUAL,
        aggregate_function=AggregateFunction.AT_LEAST_95_PERCENT,
    ),
)
@register_signals(EXAMPLE, TestSignals)
@register_pre_processor(alias="parkin_end", pre_processor=ParkInEndPreProcessor)
class ParkInEndPerpAngF(TestStep):
    """Test step for park in end position."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step."""
        super().__init__()

    def process(self, **kwargs):
        """This function processes signal data to evaluate certain conditions and generates plots and remarks based on the evaluation results."""
        _log.debug("Starting processing...")
        try:
            self.result.details.update(
                {
                    "Plots": [],
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                    "file_path": os.path.abspath(self.artifacts[0].file_path),
                }
            )
            # self.result.measured_result = None

            plot_titles, plots, remarks = fh.rep([], 3)
            self.result.measured_result = DATA_NOK
            verdict_obj.step_2 = fc.NOT_ASSESSED

            sig_sum, fig, meas_res, park_type = self.pre_processors["parkin_end"]

            if park_type == "perpendicular forward" or park_type == "angular forward":

                self.result.measured_result = Result(meas_res, unit="%")
                verdict_obj.step_1 = fc.PASS

            else:
                self.result.measured_result = NAN
                verdict_obj.step_1 = fc.NOT_ASSESSED

            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append(f"Parking type: {park_type}")

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

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=2,
    name="PERP/ANG BACKWARD",
    description="Perpendicular and angular backwards scenario.",
    expected_result=ExpectedResult(
        95,
        unit="%",
        operator=RelationOperator.GREATER_OR_EQUAL,
        aggregate_function=AggregateFunction.AT_LEAST_95_PERCENT,
    ),
)
@register_signals(EXAMPLE, TestSignals)
@register_pre_processor(alias="parkin_end", pre_processor=ParkInEndPreProcessor)
class ParkInEndPerpAngB(TestStep):
    """Test step for park in end position."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step."""
        super().__init__()

    def process(self, **kwargs):
        """This function processes signal data to evaluate certain conditions and generates plots and remarks based on the evaluation results."""
        _log.debug("Starting processing...")
        try:
            self.result.details.update(
                {
                    "Plots": [],
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                    "file_path": os.path.abspath(self.artifacts[0].file_path),
                }
            )
            # self.result.measured_result = None

            plot_titles, plots, remarks = fh.rep([], 3)
            self.result.measured_result = DATA_NOK
            verdict_obj.step_2 = fc.NOT_ASSESSED

            sig_sum, fig, meas_res, park_type = self.pre_processors["parkin_end"]

            if park_type == "perpendicular backward" or park_type == "angular backward":

                self.result.measured_result = Result(meas_res, unit="%")
                verdict_obj.step_2 = fc.PASS

            else:
                self.result.measured_result = NAN
                verdict_obj.step_2 = fc.NOT_ASSESSED

            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append(f"Parking type: {park_type}")

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

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=3,
    name="PAR",
    description="Parallel scenario.",
    expected_result=ExpectedResult(
        95,
        unit="%",
        operator=RelationOperator.GREATER_OR_EQUAL,
        aggregate_function=AggregateFunction.AT_LEAST_95_PERCENT,
    ),
)
@register_signals(EXAMPLE, TestSignals)
@register_pre_processor(alias="parkin_end", pre_processor=ParkInEndPreProcessor)
class ParkInEndPar(TestStep):
    """Test step for park in end position."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step."""
        super().__init__()

    def process(self, **kwargs):
        """This function processes signal data to evaluate certain conditions and generates plots and remarks based on the evaluation results."""
        _log.debug("Starting processing...")
        try:
            self.result.details.update(
                {
                    "Plots": [],
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                    "file_path": os.path.abspath(self.artifacts[0].file_path),
                }
            )
            # self.result.measured_result = None

            plot_titles, plots, remarks = fh.rep([], 3)
            self.result.measured_result = DATA_NOK
            verdict_obj.step_3 = fc.NOT_ASSESSED

            sig_sum, fig, meas_res, park_type = self.pre_processors["parkin_end"]

            if park_type == "parallel":

                self.result.measured_result = Result(meas_res, unit="%")
                verdict_obj.step_3 = fc.PASS

            else:
                self.result.measured_result = NAN
                verdict_obj.step_3 = fc.NOT_ASSESSED

            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append("")

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
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=4,
    name="UNKNOWN",
    description="Unknown parking type.",
    expected_result=ExpectedResult(
        95,
        unit="%",
        operator=RelationOperator.GREATER_OR_EQUAL,
        aggregate_function=AggregateFunction.AT_LEAST_95_PERCENT,
    ),
)
@register_signals(EXAMPLE, TestSignals)
@register_pre_processor(alias="parkin_end", pre_processor=ParkInEndPreProcessor)
class ParkInEndBase(TestStep):
    """Test step for park in end position."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step."""
        super().__init__()

    def process(self, **kwargs):
        """This function processes signal data to evaluate certain conditions and generates plots and remarks based on the evaluation results."""
        _log.debug("Starting processing...")
        try:
            self.result.details.update(
                {
                    "Plots": [],
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                    "file_path": os.path.abspath(self.artifacts[0].file_path),
                }
            )
            # self.result.measured_result = None

            plot_titles, plots, remarks = fh.rep([], 3)
            self.result.measured_result = DATA_NOK
            verdict_obj.step_3 = fc.NOT_ASSESSED

            sig_sum, fig, meas_res, park_type = self.pre_processors["parkin_end"]

            if park_type == "unknown" or park_type == "perpendicular" or park_type == "angular":

                self.result.measured_result = Result(meas_res, unit="%")
                verdict_obj.step_3 = fc.PASS

            else:
                self.result.measured_result = NAN
                verdict_obj.step_3 = fc.NOT_ASSESSED

            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append("")

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
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("966658")
@testcase_definition(
    name="Park in success rate ",
    description="The park in success rate considers the number of successfully finished AP park in maneuvers in relation to the overall number of the initiated AP park in maneuvers for a particular scenario(parallel, perpendicular/angular fowards and perpendicular/angular backwards). The park in success rate is given in percents",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FMD_rKDgEclZEe2iKqc0KPO99Q&artifactInModule=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_PfA1C8lcEe2iKqc0KPO99Q&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_lWHOEPvsEeqIqKySVwTVNQ%2Fcomponents%2F_u4eQYMlKEe2iKqc0KPO99Q&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/parking")
# @register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class ParkinSuccessKPI(TestCase):
    """Test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            ParkInEndBase,
            ParkInEndPerpAngF,
            ParkInEndPerpAngB,
            ParkInEndPar,
        ]
