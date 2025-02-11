#!/usr/bin/env python3
"""Root cause analysis kpi for LSCA"""
import logging
import os
import sys
from typing import List

import pandas as pd
import plotly.graph_objects as go
from tsf.core.report import (
    ProcessingResult,
    ProcessingResultsList,
)
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    CustomReportTestStep,
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.db.results import TeststepResult
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "Pinzariu, George-Claudiu (uif94738)"
__copyright__ = "2024-2012, Continental AG"
__version__ = "1.0"
__status__ = "Development"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ALIAS = "RCA_LSCA"
VALID_SIGNAL_STATUS = 1


class CustomTeststepReport(CustomReportTestStep):
    """Custom test step report"""

    def overview(
        self,
        processing_details_list: ProcessingResultsList,
        teststep_result: List["TeststepResult"],
    ):
        """Method which customize the overview page in report"""
        s = ""

        self.result_list = []
        pr_list = processing_details_list

        for file in range(len(pr_list)):
            json_entries = ProcessingResult.from_json(pr_list.processing_result_files[file])
            a = {"Measurement": json_entries["file_name"]}
            a.update(json_entries["Additional_results"])
            self.result_list.append(a)

        s += "<br>"
        s += "<br>"
        try:
            from json import dumps

            columns = []
            row_events = []
            for r in self.result_list:
                columns.extend(list(r.keys()))
                break

            for d in self.result_list:
                r = []
                for c in columns:
                    if c in d:
                        v = d[c]
                        if isinstance(v, dict):
                            if "color" in v:
                                r.append(
                                    str(
                                        f"""<span align="center" style="width: 100%; height: 100%; display: block;background-color: {v['color']}; color : #ffffff">{v['value']}</span>"""
                                    )
                                )
                            else:
                                r.append(
                                    str(
                                        f"""<span align="center" style="width: 100%; height: 100%; display: block">{v['value']}</span>"""
                                    )
                                )
                        elif "Measurement" in c:
                            r.append(
                                str(
                                    f"""<span align="center" style="background-color: {d['Verdict']['color']}; color : #ffffff">{v}</span>"""
                                )
                            )
                        else:
                            r.append(v)

                    else:
                        r.append("")
                row_events.append(r)

            column_names = [{"title": str(c)} for c in columns]
            additional_tables = (
                """
        <h2>Additional Information</h2>
<script>
var table_column_names = """
                + dumps(column_names)
                + """;
var table_rows_events =  """
                + dumps(row_events)
                + """
$(document).ready(function() {
$('#events_table').DataTable( {
paging:    true,
searching: true,
info:      true,
scrollX: true,
ordering: true,
data: table_rows_events,
columns: table_column_names
} );
});
</script>
<table class="table-sm table-striped compact nowrap" id="events_table">
<caption>Table: Additional Information</caption>
</table>
"""
            )
            s += additional_tables

        except Exception:
            s += "<h6>No additional info available</h6>"
        return s

    def details(self, processing_details: ProcessingResult, teststep_result: "TeststepResult") -> str:
        """Method to customize the details page in report."""
        s = "<br>"
        m_res = teststep_result.measured_result
        e_res = teststep_result.teststep_definition.expected_results[None]
        (
            _,
            status,
        ) = e_res.compute_result_status(m_res)
        verdict = status.key.lower()

        if "data nok" in verdict:
            verdict = fc.NOT_ASSESSED
        s += (
            '<span align="center" style="width: 100%; height: 100%; display: block;background-color:'
            f' {fh.get_color(verdict)}; color : #ffffff">Step result: {verdict.upper()}</span>'
        )
        for k, v in processing_details.details.items():
            if "Plots" in k:
                s += "<div>"
                for plot in v:
                    s += plot
                s += "</div>"

        return s


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        SI_SIGNALS = "Signal_{}"
        ACTIVATE_BRAKE_INTERV = "ActivateBrakeIntervScreen"
        VELOCITY = "Velocity"
        SI_STATUS_PERCEPTION = "SI_STATUS_PERCEPTION"
        SI_STATUS_EGOMOTIONPORT = "SI_STATUS_EGOMOTIONPORT"
        SI_STATUS_COLLENVMODELPORT = "SI_STATUS_COLLENVMODELPORT"
        CEM_STATUS = "CEM_STATUS"
        PARKSM_STATUS = "PARKSM_STATUS"
        VD_vehicleOccupancyStatusPort = "VD_vehicleOccupancyStatusPort"
        VD_IuTrailerStatusPort = "VD_IuTrailerStatusPort"
        VD_IuDoorStatusPort = "VD_IuDoorStatusPort"
        VD_IuLaDMCStatusPort = "VD_IuLaDMCStatusPort"
        VD_IuLoDMCStatusPort = "VD_IuLoDMCStatusPort"
        VD_IuGearboxCtrlStatusPort = "VD_IuGearboxCtrlStatusPort"
        VD_IuEngineCtrlStatusPort = "VD_IuEngineCtrlStatusPort"

        STEERING_ANGLE = "SteeringAngle"
        TIMESTAMP = "mts_ts"
        motionState_nu = "Egomotionport_motionState_nu"
        pitch_rad = "Egomotionport_pitch_rad"
        roll_rad = "Egomotionport_roll_rad"
        frontWheelAngle_rad = "Egomotionport_frontWheelAngle_rad"
        rearWheelAngle_rad = "Egomotionport_rearWheelAngle_rad"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.VD_vehicleOccupancyStatusPort: [
                "ADC5xx_Device.VD_DATA.vehicleOccupancyStatusPort.sSigHeader.eSigStatus",
                "MTA_ADC5.VDP_DATA.vehicleOccupancyStatusPort.sSigHeader.eSigStatus",
            ],
            self.Columns.VD_IuTrailerStatusPort: [
                "ADC5xx_Device.VD_DATA.IuTrailerStatusPort.sSigHeader.eSigStatus",
                "MTA_ADC5.VDP_DATA.TrailerStatusPort.sSigHeader.eSigStatus",
            ],
            self.Columns.VD_IuDoorStatusPort: [
                "ADC5xx_Device.VD_DATA.IuDoorStatusPort.sSigHeader.eSigStatus",
                "MTA_ADC5.VDP_DATA.DoorStatusPort.sSigHeader.eSigStatus",
            ],
            self.Columns.VD_IuLaDMCStatusPort: [
                "ADC5xx_Device.VD_DATA.IuLaDMCStatusPort.sSigHeader.eSigStatus",
                "MTA_ADC5.AP_LODMC_DATA.LaDMCStatusPort.sSigHeader.eSigStatus",
            ],
            self.Columns.VD_IuLoDMCStatusPort: [
                "ADC5xx_Device.VD_DATA.IuLoDMCStatusPort.sSigHeader.eSigStatus",
                "MTA_ADC5.AP_LODMC_DATA.LoDMCStatusPort.sSigHeader.eSigStatus",
            ],
            self.Columns.VD_IuGearboxCtrlStatusPort: [
                "ADC5xx_Device.VD_DATA.IuGearboxCtrlStatusPort.sSigHeader.eSigStatus",
                "MTA_ADC5.VDP_DATA.GearboxCtrlStatusPort.sSigHeader.eSigStatus",
            ],
            self.Columns.VD_IuEngineCtrlStatusPort: [
                "ADC5xx_Device.VD_DATA.IuEngineCtrlStatusPort.sSigHeader.eSigStatus",
                "MTA_ADC5.VDP_DATA.EngineCtrlStatusPort.sSigHeader.eSigStatus",
            ],
            self.Columns.SI_STATUS_PERCEPTION: [
                "ADC5xx_Device.EM_DATA.EmPerceptionAvailabilityPort.sSigHeader.eSigStatus",
                "MTA_ADC5.SI_DATA.m_perceptionAvailabilityPort.sSigHeader.eSigStatus",
            ],
            self.Columns.SI_STATUS_EGOMOTIONPORT: [
                "ADC5xx_Device.EM_DATA.EmEgoMotionPort.sSigHeader.eSigStatus",
                "MTA_ADC5.SI_DATA.m_egoMotionPort.sSigHeader.eSigStatus",
            ],
            self.Columns.SI_STATUS_COLLENVMODELPORT: [
                "ADC5xx_Device.EM_DATA.EmCollEnvModelPort.sSigHeader.eSigStatus",
                "MTA_ADC5.SI_DATA.m_collisionEnvironmentModelPort.sSigHeader.eSigStatus",
            ],
            self.Columns.CEM_STATUS: [
                "ADC5xx_Device.CEM_EM_DATA.AUPDF_DynamicObjects.sSigHeader.eSigStatus",
                "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.sSigHeader.eSigStatus",
            ],
            self.Columns.PARKSM_STATUS: [
                "ADC5xx_Device.EM_DATA.EmOverrideLSCAPort.sSigHeader.eSigStatus",
                "MTA_ADC5.APPDEMO_PARKSM_DATA.overrideLSCAPort.sSigHeader.eSigStatus",
            ],
        }


