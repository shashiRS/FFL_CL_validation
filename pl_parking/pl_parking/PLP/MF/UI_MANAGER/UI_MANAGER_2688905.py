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
ALIAS = "UI_MANAGER_2688905"


flag = {0: "FALSE", 1: "TRUE"}


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"

        PDC_USER_INTERACTION_LSCA_ACTIVE = "PDC_USER_ACTION"
        HMI_OUTPUT_USER_ACTION = "HMI_OUTPUT_USER_ACTION"
        door_fr_psgr = "Front passenger door"
        door_rear_left = "Rear left door"
        door_rear_right = "Rear right door"
        door_driver = "Driver door"
        front_lid = "Front lid"
        trunk_lid = "Trunk lid"
        SECTOR_DISTANCE_HMI = "SECTOR_DISTANCE_{0}_{1}"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.door_fr_psgr: "SignalManipulation.doorStatusPort_status_frontPsgr_nu",
            self.Columns.door_rear_left: "SignalManipulation.doorStatusPort_status_rearLeft_nu",
            self.Columns.door_rear_right: "SignalManipulation.doorStatusPort_status_rearRight_nu",
            self.Columns.door_driver: "SignalManipulation.doorStatusPort_status_driver_nu",
            self.Columns.front_lid: "SignalManipulation.additionalBCMStatusPort_frontLidOpen_nu",
            self.Columns.trunk_lid: "SignalManipulation.trunkLidStatusPort_open_nu",
            self.Columns.HMI_OUTPUT_USER_ACTION: "AP.hmiOutputPort.userActionHeadUnit_nu",
            self.Columns.PDC_USER_INTERACTION_LSCA_ACTIVE: "AP.PDCUserInteractionPort.lscaAutoActivate_nu",
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
                        self.Columns.SECTOR_DISTANCE_HMI.format(
                            side, x
                        ): f"AP.hmiInputPort.pdcSectors.{side.lower()}_{x}.smallestDistance_m",
                    }
                )


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="Default values for Partial availability",  # this would be shown as a test step name in html report
    description=(
        "In case of Partial availability, The HMIManager shall forward information the default values for sectors to InstrumentClusterDisplay."
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
            transition_events = []
            transition_message = []
            s1 = signals[Signals.Columns.door_fr_psgr]
            s2 = signals[Signals.Columns.door_rear_left]
            s3 = signals[Signals.Columns.door_rear_right]
            s4 = signals[Signals.Columns.door_driver]
            s5 = signals[Signals.Columns.front_lid]
            s6 = signals[Signals.Columns.trunk_lid]
            door_location_map_to_sectors = {
                Signals.Columns.door_fr_psgr: [
                    Signals.Columns.SECTOR_DISTANCE_HMI.format(signals_obj.RI, y) for y in range(4)
                ],
                Signals.Columns.door_rear_left: [
                    Signals.Columns.SECTOR_DISTANCE_HMI.format(signals_obj.LE, y) for y in range(4)
                ],
                Signals.Columns.door_rear_right: [
                    Signals.Columns.SECTOR_DISTANCE_HMI.format(signals_obj.RI, y) for y in range(4)
                ],
                Signals.Columns.door_driver: [
                    Signals.Columns.SECTOR_DISTANCE_HMI.format(signals_obj.LE, y) for y in range(4)
                ],
                Signals.Columns.front_lid: [
                    Signals.Columns.SECTOR_DISTANCE_HMI.format(signals_obj.FR, y) for y in range(4)
                ],
                Signals.Columns.trunk_lid: [
                    Signals.Columns.SECTOR_DISTANCE_HMI.format(signals_obj.RE, y) for y in range(4)
                ],
            }

            series_dict = {
                Signals.Columns.door_fr_psgr: s1,
                Signals.Columns.door_rear_left: s2,
                Signals.Columns.door_rear_right: s3,
                Signals.Columns.door_driver: s4,
                Signals.Columns.front_lid: s5,
                Signals.Columns.trunk_lid: s6,
            }

            any_door_open_dict = [name for name, series in series_dict.items() if (1 in series.values)]

            if any_door_open_dict:
                door_name = any_door_open_dict[0]
                door_open_mask = signals[door_name] == constants.UiManager.DoorStatus.DOOR_STATUS_OPEN
                sectors = door_location_map_to_sectors[door_name]

                T1 = list(signals.index).index(signals[door_name][door_open_mask].index[0])
                timestamp_events = [T1] * len(sectors)
                for sector in sectors:
                    sub_series = signals[sector].iloc[T1 : T1 + max_delay + 1]
                    if not sub_series[sub_series >= constants.UiManager.PDW_DEFAULT_MINIMUM_DISTANCE].empty:
                        transition_events.append(True)
                        end_idx = sub_series[sub_series >= constants.UiManager.PDW_DEFAULT_MINIMUM_DISTANCE].first_valid_index()
                        end_idx = list(signals.index).index(end_idx)

                        it_took = (end_idx - T1) * 10

                        transition_message.append(
                            f"HMIManager did forward information the default values for sectors to Instrument Cluster Display, after {it_took} ms, within {max_delay * 10} ms of Partial availability."
                        )
                    else:
                        transition_events.append(False)
                        transition_message.append(
                            f"HMIManager did not forward information the default values for sectors to Instrument Cluster Display, within {max_delay * 10} ms of Partial availability."
                        )

                signal_summary = {
                    "Timestamp [s]": {idx: ap_time.iloc[x] for idx, x in enumerate(timestamp_events)},
                    "Evaluation": {idx: x for idx, x in enumerate(transition_message)},
                    "Verdict": {idx: ui_helper.get_result_color(x) for idx, x in enumerate(transition_events)},
                }
            else:
                signal_summary = {
                    "Timestamp [s]": {"0": "-"},
                    "Evaluation": {"0": "No door was opened."},
                    "Verdict": {"0": f"{ui_helper.get_result_color('NOT ASSESSED')}"},
                }

            if all(transition_events) and len(transition_events) > 0:
                self.result.measured_result = TRUE
                self.test_result = fc.PASS
            elif any(timestamp_events):
                self.result.measured_result = FALSE
                self.test_result = fc.FAIL
            else:
                self.result.measured_result = DATA_NOK
                self.test_result = fc.INPUT_MISSING
            table_title = "Check if HMIManager forwards information the default values for sectors to Instrument Cluster Display when in Partial availability."
            remark = f"<b>Signals evaluated:</b><br><br>\
                       Input: <b>{signals_obj._properties[door_name]} == {constants.UiManager.DoorStatus.get_variable_name(constants.UiManager.DoorStatus.DOOR_STATUS_OPEN)}</b><br> \
                       Output: <b>{signals_obj._properties[door_location_map_to_sectors[door_name][0]].replace('_0.','_%.')}</b>"

            signal_summary = fh.build_html_table(pd.DataFrame(signal_summary), remark, table_title)
            plots.append(signal_summary)

            ap_time = ap_time.values.tolist()
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=signals[door_name].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[door_name],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>"
                        f"Door status:<br>"
                        f"{constants.UiManager.DoorStatus.get_variable_name(state)}"
                        for idx, state in enumerate(signals[door_name].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )
            for sector in sectors:

                fig.add_trace(
                    go.Scatter(
                        x=ap_time,
                        y=signals[sector].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[sector],
                        text=[
                            f"Timestamp: {ap_time[idx]} <br>" f"HMI PDC minimum distance:<br>" f"{state} m"
                            for idx, state in enumerate(signals[sector].values.tolist())
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
    name="UI_MANAGER_2688905",
    description="In case of Partial availability, The HMIManager shall forward information the default values for sectors to InstrumentClusterDisplay.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_ZdvgYXpsEe-9FrFCDLx05w&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_ns_CwE4gEe6M5-WQsF_-tQ&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class TestCaseFT(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepUI_MANAGER]
