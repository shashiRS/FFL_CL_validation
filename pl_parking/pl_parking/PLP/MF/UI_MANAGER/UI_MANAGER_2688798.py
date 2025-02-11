"""Example functional test"""  # this is a required docstring

"""import libraries"""
import logging
import os
import sys

import numpy as np
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
ALIAS = "UI_MANAGER_2688798"


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "Time"
        LSCA_ACTIVATE = "LSCA Activate"
        HMI_OUTPUT_SCREEN = "HMI Output Screen"
        HMI_OUTPUT_MESSAGE = "HMI Output Message"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.LSCA_ACTIVATE: "AP.lscaHMIPort.activateBrakeInterventionScreen_nu",
            self.Columns.HMI_OUTPUT_MESSAGE: "AP.headUnitVisualizationPort.message_nu",
            self.Columns.HMI_OUTPUT_SCREEN: "AP.headUnitVisualizationPort.screen_nu",
            self.Columns.TIME: "Time",
        }


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="Inform Instrument Cluster Display about iimminent collision",  # this would be shown as a test step name in html report
    description=(" "),  # this would be shown as a test step description in html report
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
            delay = 1
            max_delay = 6

            T1 = None
            self.test_result = fc.INPUT_MISSING  # Result
            self.result.measured_result = DATA_NOK  # Initializing the result with data nok
            # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
            plots = []

            signal_summary = {}  # Initializing the dictionary with data for final evaluation table

            signals = self.readers[ALIAS]
            signals[Signals.Columns.TIMESTAMP] = signals.index
            bool_eval_screen = False
            bool_eval_message = False
            ap_time = round(signals[Signals.Columns.TIME], 3)
            lsca_activate = signals[Signals.Columns.LSCA_ACTIVATE]
            hmi_output_screen = signals[Signals.Columns.HMI_OUTPUT_SCREEN]
            hmi_output_message = signals[Signals.Columns.HMI_OUTPUT_MESSAGE]

            if np.any(lsca_activate == constants.LscaConstants.ACTIVATE):
                T1 = np.argmax(lsca_activate == constants.LscaConstants.ACTIVATE)

            if T1 is not None:

                sub_series = hmi_output_screen.iloc[T1 : T1 + max_delay + 1]
                if not sub_series[sub_series == constants.UiManager.HmiScreen.MANEUVER_INTERRUPTED].empty:
                    bool_eval_screen = True

                    screen_idx = sub_series[
                        sub_series == constants.UiManager.HmiScreen.MANEUVER_INTERRUPTED
                    ].first_valid_index()
                    screen_idx = list(signals.index).index(screen_idx)

                    it_took = (screen_idx - T1) * 10

                    eval_screen = f"Head Unit Screen was set to  \
                {constants.UiManager.HmiScreen.get_variable_name(hmi_output_screen.iloc[screen_idx])} after {it_took} ms, within {max_delay * 10} ms of LSCA activation."
                else:
                    eval_screen = f"Head Unit Screen was not set to \
                {constants.UiManager.HmiScreen.get_variable_name(constants.UiManager.HmiScreen.MANEUVER_INTERRUPTED)} within {max_delay * 10} ms of LSCA activation."

                # Evvaluation for HMI Output Message

                sub_series = hmi_output_message.iloc[T1 : T1 + max_delay + 1]
                if not sub_series[sub_series == constants.UiManager.HmiMessage.VERY_CLOSE_TO_OBJECTS].empty:
                    bool_eval_message = True
                    message_idx = sub_series[
                        sub_series == constants.UiManager.HmiMessage.VERY_CLOSE_TO_OBJECTS
                    ].first_valid_index()
                    message_idx = list(signals.index).index(message_idx)

                    it_took = (message_idx - T1) * 10
                    # it_took = t1_epoch - lactrl_t1_idx
                    eval_message = f"Head Unit Message was set to  \
                {constants.UiManager.HmiMessage.get_variable_name(hmi_output_message.iloc[screen_idx])} after {it_took} ms, within {max_delay*10} ms of LSCA activation."
                else:
                    eval_message = f"Head Unit Message was not set to \
                {constants.UiManager.HmiMessage.get_variable_name(constants.UiManager.HmiMessage.VERY_CLOSE_TO_OBJECTS)}, within {max_delay*10} ms of LSCA activation."

            if True:
                signal_summary = {
                    "Condition": {
                        "0": f"When the state of {signals_obj._properties[Signals.Columns.LSCA_ACTIVATE]} \
                is set to {constants.LscaConstants.get_variable_name(constants.LscaConstants.ACTIVATE)}, the signal \
                {signals_obj._properties[Signals.Columns.HMI_OUTPUT_MESSAGE]} should be set to {constants.UiManager.HmiMessage.get_variable_name(constants.UiManager.HmiMessage.VERY_CLOSE_TO_OBJECTS)}.",
                        "1": f"When the state of {signals_obj._properties[Signals.Columns.LSCA_ACTIVATE]} \
                is set to {constants.LscaConstants.get_variable_name(constants.LscaConstants.ACTIVATE)}, the signal \
                {signals_obj._properties[Signals.Columns.HMI_OUTPUT_SCREEN]} should be set to {constants.UiManager.HmiScreen.get_variable_name(constants.UiManager.HmiScreen.MANEUVER_INTERRUPTED)}.",
                    },
                    "Evaluation": {
                        "0": eval_message if T1 else "NOT ASSESSED, LSCA not activated.",
                        "1": eval_screen if T1 else "NOT ASSESSED, LSCA not activated.",
                    },
                    "Verdict": {
                        "0": (
                            ui_helper.get_result_color(bool_eval_message)
                            if T1
                            else ui_helper.get_result_color("NOT ASSESSED")
                        ),
                        "1": (
                            ui_helper.get_result_color(bool_eval_screen)
                            if T1
                            else ui_helper.get_result_color("NOT ASSESSED")
                        ),
                    },
                }

            if bool_eval_screen and bool_eval_message:
                self.result.measured_result = TRUE
                self.test_result = fc.PASS
            elif T1 is None:
                self.result.measured_result = DATA_NOK
                self.test_result = fc.NOT_ASSESSED
            else:
                self.result.measured_result = FALSE
                self.test_result = fc.FAIL
            T1 = f"{ap_time.iloc[T1]} s" if T1 is not None else "NOT ASSESSED"
            remark = f"<b>Legend:</b><br><br>\
                        delay = {delay/100} s <br>\
                        T1 :<b>{signals_obj._properties[Signals.Columns.LSCA_ACTIVATE]} == {constants.LscaConstants.get_variable_name(constants.LscaConstants.ACTIVATE)}</b> ({T1})<br>\
                        <br>\
                        <b>Signals evaluated:</b><br><br>\
                        {signals_obj._properties[Signals.Columns.HMI_OUTPUT_MESSAGE]}<br>\
                        {signals_obj._properties[Signals.Columns.HMI_OUTPUT_SCREEN]}<br>"

            signal_summary = fh.build_html_table(pd.DataFrame(signal_summary), remark)
            plots.append(signal_summary)

            ap_time = ap_time.values.tolist()

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=signals[Signals.Columns.HMI_OUTPUT_MESSAGE].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.HMI_OUTPUT_MESSAGE],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>"
                        f"HMI Output Message:<br>"
                        f"{constants.UiManager.HmiMessage.get_variable_name(state)}"
                        for idx, state in enumerate(signals[Signals.Columns.HMI_OUTPUT_MESSAGE].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=signals[Signals.Columns.HMI_OUTPUT_SCREEN].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.HMI_OUTPUT_SCREEN],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>"
                        f"HMI Output Screen:<br>"
                        f"{constants.UiManager.HmiScreen.get_variable_name(state)}"
                        for idx, state in enumerate(signals[Signals.Columns.HMI_OUTPUT_SCREEN].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=signals[Signals.Columns.LSCA_ACTIVATE].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.LSCA_ACTIVATE],
                    # text=[f"{constants.LscaConstants.get_variable_name(value)}" for value in lsca_eba.values.tolist())],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>"
                        f"LSCA HMI PORT:<br>"
                        f"{constants.LscaConstants.get_variable_name(state)}"
                        for idx, state in enumerate(signals[Signals.Columns.LSCA_ACTIVATE].values.tolist())
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
    name="UI_MANAGER_2688798",
    description="The HMIManager shall give the input to the InstrumentClusterDisplay about an imminent collision.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_ZdMGwnpsEe-9FrFCDLx05w&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_ns_CwE4gEe6M5-WQsF_-tQ&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class TestCaseFT(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepUI_MANAGER]
