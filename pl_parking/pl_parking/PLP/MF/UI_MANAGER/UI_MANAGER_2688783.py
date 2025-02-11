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
import pl_parking.PLP.MF.UI_MANAGER.UI_Manager_helper as ui_helper
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport

__author__ = "Pinzariu George-Claudiu <uif94738>"
__copyright__ = "2020-2024, Continental AG"
__version__ = "0.1.0"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ALIAS = "UI_MANAGER_2688783"


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"

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


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="Inform driver about PDW state",  # this would be shown as a test step name in html report
    description=(
        "HMIHandler shall inform the ego vehicle driver of the current system state of the PDW function."
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepUI_MANAGER(TestStep):
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
            max_delay = 6

            T1 = None

            self.test_result = fc.INPUT_MISSING  # Result
            self.result.measured_result = DATA_NOK  # Initializing the result with data nok

            plots = []

            signal_summary = {}  # Initializing the dictionary with data for final evaluation table

            signals = self.readers[ALIAS]
            signals[Signals.Columns.TIMESTAMP] = signals.index
            ap_time = round(signals[Signals.Columns.TIME], 3)
            pdw_series = signals[Signals.Columns.PDWSYSTEMSTATE]
            hmi_series = signals[Signals.Columns.HMIINPUTPORTPDC]
            pdw_events = pdw_series.rolling(2).apply(lambda x: x[1] != x[0], raw=True)
            transition_events = []
            transition_message = []
            timestamp_pdw_events = [row for row, val in pdw_events.items() if val == 1]

            if timestamp_pdw_events:
                for ts in timestamp_pdw_events:
                    pdw_sys_state = pdw_series.loc[ts]
                    T1 = list(signals.index).index(ts)
                    sub_series = hmi_series.iloc[T1 : T1 + max_delay + 1]
                    if not sub_series[sub_series == pdw_sys_state].empty:
                        transition_events.append(True)

                        end_idx = sub_series[sub_series == pdw_sys_state].first_valid_index()
                        end_idx = list(signals.index).index(end_idx)

                        it_took = (end_idx - T1) * 10

                        transition_message.append(
                            f"HMI Handler informed the driver about the PDW System State:  \
                    {constants.UiManager.pdwSystemState.get_variable_name(pdw_sys_state)} after {it_took} ms, within {max_delay * 10} ms of PDW Transition."
                        )
                    else:
                        transition_events.append(False)
                        transition_message.append(
                            f"HMI Handler did not inform the driver about the PDW System State: \
                    {constants.UiManager.pdwSystemState.get_variable_name(pdw_sys_state)} within {max_delay * 10} ms of PDW Transition."
                        )

                signal_summary = {
                    "Timestamp [s]": {idx: ap_time.loc[x] for idx, x in enumerate(timestamp_pdw_events)},
                    "Evaluation": {idx: x for idx, x in enumerate(transition_message)},
                    "Verdict": {idx: ui_helper.get_result_color(x) for idx, x in enumerate(transition_events)},
                }
            else:
                signal_summary = {
                    "Timestamp [s]": "No PDW Transition",
                    "Evaluation": "No PDW Transition",
                    "Verdict": "No PDW Transition",
                }
            if all(transition_events):
                self.result.measured_result = TRUE
                self.test_result = fc.PASS
            elif any(timestamp_pdw_events):
                self.result.measured_result = FALSE
                self.test_result = fc.FAIL
            else:
                self.result.measured_result = DATA_NOK
                self.test_result = fc.INPUT_MISSING
            table_title = f"Check if the HMI Handler informs the driver about the PDW System State within {max_delay * 10} ms of PDW Transition"
            remark = f"<b>Signals evaluated:</b><br><br>\
                        <b>{signals_obj._properties[Signals.Columns.PDWSYSTEMSTATE]}</b> == <b>{signals_obj._properties[Signals.Columns.HMIINPUTPORTPDC]}</b>"

            signal_summary = fh.build_html_table(pd.DataFrame(signal_summary), remark, table_title)
            plots.append(signal_summary)

            ap_time = ap_time.values.tolist()
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=signals[Signals.Columns.HMIINPUTPORTPDC].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.HMIINPUTPORTPDC],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>"
                        f"HMI System State:<br>"
                        f"{constants.UiManager.pdwSystemState.get_variable_name(state)}"
                        for idx, state in enumerate(signals[Signals.Columns.HMIINPUTPORTPDC].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=signals[Signals.Columns.PDWSYSTEMSTATE].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.PDWSYSTEMSTATE],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>"
                        f"PDW System State:<br>"
                        f"{constants.UiManager.pdwSystemState.get_variable_name(state)}"
                        for idx, state in enumerate(signals[Signals.Columns.PDWSYSTEMSTATE].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )

            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plots.append(fig)
            # Add the plots in html page
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
    name="UI_MANAGER_2688783",
    description="HMIHandler shall inform the ego vehicle driver of the current system state of the PDW function.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_ZdHOQXpsEe-9FrFCDLx05w&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_ns_CwE4gEe6M5-WQsF_-tQ&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class TestCaseFT(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepUI_MANAGER]
