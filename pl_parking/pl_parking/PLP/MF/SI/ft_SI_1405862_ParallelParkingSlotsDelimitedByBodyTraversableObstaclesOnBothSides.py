#!/usr/bin/env python3

"""req id : 1405862
Body-traversable objects that delimit the free spaces on the right or left side shall not allow parking with the
ego car's boot or front (bumper) overhanging them.
- Inputs to SI:
○ SgfOutput.staticObjectsOutput.staticObjectVerticesOutput.numberOfVertices
○ SgfOutput.staticObjectsOutput.staticObjectVerticesOutput.vertices[%]
○ SgfOutput.staticObjectsOutput.numberOfObjects
○ SgfOutput.staticObjectsOutput.objects[%].heightConfidences
- Outputs of SI:
○ ApParkingBoxPort.numValidParkingBoxes_nu
○ ApParkingBoxPort.parkingBoxes[%].slotCoordinates_m
"""

"""import libraries"""
import logging
import os
import sys

# import seaborn as sns
import pandas as pd
import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
"""imports from tsf core"""
from tsf.core.results import (
    FALSE,
    TRUE,
    BooleanResult,
)
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

"""imports from current repo"""

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    SISignals,
)
from pl_parking.PLP.MF.constants import DrawCarLayer, PlotlyTemplate
from pl_parking.PLP.MF.SI import ft_helper

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

"""any test must have a specific and UNIQUE alias as it will contain a data frame
with all the signals for a test script"""

READER_NAME = "SI_1405861"
signals_obj = SISignals()


