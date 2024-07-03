"""LSCA functional test"""

import logging

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
import plotly.graph_objects as go
from tsf.core.results import FALSE, TRUE, BooleanResult
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
from pl_parking.PLP.MF.constants import ConstantsLSCA, GeneralConstants, PlotlyTemplate

SIGNAL_DATA = "MF_LSCA"

example_obj = MfSignals()


class StoreStepResult:
    """Initializes variables for multiple steps and provides a method
    to check their status and return corresponding results and color codes.
    """

    def __init__(self):
        """Initialize the test steps results"""
        self.step_1 = fc.INPUT_MISSING
        self.step_2 = fc.INPUT_MISSING
        self.step_3 = fc.INPUT_MISSING

    def check_result(self):
        """
        The function `check_result` checks the status of multiple steps and returns a corresponding result and color code.
        :return: The `check_result` method is returning a tuple with two values. The first value is one of the constants
        `fc.PASS`, `fc.INPUT_MISSING`, `fc.NOT_ASSESSED`, or `fc.FAIL` based on the conditions checked in the method. The
        second value is a color code represented as a string.
        """
        if self.step_1 == fc.PASS or self.step_2 == fc.PASS or self.step_3 == fc.PASS:
            # self.case_result == fc.PASS
            return fc.PASS, "#28a745"
        elif self.step_1 == fc.INPUT_MISSING or self.step_2 == fc.INPUT_MISSING or self.step_3 == fc.INPUT_MISSING:
            # self.case_result == fc.INPUT_MISSING
            return fc.INPUT_MISSING, "rgb(33,39,43)"
        else:
            # self.case_result == fc.FAIL
            return fc.FAIL, "#dc3545"


final_result = StoreStepResult()


