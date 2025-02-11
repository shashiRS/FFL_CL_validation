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
ALIAS = "UI_MANAGER_2688802"


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"

        warningBody_nu_hmi = "warningBody_nu"
        warningObject_nu_hmi = "warningObject_nu"
        warningWheel_nu_hmi = "warningWheel_nu"

        warningBody_nu_lsca = "warningBody_nu"
        warningObject_nu_lsca = "warningObject_nu"
        warningWheel_nu_lsca = "warningWheel_nu"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.TIME: [
                "Time",
                "Another version of signal",
            ],
            self.Columns.warningBody_nu_hmi: "AP.hmiInputPort.lscaWarnings.warningBody_nu",
            self.Columns.warningObject_nu_hmi: "AP.hmiInputPort.lscaWarnings.warningObject_nu",
            self.Columns.warningWheel_nu_hmi: "AP.hmiInputPort.lscaWarnings.warningWheel_nu",
            self.Columns.warningBody_nu_lsca: "AP.lscaHMIPort.warningBody",
            self.Columns.warningObject_nu_lsca: "AP.lscaHMIPort.warningObject",
            self.Columns.warningWheel_nu_lsca: "AP.lscaHMIPort.warningWheel",
        }


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="Inform driver about the brake",  # this would be shown as a test step name in html report
    description=(
        "The HMIHandler shall inform the ego vehicle driver about the brake activated by the system."
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

            warning_body_lsca = signals[Signals.Columns.warningBody_nu_lsca]
            warning_object_lsca = signals[Signals.Columns.warningObject_nu_lsca]
            warning_wheel_lsca = signals[Signals.Columns.warningWheel_nu_lsca]

            warning_body_hmi = signals[Signals.Columns.warningBody_nu_hmi]
            warning_object_hmi = signals[Signals.Columns.warningObject_nu_hmi]
            warning_wheel_hmi = signals[Signals.Columns.warningWheel_nu_hmi]
            to_be_evaluated = {
                "warning Body": (warning_body_lsca, warning_body_hmi),
                "warning Object": (warning_object_lsca, warning_object_hmi),
                "warning Wheel": (warning_wheel_lsca, warning_wheel_hmi),
            }
            eval_template = "The HMIHandler {verduct} inform the ego vehicle driver about the brake  after {it_took} ms, within {max_delay_ms} ms of LSCA event."
            overall_events = []
            for key, (lsca_series, hmi_series) in to_be_evaluated.items():

                lsca_series_events = lsca_series.rolling(2).apply(
                    lambda x: x[1] != x[0],
                    raw=True,
                )
                lsca_series.values.tolist()
                transition_message = []
                transition_events = []
                timestamp_lsca_series_events = [row for row, val in lsca_series_events.items() if val == 1]

                if timestamp_lsca_series_events:
                    for ts in timestamp_lsca_series_events:
                        lsca_state = lsca_series.loc[ts]
                        T1 = list(signals.index).index(ts)
                        sub_series = hmi_series.iloc[T1 : T1 + max_delay + 1]
                        if not sub_series[sub_series == lsca_state].empty:
                            transition_events.append(True)

                            end_idx = sub_series[sub_series == lsca_state].first_valid_index()
                            end_idx = list(signals.index).index(end_idx)

                            it_took = (end_idx - T1) * 10

                            transition_message.append(
                                f"{eval_template.format(verduct='did', it_took=it_took, max_delay_ms=max_delay * 10)}"
                            )
                        else:
                            transition_events.append(False)

                            transition_message.append(
                                f"{eval_template.format(verduct='did not', it_took='N/A', max_delay_ms=max_delay * 10)}"
                            )

                    signal_summary = {
                        "Timestamp [s]": {idx: ap_time.loc[x] for idx, x in enumerate(timestamp_lsca_series_events)},
                        "Evaluation": {idx: x for idx, x in enumerate(transition_message)},
                        "Verdict": {idx: ui_helper.get_result_color(x) for idx, x in enumerate(transition_events)},
                    }
                else:
                    signal_summary = {
                        "Timestamp [s]": {"0": "N/A"},
                        "Evaluation": {"0": f"No {key.title()} events detected"},
                        "Verdict": {"0": f"{ui_helper.get_result_color('NOT ASSESSED')}"},
                    }
                table_title = f"Check if the HMI Handler informs the driver about the current {key.title()} information"
                overall_events.append(transition_events)
                signal_summary = fh.build_html_table(pd.DataFrame(signal_summary), table_title=table_title)
                plots.append(signal_summary)
            final_verdicts = []
            for _, events in enumerate(overall_events):
                for event in events:
                    final_verdicts.append(event)
            if len(final_verdicts) == 0:
                self.result.measured_result = DATA_NOK
                self.test_result = fc.INPUT_MISSING
            elif all(final_verdicts):
                self.result.measured_result = TRUE
                self.test_result = fc.PASS
            else:
                self.result.measured_result = FALSE
                self.test_result = fc.FAIL

            ap_time = ap_time.values.tolist()
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=warning_body_hmi.values.tolist(),
                    mode="lines",
                    line=dict(color="blue"),
                    name=signals_obj._properties[Signals.Columns.warningBody_nu_hmi],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=warning_object_hmi.values.tolist(),
                    mode="lines",
                    line=dict(color="blue"),
                    name=signals_obj._properties[Signals.Columns.warningObject_nu_hmi],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=warning_wheel_hmi.values.tolist(),
                    mode="lines",
                    line=dict(color="blue"),
                    name=signals_obj._properties[Signals.Columns.warningWheel_nu_hmi],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=warning_body_lsca.values.tolist(),
                    mode="lines",
                    line=dict(color="red"),
                    name=signals_obj._properties[Signals.Columns.warningBody_nu_lsca],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=warning_object_lsca.values.tolist(),
                    mode="lines",
                    line=dict(color="red"),
                    name=signals_obj._properties[Signals.Columns.warningObject_nu_lsca],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=warning_wheel_lsca.values.tolist(),
                    mode="lines",
                    line=dict(color="red"),
                    name=signals_obj._properties[Signals.Columns.warningWheel_nu_lsca],
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
    name="UI_MANAGER_2688802",
    description="The HMIHandler shall inform the ego vehicle driver about the brake that is made by the system.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_ZdN78npsEe-9FrFCDLx05w&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_ns_CwE4gEe6M5-WQsF_-tQ&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class TestCaseFT(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepUI_MANAGER]
