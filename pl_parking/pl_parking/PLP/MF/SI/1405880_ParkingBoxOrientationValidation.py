"""Validate Parking Box Orientation According to Parking Line Markings"""

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
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import (
    MfCustomTeststepReport,
    SISignals,
    build_html_table,
    get_color,
)
from pl_parking.PLP.MF.constants import (
    ConstantsSI,
    ConstantsTrajpla,
)
from pl_parking.PLP.MF.SI import ft_helper

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "SI_ParkingBoxOrientationValidation"
signals_obj = SISignals()


@teststep_definition(
    step_number=1,
    name="Check for SI ParkingBoxOrientation",
    description="This test step checks whether the detected parking box orientation aligns with the orientation of the parking line markings.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SISignals)
class ParkingBoxOrientationCheck(TestStep):
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

        plot_titles, plots, remarks = fh.rep([], 3)

        try:
            plots = []
            read_data = self.readers[SIGNAL_DATA]

            df = read_data.as_plain_df
            df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
            df.columns = df.columns.str.replace(r"\\n", "", regex=True)

            ap_state = df[SISignals.Columns.AP_STATE]
            # ego_x = df[signals_obj.Columns.EGO_POS_X]
            # ego_y = df[signals_obj.Columns.EGO_POS_Y]
            # ego_yaw = df[signals_obj.Columns.EGO_POS_YAW]
            ap_time = df[SISignals.Columns.TIME].values.tolist()

            marker_filtered_df = pd.DataFrame()
            marker_single_df = pd.DataFrame()
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
            # pb_cols = pb_signal_df[pb_col_with_values]
            pb_signal_df = pb_signal_df[pb_col_with_values]
            # df[SISignals.Columns.PARKING_SCENARIO_0]
            num_valid_pb = df[signals_obj.Columns.NUMVALIDPARKINGBOXES_NU]

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

            # mask_num_valid_pb = (
            # num_valid_pb[mask_apstate_park_scan_in].rolling(2).apply(lambda x: x[0] < x[1], raw=True)
            # )
            m_num_valid_pb = num_valid_pb != 0
            # numValidPbTimestamps = [row for row, val in mask_num_valid_pb.items() if val == 1]

            # Combine masks to get the final mask with valid values
            mask_final = (
                marker_single_df.applymap(lambda x: any(i != 0 for i in x)).any(axis=1)
                & mask_apstate_park_scan_in
                & m_num_valid_pb
            )
            # Apply mask to get the final dataframe

            marker_filtered_df = marker_single_df[mask_final]

            delim_col_with_values = [
                col
                for col in marker_filtered_df.columns
                if not marker_filtered_df[col].apply(ft_helper.is_all_zeros).all()
            ]

            delimiter_selected_columns = marker_filtered_df[delim_col_with_values]
            filtered_timestamps = list(marker_filtered_df.index)

            # Transform apstate to list
            ap_state = ap_state.values.tolist()

            # all_timestamp_filtered = df["timestamp"].tolist()
            list_delimiter_box_angles = []
            list_parking_box_angles = []
            list_timestamp_val = []
            list_ap_time_in_sec = []
            list_AC_width_pb = []
            list_AC_width_delimiters = []

            timestamp_val_l = []
            for timestamp_val in filtered_timestamps:
                timestamp_val_l.append(timestamp_val)
                ap_time_in_sec = ap_time[list(df.index).index(timestamp_val)]
                list_ap_time_in_sec.append(ap_time_in_sec)

                try:
                    column_names = list(pb_signal_df.columns)
                    vertices_pb = pb_signal_df.loc[timestamp_val, column_names]
                    vertices_pb = vertices_pb.tolist()

                    vertices_pb = [item for sublist in vertices_pb for item in sublist]

                    vertices_pb = list(zip(vertices_pb[::2], vertices_pb[1::2]))

                except Exception as e:
                    print(e)

                distances_between_pb = ft_helper.quadrilateral_distances(vertices_pb)
                AC_width_pb = float(f'{distances_between_pb.get("AC",0):.2f}')
                list_AC_width_pb.append(AC_width_pb)

                pb_coords = vertices_pb

                # Calculate the orientation of pb
                PB_orientation_angle = ft_helper.calculate_orientation(pb_coords)
                PB_orientation_angle = f"{PB_orientation_angle:.2f}"

                ## calculate delimiters orientations
                delimiter_column_names = list(delimiter_selected_columns.columns)
                delimiters_vertices = delimiter_selected_columns.loc[timestamp_val, delimiter_column_names]
                delimiters_vertices = delimiters_vertices.tolist()

                delimiters_vertices = [item for sublist in delimiters_vertices for item in sublist]

                delimiters_vertices_new = list(zip(delimiters_vertices[::2], delimiters_vertices[1::2]))

                distances_between_delimiters = ft_helper.quadrilateral_distances(delimiters_vertices_new)
                AC_width_delimiters = float(f'{distances_between_delimiters.get("AC", 0):.2f}')
                list_AC_width_delimiters.append(AC_width_delimiters)
                delimiters_coords = delimiters_vertices_new

                # Calculate the orientation of delimiters
                delimiters_orientation_angle = ft_helper.calculate_orientation(delimiters_coords)
                delimiters_orientation_angle = f"{delimiters_orientation_angle:.2f}"
                list_delimiter_box_angles.append(delimiters_orientation_angle)
                list_parking_box_angles.append(PB_orientation_angle)
                list_timestamp_val.append(timestamp_val)

            # Compare parking box orientation to parking line orientation
            orientation_Result_List = []
            orientation_match_list = []
            orientation_match_list_desc = []

            for idx, (box_angle, line_angle) in enumerate(zip(list_delimiter_box_angles, list_parking_box_angles)):
                angle_difference = abs(float(box_angle) - float(line_angle))
                if (
                    angle_difference > ConstantsSI.DEGREE_OF_TOLERENCE_FOR_ORIENTATION
                ):  # Assuming 10 degrees of tolerance for orientation matching
                    _log.debug(
                        f"Mismatch in orientation for parking box {idx}. Angle difference: {angle_difference:.2f}"
                    )
                    # orientation_match = False
                    orientation_match_list.append(False)
                    sentence = f"The orientation of the detected parking box is {box_angle} ,orientation  of parking line marking is {line_angle} and there angle difference is {angle_difference}"
                    orientation_match_list_desc.append(sentence)

                    orientation_Result_List.append(ft_helper.get_result_color("FAIL"))

                else:
                    # orientation_match = True
                    orientation_match_list.append(True)
                    sentence = f"The orientation of the detected parking box is {box_angle} ,orientation  of parking line marking is {line_angle} and there angle difference is {angle_difference}"
                    orientation_match_list_desc.append(sentence)
                    orientation_Result_List.append(ft_helper.get_result_color("PASS"))

            table_remark = "<b>The orientation of the detected parking box shall be oriented according to  the orientation of parking line markings, if present</b> <br><br>"
            val_True = True
            res1 = all(x == val_True for x in orientation_match_list)

            if orientation_match_list:

                if res1:
                    test_result = fc.PASS
                    self.result.measured_result = TRUE
                else:
                    test_result = fc.FAIL
                    self.result.measured_result = FALSE

                sig_sum = {
                    "Timestamp [s]": [],
                    "Orientation of parking line markings [degree]": [],
                    "Orientation of the detected parking box [degree]": [],
                    "Orientation details [degree]": [],
                    "Result": [],
                }
                sig_sum["Timestamp [s]"] = list_ap_time_in_sec
                sig_sum["Orientation of parking line markings [degree]"] = list_delimiter_box_angles
                sig_sum["Orientation of the detected parking box [degree]"] = list_parking_box_angles
                sig_sum["Orientation details [degree]"] = orientation_match_list_desc
                sig_sum["Result"] = orientation_Result_List
                sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                sig_sum = ft_helper.create_hidden_table(sig_sum, 1, button_text="Show Table Orientation information")
                plots.append(sig_sum)

                ########
                list_delimiter_box_angles = [float(i) for i in list_delimiter_box_angles]
                list_parking_box_angles = [float(i) for i in list_parking_box_angles]

                # Create the figure
                fig = go.Figure()

                # Add first dataset scatter plot
                fig.add_trace(
                    go.Scatter(
                        x=list_ap_time_in_sec,
                        y=list_delimiter_box_angles,
                        mode="lines+markers",
                        name="Orientation of parking line markings",
                        line=dict(color="blue"),
                        marker=dict(size=8),
                    )
                )

                # Add second dataset scatter plot
                fig.add_trace(
                    go.Scatter(
                        x=list_ap_time_in_sec,
                        y=list_parking_box_angles,
                        mode="lines+markers",
                        name="Orientation of the detected parking box",
                        line=dict(color="green"),
                        marker=dict(size=8),
                    )
                )

                # Customize layout
                fig.update_layout(
                    title="Scatter Plot of Orientation of the parking line markings with detected parking box",
                    xaxis_title="Timestamp [s]",
                    yaxis_title="Orientation [degree]",
                    template="plotly_white",
                    xaxis=dict(tickformat="%Y-%m"),  # Format the x-axis for month-year
                    font=dict(size=14),
                )

                plot_titles.append("")
                plots.append(fig)

            else:
                test_result = fc.NOT_ASSESSED
                self.result.measured_result = DATA_NOK
                sig_sum = ({"Evaluation not possible": "No valid orientation found"},)
                sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                sig_sum = ft_helper.create_hidden_table(sig_sum, 1, button_text="Show Table Orientation information")
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


@verifies("ReqId_1405880")
@testcase_definition(
    name="ParkingBoxOrientationCheckTC",
    description="Test Case for validating parking box orientation against parking line markings.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_9tw5njpwEe6GONELpfdJ2Q&oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg",
)
@register_inputs("/Playground_2/TSF-Debug")
class ParkingBoxOrientationCheckTC(TestCase):
    """Test Case for validating parking box orientation against parking line markings."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            ParkingBoxOrientationCheck,
        ]


def main(data_folder, temp_dir=None, open_explorer=True):
    """Main entry point for debugging the test case."""
    # test_bsigs = r"D:\reporting-ui\workspace\workspace\pl_parking\recordings\SI_recc\mine\08_11_2024\1405880_measurement\SISim_UC_Perpendicular_Empty_Prk_Markings_Wide_Enough.testrun.erg"

    debug(
        ParkingBoxOrientationCheckTC,
        # test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
    )


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"

    out_folder = working_directory / "out"

    main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)
