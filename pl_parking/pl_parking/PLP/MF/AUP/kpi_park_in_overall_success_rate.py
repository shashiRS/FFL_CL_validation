#!/usr/bin/env python3
"""KPI for park in overall success rate."""
import logging
import os
import sys
from typing import List

import pandas as pd
import plotly.graph_objects as go
from tsf.core.report import (
    ProcessingResult,
    ProcessingResultsList,
)
from tsf.core.results import NAN, Result
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
from tsf.db.results import TeststepResult
from tsf.io.signals import SignalDefinition

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.PLP.MF.constants import ParkInEndSuccessRate as Threshold

__author__ = "Pinzariu, George-Claudiu (uif94738)"
__copyright__ = "2024-2012, Continental AG"
__version__ = "1.0"
__status__ = "Development"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ALIAS = "Park_in_Overall_Success_Rate"


class CustomTeststepReport(CustomReportTestStep):
    """Custom test report."""

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
            # try:
            if json_entries["Additional_results"] != "-":
                file_counter += 1

                a = {"Measurement": json_entries["file_name"]}
                a.update(json_entries["Additional_results"])
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

    def details(self, processing_details: ProcessingResult, teststep_result: "TeststepResult") -> str:
        """This function customize the details page in report."""
        s = ""
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
        GEAR = "GearReqFusion"
        LONG_ERROR = "LONG_ERROR"
        LAT_ERROR = "LAT_ERROR"
        HEAD_SCREEN = "SELECTED_PB"
        ORIENTATION_ERROR = "ORIENTATION_ERROR"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["ADC5xx_Device", "MTA_ADC5"]

        self._properties = {
            self.Columns.PPC_PARKING_MODE: [
                ".EM_DATA.EmCtrlCommandPort.ppcParkingMode_nu",
                "MTA_ADC5.APPDEMO_PARKSM_DATA.ctrlCommandPort.ppcParkingMode_nu",
            ],
            self.Columns.CORE_STOP_REASON: [
                "ADC5xx_Device.EM_DATA.EmPARRKSMCoreStatusPort.coreStopReason_nu",
                "MTA_ADC5.MF_PARKSM_CORE_DATA.parksmCoreStatusPort.coreStopReason_nu",
            ],
            self.Columns.PARKING_SCENARIO: [
                "ADC5xx_Device.EM_DATA.EmApParkingBoxPort.parkingBoxes[0].parkingScenario_nu",
                "MTA_ADC5.SI_DATA.m_parkingBoxesPort.parkingBoxes[0].parkingScenario_nu",
            ],
            self.Columns.PPC_STATE_VAR_MODE: [
                ".EM_DATA.EmPSMDebugPort.stateVarPPC_nu",
                "MTA_ADC5.APPDEMO_PARKSM_DATA.psmDebugPort.stateVarPPC_nu",
            ],
            self.Columns.GEAR: [
                "ADC5xx_Device.VD_DATA.IuGearboxCtrlRequestPort.gearReq_nu",
                "MTA_ADC5.MF_TRJCTL_DATA.GearboxCtrlRequestPort.gearReq_nu",
            ],
            self.Columns.LONG_ERROR: [
                ".TRJPLA_DATA.TrjPlaTAPOSDDebugPort.longDistToTarget_m",
                "MTA_ADC5.MF_TRJPLA_DATA.taposdDebugPort.longDistToTarget_m",
            ],
            self.Columns.LAT_ERROR: [
                ".VD_DATA.IuTrajCtrlDebugPort.currentDeviation_m",
                "MTA_ADC5.MF_TRJCTL_DATA.TrajCtrlDebugPort.currentDeviation_m",
            ],
            self.Columns.ORIENTATION_ERROR: [
                ".VD_DATA.IuTrajCtrlDebugPort.orientationError_rad",
                "MTA_ADC5.MF_TRJCTL_DATA.TrajCtrlDebugPort.orientationError_rad",
            ],
            self.Columns.HEAD_SCREEN: [
                ".EM_DATA.EmHeadUnitVisualizationPort.screen_nu",
                "MTA_ADC5.IU_PAR230_DATA.HeadUnitVisualizationPort.screen_nu",
            ],
        }


