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
import pl_parking.PLP.MF.UI_MANAGER.UI_Manager_helper as ui_helper
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport

__author__ = "Pinzariu George-Claudiu <uif94738>"
__copyright__ = "2020-2024, Continental AG"
__version__ = "0.1.0"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "UI_MANAGER_2688890"


flag = {0: "FALSE", 1: "TRUE"}


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"

        TONH_USER_INTERFACE = "TONH_USER_INTERFACE"
        HMI_OUTPUT_USER_ACTION = "HMI_OUTPUT_USER_ACTION"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.HMI_OUTPUT_USER_ACTION: "AP.hmiOutputPort.userActionHeadUnit_nu",
            self.Columns.TONH_USER_INTERFACE: "AP.TONHUserInteractionPort.tonhUserActionHeadUnit_nu",
            self.Columns.TIME: [
                "Time",
                "Another version of signal",
            ],
        }


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="Status of acoustical warning- ON/OFF",  # this would be shown as a test step name in html report
    description=(
        "HMIManager shall arbitrate the information that comes from pressing the button about audio warning and PDWCore (status of acoustical warning- ON/OFF)."
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
            tone_h_series = signals[Signals.Columns.TONH_USER_INTERFACE]
            hmi_series = signals[Signals.Columns.HMI_OUTPUT_USER_ACTION]

            hmi_series_events = hmi_series.rolling(2).apply(
                lambda x: x[1] != x[0] and x[1] == constants.UiManager.UserAction.TAP_ON_MUTE, raw=True
            )
            transition_events = []
            transition_message = []
            timestamp_pdw_events = [row for row, val in hmi_series_events.items() if val == 1]

            if timestamp_pdw_events:
                for ts in timestamp_pdw_events:
                    # pdw_sys_state = pdc_series.loc[ts]
                    T1 = list(signals.index).index(ts)
                    sub_series = tone_h_series.iloc[T1 : T1 + max_delay + 1]
                    if not sub_series[sub_series == constants.UiManager.TONHUserActionHeadUnit.TONH_TAP_ON_MUTE].empty:
                        # transition_events.append(True)

                        end_idx = sub_series[
                            sub_series == constants.UiManager.TONHUserActionHeadUnit.TONH_TAP_ON_MUTE
                        ].first_valid_index()
                        end_idx = list(signals.index).index(end_idx)

                        it_took = (end_idx - T1) * 10
                        eval_text = f"HMIManager did forward the input, after {it_took} ms, within {max_delay * 10} ms of user input"
                        # transition_message.append(
                        #     f"HMIManager did forward the input, after {it_took} ms, within {max_delay * 10} ms of user input."
                        # )
                        sub_series_t1 = hmi_series.iloc[T1:]
                        T1_end_idx = sub_series_t1[
                            sub_series_t1 == constants.UiManager.UserAction.NO_USER_ACTION
                        ].first_valid_index()
                        T1_end_idx = list(signals.index).index(T1_end_idx)
                        sub_series = tone_h_series.iloc[T1_end_idx : T1_end_idx + max_delay + 1]
                        if not sub_series[
                            sub_series == constants.UiManager.TONHUserActionHeadUnit.TONH_NO_USER_ACTION
                        ].empty:
                            transition_events.append(True)
                            eval_text += "."
                        else:
                            transition_events.append(False)
                            eval_text += f", but it did not return to {constants.UiManager.TONHUserActionHeadUnit.get_variable_name(constants.UiManager.TONHUserActionHeadUnit.TONH_NO_USER_ACTION)}, within {max_delay * 10} ms."
                    else:
                        transition_events.append(False)
                        eval_text = f"HMIManager did not forward the input, within {max_delay * 10} ms of user input."
                    transition_message.append(eval_text)
                signal_summary = {
                    "Timestamp [s]": {idx: ap_time.loc[x] for idx, x in enumerate(timestamp_pdw_events)},
                    "Evaluation": {idx: x for idx, x in enumerate(transition_message)},
                    "Verdict": {idx: ui_helper.get_result_color(x) for idx, x in enumerate(transition_events)},
                }
            else:
                signal_summary = {
                    "Timestamp [s]": {"0": "-"},
                    "Evaluation": {"0": "No user input detected."},
                    "Verdict": {"0": f"{ui_helper.get_result_color('NOT ASSESSED')}"},
                }
            if all(transition_events) and len(transition_events) > 0:
                self.result.measured_result = TRUE
                self.test_result = fc.PASS
            elif all(tone_h_series == hmi_series):
                self.result.measured_result = TRUE
                self.test_result = fc.PASS
            elif any(timestamp_pdw_events):
                self.result.measured_result = FALSE
                self.test_result = fc.FAIL
            else:
                self.result.measured_result = DATA_NOK
                self.test_result = fc.INPUT_MISSING
            table_title = (
                "HMIManager shall forward the input about the selection of the acoustical warning (turn ON or OFF)"
            )
            remark = f"<b>Signals evaluated:</b><br><br>\
                       Input: <b>{signals_obj._properties[Signals.Columns.HMI_OUTPUT_USER_ACTION]}</b> == {constants.UiManager.UserAction.TAP_ON_MUTE}<br> \
                       Output: <b>{signals_obj._properties[Signals.Columns.TONH_USER_INTERFACE]} == {constants.UiManager.TONHUserActionHeadUnit.TONH_TAP_ON_MUTE}</b>"

            signal_summary = fh.build_html_table(pd.DataFrame(signal_summary), remark, table_title)
            plots.append(signal_summary)

            ap_time = ap_time.values.tolist()
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=signals[Signals.Columns.HMI_OUTPUT_USER_ACTION].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.HMI_OUTPUT_USER_ACTION],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>"
                        f"HMI USER OUTPUT:<br>"
                        f"{constants.UiManager.UserAction.get_variable_name(state)}"
                        for idx, state in enumerate(signals[Signals.Columns.HMI_OUTPUT_USER_ACTION].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=signals[Signals.Columns.TONH_USER_INTERFACE].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.TONH_USER_INTERFACE],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>"
                        f"PDC User Action:<br>"
                        f"{constants.UiManager.PDCUserActionHeadUnit.get_variable_name(state)}"
                        for idx, state in enumerate(signals[Signals.Columns.TONH_USER_INTERFACE].values.tolist())
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
    name="UI_MANAGER_2688890",
    description="HMIManager shall arbitrate the information that comes from pressing the button about audio warning and PDWCore (status of acoustical warning- ON/OFF).",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_ZdqA0HpsEe-9FrFCDLx05w&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_ns_CwE4gEe6M5-WQsF_-tQ&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class TestCaseFT(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepUI_MANAGER]