signals_obj = Signals()


def port_status(signal_status):
    """Method to give a signal status with verdict and color."""
    color_dict = {
        0: "#ffc107",  # signal is not valid
        1: "#28a745",
    }
    text_dict = {
        0: "INVALID (only values of 0 were found)",  # signal is not valid
        1: "VALID",
    }
    return (
        f'<span align="center" style="width: 100%; height: 100%; display: block;background-color: {color_dict[signal_status]}'
        f' ; color : #ffffff">{text_dict[signal_status]}</span>'
    )


def port_status_v2(signal_status):
    """Method to give a signal status with verdict and color."""
    bg_color = ""
    message = ""
    color_dict = {
        0: "#ffc107",  # signal is not valid
        1: "#28a745",
        2: "#dc3545",
    }
    text_dict = {
        0: "NOT INITIALIZED (0)",  # signal is not valid
        1: "VALID (1)",
        2: "INVALID (2)",  # signal is not valid
    }
    if any(signal_status == constants.RCA_LSCA.AL_SIG_STATE_INVALID):
        bg_color = color_dict[constants.RCA_LSCA.AL_SIG_STATE_INVALID]
        message = text_dict[constants.RCA_LSCA.AL_SIG_STATE_INVALID]
    elif all(signal_status == constants.RCA_LSCA.AL_SIG_STATE_INIT):
        bg_color = color_dict[constants.RCA_LSCA.AL_SIG_STATE_INIT]
        message = text_dict[constants.RCA_LSCA.AL_SIG_STATE_INIT]
    elif any(signal_status == constants.RCA_LSCA.AL_SIG_STATE_OK):
        bg_color = color_dict[constants.RCA_LSCA.AL_SIG_STATE_OK]
        message = text_dict[constants.RCA_LSCA.AL_SIG_STATE_OK]
    return (
        f'<span align="center" style="width: 100%; height: 100%; display: block;background-color: {bg_color}'
        f' ; color : #ffffff">{message}</span>'
    )


