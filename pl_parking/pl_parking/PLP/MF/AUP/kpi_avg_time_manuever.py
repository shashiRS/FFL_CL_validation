#!/usr/bin/env python3
"""Average manuever time KPI"""
import logging
import os
import sys
from typing import List

import pandas as pd
import plotly.graph_objects as go
from tsf.core.common import AggregateFunction, RelationOperator
from tsf.core.report import (
    ProcessingResult,
    ProcessingResultsList,
    TeststepResult,
)
from tsf.core.results import DATA_NOK, NAN, ExpectedResult, Result
from tsf.core.testcase import (
    CustomReportTestStep,
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh  # nopep8
import pl_parking.PLP.MF.constants as constants

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))  # nopep8
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "<CHANGE ME>"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

EXAMPLE = "VEHICLE_TIME"


class MfCustomTeststepReport(CustomReportTestStep):
    """This is a custom test step report."""

    def overview(
        self,
        processing_details_list: ProcessingResultsList,
        teststep_result: List["TeststepResult"],
    ):
        """This is function which modify the overview page in report."""
        s = ""
        file_counter = 0
        self.result_list = []

        pr_list = processing_details_list

        for file in range(len(pr_list)):
            json_entries = ProcessingResult.from_json(pr_list.processing_result_files[file])
            # try:
            if json_entries["Additional_results_ts"] != "-":
                file_counter += 1

                a = {"Measurement": json_entries["file_name"]}
                a.update(json_entries["Additional_results_ts"])
                self.result_list.append(a)
            # except:
            #     pass
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
</table>
"""
            )
            s += additional_tables

        except Exception:
            s += "<h6>No additional info available</h6>"
        return s

        return s

    def details(self, processing_details: ProcessingResult, teststep_result: "TeststepResult") -> str:
        """This function modify the details page from report."""
        s = "<br>"
        # color = ''
        # m_res = teststep_result.measured_result
        # e_res = teststep_result.teststep_definition.expected_results[None]
        # (_, status,) = e_res.compute_result_status(m_res)
        # verdict = status.key.lower()

        # if "data nok" in verdict:
        #     verdict = fc.NOT_ASSESSED

        # s += f'<span align="center" style="width: 100%; height: 100%; display: block;background-color: {fh.get_color(verdict)}; color : #ffffff">Step result: {verdict.upper()}</span>'

        for k, v in processing_details.details.items():
            if "Plots" in k:
                s += "<div>"
                for plot in v:

                    s += plot
                s += "</div>"

        return s


class StoreStepResults:
    """Initializes variables for multiple steps and provides a method
    to check their status and return corresponding results and color codes.
    """

    def __init__(self):
        """Initialize object attributes."""
        self.step_1 = fc.INPUT_MISSING
        self.step_2 = fc.INPUT_MISSING
        self.step_3 = fc.INPUT_MISSING
        self.park_verdict_1 = "Unknown"
        self.park_verdict_2 = "Unknown"
        self.park_verdict_3 = "Unknown"

    def check_result(self):
        """
        The function `check_result` checks the status of multiple steps and returns a corresponding result and color code.
        :return: The `check_result` method is returning a tuple with two values. The first value is one of the constants
        `fc.PASS`, `fc.INPUT_MISSING`, `fc.NOT_ASSESSED`, or `fc.FAIL` based on the conditions checked in the method. The
        second value is a color code represented as a string.
        """
        if self.step_1 == fc.PASS or self.step_2 == fc.PASS or self.step_3 == fc.PASS:
            return fc.PASS, "#28a745"
        elif self.step_1 == fc.NOT_ASSESSED and self.step_2 == fc.NOT_ASSESSED and self.step_3 == fc.NOT_ASSESSED:
            return fc.NOT_ASSESSED, "rgb(129, 133, 137)"
        else:
            # self.case_result == fc.FAIL
            return fc.FAIL, "#dc3545"

    def check_parking_success(self):
        """
        The function `check_result` checks the status of multiple steps and returns a corresponding result and color code.
        :return: The `check_result` method is returning a tuple with two values. The first value is one of the constants
        `fc.PASS`, `fc.INPUT_MISSING`, `fc.NOT_ASSESSED`, or `fc.FAIL` based on the conditions checked in the method. The
        second value is a color code represented as a string.
        """
        if self.park_verdict_1 == "Success" or self.park_verdict_2 == "Success" or self.park_verdict_3 == "Success":
            return "Success"
        elif self.park_verdict_1 == "Unknown" and self.park_verdict_2 == "Unknown" and self.park_verdict_3 == "Unknown":
            return "Unknown"
        else:
            return "Failed"


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        VALID_SEGMENTS = "NumValidSegments"
        PARKING_MODE = "ppcParkingMode"
        STOP_REASON = "CoreStopReason"
        PARKING_SCENARIO = "ParkingScenario"
        TARGET_POSE = "TargetPose0_type"
        VALID_PB = "NumberOfValidParkingBoxes"
        GEAR = "GearReqFusion"
        DRIVING_DIRECTION = "DrivingDirection"
        TIME = "Time"
        HEAD_SCREEN = "HMIUnitScreen"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = [
            "ADC5xx_Device",
            "ADAS_CAN",
            "MTA_ADC5",
        ]

        self._properties = {
            # self.Columns.sg_time: ".TimeStamp",
            self.Columns.VALID_SEGMENTS: [
                "ADC5xx_Device.TRJPLA_DATA.TrjPlaTrajPlanVisuPort.numValidSegments",
                "MTA_ADC5.MF_TRJPLA_DATA.trjplaVisuPort.numValidSegments",
            ],
            self.Columns.PARKING_MODE: [
                "ADC5xx_Device.EM_DATA.EmPSMDebugPort.stateVarPPC_nu",
                "MTA_ADC5.IU_PAR230_DATA.PsmDebugPort.stateVarPPC_nu",
            ],
            self.Columns.STOP_REASON: [
                "ADC5xx_Device.EM_DATA.EmPARRKSMCoreStatusPort.coreStopReason_nu",
                "MTA_ADC5.MF_PARKSM_CORE_DATA.parksmCoreStatusPort.coreStopReason_nu",
            ],
            self.Columns.PARKING_SCENARIO: [
                "ADC5xx_Device.EM_DATA.EmApParkingBoxPort.parkingBoxes[0].parkingScenario_nu",
                "MTA_ADC5.SI_DATA.m_parkingBoxesPort.parkingBoxes[0].parkingScenario_nu",
            ],
            self.Columns.TARGET_POSE: [
                "ADC5xx_Device.TRJPLA_DATA.TrjPlaTargetPosesPort.targetPoses[0].type",
                "MTA_ADC5.MF_TRJPLA_DATA.targetPoses.targetPoses[0].type",
            ],
            self.Columns.VALID_PB: [
                "ADC5xx_Device.EM_DATA.EmApParkingBoxPort.numValidParkingBoxes_nu",
                "MTA_ADC5.SI_DATA.m_parkingBoxesPort.numValidParkingBoxes_nu",
            ],
            self.Columns.GEAR: [
                "ADC5xx_Device.VD_DATA.IuGearboxCtrlRequestPort.gearReq_nu",
                "MTA_ADC5.MF_TRJCTL_DATA.GearboxCtrlRequestPort.gearReq_nu",
            ],
            self.Columns.DRIVING_DIRECTION: [
                "ADC5xx_Device.EM_DATA.EmHMIGeneralInputPort.general.drivingDirection_nu",
                "MTA_ADC5.IU_PAR230_DATA.HmiGeneralInputPort.general.drivingDirection_nu",
            ],
            self.Columns.TIME: [
                "ADC5xx_Device.EM_DATA.EmHeadUnitVisualizationPort.sSigHeader.uiTimeStamp",
                "MTA_ADC5.IU_PAR230_DATA.HeadUnitVisualizationPort.sSigHeader.uiTimeStamp",
            ],
            self.Columns.HEAD_SCREEN: [
                ".EM_DATA.EmHeadUnitVisualizationPort.screen_nu",
                "MTA_ADC5.IU_PAR230_DATA.HeadUnitVisualizationPort.screen_nu",
            ],
        }


example_obj = Signals()
verdict_obj = StoreStepResults()


@teststep_definition(
    step_number=1,
    name="PERP/ANG FORWARD",
    description=("Verify the average  maneuvering time for perp/ang forward parking type."),
    expected_result=ExpectedResult(
        operator=RelationOperator.LESS,
        numerator=65,
        unit="s",
        aggregate_function=AggregateFunction.MEAN,
    ),
)
@register_signals(EXAMPLE, Signals)
class AvgNbTimePerpAngF(TestStep):
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

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        self.result.details.update(
            {
                "Plots": [],
                "software_version_file": "",
                "Km_driven": 0,
                "driven_time": 0,
                "Plot_titles": [],
                "Remarks": [],
                "file_name": os.path.basename(self.artifacts[0].file_path),
            }
        )

        df = self.readers[EXAMPLE]
        df[Signals.Columns.TIMESTAMP] = df.index
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        # Defining signal variables for signal handling

        sg_core_stop_reason = "CoreStopReason"
        sg_screen = "HMIUnitScreen"

        signal_summary = {}

        usecase_const = False
        usecases_dict = constants.ParkingUseCases.parking_usecase_id
        for key, value in usecases_dict.items():
            if self.result.details["file_name"].find(f"{key}") != -1:
                if value.lower().find("forward") != -1 and (
                    value.lower().find("perpendicular") != -1 or value.lower().find("angular") != -1
                ):
                    usecase_const = True

        try:
            # Converting microseconds to seconds
            df[Signals.Columns.TIMESTAMP] = df[Signals.Columns.TIMESTAMP] / constants.GeneralConstants.US_IN_S
            # Converting epoch time to seconds passed
            df[Signals.Columns.TIMESTAMP] = df[Signals.Columns.TIMESTAMP] - df[Signals.Columns.TIMESTAMP].iat[0]
            global total_time
            headscreen_nu = df[Signals.Columns.HEAD_SCREEN]

            # Get the number of seconds that have passed from frame to frame
            seconds = df[Signals.Columns.TIMESTAMP].rolling(2).apply(lambda x: x[1] - x[0], raw=True)

            msk_prk_selection = headscreen_nu == constants.HeadUnitVisuPortScreenVal.PARKING_SPACE_SELECTION
            msk_maneuver_active = headscreen_nu == constants.HeadUnitVisuPortScreenVal.MANEUVER_ACTIVE
            msk_maneuver_fnsh = headscreen_nu == constants.HeadUnitVisuPortScreenVal.MANEUVER_FINISHED

            headscreen_nu_mask = msk_prk_selection | msk_maneuver_active | msk_maneuver_fnsh.shift(1).fillna(False)

            headscreen_nu_filtered = pd.concat([seconds, headscreen_nu], axis=1)

            headscreen_nu_filtered = headscreen_nu_filtered[headscreen_nu_mask]
            seconds_while_parking = headscreen_nu_filtered[Signals.Columns.TIMESTAMP].sum()
            total_time = round(seconds_while_parking, 2)
            stop_reason_mask = df[sg_core_stop_reason] == constants.StrokeConstants.PARKING_SUCCESS_VALUE

            verdict_obj.park_verdict_1 = "Success" if any(stop_reason_mask) else "Failed"

            if any(stop_reason_mask) and usecase_const:
                evaluation1 = f"The measurement parked successfully in {total_time}"
                self.result.measured_result = Result(total_time)
                verdict_obj.step_1 = fc.PASS
            else:
                evaluation1 = (
                    "The parking failed to finish."
                    if usecase_const
                    else "The measurement could not be evaluated due to wrong parking scenario."
                )
                verdict_obj.step_1 = fc.NOT_ASSESSED
                self.result.measured_result = DATA_NOK if usecase_const else NAN

            signal_summary[Signals.Columns.STOP_REASON] = evaluation1
            remark = " "
            self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)

            if usecase_const:
                plot_titles.append("")
                plots.append(self.sig_sum)
                remarks.append("")
                self.fig = go.Figure()
                self.fig.add_trace(
                    go.Scatter(
                        x=df[Signals.Columns.TIMESTAMP],
                        y=df[sg_core_stop_reason],
                        mode="lines",
                        name=Signals.Columns.STOP_REASON,
                    )
                )
                self.fig.add_trace(
                    go.Scatter(
                        x=df[Signals.Columns.TIMESTAMP],
                        y=df[sg_screen],
                        mode="lines",
                        name=Signals.Columns.HEAD_SCREEN,
                    )
                )

                self.fig.layout = go.Layout(
                    yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]"
                )
                self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

                plot_titles.append("")
                plots.append(self.fig)
                remarks.append("")

        except Exception as err:
            print(str(err))
            # write_log_message(f"Test failed, the following signal is missing:{str(err)}", "error", LOGGER)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")

        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)
        if usecase_const:
            color = "#28a745" if verdict_obj.step_1 == fc.PASS else "rgb(129, 133, 137)"
            park_status = verdict_obj.check_parking_success()
            additional_results_dict = {
                "Verdict": {"value": verdict_obj.step_1.title(), "color": color},
                "Measured result [seconds]": {"value": total_time},
                "Parking finished": {"value": f"{park_status}"},
                # "Parking scenario": {"value": f"{park_status}"}
            }
            self.result.details["Additional_results_ts"] = additional_results_dict


@teststep_definition(
    step_number=2,
    name="PERP/ANG BACKWARD",
    description=("Verify the average  maneuvering time for perp/ang backward parking type."),
    expected_result=ExpectedResult(
        operator=RelationOperator.LESS,
        numerator=65,
        unit="s",
        aggregate_function=AggregateFunction.MEAN,
    ),
)
@register_signals(EXAMPLE, Signals)
class AvgNbTimePerpAngB(TestStep):
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

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
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

        df = self.readers[EXAMPLE]
        df[Signals.Columns.TIMESTAMP] = df.index
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        # Defining signal variables for signal handling

        sg_core_stop_reason = "CoreStopReason"
        sg_screen = "HMIUnitScreen"

        # Converting microseconds to seconds
        df[Signals.Columns.TIMESTAMP] = df[Signals.Columns.TIMESTAMP] / constants.GeneralConstants.US_IN_S
        # Converting epoch time to seconds passed
        df[Signals.Columns.TIME] = df[Signals.Columns.TIMESTAMP] - df[Signals.Columns.TIMESTAMP].iat[0]

        signal_summary = {}
        usecase_const = False
        usecases_dict = constants.ParkingUseCases.parking_usecase_id
        for key, value in usecases_dict.items():
            if self.result.details["file_name"].find(f"{key}") != -1:
                if value.lower().find("backward") != -1 and (
                    value.lower().find("perpendicular") != -1 or value.lower().find("angular") != -1
                ):
                    usecase_const = True

        try:
            stop_reason_mask = df[sg_core_stop_reason] == constants.StrokeConstants.PARKING_SUCCESS_VALUE

            verdict_obj.park_verdict_2 = "Success" if any(stop_reason_mask) else "Failed"
            if any(stop_reason_mask) and usecase_const:
                evaluation1 = f"The measurement parked successfully in {total_time}"
                self.result.measured_result = Result(total_time)
                verdict_obj.step_2 = fc.PASS
            else:
                evaluation1 = (
                    "The parking failed to finish."
                    if usecase_const
                    else "The measurement could not be evaluated due to wrong parking scenario."
                )
                verdict_obj.step_2 = fc.NOT_ASSESSED
                self.result.measured_result = DATA_NOK if usecase_const else NAN

            signal_summary[Signals.Columns.STOP_REASON] = evaluation1
            remark = " "
            self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
            if usecase_const:
                plot_titles.append("")
                plots.append(self.sig_sum)
                remarks.append("")

                self.fig = go.Figure()

                self.fig.add_trace(
                    go.Scatter(
                        x=df[Signals.Columns.TIMESTAMP],
                        y=df[sg_core_stop_reason],
                        mode="lines",
                        name=Signals.Columns.STOP_REASON,
                    )
                )

                self.fig.add_trace(
                    go.Scatter(
                        x=df[Signals.Columns.TIMESTAMP],
                        y=df[sg_screen],
                        mode="lines",
                        name=Signals.Columns.HEAD_SCREEN,
                    )
                )

                self.fig.layout = go.Layout(
                    yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]"
                )
                self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

                plot_titles.append("")
                plots.append(self.fig)
                remarks.append("")

        except Exception as err:
            print(str(err))
            # write_log_message(f"Test failed, the following signal is missing:{str(err)}", "error", LOGGER)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")

        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)
        if usecase_const:
            color = "#28a745" if verdict_obj.step_2 == fc.PASS else "rgb(129, 133, 137)"
            park_status = verdict_obj.check_parking_success()
            additional_results_dict = {
                "Verdict": {"value": verdict_obj.step_2.title(), "color": color},
                "Measured result [seconds]": {"value": total_time},
                "Parking finished": {"value": f"{park_status}"},
                # "Parking scenario": {"value": f"{park_status}"}
            }
            self.result.details["Additional_results_ts"] = additional_results_dict


@teststep_definition(
    step_number=3,
    name="PAR",
    description=("Verify the average  maneuvering time for parallel parking type."),
    expected_result=ExpectedResult(
        operator=RelationOperator.LESS,
        numerator=65,
        unit="s",
        aggregate_function=AggregateFunction.MEAN,
    ),
)
@register_signals(EXAMPLE, Signals)
class AvgNbTimePar(TestStep):
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

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        df = self.readers[EXAMPLE]
        df[Signals.Columns.TIMESTAMP] = df.index
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        # Defining signal variables for signal handling

        sg_core_stop_reason = "CoreStopReason"
        sg_screen = "HMIUnitScreen"

        signal_summary = {}
        usecase_const = False
        usecases_dict = constants.ParkingUseCases.parking_usecase_id
        for key, value in usecases_dict.items():
            if self.result.details["file_name"].find(f"{key}") != -1:
                if value.lower().find("parallel") != -1 and (
                    value.lower().find("perpendicular") == -1 and value.lower().find("angular") == -1
                ):
                    usecase_const = True

        try:
            # Converting microseconds to seconds
            df[Signals.Columns.TIMESTAMP] = df[Signals.Columns.TIMESTAMP] / constants.GeneralConstants.US_IN_S
            # Converting epoch TIMESTAMP to seconds passed
            df[Signals.Columns.TIMESTAMP] = df[Signals.Columns.TIMESTAMP] - df[Signals.Columns.TIMESTAMP].iat[0]
            stop_reason_mask = df[sg_core_stop_reason] == constants.StrokeConstants.PARKING_SUCCESS_VALUE

            if any(stop_reason_mask) and usecase_const:
                evaluation1 = f"The measurement parked successfully in {total_time}"
                self.result.measured_result = Result(total_time)
                verdict_obj.step_3 = fc.PASS

            else:
                evaluation1 = (
                    "The parking failed to finish."
                    if usecase_const
                    else "The measurement could not be evaluated due to wrong parking scenario."
                )
                verdict_obj.step_3 = fc.NOT_ASSESSED
                self.result.measured_result = DATA_NOK if usecase_const else NAN

            signal_summary[Signals.Columns.STOP_REASON] = evaluation1
            remark = " "
            self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)

            if usecase_const:

                plot_titles.append("")
                plots.append(self.sig_sum)
                remarks.append("")
                self.fig = go.Figure()

                self.fig.add_trace(
                    go.Scatter(
                        x=df[Signals.Columns.TIMESTAMP],
                        y=df[sg_core_stop_reason],
                        mode="lines",
                        name=Signals.Columns.STOP_REASON,
                    )
                )

                self.fig.add_trace(
                    go.Scatter(
                        x=df[Signals.Columns.TIMESTAMP],
                        y=df[sg_screen],
                        mode="lines",
                        name=Signals.Columns.HEAD_SCREEN,
                    )
                )

                self.fig.layout = go.Layout(
                    yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]"
                )
                self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

                plot_titles.append("")
                plots.append(self.fig)
                remarks.append("")

            color = "#28a745" if verdict_obj.step_3 == fc.PASS else "rgb(129, 133, 137)"
            park_status = verdict_obj.check_parking_success()
            if usecase_const:
                additional_results_dict = {
                    "Verdict": {"value": verdict_obj.step_3.title(), "color": color},
                    "Measured result [seconds]": {"value": total_time},
                    "Parking finished": {"value": f"{park_status}"},
                    # "Parking scenario": {"value": f"{park_status}"}
                }
                self.result.details["Additional_results_ts"] = additional_results_dict

        except Exception as err:
            print(str(err))
            # write_log_message(f"Test failed, the following signal is missing:{str(err)}", "error", LOGGER)

            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")

        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@verifies("1028792")
@testcase_definition(
    name="Average maneuvering time [s]",
    description=("Verify the average maneuvering time for specific parking scenarios. "),
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_zX9IAehNEe2m7JKTm3pqog?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
class AvgTime(TestCase):
    """Test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AvgNbTimePerpAngF,
            AvgNbTimePerpAngB,
            AvgNbTimePar,
        ]
