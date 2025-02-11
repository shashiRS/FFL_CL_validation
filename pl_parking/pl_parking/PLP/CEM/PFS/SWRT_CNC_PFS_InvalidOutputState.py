"""PFS Output Invalid State Test."""

import logging

from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

TRC_ROOT = os.path.abspath(os.path.join(__file__, "", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


import pandas as pd

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import ConstantsCem

SIGNAL_DATA = "PFS_Output_Invalid_State"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS Invalid Output State",
    description="This test case checks that PFS shall set INVALID state on its output if any of its input signal's "
    "state is AL_SIG_STATE_INVALID.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtInvalidOutputState(TestStep):
    """PFS Invalid State Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step"""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        data_df = reader.as_plain_df

        pfs_output_data = data_df.filter(regex="Cem")

        pfs_parklines_input_data = data_df[
            [
                "PMDCamera_Front_eSigStatus",
                "PMDCamera_Rear_eSigStatus",
                "PMDCamera_Left_eSigStatus",
                "PMDCamera_Right_eSigStatus",
            ]
        ]

        pfs_ws_input_data = data_df[
            [
                "PMDWs_Front_eSigStatus",
                "PMDWs_Rear_eSigStatus",
                "PMDWs_Left_eSigStatus",
                "PMDWs_Right_eSigStatus",
            ]
        ]

        pfs_slot_input_data = data_df[
            [
                "PmsdSlot_Front_eSigStatus",
                "PmsdSlot_Rear_eSigStatus",
                "PmsdSlot_Left_eSigStatus",
                "PmsdSlot_Right_eSigStatus",
            ]
        ]

        pfs_wl_input_data = data_df[
            [
                "PMDWl_Front_eSigStatus",
                "PMDWl_Rear_eSigStatus",
                "PMDWl_Left_eSigStatus",
                "PMDWl_Right_eSigStatus",
            ]
        ]

        pfs_stoplines_input_data = data_df[
            [
                "PMDSl_Front_eSigStatus",
                "PMDSl_Rear_eSigStatus",
                "PMDSl_Left_eSigStatus",
                "PMDSl_Right_eSigStatus",
            ]
        ]

        pfs_pedcrossings_input_data = data_df[
            [
                "PMDPEDCROS_Front_eSigStatus",
                "PMDPEDCROS_Rear_eSigStatus",
                "PMDPEDCROS_Left_eSigStatus",
                "PMDPEDCROS_Right_eSigStatus",
            ]
        ]

        evaluation = ["", "", "", "", "", ""]

        #  Check for PFS PCL lines invalid input data
        pcl_result_list = []
        for column_name in pfs_parklines_input_data:
            for pcl_value in pfs_parklines_input_data[column_name]:
                for cem_pcl_value in pfs_output_data["Cem_pcl_eSigStatus"]:
                    if pcl_value == ConstantsCem.AL_SIG_STATE_INVALID:
                        if cem_pcl_value == ConstantsCem.AL_SIG_STATE_INVALID:
                            pcl_result_list.append(1)
                            break
                        else:
                            pcl_result_list.append(0)
                            break

        #  Check for PFS wheel stopper invalid input data
        ws_result_list = []
        for column_name in pfs_ws_input_data:
            for ws_value in pfs_ws_input_data[column_name]:
                for cem_ws_value in pfs_output_data["CemWs_eSigStatus"]:
                    if ws_value == ConstantsCem.AL_SIG_STATE_INVALID:
                        if cem_ws_value == ConstantsCem.AL_SIG_STATE_INVALID:
                            ws_result_list.append(1)
                            break
                        else:
                            ws_result_list.append(0)
                            break

        #  Check for PFS parking slots invalid input data
        slots_result_list = []
        for column_name in pfs_slot_input_data:
            for slot_value in pfs_slot_input_data[column_name]:
                for cem_slot_value in pfs_output_data["CemSlot_eSigStatus"]:
                    if slot_value == ConstantsCem.AL_SIG_STATE_INVALID:
                        if cem_slot_value == ConstantsCem.AL_SIG_STATE_INVALID:
                            slots_result_list.append(1)
                            break
                        else:
                            slots_result_list.append(0)
                            break

        #  Check for PFS wheel locker invalid input data
        wl_result_list = []
        for column_name in pfs_wl_input_data:
            for wl_value in pfs_wl_input_data[column_name]:
                for cem_wl_value in pfs_output_data["CemWl_eSigStatus"]:
                    if wl_value == ConstantsCem.AL_SIG_STATE_INVALID:
                        if cem_wl_value == ConstantsCem.AL_SIG_STATE_INVALID:
                            wl_result_list.append(1)
                            break
                        else:
                            wl_result_list.append(0)
                            break

        #  Check for PFS stop lines invalid input data
        stopline_result_list = []
        for column_name in pfs_stoplines_input_data:
            for sl_value in pfs_stoplines_input_data[column_name]:
                for cem_sl_value in pfs_output_data["Cem_stopLines_eSigStatus"]:
                    if sl_value == ConstantsCem.AL_SIG_STATE_INVALID:
                        if cem_sl_value == ConstantsCem.AL_SIG_STATE_INVALID:
                            stopline_result_list.append(1)
                            break
                        else:
                            stopline_result_list.append(0)
                            break

        #  Check for PFS pedestrian crossings invalid input data
        pedcros_result_list = []
        for column_name in pfs_pedcrossings_input_data:

            i = 0
            for pedcros_value in pfs_pedcrossings_input_data[column_name]:
                i = i + 1
                for cem_pedcros_value in pfs_output_data["Cem_pedCrossings_eSigStatus"]:

                    if pedcros_value == ConstantsCem.AL_SIG_STATE_INVALID:
                        if cem_pedcros_value == ConstantsCem.AL_SIG_STATE_INVALID:
                            pedcros_result_list.append(1)
                            break
                        else:
                            pedcros_result_list.append(0)
                            break

        if not pcl_result_list:
            evaluation[0] = "None of the PFS PCL input has the invalid state"
            pcl_test_result = True
        elif all(pcl_result_list):
            evaluation[0] = "PFS sets invalid state if any of its pcl input state is invalid"
            pcl_test_result = True
        else:
            evaluation[0] = "PFS does not set invalid state if any of its pcl input state is invalid"
            pcl_test_result = False

        if not ws_result_list:
            evaluation[1] = "None of the PFS ws input has the invalid state"
            ws_test_result = True
        elif all(ws_result_list):
            evaluation[1] = "PFS sets invalid state if any of its ws input state is invalid"
            ws_test_result = True
        else:
            evaluation[1] = "PFS does not set invalid state if any of its ws input state is invalid"
            ws_test_result = False

        if not slots_result_list:
            evaluation[2] = "None of the PFS slots input has the invalid state"
            slot_test_result = True
        elif all(slots_result_list):
            evaluation[2] = "PFS sets invalid state if any of its slots input state is invalid"
            slot_test_result = True
        else:
            evaluation[2] = "PFS does not set invalid state if any of its slots input state is invalid"
            slot_test_result = False

        if not wl_result_list:
            evaluation[3] = "None of the PFS wl input has the invalid state"
            wl_test_result = True
        elif all(wl_result_list):
            evaluation[3] = "PFS sets invalid state if any of its wl input state is invalid"
            wl_test_result = True
        else:
            evaluation[3] = "PFS does not set invalid state if any of its wl input state is invalid"
            wl_test_result = False

        if not stopline_result_list:
            evaluation[4] = "None of the PFS sl input has the invalid state"
            sl_test_result = True
        elif all(stopline_result_list):
            evaluation[4] = "PFS sets invalid state if any of its sl input state is invalid"
            sl_test_result = True
        else:
            sl_test_result = False
            evaluation[4] = "PFS does not set invalid state if any of its sl input state is invalid"

        if not pedcros_result_list:
            evaluation[5] = "None of the PFS pedcrossings input has the invalid state"
            pedcros_test_result = True
        elif all(pedcros_result_list):
            evaluation[5] = "PFS sets invalid state if any of its pedcrossings input state is invalid"
            pedcros_test_result = True
        else:
            pedcros_test_result = False
            evaluation[5] = "PFS does not set invalid state if any of its pedcrossings input state is invalid"

        eval_cond = [
            pcl_test_result,
            ws_test_result,
            slot_test_result,
            wl_test_result,
            sl_test_result,
            pedcros_test_result,
        ]

        test_result = fc.PASS if all(eval_cond) else fc.FAIL

        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": "PFS shall set INVALID state on its output if any of its  PCL input signal's state is "
                    "AL_SIG_STATE_INVALID.",
                    "2": "PFS shall set INVALID state on its output if any of its Wheelstopper input signal's state is "
                    "AL_SIG_STATE_INVALID.",
                    "3": "PFS shall set INVALID state on its output if any of its slots input signal's state is "
                    "AL_SIG_STATE_INVALID.",
                    "4": "PFS shall set INVALID state on its output if any of its  Wheellocker input signal's state "
                    "is AL_SIG_STATE_INVALID.",
                    "5": "PFS shall set INVALID state on its output if any of its StopLines input signal's state is "
                    "AL_SIG_STATE_INVALID.",
                    "6": "PFS shall set INVALID state on its output if any of its Ped crossings input signal's state "
                    "is AL_SIG_STATE_INVALID.",
                },
                "Result": {
                    "1": evaluation[0],
                    "2": evaluation[1],
                    "3": evaluation[2],
                    "4": evaluation[3],
                    "5": evaluation[4],
                    "6": evaluation[5],
                },
                "Verdict": {
                    "1": "PASSED" if eval_cond[0] else "FAILED",
                    "2": "PASSED" if eval_cond[1] else "FAILED",
                    "3": "PASSED" if eval_cond[2] else "FAILED",
                    "4": "PASSED" if eval_cond[3] else "FAILED",
                    "5": "PASSED" if eval_cond[4] else "FAILED",
                    "6": "PASSED" if eval_cond[5] else "FAILED",
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="PFS Invalid Input State")
        self.result.details["Plots"].append(sig_sum)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2047072"],
            fc.TESTCASE_ID: ["85701"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test case checks that PFS shall set INVALID state on its output if any of its input signal's "
                "state is AL_SIG_STATE_INVALID."
            ],
            fc.TEST_RESULT: [test_result],
        }

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = result_df


@verifies("2047072")
@testcase_definition(
    name="SWRT_CNC_PFS_InvalidOutputState",
    description="Verify Invalid Output State",
)
class FtInvalidOutputState(TestCase):
    """PFS Invalid Output Test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TestStepFtInvalidOutputState,
        ]
