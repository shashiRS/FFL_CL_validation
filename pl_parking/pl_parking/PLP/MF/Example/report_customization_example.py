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
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "MF_EXAMPLE_3"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "Time"
        SCREEN_NU = "headUnitVisualizationPort.screen_nu"
        VELOCITY = "Vhcl.v"
        APSTATE = "apStates"
        CARAX = "Car.ax"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.SCREEN_NU: [
                ".headUnitVisualizationPort.screen_nu",  # tail of signal which would be matched with a root string
            ],
            self.Columns.VELOCITY: [
                "Vhcl.v",  # also the full version of signal can be included
                ".Conti_Veh_CAN.VehVelocity.VehVelocityExt",  # a signal can have defined different version of paths for different type of measurements
            ],
            self.Columns.TIME: [
                "Time",
                "Another version of signal",
            ],
            self.Columns.APSTATE: [
                ".planningCtrlPort.apStates",
            ],
            self.Columns.CARAX: [
                "Car.ax",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Functional test",  # this would be shown as a test step name in html report
    description=(
        "Check that after Planning control port is equal to 3, the maximum acceleration and speed does not"
        " exceed accepted values."
    ),
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepFtExample(TestStep):
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
        """
        _log.debug("Starting processing...")

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signals = self.readers[ALIAS]
        signals[Signals.Columns.TIMESTAMP] = signals.index

        ap_time = signals[Signals.Columns.TIME]
        ap_state = signals[Signals.Columns.APSTATE]
        car_ax = signals[Signals.Columns.CARAX]

        self.test_result = fc.INPUT_MISSING  # Result
        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        # "Ap.planningCtrlPort.apStates"[idx] == constants.ConstantsAupCore.THRESHOLD_T3
        t3 = None
        signal_summary = {}

        if np.any(ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN):
            t3 = np.argmax(ap_state == constants.GeneralConstants.AP_AVG_ACTIVE_IN)
        evaluation1 = " ".join(
            f"The evaluation of car acceleration is PASSED with values <"
            f"{constants.ConstantsAupCore.LONG_ACC_EGO_MAX} [m/s^2].".split()
        )
        eval_cond = True
        if t3 is not None:
            car_ax_mask = car_ax.iloc[t3:] >= constants.ConstantsAupCore.LONG_ACC_EGO_MAX

            if any(car_ax_mask):
                idx = car_ax_mask[car_ax_mask].idxmin()

                evaluation1 = " ".join(
                    f"The evaluation of car acceleration is FAILED with a value"
                    f" >={constants.ConstantsAupCore.LONG_ACC_EGO_MAX} [m/s^2] at timestamp "
                    f"{round(ap_time.loc[idx], 3)} [s].".split()
                )
                eval_cond = False

            if eval_cond:
                self.result.measured_result = TRUE
                verdict = "PASSED"
            else:
                self.result.measured_result = FALSE
                verdict = "FAILED"
        else:
            evaluation1 = " ".join(
                "Evaluation not possible, the trigger value AP_AVG_ACTIVE_IN(3) for "
                f"{signals_obj._properties[Signals.Columns.APSTATE]} was never found.".split()
            )
            self.result.measured_result = DATA_NOK
            verdict = "INVALID DATA"
        signal_summary["T3"] = [Signals.Columns.CARAX, evaluation1, verdict]

        remark = " ".join(
            "Checks that after AP.planningCtrlPort.apStates == 3 (AP_AVG_ACTIVE_IN), the "
            " maximum acceleration and speed does not "
            " exceed the accepted value".split()
        )
        self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
        plots.append(self.sig_sum)
        signals["status"] = ap_state.apply(lambda x: fh.get_status_label(x, ApStateConstants))
        self.fig = go.Figure()
        self.fig.add_trace(go.Scatter(x=ap_time, y=car_ax, mode="lines", name=Signals.Columns.CARAX))
        self.fig.add_trace(
            go.Scatter(x=ap_time, y=ap_state, mode="lines", name=Signals.Columns.APSTATE, text=signals["status"])
        )

        self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
        self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
        # self.fig.add_vrect(  # an example of how to add a highlight
        #     x0=ap_time.iat[1],
        #     x1=ap_time.iat[10],
        #     fillcolor="LimeGreen",
        #     line_width=0,
        #     opacity=0.3,
        #     # annotation_text="Example of highlight",
        #     layer="below",
        # )
        self.fig.add_vline(
            x=ap_time.iat[t3], line_width=1, line_dash="dash", line_color="darkslategray", annotation_text="T3"
        )
        fh.highlight_segments(
            self.fig, ap_state, ApStateConstants.AP_AVG_ACTIVE_IN, ap_time, "LightSalmon", "AP_AVG_ACTIVE_IN"
        )

        plots.append(self.fig)

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)


# Define the test case definition. This will include the name of the test case and a description of the test.


@testcase_definition(
    name="Test case customization example",
    description=("This an example of test case with two test steps."),
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FMD_uWvyAFdVEe6Src_hoJzMtg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F18557",
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class TestExampleCustomization(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepFtExample]  # in this list all the needed test steps are included


def convert_dict_to_pandas(  # this is a modified function from "workspace\pl_parking\pl_parking\common_ft_helper.py"
    signal_summary: dict,
    table_remark="",
    table_title="",
):
    """Converts a dictionary to a Pandas DataFrame and creates an HTML table."""
    # Create a DataFrame from the dictionary
    evaluation_summary = pd.DataFrame(  # here you can add columns for your table, use unique identifier for key column
        {
            "Trigger": {key: key for key, val in signal_summary.items()},
            "Signal Evaluation": {key: val[0] for key, val in signal_summary.items()},
            "Summary": {key: val[1] for key, val in signal_summary.items()},
            "Verdict": {key: val[2] for key, val in signal_summary.items()},
        }
    )

    # Generate HTML table using build_html_table function
    return fh.build_html_table(evaluation_summary, table_remark, table_title)


class ApStateConstants:
    """Class of ApState constants"""

    AP_INACTIVE = 0
    AP_SCAN_IN = 1
    AP_SCAN_OUT = 2
    AP_AVG_ACTIVE_IN = 3
    AP_AVG_ACTIVE_OUT = 4
    AP_AVG_PAUSE = 5
    AP_AVG_UNDO = 6
    AP_ACTIVE_HANDOVER_AVAILABLE = 7
    AP_AVG_FINISHED = 8
