"""The orientation of the detected parking box shall be oriented according to the orientation of linked cnn slots, if present"""

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
READER_NAME = "SI_ParkingBoxOrientation_with_cnn_slots"
signals_obj = SISignals()


@teststep_definition(
    step_number=1,
    name="Check for SI_ParkingBoxOrientation_with_cnn_slots",
    description="The orientation of the detected parking box shall be oriented according to the orientation of linked cnn slots, if present.",
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(READER_NAME, SISignals)
class SI_ParkingBoxOrientation_with_cnn_slots(TestStep):
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

            pb_signal_df = pd.DataFrame()
            sig_sum = {
                "Timestamp [s]": [],
                "pb_coords_orientation_angle [degree]": [],
                "CNN_slots_orientation_angle [degree]": [],
                "description": [],
                "Result": [],
            }

            ANGLE_DIFFERENCE_ALLOWED = threshold.ANGLE_DIFFERENCE_ALLOWED
            list_zero_degree = threshold.LIST_ZERO_DEGREE
            pb_with_marker_match = {}
            table_remark = "The orientation of the detected parking box shall be oriented according to the orientation of linked cnn slots, if present. <br><br>"

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

            collect_data_dict = {
                ts: {
                    "pb": {},
                    "ts": ap_time[list(df.index).index(ts)],
                    "ap_state": ap_state.loc[ts],
                    "markers": {},
                    "ANGLE_DIFFERENCE_ALLOWED": {},
                    "verdict": {},
                    "pb_coords_orientation_angle": {},
                    "CNN_slots_orientation_angle": {},
                    "description": {},
                }
                for ts in filtered_timestamps
            }

            ap_state = ap_state.values.tolist()

            static_object_column = [
                col
                for col in list(df.columns)
                if any(stat_obj in col for stat_obj in ft_helper.combine_list_static_object)
            ]
            static_object_df = df[static_object_column]
            static_object_df = static_object_df.loc[:, (static_object_df != 0).any(axis=0)]

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

            delim_col_with_values = [
                col for col in marker_single_df.columns if not marker_single_df[col].apply(ft_helper.is_all_zeros).all()
            ]

            marker_single_df = marker_single_df[delim_col_with_values]

            CNN_slots_column = [
                col
                for col in list(df.columns)
                if any(stat_obj in col for stat_obj in ft_helper.combine_list_mODSlots_CNN_list)
            ]
            CNN_slots_df = df[CNN_slots_column]
            CNN_slots_df = CNN_slots_df.loc[:, (CNN_slots_df != 0).any(axis=0)]
            # Get column names
            # column_names_CNN_slots_df = CNN_slots_df.columns.tolist()
            mODSlots_slot_corners_x_0_columns = sorted(
                [col for col in CNN_slots_df.columns if "mODSlots.slot_corners._0_.x_0" in col]
            )
            mODSlots_slot_corners_y_0_columns = sorted(
                [col for col in CNN_slots_df.columns if "mODSlots.slot_corners._0_.y_0" in col]
            )
            mODSlots_slot_corners_x_1_columns = sorted(
                [col for col in CNN_slots_df.columns if "mODSlots.slot_corners._1_.x_0" in col]
            )
            mODSlots_slot_corners_y_1_columns = sorted(
                [col for col in CNN_slots_df.columns if "mODSlots.slot_corners._1_.y_0" in col]
            )
            mODSlots_slot_corners_x_2_columns = sorted(
                [col for col in CNN_slots_df.columns if "mODSlots.slot_corners._2_.x_0" in col]
            )
            mODSlots_slot_corners_y_2_columns = sorted(
                [col for col in CNN_slots_df.columns if "mODSlots.slot_corners._2_.y_0" in col]
            )
            mODSlots_slot_corners_x_3_columns = sorted(
                [col for col in CNN_slots_df.columns if "mODSlots.slot_corners._3_.x_0" in col]
            )
            mODSlots_slot_corners_y_3_columns = sorted(
                [col for col in CNN_slots_df.columns if "mODSlots.slot_corners._3_.y_0" in col]
            )
            df_CNN_slots_zip = pd.DataFrame(
                {
                    "array_x_y_dir": [
                        list(
                            zip(
                                row[mODSlots_slot_corners_x_0_columns],
                                row[mODSlots_slot_corners_y_0_columns],
                                row[mODSlots_slot_corners_x_1_columns],
                                row[mODSlots_slot_corners_y_1_columns],
                                row[mODSlots_slot_corners_x_2_columns],
                                row[mODSlots_slot_corners_y_2_columns],
                                row[mODSlots_slot_corners_x_3_columns],
                                row[mODSlots_slot_corners_y_3_columns],
                            )
                        )
                        for _, row in CNN_slots_df.iterrows()
                    ]
                },
                index=CNN_slots_df.index,
            )

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
                    # distances_between_pb = ft_helper.quadrilateral_distances(vertices_pb)

                    #####
                    # Reordered list
                    reordered_vertices_pb = [
                        vertices_pb[0],  # First point
                        vertices_pb[2],  # Third point
                        vertices_pb[1],  # Second point
                        vertices_pb[3],  # Fourth point
                    ]

                    #####

                    pb_coords_orientation_angle = ft_helper.calculate_orientation(reordered_vertices_pb)

                    pb_coords_orientation_angle = f"{pb_coords_orientation_angle:.2f}"
                    pb_coords_orientation_angle = float(pb_coords_orientation_angle)
                    if pb_coords_orientation_angle in list_zero_degree:
                        pb_coords_orientation_angle = 0.00

                    CNN_slots_list = df_CNN_slots_zip.loc[timestamp_val][0]
                    # Flatten the tuple and group into pairs
                    CNN_slots_list = [
                        (CNN_slots_list[0][i], CNN_slots_list[0][i + 1]) for i in range(0, len(CNN_slots_list[0]), 2)
                    ]

                    ########## mine
                    odoEstimation_yAngle_each_timestamp_index_val = df.loc[timestamp_val, "odoEstimation.yAngle"]
                    odoEstimation_xPosition_m_each_timestamp_index_val = df.loc[
                        timestamp_val, "odoEstimation.xPosition_m"
                    ]
                    odoEstimation_yPosition_m_each_timestamp_index_val = df.loc[
                        timestamp_val, "odoEstimation.yPosition_m"
                    ]

                    # Example Data
                    ego_position = (
                        odoEstimation_xPosition_m_each_timestamp_index_val,
                        odoEstimation_yPosition_m_each_timestamp_index_val,
                    )  # Ego vehicle position in the world frame (x, y)
                    ego_orientation = odoEstimation_yAngle_each_timestamp_index_val  # Ego orientation in radians

                    # CNN slots: Each slot has 4 vertices defined in the ego frame
                    # cnn_slots = CNN_slots_list

                    # Transform the CNN slot coordinates to the world frame
                    world_slots = ft_helper.transform_ego_to_world(ego_position, ego_orientation, CNN_slots_list)
                    # print(f"world_slots is : {world_slots}")

                    ######### mine end

                    CNN_slots_orientation_angle = ft_helper.calculate_orientation(world_slots)

                    CNN_slots_orientation_angle = ft_helper.normalize_angle_to_360(CNN_slots_orientation_angle)
                    ########
                    CNN_slots_orientation_angle = f"{CNN_slots_orientation_angle:.2f}"
                    CNN_slots_orientation_angle = float(CNN_slots_orientation_angle)
                    if CNN_slots_orientation_angle in list_zero_degree:
                        CNN_slots_orientation_angle = 0.00

                    collect_data_dict[timestamp_val]["pb_coords_orientation_angle"][
                        park_box_id
                    ] = pb_coords_orientation_angle
                    collect_data_dict[timestamp_val]["CNN_slots_orientation_angle"][
                        park_box_id
                    ] = CNN_slots_orientation_angle

                    collect_data_dict[timestamp_val]["ANGLE_DIFFERENCE_ALLOWED"][park_box_id] = ANGLE_DIFFERENCE_ALLOWED

                    Angle_diff_pb_and_cnn = abs(float(pb_coords_orientation_angle) - float(CNN_slots_orientation_angle))

                    if Angle_diff_pb_and_cnn < ANGLE_DIFFERENCE_ALLOWED:
                        collect_data_dict[timestamp_val]["verdict"][park_box_id] = "PASS"
                        collect_data_dict[timestamp_val]["description"][
                            park_box_id
                        ] = f"The PB coordinates orientation angle is {pb_coords_orientation_angle} [degree], and the CNN slots orientation angle is {CNN_slots_orientation_angle} [degree]. The angle difference between them is {Angle_diff_pb_and_cnn} [degree]."
                    else:
                        collect_data_dict[timestamp_val]["verdict"][park_box_id] = "FAIL"
                        collect_data_dict[timestamp_val]["description"][
                            park_box_id
                        ] = f"The PB coordinates orientation angle is {pb_coords_orientation_angle} [degree], and the CNN slots orientation angle is {CNN_slots_orientation_angle} [degree]. The angle difference between them is {Angle_diff_pb_and_cnn} [degree]."

            res = [val["verdict"][x] for val in collect_data_dict.values() for x in val["verdict"].keys()]
            if res and pb_from_ts:
                res = all([x == "PASS" for x in res])
                if res:
                    test_result = fc.PASS
                    self.result.measured_result = TRUE
                    for ts in numValidPbTimestamps:

                        for pb_id in collect_data_dict[ts]["pb_coords_orientation_angle"].keys():
                            sig_sum["Timestamp [s]"].append(collect_data_dict[ts]["ts"])
                            sig_sum["pb_coords_orientation_angle [degree]"].append(
                                collect_data_dict[ts]["pb_coords_orientation_angle"][pb_id]
                            )
                            sig_sum["CNN_slots_orientation_angle [degree]"].append(
                                collect_data_dict[ts]["CNN_slots_orientation_angle"][pb_id]
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
                            for pb_id in val["pb_coords_orientation_angle"].keys():
                                if val["verdict"][pb_id] == "FAIL":
                                    sig_sum["Timestamp [s]"].append(val["ts"])
                                    sig_sum["pb_coords_orientation_angle [degree]"].append(
                                        val["pb_coords_orientation_angle"][pb_id]
                                    )
                                    sig_sum["CNN_slots_orientation_angle [degree]"].append(
                                        val["CNN_slots_orientation_angle"][pb_id]
                                    )
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


@verifies("ReqId_1405881")
@testcase_definition(
    name="SI_ParkingBoxOrientation_with_cnn_slotsTC",
    description="Test Case for validating parking box orientation with CNN slots.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_9tw5nzpwEe6GONELpfdJ2Q&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg",
)
@register_inputs("/Playground_2/TSF-Debug")
class SI_ParkingBoxOrientation_with_cnn_slotsTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SI_ParkingBoxOrientation_with_cnn_slots,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to

    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.

    """
    # test_bsigs = r"D:\reporting-ui\workspace\workspace\pl_parking\recordings\SI_recc\1405881\05_12_2024\SISim_UC_Parallel_Empty_Prk_GT_Min_Defined.testrun.erg"
    debug(
        SI_ParkingBoxOrientation_with_cnn_slotsTC,
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
