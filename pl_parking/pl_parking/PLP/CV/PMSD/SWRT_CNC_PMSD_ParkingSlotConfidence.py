#!/usr/bin/env python3
"""Defining  pmsd SlotConfidenceLevel testcases"""
import logging
import os

import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep

SIGNAL_DATA = "PMSD_SlotConfidenceLevel"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="PMSD Confidence of the detected parking slot ",
    description="This teststep checks confidence of the detected parking slot",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class PmsdSlotConfidenceLevelTestStep(TestStep):
    """PMSD Slot Confidence Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarsk based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)
        signal_summary = {}

        reader = self.readers[SIGNAL_DATA].signals

        df = reader.as_plain_df
        df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]

        # Front Camera Parking slots
        FC_Conf_Ang = df.loc[:, df.columns.str.contains("PsdSlot_Front_parkingLines_sc_angled")]
        FC_Conf_Par = df.loc[:, df.columns.str.contains("PsdSlot_Front_parkingLines_sc_parallel")]
        FC_Conf_Per = df.loc[:, df.columns.str.contains("PsdSlot_Front_parkingLines_sc_perpendicular")]

        # Rear Camera Parking slots
        RC_Conf_Ang = df.loc[:, df.columns.str.contains("PsdSlot_Rear_parkingLines_sc_angled")]
        RC_Conf_Par = df.loc[:, df.columns.str.contains("PsdSlot_Rear_parkingLines_sc_parallel")]
        RC_Conf_Per = df.loc[:, df.columns.str.contains("PsdSlot_Rear_parkingLines_sc_perpendicular")]

        # Left Camera Parking slots
        LSC_Conf_Ang = df.loc[:, df.columns.str.contains("PsdSlot_Left_parkingLines_sc_angled")]
        LSC_Conf_Par = df.loc[:, df.columns.str.contains("PsdSlot_Left_parkingLines_sc_parallel")]
        LSC_Conf_Per = df.loc[:, df.columns.str.contains("PsdSlot_Left_parkingLines_sc_perpendicular")]

        # Right Camera Parking slots
        RSC_Conf_Ang = df.loc[:, df.columns.str.contains("PsdSlot_Right_parkingLines_sc_angled")]
        RSC_Conf_Par = df.loc[:, df.columns.str.contains("PsdSlot_Right_parkingLines_sc_parallel")]
        RSC_Conf_Per = df.loc[:, df.columns.str.contains("PsdSlot_Right_parkingLines_sc_perpendicular")]

        evaluation = ["", "", "", "", "", "", "", "", "", "", "", ""]
        if not FC_Conf_Ang.empty:
            evaluation[0] = "FC Confidence of the detected angled parking slot is present"
            FC_ang_result = True
        else:
            evaluation[0] = "FC Confidence of the detected angled parking slot is not present"
            FC_ang_result = False

        if not FC_Conf_Par.empty:
            evaluation[1] = "FC Confidence of the detected parallel parking slot is present"
            FC_par_result = True
        else:
            evaluation[1] = "FC Confidence of the detected parallel parking slot is not present"
            FC_par_result = False

        if not FC_Conf_Per.empty:
            evaluation[2] = "FC Confidence of the detected perpendicular parking slot is present"
            FC_per_result = True
        else:
            evaluation[2] = "FC Confidence of the detected perpendicular parking slot is not present"
            FC_per_result = False

        # Check the slot confidence of Rear camera
        if not RC_Conf_Ang.empty:
            evaluation[3] = "RC Confidence of the detected angled parking slot is present"
            RC_ang_result = True
        else:
            evaluation[3] = "RC Confidence of the detected angled parking slot is not present"
            RC_ang_result = False

        if not RC_Conf_Par.empty:
            evaluation[4] = "RC Confidence of the detected parallel parking slot is present"
            RC_par_result = True
        else:
            evaluation[4] = "RC Confidence of the detected parallel parking slot is not present"
            RC_par_result = False

        if not RC_Conf_Per.empty:
            evaluation[5] = "RC Confidence of the detected perpendicular parking slot is present"
            RC_per_result = True
        else:
            evaluation[5] = "RC Confidence of the detected perpendicular parking slot is not present"
            RC_per_result = False

        # Check the slot confidence of Left camera
        if not LSC_Conf_Ang.empty:
            evaluation[6] = "LSC Confidence of the detected angled parking slot is present"
            LSC_ang_result = True
        else:
            evaluation[6] = "LSC Confidence of the detected angled parking slot is not present"
            LSC_ang_result = False

        if not LSC_Conf_Par.empty:
            evaluation[7] = "LSC Confidence of the detected parallel parking slot is present"
            LSC_par_result = True
        else:
            evaluation[7] = "LSC Confidence of the detected parallel parking slot is not present"
            LSC_par_result = False

        if not LSC_Conf_Per.empty:
            evaluation[8] = "LSC Confidence of the detected perpendicular parking slot is present"
            LSC_per_result = True
        else:
            evaluation[8] = "LSC Confidence of the detected perpendicular parking slot is not present"
            LSC_per_result = False

        # Check the slot confidence of Left camera
        if not RSC_Conf_Ang.empty:
            evaluation[9] = "RSC Confidence of the detected angled parking slot is present"
            RSC_ang_result = True
        else:
            evaluation[9] = "RSC Confidence of the detected angled parking slot is not present"
            RSC_ang_result = False

        if not RSC_Conf_Par.empty:
            evaluation[10] = "RSC Confidence of the detected parallel parking slot is present"
            RSC_par_result = True
        else:
            evaluation[10] = "RSC Confidence of the detected parallel parking slot is not present"
            RSC_par_result = False

        if not RSC_Conf_Per.empty:
            evaluation[11] = "RSC Confidence of the detected perpendicular parking slot is present"
            RSC_per_result = True
        else:
            evaluation[11] = "RSC Confidence of the detected perpendicular parking slot is not present"
            RSC_per_result = False

        cond_bool = [
            FC_ang_result,
            FC_par_result,
            FC_per_result,
            RC_ang_result,
            RC_par_result,
            RC_per_result,
            LSC_ang_result,
            LSC_par_result,
            LSC_per_result,
            RSC_ang_result,
            RSC_par_result,
            RSC_per_result,
        ]

        test_result = fc.PASS if all(cond_bool) else fc.FAIL
        signal_summary["FC_confidence_angled"] = evaluation[0]
        signal_summary["FC_confidence_parallel"] = evaluation[1]
        signal_summary["FC_confidence_perpendicular"] = evaluation[2]
        signal_summary["RC_confidence_angled"] = evaluation[3]
        signal_summary["RC_confidence_parallel"] = evaluation[4]
        signal_summary["RC_confidence_perpendicular"] = evaluation[5]
        signal_summary["LSC_confidence_angled"] = evaluation[6]
        signal_summary["LSC_confidence_parallel"] = evaluation[7]
        signal_summary["LSC_confidence_perpendicular"] = evaluation[8]
        signal_summary["RSC_confidence_angled"] = evaluation[9]
        signal_summary["RSC_confidence_parallel"] = evaluation[10]
        signal_summary["RSC_confidence_perpendicular"] = evaluation[11]

        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Signal Evaluation", "Summary"]),
                    cells=dict(values=[list(signal_summary.keys()), list(signal_summary.values())]),
                )
            ]
        )

        plot_titles.append("Signal Evaluation")
        plots.append(fig)
        remarks.append("PMSD Evaluation")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1988316"],
            fc.TESTCASE_ID: ["61399"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: ["Verify confidence of the detected parking slot."],
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


@verifies("1988316")
@testcase_definition(
    name="SWRT_CNC_PMSD_ParkingSlotConfidence",
    description="Verify Parking Slots Confidence",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class PmsdSlotConfidenceLevel(TestCase):
    """Slot ConfidenceLevel test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PmsdSlotConfidenceLevelTestStep,
        ]