@teststep_definition(
    name="Check for SI_Prevention_of_Parking_Overhang_Over_Body-Traversable_Objects_Delimiting_Free_Spaces",
    description="Check if body-traversable objects that delimit the free spaces on the right or left side not allow \
        parking with the ego car's boot or front (bumper) overhanging them.",
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(READER_NAME, SISignals)
class SI_IdentificationOfParallelParkingSlotsDelimitedByBodyTraversableObstaclesOnBothSides(TestStep):
    """Example test step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        super().__init__()

    def process(self, **kwargs):
        """Evaluating test case"""
        _log.debug("Starting processing...")
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        try:
            # Get the read data frame
            read_data = self.readers[READER_NAME]
            self.test_result = fc.INPUT_MISSING  # Result

            df = read_data.as_plain_df
            df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]

            # plots and remarks need to have the same length
            plot_titles, plots, remarks = fh.rep([], 3)
            collected_info = None
            signal_summary = {}
            ap_time = df[SISignals.Columns.TIME]
            # type of parking is verified, because the parking box should be parallel
            ap_state = df[SISignals.Columns.AP_STATE]
            # Get the parking box coordinates, number of parking boxes and the parking box dimensions

            collected_info = ft_helper.process_data_three_obj_shapes(df)

            signal_summary = {
                "Timestamp [s]": [],
                "Evaluation": [],
                "Result": [],
            }
            fig = go.Figure()
            for _, value in collected_info.items():
                signal_summary["Timestamp [s]"].append(value["ts"])
                signal_summary["Evaluation"].append(value["fail_reason"])
                signal_summary["Result"].append(ft_helper.get_result_color(value["verdict"]))
                obj_0 = go.Scatter(
                    x=value["obj_0"][::2],
                    y=value["obj_0"][1::2],
                    # showlegend=True if is_pb_found else False,
                    mode="lines",
                    fill="toself",  # Fill the polygon
                    # fillcolor="black",  # Fill color
                    line=dict(color="black"),
                    name="Body traversable object",
                    text=[
                        f"Timestamp: {value['ts']}<br>" f"X: {value['obj_0'][::2][x]}<br>" f"Y: {ycoord}"
                        for x, ycoord in enumerate(value["obj_0"][1::2])
                    ],
                    hoverinfo="text",
                )
                obj_1 = go.Scatter(
                    x=value["obj_1"][::2],
                    y=value["obj_1"][1::2],
                    # showlegend=True if is_pb_found else False,
                    mode="lines",
                    fill="toself",  # Fill the polygon
                    # fillcolor="black",  # Fill color
                    line=dict(color="black"),
                    name="Body traversable object",
                    text=[
                        f"Timestamp: {value['ts']}<br>" f"X: {value['obj_1'][::2][x]}<br>" f"Y: {ycoord}"
                        for x, ycoord in enumerate(value["obj_1"][1::2])
                    ],
                    hoverinfo="text",
                )
                obj_2 = go.Scatter(
                    x=value["obj_2"][::2],
                    y=value["obj_2"][1::2],
                    # showlegend=True if is_pb_found else False,
                    mode="lines",
                    fill="toself",  # Fill the polygon
                    # fillcolor="black",  # Fill color
                    line=dict(color="black"),
                    name="Static object",
                    text=[
                        f"Timestamp: {value['ts']}<br>" f"X: {value['obj_2'][::2][x]}<br>" f"Y: {ycoord}"
                        for x, ycoord in enumerate(value["obj_2"][1::2])
                    ],
                    hoverinfo="text",
                )
                pb_0 = go.Scatter(
                    x=value["pb_0"][::2],
                    y=value["pb_0"][1::2],
                    mode="lines",
                    # Fill the polygon
                    fill="toself",
                    fillcolor="rgba(0, 255, 0, 0.5)",  # Fill color with transparency
                    # fillcolor="green",  # Fill color
                    # fillcolor="rgba(0, 255,0 , 0.5)",  # Fill color with transparency
                    line=dict(color="green"),
                    name="Parking box detected by SI",
                    text=[
                        f"Timestamp: {value['ts']}<br>" f"X: {value['pb_0'][::2][x]}<br>" f"Y: {ycoord}"
                        for x, ycoord in enumerate(value["pb_0"][1::2])
                    ],
                    hoverinfo="text",
                )
                pb_1 = go.Scatter(
                    x=value["pb_1"][::2],
                    y=value["pb_1"][1::2],
                    mode="lines",
                    # Fill the polygon
                    fill="toself",
                    fillcolor="rgba(0, 255, 0, 0.5)",  # Fill color with transparency
                    # fillcolor="green",  # Fill color
                    # fillcolor="rgba(0, 255,0 , 0.5)",  # Fill color with transparency
                    line=dict(color="green"),
                    name="Parking box detected by SI",
                    text=[
                        f"Timestamp: {value['ts']}<br>" f"X: {value['pb_1'][::2][x]}<br>" f"Y: {ycoord}"
                        for x, ycoord in enumerate(value["pb_1"][1::2])
                    ],
                    hoverinfo="text",
                )
                new_origin_x, new_origin_y, new_origin_yaw = value.get("ego_vehicle", None)[0]
                vehicle_plot = DrawCarLayer.draw_car(new_origin_x, new_origin_y, new_origin_yaw)
                vehicle_plot = vehicle_plot[1]
                fig.add_trace(pb_1)
                fig.add_trace(pb_0)
                fig.add_trace(obj_0)
                fig.add_trace(obj_1)
                fig.add_trace(obj_2)
                for p in vehicle_plot:
                    fig.add_trace(p)

            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="X coordinates",
                yaxis_title="Y coordinates",
                title="Prevention of Parking Overhang Over Body-Traversable Objects Delimiting Free Spaces",
            )
            fig.update_layout(PlotlyTemplate.lgt_tmplt, showlegend=True)

            self.test_result = fc.PASS if value["verdict"] else fc.FAIL
            self.result.measured_result = TRUE if value["verdict"] else FALSE

            # Create a plot for the signal summary
            self.sig_sum = fh.build_html_table(pd.DataFrame(signal_summary))
            plots.append(self.sig_sum)

            if collected_info:
                plots.append(fig)
            signal_fig = go.Figure()
            ap_time = [round(x, 2) for x in ap_time.values.tolist()]
            signal_fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=ap_state,
                    mode="lines",
                    name=signals_obj._properties[SISignals.Columns.AP_STATE],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>" f"AP State: {ft_helper.ap_state_dict(state)}"
                        for idx, state in enumerate(ap_state)
                    ],
                    hoverinfo="text",
                )
            )
            signal_fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=df[SISignals.Columns.NUMVALIDPARKINGBOXES_NU].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[SISignals.Columns.NUMVALIDPARKINGBOXES_NU][0],
                )
            )

            signal_fig.layout = go.Layout(
                yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]"
            )
            signal_fig.update_layout(
                PlotlyTemplate.lgt_tmplt,
                title="AP State and Number of Valid Parking Boxes",
            )

            plots.append(signal_fig)
            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)

        except Exception as err:
            print(str(err))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("ReqId_1405862")
@testcase_definition(
    name="SI Identification Of Parallel Parking Slots Delimited By Body Traversable Obstacles On Both Sides TC",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_9tw5ijpwEe6GONELpfdJ2Q?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
    description="The Scene Interpretation system shall correctly identify and provide parallel parking slots that are delimited by body-traversable obstacles \
        (e.g., curbs, low barriers) on both the left and right sides. The curb side delimiter is optional and should not affect the identification of valid parking slots.",
)
@register_inputs("/parking")
class SI_IdentificationOfParallelParkingSlotsDelimitedByBodyTraversableObstaclesOnBothSides_TC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SI_IdentificationOfParallelParkingSlotsDelimitedByBodyTraversableObstaclesOnBothSides,
        ]