class BaseStep(TestStep):
    """Teststep that contains all generic functions that can be used by other test steps"""

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
        condition_list = [False] * 5
        last_index = 0
        lat_error_m = 0
        long_error_m = 0
        orr_error_rad = 0

        # Read measurement

        df = self.readers[ALIAS]  # for rrec
        df[TestSignals.Columns.TIMESTAMP] = df.index

        df[TestSignals.Columns.TIMESTAMP] -= df[TestSignals.Columns.TIMESTAMP].iat[0]
        df[TestSignals.Columns.TIMESTAMP] /= constants.GeneralConstants.US_IN_S
        ppc_parking_mode = df[TestSignals.Columns.PPC_PARKING_MODE]
        state_var = df[TestSignals.Columns.PPC_STATE_VAR_MODE]
        lateral_error = df[TestSignals.Columns.LAT_ERROR]
        longitudinal_error = df[TestSignals.Columns.LONG_ERROR]
        orientation_error = df[TestSignals.Columns.ORIENTATION_ERROR]
        parking_in_mask = ppc_parking_mode == constants.ParkingModes.PARK_IN
        parking_mode = df[TestSignals.Columns.CORE_STOP_REASON]
        parking_success_mask = parking_mode == constants.CoreStopStatus.PARKING_SUCCESS
        perform_parking = state_var == constants.ParkingMachineStates.PPC_PERFORM_PARKING
        perform_park_in_mask = parking_in_mask & perform_parking

        headscreen_nu = df[TestSignals.Columns.HEAD_SCREEN]

        # Get the number of seconds that have passed from frame to frame
        seconds = df[TestSignals.Columns.TIMESTAMP].rolling(2).apply(lambda x: x[1] - x[0], raw=True)

        msk_prk_selection = headscreen_nu == constants.HeadUnitVisuPortScreenVal.PARKING_SPACE_SELECTION
        msk_maneuver_active = headscreen_nu == constants.HeadUnitVisuPortScreenVal.MANEUVER_ACTIVE
        msk_maneuver_fnsh = headscreen_nu == constants.HeadUnitVisuPortScreenVal.MANEUVER_FINISHED

        headscreen_nu_mask = msk_prk_selection | msk_maneuver_active | msk_maneuver_fnsh.shift(1).fillna(False)

        headscreen_nu_filtered = pd.concat([seconds, headscreen_nu], axis=1)

        headscreen_nu_filtered = headscreen_nu_filtered[headscreen_nu_mask]
        seconds_while_parking = headscreen_nu_filtered[TestSignals.Columns.TIMESTAMP].sum()

        valid_gear_req = df[TestSignals.Columns.GEAR]

        if any(perform_park_in_mask):
            """Check if there was any parking performed"""

            if any(parking_success_mask):
                """Check lat/long/orr error, avg strokes and maneuver time"""
                last_index = parking_success_mask.index[-1]
                lat_error_m = lateral_error.loc[last_index]
                long_error_m = longitudinal_error.loc[last_index]
                orr_error_rad = orientation_error.loc[last_index]

                usable_data = valid_gear_req[valid_gear_req.diff() != 0]
                strokes = [
                    i
                    for i in usable_data.values
                    if i == constants.GearReqConstants.GEAR_D or i == constants.GearReqConstants.GEAR_R
                ]
                total_number_of_strokes = len(strokes)
                if Threshold.Par.LAT_ERROR[0] <= lat_error_m <= Threshold.Par.LAT_ERROR[1]:
                    condition_list[0] = True
                if Threshold.Par.LONG_ERROR[0] <= long_error_m <= Threshold.Par.LONG_ERROR[1]:
                    condition_list[1] = True
                if Threshold.Par.ORIENTATION_ERROR[0] <= orr_error_rad <= Threshold.Par.ORIENTATION_ERROR[1]:
                    condition_list[2] = True
                if total_number_of_strokes <= Threshold.Par.NB_STROKES:
                    condition_list[3] = True
                if seconds_while_parking <= Threshold.Par.TIME:
                    condition_list[4] = True

                if all(condition_list):
                    self.test_result = fc.PASS
                    self.result.measured_result = Result(100)
                else:
                    self.test_result = fc.FAIL
                    self.result.measured_result = Result(0)

                signal_summary = pd.DataFrame(
                    {
                        "Evaluation": {
                            "1": f"Signal {signals_obj.Columns.LAT_ERROR} should be &plusmn; {Threshold.Par.LAT_ERROR[1]} m",
                            "2": f"Signal {signals_obj.Columns.LONG_ERROR} should be &plusmn; {Threshold.Par.LONG_ERROR[1]} m",
                            "3": f"Signal {signals_obj.Columns.ORIENTATION_ERROR} should be &plusmn; {Threshold.Par.ORIENTATION_ERROR[1]} &deg;",
                            "4": f"Parking should be finished in &le; {Threshold.Par.NB_STROKES} strokes",
                            "5": f"Signal {signals_obj.Columns.HEAD_SCREEN} should be Active ({constants.HeadUnitVisuPortScreenVal.MANEUVER_ACTIVE}) &le; {Threshold.Par.TIME} seconds",
                        },
                        "Result": {
                            "1": f"Lateral error found {lat_error_m} m",
                            "2": f"Longitudinal error found {long_error_m} m",
                            "3": f"Orientation error found {orr_error_rad} &deg;",
                            "4": f"Total number of strokes: {total_number_of_strokes}",
                            "5": f"Total number of seconds it took the car to park: {seconds_while_parking:.2f}",
                        },
                        "Verdict": {
                            "1": f"{fetch_verdict(condition_list[0])}",
                            "2": f"{fetch_verdict(condition_list[1])}",
                            "3": f"{fetch_verdict(condition_list[2])}",
                            "4": f"{fetch_verdict(condition_list[3])}",
                            "5": f"{fetch_verdict(condition_list[4])}",
                        },
                    }
                )

                sig_sum = fh.build_html_table(signal_summary)
                fig = go.Figure()
                plot_titles.append("")
                plots.append(sig_sum)
                remarks.append("")
            else:
                self.result.measured_result = Result(0)
                self.test_result = fc.FAIL
                signal_summary = pd.DataFrame(
                    {
                        "Evaluation": {
                            "1": f"Signal {signals_obj.Columns.LAT_ERROR} should be &plusmn; {Threshold.Par.LAT_ERROR[1]} m",
                            "2": f"Signal {signals_obj.Columns.LONG_ERROR} should be &plusmn; {Threshold.Par.LONG_ERROR[1]} m",
                            "3": f"Signal {signals_obj.Columns.ORIENTATION_ERROR} should be &plusmn; {Threshold.Par.ORIENTATION_ERROR[1]} &deg;",
                            "4": f"Parking should be finished in &le; {Threshold.Par.NB_STROKES} strokes",
                            "5": f"Signal {signals_obj.Columns.HEAD_SCREEN} should be Active ({constants.HeadUnitVisuPortScreenVal.MANEUVER_ACTIVE}) &le; {Threshold.Par.TIME} seconds",
                        },
                        "Result": {
                            "1": "Evaluation not possible, car did not park",
                            "2": "Evaluation not possible, car did not park",
                            "3": "Evaluation not possible, car did not park",
                            "4": "Evaluation not possible, car did not park",
                            "5": "Evaluation not possible, car did not park",
                        },
                        "Verdict": {
                            "1": f"{fetch_verdict(condition_list[0])}",
                            "2": f"{fetch_verdict(condition_list[1])}",
                            "3": f"{fetch_verdict(condition_list[2])}",
                            "4": f"{fetch_verdict(condition_list[3])}",
                            "5": f"{fetch_verdict(condition_list[4])}",
                        },
                    }
                )

                sig_sum = fh.build_html_table(signal_summary)
                fig = go.Figure()
                plot_titles.append("")
                plots.append(sig_sum)
                remarks.append("")
        else:
            self.result.measured_result = NAN
            self.test_result = fc.NOT_ASSESSED
        if self.test_result in [fc.NOT_ASSESSED, fc.FAIL]:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df[TestSignals.Columns.TIMESTAMP].values.tolist(),
                    y=df[TestSignals.Columns.PARKING_SCENARIO].values.tolist(),
                    mode="lines",
                    name=TestSignals.Columns.PARKING_SCENARIO,
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df[TestSignals.Columns.TIMESTAMP].values.tolist(),
                    y=df[TestSignals.Columns.HEAD_SCREEN].values.tolist(),
                    mode="lines",
                    name=TestSignals.Columns.HEAD_SCREEN,
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
                    y=df[TestSignals.Columns.PPC_STATE_VAR_MODE].values.tolist(),
                    mode="lines",
                    name=TestSignals.Columns.PPC_STATE_VAR_MODE,
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


