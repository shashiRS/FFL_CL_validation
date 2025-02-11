"""SWRT CNC TRAJPLA TestCases"""

import logging
import os
import sys

import pandas as pd
import plotly.graph_objects as go
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, MfSignals

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)


SIGNAL_DATA = "MF_RESET_COUNTER"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Trjpla Reset Counter",
    description="Verify TargetPosesPort.resetCounter == .resetOriginResult.resetCounter_nu",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TrjplaResetCounter(TestStep):
    """Defining teststep"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")
        # Update the details from the results page with the needed information
        # All the information from self.result.details is transferred to
        # report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # Create empty lists for titles, plots and remarks,if they are needed,
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        try:
            evaluation = ""
            read_data = self.readers[SIGNAL_DATA]
            signal_summary = {}
            signal_name = example_obj._properties
            self.result.measured_result = DATA_NOK  # Initializing the result with data nok
            # Create a lists which will contain test status  and test result for each frame
            # based on test condition.
            frame_test_status = []
            frame_test_result = []

            reset_counter = read_data["resetCounter"]
            reset_counter_nu = read_data["resetCounter_nu"]

            for idx in range(0, len(reset_counter)):
                if reset_counter.iloc[idx] == reset_counter_nu.iloc[idx]:
                    frame_test_result.append(True)
                    frame_test_status.append("Pass")
                else:
                    evaluation = " ".join(
                        f"Failed: {signal_name['resetCounter']} != {signal_name['resetCounter_nu']} at "
                        f"frame {idx} s.".split()
                    )
                    frame_test_result.append(False)
                    frame_test_status.append("Fail")

            if False in frame_test_result:
                verdict = fc.FAIL
                self.result.measured_result = FALSE
            else:
                verdict = fc.PASS
                self.result.measured_result = TRUE
                evaluation = "Passed"

            expected_val = f"{signal_name['resetCounter']} = {signal_name['resetCounter_nu']}"
            signal_summary[f"{signal_name['resetCounter']}"] = [expected_val, evaluation, verdict]
            remark = f"Check if {signal_name['resetCounter']} = {signal_name['resetCounter_nu']}, for all frames"
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            frame_number_list = list(range(0, len(reset_counter)))
            # add graph for  evaluated signals
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=reset_counter,
                    mode="lines",
                    name=f"{signal_name['resetCounter']}",
                    hovertemplate="Frame: %{x}<br>Value: %{y}<extra></extra>",
                ),
            )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=reset_counter_nu,
                    mode="lines",
                    name=f"{signal_name['resetCounter_nu']}",
                    hovertemplate="Frame: %{x}<br>Value: %{y}<extra></extra>",
                ),
            )
            if True in frame_test_result or False in frame_test_result:
                fig.add_trace(
                    go.Scatter(
                        x=frame_number_list,
                        y=[0] * len(frame_number_list),
                        mode="lines",  # 'lines' or 'markers'
                        name="Test Status",
                        hovertemplate="Frame: %{x}<br><br>status: %{text}<extra></extra>",
                        text=frame_test_status,
                    )
                )
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Frames",
                showlegend=True,
                title="Graphical Overview of Evaluated signals",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plots.append(fig)

            result_df = {
                "Verdict": {"value": verdict.title(), "color": fh.get_color(verdict)},
                fc.REQ_ID: ["1520660"],
                fc.TESTCASE_ID: ["42097"],
                fc.TEST_SAFETY_RELEVANT: [fc.SAFETY_RELEVANT_QM],
                fc.TEST_RESULT: [verdict],
            }
            self.result.details["Additional_results"] = result_df

        except Exception as e:
            _log.error(f"Error processing signals: {e}")
            self.result.measured_result = DATA_NOK
            self.sig_sum = f"<p>Error processing signals : {e}</p>"
            plots.append(self.sig_sum)

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)


@verifies("1520660")
@testcase_definition(
    name="SWRT_CNC_TRJPLA_ResetCounter",
    description="This tescase will verfiy that TRJPLA shall transform its data to the new "
    "origin by using ApEnvModelPort.resetOriginResult.originTransformation"
    "(indicated by TargetPosesPort.resetCounter == ApEnvModelPort.resetOriginResult.resetCounter_nu).",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_aqZBcEv3Ee6M5-WQsF_-tQ&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_p9KzlDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class TrjplaResetCounterTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TrjplaResetCounter,
        ]


def convert_dict_to_pandas(
    signal_summary: dict,
    table_remark="",
    table_title="",
):
    """Converts a dictionary to a Pandas DataFrame and creates an HTML table."""
    # Create a DataFrame from the dictionary
    evaluation_summary = pd.DataFrame(
        {
            "Signal Summary": {key: key for key, val in signal_summary.items()},
            "Expected Values": {key: val[0] for key, val in signal_summary.items()},
            "Summary": {key: val[1] for key, val in signal_summary.items()},
            "Verdict": {key: val[2] for key, val in signal_summary.items()},
        }
    )

    # Generate HTML table using build_html_table function
    return fh.build_html_table(evaluation_summary, table_remark, table_title)
