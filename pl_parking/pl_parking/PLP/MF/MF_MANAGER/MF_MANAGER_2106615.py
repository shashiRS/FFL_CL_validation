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
ALIAS = "MF_MANAGER_2106615"


def get_result_color(result):
    """Method to give a signal status with verdict and color."""
    color_dict = {
        False: "#dc3545",  # signal is not valid
        True: "#28a745",
        "NOT ASSESSED": "#818589",
    }
    text_dict = {
        False: "FAILED",  # signal is not valid
        True: "PASSED",
        "NOT ASSESSED": "NOT ASSESSED",  # signal is not valid
    }

    return (
        f'<span align="center" style="width: 100%; height: 100%; display: block;background-color: {color_dict[result]}'
        f' ; color : #ffffff">{text_dict[result]}</span>'
    )


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        PARKSMCORESTATUS = "ParksMCoreStatus"
        LSCAEBA = "Lsca EBA"
        LSCABRAKEPORTREQUESTMODE = "Lsca Brake Port Request Mode"
        AUTOMATEDGUIDANCE = "automatedVehicleGuidanceState"
        APSTATE = "AP State"
        CARAX = "Car_ax"
        LACTRLREQUESTPORT = "laCtrlRequestPort"
        LOCTRLREQUESTPORT = "loCtrlRequestPort"
        TRAJ_CTRL_REQUEST = "Trajectory Control Request"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.TRAJ_CTRL_REQUEST: "AP.trajCtrlRequestPort.trajCtrlActive_nu",
            self.Columns.LACTRLREQUESTPORT: [
                "AP.laCtrlRequestPort.laCtrlRequestSource_nu",
            ],  # TODO FIX THIS aafter signal is available in mf_sil
            self.Columns.LOCTRLREQUESTPORT: "AP.loCtrlRequestPort.loCtrlRequestSource_nu",
            self.Columns.TIME: [
                "Time",
                "Another version of signal",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Functional test",  # this would be shown as a test step name in html report
    description=(
        "MF_MANAGER_Stack shall route the active Maneuvering Function's motion control request to Motion Control, when there's no active LSCA brake request and MF_MANAGER has not requested a safe stop."
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepMF_MANAGER(TestStep):
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
            max_delay = 8

            T1 = None

            self.test_result = fc.INPUT_MISSING  # Result
            self.result.measured_result = DATA_NOK  # Initializing the result with data nok
            # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
            plots = []

            signal_summary = {}  # Initializing the dictionary with data for final evaluation table

            signals = self.readers[ALIAS]
            signals[Signals.Columns.TIMESTAMP] = signals.index
            eval_cond_t1 = [False] * 4

            ap_time = round(signals[Signals.Columns.TIME], 3)
            traj_ctrl_request = signals[Signals.Columns.TRAJ_CTRL_REQUEST]

            lactrl_request_port = signals[Signals.Columns.LACTRLREQUESTPORT]
            loctrl_request_port = signals[Signals.Columns.LOCTRLREQUESTPORT]
            # # Define the search range

            if np.any(traj_ctrl_request == constants.TrajCtrlActive_nu.FOLLOW_TRAJ):
                T1 = np.argmax(traj_ctrl_request == constants.TrajCtrlActive_nu.FOLLOW_TRAJ)

            if T1 is not None:
                if lactrl_request_port.iloc[T1 - delay] == constants.LaCtrlRequestSource_nu.LADMC_REQ_SRC_NO_REQEUESTER:
                    eval_cond_t1[0] = True
                if loctrl_request_port.iloc[T1 - delay] == constants.LoCtrlRequestSource_nu.LODMC_REQ_SRC_NO_REQEUESTER:
                    eval_cond_t1[1] = True

                sub_series = lactrl_request_port.iloc[T1 : T1 + max_delay + 1]
                if not sub_series[sub_series != constants.LaCtrlRequestSource_nu.LADMC_REQ_SRC_NO_REQEUESTER].empty:
                    eval_cond_t1[2] = True

                    lactrl_t1_idx = sub_series[
                        sub_series != constants.LaCtrlRequestSource_nu.LADMC_REQ_SRC_NO_REQEUESTER
                    ].first_valid_index()
                    lactrl_t1_idx = list(signals.index).index(lactrl_t1_idx)

                    it_took = (lactrl_t1_idx - T1) / 100

                    eval_lat_t1 = f"Lactrl set to \
                {constants.LaCtrlRequestSource_nu.get_variable_name(lactrl_request_port.iloc[lactrl_t1_idx])} after {it_took} s within {max_delay/100} s."
                else:
                    eval_lat_t1 = f"Lactrl was not set to !=\
                {constants.LaCtrlRequestType.get_variable_name(constants.LaCtrlRequestSource_nu.LADMC_REQ_SRC_NO_REQEUESTER)} within {max_delay/100} s."

                sub_series = loctrl_request_port.iloc[T1 : T1 + max_delay + 1]
                if not sub_series[sub_series != constants.LoCtrlRequestSource_nu.LODMC_REQ_SRC_NO_REQEUESTER].empty:
                    eval_cond_t1[3] = True
                    loctrl_t1_idx = sub_series[
                        sub_series != constants.LoCtrlRequestSource_nu.LODMC_REQ_SRC_NO_REQEUESTER
                    ].first_valid_index()
                    loctrl_t1_idx = list(signals.index).index(loctrl_t1_idx)

                    it_took = (loctrl_t1_idx - T1) / 100

                    eval_lot_t1 = f"Loctrl set to \
                {constants.LoCtrlRequestSource_nu.get_variable_name(loctrl_request_port.iloc[loctrl_t1_idx])} after {it_took} s within {max_delay/100} s."
                else:
                    eval_lot_t1 = f"Loctrl was not set to != \
                {constants.LoCtrlRequestType.get_variable_name(constants.LoCtrlRequestSource_nu.LODMC_REQ_SRC_NO_REQEUESTER)} within {max_delay/100} s."

            signal_summary = {
                "Condition": {
                    "0": f"Before the state of {signals_obj._properties[Signals.Columns.TRAJ_CTRL_REQUEST]} \
            being set to {constants.TrajCtrlActive_nu.get_variable_name(constants.TrajCtrlActive_nu.FOLLOW_TRAJ)}, the signal \
            {signals_obj._properties[Signals.Columns.LACTRLREQUESTPORT][0]} should be set to {constants.LaCtrlRequestSource_nu.get_variable_name(constants.LaCtrlRequestSource_nu.LADMC_REQ_SRC_NO_REQEUESTER)}.",
                    "1": f"Before the state of {signals_obj._properties[Signals.Columns.TRAJ_CTRL_REQUEST]} \
            being set to {constants.TrajCtrlActive_nu.get_variable_name(constants.TrajCtrlActive_nu.FOLLOW_TRAJ)}, the signal \
            {signals_obj._properties[Signals.Columns.LOCTRLREQUESTPORT]} should be set to {constants.LoCtrlRequestSource_nu.get_variable_name(constants.LoCtrlRequestSource_nu.LODMC_REQ_SRC_NO_REQEUESTER)}.",
                    "2": f"After the state of {signals_obj._properties[Signals.Columns.TRAJ_CTRL_REQUEST]} \
            being set to {constants.TrajCtrlActive_nu.get_variable_name(constants.TrajCtrlActive_nu.FOLLOW_TRAJ)}, the signal \
            {signals_obj._properties[Signals.Columns.LACTRLREQUESTPORT][0]} should be set to !={constants.LaCtrlRequestSource_nu.get_variable_name(constants.LaCtrlRequestSource_nu.LADMC_REQ_SRC_NO_REQEUESTER)}.",
                    "3": f"After the state of {signals_obj._properties[Signals.Columns.TRAJ_CTRL_REQUEST]} \
            being set to {constants.TrajCtrlActive_nu.get_variable_name(constants.TrajCtrlActive_nu.FOLLOW_TRAJ)}, the signal \
            {signals_obj._properties[Signals.Columns.LOCTRLREQUESTPORT]} should be set to !={constants.LoCtrlRequestSource_nu.get_variable_name(constants.LoCtrlRequestSource_nu.LODMC_REQ_SRC_NO_REQEUESTER)}.",
                },
                "Evaluation": {
                    "0": (
                        f"Lactrl set to \
            {constants.LaCtrlRequestSource_nu.get_variable_name(lactrl_request_port.iloc[T1-delay])} at timestamp  {(T1-delay)/100} s."
                        if T1
                        else "NOT ASSESSED, T1 not found."
                    ),
                    "1": (
                        f"Loctrl set to \
            {constants.LoCtrlRequestSource_nu.get_variable_name(loctrl_request_port.iloc[T1-delay])} at timestamp  {(T1-delay)/100} s."
                        if T1
                        else "NOT ASSESSED, T1 not found."
                    ),
                    "2": eval_lat_t1 if T1 else "NOT ASSESSED, T1 not found.",
                    "3": eval_lot_t1 if T1 else "NOT ASSESSED, T1 not found.",
                },
                "Verdict": {
                    "0": get_result_color(eval_cond_t1[0]) if T1 is not None else get_result_color("NOT ASSESSED"),
                    "1": get_result_color(eval_cond_t1[1]) if T1 is not None else get_result_color("NOT ASSESSED"),
                    "2": get_result_color(eval_cond_t1[2]) if T1 is not None else get_result_color("NOT ASSESSED"),
                    "3": get_result_color(eval_cond_t1[3]) if T1 is not None else get_result_color("NOT ASSESSED"),
                },
            }
            if all(eval_cond_t1):
                self.result.measured_result = TRUE
                self.test_result = fc.PASS
            else:
                if T1 is not None:
                    self.result.measured_result = FALSE
                    self.test_result = fc.FAIL
                else:
                    self.result.measured_result = DATA_NOK
                    self.test_result = fc.NOT_ASSESSED
            T1 = f"{ap_time.iloc[T1]} s" if T1 is not None else "NOT ASSESSED"
            # T2 = f"{ap_time.iloc[T2]} s" if T2 is not None else "NOT ASSESSED"
            remark = f"<b>Legend:</b><br><br>\
                        delay = {delay/100} s <br>\
                        T1 :<b>{signals_obj._properties[Signals.Columns.TRAJ_CTRL_REQUEST]} == {constants.TrajCtrlActive_nu.get_variable_name(constants.TrajCtrlActive_nu.FOLLOW_TRAJ)}</b> ({T1})<br>"

            signal_summary = fh.build_html_table(pd.DataFrame(signal_summary), remark)
            plots.append(signal_summary)

            ap_time = ap_time.values.tolist()
            lactrl_request_port = lactrl_request_port.values.tolist()
            loctrl_request_port = loctrl_request_port.values.tolist()
            traj_ctrl_request = traj_ctrl_request.values.tolist()
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=traj_ctrl_request,
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.TRAJ_CTRL_REQUEST],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>"
                        f"Traj Ctrl Active:<br>"
                        f"{constants.TrajCtrlActive_nu.get_variable_name(state)}"
                        for idx, state in enumerate(traj_ctrl_request)
                    ],
                    hoverinfo="text",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=lactrl_request_port,
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.LACTRLREQUESTPORT][0],
                    # text=[f"{constants.LscaConstants.get_variable_name(value)}" for value in lsca_eba.values.tolist())],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>"
                        f"Lateral Ctrl Request:<br>"
                        f"{constants.LaCtrlRequestType.get_variable_name(state)}"
                        for idx, state in enumerate(lactrl_request_port)
                    ],
                    hoverinfo="text",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=loctrl_request_port,
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.LOCTRLREQUESTPORT],
                    # text=[f"{constants.LscaConstants.get_variable_name(value)}" for value in lsca_eba.values.tolist())],
                    text=[
                        f"Timestamp: {ap_time[idx]} <br>"
                        f"Longitudinal Ctrl Request:<br>"
                        f"{constants.LoCtrlRequestType.get_variable_name(state)}"
                        for idx, state in enumerate(loctrl_request_port)
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
        except Exception as err:
            print(str(err))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")
            signal_names = [x for x in signals_obj._properties.keys()]
            plots = []
            self.result.measured_result = DATA_NOK
            signal_missing = []
            signal_summary = {}
            for signal in signal_names:
                if signal not in signals.columns:
                    if isinstance(signals_obj._properties[signal], list):
                        for s in signals_obj._properties[signal]:
                            signal_missing.append(s)
                    else:
                        signal_missing.append(signals_obj._properties[signal])
            signal_missing = list(dict.fromkeys(signal_missing))
            signal_summary = {
                "Signal missing from measurement": {i: signal for i, signal in enumerate(signal_missing)},
            }
            signal_summary = fh.build_html_table(pd.DataFrame(signal_summary), "Signal missing")
            self.result.details["Plots"].append(signal_summary)


# Define the test case definition. This will include the name of the test case and a description of the test.
@testcase_definition(
    name="MF_MANAGER_2106615",
    description="When there is no maneuvering function (or AVGA) requesting control, MF_Manager shall provide its outputs towards motion control filled with default values.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_T76hwAFmEe-JmbR7EsJ0UA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_bFpNkIhREe62BpLgEHoMZA&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36638",
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class TestCaseFT(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepMF_MANAGER]


import os
import sys
import tempfile
from pathlib import Path

from tsf.core.utilities import debug


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to

    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.

    """
    # test_bsigs = r"C:\Users\uif94738\Downloads\AUPSim_UC_PerpRigth_B_LongPed_LSCAIntervention.erg"

    test_bsigs = r"C:\Users\uif94738\Downloads\AUPSim_UC_PerpRigth_B_LongPed_LSCAIntervention_.erg"
    debug(
        TestCaseFT,
        test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
        kpi_report=False,
        dev_report=True,
    )

    _log.debug("All done.")


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"

    out_folder = working_directory / "out"

    main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)
