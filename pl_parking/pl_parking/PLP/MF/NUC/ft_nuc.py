"""NUC Functional Test"""

import os
import sys

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

import logging

import plotly.graph_objects as go
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, MfSignals
from pl_parking.PLP.MF.constants import ConstantsNuc, GeneralConstants, PlotlyTemplate

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


SIGNAL_DATA = "MF_NUC"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="NUC",
    description=(
        "Check that after Ap.planningCtrlPort.apStates == 1 (PLANNING_CONTROL_ACTIVE), driving mode request is not"
        " TRUE, trajectory control is NOT ACTIVE and use case is FALSE.."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TestStepFtParkingNUC(TestStep):
    """Test Step Class"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        t2 = None
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        read_data = self.readers[SIGNAL_DATA].signals
        test_result = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        signal_summary = {}

        sim_time = None
        max_ap_state = None
        max_strokes = None
        max_visu_screen = None
        T9 = None
        T11 = None
        signal_name = example_obj._properties

        ap_state = read_data["ApState"].tolist()
        ap_traj_ctrl_active = read_data["ApTrajCtrlActive"].tolist()
        ap_driving_mode_req = read_data["ApDrivingModeReq"].tolist()
        ap_usecase = read_data["ApUsecase"].tolist()
        ap_time = read_data["time"].tolist()
        ap_nr_strokes = read_data["NumberOfStrokes"].tolist()
        head_unit_screen = read_data["headUnitVisu_screen_nu"].tolist()

        for idx, val in enumerate(ap_state):
            if val == ConstantsNuc.PLANNING_CONTROL_ACTIVE:
                t2 = idx
                break

        evaluation1 = " ".join(
            f"The evaluation for {signal_name['ApTrajCtrlActive']} is PASSED,            with values !="
            f" {ConstantsNuc.TRAJ_CTRL_ACTIVE}".split()
        )
        evaluation2 = " ".join(
            f"The evaluation for {signal_name['ApDrivingModeReq']} is PASSED,            with values !="
            f" {ConstantsNuc.DRIVING_MODE_REQUEST_TRUE}".split()
        )
        evaluation3 = " ".join(
            f"The evaluation for {signal_name['ApUsecase']} is PASSED,            with values =="
            f" {ConstantsNuc.USE_CASE_FALSE}".split()
        )
        if t2 is not None:
            eval_cond = [True] * 3

            for idx in range(t2, len(ap_state)):
                if ap_traj_ctrl_active[idx] == ConstantsNuc.TRAJ_CTRL_ACTIVE and eval_cond[0]:
                    evaluation1 = " ".join(
                        f"The evaluation for {signal_name['ApTrajCtrlActive']} is FAILED because                       "
                        f"          there is a value equal to {ConstantsNuc.TRAJ_CTRL_ACTIVE} at timestamp             "
                        f"                    {round(ap_time[idx], 3)} s.".split()
                    )
                    eval_cond[0] = False

                if ap_driving_mode_req[idx] == ConstantsNuc.DRIVING_MODE_REQUEST_TRUE and eval_cond[1]:
                    evaluation2 = " ".join(
                        f"The evaluation for {signal_name['ApDrivingModeReq']} is FAILED because                       "
                        f"          there is a value equal to {ConstantsNuc.DRIVING_MODE_REQUEST_TRUE} at timestamp    "
                        f"                             {round(ap_time[idx], 3)} s.".split()
                    )
                    eval_cond[1] = False

                if ap_usecase[idx] != ConstantsNuc.USE_CASE_FALSE and eval_cond[2]:
                    evaluation3 = " ".join(
                        f"The evaluation for {signal_name['ApUsecase']} is FAILED because                              "
                        f"   there is a value that is NOT equal to {ConstantsNuc.USE_CASE_FALSE} at timestamp          "
                        f"                       {round(ap_time[idx], 3)} s.".split()
                    )
                    eval_cond[2] = False

            if all(eval_cond):
                test_result = fc.PASS
            else:
                test_result = fc.FAIL
        else:
            test_result = fc.NOT_ASSESSED
            evaluation1 = evaluation2 = evaluation3 = " ".join(
                "Evaluation not possible, the trigger value PLANNING_CONTROL_ACTIVE                    "
                f" ({ConstantsNuc.PLANNING_CONTROL_ACTIVE}) for {signal_name['ApState']} was never found.".split()
            )

        signal_summary[signal_name["ApTrajCtrlActive"]] = evaluation1
        signal_summary[signal_name["ApDrivingModeReq"]] = evaluation2
        signal_summary[signal_name["ApUsecase"]] = evaluation3
        remark = " ".join(
            "Check that after .planningCtrlPort.apStates == 1 (PLANNING_CONTROL_ACTIVE), driving mode request is       "
            "      not TRUE, trajectory control is NOT ACTIVE and use case is FALSE.".split()
        )
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif test_result == fc.NOT_ASSESSED:
            self.result.measured_result = DATA_NOK
        else:
            self.result.measured_result = FALSE

        if self.result.measured_result in [FALSE, DATA_NOK] or bool(GeneralConstants.ACTIVATE_PLOTS):
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=ap_time, y=ap_state, mode="lines", name=signal_name["ApState"]))
            fig.add_trace(
                go.Scatter(x=ap_time, y=ap_traj_ctrl_active, mode="lines", name=signal_name["ApTrajCtrlActive"])
            )
            fig.add_trace(
                go.Scatter(x=ap_time, y=ap_driving_mode_req, mode="lines", name=signal_name["ApDrivingModeReq"])
            )
            fig.add_trace(go.Scatter(x=ap_time, y=ap_usecase, mode="lines", name=signal_name["ApUsecase"]))
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        T9 = ap_time[0]  # start of measurement
        T11 = ap_time[-1]  # end of measurement

        if T9 is not None and T11 is not None:
            sim_time = round(max(ap_time), 3)
            max_ap_state = max(ap_state)
            max_strokes = max(ap_nr_strokes)
            max_visu_screen = max(head_unit_screen)
        else:
            sim_time = "n.a"
            max_ap_state = "n.a"
            max_strokes = "n.a"
            max_visu_screen = "n.a"

        color = fh.get_color(test_result)
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": color},
            "SimulationTime[s]": {"value": sim_time, "color": fh.apply_color(sim_time, 0, ">")},
            "apStates": {"value": max_ap_state, "color": fh.apply_color(max_ap_state, 5, "<")},
            "Nr_Of_Strokes": {"value": max_strokes, "color": fh.apply_color(max_strokes, 11, "<", 1, ">=<=")},
            "AP_VISU_screen": {"value": max_visu_screen, "color": fh.apply_color(max_visu_screen, 5, "<")},
        }

        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="MF NUC",
    description=(
        "Check that after Planning control port is equal to 1(PLANNING_CONTROL_ACTIVE), driving mode request is not"
        " TRUE, trajectory control is NOT ACTIVE and use case is FALSE."
    ),
)
class FtParkingNUC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [TestStepFtParkingNUC]
