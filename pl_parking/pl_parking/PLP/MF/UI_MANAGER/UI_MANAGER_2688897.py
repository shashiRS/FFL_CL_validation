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
ALIAS = "UI_MANAGER_2688897"


flag = {0: "FALSE", 1: "TRUE"}


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"

        PDC_USER_ACTION = "PDC_USER_ACTION"
        HMI_OUTPUT_USER_ACTION = "HMI_OUTPUT_USER_ACTION"
        VHCL_V = "VHCL_V"
        Rear_Volume = "Rear_Volume"
        Front_Volume = "Front_Volume"
        WHEEL_FL = "WHEEL_FL"
        WHEEL_FR = "WHEEL_FR"
        WHEEL_RL = "WHEEL_RL"
        WHEEL_RR = "WHEEL_RR"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.HMI_OUTPUT_USER_ACTION: "AP.hmiOutputPort.userActionHeadUnit_nu",
            self.Columns.PDC_USER_ACTION: "AP.PDCUserInteractionPort.pdcUserActionHeadUnit_nu",
            self.Columns.TIME: [
                "Time",
            ],
            self.Columns.VHCL_V: "Vhcl.v",
            self.Columns.Rear_Volume: "AP.toneOutputPort.RearVolume_nu",
            self.Columns.Front_Volume: "AP.toneOutputPort.FrontVolume_nu",
            self.Columns.WHEEL_FL: "AP.odoInputPort.odoSigFcanPort.wheelMeasurements.wheelDrivingDirections.wheelDrivingDirection_FL_nu",
            self.Columns.WHEEL_FR: "AP.odoInputPort.odoSigFcanPort.wheelMeasurements.wheelDrivingDirections.wheelDrivingDirection_FR_nu",
            self.Columns.WHEEL_RL: "AP.odoInputPort.odoSigFcanPort.wheelMeasurements.wheelDrivingDirections.wheelDrivingDirection_RL_nu",
            self.Columns.WHEEL_RR: "AP.odoInputPort.odoSigFcanPort.wheelMeasurements.wheelDrivingDirections.wheelDrivingDirection_RR_nu",
        }


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="Check if HMIInterface sends request to reduce volume",  # this would be shown as a test step name in html report
    description=(
        "If the ego vehicle is in standstill for a defined time, the HMIManager shall forward an input to InstrumentClusterDisplay about the reduced acoustical warning,"
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

            T1 = None

            self.test_result = fc.INPUT_MISSING  # Result
            self.result.measured_result = DATA_NOK  # Initializing the result with data nok

            plots = []

            signal_summary = {}  # Initializing the dictionary with data for final evaluation table

            signals = self.readers[ALIAS]
            signals[Signals.Columns.TIMESTAMP] = signals.index
            ap_time = round(signals[Signals.Columns.TIME], 3)
            velocity = signals[Signals.Columns.VHCL_V]

            wheelfl = signals[Signals.Columns.WHEEL_FL]
            wheelfr = signals[Signals.Columns.WHEEL_FR]
            wheelrl = signals[Signals.Columns.WHEEL_RL]
            wheelrr = signals[Signals.Columns.WHEEL_RR]

            # check ego vehicle stand still
            if any(signals[Signals.Columns.Rear_Volume] != 0):
                tone_h = signals[Signals.Columns.Rear_Volume]
            else:
                tone_h = signals[Signals.Columns.Front_Volume]

            velocity_standstill = velocity < constants.SilCl.PDWConstants.VEH_STANDSTILL
            wheelfl_standstill = wheelfl == constants.SilCl.PDWConstants.WheelDirection.WHEEL_DIRECTION_NONE
            wheelfr_standstill = wheelfr == constants.SilCl.PDWConstants.WheelDirection.WHEEL_DIRECTION_NONE
            wheelrl_standstill = wheelrl == constants.SilCl.PDWConstants.WheelDirection.WHEEL_DIRECTION_NONE
            wheelrr_standstill = wheelrr == constants.SilCl.PDWConstants.WheelDirection.WHEEL_DIRECTION_NONE
            car_moves = velocity > constants.SilCl.PDWConstants.VEH_STANDSTILL
            car_moves_index = velocity[car_moves].index[0]

            car_standstill_index = velocity.loc[car_moves_index:][
                velocity_standstill & wheelfl_standstill & wheelfr_standstill & wheelrl_standstill & wheelrr_standstill
            ].index[0]

            tone_h_events = tone_h.loc[car_standstill_index:].rolling(2).apply(lambda x: x[1] != x[0], raw=True)
            transition_events = []
            transition_message = []
            timestamp_tone_h_events = [row for row, val in tone_h_events.items() if val == 1]
            if timestamp_tone_h_events:
                for ts in timestamp_tone_h_events:
                    # pdw_sys_state = pdc_series.loc[ts]
                    T1 = list(signals.index).index(ts)
                    if tone_h.iloc[T1 - 1] < tone_h.iloc[T1]:
                        transition_events.append(False)
                        transition_message.append(
                            f"Tone H did not reduce volume, it transitioned from {tone_h.iloc[T1-1]} to {tone_h.iloc[T1]},."
                        )
                    else:
                        transition_events.append(True)
                        transition_message.append(
                            f"Tone H reduced volume, transitioning from {tone_h.iloc[T1-1]} to {tone_h.iloc[T1]},."
                        )

                it_took = round(ap_time.loc[timestamp_tone_h_events[0]] - ap_time.loc[car_standstill_index], 3)
                # transition_events.append(True)
                # timestamp_tone_h_events.insert(0, f"{ap_time.loc[timestamp_tone_h_events[0]]} - {ap_time.loc[car_standstill_index]}")
                # transition_message.insert(0, f"Car was in standstill for {it_took} s, before HMIInterface forwarded an input to InstrumentClusterDisplay about the reduced acoustical warning.")
                signal_summary = {
                    "Timestamp [s]": {
                        -1: f"{ap_time.loc[car_standstill_index]} -> {ap_time.loc[timestamp_tone_h_events[0]]}"
                    },
                    "Evaluation": {
                        -1: f"Car was in standstill for {it_took} s, before HMIInterface forwarded an input to InstrumentClusterDisplay about the reduced acoustical warning."
                    },
                    "Verdict": {-1: ui_helper.get_result_color(fc.PASS)},
                }
                signal_summary["Evaluation"].update({idx: x for idx, x in enumerate(transition_message)})
                signal_summary["Verdict"].update(
                    {idx: ui_helper.get_result_color(x) for idx, x in enumerate(transition_events)}
                )
                signal_summary["Timestamp [s]"].update(
                    {idx: ap_time.loc[x] for idx, x in enumerate(timestamp_tone_h_events)}
                )

            else:
                signal_summary = {
                    "Timestamp [s]": {"0": "-"},
                    "Evaluation": {"0": "No Tone H transitions."},
                    "Verdict": {"0": f"{ui_helper.get_result_color(fc.FAIL)}"},
                }
            if all(transition_events) and len(transition_events) > 0:
                self.result.measured_result = TRUE
                self.test_result = fc.PASS
            else:
                self.result.measured_result = FALSE
                self.test_result = fc.FAIL

            table_title = (
                "HMIManager shall forward an input to InstrumentClusterDisplay about the reduced acoustical warning"
            )
            remark = f"<b>Signals evaluated:</b><br><br>\
                       <b>{signals_obj._properties[tone_h.name]}</b><br>\
                        <b>{signals_obj._properties[velocity.name]} < {constants.SilCl.PDWConstants.VEH_STANDSTILL}</b>"

            signal_summary = fh.build_html_table(pd.DataFrame(signal_summary), remark, table_title)
            plots.append(signal_summary)

            ap_time = ap_time.values.tolist()
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=signals[tone_h.name].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[tone_h.name],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>" f"Tone H<br>" f"{state}"
                        for idx, state in enumerate(signals[tone_h.name].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=signals[Signals.Columns.VHCL_V].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.VHCL_V],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>" f"Velocity<br>" f"{state}"
                        for idx, state in enumerate(signals[Signals.Columns.VHCL_V].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )

            fig.layout = go.Layout(
                showlegend=True, yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]"
            )
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
    name="UI_MANAGER_2688897",
    description="If the ego vehicle is in standstill for a defined time, the HMIManager shall forward an input to InstrumentClusterDisplay about the reduced acoustical warning,",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_ZdsdEXpsEe-9FrFCDLx05w&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_ns_CwE4gEe6M5-WQsF_-tQ&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class TestCaseFT(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepUI_MANAGER]
