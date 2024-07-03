#!/usr/bin/env python3
"""AUP CORE TEST for mf_sil."""
import logging
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.core.utilities import debug

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))  # nopep8
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh  # nopep8
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, MfSignals

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

EXAMPLE = "MF_AUP_CORE"


class StoreStepResults:
    """Initializes variables for multiple steps and provides a method
    to check their status and return corresponding results and color codes.
    """

    def __init__(self):
        """Initializes six variables with the value `fc.INPUT_MISSING`."""
        self.step_1 = fc.INPUT_MISSING
        self.step_2 = fc.INPUT_MISSING
        self.step_3 = fc.INPUT_MISSING
        self.step_4 = fc.INPUT_MISSING
        self.step_5 = fc.INPUT_MISSING
        self.step_6 = fc.INPUT_MISSING

    def check_result(self):
        """
        The function `check_result` checks the status of multiple steps and returns a corresponding result and color code.
        :return: The `check_result` method is returning a tuple with two values. The first value is one of the constants
        `fc.PASS`, `fc.INPUT_MISSING`, `fc.NOT_ASSESSED`, or `fc.FAIL` based on the conditions checked in the method. The
        second value is a color code represented as a string.
        """
        if (
            self.step_1 == fc.PASS
            and self.step_2 == fc.PASS
            and self.step_3 == fc.PASS
            and self.step_4 == fc.PASS
            and self.step_5 == fc.PASS
            and self.step_6 == fc.PASS
        ):
            return fc.PASS, "#28a745"
        elif (
            self.step_1 == fc.INPUT_MISSING
            or self.step_2 == fc.INPUT_MISSING
            or self.step_3 == fc.INPUT_MISSING
            or self.step_4 == fc.INPUT_MISSING
            or self.step_5 == fc.INPUT_MISSING
            or self.step_6 == fc.INPUT_MISSING
        ):
            return fc.INPUT_MISSING, "rgb(33,39,43)"
        elif (
            self.step_1 == fc.NOT_ASSESSED
            or self.step_2 == fc.NOT_ASSESSED
            or self.step_3 == fc.NOT_ASSESSED
            or self.step_4 == fc.NOT_ASSESSED
            or self.step_5 == fc.NOT_ASSESSED
            or self.step_6 == fc.NOT_ASSESSED
        ):
            return fc.NOT_ASSESSED, "rgb(129, 133, 137)"
        else:
            # self.case_result == fc.FAIL
            return fc.FAIL, "#dc3545"


verdict_obj = StoreStepResults()
signals_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Maneuver Check",
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START) to"
        "reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required"
        "speed (V_MIN = 0.002777778)."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, MfSignals)
class AupCoreET2FirstTest(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START)
    to reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required
    speed (V_MIN = 0.002777778).

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

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
        self.test_result = None

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        t2 = None
        signal_summary = {}
        example_signals = self.readers[EXAMPLE].signals

        vhcl_v = example_signals[MfSignals.Columns.VHCL_V]
        ap_time = example_signals[MfSignals.Columns.TIME]
        ap_state = example_signals[MfSignals.Columns.APSTATE]

        example_signals[MfSignals.Columns.HEADUNITVISU_SCREEN_NU]
        steer_ang_req = example_signals[MfSignals.Columns.STEERANGREQ_RAD]

        # "AP.headUnitVisualizationPort.screen_nu"[idx] == constants.HeadUnitVisuPortScreenVal.MANEUVER_A

        if np.any(ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN):
            t2 = np.argmax(ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN)

        if t2 is not None:
            idx_steer = None
            idx_vhcl_v = None
            cond_steer = False
            cond_vhcl_v = False

            idx_steer_mask = abs(steer_ang_req.iloc[t2:]) > constants.ConstantsAupCore.STEER_ANGLE_REQ_MIN
            idx_vhcl_v_mask = abs(vhcl_v.iloc[t2:]) > constants.ConstantsAupCore.V_MIN

            if any(idx_steer_mask):
                idx_steer = idx_steer_mask[idx_steer_mask].idxmin()

            if any(idx_vhcl_v_mask):
                idx_vhcl_v = idx_vhcl_v_mask[idx_vhcl_v_mask].idxmin()

            evaluation1 = " ".join(
                f"The evaluation of {signals_obj._properties[MfSignals.Columns.STEERANGREQ_RAD]} is PASSED, it took"
                " less than                                         10 seconds to reach the minimum                   "
                f"                      required steering angle({constants.ConstantsAupCore.STEER_ANGLE_REQ_MIN} rad).".split()
            )
            evaluation2 = " ".join(
                f"The evaluation of {signals_obj._properties[MfSignals.Columns.VHCL_V]} is PASSED,it took less than    "
                "                             10 seconds to reach the minimum                                 required"
                f" speed({constants.ConstantsAupCore.V_MIN} m/s).".split()
            )
            if idx_steer is not None:
                time_steer = ap_time.loc[idx_steer] - ap_time.iloc[t2]
                cond_steer = time_steer <= constants.ConstantsAupCore.T_SIM_MAX_START
                if not cond_steer:
                    evaluation1 = " ".join(
                        f"The evaluation of {signals_obj._properties[MfSignals.Columns.STEERANGREQ_RAD]} is FAILED, it"
                        f" took more than                         10 seconds({round(time_steer, 3)} s) to reach the"
                        " minimum                         required steering"
                        f" angle({constants.ConstantsAupCore.STEER_ANGLE_REQ_MIN} rad).".split()
                    )
            else:
                evaluation1 = " ".join(
                    f"The evaluation of {signals_obj._properties[MfSignals.Columns.STEERANGREQ_RAD]} is FAILED, the"
                    " values                         of the signal are always <"
                    f" {constants.ConstantsAupCore.STEER_ANGLE_REQ_MIN}.".split()
                )
            if idx_vhcl_v is not None:
                time_vhcl_v = ap_time.loc[idx_vhcl_v] - ap_time.iloc[t2]
                cond_vhcl_v = time_vhcl_v <= constants.ConstantsAupCore.T_SIM_MAX_START
                if not cond_vhcl_v:
                    evaluation2 = " ".join(
                        f"The evaluation of {signals_obj._properties[MfSignals.Columns.VHCL_V]} is FAILED, it took more"
                        f" than                             10 seconds({round(time_vhcl_v, 3)} s) to reach the minimum "
                        f"                            required speed({constants.ConstantsAupCore.V_MIN} m/s).".split()
                    )
            else:
                evaluation2 = " ".join(
                    f"The evaluation of {signals_obj._properties[MfSignals.Columns.VHCL_V]} is FAILED, the values      "
                    f"                   of the signal are always < {constants.ConstantsAupCore.V_MIN}.".split()
                )
            if cond_steer or cond_vhcl_v:
                self.result.measured_result = TRUE
                verdict_obj.step_1 = fc.PASS
            else:
                self.result.measured_result = FALSE
                verdict_obj.step_1 = fc.FAIL
        else:
            evaluation1 = evaluation2 = " ".join(
                "Evaluation not possible, the trigger value found in                "
                f" {signals_obj._properties[MfSignals.Columns.APSTATE]} (AP_AVG_ACTIVE_IN(3)) was never found.".split()
            )

            self.result.measured_result = DATA_NOK
            verdict_obj.step_1 = fc.NOT_ASSESSED

        signal_summary[MfSignals.Columns.STEERANGREQ_RAD] = evaluation1
        signal_summary[MfSignals.Columns.VHCL_V] = evaluation2
        remark = " ".join(
            "Verify that when AP.planningCtrlPort.apStates == 3 (AP_AVG_ACTIVE_IN), it takes less than 10.0 seconds"
            " (T_SIM_MAX_START)     to reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1 s) OR"
            " minimum required speed       (V_MIN = 0.002777778 s).".split()
        )
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.result.measured_result in [FALSE, DATA_NOK] or bool(constants.GeneralConstants.ACTIVATE_PLOTS):
            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=steer_ang_req.values.tolist(),
                    mode="lines",
                    name=MfSignals.Columns.STEERANGREQ_RAD,
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(), y=vhcl_v.values.tolist(), mode="lines", name=MfSignals.Columns.VHCL_V
                )
            )
            # self.fig.add_trace(
            #     go.Scatter(x=ap_time, y=head_unit_screen, mode="lines", name=MfSignals.Columns.HEADUNITVISU_SCREEN_NU)
            # )
            self.fig.add_trace(go.Scatter(x=ap_time, y=ap_state, mode="lines", name=MfSignals.Columns.APSTATE))
            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")
        try:
            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)
        except Exception as e:
            print(str(e))
        self.test_result = verdict_obj.step_1
        self.result.details["Step_result"] = verdict_obj.step_1