def fetch_verdict(verdict):
    """Method to fetch verdict"""
    if verdict:
        return "PASSED"
    else:
        return "FAILED"


signals_obj = TestSignals()


@teststep_definition(step_number=1, name="PAR", description="Parallel scenario.", expected_result="> 85 %")
@register_signals(ALIAS, TestSignals)
class Step1(BaseStep):
    """Test step class"""

    custom_report = CustomTeststepReport

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
                """Check if measurement fits the TestStep usecase"""
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
    step_number=2, name="PERP/ANG", description="Perpendicular and angular scenario.", expected_result="> 85 %"
)
@register_signals(ALIAS, TestSignals)
class Step2(BaseStep):
    """Test step class"""

    custom_report = CustomTeststepReport

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
            parking_types = [
                "forwards angular",
                "forwards perpendicular",
                "backwards angular",
                "backwards perpendicular",
            ]
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
                """Check if measurement fits the TestStep usecase"""
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


@verifies("1028835")
@testcase_definition(
    name="Park in overall success rate",
    description="The parking in overall success rate performance indicator considers the number of successfully finished park in maneuvers by the AP function - where both parking in maneuvering and end position performance indicators have fulfilled the criteria - in relation to the total number of repetitions",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_zX-WIOhNEe2m7JKTm3pqog&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_lWHOEPvsEeqIqKySVwTVNQ%2Fcomponents%2F_u4eQYMlKEe2iKqc0KPO99Q",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class ParkinOverallSuccessKPI(TestCase):
    """Test case class"""

    # custom_report = MfCustomTestcaseReport
    @property
    def test_steps(self):
        """Define the test steps."""
        return [Step1, Step2]
