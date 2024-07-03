"""Functional test for runtime"""

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
from pl_parking.PLP.MF.constants import RtaEvents, RunTimeId
from pl_parking.PLP.MF.ft_helper import ExampleSignals

SIGNAL_DATA = "MF_RUN_TIMES"

example_obj = EntrySignals()


class EventData:
    """In this function the devine variables for event data."""

    def __init__(self) -> None:
        """Initialize object attributes."""
        self.real_time_us = 0
        self.event_type = 0
        self.local_id = -1
        self.global_id = -1


@teststep_definition(
    step_number=1,
    name="RUN TIMES",
    description=(
        "Maximum run time for TCE Average run time for TCE Maximum run time for VEDODO Average run time for VEDODO"
        " Maximum run time for US_DRV Average run time for US_DRV Maximum run time for TRJCTL Average run time for"
        " TRJCTL Maximum run time for US_PROCESSING Average run time for US_PROCESSING Maximum run time for US_EM"
        " Average run time for US_EM Maximum run time for US_PSI Average run time for US_PSI Maximum run time for"
        " APPDEMO_PARKSM Average run time for APPDEMO_PARKSM Maximum run time for MF_PARKSM_CORE Average run time for"
        " MF_PARKSM_CORE Maximum run time for MF_TRJPLA Average run time for MF_TRJPLA Maximum run time for MF_LSCA"
        " Average run time for MF_LSCA Maximum run time for MF_MANAGER Average run time for MF_MANAGER Maximum run time"
        " for MF_PDW Average run time for MF_PDW Maximum run time for APPDEMO_DRV Average run time for APPDEMO_DRV"
        " Maximum run time for MF_DRV Average run time for MF_DRV Maximum run time for APPDEMO_TONH Average run time"
        " for APPDEMO_TONH Maximum run time for APPDEMO_HMIH Average run time for APPDEMO_HMIH"
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ExampleSignals)
class TestStepFtParkingCalculateRuntimes(TestStep):
    """Test step class"""

    custom_report = MfCustomTeststepReport
    m_max_net_task = {}
    m_avg_net_task = {}

    def __init__(self):
        """Initialize test step"""
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
        result_final = fc.INPUT_MISSING
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = rep([], 3)

        self.m_rta_data = []
        self.idx_tce = []
        self.ev_cont_real_time = []
        self.ev_cont_local_id = []
        self.ev_cont_event_type = []
        self.ev_cont_global_id = []
        signal_name = example_obj._properties
        eval_cond = [fc.INPUT_MISSING] * 34

        sg_ref_ts_us = "RtaRefTsUs"
        sg_max_event_idx = "RtaMaxEventIndex"
        sg_time = "TimeStamp"

        def parse_measurement_rta_data(ref_ts_us, max_event_idx):
            self.m_rta_data = []
            for idx, time_ref in ref_ts_us.items():
                for i in range(max_event_idx[idx]):
                    obj_ev_data = EventData()
                    obj_ev_data.real_time_us = self.ev_cont_real_time[i][idx] + time_ref
                    obj_ev_data.local_id = self.ev_cont_local_id[i][idx]
                    obj_ev_data.event_type = self.ev_cont_event_type[i][idx]
                    obj_ev_data.global_id = self.ev_cont_global_id[i][idx]
                    self.m_rta_data.append(obj_ev_data)

        def analyze_mesurements():
            """MaxNetTask in cpp profilinganalysis.cpp this is an example for TCE"""
            # std::stable_sort applied line
            self.m_rta_data.sort(key=lambda x: x.real_time_us)

            last_event = self.m_rta_data[0].real_time_us
            m_x_min = -1 if last_event > 0 else 0
            m_x_max = self.m_rta_data[-1].real_time_us + 1

            start_event = {
                RunTimeId.US_CORRELATOR: m_x_min + 1,
                RunTimeId.VEDODO: m_x_min + 1,
                RunTimeId.TRJCTL: m_x_min + 1,
                RunTimeId.TCE: m_x_min + 1,
                RunTimeId.US_DRV: m_x_min + 1,
                RunTimeId.US_PROCESSING: m_x_min + 1,
                RunTimeId.US_EM: m_x_min + 1,
                RunTimeId.US_PSI: m_x_min + 1,
                RunTimeId.APPDEMO_PARKSM: m_x_min + 1,
                RunTimeId.MF_PARKSM_CORE: m_x_min + 1,
                RunTimeId.MF_TRJPLA: m_x_min + 1,
                RunTimeId.MF_LSCA: m_x_min + 1,
                RunTimeId.MF_MANAGER: m_x_min + 1,
                RunTimeId.MF_PDW: m_x_min + 1,
                RunTimeId.MF_DRV: m_x_min + 1,
                RunTimeId.APPDEMO_HMIH: m_x_min + 1,
                RunTimeId.APPDEMO_DRV: m_x_min + 1,
                RunTimeId.APPDEMO_TONH: m_x_min + 1,
                RunTimeId.US_DRV_SPI: m_x_min + 1,
                RunTimeId.RTARUN: m_x_min + 1,
                RunTimeId.CFG_MGR: m_x_min + 1,
                RunTimeId.VEHICLE_SIGNALS: m_x_min + 1,
                RunTimeId.MEASFREEZE_CAN: m_x_min + 1,
                RunTimeId.VEHICLE_SIGNALS_EM: m_x_min + 1,
                RunTimeId.MEASFREEZE_EM: m_x_min + 1,
                RunTimeId.MF_WHLPROTECT: m_x_min + 1,
            }

            sum_net_events = {
                RunTimeId.US_CORRELATOR: 0,
                RunTimeId.VEDODO: 0,
                RunTimeId.TRJCTL: 0,
                RunTimeId.TCE: 0,
                RunTimeId.US_DRV: 0,
                RunTimeId.US_PROCESSING: 0,
                RunTimeId.US_EM: 0,
                RunTimeId.US_PSI: 0,
                RunTimeId.APPDEMO_PARKSM: 0,
                RunTimeId.MF_PARKSM_CORE: 0,
                RunTimeId.MF_TRJPLA: 0,
                RunTimeId.MF_LSCA: 0,
                RunTimeId.MF_MANAGER: 0,
                RunTimeId.MF_PDW: 0,
                RunTimeId.MF_DRV: 0,
                RunTimeId.APPDEMO_HMIH: 0,
                RunTimeId.APPDEMO_DRV: 0,
                RunTimeId.APPDEMO_TONH: 0,
                RunTimeId.US_DRV_SPI: 0,
                RunTimeId.RTARUN: 0,
                RunTimeId.CFG_MGR: 0,
                RunTimeId.VEHICLE_SIGNALS: 0,
                RunTimeId.MEASFREEZE_CAN: 0,
                RunTimeId.VEHICLE_SIGNALS_EM: 0,
                RunTimeId.MEASFREEZE_EM: 0,
                RunTimeId.MF_WHLPROTECT: 0,
            }

            accumulative_net = {
                RunTimeId.US_CORRELATOR: 0,
                RunTimeId.VEDODO: 0,
                RunTimeId.TRJCTL: 0,
                RunTimeId.TCE: 0,
                RunTimeId.US_DRV: 0,
                RunTimeId.US_PROCESSING: 0,
                RunTimeId.US_EM: 0,
                RunTimeId.US_PSI: 0,
                RunTimeId.APPDEMO_PARKSM: 0,
                RunTimeId.MF_PARKSM_CORE: 0,
                RunTimeId.MF_TRJPLA: 0,
                RunTimeId.MF_LSCA: 0,
                RunTimeId.MF_MANAGER: 0,
                RunTimeId.MF_PDW: 0,
                RunTimeId.MF_DRV: 0,
                RunTimeId.APPDEMO_HMIH: 0,
                RunTimeId.APPDEMO_DRV: 0,
                RunTimeId.APPDEMO_TONH: 0,
                RunTimeId.US_DRV_SPI: 0,
                RunTimeId.RTARUN: 0,
                RunTimeId.CFG_MGR: 0,
                RunTimeId.VEHICLE_SIGNALS: 0,
                RunTimeId.MEASFREEZE_CAN: 0,
                RunTimeId.VEHICLE_SIGNALS_EM: 0,
                RunTimeId.MEASFREEZE_EM: 0,
                RunTimeId.MF_WHLPROTECT: 0,
            }

            self.m_max_net_task = {
                RunTimeId.US_CORRELATOR: 0,
                RunTimeId.VEDODO: 0,
                RunTimeId.TRJCTL: 0,
                RunTimeId.TCE: 0,
                RunTimeId.US_DRV: 0,
                RunTimeId.US_PROCESSING: 0,
                RunTimeId.US_EM: 0,
                RunTimeId.US_PSI: 0,
                RunTimeId.APPDEMO_PARKSM: 0,
                RunTimeId.MF_PARKSM_CORE: 0,
                RunTimeId.MF_TRJPLA: 0,
                RunTimeId.MF_LSCA: 0,
                RunTimeId.MF_MANAGER: 0,
                RunTimeId.MF_PDW: 0,
                RunTimeId.MF_DRV: 0,
                RunTimeId.APPDEMO_HMIH: 0,
                RunTimeId.APPDEMO_DRV: 0,
                RunTimeId.APPDEMO_TONH: 0,
                RunTimeId.US_DRV_SPI: 0,
                RunTimeId.RTARUN: 0,
                RunTimeId.CFG_MGR: 0,
                RunTimeId.VEHICLE_SIGNALS: 0,
                RunTimeId.MEASFREEZE_CAN: 0,
                RunTimeId.VEHICLE_SIGNALS_EM: 0,
                RunTimeId.MEASFREEZE_EM: 0,
                RunTimeId.MF_WHLPROTECT: 0,
            }

            m_y = {
                RunTimeId.US_CORRELATOR: [],
                RunTimeId.VEDODO: [],
                RunTimeId.TRJCTL: [],
                RunTimeId.TCE: [],
                RunTimeId.US_DRV: [],
                RunTimeId.US_PROCESSING: [],
                RunTimeId.US_EM: [],
                RunTimeId.US_PSI: [],
                RunTimeId.APPDEMO_PARKSM: [],
                RunTimeId.MF_PARKSM_CORE: [],
                RunTimeId.MF_TRJPLA: [],
                RunTimeId.MF_LSCA: [],
                RunTimeId.MF_MANAGER: [],
                RunTimeId.MF_PDW: [],
                RunTimeId.MF_DRV: [],
                RunTimeId.APPDEMO_HMIH: [],
                RunTimeId.APPDEMO_DRV: [],
                RunTimeId.APPDEMO_TONH: [],
                RunTimeId.US_DRV_SPI: [],
                RunTimeId.RTARUN: [],
                RunTimeId.CFG_MGR: [],
                RunTimeId.VEHICLE_SIGNALS: [],
                RunTimeId.MEASFREEZE_CAN: [],
                RunTimeId.VEHICLE_SIGNALS_EM: [],
                RunTimeId.MEASFREEZE_EM: [],
                RunTimeId.MF_WHLPROTECT: [],
            }

            self.m_avg_net_task = {
                RunTimeId.US_CORRELATOR: 0,
                RunTimeId.VEDODO: 0,
                RunTimeId.TRJCTL: 0,
                RunTimeId.TCE: 0,
                RunTimeId.US_DRV: 0,
                RunTimeId.US_PROCESSING: 0,
                RunTimeId.US_EM: 0,
                RunTimeId.US_PSI: 0,
                RunTimeId.APPDEMO_PARKSM: 0,
                RunTimeId.MF_PARKSM_CORE: 0,
                RunTimeId.MF_TRJPLA: 0,
                RunTimeId.MF_LSCA: 0,
                RunTimeId.MF_MANAGER: 0,
                RunTimeId.MF_PDW: 0,
                RunTimeId.MF_DRV: 0,
                RunTimeId.APPDEMO_HMIH: 0,
                RunTimeId.APPDEMO_DRV: 0,
                RunTimeId.APPDEMO_TONH: 0,
                RunTimeId.US_DRV_SPI: 0,
                RunTimeId.RTARUN: 0,
                RunTimeId.CFG_MGR: 0,
                RunTimeId.VEHICLE_SIGNALS: 0,
                RunTimeId.MEASFREEZE_CAN: 0,
                RunTimeId.VEHICLE_SIGNALS_EM: 0,
                RunTimeId.MEASFREEZE_EM: 0,
                RunTimeId.MF_WHLPROTECT: 0,
            }

            current_task = constants.SignalsNumber.CURRENT_TASK_START
            stack = []

            for i, _ in enumerate(self.m_rta_data):
                local_id = self.m_rta_data[i].local_id

                if self.m_rta_data[i].event_type == RtaEvents.RTA_EVT_ALGOSTART:
                    start_event[local_id] = self.m_rta_data[i].real_time_us
                    stack.append([local_id, current_task, self.m_rta_data[i].real_time_us])
                    last_event = self.m_rta_data[i].real_time_us

                elif self.m_rta_data[i].event_type == RtaEvents.RTA_EVT_ALGOEND:
                    for j, val in enumerate(stack):
                        if val[0] == local_id:
                            stack.pop(j)
                            break
                    elapsed_time = self.m_rta_data[i].real_time_us - start_event[local_id]
                    accumulative_net[local_id] += self.m_rta_data[i].real_time_us - last_event
                    sum_net_events[local_id] += accumulative_net[local_id]
                    if accumulative_net[local_id] > self.m_max_net_task[local_id]:
                        self.m_max_net_task[local_id] = accumulative_net[local_id]

                    accumulative_net[local_id] = 0
                    m_y[local_id].append(elapsed_time)
                    if self.m_rta_data[i].real_time_us > m_x_max:
                        m_x_max = self.m_rta_data[i].real_time_us
                    last_event = self.m_rta_data[i].real_time_us

                elif self.m_rta_data[i].event_type == RtaEvents.RTA_EVT_TASKSWITCH:
                    for stack_val in reversed(stack):
                        if stack_val[1] == current_task:
                            accumulative_net[stack_val[0]] += self.m_rta_data[i].real_time_us - last_event
                            stack_val[2] = self.m_rta_data[i].real_time_us
                    current_task = self.m_rta_data[i].global_id
                    last_event = self.m_rta_data[i].real_time_us

            for val in stack:
                local_id = val[0]
                elapsed_time = (m_x_max - 1) - start_event[local_id]
                accumulative_net[local_id] += (m_x_max - 1) - last_event
                sum_net_events[local_id] += accumulative_net[local_id]
                if accumulative_net[local_id] > self.m_max_net_task[local_id]:
                    self.m_max_net_task[local_id] = accumulative_net[local_id]
                accumulative_net[local_id] = 0
                m_y[local_id].append(elapsed_time)

            val_enum = set(item.value for item in RunTimeId)

            for id in val_enum:
                if len(m_y[id]) > 0:
                    self.m_avg_net_task[id] = np.floor(sum_net_events[id] / len(m_y[id]))

        try:
            for i in range(constants.SignalsNumber.RTA_EV_CONT_NUMBER):
                try:
                    self.ev_cont_real_time.append(df[("u_RelTime_us", i)])
                    self.ev_cont_local_id.append(df[("u_LocalId", i)])
                    self.ev_cont_event_type.append(df[("u_EventType", i)])
                    self.ev_cont_global_id.append(df[("u_GlobalId", i)])
                except KeyError as e:
                    print(e)

            ref_ts_us = df[sg_ref_ts_us]
            max_event_idx = df[sg_max_event_idx]

            # Converting microseconds to seconds
            df[sg_time] = df[sg_time] / constants.GeneralConstants.US_IN_S
            # Converting epoch time to seconds passed
            df[sg_time] = df[sg_time] - df[sg_time].iat[0]

            if not self.m_max_net_task:
                parse_measurement_rta_data(ref_ts_us, max_event_idx)
                analyze_mesurements()

            eval_res = [
                self.m_max_net_task[RunTimeId.TCE],
                self.m_avg_net_task[RunTimeId.TCE],
                self.m_max_net_task[RunTimeId.VEDODO],
                self.m_avg_net_task[RunTimeId.VEDODO],
                self.m_max_net_task[RunTimeId.US_DRV],
                self.m_avg_net_task[RunTimeId.US_DRV],
                self.m_max_net_task[RunTimeId.TRJCTL],
                self.m_avg_net_task[RunTimeId.TRJCTL],
                self.m_max_net_task[RunTimeId.US_PROCESSING],
                self.m_avg_net_task[RunTimeId.US_PROCESSING],
                self.m_max_net_task[RunTimeId.US_EM],
                self.m_avg_net_task[RunTimeId.US_EM],
                self.m_max_net_task[RunTimeId.US_PSI],
                self.m_avg_net_task[RunTimeId.US_PSI],
                self.m_max_net_task[RunTimeId.APPDEMO_PARKSM],
                self.m_avg_net_task[RunTimeId.APPDEMO_PARKSM],
                self.m_max_net_task[RunTimeId.MF_PARKSM_CORE],
                self.m_avg_net_task[RunTimeId.MF_PARKSM_CORE],
                self.m_max_net_task[RunTimeId.MF_TRJPLA],
                self.m_avg_net_task[RunTimeId.MF_TRJPLA],
                self.m_max_net_task[RunTimeId.MF_LSCA],
                self.m_avg_net_task[RunTimeId.MF_LSCA],
                self.m_max_net_task[RunTimeId.MF_MANAGER],
                self.m_avg_net_task[RunTimeId.MF_MANAGER],
                self.m_max_net_task[RunTimeId.MF_PDW],
                self.m_avg_net_task[RunTimeId.MF_PDW],
                self.m_max_net_task[RunTimeId.APPDEMO_DRV],
                self.m_avg_net_task[RunTimeId.APPDEMO_DRV],
                self.m_max_net_task[RunTimeId.MF_DRV],
                self.m_avg_net_task[RunTimeId.MF_DRV],
                self.m_max_net_task[RunTimeId.APPDEMO_TONH],
                self.m_avg_net_task[RunTimeId.APPDEMO_TONH],
                self.m_max_net_task[RunTimeId.APPDEMO_HMIH],
                self.m_avg_net_task[RunTimeId.APPDEMO_HMIH],
            ]

            for i in range(constants.SignalsNumber.RUN_TIME_STEP_NUMBERS):
                if eval_res[i] >= 0:
                    eval_cond[i] = fc.PASS
                else:
                    eval_res[i] = "N/A"
                    eval_cond[i] = fc.NOT_ASSESSED

            # Set table dataframe
            signal_summary = pd.DataFrame(
                {
                    "Condition": {
                        x: (
                            f"{['Maximum run time for TCE', 'Average run time for TCE', 'Maximum run time for VEDODO', 'Average run time for VEDODO', 'Maximum run time for US_DRV', 'Average run time for US_DRV', 'Maximum run time for TRJCTL', 'Average run time for TRJCTL', 'Maximum run time for US_PROCESSING', 'Average run time for US_PROCESSING', 'Maximum run time for US_EM', 'Average run time for US_EM', 'Maximum run time for US_PSI', 'Average run time for US_PSI', 'Maximum run time for APPDEMO_PARKSM', 'Average run time for APPDEMO_PARKSM', 'Maximum run time for MF_PARKSM_CORE', 'Average run time for MF_PARKSM_CORE', 'Maximum run time for MF_TRJPLA', 'Average run time for MF_TRJPLA', 'Maximum run time for MF_LSCA', 'Average run time for MF_LSCA', 'Maximum run time for MF_MANAGER', 'Average run time for MF_MANAGER', 'Maximum run time for MF_PDW', 'Average run time for MF_PDW', 'Maximum run time for APPDEMO_DRV', 'Average run time for APPDEMO_DRV', 'Maximum run time for MF_DRV', 'Average run time for MF_DRV', 'Maximum run time for APPDEMO_TONH', 'Average run time for APPDEMO_TONH', 'Maximum run time for APPDEMO_HMIH', 'Average run time for APPDEMO_HMIH'][x]} should"
                            " be >= 0."
                        )
                        for x in range(constants.SignalsNumber.RUN_TIME_STEP_NUMBERS)
                    },
                    "Result [us]": {x: eval_res[x] for x in range(constants.SignalsNumber.RUN_TIME_STEP_NUMBERS)},
                    "Verdict": {x: eval_cond[x].upper() for x in range(constants.SignalsNumber.RUN_TIME_STEP_NUMBERS)},
                }
            )

            self.sig_sum = go.Figure(
                data=[
                    go.Table(
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

            self.sig_sum.update_layout(
                constants.PlotlyTemplate.lgt_tmplt, height=fh.calc_table_height(signal_summary["Condition"].to_dict())
            )

            plot_titles.append("Condition Evaluation")
            plots.append(self.sig_sum)
            remarks.append("")
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=df[sg_time].tolist(),
                    y=df[sg_ref_ts_us].values.tolist(),
                    mode="lines",
                    name=signal_name[sg_ref_ts_us],
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=df[sg_time].tolist(),
                    y=df[sg_max_event_idx].values.tolist(),
                    mode="lines",
                    name=signal_name[sg_max_event_idx],
                )
            )

            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plot_titles.append("Graphical Overview")
            plots.append(fig)
            remarks.append("")
            if any(eval_cond):
                result_final = fc.PASS

            additional_results_dict = {}
            additional_results_dict["Verdict"] = ({"value": result_final.title(), "color": fh.get_color(result_final)},)
            for i in range(constants.SignalsNumber.RUN_TIME_STEP_NUMBERS):
                additional_results_dict[f"Run time computing-{i}"] = {
                    "value": [
                        "Maximum run time for TCE",
                        "Average run time for TCE",
                        "Maximum run time for VEDODO",
                        "Average run time for VEDODO",
                        "Maximum run time for US_DRV",
                        "Average run time for US_DRV",
                        "Maximum run time for TRJCTL",
                        "Average run time for TRJCTL",
                        "Maximum run time for US_PROCESSING",
                        "Average run time for US_PROCESSING",
                        "Maximum run time for US_EM",
                        "Average run time for US_EM",
                        "Maximum run time for US_PSI",
                        "Average run time for US_PSI",
                        "Maximum run time for APPDEMO_PARKSM",
                        "Average run time for APPDEMO_PARKSM",
                        "Maximum run time for MF_PARKSM_CORE",
                        "Average run time for MF_PARKSM_CORE",
                        "Maximum run time for MF_TRJPLA",
                        "Average run time for MF_TRJPLA",
                        "Maximum run time for MF_LSCA",
                        "Average run time for MF_LSCA",
                        "Maximum run time for MF_MANAGER",
                        "Average run time for MF_MANAGER",
                        "Maximum run time for MF_PDW",
                        "Average run time for MF_PDW",
                        "Maximum run time for APPDEMO_DRV",
                        "Average run time for APPDEMO_DRV",
                        "Maximum run time for MF_DRV",
                        "Average run time for MF_DRV",
                        "Maximum run time for APPDEMO_TONH",
                        "Average run time for APPDEMO_TONH",
                        "Maximum run time for APPDEMO_HMIH",
                        "Average run time for APPDEMO_HMIH",
                    ][i]
                }
                additional_results_dict[f"Expected-{i} [us]"] = {"value": ">= 0"}
                additional_results_dict[f"Measured-{i} [us]"] = {"value": f"{eval_res[i]:.1f}"}

        except Exception as err:
            result_final = fc.INPUT_MISSING
            print(f"Test failed, the following signal is missing:{str(err)}")
            # write_log_message(f"Test failed, the following signal is missing:{str(err)}", "error", LOGGER)
            additional_results_dict = {}
            additional_results_dict["Verdict"] = ({"value": result_final.title(), "color": fh.get_color(result_final)},)
            for i in range(constants.SignalsNumber.RUN_TIME_STEP_NUMBERS):
                additional_results_dict[f"Run time computing-{i}"] = {"value": ""}
                additional_results_dict[f"Expected-{i} [us]"] = {"value": ""}
                additional_results_dict[f"Measured-{i} [us]"] = {"value": ""}
            irst = list(additional_results_dict.keys())[0]
            additional_results_dict[irst] = {"value": f"Signal missing: {str(err)}"}
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
    name="MF RUN TIMES",
    description=(
        "Maximum run time for TCE Average run time for TCE Maximum run time for VEDODO Average run time for VEDODO"
        " Maximum run time for US_DRV Average run time for US_DRV Maximum run time for TRJCTL Average run time for"
        " TRJCTL Maximum run time for US_PROCESSING Average run time for US_PROCESSING Maximum run time for US_EM"
        " Average run time for US_EM Maximum run time for US_PSI Average run time for US_PSI Maximum run time for"
        " APPDEMO_PARKSM Average run time for APPDEMO_PARKSM Maximum run time for MF_PARKSM_CORE Average run time for"
        " MF_PARKSM_CORE Maximum run time for MF_TRJPLA Average run time for MF_TRJPLA Maximum run time for MF_LSCA"
        " Average run time for MF_LSCA Maximum run time for MF_MANAGER Average run time for MF_MANAGER Maximum run time"
        " for MF_PDW Average run time for MF_PDW Maximum run time for APPDEMO_DRV Average run time for APPDEMO_DRV"
        " Maximum run time for MF_DRV Average run time for MF_DRV Maximum run time for APPDEMO_TONH Average run time"
        " for APPDEMO_TONH Maximum run time for APPDEMO_HMIH Average run time for APPDEMO_HMIH"
    ),
)
class FtParkingCalculateRuntimes(TestCase):
    """Test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtParkingCalculateRuntimes]
