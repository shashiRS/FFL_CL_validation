#!/usr/bin/env python3
"""
    The perpendicular parking box shall have a minimum depth of

( {AP_V_LENGTH_M} + {AP_SI_NONPAR_SLOT_MIN_OFFSET_DEPTH_SCAN_M} ) during Scanning Mode  /or/

( {AP_V_LENGTH_M} + {AP_SI_NONPAR_SLOT_MIN_OFFSET_DEPTH_PARK_M} ) during Parking Mode

If the parking space is limited by an obstacle on the curb side, the parking box shall be shifted onto the road up to a maximum road side extension of

( {AP_G_PER_MAX_ROAD_OVERHANG_M} )
"""

# import libraries
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
    PlotlyTemplate,
)
from pl_parking.PLP.MF.SI import ft_helper

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

"""any test must have a specific and UNIQUE alias as it will contain a data frame
with all the signals for a test script"""
READER_NAME = "SI_ParallelParkingMaxDepth"
signals_obj = SISignals()


@teststep_definition(
    step_number=1,
    name="Check for SI_PerpendicularParkingMinDepthObstacle",
    description="Perpendicular parking should have min depth and if obstacle on curb side then PB should be extended on road",
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(READER_NAME, SISignals)
class SI_PerpendicularParkingMinDepthObstacle(TestStep):
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
            df = read_data.as_plain_df

            df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
            ap_state = df[SISignals.Columns.AP_STATE]
            ap_time = df[SISignals.Columns.TIME].values.tolist()

            ###### mine
            ego_x = df[SISignals.Columns.EGO_POS_X]
            ego_y = df[SISignals.Columns.EGO_POS_Y]
            ego_yaw = df[SISignals.Columns.EGO_POS_YAW]

            #### mine end

            pb_signal_df = pd.DataFrame()
            sig_sum = {
                "Timestamp [s]": [],
                "Perpendicular PB depth [m]": [],
                "MIN_DEPTH_PER_PARKING_BOX [m]": [],
                "description": [],
                "Result": [],
            }

            MIN_DEPTH_PER_PARKING_BOX_val_park = threshold.MIN_DEPTH_PER_PARK_M
            MIN_DEPTH_PER_PARKING_BOX_val_Scan = threshold.MIN_DEPTH_PER_SCAN_M
            pb_with_marker_match = {}
            # table_remark = f"The Perpendicular box shall have min depth of <br> {MIN_DEPTH_PER_PARKING_BOX_val_Scan} [m] during Scanning Mode  /or/ {MIN_DEPTH_PER_PARKING_BOX_val_Scan} [m] during Parking Mode  to the curb side edge. <br><br>"
            table_remark = f"The Perpendicular box shall have min depth of <br> {MIN_DEPTH_PER_PARKING_BOX_val_Scan} [m] during Scanning Mode  /or/ {MIN_DEPTH_PER_PARKING_BOX_val_Scan} [m] during Parking Mode  <br>\
            If the parking space is limited by an obstacle on the curb side, the parking box shall be shifted onto the road <br>\
            up to a maximum road side extension of {threshold.AP_G_PER_MAX_ROAD_OVERHANG_M}[m]. <br><br>"
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
            num_valid_pb = df[signals_obj.Columns.NUMVALIDPARKINGBOXES_NU]

            mask_apstate_park_scan_in = (ap_state == ConstantsTrajpla.AP_AVG_ACTIVE_IN) | (
                ap_state == ConstantsTrajpla.AP_SCAN_IN
            )

            mask_num_valid_pb = (
                num_valid_pb[mask_apstate_park_scan_in].rolling(2).apply(lambda x: x[0] < x[1], raw=True)
            )
            m_num_valid_pb = num_valid_pb != 0
            numValidPbTimestamps = [row for row, val in mask_num_valid_pb.items() if val == 1]

            # Combine masks to get the final mask with valid values
            mask_final = (
                pb_signal_df.applymap(lambda x: any(i != 0 for i in x)).any(axis=1)
                & mask_apstate_park_scan_in
                & m_num_valid_pb
            )
            # Apply mask to get the final dataframe

            pb_filtered_df = pb_signal_df[mask_final]

            filtered_timestamps = list(pb_filtered_df.index)
            ap_time = [round(i, 3) for i in ap_time]

            ########## mine
            marker_single_df = pd.DataFrame()
            # Get how many delimiters signals are
            delimiter_count = len(
                [x for x in list(df.columns) if SISignals.Columns.DELIMITERS_STARTPOINTXPOSITION in x]
            )
            for idx in range(delimiter_count):
                # Get each delimiter with it's 4 coordinates into a single list
                marker = [x.format(idx) for x in ft_helper.delimiter_list]
                marker_single_df[SISignals.Columns.DELIMITERS_COORDINATES_LIST.format(idx)] = df[marker].apply(
                    lambda row: row.values.tolist(), axis=1
                )

            mask_apstate_park_scan_in = (ap_state == ConstantsTrajpla.AP_AVG_ACTIVE_IN) | (
                ap_state == ConstantsTrajpla.AP_SCAN_IN
            )

            # Combine masks to get the final mask with valid values
            mask_final = (
                marker_single_df.applymap(lambda x: any(i != 0 for i in x)).any(axis=1) & mask_apstate_park_scan_in
            )

            # total_brake_events = mask_brake_events.sum()
            marker_filtered_df = marker_single_df[mask_final]

            delim_col_with_values = [
                col
                for col in marker_filtered_df.columns
                if not marker_filtered_df[col].apply(ft_helper.is_all_zeros).all()
            ]

            ########## mine end

            # Create a dictionary to store the collected data
            collect_data_dict = {
                ts: {
                    "pb": {},
                    "ts": ap_time[list(df.index).index(ts)],
                    "ap_state": ap_state.loc[ts],
                    "markers": {},
                    "MIN_DEPTH_PER_PARKING_BOX": {},
                    "verdict": {},
                    "pb_depth": {},
                    "obstacle_depth": {},
                    "description": {},
                }
                for ts in filtered_timestamps
            }

            # Transform apstate to list
            ap_state = ap_state.values.tolist()

            static_object_column = [
                col
                for col in list(df.columns)
                if any(stat_obj in col for stat_obj in ft_helper.combine_list_static_object)
            ]
            static_object_df = df[static_object_column]
            static_object_df = static_object_df.loc[:, (static_object_df != 0).any(axis=0)]
            x_columns = sorted([col for col in static_object_df.columns if "array_x_dir" in col])
            y_columns = sorted([col for col in static_object_df.columns if "array_y_dir" in col])
            df_static_obj_vertices = pd.DataFrame(
                {
                    "array_x_y_dir": [
                        list(zip(row[x_columns], row[y_columns])) for _, row in static_object_df.iterrows()
                    ]
                },
                index=static_object_df.index,
            )
            shortest_distance_list = []
            listthreshold_AP_G_PER_MAX_ROAD_OVERHANG_M = []
            # filtered_timestamps=[23600000]
            for timestamp_val in filtered_timestamps:
                pb_with_marker_match.clear()
                # result_delimiter_curb_side = None
                # result_pb_curb_side = None

                delims_from_ts = {x: [] for x in range(len(delim_col_with_values))}
                pb_from_ts = {x: [(0.0, 0.0)] * 4 for x in range(len(pb_col_with_values))}

                for i, col_name in enumerate(pb_col_with_values):
                    pb_coords = pb_signal_df[col_name].loc[timestamp_val]
                    vertices_pb = list(zip(pb_coords[::2], pb_coords[1::2]))
                    pb_from_ts[i] = vertices_pb
                # Remove the parking box with all zeros
                pb_from_ts = {x: y for x, y in pb_from_ts.items() if all(val1 != 0 for val1, val2 in y)}

                for i, col_name in enumerate(delim_col_with_values):
                    delim_coords = marker_single_df[col_name].loc[timestamp_val]
                    delim_coords = ft_helper.transform_odo(
                        delim_coords, ego_x.loc[timestamp_val], ego_y.loc[timestamp_val], ego_yaw.loc[timestamp_val]
                    )

                    delims_from_ts[i] = delim_coords
                delims_from_ts = {x: y for x, y in delims_from_ts.items() if all(val != 0 for val in y)}

                # Keep only keys 0 and 1
                delims_from_ts = {key: value for key, value in delims_from_ts.items() if key in [0, 1]}

                # Step 1: Convert dictionary to a list of tuples (x, y)
                tuples_list_delimiter = []
                # for key, values in delims_from_ts.items():
                for values in delims_from_ts.values():
                    tuples_list_delimiter.append((values[0], values[1]))  # First pair (x1, y1)
                    tuples_list_delimiter.append((values[2], values[3]))  # Second pair (x2, y2)

                # Step 2: Sort the list by y-values (second element of each tuple)
                # sorted_tuples_delimiter = sorted(tuples_list_delimiter, key=lambda t: t[1], reverse=True)
                sorted_tuples_delimiter = sorted(tuples_list_delimiter, key=lambda t: t[1])

                # Step 3: Keep the two smallest y-values
                result_delimiter_curb_side = sorted_tuples_delimiter[:2]

                print(f"at {timestamp_val} result_delimiter_curb_side : {result_delimiter_curb_side}")

                # tuples_list_pb = pb_from_ts[0]

                # # Sort tuples by the y-value (second element of each tuple)
                # sorted_tuples_pb = sorted(tuples_list_pb, key=lambda t: t[1])

                # # Get the tuples with the two smallest y-values
                # result_pb_curb_side = sorted_tuples_pb[:2]
                # Input dictionary
                # data = {
                # 0: [(-7.053142070770264, 1.3088414669036865),
                # (-7.05313777923584, 6.575841903686523),
                # (-4.059944152832031, 1.3088390827178955),
                # (-4.059939384460449, 6.575839042663574)]
                # }

                # Extract the list of tuples
                tuples_list_pb = pb_from_ts[0]

                # Sort tuples by the y-value (second element of each tuple) in descending order
                # sorted_tuples_pb = sorted(tuples_list_pb, key=lambda t: t[1], reverse=True)
                sorted_tuples_pb = sorted(tuples_list_pb, key=lambda t: t[1])

                # Get the tuples with the two largest y-values
                result_pb_curb_side = sorted_tuples_pb[:2]

                print(f"at {timestamp_val} result_pb_curb_side : {result_pb_curb_side}")

                # Combining the lists
                combined_list = result_delimiter_curb_side + result_pb_curb_side

                # Find shortest distance
                shortest_distance, closest_pair = ft_helper.find_shortest_distance(combined_list)

                print(f"at {timestamp_val} Shortest distance: {shortest_distance}")
                print(f"at {timestamp_val} Closest pair: {closest_pair}")
                shortest_distance_list.append(shortest_distance)
                val_thres = threshold.AP_G_PER_MAX_ROAD_OVERHANG_M
                listthreshold_AP_G_PER_MAX_ROAD_OVERHANG_M.append(val_thres)

                if pb_from_ts:

                    park_box_id = list(pb_from_ts.keys())[0]
                    vertices_pb = pb_from_ts[park_box_id]
                    distances_between_pb = ft_helper.quadrilateral_distances(vertices_pb)
                    AB_depth_pb = float(f'{distances_between_pb.get("AB",0):.2f}')

                    sta_obj_vertices = df_static_obj_vertices.loc[timestamp_val][0]
                    distance_between_stat_obj = ft_helper.quadrilateral_distances(sta_obj_vertices)
                    DA_depth_stat_obj = float(f'{distance_between_stat_obj.get("DA", 0): .2f}')

                    collect_data_dict[timestamp_val]["pb_depth"][park_box_id] = AB_depth_pb
                    collect_data_dict[timestamp_val]["obstacle_depth"][park_box_id] = DA_depth_stat_obj

                    collect_data_dict[timestamp_val]["MIN_DEPTH_PER_PARKING_BOX"][
                        park_box_id
                    ] = MIN_DEPTH_PER_PARKING_BOX_val_park

                    if AB_depth_pb < MIN_DEPTH_PER_PARKING_BOX_val_park:
                        collect_data_dict[timestamp_val]["verdict"][park_box_id] = "FAIL"
                        collect_data_dict[timestamp_val]["description"][
                            park_box_id
                        ] = f"perpendicular parking box depth is {AB_depth_pb} which is less than the minimum depth of\
                             {MIN_DEPTH_PER_PARKING_BOX_val_park}."

                    elif shortest_distance > threshold.AP_G_PER_MAX_ROAD_OVERHANG_M:
                        collect_data_dict[timestamp_val]["verdict"][park_box_id] = "FAIL"
                        collect_data_dict[timestamp_val]["description"][
                            park_box_id
                        ] = f"size of the obstacle is {DA_depth_stat_obj}m and extension of the perpendicular parking box is {shortest_distance} \
                         to road side exceeds {threshold.AP_G_PER_MAX_ROAD_OVERHANG_M} limit."
                    else:
                        collect_data_dict[timestamp_val]["verdict"][park_box_id] = "PASS"
                        collect_data_dict[timestamp_val]["description"][
                            park_box_id
                        ] = f"Perpendicular Parking box having depth <b>{AB_depth_pb}[m]</b> which is greater than minimum depth of\
                             <b>{MIN_DEPTH_PER_PARKING_BOX_val_park:.3f}[m]</b> and there is obstacle of size <b>{DA_depth_stat_obj}[m]</b>\
                            on curb side and extension of the PB on road side is <b>{shortest_distance: .2f}[m]</b> which is within max PB road side extension of <b>{threshold.AP_G_PER_MAX_ROAD_OVERHANG_M}[m]</b>"

            res = [val["verdict"][x] for val in collect_data_dict.values() for x in val["verdict"].keys()]
            if res and pb_from_ts:
                res = all([x == "PASS" for x in res])
                if res:
                    test_result = fc.PASS
                    self.result.measured_result = TRUE
                    for ts in numValidPbTimestamps:

                        for pb_id in collect_data_dict[ts]["pb_depth"].keys():
                            sig_sum["Timestamp [s]"].append(collect_data_dict[ts]["ts"])
                            sig_sum["Perpendicular PB depth [m]"].append(collect_data_dict[ts]["pb_depth"][pb_id])
                            sig_sum["MIN_DEPTH_PER_PARKING_BOX [m]"].append(
                                collect_data_dict[ts]["MIN_DEPTH_PER_PARKING_BOX"][pb_id]
                            )
                            sig_sum["description"].append(collect_data_dict[ts]["description"][pb_id])
                            sig_sum["Result"].append(
                                ft_helper.get_result_color(collect_data_dict[ts]["verdict"][pb_id])
                            )

                    sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                    plots.append(sig_sum)

                else:
                    test_result = fc.FAIL
                    self.result.measured_result = FALSE
                    for ts, val in collect_data_dict.items():
                        if ts:
                            for pb_id in val["pb_depth"].keys():
                                if val["verdict"][pb_id] == "FAIL":
                                    sig_sum["Timestamp [s]"].append(val["ts"])
                                    sig_sum["Perpendicular PB depth [m]"].append(val["pb_depth"][pb_id])
                                    sig_sum["MIN_DEPTH_PER_PARKING_BOX [m]"].append(
                                        val["MIN_DEPTH_PER_PARKING_BOX"][pb_id]
                                    )
                                    sig_sum["description"].append(val["description"][pb_id])
                                    sig_sum["Result"].append(ft_helper.get_result_color(val["verdict"][pb_id]))

                    sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                    sig_sum = ft_helper.create_hidden_table(
                        sig_sum, 1, button_text="Show Table Perpendicular_Parking_depth information"
                    )
                    plots.append(sig_sum)

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

                plots.append(signal_fig)

                signal_fig = go.Figure()
                signal_fig.add_trace(
                    go.Scatter(
                        x=ap_time,
                        y=shortest_distance_list,
                        mode="lines",
                        name="shifted onto the road side",
                    )
                )
                signal_fig.add_trace(
                    go.Scatter(
                        x=ap_time,
                        y=listthreshold_AP_G_PER_MAX_ROAD_OVERHANG_M,
                        mode="lines",
                        name="Maximum road side extension",
                    )
                )

                signal_fig.layout = go.Layout(
                    yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]"
                )
                signal_fig.update_layout(
                    PlotlyTemplate.lgt_tmplt,
                    title="Maximum road side extension along with Parking box shifted onto the road side",
                )

                plots.append(signal_fig)

                #### mine end
            else:
                test_result = fc.NOT_ASSESSED
                self.result.measured_result = DATA_NOK
                sig_sum = ({"Evaluation not possible": "DATA_NOK"},)
                sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
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
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("ReqId_1405922")
@testcase_definition(
    name="SI_PerpendicularParkingMinDepthObstacleTC",
    description="Perpendicular Parking shall have min depth and if obstacle is present on the curb side then extend Pb on road to max AP_G_PER_MAX_ROAD_OVERHANG_M ",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_9tyHqTpwEe6GONELpfdJ2Q&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/Playground_2/TSF-Debug")
class SI_PerpendicularParkingMinDepthObstacleTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SI_PerpendicularParkingMinDepthObstacle,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to

    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.

    """
    # test_bsigs = r"D:\SI\New_adc5_platform_meta\adc5_platform_meta\modules\parking\mf\mf_sil\tests\SIL\CarMaker\SimOutput\SISim_UC_Perpendicular_Empty_Prk_Obs_Min_Depth.testrun.erg"

    debug(
        SI_PerpendicularParkingMinDepthObstacleTC,
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
