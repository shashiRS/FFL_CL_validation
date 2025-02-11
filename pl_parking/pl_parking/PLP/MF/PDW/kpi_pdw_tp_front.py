#!/usr/bin/env python3
"""Test case for the Proximity Detection Warning (PDW) component (front sector)."""
import logging
import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from tsf.core.common import AggregateFunction, PathSpecification, RelationOperator
from tsf.core.results import DATA_NOK, ExpectedResult, Result
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_side_load,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.io.sideload import JsonSideLoad
from tsf.io.signals import SignalDefinition

import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "Grubii Otilia (uif32707)"
__copyright__ = "2024-2012, Continental AG"
__version__ = "0.1"
__status__ = "Development"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


ALIAS = "TP_PDW_Front"
ALIAS_JSON = "TP_PDW_FRONT_GT"


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        ACTIVATE_BRAKE_INTERV = "ActivateBrakeIntervScreen"
        VELOCITY = "Velocity"
        STEERING_ANGLE = "SteeringAngle"
        TIMESTAMP = "time"
        MINIMUM_DISTANCE = "MINIMUM_DISTANCE"
        DRIVEN_DISTANCE = "DRIVEN_DISTANCE"
        SECTOR_CRITICALLY0 = "SECTOR_CRITICALLY0"
        SECTOR_CRITICALLY = "SECTOR_CRITICALLY{}"
        SECTOR_DISTANCE0 = "SECTOR_DISTANCE0"
        SECTOR_DISTANCE = "SECTOR_DISTANCE{}"
        SECTOR_CRITICALLY1 = "SECTOR_CRITICALLY1"
        SECTOR_DISTANCE1 = "SECTOR_DISTANCE1"
        SECTOR_CRITICALLY2 = "SECTOR_CRITICALLY2"
        SECTOR_DISTANCE2 = "SECTOR_DISTANCE2"
        SECTOR_CRITICALLY3 = "SECTOR_CRITICALLY3"
        SECTOR_DISTANCE3 = "SECTOR_DISTANCE3"
        SECTOR_ID_0 = "SECTOR_ID_0"
        SECTOR_ID = "SECTOR_ID_{}"
        SECTOR_ID_1 = "SECTOR_ID_1"
        SECTOR_ID_2 = "SECTOR_ID_2"
        SECTOR_ID_3 = "SECTOR_ID_3"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = [
            "MTA_ADC5",
        ]
        self._properties = {
            self.Columns.ACTIVATE_BRAKE_INTERV: ".MF_LSCA_DATA.hmiPort.activateBrakeInterventionScreen_nu",
            self.Columns.VELOCITY: ".SI_DATA.m_egoMotionPort.vel_mps",
            self.Columns.MINIMUM_DISTANCE: ".MF_PDWARNPROC_DATA.procToLogicPort.minimalDistance_m",
            self.Columns.DRIVEN_DISTANCE: ".SI_DATA.m_egoMotionPort.drivenDistance_m",
            self.Columns.TIMESTAMP: ".MF_LSCA_DATA.hmiPort.sSigHeader.uiTimeStamp",
        }

        front_sectors_critical = {
            self.Columns.SECTOR_CRITICALLY.format(
                x
            ): f".MF_PDWARNPROC_DATA.pdcpSectorsPort.sectorsFront[{x}].criticalityLevel_nu"
            for x in range(constants.PDWConstants.NUMBER_SECTORS)
        }
        front_sectors_id = {
            self.Columns.SECTOR_ID.format(x): f".MF_PDWARNPROC_DATA.pdcpSectorsPort.sectorsFront[{x}].sectorID_nu"
            for x in range(constants.PDWConstants.NUMBER_SECTORS)
        }
        front_sectors_distance = {
            self.Columns.SECTOR_DISTANCE.format(
                x
            ): f".MF_PDWARNPROC_DATA.pdcpSectorsPort.sectorsFront[{x}].smallestDistance_m"
            for x in range(constants.PDWConstants.NUMBER_SECTORS)
        }
        self._properties.update(front_sectors_critical)
        self._properties.update(front_sectors_id)
        self._properties.update(front_sectors_distance)


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="Front Sectors",
    description="Check TP of PDW component(front sector).",
    expected_result=ExpectedResult(
        operator=RelationOperator.GREATER_OR_EQUAL,
        numerator=95.0,
        unit="%",
        aggregate_function=AggregateFunction.AT_LEAST_95_PERCENT,
    ),
)
@register_side_load(
    alias=ALIAS_JSON,
    side_load=JsonSideLoad,
    path_spec=PathSpecification(
        folder=r"s3://par230-prod-data-lake-sim/gt_labels/", extension=".json", suffix="_pdw", s3=True
    ),  # CAEdge path
)
@register_signals(ALIAS, Signals)
class Step1(TestStep):
    """Test step for the Proximity Detection Warning (PDW) component (front sector)."""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        super().__init__()

    def process(self, **kwargs):
        """Process the test step."""
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
            plot_titles, plots, remarks = fh.rep([], 3)

            # Read gt json file
            # def load_json(filepath):
            #     """
            #     Load JSON data from a file.

            #     Parameters:
            #     - filepath: str, the path to the JSON file.

            #     Returns:
            #     - data: dictionary, the parsed JSON data.
            #     """
            #     try:
            #         with open(filepath) as file:
            #             data = json.load(file)
            #     except FileNotFoundError:
            #         _log.error("Ground truth file not found.")
            #         data = "Ground truth file not found."
            #     return data

            # file_path = os.path.abspath(self.artifacts[0].file_path)
            # current_dir = os.path.dirname(file_path)
            # file_name = self.result.details["file_name"]
            # file_name = file_name.replace(".rrec", "")
            # # file_name = file_name.replace("_extract", "")
            # gt_json = os.path.join(current_dir, f"{file_name}_pdw.json")
            # gt_data = load_json(gt_json)
            gt_data = self.side_load[ALIAS_JSON]
            data = {
                "Sector": [0, 1, 2, 3],
                "X": [1, 1, 2, 2],  # X coordinates for 2x2 grid
                "Y": [1, 2, 1, 2],  # Y coordinates for 2x2 grid
                "Critical Level": [0, 1, 2, 3],  # Example critical levels for each sector
            }
            pd.DataFrame(data)

            percent_tp = 0
            self.result.measured_result = DATA_NOK
            measured_critical_level = None
            initial_detection_timestamp = None
            evaluated_list = []
            sector_id_list = []
            result_dict = {}
            json_root_key = "SectorBasedDistance"
            json_timestamp_key = "Timestamp"
            json_sector_id_key = "Sectors"
            sector_dict = {}
            sector_dict_1 = {}
            pdw_list = []

            df = self.readers[ALIAS]  # for rrec
            # df[Signals.Columns.TIMESTAMP] = df.index

            df[Signals.Columns.VELOCITY] *= constants.GeneralConstants.MPS_TO_KMPH
            velocity = df[Signals.Columns.VELOCITY]
            time = df[Signals.Columns.TIMESTAMP] - df[Signals.Columns.TIMESTAMP].iat[0]
            time /= constants.GeneralConstants.US_IN_S
            df[Signals.Columns.DRIVEN_DISTANCE] -= df[Signals.Columns.DRIVEN_DISTANCE].iat[0]
            df[Signals.Columns.DRIVEN_DISTANCE] /= constants.GeneralConstants.M_TO_KM

            for sector in range(constants.PDWConstants.NUMBER_SECTORS):
                filter_outside_zone = df[Signals.Columns.SECTOR_DISTANCE.format(sector)][
                    df[Signals.Columns.SECTOR_DISTANCE.format(sector)] > 0
                ]
                if any(filter_outside_zone[filter_outside_zone < 2.55]):
                    first_timestamp = filter_outside_zone[filter_outside_zone < 2.55].index[0]
                    sector_dict[sector] = first_timestamp

            sector_dict = {}
            for sector in range(constants.PDWConstants.NUMBER_SECTORS):
                sector_dict_1[sector] = {
                    "sector_id": df[Signals.Columns.SECTOR_ID.format(sector)],
                    "sector_distance": df[Signals.Columns.SECTOR_DISTANCE.format(sector)],
                    "sector_criticality": df[Signals.Columns.SECTOR_CRITICALLY.format(sector)],
                }
            standstill_events = velocity.rolling(2).apply(
                lambda x: abs(x[0]) > abs(x[1]) and abs(x[1]) <= 0.01, raw=True
            )
            list_standstill_events = [idx for idx, val in enumerate(standstill_events) if val]
            filtered_standstill_events = [val for val in list_standstill_events if val != 0]
            initial_detection_timestamp = filtered_standstill_events[-1] if filtered_standstill_events else None
            total_standstill_events = standstill_events.sum()
            valid_gt_data = {}
            valid_timestamps = []

            for sector in range(constants.PDWConstants.NUMBER_SECTORS):
                sector_id_list.append(max(df[Signals.Columns.SECTOR_ID.format(sector)]))
                # print(sector_id_list)
            for sector in sector_id_list:
                sector_dict.setdefault(sector, initial_detection_timestamp)

            def get_sector_parameter(sector_id: int) -> str:
                sectors = ["Front", "Right", "Rear", "Left"]
                if 0 <= sector_id <= 15:
                    return sectors[sector_id // 4]
                else:
                    return "Invalid sector ID"

            # retrieve information from gt json file
            if gt_data != "Ground truth file not found.":
                for entry in gt_data[json_root_key]:
                    for sector_id, sector_data in entry[json_sector_id_key].items():
                        if sector_data:
                            valid_gt_data[entry[json_timestamp_key]] = {
                                f"sector_{sector_id}": {
                                    "objectID": sector_data["objectID"],
                                    "distanceValue": sector_data["distanceValue"],
                                    "distanceError": sector_data["distanceError"],
                                    "sectorID": get_sector_parameter(int(sector_id)),
                                }
                            }
                            valid_timestamps.append(entry[json_timestamp_key])
                eval_text_gt = "Ground truth data loaded successfully</br>"
                # Append valid_gt_data info to eval_text_gt
                # for timestamp, sector_info in valid_gt_data.items():
                #     eval_text_gt += f"Timestamp: {timestamp}, Sector Info: {sector_info},</br>"
                if len(valid_gt_data) == 0:
                    eval_text_gt += "No object detected in GT file."
            else:
                eval_text_gt = "Ground truth file not found."

            if total_standstill_events == 0 or initial_detection_timestamp is None:
                # self.result.measured_result = Result(0, unit="%")
                eval_text = (
                    "No standstill events detected, thus PDW function cannot be evaluated and the verdict is FAILED."
                )
                evaluated_list = [False]
            else:
                # self.result.measured_result = Result(100, unit="%")
                eval_text = "PDW function evaluated successfully."
                fig_pdw = go.Figure()
                # Plot all front points first
                # fig_pdw.add_trace(go.Scatter(
                #                 x=x_coords_front,  # X-coordinates for all points
                #                 y=y_coords_front,  # Y-coordinates for all points
                #                 mode='lines',  # Display points as lines
                #                 name='All Front Points',
                #                 marker=dict(color='blue', size=5),  # Marker properties
                #                 showlegend=False
                # ))
                for sector_id, initial_detection_timestamp in sector_dict.items():
                    initial_critical_level = df[Signals.Columns.SECTOR_CRITICALLY.format(sector_id)].iat[
                        initial_detection_timestamp
                    ]
                    initial_distance = df[Signals.Columns.SECTOR_DISTANCE.format(sector_id)].iat[
                        initial_detection_timestamp
                    ]
                    if f"sector_{sector_id}" in valid_gt_data[valid_timestamps[0]]:
                        measured_critical_level = fh.pdw_threshold_check(
                            valid_gt_data[valid_timestamps[0]][f"sector_{sector_id}"]["distanceValue"]
                        )
                    else:
                        measured_critical_level = 0
                    result_dict[f"Sector {sector_id}"] = {
                        "Text": f"Minimum distance {initial_distance:.2f} m for sector {sector_id}\
                    , at timestamp {time.iat[initial_detection_timestamp]:.2f} s (epoch : {df[Signals.Columns.TIMESTAMP].iat[initial_detection_timestamp]}) at velocity {velocity.iat[initial_detection_timestamp]:.2f} km/h.\
                        Critical level detected by PDW : {initial_critical_level}. Real critical level {measured_critical_level}.",
                        "TP": initial_critical_level == measured_critical_level,
                    }
                    evaluated_list.append(initial_critical_level == measured_critical_level)

                    # Get the region data for the valid sector and critical level
                    if initial_critical_level != 0:
                        pdw_list.append(
                            (
                                sector_id,
                                initial_critical_level,
                                f"PDW critical level({initial_critical_level})  sector-{sector_id}",
                            )
                        )
                        # fig_pdw = plot_multiple_sectors(sector, initial_critical_level, sector_dict_front[sector][initial_critical_level]["name"])
                    if measured_critical_level != 0:
                        pdw_list.append(
                            (
                                sector_id,
                                measured_critical_level,
                                f"Real critical level({measured_critical_level}) sector-{sector_id}",
                            )
                        )
                fig_pdw = plot_multiple_sectors(pdw_list)

                event_summary = pd.DataFrame(result_dict)
                event_summary = fh.build_html_table(event_summary)
                plot_titles.append("")
                plots.append(event_summary)
                remarks.append("")

                plot_titles.append("")
                plots.append(fig_pdw)
                remarks.append("")

            signal_summary = pd.DataFrame(
                {
                    "Prerequisites": {
                        "1": "Activation of PDW",
                        "2": "GT data loaded",
                    },
                    "Additional information": {
                        "1": eval_text,
                        "2": eval_text_gt,
                    },
                }
            )
            if all(evaluated_list):
                percent_tp = 100
                self.result.measured_result = Result(percent_tp, unit="%")
            else:
                self.result.measured_result = Result(percent_tp, unit="%")

            sig_sum = fh.build_html_table(signal_summary)
            fig = go.Figure()
            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append("")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=df[Signals.Columns.ACTIVATE_BRAKE_INTERV].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.ACTIVATE_BRAKE_INTERV],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=df[Signals.Columns.VELOCITY].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.VELOCITY],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=df[Signals.Columns.DRIVEN_DISTANCE].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.DRIVEN_DISTANCE],
                )
            )
            for i in range(constants.PDWConstants.NUMBER_SECTORS):
                fig.add_trace(
                    go.Scatter(
                        x=time,
                        y=df[Signals.Columns.SECTOR_CRITICALLY.format(i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALLY.format(i)],
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=time,
                        y=df[Signals.Columns.SECTOR_DISTANCE.format(i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCE.format(i)],
                    )
                )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=df[Signals.Columns.MINIMUM_DISTANCE].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.MINIMUM_DISTANCE],
                )
            )

            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time [s]",
                title="Graphical Overview of PDW Front",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            # fig.add_annotation(
            #     dict(
            #         font=dict(color="black", size=12),
            #         x=0,
            #         y=-0.12,
            #         showarrow=False,
            #         text="Graphical Overview",
            #         textangle=0,
            #         xanchor="left",
            #         xref="paper",
            #         yref="paper",
            #     )
            # )
            plot_titles.append("")
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