@teststep_definition(
    step_number=2,
    name="Maneuver Completion Time Check",
    description=(
        "Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and MANEUVER_FINISHED(5) were found)              "
        "   in less than 200.0 seconds(T_SIM_MAX)."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, MfSignals)
class AupCoreET2SecondTest(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and MANEUVER_FINISHED(5) were found)
    in less than 200.0 seconds(T_SIM_MAX).
    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """
        This function processes data related to head unit visualization screens and generates plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        self.test_result = None
        example_signals = self.readers[EXAMPLE].signals
        ap_time = example_signals[MfSignals.Columns.TIME]
        head_unit_screen = example_signals[MfSignals.Columns.HEADUNITVISU_SCREEN_NU]

        t2 = None
        signal_summary = {}
        cond_head_unit = False

        if np.any(head_unit_screen == constants.GeneralConstants.MANEUVER_ACTIVE):
            t2 = np.argmax(head_unit_screen == constants.GeneralConstants.MANEUVER_ACTIVE)

        if t2 is not None:
            idx_head_unit = None
            idx_steer_mask = abs(head_unit_screen.iloc[t2:]) == constants.HeadUnitVisuPortScreenVal.MANEUVER_FINISHED
            if any(idx_steer_mask):
                idx_head_unit = idx_steer_mask[idx_steer_mask].idxmin()

            evaluation = " ".join(
                f"The evaluation of {signals_obj._properties[MfSignals.Columns.HEADUNITVISU_SCREEN_NU]} is PASSED with"
                " value                     MANEUVER_FINISHED(5) found within"
                f" {constants.ConstantsAupCore.T_SIM_MAX} s.".split()
            )
            if idx_head_unit is not None:
                time_head_unit = ap_time.loc[idx_head_unit] - ap_time.iloc[t2]
                cond_head_unit = time_head_unit <= constants.ConstantsAupCore.T_SIM_MAX
                if not cond_head_unit:
                    evaluation = " ".join(
                        f"The evaluation of {signals_obj._properties[MfSignals.Columns.HEADUNITVISU_SCREEN_NU]} is"
                        f" FAILED with values >                         than {constants.ConstantsAupCore.T_SIM_MAX} s"
                        f" at timestamp                         {round(ap_time.loc[idx_head_unit], 3)} s.".split()
                    )
            else:
                evaluation = " ".join(
                    f"The evaluation of {signals_obj._properties[MfSignals.Columns.HEADUNITVISU_SCREEN_NU]} is FAILED,"
                    " the value                         MANEUVER_FINISHED(5) was not found.".split()
                )
            if cond_head_unit:
                self.result.measured_result = TRUE
                verdict_obj.step_2 = fc.PASS
            else:
                self.result.measured_result = FALSE
                verdict_obj.step_2 = fc.FAIL
        else:
            evaluation = " ".join(
                "The evaluation was not possible, the value MANEUVER_ACTIVE(17) for                    "
                f" {signals_obj._properties[MfSignals.Columns.HEADUNITVISU_SCREEN_NU]} was never found.".split()
            )
            self.result.measured_result = DATA_NOK
            verdict_obj.step_2 = fc.NOT_ASSESSED

        signal_summary[MfSignals.Columns.HEADUNITVISU_SCREEN_NU] = evaluation
        remark = " ".join(
            "Verify that the maneuver was finished (AP.headUnitVisualizationPort.screen_nu == 5) in less than 200.0"
            " seconds(T_SIM_MAX)".split()
        )
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        self.test_result = verdict_obj.step_2
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.result.measured_result in [FALSE, DATA_NOK] or bool(constants.GeneralConstants.ACTIVATE_PLOTS):
            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=head_unit_screen.values.tolist(),
                    mode="lines",
                    name=MfSignals.Columns.HEADUNITVISU_SCREEN_NU,
                )
            )
            self.fig.update_traces(showlegend=True, name=MfSignals.Columns.HEADUNITVISU_SCREEN_NU)
            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            # self.result.details["Plots"].append(
            #     self.fig.to_html(full_html=False, include_plotlyjs=False))
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)
        self.result.details["Step_result"] = verdict_obj.step_2


@teststep_definition(
    step_number=3,
    name="Simulation Time Check",
    description=(
        "Verify that the simulation time does not exceed the maximum time, maneuver has not been              "
        "   interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than          "
        "       maximum accepted."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, MfSignals)
class AupCoreET1ET5Test(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

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
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        self.test_result = None
        example_signals = self.readers[EXAMPLE].signals
        ap_time = example_signals[MfSignals.Columns.TIME]
        t_sim_max_s = example_signals[MfSignals.Columns.T_SIM_MAX_S]
        head_unit_screen = example_signals[MfSignals.Columns.HEADUNITVISU_SCREEN_NU]
        visu_port_messages = example_signals[MfSignals.Columns.HEADUNITVISU_MESSAGE_NU]
        maneuvering_space_exceed = example_signals[MfSignals.Columns.ALLOWEDMANEUVERINGSPACEEXCEED_BOOL]
        max_cycle_time_aup_step = example_signals[MfSignals.Columns.MAXCYCLETIMEOFAUPSTEP_MS]

        visu_constants = [
            constants.HeadUnitVisuPortMsgVal.INTERNAL_SYSTEM_ERROR,
            constants.HeadUnitVisuPortMsgVal.MAX_WAITING_TIME_EXCEEDED,
            constants.HeadUnitVisuPortMsgVal.PARKING_CANCELLED,
            constants.HeadUnitVisuPortMsgVal.PARKING_CANCELLED_THROTTLE,
            constants.HeadUnitVisuPortMsgVal.PARKING_CANCELLED_STEER,
            constants.HeadUnitVisuPortMsgVal.PARKING_FAILED,
        ]
        signal_summary = {}
        evaluation_visu = " ".join(
            f"The evaluation of {signals_obj._properties[MfSignals.Columns.HEADUNITVISU_SCREEN_NU]} is PASSED, with    "
            f"             values != {visu_constants}".split()
        )
        evaluation1 = " ".join(
            f"The evaluation of {signals_obj._properties[MfSignals.Columns.TIME]} is PASSED, with                    "
            f" values < values of {signals_obj._properties[MfSignals.Columns.T_SIM_MAX_S]} for the whole time period".split()
        )
        evaluation2 = " ".join(
            f"The evaluation of {signals_obj._properties[MfSignals.Columns.HEADUNITVISU_SCREEN_NU]} is PASSED, with    "
            f"                 values != {constants.HeadUnitVisuPortScreenVal.MANEUVER_INTRRERUPTED}".split()
        )
        evaluation3 = " ".join(
            f"The evaluation of {signals_obj._properties[MfSignals.Columns.ALLOWEDMANEUVERINGSPACEEXCEED_BOOL]} is"
            " PASSED, with                     values < 1".split()
        )
        evaluation4 = " ".join(
            f"The evaluation of {signals_obj._properties[MfSignals.Columns.MAXCYCLETIMEOFAUPSTEP_MS]} is PASSED, with  "
            f"                   values < {constants.ConstantsAupCore.AUP_CYCLE_TIME_MAX} (AUP_CYCLE_TIME_MAX)".split()
        )

        eval_cond = [True] * 5

        time_mask = ap_time >= t_sim_max_s
        head_unit_screen_mask = head_unit_screen == constants.HeadUnitVisuPortScreenVal.MANEUVER_INTRRERUPTED
        visu_port_messages_mask = visu_port_messages.isin(visu_constants)
        maneuvering_space_exceed_mask = maneuvering_space_exceed >= 1
        max_cycle_time_aup_step_mask = max_cycle_time_aup_step >= constants.ConstantsAupCore.AUP_CYCLE_TIME_MAX

        if any(time_mask):
            idx = time_mask[time_mask].idxmin()

            evaluation1 = " ".join(
                f"The evaluation of {signals_obj._properties[MfSignals.Columns.TIME]} is FAILED, with              "
                f"       a value >= {round(t_sim_max_s.loc[idx], 3)} s at timestamp"
                f" {round(ap_time.loc[idx], 3)} s.".split()
            )
            eval_cond[0] = False

        if any(head_unit_screen_mask):
            idx = head_unit_screen_mask[head_unit_screen_mask].idxmin()

            evaluation2 = " ".join(
                f"The evaluation of {signals_obj._properties[MfSignals.Columns.HEADUNITVISU_SCREEN_NU]} is FAILED,"
                " with                     a value =="
                f" {constants.HeadUnitVisuPortScreenVal.MANEUVER_INTRRERUPTED} at timestamp                    "
                f" {round(ap_time.loc[idx], 3)} s.".split()
            )
            eval_cond[1] = False
        if any(visu_port_messages_mask):
            idx = visu_port_messages_mask[visu_port_messages_mask].idxmin()

            evaluation_visu = " ".join(
                f"The evaluation of {signals_obj._properties[MfSignals.Columns.HEADUNITVISU_SCREEN_NU]} is FAILED,"
                f" with a                             value == {visu_port_messages.loc[idx]} at timestamp"
                f" {round(ap_time.loc[idx], 3)} s                             (all the values should be different"
                f" from the following: {visu_constants}).".split()
            )
            eval_cond[2] = False
        if any(maneuvering_space_exceed_mask):
            idx = maneuvering_space_exceed_mask[maneuvering_space_exceed_mask].idxmin()

            evaluation3 = " ".join(
                "The evaluation of"
                f" {signals_obj._properties[MfSignals.Columns.ALLOWEDMANEUVERINGSPACEEXCEED_BOOL]} is FAILED, with "
                f"                    a value >= 1 at timestamp {round(ap_time.loc[idx], 3)} ss".split()
            )
            eval_cond[3] = False
        if any(max_cycle_time_aup_step_mask):
            idx = max_cycle_time_aup_step_mask[max_cycle_time_aup_step_mask].idxmin()

            evaluation4 = " ".join(
                f"The evaluation of {signals_obj._properties[MfSignals.Columns.MAXCYCLETIMEOFAUPSTEP_MS]} is"
                " FAILED, with                     a value >"
                f" AUP_CYCLE_TIME_MAX({constants.ConstantsAupCore.AUP_CYCLE_TIME_MAX}) at timestamp                "
                f"     {round(ap_time.loc[idx], 3)} s.".split()
            )
            eval_cond[4] = False

        if all(eval_cond):
            self.result.measured_result = TRUE
            verdict_obj.step_3 = fc.PASS
        else:
            self.result.measured_result = FALSE
            verdict_obj.step_3 = fc.FAIL
        signal_summary[MfSignals.Columns.TIME] = evaluation1
        signal_summary[MfSignals.Columns.HEADUNITVISU_SCREEN_NU] = evaluation2
        signal_summary[MfSignals.Columns.HEADUNITVISU_MESSAGE_NU] = evaluation_visu
        signal_summary[MfSignals.Columns.ALLOWEDMANEUVERINGSPACEEXCEED_BOOL] = evaluation3
        signal_summary[MfSignals.Columns.MAXCYCLETIMEOFAUPSTEP_MS] = evaluation4

        self.test_result = verdict_obj.step_3

        remark = " ".join(
            "Verify that for the whole parking, the duration has not exceeded                                          "
            "             max time, manuever has not been intrerupted, no error messages                               "
            "                        appeared, space has not been exceeded and cycle time is                           "
            "                              lower than maximum accepted".split()
        )
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")
        # remarks.append(
        #     "3. Verify that for the whole parking, the duration has not exceeded max time, manuever has not \
        #     been intrerupted, no error messages appeared, space has not been exceeded and cycle time is \
        #     lower than maximum accepted")

        if self.result.measured_result in [FALSE, DATA_NOK] or bool(constants.GeneralConstants.ACTIVATE_PLOTS):
            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=head_unit_screen.values.tolist(),
                    mode="lines",
                    name=MfSignals.Columns.HEADUNITVISU_SCREEN_NU,
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=visu_port_messages.values.tolist(),
                    mode="lines",
                    name=MfSignals.Columns.HEADUNITVISU_SCREEN_NU,
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=maneuvering_space_exceed.values.tolist(),
                    mode="lines",
                    name=MfSignals.Columns.ALLOWEDMANEUVERINGSPACEEXCEED_BOOL,
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=max_cycle_time_aup_step.values.tolist(),
                    mode="lines",
                    name=MfSignals.Columns.MAXCYCLETIMEOFAUPSTEP_MS,
                )
            )
            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)
        self.result.details["Step_result"] = verdict_obj.step_3


@teststep_definition(
    step_number=4,
    name="Number of Strokes Threshold check",
    description=(
        "Verify that after the maneuver has begun, the number of strokes does not exceed maximum accepted              "
        "   number of strokes."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, MfSignals)
class AupCoreET2ET5Test(TestStep):
    """testcase that can be tested by a simple pass/fail test.

        Objective
        ---------
    .
        Detail
        ------

        In case there is no signal change to 1 the testcase is failed.
        The test ist performed for all recordings of the collection
    """

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
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        self.test_result = None
        example_signals = self.readers[EXAMPLE].signals
        ap_time = example_signals[MfSignals.Columns.TIME]
        ap_state = example_signals[MfSignals.Columns.APSTATE]
        # head_unit_screen = example_signals[MfSignals.Columns.HEADUNITVISU_SCREEN_NU]
        n_strokes_max = example_signals[MfSignals.Columns.N_STROKES_MAX_NU]
        ap_num_strokes = example_signals[MfSignals.Columns.NUMBEROFSTROKES]

        # "AP.planningCtrlPort.apStates"[idx] == constants.HeadUnitVisuPortScreenVal.MANEUVER_ACTIVE
        t2 = None
        signal_summary = {}

        if np.any(ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN):
            t2 = np.argmax(ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN)
        evaluation = " ".join(
            f"The evaluation of {signals_obj._properties[MfSignals.Columns.NUMBEROFSTROKES]}                     is"
            f" PASSED with values <= than values of {signals_obj._properties[MfSignals.Columns.N_STROKES_MAX_NU]}".split()
        )
        if t2 is not None:
            self.result.measured_result = TRUE
            verdict_obj.step_4 = fc.PASS
            num_strokes_check_mask = ap_num_strokes.iloc[t2:] > n_strokes_max.iloc[t2:]
            if (num_strokes_check_mask).any():
                idx = num_strokes_check_mask.index[num_strokes_check_mask][0]
                evaluation = " ".join(
                    f"The evaluation of {signals_obj._properties[MfSignals.Columns.NUMBEROFSTROKES]}               "
                    f"          is FAILED because there is a value > {n_strokes_max.loc[idx]} at timestamp        "
                    f"                 {round(ap_time.loc[idx], 3)} s.".split()
                )
                self.result.measured_result = FALSE
                verdict_obj.step_4 = fc.FAIL
        else:
            self.result.measured_result = DATA_NOK
            verdict_obj.step_4 = fc.NOT_ASSESSED
            evaluation = " ".join(
                "Evaluation not possible, the trigger value AP_AVG_ACTIVE_IN(3) for                        "
                f" {signals_obj._properties[MfSignals.Columns.APSTATE]} was never found.".split()
            )
        signal_summary[MfSignals.Columns.NUMBEROFSTROKES] = evaluation
        self.test_result = verdict_obj.step_4
        remark = " ".join(
            "Verify that after the maneuver has begun (AP.planningCtrlPort.apStates == 3 [AP_AVG_ACTIVE_IN]), the"
            " number of strokes                                                        does not exceed maximum accepted"
            " number of strokes".split()
        )
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.result.measured_result in [FALSE, DATA_NOK] or bool(constants.GeneralConstants.ACTIVATE_PLOTS):
            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=ap_num_strokes.values.tolist(),
                    mode="lines",
                    name=MfSignals.Columns.NUMBEROFSTROKES,
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(), y=ap_state.values.tolist(), mode="lines", name=MfSignals.Columns.APSTATE
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=n_strokes_max.values.tolist(),
                    mode="lines",
                    name=MfSignals.Columns.N_STROKES_MAX_NU,
                )
            )
            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            # self.result.details["Plots"].append(
            #     self.fig.to_html(full_html=False, include_plotlyjs=False))
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)
        self.result.details["Step_result"] = verdict_obj.step_4


@teststep_definition(
    step_number=5,
    name="Acceleration and Speed Threshold Check",
    description=(
        "Check that after Planning control port is equal to 3, the maximum acceleration and speed does not             "
        "    exceed accepted values."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, MfSignals)
class AupCoreET3ET5Test(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

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
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        example_signals = self.readers[EXAMPLE].signals
        vhcl_v = example_signals[MfSignals.Columns.VHCL_V]
        ap_time = example_signals[MfSignals.Columns.TIME]
        ap_state = example_signals[MfSignals.Columns.APSTATE]
        car_ax = example_signals[MfSignals.Columns.CAR_AX]
        car_ay = example_signals[MfSignals.Columns.CAR_AY]
        vhcl_yaw_rate = example_signals[MfSignals.Columns.VHCLYAWRATE]
        self.test_result = None
        # "Ap.planningCtrlPort.apStates"[idx] == constants.ConstantsAupCore.THRESHOLD_T3
        t3 = None
        signal_summary = {}

        if np.any(ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN):
            t3 = np.argmax(ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN)
        evaluation1 = " ".join(
            f"The evaluation of {signals_obj._properties[MfSignals.Columns.CAR_AX]} is PASSED with values <            "
            f"                     {constants.ConstantsAupCore.LONG_ACC_EGO_MAX} m/s^2.".split()
        )
        evaluation2 = " ".join(
            f"The evaluation of {signals_obj._properties[MfSignals.Columns.CAR_AY]} is PASSED with values <=           "
            f"                      {constants.ConstantsAupCore.LAT_ACC_EGO_MAX} m/s^2.".split()
        )
        evaluation3 = " ".join(
            f"The evaluation of {signals_obj._properties[MfSignals.Columns.VHCL_V]} is PASSED with values <=           "
            f"                      {constants.GeneralConstants.V_MAX_L3} m/s".split()
        )
        evaluation4 = " ".join(
            f"The evaluation of {signals_obj._properties[MfSignals.Columns.VHCLYAWRATE]} is PASSED with values <=      "
            f"                           {constants.ConstantsAupCore.YAW_RATE_MAX} rad/s.".split()
        )
        eval_cond = [True] * 4
        if t3 is not None:
            car_ax_mask = car_ax.iloc[t3:] >= constants.ConstantsAupCore.LONG_ACC_EGO_MAX
            car_ay_mask = car_ay.iloc[t3:] >= constants.ConstantsAupCore.LAT_ACC_EGO_MAX
            vhcl_v_mask = vhcl_v.iloc[t3:] >= constants.GeneralConstants.V_MAX_L3
            vhcl_yaw_rate_mask = vhcl_yaw_rate.iloc[t3:] >= constants.ConstantsAupCore.YAW_RATE_MAX

            if any(car_ax_mask):
                idx = car_ax_mask[car_ax_mask].idxmin()

                evaluation1 = " ".join(
                    f"The evaluation of {signals_obj._properties[MfSignals.Columns.CAR_AX]} is FAILED with a value"
                    f" >=                         {constants.ConstantsAupCore.LONG_ACC_EGO_MAX} m/s^2 at timestamp "
                    f"                       {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[0] = False
            if any(car_ay_mask):
                idx = car_ay_mask[car_ay_mask].idxmin()

                evaluation2 = " ".join(
                    f"The evaluation of {signals_obj._properties[MfSignals.Columns.CAR_AY]} is FAILED with a value"
                    f" >=                         {constants.ConstantsAupCore.LAT_ACC_EGO_MAX} m/s^2 at timestamp  "
                    f"                       {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[1] = False
            if any(vhcl_v_mask):
                idx = vhcl_v_mask[vhcl_v_mask].idxmin()

                evaluation3 = " ".join(
                    f"The evaluation of {signals_obj._properties[MfSignals.Columns.VHCL_V]} is FAILED with a value"
                    f" >=                         {constants.GeneralConstants.V_MAX_L3} m/s at timestamp           "
                    f"              {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[2] = False
            if any(vhcl_yaw_rate_mask):
                idx = vhcl_yaw_rate_mask[vhcl_yaw_rate_mask].idxmin()

                evaluation4 = " ".join(
                    f"The evaluation of {signals_obj._properties[MfSignals.Columns.VHCLYAWRATE]} is FAILED with a"
                    f" value >=                         {constants.ConstantsAupCore.YAW_RATE_MAX} rad/s at"
                    f" timestamp                         {round(ap_time.loc[idx], 3)} s.".split()
                )
                eval_cond[3] = False

            if all(eval_cond):
                self.result.measured_result = TRUE
                verdict_obj.step_5 = fc.PASS
            else:
                self.result.measured_result = FALSE
                verdict_obj.step_5 = fc.FAIL
        else:
            evaluation1 = evaluation2 = evaluation3 = evaluation4 = " ".join(
                "Evaluation not possible, the trigger value AP_AVG_ACTIVE_IN(3) for                            "
                f" {signals_obj._properties[MfSignals.Columns.APSTATE]} was never found.".split()
            )
            self.result.measured_result = DATA_NOK
            verdict_obj.step_5 = fc.NOT_ASSESSED
        self.test_result = verdict_obj.step_5
        signal_summary[MfSignals.Columns.CAR_AX] = evaluation1
        signal_summary[MfSignals.Columns.CAR_AY] = evaluation2
        signal_summary[MfSignals.Columns.VHCL_V] = evaluation3
        signal_summary[MfSignals.Columns.VHCLYAWRATE] = evaluation4

        remark = " ".join(
            "Checks that after AP.planningCtrlPort.apStates == 3 (AP_AVG_ACTIVE_IN), the                 "
            "        maximum acceleration and speed does not                                                         "
            " exceed the accepted value".split()
        )
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.result.measured_result in [FALSE, DATA_NOK] or bool(constants.GeneralConstants.ACTIVATE_PLOTS):
            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(), y=car_ax.values.tolist(), mode="lines", name=MfSignals.Columns.CAR_AX
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(), y=car_ay.values.tolist(), mode="lines", name=MfSignals.Columns.CAR_AY
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(), y=vhcl_v.values.tolist(), mode="lines", name=MfSignals.Columns.VHCL_V
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=vhcl_yaw_rate.values.tolist(),
                    mode="lines",
                    name=MfSignals.Columns.VHCLYAWRATE,
                )
            )
            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            # self.result.details["Plots"].append(
            #     self.fig.to_html(full_html=False, include_plotlyjs=False))
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)
        self.result.details["Step_result"] = verdict_obj.step_5


@teststep_definition(
    step_number=6,
    name="Position Check",
    description="Check that after the target has reached the desired position, no deviations are present.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, MfSignals)
class AupCoreET4ET5Test(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

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

        # self.result.details["Plots"] = []
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        self.test_result = None
        T12 = None
        T11 = None
        T10 = None
        first_valid_index = None
        sim_time = None
        total_time = None
        idx_last = None
        max_collision = None
        max_head_unit = None
        max_speed = None
        max_steer_whl_ang = None
        max_lat_dist = None
        max_long_dist = None
        max_yaw_diff = None
        max_nr_of_stroks = None
        max_huv_is_port = None
        max_maneuvering_space_exceed = None
        max_car_ay = None
        max_yaw_rate = None
        max_car_ax = None
        max_cycle_time = None
        max_long_dist_error_otp = None
        max_lat_dist_error_otp = None
        max_yaw_dist_error_otp = None
        example_signals = self.readers[EXAMPLE].signals
        ap_time = example_signals[MfSignals.Columns.TIME]
        reached_status = example_signals[MfSignals.Columns.REACHEDSTATUS]
        dev_lat_dist_to_target = example_signals[MfSignals.Columns.LATDISTTOTARGET]
        ap_lat_max_dev = example_signals[MfSignals.Columns.LATMAXDEVIATION]
        dev_long_dist_to_target = example_signals[MfSignals.Columns.LONGDISTTOTARGET]
        ap_long_max_dev = example_signals[MfSignals.Columns.LONGMAXDEVIATION]
        dev_yaw_diff_to_target = example_signals[MfSignals.Columns.YAWDIFFTOTARGET]
        ap_yaw_max_dev = example_signals[MfSignals.Columns.YAWMAXDEVIATION]

        signal_summary = {}
        t_start_evaluation = None
        total_time = 0
        idx_last = None
        # # the index when AP.targetPosesPort.selectedPoseData.reachedStatus >0 for 0.8s
        first_valid_index = None

        for idx, val in enumerate(reached_status):
            if val > 0:
                if idx_last is not None:
                    total_time += (idx - idx_last) / constants.GeneralConstants.IDX_TO_S
                    if first_valid_index is None:
                        first_valid_index = idx
                    if round(total_time, 6) >= constants.GeneralConstants.T_POSE_REACHED:
                        t_start_evaluation = first_valid_index
                        T11 = first_valid_index
                        break
                idx_last = idx
            else:
                idx_last = None
                total_time = 0

        evaluation0 = " ".join(
            "The evaluation is PASSED, all values for                "
            f" {signals_obj._properties[MfSignals.Columns.LATDISTTOTARGET]} are < values of"
            f" {signals_obj._properties[MfSignals.Columns.LATMAXDEVIATION]}.".split()
        )
        evaluation1 = " ".join(
            "The evaluation is PASSED, all values for                "
            f" {signals_obj._properties[MfSignals.Columns.LONGDISTTOTARGET]} are < values of"
            f" {signals_obj._properties[MfSignals.Columns.LONGMAXDEVIATION]}.".split()
        )
        evaluation2 = " ".join(
            "The evaluation is PASSED, all values for                "
            f" {signals_obj._properties[MfSignals.Columns.YAWDIFFTOTARGET]} are < values of"
            f" {signals_obj._properties[MfSignals.Columns.YAWMAXDEVIATION]}.".split()
        )

        if t_start_evaluation is not None:
            """check if TARGET_POSE_DEV_LAT, TARGET_POSE_DEV_LONG and TARGET_POSE_DEV_YAW are lower than
            the maximum signal for each signal"""
            # t_start_evaluation = idx+ 0.8
            dev_lat_dist_to_target_mask = (
                dev_lat_dist_to_target.iloc[t_start_evaluation:] >= ap_lat_max_dev.iloc[t_start_evaluation:]
            )

            dev_long_dist_to_target_mask = (
                dev_long_dist_to_target.iloc[t_start_evaluation:] >= ap_long_max_dev.iloc[t_start_evaluation:]
            )

            dev_yaw_diff_to_target_mask = (
                dev_yaw_diff_to_target.iloc[t_start_evaluation:] >= ap_yaw_max_dev.iloc[t_start_evaluation:]
            )

            eval_cond = [True] * 3

            if any(np.absolute(dev_lat_dist_to_target_mask)):

                idx = dev_lat_dist_to_target_mask[dev_lat_dist_to_target_mask].idxmin()
                eval_cond[0] = False
                evaluation0 = " ".join(
                    f"The evaluation for {signals_obj._properties[MfSignals.Columns.LATDISTTOTARGET]} is FAILED,"
                    " the value is                         >="
                    f" {signals_obj._properties[MfSignals.Columns.LATMAXDEVIATION]} at timestamp"
                    f" {round(ap_time.loc[idx], 3)} s.".split()
                )
            if any(np.absolute(dev_long_dist_to_target_mask)):

                idx = dev_long_dist_to_target_mask[dev_long_dist_to_target_mask].idxmin()
                eval_cond[1] = False
                evaluation1 = " ".join(
                    f"The evaluation for {signals_obj._properties[MfSignals.Columns.LONGDISTTOTARGET]} is FAILED,"
                    " the value is                         >="
                    f" {signals_obj._properties[MfSignals.Columns.LONGMAXDEVIATION]} at timestamp"
                    f" {round(ap_time.loc[idx], 3)} s.".split()
                )
            if any(np.absolute(dev_yaw_diff_to_target_mask)):

                idx = dev_yaw_diff_to_target_mask[dev_yaw_diff_to_target_mask].idxmin()
                eval_cond[2] = False
                evaluation2 = " ".join(
                    f"The evaluation for {signals_obj._properties[MfSignals.Columns.YAWDIFFTOTARGET]} is FAILED,"
                    " the value is                         >="
                    f" {signals_obj._properties[MfSignals.Columns.YAWMAXDEVIATION]} at timestamp"
                    f" {round(ap_time.loc[idx], 3)} s.".split()
                )

            if all(eval_cond):
                self.result.measured_result = TRUE
                verdict_obj.step_6 = fc.PASS
            else:
                self.result.measured_result = FALSE
                verdict_obj.step_6 = fc.FAIL
        else:
            self.result.measured_result = DATA_NOK
            verdict_obj.step_6 = fc.NOT_ASSESSED
            # eval_cond = [False] * 3
            evaluation0 = evaluation1 = evaluation2 = " ".join(
                f"Evaluation not possible, {signals_obj._properties[MfSignals.Columns.REACHEDSTATUS]} was not  > 0 for"
                " 0.8s.".split()
            )
        signal_summary[MfSignals.Columns.LATDISTTOTARGET] = evaluation0
        signal_summary[MfSignals.Columns.LONGDISTTOTARGET] = evaluation1
        signal_summary[MfSignals.Columns.YAWDIFFTOTARGET] = evaluation2
        self.test_result = verdict_obj.step_6

        remark = " ".join(
            "Check that after the target has reached the desired position        "
            " (Ap.targetPosesPort.selectedPoseData.reachedStatus > 0 for 0.8s), no deviations are present".split()
        )
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.result.measured_result in [FALSE, DATA_NOK] or bool(constants.GeneralConstants.ACTIVATE_PLOTS):
            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=reached_status.values.tolist(),
                    mode="lines",
                    name=MfSignals.Columns.REACHEDSTATUS,
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=dev_lat_dist_to_target.values.tolist(),
                    mode="lines",
                    name=MfSignals.Columns.LATDISTTOTARGET,
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=ap_lat_max_dev.values.tolist(),
                    mode="lines",
                    name=MfSignals.Columns.LATMAXDEVIATION,
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=dev_long_dist_to_target.values.tolist(),
                    mode="lines",
                    name=MfSignals.Columns.LONGDISTTOTARGET,
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=ap_long_max_dev.values.tolist(),
                    mode="lines",
                    name=MfSignals.Columns.LONGMAXDEVIATION,
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=dev_yaw_diff_to_target.values.tolist(),
                    mode="lines",
                    name=MfSignals.Columns.YAWDIFFTOTARGET,
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time.values.tolist(),
                    y=ap_yaw_max_dev.values.tolist(),
                    mode="lines",
                    name=MfSignals.Columns.YAWMAXDEVIATION,
                )
            )
            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plot_titles.append("")
            plots.append(self.fig)
            remarks.append("")

        try:
            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
            for plot_title in plot_titles:
                self.result.details["Plot_titles"].append(plot_title)
            for remark in remarks:
                self.result.details["Remarks"].append(remark)
        except Exception as e:
            print(str(e))

        vhcl_v = example_signals[MfSignals.Columns.VHCL_V]
        ap_time = example_signals[MfSignals.Columns.TIME]
        ap_state = example_signals[MfSignals.Columns.APSTATE]
        car_ax = example_signals[MfSignals.Columns.CAR_AX]
        car_ay = example_signals[MfSignals.Columns.CAR_AY]
        vhcl_yaw_rate = example_signals[MfSignals.Columns.VHCLYAWRATE]
        action_head_unit = example_signals[MfSignals.Columns.USERACTIONHEADUNIT_NU]
        sensor_collision_count = example_signals[MfSignals.Columns.COLLISIONCOUNT]
        head_unit_screen = example_signals[MfSignals.Columns.HEADUNITVISU_SCREEN_NU]
        ap_num_strokes = example_signals[MfSignals.Columns.NUMBEROFSTROKES]
        visu_port_messages = example_signals[MfSignals.Columns.HEADUNITVISU_MESSAGE_NU]
        maneuvering_space_exceed = example_signals[MfSignals.Columns.ALLOWEDMANEUVERINGSPACEEXCEED_BOOL]
        steer_ang_req = example_signals[MfSignals.Columns.STEERANGREQ_RAD]
        max_cycle_time_aup_step = example_signals[MfSignals.Columns.MAXCYCLETIMEOFAUPSTEP_MS]
        long_diff_optimal_tp = example_signals[MfSignals.Columns.LONGDIFFOPTIMALTP_FINALEGOPOSE]
        lat_diff_optimal_tp = example_signals[MfSignals.Columns.LATDIFFOPTIMALTP_FINALEGOPOSE]
        yaw_diff_optimal_tp = example_signals[MfSignals.Columns.YAWDIFFOPTIMALTP_FINALEGOPOSE]

        if np.any(ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN):
            T12 = np.argmax(ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN)

        if np.any(action_head_unit == constants.ConstantsAupCore.TOGGLE_AP_ACTIVE):
            T10 = np.argmax(action_head_unit == constants.ConstantsAupCore.TOGGLE_AP_ACTIVE)

        # calc for every element in the table
        if T10 is not None:

            sim_time = round(ap_time.iloc[-1], 3)
            max_collision = round(max(sensor_collision_count.iloc[T10:]), 3)
            max_head_unit = round(max(head_unit_screen.iloc[T10:]), 3)
            max_steer_whl_ang = round(max(np.absolute(np.rad2deg(steer_ang_req.iloc[T10:]))), 3)
            max_nr_of_stroks = round(max(ap_num_strokes.iloc[T10:]), 3)
            max_huv_is_port = round(max(visu_port_messages.iloc[T10:]), 3)
            max_maneuvering_space_exceed = round(max(maneuvering_space_exceed.iloc[T10:]), 3)

        else:
            sim_time = "n.a."
            max_collision = "n.a."
            max_head_unit = "n.a."
            max_steer_whl_ang = "n.a."
            max_nr_of_stroks = "n.a."
            max_huv_is_port = "n.a."
            max_maneuvering_space_exceed = "n.a."

        if T11 is not None:
            max_lat_dist = round(max(np.absolute(dev_lat_dist_to_target.iloc[T11:])), 3)
            max_long_dist = round(max(np.absolute(dev_long_dist_to_target.iloc[T11:])), 3)
            max_yaw_diff = round(max(np.rad2deg(np.absolute(dev_yaw_diff_to_target.iloc[T11:]))), 3)
        else:
            max_lat_dist = "n.a."
            max_long_dist = "n.a."
            max_yaw_diff = "n.a."

        if T12 is not None:
            max_speed = round(max(np.absolute(vhcl_v.iloc[T12:])), 3)
            max_car_ay = round(max(np.absolute(car_ay.iloc[T12:])), 3)
            max_yaw_rate = round(max(np.absolute(np.rad2deg(vhcl_yaw_rate.iloc[T12:]))), 3)
            max_car_ax = round(max(np.absolute(car_ax.iloc[T12:])), 3)
        else:
            max_speed = "n.a."
            max_car_ay = "n.a."
            max_yaw_rate = "n.a."
            max_car_ax = "n.a."

        max_cycle_time = round(max(max_cycle_time_aup_step), 3)
        max_long_dist_error_otp = round(max(long_diff_optimal_tp), 3)
        max_lat_dist_error_otp = round(max(lat_diff_optimal_tp), 3)
        max_yaw_dist_error_otp = round(max(yaw_diff_optimal_tp), 3)
        verdict, color = verdict_obj.check_result()

        additional_results_dict = {
            "Verdict": {"value": verdict.title(), "color": color},
            "SimulationTime[s]": {"value": sim_time, "color": fh.apply_color(sim_time, 200, "<", 20, ">=<=")},
            "max Collisions": {"value": max_collision, "color": fh.apply_color(max_collision, 0, "==")},
            "max headUnitVisPortScreen": {
                "value": max_head_unit,
                "color": fh.apply_color(max_head_unit, 5, "==", 5, ">"),
            },
            "max VehicleSpeed[m/s]": {"value": max_speed, "color": fh.apply_color(max_speed, 2.7, "<", 1.35, ">=<=")},
            "max steerWhlAngRequest[deg]": {
                "value": max_steer_whl_ang,
                "color": fh.apply_color(max_steer_whl_ang, 5.7, ">="),
            },
            "max abs latDistToTarget[m]": {
                "value": max_lat_dist,
                "color": fh.apply_color(max_lat_dist, 0.05, "<", 0.03, ">=<="),
            },
            "max abs longDistToTarget[m]": {
                "value": max_long_dist,
                "color": fh.apply_color(max_long_dist, 0.10, "<", 0.05, ">=<="),
            },
            "max abs yawDiffToTarget[deg]": {
                "value": max_yaw_diff,
                "color": fh.apply_color(max_yaw_diff, 1.0, "<", 0.5, ">=<="),
            },
            "max NoOfStrokes": {
                "value": max_nr_of_stroks,
                "color": fh.apply_color(max_nr_of_stroks, 11, "<", 1, ">=<="),
            },
            "max HUVisPort.message": {"value": max_huv_is_port, "color": fh.apply_color(max_huv_is_port, 6, "!=")},
            "max ManeuveringSpaceExceed": {
                "value": max_maneuvering_space_exceed,
                "color": fh.apply_color(max_maneuvering_space_exceed, 1, "<"),
            },
            "max Car.ay[m/s^2]": {"value": max_car_ay, "color": fh.apply_color(max_car_ay, 1, "<", 0.5, ">=<=")},
            "max YawRate_max[deg/s]": {
                "value": max_yaw_rate,
                "color": fh.apply_color(max_yaw_rate, 25, "<", 10, ">=<="),
            },
            "max Car.ax[m/s^2]": {"value": max_car_ax, "color": fh.apply_color(max_car_ax, 2, "<", 1, ">=<=")},
            "max CycleTime": {"value": max_cycle_time, "color": fh.apply_color(max_cycle_time, 100, "<")},
            "max LongDistErrorOTP_FinalEgoPoss[m]": {
                "value": max_long_dist_error_otp,
                "color": fh.apply_color(max_long_dist_error_otp, -1, "==", [0, 0.2], "[>=<]"),
            },
            "max LatDistErrorOTP_FinalEgoPoss[m]": {
                "value": max_lat_dist_error_otp,
                "color": fh.apply_color(max_lat_dist_error_otp, -1, "==", [0, 0.1], "[>=<]"),
            },
            "max YawDistErrorOTP_FinalEgoPoss[deg]": {
                "value": max_yaw_dist_error_otp,
                "color": fh.apply_color(max_yaw_dist_error_otp, -1, "==", [0, 2], "[>=<]"),
            },
        }
        self.result.details["Additional_results"] = additional_results_dict


@verifies("req-001")
@testcase_definition(
    name="MF AUP CORE",
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START)                 to"
        " reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required                "
        " speed (V_MIN = 0.002777778).                 Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and"
        " MANEUVER_FINISHED(5) were found)                 in less than 200.0 seconds(T_SIM_MAX).                "
        " Verify that for the whole parking, the duration has not exceeded max time, maneuver has not been             "
        "    interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than         "
        "        maximum accepted.                 Verify that after the maneuver has begun, the number of strokes does"
        " not exceed maximum accepted                 number of strokes.                 Check that after Planning"
        " control port is equal to 3, the maximum acceleration and speed does not                 exceed accepted"
        " values.                 Check that after the target has reached the desired position, no deviations are"
        " present."
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class FTParkingAupCore(TestCase):
    """AUP CORE test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            AupCoreET2FirstTest,
            AupCoreET2SecondTest,
            AupCoreET1ET5Test,
            AupCoreET2ET5Test,
            AupCoreET3ET5Test,
            AupCoreET4ET5Test,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.
    """
    test_bsigs = [r"D:\parking\S_2023-06-30_11-48\AP_SmallRegressionTests\AUPSim_UC_ParRight_ST-1_06_01_B_SI_On.erg"]

    debug(
        FTParkingAupCore,
        *test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
        kpi_report=False,
        dev_report=True,
    )
    _log.debug("All done.")


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"
    out_folder = working_directory / "out"

    main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)
