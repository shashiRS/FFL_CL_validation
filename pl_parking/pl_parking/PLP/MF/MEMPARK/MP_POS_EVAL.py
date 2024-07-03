#!/usr/bin/env python3
"""MP Check pose test cases"""

import logging
import os
import sys

import pandas as pd
import plotly.graph_objects as go

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, MfSignals
from pl_parking.PLP.MF.constants import ConstantsMPmaneuver, PlotlyTemplate

__author__ = "Santiago Carvajal"
__copyright__ = "2024-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Development"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "MP_POSCHK"
ACTIVATE_PLOTS = True

signals_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Memory Parking Maneuver evaluation",
    description=(
        "Check that the maneuver is completer and the position of the vehicle stored.\
        by the user versus the end position of the vehicle after MP validates.\
        the position. Position X, Y and yaw angle"
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TestStepFtPosesMP(TestStep):
    """Test step class"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        self.test_result = fc.INPUT_MISSING  # Result
        self.result.measured_result = DATA_NOK  # Initializing the result with data nok

        plot_titles, plots, remarks = fh.rep([], 3)

        signal_summary = {}  # Initializing the dictionary with data for final evaluation table
        signals: pd.DataFrame = self.readers[
            SIGNAL_DATA
        ].signals  # Make a dataframe(df) with all signals extracted from Signals class

        time_signal = signals[MfSignals.Columns.TIME]
        confirmation_user = signals[MfSignals.Columns.USERACTIONHEADUNIT_NU]
        posxcheck = signals[MfSignals.Columns.APODOESTIMXPOSM]
        posycheck = signals[MfSignals.Columns.APODOESTIMYPOSM]
        posyawcheck = signals[MfSignals.Columns.APODOESTIMYAWRATERADPS]
        mp_end_man = signals[MfSignals.Columns.MPSTATE]

        last_mp_status = 0
        for _, val in enumerate(mp_end_man.values):
            if val == ConstantsMPmaneuver.MP_END_MANEUVER:
                # Vaidation that the maneuver ended - Status 7, due to possible refinement
                # of the position the validation is through all the file
                # Only last MP index is stored
                last_mp_status = ConstantsMPmaneuver.MP_END_MANEUVER

        savepos_x = 0.0
        savepos_y = 0.0
        savepos_yawr = 0.0
        endpos_x = 0.0
        endpos_y = 0.0
        endpos_yawr = 0.0
        deltaposx = 0.0
        deltaposy = 0.0
        deltaposyawr = 0.0
        T1 = None

        eval_cond = [True] * 4

        if last_mp_status != ConstantsMPmaneuver.MP_END_MANEUVER:  # Constant end of maneuver Mem Parking = 7
            # "Failed maneuver, The signal position values were not found"
            evaluation1 = evaluation2 = evaluation3 = evaluation4 = (
                "Evaluation is not possible because of missing info, maneuver not completed"
            )
            eval_cond = [False] * 4
            self.test_result = fc.INPUT_MISSING
            self.result.measured_result = FALSE

        else:
            # "Succesfull maneuver, completed Memory Parking"
            evaluation1 = "The Maneuver has finished correctly"
            eval_cond[0] = True
            # "Check Position of Vehicle to be stored"

            for idx, val in enumerate(confirmation_user):
                if val == ConstantsMPmaneuver.MP_CONFIRM_SLOT:
                    # Check for the confirmation of the user through all the measurement.
                    # The value is temporary stored, only the last T1 is stored.
                    T1 = idx

            if T1 is not None:
                # "Check End Position of Vehicle at the end of the maneuver MP-States = 7"
                savepos_x = posxcheck.values[T1]
                savepos_y = posycheck.values[T1]
                savepos_yawr = posyawcheck.values[T1]

                # "Check Stored position  of Vehicle at the end position of the recording"
                endpos_x = posxcheck.values[-1]
                endpos_y = posycheck.values[-1]
                endpos_yawr = posyawcheck.values[-1]

                # "Calculate Deltas"
                deltaposx = savepos_x - endpos_x
                deltaposy = savepos_y - endpos_y
                deltaposyawr = savepos_yawr - endpos_yawr

                # "Eval X Position"
                if abs(deltaposx) < ConstantsMPmaneuver.MP_MAX_DIST_TO_SAVEDPOSE_X:  # Constant for X check
                    # "Succesfull maneuver, X position in range"
                    evaluation2 = "The evaluation of X position is in range - PASS"
                    eval_cond[1] = True
                else:
                    # "Failed maneuver, X position not in range"
                    evaluation2 = "The evaluation of X position is not in range - FAIL"
                    eval_cond[1] = False

                # "Eval Y Position"
                if abs(deltaposy) < ConstantsMPmaneuver.MP_MAX_DIST_TO_SAVEDPOSE_Y:  # Constant for Y check
                    # "Succesfull maneuver, Y position in range"
                    evaluation3 = "The evaluation of Y position is in range - PASS"
                    eval_cond[2] = True
                else:
                    # "Failed maneuver, Y position not in range"
                    evaluation3 = "The evaluation of Y position is not in range - FAIL"
                    eval_cond[2] = False

                # "Eval Yaw Rate deviation"
                if abs(deltaposyawr) < ConstantsMPmaneuver.MP_MAX_DIST_TO_SAVEDPOSE_YAWR:  # Constant for Yaw Rate check
                    # "Succesfull maneuver, Yaw rate position in range"
                    evaluation4 = "The evaluation of Yaw rate position is in range - PASS"
                    eval_cond[3] = True
                else:
                    # "Failed maneuver, Yaw rate position not in range"
                    evaluation4 = "The evaluation of Yaw rate position is not in range - FAIL"
                    eval_cond[3] = False

        signal_summary[MfSignals.Columns.MPSTATE] = evaluation1
        signal_summary[MfSignals.Columns.APODOESTIMXPOSM] = evaluation2
        signal_summary[MfSignals.Columns.APODOESTIMYPOSM] = evaluation3
        signal_summary[MfSignals.Columns.APODOESTIMYAWRATERADPS] = evaluation4

        remark = " ".join("Check that maneuver ends at state 7".split())

        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)

        plots.append(self.sig_sum)

        if all(eval_cond):
            self.test_result = fc.PASS
        else:
            self.test_result = fc.FAIL

        if self.test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif self.test_result == fc.FAIL:
            self.result.measured_result = FALSE
        else:
            self.result.measured_result = DATA_NOK

        """Generate chart if test result FAILED """
        if self.test_result == fc.FAIL or ACTIVATE_PLOTS is True:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=time_signal.values.tolist(),
                    y=confirmation_user.values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[MfSignals.Columns.USERACTIONHEADUNIT_NU],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time_signal.values.tolist(),
                    y=posxcheck.values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[MfSignals.Columns.APODOESTIMXPOSM],
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=time_signal.values.tolist(),
                    y=posycheck.values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[MfSignals.Columns.APODOESTIMYPOSM],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time_signal.values.tolist(),
                    y=posyawcheck.values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[MfSignals.Columns.APODOESTIMYAWRATERADPS],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time_signal.values.tolist(),
                    y=mp_end_man.values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[MfSignals.Columns.MPSTATE],
                )
            )

            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)
            plots.append(fig)

        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)


@verifies("req-001")
@testcase_definition(
    name="Memory Parking End Maneuver evaluation",
    description="Verify that the MP is completed and position is in range between saved vs reached end position",
    # expected_result=BooleanResult(TRUE),
)
# @register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class MPCheckManeuver(TestCase):
    """MP test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPosesMP]
