"""Validate if SI does not detect parking boxes when the ego vehicle's velocity is higher than AP_G_V_SCANNING_THRESH_OFF_MPS"""

import tempfile
from pathlib import Path

"""import libraries"""
import logging
import os
import sys

import pandas as pd
import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

"""imports from tsf core"""
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

"""imports from current repo"""
from tsf.core.utilities import debug

import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import (
    MfCustomTeststepReport,
    SISignals,
    build_html_table,
    get_color,
)
from pl_parking.PLP.MF.constants import ConstantsSI, ConstantsTrajpla, DrawCarLayer, PlotlyTemplate
from pl_parking.PLP.MF.SI import ft_helper

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "ParkingBoxDetection_High_Velocity"
signals_obj = SISignals()


@teststep_definition(
    step_number=1,
    name="Check for SI ParkingBoxDetection_High_Velocity",
    description="This test step checks if SI does not detect parking boxes when the ego vehicle's velocity is higher than AP_G_V_SCANNING_THRESH_OFF_MPS",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SISignals)
class ParkingBoxDetection_High_Velocity(TestStep):
    """Test Step for validating parking box orientation against parking line markings."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step."""
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

        plots = []
        pb_signal_df = pd.DataFrame()

        try:
            plots = []
            read_data = self.readers[SIGNAL_DATA]
            test_result = fc.FAIL
            self.result.measured_result = FALSE
            df = read_data.as_plain_df

            df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
            ap_state = df[SISignals.Columns.AP_STATE]
            ego_x = df[SISignals.Columns.EGO_POS_X]
            ego_y = df[SISignals.Columns.EGO_POS_Y]
            ego_yaw = df[SISignals.Columns.EGO_POS_YAW]
            ego_velocity = df[SISignals.Columns.VELOCITY]
            ap_time = df[SISignals.Columns.TIME].values.tolist()

            pb_signal_df = pd.DataFrame()

            ap_time = [round(i, 3) for i in ap_time]

            pb_count = len([x for x in list(df.columns) if SISignals.Columns.PB_SLOTCORDINATES_FRONTLEFT_X in x])
            # Combine all coordinates into a single list for each parking box
            for i in range(pb_count):
                pb_signal_df[SISignals.Columns.PARKBOX_COORDINATES_LIST.format(i)] = df[
                    [x.format(i) for x in ft_helper.combined_list_for_all_pb]
                ].apply(lambda row: row.values.tolist(), axis=1)

            pb_col_with_values = [col for col in pb_signal_df.columns]
            pb_signal_df = pb_signal_df[pb_col_with_values]

            mask_high_velocity = ego_velocity >= ConstantsSI.AP_G_V_SCANNING_THRESH_OFF_MPS
            mask_final = pb_signal_df[mask_high_velocity]

            filtered_timestamps = list(mask_final.index)
            # Create a dictionary to store the collected data
            collect_data_dict = {
                ts: {
                    "pb": {},
                    "ts": ap_time[list(df.index).index(ts)],
                    "ap_state": ap_state.loc[ts],
                    "velocity": ego_velocity.loc[ts],
                    "verdict": {},
                    "ego_vehicle": [(ego_x.loc[ts], ego_y.loc[ts], ego_yaw.loc[ts])],
                    "description": {},
                }
                for ts in filtered_timestamps
            }

            for timestamp_val in filtered_timestamps:

                pb_from_ts = {x: [(0.0, 0.0)] * 4 for x in range(len(pb_col_with_values))}
                for i, col_name in enumerate(pb_col_with_values):
                    pb_coords = pb_signal_df[col_name].loc[timestamp_val]
                    vertices_pb = list(zip(pb_coords[::2], pb_coords[1::2]))
                    pb_from_ts[i] = vertices_pb

                if pb_from_ts:
                    for ids in pb_from_ts.keys():
                        park_box_id = list(pb_from_ts.keys())[ids]
                        vertices_pb = pb_from_ts[park_box_id]
                        collect_data_dict[timestamp_val]["pb"][park_box_id] = [
                            vertices_pb[0],
                            vertices_pb[1],
                            vertices_pb[3],
                            vertices_pb[2],
                            vertices_pb[0],
                        ]
                        collect_data_dict[timestamp_val]["description"][park_box_id] = ""
                        collect_data_dict[timestamp_val]["verdict"][park_box_id] = "Unknown"
            ts_to_be_removed = []

            for ts, val in collect_data_dict.items():

                if not val["pb"].keys():
                    ts_to_be_removed.append(ts)

            new_collected_info = {k: v for k, v in collect_data_dict.items() if k not in ts_to_be_removed}

            sig_sum = {
                "Timestamp [s]": [],
                "Velocity [m/s]": [],
                "description": [],
                "Result": [],
            }

            table_remark = f"When the ego vehicle has a velocity higher than {ConstantsSI.AP_G_V_SCANNING_THRESH_OFF_MPS}, \
                        the SceneInterpretation shall not detect new parking boxes. \
                        The SceneInterpretation shall not provide the already detected parking boxes any more until \
                        the ego velocity drops below {ConstantsSI.AP_G_V_SCANNING_THRESH_OFF_MPS}."

            origin_reset = False
            # Check if the origin of the ego vehicle resets
            if any(ap_state == ConstantsTrajpla.AP_AVG_ACTIVE_IN):
                origin_reset = True
                mask_reset_ego = ego_x.rolling(2).apply(lambda x: x[0] > x[1] and round(x[1]) == 0, raw=True)

                index_ego_after_reset = [row for row, val in mask_reset_ego.items() if val == 1]
                index_ego_after_reset = index_ego_after_reset[0]
                index_of_ego_before_reset = list(df.index).index(index_ego_after_reset) - 1

                old_origin = (ego_x.iloc[index_of_ego_before_reset], ego_y.iloc[index_of_ego_before_reset])
            else:
                index_ego_after_reset = -1

            ap_state = ap_state.values.tolist()
            for timestamp_val in new_collected_info.keys():
                for parking_box_id in new_collected_info[timestamp_val]["pb"]:
                    the_state_of_ap = new_collected_info[timestamp_val]["ap_state"]
                    new_collected_info[timestamp_val]["description"][parking_box_id] += (
                        f"Ego velocity is higher than {ConstantsSI.AP_G_V_SCANNING_THRESH_OFF_MPS}<br>"
                        f"The car was in Apstate {ft_helper.ap_state_dict(the_state_of_ap)}.<br>"
                    )
                    if any(coord != (0.0, 0.0) for coord in new_collected_info[timestamp_val]["pb"][parking_box_id]):
                        new_collected_info[timestamp_val]["verdict"][parking_box_id] = "FAIL"
                        new_collected_info[timestamp_val]["description"][
                            parking_box_id
                        ] += "There is a parking box detected.<br>"
                    else:
                        new_collected_info[timestamp_val]["verdict"][parking_box_id] = "PASS"
                        new_collected_info[timestamp_val]["description"][
                            parking_box_id
                        ] += "There is no parking box detected.<br>"

            res = [val["verdict"][x] for val in new_collected_info.values() for x in val["verdict"].keys()]
            if res:
                if all([x == "PASS" for x in res]):
                    test_result = fc.PASS
                    self.result.measured_result = TRUE
                    for ts in new_collected_info.keys():
                        for pb_id in new_collected_info[ts]["pb"].keys():
                            if new_collected_info[ts]["ts"] in sig_sum["Timestamp [s]"]:
                                continue
                            else:
                                sig_sum["Timestamp [s]"].append(new_collected_info[ts]["ts"])
                                sig_sum["Velocity [m/s]"].append(new_collected_info[ts]["velocity"])
                                sig_sum["description"].append(new_collected_info[ts]["description"][pb_id])
                                sig_sum["Result"].append(
                                    ft_helper.get_result_color(new_collected_info[ts]["verdict"][pb_id])
                                )
                    sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                else:
                    test_result = fc.FAIL
                    self.result.measured_result = FALSE
                    for _, val in new_collected_info.items():
                        for pb_id in val["pb"].keys():
                            if val["ts"] in sig_sum["Timestamp [s]"]:
                                continue
                            else:
                                sig_sum["Timestamp [s]"].append(val["ts"])
                                sig_sum["Velocity [m/s]"].append(val["velocity"])
                                sig_sum["description"].append(val["description"][pb_id])
                                sig_sum["Result"].append(ft_helper.get_result_color(val["verdict"][pb_id]))
                    sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                    sig_sum = ft_helper.create_hidden_table(sig_sum)
            else:
                test_result = fc.NOT_ASSESSED
                self.result.measured_result = DATA_NOK
                sig_sum = ({"Evaluation not possible": "No valid parking boxes found"},)
                sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)

            TimestampValue = [list(read_data.index).index(i) for i in list(new_collected_info.keys())]
            for _, v in new_collected_info.items():
                for x in range(len(pb_col_with_values)):
                    if x not in list(v["pb"].keys()):
                        v["pb"].setdefault(x, [(None, None), (None, None), (None, None), (None, None), (None, None)])
                    if x not in list(v["verdict"].keys()):
                        v["verdict"].setdefault(x, "FAIL")
                    if x not in list(v["description"].keys()):
                        v["description"].setdefault(x, "Unknown classification")

            fig = go.Figure()
            global_x_min = float("inf")
            global_x_max = float("-inf")
            global_y_min = float("inf")
            global_y_max = float("-inf")
            first_frame = True

            frames = []

            for key, val in new_collected_info.items():
                if val.get("ego_vehicle", None)[0] == (0, 0, 0):
                    continue
                if key == index_ego_after_reset:
                    origin_reset = False
                frame_data = []  # np.rad2deg(val.get('ego_vehicle',None)[0][2])
                new_origin_x, new_origin_y, new_origin_yaw = val.get("ego_vehicle", None)[0]
                if origin_reset:
                    new_origin_x, new_origin_y = ft_helper.transform_coordinates_with_new_origin(
                        old_origin, [(new_origin_x, new_origin_y)]
                    )[0]
                vehicle_plot = DrawCarLayer.draw_car(new_origin_x, new_origin_y, new_origin_yaw)
                car_x = vehicle_plot[0][0]
                car_y = vehicle_plot[0][1]
                vehicle_plot = vehicle_plot[1]

                global_x_min = min(global_x_min, min(car_x))
                global_x_max = max(global_x_max, max(car_x))
                padding = 3  # Padding to ensure the plot fits well on a 16:9 ratio plot
                global_y_min = min(global_y_min, min(car_y) - padding)
                global_y_max = max(global_y_max, max(car_y) + padding)

                if any(coords != (0.0, 0.0) for i in val.get("pb", None) for coords in val["pb"][i]):
                    for pb_id, val_coords in val["pb"].items():
                        x_coords_box, y_coords_box = zip(*val_coords)
                        if origin_reset:
                            val_coords_to_plot = ft_helper.transform_coordinates_with_new_origin(
                                old_origin, val_coords
                            )
                            x_coords_box_to_plot, y_coords_box_to_plot = zip(*val_coords_to_plot)
                        else:
                            x_coords_box_to_plot, y_coords_box_to_plot = x_coords_box, y_coords_box
                        is_pb_found = False
                        if x_coords_box[0]:
                            is_pb_found = True
                            global_x_min = min(global_x_min, min(x_coords_box_to_plot))
                            global_x_max = max(global_x_max, max(x_coords_box_to_plot))
                            global_y_min = min(global_y_min, min(y_coords_box_to_plot))
                            global_y_max = max(global_y_max, max(y_coords_box_to_plot))
                        parking_box_trace = go.Scatter(
                            x=x_coords_box_to_plot,
                            y=y_coords_box_to_plot,
                            showlegend=True if is_pb_found else False,
                            mode="markers+lines",
                            line=dict(color=ft_helper.get_slot_color(val["verdict"][pb_id])),
                            fill="toself",  # Fill the polygon
                            fillcolor=ft_helper.get_slot_color(val["verdict"][pb_id]),
                            name=f"Parking Box {pb_id}",
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

                frames.append(go.Frame(data=frame_data, name=str(new_collected_info[key]["ts"])))

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
                xaxis=dict(range=[(global_x_min - 2), (global_x_max + 2)]),
                yaxis=dict(range=[(global_y_min - 2), (global_y_max + 2)]),
                sliders=sliders,
                height=1000,
                xaxis_title="Time [s]",
                updatemenus=[
                    dict(
                        type="buttons",
                        showactive=False,
                        direction="left",
                        y=-0.2,  # Adjust this value to position the buttons below the slider
                        x=0.5,  # Center the buttons horizontally
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

            signal_fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=df[SISignals.Columns.VELOCITY].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[SISignals.Columns.VELOCITY],
                )
            )
            signal_fig.add_trace(
                go.Scatter(
                    x=[min(ap_time), max(ap_time)],
                    y=[ConstantsSI.AP_G_V_SCANNING_THRESH_OFF_MPS] * 2,
                    mode="lines",
                    line=dict(color="Red", width=2, dash="dash"),
                    name=f"Velocity threshold - AP_G_V_SCANNING_THRESH_OFF_MPS({ConstantsSI.AP_G_V_SCANNING_THRESH_OFF_MPS})",
                )
            )

            signal_fig.layout = go.Layout(
                yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]"
            )
            signal_fig.update_layout(
                PlotlyTemplate.lgt_tmplt,
                title="AP State and Number of Valid Parking Boxes. Velocity included",
            )

            plots.append(fig)

            plots.append(signal_fig)
            plots.append(sig_sum)

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)

            """Add the data in the table from Functional Test Filter Results"""
            additional_results_dict = {
                "Verdict": {"value": test_result.title(), "color": get_color(test_result)},
            }
            self.result.details["Additional_results"] = additional_results_dict
        except Exception as err:
            print(str(err))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("ReqId_1405825")
@testcase_definition(
    name="ParkingBoxDetection_High_Velocity_TC",
    description="Test Case for validating parking box detection with high velocity.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_9twSezpwEe6GONELpfdJ2Q&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36325",
)
@register_inputs("/Playground_2/TSF-Debug")
class ParkingBoxDetection_High_Velocity_TC(TestCase):
    """Test Case for validating parking box detection with high velocity."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            ParkingBoxDetection_High_Velocity,
        ]


def main(data_folder, temp_dir=None, open_explorer=True):
    """Main entry point for debugging the test case."""
    # test_bsigs = r"C:\Users\uif65342\Downloads\SimOutput 4 2 (1)\SISim_UC_Parallel_Empty_Prk_Mrk_Defined.testrun.erg"

    debug(
        ParkingBoxDetection_High_Velocity_TC,
        # test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
    )


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"

    out_folder = working_directory / "out"

    main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)
