#!/usr/bin/env python3
"""KPI for LSCA true positive"""

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
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
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
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "Pinzariu, George-Claudiu (uif94738)"
__copyright__ = "2024-2012, Continental AG"
__version__ = "1.0"
__status__ = "Development"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

EXAMPLE = "NUC_LSCA"


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
        driven_time = 0
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
            if "driven_time" in json_entries.details:
                driven_time += json_entries.details["driven_time"]
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
                    "1": f"< {constants.LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{constants.LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[1]):.2f}] cm"
                    ),
                    "3": (
                        f"> {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[1]):.2f} cm"
                    ),
                },
                "2 km/h": {
                    "1": f"< {constants.LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{constants.LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[2]):.2f}] cm"
                    ),
                    "3": (
                        f"> {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[2]):.2f} cm"
                    ),
                },
                "3 km/h": {
                    "1": f"< {constants.LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{constants.LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[3]):.2f}] cm"
                    ),
                    "3": (
                        f"> {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[3]):.2f} cm"
                    ),
                },
                "4 km/h": {
                    "1": f"< {constants.LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{constants.LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[4]):.2f}] cm"
                    ),
                    "3": (
                        f"> {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[4]):.2f} cm"
                    ),
                },
                "5 km/h": {
                    "1": f"< {constants.LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{constants.LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[5]):.2f}] cm"
                    ),
                    "3": (
                        f"> {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[5]):.2f} cm"
                    ),
                },
                "6 km/h": {
                    "1": f"< {constants.LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{constants.LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[6]):.2f}] cm"
                    ),
                    "3": (
                        f"> {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[6]):.2f} cm"
                    ),
                },
                "7 km/h": {
                    "1": f"< {constants.LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{constants.LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[7]):.2f}] cm"
                    ),
                    "3": (
                        f"> {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[7]):.2f} cm"
                    ),
                },
                "8 km/h": {
                    "1": f"< {constants.LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{constants.LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[8]):.2f}] cm"
                    ),
                    "3": (
                        f"> {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[8]):.2f} cm"
                    ),
                },
                "9 km/h": {
                    "1": f"< {constants.LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{constants.LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[9]):.2f}] cm"
                    ),
                    "3": (
                        f"> {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[9]):.2f} cm"
                    ),
                },
                "10 km/h": {
                    "1": f"< {constants.LscaConstants.SAFETY_MARGIN_CRASH} cm",
                    "2": (
                        f"[{constants.LscaConstants.SAFETY_MARGIN_CRASH} ,"
                        f" {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[10]):.2f}] cm"
                    ),
                    "3": (
                        f"> {(constants.LscaConstants.SAFETY_MARGIN_STATIC + constants.LscaConstants.DISTANCE_TO_OBJ[10]):.2f} cm"
                    ),
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
        """
        Pentru semnale:
        ACTIVATE_BRAKE_INTERV <-> LSCA.staticBraking.EbaActive
        VELOCITY <-> Vhcl.v
        MINIMUM_DISTANCE <-> AP.shortestDistanceToHighObject_m (de investigat si ce se scrie in AP.pdwProcToLogicPort.minimalDistance_m)
        DRIVEN_DISTANCE <-> Nu cred ca are un echivalent - se poate calcula folosing Vhcl.sRoad intre 2 triger-e (e.g. intre LSCA.staticBraking.EbaActive == 1 si Vhcl.v < 0.01)
        TIME <-> Time
        """

        ACTIVATE_BRAKE_INTERV = "ActivateBrakeIntervScreen"
        VELOCITY = "Velocity"
        TIME = "Time"
        MINIMUM_DISTANCE = "MINIMUM_DISTANCE"
        MIN_DIST_HIGH_OBJ = "MIN_DIST_HIGH_OBJ"
        VELOCITY_ROAD = "VELOCITY_ROAD"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = [
            (
                self.Columns.ACTIVATE_BRAKE_INTERV,
                [
                    "LSCA.staticBraking.EbaActive",
                ],
            ),
            (
                self.Columns.VELOCITY,
                [
                    "Vhcl.v",
                ],
            ),
            (
                self.Columns.MINIMUM_DISTANCE,
                [
                    "AP.pdwProcToLogicPort.minimalDistance_m",
                ],
            ),
            (
                self.Columns.MIN_DIST_HIGH_OBJ,
                [
                    "AP.shortestDistanceToHighObject_m",
                ],
            ),
            (
                self.Columns.VELOCITY_ROAD,
                [
                    "Vhcl.sRoad",
                ],
            ),
            (
                self.Columns.TIME,
                [
                    "Time",
                ],
            ),
        ]


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="LSCA NUC ",
    description="Check the non-activation of LSCA function.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class LscaNucTestStep(TestStep):
    """Test step class"""

    custom_report = MfCustomTeststepReport

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
                    "driven_time": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            plot_titles, plots, remarks = fh.rep([], 3)
            signal_summary = {}
            # test_result = fc.INPUT_MISSING

            # brake_classification = fc.INPUT_MISSING
            # self.result.measured_result = DATA_NOK
            driven_time = []
            eval_cond = False
            eval_text = ""

            # Read measurement

            df = self.readers[EXAMPLE].signals  # for erg

            driven_distance = []
            velocity = df[Signals.Columns.VELOCITY]
            minimum_distance = (
                df[Signals.Columns.MINIMUM_DISTANCE] * 100
            )  # transforma in cm pentru a verifica cu tresholduri const
            active_lsca = df[Signals.Columns.ACTIVATE_BRAKE_INTERV]
            for idx, val in enumerate(velocity):
                if val > 0:
                    driven_time.append(df[Signals.Columns.TIME].iat[idx])
                    driven_distance.append(df[Signals.Columns.VELOCITY_ROAD].iat[idx])
            driven_time = driven_time[-1] - driven_time[0]

            (active_lsca == 1) & (velocity < 0.01)

            driven_distance -= df[Signals.Columns.VELOCITY_ROAD].iat[0]

            # Get individual brake events from recording
            # Ex: Signal '0001110010110' would mean 3 separate LSCA activations
            # It takes 2 rows at a time and check if first element is != than the second
            mask_brake_events = active_lsca.rolling(2).apply(
                lambda x: x[0] == 0 and x[1] == 1, raw=True
            )  # 1 ar putea fi
            min_dist_crush = minimum_distance <= constants.LscaConstants.SAFETY_MARGIN_CRASH
            timestamp_crush_events = [row for row, val in min_dist_crush.items() if val == 1]

            total_brake_events = mask_brake_events.sum()
            timestamp_brake_events = [row for row, val in mask_brake_events.items() if val == 1]
            velocity *= constants.GeneralConstants.MPS_TO_KMPH  # din cauza ca offsetul din req doors ii kph

            # timestamp_eba_events = [row for row, val in min_dist_eba.items() if val == 1]
            # velocity *= constants.GeneralConstants.MPS_TO_KMPH # din cauza ca offsetul din req doors ii kph
            # abs() is used for negative speeds (backwards driving)
            # .format is used for a better rounding method

            # def velocity_value(vel, active):
            #     return max([vel.iat[i] for i in range(len(vel)) if active.iat[i] == 1]) * constants.GeneralConstants.MPS_TO_KMPH
            # # rounded_vel = velocity_value(velocity, active_lsca)
            # rounded_velocity = abs(int(f"{velocity_value(velocity, active_lsca):.0f}"))
            if not total_brake_events:
                if min(minimum_distance) > constants.LscaConstants.SAFETY_MARGIN_CRASH:
                    test_result = fc.PASS
                    self.result.measured_result = TRUE
                    eval_text = "LSCA component was not activated and no collisions occurred during measurement."
                    eval_cond = "PASSED"
                else:
                    test_result = fc.FAIL
                    self.result.measured_result = FALSE
                    eval_text = " ".join(
                        "LSCA component was not activated but a collisions occurred"
                        f" at timestamp {df[Signals.Columns.TIME].loc[timestamp_crush_events[0]]:.2f} s "
                        f"with velocity {velocity.loc[timestamp_crush_events[0]]:.2f} kph.".split()
                    )
                    eval_cond = "FAILED"
            elif total_brake_events.any():
                test_result = fc.FAIL
                self.result.measured_result = FALSE
                eval_text = f"LSCA component was activated at timestamp {df[Signals.Columns.TIME].loc[timestamp_brake_events[0]]:.2f} s."
                eval_cond = "FAILED"
            else:
                test_result = fc.NOT_ASSESSED
                self.result.measured_result = DATA_NOK
                eval_text = "The measurement does not have LSCA data."
                eval_cond = "NOT ASSESSED"

            # Set table dataframe
            signal_summary = pd.DataFrame(
                {
                    "Evaluation": {
                        "1": eval_cond,
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

            v_sroad = df[Signals.Columns.VELOCITY_ROAD]
            v_sroad -= df[Signals.Columns.VELOCITY_ROAD].iat[0]

            fig.add_trace(
                go.Scatter(
                    x=df[Signals.Columns.TIME].values.tolist(),
                    y=df[Signals.Columns.ACTIVATE_BRAKE_INTERV].values.tolist(),
                    mode="lines",
                    name="LSCA.staticBraking.EbaActive",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df[Signals.Columns.TIME].values.tolist(),
                    y=velocity.values.tolist(),
                    mode="lines",
                    name="Vhcl.v [kph]",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df[Signals.Columns.TIME].values.tolist(),
                    y=minimum_distance.values.tolist(),
                    mode="lines",
                    name="AP.pdwProcToLogicPort.minimalDistance_m [cm]",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df[Signals.Columns.TIME].values.tolist(),
                    y=v_sroad.values.tolist(),
                    mode="lines",
                    name="Vhcl.sRoad",
                )
            )
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plot_titles.append("Graphical Overview")
            plots.append(fig)
            remarks.append("")
            eba_result = "Active" if total_brake_events.any() else "Inactive"
            # driven_km_output = f"{driven_km[-1]:.2f}" if len(driven_km) > 0 else "n/a"

            additional_results_dict = {
                "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                "Max velocity [kph]": {"value": f"{max(velocity):.2f}"},
                "EBA": {"value": f"{eba_result}"},
                "Minimum distance to object [cm]": {"value": f"{min(minimum_distance):.2f}"},
                # "Brake classification": {"value": brake_classification, "color": fh.get_color(test_result_brake)},
                # "Distance to object [cm]": {"value": f"{distance_ego_object:.2f}"},
                # "Velocity before braking [km/h]": {"value": f"{rounded_velocity}"},
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

            # self.result.details[brake_classification] = 1
            # self.result.details["driven_time"] = driven_time
            self.result.details["Additional_results"] = additional_results_dict
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("1561220")
@testcase_definition(
    name="NUC LSCA",
    description="LSCA function shall reach a classification <passed> if no intervention does NOT lead to a collision with a <protected ego part> and the system does not brake.",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class LscaNUC(TestCase):
    """Test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            LscaNucTestStep,
        ]
