"""Functional test for SI slot shrinkage"""

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
from pl_parking.PLP.MF.constants import ConstantsSiSlotShrinkage as si_const
from pl_parking.PLP.MF.ENTRY.usemLagLeadShrinkHelper import ParkingSlotHelper
from pl_parking.PLP.MF.ft_helper import ExampleSignals

SIGNAL_DATA = "MF_SI_SLOT_SHRINKAGE"

example_obj = EntrySignals()


@teststep_definition(
    step_number=1,
    name="SI SLOT SHRINKAGE",
    description=(
        " Base class for computing the SI slot shrinkage in several different cases.         Provides the necessary"
        " masks for computing the start position leading to the initial value of the coordinates coordinates,        "
        " when state is PPC_PERFORM_PARKING (in signal M7board.EM_Thread.PSMDebugPort.stateVarPPC_nu), PPC_PARKING_MODE"
        " is PARK_IN         (in signal M7board.EM_Thread.CtrlCommandPort.ppcParkingMode_nu),         and a single"
        " parking box has been selected (M7board.EM_Thread.ApParkingBoxPort.numValidParkingBoxes_nu)."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ExampleSignals)
class TestStepFtParkingSISlotShrinkage(TestStep):
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
        sg_ppc_park_mode = "ppcParkingMode"
        sg_slotcoordinates = "SlotCoordinates"
        sg_nb_valid_parking_boxs = "NumberOfValidParkingBoxes"

        _parking_mode_mask = None
        _state_start_mask = None
        _state_var = None
        _nb_valid_pb_mask = None
        _start_mask = None
        _final_mask = None
        signal_name = example_obj._properties

        class SISlotShrinkageHil:
            """
            HIL SI Slot Shrinkage
            Shrinkage of SI box
            Difference of SI box at the beginning and the end of the park in manoeuvre in cm
            """

            def __init__(self):
                """Initialize object attributes."""
                self.result = None

            def _calculate_slot_shrinkage(self):
                if _start_mask[_start_mask.idxmax()] and _final_mask[_final_mask.idxmax()]:
                    [start_coordinates, final_coordinates] = ParkingSlotHelper.extract_slot_coordinates(
                        df, _start_mask.idxmax(), _final_mask.idxmax(), sg_slotcoordinates
                    )

                    # Calculate the slot shrinkage
                    start_parking_box_width_m = self.__calc_width(start_coordinates)
                    final_parking_box_width_m = self.__calc_width(final_coordinates)
                    start_parking_box_width_m = self.__remove_sampling_frequency_issue(
                        _start_mask, start_parking_box_width_m
                    )
                    slot_shrinkage_cm = (
                        start_parking_box_width_m - final_parking_box_width_m
                    ) * constants.GeneralConstants.M_TO_CM

                    measured_result = slot_shrinkage_cm
                else:
                    measured_result = constants.DgpsConstants.INVALID_VALUE_SLOT_SHRINKAGE

                self.result = measured_result

            def __remove_sampling_frequency_issue(self, mask, width):
                """Remove possible issue due to sampling frequency
                :param signals: instance of SignalDataFrame class with the desired signals read from the bsig file
                :param mask: instance of SeriesDataFrame with the mask
                :param width: width of the parking box
                :return : the width of the parking box after removing of sampling frequency issue if is the case
                """
                new_mask = mask.reset_index()
                start_index = new_mask.index[new_mask["TimeStamp"] == mask.idxmax()]

                for i in range(start_index[0], (len(mask) - 1)):
                    if (
                        (mask.index[i] - mask.index[start_index[0]]) / constants.GeneralConstants.US_IN_S
                    ) < constants.SiSlotShrinkageConstants.THRESOLD_TIME_S:
                        slot_coordinates_time = []

                        for j in range(constants.ParkingBoxConstants.NB_COORDINATES):
                            slot_coordinates_time.append(df[sg_slotcoordinates][mask.index[i]][j])

                        if (
                            slot_coordinates_time[constants.ParkingBoxConstants.X_COORD_LEFT_BOTTOM] != 0
                            and slot_coordinates_time[constants.ParkingBoxConstants.X_COORD_RIGHT_BOTTOM] != 0
                        ):
                            width_temp = self.__calc_width(slot_coordinates_time)
                            if abs(width - width_temp) > constants.SiSlotShrinkageConstants.THRESOLD_WIDTH_M:
                                return width_temp
                    else:
                        break
                return width

            @staticmethod
            def __calc_width(coordinates: list) -> float:
                """Calculate the width
                :param coordinates: list with x,y coordinates of the corners of the parking box
                :return: the width of the parking box
                """
                point_left_top = np.array(
                    [
                        coordinates[constants.ParkingBoxConstants.X_COORD_LEFT_TOP],
                        coordinates[constants.ParkingBoxConstants.Y_COORD_LEFT_TOP],
                    ]
                )
                point_right_top = np.array(
                    [
                        coordinates[constants.ParkingBoxConstants.X_COORD_RIGHT_TOP],
                        coordinates[constants.ParkingBoxConstants.Y_COORD_RIGHT_TOP],
                    ]
                )
                point_left_bottom = np.array(
                    [
                        coordinates[constants.ParkingBoxConstants.X_COORD_LEFT_BOTTOM],
                        coordinates[constants.ParkingBoxConstants.Y_COORD_LEFT_BOTTOM],
                    ]
                )
                point_right_bottom = np.array(
                    [
                        coordinates[constants.ParkingBoxConstants.X_COORD_RIGHT_BOTTOM],
                        coordinates[constants.ParkingBoxConstants.Y_COORD_RIGHT_BOTTOM],
                    ]
                )

                width_1 = np.linalg.norm(point_left_top - point_right_top)
                width_2 = np.linalg.norm(point_left_bottom - point_right_bottom)

                return min(width_1, width_2)

        class CheckConditions:
            """Check if all conditions are true at the same time"""

            def __init__(self) -> None:
                """Initialize object attributes."""
                self.test_result: str = fc.INPUT_MISSING
                self.sig_sum = None
                self.fig = None

            def run(self, result):
                signal_summary = {}
                eval_cond = [False] * 6

                # Set condition strings
                cond_0 = " ".join(
                    f"Parking mode should be PARK_IN({constants.ParkingModes.PARK_IN})                or"
                    f" GARAGE_PARKING_IN({constants.ParkingModes.GARAGE_PARKING_IN})                 in signal"
                    f" {signal_name[sg_ppc_park_mode]}.".split()
                )
                cond_1 = " ".join(
                    "Parking state should be PPC_PERFORM_PARKING                "
                    f" ({constants.ParkingMachineStates.PPC_PERFORM_PARKING}) in signal {signal_name[sg_parking_mode]}.".split()
                )
                cond_2 = " ".join(
                    f"Number of valid parking boxes should be {si_const.NUMBER_OF_BOXES} in signal                "
                    f" {signal_name[sg_nb_valid_parking_boxs]}.".split()
                )
                cond_3 = " ".join("All the conditions from above should be true at the same time.".split())
                cond_4 = " ".join(f"Measured result should be within range {si_const.SI_SHRINKAGE_RANGE} cm.".split())
                cond_5 = " ".join("There should exist a set of final coordinates.".split())

                if _parking_mode_mask.any():
                    eval_cond[0] = True
                if _state_start_mask.any():
                    eval_cond[1] = True
                if _nb_valid_pb_mask.any():
                    eval_cond[2] = True
                if _start_mask.any():
                    eval_cond[3] = True

                if result > si_const.SI_SHRINKAGE_RANGE[0] and result < si_const.SI_SHRINKAGE_RANGE[1]:
                    eval_cond[4] = True

                if _final_mask.any():
                    eval_cond[5] = True

                if all(eval_cond):
                    self.test_result = True
                else:
                    self.test_result = False

                # Set table dataframe
                signal_summary = pd.DataFrame(
                    {
                        "Conditions": {
                            "0": cond_0,
                            "1": cond_1,
                            "2": cond_2,
                            "3": cond_3,
                            "4": cond_4,
                            "5": cond_5,
                        },
                        "Result": {
                            "0": (
                                " ".join(
                                    f"Parking mode PARK_IN({constants.ParkingModes.PARK_IN})                    was"
                                    " found.".split()
                                )
                                if any(ppc_parking_mode == constants.ParkingModes.PARK_IN)
                                else (
                                    " ".join(
                                        f"Parking mode GARAGE_PARKING_IN({constants.ParkingModes.GARAGE_PARKING_IN})   "
                                        "                 was found.".split()
                                    )
                                    if any(ppc_parking_mode == constants.ParkingModes.GARAGE_PARKING_IN)
                                    else " ".join("No parking                     mode was found.".split())
                                )
                            ),
                            "1": (
                                " ".join(
                                    "Parking state PPC_PERFORM_PARKING"
                                    f" ({constants.ParkingMachineStates.PPC_PERFORM_PARKING})                    was"
                                    " found.".split()
                                )
                                if eval_cond[1]
                                else " ".join(
                                    "Parking state PPC_PERFORM_PARKING                   "
                                    f" ({constants.ParkingMachineStates.PPC_PERFORM_PARKING}) was not found.".split()
                                )
                            ),
                            "2": (
                                f"Number of valid parking boxes = {si_const.NUMBER_OF_BOXES}."
                                if eval_cond[2]
                                else "Invalid parking box."
                            ),
                            "3": (
                                " ".join("All of the above conditions were fulfiled at the same time.".split())
                                if eval_cond[4]
                                else " ".join(f"A number of {eval_cond.count(False)} conditions were false.".split())
                            ),
                            "4": " ".join(f"Measured result is {result:.3f} cm.".split()),
                            "5": (
                                "A set of final coordinates was found."
                                if eval_cond[5]
                                else "No coordinate set was found."
                            ),
                        },
                        "Verdict": {
                            "0": "PASSED" if eval_cond[0] else "FAILED",
                            "1": "PASSED" if eval_cond[1] else "FAILED",
                            "2": "PASSED" if eval_cond[2] else "FAILED",
                            "3": "PASSED" if eval_cond[3] else "FAILED",
                            "4": "PASSED" if eval_cond[4] else "FAILED",
                            "5": "PASSED" if eval_cond[5] else "FAILED",
                        },
                    }
                )

                self.sig_sum = go.Figure(
                    data=[
                        go.Table(
                            columnwidth=[38, 35, 5],
                            header=dict(
                                values=["Signal Evaluation", "Summary"],
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
                    height=fh.calc_table_height(signal_summary["Conditions"].to_dict()),
                )

        try:
            df.set_index(sg_time, inplace=True)
            _state_var = df[sg_parking_mode]
            nb_valid_pb = df[sg_nb_valid_parking_boxs]
            ppc_parking_mode = df[sg_ppc_park_mode]
            _parking_mode_mask = (ppc_parking_mode == constants.ParkingModes.PARK_IN) | (
                ppc_parking_mode == constants.ParkingModes.GARAGE_PARKING_IN
            )
            _state_start_mask = _state_var == constants.ParkingMachineStates.PPC_PERFORM_PARKING
            _nb_valid_pb_mask = nb_valid_pb == 1
            _start_mask = _parking_mode_mask & _state_start_mask & _nb_valid_pb_mask

            if _nb_valid_pb_mask.any():
                _final_mask = _nb_valid_pb_mask[_nb_valid_pb_mask].iloc[[-1]]
            else:
                _final_mask = _nb_valid_pb_mask.iloc[[0]]

            si_slot_test = SISlotShrinkageHil()
            si_slot_test._calculate_slot_shrinkage()

            # Converting microseconds to seconds
            df.index = df.index / constants.GeneralConstants.US_IN_S  # constants.GeneralConstants.US_TO_S
            # Converting epoch time to seconds passed
            df.index = df.index - df.index[0]

            check_conditions = CheckConditions()
            check_conditions.run(si_slot_test.result)

            if check_conditions.test_result is True:
                result_final = fc.PASS

            else:
                result_final = fc.FAIL

            plot_titles.append("Condition Evaluation")
            plots.append(check_conditions.sig_sum)
            remarks.append("Check if all conditions are true")

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df.index.values.tolist(),
                    y=df[sg_parking_mode].values.tolist(),
                    mode="lines",
                    name=signal_name[sg_parking_mode],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df.index.values.tolist(),
                    y=df[sg_ppc_park_mode].values.tolist(),
                    mode="lines",
                    name=signal_name[sg_ppc_park_mode],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df.index.values.tolist(),
                    y=df[sg_nb_valid_parking_boxs].values.tolist(),
                    mode="lines",
                    name=signal_name[sg_nb_valid_parking_boxs],
                )
            )

            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            plot_titles.append("Graphical Overview")
            plots.append(fig)
            remarks.append("")

            additional_results_dict = {
                "Verdict": {"value": result_final.title(), "color": fh.get_color(result_final)},
                "Name": {"value": "Difference of SI box at the beginning and the end of the park in maneuver in cm."},
                "Expected [cm]": {"value": f"{si_const.SI_SHRINKAGE_RANGE}"},
                "Measured [cm]": {"value": round(si_slot_test.result, 2)},
            }
        except Exception as err:
            result_final = fc.INPUT_MISSING
            print(str(err))
            # write_log_message(f"Test failed, the following signal is missing:{str(err)}", "error", LOGGER)
            additional_results_dict = {
                "Verdict": {"value": result_final.title(), "color": fh.get_color(result_final)},
                "Name": {"value": f"Signal missing: { str(err)}"},
                "Expected [cm]": {"value": ""},
                "Measured [cm]": {"value": ""},
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
    name="MF SI SLOT SHRINKAGE",
    description=(
        " Base class for computing the SI slot shrinkage in several different cases. Provides the necessary masks for"
        " computing the start position leading to the initial value of the coordinates coordinates, when state is"
        " PPC_PERFORM_PARKING (in signal M7board.EM_Thread.PSMDebugPort.stateVarPPC_nu), PPC_PARKING_MODE is PARK_IN"
        " (in signal M7board.EM_Thread.CtrlCommandPort.ppcParkingMode_nu), and a single parking box has been selected"
        " (M7board.EM_Thread.ApParkingBoxPort.numValidParkingBoxes_nu). "
    ),
)
class FtParkingSISlotShrinkage(TestCase):
    """Test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtParkingSISlotShrinkage]
