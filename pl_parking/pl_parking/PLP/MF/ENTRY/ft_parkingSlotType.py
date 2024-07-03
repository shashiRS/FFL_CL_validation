"""Functional test for parking slot type"""

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
from pl_parking.PLP.MF.ft_helper import ExampleSignals

SIGNAL_DATA = "MF_SLOT_TYPE"

example_obj = EntrySignals()


@teststep_definition(
    step_number=1,
    name="MF SLOT TYPE",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ExampleSignals)
class TestStepFtParkingSlotType(TestStep):
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
        sg_ppc_prk_mode = "ppcParkingMode"
        sg_time = "TimeStamp"
        sg_prk_mode = "PSMDebugPort"
        sg_prk_scenario = "ParkingScenario"
        sg_nb_bxs = "NumberOfValidParkingBoxes"
        signal_name = example_obj._properties
        results_lst = [fc.INPUT_MISSING] * 6

        try:
            # Converting microseconds to seconds
            df[sg_time] = df[sg_time] / constants.GeneralConstants.US_IN_S
            # Converting epoch time to seconds passed
            df[sg_time] = df[sg_time] - df[sg_time].iat[0]

            def check_parking_scenarios():
                scenario_dict = {
                    "Parallel parking": constants.ParkingScenario.PARALLEL_PARKING,
                    "Perpendicular parking": constants.ParkingScenario.PERPENDICULAR_PARKING,
                    "Angled front parking": constants.ParkingScenario.ANGLED_PARKING_OPENING_TOWARDS_FRONT,
                    "Angled back parking": constants.ParkingScenario.ANGLED_PARKING_OPENING_TOWARDS_BACK,
                    "Garage parking": constants.ParkingScenario.GARAGE_PARKING,
                    "Direct park in": constants.ParkingScenario.DIRECT_PARKING,
                }

                attempts_list = ["N/A"] * 6
                result_list = [fc.INPUT_MISSING] * 6

                parking_in_mask = (df[sg_ppc_prk_mode] == constants.ParkingModes.PARK_IN) | (
                    df[sg_ppc_prk_mode] == constants.ParkingModes.GARAGE_PARKING_IN
                )
                parking_mask = df[sg_prk_mode] == constants.ParkingMachineStates.PPC_PERFORM_PARKING
                num_boxes_mask = df[sg_nb_bxs] == constants.ConstantsParkingSlotType.NUMBER_OF_BOXES

                for key, value in scenario_dict.items():
                    eval_cond = [False] * 5
                    parking_scenario_mask = df[sg_prk_scenario] == value

                    if parking_scenario_mask.any():
                        performed_park_mask = parking_in_mask & parking_scenario_mask & parking_mask & num_boxes_mask

                        if parking_in_mask.any():
                            eval_cond[0] = True
                        if parking_mask.any():
                            eval_cond[1] = True
                        if num_boxes_mask.any():
                            eval_cond[2] = True
                        if parking_scenario_mask.any():
                            eval_cond[3] = True
                        if performed_park_mask.any():
                            eval_cond[4] = True

                        if all(eval_cond):
                            sig_sum = None
                            idx = list(scenario_dict).index(key)
                            result_list[idx] = fc.PASS
                            attempts_list[idx] = "1"

                            # Set condition strings
                            cond_0 = " ".join(
                                f"Parking mode must be set to PARK_IN({constants.ParkingModes.PARK_IN}) or             "
                                f"                    GARAGE_PARKING_IN({constants.ParkingModes.GARAGE_PARKING_IN}) in"
                                f" signal                                 {signal_name[sg_ppc_prk_mode]}.".split()
                            )
                            cond_1 = " ".join(
                                "Parking state must be set to PPC_PERFORM_PARKING                               "
                                f" ({constants.ParkingMachineStates.PPC_PERFORM_PARKING}) in signal                    "
                                f"             {signal_name[sg_prk_mode]}.".split()
                            )
                            cond_2 = " ".join(
                                "The NUMBER_OF_VALID_PARKING_BOXES should be set to 1 in signal                       "
                                f"          {signal_name[sg_nb_bxs]}.".split()
                            )
                            cond_3 = " ".join(f"Occurence where PARKING_SCENARIO is set to {key}.".split())
                            cond_4 = " ".join(
                                "All the conditions from above are true for this type of parking scenario.".split()
                            )

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
                                    "Verdict": {
                                        "0": "PASSED",
                                        "1": "PASSED",
                                        "2": "PASSED",
                                        "3": "PASSED",
                                        "4": "PASSED",
                                    },
                                }
                            )

                            # Create table with eval conditions from the summary dataframe
                            sig_sum = go.Figure(
                                data=[
                                    go.Table(
                                        columnwidth=[4, 1],
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
                                constants.PlotlyTemplate.lgt_tmplt,
                                height=fh.calc_table_height(signal_summary["Condition"].to_dict()),
                            )
                            plot_titles.append(key)
                            plots.append(sig_sum)
                            remarks.append("Parking type found")

                return result_list, attempts_list

            results_lst, attempts_lst = check_parking_scenarios()

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df[sg_time].values.tolist(),
                    y=df[sg_prk_mode].values.tolist(),
                    mode="lines",
                    name=signal_name[sg_prk_mode],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df[sg_time].values.tolist(),
                    y=df[sg_prk_scenario].values.tolist(),
                    mode="lines",
                    name=signal_name[sg_prk_scenario],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df[sg_time].values.tolist(),
                    y=df[sg_ppc_prk_mode].values.tolist(),
                    mode="lines",
                    name=signal_name[sg_ppc_prk_mode],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df[sg_time].values.tolist(),
                    y=df[sg_nb_bxs].values.tolist(),
                    mode="lines",
                    name=signal_name[sg_nb_bxs],
                )
            )
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plot_titles.append("Graphical Overview")
            plots.append(fig)
            remarks.append("")

            if fc.PASS in results_lst:
                result_final = fc.PASS
            else:
                result_final = fc.FAIL

            additional_results_dict = {
                "Verdict": {"value": result_final.title(), "color": fh.get_color(result_final)},
                "Name": {"value": "Type of parking slot"},
                "Expected result [max no. slots]": {
                    "value": f" < {constants.ParkingScenario.MAX_NUM_PARKING_SCENARIO_TYPES}"
                },
                "Parallel parking [attempts]": {"value": attempts_lst[0]},
                "Perpendicular parking [attempts]": {"value": attempts_lst[1]},
                "Angled front parking [attempts]": {"value": attempts_lst[2]},
                "Angled back parking [attempts]": {"value": attempts_lst[3]},
                "Garage parking [attempts]": {"value": attempts_lst[4]},
                "Direct park in [attempts]": {"value": attempts_lst[5]},
            }
        except Exception as err:
            result_final = fc.INPUT_MISSING
            print(str(err))
            # write_log_message(f"Test failed, the following signal is missing:{str(err)}", "error", LOGGER)
            additional_results_dict = {
                "Name": {"value": f"Signal missing: { str(err)}"},
                "Expected result [max no. slots]": {"value": ""},
                "Parallel parking [attempts]": {"value": ""},
                "Perpendicular parking [attempts]": {"value": ""},
                "Angled front parking [attempts]": {"value": ""},
                "Angled back parking [attempts]": {"value": ""},
                "Garage parking [attempts]": {"value": ""},
                "Direct park in [attempts]": {"value": ""},
            }
        pd.DataFrame(
            {
                fc.REQ_ID: [["1", "2", "3", "4", "5", "6"][i] for i in range(0, 6)],
                fc.TESTCASE_ID: [["1", "2", "3", "4", "5", "6"][i] for i in range(0, 6)],
                fc.TEST_SAFETY_RELEVANT: ["input missing" for _ in range(0, 6)],
                fc.TEST_DESCRIPTION: [
                    [
                        "Parallel parking slot",
                        "Perpendicular parking slot",
                        "Angled front parking slot",
                        "Angled back parking slot",
                        "Garage parking slot",
                        "Direct park in slot",
                    ][i]
                    for i in range(0, 6)
                ],
                fc.TEST_RESULT: [results_lst[i] for i in range(0, 6)],
            }
        )

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
    name="MF SLOT TYPE",
    description=(
        "Parallel parking slot Perpendicular parking slot Angled front parking slot Angled back parking slot Garage"
        " parking slot Direct park in slot"
    ),
)
class FtParkingSlotType(TestCase):
    """Test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtParkingSlotType]
