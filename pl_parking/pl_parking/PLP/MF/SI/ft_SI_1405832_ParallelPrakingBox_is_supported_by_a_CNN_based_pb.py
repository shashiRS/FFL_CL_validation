"""Test if parking boxes are only pesent on the output in case of a CNN based slot supporting it."""

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
    ConstantsTrajpla,
    PlotlyTemplate,
)
from pl_parking.PLP.MF.SI import ft_helper

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

"""any test must have a specific and UNIQUE alias as it will contain a data frame
with all the signals for a test script"""
READER_NAME = "SI_ParallelPrakingBox_is_supported_by_a_CNN_based_pb"
signals_obj = SISignals()


@teststep_definition(
    step_number=1,
    name="Check for SI_ParallelPrakingBox_is_supported_by_a_CNN_based_pb",
    description="Test if parking boxes are only pesent on the output in case of a CNN based slot supporting it.",
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(READER_NAME, SISignals)
class SI_ParallelPrakingBox_is_supported_by_a_CNN_based_pb(TestStep):
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

            ######### mine

            # ego_x_col = read_data[["envModelPort.egoVehiclePoseForAP.pos_x_m", "timestamp"]]
            # ego_y_col = read_data[["envModelPort.egoVehiclePoseForAP.pos_y_m", "timestamp"]]
            # ego_orientations = read_data[["Ego_pos_yaw", "timestamp"]]

            ###### mine end

            pb_signal_df = pd.DataFrame()
            sig_sum = {
                "Timestamp [s]": [],
                "Parallel PB edges [m]": [],
                "CNN box edges [m]": [],
                "description": [],
                "Result": [],
            }

            # VAL_AP_SI_CNN_ROAD_ALIGN_LIMIT_TO_ROAD_PARA_M = threshold.AP_SI_CNN_ROAD_ALIGN_LIMIT_TO_ROAD_PARA_M
            pb_with_marker_match = {}
            """
            The road side edge of a parallel parking box shall not be moved by more than {AP_SI_CNN_ROAD_ALIGN_LIMIT_TO_ROAD_PARA_M}
            closer to the road than the road side edge of the CNN slot.

            """
            # table_remark = f"The Parallel box shall have min depth of <br> {MIN_DEPTH_PARALLEL_PARKING_BOX_val_park} [m] during Scanning Mode  /or/ {MIN_DEPTH_PARALLEL_PARKING_BOX_val_Scan} [m] during Parking Mode  to the curb side edge. <br><br>"
            table_remark = "No parking box shall ever be identified which is unbounded on both its left and its right edges, <br> unless the parking box is supported by a CNN-based parking box. <br><br>"

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

            # Create a dictionary to store the collected data
            collect_data_dict = {
                ts: {
                    "pb": {},
                    "ts": ap_time[list(df.index).index(ts)],
                    "ap_state": ap_state.loc[ts],
                    "markers": {},
                    "Edge of the CNN slot": {},
                    # "MIN_DEPTH_PARALLEL_PARKING_BOX": {},
                    "verdict": {},
                    "pb_depth": {},
                    "CNN box edges": {},
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

            CNN_slots_column = [
                col
                for col in list(df.columns)
                if any(
                    cnn_obj in col for cnn_obj in ft_helper.combine_list_cnnBasedParkingSpaces_parkingSlots_slotCorners
                )
            ]
            CNN_slots_df = df[CNN_slots_column]
            CNN_slots_df = CNN_slots_df.loc[:, (CNN_slots_df != 0).any(axis=0)]
            # Get column names
            # column_names_CNN_slots_df = CNN_slots_df.columns.tolist()
            cnnBasedParkingSpaces_parkingSlots_0_x_0_columns = sorted(
                [
                    col
                    for col in CNN_slots_df.columns
                    if "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_0.x" in col
                ]
            )
            cnnBasedParkingSpaces_parkingSlots_0_y_0_columns = sorted(
                [
                    col
                    for col in CNN_slots_df.columns
                    if "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_0.y" in col
                ]
            )
            cnnBasedParkingSpaces_parkingSlots_0_x_1_columns = sorted(
                [
                    col
                    for col in CNN_slots_df.columns
                    if "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_1.x" in col
                ]
            )
            cnnBasedParkingSpaces_parkingSlots_0_y_1_columns = sorted(
                [
                    col
                    for col in CNN_slots_df.columns
                    if "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_1.y" in col
                ]
            )
            cnnBasedParkingSpaces_parkingSlots_0_x_2_columns = sorted(
                [
                    col
                    for col in CNN_slots_df.columns
                    if "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_2.x" in col
                ]
            )
            cnnBasedParkingSpaces_parkingSlots_0_y_2_columns = sorted(
                [
                    col
                    for col in CNN_slots_df.columns
                    if "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_2.y" in col
                ]
            )
            cnnBasedParkingSpaces_parkingSlots_0_x_3_columns = sorted(
                [
                    col
                    for col in CNN_slots_df.columns
                    if "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_3.x" in col
                ]
            )
            cnnBasedParkingSpaces_parkingSlots_0_y_3_columns = sorted(
                [
                    col
                    for col in CNN_slots_df.columns
                    if "SiInputPort.cnnBasedParkingSpaces.parkingSlots_0.slotCorners_3.y" in col
                ]
            )
            df_CNN_slots_zip = pd.DataFrame(
                {
                    "array_x_y_dir": [
                        list(
                            zip(
                                row[cnnBasedParkingSpaces_parkingSlots_0_x_0_columns],
                                row[cnnBasedParkingSpaces_parkingSlots_0_y_0_columns],
                                row[cnnBasedParkingSpaces_parkingSlots_0_x_1_columns],
                                row[cnnBasedParkingSpaces_parkingSlots_0_y_1_columns],
                                row[cnnBasedParkingSpaces_parkingSlots_0_x_2_columns],
                                row[cnnBasedParkingSpaces_parkingSlots_0_y_2_columns],
                                row[cnnBasedParkingSpaces_parkingSlots_0_x_3_columns],
                                row[cnnBasedParkingSpaces_parkingSlots_0_y_3_columns],
                            )
                        )
                        for _, row in CNN_slots_df.iterrows()
                    ]
                },
                index=CNN_slots_df.index,
            )

            #######
            for timestamp_val in filtered_timestamps:
                pb_with_marker_match.clear()

                pb_from_ts = {x: [(0.0, 0.0)] * 4 for x in range(len(pb_col_with_values))}

                for i, col_name in enumerate(pb_col_with_values):
                    pb_coords = pb_signal_df[col_name].loc[timestamp_val]
                    vertices_pb = list(zip(pb_coords[::2], pb_coords[1::2]))
                    pb_from_ts[i] = vertices_pb
                # Remove the parking box with all zeros
                pb_from_ts = {x: y for x, y in pb_from_ts.items() if all(val1 != 0 for val1, val2 in y)}

                if pb_from_ts:

                    # the_state_of_ap = collect_data_dict[timestamp_val]["ap_state"]

                    park_box_id = list(pb_from_ts.keys())[0]
                    vertices_pb = pb_from_ts[park_box_id]
                    distances_between_pb = ft_helper.quadrilateral_distances(vertices_pb)
                    # min_distances_between_pb = min(distances_between_pb.values())
                    # AB_depth_pb = float(f'{distances_between_pb.get("AB",0):.2f}')
                    AB_depth_pb = distances_between_pb

                    # sta_obj_vertices = df_static_obj_vertices.loc[timestamp_val][0]

                    CNN_slots_list = df_CNN_slots_zip.loc[timestamp_val][0]
                    # Flatten the tuple and group into pairs
                    # CNN_slots_list = [
                    # (CNN_slots_list[0][i], CNN_slots_list[0][i + 1]) for i in range(0, len(CNN_slots_list[0]), 2)
                    # ]

                    # Convert the flat list to a list of tuples
                    tuple_pairs = [
                        (CNN_slots_list[0][i], CNN_slots_list[0][i + 1]) for i in range(0, len(CNN_slots_list[0]), 2)
                    ]

                    # Rearrange the tuples: (first, fourth, second, third)
                    CNN_slots_list = [tuple_pairs[0], tuple_pairs[3], tuple_pairs[1], tuple_pairs[2]]

                    # Print the result
                    # print(f"CNN_slots_list is : {CNN_slots_list}")

                    ####################################

                    egoVehiclePoseForAP_pos_x_m_index_val = df.loc[
                        timestamp_val, "envModelPort.egoVehiclePoseForAP.pos_x_m"
                    ]
                    egoVehiclePoseForAP_pos_y_m_index_val = df.loc[
                        timestamp_val, "envModelPort.egoVehiclePoseForAP.pos_y_m"
                    ]
                    egoVehiclePoseForAP_Ego_pos_yaw_index_val = df.loc[timestamp_val, "Ego_pos_yaw"]

                    # Example Data
                    ego_position = (egoVehiclePoseForAP_pos_x_m_index_val, egoVehiclePoseForAP_pos_y_m_index_val)
                    ego_orientation = egoVehiclePoseForAP_Ego_pos_yaw_index_val  # Ego orientation in radians

                    # Transform the CNN slot coordinates to the world frame
                    CNN_world_slots = ft_helper.transform_ego_to_world(ego_position, ego_orientation, CNN_slots_list)
                    # print(f"CNN_world_slots is : {CNN_world_slots}")

                    distance_between_CNN_slots = ft_helper.quadrilateral_distances(CNN_world_slots)
                    # Get the minimum value
                    # min_distance_between_CNN_slots = min(distance_between_CNN_slots.values())
                    min_distance_between_CNN_slots = distance_between_CNN_slots

                    collect_data_dict[timestamp_val]["pb_depth"][park_box_id] = AB_depth_pb
                    collect_data_dict[timestamp_val]["CNN box edges"][park_box_id] = min_distance_between_CNN_slots

                    if AB_depth_pb and min_distance_between_CNN_slots:
                        collect_data_dict[timestamp_val]["verdict"][park_box_id] = "PASS"
                        collect_data_dict[timestamp_val]["description"][
                            park_box_id
                        ] = f"The parking box 's  edges are {AB_depth_pb} [m],          CNN slot edges are {min_distance_between_CNN_slots} [m] \
                        , which are almost alligned ."

                    else:
                        collect_data_dict[timestamp_val]["verdict"][park_box_id] = "FAIL"
                        collect_data_dict[timestamp_val]["description"][
                            park_box_id
                        ] = f"The parking box 's  edges are {AB_depth_pb} [m],          CNN slot edges are {min_distance_between_CNN_slots} [m] \
                        , which are not alligned ."
            res = [val["verdict"][x] for val in collect_data_dict.values() for x in val["verdict"].keys()]
            if res and pb_from_ts:
                res = all([x == "PASS" for x in res])
                if res:
                    test_result = fc.PASS
                    self.result.measured_result = TRUE
                    for ts in numValidPbTimestamps:

                        for pb_id in collect_data_dict[ts]["pb_depth"].keys():
                            sig_sum["Timestamp [s]"].append(collect_data_dict[ts]["ts"])
                            sig_sum["Parallel PB edges [m]"].append(collect_data_dict[ts]["pb_depth"][pb_id])
                            sig_sum["CNN box edges [m]"].append(collect_data_dict[ts]["CNN box edges"][pb_id])
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
                                    sig_sum["Parallel PB edges [m]"].append(val["pb_depth"][pb_id])
                                    sig_sum["CNN box edges [m]"].append(val["CNN box edges"][pb_id])
                                    sig_sum["description"].append(val["description"][pb_id])
                                    sig_sum["Result"].append(ft_helper.get_result_color(val["verdict"][pb_id]))

                    sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                    sig_sum = ft_helper.create_hidden_table(
                        sig_sum, 1, button_text="Show Table Parallel_Parking_depth information"
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


@verifies("ReqId_1405832")
@testcase_definition(
    name="SI_ParallelPrakingBox_is_supported_by_a_CNN_based_pbTC",
    description="Test if parking boxes are only pesent on the output in case of a CNN based slot supporting it.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_9twSgTpwEe6GONELpfdJ2Q&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
@register_inputs("/Playground_2/TSF-Debug")
class SI_ParallelPrakingBox_is_supported_by_a_CNN_based_pbTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SI_ParallelPrakingBox_is_supported_by_a_CNN_based_pb,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to

    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.

    """
    # test_bsigs = r"D:\reporting-ui\workspace\workspace\pl_parking\recordings\SI_recc\1405832_new\SISim_UC_Parallel_CNN_Slots.testrun.erg"
    debug(
        SI_ParallelPrakingBox_is_supported_by_a_CNN_based_pbTC,
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
