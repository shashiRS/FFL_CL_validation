"""Validate Parking Box Orientation According to ego vehicle"""

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
from pl_parking.PLP.MF.constants import ConstantsSI, ConstantsTrajpla, PlotlyTemplate
from pl_parking.PLP.MF.SI import ft_helper

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "SI_ParkingBox_Orientation_Validation_with_ego_vehicle"
signals_obj = SISignals()


@teststep_definition(
    step_number=1,
    name="Check for SI ParkingBox_Orientation_Validation_with_ego_vehicle",
    description="This test step checks whether the detected parking box orientation aligns with the orientation of the ego vehicle.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SISignals)
class ParkingBoxOrientationCheck_with_ego_vehicle(TestStep):
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
        pb_signal_df = pd.DataFrame()

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

            # ODOESTIMATION_x = df[signals_obj.Columns.ODOESTIMATION_XPOSITION_M]
            # ODOESTIMATION_y = df[signals_obj.Columns.ODOESTIMATION_YPOSITION_M]
            # ODOESTIMATION_yaw = df[signals_obj.Columns.ODOESTIMATION_YANGLE]

            ap_time = df[SISignals.Columns.TIME].values.tolist()

            pb_with_marker_match = {}
            AP_G_PAR_MAX_ORI_ANGLE_RAD = (
                ConstantsSI.AP_G_PAR_MAX_ORI_ANGLE_RAD
            )  # Example: convert 10 degrees to radians
            table_remark = f"The SceneInterpretation shall offer a free parallel parking box, if the orientation of the road side edge of the box is between <br> [-{AP_G_PAR_MAX_ORI_ANGLE_RAD}; +{AP_G_PAR_MAX_ORI_ANGLE_RAD}]  with <br> respect to the orientation of the ego vehicle while passing the parking slot.<br><br>"
            sig_sum = {
                "Timestamp [s]": [],
                "Orientation_pb [rad]": [],
                "Orientation_ego_vehicle [rad]": [],
                "description": [],
                "Result": [],
            }

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

            # delim_col_with_values = [
            # col for col in pb_filtered_df.columns if not pb_filtered_df[col].apply(ft_helper.is_all_zeros).all()
            # ]
            filtered_timestamps = list(pb_filtered_df.index)

            ap_time = [round(i, 3) for i in ap_time]
            #######
            # Create a dictionary to store the collected data
            collect_data_dict = {
                ts: {
                    "pb": {},
                    "ts": ap_time[list(df.index).index(ts)],
                    "ap_state": ap_state.loc[ts],
                    "markers": {},
                    # "intersection": {},
                    "Orientation_ego_vehicle": {},
                    "verdict": {},
                    # "ego_vehicle": [(ego_x.loc[ts], ego_y.loc[ts],ego_yaw.loc[ts])],
                    "Orientation_pb": {},
                    # "delim_width":{},
                    "description": {},
                }
                for ts in filtered_timestamps
            }

            # Transform apstate to list
            ap_state = ap_state.values.tolist()

            # distances_between_pb = {}

            for timestamp_val in filtered_timestamps:
                pb_with_marker_match.clear()

                pb_from_ts = {x: [(0.0, 0.0)] * 4 for x in range(len(pb_col_with_values))}

                for i, col_name in enumerate(pb_col_with_values):
                    pb_coords = pb_signal_df[col_name].loc[timestamp_val]
                    vertices_pb = list(zip(pb_coords[::2], pb_coords[1::2]))
                    # vertices_pb_new = vertices_pb[::2]
                    pb_from_ts[i] = vertices_pb[::2]
                    # vertices_pb_new[i] = vertices_pb_new
                # Remove the parking box with all zeros
                pb_from_ts = {x: y for x, y in pb_from_ts.items() if all(val1 != 0 for val1, val2 in y)}

                if pb_from_ts:

                    # the_state_of_ap = collect_data_dict[timestamp_val]["ap_state"]

                    park_box_id = list(pb_from_ts.keys())[0]
                    vertices_pb = pb_from_ts[park_box_id]
                    box_orientation_in_rad = ft_helper.cal_orientation_pb(vertices_pb)
                    box_orientation_in_rad_str = f"{box_orientation_in_rad:.10f}"
                    # Convert string back to radian
                    box_orientation_in_rad = float(box_orientation_in_rad_str)

                    # The ego vehicle orientation vector {1.0, 0.0} represents the vehicle's direction in a 2D coordinate system,
                    # typically used in autonomous driving and robotics. This orientation vector is defined by two components: {x, y},
                    # where 1.0 in the x-direction and 0.0 in the y-direction means the vehicle is facing directly along the positive x-axis.

                    # vertices_pb_vehicle = ConstantsSI.VERTICES_PB_VEHICLE
                    # ego_vehicle_orientation_in_rad = ft_helper.cal_orientation_vehicle(vertices_pb_vehicle)
                    # ego_vehicle_orientation_in_rad_str = f"{ego_vehicle_orientation_in_rad:.1f}"

                    odoEstimation_yAngle_each_timestamp_index_val = df.loc[timestamp_val, "odoEstimation.yAngle"]
                    # print(f"odoEstimation_yAngle_each_timestamp_index_val: {odoEstimation_yAngle_each_timestamp_index_val}")
                    ego_vehicle_orientation_in_rad_str = odoEstimation_yAngle_each_timestamp_index_val
                    ############################################
                    # Convert string back to radian
                    ego_vehicle_orientation_in_rad = float(ego_vehicle_orientation_in_rad_str)

                    collect_data_dict[timestamp_val]["Orientation_ego_vehicle"][
                        park_box_id
                    ] = ego_vehicle_orientation_in_rad_str
                    collect_data_dict[timestamp_val]["Orientation_pb"][park_box_id] = box_orientation_in_rad_str

                    # Check if the box is free for parallel parking
                    relative_orientation_in_rad = ft_helper.is_parallel_parking_box_free(
                        ego_vehicle_orientation_in_rad, box_orientation_in_rad
                    )
                    relative_orientation_in_rad = abs(relative_orientation_in_rad)
                    relative_orientation_in_rad_str = f"{relative_orientation_in_rad:.10f}"
                    relative_orientation_in_rad = float(relative_orientation_in_rad_str)

                    if -AP_G_PAR_MAX_ORI_ANGLE_RAD <= relative_orientation_in_rad <= AP_G_PAR_MAX_ORI_ANGLE_RAD:
                        # print("The parking box is free for parallel parking.")
                        collect_data_dict[timestamp_val]["verdict"][park_box_id] = "PASS"
                        collect_data_dict[timestamp_val]["description"][
                            park_box_id
                        ] = f"Orientation of Ego Vehicle is {ego_vehicle_orientation_in_rad_str} [rad] ,Parking Box Orientation is {box_orientation_in_rad_str} [rad]\
                        and there absolute Orientation difference is {relative_orientation_in_rad_str} [rad] falls in range [-{AP_G_PAR_MAX_ORI_ANGLE_RAD} to {AP_G_PAR_MAX_ORI_ANGLE_RAD}] [rad]"
                    else:
                        # print("The parking box is not suitable for parallel parking.")
                        collect_data_dict[timestamp_val]["verdict"][park_box_id] = "FAIL"
                        collect_data_dict[timestamp_val]["description"][
                            park_box_id
                        ] = f"Orientation of Ego Vehicle is {ego_vehicle_orientation_in_rad_str} [rad] ,Parking Box Orientation is {box_orientation_in_rad_str} [rad]\
                        and there absolute Orientation difference is {relative_orientation_in_rad_str} [rad] does not falls in range [-{AP_G_PAR_MAX_ORI_ANGLE_RAD} to {AP_G_PAR_MAX_ORI_ANGLE_RAD}] [rad]"

            res = [val["verdict"][x] for val in collect_data_dict.values() for x in val["verdict"].keys()]

            if res and pb_from_ts:
                res = all([x == "PASS" for x in res])
                if res:
                    test_result = fc.PASS
                    self.result.measured_result = TRUE
                    for ts in numValidPbTimestamps:

                        for pb_id in collect_data_dict[ts]["Orientation_pb"].keys():
                            sig_sum["Timestamp [s]"].append(collect_data_dict[ts]["ts"])
                            sig_sum["Orientation_pb [rad]"].append(collect_data_dict[ts]["Orientation_pb"][pb_id])
                            sig_sum["Orientation_ego_vehicle [rad]"].append(
                                collect_data_dict[ts]["Orientation_ego_vehicle"][pb_id]
                            )
                            sig_sum["description"].append(collect_data_dict[ts]["description"][pb_id])
                            sig_sum["Result"].append(
                                ft_helper.get_result_color(collect_data_dict[ts]["verdict"][pb_id])
                            )
                    sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                    sig_sum = ft_helper.create_hidden_table(
                        sig_sum, 1, button_text="Show Table Orientation of pb with ego vehicle"
                    )
                    plots.append(sig_sum)
                else:
                    test_result = fc.FAIL
                    self.result.measured_result = FALSE
                    for ts, val in collect_data_dict.items():
                        if ts:
                            for pb_id in val["Orientation_pb"].keys():
                                sig_sum["Timestamp [s]"].append(val["ts"])
                                sig_sum["Orientation_pb [rad]"].append(val["Orientation_pb"][pb_id])
                                sig_sum["Orientation_ego_vehicle [rad]"].append(val["Orientation_ego_vehicle"][pb_id])
                                sig_sum["description"].append(val["description"][pb_id])
                                sig_sum["Result"].append(ft_helper.get_result_color(val["verdict"][pb_id]))

                    sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                    sig_sum = ft_helper.create_hidden_table(
                        sig_sum, 1, button_text="Show Table Orientation of pb with ego vehicle"
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


@verifies("ReqId_1405829")
@testcase_definition(
    name="ParkingBoxOrientationCheck_with_ego_vehicleTC",
    description="Test Case for validating parking box orientation with  ego vehicle",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_9twSfTpwEe6GONELpfdJ2Q&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
@register_inputs("/Playground_2/TSF-Debug")
class ParkingBoxOrientationCheck_with_ego_vehicleTC(TestCase):
    """Test Case for validating parking box orientation against parking line markings."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            ParkingBoxOrientationCheck_with_ego_vehicle,
        ]


def main(data_folder, temp_dir=None, open_explorer=True):
    """Main entry point for debugging the test case."""
    # test_bsigs = r"D:\reporting-ui\workspace\workspace\pl_parking\recordings\SI_recc\10_12_2024\1405829\SISim_UC_Parallel_Orientation_15Deg.testrun.erg"

    debug(
        ParkingBoxOrientationCheck_with_ego_vehicleTC,
        # test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
    )


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"

    out_folder = working_directory / "out"

    main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)