@teststep_definition(
    step_number=1,
    name="LSCA 1",
    description=(
        "Check the following conditions:                 ('AP.lscaDisabled_nu' == 1                 AND"
        " 'Sensor.Collision.Vhcl.Fr1.Count' == 1 once                 AND 'LSCA.statusPort.brakingModuleState_nu' == 0 "
        "                AND 'LSCA.brakePort.requestMode' == 0)                 OR TestCase 2 OR TestCase 3"
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TestStepFtLSCA1(TestStep):
    """Test step class"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize test step"""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        read_data = self.readers[SIGNAL_DATA].signals

        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        signal_name = example_obj._properties

        read_data["ApUsecase"].tolist()
        ap_lsca_disabled = read_data["lscaDisabled"].tolist()
        lsca_request_mode = read_data["lscaRequestMode"].tolist()
        lsca_braking_module_state = read_data["brakeModeState"].tolist()
        ap_time = read_data["time"].tolist()
        read_data["Car_v"].tolist()
        sensor_collision_count = read_data["CollisionCount"].tolist()

        self.test_result: str = fc.INPUT_MISSING
        self.sig_sum = None
        self.fig = None

        t2 = 0
        signal_summary = {}
        evaluation_lsca_disabled_1 = " ".join(
            "The condition is PASSED, the value of                                        "
            f" {signal_name['lscaDisabled']} is 1 all the time.".split()
        )
        evaluation_collision_count = " ".join(
            "The condition is PASSED,the signal                                        "
            f" {signal_name['CollisionCount']} has the value 1 minimum once.".split()
        )
        evaluation_brake_mode_state = " ".join(
            "The condition is PASSED, the value of                                        "
            f" {signal_name['brakeModeState']} is 0.".split()
        )
        evaluation_lsca_request_mode = " ".join(
            "The condition is PASSED, the value of                                        "
            f" {signal_name['lscaRequestMode']} is 0.".split()
        )

        """ignore the first samples, because they might not be relevant"""
        for idx, val in enumerate(ap_time):
            if val > 0:
                t2 = idx
                break

        if t2 is not None:
            eval_cond = [True] * 4
            for idx in range(t2, len(ap_time)):

                if ap_lsca_disabled[idx] != 1 and eval_cond[0]:
                    evaluation_lsca_disabled_1 = " ".join(
                        "The condition is FAILED, the value of                                                        "
                        f"     {signal_name['lscaDisabled']} is != 1 at                                                "
                        f"             timestamp {round(ap_time[idx],3)} s.".split()
                    )
                    eval_cond[0] = False

                if 1 not in sensor_collision_count and eval_cond[1]:
                    evaluation_collision_count = " ".join(
                        "The condition is FAILED, the value of                                                        "
                        f"     {signal_name['CollisionCount']} is !=1, first                                           "
                        f"                  point at {round(ap_time[idx], 3)} s.".split()
                    )
                    eval_cond[1] = False

                if lsca_braking_module_state[idx] != 0 and eval_cond[2]:
                    evaluation_brake_mode_state = " ".join(
                        "The condition is FAILED, the value of                                                        "
                        f" {signal_name['brakeModeState']} is  != 0 at                                                 "
                        f"        timestamp {round(ap_time[idx], 3)} s.".split()
                    )
                    eval_cond[2] = False

                if lsca_request_mode[idx] != 0 and eval_cond[3]:
                    evaluation_lsca_request_mode = " ".join(
                        "The condition is FAILED, the value of                                                        "
                        f"     {signal_name['lscaRequestMode']} is  != 0 at                                            "
                        f"                 timestamp {round(ap_time[idx], 3)} s.".split()
                    )
                    eval_cond[3] = False

        if all(eval_cond):
            self.result.measured_result = TRUE
            self.test_result = fc.PASS
            final_result.step_1 = fc.PASS
        else:
            self.test_result = fc.FAIL
            self.result.measured_result = FALSE
            final_result.step_1 = fc.FAIL

        signal_summary[signal_name["lscaDisabled"]] = evaluation_lsca_disabled_1
        signal_summary[signal_name["CollisionCount"]] = evaluation_collision_count
        signal_summary[signal_name["brakeModeState"]] = evaluation_brake_mode_state
        signal_summary[signal_name["lscaRequestMode"]] = evaluation_lsca_request_mode

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.test_result == fc.FAIL or bool(GeneralConstants.ACTIVATE_PLOTS):
            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(x=ap_time, y=sensor_collision_count, mode="lines", name=signal_name["CollisionCount"])
            )
            self.fig.add_trace(
                go.Scatter(x=ap_time, y=ap_lsca_disabled, mode="lines", name=signal_name["lscaDisabled"])
            )
            self.fig.add_trace(
                go.Scatter(x=ap_time, y=lsca_request_mode, mode="lines", name=signal_name["lscaRequestMode"])
            )
            self.fig.add_trace(
                go.Scatter(x=ap_time, y=lsca_braking_module_state, mode="lines", name=signal_name["brakeModeState"])
            )

            self.fig.layout = go.Layout(
                autosize=True, yaxis=dict(tickformat="5"), xaxis=dict(tickformat="5"), xaxis_title="Time[s]"
            )
            self.fig.update_layout(PlotlyTemplate.lgt_tmplt)
        if self.fig:
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


@teststep_definition(
    step_number=2,
    name="LSCA 2",
    description=(
        "Check the following conditions:                 ('AP.lscaDisabled_nu' == 1                 AND"
        " 'Sensor.Collision.Vhcl.Fr1.Count' == 1 once                 AND 'LSCA.statusPort.brakingModuleState_nu' == 0 "
        "                AND 'LSCA.brakePort.requestMode' == 0)                 OR TestCase 2 OR TestCase 3"
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TestStepFtLSCA2(TestStep):
    """Test step class"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        read_data = self.readers[SIGNAL_DATA].signals

        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        signal_name = example_obj._properties

        ap_usecase = read_data["ApUsecase"].tolist()
        read_data["lscaDisabled"].tolist()
        lsca_request_mode = read_data["lscaRequestMode"].tolist()
        read_data["brakeModeState"].tolist()
        ap_time = read_data["time"].tolist()
        car_v = read_data["Car_v"].tolist()
        sensor_collision_count = read_data["CollisionCount"].tolist()
        self.test_result: str = fc.INPUT_MISSING
        self.sig_sum = None
        self.fig = None

        t2 = 0
        signal_summary = {}

        evaluation_ap_usecase = " ".join(
            "The condition is PASSED, all values for signal                                        "
            f" {signal_name['ApUsecase']} are == 0.".split()
        )
        evaluation_collision_count = " ".join(
            "The condition is PASSED,the value of                                        "
            f" {signal_name['CollisionCount']} is 1 minimum once.".split()
        )
        evaluation_lsca_request_mode = " ".join(
            "The condition is PASSED, all values for signal                                        "
            f" {signal_name['lscaRequestMode']} are 0.".split()
        )

        for idx, val in enumerate(ap_time):
            if val > 0:
                t2 = idx
                break

        if t2 is not None:
            eval_cond = [True] * 3
            for idx in range(t2, len(ap_time)):
                if not (ap_usecase[idx] == 0) and eval_cond[0]:
                    evaluation_ap_usecase = " ".join(
                        "The condition is FAILED, the value of                                                "
                        f" {signal_name['ApUsecase']} is != 0 at timestamp                                             "
                        f"    {round(ap_time[idx], 3)} s.".split()
                    )
                    eval_cond[0] = False
                if 1 not in sensor_collision_count and eval_cond[1]:
                    evaluation_collision_count = " ".join(
                        "The condition is FAILED, the value of                                                    "
                        f" {signal_name['CollisionCount']} is never 1.".split()
                    )
                    eval_cond[1] = False
                if not (lsca_request_mode[idx] == 0) and eval_cond[2]:
                    evaluation_lsca_request_mode = " ".join(
                        "The condition is FAILED, the value of                                                    "
                        f" {signal_name['lscaRequestMode']} is != 0 at                                                 "
                        f"    timestamp {round(ap_time[idx], 3)} s.".split()
                    )
                    eval_cond[2] = False
        if all(eval_cond):
            self.result.measured_result = TRUE
            self.test_result = fc.PASS
            final_result.step_2 = fc.PASS
        else:
            self.test_result = fc.FAIL
            self.result.measured_result = FALSE
            final_result.step_2 = fc.FAIL

        signal_summary[signal_name["ApUsecase"]] = evaluation_ap_usecase
        signal_summary[signal_name["CollisionCount"]] = evaluation_collision_count
        signal_summary[signal_name["lscaRequestMode"]] = evaluation_lsca_request_mode

        self.sig_sum = go.Figure(
            data=[
                go.Table(
                    columnwidth=[3, 5],
                    header=dict(
                        values=["Signal Evaluation", "Summary"],
                        fill_color="rgb(255,165,0)",
                        font=dict(size=12, family="Arial", color="rgb(0,0,0)"),
                        align="center",
                    ),
                    cells=dict(
                        values=[list(signal_summary.keys()), list(signal_summary.values())],
                        height=42,
                        align="center",
                        font=dict(size=12),
                    ),
                )
            ]
        )
        self.sig_sum.update_layout(height=fh.calc_table_height(signal_summary))
        self.sig_sum.update_layout(PlotlyTemplate.lgt_tmplt)

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("TestCase 2")

        if self.test_result == fc.FAIL or bool(GeneralConstants.ACTIVATE_PLOTS):
            self.fig = go.Figure()
            self.fig.add_trace(go.Scatter(x=ap_time, y=car_v, mode="lines", name=signal_name["Car_v"]))
            self.fig.add_trace(
                go.Scatter(x=ap_time, y=sensor_collision_count, mode="lines", name=signal_name["CollisionCount"])
            )

            self.fig.layout = go.Layout(yaxis=dict(tickformat="20"), xaxis=dict(tickformat="20"), xaxis_title="Time[s]")
            self.fig.update_layout(PlotlyTemplate.lgt_tmplt)
        if self.fig:
            plot_titles.append("Graphical Overview")
            plots.append(self.fig)
            remarks.append("Test Graphics evaluation CarMaker")
        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=3,
    name="LSCA 3",
    description=(
        "Check the following conditions:                 ('AP.lscaDisabled_nu has' == 0                 AND"
        " 'Sensor.Collision.Vhcl.Fr1.Count' == 0                 AND 'LSCA.brakePort.requestMode' == 2 once            "
        "     AND 'LSCA.statusPort.brakingModuleState_nu' == 2)                 OR TestCase 1 OR TestCase 2."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TestStepFtLSCA3(TestStep):
    """Test step class"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        read_data = self.readers[SIGNAL_DATA].signals

        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        signal_name = example_obj._properties

        read_data["ApUsecase"].tolist()
        ap_lsca_disabled = read_data["lscaDisabled"].tolist()
        read_data["lscaRequestMode"].tolist()
        lsca_braking_module_state = read_data["brakeModeState"].tolist()
        ap_time = read_data["time"].tolist()
        read_data["Car_v"].tolist()
        sensor_collision_count = read_data["CollisionCount"].tolist()
        self.test_result: str = fc.INPUT_MISSING
        self.sig_sum = None
        self.fig = None

        t2 = 0
        signal_summary = {}

        evaluation_lsca_disabled_0 = " ".join(
            "The condition is PASSED, the value of                                        "
            f" {signal_name['lscaDisabled']} is = 0.".split()
        )
        evaluation_collision_count_1 = " ".join(
            "The condition is PASSED,all the value of                                            "
            f" {signal_name['CollisionCount']} is = 0.".split()
        )
        evaluation_brake_mode_state_2 = " ".join(
            "The condition is PASSED, the value of                                            "
            f" {signal_name['brakeModeState']} is equale with 2                                             minimum"
            " once.".split()
        )
        evaluation_lsca_request_mode_2 = " ".join(
            "The condition is PASSED, the value of                                            "
            f" {signal_name['lscaRequestMode']}is equale with 2                                             minimum"
            " once.".split()
        )

        for idx, val in enumerate(ap_time):
            if val > 0:
                t2 = idx
                break

        if t2 is not None:
            eval_cond = [True] * 4
            for idx in range(t2, len(ap_time)):

                if ap_lsca_disabled[idx] != 0 and eval_cond[0]:
                    evaluation_lsca_disabled_0 = " ".join(
                        "The condition is FAILED, the value of                                                    "
                        f" {signal_name['lscaDisabled']} is != 0 at                                                    "
                        f" timestamp {round(ap_time[idx], 3)} s.".split()
                    )
                    eval_cond[0] = False
                if sensor_collision_count[idx] != 0 and eval_cond[1]:
                    evaluation_collision_count_1 = " ".join(
                        "The condition is FAILED, the value of                                                        "
                        f" {signal_name['CollisionCount']} is != 0 at                                                  "
                        f"      timestamp {round(ap_time[idx], 3)} s.".split()
                    )
                    eval_cond[1] = False
                if ConstantsLSCA.VAL_LSCA not in lsca_braking_module_state[t2:] and eval_cond[2]:
                    evaluation_brake_mode_state_2 = " ".join(
                        "The condition is FAILED, the value of                                                        "
                        f" {signal_name['brakeModeState']} =                                                        "
                        f" {ConstantsLSCA.VAL_LSCA} was never found.".split()
                    )
                    eval_cond[2] = False
                if ConstantsLSCA.VAL_LSCA not in lsca_braking_module_state[t2:] and eval_cond[3]:
                    evaluation_lsca_request_mode_2 = " ".join(
                        "The condition is FAILED, the value of                                                        "
                        f"     {signal_name['lscaRequestMode']} =                                                      "
                        f"       {ConstantsLSCA.VAL_LSCA} was never found.".split()
                    )
                    eval_cond[3] = False

        if all(eval_cond):
            self.result.measured_result = TRUE
            self.test_result = fc.PASS
            final_result.step_3 = fc.PASS
        else:
            self.test_result = fc.FAIL
            self.result.measured_result = FALSE
            final_result.step_3 = fc.FAIL

        signal_summary[f" {signal_name['lscaDisabled']}"] = evaluation_lsca_disabled_0
        signal_summary[f" {signal_name['CollisionCount']}"] = evaluation_collision_count_1
        signal_summary[f" {signal_name['brakeModeState']}"] = evaluation_brake_mode_state_2
        signal_summary[f" {signal_name['lscaRequestMode']}"] = evaluation_lsca_request_mode_2

        self.sig_sum = go.Figure(
            data=[
                go.Table(
                    columnwidth=[3, 5],
                    header=dict(
                        values=["Signal Evaluation", "Summary"],
                        fill_color="rgb(255,165,0)",
                        font=dict(size=12, family="Arial", color="rgb(0,0,0)"),
                        align="center",
                    ),
                    cells=dict(
                        values=[list(signal_summary.keys()), list(signal_summary.values())],
                        height=42,
                        align="center",
                        font=dict(size=12),
                    ),
                )
            ]
        )
        self.sig_sum.update_layout(height=fh.calc_table_height(signal_summary))
        self.sig_sum.update_layout(PlotlyTemplate.lgt_tmplt)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("TestCase 3")
        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        verdict, color = final_result.check_result()

        # result_df = pd.DataFrame(
        #     {fc.REQ_ID: [['1', '2', '3'][i] for i in range(0, 3)],
        #      fc.TESTCASE_ID: [['1', '2', '3'][i] for i in range(0, 3)],
        #      fc.TEST_SAFETY_RELEVANT: ["input missing" for _ in range(0, 3)],
        #      fc.TEST_DESCRIPTION: [["Check the following conditions:                 ('AP.lscaDisabled_nu' == 1                 AND 'Sensor.Collision.Vhcl.Fr1.Count' == 1 once                 AND 'LSCA.statusPort.brakingModuleState_nu' == 0                 AND 'LSCA.brakePort.requestMode' == 0)                 OR TestCase 2 OR TestCase 3", "Check the following conditions:                 ('AP.evaluationPort.useCase_nu' == 0                 AND 'Sensor.Collision.Vhcl.Fr1.Count' == 1 once                 AND 'LSCA.brakePort.requestMode' == 0)                 OR TestCase 1 OR TestCase 3.", "Check the following conditions:                 ('AP.lscaDisabled_nu has' == 0                 AND 'Sensor.Collision.Vhcl.Fr1.Count' == 0                 AND 'LSCA.brakePort.requestMode' == 2 once                 AND 'LSCA.statusPort.brakingModuleState_nu' == 2)                 OR TestCase 1 OR TestCase 2."][i] for i in range(0, 3)],
        #      fc.TEST_RESULT: [lsca_1.test_result, lsca_2.test_result, lsca_3.test_result]})

        max_collision = max(sensor_collision_count)
        additional_results_dict = {
            "Verdict": {"value": verdict.title(), "color": color},
            "max Collisions": {"value": max_collision, "color": "rgb(33,39,43)"},
        }

        # if final_result == fc.PASS:
        #     self.result.measured_result = TRUE
        # else:
        #     self.result.measured_result = FALSE

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="MF LSCA",
    description="Check that at least one of test steps is true.",
)
class FtLSCA(TestCase):
    """Test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [TestStepFtLSCA1, TestStepFtLSCA2, TestStepFtLSCA3]
