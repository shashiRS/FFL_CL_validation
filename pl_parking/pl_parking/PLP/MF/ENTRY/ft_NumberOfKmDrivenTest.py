"""Functional test for number of driven kilometers"""

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
from pl_parking.PLP.MF.ft_helper import ExampleSignals

SIGNAL_DATA = "MF_KM_DRIVEN"

example_obj = EntrySignals()


@teststep_definition(
    step_number=1,
    name="KM DRIVEN",
    description=(
        " Evaluates the number of Km driven during the recording by using the signal"
        " M7board.EM_Thread.EgoMotionPort.drivenDistance_m. If the signal is empty, 0 will be returned. The signal goes"
        " up to 999 and then wraps around to 0 when it goes above 1000, this is handled by 'wrap_number' variable. "
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ExampleSignals)
class TestStepFtParkingSlotTypeBase(TestStep):
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
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)

        # Defining signal variables for signal handling
        sg_km_driven = "NumberOfKmDriven"
        sg_time = "TimeStamp"
        sg_parking_mode = "PSMDebugPort"

        signal_summary = {}
        eval_cond = [False] * 5
        signal_name = example_obj._properties
        distance_driven = None

        try:
            # Converting microseconds to seconds
            df[sg_time] = df[sg_time] / constants.GeneralConstants.US_IN_S
            # Converting epoch time to seconds passed
            df[sg_time] = df[sg_time] - df[sg_time].iat[0]
            df[sg_km_driven] = df[sg_km_driven] - df[sg_km_driven].iat[0]
            distance_recording = df[sg_km_driven]
            scanning_in_mask = df[sg_parking_mode] == constants.ParkingMachineStates.PPC_SCANNING_IN
            distance_recording = distance_recording[scanning_in_mask]
            driven_km = distance_recording[distance_recording > 0]
            km_array = driven_km.to_numpy()

            # Convert dataframes to lists
            time_lst = df[sg_time].values.tolist()
            prk_mod_lst = df[sg_parking_mode].values.tolist()
            km_driven_list = df[sg_km_driven].values.tolist()

            #####################
            # The signal goes up to 999 and then wraps around to 0 when it goes above 1000,
            # this is handled by "wrap_number" variable

            # TODO # This must be tested when signal goes over 999
            diff_array = np.diff(km_array)
            wrap_number = np.count_nonzero(diff_array < 0)

            try:
                distance_driven = km_array[-1] - km_array[0] + wrap_number * constants.ConstantsNumberKmDriven.KM_TO_M
                distance_driven /= constants.GeneralConstants.KM_TO_M
            except IndexError:
                distance_driven = 0

            # Set condition strings
            cond_0 = " ".join(
                "Parking state should be set to PPC_SCANNING_IN                "
                f" ({constants.ParkingMachineStates.PPC_SCANNING_IN}) in signal {signal_name[sg_parking_mode]}.".split()
            )
            cond_1 = " ".join(
                "The car should be moving while the parking state is set to PPC_SCANNING_IN                "
                f" ({constants.ParkingMachineStates.PPC_SCANNING_IN}) in signal {signal_name[sg_parking_mode]}.        "
                f"        The movement of the car was checked in signal {signal_name[sg_km_driven]}.".split()
            )
            cond_2 = " ".join(
                "The distance should be > 0 km while parking state is set to PPC_SCANNING_IN               "
                f" ({constants.ParkingMachineStates.PPC_SCANNING_IN}) in signal {signal_name[sg_parking_mode]}.".split()
            )
            cond_3 = " ".join("Number of elements for distance array should be > 0.".split())
            cond_4 = " ".join("The number of km driven should be >= 0.".split())

            if len(distance_recording) > 0:
                eval_cond[0] = True
            if scanning_in_mask.any():
                eval_cond[1] = True
            if len(driven_km) > 0:
                eval_cond[2] = True
            if len(km_array) > 0:
                eval_cond[3] = True
            if distance_driven >= 0:
                eval_cond[4] = True

            if eval_cond[4]:
                result_final = fc.PASS
            else:
                result_final = fc.FAIL

            # Set table dataframe
            signal_summary = pd.DataFrame(
                {
                    "Condition": {
                        "0": cond_0,
                        "1": cond_1,
                        "2": cond_2,
                        "3": cond_3,
                        "4": cond_4,
                    },
                    "Result": {
                        "0": (
                            " ".join(
                                f"Parking state PPC_SCANNING_IN ({constants.ParkingMachineStates.PPC_SCANNING_IN})     "
                                "               was found.".split()
                            )
                            if eval_cond[1]
                            else " ".join(
                                "Parking state PPC_SCANNING_IN                    "
                                f" ({constants.ParkingMachineStates.PPC_SCANNING_IN}) was not found.".split()
                            )
                        ),
                        "1": (
                            " ".join(
                                "The car was in motion while parking state was set to                    "
                                f" PPC_SCANNING_IN ({constants.ParkingMachineStates.PPC_SCANNING_IN}).".split()
                            )
                            if eval_cond[0]
                            else (
                                " ".join(
                                    "The car was stationary while parking state was set to                    "
                                    f" PPC_SCANNING_IN ({constants.ParkingMachineStates.PPC_SCANNING_IN}).".split()
                                )
                                if eval_cond[1]
                                else " ".join(
                                    f"Parking state PPC_SCANNING_IN ({constants.ParkingMachineStates.PPC_SCANNING_IN}) "
                                    "                                  was not found.".split()
                                )
                            )
                        ),
                        "2": (
                            " ".join(
                                "Elements indicating a distance > 0 were found, while parking state was set to        "
                                f"             PPC_SCANNING_IN({constants.ParkingMachineStates.PPC_SCANNING_IN}).".split()
                            )
                            if eval_cond[2]
                            else (
                                " ".join(
                                    "No elements have been found while parking state was set to                    "
                                    f" PPC_SCANNING_IN ({constants.ParkingMachineStates.PPC_SCANNING_IN}) .".split()
                                )
                                if eval_cond[1]
                                else " ".join(
                                    "Parking state                     PPC_SCANNING_IN"
                                    f" ({constants.ParkingMachineStates.PPC_SCANNING_IN}) was not found.".split()
                                )
                            )
                        ),
                        "3": (
                            f"Number of elements for distance array == {len(km_array)}."
                            if eval_cond[3]
                            else "Number of elements for distance array == 0."
                        ),
                        "4": f"The number of km driven is {distance_driven:.3f} km.",
                    },
                    "Verdict": {
                        "0": "PASSED" if eval_cond[0] else "ACCEPTABLE",
                        "1": "PASSED" if eval_cond[1] else "ACCEPTABLE",
                        "2": "PASSED" if eval_cond[2] else "ACCEPTABLE",
                        "3": "PASSED" if eval_cond[3] else "ACCEPTABLE",
                        "4": "PASSED" if eval_cond[4] else "FAILED",
                    },
                }
            )

            # Create table with eval conditions from the summary dataframe
            sig_sum = go.Figure(
                data=[
                    go.Table(
                        columnwidth=[38, 35, 5],
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
            sig_sum.update_layout(
                constants.PlotlyTemplate.lgt_tmplt, height=fh.calc_table_height(signal_summary["Verdict"].to_dict())
            )

            plot_titles.append("Condition Evaluation")
            plots.append(sig_sum)
            remarks.append("")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=time_lst, y=prk_mod_lst, mode="lines", name=signal_name[sg_parking_mode]))
            fig.add_trace(go.Scatter(x=time_lst, y=km_driven_list, mode="lines", name=signal_name[sg_km_driven]))

            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plot_titles.append("Graphical Overview")
            plots.append(fig)
            remarks.append("")

            additional_results_dict = {
                "Verdict": {"value": result_final.title(), "color": fh.get_color(result_final)},
                "Name": {"value": "Number of Km driven"},
                "Expected result [km]": {"value": ">= 0"},
                "Measured result [km]": {"value": round(distance_driven, 3)},
            }
        except Exception as err:
            result_final = fc.INPUT_MISSING
            print(str(err))
            # write_log_message(f"Test failed, the following signal is missing:{str(err)}", "error", LOGGER)
            additional_results_dict = {
                "Verdict": {"value": result_final.title(), "color": fh.get_color(result_final)},
                "Name": {"value": f"Signal missing: { str(err)}"},
                "Expected result [km]": {"value": ""},
                "Measured result [km]": {"value": ""},
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
    name="MF KM DRIVEN",
    description=(
        " Evaluates the number of Km driven during the recording by using the signal"
        " M7board.EM_Thread.EgoMotionPort.drivenDistance_m. If the signal is empty, 0 will be returned. The signal goes"
        " up to 999 and then wraps around to 0 when it goes above 1000, this is handled by 'wrap_number' variable. "
    ),
)
class FtParkingSlotTypeBase(TestCase):
    """Test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtParkingSlotTypeBase]