def check_range(measured, thresholds, signal_status):
    """Method to check the range of signal status."""
    color_dict = {
        0: "#dc3545",  # outside thresholds
        1: "#28a745",  # witthin thresholds
    }
    if signal_status is True:
        color_string = color_dict[measured[0] >= thresholds[0] and measured[1] <= thresholds[1]]
    else:
        color_string = "#ffc107"  # signal is not valid
    return (
        f'<span align="center" style="width: 100%; height: 100%; display: block;background-color: {color_string}'
        ' ; color : #ffffff">{}</span>'
    )


@teststep_definition(
    step_number=1,
    name="SI",
    description="Check the output signals of SI component.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class Step1(TestStep):
    """Test step class"""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:
            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "druveb_time": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            plot_titles, plots, remarks = fh.rep([], 3)
            test_result = fc.INPUT_MISSING

            self.result.measured_result = DATA_NOK
            # Read measurement

            df = self.readers[ALIAS]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            sig_status_collenv = any(df[Signals.Columns.SI_STATUS_COLLENVMODELPORT] == VALID_SIGNAL_STATUS)
            sig_status_egomotion = any(df[Signals.Columns.SI_STATUS_EGOMOTIONPORT] == VALID_SIGNAL_STATUS)
            sig_status_perception = any(df[Signals.Columns.SI_STATUS_PERCEPTION] == VALID_SIGNAL_STATUS)

            if sig_status_collenv and sig_status_egomotion and sig_status_perception:

                test_result = fc.PASS
                self.result.measured_result = TRUE
            else:
                test_result = fc.FAIL
                self.result.measured_result = FALSE

            ego_motion_table = pd.DataFrame(
                {
                    "Signal evaluated": {
                        "0": signals_obj._properties[signals_obj.Columns.SI_STATUS_EGOMOTIONPORT][1],
                        "6": signals_obj._properties[signals_obj.Columns.SI_STATUS_COLLENVMODELPORT][1],
                        "7": signals_obj._properties[signals_obj.Columns.SI_STATUS_PERCEPTION][1],
                    },
                    "Expected value": {
                        "0": str(VALID_SIGNAL_STATUS),
                        "6": str(VALID_SIGNAL_STATUS),
                        "7": str(VALID_SIGNAL_STATUS),
                    },
                    "Port Status": {
                        "0": port_status_v2(df[Signals.Columns.SI_STATUS_EGOMOTIONPORT]),
                        "6": port_status_v2(df[Signals.Columns.SI_STATUS_COLLENVMODELPORT]),
                        "7": port_status_v2(df[Signals.Columns.SI_STATUS_PERCEPTION]),
                    },
                }
            )
            sig_sum = fh.build_html_table(ego_motion_table)

            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append("")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    y=df[Signals.Columns.SI_STATUS_EGOMOTIONPORT].values.tolist(),
                    x=df[Signals.Columns.TIMESTAMP].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.SI_STATUS_EGOMOTIONPORT][1],
                )
            )
            fig.add_trace(
                go.Scatter(
                    y=df[Signals.Columns.SI_STATUS_COLLENVMODELPORT].values.tolist(),
                    x=df[Signals.Columns.TIMESTAMP].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.SI_STATUS_COLLENVMODELPORT][1],
                )
            )
            fig.add_trace(
                go.Scatter(
                    y=df[Signals.Columns.SI_STATUS_PERCEPTION].values.tolist(),
                    x=df[Signals.Columns.TIMESTAMP].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.SI_STATUS_PERCEPTION][1],
                )
            )
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [epoch]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

            additional_results_dict = {
                "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
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

            self.result.details["root_cause_text"] = test_result
            self.result.details["Additional_results"] = additional_results_dict
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=2,
    name="CEM",
    description="Check the output signals of CEM component.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class Step2(TestStep):
    """Test step class"""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:
            self.result.details.update(
                {
                    "Plots": [],
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            plot_titles, plots, remarks = fh.rep([], 3)

            test_result = fc.INPUT_MISSING
            self.result.measured_result = DATA_NOK
            # Read measurement

            df = self.readers[ALIAS]
            df[Signals.Columns.TIMESTAMP] = df.index
            sig_status_cem = any(df[Signals.Columns.CEM_STATUS] == VALID_SIGNAL_STATUS)

            if sig_status_cem:

                test_result = fc.PASS
                self.result.measured_result = TRUE
            else:
                test_result = fc.FAIL
                self.result.measured_result = FALSE

            signal_status_table = pd.DataFrame(
                {
                    "Signal evaluated": {
                        "0": signals_obj._properties[signals_obj.Columns.CEM_STATUS][1],
                    },
                    "Expected value": {
                        "0": str(VALID_SIGNAL_STATUS),
                    },
                    "Port Status": {
                        "0": port_status_v2(df[Signals.Columns.CEM_STATUS]),
                    },
                }
            )

            sig_sum = fh.build_html_table(signal_status_table)

            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append("")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    y=df[Signals.Columns.CEM_STATUS].values.tolist(),
                    x=df[Signals.Columns.TIMESTAMP].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.CEM_STATUS][1],
                )
            )

            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [epoch]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plot_titles.append("car")
            plots.append(fig)
            remarks.append("")
            additional_results_dict = {
                "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
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
            self.result.details["root_cause_text"] = test_result
            self.result.details["Additional_results"] = additional_results_dict
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=3,
    name="PARKSM",
    description="Check the output signals of PARKSM component.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class Step3(TestStep):
    """Test step class"""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:
            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "druveb_time": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            plot_titles, plots, remarks = fh.rep([], 3)

            test_result = fc.INPUT_MISSING
            self.result.measured_result = DATA_NOK
            # Read measurement

            df = self.readers[ALIAS]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index
            sig_status_parksm = any(df[Signals.Columns.PARKSM_STATUS] == VALID_SIGNAL_STATUS)

            if sig_status_parksm:
                test_result = fc.PASS
                self.result.measured_result = TRUE
            else:
                test_result = fc.FAIL
                self.result.measured_result = FALSE

            signal_status_table = pd.DataFrame(
                {
                    "Signal evaluated": {
                        "0": signals_obj._properties[signals_obj.Columns.PARKSM_STATUS][1],
                    },
                    "Expected value": {
                        "0": str(VALID_SIGNAL_STATUS),
                    },
                    "Port Status": {
                        "0": port_status_v2(df[Signals.Columns.PARKSM_STATUS]),
                    },
                }
            )

            sig_sum = fh.build_html_table(signal_status_table)

            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append("")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    y=df[Signals.Columns.PARKSM_STATUS].values.tolist(),
                    x=df[Signals.Columns.TIMESTAMP].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.PARKSM_STATUS][1],
                )
            )

            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [epoch]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plot_titles.append("car")
            plots.append(fig)
            remarks.append("")
            additional_results_dict = {
                "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
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
            self.result.details["root_cause_text"] = test_result
            self.result.details["Additional_results"] = additional_results_dict
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=4,
    name="VD",
    description="Check the output signals of VD component.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class Step4(TestStep):
    """Test step class"""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:
            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "druveb_time": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            plot_titles, plots, remarks = fh.rep([], 3)

            test_result = fc.INPUT_MISSING
            self.result.measured_result = DATA_NOK
            # Read measurement

            df = self.readers[ALIAS]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index
            sig_status_vd_1 = any(df[Signals.Columns.VD_vehicleOccupancyStatusPort] == VALID_SIGNAL_STATUS)
            sig_status_vd_2 = any(df[Signals.Columns.VD_IuTrailerStatusPort] == VALID_SIGNAL_STATUS)
            sig_status_vd_3 = any(df[Signals.Columns.VD_IuDoorStatusPort] == VALID_SIGNAL_STATUS)
            sig_status_vd_4 = any(df[Signals.Columns.VD_IuLaDMCStatusPort] == VALID_SIGNAL_STATUS)
            sig_status_vd_5 = any(df[Signals.Columns.VD_IuLoDMCStatusPort] == VALID_SIGNAL_STATUS)
            sig_status_vd_6 = any(df[Signals.Columns.VD_IuGearboxCtrlStatusPort] == VALID_SIGNAL_STATUS)
            sig_status_vd_7 = any(df[Signals.Columns.VD_IuEngineCtrlStatusPort] == VALID_SIGNAL_STATUS)

            if (
                sig_status_vd_1
                and sig_status_vd_2
                and sig_status_vd_3
                and sig_status_vd_4
                and sig_status_vd_5
                and sig_status_vd_6
                and sig_status_vd_7
            ):

                test_result = fc.PASS
                self.result.measured_result = TRUE
            else:
                test_result = fc.FAIL
                self.result.measured_result = FALSE

            signal_status_table = pd.DataFrame(
                {
                    "Signal evaluated": {
                        "0": signals_obj._properties[signals_obj.Columns.VD_vehicleOccupancyStatusPort][1],
                        "1": signals_obj._properties[signals_obj.Columns.VD_IuTrailerStatusPort][1],
                        "2": signals_obj._properties[signals_obj.Columns.VD_IuDoorStatusPort][1],
                        "3": signals_obj._properties[signals_obj.Columns.VD_IuLaDMCStatusPort][1],
                        "4": signals_obj._properties[signals_obj.Columns.VD_IuLoDMCStatusPort][1],
                        "5": signals_obj._properties[signals_obj.Columns.VD_IuGearboxCtrlStatusPort][1],
                        "6": signals_obj._properties[signals_obj.Columns.VD_IuEngineCtrlStatusPort][1],
                    },
                    "Expected value": {
                        "0": str(VALID_SIGNAL_STATUS),
                        "1": str(VALID_SIGNAL_STATUS),
                        "2": str(VALID_SIGNAL_STATUS),
                        "3": str(VALID_SIGNAL_STATUS),
                        "4": str(VALID_SIGNAL_STATUS),
                        "5": str(VALID_SIGNAL_STATUS),
                        "6": str(VALID_SIGNAL_STATUS),
                    },
                    "Port Status": {
                        "0": port_status_v2(df[Signals.Columns.VD_vehicleOccupancyStatusPort]),
                        "1": port_status_v2(df[Signals.Columns.VD_IuTrailerStatusPort]),
                        "2": port_status_v2(df[Signals.Columns.VD_IuDoorStatusPort]),
                        "3": port_status_v2(df[Signals.Columns.VD_IuLaDMCStatusPort]),
                        "4": port_status_v2(df[Signals.Columns.VD_IuLoDMCStatusPort]),
                        "5": port_status_v2(df[Signals.Columns.VD_IuGearboxCtrlStatusPort]),
                        "6": port_status_v2(df[Signals.Columns.VD_IuEngineCtrlStatusPort]),
                    },
                }
            )

            sig_sum = fh.build_html_table(signal_status_table)

            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append("")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    y=df[Signals.Columns.VD_vehicleOccupancyStatusPort].values.tolist(),
                    x=df[Signals.Columns.TIMESTAMP].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.VD_vehicleOccupancyStatusPort][1],
                )
            )
            fig.add_trace(
                go.Scatter(
                    y=df[Signals.Columns.VD_IuTrailerStatusPort].values.tolist(),
                    x=df[Signals.Columns.TIMESTAMP].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.VD_IuTrailerStatusPort][1],
                )
            )
            fig.add_trace(
                go.Scatter(
                    y=df[Signals.Columns.VD_IuLoDMCStatusPort].values.tolist(),
                    x=df[Signals.Columns.TIMESTAMP].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.VD_IuLoDMCStatusPort][1],
                )
            )
            fig.add_trace(
                go.Scatter(
                    y=df[Signals.Columns.VD_IuLaDMCStatusPort].values.tolist(),
                    x=df[Signals.Columns.TIMESTAMP].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.VD_IuLaDMCStatusPort][1],
                )
            )
            fig.add_trace(
                go.Scatter(
                    y=df[Signals.Columns.VD_IuGearboxCtrlStatusPort].values.tolist(),
                    x=df[Signals.Columns.TIMESTAMP].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.VD_IuGearboxCtrlStatusPort][1],
                )
            )
            fig.add_trace(
                go.Scatter(
                    y=df[Signals.Columns.VD_IuEngineCtrlStatusPort].values.tolist(),
                    x=df[Signals.Columns.TIMESTAMP].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.VD_IuEngineCtrlStatusPort][1],
                )
            )
            fig.add_trace(
                go.Scatter(
                    y=df[Signals.Columns.VD_IuDoorStatusPort].values.tolist(),
                    x=df[Signals.Columns.TIMESTAMP].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.VD_IuDoorStatusPort][1],
                )
            )
            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [epoch]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plot_titles.append("car")
            plots.append(fig)
            remarks.append("")
            additional_results_dict = {
                "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
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
            self.result.details["root_cause_text"] = test_result
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("988206")
@testcase_definition(
    name="Output check",
    description="",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class OutputCheckLSCA(TestCase):
    """Test case class"""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            Step1,
            Step2,
            Step3,
            Step4,
        ]


ALIAS_ROOT = "ALIAS_ROOT"


@teststep_definition(
    step_number=1,
    name="SI",
    description="Check the output signals of VD component.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS_ROOT, Signals)
class Step1_ROOT(TestStep):
    """Test step class"""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")

        self.result.details.update(
            {
                "Plots": [],
                "software_version_file": "",
                "Km_driven": 0,
                "druveb_time": 0,
                "Plot_titles": [],
                "Remarks": [],
                "file_name": os.path.basename(self.artifacts[0].file_path),
            }
        )
        plot_titles, plots, remarks = fh.rep([], 3)

        test_result = fc.INPUT_MISSING
        self.result.measured_result = DATA_NOK
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
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
        self.result.details["root_cause_text"] = test_result


@teststep_definition(
    step_number=2,
    name="CEM",
    description="Check the output signals of VD component.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS_ROOT, Signals)
class Step2_ROOT(TestStep):
    """Test step class"""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")

        self.result.details.update(
            {
                "Plots": [],
                "software_version_file": "",
                "Km_driven": 0,
                "druveb_time": 0,
                "Plot_titles": [],
                "Remarks": [],
                "file_name": os.path.basename(self.artifacts[0].file_path),
            }
        )
        plot_titles, plots, remarks = fh.rep([], 3)

        test_result = fc.INPUT_MISSING
        self.result.measured_result = DATA_NOK
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
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
        self.result.details["root_cause_text"] = test_result


@teststep_definition(
    step_number=3,
    name="PARKSM",
    description="Check the output signals of VD component.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS_ROOT, Signals)
class Step3_ROOT(TestStep):
    """Test step class"""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")

        self.result.details.update(
            {
                "Plots": [],
                "software_version_file": "",
                "Km_driven": 0,
                "druveb_time": 0,
                "Plot_titles": [],
                "Remarks": [],
                "file_name": os.path.basename(self.artifacts[0].file_path),
            }
        )
        plot_titles, plots, remarks = fh.rep([], 3)

        test_result = fc.INPUT_MISSING
        self.result.measured_result = DATA_NOK
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
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
        self.result.details["root_cause_text"] = test_result


@teststep_definition(
    step_number=4,
    name="VD",
    description="Check the output signals of VD component.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS_ROOT, Signals)
class Step4_ROOT(TestStep):
    """Test step class"""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")

        self.result.details.update(
            {
                "Plots": [],
                "software_version_file": "",
                "Km_driven": 0,
                "druveb_time": 0,
                "Plot_titles": [],
                "Remarks": [],
                "file_name": os.path.basename(self.artifacts[0].file_path),
            }
        )
        plot_titles, plots, remarks = fh.rep([], 3)

        test_result = fc.INPUT_MISSING
        self.result.measured_result = DATA_NOK
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
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
        self.result.details["root_cause_text"] = test_result


@verifies("988206")
@testcase_definition(
    name="Root Cause Analisys",
    description="",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class RootCauseLSCA(TestCase):
    """Root cause test case class"""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            Step1_ROOT,
            Step2_ROOT,
            Step3_ROOT,
            Step4_ROOT,
        ]
