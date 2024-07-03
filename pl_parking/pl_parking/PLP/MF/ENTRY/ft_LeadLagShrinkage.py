"""Functional test for lead lag shrinkage"""

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

import numpy as np
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
from pl_parking.PLP.MF.constants import ConstantsUsemLeagLagShrinkage as usem_const
from pl_parking.PLP.MF.ENTRY.ft_dgps_helper import DgpsSignalsProcessing
from pl_parking.PLP.MF.ENTRY.usemLagLeadShrinkHelper import EgoInfo, LeadLagPointsHelper, ParkingSlotHelper
from pl_parking.PLP.MF.ft_helper import ExampleSignals

SIGNAL_DATA = "MF_USEM_LEAD_LAG_SHRINKAGE"

example_obj = EntrySignals()


@teststep_definition(
    step_number=1,
    name="USEM LEAD LAG SHRINKAGE",
    description="HIL Lag Point HIL Lead Point HIL Slot Shrinkage",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ExampleSignals)
class TestStepFtParkingUsemLeadLagShrinkage(TestStep):
    """Test step class"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize test step."""
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
        result_list = [fc.INPUT_MISSING] * 3
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)
        signal_name = example_obj._properties

        # Defining signal variables for signal handling
        sg_time = "TimeStamp"
        sg_parking_mode = "PSMDebugPort"
        sg_ppc_park_mode = "ppcParkingMode"
        sg_slot_coordinates = "SlotCoordinates"
        sg_slot_coordinates_1 = "SlotCoordinates1"
        sg_slot_coordinates_2 = "SlotCoordinates2"
        sg_ego = "EgoPositionAP"
        sg_nb_valid_static_obj = "NumberValidStaticObjects"

        lag_cm = constants.DgpsConstants.INVALID_VALUE_SLOT_SHRINKAGE
        lead_cm = constants.DgpsConstants.INVALID_VALUE_SLOT_SHRINKAGE

        _nearest_point_left = None
        _nearest_point_right = None
        start_coordinates = []
        _start_mask = None
        _final_mask = None
        _valid_parkin = False
        parking_mode_mask = None
        state_start_mask = None
        state_final_mask = None
        empty_box_1_mask = None
        empty_box_2_mask = None

        class UsemLeadLagShrinkageHilTestCase:
            def __init__(self):
                """Initialize object attributes."""
                self.result = fc.INPUT_MISSING
                self.lag_res = fc.INPUT_MISSING
                self.lead_res = fc.INPUT_MISSING
                self.usem_shrk_res = fc.INPUT_MISSING
                self.shrinkage_cm = constants.DgpsConstants.INVALID_VALUE_SLOT_SHRINKAGE

            def run(self):
                # Checks left side shrinkage in cm

                if lag_cm > usem_const.LAG_RANGE[0] and lag_cm < usem_const.LAG_RANGE[1]:
                    self.lag_res = fc.PASS
                else:
                    self.lag_res = fc.FAIL

                # Checks right side shrinkage in cm
                if lead_cm > usem_const.LEAD_RANGE[0] and lead_cm < usem_const.LEAD_RANGE[1]:
                    self.lead_res = fc.PASS
                else:
                    self.lead_res = fc.FAIL

                # Checks total shrinkage in cm
                if (
                    lag_cm != constants.DgpsConstants.INVALID_VALUE_SLOT_SHRINKAGE
                    or lead_cm != constants.DgpsConstants.INVALID_VALUE_SLOT_SHRINKAGE
                ):
                    self.shrinkage_cm = 0.0
                    if lag_cm < constants.DgpsConstants.INVALID_VALUE_SLOT_SHRINKAGE:
                        self.shrinkage_cm += lag_cm
                    if lead_cm < constants.DgpsConstants.INVALID_VALUE_SLOT_SHRINKAGE:
                        self.shrinkage_cm += lead_cm

                if np.isnan(lag_cm):
                    self.shrinkage_cm = lag_cm

                if (
                    self.shrinkage_cm > usem_const.SLOT_SHRINKAGE_RANGE[0]
                    and self.shrinkage_cm < usem_const.SLOT_SHRINKAGE_RANGE[1]
                ):
                    self.usem_shrk_res = fc.PASS
                else:
                    self.usem_shrk_res = fc.FAIL

                if self.lead_res is fc.PASS and self.lag_res is fc.PASS and self.usem_shrk_res is fc.PASS:
                    self.result = fc.PASS
                else:
                    self.result = fc.FAIL

        class CheckConditions:
            """Check if all conditions are true at the same time"""

            def __init__(self) -> None:
                """Initialize object attributes."""
                self.test_result: str = fc.INPUT_MISSING
                self.sig_sum = None
                self.fig = None

            def run(self):
                signal_summary = {}
                eval_cond = [False] * 9

                # Set condition strings
                cond_0 = " ".join(
                    f"PARK_IN ({constants.ParkingModes.PARK_IN}) or GARAGE_PARKING_IN                    "
                    f" ({constants.ParkingModes.GARAGE_PARKING_IN}) modes should be present                     in"
                    f" signal {signal_name[sg_ppc_park_mode]}.".split()
                )
                cond_1 = " ".join(
                    f"PPC_PERFORM_PARKING state({constants.ParkingMachineStates.PPC_PERFORM_PARKING}) should be present"
                    f"                    in signal {signal_name[sg_parking_mode]}.".split()
                )
                cond_2 = " ".join(
                    f"PPC_SUCCESS state({constants.ParkingMachineStates.PPC_SUCCESS}) should be present                "
                    f"     in signal {signal_name[sg_parking_mode]}.".split()
                )
                cond_3 = " ".join(
                    f"The value of signal {signal_name[sg_slot_coordinates_1]}                     at index 0 should"
                    " be 0.".split()
                )
                cond_4 = " ".join(
                    f"The value of signal {signal_name[sg_slot_coordinates_2]}                     at index 0 should"
                    " be 0.".split()
                )
                cond_5 = " ".join(
                    "All of the above conditions should be fulfilled at the same time, with parking state set to      "
                    f"               PPC_PERFORM_PARKING in signal {signal_name[sg_parking_mode]}.".split()
                )
                cond_6 = " ".join(
                    "All of the above conditions should be fulfilled at the same time, with parking state set to      "
                    f"               PPC_SUCCESS({constants.ParkingMachineStates.PPC_SUCCESS}) in                    "
                    f" signal {signal_name[sg_parking_mode]}.".split()
                )
                cond_7 = " ".join("Parking operation should be valid.".split())
                cond_8 = " ".join(f"Left side shrinkage should be within range of {usem_const.LAG_RANGE} cm.".split())
                cond_9 = " ".join(f"Right side shrinkage should be within range of {usem_const.LEAD_RANGE} cm.".split())
                cond_10 = " ".join(
                    f"Total shrinkage should be within range of {usem_const.SLOT_SHRINKAGE_RANGE} cm.".split()
                )

                if parking_mode_mask.any():
                    eval_cond[0] = True
                if state_start_mask.any():
                    eval_cond[1] = True
                if state_final_mask.any():
                    eval_cond[2] = True
                if empty_box_1_mask.any():
                    eval_cond[3] = True
                if empty_box_2_mask.any():
                    eval_cond[4] = True
                if _start_mask.any():
                    eval_cond[5] = True
                if _final_mask.any():
                    eval_cond[6] = True
                if _valid_parkin.any():
                    eval_cond[7] = True
                if usem_tst.result is fc.PASS:
                    eval_cond[8] = True

                if all(eval_cond):
                    self.test_result = fc.PASS
                else:
                    self.test_result = fc.FAIL

                # Set table dataframe
                signal_summary = pd.DataFrame(
                    {
                        "Condition": {
                            "0": cond_0,
                            "1": cond_1,
                            "2": cond_2,
                            "3": cond_3,
                            "4": cond_4,
                            "5": cond_5,
                            "6": cond_6,
                            "7": cond_7,
                            "8": cond_8,
                            "9": cond_9,
                            "10": cond_10,
                        },
                        "Results": {
                            "0": (
                                " ".join(
                                    f"Parking mode PARK_IN({constants.ParkingModes.PARK_IN})                        was"
                                    " found.".split()
                                )
                                if any(ppc_parking_mode == constants.ParkingModes.PARK_IN)
                                else (
                                    " ".join(
                                        "Parking mode GARAGE_PARKING_IN                       "
                                        f" ({constants.ParkingModes.GARAGE_PARKING_IN}) was found.".split()
                                    )
                                    if any(ppc_parking_mode == constants.ParkingModes.GARAGE_PARKING_IN)
                                    else " ".join("No parking mode was found.".split())
                                )
                            ),
                            "1": (
                                " ".join(
                                    "Parking state PPC_PERFORM_PARKING"
                                    f" ({constants.ParkingMachineStates.PPC_PERFORM_PARKING})                       "
                                    " was found.".split()
                                )
                                if eval_cond[1]
                                else " ".join(
                                    "Parking state PPC_PERFORM_PARKING                        "
                                    f" ({constants.ParkingMachineStates.PPC_PERFORM_PARKING}) was not found.".split()
                                )
                            ),
                            "2": (
                                " ".join(
                                    f"Parking state PPC_SUCCESS ({constants.ParkingMachineStates.PPC_SUCCESS})         "
                                    "               was found.".split()
                                )
                                if eval_cond[2]
                                else " ".join(
                                    "Parking state PPC_SUCCESS                        "
                                    f" ({constants.ParkingMachineStates.PPC_PERFORM_PARKING}) was not found.".split()
                                )
                            ),
                            "3": (
                                "The value at the first index = 0."
                                if eval_cond[3]
                                else "The value at the first index != 0."
                            ),
                            "4": (
                                "The value at the first index = 0."
                                if eval_cond[4]
                                else "The value at the first index != 0."
                            ),
                            "5": (
                                "All of the above conditions were fulfiled at the same time."
                                if eval_cond[5]
                                else " ".join(
                                    f"A number of {eval_cond[:4].count(False)} conditions were                         "
                                    "                set to ACCEPTABLE.".split()
                                )
                            ),
                            "6": (
                                "All of the above conditions were fulfiled at the same time."
                                if eval_cond[6]
                                else " ".join(
                                    f"A number of {eval_cond[:7].count(False)} conditions were                         "
                                    "                set to ACCEPTABLE.".split()
                                )
                            ),
                            "7": "Parking operation is valid." if eval_cond[7] else "Parking operation is not valid.",
                            "8": f"Value found: {lag_cm:.2f} cm.",
                            "9": f"Value found: {lead_cm:.2f} cm.",
                            "10": f"Value found: {usem_tst.shrinkage_cm:.2f} cm.",
                        },
                        "Verdict": {
                            "0": "PASSED" if eval_cond[0] else "ACCEPTABLE",
                            "1": "PASSED" if eval_cond[1] else "ACCEPTABLE",
                            "2": "PASSED" if eval_cond[2] else "ACCEPTABLE",
                            "3": "PASSED" if eval_cond[3] else "ACCEPTABLE",
                            "4": "PASSED" if eval_cond[4] else "ACCEPTABLE",
                            "5": "PASSED" if eval_cond[5] else "ACCEPTABLE",
                            "6": "PASSED" if eval_cond[6] else "ACCEPTABLE",
                            "7": "PASSED" if eval_cond[7] else "ACCEPTABLE",
                            "8": "PASSED" if usem_tst.lag_res is fc.PASS else "FAILED",
                            "9": "PASSED" if usem_tst.lead_res is fc.PASS else "FAILED",
                            "10": "PASSED" if usem_tst.usem_shrk_res is fc.PASS else "FAILED",
                        },
                    }
                )

                self.sig_sum = go.Figure(
                    data=[
                        go.Table(
                            columnwidth=[40, 20, 7],
                            header=dict(
                                values=list(signal_summary.columns),
                                fill_color="rgb(255,165,0)",
                                font=dict(size=12, family="Arial", color="rgb(0,0,0)"),
                                align="center",
                            ),
                            cells=dict(
                                values=[signal_summary[col] for col in signal_summary.columns],
                                height=40,
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

        try:
            ppc_parking_mode = df[sg_ppc_park_mode]
            state_var = df[sg_parking_mode]
            slot_coordinates_box_1 = df[sg_slot_coordinates_1].str[0]
            slot_coordinates_box_2 = df[sg_slot_coordinates_2].str[0]
            ego_x_coord = df[sg_ego].str[constants.EgoPoseApConstants.X_COORD]
            ego_y_coord = df[sg_ego].str[constants.EgoPoseApConstants.Y_COORD]
            ego_yaw_coord = df[sg_ego].str[constants.EgoPoseApConstants.YAW_ANGLE]
            nb_valid_static_obj = df[sg_nb_valid_static_obj]

            # Filtering the signals to obtain them when ego is starting/finishing the park-in maneuver
            parking_mode_mask = (ppc_parking_mode == constants.ParkingModes.PARK_IN) | (
                ppc_parking_mode == constants.ParkingModes.GARAGE_PARKING_IN
            )
            state_start_mask = state_var == constants.ParkingMachineStates.PPC_PERFORM_PARKING
            state_final_mask = state_var == constants.ParkingMachineStates.PPC_SUCCESS
            empty_box_1_mask = slot_coordinates_box_1 == 0
            empty_box_2_mask = slot_coordinates_box_2 == 0
            _start_mask = parking_mode_mask & state_start_mask & empty_box_1_mask & empty_box_2_mask
            _final_mask = parking_mode_mask & state_final_mask & empty_box_1_mask & empty_box_2_mask

            # Calculate if the parking in maneuver is valid or not.
            # Parking in maneuver needs to start (PPC_PERFORM_PARKING)
            _valid_parkin = _start_mask[_start_mask.idxmax()]
            if _valid_parkin:

                # Obtain the x,y coordinates of the parking box when ego is starting/finishing the park-in maneuver
                [start_coordinates, _final_coordinates] = ParkingSlotHelper.extract_slot_coordinates(
                    df, _start_mask.idxmax(), _final_mask.idxmax(), sg_slot_coordinates
                )
                # Obtain ego x,y and yaw angle for start/ final parking maneuver
                ego_info_start = EgoInfo(
                    ego_x_coord[_start_mask.idxmax()],
                    ego_y_coord[_start_mask.idxmax()],
                    ego_yaw_coord[_start_mask.idxmax()],
                )

                # Calculate the distance of the closest static object point to parking box (left/right side)
                obj_lead_lag_help = LeadLagPointsHelper()

                # store_vector_signals TAKES 5 SECONDS
                # TO REDUCE
                static_obj_shape_dict = obj_lead_lag_help.store_vector_signals(
                    df,
                    constants.StaticObjectsShapeConstants.NAME_COLUMN_DF,
                    constants.StaticObjectsShapeConstants.NB_OBJ_SHAPE,
                )

                static_obj_valid_start = list(static_obj_shape_dict)[: nb_valid_static_obj[_start_mask.idxmax()]]

                [points_on_left_side, points_on_right_side] = obj_lead_lag_help.obtain_points_on_sides(
                    static_obj_shape_dict,
                    static_obj_valid_start,
                    start_coordinates,
                    _start_mask.idxmax(),
                    ego_info_start,
                )

                obj_lead_lag_help.extract_nearest_points_to_slot_sides(
                    points_on_left_side, points_on_right_side, start_coordinates
                )

                _nearest_point_left = obj_lead_lag_help.nearest_point_left
                _nearest_point_right = obj_lead_lag_help.nearest_point_right

                dgps_processing = DgpsSignalsProcessing(df)

                dgps_processing.process()

                signals = dgps_processing.get_signals()

                [points_left, points_right] = DgpsSignalsProcessing.extract_points_side_lines_dgps_boxes(
                    signals, _start_mask.idxmax()
                )

                [lead_cm, lag_cm] = LeadLagPointsHelper.calc_lead_lag_shrink(
                    points_left, points_right, _nearest_point_left, _nearest_point_right
                )

            usem_tst = UsemLeadLagShrinkageHilTestCase()
            usem_tst.run()

            check_conditions = CheckConditions()
            check_conditions.run()

            if check_conditions.test_result is fc.PASS:
                result_final = fc.PASS
            else:
                result_final = fc.FAIL

            result_list[0] = usem_tst.lag_res
            result_list[1] = usem_tst.lead_res
            result_list[2] = usem_tst.usem_shrk_res

            # Converting microseconds to seconds
            df[sg_time] = df[sg_time] / constants.GeneralConstants.US_IN_S
            # Converting epoch time to seconds passed
            df[sg_time] = df[sg_time] - df[sg_time].iat[0]

            plot_titles.append("Condition Evaluation")
            plots.append(check_conditions.sig_sum)
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
                    y=df[sg_ppc_park_mode].values.tolist(),
                    mode="lines",
                    name=signal_name[sg_ppc_park_mode],
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
                "Name HIL Lag Point": {"value": "Left side shrinkage"},
                "Expected-01 [cm]": {"value": f"{usem_const.LAG_RANGE}"},
                "Measured-01 [cm]": {"value": round(lag_cm, 2)},
                "Name HIL Lead Point": {"value": "Right side shrinkage"},
                "Expected-02 [cm]": {"value": f"{usem_const.LEAD_RANGE}"},
                "Measured-02 [cm]": {"value": round(lead_cm, 2)},
                "Name HIL Slot Shrinkage": {"value": "Total shrinkage"},
                "Expected-03 [cm]": {"value": f"{usem_const.SLOT_SHRINKAGE_RANGE}"},
                "Measured-03 [cm]": {"value": round(usem_tst.shrinkage_cm, 2)},
            }
        except Exception as err:
            result_final = fc.INPUT_MISSING
            print(f"Test failed, the following signal is missing:{str(err)}")
            # write_log_message(f"Test failed, the following signal is missing:{str(err)}", "error", LOGGER)
            additional_results_dict = {
                "Verdict": {"value": result_final.title(), "color": fh.get_color(result_final)},
                "Name HIL Lag Point": {"value": f"Signal missing: { str(err)}"},
                "Expected-01 [cm]": {"value": ""},
                "Measured-01 [cm]": {"value": ""},
                "Name HIL Lead Point": {"value": ""},
                "Expected-02 [cm]": {"value": ""},
                "Measured-02 [cm]": {"value": ""},
                "Name HIL Slot Shrinkage": {"value": ""},
                "Expected-03 [cm]": {"value": ""},
                "Measured-03 [cm]": {"value": ""},
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
    name="MF USEM LEAD LAG SHRINKAGE",
    description="HIL Lag Point HIL Lead Point HIL Slot Shrinkage",
)
class FtParkingUsemLeadLagShrinkage(TestCase):
    """Test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtParkingUsemLeadLagShrinkage]
