"""Fail reason test."""

import logging
import os
import sys

import pandas as pd
import plotly.graph_objects as go

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", "..", ".."))  # nopep8
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
# PlotlyTemplate, ParkingModes,LateralErrorConstants,GeneralConstants
from tsf.core.results import FALSE, TRUE, BooleanResult  # nopep8
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, calc_table_height

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


SIGNAL_DATA = "FAIL_REASON"
signal_obj = fh.MfSignals()


@teststep_definition(
    step_number=1,
    name="Park Fail Reason",
    description="""Check if ppcParkingMode_nu has one of the value set to:
            PARK_IN(1), GARAGE_PARKING_IN(3), PARK_OUT(2) or GARAGE_PARKING_OUT(4), the
            coreStopReason_nu not contain values for
            PARKING_FAILED_TPD_LOST(1) and PARKING_FAILED_PATH_LOST(2) and the
            failReason contain values > 0 at the end of parking maneuver.""",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, fh.MfSignals)
class Step1(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------
    Verify that vehicle velocity[km/h] has values greater than 0 until a slot is selected by the driver.

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        try:
            df = self.readers[SIGNAL_DATA].signals
            signal_name = signal_obj._properties
            self.test_result = fc.INPUT_MISSING
            verdict_color = "rgb(33,39,43)"  # fc.InputMissing
            # plots and remarks need to have the same length
            plot_titles, plots, remarks = fh.rep([], 3)

            eval_cond = [False] * 5
            fail_reason = 0
            eval_cond = [False] * 6
            found_trigger_list = []
            sg_core_stop_reason = "CoreStopReason"
            sg_parking_fail_reason = "ParkingFaileReason"
            sg_ppc_parking_mode = fh.MfSignals.Columns.PPCPARKINGMODE

            time = df[fh.MfSignals.Columns.TIME]

            fail_reason_signal = df[sg_parking_fail_reason]

            ppc_parking_mode = df[sg_ppc_parking_mode]

            state_var = df[sg_core_stop_reason]
            parking_failed_tpd_mask = state_var == constants.CoreStopStatus.PARKING_FAILED_TPD_LOST
            parking_failed_path_lost = state_var == constants.CoreStopStatus.PARKING_FAILED_PATH_LOST
            var_mask_failed = parking_failed_tpd_mask | parking_failed_path_lost

            #################################################
            # Check if any trigger was found. If so, add to list to use in signal_summary
            if parking_failed_tpd_mask.any():
                found_trigger_list.append(
                    f"PARKING_FAILED_TPD_LOST({constants.CoreStopStatus.PARKING_FAILED_TPD_LOST})"
                )
            if parking_failed_path_lost.any():
                found_trigger_list.append(
                    f"PARKING_FAILED_PATH_LOST({constants.CoreStopStatus.PARKING_FAILED_PATH_LOST})"
                )

            found_trigger_list = " and ".join(found_trigger_list)

            parking_in_mask = ppc_parking_mode == constants.ParkingModes.PARK_IN
            parking_in_garage_mask = ppc_parking_mode == constants.ParkingModes.GARAGE_PARKING_IN
            ppc_parking_in_mask = parking_in_mask | parking_in_garage_mask

            parking_out_mask = ppc_parking_mode == constants.ParkingModes.PARK_OUT
            parking_out_garage_mask = ppc_parking_mode == constants.ParkingModes.GARAGE_PARKING_OUT
            ppc_parking_out_mask = parking_out_mask | parking_out_garage_mask

            mask_in = var_mask_failed & ppc_parking_in_mask
            mask_out = var_mask_failed & ppc_parking_out_mask

            parking_in_failed = mask_in[mask_in.idxmax()]
            parking_out_failed = mask_out[mask_out.idxmax()]

            if parking_in_failed:
                fail_reason = fail_reason_signal[mask_in.idxmax()]
            elif parking_out_failed:
                fail_reason = fail_reason_signal[mask_out.idxmax()]

            if not var_mask_failed.any():
                eval_cond[0] = True
            if ppc_parking_in_mask.any():
                eval_cond[1] = True
            if ppc_parking_out_mask.any():
                eval_cond[2] = True
            if not mask_in.any():
                eval_cond[3] = True
            if not mask_out.any():
                eval_cond[4] = True
            if fail_reason == 0:
                eval_cond[5] = True
                self.test_result = fc.PASS
                verdict_color = "#28a745"
                self.result.measured_result = TRUE
            else:
                self.test_result = fc.FAIL
                verdict_color = "#dc3545"
                self.result.measured_result = FALSE

            # Set condition strings
            cond_0 = " ".join(
                f"The signal {signal_name[sg_core_stop_reason]} should not have instances of                "
                f" PARKING_FAILED_TPD_LOST({constants.CoreStopStatus.PARKING_FAILED_TPD_LOST})                 or"
                f" PARKING_FAILED_PATH_LOST({constants.CoreStopStatus.PARKING_FAILED_PATH_LOST}) statuses.".split()
            )
            cond_1 = " ".join(
                f"The mode GARAGE_PARKING_IN({constants.ParkingModes.GARAGE_PARKING_IN}) or                "
                f" PARK_IN({constants.ParkingModes.PARK_IN}) should be found at least once in signal                 "
                f" {signal_name[sg_ppc_parking_mode]}.".split()
            )
            cond_2 = " ".join(
                f"The mode GARAGE_PARKING_OUT({constants.ParkingModes.GARAGE_PARKING_OUT}) or                "
                f" PARK_OUT({constants.ParkingModes.PARK_OUT}) should be found at least once in signal                 "
                f" {signal_name[sg_ppc_parking_mode]}.".split()
            )
            cond_3 = " ".join(
                f"Parking should not fail while the mode of PARK_IN({constants.ParkingModes.PARK_IN}) or               "
                f"  GARAGE_PARKING_IN({constants.ParkingModes.GARAGE_PARKING_IN}) is active.".split()
            )
            cond_4 = " ".join(
                f"Parking should not fail while the mode of PARK_OUT({constants.ParkingModes.PARK_OUT}) or             "
                f"    GARAGE_PARKING_OUT({constants.ParkingModes.GARAGE_PARKING_OUT}) is active.".split()
            )
            cond_5 = " ".join(
                f"The signal {signal_name[sg_parking_fail_reason]} should be 0 (parking did not                 fail)"
                " at the end of parking maneuver.".split()
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
                        "5": cond_5,
                    },
                    "Result": {
                        "0": (
                            " ".join("No triggers were present.".split())
                            if eval_cond[0]
                            else " ".join(f"The following triggers were found: {found_trigger_list}".split())
                        ),
                        "1": (
                            " ".join(
                                f"Parking mode PARK_IN({constants.ParkingModes.PARK_IN})                        was found.".split()
                            )
                            if parking_in_mask.any()
                            else (
                                " ".join(
                                    f"Parking mode GARAGE_PARKING_IN ({constants.ParkingModes.GARAGE_PARKING_IN})          "
                                    "               was found.".split()
                                )
                                if parking_in_garage_mask.any()
                                else " ".join("No parking mode was found.".split())
                            )
                        ),
                        "2": (
                            " ".join(f"Parking mode PARK_OUT({constants.ParkingModes.PARK_OUT}) was found.".split())
                            if parking_out_mask.any()
                            else (
                                " ".join(
                                    f"Parking mode GARAGE_PARKING_OUT ({constants.ParkingModes.GARAGE_PARKING_OUT})        "
                                    "                 was found.".split()
                                )
                                if parking_out_garage_mask.any()
                                else " ".join("No parking mode was found.".split())
                            )
                        ),
                        "3": (
                            " ".join("Parking did not fail.".split())
                            if eval_cond[3]
                            else " ".join("Parking failed.".split())
                        ),
                        "4": (
                            " ".join("Parking did not fail.".split())
                            if eval_cond[4]
                            else " ".join("Parking failed.".split())
                        ),
                        "5": (
                            " ".join("Parking did not fail.".split())
                            if eval_cond[5]
                            else " ".join(
                                f"Parking failed with                         fail reason: {fail_reason}".split()
                            )
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

            # Create table with eval conditions from the summary dict
            sig_sum = go.Figure(
                data=[
                    go.Table(
                        columnwidth=[50, 20, 7],
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
                constants.PlotlyTemplate.lgt_tmplt, height=calc_table_height(signal_summary["Condition"].to_dict())
            )
            plot_titles.append("Condition Evaluation")
            plots.append(sig_sum)
            remarks.append("")

            if self.test_result == fc.FAIL or bool(constants.GeneralConstants.ACTIVATE_PLOTS):
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=time.values.tolist(),
                        y=df[sg_core_stop_reason].values.tolist(),
                        mode="lines",
                        name=signal_name[sg_core_stop_reason],
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=time.values.tolist(),
                        y=df[sg_parking_fail_reason].values.tolist(),
                        mode="lines",
                        name=f"{signal_name[sg_parking_fail_reason]}",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=time.values.tolist(),
                        y=df[sg_ppc_parking_mode].values.tolist(),
                        mode="lines",
                        name=f"{signal_name[sg_ppc_parking_mode]}",
                    )
                )

                fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]")
                fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

                plot_titles.append("Graphical overview")
                plots.append(fig)
                remarks.append("")

            for plot in plots:
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)

            additional_results_dict = {
                "Verdict": {"value": self.test_result.title(), "color": verdict_color},
            }

            self.result.details["Additional_results"] = additional_results_dict
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@testcase_definition(
    name="MF PARK FAIL REASON",
    description="""Check if ppcParkingMode_nu has one of the value set to:
            PARK_IN(1), GARAGE_PARKING_IN(3), PARK_OUT(2) or GARAGE_PARKING_OUT(4), the
            coreStopReason_nu not contain values for
            PARKING_FAILED_TPD_LOST(1) and PARKING_FAILED_PATH_LOST(2) and the
            failReason contain values > 0 at the end of parking maneuver.""",
)
class ParkFailReason(TestCase):
    """Test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            Step1,
        ]
