#!/usr/bin/env python3
"""KPI for park in end position"""
import json
import logging
import math
import os
import re
import sys
from typing import List

import pandas as pd
import plotly.graph_objects as go
from tsf.core.common import AggregateFunction, PathSpecification, RelationOperator
from tsf.core.report import (
    ProcessingResult,
    ProcessingResultsList,
)
from tsf.core.results import DATA_NOK, NAN, ExpectedResult, Result
from tsf.core.testcase import (
    CustomReportTestStep,
    PreProcessor,
    TestCase,
    TestStep,
    register_inputs,
    register_pre_processor,
    register_side_load,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.db.results import Result, TeststepResult  # noqa: F811
from tsf.io.sideload import JsonSideLoad
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

ALIAS = "Park_in_end_position_Success_Rate_GT"


class CustomTeststepReport(CustomReportTestStep):
    """Custom test step report class"""

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
        LONG_ERROR = "LONG_ERROR"
        LAT_ERROR = "LAT_ERROR"
        ORIENTATION_ERROR = "ORIENTATION_ERROR"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["ADC5xx_Device", "ADAS_CAN", "MTA_ADC5", "AP_Conti_CAN"]

        self._properties = {
            self.Columns.PPC_PARKING_MODE: [
                ".EM_DATA.EmCtrlCommandPort.ppcParkingMode_nu",
                ".APPDEMO_PARKSM_DATA.ctrlCommandPort.ppcParkingMode_nu",
            ],
            self.Columns.CORE_STOP_REASON: [
                ".EM_DATA.EmPARRKSMCoreStatusPort.coreStopReason_nu",
                ".MF_PARKSM_CORE_DATA.parksmCoreStatusPort.coreStopReason_nu",
            ],
            self.Columns.PARKING_SCENARIO: [
                ".EM_DATA.EmApParkingBoxPort.parkingBoxes[0].parkingScenario_nu",
                ".SI_DATA.m_parkingBoxesPort.parkingBoxes[0].parkingScenario_nu",
            ],
            self.Columns.PPC_STATE_VAR_MODE: [
                ".EM_DATA.EmPSMDebugPort.stateVarPPC_nu",
                ".APPDEMO_PARKSM_DATA.psmDebugPort.stateVarPPC_nu",
            ],
            self.Columns.LONG_ERROR: [
                ".TRJPLA_DATA.TrjPlaTAPOSDDebugPort.longDistToTarget_m",
                ".MF_TRJPLA_DATA.taposdDebugPort.longDistToTarget_m",
            ],
            self.Columns.LAT_ERROR: [
                ".VD_DATA.IuTrajCtrlDebugPort.currentDeviation_m",
                ".MF_TRJCTL_DATA.TrajCtrlDebugPort.currentDeviation_m",
            ],
            self.Columns.ORIENTATION_ERROR: [
                ".VD_DATA.IuTrajCtrlDebugPort.orientationError_rad",
                ".MF_TRJCTL_DATA.TrajCtrlDebugPort.orientationError_rad",
            ],
        }


signals_obj = TestSignals()
ALIAS_JSON = "gt_park_ended_output"


@register_signals(ALIAS, TestSignals)

# @register_side_load(alias=ALIAS_JSON,side_load= JsonSideLoad,path_spec= PathSpecification(folder=Path("D:/gt_Pollerman_mring"), sub_folders=["20240617_143031_AP_UC_018_02_1_parked_in"], extension=".json"))
class ParkEndPreprocessor(PreProcessor):
    """Preprocessor for the ParkEnd test step."""

    def pre_process(self):
        """
        Preprocesses the data before further processing.

        Returns:
        - df: pd.DataFrame, the preprocessed data.
        """

        def load_json(filepath):
            """
            Load JSON data from a file.

            Parameters:
            - filepath: str, the path to the JSON file.

            Returns:
            - data: dictionary, the parsed JSON data.
            """
            try:
                with open(filepath) as file:
                    data = json.load(file)
            except FileNotFoundError:
                _log.error("Ground truth file not found.")
                data = "Ground truth file not found."
            return data

        # self.side_load["ALIAS_JSON"]
        df = self.readers[ALIAS]  # for rrec
        eval_cond = []
        df[TestSignals.Columns.TIMESTAMP] = df.index
        df[TestSignals.Columns.TIMESTAMP] -= df[TestSignals.Columns.TIMESTAMP].iat[0]
        df[TestSignals.Columns.TIMESTAMP] /= constants.GeneralConstants.US_IN_S
        time = df[TestSignals.Columns.TIMESTAMP]
        ppc_parking_mode = df[TestSignals.Columns.PPC_PARKING_MODE]
        state_var = df[TestSignals.Columns.PPC_STATE_VAR_MODE]
        parking_in_mask = ppc_parking_mode == constants.ParkingModes.PARK_IN
        parking_mode = df[TestSignals.Columns.CORE_STOP_REASON]
        parking_success_mask = parking_mode == constants.CoreStopStatus.PARKING_SUCCESS
        perform_parking = state_var == constants.ParkingMachineStates.PPC_PERFORM_PARKING
        perform_park_in_mask = parking_in_mask & perform_parking

        lat_error_m = 0
        long_error_m = 0
        orr_error_deg = 0
        Result = 0
        eval_cond = [False] * 3

        file_path = os.path.abspath(self.artifacts[0].file_path)
        current_dir = os.path.dirname(file_path)
        gt_json = os.path.join(current_dir, "gt_park_ended_output.json")

        def get_parking_type_from_file_path(file_path):
            # Define the dictionary mapping use case IDs to parking types
            parking_type_dict = {
                "AP_UC_001": "Parallel",
                "AP_UC_002": "Parallel",
                "AP_UC_011": "Parallel",
                "AP_UC_003": "Parallel",
                "AP_UC_004": "Parallel",
                "AP_UC_005": "Parallel",
                "AP_UC_006": "Parallel",
                "AP_UC_007": "Parallel",
                "AP_UC_008": "Parallel",
                "AP_UC_009": "Parallel",
                "AP_UC_010": "Parallel",
                "AP_UC_012": "Parallel",
                "AP_UC_013": "Parallel",
                "AP_UC_014": "Parallel",
                "AP_UC_015": "Parallel",
                "AP_UC_016": "Parallel",
                "AP_UC_017": "Parallel",
                "AP_UC_018": "Perpendicular",
                "AP_UC_019": "Perpendicular",
                "AP_UC_020": "Perpendicular",
                "AP_UC_021": "Perpendicular",
                "AP_UC_022": "Perpendicular",
                "AP_UC_023": "Perpendicular",
                "AP_UC_059": "Perpendicular",
                "AP_UC_024": "Perpendicular",
                "AP_UC_025": "Perpendicular",
                "AP_UC_026": "Perpendicular",
                "AP_UC_027": "Perpendicular",
                "AP_UC_028": "Perpendicular",
                "AP_UC_029": "Perpendicular",
                "AP_UC_031": "Perpendicular",
                "AP_UC_032": "Perpendicular",
                "AP_UC_033": "Perpendicular",
                "AP_UC_034": "Perpendicular",
                "AP_UC_035": "Perpendicular",
                "AP_UC_036": "Perpendicular",
                "AP_UC_037": "Perpendicular",
                "AP_UC_068": "Perpendicular",
                "AP_UC_069": "Perpendicular",
                "AP_UC_038": "Angular",
                "AP_UC_070": "Angular",
                "AP_UC_039": "Angular",
                "AP_UC_71": "Angular",
                "AP_UC_040": "Angular",
                "AP_UC_041": "Angular",
                "AP_UC_044": "Angular",
                "AP_UC_060": "Angular",
                "AP_UC_061": "Angular",
                "AP_UC_100": "Unknown",
                "AP_UC_101": "Unknown",
                "AP_UC_102": "Unknown",
                "AP_UC_103": "Unknown",
                "AP_UC_104": "Unknown",
                "AP_UC_105": "Unknown",
                "AP_UC_106": "Unknown",
                "AP_UC_045": "Unknown",
                "AP_UC_046": "Unknown",
                "AP_UC_047": "Unknown",
                "AP_UC_048": "Unknown",
                "AP_UC_049": "Unknown",
                "AP_UC_050": "Unknown",
                "AP_UC_051": "Unknown",
                "AP_UC_052": "Unknown",
                "AP_UC_053": "Unknown",
                "AP_UC_054": "Unknown",
                "AP_UC_055": "Unknown",
                "AP_UC_056": "Unknown",
                "AP_UC_057": "Unknown",
                "AP_UC_058": "Unknown",
            }
            # Use a regular expression to find the use case ID in the file path
            match = re.search(r"AP_UC_\d+", file_path)
            if match:
                usecase_id = match.group()
            else:
                return "Unknown"
            # Return the parking type if the use case ID is found in the dictionary, else return "Unknown"
            return parking_type_dict.get(usecase_id, "Unknown")

        parking_type = get_parking_type_from_file_path(file_path)
        if parking_type == "Perpendicular" or "Angular":
            UC = Threshold.PerpAng
        elif parking_type == "Parallel":
            UC = Threshold.Par
        else:
            UC = "Unknown"
        try:
            # Calculate the errors if the ground truth file is found
            gt_data = load_json(gt_json) if os.path.exists(gt_json) else self.side_load[ALIAS_JSON]
            # gt_data = self.side_load[ALIAS_JSON]
            if len(gt_data) > 0:  # Check if the ground truth data is not empty
                if "ParkingEnded" in gt_data:
                    fig = go.Figure()
                    for parking_event in gt_data["ParkingEnded"]:
                        if parking_event["timedObjs"]:  # Check if there are timed objects
                            for timed_obj in parking_event["timedObjs"]:
                                ego_vehicle = timed_obj.get("EgoVehicle", {})
                                slot = timed_obj.get("Slot", {})

                                # Extracting positions
                                ego_vehicle_pos = ego_vehicle.get("position", {})
                                slot_center_point = slot.get("centerPoint", {})

                                # Plotting EgoVehicle position
                                fig.add_trace(
                                    go.Scatter(
                                        x=[ego_vehicle_pos.get("x", "N/A")],
                                        y=[ego_vehicle_pos.get("y", "N/A")],
                                        mode="markers",
                                        marker=dict(size=10, color="blue"),
                                        name="EgoVehicle Position",
                                    )
                                )

                                # Plotting Slot position
                                fig.add_trace(
                                    go.Scatter(
                                        x=[slot_center_point.get("x", "N/A")],
                                        y=[slot_center_point.get("y", "N/A")],
                                        mode="markers",
                                        marker=dict(size=10, color="red"),
                                        name="Slot Position",
                                    )
                                )

                                # Function to calculate end point of orientation vector
                                def calculate_end_point(start_x, start_y, angle_deg, length=0.01):
                                    angle_rad = math.radians(angle_deg)
                                    end_x = start_x + length * math.cos(angle_rad)
                                    end_y = start_y + length * math.sin(angle_rad)
                                    return end_x, end_y

                                # Calculate end points for orientation vectors
                                ego_vehicle_end_x, ego_vehicle_end_y = calculate_end_point(
                                    ego_vehicle_pos.get("x", 0),
                                    ego_vehicle_pos.get("y", 0),
                                    ego_vehicle.get("orientation", {}).get("heading", 0),
                                )
                                slot_end_x, slot_end_y = calculate_end_point(
                                    slot_center_point.get("x", 0),
                                    slot_center_point.get("y", 0),
                                    slot.get("orientationDeg", 0),
                                )
                                # Orientation degrees rounded to 4 digits
                                ego_vehicle_orientation_deg = round(
                                    ego_vehicle.get("orientation", {}).get("heading", 0), 4
                                )
                                slot_orientation_deg = round(slot.get("orientationDeg", 0), 4)

                                # Plotting orientation vectors with numeric information
                                fig.add_trace(
                                    go.Scatter(
                                        x=[ego_vehicle_pos.get("x", "N/A"), ego_vehicle_end_x],
                                        y=[ego_vehicle_pos.get("y", "N/A"), ego_vehicle_end_y],
                                        mode="lines+text",
                                        line=dict(color="blue", width=2),
                                        name="EgoVehicle Orientation",
                                        text=[
                                            None,
                                            f"{ego_vehicle_orientation_deg}°",
                                        ],  # Display orientation degree at the end of the line
                                        textposition="top right",
                                    )
                                )

                                fig.add_trace(
                                    go.Scatter(
                                        x=[slot_center_point.get("x", "N/A"), slot_end_x],
                                        y=[slot_center_point.get("y", "N/A"), slot_end_y],
                                        mode="lines+text",
                                        line=dict(color="red", width=2),
                                        name="Slot Orientation",
                                        text=[
                                            None,
                                            f"{slot_orientation_deg}°",
                                        ],  # Display orientation degree at the end of the line
                                        textposition="top right",
                                    )
                                )

                                fig.update_layout(
                                    title="EgoVehicle and Slot Positions with Orientation",
                                    xaxis_title="X",
                                    yaxis_title="Y",
                                    legend_title="Legend",
                                )
                        else:
                            fig.add_trace(
                                go.Scatter(
                                    x=[0, 0],
                                    y=[0, 0],
                                    mode="markers",
                                    marker=dict(size=10, color="red"),
                                    name="Position",
                                )
                            )
                            fig.update_layout(
                                title="GT Data didn't contain any timed objects",
                                xaxis_title="X",
                                yaxis_title="Y",
                                legend_title="Legend",
                            )
                try:
                    # Extract vehicle and slot information
                    vehicle = gt_data["ParkingEnded"][0]["timedObjs"][0]["EgoVehicle"]
                    slot = gt_data["ParkingEnded"][0]["timedObjs"][0]["Slot"]

                    # Vehicle position and orientation
                    vehicle_x = vehicle["position"]["x"]
                    vehicle_y = vehicle["position"]["y"]
                    vehicle_orientation = vehicle["orientation"]["heading"]

                    # Slot position and orientation
                    slot_x = slot["centerPoint"]["x"]
                    slot_y = slot["centerPoint"]["y"]
                    slot_orientation = slot["orientationDeg"]

                    # Calculate errors
                    lat_error_m = abs(slot_x - vehicle_x)
                    long_error_m = abs(slot_y - vehicle_y)
                    orr_error_deg = abs(slot_orientation - vehicle_orientation)

                    if UC != "Unknown":
                        if UC.LAT_ERROR[0] <= lat_error_m <= UC.LAT_ERROR[1]:
                            eval_cond[0] = True
                        if UC.LONG_ERROR[0] <= long_error_m <= UC.LONG_ERROR[1]:
                            eval_cond[1] = True
                        if UC.ORIENTATION_ERROR[0] <= orr_error_deg <= UC.ORIENTATION_ERROR[1]:
                            eval_cond[2] = True
                            # Plotting errors as lines
                        fig.add_shape(
                            type="line",
                            x0=vehicle_x,
                            y0=vehicle_y,
                            x1=slot_x,
                            y1=vehicle_y,
                            line=dict(color="green", width=2),
                            name="Lat Error",
                        )
                        fig.add_shape(
                            type="line",
                            x0=slot_x,
                            y0=vehicle_y,
                            x1=slot_x,
                            y1=slot_y,
                            line=dict(color="purple", width=2),
                            name="Long Error",
                        )
                        # Calculate rectangle corners based on error thresholds
                        rect_x0 = slot_x + UC.LAT_ERROR[0]
                        rect_x1 = slot_x + UC.LAT_ERROR[1]
                        rect_y0 = slot_y + UC.LONG_ERROR[0]
                        rect_y1 = slot_y + UC.LONG_ERROR[1]

                        # Add rectangle to the plot
                        fig.add_shape(
                            type="rect",
                            x0=rect_x0,
                            y0=rect_y0,
                            x1=rect_x1,
                            y1=rect_y1,
                            line=dict(color="Red"),
                            fillcolor="LightSalmon",
                            opacity=0.5,
                            name="Error thresholds near slot center point.",
                        )
                        # Add annotation
                        fig.add_annotation(
                            x=(rect_x0 + rect_x1) / 2,
                            y=(rect_y0 + rect_y1) / 2,
                            text="Error thresholds near slot center point[m].",
                            showarrow=False,
                            font=dict(size=12, color="black"),
                            # bordercolor="black",
                            # borderwidth=1,
                            # borderpad=4,
                            # opacity=0.5,
                            # bgcolor="white",
                            yshift=-25,  # Adjust the y-shift value to position the text below the shape
                        )

                        # Calculate rectangle corners based on error thresholds
                        rect_x0 = vehicle_x + UC.LAT_ERROR[0]
                        rect_x1 = vehicle_x + UC.LAT_ERROR[1]
                        rect_y0 = vehicle_y + UC.LONG_ERROR[0]
                        rect_y1 = vehicle_y + UC.LONG_ERROR[1]

                    else:
                        eval_cond = [False] * 3
                except (KeyError, IndexError, TypeError):
                    pass

                table_final = fig
        except Exception as e:
            _log.error(f"Error while processing ground truth data: {e}")
            table = pd.DataFrame(
                {
                    "JSON DATA": {
                        "1": "Ground truth file not found.",
                    }
                }
            )
            table_final = fh.build_html_table(table)
            gt_data = "Ground truth file not found."
        # Signal Summary
        if gt_data == "Ground truth file not found.":
            table = pd.DataFrame(
                {
                    "JSON DATA": {
                        "1": "Ground truth file not found.",
                    }
                }
            )
            table_final = fh.build_html_table(table)
            signal_summary = pd.DataFrame(
                {
                    "Evaluation": {
                        "1": "Evaluation not possible, because of invalid ground truth data.",
                    },
                    "Verdict": {
                        "1": "INVALID DATA",
                    },
                }
            )
            Result = 0
        elif UC == "Unknown":
            signal_summary = pd.DataFrame(
                {
                    "Evaluation": {
                        "1": "Evaluation not possible, because of unknown parking type.",
                    },
                    "Verdict": {
                        "1": "UNKNOWN PARKING TYPE",
                    },
                }
            )
            Result = 0
        elif UC != "Unknown":
            if parking_event["timedObjs"]:
                signal_summary = pd.DataFrame(
                    {
                        "Evaluation": {
                            "1": f"The lateral error should be within ({UC.LAT_ERROR[0]} - {UC.LAT_ERROR[1]}) meters.",
                            "2": f"The longitudinal error should be within ({UC.LONG_ERROR[0]} - {UC.LONG_ERROR[1]}) meters.",
                            "3": f"The orientation error should be within ({UC.ORIENTATION_ERROR[0]} - {UC.ORIENTATION_ERROR[1]}) degrees.",
                            "4": f"The {signals_obj.Columns.PPC_STATE_VAR_MODE} signal should reach the PPC_PERFORM_PARKING({constants.ParkingMachineStates.PPC_PERFORM_PARKING}) state.",
                            "5": f"The {signals_obj.Columns.PPC_PARKING_MODE} signal should reach the PARK IN({constants.ParkingModes.PARK_IN}) state.",
                        },
                        "Result": {
                            "1": f"The calculated lateral error is {round(lat_error_m, 5)} meters.",
                            "2": f"The calculated longitudinal error is {round(long_error_m, 5)} meters.",
                            "3": f"The calculated orientation error is {round(orr_error_deg, 5)} degrees.",
                            "4": (
                                "The vehicle started a parking maneuver."
                                if any(perform_park_in_mask)
                                else "The vehicle did not start a parking maneuver."
                            ),
                            "5": (
                                "The vehicle parked in the end position."
                                if any(parking_success_mask)
                                else "The vehicle did not park in the end position."
                            ),
                        },
                        "Verdict": {
                            "1": "PASSED" if eval_cond[0] else "FAILED",
                            "2": "PASSED" if eval_cond[1] else "FAILED",
                            "3": "PASSED" if eval_cond[2] else "FAILED",
                            "4": "PASSED" if any(perform_park_in_mask) else "FAILED",
                            "5": "PASSED" if any(parking_success_mask) else "FAILED",
                        },
                    }
                )
            else:
                signal_summary = pd.DataFrame(
                    {
                        "Evaluation": {
                            "1": "Ground truth data does not contain any coordinates for slot and vehicle positions.",
                        },
                        "Verdict": {
                            "1": "NO TIMED OBJECTS",
                        },
                    }
                )
                Result = 0

            if all(eval_cond):
                Result = 100
            else:
                Result = 0
        sig_sum = fh.build_html_table(signal_summary, f"Parking type: {parking_type};")
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=time,
                y=df[TestSignals.Columns.PARKING_SCENARIO],
                mode="lines",
                name=TestSignals.Columns.PARKING_SCENARIO,
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
                y=df[TestSignals.Columns.PPC_STATE_VAR_MODE],
                mode="lines",
                name=TestSignals.Columns.PPC_STATE_VAR_MODE,
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

        fig.layout = go.Layout(
            yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]", title="Graphical Overview"
        )
        fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

        return [parking_type, sig_sum, fig, Result, table_final]


