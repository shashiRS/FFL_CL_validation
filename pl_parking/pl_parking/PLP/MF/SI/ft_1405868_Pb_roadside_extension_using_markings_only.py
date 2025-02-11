#!/usr/bin/env python3

"""import libraries"""
import logging
import os
import sys
import tempfile
from pathlib import Path

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
from tsf.core.utilities import debug

import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    SISignals,
    build_html_table,
    get_color,
)
from pl_parking.PLP.MF.constants import DrawCarLayer, PlotlyTemplate
from pl_parking.PLP.MF.SI import ft_helper

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

"""any test must have a specific and UNIQUE alias as it will contain a data frame
with all the signals for a test script"""
READER_NAME = "SI_1405868"
signals_obj = SISignals()


@teststep_definition(
    name="Alignment check",
    description="Given a bounding box formed by an parking line and a static object(car or wall), check if only the parking line marking was used for the road side alignment of the parking box .",
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(READER_NAME, SISignals)
class SI_TestStep(TestStep):
    """Example test step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        super().__init__()

    def process(self, **kwargs):
        """Evaluating test case"""
        _log.debug("Starting processing...")
        self.result.details.update(
            {
                "Plots": [],
                "file_name": os.path.basename(self.artifacts[0].file_path),
            }
        )
        try:
            plots = []
            # Get the read data frame

            read_data = self.readers[READER_NAME]
            # new_collected_info = ft_helper.process_data(read_data)
            df = read_data.as_plain_df
            remark = "Signals used for the evaluation:<br><br>\
                <b>For objects</b><br> \
                    GT.envModelPort.staticObjects._%_.objShape_m.array._%_.x_dir<br>\
                    GT.envModelPort.staticObjects._%_.objShape_m.array._%_.y_dir<br>\
                <b>For delimiter</b><br> \
                    GT.envModelPort.parkingSpaceMarkings._0_.pos_m.array._%_.x_dir<br>\
                    GT.envModelPort.parkingSpaceMarkings._0_.pos_m.array._%_.y_dir<br>\
                <b>For parking box</b><br> \
                    AP.parkingBoxPort.parkingBoxes_0.slotCoordinates_FrontLeft_x<br>\
                    AP.parkingBoxPort.parkingBoxes_0.slotCoordinates_FrontLeft_y<br>\
                    AP.parkingBoxPort.parkingBoxes_0.slotCoordinates_FrontRight_x<br>\
                    AP.parkingBoxPort.parkingBoxes_0.slotCoordinates_FrontRight_y<br>\
                    AP.parkingBoxPort.parkingBoxes_0.slotCoordinates_RearLeft_x<br>\
                    AP.parkingBoxPort.parkingBoxes_0.slotCoordinates_RearLeft_y<br>\
                    AP.parkingBoxPort.parkingBoxes_0.slotCoordinates_RearRight_x<br>\
                    AP.parkingBoxPort.parkingBoxes_0.slotCoordinates_RearRight_y<br>"
            df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
            collected_info = ft_helper.process_from_one_object_and_delimiter(df)

            sig_sum = {
                "Timestamp [s]": [],
                # "Space between delimiter width [m]": [],
                # "Parking spot dimensions [m]": [],
                "Detection details": [],
                "Result": [],
            }
            missalignment_value_list = []
            test_results = [val["verdict"] for val in collected_info.values()]
            if all(test_results):
                self.result.measured_result = TRUE
                test_result = fc.PASS
                # Check if delimiters are present
                first_key = list(collected_info.keys())[0]
                sig_sum = {
                    "Timestamp [s]": {"0": collected_info[first_key]["ts"]},
                    "Evaluation": {
                        "0": "The parking box is detected between the two vehicles, with one parking marker present in the space."
                    },
                    "Result": {"0": ft_helper.get_result_color(collected_info[first_key]["verdict"])},
                }
                sig_sum = build_html_table(pd.DataFrame(sig_sum), remark)
            else:
                self.result.measured_result = FALSE
                test_result = fc.FAIL
                for _, val in collected_info.items():
                    if not val["verdict"]:
                        missalignment_value_list.append(val["misalignment_dist"])
                        sig_sum["Timestamp [s]"].append(val["ts"])
                        sig_sum["Result"].append(ft_helper.get_result_color(val["verdict"]))
                        sig_sum["Detection details"].append(val["fail_reason"])
                sig_sum = build_html_table(pd.DataFrame(sig_sum), remark)
                sig_sum = ft_helper.create_hidden_table(sig_sum)

            plots.append(sig_sum)
            TimestampValue = [list(read_data.index).index(i) for i in list(collected_info.keys())]
            fig = go.Figure()
            global_x_min = float("inf")
            global_x_max = float("-inf")
            global_y_min = float("inf")
            global_y_max = float("-inf")
            first_frame = True

            frames = []

            for key, val in collected_info.items():

                frame_data = []  # np.rad2deg(val.get('ego_vehicle',None)[0][2])
                new_origin_x, new_origin_y, new_origin_yaw = val.get("ego_vehicle", None)[0]

                vehicle_plot = DrawCarLayer.draw_car(new_origin_x, new_origin_y, new_origin_yaw)

                vehicle_plot = vehicle_plot[1]

                val_coords = val["pb"]
                x_coords_box, y_coords_box = val_coords[::2], val_coords[1::2]

                x_coords_box_to_plot = x_coords_box
                y_coords_box_to_plot = y_coords_box
                # if x_coords_box_to_plot[0]:
                #     global_x_min = min(global_x_min, min(x_coords_box_to_plot))
                #     global_x_max = max(global_x_max, max(x_coords_box_to_plot))
                #     global_y_min = min(global_y_min, min(y_coords_box_to_plot))
                #     global_y_max = max(global_y_max, max(y_coords_box_to_plot))
                if x_coords_box_to_plot[0]:
                    global_x_min = min(x_coords_box_to_plot)
                    global_x_max = max(x_coords_box_to_plot)
                    global_y_min = min(y_coords_box_to_plot)
                    global_y_max = max(y_coords_box_to_plot)
                parking_box_trace = go.Scatter(
                    x=x_coords_box_to_plot,
                    y=y_coords_box_to_plot,
                    # showlegend=True if is_pb_found else False,
                    mode="markers+lines",
                    line=dict(color=ft_helper.get_slot_color(val["verdict"])),
                    # line=dict(color="red" if val["verdict"][pb_id] == "FAIL" else "green"),
                    fill="toself",  # Fill the polygon
                    fillcolor=ft_helper.get_slot_color(val["verdict"]),
                    # fillcolor='rgba(255, 0, 0, 0.3)' if val["verdict"][pb_id] == "FAIL" else\
                    #         "rgba(0, 255, 0, 0.3)" if val["verdict"][pb_id] == "PASS" else "rgba(239, 239, 240, 0.3)",  # Semi-transparent red fill
                    name="Parking Box",
                    text=[
                        f"Timestamp: {val['ts']}<br>" f"X: {x_coords_box[x]}<br>" f"Y: {ycoord}"
                        for x, ycoord in enumerate(y_coords_box)
                    ],
                    hoverinfo="text",
                )

                # Add the parking box trace to the figure, then add to frame_data
                if first_frame:
                    fig.add_trace(parking_box_trace)
                    frame_data.append(parking_box_trace)
                else:
                    frame_data.append(parking_box_trace)
                val_coords = val["misalignment"]
                x_coords_box, y_coords_box = val_coords[::2][0], val_coords[1::2][0]

                x_coords_box_to_plot = x_coords_box
                y_coords_box_to_plot = y_coords_box
                parking_box_trace = go.Scatter(
                    x=x_coords_box_to_plot,
                    y=y_coords_box_to_plot,
                    showlegend=True if not val["verdict"] else False,  # Show only when failed
                    # showlegend=True if is_pb_found else False,
                    mode="lines",
                    line=dict(color="#818589"),
                    # line=dict(color="red" if val["verdict"][pb_id] == "FAIL" else "green"),
                    fill="toself",  # Fill the polygon
                    fillcolor="#818589",
                    # fillcolor='rgba(255, 0, 0, 0.3)' if val["verdict"][pb_id] == "FAIL" else\
                    #         "rgba(0, 255, 0, 0.3)" if val["verdict"][pb_id] == "PASS" else "rgba(239, 239, 240, 0.3)",  # Semi-transparent red fill
                    name=f"Misalignment of {val['misalignment_dist']} m" if not val["verdict"] else " ",
                    text=[],
                    hoverinfo="text",
                )

                # Add the parking box trace to the figure, then add to frame_data
                if first_frame:
                    fig.add_trace(parking_box_trace)
                    frame_data.append(parking_box_trace)
                else:
                    frame_data.append(parking_box_trace)
                val_coords = val["obj_1"]
                x_coords_box, y_coords_box = val_coords[::2], val_coords[1::2]

                x_coords_box_to_plot = x_coords_box[0]
                y_coords_box_to_plot = y_coords_box[0]

                # global_x_min = min(global_x_min, min(x_coords_box_to_plot))
                # global_x_max = max(global_x_max, max(x_coords_box_to_plot))
                # global_y_min = min(global_y_min, min(y_coords_box_to_plot))
                # global_y_max = max(global_y_max, max(y_coords_box_to_plot))
                parking_box_trace = go.Scatter(
                    x=x_coords_box_to_plot,
                    y=y_coords_box_to_plot,
                    # showlegend=True if is_pb_found else False,
                    mode="lines",
                    line=dict(color="black"),
                    name="Object ",
                    text=[
                        f"Timestamp: {val['ts']}<br>" f"X: {x_coords_box[x]}<br>" f"Y: {ycoord}"
                        for x, ycoord in enumerate(y_coords_box)
                    ],
                    hoverinfo="text",
                )

                # Add the parking box trace to the figure, then add to frame_data
                if first_frame:
                    fig.add_trace(parking_box_trace)
                    frame_data.append(parking_box_trace)
                else:
                    frame_data.append(parking_box_trace)

                val_coords = val["delimiter"]
                x_coords_box, y_coords_box = val_coords[::2], val_coords[1::2]

                x_coords_box_to_plot = x_coords_box
                y_coords_box_to_plot = y_coords_box

                # global_x_min = min(global_x_min, min(x_coords_box_to_plot))
                # global_x_max = max(global_x_max, max(x_coords_box_to_plot))
                # global_y_min = min(global_y_min, min(y_coords_box_to_plot))
                # global_y_max = max(global_y_max, max(y_coords_box_to_plot))
                parking_box_trace = go.Scatter(
                    x=x_coords_box_to_plot,
                    y=y_coords_box_to_plot,
                    # showlegend=True if is_pb_found else False,
                    mode="lines",
                    line=dict(dash="dash", color="black"),
                    name="Delimiter",
                    text=[
                        f"Timestamp: {val['ts']}<br>" f"X: {x_coords_box[x]}<br>" f"Y: {ycoord}"
                        for x, ycoord in enumerate(y_coords_box)
                    ],
                    hoverinfo="text",
                )

                # Add the parking box trace to the figure, then add to frame_data
                if first_frame:
                    fig.add_trace(parking_box_trace)
                    frame_data.append(parking_box_trace)
                else:
                    frame_data.append(parking_box_trace)
                if first_frame:
                    for p in vehicle_plot:
                        fig.add_trace(p)

                for p in vehicle_plot:
                    frame_data.append(p)
                first_frame = False

                frames.append(go.Frame(data=frame_data, name=str(collected_info[key]["ts"])))
            ap_time = df[SISignals.Columns.TIME].values.tolist()
            ap_time = [round(i, 2) for i in ap_time]
            # Add frames to the figure
            fig.frames = frames

            # Configure the slider
            sliders = [
                dict(
                    steps=[
                        dict(
                            method="animate",
                            args=[
                                [str(ap_time[i])],  # The frame name is the timestamp
                                dict(
                                    mode="immediate",
                                    frame=dict(duration=500, redraw=True),
                                    transition=dict(duration=300),
                                ),
                            ],
                            label=str(ap_time[i]),
                        )
                        for i in TimestampValue
                    ],
                    active=0,
                    transition=dict(duration=300),
                    x=0,  # Slider position
                    xanchor="left",
                    y=0,
                    bgcolor="#FFA500",
                    yanchor="top",
                )
            ]
            # Add slider to layout
            fig.update_layout(
                dragmode="pan",
                title="Parking Box and Delimiters visualization",
                showlegend=True,
                xaxis=dict(range=[(global_x_min - 16), (global_x_max + 14)]),
                yaxis=dict(range=[(global_y_min - 4), (global_y_max + 4)]),
                sliders=sliders,
                height=1000,
                xaxis_title="Time [s]",
                updatemenus=[
                    dict(
                        type="buttons",
                        showactive=False,
                        direction="left",
                        y=-0.2,  # Adjust this value to position the buttons below the slider
                        x=0.5,  # Center the buttons horizontally (optional)
                        xanchor="center",  # Anchor to the center of the button container
                        yanchor="top",  # Anchor to the top of the button container
                        buttons=[
                            dict(
                                label="Play",
                                method="animate",
                                args=[None, dict(frame=dict(duration=500, redraw=True), fromcurrent=True)],
                            ),
                            # args=[None, dict(frame=dict(duration=500, redraw=True), fromcurrent=True)]
                            dict(
                                label="Pause",
                                method="animate",
                                args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")],
                            ),
                        ],
                    )
                ],
            )
            fig.update_layout(
                modebar=dict(
                    bgcolor="rgba(255, 255, 255, 0.8)",  # Optional: background color for mode bar
                    activecolor="#FFA500",  # Optional: active color for mode bar buttons
                )
            )

            signal_fig = go.Figure()
            signal_fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=df[SISignals.Columns.AP_STATE].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[SISignals.Columns.AP_STATE],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>" f"AP State: {ft_helper.ap_state_dict(state)}"
                        for idx, state in enumerate(df[SISignals.Columns.AP_STATE].values.tolist())
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

            plots.append(fig)

            plots.append(signal_fig)
            # plots.append(sig_sum)

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)

            """Add the data in the table from Functional Test Filter Results"""
            additional_results_dict = {
                "Verdict": {"value": test_result.title(), "color": get_color(test_result)},
                "Mean misalignment distance [m]": {
                    "value": (
                        round(sum(missalignment_value_list) / len(missalignment_value_list), 2)
                        if missalignment_value_list
                        else 0
                    )
                },
            }
            self.result.details["Additional_results"] = additional_results_dict
        except Exception as err:
            print(str(err))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies(
    "ReqId_1405868",
    r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_9tw5jzpwEe6GONELpfdJ2Q&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
@testcase_definition(
    name="SI Parking box detection between static object and a delimiter.",
    description="If the bounding feature on one side (only) of a parking box is a parking marking, only the parking line marking shall be used for the road side alignment of the parking box.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FMD_CBo-8DpwEe6GONELpfdJ2Q&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
@register_inputs("/Playground_2/TSF-Debug")
class SI_TC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SI_TestStep,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to

    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.

    """
    # test_bsigs = r"D:\reporting-ui\workspace\workspace\pl_parking\recordings\SI_recc\erg_dana_new_23_09\PFS_FusionAndTracking_pm-ps.erg"

    debug(
        SI_TC,
        # test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
        kpi_report=False,
        dev_report=True,
    )

    _log.debug("All done.")


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"

    out_folder = working_directory / "out"

    main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)