@verifies("1167005")
@testcase_definition(
    name="TP PDW Front",
    description="PDW shall set the criticality level accordingly based on the distance between the car contour and the relevant obstacle. The reference criticality is to be measured when at standstill for front sector.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FTX_lKKMEF33Ee6hyY-R-i-gng&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_fdSOICuJEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/parking/")
# @register_inputs("/TSF_DEBUG/")
class FtPdwTPFront(TestCase):
    """Test case for the Proximity Detection Warning (PDW) component (front sector)."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            Step1,
        ]


# Front coordinates provided earlier
x_coords_front = [
    -79,
    -261,
    -478,
    -659,
    -451,
    -412,
    -323,
    -290,
    -79,
    -261,
    -323,
    -412,
    -478,
    -460,
    -591,
    -540,
    -440,
    -367,
    -296,
    -200,
    -150,
    -277,
    -367,
    -460,
    -478,
    -367,
    -367,
    -367,
    -367,
]
y_coords_front = [
    -128,
    -4,
    -4,
    -128,
    -240,
    -215,
    -215,
    -240,
    -128,
    -4,
    -215,
    -215,
    -4,
    -60,
    -165,
    -192,
    -125,
    -125,
    -125,
    -192,
    -165,
    -60,
    -60,
    -60,
    -4,
    -4,
    -60,
    -125,
    -215,
]

# Provided dictionary
sector_dict_front = {
    3: {
        3: {
            "x": [-290, -323, -296, -200],
            "y": [-240, -215, -125, -192],
            "name": "Sector 3, critical 3",
            "fill": "rgba(255, 0, 0, 0.5)",
        },
        2: {
            "x": [-150, -277, -296, -200],
            "y": [-165, -60, -125, -192],
            "name": "Sector 3, critical 2",
            "fill": "rgba(255, 255, 0, 0.5)",
        },
        1: {
            "x": [-150, -277, -261, -79],
            "y": [-165, -60, -4, -128],
            "name": "Sector 3, critical 1",
            "fill": "rgba(0, 255, 0, 0.5)",
        },
        # 0: {"x": [-329, -349, -541, -158], "y": [-110, -70, 100, 10], "name": "Sector 3, critical 0", "fill": "rgba(128, 128,  128, 0.5)"},
    },
    2: {
        3: {
            "x": [-367, -323, -296, -367],
            "y": [-215, -215, -125, -125],
            "name": "Sector 2, critical 3",
            "fill": "rgba(255, 0, 0, 0.5)",
        },
        2: {
            "x": [-367, -277, -296, -367],
            "y": [-60, -60, -125, -125],
            "name": "Sector 2, critical 2",
            "fill": "rgba(255, 255, 0, 0.5)",
        },
        1: {
            "x": [-367, -367, -277, -261],
            "y": [-4, -60, -60, -4],
            "name": "Sector 2, critical 1",
            "fill": "rgba(0, 255, 0, 0.5)",
        },
        # 0: {"x": [-670, -740, -550, -480], "y": [-110, -70, 100, 10], "name": "Sector 2, critical 0", "fill": "rgba(128, 128,  128, 0.5)"},
    },
    1: {
        3: {
            "x": [-367, -412, -440, -367],
            "y": [-215, -215, -125, -125],
            "name": "Sector 1, critical 3",
            "fill": "rgba(255, 0, 0, 0.5)",
        },
        2: {
            "x": [-367, -460, -440, -367],
            "y": [-60, -60, -125, -125],
            "name": "Sector 1, critical 2",
            "fill": "rgba(255, 255, 0, 0.5)",
        },
        1: {
            "x": [-367, -367, -460, -478],
            "y": [-4, -60, -60, -4],
            "name": "Sector 1, critical 1",
            "fill": "rgba(0, 255, 0, 0.5)",
        },
        # 0: {"x": [-670, -740, -550, -480], "y": [-110, -70, 100, 10], "name": "Sector 1, critical 0", "fill": "rgba(128, 128,  128, 0.5)"},
    },
    0: {
        3: {
            "x": [-451, -412, -440, -540],
            "y": [-240, -215, -125, -192],
            "name": "Sector 0, critical 3",
            "fill": "rgba(255, 0, 0, 0.5)",
        },
        2: {
            "x": [-591, -460, -440, -540],
            "y": [-165, -60, -125, -192],
            "name": "Sector 0, critical 2",
            "fill": "rgba(255, 255, 0, 0.5)",
        },
        1: {
            "x": [-591, -460, -478, -659],
            "y": [-165, -60, -4, -128],
            "name": "Sector 0, critical 1",
            "fill": "rgba(0, 255, 0, 0.5)",
        },
        # 0: {"x": [-670, -740, -550, -480], "y": [-110, -70, 100, 10], "name": "Sector 0, critical 0", "fill": "rgba(128, 128,  128, 0.5)"},
    },
}


def plot_multiple_sectors(sectors_critical_levels_legend, total_sectors=4, total_critical_levels=3):
    """
    Creates a Proximity Detection Warning (PDW) sensor visualization grid using Plotly.

    Parameters:
    - sectors_critical_levels_legend (list of tuples):
        A list of tuples in the format [(sector, critical_level, legend), ...], where:
        - sector (int): Sector number (0 = far left, increasing clockwise).
        - critical_level (int): Critical level in the sector (3 = closest, 1 = farthest).
        - legend (str): Description or label for the highlighted area.
    - total_sectors (int): Total number of sectors (spread over a semi-circle).
    - total_critical_levels (int): Total critical levels (concentric distance ranges).
    """
    # Define colors for critical levels (inverted: 3 = closest to the car)
    base_colors = {
        3: "rgba(255, 0, 0, {opacity})",  # Red
        2: "rgba(255, 255, 0, {opacity})",  # Yellow
        1: "rgba(0, 255, 0, {opacity})",
    }  # Green

    # Combine legends and count duplicates
    combined_data = {}
    for sector, critical_level, legend in sectors_critical_levels_legend:
        key = (sector, critical_level)
        if key in combined_data:
            combined_data[key]["legend"] += f", {legend}"
            combined_data[key]["count"] += 1
        else:
            combined_data[key] = {"legend": legend, "count": 1}

    # Define angular range for the semi-circle
    theta = np.linspace(0, np.pi, total_sectors + 1)

    # Create figure
    fig = go.Figure()

    # Draw grid: sectors and levels (outermost = green, innermost = red)
    for level in range(1, total_critical_levels + 1):
        # Compute radius for the current level
        radius_outer = (total_critical_levels - level + 1) / total_critical_levels
        radius_inner = (total_critical_levels - level) / total_critical_levels if level > 1 else 0

        for i in range(total_sectors):
            # Compute angular boundaries of the sector
            theta_start = theta[i]
            theta_end = theta[i + 1]

            # Generate polar coordinates for the wedge
            theta_points = np.linspace(theta_start, theta_end, 100)
            x_outer = radius_outer * np.cos(theta_points)
            y_outer = radius_outer * np.sin(theta_points)
            x_inner = radius_inner * np.cos(theta_points[::-1])
            y_inner = radius_inner * np.sin(theta_points[::-1])

            # Combine outer and inner coordinates
            x_coords = np.concatenate((x_outer, x_inner))
            y_coords = np.concatenate((y_outer, y_inner))

            # Add sector wedge to the grid
            fig.add_trace(
                go.Scatter(
                    x=x_coords,
                    y=y_coords,
                    mode="lines",
                    fill="toself",
                    line=dict(color="blue", width=0.5),
                    fillcolor="rgba(200, 200, 200, 0.1)",
                    hoverinfo="skip",
                )
            )

    # Add the diameter (base line of the semicircle)
    fig.add_trace(go.Scatter(x=[-1, 1], y=[0, 0], mode="lines", line=dict(color="blue", width=0.5), hoverinfo="skip"))

    # Highlight sectors based on combined data
    for (sector, critical_level), data in combined_data.items():
        legend = data["legend"]
        count = data["count"]  # Number of duplicates

        # Compute opacity based on the number of duplicates
        opacity = min(0.3 + count * 0.2, 1.0)  # Ensure max opacity is 1.0

        # Compute angular boundaries of the highlighted sector
        theta_start = theta[sector]
        theta_end = theta[sector + 1]
        radius_outer = (total_critical_levels - critical_level + 1) / total_critical_levels
        radius_inner = (total_critical_levels - critical_level) / total_critical_levels if critical_level > 1 else 0

        # Generate polar coordinates for the highlighted wedge
        theta_points = np.linspace(theta_start, theta_end, 100)
        x_outer = radius_outer * np.cos(theta_points)
        y_outer = radius_outer * np.sin(theta_points)
        x_inner = radius_inner * np.cos(theta_points[::-1])
        y_inner = radius_inner * np.sin(theta_points[::-1])

        # Combine outer and inner coordinates
        x_coords = np.concatenate((x_outer, x_inner))
        y_coords = np.concatenate((y_outer, y_inner))

        # Add highlighted wedge
        fig.add_trace(
            go.Scatter(
                x=x_coords,
                y=y_coords,
                mode="lines",
                fill="toself",
                line=dict(color="black", width=1),
                fillcolor=base_colors[critical_level].format(opacity=opacity),
                text=f"Sector {sector}<br>Level {critical_level}<br>{legend}",
                hoverinfo="text",
                opacity=opacity,
            )
        )

    # Add CAR label at the base
    fig.add_trace(
        go.Scatter(x=[0], y=[-0.05], mode="text", text=["CAR"], textfont=dict(size=16, color="black"), hoverinfo="skip")
    )

    # Set layout
    fig.update_layout(
        showlegend=False,
        xaxis=dict(visible=False, range=[-1.1, 1.1]),
        yaxis=dict(visible=False, range=[-0.1, 1.1]),
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor="white",
    )

    # Show the plot
    # fig.show()
    return fig