@teststep_definition(
    step_number=2,
    name="PAR",
    description="This test step calculates the percentage of successfully parked vehicles using the parallel parking scenario.",
    expected_result=ExpectedResult(
        operator=RelationOperator.GREATER,
        numerator=95,
        unit="%",
        aggregate_function=AggregateFunction.MEAN,
    ),
)
@register_signals(ALIAS, TestSignals)
@register_side_load(
    alias=ALIAS_JSON,
    side_load=JsonSideLoad,
    path_spec=PathSpecification(folder=r"s3://par230-prod-data-lake-sim/gt_labels/", extension=".json", s3=True),
)
@register_pre_processor(alias="park_end_gt", pre_processor=ParkEndPreprocessor)
class ParStep(TestStep):
    """Test step that contains generic functions used by other test steps."""

    custom_report = CustomTeststepReport

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
            self.test_result = fc.NOT_ASSESSED
            park_type, sig_sum, fig, Result_in_percent, table = self.pre_processors["park_end_gt"]
            if park_type == "Parallel":
                self.result.measured_result = Result(Result_in_percent, unit="%")
                self.test_result = fc.PASS if Result_in_percent == 100 else fc.FAIL
            else:
                self.result.measured_result = NAN
                self.test_result = fc.NOT_ASSESSED

            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append(f"Parking type: {park_type}")

            plot_titles.append("Ground Truth Data")
            plots.append(table)
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
    step_number=3,
    name="PERP/ANG",
    description="This test step calculates the percentage of successfully parked vehicles using the perpendicular and angular parking scenarios.",
    expected_result=ExpectedResult(
        operator=RelationOperator.GREATER,
        numerator=95,
        unit="%",
        aggregate_function=AggregateFunction.MEAN,
    ),
)
@register_signals(ALIAS, TestSignals)
@register_side_load(
    alias=ALIAS_JSON,
    side_load=JsonSideLoad,
    path_spec=PathSpecification(folder=r"s3://par230-prod-data-lake-sim/gt_labels/", extension=".json", s3=True),
)
@register_pre_processor(alias="park_end_gt", pre_processor=ParkEndPreprocessor)
class PerpAngStep(TestStep):
    """Test step that contains generic functions used by other test steps."""

    custom_report = CustomTeststepReport

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
            self.result.measured_result = DATA_NOK
            self.test_result = fc.NOT_ASSESSED
            plot_titles, plots, remarks = fh.rep([], 3)
            # self.result.measured_result = Result(None)

            park_type, sig_sum, fig, Result_in_percent, table = self.pre_processors["park_end_gt"]
            if park_type == "Perpendicular" or park_type == "Angular":
                self.result.measured_result = Result(Result_in_percent, unit="%")
                self.test_result = fc.PASS if Result_in_percent == 100 else fc.FAIL
            else:
                self.result.measured_result = NAN
                self.test_result = fc.NOT_ASSESSED

            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append(f"Parking type: {park_type}")

            plot_titles.append("Ground Truth Data")
            plots.append(table)
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
    step_number=1,
    name="UNKNOWN",
    description="This test step calculates the percentage of successfully parked vehicles (unknown parking type).",
    expected_result=ExpectedResult(
        operator=RelationOperator.GREATER,
        numerator=95,
        unit="%",
        aggregate_function=AggregateFunction.MEAN,
    ),
)
@register_signals(ALIAS, TestSignals)
@register_side_load(
    alias=ALIAS_JSON,
    side_load=JsonSideLoad,
    path_spec=PathSpecification(folder=r"s3://par230-prod-data-lake-sim/gt_labels/", extension=".json", s3=True),
)
@register_pre_processor(alias="park_end_gt", pre_processor=ParkEndPreprocessor)
class BaseStep(TestStep):
    """Test step that contains generic functions used by other test steps."""

    custom_report = CustomTeststepReport

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
            self.result.measured_result = DATA_NOK
            self.test_result = fc.NOT_ASSESSED
            plot_titles, plots, remarks = fh.rep([], 3)
            # self.result.measured_result = Result(None)

            park_type, sig_sum, fig, Result_in_percent, table = self.pre_processors["park_end_gt"]
            if park_type == "Unknown":
                self.result.measured_result = Result(Result_in_percent, unit="%")
            else:
                self.result.measured_result = NAN
                self.test_result = fc.NOT_ASSESSED

            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append(f"Parking type: {park_type}")

            plot_titles.append("Ground Truth Data")
            plots.append(table)
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


@testcase_definition(
    name="Park in end position success rate GT",
    description="The park in end position success rate performance indicator considers the number of successfully finished park in maneuvers by the AP function, where all end position performance indicators have fulfilled the criteria (longitudinal, lateral and orientation error within tolerances), in relation to the total number of successfully finished park in maneuvers",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class ParkinEndPosSuccessKPIGT(TestCase):
    """Test case class"""

    # custom_report = MfCustomTestcaseReport
    @property
    def test_steps(self):
        """Define the test steps."""
        return [BaseStep, ParStep, PerpAngStep]
