"""Example functional test"""  # this is a required docstring

"""import libraries"""
import logging
import os
import sys

import pandas as pd
import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
"""imports from tsf core"""
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.io.signals import SignalDefinition

"""imports from current repo"""
import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
import pl_parking.PLP.MF.UI_MANAGER.UI_Manager_helper as pdwh
import pl_parking.PLP.MF.UI_MANAGER.UI_Manager_helper as ui_helper
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport

__author__ = "Pinzariu George-Claudiu <uif94738>"
__copyright__ = "2020-2024, Continental AG"
__version__ = "0.1.0"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "UI_MANAGER_2688787"


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"

        SECTOR_CRITICALITY_PDW = "SECTOR_CRITICALITY_PDW_{}_{}"
        SECTOR_DISTANCE_PDW = "SECTOR_DISTANCE_PDW_{}_{}"
        SECTOR_CRITICALITY_HMI = "SECTOR_CRITICALITY_HMI_{}_{}"
        SECTOR_DISTANCE_HMI = "SECTOR_DISTANCE_HMI_{}_{}"
        PDWSYSTEMSTATE = "PDW System State"
        HMIINPUTPORTPDC = "hmiInputPortPDC"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.HMIINPUTPORTPDC: "AP.hmiInputPort.general.pdcSystemState_nu",
            self.Columns.PDWSYSTEMSTATE: "AP.drvWarnStatus.pdwSystemState_nu",
            self.Columns.TIME: [
                "Time",
                "Another version of signal",
            ],
        }
        self.FR, self.LE, self.RE, self.RI = ["Front", "Left", "Rear", "Right"]
        self.sides = [self.FR, self.LE, self.RE, self.RI]

        for side in self.sides:
            for x in range(4):
                self._properties.update(
                    {
                        self.Columns.SECTOR_CRITICALITY_PDW.format(
                            side, x
                        ): f"AP.pdcpSectorsPort.sectors{side}_{x}.criticalityLevel_nu",
                        self.Columns.SECTOR_DISTANCE_PDW.format(
                            side, x
                        ): f"AP.pdcpSectorsPort.sectors{side}_{x}.smallestDistance_m",
                        self.Columns.SECTOR_CRITICALITY_HMI.format(
                            side, x
                        ): f"AP.hmiInputPort.pdcSectors.{side.lower()}_{x}.criticalityLevel_nu",
                        self.Columns.SECTOR_DISTANCE_HMI.format(
                            side, x
                        ): f"AP.hmiInputPort.pdcSectors.{side.lower()}_{x}.smallestDistance_m",
                    }
                )


signals_obj = Signals()


