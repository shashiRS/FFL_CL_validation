"""Functional test for usemkpi"""

import logging

from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

import pandas as pd
import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import (
    EntrySignals,
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    rep,
)
from pl_parking.PLP.MF.ENTRY.ft_dgps_helper import DgpsSignalsProcessing
from pl_parking.PLP.MF.ENTRY.usemLagLeadShrinkHelper import (
    EgoInfo,
    GhostObjectsHelper,
    LeadLagPointsHelper,
    LocalConstantsHelper,
    ParkingBoxPoints,
    transf_local_to_global,
)
from pl_parking.PLP.MF.ft_helper import ExampleSignals

SIGNAL_DATA = "MF_USEM_KPI"

example_obj = EntrySignals()


@teststep_definition(
    step_number=1,
    name="USEM KPI",
    description=(
        "Check if there is not an object outside bounding boxes starting with first object detection until the end of"
        " the test Check if the bounding boxes are not empty after scanning Check if the bounding boxes contains only"
        " one object inside each starting with first object detection until the end of the test"
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ExampleSignals)
class TestStepFtGroundTruthBoundingBox(TestStep):
    """Test step class"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        try:
            df = self.readers[SIGNAL_DATA].signals
        except Exception:
            df = self.readers[SIGNAL_DATA]
            df[EntrySignals.Columns.TIMESTAMP] = df.index
        result_final = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)

        # Defining signal variables for signal handling
        sg_time = "TimeStamp"
        sg_parking_mode = "PSMDebugPort"
        sg_ego = "EgoPositionAP"
        sg_nb_valid_static_obj = "NumberValidStaticObjects"

        signal_name = example_obj._properties
        signal_summary = {}
        eval_cond = [False] * 8
        self.usem_1_step = fc.PASS
        self.usem_2_step = fc.PASS
        self.usem_3_step = fc.PASS

        class USEMKPI:
            """
            USEM objects relative to bounding boxes
            Check the position of usem objects relative with a given ground truth bounding boxes
            """

            PASSED = 1
            FAILED = 0

            def __init__(self) -> None:
                """Initialize object attributes."""
                self.signals_box: pd.DataFrame = None
                self.NO_OBJ_OUTSIDE_BOXES = USEMKPI.PASSED
                self.BOXES_NOT_EMPTY = USEMKPI.PASSED
                self.OBJ_INSIDE_BOXES_ONE = USEMKPI.PASSED
                self.box_1: ParkingBoxPoints = None
                self.box_2: ParkingBoxPoints = None
                self.STATIC_OBJ_SHAPE_DCT = None
                self.START_IDX = None
                self.START_IDX_NO_EMPTY_BOX = None
                self.static_obj_shape_dict = None
                self._start_idx = None
                self._start_idx_no_empty_box = None
                self._static_obj_valid: list = None
                self._ego_info: EgoInfo = None
                self.error = None

            def run(self):
                try:
                    dgps_processing = DgpsSignalsProcessing(df)

                    dgps_processing.process()
                    self.signals_box = dgps_processing.get_signals()

                    obj_lead_lag_help = LeadLagPointsHelper()

                    self.static_obj_shape_dict = obj_lead_lag_help.store_vector_signals(
                        df,
                        constants.StaticObjectsShapeConstants.NAME_COLUMN_DF,
                        constants.StaticObjectsShapeConstants.NB_OBJ_SHAPE,
                    )
                    self.STATIC_OBJ_SHAPE_DCT = self.static_obj_shape_dict
                    if self._calculate_start_mask():

                        for idx in df.loc[self._start_idx :].index:
                            box_1, box_2 = self.get_helper_data(idx)

                            self.compute_kpis(self._static_obj_valid, self._ego_info, box_1, box_2, idx)
                            if (
                                self.NO_OBJ_OUTSIDE_BOXES == USEMKPI.FAILED
                                and self.OBJ_INSIDE_BOXES_ONE == USEMKPI.FAILED
                            ):
                                break
                    else:
                        self.NO_OBJ_OUTSIDE_BOXES = USEMKPI.FAILED
                        self.OBJ_INSIDE_BOXES_ONE = USEMKPI.FAILED

                    # Computation of UsemSilKpisCalc.BOXES_NOT_EMPTY
                    if self._calculate_start_mask_no_empty_boxes():
                        box_1, box_2 = self.get_helper_data(self._start_idx_no_empty_box)

                        if not self.check_boxes_not_empty_kpi(self._static_obj_valid, self._ego_info, box_1, box_2):
                            self.BOXES_NOT_EMPTY = USEMKPI.FAILED

                    else:
                        self.BOXES_NOT_EMPTY = USEMKPI.FAILED
                except KeyError as err:
                    self.error = str(err)

                    self.NO_OBJ_OUTSIDE_BOXES = USEMKPI.FAILED
                    self.BOXES_NOT_EMPTY = USEMKPI.FAILED
                    self.OBJ_INSIDE_BOXES_ONE = USEMKPI.FAILED
                    # raise Exception from key_error

            def compute_kpis(
                self,
                static_obj_valid,
                ego_info: EgoInfo,
                box_points_1: ParkingBoxPoints,
                box_points_2: ParkingBoxPoints,
                idx,
            ) -> bool:
                """This method computes the result for two of the kpis:
                - UsemSilKpisCalc.NO_OBJ_OUTSIDE_BOXES -> 1 or 0 (no object outside the boxes)
                - UsemSilKpisCalc.OBJ_INSIDE_BOXES_ONE -> 1 or 0 (number of objects inside a bounding box is 1)
                """
                objects_inside_box_1 = []
                objects_inside_box_2 = []

                for obj in static_obj_valid:
                    points_inside_box_1 = []
                    points_inside_box_2 = []

                    for i in range(0, len(self.static_obj_shape_dict[obj]), LocalConstantsHelper.STEP_X_COORD):
                        if (
                            self.static_obj_shape_dict[obj][i][idx] != 0.0
                            and self.static_obj_shape_dict[obj][i + 1][idx] != 0.0
                        ):
                            point_obj = transf_local_to_global(
                                self.static_obj_shape_dict[obj][i][idx],
                                self.static_obj_shape_dict[obj][i + 1][idx],
                                ego_info.ego_x,
                                ego_info.ego_y,
                                ego_info.ego_yaw,
                            )
                            points_inside_box_1.append(
                                GhostObjectsHelper.check_point_inside_polygon(box_points_1, point_obj, borders=True)
                            )
                            points_inside_box_2.append(
                                GhostObjectsHelper.check_point_inside_polygon(box_points_2, point_obj, borders=True)
                            )
                    cond_bool = [
                        (bool(points_inside_box_1) and all(points_inside_box_1)),
                        (bool(points_inside_box_2) and all(points_inside_box_2)),
                    ]

                    # NoObjectOutsideBoundingBoxesTest computation
                    if not cond_bool[0] and not cond_bool[1]:
                        self.NO_OBJ_OUTSIDE_BOXES = USEMKPI.FAILED

                    # NoEmptyBoundingBoxesTest and NumberObjectsInsideBoxOneTest computations
                    self.add_obj_inside_box(any(points_inside_box_1), obj, objects_inside_box_1)
                    self.add_obj_inside_box(any(points_inside_box_2), obj, objects_inside_box_2)

                # NumberObjectsInsideBoxOneTest computation
                if not (len(objects_inside_box_1) == 1 and len(objects_inside_box_2) == 1):
                    self.OBJ_INSIDE_BOXES_ONE = USEMKPI.FAILED

            def add_obj_inside_box(self, cond_bool: bool, obj: str, obj_inside_box: list) -> None:
                """Store the objects inside a box"""
                if cond_bool:
                    obj_inside_box.append(obj)

            def get_helper_data(self, idx: int):
                """Return static_obj_valid and ego_info at a certain index"""
                self._static_obj_valid = LeadLagPointsHelper.obtain_static_obj_valid(
                    df, self.static_obj_shape_dict, idx, sg_nb_valid_static_obj
                )
                box_1, box_2 = self.generate_left_right_boxes(idx)
                self._ego_info = LeadLagPointsHelper.generate_ego_info(df, idx, sg_ego)
                return box_1, box_2

            def generate_left_right_boxes(self, idx):
                """Generate the bounding boxes around the parking slot (created by dgps points)"""
                self.box_1 = DgpsSignalsProcessing.extract_points_dgps_box_left(self.signals_box, idx)
                self.box_2 = DgpsSignalsProcessing.extract_points_dgps_box_right(self.signals_box, idx)

                return self.box_1, self.box_2

            def _calculate_start_mask(self):
                """Starting index is the one from the first occurence of an object inside the box"""
                for idx in df.index:
                    static_obj_valid = LeadLagPointsHelper.obtain_static_obj_valid(
                        df, self.static_obj_shape_dict, idx, sg_nb_valid_static_obj
                    )
                    box_1, box_2 = self.generate_left_right_boxes(idx)
                    ego_info = LeadLagPointsHelper.generate_ego_info(df, idx, sg_ego)

                    if self.check_obj_inside_box_first(static_obj_valid, ego_info, box_1, box_2, idx):
                        self._start_idx = idx
                        self.START_IDX = self._start_idx
                        return True

                return False

            def check_obj_inside_box_first(
                self,
                static_obj_valid,
                ego_info: EgoInfo,
                box_points_1: ParkingBoxPoints,
                box_points_2: ParkingBoxPoints,
                idx,
            ) -> bool:
                """Check the first occurence of an object inside a bounding box"""
                for obj in static_obj_valid:
                    points_inside_box_1 = []
                    points_inside_box_2 = []

                    for i in range(0, len(self.static_obj_shape_dict[obj]), LocalConstantsHelper.STEP_X_COORD):
                        if (
                            self.static_obj_shape_dict[obj][i][idx] != 0.0
                            and self.static_obj_shape_dict[obj][i + 1][idx] != 0.0
                        ):
                            point_obj = transf_local_to_global(
                                self.static_obj_shape_dict[obj][i][idx],
                                self.static_obj_shape_dict[obj][i + 1][idx],
                                ego_info.ego_x,
                                ego_info.ego_y,
                                ego_info.ego_yaw,
                            )
                            points_inside_box_1.append(
                                GhostObjectsHelper.check_point_inside_polygon(box_points_1, point_obj)
                            )
                            points_inside_box_2.append(
                                GhostObjectsHelper.check_point_inside_polygon(box_points_2, point_obj)
                            )
                    cond_bool = (points_inside_box_1 and all(points_inside_box_1)) or (
                        points_inside_box_2 and all(points_inside_box_2)
                    )

                    if cond_bool:
                        return True
                return False

            def _calculate_start_mask_no_empty_boxes(self) -> bool:
                """Starting index for no empty bounding boxes is done after the scanning is finished"""
                mask = df[sg_parking_mode] == constants.ParkingMachineStates.PPC_SCANNING_IN
                idx_final_scan = mask[::-1].idxmax() if not mask[mask].empty else None

                if idx_final_scan:
                    mask_reset = mask.reset_index()
                    nb_idx_final_scan = mask_reset.index[mask_reset["index"] == idx_final_scan][0]

                    if mask.index[-1] == mask.index[nb_idx_final_scan]:
                        self._start_idx_no_empty_box = mask.index[nb_idx_final_scan]
                    else:
                        self._start_idx_no_empty_box = mask.index[nb_idx_final_scan + 1]
                    self.START_IDX_NO_EMPTY_BOX = self._start_idx_no_empty_box
                    return True
                return False

            def check_boxes_not_empty_kpi(
                self,
                static_obj_valid,
                ego_info: EgoInfo,
                box_points_1: ParkingBoxPoints,
                box_points_2: ParkingBoxPoints,
            ) -> bool:
                """Check if boxes are not empty (they contains objects inside at least one point \
                of the object has to be inside the bounding boxes)
                """
                points_inside_box_1 = []
                points_inside_box_2 = []

                for obj in static_obj_valid:
                    for i in range(0, len(self.static_obj_shape_dict[obj]), LocalConstantsHelper.STEP_X_COORD):
                        if (
                            self.static_obj_shape_dict[obj][i][self._start_idx_no_empty_box] != 0.0
                            and self.static_obj_shape_dict[obj][i + 1][self._start_idx_no_empty_box] != 0.0
                        ):
                            point_obj = transf_local_to_global(
                                self.static_obj_shape_dict[obj][i][self._start_idx_no_empty_box],
                                self.static_obj_shape_dict[obj][i + 1][self._start_idx_no_empty_box],
                                ego_info.ego_x,
                                ego_info.ego_y,
                                ego_info.ego_yaw,
                            )
                            points_inside_box_1.append(
                                GhostObjectsHelper.check_point_inside_polygon(box_points_1, point_obj)
                            )
                            points_inside_box_2.append(
                                GhostObjectsHelper.check_point_inside_polygon(box_points_2, point_obj)
                            )
                    cond_bool = (any(points_inside_box_1)) and (any(points_inside_box_2))

                    if cond_bool:
                        return True
                return False

        try:
            usem_test = USEMKPI()
            usem_test.run()

            if usem_test.error is None:

                if usem_test.NO_OBJ_OUTSIDE_BOXES == USEMKPI.FAILED:
                    self.usem_1_step = fc.FAIL
                if usem_test.BOXES_NOT_EMPTY == USEMKPI.FAILED:
                    self.usem_2_step = fc.FAIL
                if usem_test.OBJ_INSIDE_BOXES_ONE == USEMKPI.FAILED:
                    self.usem_3_step = fc.FAIL
                if self.usem_1_step is fc.PASS and self.usem_2_step is fc.PASS and self.usem_3_step is fc.PASS:
                    result_final = fc.PASS
                else:
                    result_final = fc.FAIL

                # Set condition strings
                cond_0 = " ".join("Start index should be present.".split())
                cond_1 = " ".join("Start index where there are no empty boxes should be present.".split())
                cond_2 = " ".join("Shape of the static objects should be present.".split())

                if usem_test.START_IDX is not None:
                    eval_cond[0] = True
                if usem_test.START_IDX_NO_EMPTY_BOX is not None:
                    eval_cond[1] = True
                if usem_test.STATIC_OBJ_SHAPE_DCT is not None:
                    eval_cond[2] = True

                # Set table dataframe
                signal_summary = pd.DataFrame(
                    {
                        "Name": {
                            "0": "",
                            "1": "USEM KPI 1",
                            "2": "",
                            "3": "",
                            "4": "",
                            "5": "",
                            "6": "USEM KPI 2",
                            "7": "",
                            "8": "",
                            "9": "",
                            "10": "",
                            "11": "USEM KPI 3",
                            "12": "",
                            "13": "",
                        },
                        "Condition": {
                            "0": cond_0,
                            "1": cond_1,
                            "2": cond_2,
                            "3": "No object must be present outside boxes.",
                            "4": "",
                            "5": cond_0,
                            "6": cond_1,
                            "7": cond_2,
                            "8": "At least one point of the object has to be inside the bounding boxes.",
                            "9": "",
                            "10": cond_0,
                            "11": cond_1,
                            "12": cond_2,
                            "13": "The number of objects inside a bounding box must be 1.",
                        },
                        "Result": {
                            "0": "Start index was found." if eval_cond[0] else "Start index was not found.",
                            "1": (
                                "Start index where there are no empty boxes was found."
                                if eval_cond[1]
                                else "Start index was not found."
                            ),
                            "2": (
                                "Shape of the static objects was found."
                                if eval_cond[2]
                                else "Shape of static object was not found."
                            ),
                            "3": (
                                "There is no object found."
                                if self.usem_1_step is fc.PASS
                                else "The number of objects found was > 0."
                            ),
                            "4": "",
                            "5": "Start index was found." if eval_cond[0] else "Start index was not found.",
                            "6": (
                                "Start index where there are no empty boxes was found."
                                if eval_cond[1]
                                else "Start index was not found."
                            ),
                            "7": (
                                "Shape of the static objects was found."
                                if eval_cond[2]
                                else "Shape of static object was not found."
                            ),
                            "8": (
                                "At least one valid point was available."
                                if self.usem_2_step is fc.PASS
                                else "No valid point was found."
                            ),
                            "9": "",
                            "10": "Start index was found." if eval_cond[0] else "Start index was not found.",
                            "11": (
                                "Start index where there are no empty boxes was found."
                                if eval_cond[1]
                                else "Start index was not found."
                            ),
                            "12": (
                                "Shape of the static objects was found."
                                if eval_cond[2]
                                else "Shape of static object was not found."
                            ),
                            "13": (
                                "The number of objects inside of a bounding box is 1."
                                if self.usem_3_step is fc.PASS
                                else "The number of objects inside of a bounding box is != 1."
                            ),
                        },
                        "Verdict": {
                            "0": "PASSED" if eval_cond[0] else "ACCEPTABLE",
                            "1": "PASSED" if eval_cond[1] else "ACCEPTABLE",
                            "2": "PASSED" if eval_cond[2] else "ACCEPTABLE",
                            "3": "PASSED" if self.usem_1_step is fc.PASS else "FAILED",
                            "4": "",
                            "5": "PASSED" if eval_cond[0] else "ACCEPTABLE",
                            "6": "PASSED" if eval_cond[1] else "ACCEPTABLE",
                            "7": "PASSED" if eval_cond[2] else "ACCEPTABLE",
                            "8": "PASSED" if self.usem_2_step is fc.PASS else "FAILED",
                            "9": "",
                            "10": "PASSED" if eval_cond[0] else "ACCEPTABLE",
                            "11": "PASSED" if eval_cond[1] else "ACCEPTABLE",
                            "12": "PASSED" if eval_cond[2] else "ACCEPTABLE",
                            "13": "PASSED" if self.usem_3_step is fc.PASS else "FAILED",
                        },
                    }
                )
                # Changes the colors of the table
                fill_color = [["rgb(80,103,132)"] * 14] * 4
                fill_color[0][4] = "rgb(33,39,43)"
                fill_color[0][9] = "rgb(33,39,43)"

                # Converting microseconds to seconds
                df[sg_time] = df[sg_time] / constants.GeneralConstants.US_IN_S
                # Converting epoch time to seconds passed
                df[sg_time] = df[sg_time] - df[sg_time].iat[0]

                self.sig_sum = go.Figure(
                    data=[
                        go.Table(
                            header=dict(
                                values=list(signal_summary.columns),
                                fill_color="rgb(255,165,0)",
                                font=dict(size=12, family="Arial", color="rgb(0,0,0)"),
                                align="center",
                            ),
                            cells=dict(
                                values=[signal_summary[col] for col in signal_summary.columns],
                                fill_color=fill_color,
                                height=37,
                                align="center",
                                font=dict(size=12),
                            ),
                        )
                    ]
                )
                self.sig_sum.update_layout(
                    constants.PlotlyTemplate.lgt_tmplt,
                    height=fh.calc_table_height(signal_summary["Condition"].to_dict()),
                )
                plot_titles.append("Condition Evaluation")
                plots.append(self.sig_sum)
                remarks.append("")

                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=df[sg_time].values.tolist(),
                        y=df[sg_parking_mode].values.tolist(),
                        mode="lines",
                        name=signal_name[sg_parking_mode],
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=df[sg_time].values.tolist(),
                        y=df[sg_nb_valid_static_obj].values.tolist(),
                        mode="lines",
                        name=signal_name[sg_nb_valid_static_obj],
                    )
                )

                fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]")
                fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
                plot_titles.append("Graphical Overview")
                plots.append(fig)
                remarks.append("")

                additional_results_dict = {
                    "Verdict": {"value": result_final.title(), "color": fh.get_color(result_final)},
                    "Name USEM KPIS-01": {"value": "No objects outside bounding boxes"},
                    "USEM KPIS-01 expected value": {"value": "1"},
                    "USEM KPIS-01 measured": {"value": usem_test.NO_OBJ_OUTSIDE_BOXES},
                    "Name USEM KPIS-02": {"value": "The bounding boxes are not empty"},
                    "USEM KPIS-02 expected value": {"value": "1"},
                    "USEM KPIS-02 measured": {"value": usem_test.BOXES_NOT_EMPTY},
                    "Name USEM KPIS-03": {"value": "The bounding boxes must contain only one object inside each"},
                    "USEM KPIS-03 expected value": {"value": "1"},
                    "USEM KPIS-03 measured": {"value": usem_test.OBJ_INSIDE_BOXES_ONE},
                }

            else:
                self.usem_1_step = fc.INPUT_MISSING
                self.usem_2_step = fc.INPUT_MISSING
                self.usem_3_step = fc.INPUT_MISSING

                print(f"Test failed, the following signal is missing:{str(usem_test.error)}")
                # write_log_message(
                # f"Test failed, the following signal is missing:{str(usem_test.error)}", "error", LOGGER)

                additional_results_dict = {
                    "Verdict": {"value": result_final.title(), "color": fh.get_color(result_final)},
                    "Name USEM KPIS-01": {"value": f"Signal missing: {str(usem_test.error)}"},
                    "USEM KPIS-01 expected value": {"value": ""},
                    "USEM KPIS-01 measured": {"value": ""},
                    "Name USEM KPIS-02": {"value": ""},
                    "USEM KPIS-02 expected value": {"value": ""},
                    "USEM KPIS-02 measured": {"value": ""},
                    "Name USEM KPIS-03": {"value": ""},
                    "USEM KPIS-03 expected value": {"value": ""},
                    "USEM KPIS-03 measured": {"value": ""},
                }

        except Exception as err:
            self.usem_1_step = fc.INPUT_MISSING
            self.usem_2_step = fc.INPUT_MISSING
            self.usem_3_step = fc.INPUT_MISSING
            result_final = fc.INPUT_MISSING

            print(f"Test failed, the following signal is missing:{str(err)}")
            # write_log_message(f"Test failed, the following signal is missing:{str(err)}", "error", LOGGER)

            additional_results_dict = {
                "Verdict": {"value": result_final.title(), "color": fh.get_color(result_final)},
                "Name USEM KPIS-01": {"value": f"Signal missing: {str(err)}"},
                "USEM KPIS-01 expected value": {"value": ""},
                "USEM KPIS-01 measured": {"value": ""},
                "Name USEM KPIS-02": {"value": ""},
                "USEM KPIS-02 expected value": {"value": ""},
                "USEM KPIS-02 measured": {"value": ""},
                "Name USEM KPIS-03": {"value": ""},
                "USEM KPIS-03 expected value": {"value": ""},
                "USEM KPIS-03 measured": {"value": ""},
            }
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")

        if result_final == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="MF USEM KPI",
    description=(
        "Check if there is not an object outside bounding boxes starting with first object detection until the end of"
        " the test Check if the bounding boxes are not empty after scanning Check if the bounding boxes contains only"
        " one object inside each starting with first object detection until the end of the test"
    ),
)
class FtGroundTruthBoundingBox(TestCase):
    """Test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtGroundTruthBoundingBox]
