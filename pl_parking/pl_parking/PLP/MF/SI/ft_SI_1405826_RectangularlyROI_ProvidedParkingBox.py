"""The SceneInterpretation shall provide a free parking box until the
longitudinal or lateral distance of the ego vehicle's rear edge to the
closest edge of this parking box increases over {AP_G_SCAN_OFFER_SLOTS_LO_DIST_M}.
"""

import logging
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from shapely.geometry import Polygon

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
from tsf.core.utilities import debug

"""imports from current repo"""
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

SIGNAL_DATA = "ParkingBoxScanZone"
signals_obj = SISignals()


@teststep_definition(
    step_number=1,
    name="Check for SI RectangularlyROI",
    description="This test step checks whether the SI offers a parking box that falls inside the rectangulary ROI",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SISignals)
class RectangularlyROICheck(TestStep):
    """Test Step for validating if parking box is present within the rectangulary ROI."""

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
            # new_collected_info = ft_helper.process_data_GT_without_scanned_pb(read_data)
            df = read_data.as_plain_df
            test_result = fc.FAIL
            self.result.measured_result = FALSE

            df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
            ap_state = df[SISignals.Columns.AP_STATE]
            ego_x = df[SISignals.Columns.EGO_POS_X]
            ego_y = df[SISignals.Columns.EGO_POS_Y]
            ego_yaw = df[SISignals.Columns.EGO_POS_YAW]
            ap_time = df[SISignals.Columns.TIME].values.tolist()

            pb_signal_df = pd.DataFrame()

            ap_time = [round(i, 3) for i in ap_time]

            pb_count = len([x for x in list(df.columns) if SISignals.Columns.PB_SLOTCORDINATES_FRONTLEFT_X in x])
            # Combine all coordinates into a single list for each parking box
            for i in range(pb_count):
                pb_signal_df[SISignals.Columns.PARKBOX_COORDINATES_LIST.format(i)] = df[
                    [x.format(i) for x in ft_helper.combined_list_for_all_pb]
                ].apply(lambda row: row.values.tolist(), axis=1)

            pb_col_with_values = [
                col for col in pb_signal_df.columns if not pb_signal_df[col].apply(ft_helper.is_all_zeros).all()
            ]
            pb_signal_df = pb_signal_df[pb_col_with_values]

            mask_apstate_park_scan_in = (ap_state == ConstantsTrajpla.AP_AVG_ACTIVE_IN) | (
                ap_state == ConstantsTrajpla.AP_SCAN_IN
            )
            mask_final = pb_signal_df[mask_apstate_park_scan_in]

            filtered_timestamps = list(mask_final.index)
            # Create a dictionary to store the collected data
            collect_data_dict = {
                ts: {
                    "pb": {},
                    "ts": ap_time[list(df.index).index(ts)],
                    "ap_state": ap_state.loc[ts],
                    "verdict": {},
                    # "longitudinal_vector": {},
                    # "lateral_vector": {},
                    "RoI": {},
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

                # Remove the parking box with all zeros
                pb_from_ts = {x: y for x, y in pb_from_ts.items() if all(val1 != 0 for val1, val2 in y)}
                if pb_from_ts:
                    for park_box_id in list(pb_from_ts.keys()):
                        # park_box_id = list(pb_from_ts.keys())[i]
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
                "description": [],
                "Result": [],
            }

            table_remark = f"The SceneInterpretation shall provide a free parking box until the longitudinal \
                            or lateral distance of the ego vehicle's rear edge to the closest edge of this \
                            parking box increases over {ConstantsSI.AP_G_SCAN_OFFER_SLOTS_LO_DIST_M}.\
                            This results in a rectangularly shaped region of interest (ROI). \
                            If the parking box falls outside that ROI, it is no longer provided."

            mask_apstate_park_scan_in = (ap_state == ConstantsTrajpla.AP_AVG_ACTIVE_IN) | (
                ap_state == ConstantsTrajpla.AP_SCAN_IN
            )

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
                    ego_x = new_collected_info[timestamp_val]["ego_vehicle"][0][0]
                    ego_y = new_collected_info[timestamp_val]["ego_vehicle"][0][1]
                    ego_yaw = new_collected_info[timestamp_val]["ego_vehicle"][0][2]

                    vertices_pb_list = [
                        list(point) for point in new_collected_info[timestamp_val]["pb"][parking_box_id]
                    ]
                    center_rear_bumper = {
                        "x": (
                            DrawCarLayer.CarCoordinates.sensor_rear_inner_left[0]
                            + DrawCarLayer.CarCoordinates.sensor_rear_inner_right[0]
                        )
                        / 2,
                        "y": (
                            DrawCarLayer.CarCoordinates.sensor_rear_inner_left[1]
                            + DrawCarLayer.CarCoordinates.sensor_rear_inner_right[1]
                        )
                        / 2,
                    }
                    transformed_center_rear_bumper = ft_helper.translate_and_rotate(
                        center_rear_bumper, ego_x, ego_y, ego_yaw
                    )

                    dist = ConstantsSI.AP_G_SCAN_OFFER_SLOTS_LO_DIST_M
                    x, y = transformed_center_rear_bumper["x"], transformed_center_rear_bumper["y"]
                    rectangular_ROI = [
                        (x + dist, y + dist),
                        (x - dist, y + dist),
                        (x - dist, y - dist),
                        (x + dist, y - dist),
                        (x + dist, y + dist),
                    ]

                    new_collected_info[timestamp_val]["RoI"][parking_box_id] = rectangular_ROI

                    parking_slot_polygon = Polygon(vertices_pb_list)
                    rectangular_ROI_polygon = Polygon(rectangular_ROI)
                    intersects_with_roi = parking_slot_polygon.intersects(rectangular_ROI_polygon)

                    if intersects_with_roi:
                        new_collected_info[timestamp_val]["verdict"][parking_box_id] = "PASS"
                        new_collected_info[timestamp_val]["description"][
                            parking_box_id
                        ] = "Parking box is within the rectangulary ROI"
                    else:
                        new_collected_info[timestamp_val]["verdict"][parking_box_id] = "FAIL"
                        new_collected_info[timestamp_val]["description"][
                            parking_box_id
                        ] = "Parking box is outside the rectangulary ROI"

            res = [val["verdict"][x] for val in new_collected_info.values() for x in val["verdict"].keys()]
            if res:
                if all([x == "PASS" for x in res]):
                    for _, val in new_collected_info.items():
                        for pb_id in val["pb"].keys():
                            if val["description"][pb_id] != "":
                                sig_sum["Timestamp [s]"].append(val["ts"])
                                sig_sum["description"].append(val["description"][pb_id])
                                sig_sum["Result"].append(ft_helper.get_result_color(val["verdict"][pb_id]))
                    sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                    test_result = fc.PASS
                    self.result.measured_result = TRUE
                else:
                    for _, val in new_collected_info.items():
                        for pb_id in val["pb"].keys():
                            if val["description"][pb_id] != "":
                                sig_sum["Timestamp [s]"].append(val["ts"])
                                sig_sum["description"].append(val["description"][pb_id])
                                sig_sum["Result"].append(ft_helper.get_result_color(val["verdict"][pb_id]))
                    sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                    sig_sum = ft_helper.create_hidden_table(sig_sum)
                    test_result = fc.FAIL
                    self.result.measured_result = FALSE
            else:
                test_result = fc.NOT_ASSESSED
                self.result.measured_result = DATA_NOK
                sig_sum = {"Evaluation not possible"}
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
                global_y_min = min(global_y_min, min(car_y))
                global_y_max = max(global_y_max, max(car_y))

                # Parking box coordinates for the current frame (if they exist)
                if val.get("pb", None):  # Only create the parking box trace if coordinates exist
                    for pb_id, val_coords in val["pb"].items():
                        x_coords_box, y_coords_box = zip(*val_coords)
                        if origin_reset:
                            val_coords_to_plot = ft_helper.transform_coordinates_with_new_origin(old_origin, val_coords)
                            x_coords_box_to_plot, y_coords_box_to_plot = zip(*val_coords_to_plot)
                        else:
                            x_coords_box_to_plot, y_coords_box_to_plot = x_coords_box, y_coords_box
                        is_pb_found = False
                        if x_coords_box[0]:
                            is_pb_found = True
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

                        # Plot the ROI
                        for i in val["RoI"]:
                            roi_x_coords, roi_y_coords = zip(*val["RoI"][i])
                            global_x_min = min(global_x_min, min(roi_x_coords))
                            global_x_max = max(global_x_max, max(roi_x_coords))
                            global_y_min = min(global_y_min, min(roi_y_coords))
                            global_y_max = max(global_y_max, max(roi_y_coords))
                            roi_trace = go.Scatter(
                                x=roi_x_coords,
                                y=roi_y_coords,
                                mode="markers+lines",
                                line=dict(color="blue", dash="dash"),
                                name="Rectangular ROI",
                                text=[
                                    f"Timestamp: {val['ts']}<br>" f"X: {roi_x_coords[x]}<br>" f"Y: {ycoord}"
                                    for x, ycoord in enumerate(roi_y_coords)
                                ],
                                showlegend=True,
                                fill="toself",
                                fillcolor="rgba(0, 0, 255, 0.1)",  # Adjusted transparency
                            )

                        if first_frame:
                            fig.add_trace(roi_trace)
                            fig.add_trace(parking_box_trace)
                            frame_data.append(parking_box_trace)
                            frame_data.append(roi_trace)
                        else:
                            frame_data.append(parking_box_trace)
                            frame_data.append(roi_trace)

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
                title="Parking Box and GT visualization",
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

            signal_fig.layout = go.Layout(
                yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]"
            )
            signal_fig.update_layout(
                PlotlyTemplate.lgt_tmplt,
                title="AP State and Number of Valid Parking Boxes",
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


@verifies("ReqId_1405826")
@testcase_definition(
    name="RectangularlyROI_TC",
    description="Test Case for validating if the parkingbox is within the rectangulary ROI",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FTX_4cnI8jpwEe6GONELpfdJ2Q&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36325",
)
@register_inputs("/Playground_2/TSF-Debug")
class RectangularlyROI_TC(TestCase):
    """Test Case for validating the offer of a free slot within the scan zone while passing the parking box."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            RectangularlyROICheck,
        ]


def main(data_folder, temp_dir=None, open_explorer=True):
    """Main entry point for debugging the test case."""
    # test_bsigs = r"C:\Users\uif65342\Downloads\SimOutput 4 2 (1)\SISim_UC_Parallel_Empty_Prk_Mrk_Defined.testrun.erg"

    debug(
        RectangularlyROI_TC,
        # test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
    )


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"

    out_folder = working_directory / "out"

    main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)
