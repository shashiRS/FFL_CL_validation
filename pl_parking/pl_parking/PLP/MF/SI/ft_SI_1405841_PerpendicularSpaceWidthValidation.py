#!/usr/bin/env python3
"""
Check if there are two parking markings with appropriately sized free space between them,
a parking box is defined covering the entire width of that free space.
"""

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
    DATA_NOK,
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
from pl_parking.PLP.MF.constants import (
    ConstantsSI as threshold,
)
from pl_parking.PLP.MF.constants import (
    ConstantsTrajpla,
    DrawCarLayer,
    PlotlyTemplate,
)
from pl_parking.PLP.MF.SI import ft_helper

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

"""any test must have a specific and UNIQUE alias as it will contain a data frame
with all the signals for a test script"""
READER_NAME = "SI_PerpendicularSpaceWidthValidation"
signals_obj = SISignals()


@teststep_definition(
    name="Check for SI_PerpendicularSpaceWidthValidation",
    description="Check if there are two parking markings with appropriately sized free space between them,"
    "a parking box is defined covering the entire width of that free space.",
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(READER_NAME, SISignals)
class SI_PerpendicularSpaceWidthValidation(TestStep):
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
            num_valid_pb = read_data[SISignals.Columns.NUMVALIDPARKINGBOXES_NU] != 0

            new_collected_info = ft_helper.process_data_initial(read_data[num_valid_pb])
            df = read_data.as_plain_df

            df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
            ap_state = df[SISignals.Columns.AP_STATE]
            ego_x = df[signals_obj.Columns.EGO_POS_X]
            ego_y = df[signals_obj.Columns.EGO_POS_Y]
            ap_time = df[SISignals.Columns.TIME].values.tolist()
            pb_signal_df = pd.DataFrame()
            sig_sum = {
                "Timestamp [s]": [],
                "Space between delimiter width [m]": [],
                "Parking spot dimensions [m]": [],
                "Detection details": [],
                "Result": [],
            }
            table_remark = f"Check when the number of valid parking boxes increases <b>(from signal {signals_obj._properties[SISignals.Columns.NUMVALIDPARKINGBOXES_NU][0]})</b> if the width of space between delimiters(from signals <b>pclOutput.delimiters._%_ )</b> has the same dimensions \
        from detected parking slots found in between the delimiters (from signal <b>parkingBoxPort.parkingBoxes_% )</b> <br><br>"
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
            df[SISignals.Columns.PARKING_SCENARIO_0]
            num_valid_pb = df[signals_obj.Columns.NUMVALIDPARKINGBOXES_NU]

            mask_apstate_park_scan_in = (ap_state == ConstantsTrajpla.AP_AVG_ACTIVE_IN) | (
                ap_state == ConstantsTrajpla.AP_SCAN_IN
            )

            mask_num_valid_pb = (
                num_valid_pb[mask_apstate_park_scan_in].rolling(2).apply(lambda x: x[0] < x[1], raw=True)
            )
            numValidPbTimestamps = [row for row, val in mask_num_valid_pb.items() if val == 1]

            # Combine masks to get the final mask with valid values
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
                if new_collected_info[timestamp_val].get("marker_match", "") == "marker_only":
                    for park_box_id in new_collected_info[timestamp_val]["markers"].keys():
                        # Check if the state of AP is Park in or Scan in
                        # use different threshold for each state
                        the_state_of_ap = new_collected_info[timestamp_val]["ap_state"]
                        max_perp_park_threshold = (
                            threshold.MAX_PERP_WDTH_PARK_IN
                            if the_state_of_ap == ConstantsTrajpla.AP_AVG_ACTIVE_IN
                            else threshold.MAX_PERP_WDTH_SCAN_IN
                        )

                        AC_width_delimiter = new_collected_info[timestamp_val]["delimiter_width_value"][park_box_id]
                        # is_whole_delim_area_covered_bool = (AC_width_pb == AC_width_delimiter and overlap_percentage >= 99.6)

                        is_wide_enough_bool = AC_width_delimiter > threshold.MIN_WDTH_PERP
                        is_wider_than_min_parallel_bool = AC_width_delimiter > threshold.MIN_LEN_PARALLEL
                        is_wider_than_max_perp_bool = (
                            AC_width_delimiter > threshold.MAX_PERP_WDTH_PARK_IN
                            if the_state_of_ap == ConstantsTrajpla.AP_AVG_ACTIVE_IN
                            else AC_width_delimiter > threshold.MAX_PERP_WDTH_SCAN_IN
                        )
                        if is_wide_enough_bool and not is_wider_than_min_parallel_bool:
                            new_collected_info[timestamp_val]["description"][
                                park_box_id
                            ] += "<b>There is no detection from SI.</b><br>"
                            if is_wide_enough_bool and not is_wider_than_max_perp_bool:
                                new_collected_info[timestamp_val]["description"][
                                    park_box_id
                                ] += f"Wide enough to fit a perpendicular parking space (between <b>{threshold.MIN_WDTH_PERP}</b> and <b>{max_perp_park_threshold} [m]</b>).\
                                The car was in Apstate {ft_helper.ap_state_dict(the_state_of_ap)}."
                            if is_wider_than_max_perp_bool and not is_wider_than_min_parallel_bool:
                                new_collected_info[timestamp_val]["description"][
                                    park_box_id
                                ] += f"Wider than the maximum width for a perpendicular parking space(larger than <b>{max_perp_park_threshold} [m]</b>)\
                                    but not wide enough to fit a parallel parking space (smaller than <b>{threshold.MIN_LEN_PARALLEL} [m]</b>).\
                                    The car was in Apstate {ft_helper.ap_state_dict(the_state_of_ap)}"
                            new_collected_info[timestamp_val]["verdict"][park_box_id] = "FAIL"

                        elif not is_wide_enough_bool:
                            new_collected_info[timestamp_val]["verdict"][park_box_id] = "PASS"
                            new_collected_info[timestamp_val]["description"][
                                park_box_id
                            ] += f"<b>This slot was not detected</b><br>Smaller than the minimum space for a perpendicular parking space (greater than <b>{threshold.MIN_WDTH_PERP} [m]</b>).\
                                The car was in Apstate {ft_helper.ap_state_dict(the_state_of_ap)}"
                        else:
                            new_collected_info[timestamp_val]["verdict"][park_box_id] = "PASS"
                            new_collected_info[timestamp_val]["description"][
                                park_box_id
                            ] += f"<b>This slot was not detected</b><br>Wider than the minimum width to fit a parallel parking space (greater than <b>{threshold.MIN_LEN_PARALLEL} [m]</b>).\
                                 The car was in Apstate {ft_helper.ap_state_dict(the_state_of_ap)}"

                if new_collected_info[timestamp_val].get("marker_match", "") == "marker_pb":
                    for park_box_id in new_collected_info[timestamp_val]["pb_with_marker_match"]:

                        AC_width_delimiter = new_collected_info[timestamp_val]["delimiter_width_value"][park_box_id]
                        AC_width_pb = new_collected_info[timestamp_val]["parking_box_width_value"][park_box_id]
                        #overlap_percentage = new_collected_info[timestamp_val]["overlap_percentage"][park_box_id]
                        # Check if the state of AP is Park in or Scan in
                        # use different threshold for each state
                        the_state_of_ap = new_collected_info[timestamp_val]["ap_state"]
                        max_perp_park_threshold = (
                            threshold.MAX_PERP_WDTH_PARK_IN
                            if the_state_of_ap == ConstantsTrajpla.AP_AVG_ACTIVE_IN
                            else threshold.MAX_PERP_WDTH_SCAN_IN
                        )
                        is_whole_delim_area_covered_bool = ( round((AC_width_delimiter-AC_width_pb),2) >= 0 #
                            #AC_width_pb == AC_width_delimiter #and overlap_percentage >= 99.6
                            )
                        is_wide_enough_bool = AC_width_delimiter > threshold.MIN_WDTH_PERP

                        is_wider_than_max_perp_bool = (
                            AC_width_delimiter > threshold.MAX_PERP_WDTH_PARK_IN
                            if the_state_of_ap == ConstantsTrajpla.AP_AVG_ACTIVE_IN
                            else AC_width_delimiter > threshold.MAX_PERP_WDTH_SCAN_IN
                        )
                        if is_wide_enough_bool and not is_wider_than_max_perp_bool:
                            new_collected_info[timestamp_val]["description"][
                                park_box_id
                            ] += f"Wide enough to fit a perpendicular parking space (between <b>{threshold.MIN_WDTH_PERP}</b> and <b>{max_perp_park_threshold} [m]</b>).\
                            The car was in Apstate {ft_helper.ap_state_dict(the_state_of_ap)}."
                            if is_whole_delim_area_covered_bool:
                                new_collected_info[timestamp_val]["verdict"][park_box_id] = "PASS"
                            else:
                                new_collected_info[timestamp_val]["description"][park_box_id] = (
                                    "<b>The parking slot is not fully matching the space between the delimiters</b>.<br>"
                                    + new_collected_info[timestamp_val]["description"][park_box_id]
                                )
                                new_collected_info[timestamp_val]["verdict"][park_box_id] = "FAIL"
                        elif not is_wide_enough_bool:
                            new_collected_info[timestamp_val]["verdict"][park_box_id] = "FAIL"
                            new_collected_info[timestamp_val]["description"][
                                park_box_id
                            ] += f"<b>This slot was not supposed to be detected</b><br>Smaller than the minimum space for a perpendicular parking space (greater than <b>{threshold.MIN_WDTH_PERP} [m].</b>)\
                                The car was in Apstate {ft_helper.ap_state_dict(the_state_of_ap)}"
                            new_collected_info[timestamp_val]["verdict"][park_box_id] = "FAIL"
                            new_collected_info[timestamp_val]["description"][
                                park_box_id
                            ] += f"<b>This slot was not supposed to be detected</b><br>Smaller than the minimum space for a perpendicular parking space (smaller than <b>{threshold.MIN_WDTH_PERP} [m].</b>)\
                                The car was in Apstate {ft_helper.ap_state_dict(the_state_of_ap)}"

                        else:
                            new_collected_info[timestamp_val]["verdict"][park_box_id] = "FAIL"
                            new_collected_info[timestamp_val]["description"][
                                park_box_id
                            ] += f"<b>This slot was not supposed to be detected</b><br> Wider than the maximum width for a perpendicular parking space(larger than <b>{max_perp_park_threshold} [m].</b>)\
                                The car was in Apstate {ft_helper.ap_state_dict(the_state_of_ap)}"
                            new_collected_info[timestamp_val]["verdict"][park_box_id] = "FAIL"
                            new_collected_info[timestamp_val]["description"][
                                park_box_id
                            ] += f"<b>This slot was not supposed to be detected</b><br>Wider than the maximum width for a perpendicular parking space(larger than <b>{max_perp_park_threshold} [m].</b>)\
                                The car was in Apstate {ft_helper.ap_state_dict(the_state_of_ap)}"

            res = [val["verdict"][x] for val in new_collected_info.values() for x in val["verdict"].keys()]
            if res:
                if all([x == "PASS" for x in res]):
                    test_result = fc.PASS
                    self.result.measured_result = TRUE
                    for ts in numValidPbTimestamps:
                        for pb_id in new_collected_info[ts]["pb"].keys():

                            sig_sum["Timestamp [s]"].append(new_collected_info[ts]["ts"])
                            sig_sum["Space between delimiter width [m]"].append(
                                new_collected_info[ts]["delim_width"][pb_id]
                            )
                            sig_sum["Parking spot dimensions [m]"].append(new_collected_info[ts]["pb_width"][pb_id])
                            sig_sum["Detection details"].append(new_collected_info[ts]["description"][pb_id])
                            sig_sum["Result"].append(
                                ft_helper.get_result_color(new_collected_info[ts]["verdict"][pb_id])
                            )
                    sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                else:
                    test_result = fc.FAIL
                    self.result.measured_result = FALSE

                    for _, val in new_collected_info.items():

                        for pb_id in val["pb"].keys():
                            # if val["verdict"][pb_id] == "FAIL":
                            sig_sum["Timestamp [s]"].append(val["ts"])
                            sig_sum["Space between delimiter width [m]"].append(val["delim_width"][pb_id])
                            sig_sum["Parking spot dimensions [m]"].append(val["pb_width"][pb_id])
                            sig_sum["Detection details"].append(val["description"][pb_id])
                            sig_sum["Result"].append(ft_helper.get_result_color(val["verdict"][pb_id]))
                    sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                    sig_sum = ft_helper.create_hidden_table(sig_sum)
            else:
                test_result = fc.NOT_ASSESSED
                self.result.measured_result = DATA_NOK
                sig_sum = ({"Evaluation not possible": "No valid parking boxes found"},)
                sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)

            # new_collected_info = {k:v for k,v in new_collected_info.items() if k not in to_be_removed}
            TimestampValue = [list(read_data.index).index(i) for i in list(new_collected_info.keys())]
            for _, v in new_collected_info.items():
                for x in range(len(pb_col_with_values)):
                    if x not in list(v["pb"].keys()):
                        v["pb"].setdefault(x, [(None, None), (None, None), (None, None), (None, None), (None, None)])
                    if x not in list(v["intersection"].keys()):
                        v["intersection"].setdefault(
                            x, [(None, None), (None, None), (None, None), (None, None), (None, None)]
                        )
                    if x not in list(v["verdict"].keys()):
                        v["verdict"].setdefault(x, "FAIL")
                    if x not in list(v["delim_width"].keys()):
                        v["delim_width"].setdefault(x, 0)
                    if x not in list(v["pb_width"].keys()):
                        v["pb_width"].setdefault(x, 0)
                    if x not in list(v["description"].keys()):
                        v["description"].setdefault(x, "Unknown classification")
                    if x not in list(v["markers"].keys()):
                        v["markers"].setdefault(
                            x,
                            {
                                "id": x,
                                "coordinates": [
                                    [(None, None), (None, None), (None, None), (None, None)],
                                    [(None, None), (None, None), (None, None), (None, None)],
                                ],
                            },
                        )
                    if x not in list(v["intersection"].keys()):
                        v["intersection"].setdefault(
                            x, [(None, None), (None, None), (None, None), (None, None), (None, None)]
                        )
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
                # new_origin_yaw = np.rad2deg(new_origin_yaw)
                # car_right_windshield,lateral_trims,back_right_trim = SlotOffer.draw_car(new_origin_x, new_origin_y)
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
                            # line=dict(color="red" if val["verdict"][pb_id] == "FAIL" else "green"),
                            fill="toself",  # Fill the polygon
                            fillcolor=ft_helper.get_slot_color(val["verdict"][pb_id]),
                            # fillcolor='rgba(255, 0, 0, 0.3)' if val["verdict"][pb_id] == "FAIL" else\
                            #         "rgba(0, 255, 0, 0.3)" if val["verdict"][pb_id] == "PASS" else "rgba(239, 239, 240, 0.3)",  # Semi-transparent red fill
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
                    for _, val_coords in val["intersection"].items():
                        x_coords_box, y_coords_box = zip(*val_coords)
                        if not val_coords:
                            val_coords = [(None, None), (None, None), (None, None), (None, None), (None, None)]
                        if origin_reset:
                            val_coords_to_plot = ft_helper.transform_coordinates_with_new_origin(
                                old_origin, val_coords
                            )
                            x_coords_box_to_plot, y_coords_box_to_plot = zip(*val_coords_to_plot)
                        else:
                            x_coords_box_to_plot, y_coords_box_to_plot = x_coords_box, y_coords_box
                        is_intersect = False
                        if x_coords_box[0]:
                            is_intersect = True
                        intersect = go.Scatter(
                            x=x_coords_box_to_plot,
                            y=y_coords_box_to_plot,
                            showlegend=True if is_intersect else False,
                            mode="markers+lines",
                            visible="legendonly",
                            line=dict(color="blue"),
                            # line=dict(color="red" if val["verdict"][pb_id] == "FAIL" else "green"),
                            fill="toself",  # Fill the polygon
                            fillcolor="blue",
                            # fillcolor='rgba(255, 0, 0, 0.3)' if val["verdict"][pb_id] == "FAIL" else\
                            #         "rgba(0, 255, 0, 0.3)" if val["verdict"][pb_id] == "PASS" else "rgba(239, 239, 240, 0.3)",  # Semi-transparent red fill
                            name="Intersection between parking box and delimiters",
                            # text=[f"Timestamp: {val['ts']}<br>"
                            #         f"X: {x_coords_box[x]}<br>"
                            #         f"Y: {ycoord}" for x, ycoord in enumerate(y_coords_box)],
                            #     hoverinfo="text",
                        )

                        # Add the parking box trace to the figure, then add to frame_data
                        if first_frame:
                            fig.add_trace(intersect)
                            frame_data.append(intersect)
                        else:
                            frame_data.append(intersect)
                for pb__id, marker_info in val["markers"].items():
                    is_delim_found = True
                    delim_id_counter = 0
                    for marking in marker_info["coordinates"]:
                        x_coords, y_coords = zip(*marking)
                        if origin_reset:
                            marking_to_plot = ft_helper.transform_coordinates_with_new_origin(old_origin, marking)
                            x_coords_to_plot, y_coords_to_plot = zip(*marking_to_plot)
                        else:
                            x_coords_to_plot, y_coords_to_plot = x_coords, y_coords
                        delim_str = "No delimiter"
                        try:
                            delim_str = f'{marker_info["id"].split("_")[delim_id_counter]} for PB {pb__id}'
                            if delim_id_counter == 0:
                                delim_str = "Delimiter for AB side : " + delim_str
                            else:
                                delim_str = "Delimiter for CD side : " + delim_str
                            global_x_min = min(global_x_min, min(x_coords_to_plot))
                            global_x_max = max(global_x_max, max(x_coords_to_plot))
                            global_y_min = min(global_y_min, min(y_coords_to_plot))
                            global_y_max = max(global_y_max, max(y_coords_to_plot))
                        except Exception:
                            is_delim_found = False
                        delim_id_counter += 1
                        trace_marking = go.Scatter(
                            x=x_coords_to_plot,
                            y=y_coords_to_plot,
                            mode="lines",
                            showlegend=True if is_delim_found else False,
                            name=delim_str,
                            line=dict(dash="dash", color="black"),
                            text=[
                                f"Timestamp: {val['ts']}<br>" f"X: {x_coords[x]}<br>" f"Y: {y_}"
                                for x, y_ in enumerate(y_coords)
                            ],
                            hoverinfo="text",
                        )
                        # Add the parking box trace to the figure, then add to frame_data
                        if first_frame:
                            fig.add_trace(trace_marking)
                            frame_data.append(trace_marking)
                        else:
                            frame_data.append(trace_marking)

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


@verifies("ReqId_1405841")
@testcase_definition(
    name="SI_PerpendicularSpaceWidthValidationTC",
    description="Check if there are two parking markings with appropriately sized free space between them,"
    "a parking box is defined covering the entire width of that free space.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_9twSiDpwEe6GONELpfdJ2Q&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg&vvc.configuration=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fcm%2Fstream%2F_G3kr8DgnEe6mrdm2_agUYg",
)
@register_inputs("/Playground_2/TSF-Debug")
class SI_PerpendicularSpaceWidthValidationTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SI_PerpendicularSpaceWidthValidation,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to

    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.

    """
    # test_bsigs = r"D:\reporting-ui\workspace\workspace\pl_parking\recordings\SI_recc\erg_dana_new_23_09\PFS_FusionAndTracking_pm-ps.erg"

    debug(
        SI_PerpendicularSpaceWidthValidationTC,
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