class BaseStep(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
    """

    custom_report = MfCustomTeststepReport  # Specific overview

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """  # required docstring
        _log.debug("Starting processing...")
        # Update the details from the results page with the needed information
        # All the information from self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
        try:
            self.result.details.update({"Plots": [], "file_name": os.path.basename(self.artifacts[0].file_path)})

            self.test_result = fc.INPUT_MISSING  # Result
            self.result.measured_result = DATA_NOK  # Initializing the result with data nok

            self.results = {
                side: {"Details": "", "Result": "", "Measured Result": "", "HMI": "", "PDW": ""}
                for side in signals_obj.sides
            }

            self.signals = self.readers[ALIAS]
            self.signals[Signals.Columns.TIMESTAMP] = self.signals.index
            ap_time = round(self.signals[Signals.Columns.TIME], 3)
            self.ap_time = round(self.signals[Signals.Columns.TIME], 3)

            for side in signals_obj.sides:
                pdw_activated = self.signals[Signals.Columns.PDWSYSTEMSTATE]
                mask_activation = (
                    (pdw_activated == constants.UiManager.pdwSystemState.PDW_ACTIVATED_BY_BUTTON)
                    | (pdw_activated == constants.UiManager.pdwSystemState.PDW_ACTIVATED_BY_R_GEAR)
                    | (pdw_activated == constants.UiManager.pdwSystemState.PDW_AUTOMATICALLY_ACTIVATED)
                )
                activated_idx = pdw_activated[mask_activation].first_valid_index()
                if activated_idx:
                    smallest_dist_pdw = [
                        self.signals[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, 0)].loc[activated_idx:],
                        self.signals[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, 1)].loc[activated_idx:],
                        self.signals[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, 2)].loc[activated_idx:],
                        self.signals[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, 3)].loc[activated_idx:],
                    ]

                    critical_level_pdw = [
                        self.signals[Signals.Columns.SECTOR_CRITICALITY_PDW.format(side, 0)].loc[activated_idx:],
                        self.signals[Signals.Columns.SECTOR_CRITICALITY_PDW.format(side, 1)].loc[activated_idx:],
                        self.signals[Signals.Columns.SECTOR_CRITICALITY_PDW.format(side, 2)].loc[activated_idx:],
                        self.signals[Signals.Columns.SECTOR_CRITICALITY_PDW.format(side, 3)].loc[activated_idx:],
                    ]
                    signal_names_pdw = [
                        signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, 0)],
                        signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, 1)],
                        signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, 2)],
                        signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, 3)],
                    ]
                    signal_names_hmi = [
                        signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, 0)],
                        signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, 1)],
                        signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, 2)],
                        signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, 3)],
                    ]

                    smallest_dist_hmi = [
                        self.signals[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, 0)].loc[activated_idx:],
                        self.signals[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, 1)].loc[activated_idx:],
                        self.signals[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, 2)].loc[activated_idx:],
                        self.signals[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, 3)].loc[activated_idx:],
                    ]
                    critical_level_hmi = [
                        self.signals[Signals.Columns.SECTOR_CRITICALITY_HMI.format(side, 0)].loc[activated_idx:],
                        self.signals[Signals.Columns.SECTOR_CRITICALITY_HMI.format(side, 1)].loc[activated_idx:],
                        self.signals[Signals.Columns.SECTOR_CRITICALITY_HMI.format(side, 2)].loc[activated_idx:],
                        self.signals[Signals.Columns.SECTOR_CRITICALITY_HMI.format(side, 3)].loc[activated_idx:],
                    ]

                    signal_summary_pdw, verdict_pdw, input_timestamp_pdw = pdwh.all_sector_evaluation(
                        smallest_dist_pdw, critical_level_pdw, signal_names_pdw
                    )
                    signal_summary_hmi, verdict_hmi, input_timestamp_hmi = pdwh.all_sector_evaluation(
                        smallest_dist_hmi, critical_level_hmi, signal_names_hmi
                    )
                    self.results[side]["HMI"] = signal_summary_hmi
                    self.results[side]["PDW"] = signal_summary_pdw
                    if input_timestamp_hmi is not None:
                        if input_timestamp_hmi - input_timestamp_pdw == 0:
                            self.results[side][
                                "Details"
                            ] = "HMIHandler informed the ego vehicle driver of the current system state of the PDW function."
                            self.results[side]["Result"] = fc.PASS
                            self.results[side]["Measured Result"] = TRUE
                        else:
                            it_took = round(ap_time.iloc[input_timestamp_hmi] - ap_time.iloc[input_timestamp_pdw], 2)
                            self.results[side]["Details"] = f"HMIHandler had a delay of {it_took} s."
                            self.results[side]["Result"] = fc.FAIL
                            self.results[side]["Measured Result"] = FALSE
                    else:

                        self.results[side]["Details"] = "HMIHandler did not inform the ego vehicle driver at all."
                        self.results[side]["Result"] = fc.FAIL
                        self.results[side]["Measured Result"] = FALSE
                else:
                    self.results[side]["HMI"] = {
                        x: "Criticality = N/a, SLICE = N/a, at distance N/a m." for x in range(4)
                    }
                    self.results[side]["PDW"] = {
                        x: "Criticality = N/a, SLICE = N/a, at distance N/a m." for x in range(4)
                    }
                    self.results[side]["Details"] = "PDC was not activated."
                    self.results[side]["Result"] = fc.NOT_ASSESSED
                    self.results[side]["Measured Result"] = DATA_NOK
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=1,
    name="Left",  # this would be shown as a test step name in html report
    description=("Check for left sector."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStep_Left(BaseStep):
    """Example test step."""  # example of required docstring

    def __init__(self):
        """Initialize the test step."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test step."""  # example of required docstring
        try:

            side = signals_obj.LE
            self.result.measured_result = DATA_NOK
            super().process()
            sig_sum = {"Evaluation": {"0": ""}, "Verdict": {"0": ""}}
            additional_info = {
                "Sectors": {str(x): x for x in range(4)},
                "PDW": {str(x): val for x, val in enumerate(self.results[side]["PDW"].values())},
                "HMI": {str(x): val for x, val in enumerate(self.results[side]["HMI"].values())},
            }
            plots = []
            sig_sum["Evaluation"]["0"] = self.results[side]["Details"]
            sig_sum["Verdict"]["0"] = ui_helper.get_result_color(self.results[side]["Result"])
            table_title = f"PDW Sector Evaluation for {side} side"
            remark = ""

            plots.append(fh.build_html_table(pd.DataFrame(sig_sum), remark, table_title))
            additional_info = {
                "Sectors": {str(x): x for x in range(4)},
                "PDW": {str(x): val for x, val in enumerate(self.results[side]["PDW"].values())},
                "HMI": {str(x): val for x, val in enumerate(self.results[side]["HMI"].values())},
            }
            remark = f"<br>Additional Information:<br>\
                        <br>PDW Sectors:{signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, 0)].replace('_0.', '_%.')}<br>\
                        <br>HMI Sectors:{signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, 0)].replace('_0.', '_%.')}<br>"
            plots.append(fh.build_html_table(pd.DataFrame(additional_info), remark))
            fig = go.Figure()
            fig_criticality = go.Figure()
            for i in range(4):
                fig.add_trace(
                    go.Scatter(
                        x=self.ap_time,
                        y=self.signals[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, i)],
                        line=dict(color="red"),
                        text=[
                            f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                            f"Sector: {i}<br>"
                            f"Distance PDW: {val:.2f} m<br>"
                            for idx, val in enumerate(
                                self.signals[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, i)].values.tolist()
                            )
                        ],
                        hoverinfo="text",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=self.ap_time,
                        y=self.signals[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, i)],
                        line=dict(color="blue"),
                        text=[
                            f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                            f"Sector: {i}<br>"
                            f"Distance HMI: {val:.2f} m<br>"
                            for idx, val in enumerate(
                                self.signals[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, i)].values.tolist()
                            )
                        ],
                        hoverinfo="text",
                    )
                )
                fig_criticality.add_trace(
                    go.Scatter(
                        x=self.ap_time,
                        y=self.signals[Signals.Columns.SECTOR_CRITICALITY_PDW.format(side, i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITY_PDW.format(side, i)],
                        line=dict(color="red"),
                        text=[
                            f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                            f"Sector: {i}<br>"
                            f"Criticality PDW: {val:.2f} m<br>"
                            for idx, val in enumerate(
                                self.signals[Signals.Columns.SECTOR_CRITICALITY_PDW.format(side, i)].values.tolist()
                            )
                        ],
                        hoverinfo="text",
                    )
                )
                fig_criticality.add_trace(
                    go.Scatter(
                        x=self.ap_time,
                        y=self.signals[Signals.Columns.SECTOR_CRITICALITY_HMI.format(side, i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITY_HMI.format(side, i)],
                        line=dict(color="blue"),
                        text=[
                            f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                            f"Sector: {i}<br>"
                            f"Criticality HMI: {val:.2f} m<br>"
                            for idx, val in enumerate(
                                self.signals[Signals.Columns.SECTOR_CRITICALITY_HMI.format(side, i)].values.tolist()
                            )
                        ],
                        hoverinfo="text",
                    )
                )

            fig.layout = go.Layout(
                title="PDW is represented by red and HMI by blue",
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            fig_criticality.layout = go.Layout(
                title="PDW is represented by red and HMI by blue",
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
            )
            fig_criticality.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            fig_sys_state = go.Figure()
            fig_sys_state.add_trace(
                go.Scatter(
                    x=self.ap_time,
                    y=self.signals[Signals.Columns.HMIINPUTPORTPDC].values.tolist(),
                    mode="lines",
                    line=dict(color="blue"),
                    name=signals_obj._properties[Signals.Columns.HMIINPUTPORTPDC],
                    text=[
                        f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                        f"HMI System State:<br>"
                        f"{constants.UiManager.pdwSystemState.get_variable_name(state)}"
                        for idx, state in enumerate(self.signals[Signals.Columns.HMIINPUTPORTPDC].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )
            fig_sys_state.add_trace(
                go.Scatter(
                    x=self.ap_time,
                    y=self.signals[Signals.Columns.PDWSYSTEMSTATE].values.tolist(),
                    mode="lines",
                    line=dict(color="red"),
                    name=signals_obj._properties[Signals.Columns.PDWSYSTEMSTATE],
                    text=[
                        f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                        f"PDW System State:<br>"
                        f"{constants.UiManager.pdwSystemState.get_variable_name(state)}"
                        for idx, state in enumerate(self.signals[Signals.Columns.PDWSYSTEMSTATE].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )

            fig_sys_state.layout = go.Layout(
                title="System state", yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]"
            )
            fig_sys_state.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            plots.append(fig)
            plots.append(fig_criticality)
            plots.append(fig_sys_state)
            self.result.measured_result = self.results[signals_obj.LE]["Measured Result"]

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=2,
    name="Right",  # this would be shown as a test step name in html report
    description=("Check for right sector."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStep_Right(BaseStep):
    """Example test step."""  # example of required docstring

    def __init__(self):
        """Initialize the test step."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test step."""  # example of required docstring
        try:

            side = signals_obj.RI
            self.result.measured_result = DATA_NOK
            super().process()
            sig_sum = {"Evaluation": {"0": ""}, "Verdict": {"0": ""}}
            plots = []
            sig_sum["Evaluation"]["0"] = self.results[side]["Details"]
            sig_sum["Verdict"]["0"] = ui_helper.get_result_color(self.results[side]["Result"])
            table_title = f"PDW Sector Evaluation for {side} side"
            remark = ""
            plots.append(fh.build_html_table(pd.DataFrame(sig_sum), remark, table_title))
            additional_info = {
                "Sectors": {str(x): x for x in range(4)},
                "PDW": {str(x): val for x, val in enumerate(self.results[side]["PDW"].values())},
                "HMI": {str(x): val for x, val in enumerate(self.results[side]["HMI"].values())},
            }
            remark = f"<br>Additional Information:<br>\
                        <br>PDW Sectors:{signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, 0)].replace('_0.', '_%.')}<br>\
                        <br>HMI Sectors:{signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, 0)].replace('_0.', '_%.')}<br>"
            plots.append(fh.build_html_table(pd.DataFrame(additional_info), remark))
            fig = go.Figure()
            fig_criticality = go.Figure()
            for i in range(4):
                fig.add_trace(
                    go.Scatter(
                        x=self.ap_time,
                        y=self.signals[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, i)],
                        line=dict(color="red"),
                        text=[
                            f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                            f"Sector: {i}<br>"
                            f"Distance PDW: {val:.2f} m<br>"
                            for idx, val in enumerate(
                                self.signals[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, i)].values.tolist()
                            )
                        ],
                        hoverinfo="text",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=self.ap_time,
                        y=self.signals[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, i)],
                        line=dict(color="blue"),
                        text=[
                            f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                            f"Sector: {i}<br>"
                            f"Distance HMI: {val:.2f} m<br>"
                            for idx, val in enumerate(
                                self.signals[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, i)].values.tolist()
                            )
                        ],
                        hoverinfo="text",
                    )
                )
                fig_criticality.add_trace(
                    go.Scatter(
                        x=self.ap_time,
                        y=self.signals[Signals.Columns.SECTOR_CRITICALITY_PDW.format(side, i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITY_PDW.format(side, i)],
                        line=dict(color="red"),
                        text=[
                            f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                            f"Sector: {i}<br>"
                            f"Criticality PDW: {val:.2f} m<br>"
                            for idx, val in enumerate(
                                self.signals[Signals.Columns.SECTOR_CRITICALITY_PDW.format(side, i)].values.tolist()
                            )
                        ],
                        hoverinfo="text",
                    )
                )
                fig_criticality.add_trace(
                    go.Scatter(
                        x=self.ap_time,
                        y=self.signals[Signals.Columns.SECTOR_CRITICALITY_HMI.format(side, i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITY_HMI.format(side, i)],
                        line=dict(color="blue"),
                        text=[
                            f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                            f"Sector: {i}<br>"
                            f"Criticality HMI: {val:.2f} m<br>"
                            for idx, val in enumerate(
                                self.signals[Signals.Columns.SECTOR_CRITICALITY_HMI.format(side, i)].values.tolist()
                            )
                        ],
                        hoverinfo="text",
                    )
                )

            fig.layout = go.Layout(
                title="PDW is represented by red and HMI by blue",
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            fig_criticality.layout = go.Layout(
                title="PDW is represented by red and HMI by blue",
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
            )
            fig_criticality.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            fig_sys_state = go.Figure()
            fig_sys_state.add_trace(
                go.Scatter(
                    x=self.ap_time,
                    y=self.signals[Signals.Columns.HMIINPUTPORTPDC].values.tolist(),
                    mode="lines",
                    line=dict(color="blue"),
                    name=signals_obj._properties[Signals.Columns.HMIINPUTPORTPDC],
                    text=[
                        f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                        f"Park Core Status:<br>"
                        f"{constants.UiManager.pdwSystemState.get_variable_name(state)}"
                        for idx, state in enumerate(self.signals[Signals.Columns.HMIINPUTPORTPDC].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )
            fig_sys_state.add_trace(
                go.Scatter(
                    x=self.ap_time,
                    y=self.signals[Signals.Columns.PDWSYSTEMSTATE].values.tolist(),
                    mode="lines",
                    line=dict(color="red"),
                    name=signals_obj._properties[Signals.Columns.PDWSYSTEMSTATE],
                    text=[
                        f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                        f"PDW SYSTEM STATE:<br>"
                        f"{constants.UiManager.pdwSystemState.get_variable_name(state)}"
                        for idx, state in enumerate(self.signals[Signals.Columns.PDWSYSTEMSTATE].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )

            fig_sys_state.layout = go.Layout(
                title="System state", yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]"
            )
            fig_sys_state.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            plots.append(fig)
            plots.append(fig_criticality)
            plots.append(fig_sys_state)
            self.result.measured_result = self.results[signals_obj.LE]["Measured Result"]

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=3,
    name="Rear",  # this would be shown as a test step name in html report
    description=("Check for rear sector."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStep_Rear(BaseStep):
    """Example test step."""  # example of required docstring

    def __init__(self):
        """Initialize the test step."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test step."""  # example of required docstring
        try:

            side = signals_obj.RE
            self.result.measured_result = DATA_NOK
            super().process()
            sig_sum = {"Evaluation": {"0": ""}, "Verdict": {"0": ""}}
            plots = []
            sig_sum["Evaluation"]["0"] = self.results[side]["Details"]
            sig_sum["Verdict"]["0"] = ui_helper.get_result_color(self.results[side]["Result"])
            table_title = f"PDW Sector Evaluation for {side} side"
            remark = ""
            plots.append(fh.build_html_table(pd.DataFrame(sig_sum), remark, table_title))
            additional_info = {
                "Sectors": {str(x): x for x in range(4)},
                "PDW": {str(x): val for x, val in enumerate(self.results[side]["PDW"].values())},
                "HMI": {str(x): val for x, val in enumerate(self.results[side]["HMI"].values())},
            }
            remark = f"<br>Additional Information:<br>\
                        <br>PDW Sectors:{signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, 0)].replace('_0.', '_%.')}<br>\
                        <br>HMI Sectors:{signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, 0)].replace('_0.', '_%.')}<br>"
            plots.append(fh.build_html_table(pd.DataFrame(additional_info), remark))
            fig = go.Figure()
            fig_criticality = go.Figure()
            for i in range(4):
                fig.add_trace(
                    go.Scatter(
                        x=self.ap_time,
                        y=self.signals[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, i)],
                        line=dict(color="red"),
                        text=[
                            f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                            f"Sector: {i}<br>"
                            f"Distance PDW: {val:.2f} m<br>"
                            for idx, val in enumerate(
                                self.signals[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, i)].values.tolist()
                            )
                        ],
                        hoverinfo="text",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=self.ap_time,
                        y=self.signals[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, i)],
                        line=dict(color="blue"),
                        text=[
                            f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                            f"Sector: {i}<br>"
                            f"Distance HMI: {val:.2f} m<br>"
                            for idx, val in enumerate(
                                self.signals[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, i)].values.tolist()
                            )
                        ],
                        hoverinfo="text",
                    )
                )
                fig_criticality.add_trace(
                    go.Scatter(
                        x=self.ap_time,
                        y=self.signals[Signals.Columns.SECTOR_CRITICALITY_PDW.format(side, i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITY_PDW.format(side, i)],
                        line=dict(color="red"),
                        text=[
                            f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                            f"Sector: {i}<br>"
                            f"Criticality PDW: {val:.2f} m<br>"
                            for idx, val in enumerate(
                                self.signals[Signals.Columns.SECTOR_CRITICALITY_PDW.format(side, i)].values.tolist()
                            )
                        ],
                        hoverinfo="text",
                    )
                )
                fig_criticality.add_trace(
                    go.Scatter(
                        x=self.ap_time,
                        y=self.signals[Signals.Columns.SECTOR_CRITICALITY_HMI.format(side, i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITY_HMI.format(side, i)],
                        line=dict(color="blue"),
                        text=[
                            f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                            f"Sector: {i}<br>"
                            f"Criticality HMI: {val:.2f} m<br>"
                            for idx, val in enumerate(
                                self.signals[Signals.Columns.SECTOR_CRITICALITY_HMI.format(side, i)].values.tolist()
                            )
                        ],
                        hoverinfo="text",
                    )
                )

            fig.layout = go.Layout(
                title="PDW is represented by red and HMI by blue",
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            fig_criticality.layout = go.Layout(
                title="PDW is represented by red and HMI by blue",
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
            )
            fig_criticality.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            fig_sys_state = go.Figure()
            fig_sys_state.add_trace(
                go.Scatter(
                    x=self.ap_time,
                    y=self.signals[Signals.Columns.HMIINPUTPORTPDC].values.tolist(),
                    mode="lines",
                    line=dict(color="blue"),
                    name=signals_obj._properties[Signals.Columns.HMIINPUTPORTPDC],
                    text=[
                        f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                        f"Park Core Status:<br>"
                        f"{constants.UiManager.pdwSystemState.get_variable_name(state)}"
                        for idx, state in enumerate(self.signals[Signals.Columns.HMIINPUTPORTPDC].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )
            fig_sys_state.add_trace(
                go.Scatter(
                    x=self.ap_time,
                    y=self.signals[Signals.Columns.PDWSYSTEMSTATE].values.tolist(),
                    mode="lines",
                    line=dict(color="red"),
                    name=signals_obj._properties[Signals.Columns.PDWSYSTEMSTATE],
                    text=[
                        f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                        f"PDW SYSTEM STATE:<br>"
                        f"{constants.UiManager.pdwSystemState.get_variable_name(state)}"
                        for idx, state in enumerate(self.signals[Signals.Columns.PDWSYSTEMSTATE].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )

            fig_sys_state.layout = go.Layout(
                title="System state", yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]"
            )
            fig_sys_state.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            plots.append(fig)
            plots.append(fig_criticality)
            plots.append(fig_sys_state)
            self.result.measured_result = self.results[signals_obj.LE]["Measured Result"]

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=4,
    name="Front",  # this would be shown as a test step name in html report
    description=("Check for front sector."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStep_Front(BaseStep):
    """Example test step."""  # example of required docstring

    def __init__(self):
        """Initialize the test step."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test step."""  # example of required docstring
        try:
            side = signals_obj.FR
            self.result.measured_result = DATA_NOK
            super().process()
            sig_sum = {"Evaluation": {"0": ""}, "Verdict": {"0": ""}}
            plots = []
            sig_sum["Evaluation"]["0"] = self.results[side]["Details"]
            sig_sum["Verdict"]["0"] = ui_helper.get_result_color(self.results[side]["Result"])
            table_title = f"PDW Sector Evaluation for {side} side"
            remark = ""
            plots.append(fh.build_html_table(pd.DataFrame(sig_sum), remark, table_title))
            additional_info = {
                "Sectors": {str(x): x for x in range(4)},
                "PDW": {str(x): val for x, val in enumerate(self.results[side]["PDW"].values())},
                "HMI": {str(x): val for x, val in enumerate(self.results[side]["HMI"].values())},
            }
            remark = f"<br>Additional Information:<br>\
                        <br>PDW Sectors:{signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, 0)].replace('_0.', '_%.')}<br>\
                        <br>HMI Sectors:{signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, 0)].replace('_0.', '_%.')}<br>"
            plots.append(fh.build_html_table(pd.DataFrame(additional_info), remark))
            fig = go.Figure()
            fig_criticality = go.Figure()
            for i in range(4):
                fig.add_trace(
                    go.Scatter(
                        x=self.ap_time,
                        y=self.signals[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, i)],
                        line=dict(color="red"),
                        text=[
                            f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                            f"Sector: {i}<br>"
                            f"Distance PDW: {val:.2f} m<br>"
                            for idx, val in enumerate(
                                self.signals[Signals.Columns.SECTOR_DISTANCE_PDW.format(side, i)].values.tolist()
                            )
                        ],
                        hoverinfo="text",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=self.ap_time,
                        y=self.signals[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, i)],
                        line=dict(color="blue"),
                        text=[
                            f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                            f"Sector: {i}<br>"
                            f"Distance HMI: {val:.2f} m<br>"
                            for idx, val in enumerate(
                                self.signals[Signals.Columns.SECTOR_DISTANCE_HMI.format(side, i)].values.tolist()
                            )
                        ],
                        hoverinfo="text",
                    )
                )
                fig_criticality.add_trace(
                    go.Scatter(
                        x=self.ap_time,
                        y=self.signals[Signals.Columns.SECTOR_CRITICALITY_PDW.format(side, i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITY_PDW.format(side, i)],
                        line=dict(color="red"),
                        text=[
                            f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                            f"Sector: {i}<br>"
                            f"Criticality PDW: {val:.2f} m<br>"
                            for idx, val in enumerate(
                                self.signals[Signals.Columns.SECTOR_CRITICALITY_PDW.format(side, i)].values.tolist()
                            )
                        ],
                        hoverinfo="text",
                    )
                )
                fig_criticality.add_trace(
                    go.Scatter(
                        x=self.ap_time,
                        y=self.signals[Signals.Columns.SECTOR_CRITICALITY_HMI.format(side, i)].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[Signals.Columns.SECTOR_CRITICALITY_HMI.format(side, i)],
                        line=dict(color="blue"),
                        text=[
                            f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                            f"Sector: {i}<br>"
                            f"Criticality HMI: {val:.2f} m<br>"
                            for idx, val in enumerate(
                                self.signals[Signals.Columns.SECTOR_CRITICALITY_HMI.format(side, i)].values.tolist()
                            )
                        ],
                        hoverinfo="text",
                    )
                )

            fig.layout = go.Layout(
                title="PDW is represented by red and HMI by blue",
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            fig_criticality.layout = go.Layout(
                title="PDW is represented by red and HMI by blue",
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
            )
            fig_criticality.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            fig_sys_state = go.Figure()
            fig_sys_state.add_trace(
                go.Scatter(
                    x=self.ap_time,
                    y=self.signals[Signals.Columns.HMIINPUTPORTPDC].values.tolist(),
                    mode="lines",
                    line=dict(color="blue"),
                    name=signals_obj._properties[Signals.Columns.HMIINPUTPORTPDC],
                    text=[
                        f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                        f"Park Core Status:<br>"
                        f"{constants.UiManager.pdwSystemState.get_variable_name(state)}"
                        for idx, state in enumerate(self.signals[Signals.Columns.HMIINPUTPORTPDC].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )
            fig_sys_state.add_trace(
                go.Scatter(
                    x=self.ap_time,
                    y=self.signals[Signals.Columns.PDWSYSTEMSTATE].values.tolist(),
                    mode="lines",
                    line=dict(color="red"),
                    name=signals_obj._properties[Signals.Columns.PDWSYSTEMSTATE],
                    text=[
                        f"Timestamp: {self.ap_time.iloc[idx]} <br>"
                        f"PDW SYSTEM STATE:<br>"
                        f"{constants.UiManager.pdwSystemState.get_variable_name(state)}"
                        for idx, state in enumerate(self.signals[Signals.Columns.PDWSYSTEMSTATE].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )

            fig_sys_state.layout = go.Layout(
                title="System state", yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]"
            )
            fig_sys_state.update_layout(constants.PlotlyTemplate.lgt_tmplt)

            plots.append(fig)
            plots.append(fig_criticality)
            plots.append(fig_sys_state)
            self.result.measured_result = self.results[signals_obj.LE]["Measured Result"]

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


# Define the test case definition. This will include the name of the test case and a description of the test.
@testcase_definition(
    name="UI_MANAGER_2688787",
    description="HMIHandler shall inform the ego vehicle driver of the PDW sectorization, criticalities and slice number within the criticality level.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_ZdIcY3psEe-9FrFCDLx05w&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_ns_CwE4gEe6M5-WQsF_-tQ&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class TestCaseFT(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStep_Left, TestStep_Right, TestStep_Rear, TestStep_Front]
