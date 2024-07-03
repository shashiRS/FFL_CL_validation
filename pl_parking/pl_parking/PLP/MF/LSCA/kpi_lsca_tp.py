#!/usr/bin/env python3
"""KPI for LSCA true positive"""

import json
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
from tsf.core.results import DATA_NOK, ExpectedResult, Result
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

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.PLP.MF.constants import GeneralConstants, LscaConstants, PlotlyTemplate

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "Pinzariu, George-Claudiu (uif94738)"
__copyright__ = "2024-2012, Continental AG"
__version__ = "1.0"
__status__ = "Development"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

EXAMPLE = "TP_LSCA"


class CustomTeststepReport(CustomReportTestStep):
    """Custom test step report"""

    def overview(
        self,
        processing_details_list: ProcessingResultsList,
        teststep_result: List["TeststepResult"],
    ):
        """Method which customize the overview page in report"""
        s = "<h4>Evaluation is based on following classification:</h4>"
        crash_evnt = 0
        good_evnt = 0
        data_nok_evnt = 0
        far_evnt = 0
        file_counter = 0
        km_driven = 0.0
        druveb_time = 0
        self.result_list = []
        pr_list = processing_details_list

        for file in range(len(pr_list)):
            json_entries = ProcessingResult.from_json(pr_list.processing_result_files[file])
            file_counter += 1
            a = {"Measurement": json_entries["file_name"]}
            a.update(json_entries["Additional_results"])
            self.result_list.append(a)

            if "Km_driven" in json_entries.details:
                km_driven += json_entries.details["Km_driven"]
            if "druveb_time" in json_entries.details:
                druveb_time += json_entries.details["druveb_time"]
            if fc.CRASH in json_entries.details:
                crash_evnt += json_entries.details["crash"]
            if fc.NOT_ASSESSED in json_entries.details:
                data_nok_evnt += json_entries.details[fc.NOT_ASSESSED]
            if fc.GOOD in json_entries.details:
                good_evnt += json_entries.details["good"]
            if fc.FAR in json_entries.details:
                far_evnt += json_entries.details["far"]

        additional_table = pd.DataFrame(
            {
                "Number of measurements": {
                    "1": file_counter,
                },
                "Number of good verdicts": {
                    "1": good_evnt,
                },
                "Number of crash verdicts": {
                    "1": crash_evnt,
                },
                "Number of far verdicts": {
                    "1": far_evnt,
                },
                "Number of not assessed": {
                    "1": data_nok_evnt,
                },
            }
        )

        event_table = pd.DataFrame(
            {
                "Braking classification": {
                    "1": "Crash",
                    "2": "Good",
                    "3": "Far",
                },
                "1 km/h": {
                    "1": f"< {LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[1]):.2f}] cm"
                    ),
                    "3": (f"> {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[1]):.2f} cm"),
                },
                "2 km/h": {
                    "1": f"< {LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[2]):.2f}] cm"
                    ),
                    "3": (f"> {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[2]):.2f} cm"),
                },
                "3 km/h": {
                    "1": f"< {LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[3]):.2f}] cm"
                    ),
                    "3": (f"> {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[3]):.2f} cm"),
                },
                "4 km/h": {
                    "1": f"< {LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[4]):.2f}] cm"
                    ),
                    "3": (f"> {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[4]):.2f} cm"),
                },
                "5 km/h": {
                    "1": f"< {LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[5]):.2f}] cm"
                    ),
                    "3": (f"> {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[5]):.2f} cm"),
                },
                "6 km/h": {
                    "1": f"< {LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[6]):.2f}] cm"
                    ),
                    "3": (f"> {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[6]):.2f} cm"),
                },
                "7 km/h": {
                    "1": f"< {LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[7]):.2f}] cm"
                    ),
                    "3": (f"> {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[7]):.2f} cm"),
                },
                "8 km/h": {
                    "1": f"< {LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[8]):.2f}] cm"
                    ),
                    "3": (f"> {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[8]):.2f} cm"),
                },
                "9 km/h": {
                    "1": f"< {LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[9]):.2f}] cm"
                    ),
                    "3": (f"> {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[9]):.2f} cm"),
                },
                "10 km/h": {
                    "1": f"< {LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[10]):.2f}] cm"
                    ),
                    "3": (f"> {(LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[10]):.2f} cm"),
                },
            }
        )

        s += fh.build_html_table(event_table, table_remark="<h5>Classifications are dependent on vehicle speed</h5>")

        s += "<br>"
        s += "<br>"
        s += "<h4>Evaluation results:</h4>"
        s += fh.build_html_table(additional_table)
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
        """Method to customize the details page in report."""
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


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        ACTIVATE_BRAKE_INTERV = "ActivateBrakeIntervScreen"
        VELOCITY = "Velocity"
        STEERING_ANGLE = "SteeringAngle"
        TIMESTAMP = "mts_ts"
        MINIMUM_DISTANCE = "MINIMUM_DISTANCE"
        DRIVEN_DISTANCE = "DRIVEN_DISTANCE"
        IS_ADC5X = "IS_ADC5X"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = [
            (
                self.Columns.ACTIVATE_BRAKE_INTERV,
                [
                    "SIM VFB.MfLsca1.hmiPort.activateBrakeInterventionScreen_nu",
                    "ADC5xx_Device.EM_DATA.EmLscaHMIPort.activateBrakeInterventionScreen_nu",
                    "MTA_ADC5.MF_LSCA_DATA.hmiPort.activateBrakeInterventionScreen_nu",
                ],
            ),
            (
                self.Columns.VELOCITY,
                [
                    "SIM VFB.SiCoreGeneric.m_egoMotionPort.vel_mps",
                    "ADC5xx_Device.EM_DATA.EmEgoMotionPort.vel_mps",
                    "MTA_ADC5.SI_DATA.m_egoMotionPort.vel_mps",
                ],
            ),
            (
                self.Columns.MINIMUM_DISTANCE,
                [
                    "SIM VFB.PdCp1.procToLogicPort.minimalDistance_m",
                    "ADC5xx_Device.EM_DATA.EmProcToLogicPort.minimalDistance_m",
                    "MTA_ADC5.MF_PDWARNPROC_DATA.procToLogicPort.minimalDistance_m",
                ],
            ),
            (
                self.Columns.DRIVEN_DISTANCE,
                [
                    "SIM VFB.SiCoreGeneric.m_egoMotionPort.drivenDistance_m",
                    "ADC5xx_Device.EM_DATA.EmEgoMotionPort.drivenDistance_m",
                    "MTA_ADC5.SI_DATA.m_egoMotionPort.drivenDistance_m",
                ],
            ),
            (
                self.Columns.TIMESTAMP,
                [
                    "SIM VFB.SiCoreGeneric.m_egoMotionPort.sSigHeader.uiTimeStamp",
                    "ADC5xx_Device.EM_DATA.EmEgoMotionPort.sSigHeader.uiTimeStamp",
                    "MTA_ADC5.SI_DATA.m_egoMotionPort.sSigHeader.uiTimeStamp",
                ],
            ),
            (
                self.Columns.IS_ADC5X,
                ["ADC5xx_Device.EM_DATA.EmEgoMotionPort.uiVersionNumber"],
            ),
        ]


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="TP KPI",
    description="Check TP of LSCA function.",
    expected_result=ExpectedResult(
        operator=RelationOperator.GREATER_OR_EQUAL,
        numerator=95.0,
        unit="%",
        aggregate_function=AggregateFunction.AT_LEAST_95_PERCENT,
    ),
    doors_url=(
        "doors://rbgs854a:40000/?version=2&prodID=0&view=0000001e&urn=urn:telelogic::1-503e822e5ec3651e-O-124-00065411"
    ),
)
@register_signals(EXAMPLE, Signals)
class Step1(TestStep):
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
                    "software_version_file": "",
                    "Km_driven": 0,
                    "druveb_time": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )

            script_root_folder = os.path.abspath(os.path.join(__file__, "..", "gt_lsca_kpi_sample.json"))
            with open(script_root_folder) as read_file:
                gt_data = json.load(read_file)
            plot_titles, plots, remarks = fh.rep([], 3)
            is_adc5xx = 1
            signal_summary = {}
            test_result = fc.INPUT_MISSING
            brake_classification = fc.NOT_ASSESSED
            distance_from_gt = 0
            druven_time = 0
            rounded_velocity = 0
            eval_cond = False
            eval_text = ""
            json_root_key = "SectorBasedDistance"
            json_timestamp_key = "Timestamp"
            distance_from_gt = 255

            json_front_key = "front"
            json_rear_key = "rear"

            # Read measurement
            df = self.readers[EXAMPLE]
            df[Signals.Columns.TIMESTAMP] = df.index

            if signals_obj.Columns.IS_ADC5X not in df.columns:
                is_adc5xx = 0

            df[Signals.Columns.VELOCITY] *= GeneralConstants.MPS_TO_KMPH
            velocity = df[Signals.Columns.VELOCITY]
            df[Signals.Columns.TIMESTAMP] -= df[Signals.Columns.TIMESTAMP].iat[0]
            df[Signals.Columns.TIMESTAMP] /= GeneralConstants.US_IN_S
            # minimum_distance = df[Signals.Columns.MINIMUM_DISTANCE] * 100
            active_lsca = df[Signals.Columns.ACTIVATE_BRAKE_INTERV]
            df[Signals.Columns.DRIVEN_DISTANCE] -= df[Signals.Columns.DRIVEN_DISTANCE].iat[0]
            df[Signals.Columns.DRIVEN_DISTANCE] /= GeneralConstants.M_TO_KM
            distance_recording = df[Signals.Columns.DRIVEN_DISTANCE]
            driven_km = distance_recording[distance_recording > 0]

            # Get individual brake events from recording
            # Ex: Signal '0001110010110' would mean 3 separate LSCA activations
            # It takes 2 rows at a time and check if first element is != than the second
            mask_brake_events = active_lsca.rolling(2).apply(lambda x: x[0] == 0 and x[1] == 1, raw=True)

            total_brake_events = mask_brake_events.sum()
            timestamp_brake_events = [row for row, val in mask_brake_events.items() if val == 1]

            if not total_brake_events:
                brake_classification = fc.NOT_ASSESSED
                eval_text = "LSCA component was not active (signal != 1 throughout the measurement)."
            elif total_brake_events == LscaConstants.MAX_ALLOWED_ACTIVATIONS:
                timestamp_event = timestamp_brake_events[0]

                gt_data_package = [x for x in gt_data[json_root_key] if x[json_timestamp_key] == timestamp_event][0]
                if gt_data_package.get(json_front_key, None):
                    distance_from_gt = gt_data_package[json_front_key][0].get("distanceValue", None)
                elif gt_data_package.get(json_rear_key, None):
                    distance_from_gt = gt_data_package[json_rear_key][0].get("distanceValue", None)
                # abs() is used for negative speeds (backwards driving)
                # .format is used for a better rounding method
                rounded_velocity = abs(int(f"{velocity[timestamp_event]:.0f}"))
                if distance_from_gt < LscaConstants.SAFETY_MARGIN_CRASH:
                    brake_classification = fc.CRASH
                elif (
                    distance_from_gt
                    <= (LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[rounded_velocity])
                    and distance_from_gt >= 1
                ):
                    brake_classification = fc.GOOD
                elif distance_from_gt >= (
                    LscaConstants.SAFETY_MARGIN_STATIC + LscaConstants.DISTANCE_TO_OBJ[rounded_velocity]
                ):
                    brake_classification = fc.FAR

                eval_text = " ".join(
                    f"Braking classification for LSCA is {brake_classification.upper()} with distance to object ="
                    f" {distance_from_gt:.2f} cm and speed {rounded_velocity} km/h, at timestamp"
                    f" {df[Signals.Columns.TIMESTAMP].loc[timestamp_brake_events[0]]:.2f} s.".split()
                )

            elif total_brake_events > LscaConstants.MAX_ALLOWED_ACTIVATIONS:
                brake_classification = fc.NOT_ASSESSED
                eval_text = "LSCA component was activated more than once."

            eval_0 = " ".join(
                f"LSCA intervention should reach the break classification 'GOOD'(signal evaluated \
                    {signals_obj._properties[0][1][is_adc5xx]}).".split()
            )

            # Set table dataframe
            signal_summary = pd.DataFrame(
                {
                    "Evaluation": {
                        "1": eval_0,
                    },
                    "Result": {
                        "1": eval_text,
                    },
                }
            )

            sig_sum = fh.build_html_table(signal_summary)
            fig = go.Figure()
            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append("")

            if brake_classification == fc.GOOD:
                test_result = fc.PASS
                self.result.measured_result = Result(100, unit="%")
                eval_cond = True
            elif brake_classification == fc.CRASH or brake_classification == fc.FAR:
                eval_cond = False
                test_result = fc.FAIL
                self.result.measured_result = Result(0, unit="%")

            else:
                eval_cond = False
                test_result = fc.NOT_ASSESSED
                self.result.measured_result = DATA_NOK
            if eval_cond is False:
                fig.add_trace(
                    go.Scatter(
                        x=df[Signals.Columns.TIMESTAMP].values.tolist(),
                        y=df[Signals.Columns.ACTIVATE_BRAKE_INTERV].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[0][1][is_adc5xx],
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df[Signals.Columns.TIMESTAMP].values.tolist(),
                        y=df[Signals.Columns.VELOCITY].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[1][1][is_adc5xx],
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df[Signals.Columns.TIMESTAMP].values.tolist(),
                        y=df[Signals.Columns.DRIVEN_DISTANCE].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[2][1][is_adc5xx],
                    )
                )

                fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]")
                fig.update_layout(PlotlyTemplate.lgt_tmplt)
                plot_titles.append("Graphical Overview")
                plots.append(fig)
                remarks.append("")

            additional_results_dict = {
                "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                "Driven distance [km]": {"value": f"{driven_km.iat[-1]:.2f}"},
                "Brake classification": {"value": brake_classification, "color": fh.get_color(test_result)},
                "Distance to object [cm]": {"value": f"{distance_from_gt:.2f}"},
                "Velocity before braking [km/h]": {"value": f"{rounded_velocity}"},
            }

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)

            self.result.details[brake_classification] = 1
            self.result.details["druveb_time"] = druven_time
            self.result.details["Additional_results"] = additional_results_dict
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("988206")
@testcase_definition(
    name="TP LSCA",
    description="LSCA function shall reach a classification <passed> if the interventions that would lead to a collision with a protected ego part are in time (not too soon - to big distance, but not too late, so that the defined safety margin is exceeded).",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_WqNP5NHtEe2iKqc0KPO99Q&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_lWHOEPvsEeqIqKySVwTVNQ%2Fcomponents%2F_u4eQYMlKEe2iKqc0KPO99Q&vvc.configuration=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fcm%2Fstream%2F_bMgUkM-3Ee2iKqc0KPO99Q",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class LscaTruePositive(TestCase):
    """Test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            Step1,
        ]
