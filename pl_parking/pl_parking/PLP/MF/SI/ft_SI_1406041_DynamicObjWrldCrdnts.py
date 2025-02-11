"""Dynamic Objects Sorting by Distance from Ego Vehicle"""

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

import pl_parking.common_ft_helper as fh
from pl_parking.PLP.MF.constants import (
    ConstantsSI,
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
from pl_parking.PLP.MF.SI import ft_helper

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "SI_DynamicObjectDistanceValidation"
signals_obj = SISignals()


@teststep_definition(
    step_number=1,
    name="DynamicObjectDistanceSortingWorldCoordinatesTC",
    description="Verify dynamic objects are sorted by distance from the ego vehicle.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SISignals)
class DynamicObjectDistanceTypeSorting(TestStep):
    """Test Step for sorting dynamic objects (parking boxes) by distance from the ego vehicle."""

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
        try:
            plots = []
            # Get the read data frame
            read_data = self.readers[SIGNAL_DATA]
            self.test_result = fc.INPUT_MISSING  # Result
            self.result.measured_result = DATA_NOK  # Initializing the result with data nok
            plot_titles, plots, remarks = fh.rep([], 3)

            # Extract the number of dynamic objects and timestamps
            number_of_DynamicObjects = read_data["envModelPort.numberOfDynamicObjects_u8"]

            unique_number_of_DynamicObjects = number_of_DynamicObjects.unique().tolist()

            if len(unique_number_of_DynamicObjects) == 0:
                _log.debug("No dynamic objects found.")
                self.result.measured_result = FALSE
                return

            df = read_data.as_plain_df
            df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
            df.columns = df.columns.str.replace(r"\\n", "", regex=True)

            ap_time = df[SISignals.Columns.TIME].values.tolist()
            ap_time = [round(i, 3) for i in ap_time]

            filteredTimestamp = read_data["timestamp"].tolist()
            ego_x_col = read_data[["envModelPort.egoVehiclePoseForAP.pos_x_m", "timestamp"]]
            ego_y_col = read_data[["envModelPort.egoVehiclePoseForAP.pos_y_m", "timestamp"]]
            ego_orientations = read_data[["Ego_pos_yaw", "timestamp"]]

            vehicle_polygon = ConstantsSI.vehicle_polygon

            # Bumper_to_excel_distance = ConstantsSI.AP_V_LENGTH_M - ConstantsSI.AP_V_OVERHANG_REAR_M
            # Bumper_to_excel_distance = f"{Bumper_to_excel_distance:.3f}"

            list_min_distance_for_obj_0_all_vertices = []
            list_min_distance_for_obj_1_all_vertices = []
            list_min_distance_for_obj_2_all_vertices = []
            list_min_distance_for_obj_3_all_vertices = []

            list_ap_time_in_sec = []

            for timestamp in filteredTimestamp:

                timestamp_index = df[df["timestamp"] == timestamp].index[0]

                ap_time_in_sec = ap_time[list(df.index).index(timestamp_index)]
                list_ap_time_in_sec.append(ap_time_in_sec)

                list_obj_0_x = []
                list_obj_0_y = []
                list_obj_1_x = []
                list_obj_1_y = []
                list_obj_2_x = []
                list_obj_2_y = []
                list_obj_3_x = []
                list_obj_3_y = []
                for vertex in range(4):
                    obj_0_x_col = f"envModelPort.dynamicObjects_0.objShape_{vertex}.x"
                    obj_0_y_col = f"envModelPort.dynamicObjects_0.objShape_{vertex}.y"
                    obj_1_x_col = f"envModelPort.dynamicObjects_1.objShape_{vertex}.x"
                    obj_1_y_col = f"envModelPort.dynamicObjects_1.objShape_{vertex}.y"
                    obj_2_x_col = f"envModelPort.dynamicObjects_2.objShape_{vertex}.x"
                    obj_2_y_col = f"envModelPort.dynamicObjects_2.objShape_{vertex}.y"
                    obj_3_x_col = f"envModelPort.dynamicObjects_3.objShape_{vertex}.x"
                    obj_3_y_col = f"envModelPort.dynamicObjects_3.objShape_{vertex}.y"

                    if (
                        obj_0_x_col in df.columns
                        and obj_0_y_col in df.columns
                        and obj_1_x_col in df.columns
                        and obj_1_y_col in df.columns
                        and obj_2_x_col in df.columns
                        and obj_2_y_col in df.columns
                        and obj_3_x_col in df.columns
                        and obj_3_y_col in df.columns
                    ):
                        obj_0_x = df.loc[df["timestamp"] == timestamp, obj_0_x_col].iloc[0]
                        obj_0_y = df.loc[df["timestamp"] == timestamp, obj_0_y_col].iloc[0]

                        obj_1_x = df.loc[df["timestamp"] == timestamp, obj_1_x_col].iloc[0]
                        obj_1_y = df.loc[df["timestamp"] == timestamp, obj_1_y_col].iloc[0]

                        obj_2_x = df.loc[df["timestamp"] == timestamp, obj_2_x_col].iloc[0]
                        obj_2_y = df.loc[df["timestamp"] == timestamp, obj_2_y_col].iloc[0]

                        obj_3_x = df.loc[df["timestamp"] == timestamp, obj_3_x_col].iloc[0]
                        obj_3_y = df.loc[df["timestamp"] == timestamp, obj_3_y_col].iloc[0]

                        list_obj_0_x.append(obj_0_x)
                        list_obj_0_y.append(obj_0_y)
                        list_obj_1_x.append(obj_1_x)
                        list_obj_1_y.append(obj_1_y)
                        list_obj_2_x.append(obj_2_x)
                        list_obj_2_y.append(obj_2_y)
                        list_obj_3_x.append(obj_3_x)
                        list_obj_3_y.append(obj_3_y)

                # Ensure the lists have the same length
                if len(list_obj_0_x) == len(list_obj_0_y):
                    paired_list_obj_0 = list(zip(list_obj_0_x, list_obj_0_y))
                    # print("paired_list_obj_0:", paired_list_obj_0)
                else:
                    print("Error: Lists do not have the same number of elements.")

                if len(list_obj_1_x) == len(list_obj_1_y):
                    paired_list_obj_1 = list(zip(list_obj_1_x, list_obj_1_y))
                    # print("paired_list_obj_1:", paired_list_obj_1)
                else:
                    print("Error: Lists do not have the same number of elements.")
                if len(list_obj_2_x) == len(list_obj_2_y):
                    paired_list_obj_2 = list(zip(list_obj_2_x, list_obj_2_y))
                    # print("paired_list_obj_2:", paired_list_obj_2)
                else:
                    print("Error: Lists do not have the same number of elements.")
                if len(list_obj_3_x) == len(list_obj_3_y):
                    paired_list_obj_3 = list(zip(list_obj_3_x, list_obj_3_y))
                    # print("paired_list_obj_3:", paired_list_obj_3)
                else:
                    print("Error: Lists do not have the same number of elements.")

                ego_x_col_val = ego_x_col.loc[
                    df["timestamp"] == timestamp, "envModelPort.egoVehiclePoseForAP.pos_x_m"
                ].iloc[0]
                ego_y_col_val = ego_y_col.loc[
                    df["timestamp"] == timestamp, "envModelPort.egoVehiclePoseForAP.pos_y_m"
                ].iloc[0]

                ego_yaw_rad = ego_orientations.loc[df["timestamp"] == timestamp, "Ego_pos_yaw"].iloc[0]

                # ego_vehicle_position = (ego_x_col_val + float(Bumper_to_excel_distance), ego_y_col_val)
                ego_vehicle_position = (ego_x_col_val, ego_y_col_val)

                # Transform the ego vehicle coordinates to the world coordinates
                vehicle_polygon_in_world_coordinate = ft_helper.transform_ego_to_world(
                    ego_vehicle_position, ego_yaw_rad, vehicle_polygon
                )
                # print(f"vehicle_polygon_in_world_coordinate is : {vehicle_polygon_in_world_coordinate}")

                # Calculate the minimum distance and the closest points
                min_distance_obj_0, closest_points_obj_0 = ft_helper.vertex_to_vertex_distance(
                    vehicle_polygon_in_world_coordinate, paired_list_obj_0
                )

                # print(f"Minimum Distance min_distance_obj_0: {min_distance_obj_0}")
                # print(f"Closest Point on Polygon 1 closest_points_obj_0: {closest_points_obj_0[0]}")
                # print(f"Closest Point on Polygon 2 closest_points_obj_0: {closest_points_obj_0[1]}")

                # Calculate the minimum distance and the closest points
                min_distance_obj_1, closest_points_obj_1 = ft_helper.vertex_to_vertex_distance(
                    vehicle_polygon_in_world_coordinate, paired_list_obj_1
                )

                # print(f"Minimum Distance min_distance_obj_1: {min_distance_obj_1}")
                # print(f"Closest Point on Polygon 1 closest_points_obj_1: {closest_points_obj_1[0]}")
                # print(f"Closest Point on Polygon 2 closest_points_obj_1: {closest_points_obj_1[1]}")
                min_distance_obj_2, closest_points_obj_2 = ft_helper.vertex_to_vertex_distance(
                    vehicle_polygon_in_world_coordinate, paired_list_obj_2
                )
                min_distance_obj_3, closest_points_obj_3 = ft_helper.vertex_to_vertex_distance(
                    vehicle_polygon_in_world_coordinate, paired_list_obj_3
                )
                min_distance_obj_0 = f"{min_distance_obj_0:.3f}"
                list_min_distance_for_obj_0_all_vertices.append(float(min_distance_obj_0))

                min_distance_obj_1 = f"{min_distance_obj_1:.3f}"
                list_min_distance_for_obj_1_all_vertices.append(float(min_distance_obj_1))

                min_distance_obj_2 = f"{min_distance_obj_2:.3f}"
                list_min_distance_for_obj_2_all_vertices.append(float(min_distance_obj_2))

                min_distance_obj_3 = f"{min_distance_obj_3:.3f}"
                list_min_distance_for_obj_3_all_vertices.append(float(min_distance_obj_3))

            Description_list = [
                f"Object 1 min distance: {d0} m, Object 2 min distance: {d1} m,Object 3 min distance: {d2} m,Object 4 min distance: {d3} m, from ego vehicle."
                for d0, d1, d2, d3 in zip(
                    list_min_distance_for_obj_0_all_vertices,
                    list_min_distance_for_obj_1_all_vertices,
                    list_min_distance_for_obj_2_all_vertices,
                    list_min_distance_for_obj_3_all_vertices,
                )
            ]
            Result_List = [
                ft_helper.get_result_color("PASS") if d0 <= d1 <= d2 <= d3 else ft_helper.get_result_color("FAIL")
                for d0, d1, d2, d3 in zip(
                    list_min_distance_for_obj_0_all_vertices,
                    list_min_distance_for_obj_1_all_vertices,
                    list_min_distance_for_obj_2_all_vertices,
                    list_min_distance_for_obj_3_all_vertices,
                )
            ]
            Result_List_T_F = [
                "PASS" if d0 <= d1 <= d2 <= d3 else "FAIL"
                for d0, d1, d2, d3 in zip(
                    list_min_distance_for_obj_0_all_vertices,
                    list_min_distance_for_obj_1_all_vertices,
                    list_min_distance_for_obj_2_all_vertices,
                    list_min_distance_for_obj_3_all_vertices,
                )
            ]

            table_remark = "<b>Dynamic Objects should be sorted by their distance from the ego vehicle.</b><br><br>"
            if (
                list_min_distance_for_obj_0_all_vertices
                and list_min_distance_for_obj_1_all_vertices
                and list_min_distance_for_obj_2_all_vertices
                and list_min_distance_for_obj_3_all_vertices
            ):
                res1 = all(x == "PASS" for x in Result_List_T_F)
                if res1:
                    test_result = fc.PASS
                    self.result.measured_result = TRUE
                    sig_sum = pd.DataFrame(
                        {
                            "Timestamp [s]": list_ap_time_in_sec,
                            "Distance to Object 1 [m]": list_min_distance_for_obj_0_all_vertices,
                            "Distance to Object 2 [m]": list_min_distance_for_obj_1_all_vertices,
                            "Distance to Object 3 [m]": list_min_distance_for_obj_2_all_vertices,
                            "Distance to Object 4 [m]": list_min_distance_for_obj_3_all_vertices,
                            "Description": Description_list,
                            "Result": Result_List,
                        }
                    )
                    sig_sum_html = build_html_table(sig_sum, table_remark=table_remark)
                    sig_sum_html = ft_helper.create_hidden_table(
                        sig_sum_html, 1, button_text="Dynamic Object Distances Table"
                    )
                    plots.append(sig_sum_html)
                else:
                    test_result = fc.FAIL
                    self.result.measured_result = FALSE
                    sig_sum = pd.DataFrame(
                        {
                            "Timestamp [s]": list_ap_time_in_sec,
                            "Distance to Object 1 [m]": list_min_distance_for_obj_0_all_vertices,
                            "Distance to Object 2 [m]": list_min_distance_for_obj_1_all_vertices,
                            "Distance to Object 3 [m]": list_min_distance_for_obj_2_all_vertices,
                            "Distance to Object 4 [m]": list_min_distance_for_obj_3_all_vertices,
                            "Description": Description_list,
                            "Result": Result_List,
                        }
                    )
                    sig_sum_html = build_html_table(sig_sum, table_remark=table_remark)
                    sig_sum_html = ft_helper.create_hidden_table(
                        sig_sum_html, 1, button_text="Dynamic Object Distances Table"
                    )
                    plots.append(sig_sum_html)

                # Plotting the distances and number of dynamic objects over time
                fig = go.Figure()

                # Plot distances of object 1 to 4
                fig.add_trace(
                    go.Scatter(
                        x=list_ap_time_in_sec,
                        y=list_min_distance_for_obj_0_all_vertices,
                        mode="lines+markers",
                        name="Distance to Object 1",
                        line=dict(color="blue"),
                        marker=dict(size=8),
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=list_ap_time_in_sec,
                        y=list_min_distance_for_obj_1_all_vertices,
                        mode="lines+markers",
                        name="Distance to Object 2",
                        line=dict(color="green"),
                        marker=dict(size=8),
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=list_ap_time_in_sec,
                        y=list_min_distance_for_obj_2_all_vertices,
                        mode="lines+markers",
                        name="Distance to Object 3",
                        line=dict(color="yellow"),
                        marker=dict(size=8),
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=list_ap_time_in_sec,
                        y=list_min_distance_for_obj_3_all_vertices,
                        mode="lines+markers",
                        name="Distance to Object 4",
                        line=dict(color="orange"),
                        marker=dict(size=8),
                    )
                )

                # Plot number of dynamic objects
                fig.add_trace(
                    go.Scatter(
                        x=list_ap_time_in_sec,
                        y=number_of_DynamicObjects,
                        mode="lines+markers",
                        name="Number of Dynamic Objects",
                        line=dict(color="red"),
                        marker=dict(size=8),
                    )
                )
                fig.update_layout(
                    title="Distance of Dynamic Objects and Object Count Over Time",
                    xaxis_title="Timestamp (seconds)",
                    yaxis_title="Distance (m) / Object Count",
                    template="plotly_white",
                    font=dict(size=14),
                )

                plot_titles.append("Dynamic Object Distances and Counts")
                plots.append(fig)

                ####

            else:
                test_result = fc.NOT_ASSESSED
                self.result.measured_result = DATA_NOK
                sig_sum = ({"Evaluation not possible": "DATA_NOK"},)
                sig_sum_html = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                plots.append(sig_sum_html)

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


@verifies("ReqId_1406041")
@testcase_definition(
    name="DynamicObjectDistanceSortingWorldCoordinatesTC",
    description="Test Case for dynamic object distance sorting.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_9tz87TpwEe6GONELpfdJ2Q&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36325",
)
@register_inputs("/Playground_2/TSF-Debug")
class DynamicObjectDistanceSortingTC(TestCase):
    """Test Case for verifying sorting of dynamic objects by distance."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            DynamicObjectDistanceTypeSorting,
        ]


def main(data_folder, temp_dir=None, open_explorer=True):
    """Main entry point for debugging the test case."""
    test_bsigs = r"D:\Parking_SI\ergs\Rear_Obstacles\SISim_UC_Rear_Dynamic_Obstacles.testrun.erg"

    debug(
        DynamicObjectDistanceSortingTC,
        test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
    )


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"

    out_folder = working_directory / "out"

    main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)
